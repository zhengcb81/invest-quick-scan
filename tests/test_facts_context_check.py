"""Offline facts pack vs observation context coverage tests."""

import json
import subprocess
import sys
from pathlib import Path

from facts_offline_inputs import facts_inputs


ROOT = Path(__file__).resolve().parents[1]


def run(pack, context):
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_context_check.py"),
         "--pack", str(pack), "--context", str(context)],
        stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return done, json.loads(done.stdout)


def test_facts_pack_blocked_by_score_only_context(tmp_path, facts_inputs):
    pack, _, _ = facts_inputs
    context = tmp_path / "score-only.json"
    context.write_text(json.dumps({
        "observation_context": {"questions": {"SCORE_1": {"metadata": {"field_id": "score.growth"}}}},
    }), encoding="utf-8")
    done, result = run(pack, context)
    assert done.returncode == 2
    assert result["status"] == "blocked"
    assert result["missing_field_count"] == result["pack_questions"] > 0
    assert result["context_questions"] == 1


def test_synthetic_context_ready(tmp_path, facts_inputs):
    pack, _, _ = facts_inputs
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    questions = {
        row["id"]: {"metadata": {"field_id": row["field_id"]}} for row in manifest["questions"]
    }
    context = tmp_path / "context.json"
    context.write_text(json.dumps({"observation_context": {"questions": questions}}), encoding="utf-8")
    done, result = run(pack, context)
    assert done.returncode == 0, result
    assert result["status"] == "ready"
    assert result["missing_field_count"] == 0
