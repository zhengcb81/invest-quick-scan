"""BASIC-BANK-EXPANSION-21: the core construct set is derived from released data.

Owner ruling (2026-10-24): "必须恰好是 24 个核心题是很奇怪的限制，不应该有，基本题库要
允许自身的升级和扩张。" No production code may carry a hard-coded core count or a
fixed ``IQS_01..IQS_24`` list; every consumer derives the set from the common
module of the release it is reading.

AC-01 (unchanged data): existing 24 core constructs, no extensions — every
assertion in this file still passes and published artifacts stay byte-identical.
AC-02 (append a diagnostic extension, minor): publication passes, composition
includes the question, the fixed comparison denominator stays at the derived
core size, ``method_id`` does not move.
AC-03 (remove an extension, minor + tombstone; core add/remove/replace still
requires major + successor): see ``ExpansionUpgradeTests``.
AC-05 (routing/scoring derive): ``minimum_questions`` and ``expected_core``
follow the bank size.
"""
import copy
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import module_contract as mc  # noqa: E402
import question_sets as qs  # noqa: E402
import scoring_rubrics as sr  # noqa: E402


def _load_common():
    catalog = json.loads((ROOT / "questions/catalog.json").read_text(encoding="utf-8"))
    entry = next(item for item in catalog["modules"] if item["id"] == "common")
    return json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))


def _extension_question(template):
    """One diagnostic extension question: scored never, core never."""
    question = copy.deepcopy(template)
    question.update(id="DUPONT_EXT_01", metric_id="score.dupont_ext_01",
                    construct_id=None, comparison_role="diagnostic",
                    aggregation="diagnostic", priority=2, framework="dupont")
    question.pop("critical", None)
    return question


