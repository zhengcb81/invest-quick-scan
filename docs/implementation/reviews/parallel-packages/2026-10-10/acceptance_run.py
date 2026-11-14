"""Controller-only, offline acceptance. Never executes tests in a source repo."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[5]
INTAKE = ROOT / 'docs/implementation/intake/parallel-packages/2026-10-10'
WORK = ROOT / 'runs/p114a'
LOCK = ROOT / 'docs/implementation/parallel-lanes/packages/2026-10-10/inputs.lock.json'
PAIRS = [('EVID-REF-02', 'iqs-evidence-lab', 'evid'), ('FACT-CONTENT-01', 'iqs-fact-content-lab', 'fact')]

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def safe(path):
    probe = path
    while True:
        s = probe.lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 0x400:
            raise RuntimeError(f'link/reparse: {probe}')
        if probe.parent == probe:
            break
        probe = probe.parent
    if path.is_file() and path.stat().st_nlink != 1:
        raise RuntimeError(f'hardlink: {path}')

def inspect_inputs():
    mismatches = []
    lock = json.loads(LOCK.read_text(encoding='utf-8'))
    for x in lock['files']:
        p = Path(x['source_root']) / x['path']
        safe(p)
        if p.stat().st_size != x['bytes'] or digest(p) != x['sha256']:
            mismatches.append(x['path'])
    if mismatches:
        raise RuntimeError(f'locked input drift: {mismatches}')
    return {'files': len(lock['files']), 'mismatches': mismatches, 'lock_sha256': digest(LOCK)}

def freeze():
    assert not WORK.exists(), WORK
    inputs = inspect_inputs()
    source_git = json.loads((INTAKE / 'source-git-before.json').read_text(encoding='utf-8'))
    WORK.mkdir(parents=True)
    (WORK / 'guard').mkdir()
    (WORK / 'guard/sitecustomize.py').write_text('''import os, socket, json
from pathlib import Path
def deny(*a, **k):
    path = Path(os.environ['IQS_ACCEPT_GUARD_LOG']) / ('attempt-' + str(os.getpid()) + '.jsonl')
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps({'pid': os.getpid(), 'event': 'blocked_socket_attempt'}) + '\\n')
    raise OSError('IQS acceptance: network denied')
socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.create_connection = deny
socket.getaddrinfo = deny
''', encoding='utf-8')
    rows = []
    artifacts = []
    for (package, name, label), git in zip(PAIRS, source_git):
        src, dst = ROOT.parent / name, WORK / label
        dst.mkdir()
        tracked = git['commands'][3]['stdout'].split('\0')[:-1]
        for rel in tracked:
            pp = Path(rel)
            assert not pp.is_absolute() and '..' not in pp.parts
            assert '.git' not in pp.parts and '.codegraph' not in pp.parts
            assert not any(s.lower() in {'api_key', '.env', 'credentials', 'secrets'} for s in pp.parts)
            source, target = src / pp, dst / pp
            safe(source)
            blob = source.read_bytes()
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as f:
                f.write(blob)
            sha = hashlib.sha256(blob).hexdigest()
            assert digest(target) == sha and digest(source) == sha
            rows.append({'package': package, 'path': rel, 'bytes': len(blob), 'sha256': sha})
        handoff = src / 'docs/handoff' / package
        doc = json.loads((handoff / 'artifacts.json').read_text(encoding='utf-8'))
        entries = doc.get('artifacts', doc.get('files', []))
        for x in entries:
            rel = x['path']
            pp = Path(rel)
            assert not pp.is_absolute() and '..' not in pp.parts
            p = src / pp
            safe(p)
            artifacts.append({'package': package, 'path': rel,
                              'matches': p.stat().st_size == x['bytes'] and digest(p) == x['sha256']})
    write(INTAKE / 'source-freeze.json', {'at': now(), 'inputs': inputs, 'source_files': rows, 'artifacts': artifacts, 'external_source_written': False})
    write(WORK / 'ownership.json', {'controller': str(Path(__file__).resolve()), 'root': str(WORK), 'at': now()})
    for leaf in ['progress.md', 'findings.md']:
        with (ROOT / leaf).open('a', encoding='utf-8') as f:
            f.write('\n\n### 2026-10-10 两个独立施工包集中验收启动\n'
                    '- 用户通知EVID-REF-02与FACT-CONTENT-01交付；只读固定实际HEAD 1597a08/f7fb078和241受控文件，213输入锁逐件核对。两个源仓均无remote，Lab原CodeGraph两设施保留。\n'
                    '- IQS独占runs/p114a运行副本，源仓不运行测试、不修改；每包一次集中独审与回归/公开CLI反例。初步handoff公开校验EVID exit1/schema_invalid、FACT exit0，仅结构结论；已发现准确性资格/分母与内容hash/负例独立性疑点，待真实复现不预报签收。\n'
                    '- 前一只读信息脚本把字符串当Path.name导致exit1，无源写入；PWF首次空patch因标题不匹配被拒，task_plan有效改动保留。原C06 checkpoint07/活根和全局门不动，0付费API/公司文档下载。\n')
    print(json.dumps({'copied': len(rows), 'artifact_entries': len(artifacts), 'bad_artifacts': [x for x in artifacts if not x['matches']], 'inputs': inputs}, ensure_ascii=False))

def env(label):
    root = WORK / label
    temp = root / '.acceptance-temp'
    temp.mkdir(exist_ok=True)
    logs = WORK / 'guard-logs'
    logs.mkdir(exist_ok=True)
    allowed = {'PATH', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT', 'SYSTEMDRIVE'}
    e = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    e.update(TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp),
             PYTHONPATH=os.pathsep.join([str(WORK / 'guard'), str(root / 'src')]),
             PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
             PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', IQS_ACCEPT_GUARD_LOG=str(logs),
             IQS_ROOT=str(ROOT), IQS_EVIDENCE_LAB_IQS_ROOT=str(ROOT),
             IQS_EVIDENCE_LAB_RECEIPT_DIR=str(root / '.acceptance-receipts'))
    return e

def run(label, name, args, timeout=300):
    directory = INTAKE / 'logs'
    directory.mkdir(exist_ok=True)
    for suffix in ['stdout.log', 'stderr.log', 'result.json']:
        assert not (directory / f'{name}.{suffix}').exists()
    command = [sys.executable, '-B', '-X', 'utf8', *args]
    start = time.monotonic()
    with (directory / f'{name}.stdout.log').open('xb') as out, (directory / f'{name}.stderr.log').open('xb') as err:
        p = subprocess.Popen(command, cwd=WORK / label, env=env(label), stdout=out, stderr=err)
        try:
            rc = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            rc = p.wait()
            raise RuntimeError(f'owned process timeout pid={p.pid}, exit={rc}')
    result = {'at': now(), 'command': command, 'cwd': str(WORK / label), 'pid': p.pid,
              'exit_code': rc, 'elapsed_seconds': time.monotonic()-start,
              'terminal': p.poll() is not None, 'sanitized_environment': True,
              'external_source_written': False, 'paid_api_requests': 0,
              'stdout_sha256': digest(directory / f'{name}.stdout.log'),
              'stderr_sha256': digest(directory / f'{name}.stderr.log')}
    write(directory / f'{name}.result.json', result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    print((directory / f'{name}.stdout.log').read_text(encoding='utf-8', errors='replace')[-2200:], flush=True)
    print((directory / f'{name}.stderr.log').read_text(encoding='utf-8', errors='replace')[-1000:], flush=True)
    return result

def regress(label):
    run(label, f'{label}-package-regression-01', ['-m','pytest','tests','-q','-p','no:cacheprovider',f'--junitxml={INTAKE / (label+"-regression.xml")}'])

if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'freeze':
        freeze()
    elif action == 'regress':
        regress(sys.argv[2])
    else:
        raise SystemExit('unknown action')
