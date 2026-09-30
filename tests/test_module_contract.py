"""S04 fixed counterexamples for modular question publication contracts."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

from jsonschema import ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import module_contract as mc  # noqa: E402


class ModuleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "questions/catalog.json").read_text(encoding="utf-8"))
        cls.modules = {entry["id"]: json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
                       for entry in cls.catalog["modules"]}
        cls.contexts = json.loads((ROOT / "questions/scoring-contexts.json").read_text(encoding="utf-8"))

    def future_industry(self):
        module = copy.deepcopy(self.modules["semiconductors"])
        module.update(module_id="future_industry", version="1.0.0", kind="industries",
                      name="虚构新行业", applies_when="虚构新行业有实质收入与可核实来源",
                      activation={"mode": "automatic", "required_evidence": ["主营收入"],
                                  "exclude_when": ["只有概念提及"], "minimum_confidence": "medium"},
                      dependencies=[], conflicts=[], introduced_in="1.0.0")
        for index, question in enumerate(module["questions"], start=1):
            question["id"] = f"FUTURE_INDUSTRY_{index:02}"
            question["metric_id"] = "score." + question["id"].lower()
        return module

    def release(self):
        artifacts = {}
        records = []
        for module_id in ("common", "semiconductors"):
            module = self.modules[module_id]
            ref = f"questions/releases/baseline/{module_id}.json"
            raw = mc.canonical_bytes(module)
            artifacts[ref] = raw
            records.append({
                "module_id": module_id, "kind": module["kind"], "version": module["version"],
                "artifact_ref": ref, "artifact_sha256": hashlib.sha256(raw).hexdigest(),
                "question_semantics": [{"question_id": q["id"], "rubric_version": q["rubric_version"],
                                         "definition_sha256": mc.question_definition_sha256(q)}
                                        for q in module["questions"]]})
        body = {"schema_version": "1.0.0", "catalog_version": self.catalog["version"],
                "renderer_version": "1.0.0", "router_version": "1.0.0",
                "retired_question_ids": [], "modules": records}
        return mc.seal_release(body), artifacts

    def release_with_modules(self, *modules, retired_question_ids=()):
        release, artifacts = self.release()
        body = {key: copy.deepcopy(value) for key, value in release.items()
                if key != "release_id"}
        body["retired_question_ids"] = list(retired_question_ids)
        for module in modules:
            ref = f"questions/releases/fixtures/{module['module_id']}.json"
            raw = mc.canonical_bytes(module)
            artifacts[ref] = raw
            body["modules"].append({
                "module_id": module["module_id"], "kind": module["kind"],
                "version": module["version"], "artifact_ref": ref,
                "artifact_sha256": hashlib.sha256(raw).hexdigest(),
                "question_semantics": [
                    {"question_id": q["id"], "rubric_version": q["rubric_version"],
                     "definition_sha256": mc.question_definition_sha256(q)}
                    for q in module["questions"]
                ],
            })
        return mc.seal_release(body), artifacts

    def registry_with_modules(self, *modules):
        registry = {"common": copy.deepcopy(self.modules["common"])}
        contexts = copy.deepcopy(self.contexts)
        for module in modules:
            registry[module["module_id"]] = module
            contexts.setdefault(module["kind"], {})[module["module_id"]] = (
                f"按可核实业务边界分析{module['name']}。"
            )
        return registry, contexts

    def test_existing_48_modules_keep_their_shape_and_registry(self):
        self.assertEqual(len(self.modules), 48)
        mc.validate_registry(self.modules, self.contexts, legacy_ids=frozenset(self.modules))

    def test_new_module_requires_complete_registration_before_export(self):
        modules = {"common": self.modules["common"], "future_industry": self.future_industry()}
        with self.assertRaisesRegex(ValueError, "missing scoring context"):
            mc.validate_registry(modules, self.contexts, legacy_ids=frozenset({"common"}))
        contexts = copy.deepcopy(self.contexts)
        contexts["industries"]["future_industry"] = "按真实业务边界核实新行业经济性。"
        mc.validate_registry(modules, contexts, legacy_ids=frozenset({"common"}))
        del modules["future_industry"]["activation"]
        with self.assertRaisesRegex(ValueError, "activation evidence"):
            mc.validate_registry(modules, contexts, legacy_ids=frozenset({"common"}))

    def test_new_lens_requires_user_selection_not_llm_auto_activation(self):
        lens = self.future_industry()
        lens.update(module_id="pricing_lens", kind="lenses")
        lens["activation"]["mode"] = "automatic"
        with self.assertRaises(ValidationError):
            mc.validate_module(lens)
        lens["activation"]["mode"] = "manual"
        contexts = copy.deepcopy(self.contexts)
        contexts["lenses"] = {"pricing_lens": "用户显式选择的定价能力视角。"}
        mc.validate_registry({"common": self.modules["common"], "pricing_lens": lens},
                             contexts, legacy_ids=frozenset({"common"}))

    def test_module_dependencies_and_question_ids_fail_closed(self):
        modules = {"common": self.modules["common"], "future_industry": self.future_industry()}
        contexts = copy.deepcopy(self.contexts)
        contexts["industries"]["future_industry"] = "明确口径"
        modules["future_industry"]["dependencies"] = ["missing_module"]
        with self.assertRaisesRegex(ValueError, "unknown dependency"):
            mc.validate_registry(modules, contexts, legacy_ids=frozenset({"common"}))
        modules["future_industry"]["dependencies"] = []
        modules["future_industry"]["questions"][0]["id"] = "IQS_01"
        modules["future_industry"]["questions"][0]["metric_id"] = "score.iqs_01"
        with self.assertRaisesRegex(ValueError, "duplicate question ID across"):
            mc.validate_registry(modules, contexts, legacy_ids=frozenset({"common"}))

    def test_append_is_minor_and_old_question_meaning_cannot_change(self):
        old = self.modules["semiconductors"]
        new = copy.deepcopy(old)
        new["version"] = "3.1.0"
        appended = copy.deepcopy(old["questions"][-1])
        appended["id"] = "SEMICONDUCTORS_05"
        appended["metric_id"] = "score.semiconductors_05"
        new["questions"].append(appended)
        mc.validate_upgrade(old, new)
        self.assertEqual(old["questions"], new["questions"][:-1])
        new["version"] = "3.0.1"
        with self.assertRaisesRegex(ValueError, "minor or major"):
            mc.validate_upgrade(old, new)
        new["version"] = "3.1.0"
        new["questions"][0]["anchors"]["10"] = "改写了十分快速量表"
        with self.assertRaisesRegex(ValueError, "published question content is immutable"):
            mc.validate_upgrade(old, new)

    def test_same_id_copyedit_is_rejected_even_with_self_asserted_review(self):
        old = self.modules["semiconductors"]
        new = copy.deepcopy(old)
        new["version"] = "3.0.1"
        new["questions"][0]["question"] += "（修正标点）"
        with self.assertRaisesRegex(ValueError, "published question content is immutable"):
            mc.validate_upgrade(old, new)
        new = copy.deepcopy(old)
        new["version"] = "3.1.0"
        correction = copy.deepcopy(new["questions"][0])
        correction["id"] = "SEMICONDUCTORS_05"
        correction["metric_id"] = "score.semiconductors_05"
        correction["supersedes"] = "SEMICONDUCTORS_01"
        correction["question"] += "（修正标点）"
        new["questions"].append(correction)
        mc.validate_upgrade(old, new)
        self.assertNotEqual(mc.effective_semantic_sha256(old["questions"][0],
                                                          applied_contexts=["行业口径"], renderer_version="1.0.0"),
                            mc.effective_semantic_sha256(correction,
                                                          applied_contexts=["行业口径"], renderer_version="1.0.0"))

    def test_mod_02_s04_rejects_same_id_copyedit_and_duplicate_core_replacement(self):
        old = self.modules["semiconductors"]
        old_before = copy.deepcopy(old)

        descriptive_patch = copy.deepcopy(old)
        descriptive_patch["version"] = "3.0.1"
        descriptive_patch["name"] = "半导体行业模块（显示名修订）"
        mc.validate_upgrade(old, descriptive_patch)

        copyedit = copy.deepcopy(old)
        copyedit["version"] = "3.0.1"
        copyedit["questions"][0]["question"] += "（语义编辑）"
        with self.assertRaisesRegex(ValueError, "published question content is immutable"):
            mc.validate_upgrade(old, copyedit)
        self.assertEqual(old, old_before)

        same_ids_scope_change = copy.deepcopy(old)
        same_ids_scope_change["version"] = "3.0.1"
        same_ids_scope_change["applies_when"] = "适用范围已经发生实质变化"
        with self.assertRaisesRegex(ValueError, "applicability scope change requires successor IDs"):
            mc.validate_upgrade(old, same_ids_scope_change)

        successor_release = copy.deepcopy(old)
        successor_release["version"] = "4.0.0"
        successor_release["applies_when"] = "适用范围变化后的新定义"
        retired_ids = [question["id"] for question in old["questions"]]
        successors = []
        for index, old_question in enumerate(old["questions"], start=1):
            successor = copy.deepcopy(old_question)
            successor["id"] = f"SEMICONDUCTORS_SCOPE2_{index:02}"
            successor["metric_id"] = "score." + successor["id"].lower()
            successor["supersedes"] = old_question["id"]
            successors.append(successor)
        successor_release["questions"] = successors
        successor_release["retired_question_ids"] = retired_ids
        mc.validate_upgrade(old, successor_release)

        duplicate_type = copy.deepcopy(self.modules["operating"])
        duplicate_type["questions"][1].update(construct_id="IQS_11", replaces=["IQS_11"])
        with self.assertRaisesRegex(ValueError, "duplicate core replacement"):
            mc.validate_module(duplicate_type)

    def test_retired_question_mapping_survives_next_minor_release(self):
        v3 = self.modules["semiconductors"]
        v4 = copy.deepcopy(v3)
        v4["version"] = "4.0.0"
        old = v4["questions"].pop(0)
        v4["retired_question_ids"] = [old["id"]]
        successor = copy.deepcopy(old)
        successor["id"] = "SEMICONDUCTORS_101"
        successor["metric_id"] = "score.semiconductors_101"
        successor["supersedes"] = old["id"]
        v4["questions"].append(successor)
        mc.validate_upgrade(v3, v4)
        v41 = copy.deepcopy(v4)
        v41["version"] = "4.1.0"
        extra = copy.deepcopy(v41["questions"][-1])
        extra["id"] = "SEMICONDUCTORS_102"
        extra["metric_id"] = "score.semiconductors_102"
        del extra["supersedes"]
        v41["questions"].append(extra)
        mc.validate_upgrade(v4, v41)
        reused = copy.deepcopy(v41)
        reused["version"] = "4.2.0"
        illegal = copy.deepcopy(extra)
        illegal["id"] = old["id"]
        illegal["metric_id"] = "score." + old["id"].lower()
        illegal["question"] = "新义：只看股价涨幅？"
        reused["questions"].append(illegal)
        with self.assertRaisesRegex(ValueError, "retired question ID cannot be active"):
            mc.validate_upgrade(v41, reused)
        reused["retired_question_ids"] = []
        with self.assertRaisesRegex(ValueError, "tombstones must accumulate"):
            mc.validate_upgrade(v41, reused)

    def test_retired_id_cannot_move_to_another_module(self):
        semis = copy.deepcopy(self.modules["semiconductors"])
        semis["questions"].pop(0)
        semis["retired_question_ids"] = ["SEMICONDUCTORS_01"]
        future = self.future_industry()
        future["questions"][0]["id"] = "SEMICONDUCTORS_01"
        future["questions"][0]["metric_id"] = "score.semiconductors_01"
        contexts = copy.deepcopy(self.contexts)
        contexts["industries"]["future_industry"] = "明确口径"
        modules = {"common": self.modules["common"], "semiconductors": semis,
                   "future_industry": future}
        with self.assertRaisesRegex(ValueError, "retired question ID reused across modules"):
            mc.validate_registry(modules, contexts,
                                 legacy_ids=frozenset({"common", "semiconductors"}))

    def test_extension_cannot_disguise_a_new_core_replacement(self):
        extension = self.future_industry()
        extension["module_id"] = "universal_extra"
        extension["kind"] = "common_extensions"
        extension["questions"][0].update(comparison_role="core", construct_id="IQS_01",
                                          replaces=["IQS_01"])
        with self.assertRaisesRegex(ValueError, "non-type extension cannot enter core"):
            mc.validate_module(extension)

    def test_common_core_and_type_replacement_are_frozen(self):
        common = copy.deepcopy(self.modules["common"])
        added = copy.deepcopy(common["questions"][0])
        added.update(id="IQS_25", metric_id="score.iqs_25", construct_id="IQS_25")
        common["questions"].append(added)
        with self.assertRaisesRegex(ValueError, "frozen 24"):
            mc.validate_module(common)
        bank = copy.deepcopy(self.modules["bank"])
        bank["questions"][0].update(construct_id="IQS_25", replaces=["IQS_25"])
        with self.assertRaisesRegex(ValueError, "one frozen core construct"):
            mc.validate_module(bank)
        duplicate_type = copy.deepcopy(self.modules["operating"])
        duplicate_type["questions"][1].update(construct_id="IQS_11", replaces=["IQS_11"])
        with self.assertRaisesRegex(ValueError, "duplicate core replacement"):
            mc.validate_module(duplicate_type)

    def test_unrelated_module_does_not_change_semantic_fingerprint(self):
        question = self.modules["common"]["questions"][0]
        before = mc.effective_semantic_sha256(question, applied_contexts=["通用口径", "半导体口径"],
                                              renderer_version="1.0.0")
        modules = {**self.modules, "future_industry": self.future_industry()}
        self.assertIn("future_industry", modules)
        after = mc.effective_semantic_sha256(question, applied_contexts=["通用口径", "半导体口径"],
                                             renderer_version="1.0.0")
        changed_rule = mc.effective_semantic_sha256(question, applied_contexts=["通用口径", "半导体口径"],
                                                    renderer_version="1.0.1")
        self.assertEqual(before, after)
        self.assertNotEqual(before, changed_rule)

    def test_historical_release_resolves_old_archive_not_current_catalog(self):
        release, artifacts = self.release()
        old_modules = mc.validate_release(release, artifacts.__getitem__)
        self.assertEqual(old_modules["semiconductors"]["questions"][0]["id"], "SEMICONDUCTORS_01")
        current_changed = copy.deepcopy(self.modules["semiconductors"])
        current_changed["version"] = "99.0.0"
        self.assertNotEqual(current_changed["version"], old_modules["semiconductors"]["version"])
        self.assertEqual(mc.validate_release(release, artifacts.__getitem__)["semiconductors"],
                         self.modules["semiconductors"])
        altered = copy.deepcopy(release)
        altered["catalog_version"] = "99.0.0"
        with self.assertRaisesRegex(ValueError, "content hash mismatch"):
            mc.validate_release(altered, artifacts.__getitem__)
        without_archive = dict(artifacts)
        del without_archive["questions/releases/baseline/semiconductors.json"]
        with self.assertRaisesRegex(ValueError, "archive unavailable"):
            mc.validate_release(release, without_archive.__getitem__)
        artifacts["questions/releases/baseline/semiconductors.json"] += b" "
        with self.assertRaisesRegex(ValueError, "archive hash mismatch"):
            mc.validate_release(release, artifacts.__getitem__)

    def test_mod_14_s04_release_static_contract_fails_closed(self):
        release, artifacts = self.release()

        duplicate_body = {key: copy.deepcopy(value) for key, value in release.items()
                          if key != "release_id"}
        duplicate_body["modules"].append(copy.deepcopy(duplicate_body["modules"][-1]))
        duplicate_release = mc.seal_release(duplicate_body)
        with self.assertRaisesRegex(ValueError, "sorted unique module IDs"):
            mc.validate_release(duplicate_release, artifacts.__getitem__)

        tampered_artifacts = dict(artifacts)
        ref = release["modules"][-1]["artifact_ref"]
        tampered_artifacts[ref] += b" "
        with self.assertRaisesRegex(ValueError, "module archive hash mismatch"):
            mc.validate_release(release, tampered_artifacts.__getitem__)

        retired_body = {key: copy.deepcopy(value) for key, value in release.items()
                        if key != "release_id"}
        retired_body["retired_question_ids"] = [release["modules"][0]["question_semantics"][0]["question_id"]]
        retired_release = mc.seal_release(retired_body)
        with self.assertRaisesRegex(ValueError, "retired question ID reused in release lock"):
            mc.validate_release(retired_release, artifacts.__getitem__)

        first = self.future_industry()
        second = copy.deepcopy(first)
        second.update(module_id="future_industry_second", name="第二虚构行业")
        for index, question in enumerate(second["questions"], start=1):
            question["id"] = f"FUTURE_INDUSTRY_SECOND_{index:02}"
            question["metric_id"] = "score." + question["id"].lower()
        first["dependencies"] = [second["module_id"]]
        second["dependencies"] = [first["module_id"]]
        modules = {"common": self.modules["common"], first["module_id"]: first,
                   second["module_id"]: second}
        contexts = copy.deepcopy(self.contexts)
        contexts["industries"][first["module_id"]] = "虚构行业A的适用口径。"
        contexts["industries"][second["module_id"]] = "虚构行业B的适用口径。"
        with self.assertRaisesRegex(ValueError, "module dependency cycle"):
            mc.validate_registry(modules, contexts, legacy_ids=frozenset({"common"}))

    def test_mod_14_a01_registry_rejects_duplicate_module_identity(self):
        module = self.future_industry()
        duplicate = copy.deepcopy(module)
        duplicate["name"] = "重复身份别名"
        registry = {"common": copy.deepcopy(self.modules["common"]),
                    "future_industry": module, "future_industry_alias": duplicate}
        contexts = copy.deepcopy(self.contexts)
        contexts["industries"][module["module_id"]] = "虚构行业适用口径。"
        with self.assertRaisesRegex(ValueError, "module ID differs from registry key"):
            mc.validate_registry(registry, contexts, legacy_ids=frozenset({"common"}))

    def test_mod_14_a02_registry_rejects_unknown_self_conflicting_and_cyclic_edges(self):
        unknown = self.future_industry()
        unknown["dependencies"] = ["missing_module"]
        unknown_conflict = self.future_industry()
        unknown_conflict["conflicts"] = ["missing_module"]
        self_cases = []
        self_dependency = self.future_industry()
        self_dependency["dependencies"] = [self_dependency["module_id"]]
        self_cases.append(self_dependency)
        self_conflict = self.future_industry()
        self_conflict["conflicts"] = [self_conflict["module_id"]]
        self_cases.append(self_conflict)
        peer = self.future_industry()
        peer["module_id"] = "future_peer"
        peer["name"] = "虚构同业模块"
        for index, question in enumerate(peer["questions"], start=1):
            question["id"] = f"FUTURE_PEER_{index:02}"
            question["metric_id"] = "score." + question["id"].lower()
        contradiction = self.future_industry()
        contradiction["dependencies"] = [peer["module_id"]]
        contradiction["conflicts"] = [peer["module_id"]]
        first = self.future_industry()
        second = copy.deepcopy(peer)
        first["dependencies"] = [second["module_id"]]
        second["dependencies"] = [first["module_id"]]

        cases = [("unknown_dependency", (unknown,), "unknown dependency or conflict"),
                 ("unknown_conflict", (unknown_conflict,), "unknown dependency or conflict"),
                 ("self_dependency", (self_dependency,), "self or dependency/conflict contradiction"),
                 ("self_conflict", (self_conflict,), "self or dependency/conflict contradiction"),
                 ("dependency_conflict_contradiction", (contradiction, peer),
                  "self or dependency/conflict contradiction"),
                 ("dependency_cycle", (first, second), "module dependency cycle")]
        for name, modules, expected_error in cases:
            with self.subTest(case=name):
                registry, contexts = self.registry_with_modules(*modules)
                with self.assertRaisesRegex(ValueError, expected_error):
                    mc.validate_registry(registry, contexts, legacy_ids=frozenset({"common"}))

    def test_mod_14_a03_release_rejects_duplicate_module_and_bad_archive_hash(self):
        release, artifacts = self.release()
        duplicate_body = {key: copy.deepcopy(value) for key, value in release.items()
                          if key != "release_id"}
        duplicate_body["modules"].append(copy.deepcopy(duplicate_body["modules"][-1]))
        duplicate_release = mc.seal_release(duplicate_body)
        with self.assertRaisesRegex(ValueError, "sorted unique module IDs"):
            mc.validate_release(duplicate_release, artifacts.__getitem__)

        damaged = dict(artifacts)
        damaged[release["modules"][-1]["artifact_ref"]] += b" "
        with self.assertRaisesRegex(ValueError, "module archive hash mismatch"):
            mc.validate_release(release, damaged.__getitem__)

    def test_mod_14_a05_release_rejects_unknown_self_and_contradictory_edges(self):
        unknown = self.future_industry()
        unknown["dependencies"] = ["missing_module"]
        unknown_conflict = self.future_industry()
        unknown_conflict["conflicts"] = ["missing_module"]
        self_dependency = self.future_industry()
        self_dependency["dependencies"] = [self_dependency["module_id"]]
        self_conflict = self.future_industry()
        self_conflict["conflicts"] = [self_conflict["module_id"]]
        peer = self.future_industry()
        peer["module_id"] = "future_peer"
        peer["name"] = "虚构同业模块"
        for index, question in enumerate(peer["questions"], start=1):
            question["id"] = f"FUTURE_PEER_{index:02}"
            question["metric_id"] = "score." + question["id"].lower()
        contradiction = self.future_industry()
        contradiction["dependencies"] = [peer["module_id"]]
        contradiction["conflicts"] = [peer["module_id"]]

        cases = [("unknown_dependency", (unknown,), "unknown dependency or conflict"),
                 ("unknown_conflict", (unknown_conflict,), "unknown dependency or conflict"),
                 ("self_dependency", (self_dependency,), "self or dependency/conflict contradiction"),
                 ("self_conflict", (self_conflict,), "self or dependency/conflict contradiction"),
                 ("dependency_conflict_contradiction", (contradiction, peer),
                  "self or dependency/conflict contradiction")]
        for name, modules, expected_error in cases:
            with self.subTest(case=name):
                release, artifacts = self.release_with_modules(*modules)
                with self.assertRaisesRegex(ValueError, expected_error):
                    mc.validate_release(release, artifacts.__getitem__)

    def test_mod_14_a06_release_rejects_module_tombstone_active_collision(self):
        module = self.future_industry()
        module["retired_question_ids"] = [module["questions"][0]["id"]]
        release, artifacts = self.release_with_modules(module)
        with self.assertRaisesRegex(ValueError, "retired question ID cannot be active again"):
            mc.validate_release(release, artifacts.__getitem__)

    def test_mod_14_a07_release_rejects_release_tombstone_active_collision(self):
        release, artifacts = self.release()
        body = {key: copy.deepcopy(value) for key, value in release.items()
                if key != "release_id"}
        body["retired_question_ids"] = [release["modules"][0]["question_semantics"][0]["question_id"]]
        body["release_id"] = "modrel_" + mc.digest(body)
        with self.assertRaisesRegex(ValueError, "retired question ID reused in release lock"):
            mc.validate_release(body, artifacts.__getitem__)

    def test_mod_14_a08_release_rejects_omitted_module_tombstone(self):
        module = self.future_industry()
        module["retired_question_ids"] = ["RETIRED_QUESTION_77"]
        release, artifacts = self.release_with_modules(module)
        self.assertNotIn("RETIRED_QUESTION_77", release["retired_question_ids"])
        with self.assertRaisesRegex(ValueError, "release lock omits module retirement tombstones"):
            mc.validate_release(release, artifacts.__getitem__)

    def test_mod_14_a09_release_returns_only_complete_valid_archive_set(self):
        release, artifacts = self.release()
        complete = mc.validate_release(release, artifacts.__getitem__)
        self.assertEqual(set(complete), {"common", "semiconductors"})
        calls = []

        def fail_on_late_archive(ref):
            calls.append(ref)
            if ref == release["modules"][-1]["artifact_ref"]:
                return artifacts[ref] + b" "
            return artifacts[ref]

        with self.assertRaisesRegex(ValueError, "module archive hash mismatch"):
            mc.validate_release(release, fail_on_late_archive)
        self.assertEqual(calls, [entry["artifact_ref"] for entry in release["modules"]])

    def test_mod_14_a10_release_allows_conflicting_alternatives_to_coexist(self):
        first = self.future_industry()
        second = copy.deepcopy(first)
        second["module_id"] = "future_industry_second"
        second["name"] = "第二虚构行业"
        for index, question in enumerate(second["questions"], start=1):
            question["id"] = f"FUTURE_INDUSTRY_SECOND_{index:02}"
            question["metric_id"] = "score." + question["id"].lower()
        first["conflicts"] = [second["module_id"]]
        second["conflicts"] = [first["module_id"]]
        release, artifacts = self.release_with_modules(first, second)
        loaded = mc.validate_release(release, artifacts.__getitem__)
        self.assertIn(first["module_id"], loaded)
        self.assertIn(second["module_id"], loaded)
        self.assertEqual(len(loaded), len(release["modules"]))

    def test_mod_14_release_reader_rejects_hash_consistent_dependency_cycle(self):
        release, original_artifacts = self.release()
        artifacts = dict(original_artifacts)
        release_body = {key: copy.deepcopy(value) for key, value in release.items()
                        if key != "release_id"}

        first = self.future_industry()
        second = copy.deepcopy(first)
        second.update(module_id="future_industry_second", name="第二虚构行业")
        for index, question in enumerate(second["questions"], start=1):
            question["id"] = f"FUTURE_INDUSTRY_SECOND_{index:02}"
            question["metric_id"] = "score." + question["id"].lower()
        first["dependencies"] = [second["module_id"]]
        second["dependencies"] = [first["module_id"]]

        for module in (first, second):
            ref = f"questions/releases/cycle/{module['module_id']}.json"
            raw = mc.canonical_bytes(module)
            artifacts[ref] = raw
            release_body["modules"].append({
                "module_id": module["module_id"],
                "kind": module["kind"],
                "version": module["version"],
                "artifact_ref": ref,
                "artifact_sha256": hashlib.sha256(raw).hexdigest(),
                "question_semantics": [
                    {"question_id": question["id"],
                     "rubric_version": question["rubric_version"],
                     "definition_sha256": mc.question_definition_sha256(question)}
                    for question in module["questions"]
                ],
            })

        cyclic_release = mc.seal_release(release_body)
        self.assertEqual(cyclic_release["release_id"],
                         "modrel_" + mc.digest({key: value for key, value in cyclic_release.items()
                                                 if key != "release_id"}))
        self.assertTrue(all(hashlib.sha256(artifacts[item["artifact_ref"]]).hexdigest()
                            == item["artifact_sha256"]
                            for item in cyclic_release["modules"]))
        with self.assertRaisesRegex(ValueError, "module dependency cycle"):
            mc.validate_release(cyclic_release, artifacts.__getitem__)

    def test_release_rejects_fake_fact_payload_as_common(self):
        release, artifacts = self.release()
        fake = {"module_id": "common", "kind": "facts", "version": "1.0.0",
                "questions": [{"id": "FAKE_01", "rubric_version": "1.0.0", "score": 99}]}
        ref = "questions/releases/baseline/common.json"
        raw = mc.canonical_bytes(fake)
        artifacts[ref] = raw
        entry = release["modules"][0]
        entry["kind"] = "facts"
        entry["version"] = "1.0.0"
        entry["artifact_sha256"] = hashlib.sha256(raw).hexdigest()
        entry["question_semantics"] = [{"question_id": "FAKE_01", "rubric_version": "1.0.0",
                                        "definition_sha256": mc.question_definition_sha256(fake["questions"][0])}]
        with self.assertRaises(ValidationError):
            mc.seal_release({k: v for k, v in release.items() if k != "release_id"})

    def test_route_decision_binds_release_and_manual_expiry(self):
        release, artifacts = self.release()
        mc.validate_release(release, artifacts.__getitem__)
        source = {"title": "虚构官方业务页", "url": "https://example.com/business",
                  "published_at": "2026-09-01"}
        body = {"schema_version": "1.0.0", "release_id": release["release_id"],
                "router_version": "1.0.0", "entity_id": "E1", "as_of": "2026-09-01",
                "decided_at": "2026-09-26T12:00:00Z",
                "status": "resolved", "module_decisions": [
                    {"module_id": "common", "module_version": "3.0.0", "decision": "selected",
                     "basis": "deterministic", "confidence": "high", "rationale": "所有公司", "sources": [source]},
                    {"module_id": "semiconductors", "module_version": "3.0.0", "decision": "selected",
                     "basis": "manual", "confidence": "high", "rationale": "已复核业务",
                     "sources": [], "manual_override": {"actor": "analyst", "reason": "业务占比已复核",
                                                      "valid_until": "2026-10-01T00:00:00Z"}}]}
        decision = mc.seal_route_decision(body)
        mc.validate_route_decision(decision, release)
        forged_release = copy.deepcopy(release)
        forged_release["router_version"] = "9.0.0"
        with self.assertRaisesRegex(ValueError, "module release content hash mismatch"):
            mc.validate_route_decision(decision, forged_release)
        duplicate_body = {k: copy.deepcopy(v) for k, v in release.items() if k != "release_id"}
        duplicate_body["modules"].insert(0, copy.deepcopy(duplicate_body["modules"][0]))
        duplicate_release = mc.seal_release(duplicate_body)
        duplicate_route_body = {k: copy.deepcopy(v) for k, v in decision.items() if k != "decision_id"}
        duplicate_route_body["release_id"] = duplicate_release["release_id"]
        with self.assertRaisesRegex(ValueError, "sorted unique module IDs"):
            mc.validate_route_decision(mc.seal_route_decision(duplicate_route_body), duplicate_release)
        body["module_decisions"] = body["module_decisions"][:1]
        with self.assertRaisesRegex(ValueError, "every released module"):
            mc.validate_route_decision(mc.seal_route_decision(body), release)
        body["module_decisions"].append(decision["module_decisions"][1])
        body["module_decisions"][1]["manual_override"]["valid_until"] = "2026-09-20T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "expired"):
            mc.validate_route_decision(mc.seal_route_decision(body), release)

    def test_frozen_legacy_route_v1_fixture_remains_readable_and_rejects_v2_fields(self):
        release, _ = self.release()
        fixture = json.loads(
            (ROOT / "tests/fixtures/route_decision_legacy_v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(release["schema_version"], "1.0.0")
        self.assertEqual(release["release_id"], fixture["release_id"])

        legacy_route = fixture["valid_route"]
        self.assertEqual(legacy_route["schema_version"], "1.0.0")
        self.assertNotIn("classification_confidence", legacy_route)
        mc.validate_route_decision(legacy_route, release)

        tampered_route = copy.deepcopy(legacy_route)
        tampered_route["status"] = "partial"
        with self.assertRaisesRegex(ValueError, "route decision content hash mismatch"):
            mc.validate_route_decision(tampered_route, release)

        invalid_legacy_route = fixture["invalid_route_with_v2_only_field"]
        self.assertEqual(invalid_legacy_route["schema_version"], "1.0.0")
        self.assertIn("classification_confidence", invalid_legacy_route)
        with self.assertRaises(ValidationError):
            mc.validate_route_decision(invalid_legacy_route, release)


if __name__ == "__main__":
    unittest.main()
