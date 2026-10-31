import os,sys,json,subprocess,io,tarfile,hashlib,shutil,time,uuid
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent;SRC=ROOT.parent/'iqs-answer-audit-lab'
C='6890d1645a1a851d0af915ec3e6ab0554d954f62';EXPECTED='2fa3b04ebd6c7180e2b5a77aee7195da76a977c34b1b51e78098bf8f47cc126a'
ENV={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE','PROGRAMFILES','PROGRAMFILES(X86)'}}
ENV.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
def git(*args):return subprocess.check_output(['git','-C',str(SRC),*args],env=ENV)
def sha(data):return hashlib.sha256(data).hexdigest()
OUT.mkdir(parents=True,exist_ok=True);snap=OUT/'snapshot'
if not snap.exists():
 snap.mkdir()
 with tarfile.open(fileobj=io.BytesIO(git('archive',C))) as tf:
  for m in tf.getmembers():
   if not (snap/m.name).resolve().is_relative_to(snap.resolve()) or m.issym() or m.islnk():raise ValueError('unsafe archive')
  tf.extractall(snap,filter='data')
raw=git('show',C+':docs/payload-manifest.json');assert sha(raw)==EXPECTED
manifest=json.loads(raw);entries=manifest.get('artifacts',manifest.get('files'));hashes=[]
for row in entries:
 blob=git('show',C+':'+row['path']);match=sha(blob)==row['sha256'] and len(blob)==row['bytes']
 hashes.append({'path':row['path'],'matches':match})
assert all(x['matches'] for x in hashes)
private=ROOT/'runs/package-inputs-2026-10-30-mainline-next/live-answers-32.json'
private_sha=sha(private.read_bytes());assert private_sha=='5342c92a5a5ad6a85c4fe030190969578af30c44eaa36e159d9966f01e3937ee'
(snap/'.private-inputs').mkdir(exist_ok=True);shutil.copyfile(private,snap/'.private-inputs/live-answers-32.json')
tmp=ROOT/('.aa31-'+uuid.uuid4().hex[:8]);tmp.mkdir(exist_ok=False)
ENV.update(TEMP=str(tmp),TMP=str(tmp),PYTHONPATH=str(snap/'src')+os.pathsep+str(snap))
cmd=[sys.executable,'-B','-m','pytest','tests','-q','-p','no:cacheprovider','--override-ini','addopts=','--basetemp',str(tmp/'pytest')]
started=datetime.now(timezone.utc).isoformat();clock=time.perf_counter()
try:
 p=subprocess.run(cmd,cwd=snap,env=ENV,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=180)
 (OUT/'pytest.log').write_text(p.stdout+p.stderr,encoding='utf8')
 result={'payload_commit':C,'manifest_sha256':EXPECTED,'manifest_entries':hashes,'source_head_at_check':git('rev-parse','HEAD').decode().strip(),'source_tracked_status':git('status','--porcelain','--untracked-files=no').decode(),'private_input_sha256':private_sha,'argv':cmd,'cwd':str(snap),'utc':started,'duration_seconds':time.perf_counter()-clock,'exitcode':p.returncode,'log_sha256':sha((p.stdout+p.stderr).encode()),'output':p.stdout[-2500:]}
finally:
 if tmp.resolve().parent!=ROOT.resolve() or not tmp.name.startswith('.aa31-'):raise ValueError('cleanup boundary')
 shutil.rmtree(tmp)
 result_private=snap/'.private-inputs'
 if result_private.resolve().parent!=snap.resolve():raise ValueError('private cleanup boundary')
 shutil.rmtree(result_private)
result['cleanup']={'temporary_root':str(tmp),'temporary_absent':not tmp.exists(),'private_copy_absent':not (snap/'.private-inputs').exists(),'original_private_hash_unchanged':sha(private.read_bytes())==private_sha,'network_calls':0,'paid_api_calls':0}
(OUT/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
