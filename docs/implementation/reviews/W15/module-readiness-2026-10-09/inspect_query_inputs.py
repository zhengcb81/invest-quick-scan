"""Read only table counts from four existing isolated native backups."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[5]
DATABASES = ROOT / "runs/w15a/StockWiki/data/quick_scan"
OUT = ROOT / "docs/implementation/intake/W15/module-readiness-2026-10-09/query-input-counts-01.json"


def main():
    assert not OUT.exists()
    result = {}
    for name in ("scan.sqlite", "analysis_subjects.sqlite", "identity_receipts.sqlite", "market_registry.sqlite"):
        path = DATABASES / name
        assert path.resolve().is_relative_to(ROOT / "runs/w15a") and not path.is_symlink()
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        con = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            assert all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n) for n in names)
            counts = {n: con.execute('SELECT COUNT(*) FROM "' + n + '"').fetchone()[0] for n in names}
            result[name] = dict(user_version=con.execute("PRAGMA user_version").fetchone()[0],
                                table_counts=counts, clone_sha256=before)
        finally:
            con.close()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    OUT.write_text(json.dumps(dict(source="existing read-only native backups; no invented data",
                   databases=result, source_files_written=0, company_records_exported=0),
                   indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
