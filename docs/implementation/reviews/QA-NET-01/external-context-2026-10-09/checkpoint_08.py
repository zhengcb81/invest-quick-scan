"""Archive the five actual cross-lease regressions, preserving checkpoint07.

Not a new review gate, source publication or full-project acceptance. Uses
exact manifest writes and one-process Git blob verification from the supplement.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import checkpoint_07 as previous
from checkpoint_07_resume import verify_blobs

IQS, CONTROL, OUT, OWN = previous.IQS, previous.CONTROL, previous.OUT, previous.OWN
BASELINE = "4884e7baa03a2cbda7ba55920c8987032a9f2c88"
INDEX = OUT / "checkpoint-index-08.json"
MANIFEST = OWN / "checkpoint-paths-08.nul"
LABEL = "cross-lease-first-01"
CHANGED_TEST = "tests/unit/test_quick_scan_external_context.py"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def immutable_inputs():
    previous.earlier.source_unchanged()
    for name in ("checkpoint-index-07.json", "checkpoint-07-resume.json"):
        path = OUT / name
        assert previous.earlier.git("show", "HEAD:" + path.relative_to(IQS).as_posix()) == path.read_bytes()
        for record in json.loads(path.read_text("utf-8"))["records"]:
            assert sha((IQS / record["path"]).read_bytes()) == record["sha256"], record["path"]


def prepare():
    assert previous.earlier.git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not previous.earlier.git("diff", "--cached", "--name-only").strip()
    assert not INDEX.exists() and not MANIFEST.exists()
    immutable_inputs()
    root = OUT / "verification" / LABEL
    process = json.loads((root / "process.json").read_text("utf-8"))
    assert process["returncode"] == 0 and not process["timeout"] and process["executed_source_unchanged"]
    old = json.loads((OUT / "verification/native-events-runtime-affected-green-01/process.json").read_text("utf-8"))
    assert set(old["executed_source_hashes"]) == set(process["executed_source_hashes"])
    actual_changes = {name for name, digest in process["executed_source_hashes"].items()
        if digest != old["executed_source_hashes"][name]}
    assert actual_changes == {CHANGED_TEST}, actual_changes
    for name, digest in process["executed_source_hashes"].items():
        assert sha((root / "executed-source" / name).read_bytes()) == digest
        assert sha((OWN / "qa" / name).read_bytes()) == digest
    suite = ET.parse(root / "junit.xml").getroot().find("testsuite")
    counts = {key: int(suite.attrib[key]) for key in ("tests", "failures", "errors", "skipped")}
    assert counts == dict(tests=5, failures=0, errors=0, skipped=0)
    tracked = set(previous.earlier.git("ls-files", "-z").decode("utf-8").split("\0"))
    paths = [p for p in root.rglob("*") if p.is_file()] + [Path(__file__).resolve(), CONTROL / "recovery-interface.md"]
    records = []
    for path in sorted(paths):
        assert not path.is_symlink()
        name, raw = path.relative_to(IQS).as_posix(), path.read_bytes()
        assert name not in tracked
        if path.suffix == ".py":
            ast.parse(raw.decode("utf-8"), filename=name)
        elif path.suffix == ".json":
            json.loads(raw)
        records.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
    document = {
        "phase": 111, "state": "in_progress_private_implementation_not_published", "iqs_baseline": BASELINE,
        "source_head": previous.earlier.SOURCE, "production_schema_version": 8, "private_schema_version": 12,
        "label": LABEL, "returncode": 0, "wall_s": process["wall_s"], "junit": counts,
        "only_test_changed_since_776_batch": CHANGED_TEST, "latest_executed_source_hashes": process["executed_source_hashes"],
        "records": records, "pending": ["mcp_each_http", "os_subprocess_public_cli_and_recovery",
            "final_static_and_concentrated_review", "source_publish", "strict_cleanup"],
        "unsent_expired_external_intent": "conservative_hold_pending_explicit_resolution",
        "whole_project_gates_closed": False,
    }
    INDEX.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    selected = [*previous.earlier.ROOT_PATHS, *(r["path"] for r in records), INDEX.relative_to(IQS).as_posix()]
    assert len(selected) == len(set(selected))
    MANIFEST.write_bytes(b"\0".join(n.encode("utf-8") for n in selected) + b"\0")
    print(json.dumps({"artifacts": len(records), "selected": len(selected), "tests": 5, "production_published": False}))


def publish():
    assert previous.earlier.git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not previous.earlier.git("diff", "--cached", "--name-only").strip()
    immutable_inputs()
    document = json.loads(INDEX.read_text("utf-8"))
    records = list(document["records"])
    for record in records:
        raw = (IQS / record["path"]).read_bytes()
        assert len(raw) == record["bytes"] and sha(raw) == record["sha256"]
    raw = INDEX.read_bytes()
    records.append({"path": INDEX.relative_to(IQS).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
    selected = MANIFEST.read_bytes().split(b"\0")[:-1]
    assert len(selected) == len(set(selected))
    assert all(b"opencode" not in n and not n.startswith(b"runs/") for n in selected)
    tracked = set(previous.earlier.git("ls-files", "-z").split(b"\0"))
    changed = set(previous.earlier.git("diff", "--name-only", "-z").split(b"\0")) - {b""}
    assert changed <= set(selected)
    expected = changed | (set(selected) - tracked)
    previous.earlier.git("add", "-f", "--pathspec-from-file=" + str(MANIFEST), "--pathspec-file-nul")
    actual = set(previous.earlier.git("diff", "--cached", "--name-only", "-z").split(b"\0")[:-1])
    assert actual == expected
    verify_blobs(":", records)
    previous.earlier.git("diff", "--cached", "--check")
    previous.earlier.git("commit", "-m", "test: freeze two-stage and cross-lease recovery evidence")
    previous.earlier.git("push", "origin", "HEAD:master")
    assert previous.earlier.git("rev-parse", "HEAD") == previous.earlier.git("rev-parse", "origin/master")
    verify_blobs("HEAD:", records)
    previous.earlier.source_unchanged()
    print(json.dumps({"commit": previous.earlier.git("rev-parse", "HEAD").decode().strip(),
        "artifacts": len(document["records"]), "selected": len(selected), "changed": len(actual),
        "status": previous.earlier.git("status", "--porcelain=v1").decode("utf-8"), "production_published": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "git"])
    prepare() if parser.parse_args().mode == "prepare" else publish()
