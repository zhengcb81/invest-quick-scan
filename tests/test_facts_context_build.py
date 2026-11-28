"""Offline draft facts context builder tests."""

import json
import subprocess
import sys
from pathlib import Path

from facts_offline_inputs import facts_inputs


ROOT = Path(__file__).resolve().parents[1]


def run(tmp_path, pack, identity, profile):
    output = tmp_path / "facts-context.json"
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_context_build.py"),
         "--pack", str(pack), "--identity", str(identity), "--profile", str(profile),
         "--information-cutoff", "2026-10-18", "--output", str(output)],
        stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return done, output


def test_build_draft_context(tmp_path, facts_inputs):
    pack, _, _ = facts_inputs
    done, output = run(tmp_path, *facts_inputs)
    assert done.returncode == 0, done.stderr
    context = json.loads(output.read_text(encoding="utf-8"))
    expected = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))["questions"]
    assert context["draft_context_protocol"] == "iqs.facts_context/1.0.0"
    assert set(context["questions"]) == {row["id"] for row in expected}
    assert all(row["metadata"]["response_kind"] == "fact" for row in context["questions"].values())
    assert context["context_sha256"]

    check = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_context_check.py"),
         "--pack", str(pack), "--context", str(output)],
        stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    result = json.loads(check.stdout)
    assert check.returncode == 0, result
    assert result["status"] == "ready", result


def test_identity_without_entity_rejected(tmp_path, facts_inputs):
    pack, identity, profile = facts_inputs
    identity.write_text('{"payload": {}}', encoding="utf-8")
    done, output = run(tmp_path, pack, identity, profile)
    assert done.returncode != 0
    assert "facts_context_identity_entity_required" in done.stderr
    assert not output.exists()