class DerivedCoreSetTests(unittest.TestCase):
    def setUp(self):
        self.common = _load_common()

    def test_core_construct_ids_are_derived_from_common_data(self):
        """The core set is a projection of the module, not a frozen literal."""
        self.assertEqual(mc.core_construct_ids(self.common),
                         frozenset(q["id"] for q in self.common["questions"]))
        self.assertFalse(hasattr(mc, "CORE_IDS"),
                         "module_contract must not expose a frozen core ID literal")

    def test_common_accepts_a_diagnostic_extension_without_moving_the_core(self):
        """AC-02: an appended diagnostic extension is legal and stays out of core."""
        module = copy.deepcopy(self.common)
        module["questions"].append(_extension_question(self.common["questions"][0]))
        core = mc.core_construct_ids(module)
        self.assertEqual(core, frozenset(q["id"] for q in self.common["questions"]))
        mc.validate_module(module, core_ids=core)

    def test_common_extension_cannot_enter_core_or_replace(self):
        """An extension must not smuggle in a new core construct."""
        for field, value in (("comparison_role", "core"), ("aggregation", "scored")):
            with self.subTest(field=field):
                module = copy.deepcopy(self.common)
                question = _extension_question(self.common["questions"][0])
                question[field] = value
                module["questions"].append(question)
                core = mc.core_construct_ids(module)
                with self.assertRaisesRegex(ValueError, "core construct|extension"):
                    mc.validate_module(module, core_ids=core)

    def test_common_extension_cannot_replace_a_core_construct(self):
        module = copy.deepcopy(self.common)
        question = _extension_question(self.common["questions"][0])
        question["replaces"] = ["IQS_01"]
        module["questions"].append(question)
        with self.assertRaisesRegex(ValueError, "extension"):
            mc.validate_module(module, core_ids=mc.core_construct_ids(module))

    def test_common_extension_cannot_carry_a_construct_id(self):
        module = copy.deepcopy(self.common)
        question = _extension_question(self.common["questions"][0])
        question["construct_id"] = "IQS_01"
        module["questions"].append(question)
        with self.assertRaisesRegex(ValueError, "extension"):
            mc.validate_module(module, core_ids=mc.core_construct_ids(module))

    def test_diagnostic_questions_cannot_claim_a_critical_risk_gate(self):
        """Reject contradictory definitions before selection or aggregation."""
        _, modules = qs.load_library()
        common = copy.deepcopy(self.common)
        common["questions"].append(_extension_question(self.common["questions"][0]))
        diagnostic = copy.deepcopy(modules["dupont"])
        for module in (common, diagnostic):
            with self.subTest(kind=module["kind"]):
                module["questions"][-1]["critical"] = True
                with self.assertRaisesRegex(ValueError, "diagnostic.*critical"):
                    mc.validate_module(module)

    def test_common_requires_at_least_one_core_construct(self):
        module = copy.deepcopy(self.common)
        module["questions"] = [_extension_question(self.common["questions"][0])]
        with self.assertRaisesRegex(ValueError, "at least one core"):
            mc.validate_module(module, core_ids=frozenset())

    def test_type_replacement_targets_the_derived_core_set(self):
        """A type module may replace only constructs the release actually has."""
        catalog = json.loads((ROOT / "questions/catalog.json").read_text(encoding="utf-8"))
        entry = next(item for item in catalog["modules"] if item["id"] == "bank")
        bank = json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
        target = bank["questions"][0]["replaces"][0]
        core = mc.core_construct_ids(self.common)
        self.assertIn(target, core)
        mc.validate_module(bank, core_ids=core)
        with self.assertRaisesRegex(ValueError, "one frozen core construct"):
            mc.validate_module(bank, core_ids=core - {target})

    def test_type_replacements_preserve_critical_flags_from_the_common_module(self):
        _, modules = qs.load_library()
        common = modules["common"]
        critical_ids = frozenset(q["id"] for q in common["questions"]
                                 if q["comparison_role"] == "core" and q.get("critical"))
        bank = copy.deepcopy(modules["bank"])
        risk = next(q for q in bank["questions"] if set(q.get("replaces", [])) & critical_ids)
        for flag in (False, None):
            with self.subTest(flag=flag):
                changed = copy.deepcopy(modules)
                question = next(q for q in changed["bank"]["questions"] if q["id"] == risk["id"])
                if flag is None:
                    question.pop("critical", None)
                else:
                    question["critical"] = flag
                with self.assertRaisesRegex(ValueError, "critical core.*critical"):
                    mc.validate_registry(changed, {}, legacy_ids=frozenset(changed))
        mc.validate_module(bank, core_ids=mc.core_construct_ids(common), critical_core_ids=critical_ids)

    def test_type_critical_inheritance_follows_a_new_core_construct(self):
        _, modules = qs.load_library()
        grown = copy.deepcopy(modules)
        question = copy.deepcopy(grown["common"]["questions"][0])
        question.update(id="IQS_99", metric_id="score.iqs_99", construct_id="IQS_99", critical=True)
        grown["common"]["questions"].append(question)
        replacement = copy.deepcopy(grown["bank"]["questions"][0])
        replacement.update(id="BANK_99", metric_id="score.bank_99", construct_id="IQS_99",
                           replaces=["IQS_99"], critical=True)
        grown["bank"]["questions"].append(replacement)
        mc.validate_registry(grown, {}, legacy_ids=frozenset(grown))
        replacement["critical"] = False
        with self.assertRaisesRegex(ValueError, "critical core.*critical"):
            mc.validate_registry(grown, {}, legacy_ids=frozenset(grown))

    def test_validate_library_reports_the_derived_core_count(self):
        report = qs.validate_library()
        self.assertEqual(report["core_constructs"], 24)
        self.assertEqual(report["common_questions"], 24)


