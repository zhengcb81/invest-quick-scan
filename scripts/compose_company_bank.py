"""Compose a versioned company question bank and enforce coverage.

Wraps scripts/question_sets.py compose, adds the operating/pre-revenue industry
coverage gate, and prints the resulting bank identity so thin scans can bind it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import question_sets  # noqa: E402


def coverage_gap(profile: dict) -> list[str]:
    company_type = profile.get("company_type")
    industries = [x for x in (profile.get("industry_modules") or []) if isinstance(x, str)]
    if company_type in {"operating", "pre_revenue"} and not industries:
        return ["industry_unresolved_for_" + str(company_type)]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--mode", choices=["quick", "full"], default="quick")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--module-package-id")
    parser.add_argument("--max-questions", type=int,
                        help="optional dispatch budget; never trims mandatory basic coverage")
    parser.add_argument("--now-utc", required=True)
    parser.add_argument("--allow-coverage-gap", action="store_true")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8-sig"))
    gaps = coverage_gap(profile)
    if gaps and not args.allow_coverage_gap:
        print(json.dumps({"status": "rejected", "coverage_gaps": gaps,
                          "hint": "set --allow-coverage-gap only with an explicit reason"}, ensure_ascii=False))
        return 2
    question_sets.compose(
        profile, args.mode, args.out_dir, package_id=args.module_package_id,
        max_questions=args.max_questions, now_utc=args.now_utc,
    )
    manifest = json.loads((Path(args.out_dir) / "manifest.json").read_text(encoding="utf-8"))
    questions = manifest["questions"]
    core = [q for q in questions if q.get("comparison_role") == "core"]
    context = [q for q in questions if q.get("comparison_role") != "core"]
    print(json.dumps({
        "status": "composed",
        "manifest": str(Path(args.out_dir) / "manifest.json"),
        "package_id": manifest.get("module_package_id"),
        "release_id": manifest.get("module_release_id"),
        "modules": manifest.get("modules"),
        "questions": len(questions),
        "core": len(core),
        "context": len(context),
        "coverage_gaps": gaps,
        "mode": args.mode,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
