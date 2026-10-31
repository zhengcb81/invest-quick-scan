from pathlib import Path
import sys,os,subprocess,hashlib,json,uuid,shutil,time
from datetime import datetime,timezone
root=Path.cwd();out=root/'runs/close-support31/wiring-independent';tmp=root/('.w31last-'+uuid.uuid4().hex[:8]);tmp.mkdir()
ui=root.parent/'iqs-question-bank-ui-lab'
env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA'}}
env['PATH']=str(root.parent.parent/'nodejs')+os.pathsep+env['PATH'];env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TEMP=str(tmp),TMP=str(tmp),PYTHONPATH=os.pathsep.join([str(root/'scripts'),str(root.parent/'StockWiki')]))
commands=[([sys.executable,'-B','-m','pytest','tests/test_dashboard_entity_view_http.py','-q','-p','no:cacheprovider','--basetemp',str(tmp/'native')],root),([sys.executable,'-B','-m','pytest','tests/test_result_trust_host.py','tests/test_product_ui.py','-k','actual_host_contracts or result_trust_mount_original_callback_and_foreign_row_isolation or foreign_envelope_summary_is_diagnostic_only','-q','-p','no:cacheprovider','--basetemp',str(tmp/'ui')],ui)]
commands=commands[:1]
checks=[]
try:
 for i,(argv,cwd) in enumerate(commands):
  start=time.perf_counter();utc=datetime.now(timezone.utc).isoformat();p=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,timeout=120);log=out/f'final-http-{i}.log';log.write_bytes(p.stdout+p.stderr)
  checks.append({'argv':argv,'cwd':str(cwd),'started_at_utc':utc,'exit_code':p.returncode,'wall_seconds':time.perf_counter()-start,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'output_tail':log.read_text(encoding='utf8',errors='replace')[-1100:]})
finally:
 if tmp.resolve().parent!=root.resolve() or not tmp.name.startswith('.w31last-'):raise ValueError('cleanup scope')
 shutil.rmtree(tmp)
result={'iqs_C':'c1ee64fd5a7cd1331e67d7ec7f3a242ff2ffc0b2','ui_C':'03d6b9aa3d45011f09bc77ef69e62b4a1d21e00e','checks':checks,'cleanup':{'temporary_root_absent':not tmp.exists(),'original_source_written':False,'production_databases_touched':False,'service_mutation':False,'paid_api_calls':0}}
(out/'final-http-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=True))
