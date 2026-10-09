"""Quick-scan schema migrations (extracted from quick_scan_store).

W13 persistence needed room under the 1000-line critical gate for
quick_scan_store.py; DDL now lives here as module-level
``apply_vN(con)`` steps while the store keeps data operations and
transactions. The migrate chain in quick_scan_store.py calls these
inside its single BEGIN IMMEDIATE — behavior is unchanged.
"""

from __future__ import annotations

import sqlite3


def apply_v1(con: sqlite3.Connection) -> None:
    ddl = [
        """CREATE TABLE quick_scan_entity (
        entity_id TEXT PRIMARY KEY, identity_schema_version TEXT NOT NULL,
        identity_state TEXT NOT NULL CHECK(identity_state IN ('provisional','verified')),
        identity_revision INTEGER NOT NULL CHECK(identity_revision>=1),
        canonical_name TEXT NOT NULL, incorporation_country TEXT,
        scope_attestation_id TEXT NOT NULL, verified_issuer_receipt_id TEXT,
        company_wiki_ref TEXT, formal_stockwiki_profile TEXT)""",
        """CREATE TABLE quick_scan_source_binding (
        binding_ref TEXT PRIMARY KEY, source_namespace TEXT NOT NULL,
        source_record_id TEXT NOT NULL, source_canonical_name TEXT NOT NULL,
        security_id TEXT NOT NULL, entity_id TEXT NOT NULL, market TEXT NOT NULL,
        exchange_raw TEXT NOT NULL, ticker TEXT NOT NULL, status TEXT NOT NULL,
        UNIQUE(source_namespace,source_record_id),
        FOREIGN KEY(entity_id) REFERENCES quick_scan_entity(entity_id) DEFERRABLE INITIALLY DEFERRED,
        FOREIGN KEY(security_id) REFERENCES quick_scan_security(security_id) DEFERRABLE INITIALLY DEFERRED)""",
        """CREATE TABLE quick_scan_security (
        security_id TEXT PRIMARY KEY, entity_id TEXT NOT NULL, market TEXT NOT NULL,
        exchange_raw TEXT NOT NULL, exchange TEXT NOT NULL, ticker TEXT NOT NULL,
        currency TEXT NOT NULL, security_type TEXT NOT NULL, listing_status TEXT NOT NULL,
        source_binding_ref TEXT NOT NULL UNIQUE, adr_ratio REAL, ordinary_security_ref TEXT,
        FOREIGN KEY(entity_id) REFERENCES quick_scan_entity(entity_id) DEFERRABLE INITIALLY DEFERRED,
        FOREIGN KEY(source_binding_ref) REFERENCES quick_scan_source_binding(binding_ref) DEFERRABLE INITIALLY DEFERRED,
        FOREIGN KEY(ordinary_security_ref) REFERENCES quick_scan_security(security_id) DEFERRABLE INITIALLY DEFERRED)""",
        """CREATE TABLE quick_scan_segment (
        entity_id TEXT NOT NULL, segment_id TEXT NOT NULL, segment_name TEXT NOT NULL,
        revenue_share_pct REAL, description TEXT, PRIMARY KEY(entity_id,segment_id),
        FOREIGN KEY(entity_id) REFERENCES quick_scan_entity(entity_id) DEFERRABLE INITIALLY DEFERRED)""",
        """CREATE TABLE quick_scan_universe (
        universe_id TEXT PRIMARY KEY, name TEXT NOT NULL,
        soft_target_capacity INTEGER CHECK(soft_target_capacity IS NULL OR soft_target_capacity>=0))""",
        """CREATE TABLE quick_scan_member (
        universe_id TEXT NOT NULL, entity_id TEXT NOT NULL,
        membership_status TEXT NOT NULL CHECK(membership_status IN ('active','logically_removed')),
        manual_pin INTEGER NOT NULL CHECK(manual_pin IN (0,1)),
        scan_enabled INTEGER NOT NULL CHECK(scan_enabled IN (0,1)),
        priority INTEGER NOT NULL, added_at TEXT NOT NULL, added_reason TEXT NOT NULL,
        removed_at TEXT, removal_reason TEXT, restored_at TEXT, restoration_reason TEXT,
        version INTEGER NOT NULL CHECK(version>=1), PRIMARY KEY(universe_id,entity_id),
        FOREIGN KEY(universe_id) REFERENCES quick_scan_universe(universe_id),
        FOREIGN KEY(entity_id) REFERENCES quick_scan_entity(entity_id))""",
        """CREATE TABLE quick_scan_member_history (
        universe_id TEXT NOT NULL, entity_id TEXT NOT NULL, version INTEGER NOT NULL CHECK(version>=1),
        snapshot_json TEXT NOT NULL, PRIMARY KEY(universe_id,entity_id,version),
        FOREIGN KEY(universe_id,entity_id) REFERENCES quick_scan_member(universe_id,entity_id)
        DEFERRABLE INITIALLY DEFERRED)""",
    ]
    for statement in ddl:
        con.execute(statement)


