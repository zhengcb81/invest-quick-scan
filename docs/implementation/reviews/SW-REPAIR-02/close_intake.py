"""Finalize read-only source/hash and private-cleanup receipts, without rerunning tests."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
EVIDENCE = REPO / 'docs/implementation/intake/SW-REPAIR-02/2026-10-08'
SOURCE = Path('C:/Users/郑曾波/Projects/StockWiki')
ROOT = REPO / 'runs/sw-repair-2026-10-08-01'
RESULT = '9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def save(path, body):
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def git(*args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    return subprocess.run(['git', '-C', str(SOURCE), *args], env=env, capture_output=True, check=True).stdout.decode('utf-8').strip()

receipt = read(EVIDENCE / 'cleanup-receipt.json')
assert receipt['applied'] and receipt['files_deleted'] == 769 and not ROOT.exists(), 'private cleanup incomplete'
items = read(EVIDENCE / 'artifact-verification.json')
checks = []
for item in items:
    data = (SOURCE / item['path']).read_bytes()
    checks.append({'path': item['path'], 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                   'matched': len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']})
save(EVIDENCE / 'artifact-verification-after.json', checks)
assert all(item['matched'] for item in checks), 'received artifact drift'
paths = [item['path'] for item in items if not item['path'].startswith('docs/handoff/')]
after = {'head': git('rev-parse', 'HEAD'), 'branch': git('branch', '--show-current'),
         'status': git('status', '--porcelain=v1'), 'result_commit': RESULT,
         'card_code_diff_result_to_head': git('diff', RESULT, 'HEAD', '--', *paths),
         'artifact_matches': sum(c['matched'] for c in checks), 'coordinator_source_writes': 0}
save(EVIDENCE / 'source-after.json', after)
assert after['card_code_diff_result_to_head'] == '', 'card source drift'
verification = read(EVIDENCE / 'verification/result.json')
verification['cleanup_pending'] = False
verification['cleanup'] = {'applied': True, 'files_deleted': 769, 'junction_nodes_unlinked': 6,
                           'root_absent': True, 'scope': 'only coordinator private IQS root; worker shared TEMP not cleaned by coordinator'}
verification['source_after'] = after
save(EVIDENCE / 'verification/result.json', verification)
for name, target in [('guarded_run.py','guarded-run-final.py'), ('acceptance_cases.py','acceptance-cases-final.py')]:
    (EVIDENCE / 'verification' / target).write_bytes((Path(__file__).parent / name).read_bytes())
print(json.dumps({'source_head': after['head'], 'source_clean': not after['status'],
                  'artifact_matches': after['artifact_matches'], 'private_files_deleted': 769,
                  'root_absent': True, 'status': verification['status']}))
