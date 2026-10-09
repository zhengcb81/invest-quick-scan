"""Freeze non-secret final code, exact synthetic package bytes and source lock.

Run once after all tests/reviewer processes terminate. Does not publish owners.
"""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import platform
import sqlite3
import sys

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/r13a"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-jr13"
FILES = ["stockwiki/quick_scan_import.py", "stockwiki/quick_scan_observations.py",
         "tests/test_quick_scan_observations.py", "tests/test_quick_scan_delivery.py",
         "stockwiki/quick_scan_backup_manifest.py"]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def owned_bytes(path):
    assert path.is_absolute() and path.resolve().is_relative_to(OWN.resolve())
    for component in [path, *path.parents]:
        st = component.lstat()
        assert not getattr(st, "st_file_attributes", 0) & 0x400 and not component.is_symlink()
        if component == OWN:
            break
    assert path.lstat().st_nlink == 1 and path.is_file()
    return path.read_bytes()

def main():
    affected, joint = sys.argv[1:]
    target = OUT / "final-snapshot"
    assert not target.exists()
    src = {n: sha(owned_bytes(OWN / "sw" / n)) for n in FILES}
    for label in [affected, joint]:
        record = json.loads((OUT / label / "process.json").read_bytes())
        assert record["returncode"] == 0 and not record["source_changed_during_test"]
        assert record["source_sha256"] == src
    rows = []
    def save(source, relative, *, expected=None):
        raw = owned_bytes(source)
        if expected is not None:
            assert sha(raw) == expected
        destination = target / relative
        assert destination.resolve().is_relative_to(target.resolve()) and not destination.exists()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        rows.append(dict(path=relative, bytes=len(raw), sha256=sha(raw)))
    for n in FILES:
        save(OWN / "sw" / n, "candidate/" + n, expected=src[n])
    runtime = ["guard/sitecustomize.py", "qa_actor.py", "sw_actor.py", "legacy_qa_actor.py",
               "legacy_sw_actor.py", "joint_harness.py", "test_joint.py", "independent-release.json"]
    for n in runtime:
        save(OWN / n, "executed/" + n)
    base = json.loads((OUT / "joint-input-01.json").read_bytes())
    swbase = json.loads((OUT / "input-01.json").read_bytes())
    qa_rows = list(base["QA_source_files"])
    extra = json.loads((OUT / "joint-dependency-02.json").read_bytes())
    qa_rows.append(dict(path=extra["path"], sha256=extra["sha256"]))
    manifests = json.loads((OUT / "joint-dependency-03.json").read_bytes())
    lock = []
    for owner, entries in [("qa", qa_rows), ("sw", swbase["source_files"])]:
        for entry in entries:
            name = entry["path"]
            raw = owned_bytes(OWN / owner / name)
            expected = entry["sha256"]
            if owner == "sw" and name in src:
                expected = src[name]
            if owner == "qa" and name == "tests/fixtures/quick_scan_c06_manifest_v2_fixture.json":
                expected = manifests["execution_file_sha256"]
                save(OWN / owner / name, "executed/qa-manifest.json", expected=expected)
            assert sha(raw) == expected, "Unexpected dependency drift: " + owner + "/" + name
            lock.append(dict(owner=owner, path=name, bytes=len(raw), sha256=sha(raw)))
    packages = []
    for label in [joint]:
        case = OWN / "cases" / label
        for run, response in [("primary", case / "jr13-cold.response.json"),
                              ("independent-model", case / "j03-independent-cold.response.json")]:
            value = json.loads(owned_bytes(response))
            assert value["cli_exit"] == 0 and len(value["packages"]) == value["http_sends"] == 31
            for qid, package in sorted(value["packages"].items()):
                raw = owned_bytes(Path(package["path"]))
                data = json.loads(raw)
                relative = "synthetic-packages/" + run + "/" + qid + ".json"
                save(Path(package["path"]), relative, expected=sha(raw))
                packages.append(dict(run=run, question_id=qid, path=relative, sha256=sha(raw),
                                     package_id=data["package_id"], synthetic_only=True))
    versions = {}
    for package in ["pytest", "jsonschema", "ruff", "psutil"]:
        versions[package] = importlib.metadata.version(package)
    data = dict(schema="jr13-final-execution-lock/1", candidate_sha256=src,
                source_dependencies=lock, snapshots=rows, packages=packages,
                source_heads=dict(StockWiki=swbase["source_head"], StockQA=base["QA_head"]),
                guard_sha256=base["guard_sha256"], schema_sha256=base["schema_sha256"],
                release_sha256=base["release_sha256"], module_locks=base["module_locks"],
                tests=[affected, joint], Python=platform.python_version(), SQLite=sqlite3.sqlite_version,
                package_versions=versions, synthetic_only=True, real_owner_golden=False,
                paid_API_calls=0, source_written=False, publication="pending_fifth_path_authorization",
                authorized_paths=FILES[:4], conditional_path=FILES[4])
    (target / "execution-lock.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(snapshot_files=len(rows), locked_source_files=len(lock),
                          synthetic_packages=len(packages), source_written=False)))

if __name__ == "__main__":
    main()
