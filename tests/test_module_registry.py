"""S05 publication, historical resolution, and deterministic composition cases."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import module_contract as mc  # noqa: E402
import module_registry as registry  # noqa: E402
import question_manifest as manifest_contract  # noqa: E402
import question_sets as qs  # noqa: E402
import standard_answers as sa  # noqa: E402


class ModuleRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iqs-s05-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "questions", self.root / "questions",
                        ignore=shutil.ignore_patterns("releases"))
        for reference in ("schemas/answer-content.schema.json", "schemas/quick_scan/metric.schema.json",
                          "schemas/quick_scan/score.schema.json", "schemas/observation.schema.json",
                          "schemas/quick_scan/module-legacy-baseline.json"):
            target = self.root / reference
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / reference, target)
        self.profile = qs.read_json(ROOT / "examples/profile.json")
        self.patch_root = mock.patch.object(qs, "ROOT", self.root)
        self.patch_root.start()
        self.addCleanup(self.patch_root.stop)
        self.patch_standard_root = mock.patch.object(sa, "ROOT", self.root)
        self.patch_standard_root.start()
        self.addCleanup(self.patch_standard_root.stop)
        self.addCleanup(sa.validator.cache_clear)

    def publish(self):
        return registry.publish(root=self.root, renderer_version=qs.RENDERER_VERSION,
                                router_version="1.0.0",
                                renderer_rules_sha256=qs.renderer_rules_sha256())

    def manifest(self, name="one", profile=None, *, package_id=None, route_decision=None,
                 max_questions=None, answer_format="screening-1"):
        output = self.root / "outputs" / name
        qs.compose(profile or self.profile, "quick", output, answer_format=answer_format,
                   package_id=package_id, route_decision=route_decision,
                   max_questions=max_questions)
        return qs.read_json(output / "manifest.json")

    def _first_standard_observation(self, manifest):
        question = manifest["questions"][0]
        answer = {"question_id": question["id"], "response_kind": "score", "status": "scored",
                  "score": 8, "summary": "隔离测试结论", "information_as_of": "2026-09-01",
                  "period_start": "2026-01-01", "period_end": "2026-06-30",
                  "basis": "current", "trend": "stable", "confidence": "medium", "metrics": [],
                  "items": [], "evidence": [{"id": "e1", "title": "隔离证据",
                     "url": "https://example.com/source", "published_at": "2026-09-01",
                     "claim": "隔离测试"}], "counterevidence": "隔离测试反证",
                  "watch_triggers": [], "missing_fields": [],
                  "coverage": {"status": "partial", "reason": "仅作离线测试"}}
        receipt = {"manifest_sha256": sa.digest(manifest), "run_id": "TEST_RUN",
                   "scan_id": "TEST_SCAN", "inputset_id": "TEST_INPUT", "task_mode": "primary",
                   "comparison_group_id": None,
                   "requests": {question["id"]: {"provider": "fixture", "model_requested": "fixture",
                       "model_resolved": "fixture", "model_revision": "v1", "request_id": "r1",
                       "attempt_id": "a1", "started_at": "2026-09-22T09:00:00Z",
                       "answered_at": "2026-09-22T09:01:00Z", "search_status": "executed",
                       "search_receipt_id": "fixture-search", "prompt_sha256": question["prompt_sha256"]}}}
        return sa.build_observations(manifest, {question["id"]: answer}, receipt)["observations"][0]

    def _edit_catalog_module(self, module_id, edit):
        catalog_path = self.root / "questions/catalog.json"
        catalog = qs.read_json(catalog_path)
        entry = next(item for item in catalog["modules"] if item["id"] == module_id)
        module_path = self.root / entry["path"]
        module = qs.read_json(module_path)
        edit(module)
        entry["question_count"] = len(module["questions"])
        catalog["version"] = "3.3.0"
        qs.write_json(module_path, module)
        qs.write_json(catalog_path, catalog)

    @staticmethod
    def _add_lifecycle_metadata(module):
        module.update(activation={"mode": "automatic", "required_evidence": ["主营业务收入"],
                                  "exclude_when": ["只有概念提及"], "minimum_confidence": "medium"},
                     dependencies=[], conflicts=[], introduced_in=module["version"])

    def test_mod_02_release_is_deterministic_and_historical_archive_is_authority(self):
        first = self.publish()
        self.assertEqual(first["modules"], 48)
        self.assertEqual(first["questions"], 222)
        self.assertEqual(self.publish(), first)
        manifest = self.manifest(profile={**self.profile, "entity_id": "EXAMPLE_ENTITY_A"})
        self.assertEqual(manifest["module_package_id"], first["package_id"])
        self.assertEqual(manifest["module_release_id"], first["release_id"])
        self.assertEqual(len(qs.validate_manifest_metric_contract(manifest)), manifest["question_count"])
        self.assertEqual(len(manifest["module_locks"]), len(manifest["modules"]))
        self.assertTrue(all(q["prompt_sha256"] and q["semantic_sha256"] for q in manifest["questions"]))

        # A mutable authoring file can change after publication; the old run
        # still resolves the archived definition and prompt from its package.
        editable = self.root / "questions/industries/industrial.json"
        changed = qs.read_json(editable)
        changed["questions"][0]["question"] += " 未发布修改"
        qs.write_json(editable, changed)
        self.assertEqual(len(qs.validate_manifest_metric_contract(manifest)), manifest["question_count"])
        with self.assertRaisesRegex(ValueError, "changed or rolled-back published module version"):
            self.publish()
        changed["version"] = "3.1.0"
        qs.write_json(editable, changed)
        with self.assertRaisesRegex(ValueError, "published question content is immutable"):
            self.publish()
        self.assertEqual(registry.load_current(root=self.root)[0]["package_id"], first["package_id"])

    def test_mod_17_exact_legacy_baseline_remains_readable_and_validates_current_catalog(self):
        published = self.publish()
        package, modules, release, _ = registry.load_package(published["package_id"], root=self.root)
        self.assertEqual(package["package_id"], published["package_id"])
        self.assertEqual(len(modules), 48)
        self.assertEqual({entry["module_id"] for entry in release["modules"]}, set(modules))
        manifest = self.manifest("legacy", {**self.profile, "entity_id": "LEGACY_ENTITY"},
                                  package_id=package["package_id"], answer_format="standard-1")
        self.assertEqual(manifest["module_package_id"], package["package_id"])
        observation = self._first_standard_observation(manifest)
        self.assertEqual(observation["question_id"], manifest["questions"][0]["id"])
        catalog, validated_modules = registry.validate_source_registry(root=self.root)
        self.assertEqual(len(catalog["modules"]), 48)
        self.assertEqual(set(validated_modules), set(modules))

    def test_mod_17_rehashed_same_id_legacy_archive_is_rejected(self):
        original = self.publish()
        package, _, release, _ = registry.load_package(original["package_id"], root=self.root)
        release_body = {key: copy.deepcopy(value) for key, value in release.items()
                        if key != "release_id"}
        entry = next(item for item in release_body["modules"] if item["module_id"] == "semiconductors")
        archive_path = self.root / entry["artifact_ref"]
        changed_module = json.loads(archive_path.read_text(encoding="utf-8"))
        changed_module["name"] += " 改写"
        changed_raw = mc.canonical_bytes(changed_module) + b"\n"
        changed_sha = hashlib.sha256(changed_raw).hexdigest()
        changed_ref = (f"questions/releases/artifacts/semiconductors/"
                       f"{changed_module['version'].replace('.', '_')}-{changed_sha}.json")
        entry["artifact_ref"] = changed_ref
        entry["artifact_sha256"] = changed_sha
        sealed_release = mc.seal_release(release_body)
        registry._write_immutable(self.root / changed_ref, changed_raw)
        registry._atomic_json(registry._lock_path(self.root, sealed_release["release_id"]), sealed_release)

        package_body = {key: copy.deepcopy(value) for key, value in package.items()
                        if key != "package_id"}
        package_body["release_id"] = sealed_release["release_id"]
        forged_package = {**package_body, "package_id": "pkg_" + mc.digest(package_body)}
        registry._atomic_json(registry._package_path(self.root, forged_package["package_id"]), forged_package)
        with self.assertRaisesRegex(ValueError, "untrusted legacy module archive"):
            registry.load_package(forged_package["package_id"], root=self.root)

    def test_mod_17_unknown_module_cannot_claim_legacy_without_exact_baseline_bytes(self):
        self.publish()
        catalog_path = self.root / "questions/catalog.json"
        catalog = qs.read_json(catalog_path)
        module = qs.read_json(self.root / "questions/industries/semiconductors.json")
        module.update(module_id="unregistered_industry", version="1.0.0", name="未知行业")
        for index, question in enumerate(module["questions"], 1):
            question["id"] = f"UNREGISTERED_INDUSTRY_{index:02}"
            question["metric_id"] = "score." + question["id"].lower()
        path = self.root / "questions/industries/unregistered_industry.json"
        qs.write_json(path, module)
        catalog["modules"].append({"id": module["module_id"], "kind": module["kind"],
                                   "name": module["name"],
                                   "path": "questions/industries/unregistered_industry.json",
                                   "applies_when": module["applies_when"],
                                   "question_count": len(module["questions"])})
        catalog["version"] = "3.3.0"
        qs.write_json(catalog_path, catalog)
        with self.assertRaisesRegex(ValueError, "untrusted legacy module archive"):
            self.publish()

    def test_mod_17_package_cannot_self_assert_legacy_status(self):
        published = self.publish()
        package, _, _, _ = registry.load_package(published["package_id"], root=self.root)
        body = {key: copy.deepcopy(value) for key, value in package.items() if key != "package_id"}
        body["legacy_ids"] = ["semiconductors"]
        forged = {**body, "package_id": "pkg_" + mc.digest(body)}
        registry._atomic_json(registry._package_path(self.root, forged["package_id"]), forged)
        with self.assertRaisesRegex(ValueError, "fields are incomplete or unexpected"):
            registry.load_package(forged["package_id"], root=self.root)

    def test_mod_17_rehashed_current_catalog_edit_is_rejected(self):
        self.publish()
        module_path = self.root / "questions/industries/industrial.json"
        module = qs.read_json(module_path)
        module["name"] += " 改写"
        qs.write_json(module_path, module)
        with self.assertRaisesRegex(ValueError, "untrusted legacy module archive"):
            qs.validate_library()

    def test_mod_17_pinned_baseline_cannot_be_redeclared(self):
        baseline = self.root / "schemas/quick_scan/module-legacy-baseline.json"
        baseline.write_bytes(baseline.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "legacy module baseline hash mismatch"):
            self.publish()

    def test_release_and_catalog_paths_reject_parent_directory_symlinks(self):
        original = self.root / "questions"
        renamed = self.root / "questions-real"
        original.rename(renamed)
        link = self.root / "questions"
        if os.name == "nt":
            result = subprocess.run(["cmd.exe", "/c", "mklink", "/J", str(link), str(renamed)],
                                    capture_output=True, check=False)
            if result.returncode != 0:
                renamed.rename(original)
                self.skipTest("directory junction creation is unavailable on this Windows host")
        else:
            try:
                link.symlink_to(renamed, target_is_directory=True)
            except OSError:
                renamed.rename(original)
                self.skipTest("directory symlinks are unavailable on this host")
        try:
            with self.assertRaisesRegex(ValueError, "release archive symlink is forbidden"):
                registry._safe_path(self.root, "questions/releases/packages/example.json")
            with self.assertRaisesRegex(ValueError, "catalog module symlink is forbidden"):
                registry.source_catalog(self.root)
        finally:
            if os.name == "nt" and getattr(link, "is_junction", lambda: False)():
                link.rmdir()
            else:
                link.unlink()
            renamed.rename(original)

    def test_mod_03_append_keeps_old_question_meaning_and_old_run_readable(self):
        old = self.publish()
        profile = {**self.profile, "industry_modules": ["semiconductors"], "entity_id": "ENTITY_SEMI"}
        old_manifest = self.manifest("old", profile, package_id=old["package_id"])

        def append(module):
            self._add_lifecycle_metadata(module)
            question = copy.deepcopy(module["questions"][0])
            question.update(id="SEMI_NEW_01", metric_id="score.semi_new_01",
                            question="新增且独立的半导体问题？", priority=1)
            module["questions"].append(question)
            module["version"] = "3.1.0"

        self._edit_catalog_module("semiconductors", append)
        new = self.publish()
        self.assertNotEqual(old["package_id"], new["package_id"])
        new_manifest = self.manifest("new", profile)
        self.assertIn("SEMI_NEW_01", {q["id"] for q in new_manifest["questions"]})
        old_fingerprints = {q["id"]: q["semantic_sha256"] for q in old_manifest["questions"]}
        new_fingerprints = {q["id"]: q["semantic_sha256"] for q in new_manifest["questions"]}
        self.assertEqual(old_fingerprints, {qid: new_fingerprints[qid] for qid in old_fingerprints})
        self.assertEqual(len(qs.validate_manifest_metric_contract(old_manifest)), old_manifest["question_count"])
        self.assertEqual(len(qs.validate_manifest_metric_contract(new_manifest)), new_manifest["question_count"])

    def test_two_consecutive_major_retirements_publish_against_adjacent_version(self):
        baseline = self.publish()
        retired = "SEMICONDUCTORS_01"

        def first_major(module):
            self._add_lifecycle_metadata(module)
            previous = next(q for q in module["questions"] if q["id"] == retired)
            successor = copy.deepcopy(previous)
            successor.update(id="SEMI_SUCCESSOR_01", metric_id="score.semi_successor_01",
                             supersedes=retired)
            module["questions"] = [q for q in module["questions"] if q["id"] != retired] + [successor]
            module["retired_question_ids"] = [retired]
            module["version"] = "4.0.0"

        self._edit_catalog_module("semiconductors", first_major)
        middle = self.publish()

        def second_major(module):
            previous = next(q for q in module["questions"] if q["id"] == "SEMI_SUCCESSOR_01")
            successor = copy.deepcopy(previous)
            successor.update(id="SEMI_SUCCESSOR_02", metric_id="score.semi_successor_02",
                             supersedes="SEMI_SUCCESSOR_01")
            module["questions"] = [q for q in module["questions"] if q["id"] != "SEMI_SUCCESSOR_01"] + [successor]
            module["retired_question_ids"] = [retired, "SEMI_SUCCESSOR_01"]
            module["version"] = "5.0.0"

        self._edit_catalog_module("semiconductors", second_major)
        latest = self.publish()
        self.assertEqual(latest["questions"], baseline["questions"])
        self.assertEqual(len(registry.load_package(middle["package_id"], root=self.root)[1]), 48)
        self.assertEqual(len(registry.load_package(baseline["package_id"], root=self.root)[1]), 48)
        release = registry.load_current(root=self.root)[2]
        self.assertEqual(release["retired_question_ids"], ["SEMICONDUCTORS_01", "SEMI_SUCCESSOR_01"])

    def test_mod_04_unregistered_industry_and_missing_context_fail_before_activation(self):
        old = self.publish()
        catalog_path = self.root / "questions/catalog.json"
        catalog = qs.read_json(catalog_path)
        clone = qs.read_json(self.root / "questions/industries/semiconductors.json")
        clone.update(module_id="future_industry", version="1.0.0", kind="industries",
                     name="虚构新行业", applies_when="有实质业务及来源才启用",
                     activation={"mode": "automatic", "required_evidence": ["主营收入"],
                                 "exclude_when": ["只有概念"], "minimum_confidence": "medium"},
                     dependencies=[], conflicts=[], introduced_in="1.0.0")
        for index, question in enumerate(clone["questions"], 1):
            question["id"] = f"FUTURE_INDUSTRY_{index:02}"
            question["metric_id"] = "score." + question["id"].lower()
        path = self.root / "questions/industries/future_industry.json"
        qs.write_json(path, clone)
        catalog["modules"].append({"id": "future_industry", "kind": "industries",
                                   "name": clone["name"], "path": "questions/industries/future_industry.json",
                                   "applies_when": clone["applies_when"],
                                   "question_count": len(clone["questions"])})
        catalog["version"] = "3.3.0"
        qs.write_json(catalog_path, catalog)
        with self.assertRaisesRegex(ValueError, "missing scoring context"):
            self.publish()
        self.assertEqual(registry.load_current(root=self.root)[0]["package_id"], old["package_id"])
        contexts_path = self.root / "questions/scoring-contexts.json"
        contexts = qs.read_json(contexts_path)
        contexts["industries"]["future_industry"] = "按可核实业务边界判断新行业。"
        qs.write_json(contexts_path, contexts)
        new = self.publish()
        self.assertNotEqual(new["package_id"], old["package_id"])

    def test_mod_07_tamper_or_missing_archive_rejects_old_run(self):
        published = self.publish()
        package, _, release, _ = registry.load_package(published["package_id"], root=self.root)
        ref = release["modules"][0]["artifact_ref"]
        path = self.root / ref
        original = path.read_bytes()
        path.write_bytes(original + b" ")
        with self.assertRaisesRegex(ValueError, "archive hash mismatch"):
            registry.load_package(package["package_id"], root=self.root)
        path.write_bytes(original)
        path.unlink()
        with self.assertRaisesRegex(ValueError, "archive unavailable"):
            registry.load_package(package["package_id"], root=self.root)

    def test_manifest_prompt_forgery_is_rejected_even_with_recomputed_prompt_hash(self):
        self.publish()
        original = self.manifest("authentic", {**self.profile, "entity_id": "EXAMPLE_ENTITY_A"})
        forgery = copy.deepcopy(original)
        forgery["questions"][0]["prompt"] += " forged instruction"
        forgery["questions"][0]["prompt_sha256"] = hashlib.sha256(
            forgery["questions"][0]["prompt"].encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "prompt or semantic fingerprint mismatch"):
            qs.validate_manifest_metric_contract(forgery)

    def test_archived_metric_schema_survives_mutable_schema_change(self):
        self.publish()
        manifest = self.manifest("old", {**self.profile, "entity_id": "EXAMPLE_ENTITY_A"})
        schema_path = self.root / "schemas/quick_scan/metric.schema.json"
        schema = qs.read_json(schema_path)
        schema["definitions"]["QuestionMetricMapping"]["properties"]["dimension"]["enum"] = ["forbidden_future_dimension"]
        qs.write_json(schema_path, schema)
        self.assertEqual(len(qs.validate_manifest_metric_contract(manifest)), manifest["question_count"])

    def test_unavailable_historical_renderer_fails_closed_without_losing_archive(self):
        published = self.publish()
        manifest = self.manifest("old", {**self.profile, "entity_id": "EXAMPLE_ENTITY_A"})
        with mock.patch.object(manifest_contract, "renderer_rules_sha256", return_value="f" * 64):
            with self.assertRaisesRegex(ValueError, "historical renderer implementation unavailable"):
                qs.validate_manifest_metric_contract(manifest)
        # Stored release and questions remain readable even when the local
        # renderer implementation cannot verify an old prompt.
        _, modules, _, _ = registry.load_package(published["package_id"], root=self.root)
        self.assertEqual(len(modules), 48)

    def test_prior_package_without_observation_schema_is_readable_but_cannot_issue_observations(self):
        published = self.publish()
        current, modules, release, _ = registry.load_package(published["package_id"], root=self.root)
        old_body = {key: copy.deepcopy(value) for key, value in current.items() if key != "package_id"}
        del old_body["format_resources"]["schemas/observation.schema.json"]
        del old_body["semantic_fingerprint_version"]
        old_package_id = "pkg_" + mc.digest(old_body)
        old_package = {**old_body, "package_id": old_package_id}
        qs.write_json(self.root / f"questions/releases/packages/{old_package_id}.json", old_package)
        self.assertEqual(len(registry.load_package(old_package_id, root=self.root)[1]), len(modules))
        profile = {**self.profile, "entity_id": "EXAMPLE_ENTITY_A"}
        output = self.root / "outputs/older-standard"
        with self.assertRaisesRegex(ValueError, "historical read only"):
            qs.compose(profile, "quick", output, answer_format="standard-1", package_id=old_package_id)
        self.assertFalse(output.exists(), "old package must fail before exporting billable prompts")
        # Other historical package content remains readable and verifiable.
        screening = self.manifest("older-screening", profile, package_id=old_package_id)
        self.assertEqual(len(qs.validate_manifest_metric_contract(screening)), screening["question_count"])

    def test_real_pre_observation_package_cannot_export_standard_run(self):
        old_package_id = "pkg_92fc696506725d96746db07a308cb171e0c52f2c0c100b15e8085785de283006"
        package, modules, _, _ = registry.load_package(old_package_id, root=ROOT)
        self.assertEqual(package["package_id"], old_package_id)
        self.assertEqual(len(modules), 48)
        output = self.root / "outputs/real-old-standard"
        with mock.patch.object(qs, "ROOT", ROOT):
            with self.assertRaisesRegex(ValueError, "historical read only"):
                qs.compose({**self.profile, "entity_id": "EXAMPLE_ENTITY_A"}, "quick", output,
                           answer_format="standard-1", package_id=old_package_id)
        self.assertFalse(output.exists())

    def test_answer_format_description_change_invalidates_standard_method_comparison(self):
        self.publish()
        profile = {**self.profile, "entity_id": "EXAMPLE_ENTITY_A", "as_of": "2026-09-22"}
        first_dir = self.root / "outputs/format-before"
        qs.compose(profile, "quick", first_dir, answer_format="standard-1")
        first_manifest = qs.read_json(first_dir / "manifest.json")
        first = self._first_standard_observation(first_manifest)

        answer_path = self.root / "schemas/answer-content.schema.json"
        answer_schema = qs.read_json(answer_path)
        answer_schema["description"] = "新版格式提示：描述字段变化也进入方法指纹"
        qs.write_json(answer_path, answer_schema)
        second_package = self.publish()
        second_dir = self.root / "outputs/format-after"
        qs.compose(profile, "quick", second_dir, answer_format="standard-1")
        second_manifest = qs.read_json(second_dir / "manifest.json")
        second = self._first_standard_observation(second_manifest)

        self.assertNotEqual(first_manifest["module_package_id"], second_package["package_id"])
        self.assertNotEqual(first_manifest["questions"][0]["prompt_sha256"],
                            second_manifest["questions"][0]["prompt_sha256"])
        self.assertNotEqual(first["question_semantic_sha256"], second["question_semantic_sha256"])
        self.assertNotEqual(first["method_id"], second["method_id"])
        self.assertIn("method_id_changed", sa.compare(first, second, "time")["reasons"])
        self.assertEqual(len(qs.validate_manifest_metric_contract(first_manifest)),
                         first_manifest["question_count"])

    def test_published_observation_uses_frozen_answer_schema_and_question_after_source_edit(self):
        self.publish()
        profile = {**self.profile, "entity_id": "EXAMPLE_ENTITY_A", "as_of": "2026-09-22"}
        output = self.root / "outputs/standard"
        qs.compose(profile, "quick", output, answer_format="standard-1")
        manifest = qs.read_json(output / "manifest.json")
        question = manifest["questions"][0]
        answer = {"question_id": question["id"], "response_kind": "score", "status": "scored",
                  "score": 8, "summary": "隔离测试，不代表真实投资判断。",
                  "information_as_of": "2026-09-01", "period_start": "2026-01-01",
                  "period_end": "2026-06-30", "basis": "current", "trend": "stable",
                  "confidence": "medium", "metrics": [{
                      "metric_id": "operating.repeat_purchase_share", "value": 82,
                      "unit": "percent", "currency": None, "unit_detail": None,
                      "period_start": "2026-01-01", "period_end": "2026-06-30",
                      "basis": "current", "definition": "隔离测试重复采购占比",
                      "evidence_ids": ["e1"]}], "items": [],
                  "evidence": [{"id": "e1", "title": "隔离示例", "url": "https://example.com/source",
                                "published_at": "2026-09-01", "claim": "隔离示例"}],
                  "counterevidence": "隔离示例反证", "watch_triggers": [],
                  "missing_fields": [], "coverage": {"status": "partial", "reason": "隔离示例"}}
        receipt = {"manifest_sha256": sa.digest(manifest), "run_id": "TEST_RUN",
                   "scan_id": "TEST_SCAN", "inputset_id": "TEST_INPUT", "task_mode": "primary",
                   "comparison_group_id": None,
                   "requests": {question["id"]: {"provider": "fixture", "model_requested": "fixture",
                       "model_resolved": "fixture", "model_revision": "v1", "request_id": "r1",
                       "attempt_id": "a1", "started_at": "2026-09-22T09:00:00Z",
                       "answered_at": "2026-09-22T09:01:00Z", "search_status": "executed",
                       "search_receipt_id": "fixture-search", "prompt_sha256": question["prompt_sha256"]}}}
        record = sa.build_observations(manifest, {question["id"]: answer}, receipt)["observations"][0]
        self.assertEqual(record["answer"]["score"], 8)
        answer_schema_path = self.root / "schemas/answer-content.schema.json"
        answer_schema = qs.read_json(answer_schema_path)
        answer_schema["properties"]["score"] = {"const": 1}
        qs.write_json(answer_schema_path, answer_schema)
        observation_schema_path = self.root / "schemas/observation.schema.json"
        observation_schema = qs.read_json(observation_schema_path)
        observation_schema["properties"]["entity_id"]["maxLength"] = 1
        qs.write_json(observation_schema_path, observation_schema)
        metric_registry_path = self.root / "questions/metric-registry.json"
        metric_registry = qs.read_json(metric_registry_path)
        metric_registry["metrics"]["operating.repeat_purchase_share"]["unit"] = "ratio"
        qs.write_json(metric_registry_path, metric_registry)
        editable_common = self.root / "questions/common.json"
        common = qs.read_json(editable_common)
        common["questions"][0]["id"] = "FORGED_CURRENT_ID"
        qs.write_json(editable_common, common)
        sa.validator.cache_clear()
        self.assertEqual(sa.validate_observation(record)["observation_id"], record["observation_id"])
        rebuilt = sa.build_observations(manifest, {question["id"]: answer}, receipt)["observations"][0]
        self.assertEqual(rebuilt, record)

    def test_mod_08_budget_defers_only_optional_questions(self):
        self.publish()
        profile = {**self.profile, "entity_id": "EXAMPLE_ENTITY_A"}
        package, modules, release, contexts = registry.load_current(root=self.root)
        chosen, _, _ = qs.select_questions(profile, "quick", modules, contexts)
        mandatory = sum(q["comparison_role"] == "core" or q.get("critical", False) for q in chosen)
        self.assertGreater(len(chosen), mandatory)
        with self.assertRaisesRegex(ValueError, "below mandatory"):
            self.manifest("too-small", profile, max_questions=mandatory - 1)
        self.assertFalse((self.root / "outputs/too-small").exists())
        manifest = self.manifest("bounded", profile, max_questions=mandatory)
        self.assertEqual(manifest["question_count"], mandatory)
        self.assertTrue(manifest["deferred_questions"])
        self.assertEqual(len(manifest["deferred_questions"]), len(chosen) - mandatory)
        self.assertTrue(all(q["comparison_role"] == "core" or q.get("critical")
                            for q in manifest["questions"]))
        self.assertEqual(len(qs.validate_manifest_metric_contract(manifest)), mandatory)

    def test_unrelated_context_does_not_relabel_industrial_question_but_global_rule_does(self):
        self.publish()
        profile = {**self.profile, "entity_id": "EXAMPLE_ENTITY_A"}
        original = self.manifest("before", profile)
        contexts_path = self.root / "questions/scoring-contexts.json"
        contexts = qs.read_json(contexts_path)
        contexts["industries"]["software"] += " 新口径。"
        qs.write_json(contexts_path, contexts)
        self.publish()
        after_unrelated = self.manifest("unrelated", profile)
        self.assertEqual([(q["id"], q["semantic_sha256"], q["prompt_sha256"])
                          for q in original["questions"]],
                         [(q["id"], q["semantic_sha256"], q["prompt_sha256"])
                          for q in after_unrelated["questions"]])
        contexts["global"][0] += " 共有规则改变。"
        qs.write_json(contexts_path, contexts)
        self.publish()
        after_shared = self.manifest("shared", profile)
        self.assertNotEqual(original["questions"][0]["semantic_sha256"],
                            after_shared["questions"][0]["semantic_sha256"])
        self.assertNotEqual(original["questions"][0]["prompt_sha256"],
                            after_shared["questions"][0]["prompt_sha256"])

    def test_new_manual_lens_and_automatic_common_extension_are_separate_from_core(self):
        self.publish()
        base_profile = {**self.profile, "entity_id": "EXAMPLE_ENTITY_A"}
        original = self.manifest("before", base_profile)
        catalog_path = self.root / "questions/catalog.json"
        catalog = qs.read_json(catalog_path)
        source = qs.read_json(self.root / "questions/industries/semiconductors.json")
        for module_id, kind, mode, qid in (
                ("pricing_lens", "lenses", "manual", "PRICING_LENS_01"),
                ("universal_extension", "common_extensions", "automatic", "UNIVERSAL_EXT_01")):
            module = copy.deepcopy(source)
            question = copy.deepcopy(source["questions"][0])
            question.update(id=qid, metric_id="score." + qid.lower(),
                            construct_id=None, comparison_role="context", priority=1)
            module.update(module_id=module_id, version="1.0.0", kind=kind,
                          name=module_id, applies_when="有可核实的经济机制才使用",
                          activation={"mode": mode, "required_evidence": ["经营证据"],
                                      "exclude_when": ["无经营关联"], "minimum_confidence": "medium"},
                          dependencies=[], conflicts=[], introduced_in="1.0.0", questions=[question])
            reference = f"questions/{kind}/{module_id}.json"
            qs.write_json(self.root / reference, module)
            catalog["modules"].append({"id": module_id, "kind": kind, "name": module_id,
                                       "path": reference, "applies_when": module["applies_when"],
                                       "question_count": 1})
        catalog["version"] = "3.3.0"
        qs.write_json(catalog_path, catalog)
        contexts_path = self.root / "questions/scoring-contexts.json"
        contexts = qs.read_json(contexts_path)
        contexts["lenses"] = {"pricing_lens": "明确用户投资视角，不进入核心分母。"}
        contexts["common_extensions"] = {"universal_extension": "新增通用观察，不改变24核心构念。"}
        qs.write_json(contexts_path, contexts)
        self.publish()
        automatic = self.manifest("automatic", base_profile)
        self.assertIn("UNIVERSAL_EXT_01", {q["id"] for q in automatic["questions"]})
        self.assertNotIn("PRICING_LENS_01", {q["id"] for q in automatic["questions"]})
        with_lens = self.manifest("lens", {**base_profile,
                                            "investment_lenses": ["pricing_lens"],
                                            "lens_rationale": {"pricing_lens": "显式研究定价能力"}})
        self.assertIn("PRICING_LENS_01", {q["id"] for q in with_lens["questions"]})
        self.assertEqual(original["method_id"], with_lens["method_id"])
        self.assertEqual(sum(q["comparison_role"] == "core" for q in with_lens["questions"]), 24)
        self.assertEqual(len(qs.validate_manifest_metric_contract(with_lens)), with_lens["question_count"])

        package, modules, release, _ = registry.load_current(root=self.root)
        selected = {"common", "operating", "industrial", "mature", "cyclical",
                    "cross_border", "universal_extension", "pricing_lens"}
        source = {"title": "fixture", "url": "https://example.com/route", "published_at": "2026-09-01"}
        decisions = [{"module_id": entry["module_id"], "module_version": entry["version"],
                      "decision": "selected" if entry["module_id"] in selected else "rejected",
                      "basis": "searched_llm", "confidence": "high", "rationale": "fixture",
                      "sources": [source]} for entry in release["modules"]]
        route = mc.seal_route_decision({"schema_version": "1.0.0", "release_id": release["release_id"],
                                        "router_version": release["router_version"],
                                        "entity_id": base_profile["entity_id"], "as_of": base_profile["as_of"],
                                        "decided_at": "2026-09-19T12:00:00Z", "status": "resolved",
                                        "module_decisions": decisions})
        with self.assertRaisesRegex(ValueError, "manual lens"):
            self.manifest("llm-lens", base_profile, package_id=package["package_id"],
                          route_decision=route)
        authorized_profile = {**base_profile, "investment_lenses": ["pricing_lens"],
                              "lens_rationale": {"pricing_lens": "用户明确启用"}}
        manual_body = copy.deepcopy({key: value for key, value in route.items() if key != "decision_id"})
        manual_lens = next(item for item in manual_body["module_decisions"]
                           if item["module_id"] == "pricing_lens")
        manual_lens.update(basis="manual", sources=[], manual_override={
            "actor": "fixture-user", "reason": "显式投资视角",
            "valid_until": "2026-09-20T12:00:00Z"})
        authorized_route = mc.seal_route_decision(manual_body)
        authorized_manifest = self.manifest("manual-lens", authorized_profile,
                                            package_id=package["package_id"],
                                            route_decision=authorized_route)
        self.assertEqual(len(qs.validate_manifest_metric_contract(authorized_manifest)),
                         authorized_manifest["question_count"])
        tampered = copy.deepcopy(authorized_manifest)
        tampered_body = {key: value for key, value in tampered["route_decision"].items()
                         if key != "decision_id"}
        tampered_lens = next(item for item in tampered_body["module_decisions"]
                             if item["module_id"] == "pricing_lens")
        tampered_lens["basis"] = "searched_llm"
        tampered_lens["sources"] = [source]
        del tampered_lens["manual_override"]
        tampered["route_decision"] = mc.seal_route_decision(tampered_body)
        tampered["route_decision_id"] = tampered["route_decision"]["decision_id"]
        with self.assertRaisesRegex(ValueError, "manual lens"):
            qs.validate_manifest_metric_contract(tampered)

    def test_module_order_in_profile_is_canonical_for_same_membership(self):
        self.publish()
        profile = {**self.profile, "entity_id": "EXAMPLE_ENTITY_A",
                   "industry_modules": ["software", "industrial"]}
        first = self.manifest("first", profile)
        second = self.manifest("second", {**profile, "industry_modules": ["industrial", "software"]})
        self.assertEqual(first, second)

    def test_partial_route_uses_common_and_known_risk_without_fabricated_classification(self):
        self.publish()
        package, modules, release, _ = registry.load_current(root=self.root)
        profile = {"company": "虚构待分类公司", "ticker": "X", "exchange": "TEST",
                   "as_of": "2026-09-19", "entity_id": "ENTITY_PARTIAL"}
        source = {"title": "fixture", "url": "https://example.com/route", "published_at": "2026-09-01"}
        decisions = [{"module_id": entry["module_id"], "module_version": entry["version"],
                      "decision": "selected" if entry["module_id"] in {"common", "distressed"} else "uncertain",
                      "basis": "deterministic", "confidence": "high", "rationale": "fixture route",
                      "sources": [source]} for entry in release["modules"]]
        route = mc.seal_route_decision({"schema_version": "1.0.0", "release_id": release["release_id"],
                                        "router_version": release["router_version"],
                                        "entity_id": profile["entity_id"], "as_of": profile["as_of"],
                                        "decided_at": "2026-09-19T12:00:00Z", "status": "partial",
                                        "module_decisions": decisions})
        manifest = self.manifest("partial", profile, package_id=package["package_id"],
                                 route_decision=route)
        self.assertEqual(manifest["modules"], ["common", "distressed"])
        self.assertNotIn("company_type", manifest["profile"])
        self.assertNotIn("stage", manifest["profile"])
        self.assertIn("分类待核实", manifest["questions"][0]["prompt"])
        self.assertEqual(len(qs.validate_manifest_metric_contract(manifest)), manifest["question_count"])


if __name__ == "__main__":
    unittest.main()
