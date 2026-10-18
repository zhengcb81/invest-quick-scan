"""Offline facts pack pre-registration validation tests."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATL_PACK = ROOT / "docs/implementation/reviews/catl-profile-2026-10-18/facts-pack-quick"


def run(pack):
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_pack_check.py"), "--pack", str(pack)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return done, json.loads(done.stdout)


def test_catl_pack_valid():
    done, result = run(CATL_PACK)
    assert done.returncode == 0, result
    assert result["status"] == "valid"
    assert result["question_count"] >= 1
    assert result["mode"] == "quick"


def test_tampered_pack_rejected(tmp_path):
    manifest = json.loads((CATL_PACK / "manifest.json").read_text(encoding="utf-8"))
    manifest["source_sha256"]["questions/facts.json"] = "0" * 64
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "questions.json").write_text((CATL_PACK / "questions.json").read_text(encoding="utf-8"), encoding="utf-8")
    done, result = run(tmp_path)
    assert done.returncode == 2
    assert any(error.startswith("facts_pack_source_changed") for error in result["errors"])


def test_non_fact_question_rejected(tmp_path):
    manifest = json.loads((CATL_PACK / "manifest.json").read_text(encoding="utf-8"))
    manifest["questions"][0]["response_kind"] = "score"
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "questions.json").write_text((CATL_PACK / "questions.json").read_text(encoding="utf-8"), encoding="utf-8")
    done, result = run(tmp_path)
    assert done.returncode == 2
    assert any("non_fact_question" in error for error in result["errors"])
