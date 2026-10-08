"""Narrow offline cross-owner harness; records actual processes, no production writes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IQS = Path(__file__).resolve().parents[5]
REVIEW = Path(__file__).resolve().parent
OWN = IQS / 'runs/joint-2026-10-08-01'
OUT = IQS / 'docs/implementation/intake/G3/2026-10-08-joint/verification'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def env(owner):
    result = {k: v for k, v in os.environ.items() if k.upper() in
              {'SYSTEMROOT', 'WINDIR', 'PATH', 'PATHEXT', 'COMSPEC', 'USERPROFILE',
               'APPDATA', 'LOCALAPPDATA', 'SYSTEMDRIVE'}}
    result.update(PYTHONPATH=os.pathsep.join([str(OWN / 'guard'), str(OWN / owner),
                  str(OWN / owner / 'src')]), E97_OWNED_ROOT=str(OWN),
                  TEMP=str(OWN / 'tmp'), TMP=str(OWN / 'tmp'), TMPDIR=str(OWN / 'tmp'),
                  PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                  STOCKQA_RUN_LIVE_E2E='0')
    return result


def actor(owner, label, request, timeout=270):
    req, result = OWN / 'cases' / (label + '.request.json'), OWN / 'cases' / (label + '.response.json')
    assert not req.exists() and not result.exists(), 'Unique process label required'
    save(req, request)
    command = [sys.executable, '-B', '-X', 'utf8', str(OWN / (owner + '_driver.py')), str(req), str(result)]
    started = time.monotonic()
    try:
        proc = subprocess.run(command, cwd=OWN / owner, env=env(owner), capture_output=True, timeout=timeout)
        stdout, stderr, code, timed_out = proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code, timed_out = error.stdout or b'', error.stderr or b'', None, True
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / (label + '.stdout.log')).write_bytes(stdout)
    (OUT / (label + '.stderr.log')).write_bytes(stderr)
    save(OUT / (label + '.process.json'), dict(command=command, cwd=str(OWN / owner),
        returncode=code, timed_out=timed_out, wall_s=round(time.monotonic() - started, 3),
        stdout_sha256=hashlib.sha256(stdout).hexdigest(), stderr_sha256=hashlib.sha256(stderr).hexdigest()))
    if result.exists():
        (OUT / (label + '.response.json')).write_bytes(result.read_bytes())
    assert code == 0 and not timed_out, label + ': actor failed; inspect preserved stderr'
    return json.loads(result.read_text('utf-8'))


def prepare_release():
    raw = (OWN / 'qa/tests/fixtures/quick_scan_c06_manifest_v2_fixture.json').read_bytes()
    manifest = json.loads(raw)
    locks = []
    for lock in manifest['module_locks']:
        data = (IQS / lock['artifact_ref']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == lock['artifact_sha256']
        locks.append(dict(path=lock['artifact_ref'], sha256=lock['artifact_sha256']))
    # Independent frozen question input, established before the first model stub.
    release = dict(module_package_id=manifest['module_package_id'], release_id=manifest['module_release_id'],
                   catalog_version=manifest['template_version'], semantic_fingerprint_version='2.0.0',
                   questions={q['id']: dict(field_id=q['metric_id'], scope=q['scope'], response_kind='score',
                     rubric_version=q['rubric_version'], construct_id=q['construct_id'],
                     definition_sha256=q['definition_sha256'], semantic_sha256=q['semantic_sha256'])
                     for q in manifest['questions']})
    path = OWN / 'independent-release.json'
    save(path, release)
    save(OUT / 'release-provenance.json', dict(source='pre-dispatch frozen synthetic IQS manifest, not observations',
         manifest_sha256=hashlib.sha256(raw).hexdigest(), locks=locks, source_written=False,
         real_owner_golden=False, release_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (OUT / 'independent-release.json').write_bytes(path.read_bytes())
    return path


def main():
    for name in ['qa', 'sw']:
        (OWN / (name + '_driver.py')).write_bytes((REVIEW / (name + '_driver.py')).read_bytes())
    release = prepare_release()
    qa, sw = OWN / 'cases/a-selected', OWN / 'cases/sw-corrected'
    seed = json.loads((OUT / 'seed-corrected.response.json').read_text('utf-8'))
    assert seed['identity_state'] == 'provisional'
    produced = actor('qa', 'cold-selected', dict(op='produce', root=str(qa), run_label='J108_A', answers={
        'IQS_01': dict(score=2, large=True),
        'IQS_02': dict(status='insufficient_evidence', score=None),
        'IQS_04': dict(status='not_applicable', score=None, basis='not_applicable')}))
    save(OUT / 'producer-summary.json', produced)
    print(json.dumps(dict(producer_cli=produced['cli_exit'],
                          packages=len(produced.get('packages', {})), http=produced.get('http_sends'))), flush=True)
    assert produced['cli_exit'] == 0 and len(produced['packages']) == 31
    rows = []
    for qid in ['IQS_01', 'IQS_02', 'IQS_04', 'IQS_22']:
        delivery = produced['packages'][qid]
        result = actor('sw', 'import-' + qid, dict(op='import', root=str(sw),
             package=delivery['path'], release=str(release)))
        rows.append(dict(question_id=qid, result=result))
        print(json.dumps(dict(question=qid, exit=result['cli_exit'], receipt=result['receipt'])), flush=True)
    save(OUT / 'initial-imports.json', rows)
    assert all(x['result']['cli_exit'] == 0 and x['result']['receipt']['summary'] == {'accepted': 1} for x in rows)
    result = actor('sw', 'read-initial', dict(op='observations', root=str(sw)))
    save(OUT / 'j01-initial-observations.json', result)
    print(json.dumps(dict(initial_observation_count=result['counts']['observations'])), flush=True)


if __name__ == '__main__':
    main()
