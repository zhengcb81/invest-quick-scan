"""Adapter for the public StockQA quick-scan result contract.

This module translates StockQA's stable JSON output into the route-specific
envelope owned by invest-quick-scan. It performs no I/O, provider calls, or
database access, so the contract can be tested independently of either owner.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

import module_contract as mc


QUICK_SCAN_RESULT_V1 = "stockqa.quick_scan_result/1.0.0"
ROUTE_QUESTION_ID = "ROUTE_02"
_SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"StockQA quick-scan field {field} must be non-empty text")
    return value


def _answer_hash(answer: dict) -> str:
    return hashlib.sha256(mc.canonical_bytes(answer)).hexdigest()


def adapt_quick_scan_result(result: dict, identity: dict) -> dict:
    """Validate and project a StockQA public result containing ROUTE_02.

    The receipt's ``answer_sha256`` is defined over the complete serialized
    public answer object, not an implementation-specific provider response.
    """
    if not isinstance(result, dict) or result.get("schema_version") != QUICK_SCAN_RESULT_V1:
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
