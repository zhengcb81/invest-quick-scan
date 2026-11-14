"""Pure reuse-decision interpreter. Signature frozen by interfaces.md.

    assess_reuse(observation, question_policy, *, now_utc, information_cutoff,
                 context, verification_verifier=None) -> dict

No I/O; the caller supplies the real clock explicitly. The policy version is
chosen explicitly inside ``question_policy["policy_selection"]``; unknown
versions are named refusals. The legacy path delegates freshness math to the
byte-verified frozen stockwiki functions (oracle parity by construction); the
candidate path never promotes old data to fresh and never treats
observation/import time or model self-claims as verification.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any, Callable

from .errors import TimeSemanticsError, bad
from .legacy_oracle import (
    legacy_freshness_status,
    legacy_ttl_valid_until,
)
from .policy import (
    CANDIDATE_FAMILY,
    CANDIDATE_VERSION,
    LEGACY_FAMILY,
    LEGACY_VERSION,
    candidate_policy,
)

PROTOCOL = "iqs.temporal_policy_candidate/1.0.0"

_UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ANSWER_STATUSES = (
    "scored",
    "answered",
    "insufficient_evidence",
    "not_applicable",
    "search_unavailable",
)
_USABLE_STATUSES = {"scored", "answered", "not_applicable"}


def _parse_utc(value: Any, *, code: str = "timestamp_not_utc") -> datetime:
    if not isinstance(value, str) or not _UTC_TIMESTAMP.fullmatch(value):
        raise bad(code, repr(value)[:80])
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except (ValueError, OverflowError) as exc:
        raise bad(code, repr(value)[:80]) from exc
    if parsed.utcoffset() != timedelta(0):
        raise bad(code, value)
    return parsed


def _parse_date_only(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise bad("date_invalid", value) from exc


def _information_datetime(value: Any) -> datetime:
    """date-only -> T00:00:00Z (frozen legacy semantics); datetime -> as-is."""
    from datetime import timezone

    if not isinstance(value, str):
        raise bad("information_date_invalid", repr(value)[:80])
    if "T" in value:
        return _parse_utc(value, code="information_date_invalid")
    if not _ISO_DATE.fullmatch(value):
        raise bad("information_date_invalid", value)
    d = _parse_date_only(value)
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def _normalize_observation(obs: Any) -> dict[str, Any]:
    """Validate and return a shallow copy with the scope binding derived.

    The caller's dict is never mutated (the frozen gap-plan contract keeps
    inputs read-only); the derived scope_id mirrors the frozen payload shape
    (entity->entity_id, security->security_id, segment->segment_id).
    """
    if not isinstance(obs, dict):
        raise bad("observation_invalid", type(obs).__name__)
    required = (
        "observation_id",
        "entity_id",
        "identity_revision",
        "scope",
        "field_id",
        "question_id",
        "question_version",
        "question_semantic_sha256",
        "question_definition_sha256",
        "module_package_id",
        "module_release_id",
        "template_version",
        "information_cutoff",
        "observed_at",
        "execution",
        "answer",
    )
    for key in required:
        if key not in obs:
            raise bad("observation_missing_field", key)
    _parse_utc(obs["observed_at"])
    if not isinstance(obs["identity_revision"], int) or isinstance(obs["identity_revision"], bool):
        raise bad("identity_revision_invalid", repr(obs["identity_revision"]))
    if obs["scope"] not in ("entity", "security", "segment"):
        raise bad("scope_invalid", repr(obs["scope"]))
    if obs["scope"] == "entity" and not isinstance(obs["entity_id"], str):
        raise bad("observation_invalid", "entity_id")
    execution = obs["execution"]
    if not isinstance(execution, dict) or not isinstance(execution.get("provider"), str) or not isinstance(
        execution.get("model_resolved"), str
    ):
        raise bad("execution_invalid", "provider/model_resolved")
    answer = obs["answer"]
    if not isinstance(answer, dict) or answer.get("status") not in (
        "scored", "answered", "insufficient_evidence", "not_applicable", "search_unavailable",
    ):
        raise bad("answer_status_invalid", repr(answer.get("status") if isinstance(answer, dict) else answer))
    if not isinstance(answer.get("evidence", []), list):
        raise bad("evidence_invalid", type(answer.get("evidence")).__name__)
    if any(not isinstance(item, dict) for item in answer.get("evidence", [])):
        raise bad("evidence_invalid", "each evidence entry must be an object")
    normalized = dict(obs)
    if "check_level" not in normalized:
        # Frozen _matching_meta emits the constant check_level for reuse
        # candidates; payloads at the locked commit do not carry one.
        normalized["check_level"] = "unverified_model_output"
    if "scope_id" not in normalized:
        if obs["scope"] == "entity":
            normalized["scope_id"] = obs["entity_id"]
        elif obs["scope"] == "security":
            if "security_id" not in obs:
                raise bad("observation_missing_field", "security_id")
            normalized["scope_id"] = obs["security_id"]
        elif obs["scope"] == "segment":
            if "segment_id" not in obs:
                raise bad("observation_missing_field", "segment_id")
            normalized["scope_id"] = obs["segment_id"]
    canonical_key = {"entity": "entity_id", "security": "security_id", "segment": "segment_id"}[obs["scope"]]
    if canonical_key in obs and (
        not isinstance(obs[canonical_key], str)
        or not obs[canonical_key]
        or normalized["scope_id"] != obs[canonical_key]
    ):
        raise bad("observation_scope_id_conflict", canonical_key)
    event = obs.get("event_invalidated_at")
    if event is not None:
        # Validate on BOTH paths at the boundary: a malformed event must be a
        # named refusal even on the legacy path (review finding F-05).
        _parse_utc(event, code="event_invalidated_at_invalid")
    return normalized


def _validate_context(ctx: dict[str, Any]) -> None:
    if not isinstance(ctx, dict):
        raise bad("context_invalid", type(ctx).__name__)
    for key in (
        "entity_id",
        "identity_revision",
        "scope",
        "scope_id",
        "provider",
        "model",
        "question_id",
        "question_semantic_sha256",
        "question_definition_sha256",
        "question_version",
        "module_package_id",
        "module_release_id",
        "template_version",
        "minimum_check_level",
    ):
        if key not in ctx:
            raise bad("context_missing_field", key)
    if not isinstance(ctx["identity_revision"], int) or isinstance(ctx["identity_revision"], bool):
        raise bad("identity_revision_invalid", repr(ctx["identity_revision"]))


_CHECK_LEVELS = (
    "unverified_model_output",
    "execution_verified",
    "screening_audited",
    "formal_research_accepted",
)

# Explicit accounting-basis dimensions (card requirement 4, 口径): the frozen
# _routing_fingerprint binds these four context keys plus the subject
# perimeter. assess_reuse takes them as optional caller-provided pairs so a
# basis change blocks reuse even when every clock is fresh.
_ROUTING_CONTEXT_KEYS = ("reporting_currency", "accounting_standard", "fiscal_year_end", "security_class")


def _routing_context_gates(context: dict[str, Any]) -> list[str]:
    """Optional explicit 口径/perimeter gates.

    ``context['routing_prior']`` is the accounting-basis/perimeter snapshot
    bound to the observation (stored route/profile projection);
    ``context['routing_current']`` is the current request's. Only keys present
    on BOTH sides are compared — absent keys mean the caller does not assert
    that dimension and nothing is fabricated. Any mismatch blocks reuse
    regardless of clock freshness, mirroring the frozen routing-fingerprint
    semantics.
    """
    reasons: list[str] = []
    prior = context.get("routing_prior")
    current = context.get("routing_current")
    if isinstance(prior, dict) and isinstance(current, dict):
        for key in _ROUTING_CONTEXT_KEYS:
            if key in prior and key in current and prior[key] != current[key]:
                reasons.append("accounting_basis_changed")
        prior_perimeter = prior.get("perimeter_sha256")
        current_perimeter = current.get("perimeter_sha256")
        if (
            prior_perimeter is not None
            and current_perimeter is not None
            and prior_perimeter != current_perimeter
        ):
            reasons.append("perimeter_changed")
    return reasons


def _context_gates(obs: dict[str, Any], ctx: dict[str, Any], cutoff: str) -> list[str]:
    """Mirror the frozen compatibility checks; return mismatch reason codes."""
    reasons: list[str] = []
    if obs["identity_revision"] != ctx["identity_revision"]:
        reasons.append("identity_revision_changed")
    if obs["entity_id"] != ctx["entity_id"]:
        reasons.append("entity_changed")
    if obs["scope"] != ctx["scope"]:
        reasons.append("scope_changed")
    if obs["scope_id"] != ctx["scope_id"]:
        reasons.append("scope_id_changed")
    if obs["question_id"] != ctx["question_id"]:
        reasons.append("question_changed")
    if obs["question_semantic_sha256"] != ctx["question_semantic_sha256"]:
        reasons.append("semantic_change")
    if obs["question_definition_sha256"] != ctx["question_definition_sha256"]:
        reasons.append("semantic_change")
    if obs["question_version"] != ctx["question_version"]:
        reasons.append("meaning_version_changed")
    if obs["module_package_id"] != ctx["module_package_id"]:
        reasons.append("module_package_changed")
    if obs["module_release_id"] != ctx["module_release_id"]:
        reasons.append("module_release_changed")
    if obs["template_version"] != ctx["template_version"]:
        reasons.append("routing_change")
    if obs["execution"]["provider"] != ctx["provider"]:
        reasons.append("provider_changed")
    if obs["execution"]["model_resolved"] != ctx["model"]:
        reasons.append("model_changed")
    if obs["information_cutoff"] != cutoff:
        reasons.append("cutoff_changed")
    actual = obs["check_level"]
    minimum = ctx["minimum_check_level"]
    if actual not in _CHECK_LEVELS or minimum not in _CHECK_LEVELS:
        reasons.append("check_level_insufficient")
    elif _CHECK_LEVELS.index(actual) < _CHECK_LEVELS.index(minimum):
        reasons.append("check_level_insufficient")
    return reasons


def _status_reasons(answer_status: str) -> list[str]:
    if answer_status in _USABLE_STATUSES:
        return []
    if answer_status in {"insufficient_evidence", "search_unavailable"}:
        # No work-item store in this offline interpreter: without a real
        # next_retry_at cooldown receipt the conservative outcome is a refresh.
        return ["unknown_without_retry"]
    return [f"status_{answer_status}"]


def _legacy_decision_map(freshness: str, answer_status: str) -> tuple[str, list[str]]:
    """Frozen gap-plan semantics restated at decision level (no work items)."""
    if freshness == "event_invalidated":
        return "refresh_required", ["event_invalidated"]
    if freshness == "stale":
        return "refresh_required", ["ttl_expired"]
    if freshness == "missing_date":
        return "refresh_required", ["information_date_missing"]
    if answer_status == "not_applicable":
        return "not_applicable", ["fresh_and_compatible"]
    if answer_status in _USABLE_STATUSES:
        return "reuse_candidate", ["fresh_and_compatible"]
    return "refresh_required", ["unknown_without_retry"]


def _legacy_legs(obs: dict[str, Any], ttl_hours: int) -> str | None:
    """Exact frozen rule: min(observed_at+TTL, information_as_of+TTL)."""
    info = obs["answer"].get("information_as_of")
    if info is None:
        return None
    information_stamp = info if "T" in info else info + "T00:00:00Z"
    legs = [
        legacy_ttl_valid_until(obs["observed_at"], ttl_hours),
        legacy_ttl_valid_until(information_stamp, ttl_hours),
    ]
    return min(legs, key=lambda v: _parse_utc(v))


def _clock_reading(obs: dict[str, Any], clock: str) -> Any:
    answer = obs["answer"]
    if clock == "fact_valid_clock":
        # Candidate answer-recency leg: the frozen observed_at leg, grounded in
        # the existing 24h TTL baseline. information_as_of itself is never a
        # TTL renewal source in the candidate path.
        return obs["observed_at"]
    if clock == "market_clock":
        return answer.get("information_as_of")
    if clock == "reporting_period_clock":
        return answer.get("period_end")
    return None


def _assess_clock(
    clock: str,
    reading: Any,
    rule: dict[str, Any],
    now_dt: datetime,
) -> dict[str, Any]:
    max_age = rule.get("max_age_hours")
    on_missing = rule.get("on_missing", "refresh")
    if reading is None:
        status = "missing"
        reason = f"{clock}_missing"
        decision_effect = on_missing
    elif max_age is None:
        status = "policy_undecided"
        reason = f"{clock}_undecided"
        decision_effect = "refresh"
    else:
        reading_dt = _information_datetime(reading)
        if reading_dt > now_dt:
            raise bad("information_date_in_future", str(reading))
        age = now_dt - reading_dt
        if age < timedelta(hours=max_age):
            status, reason, decision_effect = "fresh", f"{clock}_fresh", "ok"
        else:
            status, reason, decision_effect = "stale", f"{clock}_stale", "refresh"
    return {
        "clock": clock,
        "reading": reading,
        "max_age_hours": max_age,
        "status": status,
        "reason_code": reason,
        "decision_effect": decision_effect,
    }


def _publication_check(answer: dict[str, Any], stored_cutoff: str, now_dt: datetime) -> tuple[str, list[str]]:
    """publication_clock: per-evidence constraint, never a max date.

    Strict-cutoff satisfiability is evaluated against the cutoff the
    observation was captured under (original ``source_available_as_of``
    semantics: end of cutoff day, unknown publication never satisfies).
    """
    cutoff_date = _parse_date_only(stored_cutoff)
    reasons: list[str] = []
    unknown = False
    if not answer.get("evidence"):
        return "refresh_required", ["publication_missing"]
    for item in answer.get("evidence", []):
        retracted = item.get("retracted_at")
        if retracted is not None:
            if not isinstance(retracted, str):
                raise bad('publication_invalid', repr(retracted)[:60])
            if _parse_utc(retracted, code="publication_invalid") <= now_dt:
                reasons.append("source_withdrawn_or_corrected")
        published = item.get("published_at")
        if published is None:
            unknown = True
            continue
        if not isinstance(published, str):
            raise bad("publication_invalid", repr(published)[:60])
        if "T" in published:
            published_dt = _parse_utc(published, code="publication_invalid")
            # UTC date comparison includes the complete cutoff day, including
            # fractional seconds in its last second, without rounded endpoints.
            if published_dt.date() > cutoff_date:
                reasons.append("evidence_published_after_cutoff")
            if published_dt > now_dt:
                reasons.append("evidence_published_in_future")
        else:
            published_date = _parse_date_only(published)
            if published_date > cutoff_date:
                reasons.append("evidence_published_after_cutoff")
            if published_date > now_dt.date():
                reasons.append("evidence_published_in_future")
    if unknown:
        return "not_assessable", ["publication_unknown"]
    if reasons:
        return "refresh_required", reasons
    return "ok", []


def explain_observation_clocks(observation, required_clocks, *, now_utc):
    """Project an observation's dates for display without deciding reuse."""
    now = _parse_utc(now_utc)
    rules = candidate_policy()["clock_rules"]
    answer = observation.get("answer")
    if not isinstance(answer, dict):
        raise ValueError("native_clock_answer_unreadable")
    evidence = answer.get("evidence", [])
    if not isinstance(evidence, list) or any(not isinstance(item, dict) for item in evidence):
        raise ValueError("native_clock_answer_unreadable")
    cutoff = observation.get("information_cutoff")
    information_as_of = answer.get("information_as_of")
    if information_as_of is not None:
        information_date = _information_datetime(information_as_of)
        if information_date > now:
            raise TimeSemanticsError("information_date_in_future")
        if information_date.date() > _parse_date_only(cutoff):
            raise TimeSemanticsError("information_after_cutoff")

    publication_status, publication_reasons = _publication_check(answer, cutoff, now)
    status, reasons = publication_status, publication_reasons
    event = observation.get("event_invalidated_at")
    event_status = None
    if event is not None:
        event_time = _parse_utc(event, code="event_invalidated_at_invalid")
        event_status = "invalidated" if event_time <= now else "scheduled"
        if event_status == "invalidated":
            reasons = [*reasons, "event_invalidated"]
            if status == "ok":
                status = "refresh_required"

    readings = []
    for clock in required_clocks:
        if clock == "verification_clock":
            continue
        if clock == "publication_clock":
            readings.append({"clock": clock, "reading": [entry.get("published_at") for entry in evidence],
                "max_age_hours": None,
                "status": "satisfied" if publication_status == "ok" else publication_status,
                "reason_code": publication_reasons[0] if publication_reasons else "publication_satisfied",
                "decision_effect": publication_status})
        else:
            readings.append(_assess_clock(clock, _clock_reading(observation, clock), rules[clock], now))

    return {"protocol": "iqs.temporal_clock_explanation/1.0.0", "context_assessed": False,
            "reuse_authorized": False, "clock_assessments": readings,
            "source_constraints": {"status": status, "reason_codes": reasons, "event_status": event_status},
            "actual_source_dates": {"observed_at": observation.get("observed_at"),
                "information_as_of": information_as_of, "metric_period_end": answer.get("period_end"),
                "verified_at": None, "event_invalidated_at": event}}


