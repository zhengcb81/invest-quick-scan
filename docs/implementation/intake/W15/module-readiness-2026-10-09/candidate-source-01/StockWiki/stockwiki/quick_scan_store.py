"""SQLite storage isolated from formal StockWiki profiles and company-wiki."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from typing import Any

import stockwiki.quick_scan_schema as quick_scan_schema
from stockwiki.paths import WorkspacePaths

SCHEMA_VERSION = 6


class QuickScanStoreError(RuntimeError):
    """Quick-scan persistence or integrity error."""


class QuickScanStore:
    """Identity, security and universe-membership storage for quick scans."""

    def __init__(self, paths: WorkspacePaths) -> None:
        self.paths = paths
        self.database_path = paths.data_dir / "quick_scan" / "scan.sqlite"

    def _connect(self) -> sqlite3.Connection:
        if not self.database_path.exists():
            raise QuickScanStoreError("quick-scan store has not been migrated")
        con = sqlite3.connect(self.database_path, timeout=30.0)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=30000")
        return con

    def migrate(self) -> int:
        """Apply pending schema steps atomically and reject unsupported newer schemas."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.database_path, timeout=30.0)
        try:
            con.execute("PRAGMA foreign_keys=ON")
            con.execute("BEGIN IMMEDIATE")
            version = int(con.execute("PRAGMA user_version").fetchone()[0])
            if version > SCHEMA_VERSION:
                raise QuickScanStoreError(
                    f"database schema {version} is newer than supported {SCHEMA_VERSION}"
                )
            if version == SCHEMA_VERSION:
                con.rollback()
                return version
            try:
                if version < 1:
                    quick_scan_schema.apply_v1(con)
                if version < 2:
                    quick_scan_schema.apply_v2(con)
                if version < 3:
                    quick_scan_schema.apply_v3(con)
                if version < 4:
                    quick_scan_schema.apply_v4(con)
                if version < 5:
                    quick_scan_schema.apply_v5(con)
                if version < 6:
                    quick_scan_schema.apply_v6(con)
                con.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                con.commit()
            except Exception as exc:
                con.rollback()
                raise QuickScanStoreError(f"quick-scan migration failed: {exc}") from exc
            return SCHEMA_VERSION
        finally:
            con.close()

    @staticmethod
    def _prepare(entity: dict[str, Any], source_bindings: list[dict[str, Any]]):
        required = (
            "entity_id",
            "identity_schema_version",
            "identity_state",
            "identity_revision",
            "canonical_name",
            "scope_attestation_id",
        )
        if any(not entity.get(k) for k in required):
            raise QuickScanStoreError("entity is missing a required identity field")
        if entity["identity_state"] not in {"provisional", "verified"}:
            raise QuickScanStoreError("identity_state must be provisional or verified")
        if entity["identity_state"] == "verified" and not entity.get("verified_issuer_receipt_id"):
            raise QuickScanStoreError("verified identity requires an issuer receipt")
        bindings = {row.get("binding_ref"): row for row in source_bindings}
        securities = []
        for row in entity.get("securities", []):
            if row.get("entity_id") != entity["entity_id"]:
                raise QuickScanStoreError("security entity_id does not match its entity")
            binding = bindings.get(row.get("source_binding_ref"))
            if binding is None:
                raise QuickScanStoreError("security has no explicit source binding")
            for key in ("security_id", "entity_id", "market", "exchange_raw", "ticker"):
                if row.get(key) != binding.get(key):
                    raise QuickScanStoreError(f"source binding disagrees on {key}")
            securities.append(
                {
                    k: row.get(k)
                    for k in (
                        "security_id",
                        "entity_id",
                        "market",
                        "exchange_raw",
                        "exchange",
                        "ticker",
                        "currency",
                        "security_type",
                        "listing_status",
                        "source_binding_ref",
                        "adr_ratio",
                        "ordinary_security_ref",
                    )
                }
            )
        security_ids = {r["security_id"] for r in securities}
        if len(security_ids) != len(securities):
            raise QuickScanStoreError("duplicate security_id in entity")
        binding_rows = []
        for row in source_bindings:
            if (
                row.get("entity_id") != entity["entity_id"]
                or row.get("security_id") not in security_ids
            ):
                raise QuickScanStoreError("source binding refers to a different or absent security")
            binding_rows.append(
                {
                    k: row[k]
                    for k in (
                        "binding_ref",
                        "source_namespace",
                        "source_record_id",
                        "source_canonical_name",
                        "security_id",
                        "entity_id",
                        "market",
                        "exchange_raw",
                        "ticker",
                        "status",
                    )
                }
            )
        if len({r["binding_ref"] for r in binding_rows}) != len(binding_rows):
            raise QuickScanStoreError("duplicate source binding reference")
        segments = [
            {
                "entity_id": entity["entity_id"],
                "segment_id": r["segment_id"],
                "segment_name": r["segment_name"],
                "revenue_share_pct": r.get("revenue_share_pct"),
                "description": r.get("description"),
            }
            for r in entity.get("segments", [])
        ]
        ent = {
            k: entity.get(k)
            for k in (
                "entity_id",
                "identity_schema_version",
                "identity_state",
                "identity_revision",
                "canonical_name",
                "incorporation_country",
                "scope_attestation_id",
                "verified_issuer_receipt_id",
                "company_wiki_ref",
                "formal_stockwiki_profile",
            )
        }
        return ent, securities, binding_rows, segments

    @staticmethod
    def _identity_fingerprint(
        ent: dict[str, Any],
        securities: list[dict[str, Any]],
        segments: list[dict[str, Any]],
    ) -> str:
        payload = {
            "identity_schema_version": ent["identity_schema_version"],
            "identity_state": ent["identity_state"],
            "canonical_name": ent["canonical_name"],
            "incorporation_country": ent["incorporation_country"],
            "scope_attestation_id": ent["scope_attestation_id"],
            "verified_issuer_receipt_id": ent["verified_issuer_receipt_id"],
            "company_wiki_ref": ent["company_wiki_ref"],
            "formal_stockwiki_profile": ent["formal_stockwiki_profile"],
            "securities": securities,
            "segments": segments,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)

    @staticmethod
    def _load_identity_fingerprint(con: sqlite3.Connection, entity_id: str) -> str:
        row = con.execute(
            "SELECT * FROM quick_scan_entity WHERE entity_id=?", (entity_id,)
        ).fetchone()
        stored_ent = {
            "identity_schema_version": row["identity_schema_version"],
            "identity_state": row["identity_state"],
            "canonical_name": row["canonical_name"],
            "incorporation_country": row["incorporation_country"],
            "scope_attestation_id": row["scope_attestation_id"],
            "verified_issuer_receipt_id": row["verified_issuer_receipt_id"],
            "company_wiki_ref": row["company_wiki_ref"],
            "formal_stockwiki_profile": row["formal_stockwiki_profile"],
        }
        stored_securities = [
            dict(r)
            for r in con.execute(
                "SELECT * FROM quick_scan_security WHERE entity_id=? ORDER BY security_id",
                (entity_id,),
            )
        ]
        stored_segments = [
            dict(r)
            for r in con.execute(
                "SELECT entity_id,segment_id,segment_name,revenue_share_pct,description "
                "FROM quick_scan_segment WHERE entity_id=? ORDER BY segment_id",
                (entity_id,),
            )
        ]
        return QuickScanStore._identity_fingerprint(stored_ent, stored_securities, stored_segments)

    def save_entity(self, entity: dict[str, Any], *, source_bindings: list[dict[str, Any]]) -> None:
        ent, securities, bindings, segments = self._prepare(entity, source_bindings)
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            self._save_prepared(con, ent, securities, bindings, segments)

            con.commit()
        except QuickScanStoreError:
            con.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            con.rollback()
            kind = "source binding" if "source_binding" in str(exc).lower() else "identity"
            raise QuickScanStoreError(f"{kind} integrity error: {exc}") from exc
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _save_prepared(
        self,
        con: sqlite3.Connection,
        ent: dict[str, Any],
        securities: list[dict[str, Any]],
        bindings: list[dict[str, Any]],
        segments: list[dict[str, Any]],
    ) -> None:
        """Core entity/security/binding/segment write (caller owns the transaction)."""
        for b in bindings:
            old = con.execute(
                "SELECT * FROM quick_scan_source_binding WHERE binding_ref=?",
                (b["binding_ref"],),
            ).fetchone()
            if old is not None and any(
                old[k] != b[k]
                for k in (
                    "entity_id",
                    "security_id",
                    "source_namespace",
                    "source_record_id",
                    "market",
                    "exchange_raw",
                    "ticker",
                )
            ):
                raise QuickScanStoreError(f"source binding conflict for {b['binding_ref']}")
        old = con.execute(
            "SELECT identity_revision FROM quick_scan_entity WHERE entity_id=?",
            (ent["entity_id"],),
        ).fetchone()
        if old is not None:
            old_revision = int(old["identity_revision"] or 0)
            new_revision = int(ent["identity_revision"] or 0)
            if new_revision < old_revision:
                raise QuickScanStoreError("identity revision cannot move backwards")
            if new_revision == old_revision:
                stored = self._load_identity_fingerprint(con, str(ent["entity_id"]))
                incoming = self._identity_fingerprint(
                    ent,
                    sorted(securities, key=lambda r: r["security_id"]),
                    sorted(segments, key=lambda r: r["segment_id"]),
                )
                if stored != incoming:
                    raise QuickScanStoreError(
                        f"same identity revision {old_revision} replay with different content; "
                        "bump the revision to change identity facts"
                    )
                con.commit()
                return
            if new_revision != old_revision + 1:
                raise QuickScanStoreError(
                    f"next identity revision must be {old_revision + 1}, got {new_revision}"
                )
            if new_revision != old_revision + 1:
                raise QuickScanStoreError(
                    f"next identity revision must be {old_revision + 1}, got {new_revision}"
                )
            if ent["identity_revision"] != old_revision + 1:
                raise QuickScanStoreError(
                    f"next identity revision must be {old_revision + 1}, got {ent['identity_revision']}"
                )
        con.execute(
            """INSERT INTO quick_scan_entity VALUES
            (:entity_id,:identity_schema_version,:identity_state,:identity_revision,
             :canonical_name,:incorporation_country,:scope_attestation_id,
             :verified_issuer_receipt_id,:company_wiki_ref,:formal_stockwiki_profile)
            ON CONFLICT(entity_id) DO UPDATE SET
            identity_schema_version=excluded.identity_schema_version,
            identity_state=excluded.identity_state,identity_revision=excluded.identity_revision,
            canonical_name=excluded.canonical_name,incorporation_country=excluded.incorporation_country,
            scope_attestation_id=excluded.scope_attestation_id,
            verified_issuer_receipt_id=excluded.verified_issuer_receipt_id,
            company_wiki_ref=excluded.company_wiki_ref,
            formal_stockwiki_profile=excluded.formal_stockwiki_profile""",
            ent,
        )
        for r in securities:
            con.execute(
                """INSERT INTO quick_scan_security VALUES
                (:security_id,:entity_id,:market,:exchange_raw,:exchange,:ticker,:currency,
                 :security_type,:listing_status,:source_binding_ref,:adr_ratio,:ordinary_security_ref)
                ON CONFLICT(security_id) DO UPDATE SET entity_id=excluded.entity_id,
                market=excluded.market,exchange_raw=excluded.exchange_raw,exchange=excluded.exchange,
                ticker=excluded.ticker,currency=excluded.currency,security_type=excluded.security_type,
                listing_status=excluded.listing_status,source_binding_ref=excluded.source_binding_ref,
                adr_ratio=excluded.adr_ratio,ordinary_security_ref=excluded.ordinary_security_ref""",
                r,
            )
        for r in bindings:
            con.execute(
                """INSERT INTO quick_scan_source_binding VALUES
                (:binding_ref,:source_namespace,:source_record_id,:source_canonical_name,
                 :security_id,:entity_id,:market,:exchange_raw,:ticker,:status)
                ON CONFLICT(binding_ref) DO UPDATE SET
                source_canonical_name=excluded.source_canonical_name,status=excluded.status""",
                r,
            )
        con.execute("DELETE FROM quick_scan_segment WHERE entity_id=?", (ent["entity_id"],))
        con.executemany(
            """INSERT INTO quick_scan_segment
            VALUES (:entity_id,:segment_id,:segment_name,:revenue_share_pct,:description)""",
            segments,
        )

    def add_security(
        self,
        entity_id: str,
        *,
        security: dict[str, Any],
        binding: dict[str, Any],
        expected_identity_revision: int | None = None,
    ) -> int:
        """Append a source-bound listing to an entity without duplicating it (UNI-03).

        Re-adding an identical security row is an idempotent no-op at the same
        identity revision. A genuinely new listing advances identity_revision
        by one because the identity fingerprint includes securities. Send the
        full security row exactly as stored when re-adding.
        ``expected_identity_revision`` is an optional optimistic-concurrency guard.
        """
        with closing(self._connect()) as con:
            row = con.execute(
                "SELECT * FROM quick_scan_entity WHERE entity_id=?", (entity_id,)
            ).fetchone()
            if row is None:
                raise QuickScanStoreError("cannot add a listing to a missing entity")
            current = int(row["identity_revision"])
            if expected_identity_revision is not None and expected_identity_revision != current:
                raise QuickScanStoreError(
                    f"identity revision conflict (current {current}, "
                    f"expected {expected_identity_revision})"
                )
            ent = dict(row)
            ent["securities"] = self.securities_for_entity(entity_id, connection=con)
            ent["segments"] = [
                dict(r)
                for r in con.execute(
                    "SELECT segment_id,segment_name,revenue_share_pct,description "
                    "FROM quick_scan_segment WHERE entity_id=? ORDER BY segment_id",
                    (entity_id,),
                )
            ]
            all_bindings = [
                dict(r)
                for r in con.execute(
                    "SELECT * FROM quick_scan_source_binding WHERE entity_id=?",
                    (entity_id,),
                )
            ]
        new_security = dict(security)
        new_security["entity_id"] = entity_id
        new_binding = dict(binding)
        new_binding["entity_id"] = entity_id
        new_binding["security_id"] = new_security["security_id"]
        existing = [s for s in ent["securities"] if s["security_id"] == new_security["security_id"]]
        if existing:
            old_security = existing[0]
            if any(old_security.get(k) != new_security.get(k) for k in new_security):
                raise QuickScanStoreError(
                    "security_id already exists with different content; "
                    "use a documented identity change instead"
                )
            return current  # idempotent duplicate re-add (UNI-03)
        ent["identity_revision"] = current + 1
        ent["securities"] = ent["securities"] + [new_security]
        all_bindings = [
            b for b in all_bindings if b["binding_ref"] != new_binding["binding_ref"]
        ] + [new_binding]
        prepared = self._prepare(ent, all_bindings)
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            live = con.execute(
                "SELECT identity_revision FROM quick_scan_entity WHERE entity_id=?",
                (entity_id,),
            ).fetchone()
            if int(live["identity_revision"]) != current:
                raise QuickScanStoreError("identity revision conflict during add_security")
            self._save_prepared(con, *prepared)
            con.commit()
            return current + 1
        except QuickScanStoreError:
            con.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            con.rollback()
            raise QuickScanStoreError(f"identity integrity error: {exc}") from exc
        finally:
            con.close()

    def record_listing_status(
        self,
        security_id: str,
        *,
        listing_status: str,
        reason: str,
        effective_at: str,
        recorded_at: str,
    ) -> None:
        """Transition one listing's status with append-only history (ID-06).

        Status history rows are never rewritten; an identical re-record is a
        no-op. Only the target security row changes — sibling listings,
        entities and memberships are untouched.
        """
        if listing_status not in {"active", "delisted"}:
            raise QuickScanStoreError("listing_status must be active or delisted")
        if not isinstance(reason, str) or not reason.strip():
            raise QuickScanStoreError("a non-empty reason is required")
        if not effective_at or not recorded_at:
            raise QuickScanStoreError("effective_at and recorded_at are required")
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT listing_status FROM quick_scan_security WHERE security_id=?",
                (security_id,),
            ).fetchone()
            if row is None:
                raise QuickScanStoreError("cannot record listing history for a missing security")
            previous = row["listing_status"]
            if previous == listing_status:
                con.rollback()
                return  # idempotent
            con.execute(
                "UPDATE quick_scan_security SET listing_status=? WHERE security_id=?",
                (listing_status, security_id),
            )
            con.execute(
                """INSERT INTO quick_scan_listing_history
                (security_id, listing_status, previous_listing_status, reason,
                 effective_at, recorded_at)
                VALUES (?,?,?,?,?,?)""",
                (security_id, listing_status, previous, reason.strip(), effective_at, recorded_at),
            )
            con.commit()
        except QuickScanStoreError:
            con.rollback()
            raise
        finally:
            con.close()

    def listing_history(self, security_id: str) -> list[dict[str, Any]]:
        """Append-only listing status history for one security (ID-06)."""
        with closing(self._connect()) as con:
            return [
                dict(r)
                for r in con.execute(
                    "SELECT * FROM quick_scan_listing_history WHERE security_id=? "
                    "ORDER BY effective_at, history_id",
                    (security_id,),
                )
            ]

    def apply_rename(
        self,
        entity_id: str,
        *,
        new_canonical_name: str,
        old_canonical_name: str,
        identity_revision: int,
        effective_at: str,
        recorded_at: str,
        evidence_ref: str | None = None,
        dispatch_revision: str | None = None,
    ) -> None:
        """Documented issuer rename (ID-05/ID-15): entity_id stays stable.

        Source bindings keep their historical source name; only the entity's
        canonical_name and identity_revision change, and one append-only
        identity event is written in the same transaction. The documented old
        name must match the stored canonical_name.
        """
        if not new_canonical_name or not new_canonical_name.strip():
            raise QuickScanStoreError("new canonical name is required")
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT canonical_name, identity_revision FROM quick_scan_entity WHERE entity_id=?",
                (entity_id,),
            ).fetchone()
            if row is None:
                raise QuickScanStoreError("cannot rename a missing entity")
            current = int(row["identity_revision"])
            if row["canonical_name"] != old_canonical_name:
                raise QuickScanStoreError(
                    "documented old name does not match the stored canonical_name"
                )
            if identity_revision != current + 1:
                raise QuickScanStoreError(
                    f"next identity revision must be {current + 1}, got {identity_revision}"
                )
            con.execute(
                "UPDATE quick_scan_entity SET canonical_name=?, identity_revision=? "
                "WHERE entity_id=?",
                (new_canonical_name.strip(), identity_revision, entity_id),
            )
            con.execute(
                """INSERT OR IGNORE INTO quick_scan_identity_event
                (entity_id, event_type, old_value, new_value, effective_at,
                 evidence_ref, identity_revision, dispatch_revision, recorded_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    entity_id,
                    "rename",
                    old_canonical_name,
                    new_canonical_name.strip(),
                    effective_at,
                    evidence_ref,
                    identity_revision,
                    dispatch_revision,
                    recorded_at,
                ),
            )
            con.commit()
        except QuickScanStoreError:
            con.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            con.rollback()
            raise QuickScanStoreError(f"identity event integrity error: {exc}") from exc
        finally:
            con.close()

    def apply_ticker_change(
        self,
        entity_id: str,
        security_id: str,
        *,
        new_ticker: str,
        old_ticker: str,
        identity_revision: int,
        effective_at: str,
        recorded_at: str,
        evidence_ref: str | None = None,
        dispatch_revision: str | None = None,
    ) -> None:
        """Documented exchange-qualified ticker update (ID-15).

        Updates the security row and its source binding ticker atomically and
        writes one append-only identity event; identity_revision must advance
        by one. The save-path binding conflict guard is intentionally bypassed
        here because the change is documented (old/new ticker + event row in
        the same transaction) — silent divergence through save_entity remains
        rejected.
        """
        if not new_ticker or not new_ticker.strip():
            raise QuickScanStoreError("new ticker is required")
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT s.ticker, s.source_binding_ref, e.identity_revision "
                "FROM quick_scan_security s "
                "JOIN quick_scan_entity e ON e.entity_id=s.entity_id "
                "WHERE s.security_id=? AND s.entity_id=?",
                (security_id, entity_id),
            ).fetchone()
            if row is None:
                raise QuickScanStoreError("security not found on the entity")
            if row["ticker"] != old_ticker:
                raise QuickScanStoreError("documented old ticker does not match the stored ticker")
            current = int(row["identity_revision"])
            if identity_revision != current + 1:
                raise QuickScanStoreError(
                    f"next identity revision must be {current + 1}, got {identity_revision}"
                )
            con.execute(
                "UPDATE quick_scan_security SET ticker=? WHERE security_id=?",
                (new_ticker.strip(), security_id),
            )
            con.execute(
                "UPDATE quick_scan_source_binding SET ticker=? WHERE binding_ref=?",
                (new_ticker.strip(), row["source_binding_ref"]),
            )
            con.execute(
                "UPDATE quick_scan_entity SET identity_revision=? WHERE entity_id=?",
                (identity_revision, entity_id),
            )
            con.execute(
                """INSERT OR IGNORE INTO quick_scan_identity_event
                (entity_id, event_type, old_value, new_value, effective_at,
                 evidence_ref, identity_revision, dispatch_revision, recorded_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    entity_id,
                    "ticker_change",
                    old_ticker,
                    new_ticker.strip(),
                    effective_at,
                    evidence_ref,
                    identity_revision,
                    dispatch_revision,
                    recorded_at,
                ),
            )
            con.commit()
        except QuickScanStoreError:
            con.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            con.rollback()
            raise QuickScanStoreError(f"identity event integrity error: {exc}") from exc
        finally:
            con.close()

    def identity_events(self, entity_id: str, *, value: str | None = None) -> list[dict[str, Any]]:
        """Append-only identity events; ``value`` matches the old or new side (ID-05)."""
        with closing(self._connect()) as con:
            if value is None:
                rows = con.execute(
                    "SELECT * FROM quick_scan_identity_event WHERE entity_id=? "
                    "ORDER BY effective_at, event_id",
                    (entity_id,),
                )
            else:
                rows = con.execute(
                    "SELECT * FROM quick_scan_identity_event "
                    "WHERE entity_id=? AND (old_value=? OR new_value=?) "
                    "ORDER BY effective_at, event_id",
                    (entity_id, value, value),
                )
            return [dict(r) for r in rows]

    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as con:
            row = con.execute(
                "SELECT * FROM quick_scan_entity WHERE entity_id=?", (entity_id,)
            ).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["securities"] = self.securities_for_entity(entity_id, connection=con)
            result["segments"] = [
                dict(r)
                for r in con.execute(
                    "SELECT segment_id,segment_name,revenue_share_pct,description FROM quick_scan_segment "
                    "WHERE entity_id=? ORDER BY segment_id",
                    (entity_id,),
                )
            ]
            return result

    def securities_for_entity(
        self, entity_id: str, *, connection: sqlite3.Connection | None = None
    ):
        sql = "SELECT * FROM quick_scan_security WHERE entity_id=? ORDER BY security_id"
        if connection is not None:
            return [dict(r) for r in connection.execute(sql, (entity_id,))]
        with closing(self._connect()) as con:
            return [dict(r) for r in con.execute(sql, (entity_id,))]

    def create_universe(
        self, universe_id: str, name: str, *, soft_target_capacity: int | None = None
    ) -> None:
        if (
            not universe_id
            or not name
            or (soft_target_capacity is not None and soft_target_capacity < 0)
        ):
            raise QuickScanStoreError("invalid universe id, name or soft target capacity")
        try:
            with closing(self._connect()) as con:
                con.execute(
                    "INSERT INTO quick_scan_universe VALUES (?,?,?)",
                    (universe_id, name, soft_target_capacity),
                )
                con.commit()
        except sqlite3.IntegrityError as exc:
            raise QuickScanStoreError(f"universe already exists or invalid: {exc}") from exc

    def get_universe(self, universe_id: str) -> dict[str, Any] | None:
        """Return one universe row (id, name, soft_target_capacity) or None."""
        with closing(self._connect()) as con:
            row = con.execute(
                "SELECT * FROM quick_scan_universe WHERE universe_id=?",
                (universe_id,),
            ).fetchone()
            return dict(row) if row is not None else None

    @staticmethod
    def _member_values(member: dict[str, Any]) -> dict[str, Any]:
        required = (
            "universe_id",
            "entity_id",
            "membership_status",
            "manual_pin",
            "scan_enabled",
            "priority",
            "added_at",
            "added_reason",
            "version",
        )
        if any(k not in member for k in required):
            raise QuickScanStoreError("member is missing a required field")
        result = {
            k: member.get(k)
            for k in (
                "universe_id",
                "entity_id",
                "membership_status",
                "manual_pin",
                "scan_enabled",
                "priority",
                "added_at",
                "added_reason",
                "removed_at",
                "removal_reason",
                "restored_at",
                "restoration_reason",
                "version",
            )
        }
        if result["membership_status"] not in {"active", "logically_removed"}:
            raise QuickScanStoreError("invalid membership status")
        for flag in ("manual_pin", "scan_enabled"):
            flag_value = result[flag]
            if not isinstance(flag_value, bool):
                raise QuickScanStoreError(f"{flag} must be a canonical boolean")
            result[flag] = int(flag_value)
        version = result["version"]
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise QuickScanStoreError("version must be a non-boolean integer >= 1")
        return result

    def _member_txn(self, con: sqlite3.Connection, member: dict[str, Any]) -> None:
        values = self._member_values(member)
        old = con.execute(
            "SELECT version FROM quick_scan_member WHERE universe_id=? AND entity_id=?",
            (values["universe_id"], values["entity_id"]),
        ).fetchone()
        expected = 1 if old is None else int(old["version"]) + 1
        if int(values["version"]) != expected:
            raise QuickScanStoreError(f"member version must be the next version ({expected})")
        cols = ",".join(values)
        params = ",".join(":" + k for k in values)
        updates = ",".join(
            f"{k}=excluded.{k}" for k in values if k not in {"universe_id", "entity_id"}
        )
        con.execute(
            f"""INSERT INTO quick_scan_member ({cols}) VALUES ({params})
            ON CONFLICT(universe_id,entity_id) DO UPDATE SET {updates}""",
            values,
        )
        con.execute(
            """INSERT INTO quick_scan_member_history
            (universe_id,entity_id,version,snapshot_json) VALUES (?,?,?,?)""",
            (
                values["universe_id"],
                values["entity_id"],
                values["version"],
                json.dumps(values, sort_keys=True, separators=(",", ":")),
            ),
        )

    def save_member(self, member: dict[str, Any]) -> None:
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            self._member_txn(con, member)
            con.commit()
        except QuickScanStoreError:
            con.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            con.rollback()
            raise QuickScanStoreError(f"member integrity error: {exc}") from exc
        finally:
            con.close()

    def get_member(self, universe_id: str, entity_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as con:
            row = con.execute(
                "SELECT * FROM quick_scan_member WHERE universe_id=? AND entity_id=?",
                (universe_id, entity_id),
            ).fetchone()
            return self._decode_member(row) if row is not None else None

    @staticmethod
    def _decode_member(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["manual_pin"] = bool(result["manual_pin"])
        result["scan_enabled"] = bool(result["scan_enabled"])
        return result

    def list_members(self, universe_id: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as con:
            return [
                self._decode_member(r)
                for r in con.execute(
                    "SELECT * FROM quick_scan_member WHERE universe_id=? ORDER BY entity_id",
                    (universe_id,),
                )
            ]

    def member_history(self, universe_id: str, entity_id: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as con:
            return [
                json.loads(r["snapshot_json"])
                for r in con.execute(
                    """SELECT snapshot_json FROM quick_scan_member_history
                   WHERE universe_id=? AND entity_id=? ORDER BY version""",
                    (universe_id, entity_id),
                )
            ]

    def apply_candidates(self, rows: list[dict[str, Any]], *, at: str) -> list[str]:
        """Stage candidates in ONE transaction; identity payload is immutable.

        ``inserted`` on first sight, ``unchanged`` when the same listing_key
        arrives with an identical payload_sha256 (idempotent re-import), and
        ``conflict`` when the same listing_key arrives with different content:
        the original row is KEPT and only conflict counters advance — there is
        no last-write-wins path for candidate identity content.
        """
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            outcomes: list[str] = []
            for row in rows:
                existing = con.execute(
                    "SELECT payload_sha256 FROM quick_scan_candidate WHERE listing_key=?",
                    (row["listing_key"],),
                ).fetchone()
                if existing is None:
                    columns = ",".join(row)
                    placeholders = ",".join(":" + key for key in row)
                    con.execute(
                        f"INSERT INTO quick_scan_candidate ({columns}) VALUES ({placeholders})",
                        row,
                    )
                    outcomes.append("inserted")
                elif existing["payload_sha256"] == row["payload_sha256"]:
                    outcomes.append("unchanged")
                else:
                    con.execute(
                        "UPDATE quick_scan_candidate SET conflict_count=conflict_count+1,"
                        " last_conflict_payload_sha256=? WHERE listing_key=?",
                        (row["payload_sha256"], row["listing_key"]),
                    )
                    outcomes.append("conflict")
            con.commit()
            return outcomes
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _intent_row(self, intent: dict[str, Any], at: str) -> dict[str, Any]:
        parts = [
            intent.get("universe_id"),
            intent.get("entity_id"),
            intent.get("window_key"),
            intent.get("purpose"),
        ]
        if not all(isinstance(v, str) and v for v in parts):
            raise QuickScanStoreError("scan intent fields must be non-empty strings")
        if not isinstance(intent.get("source"), str) or not intent["source"]:
            raise QuickScanStoreError("scan intent source is required")
        digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
        return {
            "intent_key": "INT_" + digest[:32],
            "universe_id": intent["universe_id"],
            "entity_id": intent["entity_id"],
            "window_key": intent["window_key"],
            "purpose": intent["purpose"],
            "source": intent["source"],
            "created_at": at,
        }

    @staticmethod
    def _intent_insert(con: sqlite3.Connection, row: dict[str, Any]) -> str:
        cur = con.execute(
            """INSERT OR IGNORE INTO quick_scan_scan_intent (intent_key, universe_id,
            entity_id, window_key, purpose, source, created_at) VALUES
            (:intent_key, :universe_id, :entity_id, :window_key, :purpose,
             :source, :created_at)""",
            row,
        )
        return "created" if cur.rowcount == 1 else "existing"

    def record_intent(self, intent: dict[str, Any], *, at: str) -> str:
        """Insert-once operating scan intent outside admission (MAINT-01)."""
        row = self._intent_row(intent, at)
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            outcome = self._intent_insert(con, row)
            con.commit()
            return outcome
        except sqlite3.IntegrityError as exc:
            con.rollback()
            raise QuickScanStoreError(f"scan intent integrity error: {exc}") from exc
        finally:
            con.close()

    def admit_with_intent(
        self, member: dict[str, Any], intent: dict[str, Any], *, at: str
    ) -> dict[str, str]:
        """Atomic member admission + insert-once scan intent (MAINT-02/07).

        One local transaction: the member row (with its history version)
        and the scan intent both land or neither does. A racing duplicate
        admission loses the version race and rolls back whole.
        """
        row = self._intent_row(intent, at)
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            self._member_txn(con, member)
            intent_outcome = self._intent_insert(con, row)
            con.commit()
            return {"member": "created", "intent": intent_outcome}
        except QuickScanStoreError:
            con.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            con.rollback()
            raise QuickScanStoreError(f"admission integrity error: {exc}") from exc
        finally:
            con.close()
