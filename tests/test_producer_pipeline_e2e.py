"""Offline end-to-end checks for the local producer side of quick scan.

This exercises the published question composer and observation builder CLIs,
then validates the resulting StockQA-to-StockWiki exchange boundary. Provider
and StockWiki runtimes are deliberately not simulated as if they were live.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import contract_validation as cv
import exchange_contract as ec
import standard_answers as sa
from live_e2e_sandbox import LiveE2ESandbox


def _fixture_answer(question):
    """A short synthetic answer; example.invalid is not a research source."""
    return {
        "question_id": question["id"],
        "response_kind": "score",
        "status": "scored",
        "score": 8,
        "summary": "离线管线样例：答案只用于验证格式与跨模块传递。",
        "information_as_of": "2026-09-01",
        "period_start": "2026-01-01",
        "period_end": "2026-06-30",
        "basis": "current",
        "trend": "stable",
        "confidence": "medium",
        "metrics": [],
        "items": [],
        "evidence": [{
            "id": "fixture-evidence",
            "title": "虚构离线测试来源",
            "url": "https://example.invalid/quick-scan-fixture",
            "published_at": "2026-09-01",
            "claim": "该引用是测试数据，不是公司证据。",
        }],
        "counterevidence": "离线测试不验证真实公司事实。",
        "watch_triggers": ["仅为固定测试字段"],
        "missing_fields": [],
        "coverage": {"status": "complete_for_scope", "reason": "固定离线fixture"},
    }


class ProducerPipelineE2ETests(unittest.TestCase):
    def setUp(self):
        self.sandbox = LiveE2ESandbox()
        self.root = self.sandbox.root
        self.workspace = self.sandbox.path("workspace")
        self.temp_root = self.sandbox.path("logs")

    def tearDown(self):
        if self.root.exists():
            self.sandbox.register_existing_files(
                action="offline_pipeline_output", component_owner="invest-quick-scan"
            )
            self.sandbox.cleanup()
        self.assertFalse(self.root.exists(), "isolated E2E workspace must be removed")

    def _clean_child_environment(self):
        blocked_fragments = ("api_key", "api-key", "token", "secret", "password")
        environment = {
            key: value for key, value in os.environ.items()
            if not any(fragment in key.casefold() for fragment in blocked_fragments)
            and key.casefold() != "stockqa_run_live_e2e"
        }
        for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
            environment[name] = str(self.workspace)
        environment["TEMP"] = str(self.temp_root)
        environment["TMP"] = str(self.temp_root)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONUTF8"] = "1"
        return environment

    def _run(self, args):
        result = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", *map(str, args)],
            cwd=ROOT,
            env=self._clean_child_environment(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        return result

    @patch.dict(os.environ, {
        "MIMO_API_KEY": "UNIT_FIXTURE_SECRET",
        "MINIMAX_API_KEY": "UNIT_FIXTURE_SECRET",
        "DEEPSEEK_API_KEY": "UNIT_FIXTURE_SECRET",
        "BRAVE_API_KEY": "UNIT_FIXTURE_SECRET",
        "TAVILY_API_KEY": "UNIT_FIXTURE_SECRET",
        "STOCKQA_RUN_LIVE_E2E": "1",
        "PIPELINE_SAFE_FIXTURE": "preserved",
    }, clear=False)
    def test_offline_child_environment_strips_provider_secrets_and_live_opt_in(self):
        environment = self._clean_child_environment()
        for name in (
            "MIMO_API_KEY", "MINIMAX_API_KEY", "DEEPSEEK_API_KEY",
            "BRAVE_API_KEY", "TAVILY_API_KEY", "STOCKQA_RUN_LIVE_E2E",
        ):
            self.assertNotIn(name, environment)
        self.assertEqual(environment["PIPELINE_SAFE_FIXTURE"], "preserved")
        self.assertEqual(environment["PYTHONDONTWRITEBYTECODE"], "1")

    def _compose_one_question(self):
        profile = json.loads((ROOT / "examples/profile.json").read_text(encoding="utf-8"))
        profile.update({
            "company": "虚构管线测试公司",
            "ticker": "FIXTURE",
            "exchange": "FIXTURE_EXCHANGE",
            "entity_id": "ENT_PIPELINE_FIXTURE",
            "security_id": "SEC_PIPELINE_FIXTURE",
            "as_of": "2026-09-22",
            "example_only": True,
        })
        profile_path = self.workspace / "profile.json"
        profile_path.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
        output_dir = self.workspace / "question-run"
        self.sandbox.assert_run_path(profile_path)
        self.sandbox.assert_run_path(output_dir / "manifest.json")

        result = self._run([
            ROOT / "scripts/question_sets.py", "compose",
            "--profile", profile_path,
            "--mode", "quick",
            "--out-dir", output_dir,
            "--answer-format", "standard-1",
        ])
        self.assertEqual(
            result.returncode,
            0,
            f"compose CLI failed (stdout_chars={len(result.stdout)}, "
            f"stderr_chars={len(result.stderr)})",
        )
        manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["answer_format"], "standard-1")
        self.assertGreater(manifest["question_count"], 1)
        return output_dir, manifest

    def _build_inputs(self, output_dir, manifest, *, wrong_prompt_hash=False):
        answers_path = output_dir / "answers.json"
        receipts_path = output_dir / "execution-receipts.json"
        answers = {}
        requests = {}
        for index, question in enumerate(manifest["questions"]):
            answers[question["id"]] = _fixture_answer(question)
            prompt_hash = hashlib.sha256(question["prompt"].encode("utf-8")).hexdigest()
            if wrong_prompt_hash and index == 0:
                prompt_hash = "0" * 64
            requests[question["id"]] = {
                "provider": "offline-fixture",
                "model_requested": "offline-fixture-model",
                "model_resolved": "offline-fixture-model",
                "model_revision": "fixture-revision-1",
                "request_id": f"REQUEST_FIXTURE_{index}",
                "attempt_id": f"ATTEMPT_FIXTURE_{index}",
                "started_at": "2026-09-22T10:00:00Z",
                "answered_at": "2026-09-22T10:01:00Z",
                "search_status": "executed",
                "search_receipt_id": f"OFFLINE_FIXTURE_NOT_SEARCH_PROOF_{index}",
                "prompt_sha256": prompt_hash,
            }
        answers_path.write_text(
            json.dumps(answers, ensure_ascii=False), encoding="utf-8"
        )
        receipt = {
            "manifest_sha256": sa.digest(manifest),
            "run_id": "RUN_OFFLINE_FIXTURE",
            "scan_id": "SCAN_OFFLINE_FIXTURE",
            "inputset_id": "INPUTSET_FIXTURE_V1",
            "task_mode": "primary",
            "comparison_group_id": "GROUP_FIXTURE",
            "requests": requests,
        }
        receipts_path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
        return answers_path, receipts_path

    def test_public_clis_build_exchange_ready_observation_in_isolation(self):
        output_dir, manifest = self._compose_one_question()
        answers_path, receipts_path = self._build_inputs(output_dir, manifest)
        observations_path = self.workspace / "observations.json"
        self.sandbox.assert_run_path(observations_path)

        built = self._run([
            ROOT / "scripts/standard_answers.py", "build",
            "--manifest", output_dir / "manifest.json",
            "--answers", answers_path,
            "--receipts", receipts_path,
            "--output", observations_path,
        ])
        self.assertEqual(
            built.returncode,
            0,
            f"standard answer CLI failed (stdout_chars={len(built.stdout)}, "
            f"stderr={built.stderr[-1000:]!r})",
        )

        assembled = json.loads(observations_path.read_text(encoding="utf-8"))
        self.assertEqual(assembled["missing_question_ids"], [])
        observation = assembled["observations"][0]
        self.assertEqual(observation["entity_id"], "ENT_PIPELINE_FIXTURE")
        self.assertEqual(observation["answer"]["score"], 8)
        self.assertEqual(observation["execution"]["model_resolved"], "offline-fixture-model")
        self.assertEqual(observation["observed_at"], "2026-09-22T10:01:00Z")
        self.assertIn("example.invalid", observation["answer"]["evidence"][0]["url"])

        package = ec.build_package(
            assembled["observations"],
            created_at="2026-09-22T10:02:00Z",
            producer_version="offline-fixture-1",
            build_id="producer-pipeline-test",
            contract_versions={
                "identity_schema": "1.0.0",
                "answer_schema": "1.0.0",
                "observation_schema": "1.0.0",
                "question_catalog": manifest["template_version"],
                "model_policy_schema": "1.0.0",
            },
        )
        package_path = self.sandbox.path("exchange") / "package.json"
        self.sandbox.assert_run_path(package_path)
        package_path.write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")
        serialized_package = json.loads(package_path.read_text(encoding="utf-8"))
        cv.validate_exchange_package(serialized_package)
        ec.validate_package_integrity(serialized_package)
        self.assertFalse(serialized_package["document_payloads_included"])
        self.assertEqual(len(serialized_package["items"]), manifest["question_count"])
        self.assertEqual(serialized_package["items"][0]["observation"]["observation_id"],
                         observation["observation_id"])
        self.assertNotIn("raw_document", json.dumps(serialized_package, ensure_ascii=False))
        self.assertEqual(len(list((self.sandbox.path("downloads")).iterdir())), 0)

    def test_public_builder_rejects_execution_receipt_for_another_prompt(self):
        output_dir, manifest = self._compose_one_question()
        answers_path, receipts_path = self._build_inputs(
            output_dir, manifest, wrong_prompt_hash=True
        )
        observations_path = self.workspace / "must-not-be-created.json"

        result = self._run([
            ROOT / "scripts/standard_answers.py", "build",
            "--manifest", output_dir / "manifest.json",
            "--answers", answers_path,
            "--receipts", receipts_path,
            "--output", observations_path,
        ])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(observations_path.exists())


if __name__ == "__main__":
    unittest.main()
