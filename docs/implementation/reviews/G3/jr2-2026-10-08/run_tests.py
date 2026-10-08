"""Guarded targeted JR2 runs with exclusive labels and preserved raw streams."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / 'runs/jr2-2026-10-08-01'
OUT = IQS / 'docs/implementation/intake/G3/2026-10-08-jr2'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--select')
    parser.add_argument('tests', nargs='*', default=[])
    args = parser.parse_args()
    assert args.label.replace('-', '').replace('_', '').isalnum()
    log = OWN / 'logs/worker' / args.label
    log.mkdir(parents=True, exist_ok=False)
    tests = args.tests or ['tests/unit/test_quick_scan_result_outbox.py',
             'tests/unit/test_q10_delivery.py', 'tests/unit/test_quick_scan_work_store.py']
    for name in tests:
        path = (OWN / 'qa' / name).resolve()
        assert path.is_relative_to(OWN / 'qa/tests') and path.is_file()
    env = {key: value for key, value in os.environ.items() if key.upper() in
       {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    env.update(PYTHONPATH=os.pathsep.join([str(OWN/'guard'),str(OWN/'qa'),str(OWN/'qa/src')]),
       E97_OWNED_ROOT=str(OWN), TEMP=str(OWN/'tmp'), TMP=str(OWN/'tmp'), TMPDIR=str(OWN/'tmp'),
       PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', STOCKQA_RUN_LIVE_E2E='0')
    command = [sys.executable, '-B', '-X', 'utf8', '-m', 'pytest', *tests, '-q', '-o', 'addopts=',
               '-p', 'no:cacheprovider', '--basetemp='+str(OWN/'tmp'/args.label),
               '--junitxml='+str(log/'junit.xml')]
    if args.select:
        command += ['-k', args.select]
    watched = ['src/utils/quick_scan_result_outbox.py', 'src/utils/quick_scan_work_store.py',
               'tests/unit/test_quick_scan_result_outbox.py', 'tests/unit/test_q10_delivery.py',
               'tests/unit/test_quick_scan_work_store.py', 'tests/unit/test_quick_scan_c06_complete_seal.py',
               'tests/integration/test_qa_c06_02_e2e.py']
    hashes = {name: hashlib.sha256((OWN/'qa'/name).read_bytes()).hexdigest() for name in watched}
    guard_sha = hashlib.sha256((OWN/'guard/sitecustomize.py').read_bytes()).hexdigest()
    start = time.monotonic()
    try:
        result = subprocess.run(command, cwd=OWN/'qa', env=env, capture_output=True, timeout=300)
        stdout, stderr, code, timeout = result.stdout, result.stderr, result.returncode, False
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code, timeout = error.stdout or b'', error.stderr or b'', None, True
    (log/'stdout.log').write_bytes(stdout)
    (log/'stderr.log').write_bytes(stderr)
    receipt = dict(command=command, returncode=code, timeout=timeout, wall_s=round(time.monotonic()-start,3),
                  key_environment_removed=True, paid_calls=0, external_source_written=False,
                  executed_source_hashes=hashes, executed_guard_sha256=guard_sha,
                  executed_source_unchanged=all(hashlib.sha256((OWN/'qa'/name).read_bytes()).hexdigest()==digest
                                               for name, digest in hashes.items()))
    (log/'process.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    archived = OUT/'verification'/args.label
    archived.mkdir(parents=True, exist_ok=False)
    for path in log.iterdir():
        assert path.is_file() and not path.is_symlink()
        (archived/path.name).write_bytes(path.read_bytes())
    print(json.dumps(receipt,ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
