"""Offline facts pack pre-registration validation tests."""

import json
import subprocess
import sys
from pathlib import Path

from facts_offline_inputs import facts_inputs


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_PACK = ROOT / "docs/implementation/reviews/catl-profile-2026-10-18/facts-pack-quick"


def run(pack):
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_pack_check.py"), "--pack", str(pack)],
        stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return done, json.loads(done.stdout)


def test_newly_composed_pack_valid(facts_inputs):
    pack, _, _ = facts_inputs
    done, result = run(pack)
    assert done.returncode == 0, result
    assert result["status"] == "valid"
    assert result["question_count"] >= 1
    assert result["mode"] == "quick"


def test_archived_pack_reports_newer_answer_schema_without_rewriting_it():
    manifest = HISTORICAL_PACK / "manifest.json"
    before = manifest.read_bytes()
    done, result = run(HISTORICAL_PACK)
    assert done.returncode == 2, result
    assert result["errors"] == ["facts_pack_source_changed:schemas/answer-content.schema.json"]
    assert manifest.read_bytes() == before


def test_tampered_pack_rejected(facts_inputs):
    pack, _, _ = facts_inputs
    path = pack / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["source_sha256"]["questions/facts.json"] = "0" * 64
    path.write_text(json.dumps(manifest), encoding="utf-8")
    done, result = run(pack)
    assert done.returncode == 2
    assert result["errors"] == ["facts_pack_source_changed:questions/facts.json"]


def test_non_fact_question_rejected(facts_inputs):
    pack, _, _ = facts_inputs
    path = pack / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["questions"][0]["response_kind"] = "score"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    done, result = run(pack)
    assert done.returncode == 2
    assert any("non_fact_question" in error for error in result["errors"])
