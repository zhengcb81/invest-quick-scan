"""Private readonly C06 owner capture. No migration or production capability.

The namespaces are captured sequentially, never represented as a cross-file
atomic transaction. Unattested legacy originals are separate history, never
current subject coverage. Retained snapshots here are bounded process captures;
durable public freeze/dispatch sidecars remain in the full C06 implementation.
"""
from __future__ import annotations

import copy
import base64
import hashlib
import json
import sqlite3
import stat
import time
from collections import OrderedDict
from contextlib import closing
from datetime import datetime, timezone

from stockwiki.identity_snapshot import listing_id_for_security
from stockwiki.quick_scan_analysis import (
    AnalysisSubjectError,
    AnalysisSubjectStore,
    perimeter_sha256,
    validate_receipt,
    validate_subject,
)
from stockwiki.quick_scan_observations import (
    ObservationImportError, QuickScanObservationStore, legacy_wire_pending,
)
from stockwiki.quick_scan_store import QuickScanStore

MAX_SOURCE_ROWS = 5000
MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 16 * 1024 * 1024
MAX_SNAPSHOTS = 32
SNAPSHOT_TTL_SECONDS = 3600


class QueryReadError(ValueError):
    """Named refusal without silently falling back to an empty/live result."""


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise QueryReadError("owner_duplicate_json_key")
        value[key] = item
    return value


def _json(raw):
    value = json.loads(raw, object_pairs_hook=_pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(
                           QueryReadError("owner_nonfinite_json")))
    _bytes(value)
    return value


class _IdentityView:
    def __init__(self, data):
        self.entities = {row["entity_id"]: copy.deepcopy(row)
                         for row in data["quick_scan_entity"]}
        for value in self.entities.values():
            value["securities"] = [copy.deepcopy(row) for row in data["quick_scan_security"]
                                   if row["entity_id"] == value["entity_id"]]
            value["segments"] = [copy.deepcopy(row) for row in data["quick_scan_segment"]
                                 if row["entity_id"] == value["entity_id"]]

    def get_entity(self, entity_id):
        return copy.deepcopy(self.entities.get(entity_id))


