"""Aggregate repeated thin-scan runs by per-question median."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=Path("runs"))
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    groups: dict[str, list[dict]] = {}
    for directory in sorted(args.runs.glob("thin-scan-*-2026-10-18")):
        answers = directory / "answers.json"
        if not answers.is_file():
            continue
        key = directory.name.replace("-retest-2026-10-18", "-2026-10-18")
        document = json.loads(answers.read_text(encoding="utf-8"))
        groups.setdefault(key, []).append(document)
    lines = ["# 重复扫描中位数汇总", "",
             "同一题多次运行取中位数；只在至少一次有分时计入。", ""]
    summary = []
    for key, documents in sorted(groups.items()):
        if len(documents) < 2:
            continue
        questions = {}
        for document in documents:
            for answer in document["answers"]:
                questions.setdefault(answer["question_id"], []).append(
                    answer["score"] if answer["status"] == "scored" else None)
        medians = []
        for values in questions.values():
            present = [v for v in values if v is not None]
            if present:
                medians.append(statistics.median(present))
        name = documents[0].get("company") or key
        total = max(len(document["answers"]) for document in documents)
        summary.append((name, len(documents), len(medians), total,
                        statistics.mean(medians) if medians else None))
    lines += ["| 公司 | 运行次数 | 有分题 | 中位数均值 |", "|---|---:|---:|---:|"]
    for name, runs, count, total, mean in summary:
        lines.append(f"| {name} | {runs} | {count}/{total} | "
                     f"{'-' if mean is None else f'{mean:.1f}'} |")
    lines += ["", "对比页仍按单次运行展示；中位数用于降低单次噪声。"]
    args.markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps([{"name": n, "runs": r, "answered": c, "total": t,
                       "mean": round(m, 2) if m else None} for n, r, c, t, m in summary], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
