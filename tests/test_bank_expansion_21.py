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
import json
from pathlib import Path
import sys
import unittest

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

    def test_validate_library_reports_the_derived_core_count(self):
        report = qs.validate_library()
        self.assertEqual(report["core_constructs"], 24)
        self.assertEqual(report["common_questions"], 24)


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
