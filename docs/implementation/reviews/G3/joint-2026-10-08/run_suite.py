"""One concentrated guarded suite; preserve failures instead of editing expectations."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import IQS, OWN, OUT, REVIEW, env, save


def main():
    for owner in ['qa', 'sw']:
        (OWN / (owner + '_driver.py')).write_bytes((REVIEW / (owner + '_driver.py')).read_bytes())
    controlled = env('qa')
    controlled['PYTHONPATH'] = os.pathsep.join([str(OWN / 'guard'), str(REVIEW)])
    command = [sys.executable, '-B', '-X', 'utf8', '-m', 'pytest', str(REVIEW / 'test_joint.py'),
        '-q', '-o', 'addopts=', '-p', 'no:cacheprovider', '--basetemp', str(OWN / 'tmp/joint'),
        '--junitxml=' + str(OWN / 'logs/joint-junit.xml')]
    start = time.monotonic()
    try:
        result = subprocess.run(command, cwd=OWN, env=controlled, capture_output=True, timeout=600)
        stdout, stderr, code, timeout = result.stdout, result.stderr, result.returncode, False
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code, timeout = error.stdout or b'', error.stderr or b'', None, True
    (OUT / 'joint-suite.stdout.log').write_bytes(stdout)
    (OUT / 'joint-suite.stderr.log').write_bytes(stderr)
    save(OUT / 'joint-suite.process.json', dict(command=command, cwd=str(OWN),
        returncode=code, timed_out=timeout, wall_s=round(time.monotonic()-start, 3),
        source_written=False, paid_calls=0, external_http=0))
    for path in (OWN / 'logs').iterdir():
        assert path.is_file() and not path.is_symlink()
        target = OUT / 'suite-actors' / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    print(json.dumps(dict(returncode=code, timed_out=timeout,
                          wall_s=round(time.monotonic()-start, 3))), flush=True)


if __name__ == '__main__':
    main()
