"""Offline draft facts authority build/check tests."""

import json
import subprocess
import sys
from pathlib import Path

from facts_offline_inputs import facts_inputs


ROOT = Path(__file__).resolve().parents[1]
RUN = {"run_id": "R1", "scan_id": "S1", "inputset_id": "I1",
       "task_mode": "native", "comparison_group_id": "G1"}
VERSIONS = {"answer_schema": "1.0.0", "identity_schema": "2.1.0",
            "model_policy_schema": "2.0.0", "observation_schema": "1.2.0",
            "question_catalog": "1.0.0"}
PRODUCER = {"component_version": "fixture-1", "build_id": "fixture-build"}


def write(tmp_path, name, value):
    path = tmp_path / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def build(tmp_path, pack, identity, profile):
    output = tmp_path / "authority.json"
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_authority_build.py"),
         "--pack", str(pack), "--identity", str(identity), "--profile", str(profile),
         "--information-cutoff", "2026-10-18",
         "--run-context", str(write(tmp_path, "run.json", RUN)),
         "--contract-versions", str(write(tmp_path, "versions.json", VERSIONS)),
         "--producer", str(write(tmp_path, "producer.json", PRODUCER)),
         "--output", str(output)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return done, output


def check(tmp_path, pack, authority):
    output = tmp_path / "authority.json"
    if authority is not None:
        output.write_text(json.dumps(authority), encoding="utf-8")
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_authority_check.py"),
         "--authority", str(output), "--pack", str(pack)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return done, json.loads(done.stdout)


def test_build_and_check_offline_authority(tmp_path, facts_inputs):
    pack, _, _ = facts_inputs
    done, _ = build(tmp_path, *facts_inputs)
    assert done.returncode == 0, done.stderr
    checked, result = check(tmp_path, pack, None)
    assert checked.returncode == 0, result
    assert result["status"] == "valid"
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    assert result["questions"] == len(manifest["questions"]) > 0


def test_tampered_context_rejected(tmp_path, facts_inputs):
    pack, _, _ = facts_inputs
    done, output = build(tmp_path, *facts_inputs)
    assert done.returncode == 0, done.stderr
    authority = json.loads(output.read_text(encoding="utf-8"))
    question = next(iter(authority["observation_context"]["questions"].values()))
    question["metadata"]["field_id"] = "facts.tampered"
    checked, result = check(tmp_path, pack, authority)
    assert checked.returncode == 2
    assert "facts_authority_context_sha256_mismatch" in result["errors"]