def apply_v2(con: sqlite3.Connection) -> None:
    ddl = [
        """CREATE TABLE quick_scan_listing_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        security_id TEXT NOT NULL,
        listing_status TEXT NOT NULL,
        previous_listing_status TEXT,
        reason TEXT NOT NULL,
        effective_at TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        FOREIGN KEY(security_id) REFERENCES quick_scan_security(security_id))""",
        """CREATE TABLE quick_scan_identity_event (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id TEXT NOT NULL,
        event_type TEXT NOT NULL CHECK(event_type IN ('rename','ticker_change','listing_delist','listing_restore')),
        old_value TEXT NOT NULL,
        new_value TEXT NOT NULL,
        effective_at TEXT NOT NULL,
        evidence_ref TEXT,
        identity_revision INTEGER NOT NULL,
        dispatch_revision TEXT,
        recorded_at TEXT NOT NULL,
        FOREIGN KEY(entity_id) REFERENCES quick_scan_entity(entity_id))""",
        "CREATE INDEX idx_quick_scan_listing_history "
        "ON quick_scan_listing_history(security_id, effective_at)",
        "CREATE INDEX idx_quick_scan_identity_event "
        "ON quick_scan_identity_event(entity_id, old_value, new_value)",
    ]
    for statement in ddl:
        con.execute(statement)


def apply_v3(con: sqlite3.Connection) -> None:
    con.execute("""CREATE TABLE quick_scan_candidate (
        listing_key TEXT PRIMARY KEY,
        market TEXT NOT NULL,
        exchange TEXT,
        ticker TEXT NOT NULL,
        security_type TEXT,
        candidate_state TEXT NOT NULL,
        entity_id TEXT,
        scan_eligible INTEGER NOT NULL DEFAULT 0,
        reasons_json TEXT NOT NULL,
        conflicts_json TEXT NOT NULL,
        name_claims_json TEXT NOT NULL,
        payload_sha256 TEXT NOT NULL,
        input_sha256 TEXT NOT NULL,
        report_sha256 TEXT NOT NULL,
        import_batch_id TEXT NOT NULL,
        imported_at TEXT NOT NULL,
        conflict_count INTEGER NOT NULL DEFAULT 0,
        last_conflict_payload_sha256 TEXT)""")
    con.execute("CREATE INDEX idx_qscand_state ON quick_scan_candidate(candidate_state)")


def apply_v4(con: sqlite3.Connection) -> None:
    """W13 maintenance persistence: nominations, scan intents, policies."""
    con.execute("""CREATE TABLE quick_scan_nomination (
        nomination_id INTEGER PRIMARY KEY AUTOINCREMENT,
        universe_id TEXT NOT NULL,
        source_namespace TEXT NOT NULL,
        source_record_id TEXT NOT NULL,
        listing_key TEXT,
        display_name TEXT NOT NULL,
        proposed_entity_id TEXT,
        identity_state TEXT NOT NULL DEFAULT 'unresolved',
        review_status TEXT NOT NULL DEFAULT 'candidate',
        reasons_json TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(universe_id, source_namespace, source_record_id))""")
    con.execute("""CREATE TABLE quick_scan_scan_intent (
        intent_key TEXT PRIMARY KEY,
        universe_id TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        window_key TEXT NOT NULL,
        purpose TEXT NOT NULL,
        source TEXT NOT NULL,
        created_at TEXT NOT NULL)""")
    con.execute("""CREATE TABLE quick_scan_maintenance_policy (
        universe_id TEXT PRIMARY KEY,
        policy TEXT NOT NULL,
        updated_at TEXT NOT NULL)""")
    con.execute(
        "CREATE INDEX idx_qsnom_universe ON quick_scan_nomination(universe_id, review_status)"
    )
    con.execute(
        "CREATE INDEX idx_qsintent_entity ON quick_scan_scan_intent(universe_id, entity_id)"
    )


