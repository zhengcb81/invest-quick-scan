"""Check search-backed observation citations against the retrieval receipts that authorized them.

Read-only, offline. For every observation with execution.search_receipt_id, load the
external search result entries for that operation and verify that each cited URL
appears in the receipt (exact URL match). Observations without a receipt are
reported as research_only, not failures.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

OBS_DB = Path("runs/c16b/native-owner-alphabet-01/owner-workspace/data/quick_scan/scan_observations.sqlite")
WORK_DB = Path("runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite")


def load(conn, sql, args=()):
    cur = conn.execute(sql, args)
    return cur.fetchall()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", type=Path, default=OBS_DB)
    parser.add_argument("--work", type=Path, default=WORK_DB)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    obs = sqlite3.connect(args.observations.resolve().as_uri() + "?mode=ro", uri=True)
    obs.row_factory = sqlite3.Row
    work = sqlite3.connect(args.work.resolve().as_uri() + "?mode=ro", uri=True)
    work.row_factory = sqlite3.Row
    results = []
    for row in obs.execute("SELECT payload_json FROM quick_scan_observation ORDER BY rowid"):
        payload = json.loads(row["payload_json"])
        execution = payload.get("execution") or {}
        receipt_id = execution.get("search_receipt_id")
        answer = payload.get("answer") or {}
        cited = [e.get("url") for e in (answer.get("evidence") or []) if isinstance(e, dict)]
        cited = [u for u in cited if isinstance(u, str) and u]
        record = {
            "question_id": payload.get("question_id"),
            "observation_id": payload.get("observation_id"),
            "answer_status": answer.get("status"),
            "search_status": execution.get("search_status"),
            "search_receipt_id": receipt_id,
            "cited": cited,
            "receipt_urls": [],
            "missing": [],
            "result": "research_only",
        }
        if receipt_id:
            result = work.execute(
                "SELECT receipt_json FROM quick_scan_external_result WHERE operation_id=?", (receipt_id,)
            ).fetchone()
            if result is None:
                record["result"] = "receipt_missing"
            else:
                receipt = json.loads(result["receipt_json"])
                urls = [e.get("url") for e in (receipt.get("entries") or []) if isinstance(e, dict)]
                record["receipt_urls"] = [u for u in urls if isinstance(u, str)]
                record["missing"] = [u for u in cited if u not in record["receipt_urls"]]
                record["result"] = "pass" if not record["missing"] else "fail"
        results.append(record)
    document = {
        "protocol": "iqs.observation-provenance-check/1.0.0",
        "observations": len(results),
        "pass": sum(1 for r in results if r["result"] == "pass"),
        "fail": sum(1 for r in results if r["result"] == "fail"),
        "research_only": sum(1 for r in results if r["result"] == "research_only"),
        "receipt_missing": sum(1 for r in results if r["result"] == "receipt_missing"),
        "results": results,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.html:
        rows = "".join(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                r["question_id"], r["result"], r["search_status"] or "",
                ", ".join(r["missing"]) or "-",
            )
            for r in results
        )
        args.html.write_text(
            "<!doctype html><meta charset='utf-8'><title>observation provenance</title>"
            "<h1>Observation provenance check</h1>"
            f"<p>observations {document['observations']} · pass {document['pass']} · fail {document['fail']} "
            f"· research_only {document['research_only']}</p>"
            "<table border='1' cellpadding='4'><tr><th>question</th><th>result</th><th>search_status</th><th>missing urls</th></tr>"
            + rows + "</table>",
            encoding="utf-8",
        )
    print(json.dumps({k: document[k] for k in ("observations", "pass", "fail", "research_only", "receipt_missing")}))


if __name__ == "__main__":
    main()
