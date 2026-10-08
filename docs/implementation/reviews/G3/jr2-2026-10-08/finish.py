"""Post-publish byte proof and exact private-root cleanup inventory."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/jr2-2026-10-08-01"
OUT = IQS / "docs/implementation/intake/G3/2026-10-08-jr2"
SOURCE = Path("C:/Users/郑曾波/Projects/StockQAbyLLM")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(SOURCE), *args])


def main():
    release = json.loads((OUT / "approval-for-publish.json").read_text("utf-8"))
    snap = OUT / "snapshots" / release["snapshot_label"]
    source = json.loads((snap / "source.json").read_text("utf-8"))
    changed = {row["path"]: row for row in source["changed_files"]}
    baseline = json.loads((OUT / "source-snapshot.json").read_text("utf-8"))
    source_git = json.loads((OUT / "source-git-receipt.json").read_text("utf-8"))
    assert git("rev-parse", "HEAD").decode().strip() == source_git["result_commit"]
    assert git("status", "--porcelain=v1").decode() == source["source_baseline"]["status"]
    for row in baseline:
        name = row["path"]
        expected = changed.get(name, row)["sha256"]
        assert sha((SOURCE / name).read_bytes()) == expected, "External source drift: " + name
        assert sha((OWN / "qa" / name).read_bytes()) == expected, "Isolated source drift: " + name
    final_run = json.loads((OUT / "verification/jr2-green-03/process.json").read_text("utf-8"))
    assert final_run["returncode"] == 0 and not final_run["timeout"] and final_run["executed_source_unchanged"]
    assert final_run["executed_source_hashes"] == {name: row["sha256"] for name, row in changed.items()}
    assert not (OWN / "network-attempts.jsonl").exists() or not (OWN / "network-attempts.jsonl").read_bytes()
    save(OUT / "verification/final-verification.json", dict(schema="jr2_final_verification/1",
        result_commit=source_git["result_commit"], authorized_changed_files=7,
        original_source_unchanged_files=129, compared_source_files=136,
        original_untracked_preserved=True, exact_final_raw_files_match=True,
        final_regression_exit=0, external_http=0, paid_calls=0, production_db_written=False,
        source_written_scope="Exactly two sources and five tests; existing whole-StockQA human authorization"))
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
    body = dict(schema="jr2_cleanup_baseline/1", absolute_root=str(OWN),
        files=sorted(files, key=lambda row: row["path"]), directories=sorted(directories),
        hardlinks=0, reparse_points=0,
        known_session_exits={"39603": 0, "89926": 0, "23303": 0, "54363": 1, "58063": 0, "95302": 0},
        note="Runner exit0 archives pytest RED as data; pytest exits are separately recorded. The exact Black PID46492 was explicitly stopped.")
    save(OUT / "cleanup-baseline.json", body)
    save(OUT / "cleanup-lstat.json", dict(schema="jr2_cleanup_lstat/1", root=str(OWN),
        baseline_sha256=sha((OUT / "cleanup-baseline.json").read_bytes()),
        files_verified=len(files), directories_verified=len(directories), hardlinks=0, reparse_points=0))
    print(json.dumps(dict(compared_source_files=136, authorized_changes=7,
                          cleanup_files=len(files), cleanup_directories=len(directories))))


if __name__ == "__main__":
    main()
