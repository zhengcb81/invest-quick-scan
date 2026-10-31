from pathlib import Path
import os,subprocess,json,hashlib,shutil,sys,uuid,time
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
SRC=ROOT/'runs/close-support31/perf-review/snapshot'
DST=OUT/'snapshot'
OUT.mkdir(exist_ok=True)
if DST.exists():raise SystemExit('refuse preexisting independent snapshot')
shutil.copytree(SRC,DST,ignore=shutil.ignore_patterns('.git','.tmp','__pycache__','.pytest_cache'))
files=['tests/integration/test_native_fault_parity.py','tests/unit/test_native_delegation_faults.py','tests/unit/test_publisher_authority_boundary.py']
pins=[]
for rel in files:
 b=(DST/rel).read_bytes();pins.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA'}}
env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
subprocess.run(['git','-C',str(DST),'init','--quiet'],env=env,check=True,capture_output=True)
tmp=ROOT/('.p31pi-'+uuid.uuid4().hex[:8]);tmp.mkdir(exist_ok=False)
env.update(TEMP=str(tmp),TMP=str(tmp),PYTHONPATH=str(DST/'src'))
cmd=[sys.executable,'-B','-m','pytest',*files,'-q','-p','no:cacheprovider','--override-ini','addopts=','--basetemp',str(tmp/'pytest')]
start=datetime.now(timezone.utc).isoformat();clock=time.perf_counter()
try:
 p=subprocess.run(cmd,cwd=DST,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
 (OUT/'pytest.log').write_text(p.stdout+p.stderr,encoding='utf-8',newline='\n')
finally:
 if tmp.resolve().parent!=ROOT.resolve() or not tmp.name.startswith('.p31pi-'):raise ValueError('cleanup boundary')
 shutil.rmtree(tmp)
result={'reviewer_agent_id':'/root/review_time_result_wiring31','author_agent_id':'/root/review_perf_close31','input_files':pins,'argv':cmd,'cwd':str(DST),'started_at':start,'elapsed_seconds':time.perf_counter()-clock,'exit_code':p.returncode,'output':p.stdout,'log_sha256':hashlib.sha256((OUT/'pytest.log').read_bytes()).hexdigest(),'cleanup':{'temporary_root':str(tmp),'removed':not tmp.exists(),'paid_api_calls':0,'source_writes':False,'network_calls':0}}
(OUT/'test-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps(result,ensure_ascii=False))
