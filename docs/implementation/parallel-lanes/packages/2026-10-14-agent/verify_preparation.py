"""Validate preparation only; no worker product or live API is executed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

P = Path(__file__).resolve().parent
ROOT = P.parents[4]
parser = argparse.ArgumentParser()
parser.add_argument('--input-root', type=Path)
args = parser.parse_args()
lock = json.loads((P / 'inputs.lock.json').read_bytes())
snapshot = (args.input_root or Path(lock['snapshot_root'])).resolve()
seen = set()
for item in lock['files']:
    assert set(item) == {'repository', 'path', 'bytes', 'sha256'}
    rel = Path(item['path'])
    assert not rel.is_absolute() and '..' not in rel.parts and ':' not in str(rel)
    path = snapshot / item['repository'] / rel
    assert path.resolve().is_relative_to(snapshot) and not path.is_symlink()
    raw = path.read_bytes()
    assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
    key = item['repository'], item['path']
    assert key not in seen
    seen.add(key)

catalog = json.loads((P / 'manifest.json').read_bytes())
package = catalog['packages'][0]
assert not catalog['workers_dispatched'] and not catalog['default_live_enabled']
assert package['id'] == 'COMPANY-AGENT-01' and package['network_scope'] == 'offline_only'
previous = json.loads((P.parent / '2026-10-14/manifest.json').read_bytes())
new = Path(package['write_scope']).resolve()
for row in previous['packages']:
    old = Path(row['write_scope']).resolve()
    assert not new.is_relative_to(old) and not old.is_relative_to(new)

registration = json.loads((ROOT / 'docs/implementation/experiments/company-agent-registration-2026-10-14.json').read_bytes())
targets = json.loads((P / 'COMPANY-AGENT-01.targets.json').read_bytes())
assert len(targets['records']) == 12
assert registration['question_ids'] == [r['question_id'] for r in targets['records']]
for record in targets['records']:
    raw = json.dumps(record['question'], ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    assert hashlib.sha256(raw).hexdigest() == record['question_object_sha256']
assert sum(v['max_model_http'] for k, v in registration['phases'].items() if k != 'S3') == 318
for stage, slots in [('S1', 216), ('S2', 108)]:
    phase = registration['phases'][stage]
    assert phase['companies'] * phase['arms'] * phase['repeats'] == phase['sessions']
    assert phase['sessions'] * 12 == slots == phase['all_arm_slots']
    assert phase['sessions'] * phase['max_model_http_per_session'] == phase['max_model_http']

documents = list(P.glob('*.md')) + [ROOT / 'docs/implementation/experiments' / name for name in ['company-agent-design-2026-10-14.md', 'company-agent-registration-2026-10-14.md']]
for doc in documents:
    for link in re.findall(r'\]\(([^)]+)\)', doc.read_text('utf-8')):
        if ':' not in link and not link.startswith('#'):
            assert (doc.parent / link).is_file(), str(doc) + ':' + link

env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'PATH', 'PATHEXT', 'COMSPEC'}}
env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(ROOT / 'scripts/parallel_handoff_cli.py'), '--catalog', str(P / 'manifest.json'), '--package-id', package['id'], '--input', str(P / 'COMPANY-AGENT-01.handoff.template.json')], capture_output=True, timeout=30, env=env)
assert result.returncode == 0, result.stdout.decode('utf-8') + result.stderr.decode('utf-8')
print(json.dumps({'frozen_files': len(seen), 'raw_bytes_verified': True, 'question_targets': 12, 'model_http_cap_arithmetic': 318, 'nonoverlap_with_previous_three': True, 'local_links_valid': True, 'handoff_shape_exit': result.returncode, 'worker_product_tests': 'not_run', 'live_calls': 0, 'validation_scope': 'preparation_only'}, ensure_ascii=False))
