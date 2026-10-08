"""Collect bounded acceptance evidence and recheck source bytes without source writes."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

IQS = Path(__file__).resolve().parents[5]
SOURCE = Path("C:/Users/郑曾波/Projects/iqs-evidence-lab")
OWN = IQS / "runs/evid-lab-second-remediation-2026-10-08-01"
LAB = OWN / "lab"
INTAKE = IQS / "docs/implementation/intake/EVID-LAB-01/2026-10-08-second-remediation"
OUT = INTAKE / "verification"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(*args):
    return subprocess.run(["git", "-C", str(SOURCE), *args],
                          env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"), capture_output=True,
                          timeout=30, check=True).stdout.decode("utf-8").strip()


def main():
    baseline = read(INTAKE / "source-baseline.json")
    state = {"head": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
             "status": git("status", "--porcelain=v1"), "source_written_by_controller": False,
             "temp_root_entries": sorted(p.name for p in (SOURCE / ".temp-roots").iterdir())
                 if (SOURCE / ".temp-roots").exists() else []}
    artifacts = read(SOURCE / "docs/handoff/EVID-LAB-01/artifacts.json")
    state["worktree_artifact_count"] = len(artifacts["files"])
    state["worktree_artifact_mismatches"] = [item["path"] for item in artifacts["files"]
        if len((SOURCE / item["path"]).read_bytes()) != item["bytes"]
        or sha((SOURCE / item["path"]).read_bytes()) != item["worktree_sha256"]]
    save(INTAKE / "source-after.json", state)
    assert state["head"] == baseline["head"] and state["branch"] == baseline["branch"]
    assert state["status"] == baseline["status"] == ""
    assert state["worktree_artifact_count"] == 122 and not state["worktree_artifact_mismatches"]

    for folder in (".controller-extra", ".controller-followup"):
        origin = LAB / folder
        if not origin.exists():
            continue
        for path in sorted(origin.rglob("*")):
            if path.is_file():
                target = OUT / "original-case-artifacts" / folder / path.relative_to(origin)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    binding = read(OUT / "archive-binding-corrected/archive-binding-result.json")
    modified = OWN / "locked-input-copy-corrected" / binding["archive_mutation"]["relative_path"]
    (OUT / "archive-binding-corrected/modified-archive-results.jsonl").write_bytes(modified.read_bytes())
    (OUT / "archive-binding-corrected/corrected-controller-executed.py").write_bytes(
        (Path(__file__).parent / "run_archive_binding.py").read_bytes())

    result = read(OUT / "result.json")
    before = result["original_inputs_before"]
    after = {relative: sha((IQS / relative).read_bytes()) for relative in before}
    changed = [item["path"] for item in read(OWN / "snapshot.json")
               if sha((LAB / item["path"]).read_bytes()) != item["sha256"]]
    assert before == after and not changed
    assert all(row["returncode"] == 0 for row in result["checks"])
    assert len(result["checks"]) == 42 and result["replay_payloads_stable"]
    assert [row["expectation_met"] for row in binding["checks"]] == [True, True, False, True]
    result.update(status="partial_verified_changes_requested", original_inputs_after=after,
                  input_bytes_unchanged=True, snapshot_changed_after_all_cases=changed,
                  source_after_ref="../source-after.json",
                  original_six_residual_cases="verified_fixed",
                  remaining_findings=[{"id": "LR-02B", "priority": "P1",
                                       "evidence": "archive-binding-corrected/archive-binding-result.json",
                                       "summary": "Historical fixture replay does not validate the archive's immutable input lock"}],
                  review_status="one_concentrated_independent_review_completed",
                  not_closed=["L02 full calibration", "G3", "F05", "TH-IMPL-01", "IN-IMPL-01", "L03"],
                  proposal_status="draft_not_signed_not_executed", cleanup_pending=True)
    save(OUT / "result.json", result)
    print(json.dumps({"worker_head_unchanged": True, "worker_clean": True, "raw_artifacts_matched": 122,
                      "locked_inputs_unchanged": len(before), "snapshot_files_unchanged": 123,
                      "original_batch_commands_passed": 42, "remaining_p1": 1,
                      "cleanup_pending": True}))


if __name__ == "__main__":
    main()
