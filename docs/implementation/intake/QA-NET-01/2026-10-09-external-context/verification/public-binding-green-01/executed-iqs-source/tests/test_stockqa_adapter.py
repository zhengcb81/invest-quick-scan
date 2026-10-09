"""Unit tests for the public StockQA result boundary adapter; no network or I/O."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import module_contract as mc
import stockqa_adapter


IDENTITY = {
    "entity_id": "E_ADAPTER",
    "identity_ref": "fixture:E_ADAPTER:v1",
    "company": "Fixture Semiconductor Co.",
    "ticker": "FIXTURE",
    "exchange": "TEST",
    "as_of": "2026-09-19",
}


def public_result():
    sources = [
        {"module_id": "semiconductors", "confidence": "high", "evidence_type": "business_activity",
         "rationale": "Public operating evidence", "sources": [{
             "title": "Fixture only", "url": "https://example.invalid/semiconductors",
             "published_at": "2026-09-18", "entity_id": IDENTITY["entity_id"],
             "claim": "Fixture semiconductor operating evidence",
         }], "materiality": {"revenue_share": 0.7}},
    ]
    candidate = {"schema_version": "2.0.0", "question_id": "ROUTE_02", "candidates": sources}
    answer = {
        "question_id": "ROUTE_02", "status": "scored", "score": 8,
        "description": json.dumps(candidate, ensure_ascii=False),
        "source_urls": ["https://example.invalid/semiconductors"],
        "published_date": None, "information_as_of": None,
        "check_level": "unverified_model_output", "check_level_receipt_id": None,
    }
    answer_sha256 = hashlib.sha256(mc.canonical_bytes(answer)).hexdigest()
    receipt = {
        "answer_sha256": answer_sha256,
        "answered_at": "2026-09-20T11:59:00Z",
        "input_question_sha256": "a" * 64,
        "provider": "openai",
        "requested_model": "fixture-model-requested",
        "actual_model": "fixture-model-resolved",
        "request_id": "req_fixture",
        "attempt_id": "attempt_fixture",
        "search_receipt_id": "search_fixture",
        "search_status": "executed",
        "web_search_calls": [{
            "id": "search_fixture", "status": "completed", "action_type": "search",
            "source_urls": ["https://example.invalid/semiconductors"],
        }],
    }
    return {
        "schema_version": stockqa_adapter.QUICK_SCAN_RESULT_V1,
        "entity": {"entity_id": IDENTITY["entity_id"], "name": IDENTITY["company"]},
        "observed_at": "2026-09-20T12:00:00Z",
        "provider": {"name": "openai", "requested_model": "fixture-model-requested"},
        "answers": {"ROUTE_02": answer},
        "execution_receipts": {"ROUTE_02": receipt},
    }


class StockQAAdapterTests(unittest.TestCase):
    def test_adapts_public_answer_receipt_and_preserves_both_model_names(self):
        result = public_result()
        adapted = stockqa_adapter.adapt_quick_scan_result(result, IDENTITY)

        self.assertEqual(adapted["native_answer"]["entity_id"], IDENTITY["entity_id"])
        self.assertEqual(adapted["classification_confidence"], {"status": "scored", "score": 8})
        self.assertEqual(adapted["execution_receipt"]["model_requested"], "fixture-model-requested")
        self.assertEqual(adapted["execution_receipt"]["model_resolved"], "fixture-model-resolved")
        self.assertEqual(adapted["execution_receipt"]["prompt_sha256"], "a" * 64)
        self.assertEqual(adapted["answer_sha256"], result["execution_receipts"]["ROUTE_02"]["answer_sha256"])

    def test_rejects_answer_changed_after_receipt_creation(self):
        result = public_result()
        result["answers"]["ROUTE_02"]["score"] = 9
        with self.assertRaisesRegex(ValueError, "does not bind the public answer hash"):
            stockqa_adapter.adapt_quick_scan_result(result, IDENTITY)

    def test_rejects_cross_company_result_even_when_answer_hash_is_valid(self):
        result = public_result()
        result["entity"]["entity_id"] = "E_OTHER"
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            stockqa_adapter.adapt_quick_scan_result(result, IDENTITY)

    def test_rejects_unverified_search(self):
        result = public_result()
        result["execution_receipts"]["ROUTE_02"]["search_status"] = "unverified"
        with self.assertRaisesRegex(ValueError, "requires a verified completed search"):
            stockqa_adapter.adapt_quick_scan_result(result, IDENTITY)

    def test_rejects_answer_sources_outside_completed_search(self):
        result = public_result()
        answer = result["answers"]["ROUTE_02"]
        answer["source_urls"] = ["https://example.invalid/unsearched"]
        result["execution_receipts"]["ROUTE_02"]["answer_sha256"] = hashlib.sha256(
            mc.canonical_bytes(answer)
        ).hexdigest()
        with self.assertRaisesRegex(ValueError, "outside its completed search"):
            stockqa_adapter.adapt_quick_scan_result(result, IDENTITY)


if __name__ == "__main__":
    unittest.main()
