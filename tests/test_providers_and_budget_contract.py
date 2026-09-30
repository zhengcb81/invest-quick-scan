"""Offline tests for the C05 model routing and budget configuration contract.

These tests validate the real policy validator and JSON Schema. They do not
claim provider execution, persistent budgeting, or multi-process behavior.
"""
import copy
import json
import importlib.util
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/model-policy.schema.json").read_text(encoding="utf-8"))
TEMPLATE = json.loads((ROOT / "examples/model-policy.template.json").read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("model_policy", ROOT / "scripts/model_policy.py")
model_policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model_policy)


class ProvidersAndBudgetContractTests(unittest.TestCase):
    def configured(self):
        policy = copy.deepcopy(TEMPLATE)
        policy["configured"] = True
        policy["budget"].update(max_cost=10, max_requests=20, max_cost_per_attempt=2)
        for i, route in enumerate(policy["models"]):
            route.update(enabled=True, provider_config_ref=f"config-{i}", model=f"model-{i}")
        return policy

    def test_schema_02_template_v2_is_valid_and_starts_unconfigured(self):
        Draft202012Validator.check_schema(SCHEMA)
        Draft202012Validator(SCHEMA).validate(TEMPLATE)
        self.assertEqual(TEMPLATE["schema_version"], "2.0.0")
        self.assertFalse(TEMPLATE["configured"])
        self.assertEqual(TEMPLATE["budget"]["max_cost"], 0)
        self.assertTrue(all(not route["enabled"] for route in TEMPLATE["models"]))
        self.assertFalse(model_policy.validate_policy(TEMPLATE)["runtime_verified"])

    def test_llm_03_order_and_one_retry_budget_are_preserved(self):
        policy = self.configured()
        policy["models"] = [policy["models"][2], policy["models"][0], policy["models"][1]]
        original = copy.deepcopy(policy)
        result = model_policy.validate_policy(policy)
        self.assertEqual(result["ordered_routes"], ["third_choice", "first_choice", "second_choice"])
        self.assertEqual(policy, original)
        self.assertEqual(policy["fallback"]["max_attempts_per_dispatch_round"], 3)

    def test_llm_04_valid_low_score_and_unknown_stop_primary_fallback(self):
        fallback = SCHEMA["properties"]["fallback"]["properties"]
        self.assertEqual(fallback["on_low_score"]["const"], "accept")
        self.assertEqual(fallback["on_unknown_answer"]["const"], "accept_with_gap")
        self.assertEqual(fallback["on_fallback_success"]["const"], "stop_dispatch_keep_primary_health")

    def test_llm_05_backup_success_cannot_mark_primary_healthy(self):
        self.assertEqual(
            SCHEMA["properties"]["fallback"]["properties"]["on_fallback_success"]["const"],
            "stop_dispatch_keep_primary_health",
        )
        self.assertTrue(TEMPLATE["resume"]["persist_cooldowns_and_budget"])

    def test_llm_06_failure_classes_distinguish_rate_limit_bad_request_and_capability(self):
        fallback = SCHEMA["properties"]["fallback"]["properties"]
        self.assertEqual(fallback["on_quota_exhausted"]["const"], "cooldown_group_then_next")
        self.assertEqual(fallback["on_rate_limit"]["const"], "respect_retry_after_then_next")
        self.assertEqual(fallback["on_server_error"]["const"], "bounded_retry_then_next")
        self.assertEqual(fallback["on_invalid_request"]["const"], "stop_without_fallback")
        self.assertEqual(fallback["on_auth_error"]["const"], "disable_route_then_next")
        self.assertEqual(fallback["on_missing_capability"]["const"], "skip_before_dispatch")
        self.assertIn("web_search", TEMPLATE["dispatch"]["required_capabilities"])

    def test_llm_10_schema_version_and_template_policy_label_are_new(self):
        old = copy.deepcopy(TEMPLATE)
        old["schema_version"] = "1.0.0"
        with self.assertRaises(ValidationError):
            Draft202012Validator(SCHEMA).validate(old)
        self.assertEqual(TEMPLATE["policy_id"], "user-model-order-template-v2")

    def test_bud_01_configured_policy_has_positive_total_and_atomic_reservation(self):
        policy = self.configured()
        Draft202012Validator(SCHEMA).validate(policy)
        self.assertTrue(policy["cost_policy"]["reserve_before_dispatch"])
        self.assertGreater(policy["budget"]["max_cost"], 0)
        self.assertGreater(policy["budget"]["max_cost_per_attempt"], 0)

    def test_bud_02_search_failed_attempts_and_fallback_share_one_cap(self):
        policy = self.configured()
        cost = policy["cost_policy"]
        self.assertTrue(cost["include_search_charges"])
        self.assertTrue(cost["include_failed_attempts"])
        self.assertFalse(policy["budget"]["reset_on_restart"])
        policy["budget"]["max_cost_per_attempt"] = 11
        with self.assertRaisesRegex(ValueError, "per-attempt cost cap"):
            model_policy.validate_policy(policy)

    def test_bud_03_uncertain_cost_is_held_and_timeout_requires_reconciliation(self):
        self.assertEqual(TEMPLATE["cost_policy"]["unknown_actual_cost_action"], "retain_reservation_and_pause")
        self.assertEqual(
            SCHEMA["properties"]["fallback"]["properties"]["on_timeout"]["const"],
            "reconcile_receipt_before_retry",
        )
        self.assertTrue(TEMPLATE["resume"]["preserve_uncertain_requests"])

    def test_bud_04_pricing_basis_needs_a_rate_card_or_explicit_per_attempt_cap(self):
        policy = self.configured()
        policy["cost_policy"].update(pricing_basis="verified_rate_card", pricing_ref=None)
        with self.assertRaises(ValidationError):
            Draft202012Validator(SCHEMA).validate(policy)
        policy["cost_policy"].update(pricing_basis="user_cap", pricing_ref=None)
        policy["budget"]["max_cost_per_attempt"] = 0
        with self.assertRaises(ValidationError):
            Draft202012Validator(SCHEMA).validate(policy)

    def test_par_01_global_group_and_route_limits_are_independent(self):
        policy = self.configured()
        self.assertEqual(policy["dispatch"]["max_in_flight_total"], 4)
        self.assertEqual(policy["quota_groups"][0]["max_in_flight"], 2)
        self.assertEqual(policy["models"][0]["max_in_flight"], 2)
        policy["models"][0]["max_in_flight"] = 3
        with self.assertRaisesRegex(ValueError, "shared quota group"):
            model_policy.validate_policy(policy)

    def test_par_02_shared_group_and_unknown_reset_are_explicit(self):
        routes = TEMPLATE["models"]
        self.assertEqual(routes[0]["quota_group"], routes[2]["quota_group"])
        self.assertEqual(TEMPLATE["quota_groups"][0]["window_seconds_hint"], 18000)
        self.assertIsNone(TEMPLATE["quota_groups"][1]["window_seconds_hint"])
        self.assertTrue(all(group["half_open_probe_limit"] == 1 for group in TEMPLATE["quota_groups"]))

    def test_par_03_capacity_waits_and_primary_does_not_race(self):
        dispatch = SCHEMA["properties"]["dispatch"]["properties"]
        self.assertEqual(dispatch["on_preferred_capacity_full"]["const"], "wait")
        self.assertFalse(dispatch["speculative_racing"]["const"])

    def test_par_06_outbox_replay_and_uncertain_request_are_separate(self):
        self.assertTrue(TEMPLATE["resume"]["replay_outbox_before_dispatch"])
        self.assertTrue(TEMPLATE["resume"]["preserve_uncertain_requests"])
        self.assertEqual(
            SCHEMA["properties"]["fallback"]["properties"]["on_timeout"]["const"],
            "reconcile_receipt_before_retry",
        )

    def test_par_07_cooldown_survives_restart_and_only_one_probe_can_open_group(self):
        self.assertTrue(TEMPLATE["resume"]["persist_cooldowns_and_budget"])
        self.assertFalse(TEMPLATE["budget"]["reset_on_restart"])
        for group in TEMPLATE["quota_groups"]:
            self.assertGreater(group["unknown_reset_cooldown_seconds"], 0)
            self.assertEqual(group["half_open_probe_limit"], 1)

    def test_par_08_comparison_has_separate_caps_and_respects_global_budget(self):
        policy = self.configured()
        comparison = policy["comparison"]
        self.assertFalse(comparison["enabled"])
        self.assertTrue(comparison["separate_from_primary_fallback"])
        comparison.update(enabled=True, max_cost=3, max_requests=5, max_models_per_question=2)
        self.assertTrue(model_policy.validate_policy(policy)["valid"])
        comparison["max_cost"] = 11
        with self.assertRaisesRegex(ValueError, "comparison cost cap"):
            model_policy.validate_policy(policy)


if __name__ == "__main__":
    unittest.main()
