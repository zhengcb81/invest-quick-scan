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
        con.execute("CREATE TABLE quick_scan_observation (observation_id TEXT, entity_id TEXT)")
        con.execute("INSERT INTO quick_scan_observation VALUES (?,?)", ("obs_1", "ENT_a"))
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
    assert summary["candidates"]["unresolved"] == 1
    page = html.read_text(encoding="utf-8")
    assert "Alpha Co" in page and "different issuer" in page and "未解决候选" in page
