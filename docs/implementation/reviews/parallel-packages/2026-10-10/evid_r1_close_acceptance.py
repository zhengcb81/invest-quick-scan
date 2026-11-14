"""Retain R1 evidence and strictly remove only the controller-owned copy."""
import importlib.util
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("evid_r1_controller", HERE / "evid_r1_acceptance_run.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
assert c.WORK.resolve() == c.ROOT / "runs/p114er1a"
assert json.loads((c.WORK / "ownership.json").read_text(encoding="utf-8"))["root"] == str(c.WORK)
assert not (c.INTAKE / "cleanup.json").exists()
state = c.git_state()
assert state[0]["stdout"].strip() == c.EXPECTED
c.helper.write(c.INTAKE / "source-git-after.json", state)
frozen = json.loads((c.INTAKE / "source-freeze.json").read_text(encoding="utf-8"))
changed = []
for entry in frozen["files"]:
    p = c.SOURCE / entry["path"]
    c.helper.safe(p)
    if p.stat().st_size != entry["bytes"] or c.helper.digest(p) != entry["sha256"]:
        changed.append(entry["path"])
assert not changed, changed
inputs = c.helper.inspect_inputs()
relocation = json.loads((c.INTAKE / "relocated-input-fixture.json").read_text(encoding="utf-8"))
legacy = relocation["legacy_original"]
assert c.helper.digest(Path(legacy["path"])) == legacy["sha256"]
cim = json.loads((c.INTAKE / "cim-terminal-check.json").read_text(encoding="utf-8-sig"))
assert cim["examined"] == "successful read-only CIM query" and cim["matching_count"] == 0
assert cim["recorded_child_pids_still_running"] == []
records = [json.loads(p.read_text(encoding="utf-8")) for p in (c.INTAKE / "logs").glob("*.result.json")]
assert records and all(r["terminal"] and not r["timed_out"] for r in records)

def retain(tree, target):
    assert not target.exists()
    for path in tree.rglob("*"):
        c.helper.safe(path)
        if path.is_file():
            dst = target / path.relative_to(tree)
            dst.parent.mkdir(parents=True, exist_ok=True)
            with dst.open("xb") as stream:
                stream.write(path.read_bytes())
            assert c.helper.digest(path) == c.helper.digest(dst)

retain(c.LAB / ".acceptance-cases", c.INTAKE / "counterexample-fixtures")
handoff = c.LAB / "docs/handoff/EVID-REF-02/remediation-01"
retain(handoff, c.INTAKE / "received-handoff-and-native-outputs")
counts = {}
for name in ("evid-r1-regression.xml", "evid-r1-regression-02.xml"):
    suites = list(ET.parse(c.INTAKE / name).getroot().iter("testsuite"))
    counts[name] = {k: sum(int(s.attrib[k]) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
assert counts["evid-r1-regression-02.xml"] == {"tests": 214, "failures": 64, "errors": 0, "skipped": 0}
cases = json.loads((c.LAB / ".acceptance-cases/results.json").read_text(encoding="utf-8"))
junction = json.loads((c.LAB / ".acceptance-cases/junction-result-02.json").read_text(encoding="utf-8"))
assert not any(r["finding_reproduced"] for r in cases["results"] if r["control"])
assert junction["finding_reproduced"] and junction["junction_removed_without_target_traversal"]
attempts = [p.name for p in (c.WORK / "guard-logs").glob("*.jsonl")]
assert not attempts, attempts

files, dirs = [], []
for path in c.WORK.rglob("*"):
    c.helper.safe(path)
    if path.is_file():
        files.append({"path": path.relative_to(c.WORK).as_posix(), "bytes": path.stat().st_size, "sha256": c.helper.digest(path)})
    elif path.is_dir():
        dirs.append(path.relative_to(c.WORK).as_posix())
    else:
        raise RuntimeError(f"unexpected object: {path}")
c.helper.safe(c.WORK)
c.helper.write(c.INTAKE / "cleanup-inventory.json", {"root": str(c.WORK), "files": files, "directories": dirs})
assert {p.relative_to(c.WORK).as_posix() for p in c.WORK.rglob("*") if p.is_file()} == {e["path"] for e in files}
for entry in files:
    path = c.WORK / entry["path"]
    c.helper.safe(path)
    assert path.stat().st_size == entry["bytes"] and c.helper.digest(path) == entry["sha256"]
for entry in files:
    (c.WORK / entry["path"]).unlink()
for rel in sorted(dirs, key=lambda p: len(Path(p).parts), reverse=True):
    (c.WORK / rel).rmdir()
c.WORK.rmdir()
c.helper.write(c.INTAKE / "acceptance-result.json", {"at": c.helper.now(), "EVID-REF-02-R1": "changes_requested",
    "source_head": c.EXPECTED, "product_commit": c.PRODUCT, "source_files_unchanged": len(frozen["files"]),
    "artifact_hashes_matched": len(frozen["artifacts"]), "inputs": inputs, "regressions": counts,
    "original_copy_regression_not_green": True, "corrected_regression_passed": 150,
    "counterexamples": {"first_group_cases": len(cases["results"]), "native_junction_followup": True,
                       "controls_passed": sum(r["control"] for r in cases["results"]),
                       "distinct_mechanical_findings": 9, "content_findings_static_only": 2},
    "relocated_probes_explicitly_synthetic": True, "handoff_shape_valid_not_acceptance": True,
    "paid_api_requests": 0, "network_attempts": 0, "company_document_downloads": 0,
    "source_written": False, "processes": records, "global_gates_closed": False})
c.helper.write(c.INTAKE / "cleanup.json", {"at": c.helper.now(), "owned_root": str(c.WORK),
    "files_removed": len(files), "directories_removed_including_root": len(dirs) + 1,
    "strict_set_lstat_single_link_bytes_sha_verified": True, "source_changed": changed,
    "verified_absent": not c.WORK.exists(), "c15a_or_shared_temp_deleted": False,
    "junction_removed_without_target_traversal": True})
print(json.dumps({"status": "changes_requested", "source_unchanged": len(frozen["files"]),
    "files_cleaned": len(files), "directories_cleaned": len(dirs) + 1, "owned_root_absent": not c.WORK.exists()}))
