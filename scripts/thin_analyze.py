"""Summarize thin-scan answers across companies: coverage and dispersion by question."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    companies = []
    for directory in sorted(args.root.iterdir()):
        answers = directory / "answers.json"
        if answers.is_file():
            companies.append((directory.name, json.loads(answers.read_text(encoding="utf-8"))))
    names = {}
    for slug, document in companies:
        names[slug] = document.get("company") or slug
    by_question = {}
    for slug, document in companies:
        for answer in document["answers"]:
            by_question.setdefault(answer["question_id"], {"question": answer["question"], "scores": {},
                                                           "insufficient": []})["scores"][slug] = (
                answer["score"] if answer["status"] == "scored" else None)
    rows = []
    for qid, data in by_question.items():
        values = [v for v in data["scores"].values() if v is not None]
        mean = statistics.mean(values) if values else None
        spread = statistics.pstdev(values) if len(values) > 1 else 0.0
        rows.append((qid, data["question"], len(values), mean, spread, data["scores"]))
    lines = ["# 薄草稿逐题分析（8 家）", "",
             "只统计草稿结果；分数只覆盖有来源的题，不能当正式结论。", "",
             "## 覆盖率最低的题", "",
             "| 题 | 有分数 | 平均 | 题目 |", "|---|---:|---:|---|"]
    for qid, question, count, mean, spread, scores in sorted(rows, key=lambda r: (r[2], r[0])):
        if count <= 2:
            lines.append(f"| {qid} | {count}/{len(companies)} | {'-' if mean is None else f'{mean:.1f}'} | {question} |")
    lines += ["", "## 分差最大的题", "",
              "| 题 | 有分数 | 平均 | 标准差 | 题目 |", "|---|---:|---:|---:|---|"]
    for qid, question, count, mean, spread, scores in sorted(rows, key=lambda r: -r[4])[:10]:
        if count >= 2:
            lines.append(f"| {qid} | {count}/{len(companies)} | {mean:.1f} | {spread:.2f} | {question} |")
    lines += ["", "## 逐题明细", "",
              "| 题 | " + " | ".join(names[s] for s, _ in companies) + " |",
              "|---|" + "---:|" * len(companies)]
    for qid, question, count, mean, spread, scores in rows:
        cells = []
        for slug, _ in companies:
            value = scores.get(slug)
            cells.append("-" if value is None else str(value))
        lines.append(f"| {qid} | " + " | ".join(cells) + " |")
    args.markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    universal = [q for q in rows if q[2] <= 1]
    print(json.dumps({"companies": len(companies), "questions": len(rows),
                      "universal_insufficient": [q[0] for q in universal]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
