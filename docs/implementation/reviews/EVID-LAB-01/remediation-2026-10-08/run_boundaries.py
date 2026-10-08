"""Run only new focused acceptance cases; never repeats the completed 81-case suite."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

IQS=Path(__file__).resolve().parents[5]
OWN=IQS/'runs/evid-lab-remediation-2026-10-08-01'
LAB=OWN/'lab'
OUT=IQS/'docs/implementation/intake/EVID-LAB-01/2026-10-08-remediation/verification'
mode=sys.argv[1:]
assert mode in ([],['followup']), 'unknown case set'
followup=bool(mode)
case_name='followup_cases.py' if followup else 'boundary_cases.py'
log_name='review-followup' if followup else 'new-boundaries'
case_count=6 if followup else 5
cases=OWN/case_name
shutil.copyfile(Path(__file__).with_name(case_name),cases)
env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','PROGRAMDATA','SYSTEMDRIVE'}}
env.update(PYTHONPATH=os.pathsep.join([str(OWN/'guard'),str(LAB/'src')]),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',
    PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TEMP=str(OWN/'tmp'),TMP=str(OWN/'tmp'),TMPDIR=str(OWN/'tmp'),
    E97_OWNED_ROOT=str(OWN.resolve()),E97_LAB_ROOT=str(LAB),IQS_EVIDENCE_LAB_IQS_ROOT=str(IQS))
cmd=[sys.executable,'-B','-X','utf8','-m','pytest',str(cases),'-q','-o','addopts=','-p','no:cacheprovider']
start=time.monotonic()
p=subprocess.run(cmd,cwd=LAB,env=env,capture_output=True,timeout=300)
for kind,data in [('stdout',p.stdout),('stderr',p.stderr)]:
    (OUT/(log_name+'.'+kind+'.log')).write_bytes(data)
records=OUT.parent/'counterexamples'
records.mkdir(exist_ok=True)
for source in (LAB/('.controller-followup' if followup else '.controller-extra')).glob('*.json'):
    (records/source.name).write_bytes(source.read_bytes())
(OUT/(log_name+'.json')).write_text(json.dumps({'command':cmd,'exit_code':p.returncode,'wall_s':round(time.monotonic()-start,3),
    'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest(),
    'cases':case_count,'kind':'focused_new_boundaries_not_a_repeated_full_suite'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(p.stdout.decode('utf-8'),end='')
print(json.dumps({'exit_code':p.returncode,'wall_s':round(time.monotonic()-start,3),'cases':case_count}))
