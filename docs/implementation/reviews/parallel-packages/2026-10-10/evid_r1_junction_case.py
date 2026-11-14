"""One actual Windows staging-junction case in the controller's owned root."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

lab = Path.cwd()
work = lab.parent
assert work.name == "p114er1a" and lab.name == "evid"
staging = lab / ".temp-roots"
target = work / "junction-target"
sentinel = target / "sentinel.txt"
assert staging.is_dir() and not list(staging.iterdir())
assert set(p.name for p in target.iterdir()) == {"sentinel.txt"}
sha = hashlib.sha256(sentinel.read_bytes()).hexdigest()
assert staging.resolve().is_relative_to(work.resolve()) and target.resolve().is_relative_to(work.resolve())
staging.rmdir()
env = dict(os.environ, IQS_TEST_JUNCTION=str(staging), IQS_TEST_TARGET=str(target),
           IQS_ROOT=str(work / "iqs"), IQS_EVIDENCE_LAB_IQS_ROOT=str(work / "iqs"))
made = subprocess.run(["powershell", "-NoProfile", "-Command",
    "$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:IQS_TEST_JUNCTION -Target $env:IQS_TEST_TARGET | Out-Null"],
    env=env, capture_output=True, text=True, timeout=30)
assert made.returncode == 0, made.stderr
assert staging.lstat().st_file_attributes & 0x400 and staging.resolve() == target.resolve()
try:
    out = lab / "docs/handoff/EVID-REF-02/remediation-01/generated/accept-staging-junction-followup"
    command = [sys.executable, "-B", "-X", "utf8", "tools/reference_entry.py", "summarize",
               "--evaluation", str(lab / ".acceptance-cases/legacy-evaluation.json"), "--output", str(out)]
    proc = subprocess.run(command, cwd=lab, env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
    result = {"case_id": "ER-R1-staging-junction-native", "expected": "exit3 before staging creation/writes",
              "actual_junction_verified": True, "owned_target": str(target), "command": command,
              "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr,
              "output_exists": out.exists(), "target_entries": sorted(p.name for p in target.iterdir()),
              "sentinel_unchanged": hashlib.sha256(sentinel.read_bytes()).hexdigest() == sha,
              "finding_reproduced": proc.returncode == 0 and out.exists()}
finally:
    os.rmdir(staging)
    assert target.is_dir() and hashlib.sha256(sentinel.read_bytes()).hexdigest() == sha
    staging.mkdir()
result.update(junction_removed_without_target_traversal=True, source_written=False, paid_calls=0)
with (lab / ".acceptance-cases/junction-result-02.json").open("x", encoding="utf-8") as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False))
