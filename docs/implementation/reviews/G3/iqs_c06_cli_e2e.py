"""Real isolated IQS authority entrypoint; synthetic identity, no HTTP or DB."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


IQS = Path(__file__).resolve().parents[4]
GUARD = Path(__file__).with_name('c06_context_guarded.py')
FROZEN = IQS / 'docs/implementation/parallel-lanes/packages/2026-10-07-wave2'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root', required=True, type=Path)
    args = parser.parse_args()
    own = args.work_root.resolve()
    if not own.is_relative_to(IQS / 'runs') or not own.name.startswith('c06-context-'):
        raise ValueError('exclusive IQS c06-context root required')
    own.mkdir(parents=True, exist_ok=False)
    for key in list(os.environ):
        if key.endswith(('API_KEY', 'API_TOKEN')) or 'RUN_LIVE' in key:
            os.environ.pop(key)
    os.environ.update(IQS_C06_TEST_ROOT=str(own), TEMP=str(own), TMP=str(own),
                      TMPDIR=str(own), PYTHONDONTWRITEBYTECODE='1',
                      PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    source = FROZEN / 'inputs/qa-phase92-overlay/tests/fixtures'
    manifest_raw = (source / 'quick_scan_c06_manifest_v2_fixture.json').read_bytes()
    authority_raw = (source / 'quick_scan_c06_authority_v2_fixture.json').read_bytes()
    expected = json.loads(authority_raw)
    metadata = next(iter(expected['observation_context']['questions'].values()))['metadata']
    run = {key: metadata[key] for key in
           ('run_id', 'scan_id', 'inputset_id', 'task_mode', 'comparison_group_id')}
    inputs = {'manifest': manifest_raw,
              'identity': b'{"fixture_class":"synthetic_opaque_not_owner_verified"}\n',
              'run': json.dumps(run).encode(),
              'versions': json.dumps(expected['contract_versions']).encode(),
              'producer': json.dumps(expected['producer']).encode()}
    paths = {}
    for key, raw in inputs.items():
        paths[key] = own / (key + '.json')
        paths[key].write_bytes(raw)
    cases = []

    def invoke(label, output, *, overrides=None, code=0):
        selected = {**paths, **(overrides or {})}
        cli = sum(([f'--{key}', str(path)] for key, path in selected.items()), [])
        command = [sys.executable, '-B', '-X', 'utf8', str(GUARD), '--public-cli',
                   *cli, '--output', str(output)]
        done = subprocess.run(command, cwd=IQS, capture_output=True, timeout=45)
        log = (b'COMMAND ' + json.dumps(command, ensure_ascii=False).encode() +
               b'\nSTDOUT\n' + done.stdout + b'\nSTDERR\n' + done.stderr +
               b'\nEXIT ' + str(done.returncode).encode() + b'\n')
        path = own / (label + '.log')
        path.write_bytes(log)
        valid = done.returncode == code and b'c06_context_guard_canaries_passed' in done.stdout
        cases.append({'id': label, 'expected_exit': code, 'actual_exit': done.returncode,
                      'guard_canaries': b'c06_context_guard_canaries_passed' in done.stdout,
                      'result': 'passed' if valid else 'failed', 'log': path.name,
                      'log_sha256': sha(log)})
        assert valid, label + ': inspect original log'
        return done

    positive = own / 'positive.json'
    invoke('CLI01_export', positive)
    original = positive.read_bytes()
    body = json.loads(original)
    context = body['observation_context']
    assert context['manifest_file_sha256'] == sha(manifest_raw)
    assert context['identity_snapshot_sha256'] == sha(inputs['identity'])
    for qid, item in context['questions'].items():
        assert item == expected['observation_context']['questions'][qid]
        assert not {'answer', 'execution', 'observation_id', 'observed_at'} & set(item['metadata'])
    assert sha(json.dumps(context, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                          allow_nan=False).encode()) == body['observation_context_sha256']
    second = own / 'repeat.json'
    invoke('CLI02_repeat_same_bytes', second)
    assert second.read_bytes() == original
    invoke('CLI03_overwrite_refused', positive, code=2)
    assert positive.read_bytes() == original

    primary = own / 'primary-run.json'
    primary.write_text(json.dumps({**run, 'task_mode': 'primary', 'comparison_group_id': None}), encoding='utf8')
    primary_output = own / 'primary.json'
    invoke('CLI04_primary', primary_output, overrides={'run': primary})
    for item in json.loads(primary_output.read_bytes())['observation_context']['questions'].values():
        assert item['metadata']['task_mode'] == 'primary'
        assert item['metadata']['comparison_group_id'] is None
    comparison = own / 'comparison-run.json'
    comparison.write_text(json.dumps({**run, 'task_mode': 'comparison',
                                      'comparison_group_id': 'fixture-comparison'}), encoding='utf8')
    comparison_output = own / 'comparison.json'
    invoke('CLI05_comparison', comparison_output, overrides={'run': comparison})
    for item in json.loads(comparison_output.read_bytes())['observation_context']['questions'].values():
        assert item['metadata']['task_mode'] == 'comparison'
        assert item['metadata']['comparison_group_id'] == 'fixture-comparison'

    bad_run = own / 'duplicate-run.json'
    canary = 'SYNTHETIC_BODY_CANARY_DO_NOT_ECHO'
    bad_run.write_text('{"run_id":"' + canary + '","run_id":"duplicate"}', encoding='utf8')
    failed = own / 'duplicate-output.json'
    result = invoke('CLI06_duplicate_json', failed, overrides={'run': bad_run}, code=2)
    assert not failed.exists() and canary.encode() not in result.stdout + result.stderr
    bad_manifest = own / 'tampered-manifest.json'
    content = json.loads(manifest_raw)
    content['questions'][0]['prompt'] += ' tampered'
    bad_manifest.write_text(json.dumps(content, ensure_ascii=False), encoding='utf8')
    failed = own / 'tampered-output.json'
    invoke('CLI07_archived_definition_reject', failed, overrides={'manifest': bad_manifest}, code=2)
    assert not failed.exists()
    bad_versions = own / 'bad-versions.json'
    versions = copy.deepcopy(expected['contract_versions'])
    versions['answer_schema'] = '999.0.0'
    bad_versions.write_text(json.dumps(versions), encoding='utf8')
    failed = own / 'version-output.json'
    invoke('CLI08_wrong_contract', failed, overrides={'versions': bad_versions}, code=2)
    assert not failed.exists()
    empty_run = own / 'missing-run.json'
    empty_run.write_bytes(b'{}')
    failed = own / 'missing-run-output.json'
    invoke('CLI09_missing_context', failed, overrides={'run': empty_run}, code=2)
    assert not failed.exists()
    existing_dir = own / 'existing-dir.json'
    existing_dir.mkdir()
    invoke('CLI10_existing_directory', existing_dir, code=2)
    assert existing_dir.is_dir() and not list(existing_dir.iterdir())
    failed = own / 'absent-parent' / 'output.json'
    invoke('CLI11_parent_absent', failed, code=2)
    assert not failed.parent.exists()
    assert not list(own.glob('.iqs-c06-*'))
    assert (source / 'quick_scan_c06_manifest_v2_fixture.json').read_bytes() == manifest_raw
    assert (source / 'quick_scan_c06_authority_v2_fixture.json').read_bytes() == authority_raw
    summary = {'schema': 'iqs.c06_producer_cli_e2e/1', 'scope': 'IQS_private_authority_producer_only',
               'fixture_class': 'synthetic_not_StockWiki_owner_golden', 'cases': cases,
               'question_count': len(context['questions']), 'stable_output_sha256': sha(original),
               'source_manifest_sha256': sha(manifest_raw), 'source_authority_sha256': sha(authority_raw),
               'source_inputs_unchanged': True, 'staging_files_remaining': 0,
               'known_child_processes_terminal': True, 'actual_external_network_calls': 0,
               'paid_calls': 0, 'identity_attested': False, 'cleanup_pending': True}
    (own / 'cli-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'cases_passed': len(cases), 'question_count': len(context['questions']),
                      'scope': summary['scope'], 'identity_attested': False}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
