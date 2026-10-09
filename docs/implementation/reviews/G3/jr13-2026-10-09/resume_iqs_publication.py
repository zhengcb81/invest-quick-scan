"""Normal scoped IQS archive Git publication; never writes another repository."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

IQS = Path(__file__).resolve().parents[5]
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-jr13"
REVIEW = IQS / "docs/implementation/reviews/G3/jr13-2026-10-09"
BASE = "54703f40168f9c507868864fd8ddb97d7eb65292"
ROOT_PATHS = [".gitattributes", "task_plan.md", "progress.md", "findings.md",
              "docs/implementation/handoff-for-new-agent.md"]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    assert not (IQS / "runs/r13a").exists()
    receipt = json.loads((OUT / "cleanup-receipt.json").read_text("utf-8-sig"))
    assert receipt["applied"] and receipt["files_deleted"] == 5029
    dest = OUT / "iqs-publication"
    assert dest.exists() and not (dest / "result.json").exists()
    env = {k:v for k,v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE",
        "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=IQS, env=env)
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    assert git("branch", "--show-current").decode().strip() == "master"
    prior_staged = set(filter(None, git("diff", "--cached", "--name-only", "-z").decode().split("\0")))
    before = git("status", "--porcelain=v1", "-z").decode().split("\0")
    for entry in filter(None, before):
        name = entry[3:]
        assert name in ROOT_PATHS + ["opencode.json"] or name.startswith((
            "docs/implementation/intake/G3/2026-10-09-jr13/",
            "docs/implementation/reviews/G3/jr13-2026-10-09/")), entry
    paths = sorted(set(ROOT_PATHS + [p.relative_to(IQS).as_posix()
        for folder in [OUT, REVIEW] for p in folder.rglob("*") if p.is_file()]))
    assert "opencode.json" not in paths and all("\n" not in n for n in paths)
    for name in paths:
        p = IQS / name
        assert p.resolve().is_relative_to(IQS.resolve()) and not p.is_symlink()
        assert not getattr(p.lstat(), "st_file_attributes", 0) & 0x400 and p.lstat().st_nlink == 1
    expected = {name:sha((IQS / name).read_bytes()) for name in paths}
    assert prior_staged.issubset(set(paths))
    index = dest / "selected-resume.json"
    assert not index.exists()
    index.write_text(json.dumps(dict(base=BASE, selected=expected,
        preserved_unknown="opencode.json (not read or staged)", source_written=False),
        indent=2) + "\n", encoding="utf-8")
    paths.append(index.relative_to(IQS).as_posix())
    expected[paths[-1]] = sha(index.read_bytes())
    for offset in range(0, len(paths), 100):
        git("add", "-f", "--", *paths[offset:offset+100])
    staged = set(filter(None, git("diff", "--cached", "--name-only", "-z").decode().split("\0")))
    assert staged == set(paths)
    object_ids = {}
    for entry in filter(None, git("ls-files", "--stage", "-z").decode().split("\0")):
        meta, name = entry.split("\t", 1)
        if name in expected:
            _, oid, stage = meta.split()
            assert stage == "0"
            object_ids[name] = oid
    assert set(object_ids) == set(paths)
    child = subprocess.Popen(["git", "cat-file", "--batch"], cwd=IQS, env=env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    payload, error = child.communicate(("\n".join(object_ids[n] for n in paths)+"\n").encode(), timeout=120)
    assert child.returncode == 0, error.decode("utf-8", errors="replace")
    cursor = 0
    for name in paths:
        end = payload.index(b"\n", cursor)
        oid, kind, size = payload[cursor:end].decode().split()
        cursor = end + 1
        size = int(size)
        raw = payload[cursor:cursor+size]
        assert oid == object_ids[name] and kind == "blob" and sha(raw) == expected[name], name
        assert sha((IQS / name).read_bytes()) == expected[name], name
        cursor += size + 1
    assert cursor == len(payload)
    # No skipped hooks, no forced push, no foreign source writes.
    def recorded(label, args):
        proc = subprocess.run(["git", *args], cwd=IQS, env=env, capture_output=True, timeout=240)
        (dest / (label+".stdout.log")).write_bytes(proc.stdout)
        (dest / (label+".stderr.log")).write_bytes(proc.stderr)
        print(proc.stdout.decode("utf-8", errors="replace")[-1600:])
        print(proc.stderr.decode("utf-8", errors="replace")[-1600:])
        assert proc.returncode == 0, label
    recorded("commit", ["commit", "-m", "Archive JR1 JR3 verified candidate and publication handoff"])
    commit = git("rev-parse", "HEAD").decode().strip()
    assert set(filter(None, git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit).decode().split("\0"))) == set(paths)
    recorded("push", ["push", "origin", "master"])
    remote = git("ls-remote", "origin", "refs/heads/master").decode().split()[0]
    assert remote == commit
    result = dict(schema="jr13-iqs-archive-publication/1", before=BASE, commit=commit,
        remote_head=remote, selected_paths=len(paths), staged_blob_sha256_all_equal=True,
        source_written=False, StockWiki_publication="pending_fifth_path_authorization",
        normal_hooks=True, force_push=False, preserved_unknown="opencode.json")
    (dest / "result.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result))

if __name__ == "__main__":
    main()