class RequiredBasicCoverageTests(unittest.TestCase):
    """Every new scan covers the shared core and both diagnostic frameworks."""

    @classmethod
    def setUpClass(cls):
        _, cls.modules = qs.load_library()
        cls.profile = qs.read_json(ROOT / "examples/profile.json")
        cls.diagnostics = {q["id"] for mid in ("dupont", "porter")
                           for q in cls.modules[mid]["questions"]}

    def chosen(self, company_type="operating", mode="full"):
        profile = {**self.profile, "company_type": company_type, "stage": "mature",
                   "cycle_sensitive": False, "overlays": [], "diagnostic_modules": [],
                   "industry_modules": ["semiconductors"] if company_type in
                   ("operating", "pre_revenue") else []}
        return qs.select_questions(profile, mode, self.modules)[0]

    def test_basic_export_combines_modules_without_moving_question_owners(self):
        questions = qs.basic_questions(self.modules)
        self.assertEqual({q["id"] for q in questions},
                         {q["id"] for q in self.modules["common"]["questions"]} | self.diagnostics)
        self.assertEqual(len(questions), len({q["id"] for q in questions}))
        self.assertEqual({q["module_id"] for q in questions}, {"common", "dupont", "porter"})

    def test_budget_preserves_every_basic_question_for_all_types_and_modes(self):
        for company_type, module in self.modules.items():
            if module["kind"] != "types":
                continue
            for mode in ("quick", "full"):
                with self.subTest(company_type=company_type, mode=mode):
                    chosen = self.chosen(company_type, mode)
                    required = [q for q in chosen if q["comparison_role"] == "core"
                                or q.get("critical") or q["module_id"] in ("dupont", "porter")]
                    kept, deferred = qs._apply_question_budget(chosen, len(required))
                    self.assertEqual({q["id"] for q in kept}, {q["id"] for q in required})
                    self.assertTrue(self.diagnostics <= {q["id"] for q in kept})
                    self.assertTrue(self.diagnostics.isdisjoint(q["question_id"] for q in deferred))

    def test_budget_below_basic_coverage_is_rejected(self):
        chosen = self.chosen()
        basic = [q for q in chosen if q["comparison_role"] == "core"
                 or q.get("critical") or q["module_id"] in ("dupont", "porter")]
        with self.assertRaisesRegex(ValueError, "budget below mandatory.*basic"):
            qs._apply_question_budget(chosen, len(basic) - 1)

    def test_explicit_legacy_budget_remains_readable(self):
        chosen = self.chosen()
        kept, deferred = qs._apply_question_budget(chosen, 40, protect_basic=False)
        self.assertTrue(deferred)
        self.assertFalse(self.diagnostics <= {q["id"] for q in kept})

    def test_financial_diagnostics_require_explicit_na_instead_of_omission(self):
        profile = {**self.profile, "company_type": "bank", "industry_modules": []}
        question = next(q for q in self.chosen("bank") if q["id"] == "DUPONT_03")
        prompt = qs.render_question(question, profile)
        self.assertIn("not_applicable", prompt)
        self.assertIn("专属替代指标", prompt)
        self.assertIn("不进入质量汇总", prompt)

    def test_company_composer_has_no_implicit_question_count_cap(self):
        import compose_company_bank as composer
        with tempfile.TemporaryDirectory(prefix='basic-cli-') as temporary:
            output = Path(temporary) / 'scan'
            captured = {}

            def compile_fixture(profile, mode, out_dir, **kwargs):
                captured.update(kwargs)
                qs.write_json(Path(out_dir) / 'manifest.json',
                              {'questions': [], 'modules': []})

            arguments = ['compose_company_bank.py', '--profile', str(ROOT / 'examples/profile.json'),
                         '--mode', 'full', '--out-dir', str(output), '--now-utc', '2026-10-25T12:00:00Z']
            with mock.patch.object(sys, 'argv', arguments), \
                    mock.patch.object(qs, 'compose', side_effect=compile_fixture), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(composer.main(), 0)
            self.assertIsNone(captured['max_questions'])

    def test_historical_default_selection_comes_from_frozen_module_versions(self):
        import question_selection as selection
        modules = copy.deepcopy(self.modules)
        for mid in ('dupont', 'porter'):
            modules[mid]['version'] = '3.0.0'
        profile = {**self.profile, 'diagnostic_modules': [], 'diagnostic_rationale': {}}
        release = {'schema_version': '1.0.0'}
        historical, historical_modules, _ = selection.published_selection(
            profile, 'full', modules, release, None, None,
            historical_profile_defaults=True)
        current, current_modules, _ = selection.published_selection(
            profile, 'full', modules, release, None, None)
        self.assertTrue(self.diagnostics.isdisjoint(q['id'] for q in historical))
        self.assertTrue(self.diagnostics <= {q['id'] for q in current})
        self.assertTrue({'dupont', 'porter'}.isdisjoint(historical_modules))
        self.assertTrue({'dupont', 'porter'} <= set(current_modules))

    def test_quick_keeps_new_low_priority_basic_extensions(self):
        modules = copy.deepcopy(self.modules)
        extension = _extension_question(modules['common']['questions'][0])
        modules['common']['questions'].append(extension)
        chosen, _, _ = qs.select_questions(self.profile, 'quick', modules)
        self.assertIn(extension['id'], {q['id'] for q in chosen})
        minimum = sum(q['comparison_role'] == 'core' or q.get('critical')
                      or q['module_id'] in ('common', 'dupont', 'porter') for q in chosen)
        kept, deferred = qs._apply_question_budget(chosen, minimum)
        self.assertIn(extension['id'], {q['id'] for q in kept})
        self.assertNotIn(extension['id'], {q['question_id'] for q in deferred})


