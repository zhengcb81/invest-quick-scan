"""Real Windows open-file handle and outside-root refusal; no source/work DB."""
from pathlib import Path
import sys,subprocess,json,uuid,hashlib
from datetime import datetime,timezone
from cleanup_benchmark_root import cleanup_owned,ROOT
OUT=Path(__file__).parent
foreign=ROOT/'task_plan.md';before=hashlib.sha256(foreign.read_bytes()).hexdigest()
try:cleanup_owned(foreign)
except ValueError:boundary=True
else:raise AssertionError('outside boundary accepted')
assert hashlib.sha256(foreign.read_bytes()).hexdigest()==before
owned=ROOT/('.c31bench-cleanup-'+uuid.uuid4().hex[:6]);owned.mkdir()
file=owned/'handle.txt';file.write_text('synthetic disposable file',encoding='utf-8')
code="import sys,time;f=open(sys.argv[1],'rb');print('opened',flush=True);time.sleep(1.5);f.close()"
p=subprocess.Popen([sys.executable,'-B','-c',code,str(file)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
try:
    assert p.stdout.readline().strip()=='opened'
    result=cleanup_owned(owned)
    p.communicate(timeout=10)
    assert result['removed'] and result['retries']>0
finally:
    if p.poll() is None:p.terminate();p.wait(timeout=5)
    if owned.exists():cleanup_owned(owned)
evidence={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'passed':2,'failed':0,
    'outside_root_rejected_unchanged':boundary,'actual_windows_open_handle_retry':result,
    'private_data':False,'paid_calls':0,'original_db_writes':False}
(OUT/'owned-cleanup-tests.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8');print(json.dumps(evidence))
