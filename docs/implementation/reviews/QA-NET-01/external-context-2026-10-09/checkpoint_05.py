"""Freeze private checkpoint/runtime progress; never publish StockQA here."""
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
INDEX = OUT / "checkpoint-index-05.json"
MANIFEST = OWN / "checkpoint-paths-05.nul"
BASELINE = "a6691beb4f1b1d87234f076bc8cd659cf3a1ec99"
SOURCE = "42a517c4bd6bc8219f926957c6c332944da3278a"
BATCHES = (
    "checkpoint-red-01", "checkpoint-green-01", "checkpoint-green-02",
    "checkpoint-affected-green-01", "checkpoint-binding-red-01",
    "checkpoint-affected-green-02", "checkpoint-metadata-red-01", "checkpoint-affected-green-03",
    "runtime-projection-red-01", "runtime-projection-green-01",
    "runtime-complete-red-01", "runtime-complete-red-02", "runtime-complete-green-01", "runtime-complete-green-02",
    "runtime-checkpoint-affected-green-01",
)
ROOT_PATHS = (
    "task_plan.md", "progress.md", "findings.md", "docs/implementation/handoff-for-new-agent.md",
    "docs/implementation/reviews/QA-NET-01/external-context-2026-10-09/plan.md",
    "docs/implementation/reviews/QA-NET-01/external-context-2026-10-09/scope.json",
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


def source_unchanged():
    source = str(IQS.parent / "StockQAbyLLM")
    assert git("-C", source, "rev-parse", "HEAD").decode().strip() == SOURCE
    expected = {"?? .codegraph/", "?? .workbuddy-ai/", "?? nul", "?? pilot_runs/b2a_2026-10-03/",
        "?? pilot_runs/g2b_alphabet_2026-10-04/", "?? pilot_runs/l02_2026-10-04/", "?? progress_update.txt"}
    assert set(git("-C", source, "status", "--porcelain=v1").decode("utf-8").splitlines()) == expected


def previous_unchanged():
    commits = {"01": "6ee1abd68d91d358116ee3f6869fbaae94f5de12",
        "02": "537a174a7c024a59dbe0b6159660df77a1cabd40",
        "03": "35df1184c028b7c2a79446004d32c439c791316d",
        "04": "a6691beb4f1b1d87234f076bc8cd659cf3a1ec99"}
    for label in ("01", "02", "03", "04"):
        path = OUT / ("checkpoint-index-" + label + ".json")
        assert git("show", "HEAD:" + path.relative_to(IQS).as_posix()) == path.read_bytes()
        for record in json.loads(path.read_text("utf-8"))["records"]:
            # Index01 included the mutable plan/scope. Their original bytes
            # remain in its actual commit; later plans must not be frozen.
            raw = (git("show", commits[label] + ":" + record["path"])
                if record["path"] in ROOT_PATHS else (IQS / record["path"]).read_bytes())
            assert sha(raw) == record["sha256"], record["path"]


def prepare():
    assert git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not git("diff", "--cached", "--name-only").strip()
    assert not INDEX.exists() and not MANIFEST.exists()
    source_unchanged()
    previous_unchanged()
    scope = set(json.loads((CONTROL / "scope.json").read_text("utf-8"))["files"])
    unchanged = 0
    for record in json.loads((OUT / "source-snapshot.json").read_text("utf-8")):
        if record["path"] not in scope:
            assert sha((OWN / "qa" / record["path"]).read_bytes()) == record["sha256"], record["path"]
            unchanged += 1
    latest = json.loads((OUT / "verification" / BATCHES[-1] / "process.json").read_text("utf-8"))
    assert latest["returncode"] == 0 and not latest["timeout"] and latest["executed_source_unchanged"]
    for name, digest in latest["executed_source_hashes"].items():
        assert sha((OWN / "qa" / name).read_bytes()) == digest, name
    paths, batches = [], []
    for label in BATCHES:
        root = OUT / "verification" / label
        process = json.loads((root / "process.json").read_text("utf-8"))
        assert not process["timeout"] and process["executed_source_unchanged"]
        suite = ET.parse(root / "junit.xml").getroot().find("testsuite")
        assert suite is not None
        batches.append({"label": label, "returncode": process["returncode"], "wall_s": process["wall_s"],
            **{key: int(suite.attrib[key]) for key in ("tests", "failures", "errors", "skipped")}})
        paths.extend(path for path in root.rglob("*") if path.is_file())
    assert batches[-1]["tests"] == 672 and all(batches[-1][key] == 0 for key in ("failures", "errors", "skipped"))
    paths.extend([Path(__file__).resolve(), CONTROL / "record_checkpoint_progress.py", CONTROL / "checkpoint-interface.md"])
    records = []
    for path in sorted(paths):
        assert not path.is_symlink()
        name, raw = path.relative_to(IQS).as_posix(), path.read_bytes()
        assert not git("ls-files", "--", name).strip(), name
        if path.suffix == ".json":
            json.loads(raw)
        elif path.suffix == ".py":
            ast.parse(raw.decode("utf-8"), filename=name)
        records.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
    document = {"phase": 111, "state": "in_progress_private_implementation_not_published", "iqs_baseline": BASELINE,
        "source_head": SOURCE, "production_schema_version": 8, "private_schema_version": 11,
        "support_files_unchanged": unchanged, "test_batches": batches,
        "latest_executed_source_hashes": latest["executed_source_hashes"], "records": records,
        "pending": ["public_result_version_and_consumer", "runner_coordinator_wiring", "async_provider_projection",
            "two_stage_recovery", "cross_lease_recovery", "mcp_handshake", "public_cli",
            "final_static_and_concentrated_review", "source_publish", "strict_cleanup"], "whole_project_gates_closed": False}
    INDEX.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    selected = [*ROOT_PATHS, *(record["path"] for record in records), INDEX.relative_to(IQS).as_posix()]
    assert len(selected) == len(set(selected))
    MANIFEST.write_bytes(b"".join(name.encode("utf-8") + b"\0" for name in selected))
    print(json.dumps({"artifacts": len(records), "selected": len(selected), "batches": len(batches),
        "support_files_unchanged": unchanged, "production_published": False}))


def checkpoint_git():
    assert git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not git("diff", "--cached", "--name-only").strip()
    source_unchanged()
    previous_unchanged()
    document = json.loads(INDEX.read_text("utf-8"))
    selected = MANIFEST.read_bytes().split(b"\0")[:-1]
    assert all(b"opencode" not in name and not name.startswith(b"runs/") for name in selected)
    for record in document["records"]:
        raw = (IQS / record["path"]).read_bytes()
        assert len(raw) == record["bytes"] and sha(raw) == record["sha256"]
    git("add", "-f", "--pathspec-from-file=" + str(MANIFEST), "--pathspec-file-nul")
    assert set(git("diff", "--cached", "--name-only", "-z").split(b"\0")[:-1]) == set(selected)
    for record in document["records"]:
        assert sha(git("show", ":" + record["path"])) == record["sha256"], record["path"]
    assert git("show", ":" + INDEX.relative_to(IQS).as_posix()) == INDEX.read_bytes()
    git("diff", "--cached", "--check")
    git("commit", "-m", "docs: checkpoint external answer persistence and runner bindings")
    git("push", "origin", "HEAD:master")
    assert git("rev-parse", "HEAD") == git("rev-parse", "origin/master")
    for record in document["records"]:
        assert sha(git("show", "HEAD:" + record["path"])) == record["sha256"]
    source_unchanged()
    print(json.dumps({"commit": git("rev-parse", "HEAD").decode().strip(), "artifacts": len(document["records"]),
        "selected": len(selected), "remaining_status": git("status", "--porcelain=v1").decode("utf-8"), "production_published": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "git"])
    args = parser.parse_args()
    prepare() if args.mode == "prepare" else checkpoint_git()
