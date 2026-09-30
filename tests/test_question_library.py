"""Dependency and behavior tests for the shared local question-library contract."""
import ast
import copy
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def imported_modules(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return tree, modules


class QuestionLibraryBoundaryTests(unittest.TestCase):
    def test_answer_builder_uses_shared_library_for_general_helpers(self):
        answer_tree, answer_imports = imported_modules(SCRIPTS / "standard_answers.py")
        self.assertIn("question_library", answer_imports)
        self.assertIn("question_manifest", answer_imports)
        self.assertNotIn("question_sets", answer_imports)

    def test_library_has_no_upward_or_effectful_imports(self):
        path = SCRIPTS / "question_library.py"
        self.assertTrue(path.is_file(), "shared question-library contract has not been extracted")
        _, imports = imported_modules(path)
        forbidden = {
            "question_sets", "standard_answers", "requests", "httpx", "urllib.request",
            "sqlite3", "stockqa", "llm_client", "llm_provider",
        }
        self.assertFalse(forbidden.intersection(imports), sorted(forbidden.intersection(imports)))

    def test_prompt_and_catalog_layers_share_one_json_io_implementation(self):
        library_tree, library_imports = imported_modules(SCRIPTS / "question_library.py")
        prompt_tree, prompt_imports = imported_modules(SCRIPTS / "question_prompts.py")
        json_io_tree, _ = imported_modules(SCRIPTS / "json_io.py")
        question_cli_tree, _ = imported_modules(SCRIPTS / "question_sets.py")
        self.assertIn("json_io", library_imports)
        self.assertIn("json_io", prompt_imports)
        self.assertFalse(any(isinstance(node, ast.FunctionDef) and node.name == "read_json"
                             for node in [*library_tree.body, *prompt_tree.body,
                                          *question_cli_tree.body]))
        json_readers = [node for node in json_io_tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == "read_json"]
        self.assertEqual(len(json_readers), 1)

    def test_clean_process_imports_succeed_in_both_orders_without_live_credentials(self):
        for imports in (
            ("question_library", "question_sets", "standard_answers"),
            ("standard_answers", "question_sets", "question_library"),
        ):
            with self.subTest(imports=imports):
                code = "\n".join(f"import {name}" for name in imports)
                child_env = {
                    key: value for key, value in os.environ.items()
                    if not any(token in key.upper() for token in ("API_KEY", "LIVE_E2E", "LIVE_TEST"))
                }
                child_env["PYTHONPATH"] = str(SCRIPTS)
                result = subprocess.run(
                    [sys.executable, "-c", code], cwd=ROOT, env=child_env,
                    capture_output=True, text=True, timeout=20,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_local_json_helpers_round_trip_only_inside_unique_temp_root(self):
        import question_library as library

        with tempfile.TemporaryDirectory(prefix="iqs-question-library-") as temp_dir:
            path = Path(temp_dir) / "nested" / "config.json"
            value = {"name": "虚构题库测试", "ordered": [3, 1, 2]}
            library.write_json(path, value)
            self.assertEqual(library.read_json(path), value)
            self.assertTrue(path.resolve().is_relative_to(Path(temp_dir).resolve()))

    def test_catalog_and_profile_contract_match_legacy_facade_at_injected_root(self):
        import question_library as library
        import question_sets as question_cli
        import standard_answers as answers

        with tempfile.TemporaryDirectory(prefix="iqs-question-catalog-") as temp_dir:
            alternate_root = Path(temp_dir)
            shutil.copytree(ROOT / "questions", alternate_root / "questions")
            catalog, modules = library.load_library(root=alternate_root)
            self.assertEqual(catalog["version"], library.read_json(
                alternate_root / "questions" / "catalog.json")["version"])
            profile = library.read_json(ROOT / "examples" / "profile.json")
            library.validate_profile(profile, modules, root=alternate_root)
            facts_path = alternate_root / "questions" / "facts.json"
            facts = library.read_json(facts_path)
            facts["version"] = "fixture-facts-isolated"
            library.write_json(facts_path, facts)
            with mock.patch.object(question_cli, "ROOT", alternate_root):
                self.assertEqual(question_cli.load_library(), (catalog, modules))
                question_cli.validate_profile(profile, modules)
            with mock.patch.object(answers, "ROOT", alternate_root):
                fact_status = answers.validate_fact_library()
                selected_bank, selected_facts = answers.select_facts(profile, "quick")
                self.assertEqual(fact_status["version"], "fixture-facts-isolated")
                self.assertEqual(selected_bank["version"], "fixture-facts-isolated")
                self.assertTrue(selected_facts)
                self.assertTrue(all(item["rubric_version"] == "fixture-facts-isolated"
                                    for item in selected_facts))

            invalid = copy.deepcopy(profile)
            invalid["routing_sources"][0]["url"] = "ftp://example.invalid/source"
            with self.assertRaisesRegex(ValueError, r"valid HTTP\(S\) URL"):
                library.validate_profile(invalid, modules, root=alternate_root)


if __name__ == "__main__":
    unittest.main()
