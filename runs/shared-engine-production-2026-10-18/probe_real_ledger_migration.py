"""Offline migration of a read-only SQLite backup, never the original ledger."""
from pathlib import Path
import hashlib
import json
import socket
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parent / 'real-ledger-migration-01'
SOURCE = ROOT / 'runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite'
sys.path.insert(0, str(ROOT.parent / 'StockQAbyLLM'))


def deny_network(*args, **kwargs):
    raise RuntimeError('offline ledger migration: network prohibited')


socket.socket.connect = deny_network
socket.create_connection = deny_network
from src.utils.quick_scan_work_store import QuickScanWorkStore


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def readonly(path):
    c = sqlite3.connect('file:' + path.resolve().as_posix() + '?mode=ro', uri=True)
    c.execute('PRAGMA query_only=ON')
    return c


def table_state(connection):
    result = {}
    names = [r[0] for r in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    for name in names:
        quoted = '"' + name.replace('"', '""') + '"'
        rows = connection.execute('SELECT * FROM ' + quoted).fetchall()
        encoded = sorted(json.dumps(row, ensure_ascii=True, separators=(',', ':'),
            default=lambda b: {'sqlite_blob_hex': b.hex()}).encode('utf8') for row in rows)
        result[name] = {'rows': len(rows), 'sha256': hashlib.sha256(b'\n'.join(encoded)).hexdigest()}
    return result


def main():
    OWN.mkdir(exist_ok=False)
    original_sha = digest(SOURCE)
    backup = OWN / 'original-readonly-backup.sqlite'
    candidate = OWN / 'migration-candidate.sqlite'
    with readonly(SOURCE) as source:
        original_version = source.execute('PRAGMA user_version').fetchone()[0]
        before = table_state(source)
        with sqlite3.connect(backup) as target:
            source.backup(target)
    assert digest(SOURCE) == original_sha
    candidate.write_bytes(backup.read_bytes())
    store = QuickScanWorkStore(candidate)
    with readonly(candidate) as c:
        version = c.execute('PRAGMA user_version').fetchone()[0]
        after = table_state(c)
        assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert c.execute('PRAGMA foreign_key_check').fetchall() == []
    assert original_version == 20 and version == 23
    assert all(after[name] == state for name, state in before.items())
    assert all(state['rows'] == 0 for name, state in after.items() if name not in before)
    assert digest(SOURCE) == original_sha
    result = {
        'protocol': 'iqs.original-ledger-isolated-migration-proof/1.0.0',
        'observed_at': datetime.now(timezone.utc).isoformat(),
        'status': 'passed', 'source_schema': original_version, 'candidate_schema': version,
        'original_unchanged_sha256': original_sha, 'backup_sha256': digest(backup),
        'candidate_sha256': digest(candidate), 'old_tables': before,
        'new_empty_tables': sorted(set(after) - set(before)),
        'original_table_rows_unchanged': True, 'source_database_writes': 0,
        'http_requests': 0, 'unknown_request_resent': False,
        'historical_visible_output_backfilled': False,
        'native_implementation_commit': '52330ab633d00fa1a282492a6ca9fc809c62e182',
        'scope': 'genuine old ledger backup migration only; not a native owner positive or financial evaluation',
        'cleanup': 'retained exact local backup/candidate for whole-node review; no database committed',
    }
    (OWN / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: result[k] for k in ('status', 'source_schema', 'candidate_schema',
        'original_table_rows_unchanged', 'source_database_writes', 'http_requests')}))


if __name__ == '__main__':
    main()
