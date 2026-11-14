"""Once: normal Git publication of the four expressly approved PWF documents."""
from pathlib import Path
import hashlib
import json
import subprocess
import os

ENV = {k:v for k,v in os.environ.items() if k.upper() in {"PATH","SYSTEMROOT","WINDIR","COMSPEC","PATHEXT","SYSTEMDRIVE","USERPROFILE","HOMEDRIVE","HOMEPATH","APPDATA","LOCALAPPDATA","USERNAME","USERDOMAIN"}}
ENV.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / 'docs/implementation/intake/parallel-packages/2026-10-10/fact-remediation-02'
RECEIPT = OUT / 'documentation-publication-fact-r2-01.json'
START = OUT / 'documentation-publication-fact-r2-01.start.json'
PATHS = ['task_plan.md', 'progress.md', 'findings.md', 'docs/implementation/handoff-for-new-agent.md']
assert not RECEIPT.exists() and not START.exists()
START.write_text('{"state":"started","once_only":true}\n', 'utf-8')
events = []
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def run(args):
    done = subprocess.run(['git', *args], cwd=ROOT, env=ENV, capture_output=True, timeout=120)
    events.append(dict(args=args, exit_code=done.returncode,
        stdout=done.stdout.decode('utf-8', errors='replace'),
        stderr=done.stderr.decode('utf-8', errors='replace')))
    if done.returncode:
        raise RuntimeError(events[-1])
    return done.stdout


record = dict(scope='four explicitly approved first-party Markdown files only; no source/intake/DB/golden/Lab export', paths=PATHS)
try:
    assert not run(['diff', '--cached', '--name-only']).strip()
    assert run(['rev-parse', 'HEAD']).decode().strip() == '85829315c848e35aa08e372a2d691a3252cd59e4'
    assert run(['branch', '--show-current']).decode().strip() == 'master'
    assert run(['remote', 'get-url', 'origin']).decode().strip() == 'https://github.com/zhengcb81/invest-quick-scan.git'
    assert all('FACT R2集中续验（2026-10-11）' in (ROOT / path).read_text('utf-8') for path in PATHS)
    record['working_tree_raw_sha256'] = {path: sha((ROOT / path).read_bytes()) for path in PATHS}
    run(['add', '--', *PATHS])
    assert set(run(['diff', '--cached', '--name-only']).decode().splitlines()) == set(PATHS)
    run(['diff', '--cached', '--check'])
    staged = {path: sha(run(['show', ':' + path])) for path in PATHS}
    run(['commit', '-m', 'docs: record FACT R2 acceptance and C06 release readiness'])
    assert not run(['diff', '--cached', '--name-only']).strip()
    commit = run(['rev-parse', 'HEAD']).decode().strip()
    assert set(run(['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines()) == set(PATHS)
    committed = {path: sha(run(['show', commit + ':' + path])) for path in PATHS}
    assert staged == committed
    record.update(commit=commit, staged_sha256=staged, committed_sha256=committed)
    run(['push', 'origin', 'HEAD:refs/heads/master'])
    remote = run(['ls-remote', '--exit-code', 'origin', 'refs/heads/master']).decode().split()[0]
    assert remote == commit
    record.update(status='published', remote_commit=remote)
except Exception as exc:
    record.update(status='failed', error=str(exc))
    raise
finally:
    record['events'] = events
    with RECEIPT.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
print(json.dumps({key: value for key, value in record.items()
    if key not in {'events', 'working_tree_raw_sha256', 'staged_sha256', 'committed_sha256'}}))
