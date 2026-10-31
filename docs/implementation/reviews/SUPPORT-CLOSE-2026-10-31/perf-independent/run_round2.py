from pathlib import Path
import os,subprocess,json,shutil,sys,hashlib,uuid,time
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
SRC=ROOT/'runs/close-support31/perf/work';DST=OUT/'round2-snapshot'
if DST.exists():raise SystemExit('independent round2 copy exists')
DST.mkdir()
for name in ['src','tests','tools','vendor_upstream','integration']:
 shutil.copytree(SRC/name,DST/name,ignore=shutil.ignore_patterns('.git','.tmp','__pycache__','.pytest_cache'))
for name in ['pyproject.toml','conftest.py']:
 if (SRC/name).exists():shutil.copyfile(SRC/name,DST/name)
env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA'}}
env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
subprocess.run(['git','-C',str(DST),'init','--quiet'],env=env,check=True,capture_output=True)
tmp=ROOT/('.p31r2-'+uuid.uuid4().hex[:7]);tmp.mkdir(exist_ok=False);env.update(TEMP=str(tmp),TMP=str(tmp),PYTHONPATH=str(DST/'src'))
files=['tests/integration/test_service_preflight.py','tests/unit/test_native_delegation_faults.py','tests/unit/test_publisher_authority_boundary.py']
cmd=[sys.executable,'-B','-m','pytest',*files,'-q','-p','no:cacheprovider','--override-ini','addopts=','--basetemp',str(tmp/'pytest')]
start=datetime.now(timezone.utc).isoformat();clock=time.perf_counter()
try:
 p=subprocess.run(cmd,cwd=DST,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
 (OUT/'round2-tests.log').write_text(p.stdout+p.stderr,encoding='utf-8',newline='\n')
finally:
 if tmp.resolve().parent!=ROOT.resolve() or not tmp.name.startswith('.p31r2-'):raise ValueError('cleanup boundary')
 shutil.rmtree(tmp)
pins=[]
for rel in files+['integration/candidate.patch']:
 b=(DST/rel).read_bytes();pins.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
d={'argv':cmd,'cwd':str(DST),'utc':start,'elapsed_seconds':time.perf_counter()-clock,'exit_code':p.returncode,'output':p.stdout,'log_sha256':hashlib.sha256((OUT/'round2-tests.log').read_bytes()).hexdigest(),'pins':pins,'cleanup':{'temporary_root':str(tmp),'removed':not tmp.exists(),'production_writes':False,'paid_api_calls':0,'network_calls':0}}
(OUT/'round2-tests.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'exit':p.returncode,'output':p.stdout[-1800:]},ensure_ascii=False))
