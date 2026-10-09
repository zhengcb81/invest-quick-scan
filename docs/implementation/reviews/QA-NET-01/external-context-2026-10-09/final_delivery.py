"""Freeze final evidence and publish IQS using exact NUL path manifests.

No tests/API calls, no old receipt refresh, no source rewrite. Old tracked
artifacts are compared with Git bytes; only named PWF/plan prose may evolve.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

IQS = Path(__file__).resolve().parents[5]
CONTROL = Path(__file__).resolve().parent
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"
BASE = "5f4e518f02528371e8ac67ca33deefa040007712"
ROOTS = ["task_plan.md", "progress.md", "findings.md", "docs/implementation/handoff-for-new-agent.md"]
LABELS = ["whole-phase-regression-01", "whole-phase-regression-02", "whole-phase-adjacent-regression-01",
          "whole-phase-iqs-consumer-01", "whole-phase-review-red-01", "whole-phase-review-green-01"]
NEW_CONTROL = ["final-review.md", "final-review.json", "final-review-recheck.md", "final-review-recheck.json",
               "run_static.py", "publish_final.py", "prepare_cleanup.py", "cleanup.ps1", "final_delivery.py", "delivery.md"]
INDEX = OUT / "final-delivery-index.json"
MANIFEST = OUT / "final-git-paths.nul"
RESULT = OUT / "final-git-result.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def git(*args, input=None, log=None, cwd=IQS):
    env = {k: v for k, v in os.environ.items() if not k.upper().endswith("_API_KEY")}
    for name in ("SKIP", "PYTHONPATH", "PRE_COMMIT_ALLOW_NO_CONFIG"):
        env.pop(name, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    run = subprocess.run(["git", *args], cwd=cwd, env=env, input=input, capture_output=True)
    if log:
        directory = OUT / "git-delivery"
        directory.mkdir(exist_ok=True)
        for stream in ("stdout", "stderr"):
            path = directory / f"{log}.{stream}.log"
            assert not path.exists()
            path.write_bytes(getattr(run, stream))
    if run.returncode:
        raise RuntimeError(f"git {args[0]} exit {run.returncode}; log {log}")
    return run.stdout


def names(raw):
    return {part.decode("utf-8") for part in raw.split(b"\0") if part}


def verify_blobs(ref, records):
    for start in range(0, len(records), 96):
        chunk = records[start:start + 96]
        queries = [(ref + row["path"]).encode("utf-8") for row in chunk]
        raw = git("cat-file", "--batch", input=b"\n".join(queries) + b"\n")
        cursor = 0
        for row in chunk:
            end = raw.index(b"\n", cursor)
            header = raw[cursor:end].split()
            assert len(header) == 3 and header[1] == b"blob", row["path"]
            size = int(header[2])
            content = raw[end + 1:end + 1 + size]
            assert len(content) == row["bytes"] and sha(content) == row["sha256"], row["path"]
            cursor = end + 1 + size
            assert raw[cursor:cursor + 1] == b"\n"
            cursor += 1
        assert cursor == len(raw)


def record(path):
    assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(IQS.resolve())
    raw = path.read_bytes()
    return {"path": path.relative_to(IQS).as_posix(), "bytes": len(raw), "sha256": sha(raw)}


def immutable():
    tracked = names(git("ls-files", "-z", "--", OUT.relative_to(IQS).as_posix(), CONTROL.relative_to(IQS).as_posix()))
    allowed = {(CONTROL / "plan.md").relative_to(IQS).as_posix()}
    rows = [record(IQS / name) for name in sorted(tracked - allowed)]
    verify_blobs("HEAD:", rows)
    return len(rows)


def final_state():
    assert not (IQS / "runs/n111a").exists(), "Owned root must be cleaned before final delivery"
    cleanup = json.loads((OUT / "cleanup-receipt.json").read_bytes())
    assert cleanup["applied"] and cleanup["files_deleted"] == cleanup["files_verified"] == 20025
    assert cleanup["directories_verified"] == 8999 and cleanup["process_matches"] == 0
    baseline = OUT / "cleanup-baseline.json"
    assert cleanup["baseline_sha256"] == sha(baseline.read_bytes())
    source = json.loads((OUT / "publication/result.json").read_bytes())
    assert source["source_published"] and source["approved_paths"] == 38
    assert source["whole_project_gates_closed"] is False
    assert git("rev-parse", "HEAD", cwd=Path("C:/Users/郑曾波/Projects/StockQAbyLLM")).decode().strip() == source["source_commit"]
    review = json.loads((CONTROL / "final-review-recheck.json").read_bytes())
    assert review["publication_artifact_hashes"] == source["reviewed_git_blob_hashes"]
    return source


def prepare():
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    assert not git("diff", "--cached", "--name-only").strip()
    source = final_state()
    old_count = immutable()
    paths = [CONTROL / name for name in NEW_CONTROL]
    folders = [OUT / "static", OUT / "publication", OUT / "independent-review"]
    folders += [OUT / "verification" / label for label in LABELS]
    for folder in folders:
        paths += [p for p in folder.rglob("*") if p.is_file()]
    paths += [OUT / name for name in ("cleanup-baseline.json", "cleanup-lstat.json", "cleanup-dry-run.json", "cleanup-receipt.json")]
    assert len(paths) == len(set(paths))
    records = []
    for path in sorted(paths):
        raw = path.read_bytes()
        if path.suffix == ".json":
            json.loads(raw)
        elif path.suffix == ".py":
            ast.parse(raw.decode("utf-8"), filename=str(path))
        records.append(record(path))
    selected = ROOTS + [(CONTROL / "plan.md").relative_to(IQS).as_posix()]
    selected += [r["path"] for r in records] + [INDEX.relative_to(IQS).as_posix(), MANIFEST.relative_to(IQS).as_posix()]
    assert len(selected) == len(set(selected))
    assert not MANIFEST.exists() and not INDEX.exists()
    MANIFEST.write_bytes(b"\0".join(name.encode("utf-8") for name in selected) + b"\0")
    records.append(record(MANIFEST))
    save(INDEX, {"schema": "phase111-final-delivery/1", "iqs_baseline": BASE,
         "state": "software_published_reviewed_cleaned_IQS_git_pending", "source_commit": source["source_commit"],
         "source_reviewed_paths": 38, "old_tracked_artifacts_unchanged": old_count,
         "final_regression": {"passed": 861, "failures": 0, "errors": 0, "skipped": 0},
         "adjacent_separate_batch": {"passed": 128}, "IQS_separate_batch": {"passed": 111, "subtests_passed": 216},
         "actual_new_OS_cases": 24, "actual_kill_positions": 11,
         "owned_files_deleted": 20025, "owned_directories_deleted": 8999,
         "whole_project_gates_closed": False, "financial_accuracy_certified": False,
         "pending": ["StockWiki_four_path_authorization_and_joint_ACK", "real_owner_facts_query_golden", "G3_F05_L03_TH_IN", "full_one_click_release"],
         "records": records, "selected_paths": selected})
    print(json.dumps({"frozen_artifacts": len(records), "selected": len(selected), "old_artifacts_unchanged": old_count,
                      "source_commit": source["source_commit"], "whole_project_gates_closed": False}))


def publish():
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    assert not git("diff", "--cached", "--name-only").strip()
    final_state()
    immutable()
    document = json.loads(INDEX.read_bytes())
    records = document["records"] + [record(INDEX)]
    for row in records:
        assert record(IQS / row["path"]) == row
    selected = document["selected_paths"]
    assert MANIFEST.read_bytes() == b"\0".join(name.encode("utf-8") for name in selected) + b"\0"
    changed = names(git("diff", "--name-only", "-z"))
    tracked = names(git("ls-files", "-z"))
    assert changed <= set(selected), changed - set(selected)
    expected = changed | (set(selected) - tracked)
    git("add", "-f", "--pathspec-from-file=" + str(MANIFEST), "--pathspec-file-nul")
    actual = names(git("diff", "--cached", "--name-only", "-z"))
    assert actual == expected
    verify_blobs(":", records)
    git("diff", "--cached", "--check")
    git("commit", "-m", "feat: retain reviewed external search release and recovery evidence", log="commit")
    head = git("rev-parse", "HEAD").decode().strip()
    verify_blobs("HEAD:", records)
    git("push", "origin", "HEAD:master", log="push")
    remote = git("ls-remote", "origin", "refs/heads/master").decode().split()[0]
    assert head == remote == git("rev-parse", "origin/master").decode().strip()
    final_state()
    save(RESULT, {"iqs_commit": head, "remote_head": remote, "selected_paths": len(selected), "actual_changed_paths": len(actual),
         "verified_artifact_git_blobs": len(records), "source_commit": document["source_commit"],
         "owned_root_absent": True, "whole_project_gates_closed": False,
         "pending": "Commit these actual Git logs/receipt and updated PWF prose only; do not change frozen artifacts"})
    print(json.dumps({"commit": head, "remote_head": remote, "selected": len(selected), "changed": len(actual),
                      "verified_artifact_blobs": len(records), "owned_root_absent": True}))


def receipt_git():
    receipt = json.loads(RESULT.read_bytes())
    assert git("rev-parse", "HEAD").decode().strip() == receipt["iqs_commit"]
    assert not git("diff", "--cached", "--name-only").strip()
    selected = ROOTS + [RESULT.relative_to(IQS).as_posix()]
    selected += [(OUT / "git-delivery" / f"{name}.{stream}.log").relative_to(IQS).as_posix()
                 for name in ("commit", "push") for stream in ("stdout", "stderr")]
    changed = names(git("diff", "--name-only", "-z"))
    assert changed <= set(ROOTS)
    raw_records = [record(IQS / name) for name in selected if name not in ROOTS]
    git("add", "-f", "--pathspec-from-file=-", "--pathspec-file-nul",
        input=b"\0".join(n.encode("utf-8") for n in selected) + b"\0")
    verify_blobs(":", raw_records)
    actual = names(git("diff", "--cached", "--name-only", "-z"))
    assert actual <= set(selected) and actual
    git("diff", "--cached", "--check")
    git("commit", "-m", "docs: record completed Phase111 release and next integration boundary")
    git("push", "origin", "HEAD:master")
    head = git("rev-parse", "HEAD").decode().strip()
    assert head == git("ls-remote", "origin", "refs/heads/master").decode().split()[0]
    verify_blobs("HEAD:", raw_records)
    final_state()
    status = git("status", "--porcelain=v1").decode("utf-8").replace("\r\n", "\n")
    assert status == "?? opencode.json\n", status
    print(json.dumps({"receipt_commit": head, "release_artifact_commit": receipt["iqs_commit"],
                      "source_commit": receipt["source_commit"], "status": status, "whole_project_gates_closed": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "git", "receipt-git"))
    {"prepare": prepare, "git": publish, "receipt-git": receipt_git}[parser.parse_args().mode]()
