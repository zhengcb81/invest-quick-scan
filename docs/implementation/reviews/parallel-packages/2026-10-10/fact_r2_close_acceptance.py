"""Preserve one FACT R2 milestone result, then remove its exact owned copies."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r2_controller", HERE / "fact_r2_acceptance_run.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
assert c.WORK.resolve() == c.ROOT / "runs/fc2a"
assert json.loads((c.WORK / "ownership.json").read_text(encoding="utf-8"))["root"] == str(c.WORK)
assert not (c.INTAKE / "cleanup-01.json").exists()
state = c.git_state()
assert state[0]["stdout"].strip() == c.EXPECTED and not state[2]["stdout"].strip()
c.old.write(c.INTAKE / "source-git-after-01.json", state)
frozen = json.loads((c.INTAKE / "source-freeze-01.json").read_text(encoding="utf-8"))
changed = []
for entry in frozen["files"]:
    p = c.SOURCE / entry["path"]
    c.old.safe(p)
    if p.stat().st_size != entry["bytes"] or c.old.digest(p) != entry["sha256"]:
        changed.append(entry["path"])
assert not changed, changed
inputs = c.old.inspect_inputs()
records = [json.loads(p.read_text(encoding="utf-8"))
           for p in (c.INTAKE / "logs").glob("*.result.json")]
assert records and all(r["terminal"] and not r["timed_out"] for r in records)
cim = json.loads((c.INTAKE / "cim-terminal-01.json").read_text(encoding="utf-8-sig"))
assert cim["examined"] == "successful read-only CIM query" and cim["matching_count"] == 0
report = json.loads((c.LAB / ".acceptance-followup/results.json").read_text(encoding="utf-8"))
c.old.write(c.INTAKE / "counterexample-original-assessments-01.json", report)
probe = next(r for r in report["cases"] if r["case"] == "FC19-legacy-nested-fake-key")
control = next(r for r in report["cases"] if r["case"] == "FC18-legacy-neutral-control")
assert control["passed"] and probe["actual"]["exit_code"] == 6
assert "secret-like path component rejected" in probe["actual"]["stderr"]
# Preserve the controller's incorrect marker assertion. Native CLI correctly
# rejected the neutral-root, true-legacy nested path; no re-execution is needed.
c.old.write(c.INTAKE / "counterexample-marker-correction-01.json", {
    "case": probe["case"], "original_controller_passed": False,
    "reason": "controller required echoed filename or 'forbidden'; actual sanitized guard uses 'secret-like path component rejected'",
    "original_result": probe, "normal_control": control, "corrected_assessment": "passed",
    "process_stdout_sha256": next(r["stdout_sha256"] for r in records
                                   if "fact_r2_counterexamples.py" in r["command"][-1]
                                   and r["exit_code"] == 0), "new_execution": False})
effective = [r for r in report["cases"] if r["passed"] or r["case"] == probe["case"]]
failures = [r for r in report["cases"] if r not in effective]
assert {r["case"] for r in failures} == {
    "FC16-nonprimary-future-context", "FC17-future-unknown-exploration"}
suites = list(ET.parse(c.INTAKE / "fact-r2-regression-02.xml").getroot().iter("testsuite"))
counts = {k: sum(int(s.attrib[k]) for s in suites)
          for k in ["tests", "failures", "errors", "skipped"]}
assert counts == {"tests": 135, "failures": 0, "errors": 0, "skipped": 0}
received = c.INTAKE / "received-handoff"
assert not received.exists()
for p in (c.LAB / c.HANDOFF).rglob("*"):
    c.old.safe(p)
    if p.is_file():
        dst = received / p.relative_to(c.LAB / c.HANDOFF)
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("xb") as f:
            f.write(p.read_bytes())
        assert c.old.digest(dst) == c.old.digest(p)

# The only remaining deliberately created reparse object is removed as a link,
# never traversed during recursive inventory/deletion.
link = c.LAB / ".acceptance-cases/junction/linked"
target = c.LAB / ".acceptance-cases/junction-target"
c.old.safe(link.parent)
c.old.safe(target)
assert link.lstat().st_file_attributes & 0x400
assert link.resolve() == target.resolve()
target_sha = c.old.digest(target / "semantic-cases.json")
c.old.write(c.INTAKE / "junction-cleanup-01.json", {
    "link": str(link), "target": str(target), "target_sha256": target_sha,
    "operation": "os.rmdir removes only the owned junction"})
os.rmdir(link)
assert not link.exists() and c.old.digest(target / "semantic-cases.json") == target_sha
files, directories = [], []
for p in c.WORK.rglob("*"):
    c.old.safe(p)
    if p.is_file():
        files.append({"path": p.relative_to(c.WORK).as_posix(),
                      "bytes": p.stat().st_size, "sha256": c.old.digest(p)})
    elif p.is_dir():
        directories.append(p.relative_to(c.WORK).as_posix())
    else:
        raise RuntimeError(f"unexpected owned object: {p}")
c.old.safe(c.WORK)
c.old.write(c.INTAKE / "cleanup-inventory-01.json", {
    "root": str(c.WORK), "files": files, "directories": directories})
assert {p.relative_to(c.WORK).as_posix() for p in c.WORK.rglob("*") if p.is_file()} == {
    e["path"] for e in files}
for e in files:
    p = c.WORK / e["path"]
    c.old.safe(p)
    assert p.stat().st_size == e["bytes"] and c.old.digest(p) == e["sha256"]
for e in files:
    (c.WORK / e["path"]).unlink()
for rel in sorted(directories, key=lambda p: len(Path(p).parts), reverse=True):
    (c.WORK / rel).rmdir()
c.WORK.rmdir()
c.old.write(c.INTAKE / "acceptance-result-01.json", {
    "at": c.old.now(), "package_id": "FACT-CONTENT-01", "coordinator_acceptance": "changes_requested",
    "head": c.EXPECTED, "product_commit": c.PRODUCT,
    "source_files_unchanged": len(frozen["files"]), "inputs": inputs,
    "artifact_matches": sum(x["matches"] for x in frozen["artifacts"]),
    "artifact_count": len(frozen["artifacts"]), "handoff_state": "present_manifest_inconsistent",
    "regression": counts, "independent_cli_cases": len(report["cases"]),
    "original_controller_expectations_matched": sum(r["passed"] for r in report["cases"]),
    "effective_cli_expectations_met": len(effective), "failed_cases": failures,
    "marker_correction": "counterexample-marker-correction-01.json",
    "eight_original_mechanical_gaps_closed": True, "legacy_public_read_present": True,
    "three_content_findings_corrected_static_review": True,
    "legacy_worker_nested_path_test_masked_by_parent_path": True,
    "processes": records, "paid_api_requests": 0, "company_document_downloads": 0,
    "source_written": False, "global_gates_closed": False})
c.old.write(c.INTAKE / "cleanup-01.json", {
    "at": c.old.now(), "owned_root": str(c.WORK), "files_removed": len(files),
    "directories_removed_including_root": len(directories) + 1,
    "junction_removed_without_traversal": True, "source_changed": changed,
    "strict_set_lstat_single_link_bytes_sha_verified": True,
    "verified_absent": not c.WORK.exists(), "c06_or_shared_temp_deleted": False})
print(json.dumps({"acceptance": "changes_requested", "regression": counts,
                  "cli_cases": len(report["cases"]), "cli_matched": len(effective),
                  "failed": [r["case"] for r in failures], "cleaned": not c.WORK.exists(),
                  "files_removed": len(files)}, ensure_ascii=False))
