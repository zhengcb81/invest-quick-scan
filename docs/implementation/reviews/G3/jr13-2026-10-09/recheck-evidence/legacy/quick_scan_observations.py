"""W05 immutable observation store: transactional import, ACK and history.

Implements the C06 import decision table from
``docs/implementation/contracts/exchange-and-query.md`` inside ONE local
transaction per package item batch: unique-key dedup, content-hash compare,
insert-or-conflict decision, and ACK/sequence record. No distributed
transaction is assumed — entity existence is cross-checked through
``QuickScanStore``'s public API before the transaction (read-only), exactly
like the evidence store does.

Deliberate invariants (DB-02/DB-03, STORE-02, ID-17, ID-23):

* Own SQLite file ``scan_observations.sqlite`` — additive new namespace; the
  identity store schema (``scan.sqlite``) is never migrated or touched.
* Append-only: this module contains no row-erasure or row-rewrite SQL of any
  kind. Corrections append a new row; old observations keep their original
  payload, subject revision, model, timestamps and hashes forever (ID-17).
* Same ``package_id+item_id`` replay returns the ORIGINAL stored ACK with
  the original sequence/received_at (DB-02). Same ``observation_id`` with the
  same payload hash → ``already_present`` (never a second authoritative row,
  information time untouched). Same ``observation_id`` with a different hash
  → ``conflict``/``immutable_key_hash_conflict``. A different
  ``observation_id`` reusing an already-stored logical execution key →
  ``conflict``/``execution_key_id_mismatch``. Nothing is ever
  last-write-wins (DB-03/STORE-02).
* Every imported observation persists identity_revision, security_id,
  listing/source-binding scope, and analysis_subject_id/revision exactly as
  carried (NULL when the legacy package carries none — legacy records are
  never silently assigned a subject; ID-23).
* ``qualification_status`` is written as ``review_pending``/screening-only —
  this module contains no code path that grants accepted/formal status
  (SC-05/SC-06).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import Any

from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_store import QuickScanStore

SCHEMA_VERSION = 1
_DATABASE_NAME = "scan_observations.sqlite"
_LEDGER_STATUSES = frozenset({"accepted", "already_present", "conflict", "rejected"})


class ObservationImportError(RuntimeError):
    """A named refusal from the quick-scan observation store."""

    def __init__(self, error_code: str, detail: str = "") -> None:
        self.error_code = error_code
        self.detail = detail
        super().__init__(f"{error_code}: {detail}" if detail else error_code)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class QuickScanObservationStore:
    """Append-only observation, ACK-ledger, conflict and correction storage."""

    def __init__(self, paths: WorkspacePaths) -> None:
        self.paths = paths
        self.database_path = paths.data_dir / "quick_scan" / _DATABASE_NAME

    @property
    def store_id(self) -> str:
        digest = hashlib.sha256(str(self.database_path).encode("utf-8")).hexdigest()
        return "qsobs_" + digest[:16]

    def _connect(self) -> sqlite3.Connection:
        if not self.database_path.exists():
            self.migrate()
        con = sqlite3.connect(self.database_path, timeout=30.0)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=30000")
        return con

    def migrate(self) -> int:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.database_path, timeout=30.0)
        try:
            version = int(con.execute("PRAGMA user_version").fetchone()[0] or 0)
            if version > SCHEMA_VERSION:
                raise ObservationImportError(
                    "observation_store_newer_schema", f"{version} > {SCHEMA_VERSION}"
                )
            if version == SCHEMA_VERSION:
                return version
            con.execute("BEGIN IMMEDIATE")
            try:
                con.execute("""CREATE TABLE quick_scan_observation (
                    observation_id TEXT PRIMARY KEY,
                    entity_id TEXT NOT NULL,
                    security_id TEXT,
                    listing_id TEXT,
                    segment_id TEXT,
                    source_binding_ref TEXT,
                    identity_revision INTEGER,
                    analysis_subject_id TEXT,
                    analysis_subject_revision INTEGER,
                    primary_issuer_id TEXT,
                    field_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    information_cutoff TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    package_id TEXT NOT NULL,
                    exec_key TEXT NOT NULL UNIQUE,
                    provider TEXT,
                    model_resolved TEXT,
                    answer_status TEXT NOT NULL,
                    reported_score INTEGER,
                    qualification_status TEXT NOT NULL,
                    publication_status TEXT NOT NULL,
                    import_sequence INTEGER NOT NULL,
                    imported_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL)""")
                con.execute("""CREATE TABLE quick_scan_import_item (
                    package_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    observation_id TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN
                        ('accepted','already_present','conflict','rejected')),
                    error_code TEXT,
                    ack_sequence INTEGER NOT NULL,
                    received_at TEXT NOT NULL,
                    store_id TEXT NOT NULL,
                    ack_json TEXT NOT NULL,
                    PRIMARY KEY(package_id, item_id))""")
                con.execute("""CREATE TABLE quick_scan_import_conflict (
                    conflict_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conflict_kind TEXT NOT NULL,
                    observation_id TEXT NOT NULL,
                    exec_key TEXT,
                    package_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    incoming_payload_sha256 TEXT NOT NULL,
                    existing_payload_sha256 TEXT,
                    details TEXT NOT NULL,
                    recorded_at TEXT NOT NULL)""")
                con.execute("""CREATE TABLE quick_scan_observation_correction (
                    correction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_observation_id TEXT NOT NULL,
                    correction_sha256 TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    correction_json TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY(target_observation_id)
                        REFERENCES quick_scan_observation(observation_id))""")
                con.execute("CREATE INDEX idx_qsobs_entity ON quick_scan_observation(entity_id)")
                con.execute(
                    "CREATE INDEX idx_qsobs_subject "
                    "ON quick_scan_observation(analysis_subject_id, analysis_subject_revision)"
                )
                con.execute(
                    "CREATE INDEX idx_qsconflict_obs "
                    "ON quick_scan_import_conflict(observation_id, conflict_kind)"
                )
                con.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                con.commit()
            except Exception as exc:
                con.rollback()
                raise ObservationImportError("observation_migration_failed", str(exc)) from exc
            return SCHEMA_VERSION
        finally:
            con.close()

    @staticmethod
    def _observation_row(
        item: dict[str, Any], sequence: int
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        obs = item["observation"]
        normalized = {
            "observation_id": obs["observation_id"],
            "entity_id": obs["entity_id"],
            "security_id": obs.get("security_id"),
            "listing_id": obs.get("listing_id"),
            "segment_id": obs.get("segment_id"),
            "source_binding_ref": obs.get("source_binding_ref"),
            "identity_revision": obs.get("identity_revision"),
            "analysis_subject_id": None,
            "analysis_subject_revision": None,
            "primary_issuer_id": None,
            "field_id": obs["field_id"],
            "question_id": obs["question_id"],
            "scope": obs["scope"],
            "observed_at": obs["observed_at"],
            "information_cutoff": obs["information_cutoff"],
            "payload_sha256": item["payload_sha256"],
            "item_id": item["item_id"],
            "package_id": item["package_id"],
            "exec_key": item["exec_key"],
            "provider": (obs.get("execution") or {}).get("provider"),
            "model_resolved": (obs.get("execution") or {}).get("model_resolved"),
            "answer_status": obs["answer"]["status"],
            "reported_score": obs["answer"].get("score"),
            "qualification_status": "review_pending",
            "publication_status": (
                "published" if "module_package_id" in obs else "legacy_readonly"
            ),
            "import_sequence": sequence,
            "imported_at": _now(),
            "payload_json": json.dumps(
                obs, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        }
        subject = obs.get("analysis_subject")
        if subject:
            normalized["analysis_subject_id"] = subject.get("analysis_subject_id")
            normalized["analysis_subject_revision"] = subject.get("analysis_subject_revision")
            normalized["primary_issuer_id"] = subject.get("primary_issuer_id")
        return normalized, subject

    def apply_decisions(
        self,
        decisions: list[dict[str, Any]],
        *,
        identity_lookup: QuickScanStore | None = None,
    ) -> list[dict[str, Any]]:
        """Apply per-item decisions in one transaction and emit ACKs.

        ``decisions`` come from ``quick_scan_import`` (validated, status
        already resolved for rejected items). Items whose outcome depends on
        authoritative-store state (already_present / conflict kinds) are
        resolved here under ``BEGIN IMMEDIATE`` so ledger, observation,
        conflict and ACK rows commit atomically. Replayed
        ``(package_id, item_id)`` pairs return the originally stored ACK.
        """
        for decision in decisions:
            if decision.get("status") not in _LEDGER_STATUSES:
                raise ObservationImportError("unknown_decision_status", str(decision.get("status")))
        if identity_lookup is not None:
            for decision in decisions:
                if decision["status"] == "rejected":
                    continue
                entity_id = decision["observation"]["entity_id"]
                if identity_lookup.get_entity(entity_id) is None:
                    raise ObservationImportError(
                        "entity_not_found", f"cannot import for missing entity {entity_id}"
                    )
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            acks: list[dict[str, Any]] = []
            for decision in decisions:
                acks.append(self._apply_one(con, decision))
            con.commit()
            return acks
        except ObservationImportError:
            con.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            con.rollback()
            raise ObservationImportError("observation_integrity_error", str(exc)) from exc
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _next_sequence(self, con: sqlite3.Connection) -> int:
        row = con.execute(
            "SELECT COALESCE(MAX(ack_sequence), 0) + 1 AS next FROM quick_scan_import_item"
        ).fetchone()
        return int(row["next"])

    def _apply_one(self, con: sqlite3.Connection, decision: dict[str, Any]) -> dict[str, Any]:
        package_id = decision["package_id"]
        item_id = decision["item_id"]
        original = con.execute(
            "SELECT ack_json FROM quick_scan_import_item WHERE package_id=? AND item_id=?",
            (package_id, item_id),
        ).fetchone()
        if original is not None:
            return json.loads(original["ack_json"])

        sequence = self._next_sequence(con)
        received_at = _now()
        status = decision["status"]
        error_code = decision.get("error_code")
        observation_id = decision["observation_id"]
        payload_sha256 = decision["payload_sha256"]

        if status == "accepted":
            existing = con.execute(
                "SELECT payload_sha256 FROM quick_scan_observation WHERE observation_id=?",
                (observation_id,),
            ).fetchone()
            if existing is not None:
                if existing["payload_sha256"] == payload_sha256:
                    status = "already_present"
                else:
                    status = "conflict"
                    error_code = "immutable_key_hash_conflict"
            else:
                exec_collision = con.execute(
                    "SELECT observation_id, payload_sha256 FROM quick_scan_observation "
                    "WHERE exec_key=?",
                    (decision["exec_key"],),
                ).fetchone()
                if exec_collision is not None:
                    status = "conflict"
                    error_code = "execution_key_id_mismatch"
                    self._record_conflict(
                        con,
                        decision,
                        conflict_kind="execution_key_id_mismatch",
                        existing_payload=exec_collision["payload_sha256"],
                        details={"existing_observation_id": exec_collision["observation_id"]},
                        recorded_at=received_at,
                    )

        if status == "accepted":
            row, _subject = self._observation_row(decision, sequence)
            columns = ",".join(row)
            placeholders = ",".join(":" + key for key in row)
            con.execute(
                f"INSERT INTO quick_scan_observation ({columns}) VALUES ({placeholders})",
                row,
            )
        elif status == "conflict" and error_code == "immutable_key_hash_conflict":
            existing = con.execute(
                "SELECT payload_sha256 FROM quick_scan_observation WHERE observation_id=?",
                (observation_id,),
            ).fetchone()
            self._record_conflict(
                con,
                decision,
                conflict_kind="immutable_key_hash_conflict",
                existing_payload=existing["payload_sha256"] if existing else None,
                details={},
                recorded_at=received_at,
            )

        original_reference = None
        if status == "already_present":
            first = con.execute(
                "SELECT package_id, ack_sequence, received_at FROM quick_scan_import_item "
                "WHERE observation_id=? ORDER BY ack_sequence LIMIT 1",
                (observation_id,),
            ).fetchone()
            if first is not None:
                original_reference = {
                    "package_id": first["package_id"],
                    "ack_sequence": int(first["ack_sequence"]),
                    "received_at": first["received_at"],
                }

        ack = {
            "schema_version": "1.0.0",
            "ack_id": "ack_"
            + hashlib.sha256(f"{package_id}|{item_id}|{sequence}".encode("utf-8")).hexdigest()[:24],
            "package_id": package_id,
            "item_id": item_id,
            "observation_id": observation_id,
            "payload_sha256": payload_sha256,
            "status": status,
            "error_code": error_code,
            "received_at": received_at,
            "consumer": {
                "component": "StockWiki",
                "namespace": "quick_scan",
                "store_id": self.store_id,
            },
            "ack_sequence": sequence,
        }
        if original_reference is not None:
            ack["original_import"] = original_reference
        con.execute(
            """INSERT INTO quick_scan_import_item
            (package_id,item_id,observation_id,payload_sha256,status,error_code,
             ack_sequence,received_at,store_id,ack_json)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                package_id,
                item_id,
                observation_id,
                payload_sha256,
                status,
                error_code,
                sequence,
                received_at,
                self.store_id,
                json.dumps(ack, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            ),
        )
        return ack

    @staticmethod
    def _record_conflict(
        con: sqlite3.Connection,
        decision: dict[str, Any],
        *,
        conflict_kind: str,
        existing_payload: str | None,
        details: dict[str, Any],
        recorded_at: str,
    ) -> None:
        con.execute(
            """INSERT INTO quick_scan_import_conflict
            (conflict_kind,observation_id,exec_key,package_id,item_id,
             incoming_payload_sha256,existing_payload_sha256,details,recorded_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                conflict_kind,
                decision["observation_id"],
                decision.get("exec_key"),
                decision["package_id"],
                decision["item_id"],
                decision["payload_sha256"],
                existing_payload,
                json.dumps(details, ensure_ascii=False, sort_keys=True),
                recorded_at,
            ),
        )

    def append_correction(
        self,
        target_observation_id: str,
        *,
        corrected_observation: dict[str, Any],
        reason: str,
    ) -> int:
        """Append a correction row; the target observation is never modified."""
        if not reason or not str(reason).strip():
            raise ObservationImportError("correction_reason_required", target_observation_id)
        correction_json = json.dumps(
            corrected_observation, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        correction_sha = hashlib.sha256(correction_json.encode("utf-8")).hexdigest()
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            target = con.execute(
                "SELECT observation_id FROM quick_scan_observation WHERE observation_id=?",
                (target_observation_id,),
            ).fetchone()
            if target is None:
                raise ObservationImportError("correction_target_missing", target_observation_id)
            cursor = con.execute(
                """INSERT INTO quick_scan_observation_correction
                (target_observation_id,correction_sha256,reason,correction_json,recorded_at)
                VALUES (?,?,?,?,?)""",
                (
                    target_observation_id,
                    correction_sha,
                    str(reason).strip(),
                    correction_json,
                    _now(),
                ),
            )
            last_id = cursor.lastrowid
            if last_id is None:
                con.rollback()
                raise ObservationImportError("correction_insert_failed", target_observation_id)
            con.commit()
            return int(last_id)
        except ObservationImportError:
            con.rollback()
            raise
        finally:
            con.close()

    def get_observation(self, observation_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as con:
            row = con.execute(
                "SELECT * FROM quick_scan_observation WHERE observation_id=?",
                (observation_id,),
            ).fetchone()
            return self._decode_observation(row) if row is not None else None

    @staticmethod
    def _decode_observation(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        return result

    def observations_for_entity(self, entity_id: str) -> list[dict[str, Any]]:
        """Historical view for one entity: originals preserved verbatim (ID-17)."""
        with closing(self._connect()) as con:
            rows = con.execute(
                "SELECT * FROM quick_scan_observation WHERE entity_id=? "
                "ORDER BY import_sequence, observation_id",
                (entity_id,),
            )
            return [self._decode_observation(r) for r in rows]

    def ack_for(self, package_id: str, item_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as con:
            row = con.execute(
                "SELECT ack_json FROM quick_scan_import_item WHERE package_id=? AND item_id=?",
                (package_id, item_id),
            ).fetchone()
            return json.loads(row["ack_json"]) if row is not None else None

    def list_conflicts(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as con:
            rows = con.execute("SELECT * FROM quick_scan_import_conflict ORDER BY conflict_id")
            return [dict(r) for r in rows]

    def list_corrections(self, target_observation_id: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as con:
            rows = con.execute(
                "SELECT * FROM quick_scan_observation_correction "
                "WHERE target_observation_id=? ORDER BY correction_id",
                (target_observation_id,),
            )
            result = []
            for row in rows:
                item = dict(row)
                item["correction"] = json.loads(item.pop("correction_json"))
                result.append(item)
            return result

    def counts(self) -> dict[str, int]:
        with closing(self._connect()) as con:
            return {
                "observations": int(
                    con.execute("SELECT COUNT(*) FROM quick_scan_observation").fetchone()[0]
                ),
                "acked_items": int(
                    con.execute("SELECT COUNT(*) FROM quick_scan_import_item").fetchone()[0]
                ),
                "conflicts": int(
                    con.execute("SELECT COUNT(*) FROM quick_scan_import_conflict").fetchone()[0]
                ),
                "corrections": int(
                    con.execute(
                        "SELECT COUNT(*) FROM quick_scan_observation_correction"
                    ).fetchone()[0]
                ),
            }
