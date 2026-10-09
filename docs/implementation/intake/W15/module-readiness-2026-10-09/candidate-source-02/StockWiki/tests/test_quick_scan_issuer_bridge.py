"""G2b A/H issuer-bridge evidence import tests (construction card 2026-10-05).

Binds the signed bridge evidence table import (121 rows after the owner
plan-A correction; the originally signed table had 122 — see the archived
original) to named refusals, content-addressed idempotency, the
zero-side-effect guarantee (no entity / member / universe rows), the
read-only report (incl. the --source diff=0 proof), and the CLI
end-to-end. Extended by the follow-up review round (P2-1/2/3 + LOW-2/3).

Originally written RED (the module did not exist yet).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from stockwiki.cli_registry import build_parser
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_store import QuickScanStore

RULES = "quick_scan_issuer_bridge_import/1.0.0"
DECISION_REF = "owner-2026-10-04-g2b-ah-bridge-signoff"


def _store(tmp_path: Path) -> QuickScanStore:
    store = QuickScanStore(WorkspacePaths.from_root(tmp_path))
    store.migrate()
    return store


def _row(cn: str, hk: str, cn_name: str, hk_name: str, **overrides) -> dict:
    evidence = "https://static.cninfo.com.cn/finalpage/2026-03-27/1225037929.PDF"
    row = {
        "schema": "g2b_ah_bridge_draft/1",
        "cn_listing_key": f"CN-A:{cn}",
        "hk_listing_key": f"HK:{hk}",
        "cn_ticker": cn,
        "hk_ticker": hk,
        "cn_name": cn_name,
        "hk_name": hk_name,
        "issuer_id": None,
        "issuer_id_status": "not_found_in_sources",
        "evidence_url": evidence,
        "evidence_kind": "annual_report_ah_section",
        "verification_source": "exchange_filing",
        "retrieved_at": "2026-10-04T17:08:15Z",
        "content_sha256": hashlib.sha256(f"{cn}{hk}".encode()).hexdigest(),
        "confidence": "high",
        "notes": "fixture row",
    }
    row.update(overrides)
    return row


def _signed(
    tmp_path: Path,
    rows: list[dict],
    *,
    status: str = "SIGNED",
    stats_rows: int | None = None,
    decision_ref: str = DECISION_REF,
) -> Path:
    payload = {
        "schema": "g2b_ah_bridge_draft/1",
        "generated_at": "2026-10-04T17:30:00Z",
        "status": status,
        "decision_ref": decision_ref,
        "rows": rows,
        "stats": {"rows": len(rows) if stats_rows is None else stats_rows},
    }
    path = tmp_path / f"ah_bridge_{abs(hash(json.dumps(rows)))}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def _import(store: QuickScanStore, source: Path, *, at: str | None = None) -> dict:
    from stockwiki.quick_scan_issuer_bridge import import_issuer_bridge

    return import_issuer_bridge(store, source, at=at)


def test_import_signed_rows_lands_evidence(tmp_path: Path) -> None:
    store = _store(tmp_path)
    rows = [
        _row("000039", "02039", "中集集团", "中集集團"),
        _row("000333", "00300", "美的集团", "美的集團"),
    ]
    receipt = _import(store, _signed(tmp_path, rows))
    assert receipt["rows_inserted"] == 2
    assert receipt["rows_unchanged"] == 0
    assert receipt["conflicts"] == 0
    assert receipt["decision_ref"] == DECISION_REF
    assert receipt["rules_version"] == RULES
    assert receipt["llm_calls"] == 0 and receipt["network_calls"] == 0
    with sqlite3.connect(store.database_path) as conn:
        n = conn.execute("SELECT COUNT(*) FROM quick_scan_issuer_bridge").fetchone()[0]
        assert n == 2
        # zero side-effect guarantee: no entities/members/universe rows appear
        for table in ("quick_scan_entity", "quick_scan_member", "quick_scan_universe"):
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_idempotent_replay_is_a_no_op(tmp_path: Path) -> None:
    store = _store(tmp_path)
    source = _signed(tmp_path, [_row("000039", "02039", "中集集团", "中集集團")])
    first = _import(store, source)
    second = _import(store, source)
    assert (first["rows_inserted"], first["rows_unchanged"]) == (1, 0)
    assert (second["rows_inserted"], second["rows_unchanged"]) == (0, 1)


def test_missing_signed_status_is_refused(tmp_path: Path) -> None:
    from stockwiki.quick_scan_issuer_bridge import ImportIssuerBridgeError

    store = _store(tmp_path)
    source = _signed(tmp_path, [_row("000039", "02039", "中集集团", "中集集團")], status="DRAFT")
    with pytest.raises(ImportIssuerBridgeError) as excinfo:
        _import(store, source)
    assert excinfo.value.error_code == "source_not_signed"


def test_row_count_mismatch_is_refused(tmp_path: Path) -> None:
    from stockwiki.quick_scan_issuer_bridge import ImportIssuerBridgeError

    store = _store(tmp_path)
    rows = [
        _row("000039", "02039", "中集集团", "中集集團"),
        _row("000333", "00300", "美的集团", "美的集團"),
    ]
    source = _signed(tmp_path, rows[:1], stats_rows=len(rows))
    with pytest.raises(ImportIssuerBridgeError) as excinfo:
        _import(store, source)
    assert excinfo.value.error_code == "row_count_mismatch"


def test_non_hex_sha_is_refused(tmp_path: Path) -> None:
    from stockwiki.quick_scan_issuer_bridge import ImportIssuerBridgeError

    store = _store(tmp_path)
    source = _signed(
        tmp_path, [_row("000039", "02039", "中集集团", "中集集團", content_sha256="deadbeef")]
    )
    with pytest.raises(ImportIssuerBridgeError) as excinfo:
        _import(store, source)
    assert excinfo.value.error_code == "sha_invalid"


def test_same_pair_different_sha_conflicts(tmp_path: Path) -> None:
    from stockwiki.quick_scan_issuer_bridge import ImportIssuerBridgeError

    store = _store(tmp_path)
    _import(store, _signed(tmp_path, [_row("000039", "02039", "中集集团", "中集集團")]))
    tampered = _signed(
        tmp_path, [_row("000039", "02039", "中集集团", "中集集團", content_sha256="b" * 64)]
    )
    with pytest.raises(ImportIssuerBridgeError) as excinfo:
        _import(store, tampered)
    assert excinfo.value.error_code == "pair_conflict"


def test_entity_binding_is_forbidden(tmp_path: Path) -> None:
    from stockwiki.quick_scan_issuer_bridge import ImportIssuerBridgeError

    store = _store(tmp_path)
    source = _signed(
        tmp_path, [_row("000039", "02039", "中集集团", "中集集團", issuer_id="ENT_abc")]
    )
    with pytest.raises(ImportIssuerBridgeError) as excinfo:
        _import(store, source)
    assert excinfo.value.error_code == "entity_binding_forbidden"


def test_row_without_evidence_is_refused(tmp_path: Path) -> None:
    from stockwiki.quick_scan_issuer_bridge import ImportIssuerBridgeError

    store = _store(tmp_path)
    source = _signed(tmp_path, [_row("000039", "02039", "中集集团", "中集集團", evidence_url=None)])
    with pytest.raises(ImportIssuerBridgeError) as excinfo:
        _import(store, source)
    assert excinfo.value.error_code == "row_shape_invalid"


def test_report_is_read_only(tmp_path: Path) -> None:
    from stockwiki.quick_scan_issuer_bridge import bridge_report

    store = _store(tmp_path)
    _import(store, _signed(tmp_path, [_row("000039", "02039", "中集集团", "中集集團")]))
    with sqlite3.connect(store.database_path) as conn:
        before = conn.execute(
            "SELECT COUNT(*), MAX(content_sha256) FROM quick_scan_issuer_bridge"
        ).fetchone()
    report = bridge_report(store)
    assert report["rows"] == 1
    assert report["confidence"] == {"high": 1}
    assert DECISION_REF in (report.get("decision_refs") or [])
    with sqlite3.connect(store.database_path) as conn:
        after = conn.execute(
            "SELECT COUNT(*), MAX(content_sha256) FROM quick_scan_issuer_bridge"
        ).fetchone()
    assert before == after


def test_cli_import_and_report_end_to_end(tmp_path: Path, capsys) -> None:
    source = _signed(tmp_path, [_row("000039", "02039", "中集集团", "中集集團")])
    parser = build_parser()
    args = parser.parse_args(
        [
            "--root",
            str(tmp_path),
            "issuer-bridge-import",
            "--source",
            str(source),
        ]
    )
    rc = args.func(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["rows_inserted"] == 1
    report_args = parser.parse_args(
        [
            "--root",
            str(tmp_path),
            "issuer-bridge-report",
        ]
    )
    assert report_args.func(report_args) == 0
    report = json.loads(capsys.readouterr().out.strip())
    assert report["rows"] == 1


def test_cli_rejects_draft_with_named_error(tmp_path: Path, capsys) -> None:
    source = _signed(tmp_path, [_row("000039", "02039", "中集集团", "中集集團")], status="DRAFT")
    parser = build_parser()
    args = parser.parse_args(
        [
            "--root",
            str(tmp_path),
            "issuer-bridge-import",
            "--source",
            str(source),
        ]
    )
    rc = args.func(args)
    assert rc == 2
    err = capsys.readouterr().err
    assert "source_not_signed" in err


# --- follow-up review round (G2b-AH-import-review P2-1/P2-2/P2-3 + LOW-2/3) ---


def test_forged_decision_ref_is_refused(tmp_path: Path) -> None:
    """P2-1: decision_ref must match the owner-YYYY-MM-DD-slug format, not
    merely be a non-empty string (reviewer probe: 'forged-ref-xyz' accepted)."""
    from stockwiki.quick_scan_issuer_bridge import ImportIssuerBridgeError

    store = _store(tmp_path)
    source = _signed(
        tmp_path,
        [_row("000039", "02039", "中集集团", "中集集團")],
        decision_ref="forged-ref-xyz",
    )
    with pytest.raises(ImportIssuerBridgeError) as excinfo:
        _import(store, source)
    assert excinfo.value.error_code == "decision_ref_invalid"


def test_expected_decision_ref_mismatch_is_refused(tmp_path: Path) -> None:
    """P2-1: when the caller states which sign-off it expects, a different
    one is an explicit refusal instead of an acceptance."""
    from stockwiki.quick_scan_issuer_bridge import (
        ImportIssuerBridgeError,
        import_issuer_bridge,
    )

    store = _store(tmp_path)
    source = _signed(tmp_path, [_row("000039", "02039", "中集集团", "中集集團")])
    with pytest.raises(ImportIssuerBridgeError) as excinfo:
        import_issuer_bridge(store, source, expect_decision_ref="owner-9999-01-01-other-signoff")
    assert excinfo.value.error_code == "decision_ref_mismatch"


def test_scan_eligible_smuggling_is_named_refusal(tmp_path: Path) -> None:
    """LOW-2: a row carrying scan_eligible gets a NAMED refusal instead of
    a silent drop (card requires both entity_id and scan_eligible refused)."""
    from stockwiki.quick_scan_issuer_bridge import ImportIssuerBridgeError

    store = _store(tmp_path)
    source = _signed(
        tmp_path,
        [_row("000039", "02039", "中集集团", "中集集團", scan_eligible=True)],
    )
    with pytest.raises(ImportIssuerBridgeError) as excinfo:
        _import(store, source)
    assert excinfo.value.error_code == "scan_eligible_forbidden"


def test_report_against_source_proves_zero_diff(tmp_path: Path) -> None:
    """P2-3: issuer-bridge-report --source proves DB<->source diff=0 and
    carries the sha-manifest digest the card requires."""
    from stockwiki.quick_scan_issuer_bridge import bridge_report

    store = _store(tmp_path)
    source = _signed(
        tmp_path,
        [
            _row("000039", "02039", "中集集团", "中集集團"),
            _row("000333", "00300", "美的集团", "美的集團"),
        ],
    )
    _import(store, source)
    report = bridge_report(store, source=source)
    diff = report["source_diff"]
    assert diff["rows_source"] == 2 and diff["rows_db"] == 2
    assert diff["mismatches"] == 0
    assert diff["missing_in_db"] == [] and diff["extra_in_db"] == []
    assert report["sha_manifest_digest"].startswith("sha256:")
    assert len(report["sha_manifest_digest"]) == len("sha256:") + 64


def test_cli_import_writes_receipt_report_copy(tmp_path: Path, capsys) -> None:
    """LOW-3: --report <path> writes the receipt copy alongside stdout."""
    source = _signed(tmp_path, [_row("000039", "02039", "中集集团", "中集集團")])
    receipt_path = tmp_path / "receipt-copy.json"
    parser = build_parser()
    args = parser.parse_args(
        [
            "--root",
            str(tmp_path),
            "issuer-bridge-import",
            "--source",
            str(source),
            "--report",
            str(receipt_path),
        ]
    )
    rc = args.func(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["rows_inserted"] == 1
    written = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert written == payload


def test_v4_to_v5_migration_preserves_staged_candidates(tmp_path: Path) -> None:
    """P2-2: the card demands the v4->v5 migration test in BOTH states —
    a bare DB upgrading to v5, and a v4 DB carrying staged candidate rows
    whose data must survive the bridge-table addition."""
    import shutil
    import sqlite3

    from stockwiki.quick_scan_schema import apply_v1, apply_v2, apply_v3, apply_v4
    from stockwiki.quick_scan_store import SCHEMA_VERSION

    # Fresh/current and genuine v4 both retain the v5 bridge contract.
    store = _store(tmp_path)
    assert store.migrate() == SCHEMA_VERSION
    con = sqlite3.connect(store.database_path)
    tables = {
        r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert "quick_scan_issuer_bridge" in tables
    con.close()

    # state B: rebuild a genuine v4 DB with one staged candidate, then migrate
    db = tmp_path / "v4_state.db"
    con = sqlite3.connect(db)
    for fn in (apply_v1, apply_v2, apply_v3, apply_v4):
        fn(con)
    con.execute("PRAGMA user_version=4")
    con.execute(
        "INSERT INTO quick_scan_candidate (listing_key, market, exchange, ticker, "
        "security_type, candidate_state, entity_id, scan_eligible, reasons_json, "
        "conflicts_json, name_claims_json, payload_sha256, input_sha256, "
        "report_sha256, import_batch_id, imported_at, conflict_count, "
        "last_conflict_payload_sha256) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "CN-A:TEST",
            "CN-A",
            None,
            "TEST",
            None,
            "unresolved",
            None,
            0,
            "[]",
            "[]",
            "[]",
            "0" * 64,
            "1" * 64,
            "2" * 64,
            "batch",
            "2026-10-05T00:00:00Z",
            0,
            None,
        ),
    )
    con.commit()
    original_candidate = con.execute("SELECT * FROM quick_scan_candidate").fetchall()
    con.close()
    ws2 = tmp_path / "v4ws"
    ws2.mkdir()
    store2 = QuickScanStore(WorkspacePaths.from_root(ws2))
    store2.database_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db, store2.database_path)
    assert store2.migrate() == SCHEMA_VERSION
    con = sqlite3.connect(store2.database_path)
    assert con.execute("SELECT * FROM quick_scan_candidate").fetchall() == original_candidate
    assert (
        con.execute(
            "SELECT COUNT(*) FROM quick_scan_candidate WHERE listing_key='CN-A:TEST'"
        ).fetchone()[0]
        == 1
    )
    assert con.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert (
        con.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='quick_scan_issuer_bridge'"
        ).fetchone()[0]
        == 1
    )
    con.close()
