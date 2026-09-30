"""Keep provider facts structured and ensure credentials never enter the inventory."""
import copy
import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "examples/provider-connectivity-profiles.json"
SCHEMA_PATH = ROOT / "schemas/provider-connectivity-profiles.schema.json"


class ProviderConnectivityProfileTests(unittest.TestCase):
    def setUp(self):
        self.profiles = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.validator = Draft202012Validator(self.schema)

    def test_inventory_and_schema_are_valid_and_have_unique_profiles(self):
        Draft202012Validator.check_schema(self.schema)
        self.validator.validate(self.profiles)
        ids = [profile["profile_id"] for profile in self.profiles["profiles"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({profile["provider"] for profile in self.profiles["profiles"]}, {"mimo", "minimax", "deepseek"})
        self.assertEqual(self.profiles["credential_policy"]["secret_values_included"], False)

    def test_profiles_record_environment_variable_names_without_key_values(self):
        expected_envs = {
            "mimo-token-plan-cn": "MIMO_PLAN_API_KEY",
            "mimo-pay-as-you-go-cn": "MIMO_API_KEY",
            "minimax-cn-responses": "MINIMAX_API_KEY",
            "minimax-global-server-tools": "MINIMAX_API_KEY",
            "minimax-mainland-responses-search": "MINIMAX_API_KEY",
            "deepseek-flash-official-api": "DEEPSEEK_API_KEY",
            "deepseek-flash-openai-responses": "DEEPSEEK_API_KEY",
            "deepseek-flash-anthropic-web-search": "DEEPSEEK_API_KEY",
        }
        profiles = {item["profile_id"]: item for item in self.profiles["profiles"]}
        self.assertEqual(set(profiles), set(expected_envs))
        for profile_id, env_name in expected_envs.items():
            self.assertEqual(profiles[profile_id]["credential_env"], env_name)

        forbidden_keys = {"api_key", "api_key_value", "secret", "secret_value", "authorization"}

        def inspect(node):
            if isinstance(node, dict):
                self.assertTrue(forbidden_keys.isdisjoint(key.lower() for key in node))
                for value in node.values():
                    inspect(value)
            elif isinstance(node, list):
                for value in node:
                    inspect(value)
            elif isinstance(node, str):
                self.assertIsNone(re.search(r"(?i)\bBearer\s+|\bsk-[A-Za-z0-9_-]{8,}", node))

        inspect(self.profiles)
        raw = PROFILE_PATH.read_text(encoding="utf-8")
        self.assertNotRegex(raw, r"(?i)\bBearer\s+|\bsk-[A-Za-z0-9_-]{8,}")

    def test_deepseek_is_text_callable_but_native_search_is_not_claimed(self):
        profile = next(item for item in self.profiles["profiles"] if item["profile_id"] == "deepseek-flash-official-api")
        self.assertEqual(profile["endpoint"]["url"], "https://api.deepseek.com/chat/completions")
        self.assertEqual(profile["model"], "deepseek-flash")
        self.assertEqual(profile["capabilities"]["text_generation"], "passed")
        self.assertEqual(profile["capabilities"]["provider_web_search_documentation"], "unsupported")
        self.assertEqual(profile["capabilities"]["provider_web_search_probe"], "not_attempted")
        self.assertTrue(profile["capabilities"]["requires_external_search_runner"])
        self.assertEqual(profile["capabilities"]["stockqa_cli_e2e"], "not_run")

    def test_deepseek_openai_responses_builtin_search_is_ignored(self):
        profile = next(item for item in self.profiles["profiles"] if item["profile_id"] == "deepseek-flash-openai-responses")
        probe = profile["probes"][0]
        self.assertEqual(profile["endpoint"]["protocol"], "openai_responses")
        self.assertEqual(profile["capabilities"]["provider_web_search_documentation"], "unsupported")
        self.assertEqual(probe["status"], "unsupported")
        self.assertEqual(probe["search_calls"], 0)
        self.assertEqual(probe["citation_annotations"], 0)

    def test_deepseek_anthropic_server_search_is_verified_and_limit_overran(self):
        profile = next(item for item in self.profiles["profiles"] if item["profile_id"] == "deepseek-flash-anthropic-web-search")
        probe = profile["probes"][0]
        self.assertEqual(profile["endpoint"]["protocol"], "anthropic_messages")
        self.assertEqual(profile["endpoint"]["url"], "https://api.deepseek.com/anthropic/v1/messages")
        self.assertEqual(profile["capabilities"]["provider_web_search_probe"], "passed")
        self.assertEqual(probe["status"], "passed")
        self.assertEqual(probe["server_tool_use_count"], 2)
        self.assertEqual(probe["web_search_result_blocks"], 2)
        self.assertEqual(probe["requested_max_uses"], 1)
        self.assertFalse(probe["max_uses_respected"])
        self.assertTrue(any(url.startswith("https://api-docs.deepseek.com/") for url in probe["source_urls"]))

    def test_minimax_historical_live_pass_is_separate_from_latest_unverified_revision(self):
        for profile in self.profiles["profiles"]:
            capability = profile["capabilities"]["stockqa_cli_e2e"]
            if profile["profile_id"] == "minimax-mainland-responses-search":
                self.assertEqual(capability, "passed_prior_revision_latest_unverified")
                evidence_path = profile["capabilities"]["stockqa_cli_e2e_evidence_path"]
                evidence = json.loads((ROOT / evidence_path).read_text(encoding="utf-8"))
                self.assertEqual(evidence["runs"][-1]["result"], "passed")
                self.assertFalse(evidence["limits"]["durable_retry_verified"])
                self.assertFalse(evidence["limits"]["independent_live_rerun"])
                latest_path = profile["capabilities"]["stockqa_cli_e2e_latest_evidence_path"]
                latest = json.loads((ROOT / latest_path).read_text(encoding="utf-8"))
                self.assertEqual(latest["status"], "latest_code_live_not_verified")
                self.assertEqual(latest["attempts"][-1]["http_status_code"], 200)
                self.assertEqual(latest["attempts"][-1]["search_status"], "unverified")
            else:
                self.assertEqual(capability, "not_run")
                self.assertNotIn("stockqa_cli_e2e_evidence_path", profile["capabilities"])
                self.assertNotIn("stockqa_cli_e2e_latest_evidence_path", profile["capabilities"])
            self.assertNotIn("stockqa_ready", profile["capabilities"])

        invalid = copy.deepcopy(self.profiles)
        invalid["profiles"][0]["capabilities"]["stockqa_cli_e2e"] = "passed"
        self.assertGreaterEqual(len(list(self.validator.iter_errors(invalid))), 1)

    def test_every_provider_probe_points_to_a_local_sanitized_evidence_file(self):
        for profile in self.profiles["profiles"]:
            for probe in profile["probes"]:
                evidence = ROOT / probe["evidence_path"]
                self.assertTrue(evidence.is_file(), str(evidence))
                raw = evidence.read_text(encoding="utf-8")
                self.assertNotRegex(raw, r"(?i)\bBearer\s+|\bsk-[A-Za-z0-9_-]{8,}")

    def test_schema_rejects_inline_credentials_and_invalid_environment_references(self):
        with_key = copy.deepcopy(self.profiles)
        with_key["profiles"][0]["api_key"] = "sk-test-do-not-store"
        self.assertGreaterEqual(len(list(self.validator.iter_errors(with_key))), 1)

        with_literal = copy.deepcopy(self.profiles)
        with_literal["profiles"][0]["credential_env"] = "sk-test-do-not-store"
        self.assertGreaterEqual(len(list(self.validator.iter_errors(with_literal))), 1)


if __name__ == "__main__":
    unittest.main()
