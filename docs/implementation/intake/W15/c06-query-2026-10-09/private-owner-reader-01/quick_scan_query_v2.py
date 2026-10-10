"""Private readonly C06 owner capture. No migration or production capability.

The namespaces are captured sequentially, never represented as a cross-file
atomic transaction. Nonempty observation projection remains explicitly pending.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import stat
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
from stockwiki.quick_scan_observations import QuickScanObservationStore
from stockwiki.quick_scan_store import QuickScanStore

MAX_SOURCE_ROWS = 5000
MAX_SOURCE_BYTES = 8 * 1024 * 1024


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

    def __init__(self, paths, *, contract, clock=None):
        self.paths = paths
        self.contract = contract
        self.clock = clock or (lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        # Constructors only calculate paths; never call their _connect/migrate.
        self.identity = QuickScanStore(paths)
        self.subjects = AnalysisSubjectStore(paths)
        self.observations = QuickScanObservationStore(paths)
        self._owner_context = {"store_id": self.observations.store_id, "observation_refs": {}}

    @property
    def owner_context(self):
        return copy.deepcopy(self._owner_context)

    def _capture(self, namespace, path, versions, tables):
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
                    for row in con.execute(f"SELECT * FROM {table} ORDER BY rowid"):
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
                    captured["sequence"] = max(
                        (row["ack_sequence"] for row in data["quick_scan_import_item"]), default=0)
                captured["content_sha256"] = _digest({"schema_version": version, "tables": data})
                captured["status"] = "available"
                captured["read_at"] = self.clock()
                con.rollback()
                return captured, data
        except (OSError, sqlite3.Error, KeyError, TypeError, ValueError, OverflowError):
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
        if _digest(subject) != row["subject_sha256"]:
            raise QueryReadError("owner_subject_hash_mismatch")
        receipts = [r for r in subject_data["reporting_perimeter_receipt"]
                    if r["subject_key"] == row["subject_key"]]
        if len(receipts) != 1:
            raise QueryReadError("owner_perimeter_receipt_missing")
        receipt = _json(receipts[0]["receipt_json"])
        validate_receipt(receipt, subject)
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

    def get_profiles(self, request):
        self.contract.validate_request(request)
        self._owner_context = {"store_id": self.observations.store_id, "observation_refs": {}}
        if request["payload"]["snapshot_id"] is not None:
            raise QueryReadError("snapshot_unavailable")
        identity_mark, identity_data = self._capture("identity", self.identity.database_path, {5, 6},
            ("quick_scan_entity", "quick_scan_security", "quick_scan_segment"))
        subject_mark, subject_data = self._capture("analysis_subjects", self.subjects.database_path, {1},
            ("analysis_subject", "reporting_perimeter_receipt"))
        observation_mark, observation_data = self._capture("observations", self.observations.database_path, {2},
            ("quick_scan_observation", "quick_scan_import_item"))
        marks = [identity_mark, subject_mark, observation_mark]
        if observation_data and observation_data["quick_scan_observation"]:
            raise QueryReadError("observation_projection_pending")
        profiles, missing = [], []
        identity = _IdentityView(identity_data) if identity_data is not None else None
        for ref in request["payload"]["subject_refs"]:
            try:
                profile = (self._profile(ref, identity, subject_data, request["payload"]["information_cutoff"])
                           if identity is not None and subject_data is not None else None)
            except (AnalysisSubjectError, QueryReadError, KeyError, TypeError, ValueError) as exc:
                raise QueryReadError("owner_subject_read_error") from exc
            if profile is None:
                missing.append(copy.deepcopy(ref))
            else:
                profiles.append(profile)
        failed = any(mark["status"] != "available" for mark in marks)
        now = self.clock()
        result = {
            "status": "unavailable" if failed else "coverage_gap", "profiles": profiles,
            "missing_subject_refs": missing, "legacy_unbound_observations": [],
            "coverage": {"status": "unknown" if failed else "not_covered",
                "requested_markets": [], "covered_markets": [],
                "requested_field_ids": list(request["payload"]["field_ids"]), "covered_field_ids": [],
                "missing_field_ids": list(request["payload"]["field_ids"]),
                "scores_available": False, "facts_available": False,
                "reason": "owner_source_unavailable" if failed else "no_bound_observation_coverage"},
            "watermark": {"store_id": self.observations.store_id, "snapshot_id": "PENDING",
                "member_sequence": 0, "observation_sequence": 0,
                "ack_sequence": observation_mark["sequence"], "read_at": now,
                "read_consistency": "sequential_owner_reads", "source_watermarks": marks},
        }
        response = self.contract.seal_response({"message_type": "response", "schema_version": "2.0.0",
            "request_id": request["request_id"], "operation": "get_profiles", "response_at": now,
            "result": result}, request=request)
        self.contract.validate_response(response, expected_request=request, expected_owner=self.owner_context)
        return response
