from pathlib import Path
import os,json,subprocess,sys,uuid,shutil,hashlib,time
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];SNAP=OUT/'snapshot'
env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA'}}
env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
tmp=ROOT/('.p31seam-'+uuid.uuid4().hex[:6]);tmp.mkdir(exist_ok=False)
env.update(TEMP=str(tmp),TMP=str(tmp),PYTHONPATH=str(SNAP/'src'))
if sys.argv[1:]==['units']:
 cmd=[sys.executable,'-B','-m','pytest','tests/unit/test_native_delegation_faults.py','tests/unit/test_publisher_authority_boundary.py','-q','-p','no:cacheprovider','--override-ini','addopts=','--basetemp',str(tmp/'pytest')];name='units-elevated'
else:
 cmd=[sys.executable,'-B','-m','pytest',str(OUT/'test_service_preflight.py'),'-q','-s','-p','no:cacheprovider','--override-ini','addopts=','--basetemp',str(tmp/'pytest')];name='seam-red'
start=datetime.now(timezone.utc).isoformat();clock=time.perf_counter()
try:
 p=subprocess.run(cmd,cwd=SNAP,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
 log=(p.stdout+p.stderr).encode('utf-8');(OUT/(name+'.log')).write_bytes(log)
finally:
 if tmp.resolve().parent!=ROOT.resolve() or not tmp.name.startswith('.p31seam-'):raise ValueError('cleanup boundary')
 shutil.rmtree(tmp)
d={'argv':cmd,'cwd':str(SNAP),'utc':start,'exit_code':p.returncode,'seconds':time.perf_counter()-clock,'log_sha256':hashlib.sha256(log).hexdigest(),'temporary_root':str(tmp),'temporary_removed':not tmp.exists(),'paid_api_calls':0,'network_calls':0,'production_writes':False}
(OUT/(name+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(p.stdout[-6000:])
