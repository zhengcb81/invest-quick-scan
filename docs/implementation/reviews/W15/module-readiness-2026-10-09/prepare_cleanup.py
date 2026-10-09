"""Archive synthetic producer bytes and inventory ONLY the owned W15 root."""
import hashlib
import json
import os
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[5]
OWN = ROOT / "runs/w15a"
OUT = ROOT / "docs/implementation/intake/W15/module-readiness-2026-10-09"
CONTROL = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    p = OUT / name
    assert not p.exists()
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    publication = json.loads((OUT / "source-publication/result.json").read_bytes())
    review = json.loads((CONTROL / "review/concentrated-recheck-02.json").read_bytes())
    index = json.loads((OUT / "candidate-index-02.json").read_bytes())
    assert publication["source_published"] and review["software_open_findings"] == 0
    assert review["candidate_index_sha256"] == sha((OUT / "candidate-index-02.json").read_bytes())
    for project, private in (("StockWiki", "sw"), ("StockQAbyLLM", "qa"), ("invest-quick-scan", None)):
        for row in index["files"][project]:
            p = (OWN / private if private else ROOT) / row["path"]
            assert sha(p.read_bytes()) == row["execution_sha256"]
            assert sha((OUT / "candidate-source-02" / project / row["path"]).read_bytes()) == row["execution_sha256"]
    archive = OUT / "actual-synthetic-producer"
    assert not archive.exists()
    archived = []
    test_names = ("test_actual_public_cli_validat0", "test_schema6_native_backup_and0",
                  "test_stockwiki_public_os_cli_b0", "test_owner_public_cli_reuse_an0")
    for name in test_names:
        origin = OWN / "storage-final-09" / name
        request = json.loads((origin / "request.json").read_bytes())
        assert request["identity"]["company"] == "Synthetic W15 company"
        for relative in ("request.json", "producer.stdout.log", "producer.stderr.log",
                         "release/run/route.json", "release/run/manifest.json"):
            p = origin / relative
            info = os.lstat(p)
            assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not getattr(info, "st_file_attributes", 0) & 0x400
            raw = p.read_bytes()
            target = archive / name / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            archived.append(dict(path=target.relative_to(OUT).as_posix(), bytes=len(raw), sha256=sha(raw)))
    save("actual-synthetic-producer-index.json", dict(files=archived, real_company_golden=False,
         source="actual OS producer bytes from storage-final-09", company_documents=0, SQLite_archived=False))
    save("acceptance.json", dict(status="software_foundation_published", source_published=True,
         open_software_findings=0, candidate_index_sha256=review["candidate_index_sha256"],
         review_sha256=sha((CONTROL / "review/concentrated-recheck-02.json").read_bytes()),
         source_publication_sha256=sha((OUT / "source-publication/result.json").read_bytes()),
         whole_W15_complete=False, financial_accuracy_validated=False, API_requests=0))
    assert OWN.resolve() == ROOT / "runs/w15a"
    queue, files, dirs = [OWN], [], []
    while queue:
        parent = queue.pop()
        info = os.lstat(parent)
        assert stat.S_ISDIR(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400
        for e in os.scandir(parent):
            p = Path(e.path)
            info = os.lstat(p)
            assert p.resolve().is_relative_to(OWN) and not stat.S_ISLNK(info.st_mode)
            assert not getattr(info, "st_file_attributes", 0) & 0x400, p
            relative = p.relative_to(OWN).as_posix()
            if stat.S_ISDIR(info.st_mode):
                dirs.append(relative)
                queue.append(p)
            else:
                assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1, p
                raw = p.read_bytes()
                after = os.lstat(p)
                assert (info.st_ino, info.st_size, info.st_mtime_ns, info.st_nlink) == (after.st_ino, after.st_size, after.st_mtime_ns, 1)
                files.append(dict(path=relative, bytes=len(raw), sha256=sha(raw), actual_lstat_nlink=1))
    save("cleanup-baseline.json", dict(schema="w15-owned-cleanup/1", absolute_root=str(OWN),
         files=sorted(files, key=lambda r: r["path"]), directories=sorted(dirs),
         no_reparse_or_hardlinked_file=True, acceptance_sha256=sha((OUT / "acceptance.json").read_bytes()),
         scope="Only IQS runs/w15a; no shared TEMP, foreign source, production data or unknown files"))
    save("cleanup-lstat.json", dict(root=str(OWN), baseline_sha256=sha((OUT/"cleanup-baseline.json").read_bytes()),
         files_verified=len(files), directories_verified=len(dirs), hardlinks=0, reparse_points=0,
         link_count_source="actual os.lstat for every regular file"))
    print(json.dumps(dict(files=len(files), directories=len(dirs), deletion_performed=False)))


if __name__ == "__main__":
    main()
