"""Exact-path IQS delivery with staged raw-byte proof and a normal push."""
import hashlib
import argparse
import json
from pathlib import Path
import subprocess

IQS = Path(__file__).resolve().parents[5]
INDEX = Path(__file__).resolve().parent / "artifacts.json"
EXPECTED_HEAD = "6d33a9bd9c8e5c5f6eb4504d7875d08fd3558895"
META = (".gitattributes", "task_plan.md", "progress.md", "findings.md",
        "docs/implementation/handoff-for-new-agent.md")


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(IQS), *args])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-staged", action="store_true")
    args = parser.parse_args()
    assert git("rev-parse", "HEAD").decode().strip() == EXPECTED_HEAD
    assert git("branch", "--show-current").decode().strip() == "master"
    staged_before = set(git("diff", "--cached", "--name-only").decode().splitlines())
    if not args.resume_staged:
        assert not staged_before
        assert set(git("diff", "--name-only").decode().splitlines()) == set(META)
    catalog = json.loads(INDEX.read_text("utf-8"))
    rows = catalog["artifacts"]
    paths = [row["path"] for row in rows] + [INDEX.relative_to(IQS).as_posix(), *META]
    assert len(paths) == len(set(paths))
    if args.resume_staged:
        assert staged_before == set(paths), "Do not absorb another writer's staged paths"
        assert set(git("diff", "--name-only", "HEAD").decode().splitlines()) == set(paths)
    assert "opencode.json" not in paths
    for row in rows:
        raw = (IQS / row["path"]).read_bytes()
        assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
    git("add", "-f", "--", *paths)
    assert set(git("diff", "--cached", "--name-only").decode().splitlines()) == set(paths)
    for row in rows:
        raw = git("show", ":"+row["path"])
        assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "Staged raw mismatch: "+row["path"]
    assert git("show", ":"+INDEX.relative_to(IQS).as_posix()) == INDEX.read_bytes()
    commands = [
        ["git", "-C", str(IQS), "-c", "core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol", "diff", "--cached", "--check"],
        ["git", "-C", str(IQS), "commit", "--quiet", "-m", "fix(quick-scan): deliver reviewed JR2 receiver binding and evidence"],
        ["git", "-C", str(IQS), "push", "origin", "HEAD:master"],
    ]
    for index, command in enumerate(commands):
        result = subprocess.run(command, capture_output=True)
        if result.returncode:
            print(json.dumps(dict(step=index, returncode=result.returncode, stopped=True)))
            print(result.stdout.decode("utf-8", "replace"))
            print(result.stderr.decode("utf-8", "replace"))
            return
    head = git("rev-parse", "HEAD").decode().strip()
    assert head == git("rev-parse", "origin/master").decode().strip()
    status = git("status", "--porcelain=v1").decode()
    assert status == "?? opencode.json\n", "Record concurrent changes instead of removing them"
    print(json.dumps(dict(result_commit=head, pushed_origin_master=True,
        precise_staged_files=len(paths), indexed_raw_files=len(rows), original_opencode_preserved=True)))


if __name__ == "__main__":
    main()
