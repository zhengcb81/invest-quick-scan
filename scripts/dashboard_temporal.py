"""Versioned read-only TIME explanation over native immutable observations.

The saved record is NOT current routing context. This sidecar cannot authorize
reuse, renew TTL, issue receipts or change the original entity/refresh DTO.
"""
from __future__ import annotations
import hashlib
import json

from iqs_temporal_vendor import (
    TimeSemanticsError, explain_observation_clocks, load_observation_clock_policies,
)

PROTOCOL = "iqs.temporal_shadow/1.0.0"
VIEW_PROTOCOL = "iqs.company_research_view/1.0.0"


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _refusal(row, code):
    return {"observation_id": row.get("observation_id"),
            "question_id": row.get("question_id"), "field_id": row.get("field_id"),
            "decision": "not_assessable", "reason_codes": [code],
            "current_context_verified": False, "reuse_authorized": False,
            "verification_receipt_available": False}


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
        result["clock_only_assessment"] = explain_observation_clocks(
            payload, policy["required_clocks"], now_utc=now_utc)
        result["reason_codes"] += result["clock_only_assessment"]["source_constraints"]["reason_codes"]
    except (TimeSemanticsError, ValueError, TypeError, KeyError) as error:
        result["reason_codes"].append(getattr(error, "error_code", "native_clock_not_assessable"))
    return result


def build_entity_view(detail, get_observation, *, entity_id, now_utc):
    """Wrap untouched original entity DTO; evaluate only exact visible native rows."""
    policies, bindings = load_observation_clock_policies()
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
