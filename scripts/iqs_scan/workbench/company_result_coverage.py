"""Per-question coverage and scale lineage derived from one public company result.

The StockWiki owner publishes one immutable snapshot: its own completeness
claim plus the observation references it binds. This module re-derives, from
that public evidence only, which frozen questions were actually observed, which
lineage group each belongs to, and what per-question state the evidence
supports.

Three rules shape it:

* a partial snapshot stays partial — the derived verdict never becomes
  ``complete`` while a frozen question has no bound observation, or while a
  scale the snapshot declares has no group to carry it;
* the owner's own claim is compared with its references instead of being
  trusted, so a contradiction is reported rather than smoothed over;
* an observation is the only evidence that a question was saved. A receipt
  saying "settled" without a bound observation is ``settled_unsaved``, never
  ``completed``.

Nothing here computes a score, re-ranks a question, re-issues a paid attempt or
writes to the owner store. A question whose fate the evidence cannot decide is
``unknown``, never guessed.
"""

from __future__ import annotations

from typing import Any

COVERAGE_PROTOCOL = "iqs.dashboard.company_coverage/1"
COVERAGE_VERSION = "1.1.0"
# The owner's own declaration for a result that carries scale lineage groups.
ASSESSMENT_PROTOCOL_V2 = "stockwiki.company_assessment/2"

# The four states this lane must keep apart, plus the honest "no evidence" one.
#   completed          an immutable observation is bound to the question
#   settled_unsaved    the attempt settled but no observation was persisted
#   provider_filtered  the provider refused the response (content filter)
#   provider_truncated the provider response was cut at its output bound
#   not_run            no attempt was dispatched for the question
#   unknown            the available evidence does not decide the state
QUESTION_STATUSES = ("completed", "settled_unsaved", "provider_filtered",
                     "provider_truncated", "not_run", "unknown")
COVERAGE_VERDICTS = ("complete", "partial", "unknown")


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _count(value: Any) -> int | None:
    if type(value) is int and value >= 0:
        return value
    return None


