"""Independent offline review; owns only this run directory and copied trees."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time

RUN=Path(__file__).resolve().parent
PROJECTS=RUN.parents[2]
IQS=RUN.parents[1]
WORK=RUN/'isolated'
WORK.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
bindings={}
for short,repo in [('query','iqs-query-identity-lab'),('source','iqs-search-source-lab'),('resume','iqs-resume-chaos-lab'),('review','iqs-review-calibration-lab'),('retrieval','iqs-search-annotation-lab')]:
    lab=PROJECTS/repo
    env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}
    commit=subprocess.check_output(['git','-C',str(lab),'rev-parse','HEAD'],env=env,text=True).strip()
    dirty=subprocess.check_output(['git','-C',str(lab),'status','--porcelain','--untracked-files=no'],env=env,text=True)
    assert not dirty,(repo,dirty)
    paths=subprocess.check_output(['git','-C',str(lab),'ls-files','-z'],env=env).decode('utf-8').split('\0')
    rows=[]
    for rel in filter(None,paths):
        source=lab/rel
        assert source.is_file() and not source.is_symlink(),source
        data=source.read_bytes()
        rows.append({'path':rel,'bytes':len(data),'raw_sha256':hashlib.sha256(data).hexdigest()})
        if short in ('review','retrieval'):
            dest=WORK/short/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    bindings[short]={'repo':repo,'commit':commit,'tracked_clean':True,'files':rows}
write(RUN/'source-bindings.json',bindings)
frozen=IQS/'runs/independent-review-wave-2026-10-16/inputs'
lock=IQS/'docs/implementation/parallel-lanes/packages/2026-10-16-independent-review-wave/inputs.lock.json'
(WORK/'review-lock').mkdir(exist_ok=True)
isolated_lock=WORK/'review-lock/inputs.lock.json'
shutil.copyfile(lock,isolated_lock)
assert sha(lock)=='968fc8a41653e24e0701feea9bc75353bff90e923ecd96f37f6b8334818d1233'
LOCKED=WORK/'review-inputs-locked'
for row in json.loads(lock.read_text('utf-8'))['files']:
    source=frozen/row['path'];dest=LOCKED/row['path']
    assert source.is_file() and sha(source)==row['raw_sha256'] and source.stat().st_size==row['bytes'],source
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
python=Path('C:/Miniconda/python.exe')
results=json.loads((RUN/'executions.json').read_text('utf-8')) if (RUN/'executions.json').exists() else []
def environment(short):
    home=WORK/(short+'-home');home.mkdir(exist_ok=True)
    tmp=WORK/(short+'-tmp');tmp.mkdir(exist_ok=True)
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','COMSPEC','PATH','PATHEXT')}
    env.update(PYTHONPATH=str(WORK/short/'src'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',HOME=str(home),USERPROFILE=str(home),TEMP=str(tmp),TMP=str(tmp),HTTP_PROXY='http://127.0.0.1:9',HTTPS_PROXY='http://127.0.0.1:9',ALL_PROXY='http://127.0.0.1:9',NO_PROXY='')
    if short=='review':env.update(IQS_INPUTS_ROOT=str(LOCKED),IQS_LOCK_PATH=str(isolated_lock),IQS_INPUTS_LOCK=str(isolated_lock),IQS_EXPECTED_LOCK_SHA=sha(lock))
    return env
def run(short,name,args):
    t=time.monotonic();p=subprocess.run([str(python),'-B','-X','utf8',*args],cwd=WORK/short,env=environment(short),capture_output=True,text=True,encoding='utf-8',timeout=180)
    (RUN/(name+'.stdout.txt')).write_text(p.stdout,encoding='utf-8');(RUN/(name+'.stderr.txt')).write_text(p.stderr,encoding='utf-8')
    record={'name':name,'argv':[str(python),'-B','-X','utf8',*args],'cwd':str(WORK/short),'exit_code':p.returncode,'seconds':round(time.monotonic()-t,3),'stdout_sha256':sha(RUN/(name+'.stdout.txt')),'stderr_sha256':sha(RUN/(name+'.stderr.txt'))}
    results.append(record);write(RUN/'executions.json',results)
    print(name,p.returncode,p.stdout[-1200:],p.stderr[-1200:],flush=True)
    return p
run('review','review-cli-focused-separated-lock',['-m','pytest','-q','-p','no:cacheprovider','--basetemp='+str(WORK/'review-pytest-separated-lock'),'tests/test_v11_envelopes.py::test_new_cli_build_has_explicit_minor_envelope','tests/test_v11_envelopes.py::test_explicit_legacy_build_remains_readable'])
if not any(r['name']=='retrieval-focused' and r['exit_code']==0 for r in results):
    run('retrieval','retrieval-focused',['-m','pytest','-q','-p','no:cacheprovider','--basetemp='+str(WORK/'retrieval-pytest'),'tests/unit/test_controller_review.py','tests/e2e/test_cli.py::test_assign_validate_compare_chain','tests/e2e/test_cli.py::test_exit_codes_and_refusals'])
common=['--inputs',str(LOCKED),'--lock',str(isolated_lock),'--expected-lock-sha256',sha(lock)]
p=run('review','review-cli-build-separated-lock',['-m','iqs_review_calibration','build',*common,'--out',str(WORK/'review-casebook.json')]);assert p.returncode==0
p=run('review','review-cli-validate',['-m','iqs_review_calibration','validate',*common,'--casebook',str(WORK/'review-casebook.json')]);assert p.returncode==0
p=run('review','review-cli-assign',['-m','iqs_review_calibration','assign',*common,'--casebook',str(WORK/'review-casebook.json'),'--seed','independent-final-review18','--output',str(WORK/'review-assigned')]);assert p.returncode==0
print('prepared',str(WORK),flush=True)
