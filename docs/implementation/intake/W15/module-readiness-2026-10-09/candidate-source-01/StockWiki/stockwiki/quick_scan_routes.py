"""W15 route history and independent current anchors in the identity store.

One decision is bound to one attested subject revision. Raw bytes are never
rewritten. Classification confidence is retained as routing evidence only.
No default validator, automatic migration, network, fee or model dispatch.
"""

from __future__ import annotations

import hashlib
from contextlib import closing
from typing import Any

from stockwiki.quick_scan_analysis import (
    AnalysisSubjectStore,
    perimeter_sha256,
    receipt_key,
    validate_receipt,
    validate_subject,
)
from stockwiki.quick_scan_freshness import parse_utc
from stockwiki.quick_scan_import import canonical_bytes
from stockwiki.quick_scan_route_validation import (
    PROTOCOL,
    RouteStoreError,
    RouteValidator,
    read_json,
)
from stockwiki.quick_scan_store import SCHEMA_VERSION, QuickScanStore

BINDING_VERSION = "stockwiki.route_subject/1.0.0"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class QuickScanRouteStore:
    def __init__(self, identity_store: QuickScanStore, *, validator: RouteValidator) -> None:
        self.identity = identity_store
        self.subjects = AnalysisSubjectStore(identity_store.paths)
        self.validator = validator

    def _connect(self):
        con = self.identity._connect()
        if con.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            con.close()
            raise RouteStoreError("route_store_schema_unavailable")
        return con

    def identity_binding(self, subject_key: str) -> dict[str, Any]:
        """Owner-side route input, obtained BEFORE asking IQS to compose it.

        This is an additive route binding, not a replacement Identity DTO or
        a claim that hashing alone authenticates an issuer/perimeter.
        """
        subject = self.subjects.get_subject(subject_key)
        receipt = self.subjects.get_perimeter_receipt(subject_key)
        if subject is None or receipt is None or receipt_key(subject) != subject_key:
            raise RouteStoreError("route_subject_unavailable")
        validate_subject(subject, identity_store=self.identity)
        validate_receipt(receipt, subject)
        entity = self.identity.get_entity(subject["primary_issuer_id"])
        if entity is None or entity["identity_state"] != "verified":
            raise RouteStoreError("route_identity_unverified")
        result = {
            "binding_version": BINDING_VERSION,
            "subject_key": subject_key,
            "analysis_subject_id": subject["analysis_subject_id"],
            "analysis_subject_revision": subject["analysis_subject_revision"],
            "entity_id": subject["primary_issuer_id"],
            "identity_revision": entity["identity_revision"],
            "perimeter_sha256": perimeter_sha256(subject),
            "entity_sha256": _sha(canonical_bytes(entity)),
            "subject": subject,
            "perimeter_receipt": receipt,
        }
        result["route_identity_ref"] = BINDING_VERSION + ":" + _sha(canonical_bytes(result))
        return result

    @staticmethod
    def _scope(route: dict[str, Any]) -> tuple[str, str]:
        if route.get("scope") == "entity" and route.get("segment_id") is None:
            return "entity", route["entity_id"]
        if (
            route.get("scope") == "segment"
            and isinstance(route.get("segment_id"), str)
            and route["segment_id"]
        ):
            return "segment", route["segment_id"]
        raise RouteStoreError("route_scope_invalid")

    def _validate(
        self,
        route_raw: bytes,
        manifest_raw: bytes,
        expected: str,
        *,
        mode: str = "history",
        now: str | None = None,
    ) -> dict[str, Any]:
        dto = self.validator.validate(
            route_raw,
            manifest_raw,
            expected_decision_id=expected,
            validation_mode=mode,
            now_utc=now,
        )
        if (
            dto.get("protocol") != PROTOCOL
            or dto.get("status") != "validated"
            or dto.get("expected_decision_id") != expected
            or dto.get("validation_mode") != mode
            or dto.get("route_raw_sha256") != _sha(route_raw)
            or dto.get("manifest_raw_sha256") != _sha(manifest_raw)
        ):
            raise RouteStoreError("route_validator_binding_mismatch")
        return dto

    def record_snapshot(
        self, route_raw: bytes, manifest_raw: bytes, *, subject_key: str, expected_decision_id: str
    ) -> dict[str, Any]:
        route, manifest = read_json(route_raw), read_json(manifest_raw)
        validation = self._validate(route_raw, manifest_raw, expected_decision_id)
        binding = self.identity_binding(subject_key)
        scope, scope_id = self._scope(route)
        if (
            route.get("decision_id") != expected_decision_id
            or route.get("entity_id") != binding["entity_id"]
            or route.get("identity_ref") != binding["route_identity_ref"]
            or manifest.get("route_decision") != route
            or manifest.get("route_decision_id") != expected_decision_id
        ):
            raise RouteStoreError("route_subject_binding_mismatch")
        if scope == "segment" and not any(
            row["segment_id"] == scope_id
            for row in self.identity.get_entity(binding["entity_id"])["segments"]
        ):
            raise RouteStoreError("route_segment_unavailable")
        metadata = {"binding": binding, "validation": validation}
        meta_raw = canonical_bytes(metadata)
        row = dict(
            decision_id=expected_decision_id,
            subject_key=subject_key,
            entity_id=binding["entity_id"],
            identity_revision=binding["identity_revision"],
            perimeter_sha256=binding["perimeter_sha256"],
            scope=scope,
            scope_id=scope_id,
            route_raw=route_raw,
            manifest_raw=manifest_raw,
            route_raw_sha256=_sha(route_raw),
            manifest_raw_sha256=_sha(manifest_raw),
            metadata_json=meta_raw.decode("utf-8"),
            metadata_sha256=_sha(meta_raw),
        )
        with closing(self._connect()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                if self.identity_binding(subject_key) != binding:
                    raise RouteStoreError("route_identity_changed")
                old = con.execute(
                    "SELECT * FROM quick_scan_route_snapshot WHERE decision_id=?",
                    (expected_decision_id,),
                ).fetchone()
                if old is not None:
                    if dict(old) != row:
                        raise RouteStoreError("route_snapshot_conflict")
                    con.rollback()
                    return {"status": "replayed", "decision_id": expected_decision_id}
                keys = list(row)
                con.execute(
                    f"INSERT INTO quick_scan_route_snapshot ({','.join(keys)}) VALUES "
                    f"({','.join(':' + key for key in keys)})",
                    row,
                )
                con.commit()
            except Exception:
                con.rollback()
                raise
        return {"status": "recorded", "decision_id": expected_decision_id}

    @staticmethod
    def _read_row(row: Any) -> dict[str, Any] | None:
        if row is None:
            return None
        result = dict(row)
        try:
            metadata_raw = result["metadata_json"].encode("utf-8")
            metadata = read_json(metadata_raw)
            route = read_json(result["route_raw"])
            binding = metadata["binding"]
            if (
                _sha(result["route_raw"]) != result["route_raw_sha256"]
                or _sha(result["manifest_raw"]) != result["manifest_raw_sha256"]
                or _sha(metadata_raw) != result["metadata_sha256"]
                or route["decision_id"] != result["decision_id"]
                or route["identity_ref"] != binding["route_identity_ref"]
                or binding["subject_key"] != result["subject_key"]
                or binding["entity_id"] != result["entity_id"]
                or binding["identity_revision"] != result["identity_revision"]
                or binding["perimeter_sha256"] != result["perimeter_sha256"]
                or QuickScanRouteStore._scope(route) != (result["scope"], result["scope_id"])
            ):
                raise ValueError("binding or bytes changed")
        except (KeyError, ValueError, TypeError) as exc:
            raise RouteStoreError("route_snapshot_corrupted") from exc
        result["metadata"] = metadata
        return result

    def get_snapshot(self, decision_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as con:
            con.execute("PRAGMA query_only=ON")
            row = con.execute(
                "SELECT * FROM quick_scan_route_snapshot WHERE decision_id=?", (decision_id,)
            ).fetchone()
        return self._read_row(row)

    def snapshots_for_subject(self, subject_key: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as con:
            con.execute("PRAGMA query_only=ON")
            rows = con.execute(
                "SELECT * FROM quick_scan_route_snapshot WHERE subject_key=? ORDER BY decision_id",
                (subject_key,),
            ).fetchall()
        return [self._read_row(row) for row in rows]

    def current_history(
        self, *, subject_key: str, scope: str, scope_id: str
    ) -> list[dict[str, Any]]:
        with closing(self._connect()) as con:
            con.execute("PRAGMA query_only=ON")
            rows = con.execute(
                "SELECT * FROM quick_scan_route_current_history WHERE subject_key=? AND scope=? AND scope_id=? ORDER BY version",
                (subject_key, scope, scope_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def _execution(
        self, snapshot: dict[str, Any], now: str, candidate: bytes | None = None
    ) -> dict[str, Any]:
        parse_utc(now)
        if self.identity_binding(snapshot["subject_key"]) != snapshot["metadata"]["binding"]:
            raise RouteStoreError("route_identity_changed")
        raw = snapshot["route_raw"] if candidate is None else candidate
        if read_json(raw).get("decision_id") != snapshot["decision_id"]:
            raise RouteStoreError("route_anchor_mismatch")
        dto = self._validate(
            raw, snapshot["manifest_raw"], snapshot["decision_id"], mode="execution", now=now
        )
        if raw != snapshot["route_raw"]:
            raise RouteStoreError("route_snapshot_bytes_mismatch")
        return dto

    def set_current(
        self,
        decision_id: str,
        *,
        subject_key: str,
        expected_current_decision_id: str | None,
        now_utc: str,
    ) -> dict[str, Any]:
        snapshot = self.get_snapshot(decision_id)
        if snapshot is None or snapshot["subject_key"] != subject_key:
            raise RouteStoreError("route_snapshot_unavailable")
        self._execution(snapshot, now_utc)
        key = (subject_key, snapshot["scope"], snapshot["scope_id"])
        with closing(self._connect()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                if (
                    self._read_row(
                        con.execute(
                            "SELECT * FROM quick_scan_route_snapshot WHERE decision_id=?",
                            (decision_id,),
                        ).fetchone()
                    )
                    != snapshot
                ):
                    raise RouteStoreError("route_snapshot_corrupted")
                if self.identity_binding(subject_key) != snapshot["metadata"]["binding"]:
                    raise RouteStoreError("route_identity_changed")
                old = con.execute(
                    "SELECT * FROM quick_scan_route_current WHERE subject_key=? AND scope=? AND scope_id=?",
                    key,
                ).fetchone()
                current_id = old["decision_id"] if old else None
                if current_id != expected_current_decision_id:
                    raise RouteStoreError("route_current_conflict")
                if old is not None and parse_utc(now_utc) < parse_utc(old["activated_at"]):
                    raise RouteStoreError("route_time_before_activation")
                if current_id == decision_id:
                    con.rollback()
                    return {
                        "status": "unchanged",
                        "decision_id": decision_id,
                        "version": old["version"],
                    }
                version = old["version"] + 1 if old else 1
                con.execute(
                    "INSERT INTO quick_scan_route_current VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(subject_key,scope,scope_id) DO UPDATE SET decision_id=excluded.decision_id, "
                    "version=excluded.version, activated_at=excluded.activated_at",
                    (*key, decision_id, version, now_utc),
                )
                con.execute(
                    "INSERT INTO quick_scan_route_current_history VALUES (?,?,?,?,?,?,?)",
                    (*key, version, decision_id, current_id, now_utc),
                )
                con.commit()
            except Exception:
                con.rollback()
                raise
        return {"status": "activated", "decision_id": decision_id, "version": version}

    def get_current_anchor(
        self, *, subject_key: str, scope: str, scope_id: str, now_utc: str
    ) -> dict[str, Any]:
        """Check immutable bytes/current identity after prior full validation.

        This read gives NO new execution permission. A caller must separately
        perform get_for_execution on run admission; it only detects owner drift.
        """
        with closing(self._connect()) as con:
            con.execute("PRAGMA query_only=ON")
            con.execute("BEGIN")
            anchor = con.execute(
                "SELECT * FROM quick_scan_route_current WHERE subject_key=? AND scope=? AND scope_id=?",
                (subject_key, scope, scope_id),
            ).fetchone()
            if anchor is None:
                raise RouteStoreError("route_current_unavailable")
            snapshot = self._read_row(
                con.execute(
                    "SELECT * FROM quick_scan_route_snapshot WHERE decision_id=?",
                    (anchor["decision_id"],),
                ).fetchone()
            )
        if snapshot is None or (
            snapshot["subject_key"],
            snapshot["scope"],
            snapshot["scope_id"],
        ) != (subject_key, scope, scope_id):
            raise RouteStoreError("route_current_corrupted")
        if parse_utc(now_utc) < parse_utc(anchor["activated_at"]):
            raise RouteStoreError("route_time_before_activation")
        if self.identity_binding(subject_key) != snapshot["metadata"]["binding"]:
            raise RouteStoreError("route_identity_changed")
        return {
            "expected_decision_id": anchor["decision_id"],
            "anchor_version": anchor["version"],
            "snapshot": snapshot,
            "new_execution_authorized": False,
        }

    def get_for_execution(
        self,
        *,
        subject_key: str,
        scope: str,
        scope_id: str,
        now_utc: str,
        candidate_route: bytes | None = None,
    ) -> dict[str, Any]:
        current = self.get_current_anchor(
            subject_key=subject_key, scope=scope, scope_id=scope_id, now_utc=now_utc
        )
        snapshot = current["snapshot"]
        validation = self._execution(snapshot, now_utc, candidate_route)
        return {
            "expected_decision_id": current["expected_decision_id"],
            "anchor_version": current["anchor_version"],
            "snapshot": snapshot,
            "execution_validation": validation,
        }
