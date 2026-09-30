"""MOD-18 dependency-closure and pre-question-dispatch regressions."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import module_contract as mc
import module_registry as registry
import question_sets as qs
import routing

_fixture_path = ROOT / "tests" / "test_routing.py"
_fixture_spec = importlib.util.spec_from_file_location("_s06_dependency_route_fixture", _fixture_path)
_fixture_module = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(_fixture_module)


def _module(kind, dependencies=(), conflicts=(), question_id=None):
    questions = []
    if question_id:
        questions = [{"id": question_id, "priority": 1, "critical": False, "replaces": []}]
    return {"kind": kind, "dependencies": list(dependencies), "conflicts": list(conflicts),
            "questions": questions}


class ModuleDependencyClosureTests(unittest.TestCase):
    def test_mod18_a01_a04_transitive_closure_deduplicates_and_is_order_stable(self):
        modules = {
            "common": _module("common", question_id="IQS_01"),
            "base_a": _module("industries", ["common"], question_id="BASE_A_01"),
            "base_b": _module("industries", ["common"], question_id="BASE_B_01"),
            "semiconductors": _module("industries", ["base_b", "base_a"], question_id="SEMI_01"),
        }
        decisions = {module_id: "selected" for module_id in modules}
        first = routing.resolve_module_dependency_closure(
            ["semiconductors"], modules, decisions)
        reordered_modules = {
            key: {**copy.deepcopy(value), "dependencies": list(reversed(value["dependencies"]))}
            for key, value in reversed(list(modules.items()))
        }
        second = routing.resolve_module_dependency_closure(
            ["base_a", "semiconductors"], reordered_modules, decisions)

        self.assertEqual(first["issues"], [])
        self.assertEqual(first["module_ids"], ["common", "base_a", "base_b", "semiconductors"])
        self.assertEqual(first, second)
        questions_a, selected_a, _ = qs.select_questions_for_route({}, "quick", modules, first["module_ids"])
        questions_b, selected_b, _ = qs.select_questions_for_route({}, "quick", reordered_modules,
                                                                    second["module_ids"])
        question_ids_a = [question["id"] for question in questions_a]
        question_ids_b = [question["id"] for question in questions_b]
        self.assertEqual(selected_a, selected_b)
        self.assertEqual(question_ids_a, ["IQS_01", "BASE_A_01", "BASE_B_01", "SEMI_01"])
        self.assertEqual(question_ids_a, question_ids_b)
        self.assertEqual(mc.digest(question_ids_a), mc.digest(question_ids_b))

    def test_mod18_a02_missing_uncertain_rejected_and_cyclic_dependencies_fail_closed(self):
        missing = {"parent": _module("industries", ["not_published"])}
        self.assertIn("dependency_missing:parent:not_published",
                      routing.resolve_module_dependency_closure(["parent"], missing)["issues"])

        for state in ("uncertain", "rejected"):
            modules = {"parent": _module("industries", ["foundation"]),
                       "foundation": _module("common_extensions")}
            result = routing.resolve_module_dependency_closure(
                ["parent"], modules, {"parent": "selected", "foundation": state})
            with self.subTest(dependency_state=state):
                self.assertIn(f"dependency_not_selected:parent:foundation:{state}", result["issues"])

        cyclic = {"alpha": _module("industries", ["beta"]),
                  "beta": _module("common_extensions", ["alpha"])}
        result = routing.resolve_module_dependency_closure(
            ["alpha"], cyclic, {"alpha": "selected", "beta": "selected"})
        self.assertIn("dependency_cycle:alpha->beta->alpha", result["issues"])

    def test_mod18_a03_conflicts_are_undirected_but_alternatives_can_coexist(self):
        modules = {
            "common": _module("common"),
            "alternative_a": _module("industries", ["common"], ["alternative_b"]),
            "alternative_b": _module("industries", ["common"]),
        }
        coexist = routing.resolve_module_dependency_closure(["alternative_a"], modules)
        self.assertEqual(coexist["issues"], [])
        both = routing.resolve_module_dependency_closure(["alternative_a", "alternative_b"], modules)
        self.assertIn("selected_conflict:alternative_a:alternative_b", both["issues"])


class DependencyDispatchBoundaryTests(_fixture_module.RoutingFixture):
    """Use the real route resolver and public composition entry with a temp package."""

    def setUp(self):
        super().setUp()
        root_patcher = patch.object(qs, "ROOT", self.root)
        root_patcher.start()
        self.addCleanup(root_patcher.stop)

    def test_mod18_a05_unresolved_dependency_or_selected_conflict_writes_no_dispatch_payload(self):
        base_loader = registry.load_package
        variants = (
            ("uncertain_dependency", {"dependencies": ["cyclical"]}),
            ("selected_conflict", {"conflicts": ["operating"]}),
        )
        for name, module_patch in variants:
            def load_with_fixture_graph(package_id, *, root=ROOT, changes=module_patch):
                package, modules, release, contexts = base_loader(package_id, root=root)
                modules = copy.deepcopy(modules)
                modules["semiconductors"].update(copy.deepcopy(changes))
                return package, modules, release, contexts

            with self.subTest(selection_issue=name), patch.object(
                    registry, "load_package", side_effect=load_with_fixture_graph):
                route = self.route()
                self.assertEqual(route["dispatch_plan"]["status"], "needs_review")
                self.assertEqual(route["dispatch_plan"]["eligible_module_ids"], [])
                self.assertTrue(any(gap.startswith(("dependency_not_selected:", "selected_conflict:"))
                                    for gap in route["dispatch_plan"]["coverage_gaps"]))

                output = self.root / "outputs" / name
                with patch.object(qs, "write_json", wraps=qs.write_json) as write_json:
                    with self.assertRaisesRegex(ValueError, "needs_review"):
                        qs.compose_from_route(route, output, now_utc=self.now,
                                              expected_route_decision_id=route["decision_id"])
                    write_json.assert_not_called()
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
