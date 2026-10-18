"""Offline facts pack vs observation context coverage tests."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATL_PACK = ROOT / "docs/implementation/reviews/catl-profile-2026-10-18/facts-pack-quick"
CATL_AUTHORITY = Path(
    "C:/Users/郑曾波/Projects/invest-quick-scan/runs/shared-engine-production-2026-10-18/"
    "actual-native-catl-profile-01/inputs/"
    "subject_1a3d169c71015eac51f7666097c19cd30d0369899f30d3437a828be4b9553698/authority.json"
)


def run(pack, context):
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_context_check.py"),
         "--pack", str(pack), "--context", str(context)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return done, json.loads(done.stdout)


def test_catl_pack_blocked_by_score_only_context():
    done, result = run(CATL_PACK, CATL_AUTHORITY)
    assert done.returncode == 2
    assert result["status"] == "blocked"
    assert result["missing_field_count"] >= 1
    assert result["pack_questions"] >= 1


def test_synthetic_context_ready(tmp_path):
    manifest = json.loads((CATL_PACK / "manifest.json").read_text(encoding="utf-8"))
    questions = {
        row["id"]: {"metadata": {"field_id": row["field_id"]}} for row in manifest["questions"]
    }
    context = tmp_path / "context.json"
    context.write_text(json.dumps({"observation_context": {"questions": questions}}), encoding="utf-8")
    done, result = run(CATL_PACK, context)
    assert done.returncode == 0, result
    assert result["status"] == "ready"
    assert result["missing_field_count"] == 0
