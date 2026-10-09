"""Freeze actual OS CLI progress and original failures, no source publication."""
import argparse
import ast
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import checkpoint_09 as previous
from checkpoint_07_resume import verify_blobs

IQS, CONTROL, OUT, OWN = previous.IQS, previous.CONTROL, previous.OUT, previous.OWN
BASELINE = "eb2fb493a1b0014f6113cde23b4e1421262c6ed4"
INDEX = OUT / "checkpoint-index-10.json"
MANIFEST = OWN / "checkpoint-paths-10.nul"
LABELS = (
    "os-public-cold-first-01", "os-public-cold-red-02", "os-public-cold-green-01",
    "os-public-interruption-first-01", "os-public-recovery-affected-green-01",
    "os-public-complete-seal-first-01", "os-public-complete-seal-green-01",
    "os-public-complete-seal-green-02", "os-public-automatic-recovery-red-01",
    "os-public-automatic-recovery-affected-green-01",
)
sha, git = previous.sha, previous.git


def immutable_inputs():
    previous.immutable_inputs()
    path = OUT / "checkpoint-index-09.json"
    assert git("show", "HEAD:" + path.relative_to(IQS).as_posix()) == path.read_bytes()
    for record in json.loads(path.read_text("utf-8"))["records"]:
        assert sha((IQS / record["path"]).read_bytes()) == record["sha256"], record["path"]


def prepare():
    assert git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not git("diff", "--cached", "--name-only").strip()
    assert not INDEX.exists() and not MANIFEST.exists()
    immutable_inputs()
    scope = set(json.loads((CONTROL / "scope.json").read_text("utf-8"))["files"])
    assert len(scope) == 38
    latest = json.loads((OUT / "verification" / LABELS[-1] / "process.json").read_text("utf-8"))
    assert latest["returncode"] == 0 and len(latest["executed_source_hashes"]) == 37
    for name, digest in latest["executed_source_hashes"].items():
        assert sha((OWN / "qa" / name).read_bytes()) == digest, name
    old = json.loads((OUT / "checkpoint-index-09.json").read_text("utf-8"))["latest_executed_source_hashes"]
    assert {name for name, digest in old.items() if latest["executed_source_hashes"][name] != digest} == {
        "src/config/quick_scan_search_policy.py", "src/runners/llm_runner.py", "tests/integration/test_external_context_cli_e2e.py"}
    support = 0
    for record in json.loads((OUT / "source-snapshot.json").read_text("utf-8")):
        if record["path"] not in scope:
            assert sha((OWN / "qa" / record["path"]).read_bytes()) == record["sha256"], record["path"]
            support += 1
    tracked = set(git("ls-files", "-z").decode("utf-8").split("\0"))
    paths, batches = [], []
    for label in LABELS:
        root = OUT / "verification" / label
        process = json.loads((root / "process.json").read_text("utf-8"))
        assert not process["timeout"] and process["executed_source_unchanged"], label
        for name, digest in process["executed_source_hashes"].items():
            assert sha((root / "executed-source" / name).read_bytes()) == digest, (label, name)
        suite = ET.parse(root / "junit.xml").getroot().find("testsuite")
        counts = {key: int(suite.attrib[key]) for key in ("tests", "failures", "errors", "skipped")}
        if process["returncode"] == 0:
            assert counts["failures"] == counts["errors"] == 0
        children = json.loads((root / "subprocess/index.json").read_text("utf-8"))
        assert children["process_sha256"] == sha((root / "process.json").read_bytes())
        for case in children["cases"]:
            for record in case["records"]:
                assert sha((root / record["path"]).read_bytes()) == record["sha256"]
        batches.append({"label": label, "returncode": process["returncode"], "wall_s": process["wall_s"],
            "junit": counts, "cases_with_allowed_logs_not_os_case_count": len(children["cases"])})
        paths.extend(p for p in root.rglob("*") if p.is_file())
    assert batches[-1]["junit"] == dict(tests=313, failures=0, errors=0, skipped=0)
    paths += [Path(__file__).resolve(), CONTROL / "archive_os_cli.py", CONTROL / "archive_os_cli_additions.py",
        CONTROL / "record_cli_progress.py", CONTROL / "cli-recovery-interface.md"]
    records = []
    for path in sorted(paths):
        assert not path.is_symlink()
        name, raw = path.relative_to(IQS).as_posix(), path.read_bytes()
        assert name not in tracked, name
        if path.suffix == ".py":
            ast.parse(raw.decode("utf-8"), filename=name)
        elif path.suffix == ".json":
            json.loads(raw)
        records.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
    document = {"phase": 111, "state": "private_os_cli_scope_verified_not_source_published", "iqs_baseline": BASELINE,
        "source_head": previous.previous.previous.earlier.SOURCE,
        "production_schema_version": 8, "private_schema_version": 13,
        "scope_paths": 38, "executed_paths": 37, "support_files_unchanged": support,
        "test_batches": batches, "latest_executed_source_hashes": latest["executed_source_hashes"], "records": records,
        "actual_os_integration_instances": 24, "actual_termination_positions": 11,
        "pending": ["final_static_whole_affected_regression_and_concentrated_review", "source_publish", "strict_cleanup"],
        "production_published": False, "whole_project_gates_closed": False}
    INDEX.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    selected = [*previous.previous.previous.earlier.ROOT_PATHS, *(r["path"] for r in records), INDEX.relative_to(IQS).as_posix()]
    assert len(selected) == len(set(selected))
    MANIFEST.write_bytes(b"\0".join(n.encode("utf-8") for n in selected) + b"\0")
    print(json.dumps({"artifacts": len(records), "selected": len(selected), "batches": len(batches), "support": support,
        "latest_passed": 313, "production_published": False}))


def publish():
    assert git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not git("diff", "--cached", "--name-only").strip()
    immutable_inputs()
    document = json.loads(INDEX.read_text("utf-8"))
    records = list(document["records"])
    for record in records:
        raw = (IQS / record["path"]).read_bytes()
        assert len(raw) == record["bytes"] and sha(raw) == record["sha256"], record["path"]
    raw = INDEX.read_bytes()
    records.append({"path": INDEX.relative_to(IQS).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
    selected = MANIFEST.read_bytes().split(b"\0")[:-1]
    assert len(selected) == len(set(selected))
    assert all(b"opencode" not in n and not n.startswith(b"runs/") for n in selected)
    tracked = set(git("ls-files", "-z").split(b"\0"))
    changed = set(git("diff", "--name-only", "-z").split(b"\0")) - {b""}
    assert changed <= set(selected), changed - set(selected)
    expected = changed | (set(selected) - tracked)
    git("add", "-f", "--pathspec-from-file=" + str(MANIFEST), "--pathspec-file-nul")
    actual = set(git("diff", "--cached", "--name-only", "-z").split(b"\0")[:-1])
    assert actual == expected
    verify_blobs(":", records)
    git("diff", "--cached", "--check")
    git("commit", "-m", "feat: verify subprocess external search and automatic recovery")
    git("push", "origin", "HEAD:master")
    assert git("rev-parse", "HEAD") == git("rev-parse", "origin/master")
    verify_blobs("HEAD:", records)
    previous.previous.previous.earlier.source_unchanged()
    print(json.dumps({"commit": git("rev-parse", "HEAD").decode().strip(), "artifacts": len(document["records"]),
        "selected": len(selected), "changed": len(actual), "status": git("status", "--porcelain=v1").decode("utf-8"),
        "production_published": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "git"])
    prepare() if parser.parse_args().mode == "prepare" else publish()
