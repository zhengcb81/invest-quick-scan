"""Fill the controller's two omitted SQL fixtures and capture true v5 source."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare import BASE, HEAD, IQS, OWN, SOURCE, git, sha, save, INTAKE

def main():
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    snapshot=json.loads((OWN/'snapshot.json').read_text('utf-8'))
    for name in ('quick_scan_work_store_v1.sql','quick_scan_work_store_v2.sql'):
        rel='tests/fixtures/'+name
        raw=(SOURCE/rel).read_bytes();blob=git('show',HEAD+':'+rel)
        assert raw.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n')
        assert not (OWN/'qa'/rel).exists()
        (OWN/'qa'/rel).write_bytes(raw)
        snapshot.append(dict(path=rel,bytes=len(raw),sha256=sha(raw),git_sha256=sha(blob)))
    save(OWN/'snapshot.json',snapshot)
    save(INTAKE/'verification/source-snapshot-extended.json',snapshot)
    legacy=git('show',BASE+':src/utils/quick_scan_work_store.py')
    (OWN/'legacy_work_store.py').write_bytes(legacy)
    (INTAKE/'verification/v5-work-store-source.py').write_bytes(legacy)
    save(INTAKE/'verification/controller-corrections.json',dict(
       source_sql_added=[x['path'] for x in snapshot[-2:]],old_snapshot_files=131,new_snapshot_files=133,
       legacy_git_commit=BASE,legacy_git_sha256=sha(legacy),
       reason='Initial freeze omitted inert SQL fixtures; first 3 migration failures were controller setup errors. Fourth was Windows asyncio socketpair blocked by controller guard. Catalog filename is manifest.json, not catalog.json.',
       source_written=False,original_logs_preserved=True))

if __name__=='__main__': main()
