"""One offline affected batch; received source unchanged, child logs preserved."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IQS=Path(__file__).resolve().parents[5]
OWN=IQS/'runs/qa-c06-remediation-2026-10-08-01'
QA=OWN/'qa'
OUT=IQS/'docs/implementation/intake/QA-C06-02/2026-10-08-remediation/verification'

def sha(data): return hashlib.sha256(data).hexdigest()
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def env():
    result={key:value for key,value in os.environ.items() if key.upper() in
        {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    result.update(PYTHONPATH=os.pathsep.join([str(OWN/'guard'),str(QA),str(QA/'src')]),
        PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        TEMP=str(OWN/'tmp'),TMP=str(OWN/'tmp'),TMPDIR=str(OWN/'tmp'),
        E97_OWNED_ROOT=str(OWN.resolve()),QA100_QA_ROOT=str(QA),STOCKQA_RUN_LIVE_E2E='0')
    return result

def execute(name,args,timeout=300):
    OUT.mkdir(parents=True,exist_ok=True)
    command=[sys.executable,'-B','-X','utf8',*args]
    start=time.monotonic()
    try:
        process=subprocess.run(command,cwd=QA,env=env(),capture_output=True,timeout=timeout)
        stdout,stderr,code=process.stdout,process.stderr,process.returncode
        timed_out=False
    except subprocess.TimeoutExpired as error:
        stdout,stderr,code=error.stdout or b'',error.stderr or b'',None
        timed_out=True  # subprocess.run has killed and waited for its direct child.
    (OUT/(name+'.stdout.log')).write_bytes(stdout)
    (OUT/(name+'.stderr.log')).write_bytes(stderr)
    row=dict(name=name,command=command,cwd=str(QA),returncode=code,timed_out=timed_out,
        wall_s=round(time.monotonic()-start,3),stdout_sha256=sha(stdout),stderr_sha256=sha(stderr))
    save(OUT/(name+'.result.json'),row)
    print(json.dumps({key:row[key] for key in ('name','returncode','timed_out','wall_s')}),flush=True)
    return row

def pytest(name,paths):
    return execute(name,['-m','pytest',*paths,'-q','-o','addopts=','-p','no:cacheprovider',
        '--basetemp',str(OWN/'tmp'/name)])

def main():
    units=['observation_context','c06_authority_binding','c06_complete_seal',
        'work_store','budget','result_outbox']
    checks=[pytest('affected-regression',[
        *['tests/unit/test_quick_scan_'+name+'.py' for name in units],
        'tests/integration/test_qa_c06_02_e2e.py','tests/integration/test_quick_scan_cli.py',
        'tests/integration/test_qa_c06_02_subprocess_cli.py'])]
    checks.append(pytest('original-nine-boundaries',[str(OWN/'controller_cases.py')]))
    checks.append(execute('public-handoff',[str(IQS/'scripts/parallel_handoff_cli.py'),
        '--input',str(OUT.parent/'worker/handoff.json'),'--package-id','QA-C06-02',
        '--catalog',str(IQS/'docs/implementation/parallel-lanes/packages/2026-10-07-wave2/manifest.json')]))
    source=json.loads((OWN/'snapshot.json').read_text('utf-8'))
    changed=[x['path'] for x in source if sha((QA/x['path']).read_bytes())!=x['sha256']]
    save(OUT/'batch-result.json',dict(checks=checks,snapshot_files=len(source),snapshot_changed=changed,
        source_written=False,external_http=0,paid_calls=0,downloads=0,synthetic_only=True,cleanup_pending=True))
    assert not changed

if __name__=='__main__': main()
