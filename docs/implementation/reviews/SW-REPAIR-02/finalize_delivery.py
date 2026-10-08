"""Bind received evidence and review helpers by exact bytes; never writes source repos."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
EVIDENCE = REPO / 'docs/implementation/intake/SW-REPAIR-02/2026-10-08'
REVIEWS = Path(__file__).resolve().parent
INDEX = EVIDENCE / 'delivery-index.json'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

if sys.argv[1:] == ['--check-staged']:
    index = read(INDEX)
    for item in index['items']:
        data = subprocess.run(['git', 'show', ':' + item['path']], cwd=REPO,
                              capture_output=True, check=True).stdout
        assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'], 'staged bytes differ: ' + item['path']
    data = subprocess.run(['git', 'show', ':' + INDEX.relative_to(REPO).as_posix()], cwd=REPO,
                          capture_output=True, check=True).stdout
    assert data == INDEX.read_bytes(), 'staged index differs'
    print(json.dumps({'staged_files_exact': len(index['items']), 'index_exact': True}))
    raise SystemExit(0)
assert not sys.argv[1:], 'unsupported mode'

result = read(EVIDENCE / 'verification/result.json')
cleanup = read(EVIDENCE / 'cleanup-receipt.json')
assert result['status'] == 'changes_requested' and not result['cleanup_pending'] and cleanup['applied']
assert result['core']['passed'] == 81 and result['browser']['passed'] == 11
assert result['additional']['methods'] == result['additional']['failed'] == 12
assert result['snapshot_files'] == 296 and not result['snapshot_changes_after_tests']
assert not (REPO / 'runs/sw-repair-2026-10-08-01').exists()
items = []
for base in (EVIDENCE, REVIEWS):
    for path in sorted(base.rglob('*')):
        if not path.is_file() or path == INDEX:
            continue
        assert not path.is_symlink() and path.resolve().is_relative_to(REPO.resolve())
        data = path.read_bytes()
        if path.suffix == '.json':
            json.loads(data.decode('utf-8-sig'))  # shape/meaning of negative goldens is deliberately not asserted
        items.append({'path': path.relative_to(REPO).as_posix(), 'bytes': len(data),
                      'sha256': hashlib.sha256(data).hexdigest()})
index = {'schema': 'iqs_sw_repair_acceptance_index/1', 'status': 'changes_requested',
         'source_result_commit': result['result_commit'], 'source_received_head': result['source_after']['head'],
         'byte_domain': 'exact archived files; -text Git attributes preserve these bytes',
         'exclusions': ['this index (no self hash)', 'mutable root PWF and handoff-for-new-agent.md', '.gitattributes'],
         'items': items, 'count': len(items)}
INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'files_bound': len(items), 'bytes': sum(i['bytes'] for i in items),
                  'private_cleanup_applied': True, 'status': 'changes_requested'}))
