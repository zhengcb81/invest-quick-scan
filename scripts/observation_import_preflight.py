"""Preflight for search-backed 1.2.0 observation packages before owner import.

Offline, read-only. Rejects packages that the vendor preview would later refuse:
score answers must be schema-consistent, external citations must be non-empty and
self-consistent (src_<sha256(url)[:16]>), and executed-search packages must carry
real attempt hashes and a receipt that exists in the work ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages", nargs="+", type=Path)
    parser.add_argument("--work", type=Path, default=Path("runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite"))
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    work = sqlite3.connect(args.work.resolve().as_uri() + "?mode=ro", uri=True)
    results = []
    for path in args.packages:
        package = json.loads(path.read_text(encoding="utf-8"))
        item = package["items"][0]
        obs = item["observation"]
        answer = obs.get("answer") or {}
        execution = obs.get("execution") or {}
        problems = []
        if obs.get("schema_version") != "1.2.0":
            problems.append("schema_not_1_2_0")
        if obs.get("task_mode") != "primary":
            problems.append("task_mode_not_primary")
        status, score = answer.get("status"), answer.get("score")
        if status == "scored" and not (isinstance(score, int) and 1 <= score <= 10):
            problems.append("scored_score_invalid")
        if status != "scored" and score is not None:
            problems.append("score_without_scored")
        evidence = [e for e in (answer.get("evidence") or []) if isinstance(e, dict)]
        if not evidence:
            problems.append("evidence_empty")
        for entry in evidence:
            url, eid = entry.get("url"), entry.get("id")
            if not (isinstance(url, str) and url.startswith("https://")):
                problems.append("evidence_url_invalid")
            elif eid != "src_" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]:
                problems.append("evidence_id_not_canonical")
        if execution.get("search_status") == "executed":
            for key in ("prompt_sha256", "request_payload_sha256"):
                value = execution.get(key)
                if not (isinstance(value, str) and len(value) == 64):
                    problems.append("execution_" + key + "_missing")
            receipt = execution.get("search_receipt_id")
            if not receipt:
                problems.append("search_receipt_missing")
            else:
                row = work.execute("SELECT 1 FROM quick_scan_external_operation WHERE operation_id=?", (receipt,)).fetchone()
                if row is None:
                    problems.append("search_receipt_not_found")
        results.append({"package": str(path), "observation_id": obs.get("observation_id"), "question_id": obs.get("question_id"), "result": "pass" if not problems else "fail", "problems": problems})
    document = {"protocol": "iqs.observation-import-preflight/1.0.0", "packages": len(results), "pass": sum(1 for r in results if r["result"] == "pass"), "fail": sum(1 for r in results if r["result"] == "fail"), "results": results}
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: document[k] for k in ("packages", "pass", "fail")}))
    for item in results:
        print(item["result"], Path(item["package"]).name, item["problems"])
    return 0 if document["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
