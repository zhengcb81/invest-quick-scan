import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bank_lint  # noqa: E402


def _write(root: Path, applies_when: str = "same", rubric: str = "1.0.0") -> None:
    (root / "questions").mkdir(parents=True)
    module = {
        "module_id": "common",
        "kind": "common",
        "version": "1.0.0",
        "applies_when": applies_when,
        "questions": [{"id": "Q1", "rubric_version": rubric}],
    }
    (root / "questions/common.json").write_text(json.dumps(module), encoding="utf-8")
    catalog = {"modules": [{
        "id": "common", "kind": "common", "path": "questions/common.json",
        "applies_when": "catalog", "question_count": 1,
    }]}
    (root / "questions/catalog.json").write_text(json.dumps(catalog), encoding="utf-8")


def test_detects_catalog_metadata_drift(tmp_path):
    _write(tmp_path)
    result = bank_lint.lint(tmp_path)
    assert any("applies_when" in error for error in result["errors"])


def test_warns_on_mixed_rubric_versions(tmp_path):
    (tmp_path / "questions").mkdir(parents=True)
    module = {
        "module_id": "common", "kind": "common", "version": "1.0.0",
        "applies_when": "same",
        "questions": [
            {"id": "Q1", "rubric_version": "1.0.0"},
            {"id": "Q2", "rubric_version": "2.0.0"},
        ],
    }
    (tmp_path / "questions/common.json").write_text(json.dumps(module), encoding="utf-8")
    catalog = {"modules": [{
        "id": "common", "kind": "common", "path": "questions/common.json",
        "applies_when": "same", "question_count": 2,
    }]}
    (tmp_path / "questions/catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    result = bank_lint.lint(tmp_path)
    assert not result["errors"]
    assert any("rubric_version" in warning for warning in result["warnings"])


def test_real_catalog_has_no_errors():
    result = bank_lint.lint(ROOT)
    assert result["errors"] == []
    assert result["modules"] == 48
