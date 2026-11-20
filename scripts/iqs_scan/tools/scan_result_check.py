"""Verify a completed thin-scan output directory is actually usable.

Why this exists: a scan can exit 0 and still be worthless. On 2026-10-22 several
runs finished "successfully" with 24 answers, all insufficient_evidence, because
credentials were missing, evidence was truncated, or the reasoning budget was
exhausted. Exit codes did not reveal any of it. This checker inspects the artifacts
and reports whether the run carries real, citable answers.

A run can also answer only part of its frozen bank. Counting the answers that
are present says nothing about the questions that are not: the report therefore
compares the answers with the bank's own question count and names the coverage
``complete`` / ``partial`` / ``unknown``. A partial run is honest data, but it
is never a usable full result.

Usage:
    python -B -X utf8 scripts/scan_result_check.py --run <dir>
Exit codes: 0 = usable, 1 = completed but carries no scored answers or only
part of its bank, 2 = unusable.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path

from ..workbench import dashboard_company_feedback as feedback

REQUIRED_FILES = ("answers.json", "run-log.json", "index.html")
RUNS_ROOT_ENV = "IQS_FEEDBACK_RUNS_ROOT"
REFERENCE_PREFIX = "iqs:scan/runs/"
COVERAGE_ISSUE = "iqs-scan-result-partial-reported-complete"
VERSION = "iqs-scan-check/1"


@dataclass(frozen=True)
class CheckRead:
    report: dict
    source_sha256: str | None = None
    search_cost_micros: int | None = None


def _bank_question_count(document: dict) -> int | None:
    """The frozen bank's own question count, when the run records one."""
    for holder in (document.get("bank"), (document.get("meta") or {}).get("bank")):
        if not isinstance(holder, dict):
            continue
        count = holder.get("question_count")
        if type(count) is int and count > 0:
            return count
    return None


def _declared_missing(document: dict) -> list[str] | None:
    missing = document.get("missing_question_ids")
    if not isinstance(missing, list):
        return None
    return [item for item in missing if isinstance(item, str) and item]


def _coverage(document: dict, answered: int) -> tuple[str, int | None, list[str] | None, int | None]:
    """Compare the answers present with the bank this run was composed from.

    Returns ``(verdict, manifest_question_count, missing_ids, missing_count)``.
    Without a bank count the checker cannot tell a short run from a small bank,
    so the coverage stays ``unknown`` instead of being assumed complete. A
    document that merely declares "nothing missing" is not proof either: only a
    count can close the question.
    """
    manifest_count = _bank_question_count(document)
    declared = _declared_missing(document)
    if manifest_count is None:
        if declared:
            # Something is missing, but the total is unknown.
            return "partial", None, declared, len(declared)
        return "unknown", None, declared, None
    if declared is not None:
        missing_count = len(declared)
        if answered + missing_count != manifest_count:
            # The declaration and the answers disagree: report what is provable.
            missing_count = max(manifest_count - answered, missing_count)
        return ("partial" if missing_count else "complete"), manifest_count, declared, missing_count
    missing_count = max(manifest_count - answered, 0)
    return ("partial" if missing_count else "complete"), manifest_count, None, missing_count


def check(run_dir: Path) -> dict:
    return inspect_run(run_dir).report


