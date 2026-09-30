"""Dependency-boundary tests for pure quick-scan question prompt rendering."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import question_prompts as qp  # noqa: E402
import question_sets as qs  # noqa: E402
import standard_answers as sa  # noqa: E402
import module_registry  # noqa: E402


def imported_modules(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


class QuestionPromptBoundaryTests(unittest.TestCase):
    def test_orchestrator_and_answer_builder_share_prompts_without_importing_each_other(self):
        question_sets = imported_modules(ROOT / "scripts" / "question_sets.py")
        standard_answers = imported_modules(ROOT / "scripts" / "standard_answers.py")
        prompts_path = ROOT / "scripts" / "question_prompts.py"

        self.assertTrue(prompts_path.is_file(), "a dedicated prompt contract module is required")
        prompt_imports = imported_modules(prompts_path)
        self.assertNotIn("standard_answers", question_sets)
        self.assertNotIn("question_sets", prompt_imports)
        self.assertNotIn("standard_answers", prompt_imports)
        self.assertIn("question_prompts", question_sets)
        self.assertIn("question_prompts", standard_answers)

    def test_clean_process_imports_succeed_in_both_orders(self):
        for imports in (("standard_answers", "question_sets", "question_prompts"),
                        ("question_sets", "question_prompts", "standard_answers")):
            with self.subTest(imports=imports):
                code = (
                    "import sys; "
                    f"sys.path.insert(0, {str(ROOT / 'scripts')!r}); "
                    + "; ".join(f"import {name}" for name in imports)
                )
                environment = {"PYTHONDONTWRITEBYTECODE": "1"}
                environment.update({key: os.environ[key] for key in (
                    "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP") if key in os.environ})
                result = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT,
                                        env=environment,
                                        capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_score_and_fact_prompts_share_one_deterministic_renderer(self):
        _, modules = qs.load_library()
        type_id = next(key for key, module in modules.items() if module["kind"] == "types")
        stage_id = next(key for key, module in modules.items() if module["kind"] == "stages")
        profile = {"company": "Fixture Company", "ticker": "FIXTURE", "exchange": "TEST",
                   "as_of": "2026-09-20", "company_type": type_id, "stage": stage_id,
                   "industry_modules": []}
        contexts = qs.read_json(ROOT / "questions" / "scoring-contexts.json")
        score_question = {**modules["common"]["questions"][0], "module_id": "common"}
        fact_question = {"id": "FACT_FIXTURE_01", "response_kind": "fact",
                         "question": "列出主要客户。", "relations": ["customer"], "max_items": 3}

        for question in (score_question, fact_question):
            with self.subTest(question=question["id"]):
                first = qp.standard_prompt(question, profile, contexts=contexts)
                second = qp.standard_prompt(question, profile, contexts=contexts)
                self.assertEqual(first, second)
                self.assertEqual(first, sa.standard_prompt(question, profile, contexts=contexts))
                self.assertIn("Fixture Company", first)
                self.assertIn("2026-09-20", first)
                self.assertIn(f"response_kind={question.get('response_kind', 'score')}", first)
                self.assertTrue(first.endswith(json.dumps(
                    qp.read_json(ROOT / "questions" / "metric-registry.json")["metrics"],
                    ensure_ascii=False, separators=(",", ":"))))

    def test_existing_question_set_rendering_names_are_compatibility_aliases(self):
        self.assertIs(qs.render_question, qp.render_question)
        self.assertIs(qs.applied_contexts, qp.applied_contexts)
        self.assertEqual(qs.ANSWER_RULE, qp.ANSWER_RULE)
        package, _, release, _ = module_registry.load_current(root=ROOT)
        self.assertEqual(qs.RENDERER_VERSION, release["renderer_version"])
        self.assertEqual(qs.renderer_rules_sha256(), package["renderer_rules_sha256"])


if __name__ == "__main__":
    unittest.main()
