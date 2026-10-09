"""Close local-only source publication (existing owner decision 7) and inventory own scratch."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

IQS = Path(__file__).resolve().parents[5]
SW = IQS.parent / "StockWiki"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-jr13/stockwiki-publication"
OWN = IQS / "runs/s13p"
COMMIT = "6c46f03b486d215d696d32bee618793bc7fcb410"
env = {k: v for k, v in os.environ.items() if k.upper() in {
    "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE",
    "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=SW, env=env)


def save(name, value):
    path = OUT / name
    assert not path.exists()
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


prior = json.loads((OUT / "input.json").read_bytes())
resume = json.loads((OUT / "resume-input.json").read_bytes())
expected = resume["reviewed_execution_sha256"]
published = resume["expected_git_blob_sha256"]
protected = prior["protected_nonsecret_source_sha256"]
assert git("rev-parse", "HEAD").decode().strip() == COMMIT
assert git("rev-parse", "HEAD^").decode().strip() == prior["source_base"]
assert git("branch", "--show-current").decode().strip() == "master"
assert not git("remote").strip() and not git("status", "--porcelain=v1").strip()
assert set(filter(None, git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", COMMIT).decode().split("\0"))) == set(expected)
for name, digest in expected.items():
    assert sha((SW / name).read_bytes()) == digest
    assert sha(git("show", COMMIT + ":" + name)) == published[name]
assert all(sha((SW / name).read_bytes()) == digest for name, digest in protected.items())
assert json.loads((OUT / "commit.process.json").read_bytes())["returncode"] == 0
assert b"Passed" in (OUT / "commit.stderr.log").read_bytes()
save("result.json", dict(schema="jr13-stockwiki-publication/1", source_published=True,
    source_commit=COMMIT, source_base=prior["source_base"], source_status="",
    remote_policy="local_only_existing_owner_decision_7", remote_names=[], remote_head=None,
    pushed=False, failed_push_receipt="push.process.json", no_remote_added=True,
    published_paths=list(expected), reviewed_execution_sha256=expected,
    published_git_blob_sha256=published, serialization_only_test_path="tests/test_quick_scan_delivery.py",
    publication_eol_note_sha256=resume["publication_eol_note_sha256"],
    protected_files_unchanged=len(protected), normal_hooks=True, forced_push=False,
    model_API_requests=0, production_DB_migrations=0, observation_schema_supported=2,
    public_ack_schema="1.0.0", global_gates_closed=False,
    test_evidence="affected-final-04 113P + joint-07 18P; execution bytes unchanged",
    cleanup_pending=str(OWN)))
assert OWN.resolve() == IQS / "runs/s13p" and OWN.parent.resolve() == IQS / "runs"
files, directories = [], []
for parent, children, names in os.walk(OWN, followlinks=False):
    p = Path(parent)
    ps = os.lstat(p)
    assert stat.S_ISDIR(ps.st_mode) and not getattr(ps, "st_file_attributes", 0) & 0x400
    if p != OWN:
        directories.append(p.relative_to(OWN).as_posix())
    for name in names:
        f = p / name
        s = os.lstat(f)
        assert stat.S_ISREG(s.st_mode) and s.st_nlink == 1
        assert not getattr(s, "st_file_attributes", 0) & 0x400 and f.resolve().is_relative_to(OWN)
        raw = f.read_bytes()
        files.append(dict(path=f.relative_to(OWN).as_posix(), size=len(raw), sha256=sha(raw), nlink=s.st_nlink))
save("cleanup-inventory.json", dict(schema="owned-publication-cleanup/1", exact_root=str(OWN),
    root_parent=str(OWN.parent), files=files, directories=directories,
    file_count=len(files), directory_count=len(directories), reparse_points=0, hard_links=0,
    source_commit=COMMIT, source_execution_sha256=expected, protected_nonsecret_source_sha256=protected,
    real_os_lstat=True, remove_source_or_shared_temp=False))
print(json.dumps(dict(source_commit=COMMIT, source_status="", remote_policy="local_only", files=len(files), directories=len(directories))))
