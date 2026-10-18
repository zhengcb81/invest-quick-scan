"""Compare two thin-scan runs of the same company (test-retest stability)."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a", type=Path, required=True)
    parser.add_argument("--b", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    first = json.loads(args.a.read_text(encoding="utf-8"))
    second = json.loads(args.b.read_text(encoding="utf-8"))
    left = {a["question_id"]: a for a in first["answers"]}
    right = {b["question_id"]: b for b in second["answers"]}
    rows = []
    deltas = []
    both_scored = 0
    for qid in sorted(left):
        a, b = left[qid], right.get(qid, {})
        sa = a["score"] if a["status"] == "scored" else None
        sb = b.get("score") if b.get("status") == "scored" else None
        if sa is not None and sb is not None:
            both_scored += 1
            deltas.append(abs(sa - sb))
        rows.append((qid, sa, sb))
    same = sum(1 for s in deltas if s == 0)
    within_one = sum(1 for s in deltas if s <= 1)
    lines = ["# 同公司重复扫描（稳定性）", "",
             f"- 第一次有分：{sum(1 for a in left.values() if a['status'] == 'scored')}/24",
             f"- 第二次有分：{sum(1 for b in right.values() if b.get('status') == 'scored')}/24",
             f"- 两次都有分：{both_scored} 题",
             f"- 完全同分：{same}；相差 ≤1：{within_one}",
             f"- 平均绝对差：{statistics.mean(deltas):.2f}" if deltas else "- 无可比分数",
             "", "| 题 | 第一次 | 第二次 | 差 |", "|---|---:|---:|---:|"]
    for qid, sa, sb in rows:
        if sa is None and sb is None:
            continue
        delta = "-" if sa is None or sb is None else str(abs(sa - sb))
        lines.append(f"| {qid} | {'-' if sa is None else sa} | {'-' if sb is None else sb} | {delta} |")
    args.markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"both_scored": both_scored, "same": same, "within_one": within_one,
                      "mean_abs_delta": round(statistics.mean(deltas), 2) if deltas else None}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
