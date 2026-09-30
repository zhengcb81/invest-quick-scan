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
        self.assertTrue(all(c.get("owner_task") for c in self.cases["cases"]))
        self.assertNotIn("status", self.task("P00"))
        self.assertNotIn("P01", {task["id"] for task in self.plan["tasks"]})

    def test_retired_task_receipt_workflow_is_absent_from_active_plan(self):
        task_ids = {task["id"] for task in self.plan["tasks"]}
        self.assertNotIn("P01", task_ids)
        self.assertNotIn("P01", self.plan["release_requirements"]["required_tasks"])
        self.assertNotIn("historical_context_edges", self.plan)
        self.assertTrue(all("P01" not in task.get("depends_on", []) for task in self.plan["tasks"]))
        self.assertTrue(all("historical_context_dependencies" not in task for task in self.plan["tasks"]))
        self.assertTrue(all(case["owner_task"] != "P01" for case in self.cases["cases"]))
        self.assertTrue(all(not case["id"].startswith("RCPT-") for case in self.cases["cases"]))

    def test_p00_historical_receipt_artifacts_are_preserved_but_not_new_write_targets(self):
        allowed = "\n".join(self.task("P00")["allowed_changes"])
        self.assertNotIn("receipt-P00.json", allowed)
        self.assertNotIn("validation-P00-*.json", allowed)
        self.assertNotIn("reviews/P00/", allowed)
        manifest = json.loads((ROOT / "docs/implementation/archive/task-receipts-v2-legacy/preservation-manifest.json").read_text(encoding="utf-8"))
        preserved = {entry["path"] for entry in manifest["entries"] if entry["kind"] == "preserved_historical_evidence"}
        self.assertIn("docs/implementation/contracts/receipt-P00.json", preserved)
        self.assertIn("docs/implementation/contracts/receipt-P01.json", preserved)

    def test_each_case_has_one_completion_owner_and_only_downstream_regression_refs(self):
        task_map = {task["id"]: task for task in self.plan["tasks"]}
        cases = {case["id"]: case for case in self.cases["cases"]}
        for cid, case in cases.items():
            owner = case["owner_task"]
            self.assertIn(cid, task_map[owner]["case_ids"])
            for task in self.plan["tasks"]:
                if cid in task["case_ids"] and task["id"] != owner:
                    self.assertIn(owner, ip.dependency_ids(task_map, task["id"]))

    def test_missing_unknown_and_forward_case_owners_are_rejected(self):
        case = next(item for item in self.cases["cases"] if item["id"] == "LLM-18")
        del case["owner_task"]
        self.rejected("LLM-18: missing owner_task")
        self.cases = copy.deepcopy(self.original_cases)
        case = next(item for item in self.cases["cases"] if item["id"] == "LLM-18")
        case["owner_task"] = "NO_SUCH_TASK"
        self.rejected("LLM-18: unknown owner_task NO_SUCH_TASK")
        self.cases = copy.deepcopy(self.original_cases)
        self.task("C02")["case_ids"].append("SC-16")
        self.rejected("C02: case SC-16 is owned by C03, which is outside its dependency closure")

    def test_case_owner_prerequisites_must_be_closed_before_owner_completion(self):
        case = next(item for item in self.cases["cases"] if item["id"] == "EVO-82")
        case["requires_tasks"].append("X11")
        self.rejected("EVO-82: owner X09 is missing prerequisite task(s): X11")

    def test_every_implementation_and_review_card_must_own_a_local_case(self):
        case = next(item for item in self.cases["cases"] if item["id"] == "UNI-09")
        case["owner_task"] = "W03"
        case["requires_tasks"] = []
        self.task("W03")["case_ids"].append("UNI-09")
        self.rejected("O01: must own at least one acceptance case")

    def test_modular_question_work_is_in_final_delivery_chain(self):
        chain = {"S04", "S05", "S06", "Q13", "W15", "F06", "U04"}
        self.assertTrue(chain <= set(ip.dependency_ids(
            {task["id"]: task for task in self.plan["tasks"]}, "G6")))
        self.assertTrue(chain <= set(self.plan["release_requirements"]["required_tasks"]))
        self.assertIn("S04", self.task("S05")["depends_on"])
        self.assertIn("S05", self.task("S06")["depends_on"])
        self.assertIn("S06", self.task("Q13")["depends_on"])
        self.assertIn("Q13", self.task("W15")["depends_on"])
        self.assertIn("F06", self.task("F02")["depends_on"])
        self.assertIn("U04", self.task("X09")["depends_on"])
        self.assertIn("MOD-10", self.task("X10")["case_ids"])

    def test_published_observation_ingest_cannot_downgrade_to_legacy(self):
        self.assertIn("S05", self.task("W05")["depends_on"])
        steps = "\n".join(self.task("W05")["steps"])
        self.assertIn("published-ingest", steps)
        self.assertIn("legacy观察只读", steps)
        self.assertIn("持久化的预期observation_id", steps)
        db03 = next(case for case in self.cases["cases"] if case["id"] == "DB-03")
        self.assertIn("同一StockQA执行键改ID重放", db03["given"])
        self.assertIn("重算语义/方法", "\n".join(db03["then"]))

    def test_route_work_includes_policy_archive_and_mandatory_risk_budget(self):
        task = self.task("S06")
        self.assertIn("scripts/routing.py", "\n".join(task["allowed_changes"]))
        self.assertIn("scripts/module_registry.py", "\n".join(task["allowed_changes"]))
        self.assertIn("route-decision.schema.json", "\n".join(task["allowed_changes"]))
        steps = "\n".join(task["steps"])
        self.assertIn("mandatory", steps)
        self.assertIn("历史manifest仅按原快照验证", steps)
        mod05 = next(case for case in self.cases["cases"] if case["id"] == "MOD-05")
        self.assertIn("max_questions=24", "\n".join(mod05["then"]))

    def test_s06_confidence_gate_has_exact_local_scope_and_atomic_cases(self):
        task = self.task("S06")
        self.assertEqual(set(task["allowed_changes"]), {
            "scripts/routing.py", "scripts/question_sets.py", "scripts/module_contract.py", "scripts/module_registry.py",
            "questions/routing-policy.v2.json", "schemas/quick_scan/route-decision.schema.json",
            "references/routing.md", "tests/test_routing.py", "tests/test_question_sets.py", "tests/test_module_registry.py",
            "tests/test_implementation_plan.py", "scripts/stockqa_adapter.py", "tests/test_stockqa_adapter.py",
            "docs/implementation/reviews/S06/run-first-segment-offline.py",
        })
        self.assertIn("MOD-19", task["case_ids"])
        case = next(case for case in self.cases["cases"] if case["id"] == "MOD-19")
        self.assertEqual(case["owner_task"], "S06")
        self.assertEqual(len(case["assertions"]), 9)
        self.assertIn("separately supplied valid verified_fact", " ".join(
            assertion["expected"] for assertion in case["assertions"]))
        a01 = next(assertion for assertion in case["assertions"] if assertion["id"] == "MOD-19.A01")
        self.assertIn("SHA-256", a01["expected"])
        self.assertIn("one complete raw answer", a01["expected"])
        a09 = next(assertion for assertion in case["assertions"] if assertion["id"] == "MOD-19.A09")
        self.assertIn("2.3.0 or later", a09["expected"])
        self.assertIn("Schema 1.3/request-protocol-3", a09["expected"])
        self.assertIn("schema also rejects", a09["expected"])
        a06 = next(assertion for assertion in case["assertions"] if assertion["id"] == "MOD-19.A06")
        self.assertIn("independently stored expected ID", a06["expected"])
        self.assertIn("snapshot hash alone is not provenance authentication", a06["expected"])
        self.assertIn("pairing answer A with answer B's separate receipt", a06["expected"])
        self.assertIn("调用方独立保存的decision_id", " ".join(task["steps"]))
        mod07 = next(case for case in self.cases["cases"] if case["id"] == "MOD-07")
        a02 = next(assertion for assertion in mod07["assertions"] if assertion["id"] == "MOD-07.A02")
        self.assertIn("trusted stored route row", a02["expected"])
        self.assertIn("before model calls or question output", a02["expected"])
        mod13 = next(case for case in self.cases["cases"] if case["id"] == "MOD-13")
        self.assertIn("历史未记录", " ".join(mod13["then"]))
        a01 = next(assertion for assertion in mod13["assertions"] if assertion["id"] == "MOD-13.A01")
        self.assertIn("fabricates no score/threshold/model/time", a01["expected"])
        w15_steps = "\n".join(self.task("W15")["steps"])
        u04_steps = "\n".join(self.task("U04")["steps"])
        self.assertIn("llm_candidates_eligible", w15_steps)
        self.assertIn("expected decision_id", w15_steps)
        self.assertIn("不是公司质量分", u04_steps)
        self.assertIn("verified_facts", u04_steps)

    def test_s07_prompt_dependency_boundary_has_unit_integration_and_e2e_cases(self):
        task = self.task("S07")
        self.assertEqual(task["depends_on"], ["S03", "S05"])
        self.assertIn("scripts/question_prompts.py", task["allowed_changes"])
        self.assertIn("scripts/implementation_plan.py", task["allowed_changes"])
        owned = {case["id"]: case for case in self.cases["cases"]
                 if case.get("owner_task") == "S07"}
        self.assertEqual(set(task["case_ids"]), {"MOD-20", "MOD-21", "MOD-22"})
        self.assertEqual(set(owned), set(task["case_ids"]))
        self.assertEqual({case["level"] for case in owned.values()}, {"unit", "integration", "e2e"})
        self.assertEqual(owned["MOD-20"]["kind"], "negative")
        self.assertIn("e2e", ip.LEVELS)
        self.assertIn("S07", self.task("G6")["depends_on"])

    def test_s08_question_library_boundary_has_unit_integration_and_e2e_cases(self):
        task = self.task("S08")
        self.assertEqual(task["depends_on"], ["S07"])
        self.assertIn("scripts/question_library.py", task["allowed_changes"])
        self.assertIn("scripts/json_io.py", task["allowed_changes"])
        owned = {case["id"]: case for case in self.cases["cases"]
                 if case.get("owner_task") == "S08"}
        self.assertEqual(set(task["case_ids"]), {"MOD-23", "MOD-24", "MOD-25"})
        self.assertEqual(set(owned), set(task["case_ids"]))
        self.assertEqual({case["level"] for case in owned.values()}, {"unit", "integration", "e2e"})
        self.assertEqual([owned[case_id]["kind"] for case_id in ("MOD-23", "MOD-24", "MOD-25")],
                         ["negative", "positive", "boundary"])
        self.assertIn("validate_manifest_metric_contract", " ".join(task["completion"]))
        self.assertIn("S08", self.task("G6")["depends_on"])

    def test_s09_fingerprint_contract_has_unit_integration_and_e2e_cases(self):
        task = self.task("S09")
        self.assertEqual(task["depends_on"], ["S08"])
        self.assertIn("scripts/question_fingerprints.py（新）", task["allowed_changes"])
        owned = {case["id"]: case for case in self.cases["cases"]
                 if case.get("owner_task") == "S09"}
        self.assertEqual(set(task["case_ids"]), {"MOD-26", "MOD-27", "MOD-28"})
        self.assertEqual(set(owned), set(task["case_ids"]))
        self.assertEqual({case["level"] for case in owned.values()}, {"unit", "integration", "e2e"})
        self.assertEqual(owned["MOD-27"]["kind"], "negative")
        self.assertIn("validate_manifest_metric_contract", " ".join(task["completion"]))
        self.assertIn("S09", self.task("G6")["depends_on"])

    def test_s10_manifest_and_selection_boundaries_have_unit_integration_and_e2e_cases(self):
        task = self.task("S10")
        self.assertEqual(task["depends_on"], ["S09"])
        self.assertIn("scripts/question_selection.py（新增）", task["allowed_changes"])
        self.assertIn("scripts/question_manifest.py（新增）", task["allowed_changes"])
        owned = {case["id"]: case for case in self.cases["cases"]
                 if case.get("owner_task") == "S10"}
        self.assertEqual(set(task["case_ids"]), {"MOD-29", "MOD-30", "MOD-31"})
        self.assertEqual(set(owned), set(task["case_ids"]))
        self.assertEqual({case["level"] for case in owned.values()},
                         {"unit", "integration", "e2e"})
        self.assertEqual(owned["MOD-30"]["kind"], "negative")
        self.assertIn("S10", self.task("G6")["depends_on"])

    def test_s03_change_allowlist_names_real_question_sources(self):
        allowed = set(self.task("S03")["allowed_changes"])
        expected = {
            "questions/catalog.json",
            "questions/common.json",
            "questions/types/pre_revenue.json",
            "main_questions.json",
            "docs/durability-and-change-design.md",
            "references/buy-side-questions.md",
            "references/common-framework.md",
            "tests/test_question_sets.py",
        }
        self.assertEqual(allowed, expected)
        self.assertFalse(any("C02" in path for path in allowed))

    def test_first_search_provider_does_not_wait_for_later_durable_retry_gate(self):
        self.assertEqual(self.task("Q02")["case_ids"], ["LLM-02", "LLM-11"])
        self.assertIn("LLM-01", self.task("L01")["case_ids"])
        self.assertIn("LLM-06", self.task("Q04")["case_ids"])
        self.assertIn("LLM-06", self.task("Q08")["case_ids"])
        self.assertNotIn("Q08", ip.dependency_ids(
            {task["id"]: task for task in self.plan["tasks"]}, "Q02"))
        llm11 = next(case for case in self.cases["cases"] if case["id"] == "LLM-11")
        self.assertIn("request_id=null", "\n".join(llm11["then"]))

    def test_modular_cases_have_failure_oracles_and_are_not_results(self):
        cases = {case["id"]: case for case in self.cases["cases"]}
        self.assertEqual({f"MOD-{n:02}" for n in range(1, 14)} <= set(cases), True)
        for cid in ("MOD-02", "MOD-04", "MOD-06", "MOD-07", "MOD-08",
                    "MOD-09", "MOD-10", "MOD-12", "MOD-13"):
            with self.subTest(case=cid):
                self.assertIn(cases[cid]["kind"], ("negative", "fault"))
                self.assertEqual(cases[cid]["status"], "specified_not_executed")
        self.assertEqual(cases["MOD-10"]["level"], "live")

    def test_module_archive_graph_legacy_trust_and_composition_closure_are_explicit(self):
        cases = {case["id"]: case for case in self.cases["cases"]}
        mod14 = cases["MOD-14"]
        self.assertIn("validate_registry", mod14["when"])
        self.assertIn("validate_release", mod14["when"])
        self.assertIn("hash", mod14["given"])
        self.assertIn("依赖成环", mod14["given"])
        self.assertIn("模块依赖闭包和无环图", mod14["then"][0])

        mod16 = cases["MOD-16"]
        self.assertIn("S05实际历史reader", mod16["given"])
        self.assertIn("依赖成环", mod16["given"])
        self.assertIn("自洽", mod16["then"][0])

        mod17 = cases["MOD-17"]
        self.assertIn("artifact_sha256", mod17["given"])
        self.assertIn("自报legacy", mod17["given"])
        self.assertIn("可信基线", mod17["then"][0])

        mod18 = cases["MOD-18"]
        self.assertEqual(mod18["owner_task"], "S06")
        self.assertIn("传递dependencies", mod18["then"][0])
        self.assertIn("冲突", mod18["then"][0])
        self.assertIn("MOD-18", self.task("S06")["case_ids"])

        contract = (ROOT / "docs/implementation/contracts/question-modules.md").read_text(encoding="utf-8")
        self.assertIn("精确命中受信任基线", contract)
        self.assertIn("validate_release", contract)
        routing = (ROOT / "references/routing.md").read_text(encoding="utf-8")
        self.assertIn("递归补齐完整`dependencies`闭包", routing)
        self.assertIn("按无向冲突处理", routing)

    def test_atomic_assertion_bindings_are_validated_and_stable(self):
        cases = {case["id"]: case for case in self.cases["cases"]}
        for case_id in ("MOD-07", "MOD-13", "MOD-14", "MOD-16", "MOD-17", "MOD-18", "MOD-19", "EVO-83"):
            with self.subTest(case=case_id):
                assertions = cases[case_id]["assertions"]
                self.assertTrue(assertions)
                self.assertEqual(
                    [item["id"] for item in assertions],
                    [f"{case_id}.A{index:02d}" for index in range(1, len(assertions) + 1)],
                )
                self.assertTrue(all(item.get("entrypoint") and item.get("expected") for item in assertions))

        case = next(item for item in self.cases["cases"] if item["id"] == "MOD-14")
        case["assertions"][1]["id"] = case["assertions"][0]["id"]
        self.rejected("MOD-14: duplicate assertion ID")
        self.cases = copy.deepcopy(self.original_cases)
        case = next(item for item in self.cases["cases"] if item["id"] == "EVO-83")
        case["assertions"][0]["entrypoint"] = " "
        self.rejected("EVO-83: assertion missing entrypoint")

    def test_compatibility_window_tasks_remain_in_the_delivery_graph_without_receipt_gate(self):
        task_map = {task["id"]: task for task in self.plan["tasks"]}
        required = set(self.plan["release_requirements"]["required_tasks"])
        self.assertNotIn("P01", required)
        self.assertNotIn("P01", self.task("G0")["depends_on"])
        for task_id in ("C01", "C02", "C03", "C04", "C05", "C06", "C07"):
            self.assertNotIn("P01", self.task(task_id)["depends_on"])
        self.assertIn("EVO-83", self.task("V16")["case_ids"])
        self.assertIn("V16", ip.dependency_ids(task_map, "G6"))

    def test_composable_evolution_is_in_release_without_blocking_scoring_on_facts(self):
        task_map = {task["id"]: task for task in self.plan["tasks"]}
        expected = {f"V{number:02}" for number in range(1, 16)}
        self.assertTrue(expected <= set(task_map))
        self.assertTrue(expected <= set(ip.dependency_ids(task_map, "G6")))
        self.assertTrue(expected <= set(self.plan["release_requirements"]["required_tasks"]))
        for tid in ("V01", "V08", "V09", "V10", "O04", "G5"):
            with self.subTest(task=tid):
                self.assertTrue({"F06", "G4"}.isdisjoint(ip.dependency_ids(task_map, tid)))
        self.assertIn("V03", self.task("F03")["depends_on"])
        self.assertIn("V07", self.task("F05")["depends_on"])
        self.assertIn("V13", self.task("F02")["depends_on"])
        self.assertIn("V15", self.task("V11")["depends_on"])
        self.assertIn("V15", self.task("X07")["depends_on"])
        self.assertIn("V12", self.task("X11")["depends_on"])

    def test_evolution_cases_and_live_boundary_are_explicit(self):
        cases = {item["id"]: item for item in self.cases["cases"]}
        self.assertTrue({f"EVO-{number:02}" for number in range(1, 44)} <= set(cases))
        self.assertEqual(cases["EVO-23"]["level"], "live")
        self.assertIn("EVO-23", self.task("X10")["case_ids"])
        self.assertIn("E2E-06", self.task("X10")["case_ids"])
        self.assertNotIn("E2E-06", self.task("X09")["case_ids"])
        self.assertNotIn("EVO-21", self.task("V11")["case_ids"])
        for tid in ("U03", "U04", "X09"):
            self.assertIn("EVO-21", self.task(tid)["case_ids"])
        self.assertIn("EVO-22", self.task("V12")["case_ids"])
        self.assertEqual(cases["EVO-22"]["level"], "review")
        self.assertTrue(all(cases[f"EVO-{number:02}"]["status"] ==
                            "specified_not_executed" for number in range(1, 44)))
        self.assertIn("absent/disabled", "\n".join(cases["EVO-01"]["then"]))
        self.assertIn("不下载公司文档", cases["E2E-06"]["given"]["real_data"])

    def test_search_batch_benchmark_is_a_gated_live_experiment(self):
        task_map = {task["id"]: task for task in self.plan["tasks"]}
        cases = {case["id"]: case for case in self.cases["cases"]}
        benchmark = task_map["B01"]
        case = cases["BENCH-01"]

        self.assertEqual(benchmark["kind"], "live")
        self.assertEqual(benchmark["stage"], "M3")
        self.assertEqual(case["level"], "live")
        self.assertEqual(case["owner_task"], "B01")
        self.assertEqual(len(case["assertions"]), 9)
        self.assertEqual(cases["BENCH-02"]["kind"], "fault")
        self.assertEqual(cases["BENCH-02"]["level"], "integration")
        self.assertIn("BENCH-02", benchmark["case_ids"])
        self.assertIn("正交子实验", case["then"][6])
        self.assertIn("source_id", case["then"][1])
        self.assertIn("MAE≤0.75", case["then"][3])
        self.assertIn("500字符", case["then"][1])
        self.assertIn("20个同口径完整run", case["then"][4])
        self.assertIn("2×2", case["then"][7])
        self.assertIn("exactly zero", " ".join(cases["BENCH-02"]["then"]))
        self.assertEqual(set(case["requires_tasks"]), {
            "L01", "G1", "Q05", "Q09", "Q10", "Q12", "W10"
        })
        self.assertIn("B01", self.task("L03")["depends_on"])
        self.assertIn("BENCH-01", self.task("B01")["case_ids"])
        self.assertIn("I56", benchmark["invariants"])
        self.assertIn("I56", self.task("L03")["invariants"])
        self.assertNotIn("I56", self.plan["global_boundaries"])
        self.assertIn("B01", self.plan["release_requirements"]["required_tasks"])
        self.assertEqual(case["status"], "specified_not_executed")

    def test_component_evolution_extensions_are_mandatory_and_owner_scoped(self):
        task_map = {task["id"]: task for task in self.plan["tasks"]}
        expected = {"V16", "V17", "W16", "Q14", "Q15", "V18"}
        ancestors = set(ip.dependency_ids(task_map, "G6"))
        self.assertTrue(expected <= ancestors)
        self.assertTrue(expected <= set(self.plan["release_requirements"]["required_tasks"]))
        self.assertEqual(self.task("Q14")["owner"], "stockqa")
        self.assertEqual(self.task("V16")["owner"], "iqs")
        self.assertEqual(self.task("V17")["owner"], "iqs")
        self.assertEqual(self.task("W16")["owner"], "stockwiki")
        self.assertEqual(self.task("Q15")["owner"], "stockqa")
        self.assertEqual(self.task("V18")["owner"], "iqs")
        cases = {case["id"]: case for case in self.cases["cases"]}
        expected_cases = {f"EVO-{number:02}" for number in range(44, 79)} | {
            "LLM-13", "LLM-14", "LLM-15"
        }
        self.assertTrue(expected_cases <= set(cases))
        self.assertEqual(cases["EVO-56"]["level"], "review")
        self.assertEqual(cases["EVO-63"]["kind"], "race")
        self.assertEqual(cases["LLM-14"]["kind"], "negative")
        self.assertIn("模型调用为零", " ".join(self.task("Q14")["steps"]))
        self.assertIn("needs_review", " ".join(self.task("V17")["steps"]))
        self.assertIn("V17", self.task("W16")["depends_on"])
        self.assertIn("W16", self.task("X05")["depends_on"])
        self.assertIn("W16", self.task("X09")["depends_on"])
        self.assertIn("Q15", ip.dependency_ids(task_map, "X05"))
        self.assertIn("Q15", ip.dependency_ids(task_map, "X09"))
        self.assertIn("V16", self.task("Q14")["depends_on"])
        self.assertIn("Q14", self.task("X07")["depends_on"])
        self.assertIn("Q14", self.task("X09")["depends_on"])
        self.assertIn("X05", self.task("X09")["depends_on"])
        self.assertIn("EVO-64", self.task("X07")["case_ids"])
        self.assertIn("EVO-68", self.task("X08")["case_ids"])
        self.assertTrue({"EVO-67", "EVO-69", "EVO-70", "EVO-71", "EVO-72",
                         "EVO-74", "EVO-76", "EVO-80", "EVO-81", "EVO-82"}
                        <= set(self.task("X09")["case_ids"]))
        self.assertTrue({"EVO-63", "EVO-65", "EVO-66", "EVO-73", "EVO-75"}
                        <= set(self.task("W16")["case_ids"]))
        self.assertTrue({"LLM-17", "EVO-76"} <= set(self.task("Q15")["case_ids"]))
        self.assertIn("EVO-77", self.task("V16")["case_ids"])
        self.assertIn("EVO-78", self.task("V18")["case_ids"])

    def test_component_evolution_cannot_be_dropped_from_final_release(self):
        self.task("G6")["depends_on"].remove("V18")
        self.rejected("G6 must include component lifecycle, impact consumer, parser and upgrade rehearsal")

    def test_public_paid_entry_cannot_bypass_impact_plan_application(self):
        self.task("X05")["depends_on"].remove("W16")
        self.rejected("X05 must consume W16 and X09 must safely settle frozen legacy attempts")
        self.plan = copy.deepcopy(self.original_plan)
        self.task("X09")["case_ids"].remove("EVO-67")
        self.rejected("X05 must consume W16 and X09 must safely settle frozen legacy attempts")
        self.plan = copy.deepcopy(self.original_plan)
        self.task("X09")["depends_on"].remove("X05")
        self.rejected("X09 must depend on X05 and exercise legacy settlement, parser receipt, and concurrency/forged-plan behavior through the installed public path")

    def test_release_set_cannot_omit_parser_release_or_actual_hash_case(self):
        self.task("X07")["depends_on"].remove("Q14")
        self.rejected("X07 release set must bind V16, V17, W16 and Q14 parser releases")
        self.plan = copy.deepcopy(self.original_plan)
        self.task("X07")["case_ids"].remove("EVO-64")
        self.rejected("X07 must validate candidate parser/schema/evidence hashes before installation")
        self.plan = copy.deepcopy(self.original_plan)
        self.task("Q14")["depends_on"].remove("V16")
        self.rejected("Q14: evolution chain misses")
        self.plan = copy.deepcopy(self.original_plan)
        self.task("X08")["case_ids"].remove("EVO-68")
        self.rejected("X08 must verify installed parser/schema/evidence hashes against X07's candidate release set")

    def test_public_e2e_requires_concurrency_and_safe_legacy_settlement_cases(self):
        for case_id in ("EVO-67", "EVO-69", "EVO-70", "EVO-71"):
            with self.subTest(case=case_id):
                self.plan = copy.deepcopy(self.original_plan)
                self.task("X09")["case_ids"].remove(case_id)
                self.rejected("X09 must depend on X05 and exercise legacy settlement, parser receipt, and concurrency/forged-plan behavior through the installed public path")
        self.plan = copy.deepcopy(self.original_plan)
        self.task("W16")["case_ids"].remove("EVO-66")
        self.rejected("W16 must cover atomic apply, old settlement, deterministic-plan rejection, candidate gating, active-pointer CAS")

    def test_owner_task_cannot_claim_downstream_integration_cases(self):
        self.task("W16")["case_ids"].append("EVO-67")
        self.rejected("W16 owner-local case EVO-67 cannot require downstream X05/X09 integration")
        self.plan = copy.deepcopy(self.original_plan)
        self.task("X07")["case_ids"].append("EVO-69")
        self.rejected("X07 cannot claim installation, runtime consumer or final readiness evidence before X08/X09")

    def test_forward_acceptance_dependencies_cannot_mark_local_tasks_complete(self):
        self.task("W01")["case_ids"].append("ID-04")
        self.rejected("W01: case ID-04 is owned by W09, which is outside its dependency closure")
        self.plan = copy.deepcopy(self.original_plan)
        self.task("S01")["case_ids"].append("REC-04")
        self.rejected("S01: case REC-04 is owned by W08, which is outside its dependency closure")
        self.plan = copy.deepcopy(self.original_plan)
        self.task("Q02")["case_ids"].append("LLM-01")
        self.rejected("Q02: case LLM-01 is owned by L01, which is outside its dependency closure")

    def test_case_requires_tasks_must_be_known_and_well_formed(self):
        case = next(item for item in self.cases["cases"] if item["id"] == "LLM-01")
        case["requires_tasks"] = ["NO_SUCH_TASK"]
        self.rejected("LLM-01: requires unknown task(s) NO_SUCH_TASK")
        self.plan = copy.deepcopy(self.original_plan)
        self.cases = copy.deepcopy(self.original_cases)
        case = next(item for item in self.cases["cases"] if item["id"] == "LLM-01")
        case["requires_tasks"] = [{"task": "Q02"}]
        self.rejected("LLM-01: requires_tasks must be unique task IDs")

    def test_active_release_set_and_pre_post_fence_are_in_final_path(self):
        cases = {case["id"]: case for case in self.cases["cases"]}
        self.assertEqual(cases["EVO-73"]["kind"], "negative")
        self.assertEqual(cases["EVO-75"]["kind"], "race")
        self.assertEqual(cases["EVO-76"]["kind"], "race")
        self.assertEqual(cases["EVO-77"]["kind"], "boundary")
        self.assertIn("candidate只可预览", " ".join(self.task("W16")["steps"]))
        self.assertIn("active ReleaseSet", " ".join(self.task("X05")["steps"]))
        self.assertIn("dispatch fence", " ".join(self.task("Q15")["steps"]))
        self.assertIn("Q15", self.plan["release_requirements"]["required_tasks"])
        self.assertIn("唯一owner", " ".join(self.task("W16")["steps"]))
        self.assertIn("短时、单次", " ".join(self.task("W16")["steps"]))
        self.assertIn("send_intent_prepared或W16 consume尚未提交即崩溃", " ".join(self.task("Q15")["steps"]))
        evo66 = cases["EVO-66"]
        self.assertIn("固定V17实现", " ".join(evo66["then"]))
        self.assertNotIn("可信owner回执", " ".join(evo66["then"]))
        self.assertIn("不应自动改变", cases["EVO-77"]["given"])
        self.assertIn("send_intent_prepared", cases["EVO-76"]["given"])
        self.assertIn("跨仓授权线性化点", " ".join(self.task("Q15")["steps"]))
        self.task("X05")["depends_on"].remove("Q15")
        self.rejected("X05 must depend on Q15 before any public paid dispatch")

    def test_two_phase_dispatch_contract_is_consistent_across_current_docs(self):
        boundary = next(item for item in self.plan["global_boundaries"] if item.startswith("W16唯一拥有dispatch fence"))
        active_docs = (
            "docs/implementation/README.md",
            "docs/implementation/composable-evolution-plan.md",
            "docs/implementation/contracts/freshness-and-jobs.md",
            "docs/implementation/cross-project-delivery.md",
            "docs/implementation/decision-register.md",
            "docs/implementation/one-click-launch.md",
            "docs/implementation/test-strategy.md",
        )
        stale_phrases = (
            "permit+send_intent",
            "将permit和本地send_intent耐久提交后才POST",
            "消费后须先将permit绑定到本地send_intent并耐久提交，再POST",
        )
        for token in ("send_intent_prepared", "consume_dispatch_permit", "dispatch_commit", "outcome_unknown"):
            self.assertIn(token, boundary)
        for relative_path in active_docs:
            with self.subTest(path=relative_path):
                content = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("consume_dispatch_permit", content)
                self.assertIn("dispatch_commit", content)
                for stale in stale_phrases:
                    self.assertNotIn(stale, content)

    def test_versioned_answer_parser_cannot_be_owned_by_quick_scan(self):
        self.task("Q14")["owner"] = "iqs"
        self.rejected("Q14 answer parser/version metadata must remain StockQA-owned")

    def test_scoring_only_graph_cannot_silently_depend_on_facts(self):
        for tid in ("V01", "V08", "V09", "V10", "O04", "G5"):
            with self.subTest(task=tid):
                self.plan = copy.deepcopy(self.original_plan)
                self.task(tid)["depends_on"].append("F06")
                self.rejected(f"{tid}: scoring-only delivery must not depend on F06 or G4")

    def test_one_click_dispatch_requires_recipe_runtime_and_store(self):
        self.task("X05")["depends_on"].remove("V10")
        self.rejected("X05 must depend on V09 and V10")

    def test_live_cleanup_case_cannot_be_claimed_by_offline_gate(self):
        self.task("X09")["case_ids"].append("E2E-06")
        self.rejected("X09 offline E2E cannot claim E2E-06")
        self.plan = copy.deepcopy(self.original_plan)
        self.task("X10")["case_ids"].remove("E2E-06")
        self.rejected("X10 live E2E must own E2E-06")

    def test_complete_ui_cannot_be_claimed_before_ui_tasks(self):
        self.task("V11")["case_ids"].append("EVO-21")
        self.rejected("V11 API contract cannot claim U03/U04")

    def test_fact_mode_requires_stockwiki_ingest_ack_owner(self):
        self.task("V15")["depends_on"].remove("F04")
        self.rejected("V15: fact-enabled chain misses")

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
        self.rejected("execution status belongs in task_plan.md/progress.md")

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
        self.assertEqual(ids, {'X01', 'X03', 'V14'})

    def test_launch_packet_contains_new_invariant_definitions(self):
        packet = ip.task_packet(self.plan, self.cases, 'X05', ip.DEFAULT_PLAN_DIR)
        self.assertEqual(len(packet['invariant_details']), len(self.task('X05')['invariants']))
        self.assertTrue(any('| I23 |' in line for line in packet['invariant_details']))

    def test_case_family_allows_e2e_but_not_malformed_ids(self):
        self.assertTrue(any(c['id'] == 'E2E-01' for c in self.cases['cases']))
        self.assertTrue(any(c['id'] == 'C05-CONTRACT-01' for c in self.cases['cases']))
        self.assertEqual(ip.validate_package(self.plan, self.cases), [])
        for cid in ('2E-01', 'E2E-1', 'E2E_01', 'E2E-01;command', '../E2E-01',
                    'C05--CONTRACT-01', 'C05-contract-01'):
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
