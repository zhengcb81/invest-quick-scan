"""Versioned read-only TIME explanation over native immutable observations.

The saved record is NOT current routing context. This sidecar cannot authorize
reuse, renew TTL, issue receipts or change the original entity/refresh DTO.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from iqs_temporal_vendor import TimeSemanticsError
from iqs_temporal_vendor.policy import candidate_policy
from iqs_temporal_vendor.assess import (_parse_utc, _clock_reading, _assess_clock,
                                       _publication_check, _information_datetime, _parse_date_only)

PROTOCOL = "iqs.temporal_shadow/1.0.0"
VIEW_PROTOCOL = "iqs.company_research_view/1.0.0"
_DATA = Path(__file__).resolve().parent / "iqs_temporal_vendor"


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _policies():
    catalog = json.loads((_DATA / "time-policy-catalog.json").read_bytes())
    bindings = json.loads((_DATA / "question-bindings.json").read_bytes())["bindings"]
    return {entry["question_id"]: entry for entry in catalog["entries"]}, bindings


def _refusal(row, code):
    return {"observation_id": row.get("observation_id"),
            "question_id": row.get("question_id"), "field_id": row.get("field_id"),
            "decision": "not_assessable", "reason_codes": [code],
            "current_context_verified": False, "reuse_authorized": False,
            "verification_receipt_available": False}


def _clock_explanation(observation, policy, now_utc):
    """Use the pinned TIME clock engine without inventing missing identity context."""
    now = _parse_utc(now_utc)
    rules = candidate_policy()["clock_rules"]
    answer = observation.get("answer")
    if not isinstance(answer, dict) or not isinstance(answer.get("evidence", []), list) or any(
            not isinstance(item, dict) for item in answer.get("evidence", [])):
        raise ValueError("native_clock_answer_unreadable")
    info = answer.get("information_as_of")
    if info is not None:
        information_date = _information_datetime(info)
        if information_date > now:
            raise TimeSemanticsError("information_date_in_future")
        if information_date.date() > _parse_date_only(observation.get("information_cutoff")):
            raise TimeSemanticsError("information_after_cutoff")
    publication_status, publication_reasons = _publication_check(
        answer, observation.get("information_cutoff"), now)
    event = observation.get("event_invalidated_at")
    event_status = None
    if event is not None:
        event_time = _parse_utc(event, code="event_invalidated_at_invalid")
        event_status = "invalidated" if event_time <= now else "scheduled"
        if event_status == "invalidated":
            publication_reasons = [*publication_reasons, "event_invalidated"]
            if publication_status == "ok":
                publication_status = "refresh_required"
    readings = []
    for clock in policy["required_clocks"]:
        if clock == "verification_clock":
            continue  # Retired receipt system; historical metadata stays in the original DTO.
        if clock == "publication_clock":
            status, reasons = _publication_check(answer, observation.get("information_cutoff"), now)
            item = {"clock": clock, "reading": [e.get("published_at") for e in answer.get("evidence", [])],
                    "max_age_hours": None, "status": "satisfied" if status == "ok" else status,
                    "reason_code": reasons[0] if reasons else "publication_satisfied",
                    "decision_effect": status}
        else:
            item = _assess_clock(clock, _clock_reading(observation, clock), rules[clock], now)
        readings.append(item)
    return {"protocol": "iqs.temporal_clock_explanation/1.0.0", "context_assessed": False,
            "reuse_authorized": False, "clock_assessments": readings,
            "source_constraints": {"status": publication_status, "reason_codes": publication_reasons,
                                   "event_status": event_status},
            "actual_source_dates": {"observed_at": observation.get("observed_at"),
                "information_as_of": answer.get("information_as_of"),
                "metric_period_end": answer.get("period_end"), "verified_at": None,
                "event_invalidated_at": event}}


def _record(row, raw, entity_id, now_utc, policies, bindings):
    result = _refusal(row, "current_context_not_verified")
    if not isinstance(raw, dict) or not isinstance(raw.get("payload"), dict):
        return _refusal(row, "native_observation_unavailable")
    payload = raw["payload"]
    try:
        if _sha(payload) != raw.get("payload_sha256"):
            return _refusal(row, "native_payload_hash_mismatch")
    except (TypeError, ValueError):
        return _refusal(row, "native_payload_invalid")
    if raw.get("entity_id") != entity_id or payload.get("entity_id") != entity_id:
        return _refusal(row, "native_identity_conflict")
    for key in ("observation_id", "field_id", "question_id", "scope"):
        if not row.get(key) or row[key] != raw.get(key) or raw.get(key) != payload.get(key):
            return _refusal(row, "native_projection_binding_mismatch")
    if row.get("payload_sha256") != raw.get("payload_sha256"):
        return _refusal(row, "projection_payload_hash_mismatch")
    for key in ("security_id", "listing_id", "segment_id"):
        if row.get(key) != payload.get(key):
            return _refusal(row, "native_scope_binding_mismatch")
    for key in ("observed_at", "information_cutoff"):
        if row.get(key) != raw.get(key) or raw.get(key) != payload.get(key):
            return _refusal(row, "native_clock_binding_mismatch")
    qid = payload.get("question_id")
    if not isinstance(qid, str):
        return _refusal(row, "native_question_invalid")
    policy, binding = policies.get(qid), bindings.get(qid)
    if not policy or policy.get("field_id") != payload.get("field_id"):
        return _refusal(row, "time_policy_unavailable")
    if (not binding or payload.get("question_definition_sha256") != binding["definition_sha256"]
            or payload.get("module_release_id") != binding["module_release_id"]
            or policy["module_id"] != binding["module_id"]):
        return _refusal(row, "time_policy_definition_unbound")
    result["knowledge_kind"] = policy["knowledge_kind"]
    result["required_clocks"] = [clock for clock in policy["required_clocks"] if clock != "verification_clock"]
    revision = raw.get("identity_revision")
    if type(revision) is not int or ("identity_revision" in payload and payload["identity_revision"] != revision):
        result["reason_codes"].append("native_identity_revision_unknown")
    try:
        # Explain the original dates; the native service alone decides cache reuse.
        result["clock_only_assessment"] = _clock_explanation(payload, policy, now_utc)
        result["reason_codes"] += result["clock_only_assessment"]["source_constraints"]["reason_codes"]
    except (TimeSemanticsError, ValueError, TypeError, KeyError) as error:
        result["reason_codes"].append(getattr(error, "error_code", "native_clock_not_assessable"))
    return result


def build_entity_view(detail, get_observation, *, entity_id, now_utc):
    """Wrap untouched original entity DTO; evaluate only exact visible native rows."""
    policies, bindings = _policies()
    sidecar = {"protocol": PROTOCOL, "evaluated_at_utc": now_utc,
        "mode": "read_only_shadow", "production_reuse_applied": False,
        "reuse_authorized": False, "current_context_verified": False,
        "legacy_policy_changed": False, "network_calls": 0, "llm_calls": 0,
        "note": "时点解释仅供阅读；实际复用仍按原服务预检，不自动续期。", "records": []}
    owner = detail.get("entity") if isinstance(detail, dict) else None
    if not isinstance(owner, dict) or owner.get("entity_id") != entity_id or (
            "entity_id" in detail and detail["entity_id"] != entity_id):
        sidecar["reason_codes"] = ["entity_envelope_identity_conflict"]
        return {"protocol": VIEW_PROTOCOL, "entity": detail, "temporal_shadow": sidecar}
    cache = {}
    groups = detail.get("groups")
    if not isinstance(groups, list):
        sidecar["reason_codes"] = ["entity_groups_unreadable"]
        groups = []
    for group in groups:
        fields = group.get("fields") if isinstance(group, dict) else None
        if not isinstance(fields, list):
            sidecar.setdefault("reason_codes", []).append("entity_fields_unreadable")
            continue
        for row in fields:
            if not isinstance(row, dict):
                continue
            if "entity_id" in row and row["entity_id"] != entity_id:
                sidecar["records"].append(_refusal(row, "child_identity_unknown_or_foreign"))
                continue
            oid = row.get("observation_id")
            if not isinstance(oid, str) or not oid:
                sidecar["records"].append(_refusal(row, "observation_id_missing"))
                continue
            if oid not in cache:
                cache[oid] = get_observation(oid)
            sidecar["records"].append(_record(row, cache[oid], entity_id, now_utc, policies, bindings))
    return {"protocol": VIEW_PROTOCOL, "entity": detail, "temporal_shadow": sidecar}
