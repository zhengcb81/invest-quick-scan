"""Coverage gap view: verified companies still waiting for an owner route.

Read-only. Builds a JSON/HTML snapshot from the roster status rows so the next
owner-admission batch is explicit instead of inferred.
"""
from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    roster = json.loads(args.roster.read_text(encoding="utf-8"))
    rows = [r for r in roster.get("rows", []) if r.get("next_action") == "needs_owner_admission"]
    by_market = Counter((r.get("listings") or [{}])[0].get("market") or "?" for r in rows)
    document = {
        "protocol": "iqs.coverage-gaps/1.0.0",
        "verified_entities": roster.get("verified"),
        "waiting_owner_admission": len(rows),
        "by_market": dict(by_market),
        "rows": [
            {
                "entity_id": r["entity_id"],
                "name": r["name"],
                "tickers": [l.get("ticker") for l in r.get("listings") or []],
                "markets": [l.get("market") for l in r.get("listings") or []],
                "reason": "没有 owner 路由（route/policy/admission 未建立）",
            }
            for r in rows
        ],
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.html:
        body = "".join(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(r["name"]), html.escape(",".join(str(t) for t in r["tickers"])),
                html.escape(",".join(str(m) for m in r["markets"])), html.escape(r["entity_id"]),
            )
            for r in document["rows"][:500]
        )
        args.html.write_text(
            "<!doctype html><meta charset='utf-8'><title>coverage gaps</title>"
            "<h1>Verified 但缺 owner 路由</h1>"
            f"<p>verified {document['verified_entities']} · 待 owner admission {document['waiting_owner_admission']} "
            f"· 分布 {html.escape(json.dumps(document['by_market'], ensure_ascii=False))}</p>"
            "<table border='1' cellpadding='4'><tr><th>name</th><th>tickers</th><th>markets</th><th>entity</th></tr>"
            + body + "</table><p>只读视图；不构成准入或投资结论。</p>",
            encoding="utf-8",
        )
    print(json.dumps({"waiting": len(rows), "by_market": dict(by_market)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
