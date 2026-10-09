"""One-time resume of staged JR13 publication; explicit Git/execution byte domains.

Never restage, rewrite sources, bypass hooks, force push, or restart after a commit.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

IQS = Path(__file__).resolve().parents[5]
SW = IQS.parent / "StockWiki"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-jr13/stockwiki-publication"
OWN = IQS / "runs/s13p"
BASE = "c40de21403720306ba21edbf71b9634a40ee58f8"
TEST = "tests/test_quick_scan_delivery.py"
NOTE_SHA = "47e9f66b3a3190e2bb3842c305fe8a20b8fc4491065d22442d079f7fb6b895c6"
GIT_TEST_SHA = "bda18d2e691fc037d955136f80f1e7cb9bed4bdaed95d693f5ac89867fbba4aa"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    assert OUT.is_dir() and OWN.is_dir() and not (OUT / "resume-input.json").exists()
    assert OWN.parent.resolve() == IQS / "runs" and OWN.resolve() == OWN.absolute()
    env = {k: v for k, v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE",
        "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1",
               PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PRE_COMMIT_HOME=str(OWN / "pc"),
               RUFF_CACHE_DIR=str(OWN / "ruff"), TEMP=str(OWN / "tmp"), TMP=str(OWN / "tmp"),
               TMPDIR=str(OWN / "tmp"))

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=SW, env=env)

    def save(name, value):
        path = OUT / name
        assert not path.exists()
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    prior = json.loads((OUT / "input.json").read_bytes())
    note_raw = (Path(__file__).parent / "publication-eol-note.json").read_bytes()
    assert sha(note_raw) == NOTE_SHA
    note = json.loads(note_raw)
    assert note["outcome"] == "publication_serialization_only_accepted"
    assert note["normal_publication_may_continue_with_explicit_two_domains"] is True
    assert sha((OUT / "input.json").read_bytes()) == note["input_sha256"]
    assert sha((OUT / "eol-diagnostic.json").read_bytes()) == note["eol_diagnostic_sha256"]
    expected = prior["candidate_sha256"]
    assert len(expected) == 5 and set(expected) == set(note["staged_paths"])
    published = dict(expected, **{TEST: GIT_TEST_SHA})
    protected = prior["protected_nonsecret_source_sha256"]
    assert len(protected) == 326
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    assert git("branch", "--show-current").decode().strip() == "master"
    assert not git("ls-files", "--others", "--exclude-standard", "-z")
    assert set(filter(None, git("diff", "--cached", "--name-only", "-z").decode().split("\0"))) == set(expected)
    assert (SW / ".git/hooks/pre-commit").is_file(), "normal pre-commit hook must exist"
    for name, digest in expected.items():
        raw = (SW / name).read_bytes()
        indexed = git("show", ":" + name)
        assert sha(raw) == digest and sha(indexed) == published[name]
        if name == TEST:
            assert indexed == raw.replace(b"\r\n", b"\n") and raw.count(b"\r\n") == 496
            assert ast.dump(ast.parse(raw), include_attributes=False) == ast.dump(ast.parse(indexed), include_attributes=False)
        else:
            assert indexed == raw
    assert all(sha((SW / name).read_bytes()) == digest for name, digest in protected.items())
    save("resume-input.json", dict(schema="jr13-publication-resume/1", source_base=BASE,
        authorization="User: 给你全部后续所需的授权", resume_from="first-attempt-note.json",
        reviewed_execution_sha256=expected, expected_git_blob_sha256=published,
        publication_eol_note_sha256=NOTE_SHA, protected_files_unchanged=len(protected),
        owned_runtime=str(OWN), normal_hooks=True, source_rewritten=False,
        restage=False, model_API_requests=0, production_DB_migrations=0))

    def recorded(label, args):
        started = time.monotonic()
        proc = subprocess.Popen(["git", *args], cwd=SW, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        save(label + ".start.json", dict(pid=proc.pid, argv=["git", *args], cwd=str(SW)))
        try:
            stdout, stderr = proc.communicate(timeout=240)
        except subprocess.TimeoutExpired:
            # Do not pretend children are terminal or blindly retry on an unknown commit.
            save(label + ".timeout.json", dict(pid=proc.pid, terminal_confirmed=False))
            raise
        (OUT / (label + ".stdout.log")).write_bytes(stdout)
        (OUT / (label + ".stderr.log")).write_bytes(stderr)
        save(label + ".process.json", dict(pid=proc.pid, argv=["git", *args], cwd=str(SW),
            terminal_confirmed=True, returncode=proc.returncode, wall_s=round(time.monotonic() - started, 3),
            stdout_sha256=sha(stdout), stderr_sha256=sha(stderr)))
        print(stdout.decode("utf-8", errors="replace")[-1800:], flush=True)
        print(stderr.decode("utf-8", errors="replace")[-1800:], flush=True)
        assert proc.returncode == 0, label

    recorded("commit", ["commit", "-m", "Preserve strict quick scan ACKs and historical replay atomically"])
    commit = git("rev-parse", "HEAD").decode().strip()
    assert commit != BASE
    assert git("rev-parse", "HEAD^").decode().strip() == BASE
    assert set(filter(None, git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit).decode().split("\0"))) == set(expected)
    for name, digest in expected.items():
        assert sha((SW / name).read_bytes()) == digest
        assert sha(git("show", commit + ":" + name)) == published[name]
    assert all(sha((SW / name).read_bytes()) == digest for name, digest in protected.items())
    assert not git("status", "--porcelain=v1").strip()
    recorded("push", ["push", "origin", "master"])
    remote = git("ls-remote", "origin", "refs/heads/master").decode().split()[0]
    assert remote == commit
    save("result.json", dict(schema="jr13-stockwiki-publication/1", source_published=True,
        source_commit=commit, remote_head=remote, source_base=BASE, source_status="",
        published_paths=list(expected), reviewed_execution_sha256=expected,
        published_git_blob_sha256=published, serialization_only_test_path=TEST,
        publication_eol_note_sha256=NOTE_SHA, protected_files_unchanged=len(protected),
        normal_hooks=True, forced_push=False, model_API_requests=0, production_DB_migrations=0,
        observation_schema_supported=2, public_ack_schema="1.0.0", global_gates_closed=False,
        test_evidence="affected-final-04 113P + joint-07 18P; reviewed execution bytes unchanged",
        cleanup_pending=str(OWN)))
    print(json.dumps(dict(source_commit=commit, remote_head=remote, source_status="", normal_hooks=True)), flush=True)


if __name__ == "__main__":
    main()
