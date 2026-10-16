"""Coordinator preparation only. Workers use the existing immutable snapshot."""
import hashlib
import json
from pathlib import Path


def main():
    here = Path(__file__).resolve().parent
    iqs = here.parents[4]
    snapshot = iqs / 'runs/research-quality-wave-2026-10-16/inputs'
    if snapshot.exists() or (here / 'inputs.lock.json').exists():
        raise SystemExit('already prepared; verify existing inputs, do not regenerate')
    rows = []

    def put(data, relative):
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        rows.append({'path': relative, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})

    old_card = here.with_name('2026-10-16-research-tools')
    old = json.loads((old_card / 'inputs.lock.json').read_text('utf-8'))
    old_root = Path(old['default_snapshot_root'])
    for ref in old['files']:
        if ref['path'].split('/')[0] not in {'iqs', 'company', 'trial', 'rules', 'reference'}:
            continue
        data = (old_root / ref['path']).read_bytes()
        assert len(data) == ref['bytes'] and hashlib.sha256(data).hexdigest() == ref['sha256']
        put(data, ref['path'])
    trial = iqs / 'runs/company-agent-isolated-2026-10-16-02'
    sources = json.loads((trial / 'sources.json').read_text('utf-8'))
    qa = next(row for row in sources['sources'] if row['name'] == 'stockqa')
    for ref in qa['files']:
        data = (trial / 'frozen-inputs' / ref['sha256']).read_bytes()
        assert len(data) == ref['bytes'] and hashlib.sha256(data).hexdigest() == ref['sha256']
        put(data, 'stockqa/' + ref['path'])
    for name in ['measurements.json', 'execution/summary.json']:
        put((trial / name).read_bytes(), 'trial-t1/' + name)
    for path in sorted((trial / 'execution').glob('*/*')):
        if path.name in {'result.json', 'events.jsonl'}:
            put(path.read_bytes(), 'trial-t1/' + path.relative_to(trial).as_posix())
    config = json.loads((trial / 'config.json').read_text('utf-8'))
    put((json.dumps(config['sessions'], ensure_ascii=False, indent=2) + '\n').encode(),
        'trial-t1/planned-sessions.json')
    put((json.dumps(config['identity'], ensure_ascii=False, indent=2) + '\n').encode(),
        'trial-t1/subject-provenance.json')
    context = {}
    for filename, key in [('questions.json', 'question_canonical_sha256'),
                          ('evidence-board.json', 'evidence_board_canonical_sha256')]:
        doc = json.loads((trial / filename).read_text('utf-8'))
        raw = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        context[key] = hashlib.sha256(raw).hexdigest()
    context.update(company_key='alphabet', cutoff='2026-10-13')
    put((json.dumps(context, ensure_ascii=False, indent=2) + '\n').encode(), 'trial-t1/context-ref.json')
    for index, expected in [('01', 'd06e0600bd0ea9df25f156b5f73f8b45018a2758b65918866815d8ba33c158d6'),
                            ('02', 'be14e240fc90c627a5dc232a90c59bd8b4c03faec75828d547c9b580b4c16a73')]:
        path = iqs / ('runs/company-agent-quality-review-2026-10-16-' + index) / 'public/independent-review.json'
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected
        put(data, 'reviews/independent-review-' + index + '.json')
    for name in ['company-agent-bounded3-registration-2026-10-16.md',
                 'company-agent-bounded3-results-2026-10-16.md',
                 'company-agent-isolated-t0-results-2026-10-16.md']:
        put((iqs / 'docs/implementation/experiments' / name).read_bytes(), 'rules/' + name)
    packages = [('SESSION-PACK-04', 'iqs-session-packing-lab'),
                ('CLAIM-GUARD-04', 'iqs-claim-guard-lab'),
                ('EVID-GAP-04', 'iqs-evidence-gap-lab')]
    package_rows = []
    for package, name in packages:
        worker = iqs.parent / name
        package_rows.append({'package_id': package, 'workspace': worker.as_posix(),
                             'workspace_existed_at_preparation': worker.exists()})
        template = {
            'protocol': 'iqs.parallel-handoff/1.0.0', 'package_id': package,
            'status': 'prepared_template', 'workspace': worker.as_posix(),
            'branch': None, 'payload_commit': None, 'final_handoff_commit': None,
            'package_version': None, 'public_protocols': [], 'input_lock_sha256': None,
            'artifacts_ref': None,
            'tests_ref': 'docs/handoff/' + package + '/tests.json',
            'report_ref': 'docs/handoff/' + package + '/report.md',
            'cleanup_ref': 'docs/handoff/' + package + '/cleanup.json',
            'actual_paid_model_http': 0, 'actual_paid_search_http': 0,
            'harness_browse_search_count': None, 'harness_tool_cost': None,
            'production_ready': False, 'financial_qualification_granted': False,
            'limitations': [], 'unrun': ['actual_model_comparison', 'production_integration'],
        }
        (here / ('handoff-' + package + '.template.json')).write_text(
            json.dumps(template, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lock = {
        'protocol': 'iqs.parallel-input-lock/1.0.0', 'prepared_on': '2026-10-16',
        'workers_dispatched': False, 'coordinator_workspace': iqs.as_posix(),
        'default_snapshot_root': snapshot.as_posix(), 'packages': package_rows,
        'source_pins': {'iqs_base_head': '703740b309709dbaef08e8a6613e4ec4ae8fc970',
                        'iqs_byte_authority': 'selected frozen inputs, including uncommitted 1.1 pilot, not full Git checkout',
                        'company': '4cb4e3d1b9bcc4e662c73135339de9b51a991916',
                        'stockqa': '8557d862c2553c9b962684de1a23a9cc15cd9e1e'},
        'other_active_workspaces': [(iqs.parent / name).as_posix() for name in
                                    ['iqs-answer-codec-lab', 'iqs-research-judge-lab', 'iqs-cache-planner-lab']],
        'files': sorted(rows, key=lambda row: row['path']),
    }
    (here / 'inputs.lock.json').write_text(json.dumps(lock, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows),
                      'worker_roots_created': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
