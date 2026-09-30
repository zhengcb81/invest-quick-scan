"""Regression tests for counterexamples found by the independent G0 review."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft7Validator, Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import contract_validation as cv
import deployment_contract as dc
import exchange_contract as ec


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


SCORE = load("schemas/quick_scan/score.schema.json")
METRIC = load("schemas/quick_scan/metric.schema.json")
RULE = load("schemas/quick_scan/rule.schema.json")
EXCHANGE = load("schemas/quick_scan/exchange.schema.json")
DEPLOYMENT = load("schemas/quick_scan/deployment.schema.json")
PACKAGE = load("examples/quick_scan/exchange-package.example.json")
DEPLOYMENT_EXAMPLES = load("examples/quick_scan/deployment-contract.examples.json")
QUERY_EXAMPLES = load("examples/quick_scan/query-contract.examples.json")


class G0RegressionTests(unittest.TestCase):
    def test_g0_01_score_state_is_closed_and_level_requires_trusted_receipt(self):
        bad_high = {
            "question_id": "IQS_01", "status": "insufficient_evidence", "score": 10,
            "description": "missing", "check_level": "unverified_model_output",
            "check_level_receipt_id": None,
        }
        bad_null = {**bad_high, "status": "scored", "score": None}
        for value in (bad_high, bad_null):
            with self.assertRaises(ValidationError):
                Draft7Validator(SCORE).validate(value)

        self_awarded = {
            "question_id": "IQS_01", "status": "scored", "score": 8,
            "description": "claim", "check_level": "formal_research_accepted",
            "check_level_receipt_id": "RCP_FORGED",
        }
        with self.assertRaises(ValueError):
            cv.validate_parsed_answer(self_awarded)
        receipt = {
            "receipt_id": "RCP_FORGED", "entity_id": "ENT_A",
            "question_id": "IQS_01", "observation_id": "OBS_A",
            "authorized_check_level": "formal_research_accepted",
            "issuer": "invest-core", "status": "active",
        }
        receipt["receipt_sha256"] = ec.canonical_sha256(receipt)
        cv.validate_parsed_answer(
            self_awarded, trusted_check_level_receipts={"RCP_FORGED": receipt},
            expected_entity_id="ENT_A", expected_observation_id="OBS_A",
        )
        mutations = [
            {"entity_id": "ENT_OTHER"}, {"question_id": "IQS_02"},
            {"observation_id": "OBS_OTHER"},
            {"authorized_check_level": "execution_verified", "issuer": "stockqa"},
            {"status": "revoked"},
        ]
        for change in mutations:
            bad = {**receipt, **change}
            bad.pop("receipt_sha256")
            bad["receipt_sha256"] = ec.canonical_sha256(bad)
            with self.assertRaises(ValueError):
                cv.validate_parsed_answer(
                    self_awarded, trusted_check_level_receipts={"RCP_FORGED": bad},
                    expected_entity_id="ENT_A", expected_observation_id="OBS_A",
                )

    def test_g0_02_cross_entity_and_manifest_drift_are_rejected(self):
        entity = {
            "entity_id": "ENT_A", "canonical_name": "A", "incorporation_country": "CN",
            "company_wiki_ref": None, "formal_stockwiki_profile": None,
            "securities": [{
                "security_id": "SEC_A", "entity_id": "ENT_B", "market": "CN",
                "exchange": "SSE", "ticker": "600000", "currency": "CNY",
                "security_type": "ordinary", "adr_ratio": None,
                "ordinary_security_ref": None, "listing_status": "active",
            }], "segments": [],
        }
        with self.assertRaises(ValueError):
            cv.validate_legacy_entity_read(entity)

        work = {
            "work_item_id": "WORK_1", "entity_id": "ENT_A", "question_id": "IQS_01",
            "generation": 1, "scope": "entity", "scope_id": "ENT_B",
            "question_fingerprint": "a" * 64, "routing_fingerprint": "b" * 64,
            "request_cache_key": None, "status": "pending", "run_ids": ["RUN_1"],
            "scan_ids": ["SCAN_1"], "attempts": [],
            "created_at": "2026-09-22T00:00:00Z", "updated_at": "2026-09-22T00:00:00Z",
        }
        with self.assertRaises(ValueError):
            cv.validate_work_item(work)

        member = {"entity_id": "ENT_A", "membership_status": "active", "manual_pin": False,
                  "added_at": "2026-09-22T00:00:00Z", "version": 1}
        manifest = {"manifest_version": "1.0.0", "updated_at": "2026-09-22T00:00:00Z",
                    "total_entities": 3, "active_entities": 2,
                    "manual_pinned_count": 0, "members": [member, copy.deepcopy(member)]}
        with self.assertRaises(ValueError):
            cv.validate_universe_manifest(manifest)

    def test_g0_04_extensions_cannot_escape_lightweight_boundary(self):
        value = copy.deepcopy(PACKAGE)
        value["extensions"] = [{"capability_id": "escape", "required": False,
                                "payload": {"nested": {"raw_document": "company body"}}}]
        with self.assertRaises((ValidationError, ValueError)):
            cv.validate_exchange_package(value)

    def test_g0_05_release_and_readiness_cannot_self_attest(self):
        release = copy.deepcopy(DEPLOYMENT_EXAMPLES["release_set"])
        release["components"][0] = {"component_id": "iqs", "required": True}
        body = {key: value for key, value in release.items() if key != "manifest_sha256"}
        release["manifest_sha256"] = ec.canonical_sha256(body)
        self.assertEqual(dc.validate_release_set(release), (False, "invalid_manifest"))

        response = copy.deepcopy(DEPLOYMENT_EXAMPLES["responses"][0])
        result = response["result"]
        result["readiness"] = "full_release_verified"
        evidence = result["readiness_evidence"]
        evidence.update(level="full_release_verified", all_required_component_hashes_match=False,
                        setup_complete=False, doctor_passed=False,
                        live_search_receipt_id=None, paid_usage_receipt_id=None,
                        gate_evidence=[], loaded_consumers=[])
        with self.assertRaises(ValidationError):
            Draft202012Validator(DEPLOYMENT, format_checker=FormatChecker()).validate(response)

        release = copy.deepcopy(DEPLOYMENT_EXAMPLES["release_set"])
        response = copy.deepcopy(DEPLOYMENT_EXAMPLES["responses"][0])
        result, evidence = response["result"], response["result"]["readiness_evidence"]
        result["readiness"] = evidence["level"] = "full_release_verified"
        evidence.update(
            release_set_id=release["release_set_id"],
            manifest_sha256=release["manifest_sha256"],
            live_search_receipt_id="LIVE_OK", paid_usage_receipt_id="PAID_OK",
            gate_evidence=[{
                "gate_id": gate, "status": "passed",
                "receipt_sha256": format(index + 1, "064x"),
                "release_set_id": release["release_set_id"],
                "manifest_sha256": release["manifest_sha256"],
            } for index, gate in enumerate(dc.REQUIRED_GATES)],
            loaded_consumers=list(dc.REQUIRED_CONSUMERS),
        )
        dc.validate_readiness_response(response, release_set=release)
        attacks = []
        duplicate = copy.deepcopy(response)
        duplicate["result"]["readiness_evidence"]["gate_evidence"] = [
            copy.deepcopy(evidence["gate_evidence"][0]) for _ in dc.REQUIRED_GATES
        ]
        attacks.append(duplicate)
        wrong_release = copy.deepcopy(response)
        wrong_release["result"]["readiness_evidence"]["gate_evidence"][0]["release_set_id"] = "REL_WRONG"
        attacks.append(wrong_release)
        wrong_manifest = copy.deepcopy(response)
        wrong_manifest["result"]["readiness_evidence"]["gate_evidence"][0]["manifest_sha256"] = "f" * 64
        attacks.append(wrong_manifest)
        duplicate_consumer = copy.deepcopy(response)
        duplicate_consumer["result"]["readiness_evidence"]["loaded_consumers"] = ["theme", "theme"]
        attacks.append(duplicate_consumer)
        bad_component_hash = copy.deepcopy(response)
        bad_component_hash["result"]["components"][0]["actual_loaded_sha256"] = "a" * 64
        attacks.append(bad_component_hash)
        missing_component = copy.deepcopy(response)
        missing_component["result"]["components"].pop()
        attacks.append(missing_component)
        for attack in attacks:
            with self.assertRaises((ValidationError, ValueError)):
                dc.validate_readiness_response(attack, release_set=release)

    def test_g0_06_scored_query_requires_lineage_and_ok_requires_coverage(self):
        response = copy.deepcopy(QUERY_EXAMPLES["responses"][0])
        response["result"]["status"] = "ok"
        response["result"]["items"] = []
        response["result"]["coverage"]["status"] = "not_covered"
        with self.assertRaises((ValidationError, ValueError)):
            cv.validate_query_response(response)

        observation = copy.deepcopy(PACKAGE["items"][0]["observation"])
        profile_response = {
            "message_type": "response", "schema_version": "1.0.0",
            "request_id": "REQ_PROFILE", "operation": "get_profiles",
            "response_at": "2026-09-23T12:00:00Z",
            "result": {
                "status": "ok",
                "profiles": [{"entity_id": "ENT_WRONG", "canonical_name": "Wrong",
                              "security_ids": [], "observations": [observation]}],
                "missing_entity_ids": [],
                "coverage": copy.deepcopy(QUERY_EXAMPLES["responses"][0]["result"]["coverage"]),
                "watermark": copy.deepcopy(QUERY_EXAMPLES["responses"][0]["result"]["watermark"]),
            },
        }
        with self.assertRaises(ValueError):
            cv.validate_query_response(profile_response)

        response = copy.deepcopy(QUERY_EXAMPLES["responses"][0])
        response["result"]["status"] = "ok"
        response["result"]["coverage"]["status"] = "complete"
        response["result"]["coverage"]["missing_field_ids"] = []
        score = response["result"]["items"][0]["score_refs"][0]
        score.update(status="scored", score=8, information_as_of=None, observed_at=None,
                     observation_id=None, model_resolved=None, check_level=None)
        with self.assertRaises((ValidationError, ValueError)):
            cv.validate_query_response(response)

    def test_g0_07_diagnostics_and_empty_rules_are_rejected(self):
        mapping = {"question_id": "RECOVERY_01", "primary_metric_ref": None,
                   "dimension": "recovery_watch", "aggregation_role": "quality_core",
                   "critical_risk": False, "replacement_for": None}
        with self.assertRaises(ValidationError):
            cv.validate_question_mapping(mapping)
        with self.assertRaises(ValidationError):
            cv.validate_rule({})

        bare_leaf = {"all": [{"field": "score", "op": ">=", "value": 8}]}
        nested_policy = {"all": [{"policy_id": "P", "version": "1.0.0",
                                   "name": "nested", "root_rule": {"condition": {
                                       "field": "score", "op": ">=", "value": 8}}}]}
        for invalid in (bare_leaf, nested_policy):
            with self.assertRaises(ValidationError):
                cv.validate_rule(invalid)
        valid = {"all": [
            {"condition": {"field": "score", "op": ">=", "value": 8}},
            {"not": {"condition": {"field": "risk", "op": ">", "value": 3}}},
        ]}
        cv.validate_rule(valid)
        self.assertEqual(cv.evaluate_rule(valid, {"score": 9, "risk": 1}), "pass")

    def test_g0_08_lineage_must_be_closed_acyclic_and_transitively_independent(self):
        target, middle, candidate = "obs_target", "obs_middle", "obs_candidate"
        self.assertFalse(ec.independent_support(target, candidate, {
            candidate: [middle], middle: [target], target: []
        }))
        self.assertFalse(ec.independent_support(target, candidate, {candidate: [middle]}))
        self.assertFalse(ec.independent_support(target, candidate, {
            candidate: [middle], middle: [candidate], target: []
        }))
        self.assertTrue(ec.independent_support(target, candidate, {
            candidate: [middle], middle: [], target: []
        }))


if __name__ == "__main__":
    unittest.main()
