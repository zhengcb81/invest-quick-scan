"""Pure offline reference rules for the C06 exchange/query contract.

This module performs no persistence, networking, identity resolution, or LLM
calls. StockWiki and StockQA must implement and test the corresponding public
transactions in their own repositories.
"""
from __future__ import annotations

import hashlib
import json
import copy


_FORBIDDEN_EVIDENCE_KEYS = {
    "source_manifest", "source_manifest_id", "source_manifest_ids",
    "evidence_span", "evidence_span_id", "evidence_span_ids",
    "accepted_ids", "raw_document", "document_body", "document_text",
}


def canonical_bytes(value: object) -> bytes:
    """UTF-8 canonical JSON used only for deterministic exchange hashes."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def validate_package_integrity(package: dict) -> None:
    """Recompute every content address after the package schema is validated."""
    for item in package["items"]:
        observation = item["observation"]
        if observation.get("observation_id") != item["observation_id"]:
            raise ValueError("exchange item observation_id does not match its payload")
        payload_hash = canonical_sha256(observation)
        if item["payload_sha256"] != payload_hash:
            raise ValueError("exchange item payload_sha256 does not match its observation")
        item_seed = {"observation_id": item["observation_id"], "payload_sha256": payload_hash}
        expected_item_id = "itm_" + canonical_sha256(item_seed)
        if item["item_id"] != expected_item_id:
            raise ValueError("exchange item_id does not match its observation content address")

    package_body = {
        key: value for key, value in package.items() if key not in {"package_id", "package_sha256"}
    }
    package_hash = canonical_sha256(package_body)
    if package["package_sha256"] != package_hash:
        raise ValueError("exchange package_sha256 does not match its content")
    if package["package_id"] != "pkg_" + package_hash:
        raise ValueError("exchange package_id does not match its content address")


def _contains_forbidden_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(str(key).casefold() in _FORBIDDEN_EVIDENCE_KEYS
                   or _contains_forbidden_key(child)
                   for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(child) for child in value)
    return False


def build_package(observations: list[dict], *, created_at: str,
                  producer_version: str, build_id: str,
                  contract_versions: dict) -> dict:
    """Create a content-addressed package without mutating observations."""
    if not observations:
        raise ValueError("exchange package must contain at least one observation")
    items = []
    for observation in observations:
        if _contains_forbidden_key(observation):
            raise ValueError("formal source artifacts or raw documents are not exchange payloads")
        detached_observation = copy.deepcopy(observation)
        observation_id = detached_observation.get("observation_id")
        if not isinstance(observation_id, str) or not observation_id.startswith("obs_"):
            raise ValueError("observation must carry its existing immutable observation_id")
        payload_hash = canonical_sha256(detached_observation)
        item_seed = {"observation_id": observation_id, "payload_sha256": payload_hash}
        items.append({"item_id": "itm_" + canonical_sha256(item_seed),
                      "observation_id": observation_id,
                      "payload_sha256": payload_hash,
                      "observation": detached_observation})
    package = {
        "schema_version": "1.0.0",
        "producer": {"component": "StockQAbyLLM", "component_version": producer_version,
                     "build_id": build_id},
        "consumer": {"component": "StockWiki", "namespace": "quick_scan",
                     "minimum_schema_version": "1.0.0"},
        "created_at": created_at,
        "data_class": "lightweight_screening",
        "required_capabilities": ["entity_security_identity_v1", "standard_observation_v1"],
        "contract_versions": copy.deepcopy(contract_versions),
        "document_payloads_included": False,
        "items": items,
        "extensions": [],
    }
    package_hash = canonical_sha256(package)
    package["package_sha256"] = package_hash
    package["package_id"] = "pkg_" + package_hash
    return package


def import_decision(*, observation_id: str, incoming_payload_hash: str,
                    existing_payload_hash: str | None, entity_exists: bool,
                    question_known: bool, schema_supported: bool,
                    payload: dict) -> tuple[str, str | None]:
    """Return an ACK decision; never writes or chooses last-write-wins."""
    if not schema_supported:
        return "rejected", "unsupported_schema"
    if not entity_exists:
        return "rejected", "missing_entity"
    if not question_known:
        return "rejected", "unknown_question"
    if _contains_forbidden_key(payload):
        return "rejected", "invalid_payload"
    if canonical_sha256(payload) != incoming_payload_hash:
        return "rejected", "invalid_payload"
    if payload.get("observation_id") != observation_id:
        return "rejected", "invalid_payload"
    if existing_payload_hash is None:
        return "accepted", None
    if existing_payload_hash == incoming_payload_hash:
        return "already_present", None
    return "conflict", "immutable_key_hash_conflict"


def search_status(match_count: int, coverage_status: str) -> str:
    """Do not turn an uncovered query into a claim that no companies exist."""
    if isinstance(match_count, bool) or not isinstance(match_count, int) or match_count < 0:
        raise ValueError("match_count must be a non-negative integer")
    if coverage_status not in {"complete", "partial", "not_covered", "unknown"}:
        raise ValueError("invalid coverage status")
    if coverage_status in {"not_covered", "unknown"}:
        return "coverage_gap"
    if coverage_status == "partial":
        return "partial"
    return "empty" if match_count == 0 else "ok"


def refresh_preview(*, requested_entities: list[str], requested_fields: list[str],
                    allowed_entities: set[str], field_states: dict,
                    budget_available: bool) -> dict:
    """Restrict a preview to the exact request; valid fields are reused."""
    if len(set(requested_entities)) != len(requested_entities) or len(set(requested_fields)) != len(requested_fields):
        raise ValueError("duplicate entities or fields in refresh request")
    if set(requested_entities) - allowed_entities:
        return {"status": "out_of_scope", "eligible": [], "reused": [], "rejected_scope": sorted(set(requested_entities) - allowed_entities), "dispatch_started": False}
    eligible, reused, invalid = [], [], []
    for entity_id in requested_entities:
        states = field_states.get(entity_id, {})
        for field_id in requested_fields:
            state = states.get(field_id)
            if state in {"fresh", "reusable"}:
                reused.append((entity_id, field_id))
            elif state in {"missing", "stale", "event_invalidated", "unknown"}:
                eligible.append((entity_id, field_id))
            else:
                invalid.append(f"{entity_id}:{field_id}")
    if invalid:
        return {"status": "out_of_scope", "eligible": [], "reused": reused, "rejected_scope": invalid, "dispatch_started": False}
    if not budget_available and eligible:
        return {"status": "budget_unavailable", "eligible": [], "reused": reused, "rejected_scope": [], "dispatch_started": False}
    return {"status": "preview_ready" if eligible else "no_gap",
            "eligible": eligible, "reused": reused, "rejected_scope": [], "dispatch_started": False}


def independent_support(
    target_observation_id: str,
    candidate_observation_id: str,
    lineage_by_observation: dict[str, list[str]],
) -> bool:
    """Return true only when a complete, acyclic lineage proves independence.

    Every visited observation must be present in ``lineage_by_observation``.
    Missing ancestry is unknown and therefore cannot be counted as independent.
    """
    if target_observation_id == candidate_observation_id:
        return False
    if candidate_observation_id not in lineage_by_observation:
        return False
    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(observation_id: str) -> bool:
        if observation_id == target_observation_id:
            return False
        if observation_id in visiting:
            return False
        if observation_id in visited:
            return True
        upstream = lineage_by_observation.get(observation_id)
        if not isinstance(upstream, list) or any(not isinstance(item, str) for item in upstream):
            return False
        visiting.add(observation_id)
        for parent in upstream:
            if parent not in lineage_by_observation or not walk(parent):
                return False
        visiting.remove(observation_id)
        visited.add(observation_id)
        return True

    return walk(candidate_observation_id)
