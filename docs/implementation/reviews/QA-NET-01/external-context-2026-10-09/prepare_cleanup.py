"""Freeze exact owned files with real os.lstat, never DirEntry's cached nlink."""
import hashlib
import json
import os
from pathlib import Path
import stat

IQS = Path(__file__).resolve().parents[5]
ROOT = IQS / "runs/n111a"
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    publication = json.loads((OUT / "publication/result.json").read_bytes())
    assert publication["source_published"] and publication["approved_paths"] == 38
    assert publication["source_commit"] == publication["remote_head"]
    assert publication["whole_project_gates_closed"] is False
    review = json.loads((IQS / "docs/implementation/reviews/QA-NET-01/external-context-2026-10-09/final-review-recheck.json").read_bytes())
    assert review["publication_artifact_hashes"] == publication["reviewed_git_blob_hashes"]
    for name, digest in review["publication_artifact_hashes"].items():
        assert sha((ROOT / "qa" / name).read_bytes()) == digest
    for label in ("whole-phase-regression-01", "whole-phase-regression-02"):
        batch = OUT / "verification" / label
        archived = json.loads((batch / "subprocess/index.json").read_bytes())
        assert archived["process_sha256"] == sha((batch / "process.json").read_bytes())
        for case in archived["cases"]:
            for record in case["records"]:
                assert sha((batch / record["path"]).read_bytes()) == record["sha256"]
    for label in ("review-20261009-01", "review-20261009-02"):
        target = OUT / "independent-review" / label
        for record in json.loads((target / "archive-index.json").read_bytes())["records"]:
            assert sha((target / record["path"]).read_bytes()) == record["sha256"]
    assert ROOT.absolute() == IQS / "runs/n111a" and ROOT.resolve() == ROOT.absolute()
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
    save(manifest, {"schema": "phase111-owned-cleanup/1", "absolute_root": str(ROOT), "files": files,
         "directories": directories, "no_reparse_or_hardlinked_file": True,
         "publication_receipt_sha256": sha((OUT / "publication/result.json").read_bytes()),
         "scope": "Only IQS runs/n111a; never shared TEMP, unknown files or any foreign repository"})
    save(OUT / "cleanup-lstat.json", {"root": str(ROOT), "baseline_sha256": sha(manifest.read_bytes()),
         "files_verified": len(files), "directories_verified": len(directories), "hardlinks": 0, "reparse_points": 0,
         "link_count_source": "os.lstat(path), every regular file positively asserted st_nlink==1",
         "source_commit": publication["source_commit"]})
    print(json.dumps({"verified_files": len(files), "verified_directories": len(directories),
                      "hardlinks": 0, "reparse_points": 0, "deletion_performed": False}))


if __name__ == "__main__":
    main()