class ExpansionUpgradeTests(unittest.TestCase):
    """AC-03: extension add/remove is minor; core change still needs major."""

    def setUp(self):
        self.common = _load_common()

    def _extended(self, version):
        module = copy.deepcopy(self.common)
        module["version"] = version
        module["questions"].append(_extension_question(self.common["questions"][0]))
        return module

    def test_appending_an_extension_is_a_minor_upgrade(self):
        mc.validate_upgrade(self.common, self._extended("3.1.0"))

    def test_appending_an_extension_with_a_patch_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "minor or major"):
            mc.validate_upgrade(self.common, self._extended("3.0.1"))

    def test_removing_an_extension_is_minor_with_a_tombstone(self):
        extended = self._extended("3.1.0")
        shrunk = copy.deepcopy(extended)
        shrunk["version"] = "3.2.0"
        shrunk["questions"] = [q for q in shrunk["questions"] if q["id"] != "DUPONT_EXT_01"]
        shrunk["retired_question_ids"] = ["DUPONT_EXT_01"]
        mc.validate_upgrade(extended, shrunk)

    def test_removing_an_extension_without_a_tombstone_is_rejected(self):
        extended = self._extended("3.1.0")
        shrunk = copy.deepcopy(extended)
        shrunk["version"] = "3.2.0"
        shrunk["questions"] = [q for q in shrunk["questions"] if q["id"] != "DUPONT_EXT_01"]
        with self.assertRaisesRegex(ValueError, "tombstones must accumulate"):
            mc.validate_upgrade(extended, shrunk)

    def test_removing_an_extension_with_only_a_patch_is_rejected(self):
        extended = self._extended("3.1.0")
        shrunk = copy.deepcopy(self.common)
        shrunk.update(version="3.1.1", retired_question_ids=["DUPONT_EXT_01"])
        with self.assertRaisesRegex(ValueError, "extension removal.*minor"):
            mc.validate_upgrade(extended, shrunk)

    def test_major_core_expansion_can_also_retire_a_diagnostic_extension(self):
        extended = self._extended("3.1.0")
        grown = copy.deepcopy(self.common)
        grown.update(version="4.0.0", retired_question_ids=["DUPONT_EXT_01"])
        question = copy.deepcopy(self.common["questions"][0])
        question.update(id="IQS_99", metric_id="score.iqs_99", construct_id="IQS_99")
        grown["questions"].append(question)
        mc.validate_upgrade(extended, grown)

    def test_major_core_successor_does_not_need_a_successor_for_a_retired_diagnostic(self):
        extended = self._extended("3.1.0")
        changed = copy.deepcopy(self.common)
        retired = changed["questions"].pop()
        successor = copy.deepcopy(retired)
        successor.update(id="IQS_90", metric_id="score.iqs_90", construct_id="IQS_90",
                         supersedes=retired["id"])
        changed["questions"].append(successor)
        changed.update(version="4.0.0", retired_question_ids=["DUPONT_EXT_01", retired["id"]])
        mc.validate_upgrade(extended, changed)

    def test_removing_an_extension_with_a_major_version_is_still_rejected(self):
        """Removing a diagnostic extension never needs a major release."""
        extended = self._extended("3.1.0")
        shrunk = copy.deepcopy(extended)
        shrunk["version"] = "4.0.0"
        shrunk["questions"] = [q for q in shrunk["questions"] if q["id"] != "DUPONT_EXT_01"]
        shrunk["retired_question_ids"] = ["DUPONT_EXT_01"]
        with self.assertRaisesRegex(ValueError, "extension removal"):
            mc.validate_upgrade(extended, shrunk)

    def test_adding_a_core_construct_still_requires_a_major_release(self):
        grown = copy.deepcopy(self.common)
        grown["version"] = "3.1.0"
        added = copy.deepcopy(self.common["questions"][0])
        added.update(id="IQS_99", metric_id="score.iqs_99", construct_id="IQS_99")
        grown["questions"].append(added)
        with self.assertRaisesRegex(ValueError, "core construct change requires a major"):
            mc.validate_upgrade(self.common, grown)

    def test_removing_a_core_construct_still_requires_a_major_with_successor(self):
        shrunk = copy.deepcopy(self.common)
        shrunk["version"] = "4.0.0"
        removed = shrunk["questions"].pop()
        shrunk["retired_question_ids"] = [removed["id"]]
        successor = copy.deepcopy(removed)
        successor.update(id="IQS_90", metric_id="score.iqs_90", construct_id="IQS_90",
                         supersedes=removed["id"])
        shrunk["questions"].append(successor)
        mc.validate_upgrade(self.common, shrunk)

        shrunk["version"] = "3.1.0"
        with self.assertRaisesRegex(ValueError, "core construct change requires a major"):
            mc.validate_upgrade(self.common, shrunk)


