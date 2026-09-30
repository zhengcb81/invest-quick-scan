"""C06 offline contract tests; StockWiki/StockQA runtime remains out of scope."""
import copy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import exchange_contract as ec
import standard_answers as sa
import contract_validation as cv

EXCHANGE = json.loads((ROOT / "schemas/quick_scan/exchange.schema.json").read_text(encoding="utf-8"))
QUERY = json.loads((ROOT / "schemas/quick_scan/query.schema.json").read_text(encoding="utf-8"))
OBSERVATION = json.loads((ROOT / "schemas/observation.schema.json").read_text(encoding="utf-8"))
ANSWER = json.loads((ROOT / "schemas/answer-content.schema.json").read_text(encoding="utf-8"))
PACKAGE = json.loads((ROOT / "examples/quick_scan/exchange-package.example.json").read_text(encoding="utf-8"))
ACK = json.loads((ROOT / "examples/quick_scan/import-ack.example.json").read_text(encoding="utf-8"))
QUERY_EXAMPLES = json.loads((ROOT / "examples/quick_scan/query-contract.examples.json").read_text(encoding="utf-8"))

REGISTRY = Registry().with_resources([
    ("urn:iqs:observation:1", Resource.from_contents(OBSERVATION)),
    ("urn:iqs:answer-content:1", Resource.from_contents(ANSWER)),
    ("urn:iqs:quick-scan:exchange:1", Resource.from_contents(EXCHANGE)),
])


def validate(schema, value):
    Draft202012Validator(schema, registry=REGISTRY, format_checker=FormatChecker()).validate(value)


def request(operation, payload, request_id="REQ_FIXTURE"):
    return {"message_type":"request", "schema_version":"1.0.0", "request_id":request_id,
            "consumer_id":"industry-research", "operation":operation,
            "requested_at":"2026-09-23T12:00:00Z", "payload":payload}


def response(operation, result, request_id="REQ_FIXTURE"):
    return {"message_type":"response", "schema_version":"1.0.0", "request_id":request_id,
            "operation":operation, "response_at":"2026-09-23T12:01:00Z", "result":result}


