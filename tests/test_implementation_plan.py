"""Catch broken handoffs, missing oracles and falsely labelled planning evidence."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("implementation_plan", ROOT / "scripts/implementation_plan.py")
ip = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ip)


class ImplementationPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_plan, cls.original_cases = ip.load_package(ip.DEFAULT_PLAN_DIR)

    def setUp(self):
        self.plan = copy.deepcopy(self.original_plan)
        self.cases = copy.deepcopy(self.original_cases)

    def task(self, tid):
        return next(t for t in self.plan["tasks"] if t["id"] == tid)

    def rejected(self, fragment):
        errors = ip.validate_package(self.plan, self.cases)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_current_package_is_valid_but_not_product_evidence(self):
        self.assertEqual(ip.validate_package(self.plan, self.cases), [])
        self.assertTrue(all(c["status"] == "specified_not_executed" for c in self.cases["cases"]))
        self.assertNotIn("status", self.task("P00"))

    def test_duplicate_task_is_rejected(self):
        self.plan["tasks"].append(copy.deepcopy(self.task("P00")))
        self.rejected("duplicate task P00")

    def test_duplicate_case_is_rejected(self):
        self.cases["cases"].append(copy.deepcopy(self.cases["cases"][0]))
        self.rejected("duplicate case")

    def test_unknown_dependency_is_rejected(self):
        self.task("C01")["depends_on"].append("NO_SUCH_TASK")
        self.rejected("unknown dependency")

    def test_dependency_cycle_is_rejected_without_recursion_loop(self):
        self.task("P00")["depends_on"] = ["C01"]
        self.rejected("dependency cycle")

    def test_self_cycle_is_rejected(self):
        self.task("P00")["depends_on"] = ["P00"]
        self.rejected("dependency cycle")

    def test_future_stage_dependency_is_rejected(self):
        self.task("C01")["depends_on"].append("W01")
        self.rejected("later stage")

    def test_missing_review_gate_is_rejected(self):
        self.plan["tasks"] = [t for t in self.plan["tasks"] if t["id"] != "G2"]
        self.rejected("missing review gate G2")

    def test_facts_cannot_start_without_score_reliability_gate(self):
        self.task("F01")["depends_on"] = ["C06"]
        self.rejected("F01: full facts work must depend on G3")

    def test_unknown_or_multiple_owner_is_rejected(self):
        for owner in ("company-wiki-writer", ["iqs", "stockwiki"]):
            with self.subTest(owner=owner):
                self.task("W01")["owner"] = owner
                self.rejected("unknown or multiple owners")

    def test_missing_scope_or_steps_is_rejected(self):
        for key in ("allowed_changes", "steps", "deliverables", "case_ids"):
            with self.subTest(key=key):
                self.plan = copy.deepcopy(self.original_plan)
                self.task("W01")[key] = []
                self.rejected(key)

    def test_unknown_case_reference_is_rejected(self):
        self.task("W01")["case_ids"].append("MISSING-99")
        self.rejected("unknown case MISSING-99")

    def test_orphan_case_is_rejected(self):
        case = copy.deepcopy(self.cases["cases"][0])
        case["id"] = "UNUSED-01"
        self.cases["cases"].append(case)
        self.rejected("orphan acceptance case UNUSED-01")

    def test_explicit_oracle_is_required(self):
        self.cases["cases"][0]["then"] = []
        self.rejected("missing explicit expected result")

    def test_case_needs_input_and_action(self):
        self.cases["cases"][0]["given"] = ""
        self.cases["cases"][0]["when"] = ""
        self.rejected("input/precondition")
        self.rejected("missing action")

    def test_happy_path_only_task_is_rejected(self):
        self.task("W01")["case_ids"] = ["DB-01"]
        self.rejected("W01: needs a negative or fault case")

    def test_live_task_cannot_be_satisfied_by_mock_cases_only(self):
        self.task("L01")["case_ids"] = ["SC-01", "LLM-02"]
        self.rejected("L01: live task needs a live case")

    def test_spec_cannot_claim_a_passed_test(self):
        self.cases["cases"][0]["status"] = "passed"
        self.rejected("cannot contain claimed test results")

    def test_task_spec_cannot_duplicate_completion_state(self):
        self.task("W01")["status"] = "verified"
        self.rejected("completion status belongs in evidence receipts")

    def test_versions_must_align(self):
        self.cases["version"] = "different"
        self.rejected("same nonempty version")

    def test_release_cannot_end_at_scoring_only_gate(self):
        self.plan['release_requirements']['final_gate'] = 'G5'
        self.rejected('complete release must end at G6')

    def test_release_cannot_omit_facts_gate(self):
        self.plan['release_requirements']['required_gates'].remove('G4')
        self.rejected('including facts/consumers G4')

    def test_final_gate_must_cover_all_task_branches(self):
        task = copy.deepcopy(self.task('P00'))
        task['id'] = 'Z01'
        task['depends_on'] = ['P00']
        self.plan['tasks'].append(task)
        self.rejected('G6 leaves unfinished task branches: Z01')

    def test_launch_contract_is_frozen_before_g0(self):
        self.task('G0')['depends_on'].remove('C07')
        self.rejected('G0 must freeze launch contract C07')

    def test_live_launch_cannot_point_to_offline_suite(self):
        self.plan['release_requirements']['live_e2e_task'] = 'X09'
        self.rejected('live_e2e_task must bind the actual M6 live path')

    def test_complete_release_cannot_drop_a_consumer(self):
        self.plan['release_requirements']['required_components'].remove('industry')
        self.rejected('every required component and consumer')

    def test_complete_release_cannot_disable_all_tasks_requirement(self):
        self.plan['release_requirements']['complete_requires_all_tasks'] = False
        self.rejected('complete release must include all tasks')

    def test_launch_configuration_owner_cannot_drift(self):
        self.plan['release_requirements']['runtime_config_owner'] = 'stockwiki'
        self.rejected('ownership must stay StockWiki/StockQA')

    def test_cli_filters_cross_project_launch_tasks(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ip.main(['list', '--stage', 'M6', '--owner', 'stockqa'])
        self.assertEqual(code, 0)
        ids = {line.split(' | ')[0] for line in out.getvalue().splitlines()}
        self.assertEqual(ids, {'X01', 'X03'})

    def test_launch_packet_contains_new_invariant_definitions(self):
        packet = ip.task_packet(self.plan, self.cases, 'X05', ip.DEFAULT_PLAN_DIR)
        self.assertEqual(len(packet['invariant_details']), len(self.task('X05')['invariants']))
        self.assertTrue(any('| I23 |' in line for line in packet['invariant_details']))

    def test_case_family_allows_e2e_but_not_malformed_ids(self):
        self.assertTrue(any(c['id'] == 'E2E-01' for c in self.cases['cases']))
        self.assertEqual(ip.validate_package(self.plan, self.cases), [])
        for cid in ('2E-01', 'E2E-1', 'E2E_01', 'E2E-01;command', '../E2E-01'):
            with self.subTest(cid=cid):
                self.cases = copy.deepcopy(self.original_cases)
                self.cases['cases'][0]['id'] = cid
                self.rejected('case has invalid ID')

    def test_unknown_invariant_is_rejected(self):
        self.task("W01")["invariants"].append("I99")
        self.rejected("unknown invariant I99")

    def test_malformed_top_level_has_actionable_error(self):
        self.plan["tasks"] = ["not an object"]
        self.rejected("tasks must be")

    def test_malformed_kind_has_validation_error_instead_of_type_error(self):
        self.task("W01")["kind"] = []
        self.cases["cases"][0]["kind"] = {}
        self.rejected("invalid task kind")
        self.rejected("invalid kind or level")

    def test_recovery_is_available_before_two_hundred_company_pilot(self):
        task_map = {t["id"]: t for t in self.plan["tasks"]}
        self.assertIn("W12", ip.dependency_ids(task_map, "L03"))
        self.assertNotIn("G3", ip.dependency_ids(task_map, "W12"))

    def test_show_is_bounded_and_contains_real_oracles(self):
        packet = ip.task_packet(self.plan, self.cases, "Q01", ip.DEFAULT_PLAN_DIR)
        self.assertEqual(packet["repository"]["name"], "StockQAbyLLM")
        self.assertEqual(packet["task"]["id"], "Q01")
        ids = {c["id"] for c in packet["acceptance_cases"]}
        self.assertEqual(ids, set(self.task("Q01")["case_ids"]))
        self.assertNotIn("LIVE-06", ids)
        self.assertIn("G0", packet["transitive_dependencies"])
        self.assertEqual(len(packet["invariant_details"]), len(self.task("Q01")["invariants"]))

    def test_show_unknown_task_never_guesses(self):
        with self.assertRaisesRegex(ValueError, "unknown task"):
            ip.task_packet(self.plan, self.cases, "UNKNOWN", ip.DEFAULT_PLAN_DIR)

    def test_packet_refuses_missing_invariant_definition(self):
        with tempfile.TemporaryDirectory() as temp:
            Path(temp, "decision-register.md").write_text("No definitions", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing invariant definitions"):
                ip.task_packet(self.plan, self.cases, "Q01", Path(temp))

    def test_cli_validation_does_not_claim_product_tests(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ip.main(["validate"])
        self.assertEqual(code, 0)
        result = json.loads(out.getvalue())
        self.assertTrue(result["planning_valid"])
        self.assertFalse(result["product_tests_executed"])

    def test_cli_stage_filter_only_returns_requested_stage(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ip.main(["list", "--stage", "M0"])
        self.assertEqual(code, 0)
        lines = out.getvalue().splitlines()
        self.assertTrue(lines)
        self.assertTrue(all(" | M0 | " in line for line in lines))
        self.assertFalse(any(line.startswith("Q01 ") for line in lines))

    def test_cli_missing_or_corrupt_plan_is_error_not_empty_success(self):
        with tempfile.TemporaryDirectory() as temp:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(ip.main(["--plan-dir", temp, "validate"]), 2)
            Path(temp, "tasks.json").write_text("{bad json", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(ip.main(["--plan-dir", temp, "validate"]), 2)


if __name__ == "__main__":
    unittest.main()
