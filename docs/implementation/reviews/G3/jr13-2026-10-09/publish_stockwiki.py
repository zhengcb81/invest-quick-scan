"""Publish the already reviewed five exact StockWiki files after broad consent.

No production DB migration, no paid API, no test replay, no hook bypass.
Run once; never restart a partially completed publication blindly.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time

IQS = Path(__file__).resolve().parents[5]
SW = IQS.parent / "StockWiki"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-jr13"
OWN = IQS / "runs/s13p"
BASE = "c40de21403720306ba21edbf71b9634a40ee58f8"

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    dest = OUT / "stockwiki-publication"
    assert not dest.exists() and not OWN.exists()
    assert OWN.absolute() == IQS / "runs/s13p" and OWN.parent.resolve() == OWN.parent.absolute()
    OWN.mkdir()
    (OWN / "tmp").mkdir()
    dest.mkdir()
    env = {k:v for k,v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE",
        "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1",
        PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PRE_COMMIT_HOME=str(OWN / "pc"),
        RUFF_CACHE_DIR=str(OWN / "ruff"), TEMP=str(OWN / "tmp"), TMP=str(OWN / "tmp"),
        TMPDIR=str(OWN / "tmp"))
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=SW, env=env)
    def save(name, value):
        p = dest / name
        assert not p.exists()
        p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    assert git("branch", "--show-current").decode().strip() == "master"
    assert not git("status", "--porcelain=v1").strip()
    assert not git("diff", "--cached", "--name-only", "-z")
    lock = json.loads((OUT / "final-snapshot/execution-lock.json").read_bytes())
    review_path = IQS / "docs/implementation/reviews/G3/jr13-2026-10-09/compatibility-recheck.json"
    review = json.loads(review_path.read_bytes())
    assert review["software_open_findings"] == 0 and review["outcome"] == "limited_software_signed_off"
    expected = lock["candidate_sha256"]
    assert expected == review["candidate_sha256"] and len(expected) == 5
    diff = json.loads((OUT / "source-candidate-diff.json").read_bytes())
    rows = {r["path"]:r for r in diff["paths"]}
    assert set(rows) == set(expected) and diff["base_head"] == BASE
    raw = {}
    for name, digest in expected.items():
        p = SW / name
        assert p.resolve().is_relative_to(SW.resolve()) and not p.is_symlink()
        assert p.lstat().st_nlink == 1 and not getattr(p.lstat(), "st_file_attributes", 0) & 0x400
        assert sha(git("show", BASE+":"+name)) == rows[name]["base_sha256"]
        raw[name] = (OUT / "final-snapshot/candidate" / name).read_bytes()
        assert sha(raw[name]) == rows[name]["candidate_sha256"] == digest
    names = [r["path"] for r in json.loads((OUT / "input-01.json").read_bytes())["source_files"]]
    protected = {n:sha((SW / n).read_bytes()) for n in names if n not in expected}
    save("input.json", dict(source_base=BASE, source_status="", candidate_sha256=expected,
        protected_nonsecret_source_sha256=protected, authorized_paths=list(expected),
        authorization='User: 给你全部后续所需的授权', normal_hooks=True,
        owned_runtime=str(OWN), model_API_requests=0, production_DB_migrations=0))
    assert git("rev-parse", "HEAD").decode().strip() == BASE and not git("status", "--porcelain=v1").strip()
    for name, data in raw.items():
        (SW / name).write_bytes(data)
    assert all(sha((SW / n).read_bytes()) == d for n,d in expected.items())
    assert all(sha((SW / n).read_bytes()) == d for n,d in protected.items())
    changed = set(filter(None, git("diff", "--name-only", "-z").decode().split("\0")))
    assert changed == set(expected)
    git("add", "--", *expected)
    assert set(filter(None, git("diff", "--cached", "--name-only", "-z").decode().split("\0"))) == set(expected)
    for name, digest in expected.items():
        assert sha(git("show", ":"+name)) == digest
    def recorded(label, args):
        started = time.monotonic()
        proc = subprocess.run(["git", *args], cwd=SW, env=env, capture_output=True, timeout=240)
        (dest / (label+".stdout.log")).write_bytes(proc.stdout)
        (dest / (label+".stderr.log")).write_bytes(proc.stderr)
        save(label+".process.json", dict(argv=["git", *args], cwd=str(SW),
            returncode=proc.returncode, wall_s=round(time.monotonic()-started, 3),
            stdout_sha256=sha(proc.stdout), stderr_sha256=sha(proc.stderr)))
        print(proc.stdout.decode("utf-8", errors="replace")[-2200:])
        print(proc.stderr.decode("utf-8", errors="replace")[-2200:])
        assert proc.returncode == 0, label
    recorded("commit", ["commit", "-m", "Preserve strict quick scan ACKs and historical replay atomically"])
    commit = git("rev-parse", "HEAD").decode().strip()
    assert set(filter(None, git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit).decode().split("\0"))) == set(expected)
    for name, digest in expected.items():
        assert sha(git("show", commit+":"+name)) == sha((SW / name).read_bytes()) == digest
    assert all(sha((SW / n).read_bytes()) == d for n,d in protected.items())
    assert not git("status", "--porcelain=v1").strip()
    recorded("push", ["push", "origin", "master"])
    remote = git("ls-remote", "origin", "refs/heads/master").decode().split()[0]
    assert remote == commit
    result = dict(schema="jr13-stockwiki-publication/1", source_published=True,
        source_commit=commit, remote_head=remote, source_base=BASE, source_status="",
        published_paths=list(expected), published_git_blob_sha256=expected,
        protected_files_unchanged=len(protected), normal_hooks=True, forced_push=False,
        model_API_requests=0, production_DB_migrations=0, observation_schema_supported=2,
        public_ack_schema="1.0.0", global_gates_closed=False,
        test_evidence="affected-final-04 113P + joint-07 18P; unchanged reviewed execution bytes",
        cleanup_pending=str(OWN))
    save("result.json", result)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
