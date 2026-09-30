"""Read-only StockQA review runner; all execution writes stay in its unique TEMP root."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

REPORT = Path(__file__).resolve().parent
REPO = Path('C:/Users/郑曾波/Projects/StockQAbyLLM')


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def snapshot():
    records, errors = {}, []
    def error(exc):
        errors.append({'path': str(exc.filename), 'error': type(exc).__name__, 'errno': exc.errno})
    for folder, dirs, names in os.walk(REPO, onerror=error, followlinks=False):
        # Git internals may change independently; use read-only status/HEAD below.
        dirs[:] = [d for d in dirs if d != '.git']
        for name in names:
            p = Path(folder) / name
            rel = p.relative_to(REPO).as_posix()
            try:
                s = p.lstat()
                data = {'size': s.st_size, 'mtime_ns': s.st_mtime_ns, 'mode': s.st_mode}
                if p.is_symlink() or name.lower() == 'nul':
                    data['sha256'] = None
                    data['hash_note'] = 'link/device-like path is not opened'
                else:
                    with p.open('rb') as fh:
                        data['sha256'] = hashlib.file_digest(fh, 'sha256').hexdigest()
                records[rel] = data
            except OSError as exc:
                error(exc)
    env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}
    git = subprocess.run(['git', '--no-optional-locks', 'status', '--porcelain=v1', '--untracked-files=all'],
                         cwd=REPO, env=env, capture_output=True, text=True, encoding='utf-8', errors='backslashreplace')
    head = subprocess.run(['git', '--no-optional-locks', 'rev-parse', 'HEAD'], cwd=REPO,
                          env=env, capture_output=True, text=True, encoding='utf-8', errors='backslashreplace')
    return {'files': records, 'read_errors': errors, 'git_status': git.stdout,
            'git_stderr': git.stderr, 'git_exit': git.returncode, 'head': head.stdout.strip()}


def child():
    root = Path(sys.argv[2]).resolve()
    os.chdir(root)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(REPO))
    denied = []
    allowed_internal_pipes = []
    def check(path, event):
        if isinstance(path, int) or path is None:
            return
        candidate = Path(os.fsdecode(path)).resolve()
        if not candidate.is_relative_to(root):
            denied.append({'event': event, 'path': str(candidate)})
            raise PermissionError('review write guard denied path outside unique TEMP root')
    def audit(event, args):
        if event == 'open':
            path, mode, flags = args
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
                    isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
                check(path, event)
        elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.utime', 'os.truncate'):
            check(args[0], event)
        elif event in ('os.rename', 'os.replace', 'os.link', 'os.symlink'):
            check(args[0], event); check(args[1], event)
        elif event == 'socket.connect':
            caller = sys._getframe(1)
            address = args[1]
            # Windows asyncio creates its wake-up self-pipe via stdlib socketpair.
            # This narrow exception is not a provider connection or general localhost allowlist.
            if (caller.f_code.co_name == '_fallback_socketpair'
                    and Path(caller.f_code.co_filename).resolve() == Path(sys.base_prefix, 'Lib', 'socket.py').resolve()
                    and isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1')):
                allowed_internal_pipes.append({'event': event, 'purpose': 'stdlib asyncio self-pipe'})
                return
            denied.append({'event': event, 'path': None})
            raise PermissionError('review prohibits live network and subprocess execution')
        elif event in ('socket.getaddrinfo', 'subprocess.Popen', 'os.system'):
            denied.append({'event': event, 'path': None})
            raise PermissionError('review prohibits live network and subprocess execution')
    sys.addaudithook(audit)
    import pytest
    selected = sys.argv[3:]
    args = ['-c', str(REPO / 'pyproject.toml'), '-o', 'addopts=', '-p', 'no:cacheprovider',
            '-p', 'pytest_asyncio.plugin', '--strict-markers', '--strict-config', '-ra', '-v',
            '--basetemp', str(root / 'pytest'), '--junitxml', str(root / 'junit.xml'),
            '--log-file', str(root / 'pytest.log'), *selected]
    try:
        code = pytest.main(args)
    finally:
        dump(root / 'guard-events.json', denied)
        dump(root / 'internal-pipes.json', allowed_internal_pipes)
    raise SystemExit(code)


def main():
    name = sys.argv[1]
    selected = sys.argv[2:]
    root = Path(tempfile.mkdtemp(prefix='stockqa-readonly-review-' + name + '-')).resolve()
    (root / 'logs').mkdir()
    before = snapshot()
    dump(REPORT / (name + '-pre-state.json'), before)
    env = dict(os.environ)
    # Do not expose or use user provider credentials/configuration during review.
    for key in list(env):
        if 'API_KEY' in key.upper() or key.upper().endswith('_TOKEN') or key == 'STOCKQA_RUN_LIVE_E2E':
            env.pop(key)
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
               TMP=str(root), TEMP=str(root), TMPDIR=str(root),
               COVERAGE_FILE=str(root / '.coverage'), PYTHONPATH=str(REPO))
    command = [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()), '--child', str(root), *selected]
    completed = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True,
                               encoding='utf-8', errors='replace', timeout=240)
    (REPORT / (name + '-stdout.log')).write_text(completed.stdout, encoding='utf-8')
    (REPORT / (name + '-stderr.log')).write_text(completed.stderr, encoding='utf-8')
    after = snapshot()
    dump(REPORT / (name + '-post-state.json'), after)
    drift = {'added': sorted(set(after['files']) - set(before['files'])),
             'removed': sorted(set(before['files']) - set(after['files'])),
             'modified': sorted(p for p in set(before['files']) & set(after['files']) if before['files'][p] != after['files'][p]),
             'git_changed': before['git_status'] != after['git_status'],
             'read_errors_changed': before['read_errors'] != after['read_errors']}
    for file in ('junit.xml', 'guard-events.json', 'internal-pipes.json'):
        if (root / file).exists():
            shutil.copyfile(root / file, REPORT / (name + '-' + file))
    artifacts = []
    for p in root.rglob('*'):
        if p.is_file():
            artifacts.append({'path': str(p), 'size': p.stat().st_size,
                              'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    result = {'timestamp': datetime.now(timezone.utc).isoformat(), 'command': command,
              'cwd': str(root), 'exit_code': completed.returncode,
              'external_readable_files': len(before['files']), 'preexisting_inaccessible': before['read_errors'],
              'external_drift': drift, 'temp_artifacts': artifacts,
              'cleanup': 'TEMP root intentionally retained as review evidence; no pre-existing files removed.'}
    dump(REPORT / (name + '-execution.json'), result)
    print(json.dumps({k: result[k] for k in ('exit_code', 'cwd', 'external_readable_files', 'external_drift')}, indent=2))
    print(completed.stdout[-7000:])
    print(completed.stderr[-1500:])


if __name__ == '__main__':
    child() if len(sys.argv) > 1 and sys.argv[1] == '--child' else main()
