"""Continue the recorded EOF-check failure without overwriting its receipt."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[5]
INTAKE = ROOT / "docs/implementation/intake/parallel-packages/2026-10-10/evid-remediation-01"
RECEIPT = INTAKE / "documentation-publication-retry.json"
PATHS = ["task_plan.md", "progress.md", "findings.md", "docs/implementation/handoff-for-new-agent.md"]
assert not RECEIPT.exists()
prior = json.loads((INTAKE / "documentation-publication.json").read_text(encoding="utf-8"))
assert prior["status"] == "failed" and prior["events"][-1]["args"] == ["diff", "--cached", "--check"]
events = []
def run(args):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, timeout=120)
    events.append({"args": args, "exit_code": p.returncode, "stdout": p.stdout.decode("utf-8", errors="replace"), "stderr": p.stderr.decode("utf-8", errors="replace")})
    if p.returncode:
        raise RuntimeError(events[-1])
    return p.stdout
sha = lambda blob: hashlib.sha256(blob).hexdigest()
record = {"paths": PATHS, "scope": "same four explicitly approved Markdown; continue owned staging from whitespace failure; private files excluded"}
try:
    assert run(["rev-parse", "HEAD"]).decode().strip() == "9c2f5fed369bfda83e6c23f6b96fe736cad3e899"
    assert run(["branch", "--show-current"]).decode().strip() == "master"
    assert run(["remote", "get-url", "origin"]).decode().strip() == "https://github.com/zhengcb81/invest-quick-scan.git"
    assert set(run(["diff", "--cached", "--name-only"]).decode().splitlines()) == set(PATHS)
    # Prior publisher staged exactly these raw LF Markdown bytes before failing.
    assert {p: sha(run(["show", ":" + p])) for p in PATHS} == prior["working_tree_raw_sha256"]
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
    record.update(status="published", commit=commit, remote_commit=remote, staged_sha256=staged, committed_sha256=committed)
except Exception as exc:
    record.update(status="failed", error=str(exc)); raise
finally:
    record["events"] = events
    with RECEIPT.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(record, f, ensure_ascii=False, indent=2); f.write("\n")
print(json.dumps({k: v for k, v in record.items() if k not in {"events", "working_tree_raw_sha256", "staged_sha256", "committed_sha256"}}))
