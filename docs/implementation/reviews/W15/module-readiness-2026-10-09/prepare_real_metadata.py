"""One-shot read-only real owner metadata backup, never original documents.

    The isolated StockWiki check interface resolves OWN/StockWiki. Files are
    exact existing metadata, not made-up positive data; no secret config or
    company document is copied. Archive contains locks only, not these copies.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat

ROOT = Path(__file__).resolve().parents[5]
OWN = ROOT / "runs/w15a"
OUT = ROOT / "docs/implementation/intake/W15/module-readiness-2026-10-09"
SOURCE = Path("C:/Users/郑曾波/Projects/StockWiki")
TARGET = OWN / "StockWiki"


def digest(path):
    state = os.lstat(path)
    assert stat.S_ISREG(state.st_mode) and not (getattr(state,"st_file_attributes",0)&0x400) and state.st_nlink==1
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert TARGET.resolve().is_relative_to(OWN.resolve()) and not TARGET.exists()
    assert not (OUT/"real-owner-metadata-input-01.json").exists()
    frozen = json.loads((OUT/"stockwiki-input-01.json").read_bytes())["nonsecret_files"]
    # Public nonsecret assets already source-frozen in this package.
    for row in frozen:
        if row["path"].startswith(("config/","framework/")):
            path = OWN/"sw"/row["path"]
            assert digest(path)==row["execution_sha256"]
            destination = TARGET/row["path"]
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,destination)
    # Deliberately synthetic zero-provider config; not a copy of owner secrets.
    (TARGET/"config/llm_providers.yaml").write_text("providers: []\n",encoding="utf-8")
    refs = sorted(SOURCE.glob("data/companies/*/evidence_index.yaml")) + sorted(SOURCE.glob("data/companies/*/review_decisions.yaml"))
    refs += [SOURCE/"data"/name for name in ("framework_changelog.yaml","framework_proposals.yaml") if (SOURCE/"data"/name).is_file()]
    rows = []
    for path in refs:
        assert path.resolve().is_relative_to(SOURCE.resolve()) and path.stat().st_size<=64*1024*1024
        before = digest(path)
        destination = TARGET/path.relative_to(SOURCE)
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,destination)
        assert digest(destination)==before and digest(path)==before
        rows.append(dict(path=path.relative_to(SOURCE).as_posix(),bytes=path.stat().st_size,sha256=before))
    databases = []
    for name in ("scan.sqlite","analysis_subjects.sqlite","identity_receipts.sqlite","market_registry.sqlite"):
        path = SOURCE/"data/quick_scan"/name
        before = digest(path)
        destination = TARGET/"data/quick_scan"/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        source_con = sqlite3.connect(path.as_uri()+"?mode=ro",uri=True)
        target_con = sqlite3.connect(destination)
        try:
            source_con.execute("PRAGMA query_only=ON")
            source_con.backup(target_con)
            version = target_con.execute("PRAGMA user_version").fetchone()[0]
            assert target_con.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        finally:
            source_con.close()
            target_con.close()
        assert digest(path)==before
        databases.append(dict(path=path.relative_to(SOURCE).as_posix(),source_raw_sha256=before,
                              backup_sha256=digest(destination),schema_version=version,consistent_native_backup=True))
    assert all(digest(SOURCE/r["path"])==r["sha256"] for r in rows)
    assert all(digest(SOURCE/r["path"])==r["source_raw_sha256"] for r in databases)
    report = dict(protocol="iqs.w15_real_metadata_clone/1.0.0",source=str(SOURCE),target=str(TARGET),
                  files=rows,databases=databases,source_files_written=0,source_DB_migrations=0,
                  company_documents_copied=0,secrets_copied=False,synthetic_provider_config=True,
                  readonly_acquisition_outside_foreign_SQLite_guard=True,model_API_requests=0,
                  cloned_observations_golden=False)
    (OUT/"real-owner-metadata-input-01.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(metadata_files=len(rows),native_backups=databases,source_files_written=0)))


if __name__=="__main__":
    main()
