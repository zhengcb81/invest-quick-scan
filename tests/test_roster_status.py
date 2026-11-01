"""Roster status tool: synthetic workspace, counts, actions and links."""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import roster_status  # noqa: E402


def build_workspace(root: Path):
    data = root / "data" / "quick_scan"
    data.mkdir(parents=True)
    with sqlite3.connect(data / "scan.sqlite") as con:
        con.executescript(
            """
            CREATE TABLE quick_scan_entity (entity_id TEXT, canonical_name TEXT, identity_state TEXT, identity_revision INTEGER);
            CREATE TABLE quick_scan_security (security_id TEXT, entity_id TEXT, market TEXT, ticker TEXT, listing_status TEXT);
            CREATE TABLE quick_scan_source_binding (binding_ref TEXT, entity_id TEXT, source_namespace TEXT);
            """
        )
        con.executemany(
            "INSERT INTO quick_scan_entity VALUES (?,?,?,?)",
            [("ENT_a", "Alpha Co", "verified", 2), ("ENT_b", "Beta Co", "provisional", 1)],
        )
        con.executemany(
            "INSERT INTO quick_scan_security VALUES (?,?,?,?,?)",
            [("SEC_a", "ENT_a", "CN", "000001", "active"), ("SEC_b", "ENT_b", "US", "BETA", "active")],
        )
        con.execute("INSERT INTO quick_scan_source_binding VALUES (?,?,?)", ("BIND_a", "ENT_a", "src"))
    with sqlite3.connect(data / "scan_observations.sqlite") as con:
        # payload_json is what roster_status parses for search-backed coverage.
        con.execute(
            "CREATE TABLE quick_scan_observation (observation_id TEXT, entity_id TEXT, payload_json TEXT)"
        )
        con.execute(
            "INSERT INTO quick_scan_observation VALUES (?,?,?)",
            ("obs_1", "ENT_a", json.dumps({"execution": {"search_status": "executed"}})),
        )
        con.execute(
            "INSERT INTO quick_scan_observation VALUES (?,?,?)",
            ("obs_2", "ENT_a", json.dumps({"execution": {"search_status": "skipped"}})),
        )
    return root


def test_roster_counts_and_actions(tmp_path):
    workspace = build_workspace(tmp_path / "ws")
    output = tmp_path / "roster.json"
    html = tmp_path / "roster.html"
    links = tmp_path / "links.json"
    links.write_text(
        json.dumps(
            {
                "candidate_count": 2,
                "linked": 1,
                "unresolved": 1,
                "unresolved_rows": [{"listing_key": "CN-A:999999", "reason": "different issuer"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert roster_status.main(["--workspace", str(workspace), "--json", str(output), "--html", str(html), "--links", str(links)]) == 0
    summary = json.loads(output.read_text(encoding="utf-8"))
    assert summary["entities"] == 2
    assert summary["verified"] == 1 and summary["provisional"] == 1
    assert summary["by_next_action"]["has_observations"] == 1
    assert summary["by_next_action"]["needs_verified_identity"] == 1
    assert summary["search_backed_entities"] == 1
    assert summary["search_backed_observations"] == 1
    assert summary["candidates"]["unresolved"] == 1
    page = html.read_text(encoding="utf-8")
    assert "Alpha Co" in page and "different issuer" in page and "未解决候选" in page
def test_archived_identity_audit_has_no_ticker_specific_evidence_bypass(tmp_path, capsys):
    import hashlib
    import json
    import runpy
    import sqlite3
    from contextlib import closing
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / 'scripts/verified_evidence_audit.py'
    module = runpy.run_path(str(script))
    main = module['main']
    # Isolate the old pilot-payload path too: a missing archive must not pass
    # simply because this one ticker's identifier can be recomputed.
    main.__globals__['ROOT'] = tmp_path
    workspace = tmp_path / 'workspace'
    store = workspace / 'data/quick_scan'
    store.mkdir(parents=True)
    entity, name = 'ENT_SYNTHETIC', 'Synthetic issuer'
    receipt = 'IVR_' + hashlib.sha256(('verified:' + entity + ':2:' + name).encode()).hexdigest()[:32]
    with closing(sqlite3.connect(store / 'scan.sqlite')) as connection:
        connection.executescript('''
            CREATE TABLE quick_scan_entity(entity_id, canonical_name, identity_state, identity_revision, verified_issuer_receipt_id);
            CREATE TABLE quick_scan_security(entity_id, ticker);
            CREATE TABLE quick_scan_source_binding(entity_id, source_record_id, source_canonical_name);
        ''')
        connection.execute('INSERT INTO quick_scan_entity VALUES (?,?,?,?,?)', (entity, name, 'verified', 2, receipt))
        connection.execute('INSERT INTO quick_scan_security VALUES (?,?)', (entity, '000002'))
        connection.commit()
    with closing(sqlite3.connect(store / 'identity_receipts.sqlite')) as connection:
        connection.execute('CREATE TABLE identity_receipt(receipt_id, kind, entity_id, identity_revision, receipt_json)')
        connection.commit()
    evidence = tmp_path / 'archive'
    evidence.mkdir()
    for filename in ('cninfo-profiles.jsonl', 'sec-profiles.jsonl'):
        (evidence / filename).write_text('', encoding='utf-8')
    output = tmp_path / 'audit.json'
    assert main(['--workspace', str(workspace), '--evidence', str(evidence), '--output', str(output)]) == 0
    result = json.loads(output.read_text(encoding='utf-8'))
    assert result['passed'] == 0 and result['failed'] == 1
    assert result['results'][0]['checks'] == [{'name': 'evidence_present', 'ok': False, 'detail': 'no archived evidence'}]
