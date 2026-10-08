"""One concentrated offline regression and public replay batch in a frozen private Lab."""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / 'runs/evid-lab-lr02b-2026-10-08-01'
LAB = OWN / 'lab'
INTAKE = IQS / 'docs/implementation/intake/EVID-LAB-01/2026-10-08-lr02b'
OUT = INTAKE / 'verification'
OLD = IQS / 'docs/implementation/reviews/EVID-LAB-01'

def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(path.read_text('utf-8-sig'))
def save(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def inputs():
    lock=IQS/'docs/implementation/parallel-lanes/packages/2026-10-07-wave2/inputs.lock.json'
    body=read(lock)
    paths=[lock]
    for key in ('iqs_inputs','working_tree_snapshots'): paths += [IQS/x['path'] for x in body[key]]
    index=IQS/body['experiment_inputs']['index_path']
    paths += [index]+[IQS/x for x in read(index)['files']]
    return {p.relative_to(IQS).as_posix():sha(p.read_bytes()) for p in paths}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','PROGRAMDATA','SYSTEMDRIVE'}}
    env.update(PYTHONPATH=os.pathsep.join([str(OWN/'guard'),str(LAB/'src')]),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TEMP=str(OWN/'tmp'),TMP=str(OWN/'tmp'),TMPDIR=str(OWN/'tmp'),
        E97_OWNED_ROOT=str(OWN.resolve()),E97_LAB_ROOT=str(LAB),IQS_EVIDENCE_LAB_IQS_ROOT=str(IQS))
    (OUT/'sitecustomize-executed.py').write_bytes((OWN/'guard/sitecustomize.py').read_bytes())
    before=inputs()
    checks=[]
    def run(name,args):
        start=time.monotonic()
        try:
            p=subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=LAB,env=env,capture_output=True,timeout=180)
        except subprocess.TimeoutExpired as exc:
            p=subprocess.CompletedProcess(args,124,exc.stdout or b'',exc.stderr or b'')
        (OUT/(name+'.stdout.log')).write_bytes(p.stdout)
        (OUT/(name+'.stderr.log')).write_bytes(p.stderr)
        row={'name':name,'command':[sys.executable,'-B','-X','utf8',*args],'returncode':p.returncode,
             'wall_s':round(time.monotonic()-start,3),'stdout_sha256':sha(p.stdout),'stderr_sha256':sha(p.stderr)}
        checks.append(row)
        print(json.dumps({k:row[k] for k in ('name','returncode','wall_s')}),flush=True)
        return p
    canary = """import json, os, socket, subprocess, sys
from pathlib import Path
import sitecustomize
from iqs_evidence_lab import __version__, STRUCTURE_RULE_VERSION, SEMANTIC_RULE_VERSION, DIAGNOSTIC_SCHEMA_VERSION
owned=Path(os.environ['E97_OWNED_ROOT'])
def denied(fn):
    try: fn()
    except PermissionError: return
    raise AssertionError('controller isolation was not enforced')
assert not any(k.upper().endswith('_API_KEY') for k in os.environ)
for path in [owned.parent/'lr02b-must-not-write.txt']:
    assert not path.exists()
    denied(lambda: path.write_bytes(b'canary'))
denied(lambda: socket.create_connection(('127.0.0.1',9),timeout=1))
denied(lambda: subprocess.run(['cmd','/c','exit','0'],cwd=owned,env=dict(os.environ),capture_output=True))
print(json.dumps({'canaries':'passed','keys_provided':0,'cli':__version__,'structure_rules':STRUCTURE_RULE_VERSION,'semantic_rules':SEMANTIC_RULE_VERSION,'diagnostic_schema':DIAGNOSTIC_SCHEMA_VERSION}))
"""
    run('isolation-canaries',['-c',canary])
    run('worker-regression',['-m','pytest','tests/','-o','addopts=','-q','-p','no:cacheprovider'])
    catalog=run('public-fixtures',['-m','iqs_evidence_lab','validate-fixtures'])
    replays=[]
    for tag in ('a','b'):
        target=LAB/('.controller-replay-'+tag)
        p=run('public-index-'+tag,['-m','iqs_evidence_lab','replay','--input','index','--output',str(target)])
        replays.append(target if p.returncode==0 else None)
    stable=None
    if all(replays):
        names=['input-verification.json','metrics.json','recoverability.json','review-join.json','diagnostics.json']
        stable=all((replays[0]/n).read_bytes()==(replays[1]/n).read_bytes() for n in names)
        for name in names+['summary.json']:
            (OUT/('replay-'+name)).write_bytes((replays[0]/name).read_bytes())
    fixture_results=[]
    for fixture in sorted((LAB/'fixtures').rglob('FX-*.json')):
        fixture_id=fixture.stem
        target=LAB/('.controller-fixture-'+fixture_id)
        p=run('fixture-'+fixture_id,['-m','iqs_evidence_lab','replay','--input',str(fixture),'--output',str(target)])
        row={'fixture_id':fixture_id,'returncode':p.returncode}
        if p.returncode==0:
            body=read(target/'diagnostics.json')
            row.update(input_sha256=body['input']['input_sha256'],answer_sha256=body['input']['answer_sha256'],records=len(body['records']))
        fixture_results.append(row)
    run('public-handoff',[str(IQS/'scripts/parallel_handoff_cli.py'),'--catalog',
        str(IQS/'docs/implementation/parallel-lanes/packages/2026-10-07-wave2/manifest.json'),
        '--package-id','EVID-LAB-01','--input',str(INTAKE/'worker/handoff.json')])
    after=inputs()
    changed=[]
    for item in read(OWN/'snapshot.json'):
        data=(LAB/item['path']).read_bytes()
        if len(data)!=item['bytes'] or sha(data)!=item['sha256']: changed.append(item['path'])
    receipt_paths=list((LAB/'docs/handoff/EVID-LAB-01/logs/remaining-repairs-2026-10-08').glob('cleanup-receipt-p*.json'))
    snapshot_paths={x['path'] for x in read(OWN/'snapshot.json')}
    receipts=[]
    for receipt in receipt_paths:
        if receipt.relative_to(LAB).as_posix() not in snapshot_paths:
            data=read(receipt)
            (OUT/receipt.name).write_bytes(receipt.read_bytes())
            receipts.append(data)
    result={'schema':'iqs_evid_lab_lr02b_acceptance/1','status':'pending_review','checks':checks,
        'fixture_results':fixture_results,'replay_payloads_stable':stable,'input_files':len(before),
        'original_inputs_before':before,'original_inputs_after':after,'input_bytes_unchanged':before==after,
        'snapshot_files':len(read(OWN/'snapshot.json')),'snapshot_changed':changed,'generated_test_cleanup_receipts':receipts,
        'worker_repository_written':False,'paid_calls':0,'downloads':0,'keys_in_child_env':0,
        'guard':'inherited Python audit, no sockets or arbitrary non-Python child; private-root writes; not full OS read isolation',
        'cleanup_pending':True}
    save(OUT/'result.json',result)
    assert before==after and not changed, 'source/input drift'
    assert len(fixture_results)==34, 'missing fixture coverage'
    print(json.dumps({'checks':len(checks),'failed_commands':sum(c['returncode']!=0 for c in checks),
          'input_unique_files':len(before),'snapshot_unchanged':not changed,'stable':stable,'cleanup_pending':True}),flush=True)

if __name__=='__main__': main()
