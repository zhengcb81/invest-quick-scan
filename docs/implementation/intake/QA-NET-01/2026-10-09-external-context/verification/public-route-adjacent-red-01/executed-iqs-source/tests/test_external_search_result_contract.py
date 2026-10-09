"""Synthetic public-wire compatibility tests; no source or fact authentication.

The producer's real-store tests live in the isolated StockQA copy. These pure
consumer tests verify binding consistency and routing, never owner goldens.
"""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import module_contract as mc
import routing
import stockqa_adapter
import test_stockqa_adapter as native_fixtures
import test_routing as routing_fixtures


def _native_hash(receipt):
    return hashlib.sha256(json.dumps(receipt, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _rehash(proof):
    proof["proof_sha256"] = mc.digest({k: v for k, v in proof.items() if k != "proof_sha256"})


def external_result(*, hybrid=False, identity=None, candidates=None, question_sha=None):
    result = native_fixtures.public_result()
    identity = identity or native_fixtures.IDENTITY
    result["entity"] = {"entity_id": identity["entity_id"], "name": identity["company"]}
    result["schema_version"] = "stockqa.quick_scan_result/1.1.0"
    answer, receipt = result["answers"]["ROUTE_02"], result["execution_receipts"]["ROUTE_02"]
    if candidates is not None:
        answer["description"] = json.dumps({"schema_version": "2.0.0", "question_id": "ROUTE_02", "candidates": candidates})
        answer["source_urls"] = list(dict.fromkeys(s["url"] for fact in candidates for s in fact["sources"]))
    external_urls = answer["source_urls"][:]
    native_urls = ["https://native.example/ir"] if hybrid else []
    answer["source_urls"] = native_urls + external_urls
    receipt.update(input_question_sha256=question_sha or receipt["input_question_sha256"],
        response_id="response_fixture", response_status="completed", http_status_code=200,
        source_urls=answer["source_urls"], prompt_sha256="b" * 64)
    original = {"provider": receipt["provider"], "requested_model": receipt["requested_model"],
        "actual_model": receipt["actual_model"], "request_id": receipt["request_id"],
        "response_id": receipt["response_id"], "attempt_id": receipt["attempt_id"],
        "response_status": "completed", "http_status_code": 200,
        "search_protocol": "responses", "response_sha256": "f" * 64,
        "response_json_basis": "provider_body", "model_resolution_sha256": "e" * 64,
        "prompt_sha256": "b" * 64, "completed_at": "2026-09-20T11:58:30Z",
        "search_status": "executed" if hybrid else "unverified",
        "search_receipt_id": "native_search_fixture" if hybrid else None,
        "source_urls": native_urls}
    receipt["web_search_calls"] = ([{"id": "native_search_fixture", "status": "completed",
        "action_type": "search", "source_urls": native_urls}] if hybrid else [])
    proof = {"schema": "stockqa.external_context_use/1.1.0", "state": "request_and_response_bound",
        "use_id": "EXTUSE_fixture", "work_item_id": "WORK_fixture",
        "work_attempt_id": "WORK_ATTEMPT_fixture",  # Distinct from the HTTP attempt ID.
        "context_sha256": "c" * 64, "question_manifest_sha256": "d" * 64,
        "answer_search_mode": "native_with_external_context" if hybrid else "external_context_only",
        "request_prompt_sha256": "9" * 64, "llm_receipt_sha256": _native_hash(original),
        "provider": receipt["provider"], "actual_model": receipt["actual_model"],
        "used_at": datetime(2026, 9, 20, 11, 58, 31, tzinfo=timezone.utc).timestamp(),
        "retrievals": [{"operation_id": "SEARCH_fixture", "query_id": "issuer",
            "route_id": "brave-primary", "route_kind": "brave", "receipt_sha256": "1" * 64,
            "retrieved_at": "2026-09-20T11:58:00Z"}], "source_urls": external_urls}
    _rehash(proof)
    receipt.update(search_receipt_id=proof["use_id"], answer_sha256=mc.digest(answer),
        search_binding={"schema": "stockqa.search_binding/1.1.0",
            "entity_id": identity["entity_id"], "question_id": "ROUTE_02",
            "identity_snapshot_sha256": "a" * 64, "external_context_use": proof, "native_receipt": original})
    return result


class ExternalSearchAdapterTests(unittest.TestCase):
    def test_external_and_hybrid_keep_native_events_separate(self):
        for hybrid in (False, True):
            with self.subTest(hybrid=hybrid):
                result = external_result(hybrid=hybrid)
                original = copy.deepcopy(result)
                adapted = stockqa_adapter.adapt_quick_scan_result(result, native_fixtures.IDENTITY)
                receipt = adapted["execution_receipt"]
                self.assertEqual(receipt["search_receipt_id"], "EXTUSE_fixture")
                self.assertEqual(receipt["web_search_calls"], result["execution_receipts"]["ROUTE_02"]["web_search_calls"])
                self.assertEqual(receipt["search_binding"], result["execution_receipts"]["ROUTE_02"]["search_binding"])
                self.assertEqual(result, original)
                self.assertEqual(adapted["classification_confidence"], {"status": "scored", "score": 8})

    def test_native_v1_and_native_v1_1_keep_the_existing_projection(self):
        result = native_fixtures.public_result()
        original = stockqa_adapter.adapt_quick_scan_result(result, native_fixtures.IDENTITY)
        result["schema_version"] = "stockqa.quick_scan_result/1.1.0"
        self.assertEqual(stockqa_adapter.adapt_quick_scan_result(result, native_fixtures.IDENTITY), original)

    def test_consumer_rejects_neighboring_binding_corruption_even_when_rehashed(self):
        # Baseline must be accepted first: version-wide rejection proves no negative.
        stockqa_adapter.adapt_quick_scan_result(external_result(), native_fixtures.IDENTITY)
        for kind in ("old_version", "entity", "question", "missing_native", "proof_hash", "native_hash",
                     "model", "provider", "use_id", "foreign_url", "future_retrieval", "future_use",
                     "empty_retrieval", "duplicate_retrieval", "extra_proof", "native_events", "http_bool",
                     "identity_revision", "unknown_mode"):
            with self.subTest(kind=kind):
                result = external_result()
                receipt = result["execution_receipts"]["ROUTE_02"]
                binding = receipt["search_binding"]
                proof = binding["external_context_use"]
                identity = dict(native_fixtures.IDENTITY)
                if kind == "old_version": result["schema_version"] = stockqa_adapter.QUICK_SCAN_RESULT_V1
                elif kind == "entity": binding["entity_id"] = "FOREIGN"
                elif kind == "question": binding["question_id"] = "IQS_99"
                elif kind == "missing_native": del binding["native_receipt"]
                elif kind == "proof_hash": proof["proof_sha256"] = "0" * 64
                elif kind == "native_hash": binding["native_receipt"]["response_id"] = "another"
                elif kind == "model": proof["actual_model"] = "another-model"; _rehash(proof)
                elif kind == "provider": proof["provider"] = "mimo"; _rehash(proof)
                elif kind == "use_id": receipt["search_receipt_id"] = "another-use"
                elif kind == "foreign_url":
                    result["answers"]["ROUTE_02"]["source_urls"] = ["https://foreign.example/ir"]
                    receipt["answer_sha256"] = mc.digest(result["answers"]["ROUTE_02"])
                elif kind == "future_retrieval": proof["retrievals"][0]["retrieved_at"] = "2027-01-01T00:00:00Z"; _rehash(proof)
                elif kind == "future_use": proof["used_at"] += 300; _rehash(proof)
                elif kind == "empty_retrieval": proof["retrievals"] = []; _rehash(proof)
                elif kind == "duplicate_retrieval": proof["retrievals"] *= 2; _rehash(proof)
                elif kind == "extra_proof": proof["audited"] = True; _rehash(proof)
                elif kind == "native_events": receipt["web_search_calls"] = [{"id": "invented", "status": "completed", "action_type": "search", "source_urls": proof["source_urls"]}]
                elif kind == "http_bool":
                    binding["native_receipt"]["http_status_code"] = True
                    proof["llm_receipt_sha256"] = _native_hash(binding["native_receipt"]); _rehash(proof)
                elif kind == "identity_revision": identity["identity_snapshot_sha256"] = "0" * 64
                elif kind == "unknown_mode": proof["answer_search_mode"] = "model_claimed_search"; _rehash(proof)
                with self.assertRaises(ValueError):
                    stockqa_adapter.adapt_quick_scan_result(result, identity)


class ExternalSearchRoutingTests(unittest.TestCase):
    def setUp(self):
        self.fixture = routing_fixtures.RoutingFixture()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_public_external_result_drives_existing_module_routing_and_replays(self):
        fixture = self.fixture
        request = routing.build_route_request(fixture.identity, package_id=fixture.package_id, root=fixture.root)
        for hybrid in (False, True):
            with self.subTest(hybrid=hybrid):
                result = external_result(hybrid=hybrid, identity=fixture.identity,
                    candidates=fixture.normal(), question_sha=request["prompt_sha256"])
                decision = routing.resolve_route_decision({**fixture.identity, "verified_facts": []},
                    package_id=fixture.package_id, root=fixture.root, route_response=result, now_utc=fixture.now)
                self.assertIn("semiconductors", fixture.selected(decision))
                self.assertIn("scaling", fixture.selected(decision))
                self.assertEqual(decision["execution"]["search_receipt_id"], "EXTUSE_fixture")
                routing.validate_route_snapshot(decision, root=fixture.root)
                routing.validate_route_for_execution(decision, root=fixture.root, now_utc=fixture.now,
                    expected_decision_id=decision["decision_id"])
                corrupted = copy.deepcopy(decision)
                corrupted["execution"]["search_binding"]["external_context_use"]["source_urls"] = ["https://foreign.example/ir"]
                _rehash(corrupted["execution"]["search_binding"]["external_context_use"])
                corrupted = mc.seal_route_decision({k: v for k, v in corrupted.items() if k != "decision_id"})
                with self.assertRaises(ValueError): routing.validate_route_snapshot(corrupted, root=fixture.root)

    def test_low_confidence_route_cannot_skip_external_receipt_validation(self):
        fixture = self.fixture
        request = routing.build_route_request(fixture.identity, package_id=fixture.package_id, root=fixture.root)
        result = external_result(identity=fixture.identity, candidates=fixture.normal(), question_sha=request["prompt_sha256"])
        answer = result["answers"]["ROUTE_02"]
        answer["score"] = 2
        result["execution_receipts"]["ROUTE_02"]["answer_sha256"] = mc.digest(answer)
        decision = routing.resolve_route_decision({**fixture.identity, "verified_facts": []},
            package_id=fixture.package_id, root=fixture.root, route_response=result, now_utc=fixture.now)
        self.assertNotIn("semiconductors", fixture.selected(decision))
        decision["execution"]["search_binding"]["external_context_use"]["proof_sha256"] = "0" * 64
        decision = mc.seal_route_decision({k: v for k, v in decision.items() if k != "decision_id"})
        with self.assertRaises(ValueError): routing.validate_route_snapshot(decision, root=fixture.root)

    def test_trusted_caller_identity_snapshot_is_checked_before_routing(self):
        fixture = self.fixture
        request = routing.build_route_request(fixture.identity, package_id=fixture.package_id, root=fixture.root)
        result = external_result(identity=fixture.identity, candidates=fixture.normal(), question_sha=request["prompt_sha256"])
        with self.assertRaises(ValueError):
            routing.parse_route_response(result, {**fixture.identity, "identity_snapshot_sha256": "0" * 64})


if __name__ == "__main__":
    unittest.main()
