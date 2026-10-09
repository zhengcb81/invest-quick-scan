"""Publish only the 38 approved artifacts; normal hooks, no API or test rerun.

Original checkpoint helpers/receipts remain immutable. This controller records
actual source bytes before publication rather than equating Git LF with a
Windows worktree. It never reads unknown files or owner provider configuration.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

IQS = Path(__file__).resolve().parents[5]
CONTROL = Path(__file__).resolve().parent
OWN = IQS / "runs/n111a"
QA = OWN / "qa"
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"
SOURCE = Path("C:/Users/郑曾波/Projects/StockQAbyLLM")
BASE = "42a517c4bd6bc8219f926957c6c332944da3278a"
EXPECTED = ("?? .codegraph/\n?? .workbuddy-ai/\n?? nul\n"
            "?? pilot_runs/b2a_2026-10-03/\n?? pilot_runs/g2b_alphabet_2026-10-04/\n"
            "?? pilot_runs/l02_2026-10-04/\n?? progress_update.txt\n")
PUB = OUT / "publication"
NAMES = {
    "cold-stdout.log", "cold-stderr.log", "warm-stdout.log", "warm-stderr.log",
    "killed-stdout.log", "killed-stderr.log", "resumed-stdout.log", "resumed-stderr.log",
    "unknown-reopen-stdout.log", "unknown-reopen-stderr.log", "missing-key-stdout.log",
    "missing-key-stderr.log", "rejected-stdout.log", "rejected-stderr.log",
    "external-child-http.jsonl", "child-barrier.json", "termination.json", "key-opens.jsonl",
    "network-attempts.jsonl", "store-clock.txt", "result.json", "guard/sitecustomize.py",
    "seal-stdout.log", "seal-stderr.log",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    assert not path.exists(), path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def env():
    result = {k: v for k, v in os.environ.items() if not k.upper().endswith("_API_KEY")}
    for name in ("PYTHONPATH", "SKIP", "PRE_COMMIT_ALLOW_NO_CONFIG"):
        result.pop(name, None)
    temp = OWN / "publication-temp"
    temp.mkdir(exist_ok=True)
    result.update(TEMP=str(temp), TMP=str(temp), PYTHONDONTWRITEBYTECODE="1",
                  MYPY_CACHE_DIR=str(temp / "mypy"), BLACK_CACHE_DIR=str(temp / "black"))
    return result


def git(*args, logged=None, input=None):
    started = time.monotonic()
    run = subprocess.run(["git", *args], cwd=SOURCE, env=env(), input=input, capture_output=True)
    if logged:
        root = PUB / logged
        root.mkdir(exist_ok=False)
        (root / "stdout.log").write_bytes(run.stdout)
        (root / "stderr.log").write_bytes(run.stderr)
        save(root / "process.json", {"command": ["git", *args], "returncode": run.returncode,
             "wall_s": round(time.monotonic() - started, 3), "api_key_environment_removed": True,
             "hooks_skipped": False, "stdout_sha256": sha(run.stdout), "stderr_sha256": sha(run.stderr)})
    if run.returncode:
        raise RuntimeError(f"git {args[0]} failed with {run.returncode}; retained logs: {logged}")
    return run.stdout


def status():
    return git("status", "--porcelain=v1").decode("utf-8").replace("\r\n", "\n")


def read_review():
    scope = json.loads((CONTROL / "scope.json").read_bytes())
    review = json.loads((CONTROL / "final-review-recheck.json").read_bytes())
    assert review["verdict"] == "approved_limited_software"
    assert review["all_38_publication_artifacts_reviewed"] is True
    hashes = review["publication_artifact_hashes"]
    assert set(hashes) == set(scope["files"]) and len(hashes) == 38
    for name, digest in hashes.items():
        path = QA / name
        assert not path.is_symlink() and path.resolve().is_relative_to(QA.resolve())
        assert sha(path.read_bytes()) == digest, name
    for name, digest in review["iqs_source_hashes"].items():
        assert sha((IQS / name).read_bytes()) == digest, name
    for name, digest in review["first_review_preserved"].items():
        assert sha((CONTROL / name).read_bytes()) == digest, name
    process = json.loads((OUT / "verification/whole-phase-regression-02/process.json").read_bytes())
    assert process["returncode"] == 0 and not process["timeout"] and process["executed_source_unchanged"]
    assert process["executed_source_hashes"] == review["source_hashes"]
    return hashes


def check_baseline():
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    assert git("branch", "--show-current").decode().strip() == "master"
    assert status() == EXPECTED, "Reconcile writer drift before publication"
    assert not git("diff", "--cached", "--name-only").strip()
    assert (SOURCE / ".git/hooks/pre-commit").is_file(), "Normal hook must exist"
    # Inspect only internally; do not emit potentially credential-bearing URLs.
    remote = git("remote", "get-url", "--push", "origin").decode().strip()
    assert remote in {"git@github.com:zhengcb81/StockQAbyLLM.git",
                     "https://github.com/zhengcb81/StockQAbyLLM.git",
                     "https://github.com/zhengcb81/StockQAbyLLM"}


def blobs(ref, hashes):
    queries = [(ref + name).encode("utf-8") for name in hashes]
    raw = git("cat-file", "--batch", input=b"\n".join(queries) + b"\n")
    cursor = 0
    for name, digest in hashes.items():
        end = raw.index(b"\n", cursor)
        header = raw[cursor:end].split()
        assert len(header) == 3 and header[1] == b"blob", name
        length = int(header[2])
        content = raw[end + 1:end + 1 + length]
        assert sha(content) == digest, name
        cursor = end + 1 + length
        assert raw[cursor:cursor + 1] == b"\n"
        cursor += 1
    assert cursor == len(raw)


def archive_children():
    for label in ("whole-phase-regression-01", "whole-phase-regression-02"):
        batch = OUT / "verification" / label
        process = json.loads((batch / "process.json").read_bytes())
        assert process["returncode"] == 0 and not process["timeout"]
        root = OWN / "tmp" / label
        assert root.is_dir() and root.resolve().is_relative_to(OWN.resolve())
        target = batch / "subprocess"
        target.mkdir(exist_ok=False)
        cases = []
        for directory in sorted(root.iterdir()):
            if directory.is_symlink() or not directory.is_dir() or directory.name.endswith("current"):
                continue
            records = []
            for name in sorted(NAMES):
                path = directory / name
                if not path.is_file():
                    continue
                assert not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
                raw = path.read_bytes()
                copied = target / f"{len(cases):02d}" / name
                copied.parent.mkdir(parents=True, exist_ok=True)
                copied.write_bytes(raw)
                assert copied.read_bytes() == raw
                records.append({"path": copied.relative_to(batch).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
            if records:
                cases.append({"case_directory": directory.name, "records": records})
        save(target / "index.json", {"label": label, "synthetic_only": True,
             "process_sha256": sha((batch / "process.json").read_bytes()),
             "cases_with_allowed_logs_not_test_count": len(cases), "cases": cases})
    for label, names in (("review-20261009-01", ("reproduce-inline-archive.py", "stdout.log", "stderr.log")),
                         ("review-20261009-02", ("recheck-inline-archive.py", "stdout.log", "stderr.log", "process.json"))):
        records = []
        for name in names:
            path = OWN / label / name
            raw = path.read_bytes()
            target = OUT / "independent-review" / label / name
            target.parent.mkdir(parents=True, exist_ok=True)
            assert not target.exists()
            target.write_bytes(raw)
            records.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
        save(OUT / "independent-review" / label / "archive-index.json", {
            "script_archive_is_post_execution_inline_copy": True, "synthetic_only": True, "records": records,
            "databases_configs_keys_and_arbitrary_temp_not_archived": True})


def prepare():
    hashes = read_review()
    check_baseline()
    assert not PUB.exists()
    archive_children()
    PUB.mkdir()
    protected = {}
    snapshot = json.loads((OUT / "source-snapshot.json").read_bytes())
    for record in snapshot:
        name = record["path"]
        if name not in hashes:
            path = SOURCE / name
            assert not path.is_symlink() and path.is_file()
            protected[name] = sha(path.read_bytes())
    tracked = set(git("ls-files", "-z").decode("utf-8").split("\0"))
    before = {name: sha((SOURCE / name).read_bytes()) if name in tracked else None for name in hashes}
    save(PUB / "input.json", {"schema": "phase111-exact-publication/1", "baseline": BASE,
         "source": str(SOURCE), "scope_file_sha256": sha((CONTROL / "scope.json").read_bytes()),
         "review_sha256": sha((CONTROL / "final-review-recheck.json").read_bytes()),
         "reviewed_artifacts": hashes, "source_worktree_bytes_before": before, "protected_worktree_hashes": protected,
         "original_unknown_status": EXPECTED, "source_published": False, "whole_project_gates_closed": False})
    (OWN / "source-publication-paths.nul").write_bytes(b"\0".join(n.encode("utf-8") for n in hashes) + b"\0")
    print(json.dumps({"prepared_paths": len(hashes), "protected_actual_worktree_paths": len(protected), "source_published": False}))


def publish():
    frozen = json.loads((PUB / "input.json").read_bytes())
    hashes = read_review()
    assert hashes == frozen["reviewed_artifacts"]
    assert sha((CONTROL / "final-review-recheck.json").read_bytes()) == frozen["review_sha256"]
    check_baseline()
    for name, digest in frozen["source_worktree_bytes_before"].items():
        path = SOURCE / name
        assert (not path.exists()) if digest is None else sha(path.read_bytes()) == digest, name
    for name, digest in frozen["protected_worktree_hashes"].items():
        assert sha((SOURCE / name).read_bytes()) == digest, name
    for name, digest in hashes.items():
        target = SOURCE / name
        assert target.resolve().is_relative_to(SOURCE.resolve()) and not target.is_symlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((QA / name).read_bytes())
        assert sha(target.read_bytes()) == digest
    manifest = OWN / "source-publication-paths.nul"
    assert manifest.read_bytes() == b"\0".join(n.encode("utf-8") for n in hashes) + b"\0"
    git("add", "--pathspec-from-file=" + str(manifest), "--pathspec-file-nul", logged="01-stage")
    changed = git("diff", "--cached", "--name-only", "-z").decode("utf-8").split("\0")[:-1]
    assert changed and set(changed) <= set(hashes)
    blobs(":", hashes)
    git("diff", "--cached", "--check", logged="02-diff-check")
    git("commit", "-m", "feat: connect external search evidence with durable recovery", logged="03-commit")
    head = git("rev-parse", "HEAD").decode().strip()
    assert head != BASE
    assert git("rev-parse", "HEAD^").decode().strip() == BASE
    blobs("HEAD:", hashes)
    git("push", "origin", "HEAD:master", logged="04-push")
    remote_head = git("ls-remote", "origin", "refs/heads/master", logged="05-remote-head").decode().split()[0]
    assert head == remote_head == git("rev-parse", "origin/master").decode().strip()
    for name, digest in frozen["protected_worktree_hashes"].items():
        assert sha((SOURCE / name).read_bytes()) == digest, name
    assert status() == EXPECTED
    save(PUB / "result.json", {"source_commit": head, "remote_head": remote_head, "source_published": True,
         "approved_paths": 38, "actual_commit_paths": changed, "reviewed_git_blob_hashes": hashes,
         "protected_worktree_paths_unchanged": len(frozen["protected_worktree_hashes"]),
         "original_unknown_status_preserved": status(), "normal_commit_hooks": True, "real_api_requests": 0,
         "production_database_changes": 0, "whole_project_gates_closed": False,
         "pending": ["strict_owned_cleanup", "IQS_evidence_and_PWF_git_delivery", "StockWiki_authorization_and_joint_ACK",
                     "real_facts_and_query_golden", "financial_accuracy", "G3_F05_L03_TH_IN"]})
    print(json.dumps({"source_commit": head, "remote_head": remote_head, "published_paths": len(changed),
                      "reviewed_blobs": len(hashes), "unknown_preserved": True, "whole_project_gates_closed": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "source"))
    args = parser.parse_args()
    prepare() if args.mode == "prepare" else publish()