def apply_v5(con: sqlite3.Connection) -> None:
    """G2b A/H bridge: owner-signed same-issuer pair evidence.

    Evidence rows only — never entities, members, or scan eligibility. The
    evidence document hash is the primary key (content-addressed replay);
    one row per A/H pair (unique pair guard turns same-pair-different-
    evidence into an explicit conflict at the import layer).
    """
    con.execute("""CREATE TABLE quick_scan_issuer_bridge (
        content_sha256 TEXT PRIMARY KEY,
        cn_listing_key TEXT NOT NULL,
        hk_listing_key TEXT NOT NULL,
        cn_ticker TEXT NOT NULL,
        hk_ticker TEXT NOT NULL,
        cn_name TEXT NOT NULL,
        hk_name TEXT NOT NULL,
        issuer_id TEXT,
        issuer_id_status TEXT NOT NULL,
        evidence_url TEXT NOT NULL,
        evidence_kind TEXT NOT NULL,
        verification_source TEXT NOT NULL,
        retrieved_at TEXT NOT NULL,
        confidence TEXT NOT NULL,
        notes TEXT,
        import_batch_id TEXT NOT NULL,
        decision_ref TEXT NOT NULL,
        imported_at TEXT NOT NULL,
        UNIQUE(cn_listing_key, hk_listing_key))""")
    con.execute("CREATE INDEX idx_qsbridge_decision ON quick_scan_issuer_bridge(decision_ref)")


def apply_v6(con: sqlite3.Connection) -> None:
    """W15 immutable route bundles and subject/scope-specific CAS pointers."""
    con.execute("""CREATE TABLE quick_scan_route_snapshot (
        decision_id TEXT PRIMARY KEY, subject_key TEXT NOT NULL,
        entity_id TEXT NOT NULL, identity_revision INTEGER NOT NULL,
        perimeter_sha256 TEXT NOT NULL,
        scope TEXT NOT NULL CHECK(scope IN ('entity','segment')),
        scope_id TEXT NOT NULL, route_raw BLOB NOT NULL, manifest_raw BLOB NOT NULL,
        route_raw_sha256 TEXT NOT NULL, manifest_raw_sha256 TEXT NOT NULL,
        metadata_json TEXT NOT NULL, metadata_sha256 TEXT NOT NULL,
        FOREIGN KEY(entity_id) REFERENCES quick_scan_entity(entity_id))""")
    con.execute("""CREATE TABLE quick_scan_route_current (
        subject_key TEXT NOT NULL, scope TEXT NOT NULL, scope_id TEXT NOT NULL,
        decision_id TEXT NOT NULL, version INTEGER NOT NULL CHECK(version>=1),
        activated_at TEXT NOT NULL, PRIMARY KEY(subject_key,scope,scope_id),
        FOREIGN KEY(decision_id) REFERENCES quick_scan_route_snapshot(decision_id))""")
    con.execute("""CREATE TABLE quick_scan_route_current_history (
        subject_key TEXT NOT NULL, scope TEXT NOT NULL, scope_id TEXT NOT NULL,
        version INTEGER NOT NULL CHECK(version>=1), decision_id TEXT NOT NULL,
        previous_decision_id TEXT, activated_at TEXT NOT NULL,
        PRIMARY KEY(subject_key,scope,scope_id,version),
        FOREIGN KEY(decision_id) REFERENCES quick_scan_route_snapshot(decision_id))""")
