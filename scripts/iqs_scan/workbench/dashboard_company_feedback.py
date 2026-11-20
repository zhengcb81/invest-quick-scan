"""Public observation projection for the IQS company result/history read.

Every row is one line of ``feedback-observation/1`` in the UTF-8 JSONL file the
process names through ``RESEARCH_FEEDBACK_OUT``. The output is optional: with
no variable set, no file is opened and the business response is byte-identical.
A failed write is reported on stderr only — the native exit code, the payload
and the billing state stay exactly as the owner contract says.

The rows describe checks this projection can make on its own public output. A
check that fails on the owner's own snapshot is attributed to that owner
(``owner=stockwiki``, ``origin_owner=invest-quick-scan``); a check that fails on
what this projection publishes is attributed here. They never carry a company
body, a credential, a physical path or a paid attempt.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..foundation.api import (
    FEEDBACK_ATTEMPT_ENV as ENV_ATTEMPT_ID,
    FEEDBACK_OUT_ENV as ENV_OUT,
    FEEDBACK_RUN_ENV as ENV_RUN_ID,
    FEEDBACK_SCHEMA as SCHEMA_VERSION,
    append_feedback,
    diagnose_feedback as diagnose,
    feedback_path,
)

OWNER = "invest-quick-scan"
OWNER_STOCKWIKI = "stockwiki"
DEFAULT_RUN_ID = "iqs-local"
DEFAULT_ATTEMPT_ID = "attempt-1"

DISPOSITIONS = frozenset({"expected", "deviation", "unknown"})

_STABLE_WORD = re.compile(r"^[a-z][a-z0-9_.:-]{0,63}$")
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
    path = feedback_path(environ)
    if path is None:
        return None
    return Context(
        out_path=path,
        run_id=_sanitize(environ.get(ENV_RUN_ID), DEFAULT_RUN_ID),
        attempt_id=_sanitize(environ.get(ENV_ATTEMPT_ID), DEFAULT_ATTEMPT_ID),
        version=_sanitize_reference(version),
    )


def _sanitize_reference(value: Any) -> str | None:
    if isinstance(value, str) and _REFERENCE.match(value):
        return value
    return None


def observations(envelope: dict[str, Any], *, read: str, receipts: Any = None,
                 run_id: str = DEFAULT_RUN_ID,
                 attempt_id: str = DEFAULT_ATTEMPT_ID,
                 version: str | None = None) -> list[dict[str, Any]]:
    """Project the checks of one public read as ``feedback-observation/1`` rows."""
    entity_id = envelope.get("entity_id") or "unknown"
    coverage = envelope.get("coverage")
    result = envelope.get("company_result")
    reason = envelope.get("reason_code")
    result_id = result.get("result_id") if isinstance(result, dict) else None
    base = {
        "schema_version": SCHEMA_VERSION,
        "origin_owner": OWNER,
        "run_id": _sanitize(run_id, DEFAULT_RUN_ID),
        "attempt_id": _sanitize(attempt_id, DEFAULT_ATTEMPT_ID),
        "step_id": f"company-{read}/{entity_id}",
        "evidence_ref": f"iqs:company/{entity_id}/{result_id or reason or 'page'}",
        "version": (_sanitize_reference(version)
                    or _sanitize_reference(envelope.get("projection_version"))
                    or "company_assessment/unknown"),
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

    if read == "history":
        _history_checks(add, coverage)
        return rows

    absent = result is None
    if absent or not isinstance(coverage, dict):
        for check_id, expected in (("coverage-claim", "claim-matches-refs"),
                                   ("scale-lineage", "scales-addressable"),
                                   ("question-status", "statuses-published"),
                                   ("missing-questions", "missing-kept"),
                                   ("release-binding", "refs-bind-frozen-questions")):
            add(check_id, expected, "no-result", disposition="unknown")
    else:
        # 1. The owner's completeness claim against the references it binds.
        if coverage.get("claim_matches_refs") is False:
            add("coverage-claim", "claim-matches-refs", "complete-claimed",
                owner=OWNER_STOCKWIKI,
                issue_key="stockwiki-company-result-completeness-claim")
        else:
            add("coverage-claim", "claim-matches-refs", "claim-matches-refs")

        # 2. Every scale the snapshot declares is carried by a group, and every
        #    group keeps its own rubric. An honestly empty group is a legal
        #    partial result, not a lost scale: it is disclosed, not blamed.
        if (coverage.get("group_issue") is not None
                or coverage.get("group_mismatch_question_ids")
                or coverage.get("missing_scale_versions")
                or coverage.get("undeclared_scale_versions")):
            add("scale-lineage", "scales-addressable", "scale-without-group",
                owner=OWNER_STOCKWIKI,
                issue_key="stockwiki-company-result-scale-lineage")
        else:
            add("scale-lineage", "scales-addressable", "scales-addressable")

        # 3. Every frozen question carries a status in the projection.
        if _statuses_missing(coverage, receipts):
            add("question-status", "statuses-published", "statuses-missing",
                issue_key="iqs-company-result-question-status-missing")
        else:
            add("question-status", "statuses-published", "statuses-published")

        # 4. A gap the owner declared is kept, not reduced away.
        if _declared_gaps_dropped(coverage):
            add("missing-questions", "missing-kept", "missing-dropped",
                issue_key="iqs-company-result-missing-questions-dropped")
        else:
            add("missing-questions", "missing-kept", "missing-kept")

        # 5. Every bound reference names a question of the frozen release.
        if coverage.get("unexpected_question_ids"):
            add("release-binding", "refs-bind-frozen-questions",
                "refs-outside-release", owner=OWNER_STOCKWIKI,
                issue_key="stockwiki-company-result-unexpected-questions")
        else:
            add("release-binding", "refs-bind-frozen-questions",
                "refs-bind-frozen-questions")

    # 6. An absent result keeps the owner's named reason.
    if not absent:
        add("owner-absence", "reason-named", "result-present", disposition="expected")
    elif isinstance(reason, str) and reason.strip():
        add("owner-absence", "reason-named", "reason-named")
    else:
        add("owner-absence", "reason-named", "reason-missing",
            issue_key="iqs-company-result-absence-unreasoned")
    return rows


def _history_checks(add, coverage: Any) -> None:
    """A bounded page carries counts only; it must still say which item is short."""
    if not isinstance(coverage, dict) or not isinstance(coverage.get("items"), list):
        add("history-coverage", "items-marked", "no-coverage", disposition="unknown")
        return
    items = coverage["items"]
    if not items:
        add("history-coverage", "items-marked", "no-items", disposition="unknown")
    elif any(not isinstance(item, dict) or not item.get("verdict")
             or item.get("verdict") == "unknown" for item in items):
        add("history-coverage", "items-marked", "items-unmarked",
            issue_key="iqs-company-history-coverage-unmarked")
    else:
        add("history-coverage", "items-marked", "items-marked")


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
    return append_feedback(context.out_path, rows)


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
    except Exception as error:  # noqa: BLE001 - the observation plane is isolated
        # Whatever goes wrong here is a tracking fault, never a business one.
        diagnose(error)
        return False
    return emit(context, rows)