class QueryReader:
    """Capture real owner SQLite with an injected, trusted pure wire contract."""

    def __init__(self, paths, *, contract, clock=None, elapsed_clock=None):
        self.paths = paths
        self.contract = contract
        self.clock = clock or (lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.elapsed_clock = elapsed_clock or time.monotonic
        self._snapshots = OrderedDict()
        self._snapshot_bytes = 0
        # Constructors only calculate paths; never call their _connect/migrate.
        self.identity = QuickScanStore(paths)
        self.subjects = AnalysisSubjectStore(paths)
        self.observations = QuickScanObservationStore(paths)
        self._owner_context = {"store_id": self.observations.store_id, "observation_refs": {}}

    @property
    def owner_context(self):
        return copy.deepcopy(self._owner_context)

    def _capture(self, namespace, path, versions, tables, *, request=None):
        captured = {"namespace": namespace, "schema_version": None, "status": "missing",
                    "sequence": 0, "read_at": self.clock(), "content_sha256": None}
        if not path.exists():
            return captured, None
        captured["status"] = "read_error"
        try:
            meta = path.lstat()
            if (not stat.S_ISREG(meta.st_mode) or path.is_symlink()
                or getattr(meta, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)):
                return captured, None
            # Do not create/update live SQLite WAL shared-memory files. An owner
            # checkpoint/export is required for that mode; immutable=1 would
            # silently ignore WAL and must not be used as a readonly shortcut.
            if any(path.with_name(path.name + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
                return captured, None
            with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2.0)) as con:
                con.row_factory = sqlite3.Row
                con.execute("PRAGMA query_only=ON")
                con.execute("BEGIN")
                version = int(con.execute("PRAGMA user_version").fetchone()[0])
                captured["schema_version"] = version
                if version not in versions:
                    captured["status"] = "schema_unavailable"
                    return captured, None
                data = {}
                total_bytes = 0
                for table in tables:  # Constant table allowlist, never caller SQL.
                    rows = []
                    parameters = ()
                    selection = ""
                    if namespace == "observations":
                        # Read only the requested rows and their ORIGINAL import
                        # receipts; unrequested history must not exhaust a scan.
                        refs = request["payload"]["subject_refs"]
                        entities = sorted({r["entity_id"] for r in refs})
                        fields = request["payload"]["field_ids"]
                        parameters = (*entities, *fields, request["payload"]["information_cutoff"])
                        selection = (" WHERE entity_id IN (" + ",".join("?" for _ in entities)
                                     + ") AND field_id IN (" + ",".join("?" for _ in fields)
                                     + ") AND information_cutoff<=?")
                        if table == "quick_scan_import_item":
                            selection = (" WHERE (package_id,item_id) IN (SELECT package_id,item_id "
                                         "FROM quick_scan_observation" + selection + ")")
                    for row in con.execute(f"SELECT * FROM {table}" + selection + " ORDER BY rowid", parameters):
                        value = dict(row)
                        total_bytes += len(_bytes(value))
                        if len(rows) >= MAX_SOURCE_ROWS or total_bytes > MAX_SOURCE_BYTES:
                            raise QueryReadError("owner_capture_limit")
                        rows.append(value)
                    data[table] = rows
                captured["sequence"] = max(
                    (int(con.execute(f"SELECT COALESCE(MAX(rowid),0) FROM {table}").fetchone()[0])
                     for table in tables), default=0)
                if namespace == "observations":
                    captured["sequence"] = int(con.execute(
                        "SELECT COALESCE(MAX(ack_sequence),0) FROM quick_scan_import_item").fetchone()[0])
                    data["counters"] = {"observation_sequence": int(con.execute(
                        "SELECT COALESCE(MAX(import_sequence),0) FROM quick_scan_observation").fetchone()[0]),
                        "ack_sequence": captured["sequence"]}
                elif namespace == "identity":
                    data["counters"] = {"member_sequence": int(con.execute(
                        "SELECT COALESCE(MAX(rowid),0) FROM quick_scan_member_history").fetchone()[0])}
                captured["content_sha256"] = _digest({"schema_version": version, "tables": data})
                captured["status"] = "available"
                captured["read_at"] = self.clock()
                con.rollback()
                return captured, data
        except (OSError, sqlite3.Error, KeyError, TypeError, ValueError, OverflowError, RecursionError):
            captured["content_sha256"] = None
            return captured, None

    def _profile(self, ref, identity, subject_data, cutoff):
        entity = identity.get_entity(ref["entity_id"])
        if entity is None:
            return None
        rows = [row for row in subject_data["analysis_subject"]
                if row["analysis_subject_id"] == ref["analysis_subject_id"]
                and row["analysis_subject_revision"] == ref["analysis_subject_revision"]]
        if len(rows) != 1:
            return None
        row = rows[0]
        subject = _json(row["subject_json"])
        validate_subject(subject, identity_store=identity)
        if any(row[k] != subject[k] for k in (
            "analysis_subject_id", "analysis_subject_revision", "display_name", "primary_issuer_id",
            "anchor_listing_id", "scope_kind", "scope_as_of", "perimeter_coverage")):
            raise QueryReadError("owner_subject_columns_mismatch")
        if (row["perimeter_sha256"] != perimeter_sha256(subject)
            or _json(row["memberships_json"]) != subject["memberships"]):
            raise QueryReadError("owner_subject_columns_mismatch")
        if _digest(subject) != row["subject_sha256"]:
            raise QueryReadError("owner_subject_hash_mismatch")
        receipts = [r for r in subject_data["reporting_perimeter_receipt"]
                    if r["subject_key"] == row["subject_key"]]
        if len(receipts) != 1:
            raise QueryReadError("owner_perimeter_receipt_missing")
        receipt = _json(receipts[0]["receipt_json"])
        validate_receipt(receipt, subject)
        if any(receipts[0][k] != receipt[k] for k in (
            "receipt_id", "status", "evidence_ref", "perimeter_sha256")):
            raise QueryReadError("owner_receipt_columns_mismatch")
        if _digest(receipt) != receipts[0]["receipt_sha256"]:
            raise QueryReadError("owner_receipt_hash_mismatch")
        if (ref["primary_issuer_id"] != subject["primary_issuer_id"]
            or ref["perimeter_sha256"] != perimeter_sha256(subject)
            or subject["scope_as_of"][:10] > cutoff):
            return None
        # A group member is not by itself an attested scan-entity/legal-issuer
        # bridge. Distinct ids await the explicit owner bridge, never name joins.
        if ref["entity_id"] != subject["primary_issuer_id"]:
            return None
        if ref["scope"] == "security":
            securities = [s for s in entity["securities"] if s["security_id"] == ref["security_id"]]
            if len(securities) != 1 or (ref["listing_id"] is not None
                and listing_id_for_security(securities[0]) != ref["listing_id"]):
                return None
        elif ref["scope"] == "segment":
            if not any(s["segment_id"] == ref["segment_id"] for s in entity["segments"]):
                return None
        return {"subject_ref": copy.deepcopy(ref), "canonical_name": entity["canonical_name"],
                "observations": []}

    def _legacy_projection(self, record, imports, request):
        """Validate independent owner columns/ACK before presenting original bytes."""
        try:
            raw = record["payload_json"].encode("utf-8")
            if len(raw) > self.contract.MAX_OBSERVATION_BYTES:
                raise QueryReadError("owner_observation_limit")
            obs = _json(raw)
            if _digest(obs) != record["payload_sha256"]:
                raise QueryReadError("owner_observation_hash_mismatch")
            scalar_fields = ("observation_id", "entity_id", "security_id", "listing_id",
                "segment_id", "source_binding_ref", "identity_revision", "field_id", "question_id",
                "scope", "observed_at", "information_cutoff")
            if any(record[k] != obs.get(k) for k in scalar_fields):
                raise QueryReadError("owner_observation_columns_mismatch")
            execution = obs["execution"]
            if (any(record[k] != execution[k] for k in ("provider", "model_resolved"))
                or record["answer_status"] != obs["answer"]["status"]
                or record["reported_score"] != obs["answer"].get("score")):
                raise QueryReadError("owner_observation_columns_mismatch")
            ack_rows = [r for r in imports if r["package_id"] == record["package_id"]
                        and r["item_id"] == record["item_id"]]
            if len(ack_rows) != 1:
                raise QueryReadError("owner_original_ack_missing")
            ack_row = ack_rows[0]
            ack = self.observations._checked_original_ack(ack_row, record)
            if (legacy_wire_pending(ack) or ack["consumer"] != {
                "component": "StockWiki", "namespace": "quick_scan", "store_id": self.observations.store_id}
                or ack_row["store_id"] != self.observations.store_id
                or ack["status"] != "accepted" or ack["error_code"] is not None
                or type(record["import_sequence"]) is not int or record["import_sequence"] < 1
                or ack_row["ack_sequence"] != record["import_sequence"]
                or record["imported_at"] != ack_row["received_at"]):
                raise QueryReadError("owner_original_ack_mismatch")
            # The captured ACK has strict JSON too; the existing pure owner
            # validator is reused above, and duplicate-key JSON is not accepted.
            if _json(ack_row["ack_json"]) != ack:
                raise QueryReadError("owner_original_ack_mismatch")
            if (self.contract._utc(ack_row["received_at"]) < self.contract._utc(obs["observed_at"])
                or self.contract._utc(ack_row["received_at"]) > self.contract._utc(self.clock())):
                raise QueryReadError("owner_original_ack_time_mismatch")
            refs = request["payload"]["subject_refs"]
            model_filter = request["payload"]["model_filter"]
            if (not request["payload"]["include_history"]
                or not any(all(obs[k] == r[k] for k in ("entity_id", "security_id", "segment_id", "scope"))
                           for r in refs)
                or (model_filter is not None
                    and any(execution[k] != model_filter[k] for k in ("provider", "model_resolved")))):
                return None
            # Stored subject columns are never a substitute for a retained
            # before-send dispatch receipt. No subject binding is manufactured.
            reference = {"payload_sha256": record["payload_sha256"], "binding_sha256": None,
                "observation_sequence": record["import_sequence"], "ack_sequence": ack_row["ack_sequence"],
                "ingest_status": ack_row["status"], "qualification_status": record["qualification_status"]}
            self._owner_context["observation_refs"][record["observation_id"]] = reference
            return {"observation_id": record["observation_id"],
                "payload_sha256": record["payload_sha256"], "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "original_json_base64": base64.b64encode(raw).decode("ascii"),
                "observation_wire_profile": "stockwiki-portable-observation/1.0.0",
                "binding_status": "legacy_unbound", "subject_binding": None,
                **{k: reference[k] for k in ("observation_sequence", "ack_sequence", "ingest_status", "qualification_status")}}
        except (ObservationImportError, KeyError, TypeError, ValueError, UnicodeError, RecursionError) as exc:
            raise QueryReadError("owner_observation_read_error") from exc

    def _remember(self, response):
        result = copy.deepcopy(response["result"])
        owner = self.owner_context
        size = len(_bytes(result)) + len(_bytes(owner))
        if size > MAX_SNAPSHOT_BYTES:
            raise QueryReadError("snapshot_retention_limit")
        snapshot_id = result["watermark"]["snapshot_id"]
        old = self._snapshots.pop(snapshot_id, None)
        if old is not None:
            self._snapshot_bytes -= old["bytes"]
        while self._snapshots and (len(self._snapshots) >= MAX_SNAPSHOTS
                                  or self._snapshot_bytes + size > MAX_SNAPSHOT_BYTES):
            _, removed = self._snapshots.popitem(last=False)
            self._snapshot_bytes -= removed["bytes"]
        self._snapshots[snapshot_id] = {"result": result, "owner": owner, "bytes": size,
            "created": self.elapsed_clock(), "query_sha256": result["watermark"]["query_sha256"]}
        self._snapshot_bytes += size

    def _replay(self, request):
        snapshot_id = request["payload"]["snapshot_id"]
        captured = self._snapshots.get(snapshot_id)
        if captured is None:
            raise QueryReadError("snapshot_unavailable")
        if self.elapsed_clock() - captured["created"] > SNAPSHOT_TTL_SECONDS:
            self._snapshot_bytes -= self._snapshots.pop(snapshot_id)["bytes"]
            raise QueryReadError("snapshot_expired")
        if captured["query_sha256"] != self.contract.query_sha256(request):
            raise QueryReadError("snapshot_query_mismatch")
        response = {"message_type": "response", "schema_version": "2.0.0",
            "request_id": request["request_id"], "operation": "get_profiles", "response_at": self.clock(),
            "result": copy.deepcopy(captured["result"])}
        self.contract.validate_response(response, expected_request=request, expected_owner=captured["owner"])
        self._owner_context = copy.deepcopy(captured["owner"])
        self._snapshots.move_to_end(snapshot_id)
        return response

    def get_profiles(self, request):
        self.contract.validate_request(request)
        self._owner_context = {"store_id": self.observations.store_id, "observation_refs": {}}
        if request["payload"]["snapshot_id"] is not None:
            return self._replay(request)
        identity_mark, identity_data = self._capture("identity", self.identity.database_path, {5, 6},
            ("quick_scan_entity", "quick_scan_security", "quick_scan_segment"))
        subject_mark, subject_data = self._capture("analysis_subjects", self.subjects.database_path, {1},
            ("analysis_subject", "reporting_perimeter_receipt"))
        observation_mark, observation_data = self._capture("observations", self.observations.database_path, {2},
            ("quick_scan_observation", "quick_scan_import_item"), request=request)
        marks = [identity_mark, subject_mark, observation_mark]
        profiles, missing = [], []
        identity = _IdentityView(identity_data) if identity_data is not None else None
        for ref in request["payload"]["subject_refs"]:
            try:
                profile = (self._profile(ref, identity, subject_data, request["payload"]["information_cutoff"])
                           if identity is not None and subject_data is not None else None)
            except (AnalysisSubjectError, QueryReadError, KeyError, TypeError, ValueError, RecursionError) as exc:
                raise QueryReadError("owner_subject_read_error") from exc
            if profile is None:
                missing.append(copy.deepcopy(ref))
            else:
                profiles.append(profile)
        failed = any(mark["status"] != "available" for mark in marks)
        legacy = []
        if not failed:
            for record in observation_data["quick_scan_observation"]:
                row = self._legacy_projection(record, observation_data["quick_scan_import_item"], request)
                if row is not None:
                    legacy.append(row)
        now = self.clock()
        result = {
            "status": "unavailable" if failed else "coverage_gap", "profiles": profiles,
            "missing_subject_refs": missing, "legacy_unbound_observations": legacy,
            "coverage": {"status": "unknown" if failed else "not_covered",
                "requested_markets": [], "covered_markets": [],
                "requested_field_ids": list(request["payload"]["field_ids"]), "covered_field_ids": [],
                "missing_field_ids": list(request["payload"]["field_ids"]),
                "scores_available": False, "facts_available": False,
                "reason": "owner_source_unavailable" if failed else "no_bound_observation_coverage"},
            "watermark": {"store_id": self.observations.store_id, "snapshot_id": "PENDING",
                "member_sequence": identity_data["counters"]["member_sequence"] if identity_data else 0,
                "observation_sequence": observation_data["counters"]["observation_sequence"] if observation_data else 0,
                "ack_sequence": observation_mark["sequence"], "read_at": now,
                "read_consistency": "sequential_owner_reads", "source_watermarks": marks},
        }
        response = self.contract.seal_response({"message_type": "response", "schema_version": "2.0.0",
            "request_id": request["request_id"], "operation": "get_profiles", "response_at": now,
            "result": result}, request=request)
        self.contract.validate_response(response, expected_request=request, expected_owner=self.owner_context)
        self._remember(response)
        return response
