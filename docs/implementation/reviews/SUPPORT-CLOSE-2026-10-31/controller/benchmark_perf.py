"""One bounded offline matrix after final related tests, short owned workspace."""
import os,sys,json,time,shutil,subprocess,hashlib,uuid
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'perf';W=OUT/'work'
deadline=time.monotonic()+1000
while True:
 evidence=json.loads((OUT/'tests.json').read_bytes())
 if 'tests' in evidence['argv']:
  if evidence['exit_code']!=0:raise SystemExit('final related suite failed; matrix not started')
  break
 if time.monotonic()>deadline:raise SystemExit('related-suite completion not observed; no matrix')
 time.sleep(3)
short=ROOT/('.c31bench-'+uuid.uuid4().hex[:6]);short.mkdir(exist_ok=False)
env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA'}}
env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0',TEMP=str(short),TMP=str(short))
cmd=None;started=datetime.now(timezone.utc).isoformat();p=None;log=b''
try:
 for item in W.iterdir():
  if item.name in {'.git','.tmp','__pycache__','.pytest_cache'}:continue
  if item.is_symlink():raise ValueError('unexpected symlink')
  dst=short/item.name
  if item.is_dir():shutil.copytree(item,dst)
  else:shutil.copyfile(item,dst)
 subprocess.run(['git','-C',str(short),'init','--quiet'],env=env,check=True,capture_output=True)
 (short/'.tmp').mkdir(exist_ok=True)
 # Generate the manifest on the exact byte form used by this matrix.
 prep=subprocess.run([sys.executable,'-B',str(short/'tools/build_candidate_source_manifest.py')],cwd=short,env=env,capture_output=True,timeout=180)
 if prep.returncode:raise RuntimeError('candidate manifest failed: '+prep.stderr.decode('utf-8','replace'))
 cmd=[sys.executable,'-B',str(short/'bench/run_benchmark.py'),'--bench-id','close31-fresh-preflight','--packets','1','3','33','36','--reps','3','--variants','baseline','candidate']
 p=subprocess.Popen(cmd,cwd=short,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (OUT/'benchmark-active.json').write_text(json.dumps({'pid':p.pid,'argv':cmd,'cwd':str(short),'started_at':started}),encoding='utf-8')
 try:stdout,stderr=p.communicate(timeout=2400)
 except subprocess.TimeoutExpired:
  # The live Popen handle is checked, never signal a retired/reused PID.
  if p.poll() is None:
   subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],env=env,capture_output=True)
  stdout,stderr=p.communicate(timeout=30)
  raise RuntimeError('matrix timed out; owned child tree terminated')
 log=stdout+stderr;(OUT/'benchmark.log').write_bytes(log)
 if p.returncode:raise RuntimeError('matrix failed: '+log.decode('utf-8','replace')[-1800:])
 bench=short/'bench'
 for name in ['benchmark-summary.json','raw-runs.json','candidate-source-manifest.json']:
  shutil.copyfile(bench/name,W/'bench'/name)
 summary=json.loads((bench/'benchmark-summary.json').read_bytes())
 semantic={'protocol':'iqs.import_perf.semantic_equivalence/1.0.0','input_lock_sha256':'d432ffce06bf5fc204a703f829f14a3e4de62f1d32957322981c6f13a1c367ab',
           'production_ready':False,'normal_matrix':summary['semantic_equivalence'],
           'fault_cases_ref':'tests/integration/test_native_fault_parity.py; test_service_preflight.py',
           'limits':['Native grant and publisher unit boundaries are explicitly synthetic; no full production public-CLI authority claim.']}
 (W/'bench/semantic-equivalence.json').write_text(json.dumps(semantic,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for item in (bench/'runs').glob('*close31-fresh-preflight*'):
  if item.is_file():shutil.copyfile(item,W/'bench/runs'/item.name)
 result={'argv':cmd,'cwd':str(short),'started_at':started,'completed_at':datetime.now(timezone.utc).isoformat(),'exit_code':p.returncode,'log_sha256':hashlib.sha256(log).hexdigest(),
         'summary_sha256':hashlib.sha256((W/'bench/benchmark-summary.json').read_bytes()).hexdigest(),'performance':summary['performance'],
         'conditions':'Same machine, serialized variants and fixed dataset. Other desktop activity is uncontrolled; descriptive wall ratios, no universal speedup claim.'}
 (OUT/'benchmark-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False))
finally:
 if p is not None and p.poll() is None:
  subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],env=env,capture_output=True)
 if short.resolve().parent!=ROOT.resolve() or not short.name.startswith('.c31bench-'):raise ValueError('cleanup boundary')
 from cleanup_benchmark_root import cleanup_owned
 cleanup_owned(short)
 (OUT/'benchmark-cleanup.json').write_text(json.dumps({'short_root':str(short),'removed':not short.exists(),'paid_calls':0,'production_db_writes':False}),encoding='utf-8')
