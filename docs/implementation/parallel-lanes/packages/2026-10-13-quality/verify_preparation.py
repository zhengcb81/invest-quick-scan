"""Read-only package preparation checks, never product/financial acceptance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
from parallel_handoff_cli import validate_handoff


def main():
    lock = json.loads((HERE / 'inputs.lock.json').read_text(encoding='utf-8'))
    catalog = json.loads((HERE / 'manifest.json').read_text(encoding='utf-8'))
    failures = []
    refs = set()
    snapshot_root = Path(lock['snapshot_root']).resolve()
    for entry in lock['files']:
        rel = entry['path']
        path = (snapshot_root / rel).resolve()
        if rel in refs or not path.is_relative_to(snapshot_root):
            failures.append('duplicate_or_escaping_input:' + rel)
            continue
        refs.add(rel)
        try:
            raw = path.read_bytes()
            if len(raw) != entry['bytes'] or hashlib.sha256(raw).hexdigest() != entry['sha256']:
                failures.append('snapshot_mismatch:' + rel)
        except OSError:
            failures.append('snapshot_missing:' + rel)
    roots = [Path(p['write_scope']).resolve() for p in catalog['packages']]
    for index, root in enumerate(roots):
        if root == ROOT or root.is_relative_to(ROOT) or ROOT.is_relative_to(root):
            failures.append('overlaps_coordinator:' + str(root))
        for other in roots[index + 1:]:
            if root == other or root.is_relative_to(other) or other.is_relative_to(root):
                failures.append('overlapping_worker_roots')
    for package in catalog['packages']:
        code, outcome = validate_handoff(HERE / (package['id'] + '.handoff.template.json'),
                                         package['id'], HERE / 'manifest.json')
        if code:
            failures.append(outcome)
        card = HERE / package['document']
        if not card.is_file():
            failures.append('missing_card:' + str(card))
    for doc in HERE.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            if not (doc.parent / target.split('#')[0]).is_file():
                failures.append('broken_link:' + target)
    result = {'status': 'valid' if not failures else 'invalid',
              'validation_scope': 'construction_documents_frozen_inputs_templates_only',
              'input_count': len(refs), 'package_count': len(roots),
              'product_tests_run': False, 'workers_dispatched': False,
              'failures': failures}
    print(json.dumps(result, ensure_ascii=False))
    return 2 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
