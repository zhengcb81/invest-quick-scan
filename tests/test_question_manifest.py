"""Unit tests for the published question-manifest validation boundary."""

import ast
import inspect
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import question_manifest as manifest_contract  # noqa: E402
import question_sets as qs  # noqa: E402


class QuestionManifestBoundaryTests(unittest.TestCase):
    def test_standard_answers_imports_manifest_contract_without_question_sets(self):
        source = (ROOT / "scripts" / "standard_answers.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

        self.assertIn("question_manifest", imported_modules)
        self.assertNotIn("question_sets", imported_modules)

    def test_manifest_and_selection_contracts_do_not_import_the_cli_orchestrator(self):
        for module_name in ("question_manifest.py", "question_selection.py"):
            with self.subTest(module=module_name):
                tree = ast.parse((ROOT / "scripts" / module_name).read_text(encoding="utf-8"))
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.update(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.add(node.module)
                self.assertNotIn("question_sets", imports)

    def test_question_sets_keeps_the_legacy_manifest_validator_entrypoint(self):
        self.assertEqual(tuple(inspect.signature(
            qs.validate_manifest_metric_contract).parameters), ("manifest",))
        self.assertIsNone(qs.validate_manifest_metric_contract({"schema_version": "2.1"}))
        with self.assertRaisesRegex(ValueError, "unsupported metric contract version"):
            qs.validate_manifest_metric_contract({"metric_contract_version": "99.0.0"})
        self.assertIsNone(manifest_contract.validate_manifest_metric_contract({"schema_version": "2.1"}))


if __name__ == "__main__":
    unittest.main()
