"""Public observation projection for the IQS company result/history read.

Every row is one line of ``feedback-observation/1`` in the UTF-8 JSONL file the
process names through ``RESEARCH_FEEDBACK_OUT``. The output is optional: with
no variable set, no file is opened and the business response is byte-identical.
A failed write is reported on stderr only — the native exit code, the payload
and the billing state stay exactly as the owner contract says.

The rows describe checks this projection can make on its own public output:
whether the owner's completeness claim agrees with the references it binds,
whether every frozen scale group is still addressable, whether each question
carries a status, whether a declared gap survived, and whether an absent result
kept its named reason. They never carry a company body, a credential, a
physical path or a paid attempt.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "feedback-observation/1"
OWNER = "invest-quick-scan"
ENV_OUT = "RESEARCH_FEEDBACK_OUT"
ENV_RUN_ID = "RESEARCH_FEEDBACK_RUN_ID"
ENV_ATTEMPT_ID = "RESEARCH_FEEDBACK_ATTEMPT_ID"
DEFAULT_RUN_ID = "iqs-local"
DEFAULT_ATTEMPT_ID = "attempt-1"

DISPOSITIONS = frozenset({"expected", "deviation", "unknown"})

_STABLE_WORD = re.compile(r"^[a-z][a-z0-9_.:-]{0,63}$")
_TOKEN = re.compile(r"^[A-Za-z0-9_.:/-]{1,200}$")
_REFERENCE = re.compile(r"^[A-Za-z0-9_.:/@+-]{1,200}$")

_FIELD_ORDER = ("schema_version", "owner", "origin_owner", "run_id", "attempt_id",
                "step_id", "parent_step_id", "check_id", "expected", "actual",
                "disposition", "issue_key", "evidence_ref", "details_ref", "version")


@dataclass(frozen=True)
class Context:
    """Where one process writes its observations, and under which identity."""

    out_path: Path
    run_id: str
    attempt_id: str
    version: str | None


def _sanitize(value: Any, default: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "")).strip("-")
    return text[:120] or default


def context_from_env(environ: dict[str, str] | None = None,
                     version: str | None = None) -> Context | None:
    """Read the observation context; ``None`` means observation is switched off."""
    environ = os.environ if environ is None else environ
    raw = environ.get(ENV_OUT)
    if not isinstance(raw, str) or not raw.strip():
        return None
    return Context(
        out_path=Path(raw).expanduser(),
        run_id=_sanitize(environ.get(ENV_RUN_ID), DEFAULT_RUN_ID),
        attempt_id=_sanitize(environ.get(ENV_ATTEMPT_ID), DEFAULT_ATTEMPT_ID),
        version=_sanitize_reference(version),
    )


def _sanitize_reference(value: Any) -> str | None:
    if isinstance(value, str) and _REFERENCE.match(value):
        return value
    return None


def diagnose(error: BaseException) -> None:
    """Report an observation-plane fault on stderr, never in the business output."""
    if isinstance(error, OSError):
        message = f"feedback observation write failed ({error.filename or 'output'}): {error.strerror}"
    else:
        message = f"feedback observation skipped ({error.__class__.__name__})"
    try:
        print(message[:300], file=sys.stderr)
    except (OSError, ValueError):
        pass


def observations(envelope: dict[str, Any], *, read: str, receipts: Any = None,
                 run_id: str = DEFAULT_RUN_ID,
                 attempt_id: str = DEFAULT_ATTEMPT_ID,
                 version: str | None = None) -> list[dict[str, Any]]:
    """Project the checks of one public read as ``feedback-observation/1`` rows."""
    entity_id = envelope.get("entity_id") or "unknown"
    result = envelope.get("company_result")
    coverage = envelope.get("coverage")
    reason = envelope.get("reason_code")
    result_id = result.get("result_id") if isinstance(result, dict) else None
    resolved_version = _sanitize_reference(version) or _sanitize_reference(
        envelope.get("projection_version")) or "company_assessment/unknown"
    base = {
        "schema_version": SCHEMA_VERSION,
        "origin_owner": OWNER,
        "run_id": _sanitize(run_id, DEFAULT_RUN_ID),
        "attempt_id": _sanitize(attempt_id, DEFAULT_ATTEMPT_ID),
        "step_id": f"company-{read}/{entity_id}",
        "evidence_ref": f"iqs:company/{entity_id}/{result_id or reason or 'absent'}",
        "version": resolved_version,
    }
    rows: list[dict[str, Any]] = []

    def add(check_id, expected, actual, *, owner=OWNER, disposition=None,
            issue_key=None):
        row = {
            **base,
            "owner": owner,
            "check_id": check_id,
            "expected": _stable_word("expected", expected),
            "actual": _stable_word("actual", actual),
            "disposition": _disposition(expected, actual, disposition),
        }
        if issue_key is not None:
            row["issue_key"] = _stable_word("issue_key", issue_key)
        rows.append({key: row[key] for key in _FIELD_ORDER if key in row})

    absent = result is None

    # 1. The owner's completeness claim against the references it binds.
    if absent:
        add("coverage-claim", "claim-matches-refs", "no-result", disposition="unknown")
    elif not isinstance(coverage, dict):
        add("coverage-claim", "claim-matches-refs", "coverage-absent",
            disposition="unknown")
    elif coverage.get("claim_matches_refs") is False:
        add("coverage-claim", "claim-matches-refs", "complete-claimed",
            owner="stockwiki", issue_key="stockwiki-company-result-completeness-claim")
    else:
        add("coverage-claim", "claim-matches-refs", "claim-matches-refs")

    # 2. Every frozen scale group stays addressable with its own rubric/role.
    if absent or not isinstance(coverage, dict):
        add("multi-group-lineage", "no-group-loss", "no-result", disposition="unknown")
    elif (coverage.get("group_issue") is not None
            or coverage.get("group_mismatch_question_ids")
            or any(group.get("empty") for group in coverage.get("groups") or ())):
        add("multi-group-lineage", "no-group-loss", "group-lost",
            issue_key="iqs-company-result-group-lost")
    else:
        add("multi-group-lineage", "no-group-loss", "no-group-loss")

    # 3. Every question the release froze carries a status in the projection.
    if absent or not isinstance(coverage, dict):
        add("question-status", "statuses-published", "no-result", disposition="unknown")
    elif _statuses_missing(coverage, receipts):
        add("question-status", "statuses-published", "statuses-missing",
            issue_key="iqs-company-result-question-status-missing")
    else:
        add("question-status", "statuses-published", "statuses-published")

    # 4. A gap the owner declared is kept, not reduced away.
    if absent or not isinstance(coverage, dict):
        add("missing-questions", "missing-kept", "no-result", disposition="unknown")
    elif _declared_gaps_dropped(coverage):
        add("missing-questions", "missing-kept", "missing-dropped",
            issue_key="iqs-company-result-missing-questions-dropped")
    else:
        add("missing-questions", "missing-kept", "missing-kept")

    # 5. An absent result keeps the owner's named reason.
    if not absent:
        add("owner-absence", "reason-named", "result-present", disposition="expected")
    elif isinstance(reason, str) and reason.strip():
        add("owner-absence", "reason-named", "reason-named")
    else:
        add("owner-absence", "reason-named", "reason-missing",
            issue_key="iqs-company-result-absence-unreasoned")
    return rows


def _statuses_missing(coverage: dict[str, Any], receipts: Any) -> bool:
    questions = coverage.get("questions")
    if not isinstance(questions, list):
        return True
    manifest_count = coverage.get("manifest_question_count")
    if type(manifest_count) is int and len(questions) != manifest_count:
        return True
    if any(not isinstance(question, dict) or not question.get("status")
           for question in questions):
        return True
    # A receipt exists, so the projection had evidence and must not fall back
    # to "unknown" for that question.
    supplied = (receipts or {}).get("questions") if isinstance(receipts, dict) else None
    if isinstance(supplied, dict):
        unclassified = set(coverage.get("unclassified_question_ids") or ())
        if unclassified & set(supplied):
            return True
    return False


def _declared_gaps_dropped(coverage: dict[str, Any]) -> bool:
    declared = coverage.get("declared")
    if not isinstance(declared, dict):
        return False
    declared_missing = declared.get("missing_question_ids")
    if not isinstance(declared_missing, list) or not declared_missing:
        return False
    published = coverage.get("missing_question_ids")
    if not isinstance(published, list):
        return True
    return bool(set(declared_missing) - set(published))


def _stable_word(name: str, value: Any) -> str:
    if not isinstance(value, str) or not _STABLE_WORD.match(value):
        raise ValueError(f"{name} must be a stable result word")
    return value


def _disposition(expected: str, actual: str, declared: str | None) -> str:
    if declared is not None:
        if declared not in DISPOSITIONS:
            raise ValueError("disposition is not one of the allowed values")
        return declared
    if expected == actual:
        return "expected"
    if "unknown" in (expected, actual) or "no-result" in (expected, actual):
        return "unknown"
    return "deviation"


def emit(context: Context, rows: list[dict[str, Any]]) -> bool:
    """Append the rows to the process-specific file; failures never raise."""
    if not isinstance(context, Context):
        return False
    try:
        payload = "".join(json.dumps(row, ensure_ascii=False, allow_nan=False,
                                     separators=(",", ":")) + "\n" for row in rows)
        context.out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(context.out_path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except (OSError, TypeError, ValueError) as error:
        diagnose(error)
        return False
    return True


def observe(envelope: dict[str, Any], *, read: str, receipts: Any = None,
            environ: dict[str, str] | None = None,
            version: str | None = None) -> bool:
    """Emit one read's observations when the process asked for them."""
    context = context_from_env(environ, version=version)
    if context is None:
        return False
    try:
        rows = observations(envelope, read=read, receipts=receipts,
                            run_id=context.run_id, attempt_id=context.attempt_id,
                            version=context.version)
    except (TypeError, ValueError, KeyError, AttributeError) as error:
        diagnose(error)
        return False
    return emit(context, rows)
