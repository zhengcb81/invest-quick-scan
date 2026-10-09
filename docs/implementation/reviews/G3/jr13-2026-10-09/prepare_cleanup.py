"""Freeze exact owned files with real os.lstat, never DirEntry's cached nlink."""
import hashlib
import json
import os
from pathlib import Path
import stat

IQS = Path(__file__).resolve().parents[5]
ROOT = IQS / "runs/r13a"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-jr13"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    acceptance = json.loads((OUT / "acceptance.json").read_bytes())
    assert acceptance["status"] == "software_verified_publication_pending"
    assert acceptance["source_written"] is False and acceptance["open_software_findings"] == 0
    frozen = OUT / "final-snapshot"
    lock = json.loads((frozen / "execution-lock.json").read_bytes())
    for row in lock["snapshots"]:
        assert sha((frozen / row["path"]).read_bytes()) == row["sha256"]
    for name, digest in lock["candidate_sha256"].items():
        assert sha((ROOT / "sw" / name).read_bytes()) == digest
    assert lock["candidate_sha256"] == acceptance["candidate_sha256"]
    for row in acceptance["review_evidence"]:
        assert sha((IQS / row["path"]).read_bytes()) == row["sha256"]
    assert ROOT.absolute() == IQS / "runs/r13a" and ROOT.resolve() == ROOT.absolute()
    root_stat = os.lstat(ROOT)
    assert stat.S_ISDIR(root_stat.st_mode) and not root_stat.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
    queue, directories, files = [ROOT], [], []
    while queue:
        parent = queue.pop()
        for entry in os.scandir(parent):
            path = Path(entry.path)
            # On Windows DirEntry.stat can return zero link-count from directory
            # enumeration. Real lstat opens the metadata; zero is never accepted.
            info = os.lstat(path)
            assert not stat.S_ISLNK(info.st_mode) and not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
            assert path.resolve().is_relative_to(ROOT.resolve())
            name = path.relative_to(ROOT).as_posix()
            if stat.S_ISDIR(info.st_mode):
                directories.append(name)
                queue.append(path)
            else:
                assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1, name
                raw = path.read_bytes()
                after = os.lstat(path)
                assert (after.st_ino, after.st_size, after.st_mtime_ns, after.st_nlink) == (
                    info.st_ino, info.st_size, info.st_mtime_ns, 1), name
                files.append({"path": name, "bytes": len(raw), "sha256": sha(raw), "actual_lstat_nlink": 1})
    files.sort(key=lambda row: row["path"])
    directories.sort()
    manifest = OUT / "cleanup-baseline.json"
    save(manifest, {"schema": "jr13-owned-cleanup/1", "absolute_root": str(ROOT), "files": files,
         "directories": directories, "no_reparse_or_hardlinked_file": True,
         "acceptance_sha256": sha((OUT / "acceptance.json").read_bytes()),
         "scope": "Only IQS runs/r13a; never shared TEMP, unknown files or any foreign repository"})
    save(OUT / "cleanup-lstat.json", {"root": str(ROOT), "baseline_sha256": sha(manifest.read_bytes()),
         "files_verified": len(files), "directories_verified": len(directories), "hardlinks": 0, "reparse_points": 0,
         "link_count_source": "os.lstat(path), every regular file positively asserted st_nlink==1",
         "source_written": False})
    print(json.dumps({"verified_files": len(files), "verified_directories": len(directories),
                      "hardlinks": 0, "reparse_points": 0, "deletion_performed": False}))


if __name__ == "__main__":
    main()
