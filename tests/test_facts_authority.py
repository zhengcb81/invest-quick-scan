"""Offline draft facts authority build/check tests."""

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


def build(tmp_path):
    output = tmp_path / "authority.json"
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_authority_build.py"),
         "--pack", str(CATL_PACK), "--identity", str(CATL_IDENTITY), "--profile", str(CATL_PROFILE),
         "--information-cutoff", "2026-10-18",
         "--run-context", str(write(tmp_path, "run.json", RUN)),
         "--contract-versions", str(write(tmp_path, "versions.json", VERSIONS)),
         "--producer", str(write(tmp_path, "producer.json", PRODUCER)),
         "--output", str(output)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return done, output


def check(tmp_path, authority):
    output = tmp_path / "authority.json"
    if authority is not None:
        output.write_text(json.dumps(authority), encoding="utf-8")
    done = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/facts_authority_check.py"),
         "--authority", str(output), "--pack", str(CATL_PACK)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return done, json.loads(done.stdout)


def test_build_and_check_catl_authority(tmp_path):
    done, output = build(tmp_path)
    assert done.returncode == 0, done.stderr
    checked, result = check(tmp_path, None)
    assert checked.returncode == 0, result
    assert result["status"] == "valid"
    assert result["questions"] >= 16


def test_tampered_context_rejected(tmp_path):
    done, output = build(tmp_path)
    assert done.returncode == 0, done.stderr
    authority = json.loads(output.read_text(encoding="utf-8"))
    authority["observation_context"]["questions"]["FACT_01"]["metadata"]["field_id"] = "facts.tampered"
    checked, result = check(tmp_path, authority)
    assert checked.returncode == 2
    assert "facts_authority_context_sha256_mismatch" in result["errors"]
