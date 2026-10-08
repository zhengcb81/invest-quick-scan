"""Run only necessary corrections/new paths; never overwrite original logs."""
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import OWN, OUT, REVIEW, env, save


def main():
    for owner in ['qa', 'sw']:
        (OWN / (owner + '_driver.py')).write_bytes((REVIEW / (owner + '_driver.py')).read_bytes())
    controlled = env('qa')
    controlled['PYTHONPATH'] = os.pathsep.join([str(OWN / 'guard'), str(REVIEW)])
    command = [sys.executable, '-B', '-X', 'utf8', '-m', 'pytest', str(REVIEW / 'test_joint_controller_corrections.py'),
       '-q', '-o', 'addopts=', '-p', 'no:cacheprovider', '--basetemp', str(OWN / 'tmp/corrections'),
       '--junitxml=' + str(OWN / 'logs/corrections-junit.xml')]
    start = time.monotonic()
    try:
        result = subprocess.run(command, cwd=OWN, env=controlled, capture_output=True, timeout=300)
        stdout, stderr, code, timeout = result.stdout, result.stderr, result.returncode, False
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code, timeout = error.stdout or b'', error.stderr or b'', None, True
    (OUT / 'corrections.stdout.log').write_bytes(stdout)
    (OUT / 'corrections.stderr.log').write_bytes(stderr)
    summary = dict(command=command, cwd=str(OWN), returncode=code, timed_out=timeout,
        wall_s=round(time.monotonic()-start, 3), source_written=False, paid_calls=0, external_http=0)
    save(OUT / 'corrections.process.json', summary)
    source = OWN / 'logs/corrections'
    for path in source.iterdir():
        assert path.is_file() and not path.is_symlink()
        target = OUT / 'correction-actors' / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    print(summary, flush=True)


if __name__ == '__main__':
    main()
