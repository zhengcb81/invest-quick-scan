"""Verify a completed thin-scan output directory is actually usable.

Why this exists: a scan can exit 0 and still be worthless. On 2026-10-22 several
runs finished "successfully" with 24 answers, all insufficient_evidence, because
credentials were missing, evidence was truncated, or the reasoning budget was
exhausted. Exit codes did not reveal any of it. This checker inspects the artifacts
and reports whether the run carries real, citable answers.

Usage:
    python -B -X utf8 scripts/scan_result_check.py --run <dir>
Exit codes: 0 = usable, 1 = completed but carries no scored answers, 2 = unusable.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_FILES = ("answers.json", "run-log.json", "index.html")


def check(run_dir: Path) -> dict:
    report: dict = {"run_dir": str(run_dir), "problems": [], "warnings": []}

    missing = [name for name in REQUIRED_FILES if not (run_dir / name).is_file()]
    if missing:
        report["problems"].append("missing artifacts: " + ", ".join(missing))
        report["ok"] = False
        report["usable"] = False
        return report

    answers_doc = json.loads((run_dir / "answers.json").read_text(encoding="utf-8"))
    answers = answers_doc.get("answers") or []
    meta = answers_doc.get("meta") or {}
    report["question_count"] = len(answers)
    report["scored"] = sum(1 for a in answers if a.get("status") == "scored")
    report["insufficient"] = sum(1 for a in answers if a.get("status") == "insufficient_evidence")
    report["model_calls"] = meta.get("calls")
    report["searches"] = meta.get("searches")
    report["importable"] = answers_doc.get("importable")
    report["provenance"] = answers_doc.get("provenance")

    if not answers:
        report["problems"].append("answers.json contains no answers")

    # A scored answer must carry a valid score and at least one evidence URL.
    for answer in answers:
        if answer.get("status") != "scored":
            continue
        score = answer.get("score")
        if not isinstance(score, int) or not 1 <= score <= 10:
            report["problems"].append(f"{answer.get('question_id')}: scored with an invalid score")
        if not answer.get("evidence"):
            report["problems"].append(f"{answer.get('question_id')}: scored without evidence")

    # Problems on every question mean the pipeline failed, not that evidence was thin.
    error_kinds: dict[str, int] = {}
    for answer in answers:
        for problem in answer.get("problems") or []:
            kind = str(problem).split(":")[0]
            error_kinds[kind] = error_kinds.get(kind, 0) + 1
    report["problem_kinds"] = error_kinds
    if answers and len(error_kinds) and all(
            count == len(answers) for count in error_kinds.values()):
        report["problems"].append(
            "every question reported the same failure: " + ", ".join(sorted(error_kinds)))

    # Zero model calls with searches performed means the model stage never ran.
    if meta.get("calls") == 0 and (meta.get("searches") or 0) > 0:
        report["problems"].append("searches ran but no model calls were made")

    # A bank-mode run must keep its manifest identity.
    if answers_doc.get("importable") is True and not (answers_doc.get("bank") or {}).get("package_id"):
        report["problems"].append("importable run lacks a bank package identity")

    if report["scored"] == 0 and not report["problems"]:
        report["warnings"].append("no question reached a scored answer")

    report["ok"] = not report["problems"]
    report["usable"] = report["ok"] and report["scored"] > 0
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether a thin-scan run carries usable answers.")
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    if not args.run.is_dir():
        print(json.dumps({"ok": False, "problems": ["run directory not found"]}, ensure_ascii=False))
        return 2
    report = check(args.run)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        return 2
    return 0 if report["usable"] else 1


if __name__ == "__main__":
    sys.exit(main())
