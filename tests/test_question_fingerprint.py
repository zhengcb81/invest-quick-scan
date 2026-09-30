import ast
import copy
import inspect
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import module_registry
import question_library
import question_sets
from question_fingerprints import question_fingerprint


ROOT = Path(question_sets.ROOT)
FINGERPRINT_FIXTURE_PACKAGE = (
    "pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f")


def published_sample():
    profile = question_library.read_json(ROOT / "examples/profile.json")
    temporary = tempfile.TemporaryDirectory(prefix="question-fingerprint-")
    output_dir = Path(temporary.name)
    question_sets.compose(profile, "quick", output_dir, answer_format="standard-1",
                          package_id=FINGERPRINT_FIXTURE_PACKAGE)
    manifest = question_sets.read_json(output_dir / "manifest.json")
    package, modules, release, contexts = module_registry.load_package(
        manifest["module_package_id"], root=ROOT)
    return temporary, manifest, package, modules, release, contexts


class QuestionFingerprintTests(unittest.TestCase):
    def test_legacy_default_and_current_fingerprint_algorithms_are_stable(self):
        temporary, manifest, package, _, release, contexts = published_sample()
        self.addCleanup(temporary.cleanup)
        question = manifest["questions"][0]
        profile = manifest["profile"]

        legacy_package = copy.deepcopy(package)
        legacy_package.pop("semantic_fingerprint_version")
        self.assertEqual(
            question_fingerprint(question, profile, contexts, legacy_package, release, "standard-1"),
            "30d2fe7dee310b825a9463ca5606f6613f7adfeba213962cb10a6a49c814a3c9")

        self.assertEqual(
            question_fingerprint(question, profile, contexts, package, release, "standard-1"),
            "64961bb9a5757f77562175eabfd67fea0e7235fce18c3d2d1c5948d80c8edb2a")

        changed_package = copy.deepcopy(package)
        changed_package["format_resources"]["schemas/answer-content.schema.json"]["x-test-changed"] = True
        self.assertNotEqual(
            question_fingerprint(question, profile, contexts, changed_package, release, "standard-1"),
            question_fingerprint(question, profile, contexts, package, release, "standard-1"))

    def test_question_sets_legacy_entrypoint_delegates_to_shared_contract(self):
        temporary, manifest, package, _, release, contexts = published_sample()
        self.addCleanup(temporary.cleanup)
        question = manifest["questions"][0]
        self.assertEqual(
            tuple(inspect.signature(question_sets._question_fingerprint).parameters),
            ("q", "profile", "contexts", "package", "release", "answer_format"))
        self.assertEqual(
            question_sets._question_fingerprint(
                question, manifest["profile"], contexts, package, release, "standard-1"),
            question_fingerprint(
                question, manifest["profile"], contexts, package, release, "standard-1"))

        legacy_package = copy.deepcopy(package)
        legacy_package.pop("semantic_fingerprint_version")
        self.assertEqual(
            question_sets._question_fingerprint(
                q=question, profile=manifest["profile"], contexts=contexts,
                package=legacy_package, release=release, answer_format="standard-1"),
            question_fingerprint(
                question, manifest["profile"], contexts, legacy_package, release, "standard-1"))

    def test_answer_builder_uses_the_stable_manifest_contract_module(self):
        source = (ROOT / "scripts" / "standard_answers.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            node.module for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        imports.update(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                       for alias in node.names)
        self.assertIn("question_manifest", imports)
        self.assertNotIn("question_sets", imports)


if __name__ == "__main__":
    unittest.main()
