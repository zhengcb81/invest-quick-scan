"""Freeze actual private MCP progress, not source publication or a new review gate."""
import argparse
import ast
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import checkpoint_08 as previous
from checkpoint_07_resume import verify_blobs

IQS, CONTROL, OUT, OWN = previous.IQS, previous.CONTROL, previous.OUT, previous.OWN
BASELINE = "6ef0cdea9750007a01db5f5bd09a62eb6a1c8eaa"
INDEX = OUT / "checkpoint-index-09.json"
MANIFEST = OWN / "checkpoint-paths-09.nul"
LABELS = (
    "mcp-control-journal-red-01", "mcp-control-journal-green-01", "mcp-control-adjacent-red-01",
    "mcp-journal-owner-affected-green-01", "mcp-protocol-transport-red-01", "mcp-control-transport-green-01",
    "mcp-full-retrieval-red-01", "mcp-full-retrieval-green-01", "mcp-retrieval-owner-affected-green-01",
    "mcp-old-blocker-fixture-green-01",
)
sha, git = previous.sha, previous.previous.earlier.git


def immutable_inputs():
    previous.previous.immutable_inputs()
    previous.immutable_inputs()
    path = OUT / "checkpoint-index-08.json"
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
    affected = json.loads((OUT / "verification" / LABELS[-2] / "process.json").read_text("utf-8"))
    assert latest["returncode"] == 0 and affected["returncode"] == 1
    assert set(latest["executed_source_hashes"]) == set(affected["executed_source_hashes"])
    changes = {n for n, digest in latest["executed_source_hashes"].items() if digest != affected["executed_source_hashes"][n]}
    assert changes == {"tests/unit/test_quick_scan_external_context.py"}
    for name, digest in latest["executed_source_hashes"].items():
        assert sha((OWN / "qa" / name).read_bytes()) == digest, name
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
        batches.append({"label": label, "returncode": process["returncode"], "wall_s": process["wall_s"], "junit": counts})
        paths.extend(p for p in root.rglob("*") if p.is_file())
    assert batches[-2]["junit"] == dict(tests=398, failures=1, errors=0, skipped=0)
    assert batches[-1]["junit"] == dict(tests=1, failures=0, errors=0, skipped=0)
    suite = ET.parse(OUT / "verification" / LABELS[-2] / "junit.xml").getroot().find("testsuite")
    mcp = [case for case in suite.findall("testcase") if case.get("classname") == "tests.unit.test_quick_scan_mcp"]
    assert len(mcp) == 47 and all(case.find("failure") is None and case.find("error") is None for case in mcp)
    paths += [Path(__file__).resolve(), CONTROL / "record_mcp_progress.py", CONTROL / "mcp-interface.md"]
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
    document = {"phase": 111, "state": "in_progress_private_implementation_not_published", "iqs_baseline": BASELINE,
        "source_head": previous.previous.earlier.SOURCE, "production_schema_version": 8, "private_schema_version": 13,
        "scope_paths": 38, "executed_paths": len(latest["executed_source_hashes"]), "support_files_unchanged": support,
        "test_batches": batches, "mcp_instances_passed_in_affected_batch": 47,
        "obsolete_preimplementation_fixture_followup": {"only_file_changed": next(iter(changes)),
            "product_source_unchanged": True, "not_a_single_398_green_batch": True},
        "latest_executed_source_hashes": latest["executed_source_hashes"], "records": records,
        "mcp_price_support": "verified_all_http_requests_per_request_only_no_default_free_controls",
        "mcp_cold_request_count_per_frozen_query": 4, "mcp_warm_request_increment": 0,
        "pending": ["os_subprocess_public_cli_and_recovery", "final_static_and_concentrated_review", "source_publish", "strict_cleanup"],
        "whole_project_gates_closed": False}
    INDEX.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    selected = [*previous.previous.earlier.ROOT_PATHS, *(r["path"] for r in records), INDEX.relative_to(IQS).as_posix()]
    assert len(selected) == len(set(selected))
    MANIFEST.write_bytes(b"\0".join(n.encode("utf-8") for n in selected) + b"\0")
    print(json.dumps({"artifacts": len(records), "selected": len(selected), "batches": len(batches), "support": support,
        "mcp_passed": 47, "production_published": False}))


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
    git("commit", "-m", "feat: freeze metered MCP retrieval and recovery evidence")
    git("push", "origin", "HEAD:master")
    assert git("rev-parse", "HEAD") == git("rev-parse", "origin/master")
    verify_blobs("HEAD:", records)
    previous.previous.earlier.source_unchanged()
    print(json.dumps({"commit": git("rev-parse", "HEAD").decode().strip(), "artifacts": len(document["records"]),
        "selected": len(selected), "changed": len(actual), "status": git("status", "--porcelain=v1").decode("utf-8"),
        "production_published": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "git"])
    prepare() if parser.parse_args().mode == "prepare" else publish()
