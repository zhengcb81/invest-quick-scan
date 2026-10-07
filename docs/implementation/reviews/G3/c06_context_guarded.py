"""Run this metadata batch in one private, offline IQS test root."""
import os
from pathlib import Path
import sys
import tempfile

IQS = Path(__file__).resolve().parents[4]
OWN = Path(os.environ['IQS_C06_TEST_ROOT']).resolve()
if not OWN.is_relative_to(IQS / 'runs') or not OWN.name.startswith('c06-context-'):
    raise RuntimeError('private c06-context root required')
OWN.mkdir(parents=True, exist_ok=True)
for name in list(os.environ):
    if name.endswith(('API_KEY', 'API_TOKEN')) or 'RUN_LIVE' in name:
        os.environ.pop(name)
os.environ.update(TEMP=str(OWN), TMP=str(OWN), TMPDIR=str(OWN),
                  PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
tempfile.tempdir = str(OWN)
sys.dont_write_bytecode = True


def audit(event, args):
    if event.startswith(('socket.', 'subprocess.', 'winreg.')) or event in ('os.system', 'os.posix_spawn'):
        raise RuntimeError('offline metadata test: network/process/registry forbidden')
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        mode, flags = args[1:3]
        writing = bool(mode and any(char in mode for char in 'wax+')) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing and not Path(os.fsdecode(args[0])).resolve().is_relative_to(OWN):
            raise RuntimeError('offline metadata test: root-out write')
    if event in ('os.remove', 'os.rmdir', 'os.mkdir', 'os.rename', 'os.link', 'os.symlink'):
        targets = args[:2] if event in ('os.rename', 'os.link', 'os.symlink') else args[:1]
        if any(isinstance(p, (str, bytes, os.PathLike)) and not Path(os.fsdecode(p)).resolve().is_relative_to(OWN) for p in targets):
            raise RuntimeError('offline metadata test: root-out mutation')


sys.addaudithook(audit)
try:
    (IQS / 'outside-c06-context-canary').write_text('forbidden', encoding='utf-8')
except RuntimeError:
    pass
else:
    raise RuntimeError('write guard failed')
import socket
try:
    socket.getaddrinfo('example.invalid', 443)
except RuntimeError:
    pass
else:
    raise RuntimeError('network guard failed')
print('c06_context_guard_canaries_passed', flush=True)
sys.path[:0] = [str(IQS / 'scripts'), str(IQS / 'tests')]
if sys.argv[1:2] == ['--public-cli']:
    # A separate OS process runs the actual entrypoint with the SAME guard;
    # this is not an in-process test double for the CLI implementation.
    import runpy
    sys.argv = [str(IQS / 'scripts/c06_authority.py'), *sys.argv[2:]]
    runpy.run_path(sys.argv[0], run_name='__main__')
    raise RuntimeError('public CLI must exit explicitly')
runtime_value = os.environ.get('IQS_STOCKQA_CONTEXT_RUNTIME')
if runtime_value:
    runtime = Path(runtime_value).resolve()
    if not runtime.is_relative_to(OWN) or not (runtime.parent / 'export-manifest.json').is_file():
        raise RuntimeError('StockQA runtime must be an exact private export')
    sys.path.insert(0, str(runtime))
os.chdir(IQS)
import pytest
raise SystemExit(pytest.main(sys.argv[1:] + ['-p', 'no:cacheprovider', '--basetemp', str(OWN / 'pytest'),
                                          '--log-file', str(OWN / 'pytest.log')]))
