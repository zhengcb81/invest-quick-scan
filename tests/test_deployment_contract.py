"""C07 deployment/lifecycle contract tests; no runtime is launched."""
import copy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import deployment_contract as dc

SCHEMA = json.loads((ROOT / "schemas/quick_scan/deployment.schema.json").read_text(encoding="utf-8"))
EXAMPLES = json.loads((ROOT / "examples/quick_scan/deployment-contract.examples.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def validate(value):
    VALIDATOR.validate(value)


def component_statuses():
    return copy.deepcopy(EXAMPLES["responses"][0]["result"]["components"])


def complete_gates(release, *, omitted=()):
    return [{"gate_id": gate, "status": "passed",
             "receipt_sha256": format(index + 100, "064x"),
             "release_set_id": release["release_set_id"],
             "manifest_sha256": release["manifest_sha256"]}
            for index, gate in enumerate(dc.REQUIRED_GATES) if gate not in omitted]


class DeploymentContractTests(unittest.TestCase):
    def setUp(self):
        Draft202012Validator.check_schema(SCHEMA)

    def test_deploy_02_missing_or_incompatible_component_blocks_without_network(self):
        validate(EXAMPLES["release_set"])
        contract_versions = EXAMPLES["release_set"]["components"][0]["contract_versions"]
        self.assertEqual(contract_versions["model_policy_schema"], "2.0.0")
        self.assertIn("observation_schema", contract_versions)
        self.assertNotIn("model_policy", contract_versions)
        for request in EXAMPLES["requests"] + EXAMPLES["responses"]:
            validate(request)
        statuses = component_statuses()[1:]
        readiness = dc.assess_readiness(release_set=EXAMPLES["release_set"],
            component_statuses=statuses, install_record_present=True,
            setup_complete=True, doctor_passed=True)
        self.assertEqual((readiness["readiness"], readiness["status"]), ("not_ready", "setup_required"))
        doctor = copy.deepcopy(EXAMPLES["requests"][0])
        doctor["payload"]["paid_calls"] = True
        with self.assertRaises(ValidationError):
            validate(doctor)
        decision = dc.command_decision("doctor", {})
        self.assertFalse(decision["network_calls_started"])
        self.assertFalse(decision["paid_calls_started"])

    def test_deploy_04_same_version_different_loaded_hash_blocks(self):
        statuses = component_statuses()
        statuses[0]["actual_loaded_sha256"] = "f" * 64
        self.assertEqual(statuses[0]["actual_version"], statuses[0]["expected_version"])
        readiness = dc.assess_readiness(release_set=EXAMPLES["release_set"],
            component_statuses=statuses, install_record_present=True,
            setup_complete=True, doctor_passed=True)
        self.assertEqual(readiness["status"], "version_mismatch")
        release = copy.deepcopy(EXAMPLES["release_set"])
        release["components"][0]["version"] = "9.9.9"
        self.assertEqual(dc.validate_release_set(release), (False, "manifest_hash_mismatch"))
        missing_capability = component_statuses()
        missing_capability[0]["capabilities"] = []
        readiness = dc.assess_readiness(release_set=EXAMPLES["release_set"],
            component_statuses=missing_capability, install_record_present=True,
            setup_complete=True, doctor_passed=True)
        self.assertEqual(readiness["error_code"], "capability_missing")

    def test_release_set_and_process_identity_reject_duplicate_or_relative_paths(self):
        duplicate_components = copy.deepcopy(EXAMPLES["release_set"]["components"])
        duplicate_components[-1] = copy.deepcopy(duplicate_components[0])
        duplicate_release = dc.build_release_set(release_set_id="REL_DUPLICATE", created_at="2026-09-23T12:00:00Z",
                                                 components=duplicate_components)
        with self.assertRaises(ValidationError):
            validate(duplicate_release)
        response = copy.deepcopy(EXAMPLES["responses"][0])
        response["result"]["components"][0]["process_identity"] = {
            "workspace_id":"WS_FIXTURE", "profile_id":"PROFILE_FIXTURE", "component_id":"iqs",
            "process_instance_id":"INSTANCE_FIXTURE_0001", "pid":1234,
            "process_started_at":"2026-09-23T12:00:00Z", "executable_sha256":"a"*64,
            "working_directory":"C:\\Fixture Path\\invest-quick-scan"}
        validate(response)
        response["result"]["components"][0]["process_identity"]["working_directory"] = "relative\\path"
        with self.assertRaises(ValidationError):
            validate(response)

    def test_start_02_repeated_start_attaches_without_duplicate_run_or_budget(self):
        context = {"readiness":"offline_ready", "workspace_id":"WS_FIXTURE",
            "profile_id":"PROFILE_FIXTURE", "budget_status":"available", "plan_has_work":True,
            "active_run":{"run_id":"RUN_EXISTING","workspace_id":"WS_FIXTURE",
                          "profile_id":"PROFILE_FIXTURE"}}
        decision = dc.command_decision("start", context)
        self.assertEqual(decision["status"], "attached")
        self.assertEqual(decision["run_id"], "RUN_EXISTING")
        self.assertFalse(decision["create_run"])
        self.assertFalse(decision["reset_budget"])
        self.assertFalse(decision["paid_calls_started"])

    def test_start_03_budget_exhaustion_survives_restart_and_resume(self):
        resumable = {"run_id":"RUN_OLD","workspace_id":"WS_FIXTURE","profile_id":"PROFILE_FIXTURE"}
        base = {"readiness":"offline_ready", "workspace_id":"WS_FIXTURE",
            "profile_id":"PROFILE_FIXTURE", "budget_status":"exhausted", "plan_has_work":True,
            "resumable_run":resumable}
        decision = dc.command_decision("resume", base)
        self.assertEqual(decision["status"], "budget_exhausted")
        self.assertFalse(decision["reset_budget"])
        self.assertEqual(decision["run_id"], "RUN_OLD")
        fresh = dc.command_decision("start", {**base, "resumable_run":None})
        self.assertEqual(fresh["status"], "budget_exhausted")
        self.assertFalse(fresh["create_run"])

    def test_start_05_optional_company_wiki_never_enables_source_pipeline(self):
        components = [copy.deepcopy(c) for c in EXAMPLES["release_set"]["components"]
                      if c["component_id"] != "company_wiki"]
        release = dc.build_release_set(release_set_id="REL_WITHOUT_IDENTITY", created_at="2026-09-23T12:00:00Z",
                                       components=components)
        validate(release)
        decision = dc.command_decision("start", {"readiness":"offline_ready",
            "workspace_id":"WS_FIXTURE", "profile_id":"PROFILE_FIXTURE",
            "budget_status":"available", "plan_has_work":True})
        self.assertEqual(decision["status"], "accepted")
        self.assertFalse(decision["source_pipeline_started"])
        self.assertFalse(decision["generic_research_scheduler_started"])

    def test_start_09_doctor_is_zero_paid_and_live_probe_requires_named_action_and_hard_caps(self):
        doctor = dc.command_decision("doctor", {"budget_status":"available"})
        self.assertFalse(doctor["network_calls_started"])
        self.assertFalse(doctor["paid_calls_started"])
        caps = {"max_model_requests": 1, "max_search_requests": 1,
                "max_input_tokens": 4096, "max_output_tokens": 1024}
        base = {"external_action": "execute_one_live_search_probe", "budget_cap": caps,
                "policy_revision": "POLICY_FIXTURE_V2",
                "active_policy_revision": "POLICY_FIXTURE_V2",
                "expected_release_set_id": "REL_FIXTURE_1",
                "active_release_set_id": "REL_FIXTURE_1", "budget_status": "available"}
        for unsafe in (
            {**base, "external_action": None},
            {**base, "budget_cap": None},
            {**base, "budget_cap": {**caps, "max_model_requests": 2}},
            {**base, "budget_cap": {**caps, "max_search_requests": 2}},
            {**base, "budget_cap": {**caps, "max_output_tokens": 1025}},
            {**base, "active_release_set_id": "REL_STALE"},
            {**base, "active_policy_revision": "POLICY_STALE"},
            {"explicit_user_confirmation": True, "approval_ref": "APPROVAL_FIXTURE",
             "expected_release_set_id": "REL_FIXTURE_1", "active_release_set_id": "REL_FIXTURE_1",
             "policy_revision_current": True, "budget_status": "available"},
        ):
            denied = dc.command_decision("verify_live", unsafe)
            self.assertEqual(denied["status"], "blocked")
            self.assertFalse(denied["dispatch_authorized"])
            self.assertFalse(denied["network_calls_started"])
            self.assertFalse(denied["paid_calls_started"])
        approved = dc.command_decision("verify_live", base)
        self.assertTrue(approved["dispatch_authorized"])
        self.assertEqual(approved["authorized_external_action"], "execute_one_live_search_probe")
        self.assertEqual(approved["dispatch_budget_cap"], caps)
        self.assertFalse(approved["network_calls_started"])
        self.assertFalse(approved["paid_calls_started"])

    def test_verify_live_schema_requires_named_external_action_and_bounded_budget(self):
        request = copy.deepcopy(EXAMPLES["requests"][-1])
        request["payload"] = {
            "external_action": "execute_one_live_search_probe",
            "policy_revision": "POLICY_FIXTURE_V2",
            "budget_cap": {"max_model_requests": 1, "max_search_requests": 1,
                           "max_input_tokens": 4096, "max_output_tokens": 1024},
        }
        validate(request)
        for mutate in (
            lambda p: p.pop("external_action"),
            lambda p: p.pop("budget_cap"),
            lambda p: p.update(explicit_user_confirmation=True),
            lambda p: p.update(approval_ref="APPROVAL_FIXTURE"),
            lambda p: p["budget_cap"].update(max_model_requests=2),
            lambda p: p["budget_cap"].update(max_search_requests=0),
            lambda p: p["budget_cap"].update(max_output_tokens=1025),
            lambda p: p["budget_cap"].update(max_input_tokens=True),
            lambda p: p["budget_cap"].update(unbounded_cost=True),
        ):
            invalid = copy.deepcopy(request)
            mutate(invalid["payload"])
            with self.assertRaises(ValidationError):
                validate(invalid)

    def test_verify_live_public_request_flows_into_bounded_decision_without_dispatch(self):
        request = copy.deepcopy(EXAMPLES["requests"][-1])
        validate(request)
        active_release = EXAMPLES["release_set"]["release_set_id"]
        authoritative_policy = {"revision": "POLICY_FIXTURE_V2"}
        context = {
            **request["payload"],
            "expected_release_set_id": request["expected_release_set_id"],
            "active_release_set_id": active_release,
            "active_policy_revision": authoritative_policy["revision"],
            "budget_status": "available",
        }
        decision = dc.command_decision("verify_live", context)
        self.assertEqual(decision["status"], "accepted")
        self.assertTrue(decision["dispatch_authorized"])
        self.assertEqual(decision["authorized_external_action"], request["payload"]["external_action"])
        self.assertEqual(decision["dispatch_budget_cap"], request["payload"]["budget_cap"])
        self.assertFalse(decision["network_calls_started"])
        self.assertFalse(decision["paid_calls_started"])

        stale_context = {**context, "policy_revision": "POLICY_STALE"}
        stale_decision = dc.command_decision("verify_live", stale_context)
        self.assertEqual(stale_decision["status"], "blocked")
        self.assertFalse(stale_decision["dispatch_authorized"])

    def test_start_11_missing_setup_inputs_block_without_example_defaults(self):
        request = {"message_type":"request", "schema_version":"1.0.0",
            "request_id":"REQ_SETUP_FIXTURE", "workspace_id":"WS_FIXTURE",
            "profile_id":"PROFILE_FIXTURE", "operation":"setup",
            "expected_release_set_id":"REL_FIXTURE_1", "idempotency_key":"setup:fixture:1",
            "requested_at":"2026-09-23T12:00:00Z", "payload":{
                "stockwiki":{"universe_profile_ref":"POOL_FIXTURE","revision":"3","config_sha256":"1"*64},
                "stockqa":{"model_policy_profile_ref":"POLICY_FIXTURE","revision":"2","config_sha256":"2"*64},
                "company_identity_source":"user_supplied_snapshot"}}
        validate(request)
        poisoned = copy.deepcopy(request)
        poisoned["payload"]["api_key"] = "fixture-secret"
        with self.assertRaises(ValidationError):
            validate(poisoned)
        setup = dc.command_decision("setup", {})
        self.assertEqual(setup["configuration_owners"], ["stockwiki", "stockqa"])
        self.assertFalse(setup["secret_values_transmitted"])
        blocked = dc.command_decision("start", {"readiness":"installed", "preflight_status":"setup_required"})
        self.assertEqual(blocked["status"], "setup_required")
        setup_response = copy.deepcopy(EXAMPLES["responses"][0])
        setup_response["operation"] = "setup"
        validate(setup_response)
        setup_response["result"]["paid_calls_started"] = True
        with self.assertRaises(ValidationError):
            validate(setup_response)

    def test_e2e_04_full_release_requires_g4_g5_g6_and_matching_release_hashes(self):
        release = EXAMPLES["release_set"]
        statuses = component_statuses()
        probe = {"release_set_id":release["release_set_id"], "manifest_sha256":release["manifest_sha256"],
                 "actual_search_executed":True, "paid_usage_recorded":True, "receipt_id":"LIVE_FIXTURE"}
        base = {"release_set":release,"component_statuses":statuses,"install_record_present":True,
                "setup_complete":True,"doctor_passed":True,"live_probe":probe}
        self.assertEqual(dc.assess_readiness(**base, gate_evidence=complete_gates(release, omitted={"G4","G5"}))["readiness"], "live_verified")
        self.assertEqual(dc.assess_readiness(**base, gate_evidence=complete_gates(release))["readiness"], "full_release_verified")
        wrong_gate = complete_gates(release)
        wrong_gate[-1]["release_set_id"] = "REL_STALE"
        self.assertEqual(dc.assess_readiness(**base, gate_evidence=wrong_gate)["readiness"], "live_verified")

    def test_e2e_05_readiness_requires_evidence_from_same_release(self):
        release = EXAMPLES["release_set"]
        statuses = component_statuses()
        base = {"release_set":release,"component_statuses":statuses,"install_record_present":True,
                "setup_complete":True,"doctor_passed":True}
        offline = dc.assess_readiness(**base)
        self.assertEqual(offline["readiness"], "offline_ready")
        stale_probe = {"release_set_id":"REL_OLD","manifest_sha256":release["manifest_sha256"],
            "actual_search_executed":True,"paid_usage_recorded":True,"receipt_id":"OLD_LIVE"}
        remains_offline = dc.assess_readiness(**base, live_probe=stale_probe,
                                              gate_evidence=complete_gates(release))
        self.assertEqual(remains_offline["readiness"], "offline_ready")
        live = {"release_set_id":release["release_set_id"],"manifest_sha256":release["manifest_sha256"],
            "actual_search_executed":True,"paid_usage_recorded":True,"receipt_id":"LIVE_FIXTURE"}
        self.assertEqual(dc.assess_readiness(**base, live_probe=live)["readiness"], "live_verified")

    def test_stop_preserves_inflight_work_and_never_terminates_unowned_process(self):
        decision = dc.command_decision("stop", {"workspace_id":"WS_FIXTURE","profile_id":"PROFILE_FIXTURE",
            "run":{"run_id":"RUN_FIXTURE","workspace_id":"WS_FIXTURE","profile_id":"PROFILE_FIXTURE"}})
        self.assertEqual(decision["action"], "stop_new_dispatch_and_drain")
        self.assertEqual(decision["run_id"], "RUN_FIXTURE")
        self.assertTrue(decision["preserve_inflight_and_outbox"])
        self.assertFalse(decision["unowned_process_terminated"])
        denied = dc.command_decision("stop", {"workspace_id":"WS_FIXTURE","profile_id":"PROFILE_FIXTURE",
            "run":{"run_id":"RUN_OTHER","workspace_id":"WS_OTHER","profile_id":"PROFILE_FIXTURE"}})
        self.assertEqual(denied["error_code"], "unowned_process")
        recorded = EXAMPLES["responses"][0]["result"]["components"][0]["process_identity"]
        self.assertIsNone(recorded)

    def test_process_identity_uses_workspace_instance_pid_start_and_executable(self):
        identity = {"workspace_id":"WS_FIXTURE","profile_id":"PROFILE_FIXTURE","component_id":"stockqa",
            "process_instance_id":"INSTANCE_FIXTURE_0001","pid":1234,"process_started_at":"2026-09-23T12:00:00Z",
            "executable_sha256":"a"*64,"working_directory":"C:\\Fixture Path\\StockQA"}
        self.assertTrue(dc.process_identity_matches(identity, copy.deepcopy(identity)))
        stale_pid = copy.deepcopy(identity); stale_pid["pid"] = 4321
        self.assertFalse(dc.process_identity_matches(identity, stale_pid))
        wrong_workspace = copy.deepcopy(identity); wrong_workspace["workspace_id"] = "WS_OTHER"
        self.assertFalse(dc.process_identity_matches(identity, wrong_workspace))

    def test_plan_no_work_and_unknown_plan_do_not_create_or_dispatch(self):
        base = {"readiness":"offline_ready","workspace_id":"WS_FIXTURE","profile_id":"PROFILE_FIXTURE",
                "budget_status":"available"}
        empty = dc.command_decision("start", {**base,"plan_has_work":False})
        self.assertEqual(empty["status"], "no_work")
        self.assertFalse(empty["create_run"])
        unknown = dc.command_decision("start", {**base,"plan_has_work":None})
        self.assertEqual(unknown["action"], "require_current_plan_result")

        request = copy.deepcopy(EXAMPLES["requests"][0])
        request.update(request_id="REQ_PLAN_FIXTURE", operation="plan", idempotency_key="plan:fixture:1")
        request["payload"] = {"scope":"all_missing","entity_ids":[],"field_ids":[],
                               "snapshot_id":None,"preview_only":True}
        validate(request)
        request["payload"].update(scope="entities", entity_ids=[])
        with self.assertRaises(ValidationError):
            validate(request)


if __name__ == "__main__":
    unittest.main()
