"""Freeze the actual dispatch/text/native-event slice; no producer publication.

One prepare at the exact baseline, then normal Git using the fixed manifest.
Never run the old helpers, overwrite old logs, or count overlapping batches.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import checkpoint_05 as earlier

IQS, CONTROL, OUT, OWN = earlier.IQS, earlier.CONTROL, earlier.OUT, earlier.OWN
BASELINE = "d2f6281815261e0a18b8a36d5e5e73e6b0375396"
INDEX = OUT / "checkpoint-index-07.json"
MANIFEST = OWN / "checkpoint-paths-07.nul"
LABELS = (
    "runner-dispatch-red-01", "runner-dispatch-red-02", "runner-dispatch-green-01", "runner-dispatch-green-02",
    "public-dispatch-red-01", "public-dispatch-red-02", "public-dispatch-green-01", "public-dispatch-green-02",
    "public-dispatch-green-03", "public-dispatch-adjacent-red-01", "public-dispatch-adjacent-green-01",
    "external-text-red-01", "public-time-binding-red-01", "external-text-green-01", "external-text-green-02",
    "external-events-green-01", "external-events-green-02", "native-events-migration-red-01",
    "native-events-runtime-affected-green-01",
)
CONSUMER_PATHS = (
    "scripts/stockqa_adapter.py", "scripts/routing.py", "schemas/quick_scan/route-decision.schema.json",
    "tests/test_external_search_result_contract.py", "tests/test_question_sets.py",
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def immutable_inputs():
    earlier.source_unchanged()
    earlier.previous_unchanged()  # 01-04, preserving mutable-plan history at its commit.
    for number in ("05", "06"):
        index = OUT / ("checkpoint-index-" + number + ".json")
        assert earlier.git("show", "HEAD:" + index.relative_to(IQS).as_posix()) == index.read_bytes()
        for record in json.loads(index.read_text("utf-8"))["records"]:
            assert sha((IQS / record["path"]).read_bytes()) == record["sha256"], record["path"]
    executed = json.loads((OUT / "verification/native-cli-fixture-green-01/process.json").read_text("utf-8"))["executed_iqs_source_hashes"]
    for name in CONSUMER_PATHS:
        raw = (IQS / name).read_bytes()
        assert sha(raw) == executed[name], name
        committed = earlier.git("show", BASELINE + ":" + name)
        if name == "schemas/quick_scan/route-decision.schema.json":
            assert committed.replace(b"\r\n", b"\n") == raw.replace(b"\r\n", b"\n"), name
        else:
            assert committed == raw, name


def prepare():
    assert earlier.git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not earlier.git("diff", "--cached", "--name-only").strip()
    assert not INDEX.exists() and not MANIFEST.exists()
    immutable_inputs()
    latest = json.loads((OUT / "verification" / LABELS[-1] / "process.json").read_text("utf-8"))
    assert latest["returncode"] == 0 and not latest["timeout"] and latest["executed_source_unchanged"]
    assert len([v for v in latest["command"] if v.startswith("tests/")]) == 16
    for name, digest in latest["executed_source_hashes"].items():
        assert sha((OWN / "qa" / name).read_bytes()) == digest, name
    scope = set(json.loads((CONTROL / "scope.json").read_text("utf-8"))["files"])
    assert len(scope) == 36
    support = 0
    for record in json.loads((OUT / "source-snapshot.json").read_text("utf-8")):
        if record["path"] not in scope:
            assert sha((OWN / "qa" / record["path"]).read_bytes()) == record["sha256"], record["path"]
            support += 1
    tracked = set(earlier.git("ls-files", "-z").decode("utf-8").split("\0"))
    paths, batches = [], []
    for label in LABELS:
        root = OUT / "verification" / label
        process = json.loads((root / "process.json").read_text("utf-8"))
        assert process["executed_source_unchanged"] and not process["timeout"], label
        for name, digest in process["executed_source_hashes"].items():
            assert sha((root / "executed-source" / name).read_bytes()) == digest, (label, name)
        suite = ET.parse(root / "junit.xml").getroot().find("testsuite")
        assert suite is not None
        counts = {key: int(suite.attrib[key]) for key in ("tests", "failures", "errors", "skipped")}
        if process["returncode"] == 0:
            assert all(counts[key] == 0 for key in ("failures", "errors")), label
        batches.append({"label": label, "returncode": process["returncode"], "timeout": process["timeout"],
            "wall_s": process["wall_s"], "junit": counts})
        paths.extend(path for path in root.rglob("*") if path.is_file())
    assert batches[-1]["junit"] == dict(tests=776, failures=0, errors=0, skipped=0)
    paths += [Path(__file__).resolve(), CONTROL / "runtime-dispatch-interface.md"]
    records = []
    for path in sorted(paths):
        assert not path.is_symlink()
        name, raw = path.relative_to(IQS).as_posix(), path.read_bytes()
        assert name not in tracked, name
        if path.suffix == ".json":
            json.loads(raw)
        elif path.suffix == ".py":
            ast.parse(raw.decode("utf-8"), filename=name)
        records.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
    document = {
        "phase": 111, "state": "in_progress_private_implementation_not_published", "iqs_baseline": BASELINE,
        "source_head": earlier.SOURCE, "production_schema_version": 8, "private_schema_version": 12,
        "private_checkpoint_version": 2, "public_result_version_private_producer": "1.1.0",
        "scope_paths": 36, "support_files_unchanged": support, "test_batches": batches,
        "latest_executed_source_hashes": latest["executed_source_hashes"],
        "consumer_unchanged_since_checkpoint06": {name: sha((IQS / name).read_bytes()) for name in CONSUMER_PATHS},
        "consumer_committed_byte_hashes": {name: sha(earlier.git("show", BASELINE + ":" + name)) for name in CONSUMER_PATHS},
        "consumer_byte_domains": "working bytes match actual checkpoint06 execution; route-decision JSON Git LF and working CRLF hashes are distinct, with exact LF-normalized equality",
        "records": records, "pending": ["two_stage_recovery", "cross_lease_recovery", "mcp_each_http",
            "os_subprocess_public_cli", "final_static_and_concentrated_review", "source_publish", "strict_cleanup"],
        "whole_project_gates_closed": False,
    }
    INDEX.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    selected = [*earlier.ROOT_PATHS, *(record["path"] for record in records), INDEX.relative_to(IQS).as_posix()]
    assert len(selected) == len(set(selected))
    MANIFEST.write_bytes(b"".join(name.encode("utf-8") + b"\0" for name in selected))
    print(json.dumps({"artifacts": len(records), "selected": len(selected), "batches": len(batches),
        "support": support, "production_published": False}))


def publish():
    assert earlier.git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not earlier.git("diff", "--cached", "--name-only").strip()
    immutable_inputs()
    document = json.loads(INDEX.read_text("utf-8"))
    selected = MANIFEST.read_bytes().split(b"\0")[:-1]
    assert len(selected) == len(set(selected))
    assert all(b"opencode" not in name and not name.startswith(b"runs/") for name in selected)
    for record in document["records"]:
        raw = (IQS / record["path"]).read_bytes()
        assert len(raw) == record["bytes"] and sha(raw) == record["sha256"], record["path"]
    tracked = set(earlier.git("ls-files", "-z").split(b"\0"))
    changed = set(earlier.git("diff", "--name-only", "-z", "--", *(name.decode("utf-8") for name in selected)).split(b"\0")) - {b""}
    expected = changed | (set(selected) - tracked)
    earlier.git("add", "-f", "--pathspec-from-file=" + str(MANIFEST), "--pathspec-file-nul")
    assert set(earlier.git("diff", "--cached", "--name-only", "-z").split(b"\0")[:-1]) == expected
    for record in document["records"]:
        assert sha(earlier.git("show", ":" + record["path"])) == record["sha256"], record["path"]
    assert earlier.git("show", ":" + INDEX.relative_to(IQS).as_posix()) == INDEX.read_bytes()
    earlier.git("diff", "--cached", "--check")
    earlier.git("commit", "-m", "feat: freeze external dispatch and native event recovery progress")
    earlier.git("push", "origin", "HEAD:master")
    assert earlier.git("rev-parse", "HEAD") == earlier.git("rev-parse", "origin/master")
    for record in document["records"]:
        assert sha(earlier.git("show", "HEAD:" + record["path"])) == record["sha256"], record["path"]
    earlier.source_unchanged()
    print(json.dumps({"commit": earlier.git("rev-parse", "HEAD").decode().strip(),
        "artifacts": len(document["records"]), "selected": len(selected), "changed": len(expected),
        "status": earlier.git("status", "--porcelain=v1").decode("utf-8"), "production_published": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "git"])
    prepare() if parser.parse_args().mode == "prepare" else publish()