def inspect_run(run_dir: Path) -> CheckRead:
    """Inspect and identify the exact saved answers without re-running the scan."""
    report: dict = {"run_dir": str(run_dir), "problems": [], "warnings": []}

    missing = [name for name in REQUIRED_FILES if not (run_dir / name).is_file()]
    if missing:
        report["problems"].append("missing artifacts: " + ", ".join(missing))
        report["ok"] = False
        report["usable"] = False
        return CheckRead(report)

    answers_bytes = (run_dir / "answers.json").read_bytes()
    answers_doc = json.loads(answers_bytes.decode("utf-8"))
    answers = answers_doc.get("answers") or []
    meta = answers_doc.get("meta") or {}
    report["question_count"] = len(answers)
    report["scored"] = sum(1 for a in answers if a.get("status") == "scored")
    report["insufficient"] = sum(1 for a in answers if a.get("status") == "insufficient_evidence")
    report["model_calls"] = meta.get("calls")
    report["searches"] = meta.get("searches")
    report["importable"] = answers_doc.get("importable")
    report["provenance"] = answers_doc.get("provenance")

    verdict, manifest_count, missing_ids, missing_count = _coverage(answers_doc, len(answers))
    report["coverage"] = verdict
    report["manifest_question_count"] = manifest_count
    report["missing_question_ids"] = missing_ids
    report["missing_question_count"] = missing_count

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

    # A short run is honest data; presenting it as a full result is not.
    if verdict == "partial" and missing_count:
        report["warnings"].append(
            f"run covers {len(answers)} of {manifest_count} frozen questions"
            if manifest_count is not None else
            f"run is missing {missing_count} frozen questions")
    elif verdict == "unknown":
        report["warnings"].append("the bank question count is not recorded; coverage is unknown")

    report["ok"] = not report["problems"]
    report["usable"] = report["ok"] and report["scored"] > 0 and verdict != "partial"
    recorded = meta.get("cost_micros")
    search_cost_micros = recorded if type(recorded) is int and recorded >= 0 else None
    return CheckRead(report, sha256(answers_bytes).hexdigest(), search_cost_micros)


def _observe(run_dir: Path, checked: CheckRead, previous: Path | None) -> None:
    context = feedback.context_from_env(version=VERSION)
    if context is None or not checked.source_sha256:
        return
    try:
        root = Path(os.environ.get(RUNS_ROOT_ENV) or "runs").resolve()
        run_id = run_dir.resolve().relative_to(root).as_posix()
        native = checked.report
        expected = {"partial": "partial-marked", "complete": "complete-marked", "unknown": "bank-count-available"}[
            native["coverage"]
        ]
        row = {
            "schema_version": feedback.SCHEMA_VERSION, "owner": feedback.OWNER, "origin_owner": feedback.OWNER,
            "run_id": run_id, "attempt_id": os.environ.get(feedback.ENV_ATTEMPT_ID) or "scan-result-check",
            "step_id": f"scan-result/{run_id}", "check_id": "coverage-claim", "expected": expected,
            "actual": expected if native["coverage"] != "unknown" else "unknown",
            "disposition": "unknown" if native["coverage"] == "unknown" else "expected",
            "version": VERSION, "evidence_ref": f"{REFERENCE_PREFIX}{run_id}@{checked.source_sha256}",
        }
        if previous is not None:
            archived_bytes = previous.read_bytes()
            archived = json.loads(archived_bytes.decode("utf-8"))
            matching_counts = all(archived.get(field) == native[field] for field in ("question_count", "scored"))
            if (
                native["coverage"] == "partial" and native["ok"] and matching_counts
                and archived.get("ok") is True and archived.get("usable") is True
            ):
                row.update(actual="complete-claimed", disposition="deviation", issue_key=COVERAGE_ISSUE,
                           details_ref=f"iqs:scan-check-before/{sha256(archived_bytes).hexdigest()}")
        feedback.emit(context, [row])
    except (OSError, ValueError, AttributeError, RuntimeError, RecursionError) as error:
        feedback.diagnose(error)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether a thin-scan run carries usable answers.")
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--previous-check", type=Path, help="Compare an archived check for opt-in local feedback.")
    args = parser.parse_args()
    if not args.run.is_dir():
        print(json.dumps({"ok": False, "problems": ["run directory not found"]}, ensure_ascii=False))
        return 2
    checked = inspect_run(args.run)
    report = checked.report
    _observe(args.run, checked, args.previous_check)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        return 2
    return 0 if report["usable"] else 1
