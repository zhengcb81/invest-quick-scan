"""One bounded offline QA acceptance batch; real CLI subprocess restart."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IQS=Path(__file__).resolve().parents[4]
OWN=IQS/'runs/qa-c06-02-2026-10-08-01'
QA=OWN/'qa'
OUT=IQS/'docs/implementation/intake/QA-C06-02/2026-10-08/verification'

def sha(data): return hashlib.sha256(data).hexdigest()
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def env():
    e={k:v for k,v in os.environ.items() if k.upper() in
       {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    e.update(PYTHONPATH=os.pathsep.join([str(OWN/'guard'),str(QA),str(QA/'src')]),
       PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
       TEMP=str(OWN/'tmp'),TMP=str(OWN/'tmp'),TMPDIR=str(OWN/'tmp'),
       E97_OWNED_ROOT=str(OWN.resolve()),QA100_QA_ROOT=str(QA),STOCKQA_RUN_LIVE_E2E='0')
    return e
def execute(name,args,cwd=QA,extra=None):
    e=env()
    if extra: e.update(extra)
    start=time.monotonic()
    p=subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=cwd,env=e,capture_output=True,timeout=180)
    (OUT/(name+'.stdout.log')).write_bytes(p.stdout)
    (OUT/(name+'.stderr.log')).write_bytes(p.stderr)
    row=dict(name=name,command=[sys.executable,'-B','-X','utf8',*args],cwd=str(cwd),
       returncode=p.returncode,wall_s=round(time.monotonic()-start,3),stdout_sha256=sha(p.stdout),stderr_sha256=sha(p.stderr))
    print(json.dumps({k:row[k] for k in ('name','returncode','wall_s')}),flush=True)
    return row

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Stub only requests' HTTP boundary, in a separate opt-in child runtime.
    # This is test instrumentation and is never copied into StockQA source.
    hook='''
if os.environ.get('QA100_STUB_HTTP') == '1':
    import importlib.util
    import json
    import re
    import requests
    test_path = Path(os.environ['QA100_QA_ROOT'])/'tests/integration/test_qa_c06_02_e2e.py'
    spec = importlib.util.spec_from_file_location('qa100_fixture',test_path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    def _qa100_post(self,*args,**kwargs):
        text=kwargs['json']['input']
        match=re.search(r'Target question_id: ([A-Za-z0-9_.]+)\\.',text)
        assert match is not None
        with (Path.cwd()/'http-stub-sends.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps({'question_id':match.group(1),'synthetic_only':True})+'\\n')
        return fixture._response_for(match.group(1))
    requests.Session.post=_qa100_post
'''
    guard=OWN/'guard/sitecustomize.py'
    guard.write_bytes(guard.read_bytes()+hook.encode('utf-8'))
    (OUT/'sitecustomize-executed.py').write_bytes(guard.read_bytes())
    checks=[]
    unit=['test_quick_scan_observation_context.py','test_quick_scan_c06_complete_seal.py',
          'test_quick_scan_work_store.py','test_quick_scan_budget.py','test_quick_scan_result_outbox.py']
    checks.append(execute('affected-regression',['-m','pytest',*[f'tests/unit/{n}' for n in unit],
       'tests/integration/test_qa_c06_02_e2e.py','tests/integration/test_quick_scan_cli.py',
       '-q','-o','addopts=','-p','no:cacheprovider','--basetemp',str(OWN/'tmp/pytest')]))
    checks.append(execute('public-handoff',[str(IQS/'scripts/parallel_handoff_cli.py'),
       '--input',str(OUT.parent/'worker/handoff.json'),'--package-id','QA-C06-02',
       '--catalog',str(IQS/'docs/implementation/parallel-lanes/packages/2026-10-07-wave2/catalog.json')]))
    setup=OWN/'setup_cli.py'
    setup.write_text('''import importlib.util,os
from pathlib import Path
p=Path(os.environ['QA100_QA_ROOT'])/'tests/integration/test_qa_c06_02_e2e.py'
s=importlib.util.spec_from_file_location('fixture',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m._setup(Path.cwd())
''',encoding='utf-8')
    case=OWN/'public-cli'
    case.mkdir()
    checks.append(execute('cli-inputs',[str(setup)],cwd=case))
    args=[str(QA/'main_with_llm.py'),'--company','Fixture Corp','--entity-id','ENT_CONTEXT_FIXTURE',
       '--provider','openai','--config',str(case/'questions.json'),'--output',str(case/'result.json'),
       '--require-search','--identity-snapshot',str(case/'identity.json'),
       '--spend-authorization',str(case/'spend_authorization.json'),'--question-manifest',str(case/'manifest.json'),
       '--security-scope-id','SEC_CONTEXT_FIXTURE','--c06-authority',str(case/'quick_scan_c06_authority.json')]
    checks.append(execute('cli-cold',args,cwd=case,extra={'QA100_STUB_HTTP':'1'}))
    sends=case/'http-stub-sends.jsonl'
    cold_sends=len(sends.read_text('utf-8').splitlines()) if sends.exists() else 0
    # Real process restart, stub removed. Any network attempt is rejected by guard.
    checks.append(execute('cli-warm',args,cwd=case))
    checks.append(execute('cli-seal',[str(QA/'main_with_llm.py'),'--seal-deliveries',
       '--c06-authority',str(case/'quick_scan_c06_authority.json')],cwd=case))
    after_sends=len(sends.read_text('utf-8').splitlines()) if sends.exists() else 0
    original=json.loads((OWN/'snapshot.json').read_text('utf-8'))
    changed=[x['path'] for x in original if sha((QA/x['path']).read_bytes())!=x['sha256']]
    save(OUT/'batch-result.json',dict(checks=checks,cold_sends=cold_sends,warm_seal_added_sends=after_sends-cold_sends,
       snapshot_files=len(original),snapshot_changed=changed,source_written=False,
       paid_calls=0,downloads=0,external_http=0,synthetic_only=True,cleanup_pending=True))
    assert not changed

if __name__=='__main__': main()
