"""One-shot publication of four previously explicitly authorized Markdown paths."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[5]
RECEIPT = ROOT / "docs/implementation/intake/parallel-packages/2026-10-10/evid-remediation-01/documentation-publication.json"
PATHS = ["task_plan.md", "progress.md", "findings.md", "docs/implementation/handoff-for-new-agent.md"]
assert not RECEIPT.exists()
events = []

def run(args):
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, timeout=120)
    event = {"args": args, "exit_code": proc.returncode, "stdout": proc.stdout.decode("utf-8", errors="replace"),
             "stderr": proc.stderr.decode("utf-8", errors="replace")}
    events.append(event)
    if proc.returncode:
        raise RuntimeError(event)
    return proc.stdout

sha = lambda blob: hashlib.sha256(blob).hexdigest()
record = {"paths": PATHS, "scope": "four approved first-party Markdown only; no Lab/source/raw fixture/database/repair card exported"}
try:
    assert not run(["diff", "--cached", "--name-only"]).strip()
    assert run(["rev-parse", "HEAD"]).decode().strip() == "9c2f5fed369bfda83e6c23f6b96fe736cad3e899"
    assert run(["branch", "--show-current"]).decode().strip() == "master"
    assert run(["remote", "get-url", "origin"]).decode().strip() == "https://github.com/zhengcb81/invest-quick-scan.git"
    assert all("2026-10-11 EVID R1续验收口" in (ROOT / p).read_text(encoding="utf-8") for p in PATHS)
    record["working_tree_raw_sha256"] = {p: sha((ROOT / p).read_bytes()) for p in PATHS}
    run(["add", "--", *PATHS])
    assert set(run(["diff", "--cached", "--name-only"]).decode().splitlines()) == set(PATHS)
    run(["diff", "--cached", "--check"])
    staged = {p: sha(run(["show", ":" + p])) for p in PATHS}
    run(["commit", "-m", "docs: record concentrated EVID R1 acceptance and clean handoff"])
    assert not run(["diff", "--cached", "--name-only"]).strip()
    commit = run(["rev-parse", "HEAD"]).decode().strip()
    assert set(run(["diff-tree", "--no-commit-id", "--name-only", "-r", commit]).decode().splitlines()) == set(PATHS)
    committed = {p: sha(run(["show", commit + ":" + p])) for p in PATHS}
    assert staged == committed
    run(["push", "origin", "HEAD:refs/heads/master"])
    remote = run(["ls-remote", "--exit-code", "origin", "refs/heads/master"]).decode().split()[0]
    assert remote == commit
    record.update(status="published", commit=commit, remote_commit=remote,
                  staged_sha256=staged, committed_sha256=committed)
except Exception as exc:
    record.update(status="failed", error=str(exc))
    raise
finally:
    record["events"] = events
    with RECEIPT.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
print(json.dumps({k: v for k, v in record.items() if k not in {"events", "working_tree_raw_sha256", "staged_sha256", "committed_sha256"}}))
