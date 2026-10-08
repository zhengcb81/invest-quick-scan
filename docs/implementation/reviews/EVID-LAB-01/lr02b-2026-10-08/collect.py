"""Collect finite LR-02B evidence without changing delivered source bytes."""
import json
import os
import re
import stat
from pathlib import Path

from prepare import INTAKE, IQS, OWN, RECEIVED, SOURCE, git, save, sha

LAB = OWN / "lab"
OUT = INTAKE / "verification"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def main():
    result = read(OUT / "result.json")
    corrected = read(OUT / "archive-binding-tests-short-temp-in-lab.result.json")
    binding = read(OUT / "archive-binding/archive-binding-result.json")
    assert len(result["checks"]) == 40
    assert [r["name"] for r in result["checks"] if r["returncode"]] == ["worker-regression"]
    assert "108 passed, 10 errors" in (OUT / "worker-regression.stdout.log").read_text("utf-8")
    assert corrected["returncode"] == 0 and corrected["original_inputs_unchanged"]
    assert re.search(r"\b10 passed\b", (OUT / "archive-binding-tests-short-temp-in-lab.stdout.log").read_text("utf-8"))
    assert all(row["expectation_met"] for row in binding["checks"])
    assert [row["returncode"] for row in binding["checks"]] == [0, 4, 2, 2]
    assert binding["lock_bytes_unchanged"] and binding["original_inputs_unchanged"]
    assert all(not row["published"] for row in binding["checks"][1:])
    assert not list((LAB / ".temp-roots").glob("staging-*"))
    modified = OWN / "locked-input-copy-boundary" / binding["archive_mutation"]["relative_path"]
    (OUT / "archive-binding/modified-archive-results.jsonl").write_bytes(modified.read_bytes())
    (OUT / "archive-binding/controller-executed.py").write_bytes(Path(__file__).with_name("run_archive_binding.py").read_bytes())
    catalog = read(OUT / "public-fixtures.stdout.log")
    assert catalog["ok"] and catalog["fixtures"] == 34 and catalog["records"] == 350
    assert len(result["fixture_results"]) == 34 and all(r["returncode"] == 0 for r in result["fixture_results"])
    assert result["replay_payloads_stable"]
    before = result["original_inputs_before"]
    after = {path: sha((IQS / path).read_bytes()) for path in before}
    changed = [item["path"] for item in read(OWN / "snapshot.json")
               if len((LAB / item["path"]).read_bytes()) != item["bytes"]
               or sha((LAB / item["path"]).read_bytes()) != item["sha256"]]
    assert before == after and not changed
    baseline = read(INTAKE / "source-baseline.json")
    source_state = {"head": git("rev-parse", "HEAD").decode().strip(),
                    "branch": git("branch", "--show-current").decode().strip(),
                    "status": git("status", "--porcelain=v1").decode().strip(),
                    "source_written_by_controller": False,
                    "temp_root_entries": sorted(p.name for p in (SOURCE / ".temp-roots").iterdir())
                        if (SOURCE / ".temp-roots").exists() else []}
    assert source_state["head"] == baseline["head"] == RECEIVED
    assert source_state["branch"] == baseline["branch"] and not source_state["status"]
    original = read(INTAKE / "worker/artifacts.json")
    artifact_checks = []
    for item in original["files"]:
        raw = (SOURCE / item["path"]).read_bytes()
        artifact_checks.append({"path": item["path"], "bytes": len(raw), "sha256": sha(raw),
                               "matched": len(raw) == item["bytes"] and sha(raw) == item["worktree_sha256"]})
    assert len(artifact_checks) == 141 and all(item["matched"] for item in artifact_checks)
    save(INTAKE / "artifact-verification-after-tests.json", artifact_checks)
    save(INTAKE / "source-after-tests.json", source_state)
    snapshot_paths = {row["path"] for row in read(OWN / "snapshot.json")}
    generated = []
    for path in (LAB / "docs/handoff/EVID-LAB-01/logs/second-remediation-2026-10-08").glob("cleanup-receipt-p*.json"):
        if path.relative_to(LAB).as_posix() not in snapshot_paths:
            body = read(path)
            assert body["verified_absent"] and not body["gaps"]
            target = OUT / "generated-test-cleanup" / path.name
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(path.read_bytes())
            generated.append({"path": target.relative_to(INTAKE).as_posix(), "root": body["root"],
                              "files_reported": body.get("file_count"), "root_absent": not Path(body["root"]).exists()})
    worker_receipts = []
    for path in (INTAKE / "worker/logs/second-remediation-2026-10-08").glob("cleanup-receipt-p*.json"):
        body = read(path)
        worker_receipts.append({"path": path.relative_to(INTAKE).as_posix(), "verified_absent_claim": body["verified_absent"],
                                "root_currently_absent": not Path(body["root"]).exists(), "gaps": body["gaps"],
                                "file_count": body.get("file_count"), "individual_manifest_in_receipt": "files" in body})
    save(INTAKE / "worker-cleanup-evidence-note.json", {"receipts": worker_receipts,
        "limits": "Receipts retain aggregate manifest SHA, not the individual file/SHA list or hardlink/process/port proof. Current absence does not independently prove historical deletion. Previous nul/shared-TEMP provenance limits stay open; controller cleanup applies only to its own root."})
    links = []
    for directory, dirs, files in os.walk(OWN, followlinks=False):
        for name in list(dirs) + files:
            entry = Path(directory) / name
            info = entry.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                links.append(str(entry))
                if name in dirs:
                    dirs.remove(name)
    assert not links
    save(INTAKE / "junction-inventory.json", {"absolute_root": str(OWN), "links": []})
    result.update(status="finite_lr02b_software_scope_verified", original_inputs_after=after,
        input_bytes_unchanged=True, snapshot_changed_after_all_cases=changed, snapshot_changes_after_tests=changed,
        worker_repository_written=False, source_repository_writes=0, paid_api_requests=0, browser={"ports": []},
        corrected_archive_binding_tests=corrected, original_four_public_cases=binding["checks"],
        regression={"prior_methods_passed": 108, "initial_controller_setup_errors": 10, "new_methods_corrected_passed": 10,
                    "unique_methods_passed_across_disjoint_batches": 118},
        generated_test_cleanup_receipts=generated, source_after=source_state, remaining_findings=[],
        review_status="one_concentrated_independent_review_completed", lr02b_software_closed=True,
        whole_project_gates_closed=False, not_closed=["fact/score accuracy", "human gold", "L02 full calibration", "G3", "F05", "TH-IMPL-01", "IN-IMPL-01", "L03"],
        proposal_status="draft_not_signed_not_executed", cleanup_pending=True)
    save(OUT / "result.json", result)
    print(json.dumps({"regression_unique_passed": 118, "original_public_cases": 4,
                      "normal_batch_commands": 40, "catalog_fixture_count": 34, "records": 350,
                      "input_unique_files_unchanged": len(before), "snapshot_unchanged": 142,
                      "source_artifacts_unchanged": 141, "generated_cleanup_receipts": len(generated)}))


if __name__ == "__main__":
    main()
