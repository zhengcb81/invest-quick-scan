"""Correct controller argv/root only; preserve the first subprocess outputs."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

IQS=Path(__file__).resolve().parents[5]
OWN=IQS/'runs/sw-sr02-4b-2026-10-08-01'
OUT=IQS/'docs/implementation/intake/SW-REPAIR-02/2026-10-08-sr02-4b/verification'
safe={'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','LOCALAPPDATA','APPDATA',
    'PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA','SYSTEMDRIVE'}
env={key:value for key,value in os.environ.items() if key.upper() in safe}
env.update(TMP=str(OWN/'temp'),TEMP=str(OWN/'temp'),TMPDIR=str(OWN/'temp'),
    PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
command=[sys.executable,'-B','-X','utf8',str(Path(__file__).with_name('guarded_run.py')),'cli']
started=time.monotonic()
process=subprocess.run(command,cwd=IQS,env=env,capture_output=True,timeout=120)
for name,data in [('stdout',process.stdout),('stderr',process.stderr)]:
    (OUT/('cli-corrected.'+name+'.log')).write_bytes(data)
row=dict(name='cli-corrected',command=command,returncode=process.returncode,
    wall_s=round(time.monotonic()-started,3),stdout_sha256=hashlib.sha256(process.stdout).hexdigest(),
    stderr_sha256=hashlib.sha256(process.stderr).hexdigest(),
    controller_correction='verify requires --name; corrected from actual documented argv; new owned roots and unique log labels, old outputs retained')
(OUT/'cli-corrected.result.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(row))
