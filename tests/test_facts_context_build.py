"""Offline draft facts context builder tests."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATL = ROOT / "docs/implementation/reviews/catl-profile-2026-10-18"
CATL_PACK = CATL / "facts-pack-quick"
CATL_PROFILE = CATL / "profile.draft.json"
CATL_IDENTITY = Path(
    "C:/Users/郑曾波/Projects/invest-quick-scan/runs/shared-engine-production-2026-10-18/"
    "actual-native-catl-profile-01/inputs/"
    "subject_1a3d169c71015eac51f7666097c19cd30d0369899f30d3437a828be4b9553698/identity.json"
)


def run(tmp_path, identity=CATL_IDENTITY, profile=CATL_PROFILE):
    output = tmp_path / "facts-context.json"
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_context_build.py"),
         "--pack", str(CATL_PACK), "--identity", str(identity), "--profile", str(profile),
         "--information-cutoff", "2026-10-18", "--output", str(output)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return done, output


def test_build_catl_draft_context(tmp_path):
    done, output = run(tmp_path)
    assert done.returncode == 0, done.stderr
    context = json.loads(output.read_text(encoding="utf-8"))
    assert context["draft_context_protocol"] == "iqs.facts_context/1.0.0"
    assert len(context["questions"]) >= 16
    assert all(row["metadata"]["response_kind"] == "fact" for row in context["questions"].values())
    assert context["context_sha256"]

    check = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_context_check.py"),
         "--pack", str(CATL_PACK), "--context", str(output)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    result = json.loads(check.stdout)
    assert result["status"] == "ready", result


def test_identity_without_entity_rejected(tmp_path):
    identity = tmp_path / "identity.json"
    identity.write_text('{"payload": {}}', encoding="utf-8")
    done, _ = run(tmp_path, identity=identity)
    assert done.returncode != 0