class FixedComparisonTests(unittest.TestCase):
    """AC-02: the fixed comparison denominator is the derived core set."""

    def setUp(self):
        self.core = [{"id": f"IQS_{index:02}", "construct_id": f"IQS_{index:02}",
                      "comparison_role": "core", "dimension": "business",
                      "aggregation": "scored", "status": "scored", "score": 5,
                      "critical": False} for index in range(1, 25)]

    def test_summarize_accepts_the_released_core_set(self):
        core_ids = frozenset(row["construct_id"] for row in self.core)
        self.assertEqual(qs.summarize(self.core, "core-constructs-v1",
                                      core_ids=core_ids)["dimensions"],
                         qs.summarize(self.core, "core-constructs-v1")["dimensions"])

    def test_summarize_rejects_a_row_set_that_differs_from_the_release(self):
        core_ids = frozenset(row["construct_id"] for row in self.core)
        with self.assertRaisesRegex(ValueError, "one row per core construct"):
            qs.summarize(self.core[:-1], "core-constructs-v1", core_ids=core_ids)
        extra = copy.deepcopy(self.core[0])
        extra.update(id="IQS_90", construct_id="IQS_90")
        with self.assertRaisesRegex(ValueError, "one row per core construct"):
            qs.summarize(self.core + [extra], "core-constructs-v1", core_ids=core_ids)

    def test_summarize_derives_the_denominator_when_no_release_is_supplied(self):
        """Without a release, the core rows must be unique and non-empty."""
        self.assertEqual(qs.summarize(self.core, "core-constructs-v1")["dimensions"],
                         qs.summarize(self.core, "core-constructs-v1",
                                      core_ids=frozenset(r["construct_id"] for r in self.core))["dimensions"])
        duplicate = copy.deepcopy(self.core[0])
        duplicate["id"] = "IQS_01_DUP"
        with self.assertRaisesRegex(ValueError, "one row per core construct"):
            qs.summarize(self.core + [duplicate], "core-constructs-v1")
        with self.assertRaisesRegex(ValueError, "one row per core construct"):
            qs.summarize([], "core-constructs-v1")

    def test_extension_rows_never_change_the_fixed_comparison(self):
        extended = self.core + [{"id": "DUPONT_EXT_01", "construct_id": None,
                                 "comparison_role": "diagnostic", "dimension": "business",
                                 "aggregation": "diagnostic", "status": "scored",
                                 "score": 10, "critical": False}]
        self.assertEqual(qs.summarize(self.core, "core-constructs-v1"),
                         qs.summarize(extended, "core-constructs-v1"))

    def test_summarize_rejects_diagnostic_critical_metadata_in_both_policies(self):
        for policy in ("legacy-all-questions", "core-constructs-v1"):
            for diagnostic_field in ("aggregation", "comparison_role"):
                with self.subTest(policy=policy, field=diagnostic_field):
                    row = copy.deepcopy(self.core[0])
                    row.update(id="DUPONT_EXT_01", construct_id=None,
                               comparison_role="context", critical=True, score=1)
                    row[diagnostic_field] = "diagnostic"
                    with self.assertRaisesRegex(ValueError, "diagnostic.*critical"):
                        qs.summarize(self.core + [row], policy)

    def test_real_critical_core_and_scored_context_still_block_quality(self):
        rows = [dict(q, score=8) for q in _load_common()["questions"]]
        rows = [dict(q, status="scored") for q in rows]
        self.assertEqual(qs.summarize(rows, "core-constructs-v1")["quality_score"], 8)
        for status, score in (("scored", 1), ("insufficient_evidence", None)):
            with self.subTest(kind="core", status=status):
                changed = copy.deepcopy(rows)
                risk = next(q for q in changed if q.get("critical"))
                risk.update(status=status, score=score)
                result = qs.summarize(changed, "core-constructs-v1")
                self.assertIsNone(result["quality_score"])
                self.assertIn(risk["id"], {q["id"] for q in result["critical_issues"]})
        context = dict(rows[0], id="CRITICAL_CONTEXT", construct_id=None,
                       comparison_role="context", critical=True, score=1)
        result = qs.summarize(rows + [context], "core-constructs-v1")
        self.assertIsNone(result["quality_score"])
        self.assertIn("CRITICAL_CONTEXT", {q["id"] for q in result["critical_issues"]})


