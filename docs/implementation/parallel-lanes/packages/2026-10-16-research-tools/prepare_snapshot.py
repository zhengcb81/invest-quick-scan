"""Coordinator-only initial freeze. Existing snapshot/lock is never overwritten."""
import hashlib
import json
from pathlib import Path


def main():
    here = Path(__file__).resolve().parent
    iqs = here.parents[4]
    projects = iqs.parent
    snapshot = iqs / 'runs/research-tools-wave-2026-10-16/inputs'
    if snapshot.exists() or (here / 'inputs.lock.json').exists():
        raise SystemExit('already prepared; verify existing freeze instead')
    files = []

    def put(source, relative):
        data = source.read_bytes()
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        assert source.read_bytes() == data, 'source changed during freeze'
        files.append({'path': relative, 'bytes': len(data),
                      'sha256': hashlib.sha256(data).hexdigest()})

    selections = [
        (iqs, 'iqs', ['scripts', 'schemas', 'questions']),
        (projects / 'iqs-company-agent-lab', 'company', ['src', 'schemas']),
        (projects / 'iqs-agent-evaluation-lab', 'evaluation', ['src', 'schemas', 'resources']),
    ]
    for source, prefix, directories in selections:
        for directory in directories:
            for path in sorted((source / directory).rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py', '.json'):
                    put(path, prefix + '/' + path.relative_to(source).as_posix())
    trial = iqs / 'runs/company-agent-isolated-2026-10-16-01'
    for name in ['questions.json', 'evidence-board.json', 'answer-schema.json', 'metrics.json', 'measurements.json']:
        put(trial / name, 'trial/' + name)
    for path in sorted((trial / 'execution').glob('*/*')):
        if path.name in ('result.json', 'events.jsonl'):
            put(path, 'trial/' + path.relative_to(trial).as_posix())
    route = iqs / 'runs/company-agent-owner-2026-10-15-01/route13-candidate-2'
    for name in ['question-projection.json', 'effective-questions.json', 'composed/manifest.json']:
        put(route / name, 'trial/routing/' + name)
    put(iqs / 'runs/company-agent-live-2026-10-15-01/s0_measurement.py', 'pricing/s0_measurement.py')
    put(here / 'historical-rate-card.json', 'pricing/historical-rate-card.json')
    for name in ['company-agent-isolated-registration-2026-10-16.md', 'company-agent-accuracy-rules-2026-10-16.md']:
        put(iqs / 'docs/implementation/experiments' / name, 'rules/' + name)
    for ext in ('json', 'md'):
        name = 'alphabet-objective-reference-2026-10-16.' + ext
        put(iqs / 'docs/implementation/experiments' / name, 'reference/' + name)
    packages = [
        ('ANSWER-CODEC-03', 'iqs-answer-codec-lab'),
        ('RESEARCH-JUDGE-03', 'iqs-research-judge-lab'),
        ('CACHE-PLAN-03', 'iqs-cache-planner-lab'),
    ]
    package_rows = []
    for package, directory in packages:
        worker = projects / directory
        package_rows.append({'package_id': package, 'workspace': worker.as_posix(),
                             'workspace_existed_at_preparation': worker.exists()})
        template = {
            'protocol': 'iqs.parallel-handoff/1.0.0', 'package_id': package,
            'status': 'prepared_template', 'workspace': worker.as_posix(),
            'branch': None, 'payload_commit': None, 'final_handoff_commit': None,
            'package_version': None, 'public_protocols': [],
            'input_lock_sha256': None, 'artifacts_ref': None,
            'tests_ref': 'docs/handoff/' + package + '/tests.json',
            'report_ref': 'docs/handoff/' + package + '/report.md',
            'cleanup_ref': 'docs/handoff/' + package + '/cleanup.json',
            'actual_paid_model_http': 0, 'actual_paid_search_http': 0,
            'production_ready': False, 'financial_qualification_granted': False,
            'limitations': [], 'unrun': ['coordinator_live_integration', 'actual_financial_review'],
            'commit_note': 'payload_commit identifies code; final handoff HEAD is reported outside its own commit to avoid self-reference',
        }
        (here / ('handoff-' + package + '.template.json')).write_text(
            json.dumps(template, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lock = {
        'protocol': 'iqs.parallel-input-lock/1.0.0', 'prepared_on': '2026-10-16',
        'workers_dispatched': False, 'default_snapshot_root': snapshot.as_posix(),
        'coordinator_workspace': iqs.as_posix(),
        'source_pins': {
            'iqs_base_head': '2a902b0c0eadcae93f9fb70a353edbde69a4b1ee',
            'iqs_worktree': 'raw snapshot includes coordinator uncommitted v1.1 pilot; file hashes are authoritative',
            'company': '4cb4e3d1b9bcc4e662c73135339de9b51a991916',
            'evaluation': '01956bdec2790525188451aefad0f2f6546765c0',
        }, 'packages': package_rows, 'files': sorted(files, key=lambda r: r['path']),
    }
    (here / 'inputs.lock.json').write_text(json.dumps(lock, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'files': len(files), 'bytes': sum(r['bytes'] for r in files),
                      'snapshot': snapshot.as_posix()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
