"""Index final immutable evidence once, then deliver exact IQS paths normally."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

IQS = Path(__file__).resolve().parents[5]
REVIEW = Path(__file__).resolve().parent
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-model-resolution"
INDEX = REVIEW / "artifacts.json"
EXPECTED_HEAD = "bc6e63a38b59b8faf52c64adeda4dfa7efeaaacf"
META = (".gitattributes", "task_plan.md", "progress.md", "findings.md",
        "docs/implementation/handoff-for-new-agent.md")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(IQS), *args])


def verify():
    delivery = json.loads((OUT / "source-git-receipt.json").read_text("utf-8"))
    release_name = delivery["release_file"]
    assert release_name in {"approval-for-publish.json", "approval-for-publish-eol.json"}
    release_raw = (OUT / release_name).read_bytes()
    assert sha(release_raw) == delivery["release_sha256"]
    release = json.loads(release_raw)
    assert release["approved_for_model_resolution_publish"] is True
    assert release["reviewed_source_sha256"] == delivery["reviewed_source_sha256"]
    manifest_raw = (OUT / "snapshots" / release["snapshot_label"] / "source.json").read_bytes()
    assert sha(manifest_raw) == release["reviewed_source_sha256"]
    manifest = json.loads(manifest_raw)
    log = OUT / "verification" / manifest["test_label"]
    receipt = json.loads((log / "process.json").read_text("utf-8"))
    assert receipt["returncode"] == 0 and not receipt["timeout"] and receipt["executed_source_unchanged"]
    suites = ET.parse(log / "junit.xml").getroot()
    totals = {key: sum(int(s.get(key, "0")) for s in suites.iter("testsuite"))
              for key in ("tests", "failures", "errors", "skipped")}
    assert totals == release["approved_junit_totals"] and totals["tests"] > 0, totals
    assert all(totals[key] == 0 for key in ("failures", "errors", "skipped"))
    changed = manifest["changed_files"]
    assert [row["path"] for row in changed] == release["approved_paths"]
    for row in changed:
        raw = (OUT / "snapshots" / release["snapshot_label"] / "source" / row["path"]).read_bytes()
        assert sha(raw) == row["sha256"] and len(raw) == row["bytes"]
        assert receipt["executed_source_hashes"].get(row["path"]) == row["sha256"]
    final = json.loads((OUT / "verification/final-verification.json").read_text("utf-8"))
    assert final["result_commit"] == delivery["result_commit"]
    assert final["reviewed_source_sha256"] == release["reviewed_source_sha256"]
    assert final["release_file"] == release_name and final["final_test_label"] == manifest["test_label"]
    assert final["exact_final_raw_files_match"] and final["authorized_changed_files"] == len(changed)
    cleanup = json.loads((OUT / "cleanup-receipt.json").read_text("utf-8-sig"))
    assert cleanup["applied"] and cleanup["process_matches"] == 0
    assert cleanup["files_deleted"] == cleanup["files_verified"]
    assert not Path(cleanup["root"]).exists()
    jsons = python_files = 0
    rows = []
    for root in (OUT, REVIEW):
        for path in sorted(root.rglob("*")):
            assert not path.is_symlink()
            if not path.is_file() or path == INDEX:
                continue
            raw = path.read_bytes()
            if path.suffix == ".json":
                json.loads(raw.decode("utf-8-sig"))
                jsons += 1
            elif path.suffix == ".py":
                ast.parse(raw.decode("utf-8-sig"), filename=str(path))
                python_files += 1
            rows.append(dict(path=path.relative_to(IQS).as_posix(), bytes=len(raw), sha256=sha(raw)))
    assert rows and len({row["path"] for row in rows}) == len(rows)
    with INDEX.open("x", encoding="utf-8") as stream:
        json.dump(dict(schema="model_resolution_artifacts/1", artifacts=rows,
                       validation=dict(json_files=jsons, python_ast_files=python_files,
                                       final_junit=totals, exact_changed_source_files=len(changed))),
                  stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(dict(indexed_files=len(rows), json_files=jsons, python_ast_files=python_files,
                         final_junit=totals, exact_changed_source_files=len(changed))))


def commit(resume):
    assert git("rev-parse", "HEAD").decode().strip() == EXPECTED_HEAD
    assert git("branch", "--show-current").decode().strip() == "master"
    rows = json.loads(INDEX.read_text("utf-8"))["artifacts"]
    paths = [row["path"] for row in rows] + [INDEX.relative_to(IQS).as_posix(), *META]
    assert len(paths) == len(set(paths)) and "opencode.json" not in paths
    staged = set(git("diff", "--cached", "--name-only").decode().splitlines())
    if resume:
        assert staged == set(paths)
        assert set(git("diff", "--name-only", "HEAD").decode().splitlines()) == set(paths)
    else:
        assert not staged
        assert set(git("diff", "--name-only").decode().splitlines()) == set(META)
    for row in rows:
        raw = (IQS / row["path"]).read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"]
    pathspec = REVIEW / "iqs-pathspec.tmp"
    with pathspec.open("xb") as stream:
        stream.write(b"\0".join(path.encode("utf-8") for path in paths) + b"\0")
    try:
        git("add", "-f", "--pathspec-from-file=" + str(pathspec), "--pathspec-file-nul")
    finally:
        pathspec.unlink()
    assert set(git("diff", "--cached", "--name-only").decode().splitlines()) == set(paths)
    for row in rows:
        raw = git("show", ":" + row["path"])
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"], "Staged raw mismatch: " + row["path"]
    assert git("show", ":" + INDEX.relative_to(IQS).as_posix()) == INDEX.read_bytes()
    commands = [
        ["git", "-C", str(IQS), "-c", "core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol", "diff", "--cached", "--check"],
        ["git", "-C", str(IQS), "commit", "--quiet", "-m", "fix(quick-scan): deliver reviewed model provenance and alias policy"],
        ["git", "-C", str(IQS), "push", "origin", "HEAD:master"],
    ]
    for index, command in enumerate(commands):
        result = subprocess.run(command, capture_output=True)
        if result.returncode:
            print(json.dumps(dict(step=index, returncode=result.returncode, stopped=True)))
            print(result.stdout.decode("utf-8", "replace"))
            print(result.stderr.decode("utf-8", "replace"))
            sys.exit(result.returncode)
    head = git("rev-parse", "HEAD").decode().strip()
    assert head == git("rev-parse", "origin/master").decode().strip()
    assert git("status", "--porcelain=v1").decode() == "?? opencode.json\n"
    print(json.dumps(dict(result_commit=head, pushed_origin_master=True, precise_staged_files=len(paths),
                         indexed_raw_files=len(rows), original_opencode_preserved=True)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("verify", "commit"))
    parser.add_argument("--resume-staged", action="store_true")
    args = parser.parse_args()
    assert args.stage == "commit" or not args.resume_staged
    verify() if args.stage == "verify" else commit(args.resume_staged)