def _verification_check(
    verifier: Callable[..., Any] | None,
    obs: dict[str, Any],
    question_policy: dict[str, Any],
    ctx: dict[str, Any],
    now_dt: datetime,
    max_age_hours: int | None,
) -> tuple[str, list[str], dict[str, Any] | None]:
    """verification_clock: only a caller-supplied trusted verifier counts.

    observed_at / imported_at / answer text are never verification evidence.
    With a decided max_age the receipt must also be time-fresh
    (now < verified_at + max_age); an undecided max_age never reuses.
    """
    from datetime import timedelta

    if verifier is None:
        return "missing", ["verification_missing"], None
    receipt = verifier(obs, question_policy, ctx, now_dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
    if not isinstance(receipt, dict):
        return "missing", ["verification_missing"], None
    verified_at = receipt.get("verified_at")
    if not isinstance(verified_at, str):
        return "invalid", ["verification_receipt_invalid"], receipt
    verified_dt = _parse_utc(verified_at, code="verification_receipt_invalid")
    if verified_dt > now_dt:
        return "invalid", ["verification_receipt_invalid"], receipt
    expires_at = receipt.get("expires_at")
    if expires_at is not None and not isinstance(expires_at, str):
        return "invalid", ["verification_receipt_invalid"], receipt
    if isinstance(expires_at, str) and _parse_utc(expires_at, code="verification_receipt_invalid") <= now_dt:
        return "expired", ["verification_receipt_expired"], receipt
    if receipt.get("withdrawn_at"):
        return "withdrawn", ["verification_receipt_withdrawn"], receipt
    binding_keys = ("entity_id", "scope", "scope_id", "question_id", "field_id", "observation_id")
    if any(receipt.get(k) != obs.get(k) for k in binding_keys):
        return "scope_mismatch", ["verification_receipt_scope_mismatch"], receipt
    selection = question_policy["policy_selection"]
    policy_version = f"{selection['policy_family']}/{selection['policy_version']}"
    if receipt.get("policy_version") != policy_version:
        return "policy_mismatch", ["verification_receipt_policy_mismatch"], receipt
    coverage = receipt.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("search_executed") is not True:
        # "searched but nothing found" without a real tool receipt is not coverage.
        return "coverage_missing", ["verification_coverage_missing"], receipt
    receipt_id = coverage.get("search_receipt_id")
    sources = coverage.get("sources_checked")
    if (
        not isinstance(receipt_id, str) or not receipt_id.strip()
        or not isinstance(sources, list) or not sources
        or any(not isinstance(source, str) or not source.strip() for source in sources)
    ):
        return "coverage_missing", ["verification_coverage_missing"], receipt
    if coverage.get("cutoff") != obs["information_cutoff"]:
        return "coverage_mismatch", ["verification_coverage_cutoff_mismatch"], receipt
    try:
        searched_dt = _parse_utc(coverage.get("searched_at"), code="verification_receipt_invalid")
    except TimeSemanticsError:
        return "invalid", ["verification_receipt_invalid"], receipt
    if searched_dt > verified_dt:
        return "invalid", ["verification_receipt_invalid"], receipt
    if max_age_hours is not None:
        if now_dt >= verified_dt + timedelta(hours=max_age_hours):
            return "expired", ["verification_receipt_expired"], receipt
    return "valid", ["verification_receipt_valid"], receipt


def _resolve_selection(question_policy: dict[str, Any]) -> tuple[str, str, int | None, dict[str, Any] | None]:
    if not isinstance(question_policy, dict):
        raise bad("question_policy_invalid", type(question_policy).__name__)
    selection = question_policy.get("policy_selection")
    if not isinstance(selection, dict):
        raise bad("policy_selection_missing", "question_policy.policy_selection")
    family = selection.get("policy_family")
    version = selection.get("policy_version")
    if family == LEGACY_FAMILY and version == LEGACY_VERSION:
        ttl = selection.get("ttl_hours")
        if isinstance(ttl, bool) or not isinstance(ttl, int) or ttl < 1:
            raise bad("ttl_invalid", repr(ttl))
        return LEGACY_FAMILY, LEGACY_VERSION, ttl, None
    if family == CANDIDATE_FAMILY and version == CANDIDATE_VERSION:
        return CANDIDATE_FAMILY, CANDIDATE_VERSION, None, selection.get("clock_rules")
    raise bad("policy_version_unknown", f"{family}/{version}")


def assess_reuse(
    observation: dict[str, Any],
    question_policy: dict[str, Any],
    *,
    now_utc: str,
    information_cutoff: str,
    context: dict[str, Any],
    verification_verifier: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    from .policy import validate_question_policy

    observation = _normalize_observation(observation)
    _validate_context(context)
    validate_question_policy(question_policy)
    if not isinstance(now_utc, str):
        raise bad("timestamp_not_utc", repr(now_utc)[:60])
    now_dt = _parse_utc(now_utc)
    if not isinstance(information_cutoff, str) or not _ISO_DATE.fullmatch(information_cutoff):
        raise bad("cutoff_invalid", repr(information_cutoff)[:60])
    cutoff_date = _parse_date_only(information_cutoff)

    family, version, ttl_hours, clock_rules = _resolve_selection(question_policy)

    info = observation["answer"].get("information_as_of")
    info_dt = _information_datetime(info) if info is not None else None
    if info_dt is not None and info_dt > now_dt:
        raise bad("information_date_in_future", str(info))
    if info is not None:
        # Import-time contract: the answer may not claim information beyond the
        # cutoff it was captured under. A DIFFERENT requested cutoff is a
        # context gate (cutoff_changed), not an information violation.
        stored_cutoff_date = _parse_date_only(observation["information_cutoff"])
        if info_dt.date() > stored_cutoff_date:
            raise bad("information_after_cutoff", f"{info} > {observation['information_cutoff']}")

    context_reasons = _context_gates(observation, context, information_cutoff)
    context_reasons = context_reasons + _routing_context_gates(context)
    if (
        question_policy.get("question_id") != observation["question_id"]
        or question_policy.get("field_id") != observation["field_id"]
    ):
        context_reasons = list(context_reasons) + ["question_policy_mismatch"]
    clock_assessments: list[dict[str, Any]] = []
    receipt_used: dict[str, Any] | None = None
    reasons: list[str] = []
    if context_reasons:
        decision = "blocked_context"
        reasons = list(context_reasons)
    elif family == LEGACY_FAMILY:
        valid_until = _legacy_legs(observation, ttl_hours)
        meta = {
            "information_as_of": info,
            "valid_until": valid_until,
            "event_invalidated_at": observation.get("event_invalidated_at"),
        }
        try:
            freshness = legacy_freshness_status(meta, now_utc)
        except TimeSemanticsError:
            raise
        except ValueError as exc:
            # Frozen FreshnessPlanError is re-namespaced so the CLI contract
            # (named refusal, exit 2) holds on the legacy path too (F-05).
            raise bad(getattr(exc, "error_code", "legacy_freshness_error"), str(exc)[:120]) from exc
        decision, reasons = _legacy_decision_map(freshness, observation["answer"]["status"])
    else:
        rules = _candidate_clock_rules(clock_rules)
        event = observation.get("event_invalidated_at")
        if event is not None and _parse_utc(event, code="event_invalidated_at_invalid") <= now_dt:
            reasons.append("event_invalidated")
        decision = None
        # Publication satisfiability is a contract constraint on every
        # candidate assessment (unknown publication never satisfies a strict
        # cutoff), independent of which clocks the entry lists.
        pub_status, pub_reasons = _publication_check(
            observation["answer"], observation["information_cutoff"], now_dt
        )
        if pub_status == "not_assessable":
            decision = "not_assessable"
            reasons.extend(pub_reasons)
        elif pub_status == "refresh_required":
            reasons.extend(pub_reasons)
        for clock in question_policy["required_clocks"]:
            if clock == "publication_clock":
                assessment = {
                    "clock": clock,
                    "reading": [e.get("published_at") for e in observation["answer"].get("evidence", [])],
                    "max_age_hours": None,
                    "status": pub_status if pub_status != "ok" else "satisfied",
                    "reason_code": pub_reasons[0] if pub_reasons else "publication_satisfied",
                    "decision_effect": pub_status if pub_status != "ok" else "ok",
                }
            elif clock == "verification_clock":
                max_age = rules[clock].get("max_age_hours")
                status, ver_reasons, checked_receipt = _verification_check(
                    verification_verifier, observation, question_policy, context, now_dt, max_age
                )
                # Only an ACCEPTED (gate-passing) receipt's dates surface in
                # actual_source_dates; rejected receipts keep their dates out
                # so the field can never be read as accepted verification
                # (review F-10). Rejection reasons stay in reason_codes and
                # clock_assessments.
                if status == "valid" and isinstance(checked_receipt, dict):
                    receipt_used = checked_receipt
                if status == "valid" and max_age is None:
                    status, reason_code, effect = (
                        "policy_undecided",
                        "verification_clock_undecided",
                        "refresh",
                    )
                    reasons.append(reason_code)
                elif status == "valid":
                    status, reason_code, effect = "fresh", "verification_clock_fresh", "ok"
                else:
                    reason_code, effect = ver_reasons[0], "refresh"
                    reasons.append(reason_code)
                assessment = {
                    "clock": clock,
                    "reading": receipt_used.get("verified_at") if isinstance(receipt_used, dict) else None,
                    "max_age_hours": max_age,
                    "status": status,
                    "reason_code": reason_code,
                    "decision_effect": effect,
                }
            else:
                assessment = _assess_clock(clock, _clock_reading(observation, clock), rules[clock], now_dt)
                if assessment["decision_effect"] == "refresh":
                    reasons.append(assessment["reason_code"])
            clock_assessments.append(assessment)
            if assessment["decision_effect"] == "not_assessable":
                decision = "not_assessable"
        status = observation["answer"]["status"]
        if decision is None:
            if reasons:
                decision = "refresh_required"
            elif status == "not_applicable":
                decision = "not_applicable"
            elif status in {"scored", "answered"}:
                decision = "reuse_candidate"
                reasons.append("fresh_and_compatible")
            else:
                decision = "refresh_required"
                reasons.extend(_status_reasons(status))
        else:
            reasons.extend(_status_reasons(status))

    legacy_valid_until = _legacy_legs(observation, ttl_hours or 24)
    legacy_meta = {
        "information_as_of": info,
        "valid_until": legacy_valid_until,
        "event_invalidated_at": observation.get("event_invalidated_at"),
    }
    try:
        legacy_freshness = legacy_freshness_status(legacy_meta, now_utc)
    except TimeSemanticsError:
        raise
    except ValueError as exc:
        legacy_freshness = f"error:{getattr(exc, 'error_code', 'legacy_error')}"
    legacy_decision, legacy_reasons = _legacy_decision_map(
        legacy_freshness, observation["answer"]["status"]
    )
    if context_reasons:
        legacy_decision, legacy_reasons = "dispatch_new_work", list(context_reasons)

    actual_dates = {
        "observed_at": observation["observed_at"],
        "information_as_of": info,
        "metric_period_end": observation["answer"].get("period_end"),
        "evidence_published_at": [
            e.get("published_at") for e in observation["answer"].get("evidence", [])
        ],
        "searched_at": (receipt_used or {}).get("coverage", {}).get("searched_at"),
        "verified_at": (receipt_used or {}).get("verified_at"),
        "event_invalidated_at": observation.get("event_invalidated_at"),
    }

    return {
        "protocol": PROTOCOL,
        "candidate_only": True,
        "production_ready": False,
        "observation_id": observation["observation_id"],
        "question_id": observation["question_id"],
        "field_id": observation["field_id"],
        "policy_ref": {"policy_family": family, "policy_version": version},
        "decision": decision,
        "reason_codes": sorted(set(reasons)),
        "actual_source_dates": actual_dates,
        "clock_assessments": clock_assessments if family == CANDIDATE_FAMILY else [],
        "legacy_equivalent": {
            "policy_ref": f"{LEGACY_FAMILY}/{LEGACY_VERSION} (frozen stockwiki@8527bc7)",
            "freshness_status": legacy_freshness,
            "valid_until": legacy_valid_until,
            "decision": legacy_decision,
            "reasons": legacy_reasons,
            "oracle": "vendor_upstream/stockwiki/stockwiki/quick_scan_freshness.py",
        },
    }


def _candidate_clock_rules(clock_rules: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    from .policy import candidate_policy

    return candidate_policy(clock_rules)["clock_rules"]
