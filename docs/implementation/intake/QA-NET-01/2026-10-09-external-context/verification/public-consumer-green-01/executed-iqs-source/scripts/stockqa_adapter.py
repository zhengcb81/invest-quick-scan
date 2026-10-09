"""Adapter for the public StockQA quick-scan result contract.

This module translates StockQA's stable JSON output into the route-specific
envelope owned by invest-quick-scan. It performs no I/O, provider calls, or
database access, so the contract can be tested independently of either owner.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

import module_contract as mc


QUICK_SCAN_RESULT_V1 = "stockqa.quick_scan_result/1.0.0"
QUICK_SCAN_RESULT_V1_1 = "stockqa.quick_scan_result/1.1.0"
SUPPORTED_RESULT_VERSIONS = frozenset({QUICK_SCAN_RESULT_V1, QUICK_SCAN_RESULT_V1_1})
ROUTE_QUESTION_ID = "ROUTE_02"
_SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"StockQA quick-scan field {field} must be non-empty text")
    return value


def _answer_hash(answer: dict) -> str:
    return hashlib.sha256(mc.canonical_bytes(answer)).hexdigest()


def _instant(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("external search time must be explicit")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid external search time") from error
    if instant.tzinfo is None:
        raise ValueError("external search time requires a timezone")
    return instant.astimezone(timezone.utc)


def _urls(value: Any) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(url, str) for url in value):
        raise ValueError("external search URLs must be a list")
    if len(value) != len(set(value)):
        raise ValueError("external search URLs must be unique")
    for url in value:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("invalid external search source URL")
    return value


def external_search_urls(receipt: dict, *, entity_id: str, question_id: str,
                         identity_snapshot_sha256: str | None = None,
                         route_receipt: bool = False) -> frozenset[str]:
    """Check a trusted producer's public binding; this is not store authentication.

    Only StockQA can authenticate the persisted retrieval/use/HTTP chain. A
    self-consistent caller dictionary or hash is not independently certified
    evidence, and this pure consumer never upgrades the answer's check level.
    """
    binding = receipt.get("search_binding")
    fields = {"schema", "entity_id", "question_id", "identity_snapshot_sha256", "external_context_use", "native_receipt"}
    if (not isinstance(binding, dict) or set(binding) != fields
            or binding["schema"] != "stockqa.search_binding/1.1.0"
            or binding["entity_id"] != entity_id or binding["question_id"] != question_id
            or not isinstance(binding["identity_snapshot_sha256"], str)
            or not _SHA256.fullmatch(binding["identity_snapshot_sha256"])
            or identity_snapshot_sha256 is not None and binding["identity_snapshot_sha256"] != identity_snapshot_sha256):
        raise ValueError("invalid external search identity binding")
    proof, native = binding["external_context_use"], binding["native_receipt"]
    proof_fields = {"schema", "state", "use_id", "work_item_id", "work_attempt_id", "context_sha256",
        "question_manifest_sha256", "answer_search_mode", "request_prompt_sha256", "llm_receipt_sha256",
        "provider", "actual_model", "used_at", "retrievals", "source_urls", "proof_sha256"}
    if (not isinstance(proof, dict) or set(proof) != proof_fields
            or proof["schema"] != "stockqa.external_context_use/1.1.0"
            or proof["state"] != "request_and_response_bound"):
        raise ValueError("invalid external search use binding")
    for key in ("context_sha256", "question_manifest_sha256", "request_prompt_sha256", "llm_receipt_sha256", "proof_sha256"):
        if not isinstance(proof[key], str) or not _SHA256.fullmatch(proof[key]):
            raise ValueError("invalid external search digest")
    if proof["proof_sha256"] != mc.digest({k: v for k, v in proof.items() if k != "proof_sha256"}):
        raise ValueError("external search use digest mismatch")
    for key in ("use_id", "work_item_id", "work_attempt_id", "provider", "actual_model"):
        _required_text(proof[key], key)
    native_fields = {"provider", "request_id", "response_id", "actual_model", "requested_model", "search_protocol",
        "response_sha256", "response_json_basis", "model_resolution_sha256", "search_status", "response_status",
        "http_status_code", "attempt_id", "prompt_sha256", "search_receipt_id", "failure_type", "provider_error_code",
        "retry_after_seconds", "completed_at", "source_urls", "usage"}
    if not isinstance(native, dict) or set(native) - native_fields:
        raise ValueError("invalid external original receipt")
    native_sha = hashlib.sha256(json.dumps(native, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if native_sha != proof["llm_receipt_sha256"]:
        raise ValueError("external original receipt digest mismatch")
    requested_key, actual_key = ("model_requested", "model_resolved") if route_receipt else ("requested_model", "actual_model")
    for target, original in (("provider", "provider"), (requested_key, "requested_model"),
                             (actual_key, "actual_model"), ("attempt_id", "attempt_id")):
        if _required_text(native.get(original), original) != receipt.get(target):
            raise ValueError("external original receipt model or attempt mismatch")
    if (proof["provider"] != native["provider"] or proof["actual_model"] != native["actual_model"]
            or receipt.get("search_status") != "executed" or receipt.get("search_receipt_id") != proof["use_id"]
            or type(native.get("http_status_code")) is not int or not 200 <= native["http_status_code"] < 300
            or native.get("response_status") != "completed"):
        raise ValueError("external use differs from the actual completed response")
    for key in ("response_id", "search_protocol", "response_json_basis"):
        _required_text(native.get(key), key)
    for key in ("response_sha256", "model_resolution_sha256", "prompt_sha256"):
        if not isinstance(native.get(key), str) or not _SHA256.fullmatch(native[key]):
            raise ValueError("external original receipt is missing response provenance")
    if not route_receipt:
        for key in ("request_id", "response_id", "response_status", "http_status_code", "prompt_sha256"):
            if receipt.get(key) != native.get(key):
                raise ValueError("external public receipt differs from original HTTP receipt")
    if type(proof["used_at"]) not in (int, float) or not math.isfinite(proof["used_at"]):
        raise ValueError("invalid external use time")
    try:
        used = datetime.fromtimestamp(proof["used_at"], timezone.utc)
    except (ValueError, OverflowError, OSError) as error:
        raise ValueError("invalid external use time") from error
    if _instant(native.get("completed_at")) > used or used > _instant(receipt.get("answered_at")):
        raise ValueError("external use time differs from completed answer")
    refs = proof["retrievals"]
    ref_fields = {"operation_id", "query_id", "route_id", "route_kind", "receipt_sha256", "retrieved_at"}
    if (not isinstance(refs, list) or not refs or any(not isinstance(ref, dict) or set(ref) != ref_fields for ref in refs)):
        raise ValueError("invalid external retrieval references")
    operations = set()
    for ref in refs:
        for key in ("operation_id", "query_id", "route_id"):
            _required_text(ref[key], key)
        if (ref["operation_id"] in operations or ref["route_kind"] not in {"brave", "tavily", "zai_rest", "zai_mcp_streamable"}
                or not isinstance(ref["receipt_sha256"], str) or not _SHA256.fullmatch(ref["receipt_sha256"])
                or _instant(ref["retrieved_at"]) > _instant(native["completed_at"])):
            raise ValueError("external retrieval reference or time mismatch")
        operations.add(ref["operation_id"])
    external_urls, native_urls = _urls(proof["source_urls"]), _urls(native.get("source_urls", []))
    calls = receipt.get("web_search_calls")
    if not isinstance(calls, list) or not external_urls:
        raise ValueError("external search has no actual source URLs")
    if proof["answer_search_mode"] == "external_context_only":
        if native.get("search_status") != "unverified" or native.get("search_receipt_id") is not None or native_urls or calls:
            raise ValueError("external-only output must not invent native events")
    elif proof["answer_search_mode"] == "native_with_external_context":
        completed = [call for call in calls if isinstance(call, dict) and call.get("status") == "completed"
                     and call.get("action_type") == "search" and isinstance(call.get("source_urls"), list)]
        completed_urls = {url for call in completed for url in _urls(call["source_urls"])}
        if (native.get("search_status") != "executed" or not native_urls
                or len([call for call in completed if call.get("id") == native.get("search_receipt_id")]) != 1
                or not set(native_urls) <= completed_urls):
            raise ValueError("hybrid output requires completed original native sources")
    else:
        raise ValueError("unknown external search mode")
    return frozenset([*native_urls, *external_urls])


def adapt_quick_scan_result(result: dict, identity: dict) -> dict:
    """Validate and project a StockQA public result containing ROUTE_02.

    The receipt's ``answer_sha256`` is defined over the complete serialized
    public answer object, not an implementation-specific provider response.
    """
    if not isinstance(result, dict) or result.get("schema_version") not in SUPPORTED_RESULT_VERSIONS:
        raise ValueError("unsupported StockQA quick-scan result version")
    if not isinstance(identity, dict) or not isinstance(result.get("entity"), dict):
        raise ValueError("StockQA quick-scan result is missing trusted entity identity")
    entity = result["entity"]
    entity_id = _required_text(entity.get("entity_id"), "entity.entity_id")
    company_name = _required_text(entity.get("name"), "entity.name")
    if entity_id != identity.get("entity_id") or company_name != identity.get("company"):
        raise ValueError("StockQA quick-scan result identity mismatch")

    answers = result.get("answers")
    receipts = result.get("execution_receipts")
    if not isinstance(answers, dict) or not isinstance(receipts, dict):
        raise ValueError("StockQA quick-scan result requires answers and execution_receipts maps")
    answer = answers.get(ROUTE_QUESTION_ID)
    receipt = receipts.get(ROUTE_QUESTION_ID)
    if not isinstance(answer, dict) or not isinstance(receipt, dict):
        raise ValueError("StockQA quick-scan result is missing the ROUTE_02 answer or receipt")

    answer_required = {
        "question_id", "status", "score", "description", "source_urls",
        "published_date", "information_as_of", "check_level", "check_level_receipt_id",
    }
    if not answer_required <= answer.keys() or answer["question_id"] != ROUTE_QUESTION_ID:
        raise ValueError("StockQA ROUTE_02 answer has an invalid public shape")
    if answer["check_level"] != "unverified_model_output" or answer["check_level_receipt_id"] is not None:
        raise ValueError("StockQA model output cannot self-grant an audited check level")
    status = answer["status"]
    score = answer["score"]
    if status not in {"scored", "unknown", "insufficient_evidence"}:
        raise ValueError("invalid StockQA route classification status")
    if ((status == "scored" and (type(score) is not int or not 1 <= score <= 10))
            or (status != "scored" and score is not None)):
        raise ValueError("StockQA route classification status and score disagree")
    description = answer["description"]
    if not isinstance(description, str):
        raise ValueError("StockQA route description must contain serialized candidate JSON")
    candidate = json.loads(description, object_pairs_hook=mc._unique_object)
    if (not isinstance(candidate, dict)
            or set(candidate) != {"schema_version", "question_id", "candidates"}
            or candidate["schema_version"] != "2.0.0"
            or candidate["question_id"] != ROUTE_QUESTION_ID
            or not isinstance(candidate["candidates"], list)):
        raise ValueError("invalid StockQA route candidate envelope")
    if (status == "scored" and not candidate["candidates"]
            or status != "scored" and candidate["candidates"]):
        raise ValueError("StockQA route classification status disagrees with candidate content")

    computed_answer_sha256 = _answer_hash(answer)
    recorded_answer_sha256 = receipt.get("answer_sha256")
    if (not isinstance(recorded_answer_sha256, str) or not _SHA256.fullmatch(recorded_answer_sha256)
            or recorded_answer_sha256 != computed_answer_sha256):
        raise ValueError("StockQA execution receipt does not bind the public answer hash")

    if receipt.get("search_status") != "executed":
        raise ValueError("StockQA ROUTE_02 requires a verified completed search")
    requested_model = _required_text(receipt.get("requested_model"), "requested_model")
    actual_model = _required_text(receipt.get("actual_model"), "actual_model")
    provider = _required_text(receipt.get("provider"), "provider")
    attempt_id = _required_text(receipt.get("attempt_id"), "attempt_id")
    search_receipt_id = _required_text(receipt.get("search_receipt_id"), "search_receipt_id")
    input_question_sha256 = receipt.get("input_question_sha256")
    if not isinstance(input_question_sha256, str) or not _SHA256.fullmatch(input_question_sha256):
        raise ValueError("StockQA receipt is missing its input question hash")
    web_search_calls = receipt.get("web_search_calls")
    if not isinstance(web_search_calls, list):
        raise ValueError("StockQA receipt web_search_calls must be a list")
    source_urls = answer.get("source_urls")
    if not isinstance(source_urls, list) or any(not isinstance(url, str) for url in source_urls):
        raise ValueError("StockQA route source_urls must be a list of strings")
    if "search_binding" in receipt:
        if result["schema_version"] != QUICK_SCAN_RESULT_V1_1:
            raise ValueError("external search binding requires public result version 1.1")
        completed_urls = external_search_urls(receipt, entity_id=entity_id, question_id=ROUTE_QUESTION_ID,
            identity_snapshot_sha256=identity.get("identity_snapshot_sha256"))
        if receipt.get("source_urls") != source_urls or not set(source_urls) <= completed_urls:
            raise ValueError("StockQA route answer cites a URL outside its external search binding")
    else:
        completed_urls = {
            url
            for call in web_search_calls
            if isinstance(call, dict) and call.get("status") == "completed"
            and call.get("action_type") == "search" and isinstance(call.get("source_urls"), list)
            for url in call["source_urls"] if isinstance(url, str)
        }
    if source_urls and not set(source_urls) <= completed_urls:
        raise ValueError("StockQA route answer cites a URL outside its completed search receipt")

    route_receipt = {
        "provider": provider,
        "model_requested": requested_model,
        "model_resolved": actual_model,
        "model_revision": actual_model,
        "attempt_id": attempt_id,
        "search_receipt_id": search_receipt_id,
        "web_search_calls": copy.deepcopy(web_search_calls),
        "entity_id": entity_id,
        "request_id": receipt.get("request_id"),
        "search_status": "executed",
        "classification_status": status,
        "classification_score": score,
        "prompt_sha256": input_question_sha256,
        "answer_sha256": computed_answer_sha256,
        "as_of": identity["as_of"],
        "answered_at": receipt.get("answered_at"),
    }
    if not isinstance(route_receipt["answered_at"], str) or not route_receipt["answered_at"].strip():
        raise ValueError("StockQA receipt is missing answered_at")
    if "search_binding" in receipt:
        route_receipt["search_binding"] = copy.deepcopy(receipt["search_binding"])
    native_answer = {
        "question_id": ROUTE_QUESTION_ID,
        "entity_id": entity_id,
        "company_name": company_name,
        "status": status,
        "score": score,
        "description": description,
    }
    return {
        "native_answer": native_answer,
        "candidate": candidate,
        "classification_confidence": {"status": status, "score": score},
        "execution_receipt": route_receipt,
        "answer_sha256": computed_answer_sha256,
    }