class ExpandedLibraryIntegrationTests(unittest.TestCase):
    """Exercise authoring, publication, composition and historical reads in isolation."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iqs-bank21-")
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
        patcher = mock.patch.object(qs, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.profile = {**qs.read_json(ROOT / "examples/profile.json"), "entity_id": "BANK21_FIXTURE"}

    def edit_common(self, *, core=False):
        catalog = qs.read_json(self.root / "questions/catalog.json")
        entry = next(item for item in catalog["modules"] if item["id"] == "common")
        module = qs.read_json(self.root / entry["path"])
        question = _extension_question(module["questions"][0])
        if core:
            question.update(id="IQS_99", metric_id="score.iqs_99", construct_id="IQS_99",
                            comparison_role="core", aggregation="scored", priority=1, critical=True)
        module["questions"].append(question)
        module.update(version="4.0.0" if core else "3.1.0", dependencies=[], conflicts=[],
                      introduced_in="3.1.0", activation={"mode": "automatic",
                          "required_evidence": ["isolated fixture"], "exclude_when": [],
                          "minimum_confidence": "medium"})
        entry["question_count"] = len(module["questions"])
        catalog["version"] = "3.3.0"
        qs.write_json(self.root / entry["path"], module)
        qs.write_json(self.root / "questions/catalog.json", catalog)
        contexts = qs.read_json(self.root / "questions/scoring-contexts.json")
        contexts["common"] = {"common": "Isolated authoring fixture; no production data."}
        qs.write_json(self.root / "questions/scoring-contexts.json", contexts)

    def compose_manifest(self, name, package_id):
        output = self.root / name
        qs.compose(self.profile, "full", output, answer_format="screening-1", package_id=package_id)
        return qs.read_json(output / "manifest.json")

    def test_diagnostic_extension_flows_through_library_publish_compose_and_history(self):
        baseline = qs.publish_library()
        before = self.compose_manifest("before", baseline["package_id"])
        self.edit_common()
        stats = qs.validate_library()
        self.assertEqual(stats["core_constructs"], 24)
        self.assertEqual(stats["common_questions"], 25)
        extended = qs.publish_library()
        after = self.compose_manifest("after", extended["package_id"])
        self.assertIn("DUPONT_EXT_01", {q["id"] for q in after["questions"]})
        self.assertEqual(before["method_id"], after["method_id"])
        self.assertEqual(self.compose_manifest("historical", baseline["package_id"]), before)
        qs.validate_manifest_metric_contract(before)
        qs.validate_manifest_metric_contract(after)
        rows_before = [dict(q, status="scored", score=8) for q in before["questions"]]
        rows_after = [dict(q, status="scored", score=1 if q["id"] == "DUPONT_EXT_01" else 8)
                      for q in after["questions"]]
        before_summary = qs.summarize(rows_before, "core-constructs-v1")
        after_summary = qs.summarize(rows_after, "core-constructs-v1")
        for field in ("dimensions", "quality_score", "quality_coverage", "critical_issues",
                      "growth_score", "valuation_score"):
            self.assertEqual(before_summary[field], after_summary[field])
        self.assertIn("DUPONT_EXT_01", after_summary["weak_points"])

    def test_library_accepts_major_new_critical_core_from_data(self):
        qs.publish_library()
        self.edit_common(core=True)
        self.assertEqual(qs.validate_library()["core_constructs"], 25)
        grown = qs.publish_library()
        manifest = self.compose_manifest("grown", grown["package_id"])
        rows = [dict(q, status="scored", score=1 if q["id"] == "IQS_99" else 8)
                for q in manifest["questions"]]
        summary = qs.summarize(rows, "core-constructs-v1", core_ids=qs._manifest_core_ids(manifest))
        self.assertIsNone(summary["quality_score"])
        self.assertIn("IQS_99", {q["id"] for q in summary["critical_issues"]})


class RubricDerivationTests(unittest.TestCase):
    """AC-05: the rubric denominator follows the released core set."""

    def _rubric(self, modules, *, version="1.0.0"):
        common = modules["common"]["questions"]
        return {"schema_version": "1.0.0", "version": version,
                "method_id": "core-constructs-v1-operating", "owner": "iqs",
                "cohort": "operating", "valid_from_utc": "2026-09-30T00:00:00Z",
                "valid_until_utc": None, "calibration_sample_refs": [],
                "minimum_check_level": "execution_verified",
                "dimension_min_coverage": 0.7, "quality_min_coverage": 0.8,
                "quality_weights": dict(qs.QUALITY_WEIGHTS), "supersedes": None,
                "core_basket": [{"construct_id": q["construct_id"], "question_id": q["id"],
                                 "question_definition_sha256": mc.digest(q),
                                 "dimension": q["dimension"], "scope": q["scope"],
                                 "rubric_version": q["rubric_version"]} for q in common],
                "critical_extensions": []}

    def test_basket_dimensions_are_derived_when_no_core_map_is_supplied(self):
        _, modules = qs.load_library()
        rubric = sr.seal_rubric(self._rubric(modules))
        self.assertEqual(len(rubric["core_basket"]), 24)

    def test_rubric_accepts_a_core_map_from_the_released_bank(self):
        _, modules = qs.load_library()
        core_map = {q["construct_id"]: q["dimension"] for q in modules["common"]["questions"]}
        rubric = sr.seal_rubric(self._rubric(modules), core_constructs=core_map)
        self.assertEqual(len(rubric["core_basket"]), len(core_map))

    def test_rubric_rejects_a_basket_that_differs_from_the_released_core(self):
        _, modules = qs.load_library()
        core_map = {q["construct_id"]: q["dimension"] for q in modules["common"]["questions"]}
        body = self._rubric(modules)
        body["core_basket"] = body["core_basket"][:-1]
        with self.assertRaises(ValueError):
            sr.seal_rubric(body, core_constructs=core_map)

    def test_rubric_rejects_a_dimension_that_contradicts_the_released_map(self):
        _, modules = qs.load_library()
        core_map = {q["construct_id"]: q["dimension"] for q in modules["common"]["questions"]}
        body = self._rubric(modules)
        body["core_basket"][0]["dimension"] = "valuation"
        with self.assertRaisesRegex(ValueError, "dimension"):
            sr.seal_rubric(body, core_constructs=core_map)


if __name__ == "__main__":
    unittest.main()
