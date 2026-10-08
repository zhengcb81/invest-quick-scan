"""Stage exactly the reviewed seven paths, normal owner hooks and normal push."""
import hashlib
import json
from pathlib import Path
import subprocess

IQS = Path(__file__).resolve().parents[5]
OUT = IQS / "docs/implementation/intake/G3/2026-10-08-jr2"
SOURCE = Path("C:/Users/郑曾波/Projects/StockQAbyLLM")


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(SOURCE), *args])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    log = OUT / "verification/source-git"
    log.mkdir(parents=True, exist_ok=False)
    release = json.loads((OUT / "approval-for-publish.json").read_text("utf-8"))
    snap = OUT / "snapshots" / release["snapshot_label"]
    manifest = json.loads((snap / "source.json").read_text("utf-8"))
    assert digest((snap / "source.json").read_bytes()) == release["reviewed_source_sha256"]
    baseline = manifest["source_baseline"]
    rows = manifest["changed_files"]
    names = [row["path"] for row in rows]
    assert len(names) == 7 and git("rev-parse", "HEAD").decode().strip() == baseline["head"]
    assert not git("diff", "--cached", "--name-only"), "An unrelated staged change exists"
    changed = set(git("diff", "--name-only").decode().splitlines())
    assert changed == set(names), "Tracked source changes drifted"
    for row in rows:
        assert digest((SOURCE / row["path"]).read_bytes()) == row["sha256"]
    original_untracked = baseline["status"].splitlines()
    assert [line for line in git("status", "--porcelain=v1").decode().splitlines() if line.startswith("?? ")] == original_untracked
    git("add", "--", *names)
    assert set(git("diff", "--cached", "--name-only").decode().splitlines()) == set(names)
    staged = []
    for row in rows:
        raw = git("show", ":"+row["path"])
        assert digest(raw) in {row["sha256"], row["normalized_lf_sha256"]}
        staged.append(dict(path=row["path"], sha256=digest(raw), bytes=len(raw),
                           same_raw=digest(raw)==row["sha256"]))
    (log / "staged-source.json").write_text(json.dumps(staged, ensure_ascii=False, indent=2)+"\n", "utf-8")
    commands = [
        ["git", "-C", str(SOURCE), "diff", "--cached", "--check"],
        ["git", "-C", str(SOURCE), "commit", "--quiet", "-m", "fix(quick-scan): bind receiver target before delivery"],
        ["git", "-C", str(SOURCE), "push", "origin", "HEAD:master"],
    ]
    receipts = []
    for index, command in enumerate(commands):
        result = subprocess.run(command, capture_output=True)
        (log / f"{index:02}.stdout.log").write_bytes(result.stdout)
        (log / f"{index:02}.stderr.log").write_bytes(result.stderr)
        receipts.append(dict(command=command, returncode=result.returncode))
        (log / "commands.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2)+"\n", "utf-8")
        if result.returncode:
            print(json.dumps(dict(step=index, returncode=result.returncode, stopped=True)))
            return
        if index == 1:
            # Hook rewriting is a new change, not silently covered by the old GREEN.
            for row in rows:
                assert digest((SOURCE / row["path"]).read_bytes()) == row["sha256"], "Owner hook changed raw source; reverify before push"
            assert set(git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").decode().splitlines()) == set(names)
    head = git("rev-parse", "HEAD").decode().strip()
    remote = git("rev-parse", "origin/master").decode().strip()
    assert head == remote
    status = git("status", "--porcelain=v1").decode()
    assert status == baseline["status"]
    result = dict(schema="jr2_source_git/1", baseline_head=baseline["head"], result_commit=head,
                  pushed_origin_master=True, source_status_preserved=True, staged_files=7,
                  original_untracked=status, commands=receipts)
    (OUT / "source-git-receipt.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", "utf-8")
    print(json.dumps(dict(result_commit=head, normal_push=True, source_status_preserved=True, staged_files=7)))


if __name__ == "__main__":
    main()