def _ids(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    identifiers = []
    for item in value:
        identifier = _text(item)
        if identifier is None:
            return None
        identifiers.append(identifier)
    return identifiers


def _read_groups(result: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, str | None]:
    """The owner's published lineage groups, or a named reason they are unreadable."""
    raw = result.get("lineage_groups")
    if raw is None:
        # A v2 snapshot without its groups is not a v1 snapshot: the scale
        # lineage it promised is missing, and that is a group loss.
        if _text(result.get("assessment_protocol")) == ASSESSMENT_PROTOCOL_V2:
            return None, "lineage-groups-missing"
        return None, None
    if not isinstance(raw, list) or not raw:
        return None, "lineage-groups-malformed"
    groups = []
    seen = set()
    for entry in raw:
        if not isinstance(entry, dict):
            return None, "lineage-groups-malformed"
        group_id = _text(entry.get("lineage_group_id"))
        rubric_version = _text(entry.get("rubric_version"))
        aggregation_role = _text(entry.get("aggregation_role"))
        question_ids = _ids(entry.get("question_ids"))
        if (group_id is None or rubric_version is None or aggregation_role is None
                or question_ids is None or group_id in seen):
            return None, "lineage-groups-malformed"
        seen.add(group_id)
        groups.append({
            "lineage_group_id": group_id,
            "rubric_version": rubric_version,
            "aggregation_role": aggregation_role,
            "question_ids": sorted(question_ids),
        })
    return groups, None


def _read_refs(result: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    raw = result.get("observation_refs")
    if not isinstance(raw, list):
        return [], []
    references = []
    malformed = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, dict) or _text(entry.get("question_id")) is None:
            malformed.append(str(index))
            continue
        references.append({
            "question_id": entry["question_id"],
            "observation_id": _text(entry.get("observation_id")),
            "lineage_group_id": _text(entry.get("lineage_group_id")),
            "aggregation_role": _text(entry.get("aggregation_role")),
        })
    return references, malformed


def _read_declared(result: dict[str, Any]) -> dict[str, Any]:
    raw = result.get("completeness")
    if not isinstance(raw, dict):
        return {"manifest_question_count": None, "observed_count": None,
                "missing_question_ids": None}
    return {
        "manifest_question_count": _count(raw.get("manifest_question_count")),
        "observed_count": _count(raw.get("observed_count")),
        "missing_question_ids": _ids(raw.get("missing_question_ids")),
    }


def _read_receipts(receipts: Any, known: set[str]) -> dict[str, dict[str, Any]]:
    """Validate the optional per-question receipt summary.

    A receipt naming a question this result does not contain is a join error,
    not something to drop: silently ignoring it would report a question as
    unobserved while its settled receipt sits right there.
    """
    if receipts is None:
        return {}
    if not isinstance(receipts, dict):
        raise ValueError("receipts must be an object")
    entries = receipts.get("questions")
    if not isinstance(entries, dict):
        raise ValueError("receipts.questions must be an object")
    normalized = {}
    for question_id, entry in entries.items():
        if question_id not in known:
            raise ValueError(f"receipt names an unknown question: {question_id}")
        if not isinstance(entry, dict):
            raise ValueError(f"receipt entry is not an object: {question_id}")
        status = entry.get("status")
        if status not in QUESTION_STATUSES:
            raise ValueError(f"receipt status is not a known question state: {question_id}")
        answer_state = entry.get("answer_state")
        normalized[question_id] = {
            "status": status,
            "answer_state": _text(answer_state),
        }
    return normalized


def derive_coverage(result: Any, *, receipts: Any = None) -> dict[str, Any] | None:
    """Derive the per-question coverage of one owner snapshot.

    Returns ``None`` for an absent result (the owner published a named reason
    instead of a snapshot): no coverage may be invented for it.
    """
    if result is None:
        return None
    if not isinstance(result, dict):
        raise ValueError("a company result must be an object")

    groups, group_issue = _read_groups(result)
    references, malformed_refs = _read_refs(result)
    declared = _read_declared(result)

    by_question: dict[str, dict[str, Any]] = {}
    duplicate_question_ids = []
    for reference in references:
        if reference["question_id"] in by_question:
            duplicate_question_ids.append(reference["question_id"])
            continue
        by_question[reference["question_id"]] = reference

    manifest_ids: list[str] | None = None
    group_by_question: dict[str, dict[str, Any]] = {}
    if groups is not None:
        manifest_ids = sorted({question_id for group in groups
                               for question_id in group["question_ids"]})
        for group in groups:
            for question_id in group["question_ids"]:
                group_by_question[question_id] = group

    known = set(by_question) | set(manifest_ids or ())
    normalized_receipts = _read_receipts(receipts, known)

    # A reference to a question the frozen release does not contain is not
    # coverage: it is counted separately so it can never inflate the result
    # into "complete", nor disappear silently.
    if manifest_ids is not None:
        unexpected = sorted(set(by_question) - set(manifest_ids))
        observed_ids = [question_id for question_id in by_question
                        if question_id in set(manifest_ids)]
        missing = sorted(set(manifest_ids) - set(by_question))
    else:
        unexpected = []
        observed_ids = sorted(by_question)
        missing = sorted(declared["missing_question_ids"] or [])

    manifest_count = (len(manifest_ids) if manifest_ids is not None
                      else declared["manifest_question_count"])
    observed_count = len(observed_ids)

    claim_matches_refs = _claim_matches(declared, manifest_count, observed_count, missing,
                                        manifest_ids is not None)

    published_scales = _scale_versions(result, groups)
    group_rubrics = {group["rubric_version"] for group in groups or []}
    missing_scale_versions = sorted(set(published_scales) - group_rubrics)
    undeclared_scale_versions = sorted(group_rubrics - set(published_scales))

    if group_issue is not None:
        basis = "lineage-groups-unreadable"
    elif manifest_ids is not None:
        basis = "lineage-groups"
    elif declared["manifest_question_count"] is not None:
        basis = "declared-completeness"
    else:
        basis = "references-only"

    if group_issue is not None:
        verdict = "unknown"
    elif missing or missing_scale_versions:
        verdict = "partial"
    elif claim_matches_refs is False:
        verdict = "partial"
    elif manifest_count is None:
        verdict = "unknown"
    elif observed_count < manifest_count:
        verdict = "partial"
    else:
        verdict = "complete"

    questions = _questions(manifest_ids, by_question, group_by_question,
                           normalized_receipts)
    status_counts: dict[str, int] = {}
    for question in questions:
        status_counts[question["status"]] = status_counts.get(question["status"], 0) + 1

    group_rows = []
    for group in groups or []:
        observed = [question_id for question_id in group["question_ids"]
                    if question_id in by_question]
        group_rows.append({
            "lineage_group_id": group["lineage_group_id"],
            "rubric_version": group["rubric_version"],
            "aggregation_role": group["aggregation_role"],
            "question_count": len(group["question_ids"]),
            "observed_count": len(observed),
            "question_ids": list(group["question_ids"]),
            "missing_question_ids": [question_id for question_id in group["question_ids"]
                                     if question_id not in by_question],
            "empty": not observed,
        })
    # Stable order: the published order of the groups is not part of the result.
    group_rows.sort(key=lambda row: (row["rubric_version"], row["aggregation_role"],
                                     row["lineage_group_id"]))

    group_ids = {group["lineage_group_id"] for group in group_rows}
    group_mismatch = sorted({
        reference["question_id"]
        for reference in references
        if group_ids and reference["lineage_group_id"] not in group_ids
    })

    return {
        "protocol": COVERAGE_PROTOCOL,
        "version": COVERAGE_VERSION,
        "result_id": _text(result.get("result_id")),
        "assessment_protocol": _text(result.get("assessment_protocol")),
        "basis": basis,
        "verdict": verdict,
        "claim_matches_refs": claim_matches_refs,
        "manifest_question_count": manifest_count,
        "observed_count": observed_count,
        "missing_question_ids": missing,
        "unexpected_question_ids": unexpected,
        "declared": declared,
        "scale_version": _text(result.get("scale_version")),
        "scale_versions": published_scales,
        "missing_scale_versions": missing_scale_versions,
        "undeclared_scale_versions": undeclared_scale_versions,
        "groups": group_rows,
        "questions": questions,
        "status_counts": dict(sorted(status_counts.items())),
        "unclassified_question_ids": [question["question_id"] for question in questions
                                       if question["status"] == "unknown"],
        "group_mismatch_question_ids": group_mismatch,
        "receipt_conflicts": _receipt_conflicts(normalized_receipts, by_question),
        "duplicate_question_ids": sorted(set(duplicate_question_ids)),
        "malformed_refs": malformed_refs,
        "group_issue": group_issue,
    }


def _receipt_conflicts(receipts: dict[str, dict[str, Any]],
                       by_question: dict[str, dict[str, Any]]) -> list[str]:
    """Questions whose receipt and bound observation disagree.

    Both directions matter: a receipt that says "never saved" for a question
    that does have an observation, and a receipt that says "completed" for a
    question with no observation at all (the settled-but-unsaved case).
    """
    conflicts = set()
    for question_id, receipt in receipts.items():
        saved = question_id in by_question
        if saved and receipt["status"] != "completed":
            conflicts.add(question_id)
        elif not saved and receipt["status"] == "completed":
            conflicts.add(question_id)
    return sorted(conflicts)


def _claim_matches(declared: dict[str, Any], manifest_count: int | None,
                   observed_count: int, missing: list[str],
                   ids_known: bool) -> bool | None:
    """Does the owner's own completeness claim agree with its references?

    ``None`` means the snapshot carries no claim at all (an older shape); that
    is not a contradiction, it is an absence of evidence.
    """
    if declared["manifest_question_count"] is None and declared["observed_count"] is None:
        return None
    if declared["observed_count"] is not None and declared["observed_count"] != observed_count:
        return False
    if (manifest_count is not None
            and declared["manifest_question_count"] is not None
            and declared["manifest_question_count"] != manifest_count):
        return False
    declared_missing = declared["missing_question_ids"]
    if declared_missing is not None:
        if sorted(set(declared_missing)) != missing:
            return False
    elif ids_known and missing:
        # The snapshot knows its own question set and still names no gaps.
        return False
    if (declared["manifest_question_count"] is not None
            and declared["observed_count"] is not None
            and declared_missing is not None
            and declared["observed_count"] + len(set(declared_missing))
            != declared["manifest_question_count"]):
        return False
    return True


def _scale_versions(result: dict[str, Any],
                    groups: list[dict[str, Any]] | None) -> list[str]:
    published = _ids(result.get("scale_versions"))
    if published is not None and published:
        return sorted(set(published))
    return sorted({group["rubric_version"] for group in groups or []})


def _questions(manifest_ids: list[str] | None, by_question: dict[str, dict[str, Any]],
               group_by_question: dict[str, dict[str, Any]],
               receipts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    identifiers = manifest_ids if manifest_ids is not None else sorted(by_question)
    questions = []
    for question_id in identifiers:
        reference = by_question.get(question_id)
        group = group_by_question.get(question_id)
        receipt = receipts.get(question_id)
        if reference is not None:
            status = "completed"
        elif receipt is not None:
            # A settled attempt without a bound observation was not saved, no
            # matter what the receipt calls its terminal state.
            status = ("settled_unsaved" if receipt["status"] == "completed"
                      else receipt["status"])
        else:
            status = "unknown"
        questions.append({
            "question_id": question_id,
            "status": status,
            "answer_state": receipt["answer_state"] if receipt is not None else None,
            "rubric_version": group["rubric_version"] if group is not None else None,
            "aggregation_role": group["aggregation_role"] if group is not None else None,
            "lineage_group_id": group["lineage_group_id"] if group is not None else None,
        })
    return questions


def derive_history_coverage(items: Any) -> dict[str, Any]:
    """Summarise a bounded history page: the page carries counts, not references."""
    rows = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        manifest_count = _count(item.get("manifest_question_count"))
        observed_count = _count(item.get("observed_count"))
        if manifest_count is None or observed_count is None or observed_count > manifest_count:
            verdict, missing = "unknown", None
        elif observed_count == manifest_count:
            verdict, missing = "complete", 0
        else:
            verdict, missing = "partial", manifest_count - observed_count
        rows.append({
            "result_id": _text(item.get("result_id")),
            "verdict": verdict,
            "manifest_question_count": manifest_count,
            "observed_count": observed_count,
            "missing_question_count": missing,
        })
    if not rows:
        verdict = "unknown"
    elif any(row["verdict"] == "partial" for row in rows):
        verdict = "partial"
    elif any(row["verdict"] == "unknown" for row in rows):
        verdict = "unknown"
    else:
        verdict = "complete"
    return {
        "protocol": COVERAGE_PROTOCOL,
        "version": COVERAGE_VERSION,
        "verdict": verdict,
        "items": rows,
    }
