"""Offline acceptance orchestrator; source repositories remain read-only."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
RUN = ROOT/'runs/evid-lab-2026-10-08-01'
LAB = RUN/'lab'
OUT = ROOT/'docs/implementation/intake/EVID-LAB-01/2026-10-08/verification'
SOURCE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    lock = ROOT/'docs/implementation/parallel-lanes/packages/2026-10-07-wave2/inputs.lock.json'
    data = json.loads(lock.read_text('utf-8'))
    paths = [lock]
    for key in ['iqs_inputs','working_tree_snapshots']:
        paths += [ROOT/r['path'] for r in data[key]]
    idx = ROOT/data['experiment_inputs']['index_path']
    paths += [idx]
    paths += [ROOT/r for r in json.loads(idx.read_text('utf-8'))['files']]
    return {p.relative_to(ROOT).as_posix():digest(p) for p in paths}


def command(name, args, env, cwd=LAB):
    start=time.monotonic()
    proc=subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=cwd,env=env,capture_output=True,timeout=600)
    (OUT/(name+'.stdout.log')).write_bytes(proc.stdout)
    (OUT/(name+'.stderr.log')).write_bytes(proc.stderr)
    return dict(name=name,command=[sys.executable,'-B','-X','utf8',*args],returncode=proc.returncode,
        wall_s=round(time.monotonic()-start,3),stdout_sha256=hashlib.sha256(proc.stdout).hexdigest(),stderr_sha256=hashlib.sha256(proc.stderr).hexdigest())


def main():
    OUT.mkdir(parents=True,exist_ok=False)
    guard=RUN/'guard';guard.mkdir()
    shutil.copyfile(SOURCE/'lab_sitecustomize.py',guard/'sitecustomize.py')
    shutil.copyfile(SOURCE/'acceptance_cases.py',RUN/'acceptance_cases.py')
    tmp=RUN/'tmp';tmp.mkdir()
    env={k:os.environ[k] for k in ['SystemRoot','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','PROGRAMDATA','SYSTEMDRIVE'] if k in os.environ}
    env.update(PYTHONPATH=os.pathsep.join([str(guard),str(LAB/'src')]),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TEMP=str(tmp),TMP=str(tmp),TMPDIR=str(tmp),
        E97_OWNED_ROOT=str(RUN.resolve()),E97_LAB_ROOT=str(LAB),IQS_EVIDENCE_LAB_IQS_ROOT=str(ROOT))
    before=inputs()
    checks=[]
    checks.append(command('worker-regression',['-m','pytest','tests/','-o','addopts=','-q','-p','no:cacheprovider'],env))
    checks.append(command('public-fixtures',['-m','iqs_evidence_lab','validate-fixtures'],env))
    checks.append(command('public-replay',['-m','iqs_evidence_lab','replay','--input','index','--output',str(LAB/'.controller-public-replay')],env))
    checks.append(command('controller-counterexamples',[str(RUN/'acceptance_cases.py')],env))
    after=inputs()
    if before != after:
        raise ValueError('original input drift')
    replay=LAB/'.controller-public-replay'
    for name in ['summary.json','metrics.json','recoverability.json','review-join.json','input-verification.json']:
        if (replay/name).exists():shutil.copyfile(replay/name,OUT/('replay-'+name))
    source_snapshot=json.loads((RUN/'snapshot.json').read_text('utf-8'))
    (OUT/'source-snapshot.json').write_text(json.dumps(source_snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result=dict(schema='evid_lab_coordinator_acceptance/1',checks=checks,original_inputs_before=before,original_inputs_after=after,
        input_bytes_unchanged=True,child_environment_has_credentials=False,offline_guard='Python audit inherited by all Python descendants, owned-root writes only; no OS arbitrary-read proof',
        charged_calls=0,downloads=0,cleanup='pending exact file manifest/process check',worker_repository_written=False)
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'checks':[{k:v for k,v in c.items() if k in ['name','returncode','wall_s']} for c in checks],
        'input_unique_files':len(before),'unchanged':True,'cleanup':'pending'},ensure_ascii=False))


if __name__=='__main__':main()