class ExchangeAndQueryContractTests(unittest.TestCase):
    def setUp(self):
        Draft202012Validator.check_schema(EXCHANGE)
        Draft202012Validator.check_schema(QUERY)

    def test_db_02_same_immutable_payload_reimport_is_idempotent(self):
        validate(EXCHANGE, PACKAGE)
        validate(EXCHANGE, ACK)
        item = PACKAGE["items"][0]
        status, error = ec.import_decision(
            observation_id=item["observation_id"], incoming_payload_hash=item["payload_sha256"],
            existing_payload_hash=item["payload_sha256"], entity_exists=True, question_known=True,
            schema_supported=True, payload=item["observation"])
        self.assertEqual((status, error), ("already_present", None))

    def test_db_03_same_key_different_hash_conflicts_and_missing_refs_reject(self):
        item = PACKAGE["items"][0]
        changed_payload = copy.deepcopy(item["observation"])
        changed_payload["answer"]["summary"] = changed_payload["answer"]["summary"] + "；修订样本"
        changed_hash = ec.canonical_sha256(changed_payload)
        status, error = ec.import_decision(
            observation_id=item["observation_id"], incoming_payload_hash=changed_hash,
            existing_payload_hash=item["payload_sha256"], entity_exists=True, question_known=True,
            schema_supported=True, payload=changed_payload)
        self.assertEqual((status, error), ("conflict", "immutable_key_hash_conflict"))
        status, error = ec.import_decision(
            observation_id=item["observation_id"], incoming_payload_hash=item["payload_sha256"],
            existing_payload_hash=None, entity_exists=False, question_known=True,
            schema_supported=True, payload=item["observation"])
        self.assertEqual((status, error), ("rejected", "missing_entity"))
        bad_ack = {**ACK, "status":"conflict", "error_code":"immutable_key_hash_conflict"}
        validate(EXCHANGE, bad_ack)

    def test_db_06_model_cannot_inject_formal_source_artifacts_or_acceptance(self):
        item = PACKAGE["items"][0]
        poisoned = {**item["observation"], "source_manifest_ids":["FAKE_MANIFEST"]}
        status, error = ec.import_decision(
            observation_id=item["observation_id"], incoming_payload_hash=ec.canonical_sha256(poisoned),
            existing_payload_hash=None, entity_exists=True, question_known=True,
            schema_supported=True, payload=poisoned)
        self.assertEqual((status, error), ("rejected", "invalid_payload"))
        with self.assertRaises(ValidationError):
            validate(OBSERVATION, poisoned)
        self.assertFalse(any("source_manifest" in key or "evidence_span" in key for key in item["observation"]))

    def test_db_07_package_is_standalone_lightweight_exchange_not_a_second_store(self):
        validate(EXCHANGE, PACKAGE)
        contract = (ROOT / "docs/implementation/contracts/exchange-and-query.md").read_text(encoding="utf-8")
        self.assertIn("v1.0.0的`extensions`固定为空数组（`[]`）", contract)
        self.assertEqual(PACKAGE["extensions"], [])
        self.assertFalse(PACKAGE["document_payloads_included"])
        self.assertEqual(PACKAGE["data_class"], "lightweight_screening")
        self.assertEqual(PACKAGE["producer"]["component"], "StockQAbyLLM")
        self.assertEqual(PACKAGE["consumer"]["component"], "StockWiki")
        self.assertTrue(all(item["observation"]["entity_id"] == "ENT_EXAMPLE_A" for item in PACKAGE["items"]))

    def test_query_01_bounded_snapshot_pagination_and_three_axis_metadata(self):
        for example in QUERY_EXAMPLES["requests"] + QUERY_EXAMPLES["responses"]:
            validate(QUERY, example)
        search = QUERY_EXAMPLES["requests"][0]
        result = QUERY_EXAMPLES["responses"][0]["result"]
        self.assertEqual(search["payload"]["page_size"], result["page_size"])
        self.assertEqual(search["payload"]["filters"]["markets"], ["CN"])
        self.assertEqual(result["snapshot_id"], result["watermark"]["snapshot_id"])
        self.assertEqual(result["items"][0]["score_refs"][0]["model_resolved"], "fixture-model")
        self.assertEqual(result["items"][0]["score_refs"][0]["information_as_of"], "2026-09-22")
        too_large = copy.deepcopy(search)
        too_large["payload"]["page_size"] = 101
        with self.assertRaises(ValidationError):
            validate(QUERY, too_large)

    def test_query_02_empty_requires_covered_scope_and_unknown_is_coverage_gap(self):
        self.assertEqual(ec.search_status(0, "complete"), "empty")
        self.assertEqual(ec.search_status(0, "not_covered"), "coverage_gap")
        self.assertEqual(ec.search_status(0, "unknown"), "coverage_gap")
        self.assertEqual(ec.search_status(1, "partial"), "partial")
        gap = copy.deepcopy(QUERY_EXAMPLES["responses"][0])
        gap["result"].update(status="coverage_gap", items=[])
        gap["result"]["coverage"].update(status="not_covered", covered_markets=[],
                                           covered_field_ids=[], missing_field_ids=["score.iqs_01"])
        validate(QUERY, gap)
        invalid_empty = copy.deepcopy(gap)
        invalid_empty["result"].update(status="empty")
        with self.assertRaises(ValidationError):
            validate(QUERY, invalid_empty)

    def test_query_capabilities_profiles_and_approved_refresh_are_typed(self):
        coverage = copy.deepcopy(QUERY_EXAMPLES["responses"][0]["result"]["coverage"])
        watermark = copy.deepcopy(QUERY_EXAMPLES["responses"][0]["result"]["watermark"])
        validate(QUERY, request("capabilities", {
            "required_capabilities": ["scores", "facts", "history", "refresh_preview"],
            "markets": ["CN", "HK", "US"]}))
        capability_result = response("capabilities", {
            "supported_operations": ["capabilities", "search", "get_profiles", "request_refresh", "approve_refresh"],
            "supported_capabilities": ["scores", "facts", "history", "refresh_preview"],
            "contract_versions": {"query": "1.0.0", "observation": "1.0.0"},
            "coverage": coverage, "watermark": watermark})
        validate(QUERY, capability_result)

        validate(QUERY, request("get_profiles", {
            "entity_ids": ["ENT_EXAMPLE_A"], "field_ids": ["score.iqs_01", "FACT_10"],
            "snapshot_id": "SNAP_FIXTURE_1", "include_history": True}))
        profile = response("get_profiles", {
            "status": "partial",
            "profiles": [{"entity_id": "ENT_EXAMPLE_A", "canonical_name": "虚构工业示例公司",
                          "security_ids": ["SEC_EXAMPLE_CN"],
                          "observations": [PACKAGE["items"][0]["observation"]]}],
            "missing_entity_ids": [], "coverage": coverage, "watermark": watermark})
        validate(QUERY, profile)

        approval = request("approve_refresh", {"preview_id": "PREVIEW_FIXTURE_1",
            "confirmation_id": "CONFIRM_FIXTURE_1", "idempotency_key": "approve:PREVIEW_FIXTURE_1"})
        validate(QUERY, approval)
        accepted = response("approve_refresh", {"refresh_request_id": "REFRESH_FIXTURE_1",
            "status": "accepted", "scope_sha256": "2" * 64, "policy_version": "POLICY_FIXTURE_V2",
            "dispatch_started": False, "idempotency_key": "approve:PREVIEW_FIXTURE_1", "error_code": None})
        validate(QUERY, accepted)
        replay = copy.deepcopy(accepted)
        replay["result"].update(status="already_submitted", refresh_request_id="REFRESH_FIXTURE_1")
        validate(QUERY, replay)
        replay["result"]["dispatch_started"] = True
        with self.assertRaises(ValidationError):
            validate(QUERY, replay)

    def test_query_04_refresh_is_exact_scope_preview_reuses_valid_fields_and_never_dispatches(self):
        states={"ENT_EXAMPLE_A":{"score.iqs_01":"fresh", "FACT_10":"missing"}}
        preview=ec.refresh_preview(requested_entities=["ENT_EXAMPLE_A"], requested_fields=["score.iqs_01","FACT_10"],
                                   allowed_entities={"ENT_EXAMPLE_A"}, field_states=states, budget_available=True)
        self.assertEqual(preview["status"], "preview_ready")
        self.assertEqual(preview["eligible"], [("ENT_EXAMPLE_A","FACT_10")])
        self.assertEqual(preview["reused"], [("ENT_EXAMPLE_A","score.iqs_01")])
        self.assertFalse(preview["dispatch_started"])
        out_scope=ec.refresh_preview(requested_entities=["ENT_OUTSIDE"], requested_fields=["FACT_10"],
                                     allowed_entities={"ENT_EXAMPLE_A"}, field_states=states, budget_available=True)
        self.assertEqual(out_scope["status"], "out_of_scope")
        self.assertEqual(out_scope["eligible"], [])
        request_value=QUERY_EXAMPLES["requests"][1]
        validate(QUERY, request_value)
        illicit=copy.deepcopy(request_value)
        illicit["payload"]["max_cost"]=1000000
        with self.assertRaises(ValidationError):
            validate(QUERY, illicit)
        no_budget=ec.refresh_preview(requested_entities=["ENT_EXAMPLE_A"], requested_fields=["FACT_10"],
                                     allowed_entities={"ENT_EXAMPLE_A"}, field_states=states, budget_available=False)
        self.assertEqual(no_budget["status"], "budget_unavailable")
        self.assertFalse(no_budget["dispatch_started"])

    def test_fact_01_existing_fact_observation_keeps_null_score_and_relation_evidence(self):
        fact=next(item["observation"] for item in PACKAGE["items"] if item["observation"]["answer"]["response_kind"]=="fact")
        validate(OBSERVATION, fact)
        self.assertIsNone(fact["answer"]["score"])
        self.assertTrue(fact["answer"]["items"])
        relation=fact["answer"]["items"][0]
        self.assertIn(relation["role"], {"producer","user","supplier","customer","channel","manager","owner","peer","industry","other"})
        self.assertTrue(relation["evidence_ids"])

    def test_candidate_set_pins_snapshot_members_and_rule_version(self):
        request_value=request("candidate_set",{"snapshot_id":"SNAP_FIXTURE_1","query_hash":"3"*64,
            "entity_ids":["ENT_EXAMPLE_A"],"observation_ids":[PACKAGE["items"][0]["observation_id"]],
            "rule_id":"RULE_FIXTURE","rule_version":"1.0.0","label":"虚构候选集"})
        validate(QUERY,request_value)
        result=response("candidate_set",{"candidate_set_id":"CSET_FIXTURE_1","candidate_set_sha256":"4"*64,
            "snapshot_id":"SNAP_FIXTURE_1","rule_id":"RULE_FIXTURE","rule_version":"1.0.0",
            "created_at":"2026-09-23T12:00:00Z","immutable":True,
            "members":[{"entity_id":"ENT_EXAMPLE_A","observation_ids":[PACKAGE["items"][0]["observation_id"]]}]})
        validate(QUERY,result)

    def test_nomination_and_conflict_feedback_do_not_auto_merge_or_admit(self):
        nomination=request("nominate",{"nomination_id":"NOM_FIXTURE","origin_task_id":"TASK_FIXTURE",
            "candidate":{"canonical_name":"虚构候选","market":"HK","exchange":"HKEX","ticker":"00001","security_type":"ordinary"},
            "observation_ids":[],"reason":"示例：由产业链主题提名，待身份核验。"})
        validate(QUERY,nomination)
        nom_result=response("nominate",{"nomination_id":"NOM_FIXTURE","status":"pending_identity_review","candidate_id":"CAND_FIXTURE","auto_admitted":False})
        validate(QUERY,nom_result)
        conflict=request("report_conflict",{"conflict_id":"CONFLICT_FIXTURE","entity_ids":["ENT_EXAMPLE_A","ENT_EXAMPLE_B"],
            "conflict_type":"possible_duplicate","reason":"虚构冲突反馈，不可自动合并。","observation_ids":[]})
        validate(QUERY,conflict)
        conflict_result=response("report_conflict",{"conflict_id":"CONFLICT_FIXTURE","status":"recorded_for_review",
            "entity_ids":["ENT_EXAMPLE_A","ENT_EXAMPLE_B"],"identity_changed":False})
        validate(QUERY,conflict_result)

    def test_cons_05_handoff_retains_origin_and_upstream_lineage_without_formal_acceptance(self):
        target=PACKAGE["items"][0]["observation_id"]
        lead={"schema_version":"1.0.0","origin_task_id":"THEME_TASK_FIXTURE","entity_id":"ENT_EXAMPLE_A",
              "observation_ids":[PACKAGE["items"][1]["observation_id"]],"upstream_observation_ids":[target],
              "evidence_urls":["https://example.invalid/fixture"],"formal_evidence_accepted":False,
              "handoff_reason":"虚构研究线索；上游观察仍作为同一来源链。"}
        validate(EXCHANGE,lead)
        candidate = lead["observation_ids"][0]
        unrelated = "obs_"+"a"*64
        lineage = {candidate: [target], target: [], unrelated: []}
        self.assertFalse(ec.independent_support(target, candidate, lineage))
        self.assertTrue(ec.independent_support(unrelated, candidate, lineage))

    def test_hashes_bind_package_item_and_observation_payload(self):
        package_body={k:v for k,v in PACKAGE.items() if k not in {"package_id","package_sha256"}}
        digest=ec.canonical_sha256(package_body)
        self.assertEqual(PACKAGE["package_sha256"],digest)
        self.assertEqual(PACKAGE["package_id"],"pkg_"+digest)
        for item in PACKAGE["items"]:
            self.assertEqual(item["payload_sha256"],ec.canonical_sha256(item["observation"]))
            self.assertEqual(item["observation_id"],item["observation"]["observation_id"])
            sa.validate_observation(item["observation"])

    def test_exchange_public_validator_rejects_any_stale_content_address(self):
        tampered = []

        observation_changed = copy.deepcopy(PACKAGE)
        observation_changed["items"][0]["observation"]["answer"]["summary"] += " altered"
        tampered.append(observation_changed)

        payload_hash_changed = copy.deepcopy(PACKAGE)
        payload_hash_changed["items"][0]["payload_sha256"] = "f" * 64
        tampered.append(payload_hash_changed)

        observation_id_changed = copy.deepcopy(PACKAGE)
        observation_id_changed["items"][0]["observation_id"] = "obs_" + "a" * 64
        tampered.append(observation_id_changed)

        item_id_changed = copy.deepcopy(PACKAGE)
        item_id_changed["items"][0]["item_id"] = "itm_" + "a" * 64
        tampered.append(item_id_changed)

        metadata_changed = copy.deepcopy(PACKAGE)
        metadata_changed["producer"]["component_version"] = "9.9.9"
        tampered.append(metadata_changed)

        package_hash_changed = copy.deepcopy(PACKAGE)
        package_hash_changed["package_sha256"] = "f" * 64
        tampered.append(package_hash_changed)

        package_id_changed = copy.deepcopy(PACKAGE)
        package_id_changed["package_id"] = "pkg_" + "a" * 64
        tampered.append(package_id_changed)

        for invalid in tampered:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                cv.validate_exchange_package(invalid)

        cv.validate_exchange_package(PACKAGE)

    def test_build_package_detaches_mutable_inputs_before_hashing(self):
        observation = copy.deepcopy(PACKAGE["items"][0]["observation"])
        versions = copy.deepcopy(PACKAGE["contract_versions"])
        package = ec.build_package([observation], created_at="2026-09-23T12:00:00Z",
            producer_version="0.1.0", build_id="BUILD_FIXTURE", contract_versions=versions)
        bound_observation = copy.deepcopy(package["items"][0]["observation"])
        bound_versions = copy.deepcopy(package["contract_versions"])
        observation["answer"]["summary"] = "caller mutation after build"
        versions["observation_schema"] = "99.0.0"
        self.assertEqual(package["items"][0]["observation"], bound_observation)
        self.assertEqual(package["contract_versions"], bound_versions)
        self.assertEqual(package["items"][0]["payload_sha256"], ec.canonical_sha256(bound_observation))
        body = {k:v for k,v in package.items() if k not in {"package_id", "package_sha256"}}
        self.assertEqual(package["package_sha256"], ec.canonical_sha256(body))


if __name__ == "__main__":
    unittest.main()
