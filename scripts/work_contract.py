"""Pure, offline reference rules for C04 freshness and work identity.

This module does not persist work, call providers, or own retries. StockQA and
StockWiki adapters remain responsible for executing these contracts.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import hashlib
import json
import re


_UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.-]{1,160}$")
_CHECK_LEVELS = ("unverified_model_output", "execution_verified", "screening_audited", "formal_research_accepted")

_ALLOWED_TRANSITIONS = {
    "pending": {"leased", "cancelled"},
    "leased": {"result_ready", "uncertain", "pending", "failed"},
    "uncertain": {"result_ready", "failed", "pending"},
    "result_ready": {"delivered"},
    "delivered": set(),
    "failed": {"pending", "cancelled"},
    "cancelled": set(),
}


def parse_utc(value: str) -> datetime:
    """Parse an explicit RFC3339 UTC timestamp; reject naive/non-UTC values."""
    if not isinstance(value, str) or not _UTC_TIMESTAMP.fullmatch(value):
        raise ValueError("timestamp must be RFC3339 UTC and end in Z or +00:00")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be UTC")
    return parsed


def _information_date(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("information_as_of must be an ISO date, UTC timestamp, or null")
    try:
        if "T" in value:
            return parse_utc(value).date()
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("information_as_of must be an ISO date or UTC timestamp") from exc


def freshness_status(meta: dict, now: str) -> str:
    """Return current freshness without changing or refreshing the observation."""
    current = parse_utc(now)
    raw_information_time = meta.get("information_as_of")
    info_date = _information_date(raw_information_time)
    if info_date is None:
        return "missing_date"
    information_is_future = (parse_utc(raw_information_time) > current
                             if isinstance(raw_information_time, str) and "T" in raw_information_time
                             else info_date > current.date())
    if information_is_future:
        raise ValueError("information_as_of cannot be in the future")
    invalidated_at = meta.get("event_invalidated_at")
    if invalidated_at is not None and parse_utc(invalidated_at) <= current:
        return "event_invalidated"
    valid_until = meta.get("valid_until")
    if valid_until is None:
        return "missing_date"
    return "fresh" if current < parse_utc(valid_until) else "stale"


def field_freshness_preview(field_metadata: dict, now: str) -> dict:
    """Classify fields independently and report refresh gaps without dispatching work."""
    if not isinstance(field_metadata, dict):
        raise ValueError("field_metadata must be a field-to-metadata mapping")
    if any(not isinstance(field_id, str) or not _IDENTIFIER.fullmatch(field_id)
           for field_id in field_metadata):
        raise ValueError("field identifiers must be stable non-empty identifiers")
    if any(not isinstance(metadata, dict) for metadata in field_metadata.values()):
        raise ValueError("each field must contain observation metadata")

    fields = {}
    refresh_needed = []
    for field_id in sorted(field_metadata):
        status = freshness_status(field_metadata[field_id], now)
        fields[field_id] = {
            "freshness_status": status,
            "refresh_needed": status != "fresh",
        }
        if status != "fresh":
            refresh_needed.append(field_id)
    return {
        "fields": fields,
        "refresh_needed_fields": refresh_needed,
        "dispatch_started": False,
    }


def validate_temporal_order(meta: dict) -> None:
    """Reject impossible execution/import ordering without manufacturing missing times."""
    started = meta.get("answer_started_at")
    answered = meta.get("answered_at")
    imported = meta.get("imported_at")
    if started is not None and answered is not None and parse_utc(answered) < parse_utc(started):
        raise ValueError("answered_at cannot precede answer_started_at")
    if answered is not None and imported is not None and parse_utc(imported) < parse_utc(answered):
        raise ValueError("imported_at cannot precede answered_at")


def source_available_as_of(published_at: str | None, cutoff: str) -> bool:
    """Unknown publication time cannot support a strict historical cutoff."""
    if published_at is None:
        return False
    cutoff_value = date.fromisoformat(cutoff)
    published = parse_utc(published_at)
    end_of_cutoff_day = datetime.combine(cutoff_value, time.max, tzinfo=timezone.utc)
    return published <= end_of_cutoff_day


def observation_compatible(observation: dict, expected: dict) -> bool:
    """Require identical field meaning/scope and sufficient independent review."""
    if expected.get("schema_version") == "2.0.0":
        if observation.get("schema_version") != "2.0.0":
            return False
        identity_fields = (
            "entity_id", "identity_revision", "source_binding_version", "source_binding_refs",
        )
        if any(expected.get(key) is None or observation.get(key) != expected[key]
               for key in identity_fields):
            return False
        if (expected.get("identity_state") not in {"provisional", "verified"}
                or observation.get("identity_state_at_answer") != expected["identity_state"]
                or observation.get("work_generation") != expected.get("generation")):
            return False
    elif observation.get("schema_version") == "2.0.0":
        return False
    for key in ("question_fingerprint", "routing_fingerprint", "scope", "scope_id"):
        if not observation.get(key) or observation.get(key) != expected.get(key):
            return False
    actual_level = observation.get("check_level")
    minimum_level = expected.get("minimum_check_level")
    if actual_level not in _CHECK_LEVELS or minimum_level not in _CHECK_LEVELS:
        return False
    return _CHECK_LEVELS.index(actual_level) >= _CHECK_LEVELS.index(minimum_level)


def reuse_decision(observation: dict, expected: dict, now: str, work_item: dict | None = None) -> str:
    """Return reuse, deferred_unknown, or dispatch without mutating an input."""
    if not observation_compatible(observation, expected):
        return "dispatch"
    status = observation.get("response_status")
    work_item = work_item or {}
    if expected.get("schema_version") == "2.0.0" and work_item:
        if (work_item.get("schema_version") != "2.0.0"
                or any(work_item.get(key) != expected.get(key) for key in (
                    "entity_id", "identity_state", "identity_revision",
                    "source_binding_version", "source_binding_refs"))):
            return "dispatch"
    requested_generation = expected.get("generation")
    if requested_generation is not None and work_item.get("generation") != requested_generation:
        return "dispatch"
    if work_item.get("status") in {"pending", "leased", "uncertain", "result_ready"}:
        return "resume_existing_work"
    retry_at = work_item.get("next_retry_at")
    if status in {"insufficient_evidence", "search_unavailable"}:
        if not retry_at:
            return "manual_refresh_required"
        if parse_utc(now) < parse_utc(retry_at):
            return "deferred_unknown"
        return "dispatch_new_generation"
    if status not in {"scored", "answered", "not_applicable"}:
        return "dispatch"
    return "reuse" if freshness_status(observation, now) == "fresh" else "dispatch"


def logical_work_key(entity_id: str, question_id: str, generation: int, scope: str, scope_id: str) -> tuple:
    """Stable task identity; run/model/attempt do not create new primary work."""
    for name, value in (("entity_id", entity_id), ("question_id", question_id), ("scope_id", scope_id)):
        if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
            raise ValueError(f"invalid {name}")
    if not re.fullmatch(r"ENT_[A-Za-z0-9_]+", entity_id):
        raise ValueError("entity_id must use the identity contract's ENT_ prefix")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        raise ValueError("generation must be a positive integer")
    if scope not in {"entity", "security", "segment"}:
        raise ValueError("scope must be entity, security, or segment")
    if scope == "entity" and scope_id != entity_id:
        raise ValueError("entity-scoped work must use entity_id as scope_id")
    if scope == "security" and not re.fullmatch(r"SEC_[A-Za-z0-9_.]+", scope_id):
        raise ValueError("security scope_id must use the identity contract's SEC_ prefix")
    if scope == "segment" and not re.fullmatch(r"SEG_[A-Za-z0-9_]+", scope_id):
        raise ValueError("segment scope_id must use the identity contract's SEG_ prefix")
    return entity_id, question_id, generation, scope, scope_id


def logical_work_key_v2(entity_id: str, question_id: str, generation: int,
                        scope: str, scope_id: str, *, identity_revision: int,
                        source_binding_version: int, identity_state: str,
                        source_binding_refs: list[str]) -> tuple:
    """Identity-bound work key. An owner revision change cannot reuse old paid work."""
    base = logical_work_key(entity_id, question_id, generation, scope, scope_id)
    for name, value in (("identity_revision", identity_revision),
                        ("source_binding_version", source_binding_version)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    if identity_state not in {"provisional", "verified"}:
        raise ValueError("invalid identity_state")
    if (not isinstance(source_binding_refs, list) or not source_binding_refs
            or not all(isinstance(ref, str) and re.fullmatch(r"BND_[A-Za-z0-9_]+", ref)
                       for ref in source_binding_refs)
            or source_binding_refs != sorted(set(source_binding_refs))):
        raise ValueError("source_binding_refs must be sorted unique binding IDs")
    return (*base, identity_revision, source_binding_version,
            identity_state, tuple(source_binding_refs))


def request_cache_key(work_key: tuple, *, provider: str, model: str, input_hash: str,
                      question_fingerprint: str, routing_fingerprint: str,
                      information_cutoff: str, search_enabled: bool) -> str:
    """Cache one exact request separately from durable logical work identity."""
    if not all(isinstance(v, str) and v for v in
               (provider, model, input_hash, question_fingerprint, routing_fingerprint, information_cutoff)):
        raise ValueError("request cache key inputs must be non-empty strings")
    if not isinstance(search_enabled, bool):
        raise ValueError("search_enabled must be boolean")
    payload = [work_key, provider, model, input_hash, question_fingerprint,
               routing_fingerprint, information_cutoff, search_enabled]
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    return "REQ_" + digest


def transition_allowed(current: str, target: str, *, now: str | None = None,
                       next_retry_at: str | None = None, confirmed_not_sent: bool = False,
                       retry_eligible: bool = False, ack_item_id: str | None = None,
                       expected_item_id: str | None = None, ack_hash: str | None = None,
                       expected_hash: str | None = None, ack_status: str | None = None,
                       attempt_ids: list[str] | None = None,
                       uncertain_attempt_id: str | None = None, reconciled_attempt_id: str | None = None,
                       reconciliation_outcome: str | None = None) -> bool:
    """Check one state change. Rejected ACKs leave result_ready unchanged."""
    if target not in _ALLOWED_TRANSITIONS.get(current, set()):
        return False
    if current == "leased" and target == "pending" and not confirmed_not_sent:
        return False
    if current == "uncertain":
        if (not uncertain_attempt_id or not attempt_ids
                or attempt_ids.count(uncertain_attempt_id) != 1
                or uncertain_attempt_id != reconciled_attempt_id):
            return False
        if target == "pending" and not (confirmed_not_sent and reconciliation_outcome == "not_sent"):
            return False
        if target == "result_ready" and reconciliation_outcome != "response_available":
            return False
        if target == "failed" and reconciliation_outcome != "terminal_error":
            return False
    if current == "failed" and target == "pending" and not retry_eligible:
        return False
    if current == "result_ready" and target == "delivered":
        return bool(expected_item_id and ack_item_id == expected_item_id
                    and expected_hash and ack_hash == expected_hash and ack_status == "accepted")
    return True


def transition_work_item(work_item: dict, target: str, *,
                         scope_owner_entity_id: str | None = None, **proof) -> bool:
    """Validate the persisted item before deriving transition identity/proofs."""
    try:
        from .contract_validation import validate_work_item
    except ImportError:
        from contract_validation import validate_work_item

    validate_work_item(work_item, scope_owner_entity_id=scope_owner_entity_id)
    proof_attempt_id = proof.pop("uncertain_attempt_id", None)
    persisted_attempt_id = work_item.get("uncertain_attempt_id")
    if proof_attempt_id is not None and proof_attempt_id != persisted_attempt_id:
        return False
    return transition_allowed(
        work_item["status"], target,
        attempt_ids=[attempt["attempt_id"] for attempt in work_item.get("attempts", [])],
        uncertain_attempt_id=persisted_attempt_id,
        **proof,
    )


def require_transition(current: str, target: str, **proof) -> None:
    if not transition_allowed(current, target, **proof):
        raise ValueError(f"transition rejected: {current} -> {target}")
