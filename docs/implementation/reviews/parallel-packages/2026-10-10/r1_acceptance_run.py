"""Offline FACT R1 continuation; external source is always read-only."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('old_controller', HERE / 'acceptance_run.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
ROOT = old.ROOT
SOURCE = ROOT.parent / 'iqs-fact-content-lab'
WORK = ROOT / 'runs/p114r1a'
LAB = WORK / 'fact'
INTAKE = ROOT / 'docs/implementation/intake/parallel-packages/2026-10-10/remediation-01'
EXPECTED = 'd00e2b64c09ff0ff9a563fe6cc3cc11ec26b7555'

def git_state():
    cmds = [['rev-parse','HEAD'], ['branch','--show-current'],
            ['status','--porcelain=v1','-uall'], ['ls-files','-z'],
            ['remote','-v'], ['diff','--name-only','f7fb07895e36ebff67f2ba8932a592fd569cb9cd','HEAD']]
    rows = []
    for args in cmds:
        p = subprocess.run(['git','-C',str(SOURCE),*args],capture_output=True,
                           text=True,encoding='utf-8',timeout=30)
        if p.returncode: raise RuntimeError(p.stderr)
        rows.append({'args':args,'stdout':p.stdout,'exit_code':p.returncode})
    return rows

def freeze():
    assert not WORK.exists() and not INTAKE.exists()
    state = git_state()
    assert state[0]['stdout'].strip() == EXPECTED
    # Only the separately authorized CodeGraph infrastructure may be untracked.
    assert all(line.startswith('?? .codegraph/') for line in state[2]['stdout'].splitlines())
    lock = old.inspect_inputs()
    files = state[3]['stdout'].split('\0')[:-1]
    WORK.mkdir(parents=True)
    INTAKE.mkdir(parents=True)
    old.write(INTAKE/'source-git-before.json',state)
    LAB.mkdir()
    rows = []
    for rel in files:
        part = Path(rel)
        assert not part.is_absolute() and '..' not in part.parts
        assert not any(s.lower() in {'.git','.codegraph','.env','secrets','credentials'} for s in part.parts)
        src, dst = SOURCE/part, LAB/part
        old.safe(src)
        blob = src.read_bytes()
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open('xb') as f: f.write(blob)
        digest = hashlib.sha256(blob).hexdigest()
        assert old.digest(src) == old.digest(dst) == digest
        rows.append({'path':rel,'bytes':len(blob),'sha256':digest})
    doc = json.loads((LAB/'docs/handoff/FACT-CONTENT-01/remediation-01/artifacts.json').read_text(encoding='utf-8'))
    checks = []
    for entry in doc['artifacts']:
        part = Path(entry['path'])
        assert not part.is_absolute() and '..' not in part.parts
        src = SOURCE/part
        old.safe(src)
        checks.append({'path':entry['path'],'matches':old.digest(src)==entry['sha256'] and src.stat().st_size==entry['bytes']})
    old.write(INTAKE/'source-freeze.json',{'at':old.now(),'files':rows,'inputs':lock,'artifacts':checks})
    (WORK/'guard').mkdir()
    (WORK/'guard-logs').mkdir()
    (WORK/'temp').mkdir()
    (WORK/'guard/sitecustomize.py').write_text('''import os, socket, json
from pathlib import Path
def deny(*args, **kwargs):
    p = Path(os.environ['IQS_ACCEPT_GUARD_LOG']) / ('attempt-' + str(os.getpid()) + '.jsonl')
    with p.open('a',encoding='utf-8') as f: f.write(json.dumps({'pid':os.getpid(),'event':'blocked_socket_attempt'})+'\\n')
    raise OSError('IQS R1 acceptance: offline')
socket.socket.connect=deny
socket.socket.connect_ex=deny
socket.create_connection=deny
socket.getaddrinfo=deny
''',encoding='utf-8')
    old.write(WORK/'ownership.json',{'root':str(WORK),'controller':str(Path(__file__).resolve()),'at':old.now()})
    print(json.dumps({'files':len(rows),'artifacts':len(checks),'bad_artifacts':[x for x in checks if not x['matches']],'inputs':lock},ensure_ascii=False))

def environment():
    keep={'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','SYSTEMDRIVE'}
    env={k:v for k,v in os.environ.items() if k.upper() in keep}
    env.update(TEMP=str(WORK/'temp'),TMP=str(WORK/'temp'),TMPDIR=str(WORK/'temp'),
               PYTHONPATH=os.pathsep.join([str(WORK/'guard'),str(LAB/'src')]),
               PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',
               PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',IQS_ACCEPT_GUARD_LOG=str(WORK/'guard-logs'),
               IQS_ROOT=str(ROOT))
    return env

def run(label,args,timeout=240):
    dest=INTAKE/'logs'
    dest.mkdir(exist_ok=True)
    paths=[dest/f'{label}.{x}' for x in ['stdout.log','stderr.log','result.json']]
    assert not any(p.exists() for p in paths)
    command=[sys.executable,'-B','-X','utf8',*args]
    start=time.monotonic()
    timed_out=False
    with paths[0].open('xb') as out,paths[1].open('xb') as err:
        proc=subprocess.Popen(command,cwd=LAB,env=environment(),stdout=out,stderr=err)
        try: rc=proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
            proc.kill()
            rc=proc.wait(timeout=30)
    result={'at':old.now(),'pid':proc.pid,'command':command,'cwd':str(LAB),
            'exit_code':rc,'timed_out':timed_out,'terminal':proc.poll() is not None,
            'seconds':time.monotonic()-start,'sanitized_environment':True,
            'stdout_sha256':old.digest(paths[0]),'stderr_sha256':old.digest(paths[1])}
    old.write(paths[2],result)
    print(json.dumps(result,ensure_ascii=False))
    print(paths[0].read_text(encoding='utf-8',errors='replace')[-1800:])
    print(paths[1].read_text(encoding='utf-8',errors='replace')[-1000:])
    return result

if __name__=='__main__':
    if sys.argv[1]=='freeze': freeze()
    elif sys.argv[1]=='regress':
        run('fact-r1-regression-01',['-m','pytest','tests','-q','-p','no:cacheprovider',
                                    '--basetemp='+str(WORK/'pytest-temp'),
                                    '--junitxml='+str(INTAKE/'fact-r1-regression.xml')])
    elif sys.argv[1]=='handoff':
        run('fact-r1-handoff-01',[str(ROOT/'scripts/parallel_handoff_cli.py'),
             '--catalog',str(ROOT/'docs/implementation/parallel-lanes/packages/2026-10-10/manifest.json'),
             '--package-id','FACT-CONTENT-01','--input',str(LAB/'docs/handoff/FACT-CONTENT-01/remediation-01/handoff.json')])
    elif sys.argv[1]=='counterexamples':
        run('fact-r1-counterexamples-01',[str(HERE/'r1_counterexamples.py')])
    elif sys.argv[1]=='followup':
        run('fact-r1-counterexamples-02',[str(HERE/'r1_followup_counterexamples.py')])
    elif sys.argv[1]=='temporal':
        run('fact-r1-temporal-corrected-03',[str(HERE/'r1_temporal_case.py')])
    else: raise SystemExit('unknown action')
