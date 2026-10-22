"""Summarise a completed bank scan: score distribution, evidence quality, gaps.

Complements scan_result_check.py (which answers "is this usable?"). This answers
"what did we actually get?" — per-module scores, evidence density, counterevidence
presence, and which questions produced no answer and why.

Usage:
    python -B -X utf8 scripts/scan_summary.py --run <dir> [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def summarise(run_dir: Path) -> dict:
    document = json.loads((run_dir / "answers.json").read_text(encoding="utf-8"))
    answers = document.get("answers") or []
    meta = document.get("meta") or {}
    summary = document.get("summary") or {}

    scored = [a for a in answers if a.get("status") == "scored"]
    insufficient = [a for a in answers if a.get("status") == "insufficient_evidence"]

    scores = [a["score"] for a in scored if isinstance(a.get("score"), int)]
    by_module: dict[str, dict] = defaultdict(lambda: {"scored": 0, "total": 0, "scores": []})
    for answer in answers:
        module = answer.get("module_id") or "unknown"
        by_module[module]["total"] += 1
        if answer.get("status") == "scored" and isinstance(answer.get("score"), int):
            by_module[module]["scored"] += 1
            by_module[module]["scores"].append(answer["score"])

    modules = {}
    for module, stats in sorted(by_module.items()):
        values = stats["scores"]
        modules[module] = {
            "total": stats["total"],
            "scored": stats["scored"],
            "mean": round(sum(values) / len(values), 2) if values else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        }

    evidence_counts = [len(a.get("evidence") or []) for a in scored]
    with_counter = sum(1 for a in scored if a.get("counterevidence"))
    reasons = Counter()
    for answer in insufficient:
        reasons[(answer.get("summary") or "").strip()[:60] or "<empty>"] += 1

    return {
        "run_dir": str(run_dir),
        "company": document.get("company"),
        "questions": len(answers),
        "scored": len(scored),
        "insufficient": len(insufficient),
        "coverage_pct": round(100 * len(scored) / len(answers), 1) if answers else 0.0,
        "mean_score": round(sum(scores) / len(scores), 2) if scores else None,
        "score_min": min(scores) if scores else None,
        "score_max": max(scores) if scores else None,
        "score_distribution": dict(sorted(Counter(scores).items())),
        "core": summary,
        "by_module": modules,
        "evidence": {
            "answers_with_evidence": sum(1 for c in evidence_counts if c > 0),
            "mean_urls_per_scored": round(sum(evidence_counts) / len(evidence_counts), 2)
            if evidence_counts else 0.0,
            "max_urls": max(evidence_counts) if evidence_counts else 0,
            "with_counterevidence": with_counter,
        },
        "model_calls": meta.get("calls"),
        "searches": meta.get("searches"),
        "search_cost_usd": round((meta.get("cost_micros") or 0) / 1_000_000, 4),
        "insufficient_reasons": dict(reasons.most_common(5)),
    }


def render(report: dict) -> str:
    lines = [
        f"公司: {report['company']}",
        f"题目: {report['questions']}  有分: {report['scored']}  "
        f"证据不足: {report['insufficient']}  覆盖率: {report['coverage_pct']}%",
        f"分数: mean={report['mean_score']} min={report['score_min']} max={report['score_max']}",
        f"分布: {report['score_distribution']}",
        f"调用: 模型 {report['model_calls']} 次 / 搜索 {report['searches']} 次 / "
        f"搜索成本 ${report['search_cost_usd']}",
        "",
        "按模块:",
    ]
    for module, stats in report["by_module"].items():
        lines.append(f"  {module:12} {stats['scored']}/{stats['total']} 有分  "
                     f"mean={stats['mean']} range={stats['min']}-{stats['max']}")
    evidence = report["evidence"]
    lines += [
        "",
        f"证据: {evidence['answers_with_evidence']} 题带 URL，平均 "
        f"{evidence['mean_urls_per_scored']} 条/题，最多 {evidence['max_urls']} 条；"
        f"{evidence['with_counterevidence']} 题带反向证据",
    ]
    if report["insufficient_reasons"]:
        lines.append("")
        lines.append("证据不足原因:")
        for reason, count in report["insufficient_reasons"].items():
            lines.append(f"  [{count}] {reason}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarise a completed bank scan.")
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()
    if not (args.run / "answers.json").is_file():
        print(json.dumps({"error": "answers.json not found"}, ensure_ascii=False))
        return 2
    report = summarise(args.run)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
