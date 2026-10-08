"""Collect the finite SR02-4B acceptance without following any test junction."""
import json
import os
import re
import stat
from pathlib import Path

from prepare import INTAKE, IQS, OWN, RECEIVED, SOURCE, git, save, sha

OUT = INTAKE / "verification"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def main():
    commands = read(OUT / "commands.json")
    corrected = read(OUT / "cli-corrected.result.json")
    assert all(row["returncode"] == 0 for row in commands["checks"][:3])
    assert commands["checks"][3]["returncode"] == 1 and corrected["returncode"] == 0
    for name, count in (("core", 43), ("utf8", 2)):
        log = (OUT / (name + ".stdout.log")).read_text("utf-8")
        assert re.search(rf"\b{count} passed\b", log), name
    cli = read(OWN / "public-cli-result.json")
    assert len(cli["checks"]) == 7
    assert sum(row["returncode"] == 0 for row in cli["checks"]) == 4
    assert sum(row["returncode"] == 2 for row in cli["checks"]) == 3
    (OUT / "public-cli-result.json").write_bytes((OWN / "public-cli-result.json").read_bytes())
    for path in (OWN / "logs").glob("*.log"):
        target = OUT / "public-cli" / path.name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(path.read_bytes())
    for name in ("public_cli_cases.py", "guard/sitecustomize.py"):
        (OUT / Path(name).name).write_bytes((OWN / name).read_bytes())
    counterexamples = INTAKE / "counterexamples"
    counterexamples.mkdir(exist_ok=True)
    count = 0
    for path in (OWN / "pytest-utf8").rglob("corrupt-manifest-result.json"):
        if any(getattr(parent.lstat(), "st_file_attributes", 0) & 0x400 for parent in path.parents if parent.is_relative_to(OWN)):
            continue
        body = read(path)
        (counterexamples / (body["operation"] + ".json")).write_bytes(path.read_bytes())
        count += 1
    assert count == 2
    snapshot = read(OWN / "export-manifest.json")
    changed = [row["path"] for row in snapshot
               if len((OWN / "runtime" / row["path"]).read_bytes()) != row["bytes"]
               or sha((OWN / "runtime" / row["path"]).read_bytes()) != row["sha256"]]
    before = read(OUT / "iqs-input-before.json")
    after = {relative: sha((IQS / relative).read_bytes()) for relative in before}
    assert before == after and not changed
    manifest = read(INTAKE / "worker/artifacts.json")
    source_rows = []
    for row in manifest["items"]:
        raw = (SOURCE / row["path"]).read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"]
        source_rows.append({"path": row["path"], "bytes": len(raw), "sha256": sha(raw)})
    assert len(source_rows) == 75
    save(INTAKE / "artifact-verification-after-tests.json", source_rows)
    assert git("rev-parse", "HEAD").decode().strip() == RECEIVED
    assert not git("status", "--porcelain=v1")
    # Two referenced R3 receipts were omitted from the worker's 75-item index.
    # Receive these actual owner files separately; do not change the source index.
    supplemental = []
    for name in ("cleanup_receipt_r3.json", "process-listener-final-state-r3.json"):
        relative = "docs/handoff/SW-REPAIR-02/logs/" + name
        raw = (SOURCE / relative).read_bytes()
        blob = git("show", RECEIVED + ":" + relative)
        assert raw.replace(b"\r\n", b"\n") == blob.replace(b"\r\n", b"\n")
        (INTAKE / "worker/logs" / name).write_bytes(raw)
        supplemental.append({"path": relative, "bytes": len(raw), "sha256": sha(raw),
                             "received_git_bytes": len(blob), "received_git_sha256": sha(blob),
                             "received_head": RECEIVED, "indexed_by_worker": False})
    save(INTAKE / "supplemental-artifacts.json", supplemental)
    worker_dry = read(INTAKE / "worker/logs/cleanup-dry-run-r3.json")
    worker_receipt = read(INTAKE / "worker/logs/cleanup_receipt_r3.json")
    nlinks = {}
    for row in worker_dry["files"]:
        key = str(row.get("nlink"))
        nlinks[key] = nlinks.get(key, 0) + 1
    assert worker_receipt["applied"] and worker_dry["totals"]["files"] == 538
    save(INTAKE / "worker-cleanup-evidence-note.json", {
        "r3_receipt_received": True, "r3_root_absent": not Path(worker_receipt["root"]).exists(),
        "r3_worker_reported_deleted_files": 538, "r3_worker_reported_deleted_dirs": 671,
        "r3_dry_run_file_nlink_distribution": nlinks,
        "hardlink_limit": "All recorded nlink values are 0, not 1. The worker's narrative nlink==1 cannot be independently proved from this already-deleted root. Do not reinterpret 0 as one link or backfill the claim.",
        "controller_witnessed_worker_deletion": False,
        "historical_r2_not_performed_and_shared_temp_provenance": "unchanged_open",
    })
    links = []
    for directory, dirs, files in os.walk(OWN, followlinks=False):
        for name in list(dirs) + files:
            path = Path(directory) / name
            info = path.lstat()
            if getattr(info, "st_file_attributes", 0) & 0x400 or stat.S_ISLNK(info.st_mode):
                target = path.resolve(strict=True)
                assert path.is_relative_to(OWN) and target.is_relative_to(OWN)
                links.append({"link": str(path), "target": str(target)})
                if name in dirs:
                    dirs.remove(name)
    assert len(links) == 6
    save(INTAKE / "junction-inventory.json", {"absolute_root": str(OWN), "links": links})
    save(OUT / "result.json", {
        "schema": "iqs_sw_sr02_4b_acceptance/1", "status": "finite_software_scope_verified",
        "result_commit": "cc587a8cf76f2c50a0cdfb4693d3767dfa5944fa", "received_head": RECEIVED,
        "checks": commands["checks"], "controller_corrected_cli": corrected,
        "affected_backup": {"passed": 43}, "original_utf8_counterexamples": {"passed": 2},
        "public_cli": {"checks": 7, "success": 4, "expected_refusals": 3},
        "browser": {"tests_rerun": 0, "ports": []}, "snapshot_files": len(snapshot),
        "snapshot_changes_after_tests": changed, "iqs_input_files": len(before),
        "iqs_inputs_unchanged": before == after, "iqs_inputs_after": after,
        "worker_indexed_artifacts": 75, "supplemental_artifacts": len(supplemental),
        "remaining_software_findings_in_sr02_4b": [], "source_repository_writes": 0,
        "paid_api_requests": 0, "keys_provided": 0, "production_database_reads_or_writes": 0,
        "downloads": 0, "cleanup_pending": True, "whole_project_gates_closed": False,
        "guard_limits": "Python write/network audit and inherited child guards; no full OS read isolation or packet capture claimed",
        "open_items": ["Historical worker R2 cleanup and shared TEMP provenance remain unproved",
            "R3 raw nlink=0 contradicts narrative nlink==1; actual deletion not witnessed by controller",
            "Worker git_blob_sha256 fields are 40-character Git SHA1 OIDs, independently checked as OIDs and true raw SHA256 separately",
            "Same-library query-time multi-variant selection remains unsupported",
            "Real owner identity/facts golden, QA joint flow, G3/F05/TH/IN/L03 stay open"]})
    print(json.dumps({"affected_passed": 43, "old_passed": 2, "public_cli_checks": 7,
                      "snapshot_unchanged": len(snapshot), "iqs_inputs_unchanged": len(before),
                      "junction_nodes": len(links), "worker_nlink_distribution": nlinks}))


if __name__ == "__main__":
    main()
