"""Once-only exact W15 foundation publication with normal owner hooks.

Preflight never reads unknown files or provider config. Apply checks an actual
same-review signed-off candidate. A partial failure must be resumed explicitly,
never by re-running apply. No production SQLite access, no model/search API.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "docs/implementation/intake/W15/module-readiness-2026-10-09"
CONTROL = Path(__file__).resolve().parent
OWN = ROOT / "runs/w15a"
PUB = OUT / "source-publication"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    path = PUB / name
    assert not path.exists(), path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def env():
    e = {k: v for k, v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE",
        "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    temp = OWN / "publication-temp"
    temp.mkdir(exist_ok=True)
    e.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1",
             PYTHONUTF8="1", PYTHONIOENCODING="utf-8", TEMP=str(temp), TMP=str(temp),
             TMPDIR=str(temp), PRE_COMMIT_HOME=str(temp / "pc"),
             BLACK_CACHE_DIR=str(temp / "black"), MYPY_CACHE_DIR=str(temp / "mypy"),
             RUFF_CACHE_DIR=str(temp / "ruff"), STOCKQA_RUN_LIVE_E2E="0")
    return e


def git(repo, *args, label=None):
    start = time.monotonic()
    p = subprocess.Popen(["git", *args], cwd=repo, env=env(), stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    if label:
        print(json.dumps(dict(label=label, pid=p.pid)), flush=True)
    stdout, stderr = p.communicate(timeout=600)
    if label:
        (PUB / (label + ".stdout.log")).write_bytes(stdout)
        (PUB / (label + ".stderr.log")).write_bytes(stderr)
        save(label + ".process.json", dict(command=["git", *args], pid=p.pid,
             terminal_confirmed=True, returncode=p.returncode, wall_s=round(time.monotonic()-start, 3),
             stdout_sha256=sha(stdout), stderr_sha256=sha(stderr), normal_hooks=True,
             credentials_inherited=False))
        print((stdout + stderr).decode("utf-8", errors="replace")[-1800:])
    if p.returncode:
        raise RuntimeError(f"git {args[0]} failed: {p.returncode}; preserved label {label}")
    return stdout


def regular(path, root):
    assert path.resolve().is_relative_to(root.resolve())
    for p in [path, *path.parents]:
        if p == root.parent:
            break
        if p.exists():
            info = os.lstat(p)
            assert not getattr(info, "st_file_attributes", 0) & 0x400 and not p.is_symlink(), p
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1, path


def preflight(label):
    assert label.replace("-", "").isalnum()
    index = json.loads((OUT / "candidate-index-02.json").read_bytes())
    states = {}
    for project in ("StockWiki", "StockQAbyLLM"):
        repo = ROOT.parent / project
        frozen = json.loads((OUT / ("stockwiki-input-01.json" if project == "StockWiki" else "executor-input-01.json")).read_bytes())
        expected_status = frozen.get("original_status", frozen.get("source_status"))
        status = git(repo, "status", "--porcelain=v1", "-uall").decode().replace("\r\n", "\n")
        assert status == expected_status and not git(repo, "diff", "--cached", "--name-only"), project
        head = git(repo, "rev-parse", "HEAD").decode().strip()
        assert head == index["baselines"][project], project
        assert git(repo, "branch", "--show-current").decode().strip() == "master"
        original = frozen["nonsecret_files"] if project == "StockWiki" else frozen["artifacts"]
        protected = {}
        candidate_names = {r["path"] for r in index["files"][project]}
        for row in original:
            p = repo / row["path"]
            regular(p, repo)
            assert sha(p.read_bytes()) == row.get("execution_sha256", row.get("sha256")), row["path"]
            if row["path"] not in candidate_names:
                protected[row["path"]] = sha(p.read_bytes())
        for row in index["files"][project]:
            p = repo / row["path"]
            candidate = OUT / "candidate-source-02" / project / row["path"]
            regular(candidate, OUT)
            assert sha(candidate.read_bytes()) == row["execution_sha256"]
            if row["baseline_execution_sha256"] is None:
                assert not p.exists(), p
            else:
                assert sha(p.read_bytes()) == row["baseline_execution_sha256"]
        assert git(repo, "rev-parse", "HEAD").decode().strip() == head
        assert git(repo, "status", "--porcelain=v1", "-uall").decode().replace("\r\n", "\n") == status
        states[project] = dict(head=head, branch="master", status=status,
                               protected_nonsecret_source_sha256=protected,
                               remote_names=git(repo, "remote").decode().splitlines())
    save(label + ".json", dict(candidate_index_sha256=sha((OUT/"candidate-index-02.json").read_bytes()),
         sources=states, source_written=False, authorization="给你全部后续所需的授权",
         unknown_files_read=False, production_DB_migrations=0, API_requests=0))
    return states, index


def apply():
    assert not (PUB / "apply-preflight.json").exists()
    review = json.loads((CONTROL / "review/concentrated-recheck-02.json").read_bytes())
    assert review["software_open_findings"] == 0
    assert review["outcome"] == "limited_foundation_signed_off"
    assert review["candidate_index_sha256"] == sha((OUT / "candidate-index-02.json").read_bytes())
    states, index = preflight("apply-preflight")
    published = {}
    # Fixed IQS code root already contains the reviewed wire contracts.
    for row in index["files"]["invest-quick-scan"]:
        assert sha((ROOT / row["path"]).read_bytes()) == row["execution_sha256"]
    for project in ("StockWiki", "StockQAbyLLM"):
        repo = ROOT.parent / project
        rows = index["files"][project]
        paths = [r["path"] for r in rows]
        state = states[project]
        assert git(repo, "rev-parse", "HEAD").decode().strip() == state["head"]
        assert git(repo, "status", "--porcelain=v1", "-uall").decode().replace("\r\n", "\n") == state["status"]
        for row in rows:
            p = repo / row["path"]
            if row["baseline_execution_sha256"] is None:
                assert not p.exists()
            else:
                assert sha(p.read_bytes()) == row["baseline_execution_sha256"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((OUT / "candidate-source-02" / project / row["path"]).read_bytes())
            regular(p, repo)
        assert all(sha((repo/n).read_bytes()) == h for n,h in state["protected_nonsecret_source_sha256"].items())
        git(repo, "add", "--", *paths)
        staged = set(filter(None, git(repo, "diff", "--cached", "--name-only", "-z").decode().split("\0")))
        assert staged == set(paths)
        domains = {}
        for row in rows:
            original = (repo / row["path"]).read_bytes()
            blob = git(repo, "show", ":" + row["path"])
            assert original == blob or original.replace(b"\r\n", b"\n") == blob, row["path"]
            assert sha(original) == row["execution_sha256"]
            domains[row["path"]] = dict(execution_sha256=sha(original), Git_blob_sha256=sha(blob),
                                        EOL_only_serialization=original != blob)
        save(project + "-staged-domains.json", domains)
        git(repo, "diff", "--cached", "--check", label=project + "-diff-check")
        git(repo, "commit", "-m", "Persist modular quick scan routes and execute incremental refresh safely",
            label=project + "-commit")
        commit = git(repo, "rev-parse", "HEAD").decode().strip()
        changed = set(filter(None, git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit).decode().split("\0")))
        assert changed == set(paths)
        assert git(repo, "status", "--porcelain=v1", "-uall").decode().replace("\r\n", "\n") == state["status"]
        assert all(sha((repo/n).read_bytes()) == h for n,h in state["protected_nonsecret_source_sha256"].items())
        for name, pair in domains.items():
            assert sha(git(repo, "show", commit + ":" + name)) == pair["Git_blob_sha256"]
            assert sha((repo/name).read_bytes()) == pair["execution_sha256"]
        remote = None
        if project == "StockQAbyLLM":
            assert "origin" in state["remote_names"]
            git(repo, "push", "origin", "master", label=project + "-push")
            remote = git(repo, "ls-remote", "origin", "refs/heads/master").decode().split()[0]
            assert remote == commit
        else:
            assert state["remote_names"] == [], "Preserve existing owner decision 7"
        published[project] = dict(commit=commit, remote_head=remote, paths=paths,
             protected_files_unchanged=len(state["protected_nonsecret_source_sha256"]),
             original_unknowns_preserved=True, source_worktree_and_Git_domains=domains)
        save(project + "-result.json", published[project])
    save("result.json", dict(protocol="iqs.w15_foundation_publication/1.0.0", sources=published,
         source_published=True, normal_hooks=True, force_push=False, production_DB_migrations=0,
         API_requests=0, whole_W15_complete=False, financial_accuracy_validated=False,
         cleanup_pending=str(OWN)))


if __name__ == "__main__":
    PUB.mkdir(exist_ok=True)
    if sys.argv[1] == "preflight":
        preflight(sys.argv[2])
        print("Source preflight unchanged; no source write.")
    elif sys.argv[1] == "apply":
        apply()
    else:
        raise ValueError("preflight or apply required")
