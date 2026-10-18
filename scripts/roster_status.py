"""Read-only roster status for the existing company list.

Shows every onboarded entity with its identity state, listing and observation
count, and the next action an operator must take. Never writes.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path

DEFAULT_WS = Path("C:/Users/郑曾波/Projects/invest-quick-scan/runs/c16b/native-owner-alphabet-01/owner-workspace")


def connect(path):
    connection = sqlite3.connect(Path(path).resolve().as_uri()+"?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WS)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)
    scan = args.workspace/"data/quick_scan/scan.sqlite"
    observations = args.workspace/"data/quick_scan/scan_observations.sqlite"
    with closing(connect(scan)) as connection:
        entities = [dict(row) for row in connection.execute(
            "SELECT entity_id, canonical_name, identity_state, identity_revision FROM quick_scan_entity ORDER BY canonical_name"
        )]
        securities = [dict(row) for row in connection.execute(
            "SELECT security_id, entity_id, market, ticker, listing_status FROM quick_scan_security"
        )]
        bindings = [dict(row) for row in connection.execute(
            "SELECT binding_ref, entity_id, source_namespace FROM quick_scan_source_binding"
        )]
    by_entity = {}
    for row in securities:
        by_entity.setdefault(row["entity_id"], []).append(row)
    binding_count = Counter(row["entity_id"] for row in bindings)
    observed = Counter()
    if observations.is_file():
        with closing(connect(observations)) as connection:
            for row in connection.execute("SELECT entity_id FROM quick_scan_observation"):
                observed[row["entity_id"]] += 1
    rows = []
    for entity in entities:
        listings = by_entity.get(entity["entity_id"], [])
        verified = entity["identity_state"] == "verified"
        if not verified:
            action = "needs_verified_identity"
        elif observed.get(entity["entity_id"], 0):
            action = "has_observations"
        else:
            action = "ready_for_profile"
        rows.append({
            "entity_id": entity["entity_id"],
            "name": entity["canonical_name"],
            "identity_state": entity["identity_state"],
            "identity_revision": entity["identity_revision"],
            "listings": [{"market": l["market"], "ticker": l["ticker"], "status": l["listing_status"]} for l in listings],
            "bindings": binding_count.get(entity["entity_id"], 0),
            "observations": observed.get(entity["entity_id"], 0),
            "next_action": action,
        })
    summary = {
        "protocol": "iqs.roster-status/1.0.0",
        "workspace": str(args.workspace),
        "entities": len(rows),
        "verified": sum(1 for r in rows if r["identity_state"] == "verified"),
        "provisional": sum(1 for r in rows if r["identity_state"] == "provisional"),
        "by_market": dict(Counter(l["market"] for r in rows for l in r["listings"])),
        "by_next_action": dict(Counter(r["next_action"] for r in rows)),
        "rows": rows,
    }
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.json:
        args.json.write_text(payload, encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("entities", "verified", "provisional", "by_market", "by_next_action")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
