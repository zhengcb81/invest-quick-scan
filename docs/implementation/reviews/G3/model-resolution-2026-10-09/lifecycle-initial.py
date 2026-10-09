"""Exact reviewed-byte publication, normal Git delivery, and private-root proof.

This batch controller is not a reusable production command. Run only after the
single concentrated review and final affected tests have been archived.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/model-resolution-2026-10-09-01"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-model-resolution"
SOURCE = Path("C:/Users/郑曾波/Projects/StockQAbyLLM")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(body, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(SOURCE), *args])


def safe_path(root, relative):
    assert relative and "\\" not in relative
    parts = relative.split("/")
    assert all(part not in {"", ".", ".."} for part in parts)
    path = root.joinpath(*parts)
    assert path.resolve() == path and path.is_relative_to(root)
    for ancestor in (root, *list(path.parents)[:len(parts) - 1], path):
        if ancestor.exists():
            info = ancestor.lstat()
            assert not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400
            if stat.S_ISREG(info.st_mode):
                assert info.st_nlink == 1
    return path


def load_release():
    release = json.loads((OUT / "approval-for-publish.json").read_text("utf-8"))
    assert release["approved_for_model_resolution_publish"] is True
    label = release["snapshot_label"]
    assert label.replace("-", "").replace("_", "").isalnum()
    snap = OUT / "snapshots" / label
    raw = (snap / "source.json").read_bytes()
    assert sha(raw) == release["reviewed_source_sha256"]
    manifest = json.loads(raw)
    scope = json.loads((Path(__file__).parent / "scope.json").read_text("utf-8"))
    rows = manifest["changed_files"]
    names = [row["path"] for row in rows]
    assert names and len(names) == len(set(names)) and set(names) <= set(scope["files"])
    assert names == release["approved_paths"]
    review_path = safe_path(IQS, release["independent_review"])
    assert sha(review_path.read_bytes()) == release["independent_review_sha256"]
    assert Path(manifest["source_baseline"]["source"]).resolve() == SOURCE
    for row in rows:
        raw = safe_path(snap / "source", row["path"]).read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"]
    receipt = json.loads((OUT / "verification" / manifest["test_label"] / "process.json").read_text("utf-8"))
    assert receipt["returncode"] == 0 and not receipt["timeout"] and receipt["executed_source_unchanged"]
    assert all(receipt["executed_source_hashes"].get(row["path"]) == row["sha256"] for row in rows), "Snapshot differs from executed test bytes"
    suites = ET.parse(OUT / "verification" / manifest["test_label"] / "junit.xml").getroot()
    totals = {key: sum(int(s.get(key, "0")) for s in suites.iter("testsuite"))
              for key in ("tests", "failures", "errors", "skipped")}
    assert totals == release["approved_junit_totals"] and totals["tests"] > 0
    assert all(totals[key] == 0 for key in ("failures", "errors", "skipped"))
    assert manifest["guard"]["network_attempts"] == 0
    return release, snap, manifest, rows


def publish(apply):
    release, snap, manifest, rows = load_release()
    baseline = manifest["source_baseline"]
    assert git("rev-parse", "HEAD").decode().strip() == baseline["head"]
    assert git("status", "--porcelain=v1").decode() == baseline["status"]
    prepared = []
    for row in rows:
        path = safe_path(SOURCE, row["path"])
        if row["before_sha256"] is None:
            assert not path.exists()
        else:
            assert path.is_file() and sha(path.read_bytes()) == row["before_sha256"]
        raw = (snap / "source" / row["path"]).read_bytes()
        prepared.append((row, path, raw))
    # Independent before-proof for every protected source, not only changed paths.
    before = json.loads((OUT / "source-snapshot.json").read_text("utf-8"))
    for row in before:
        assert sha(safe_path(SOURCE, row["path"]).read_bytes()) == row["sha256"]
    target = OUT / ("publish-receipt.json" if apply else "publish-dry-run.json")
    assert not target.exists()
    if apply:
        for row, path, raw in prepared:
            if row["before_sha256"] is None:
                assert not path.exists()
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(raw)
            else:
                assert sha(path.read_bytes()) == row["before_sha256"]
                path.write_bytes(raw)
        assert all(path.read_bytes() == raw for _, path, raw in prepared)
    body = dict(schema="model_resolution_publish/1", applied=apply,
                expected_files=len(rows), published_files=len(rows) if apply else 0,
                baseline_head=baseline["head"], exact_reviewed_sha256=release["reviewed_source_sha256"],
                other_repositories_written=False, paid_calls=0)
    save(target, body)
    print(json.dumps(body))


def commit_source():
    _, _, manifest, rows = load_release()
    baseline = manifest["source_baseline"]
    names = [row["path"] for row in rows]
    assert json.loads((OUT / "publish-receipt.json").read_text("utf-8"))["applied"]
    assert git("rev-parse", "HEAD").decode().strip() == baseline["head"]
    assert git("branch", "--show-current").decode().strip() == "master"
    assert not git("diff", "--cached", "--name-only")
    existing = {row["path"] for row in rows if row["before_sha256"] is not None}
    assert set(git("diff", "--name-only").decode().splitlines()) == existing
    status = git("status", "--porcelain=v1").decode().splitlines()
    assert [line for line in status if line[3:] not in names] == baseline["status"].splitlines()
    for row in rows:
        assert sha(safe_path(SOURCE, row["path"]).read_bytes()) == row["sha256"]
    log = OUT / "verification/source-git"
    log.mkdir(parents=True, exist_ok=False)
    git("add", "--", *names)
    assert set(git("diff", "--cached", "--name-only").decode().splitlines()) == set(names)
    staged = []
    for row in rows:
        raw = git("show", ":" + row["path"])
        assert sha(raw) in {row["sha256"], row["normalized_lf_sha256"]}
        staged.append(dict(path=row["path"], sha256=sha(raw), bytes=len(raw), same_raw=sha(raw) == row["sha256"]))
    save(log / "staged-source.json", staged)
    commands = [
        ["git", "-C", str(SOURCE), "diff", "--cached", "--check"],
        ["git", "-C", str(SOURCE), "commit", "--quiet", "-m", "fix(quick-scan): preserve frozen requested and resolved model provenance"],
        ["git", "-C", str(SOURCE), "push", "origin", "HEAD:master"],
    ]
    env = {key: value for key, value in os.environ.items() if "API_KEY" not in key.upper()}
    hook_tmp = OWN / "tmp/source-git"
    hook_tmp.mkdir(parents=True, exist_ok=True)
    env.update(TEMP=str(hook_tmp), TMP=str(hook_tmp), TMPDIR=str(hook_tmp),
               BLACK_CACHE_DIR=str(hook_tmp / "black-cache"),
               MYPY_CACHE_DIR=str(hook_tmp / "mypy-cache"),
               PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", STOCKQA_RUN_LIVE_E2E="0")
    receipts = []
    for index, command in enumerate(commands):
        result = subprocess.run(command, env=env, capture_output=True)
        (log / f"{index:02}.stdout.log").write_bytes(result.stdout)
        (log / f"{index:02}.stderr.log").write_bytes(result.stderr)
        receipts.append(dict(command=command, returncode=result.returncode))
        (log / "commands.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if result.returncode:
            print(json.dumps(dict(step=index, returncode=result.returncode, stopped=True)))
            sys.exit(result.returncode)
        if index == 1:
            for row in rows:
                assert sha((SOURCE / row["path"]).read_bytes()) == row["sha256"], "Hook changed tested bytes; reverify before push"
            assert set(git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").decode().splitlines()) == set(names)
    head = git("rev-parse", "HEAD").decode().strip()
    assert head == git("rev-parse", "origin/master").decode().strip()
    assert git("status", "--porcelain=v1").decode() == baseline["status"]
    save(OUT / "source-git-receipt.json", dict(schema="model_resolution_source_git/1",
         baseline_head=baseline["head"], result_commit=head, staged_files=len(rows), commands=receipts,
         pushed_origin_master=True, source_status_preserved=True, original_untracked=baseline["status"]))
    print(json.dumps(dict(result_commit=head, staged_files=len(rows), normal_push=True)))


def finish():
    _, _, manifest, rows = load_release()
    delivery = json.loads((OUT / "source-git-receipt.json").read_text("utf-8"))
    assert git("rev-parse", "HEAD").decode().strip() == delivery["result_commit"]
    assert git("status", "--porcelain=v1").decode() == manifest["source_baseline"]["status"]
    before = {row["path"]: row for row in json.loads((OUT / "source-snapshot.json").read_text("utf-8"))}
    extra = json.loads((OUT / "extra-baseline.json").read_text("utf-8"))[0]
    before[extra["path"]] = extra
    changed = {row["path"]: row for row in rows}
    for name in set(before) | set(changed):
        source_raw, own_raw = safe_path(SOURCE, name).read_bytes(), safe_path(OWN / "qa", name).read_bytes()
        if name == ".gitignore" and name not in changed:
            assert source_raw.replace(b"\r\n", b"\n") == own_raw.replace(b"\r\n", b"\n")
        else:
            expected = changed.get(name, before.get(name))["sha256"]
            assert sha(source_raw) == expected and sha(own_raw) == expected
    test = json.loads((OUT / "verification" / manifest["test_label"] / "process.json").read_text("utf-8"))
    assert all(sha((OWN / "qa" / name).read_bytes()) == digest for name, digest in test["executed_source_hashes"].items())
    network = OWN / "network-attempts.jsonl"
    assert not network.exists() or not network.read_bytes()
    result = dict(schema="model_resolution_final_verification/1", result_commit=delivery["result_commit"],
                  authorized_changed_files=len(rows), compared_source_files=len(set(before) | set(changed)),
                  original_source_unchanged_files=len(set(before) - set(changed)),
                  original_untracked_preserved=True, exact_final_raw_files_match=True,
                  final_regression_exit=0, external_http=0, paid_calls=0, production_db_written=False)
    save(OUT / "verification/final-verification.json", result)
    assert OWN.resolve() == OWN and OWN.is_dir()
    files, directories = [], []
    for current, children, leaves in os.walk(OWN, followlinks=False):
        for name in [".", *children, *leaves]:
            path = Path(current) if name == "." else Path(current) / name
            info = path.lstat()
            assert not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400
            assert path == OWN or OWN in path.parents
            if name == ".":
                continue
            relative = path.relative_to(OWN).as_posix()
            if stat.S_ISDIR(info.st_mode):
                directories.append(relative)
            else:
                assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                raw = path.read_bytes()
                files.append(dict(path=relative, bytes=len(raw), sha256=sha(raw)))
    save(OUT / "cleanup-baseline.json", dict(schema="model_resolution_cleanup_baseline/1", absolute_root=str(OWN),
         files=sorted(files, key=lambda row: row["path"]), directories=sorted(directories),
         hardlinks=0, reparse_points=0, note="All test/static and source Git handles must be terminal; strict CIM checked by cleanup.ps1"))
    save(OUT / "cleanup-lstat.json", dict(schema="model_resolution_cleanup_lstat/1", root=str(OWN),
         baseline_sha256=sha((OUT / "cleanup-baseline.json").read_bytes()),
         files_verified=len(files), directories_verified=len(directories), hardlinks=0, reparse_points=0))
    print(json.dumps(dict(compared_source_files=result["compared_source_files"], authorized_changes=len(rows),
                         cleanup_files=len(files), cleanup_directories=len(directories))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("publish", "commit", "finish"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    assert args.stage == "publish" or not args.apply
    {"publish": lambda: publish(args.apply), "commit": commit_source, "finish": finish}[args.stage]()
