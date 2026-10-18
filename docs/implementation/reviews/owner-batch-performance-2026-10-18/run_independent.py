from pathlib import Path
import hashlib,json,os,subprocess,sys
own=Path(__file__).resolve().parent
candidate=own.parent/'owner-batch-performance-candidate'
label=sys.argv[1]
assert label.isascii() and label.isalnum() and not (own/label).exists()
env={k:os.environ[k] for k in ('SystemRoot','SYSTEMROOT','WINDIR','PATH','PATHEXT') if k in os.environ}
env.update(PYTHONPATH=os.pathsep.join([str(own/'guard'),str(own.parents[3]/'StockQAbyLLM'),str(candidate/'qa/tests'),str(candidate/'qa/tests/unit')]),REVIEW_OWN=str(own),REVIEW_CANDIDATE=str(candidate),IQS_CONTINUATION_OWN=str(own),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TEMP=str(own/'temp'),TMP=str(own/'temp'))
cas=json.loads((candidate/'candidate-cas.json').read_text(encoding='utf-8'))
def pins():return {r['path']:hashlib.sha256(Path(r['candidate_path']).read_bytes()).hexdigest() for r in cas['source_paths']}
before=pins();assert all(before[r['path']]==r['candidate_sha256'] for r in cas['source_paths'])
result=subprocess.run([sys.executable,'-B','-m','pytest',str(own/'test_independent_batch.py'),'-q','--tb=short','-p','no:cacheprovider','--basetemp',str(own/label),'--junitxml',str(own/'evidence'/(label+'.xml'))],cwd=own,env=env,capture_output=True)
(own/'evidence'/(label+'.log')).write_bytes(result.stdout+result.stderr)
after=pins()
(own/'evidence'/(label+'-sourcepin.json')).write_text(json.dumps(dict(before=before,after=after,unchanged=before==after,returncode=result.returncode),indent=2),encoding='utf-8')
print((result.stdout+result.stderr).decode('utf-8',errors='replace'))
assert before==after
raise SystemExit(result.returncode)
