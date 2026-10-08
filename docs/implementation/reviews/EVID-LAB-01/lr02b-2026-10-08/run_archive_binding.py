"""One isolated public-CLI batch for the review's historical source-lock boundary."""
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/evid-lab-lr02b-2026-10-08-01"
LAB = OWN / "lab"
INTAKE = IQS / "docs/implementation/intake/EVID-LAB-01/2026-10-08-lr02b"
OUT = INTAKE / "verification/archive-binding"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, body):
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    previous = read(INTAKE / "verification/result.json")
    OUT.mkdir(exist_ok=False)
    clone = OWN / "locked-input-copy-boundary"
    clone.mkdir(exist_ok=False)
    before = previous["original_inputs_before"]
    for relative, expected in before.items():
        source = IQS / relative
        data = source.read_bytes()
        assert digest(data) == expected, "Original input drift before copy"
        target = clone / relative
        assert clone in target.resolve().parents, "Copy path escaped"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        assert digest(target.read_bytes()) == expected

    env = {k: v for k, v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE",
        "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "SYSTEMDRIVE"}}
    env.update(PYTHONPATH=os.pathsep.join([str(OWN / "guard"), str(LAB / "src")]),
               PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               TEMP=str(OWN / "tmp"), TMP=str(OWN / "tmp"), TMPDIR=str(OWN / "tmp"),
               E97_OWNED_ROOT=str(OWN.resolve()), E97_LAB_ROOT=str(LAB),
               IQS_EVIDENCE_LAB_IQS_ROOT=str(clone))
    root = LAB / ".controller-archive-binding"
    root.mkdir(exist_ok=False)
    original = read(LAB / "fixtures/historical/FX-032.json")
    intact = copy.deepcopy(original)
    intact["provenance"].pop("answer_sha256", None)
    modified = copy.deepcopy(intact)
    modified["case"]["answer"]["score"] = 1
    modified["case"]["answer"]["rationale"] = "Synthetic acceptance mutation of copied historical answer"
    checks = []

    def run(name, args, target, expected_exit):
        start = time.monotonic()
        command = [sys.executable, "-B", "-X", "utf8", "-m", "iqs_evidence_lab", *args]
        try:
            process = subprocess.run(command, cwd=LAB, env=env, capture_output=True, timeout=180)
        except subprocess.TimeoutExpired as exc:
            process = subprocess.CompletedProcess(command, 124, exc.stdout or b"", exc.stderr or b"")
        (OUT / (name + ".stdout.log")).write_bytes(process.stdout)
        (OUT / (name + ".stderr.log")).write_bytes(process.stderr)
        row = {"name": name, "command": command, "returncode": process.returncode,
               "expected_exit": expected_exit, "published": target.exists(),
               "wall_s": round(time.monotonic() - start, 3),
               "stdout_sha256": digest(process.stdout), "stderr_sha256": digest(process.stderr)}
        if target.exists():
            for child in sorted(target.iterdir()):
                if child.is_file():
                    (OUT / (name + "-" + child.name)).write_bytes(child.read_bytes())
            row["summary"] = read(target / "summary.json")
        row["expectation_met"] = process.returncode == expected_exit and target.exists() == (expected_exit == 0)
        checks.append(row)
        print(json.dumps({k: row[k] for k in ("name", "returncode", "expected_exit", "published", "expectation_met")}), flush=True)

    def fixture_run(name, body, expected_exit):
        path = root / (name + "-input.json")
        save(path, body)
        (OUT / path.name).write_bytes(path.read_bytes())
        target = root / (name + "-output")
        run(name, ["replay", "--input", str(path), "--output", str(target)], target, expected_exit)

    fixture_run("archive-intact-optional-hash-omitted", intact, 0)
    fixture_run("fixture-only-tamper", modified, 4)

    prov = original["provenance"]
    archive_relative = "docs/implementation/experiments/artifacts/" + prov["run"] + "/results.jsonl"
    archive = clone / archive_relative
    archive_before = archive.read_bytes()
    rows = [json.loads(line) for line in archive_before.decode("utf-8-sig").splitlines() if line.strip()]
    matched = 0
    for row in rows:
        if row["chunk_id"] == prov["chunk_id"]:
            for position, answer in enumerate(row["answers"]):
                if answer["question_id"] == prov["question_id"]:
                    row["answers"][position] = copy.deepcopy(modified["case"]["answer"])
                    matched += 1
    assert matched == 1
    archive.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    archive_after = archive.read_bytes()
    assert digest(archive_before) == before[archive_relative] and digest(archive_after) != before[archive_relative]
    fixture_run("archive-and-fixture-tamper", modified, 2)
    index_target = root / "drifted-index-output"
    run("index-rejects-same-archive-drift", ["replay", "--input", "index", "--output", str(index_target)], index_target, 2)

    original_after = {relative: digest((IQS / relative).read_bytes()) for relative in before}
    snapshot_changed = [item["path"] for item in read(OWN / "snapshot.json")
                        if digest((LAB / item["path"]).read_bytes()) != item["sha256"]]
    clone_changed = [relative for relative, expected in before.items()
                     if digest((clone / relative).read_bytes()) != expected]
    body = {"schema": "iqs_evid_lab_archive_binding_counterexample/1", "checks": checks,
            "copied_input_files": len(before), "copy_initially_byte_identical": True,
            "clone_changed_paths": clone_changed, "lock_bytes_unchanged":
                "docs/implementation/parallel-lanes/packages/2026-10-07-wave2/inputs.lock.json" not in clone_changed,
            "archive_mutation": {"relative_path": archive_relative, "chunk_id": prov["chunk_id"],
                                 "question_id": prov["question_id"], "original_sha256": digest(archive_before),
                                 "modified_sha256": digest(archive_after)},
            "original_inputs_unchanged": original_after == before, "snapshot_changed": snapshot_changed,
            "worker_repository_written": False, "paid_calls": 0, "downloads": 0,
            "not_historical_or_human_gold": True, "cleanup_pending": True}
    save(OUT / "archive-binding-result.json", body)
    previous.update(original_inputs_after=original_after, input_bytes_unchanged=original_after == before,
                    snapshot_changed_after_all_cases=snapshot_changed,
                    additional_case_result="archive-binding/archive-binding-result.json")
    save(INTAKE / "verification/result.json", previous)
    assert original_after == before and not snapshot_changed and clone_changed == [archive_relative]
    assert all(row["expectation_met"] for row in checks), "Public archive-binding expectation failed"
    assert not list((LAB/".temp-roots").glob("staging-*")), "Staging residue after failed entry"


if __name__ == "__main__":
    main()
