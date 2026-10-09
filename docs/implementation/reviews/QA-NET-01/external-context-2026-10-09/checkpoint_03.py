"""Freeze this private-development batch in IQS, without publishing StockQA.

Run prepare once at the specified HEAD, then git with the same path manifest.
Earlier checkpoints and executed evidence are immutable. This is not acceptance.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

IQS = Path(__file__).resolve().parents[5]
CONTROL = Path(__file__).parent
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"
OWN = IQS / "runs/n111a"
INDEX = OUT / "checkpoint-index-03.json"
MANIFEST = OWN / "checkpoint-paths-03.nul"
BASELINE = "67bf570e0c306590057e16d3c66671e393b8a2e0"
SOURCE = "42a517c4bd6bc8219f926957c6c332944da3278a"
BATCHES = (
    "coordinator-red-01", "coordinator-green-01", "coordinator-green-02",
    "coordinator-green-03", "coordinator-affected-green-01",
    "coordinator-health-red-01", "coordinator-health-green-01",
)

ROOT_PATHS = (
    "task_plan.md", "progress.md", "findings.md",
    "docs/implementation/handoff-for-new-agent.md",
    "docs/implementation/reviews/QA-NET-01/external-context-2026-10-09/plan.md",
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    result = subprocess.run(["git", *args], cwd=IQS, capture_output=True)
    if result.returncode:
        sys.stdout.buffer.write(result.stdout)
        sys.stderr.buffer.write(result.stderr)
        raise SystemExit(result.returncode)
    return result.stdout


def check_source():
    assert git("-C", str(IQS.parent / "StockQAbyLLM"), "rev-parse", "HEAD").decode().strip() == SOURCE
    expected = {"?? .codegraph/", "?? .workbuddy-ai/", "?? nul", "?? pilot_runs/b2a_2026-10-03/",
                "?? pilot_runs/g2b_alphabet_2026-10-04/", "?? pilot_runs/l02_2026-10-04/", "?? progress_update.txt"}
    status = git("-C", str(IQS.parent / "StockQAbyLLM"), "status", "--porcelain=v1").decode("utf-8")
    assert set(status.splitlines()) == expected


def prepare():
    assert git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not git("diff", "--cached", "--name-only").strip()
    assert not INDEX.exists() and not MANIFEST.exists()
    check_source()
    for label in ("01", "02"):
        previous = OUT / ("checkpoint-index-" + label + ".json")
        assert git("show", "HEAD:" + previous.relative_to(IQS).as_posix()) == previous.read_bytes()
    scope = set(json.loads((CONTROL / "scope.json").read_text("utf-8"))["files"])
    support = json.loads((OUT / "source-snapshot.json").read_text("utf-8"))
    support_unchanged = 0
    for record in support:
        if record["path"] not in scope:
            assert sha((OWN / "qa" / record["path"]).read_bytes()) == record["sha256"], record["path"]
            support_unchanged += 1
    latest = json.loads((OUT / "verification/coordinator-health-green-01/process.json").read_text("utf-8"))
    assert latest["returncode"] == 0 and not latest["timeout"] and latest["executed_source_unchanged"]
    for name, digest in latest["executed_source_hashes"].items():
        assert sha((OWN / "qa" / name).read_bytes()) == digest, name
    paths, batches = [], []
    for label in BATCHES:
        root = OUT / "verification" / label
        receipt = json.loads((root / "process.json").read_text("utf-8"))
        assert not receipt["timeout"] and receipt["executed_source_unchanged"]
        suite = ET.parse(root / "junit.xml").getroot().find("testsuite")
        assert suite is not None
        batches.append({"label": label, "returncode": receipt["returncode"], "wall_s": receipt["wall_s"],
                        **{name: int(suite.attrib[name]) for name in ("tests", "failures", "errors", "skipped")}})
        paths.extend(path for path in root.rglob("*") if path.is_file())
    paths.extend([Path(__file__).resolve(), CONTROL / "record_coordinator_progress.py", CONTROL / "coordinator-interface.md"])
    records = []
    for path in sorted(paths):
        assert not path.is_symlink()
        name = path.relative_to(IQS).as_posix()
        assert not git("ls-files", "--", name).strip(), name
        raw = path.read_bytes()
        if path.suffix == ".json":
            json.loads(raw)
        elif path.suffix == ".py":
            ast.parse(raw.decode("utf-8"), filename=name)
        records.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
    document = {
        "phase": 111, "state": "in_progress_private_implementation_not_published", "iqs_baseline": BASELINE,
        "source_head": SOURCE, "production_schema_version": 8, "private_schema_version": 9,
        "support_files_unchanged": support_unchanged, "test_batches": batches,
        "latest_executed_source_hashes": latest["executed_source_hashes"], "records": records,
        "pending": ["runner_coordinator_wiring", "actual_llm_context_and_use_proof", "two_stage_recovery", "cross_lease_recovery",
                    "mcp_handshake", "public_cli", "final_static_and_concentrated_review", "source_publish", "strict_cleanup"],
        "whole_project_gates_closed": False,
    }
    INDEX.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    selected = [*ROOT_PATHS, *(record["path"] for record in records), INDEX.relative_to(IQS).as_posix()]
    assert len(selected) == len(set(selected))
    MANIFEST.write_bytes(b"".join(name.encode("utf-8") + b"\0" for name in selected))
    print(json.dumps({"artifacts": len(records), "selected": len(selected), "batches": len(batches),
                      "support_files_unchanged": support_unchanged, "production_published": False}))


def publish_checkpoint():
    assert git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not git("diff", "--cached", "--name-only").strip()
    check_source()
    document = json.loads(INDEX.read_text("utf-8"))
    selected = MANIFEST.read_bytes().split(b"\0")[:-1]
    assert all(b"opencode" not in name and not name.startswith(b"runs/") for name in selected)
    for record in document["records"]:
        raw = (IQS / record["path"]).read_bytes()
        assert len(raw) == record["bytes"] and sha(raw) == record["sha256"], record["path"]
    git("add", "-f", "--pathspec-from-file=" + str(MANIFEST), "--pathspec-file-nul")
    assert set(git("diff", "--cached", "--name-only", "-z").split(b"\0")[:-1]) == set(selected)
    for record in document["records"]:
        assert sha(git("show", ":" + record["path"])) == record["sha256"], record["path"]
    assert git("show", ":" + INDEX.relative_to(IQS).as_posix()) == INDEX.read_bytes()
    git("diff", "--cached", "--check")
    git("commit", "-m", "docs: checkpoint external retrieval recovery and cooldown")
    git("push", "origin", "HEAD:master")
    assert git("rev-parse", "HEAD") == git("rev-parse", "origin/master")
    for record in document["records"]:
        assert sha(git("show", "HEAD:" + record["path"])) == record["sha256"], record["path"]
    check_source()
    print(json.dumps({"commit": git("rev-parse", "HEAD").decode().strip(), "artifacts": len(document["records"]),
                      "selected": len(selected), "remaining_status": git("status", "--porcelain=v1").decode("utf-8"),
                      "production_published": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "git"])
    args = parser.parse_args()
    prepare() if args.mode == "prepare" else publish_checkpoint()
