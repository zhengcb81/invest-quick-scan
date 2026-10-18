"""Read-only profile readiness: identity, owner route, observations per company."""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path

ROOT = Path("C:/Users/郑曾波/Projects/invest-quick-scan")
DEFAULT_WS = ROOT/"runs/c16b/native-owner-alphabet-01/owner-workspace"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WS)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)
    scan = args.workspace/"data/quick_scan/scan.sqlite"
    observations = args.workspace/"data/quick_scan/scan_observations.sqlite"
    policy_path = args.workspace/"config/quick_scan_refresh.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8")) if policy_path.is_file() else {}
    routed = {}
    for route in policy.get("routes", []):
        if route.get("scope") == "entity":
            routed[route.get("scope_id")] = route.get("subject_key")
    with closing(sqlite3.connect(scan.resolve().as_uri()+"?mode=ro", uri=True)) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=ON")
        raw = [dict(r) for r in con.execute(
            "SELECT e.entity_id, e.canonical_name, e.identity_state, s.market, s.ticker FROM quick_scan_entity e JOIN quick_scan_security s USING(entity_id) ORDER BY e.canonical_name"
        )]
    merged = {}
    for row in raw:
        item = merged.setdefault(row["entity_id"], {"entity_id": row["entity_id"], "canonical_name": row["canonical_name"],
                                                     "identity_state": row["identity_state"], "listings": []})
        item["listings"].append({"market": row["market"], "ticker": row["ticker"]})
    rows = list(merged.values())
    observed = Counter()
    if observations.is_file():
        with closing(sqlite3.connect(observations.resolve().as_uri()+"?mode=ro", uri=True)) as con:
            con.execute("PRAGMA query_only=ON")
            for (entity_id,) in con.execute("SELECT entity_id FROM quick_scan_observation"):
                observed[entity_id] += 1
    matrix = []
    for row in rows:
        verified = row["identity_state"] == "verified"
        route = routed.get(row["entity_id"])
        if not verified:
            action = "needs_verified_identity"
        elif route:
            action = "ready_for_profile"
        else:
            action = "needs_owner_admission"
        matrix.append({**row, "owner_subject_key": route, "observations": observed.get(row["entity_id"], 0), "next_action": action})
    summary = {
        "protocol": "iqs.profile-readiness/1.0.0",
        "entities": len(matrix),
        "verified": sum(1 for m in matrix if m["identity_state"] == "verified"),
        "owner_routed": len(routed),
        "by_next_action": dict(Counter(m["next_action"] for m in matrix)),
        "rows": matrix,
    }
    if args.json:
        args.json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("entities", "verified", "owner_routed", "by_next_action")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
