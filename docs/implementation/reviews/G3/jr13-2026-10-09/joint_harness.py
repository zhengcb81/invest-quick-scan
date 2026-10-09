"""Current-boundary test controller, no new production client or owner golden."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

OWN = Path(os.environ["E97_OWNED_ROOT"]).resolve()
IQS = OWN.parents[1]
TAG = os.environ["JR13_JOINT_TAG"]
CASES = OWN / "cases" / TAG
OUT = OWN / "logs" / TAG

def save(path,value):
    assert path.resolve().is_relative_to(OWN.resolve()) and not path.exists()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def env(owner):
    value={k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    value.update(PYTHONPATH=os.pathsep.join([str(OWN/"guard"),str(OWN/owner),str(OWN/owner/"src")]),
        E97_OWNED_ROOT=str(OWN),TEMP=str(OWN/"tmp"),TMP=str(OWN/"tmp"),TMPDIR=str(OWN/"tmp"),
        PYTHONDONTWRITEBYTECODE="1",PYTHONUTF8="1",PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",STOCKQA_RUN_LIVE_E2E="0",STOCKWIKI_PROJECT_PARENT=str(OWN))
    return value

def actor(owner,label,request,timeout=270,expected_code=0):
    req,result=CASES/(label+".request.json"),CASES/(label+".response.json")
    assert not result.exists()
    save(req,request)
    command=[sys.executable,"-B","-X","utf8",str(OWN/(owner+"_actor.py")),str(req),str(result)]
    started=time.monotonic()
    proc=subprocess.Popen(command,cwd=OWN/owner,env=env(owner),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        stdout,stderr=proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout,stderr=proc.communicate()
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/(label+".stdout.log")).write_bytes(stdout)
        (OUT/(label+".stderr.log")).write_bytes(stderr)
        save(OUT/(label+".process.json"),{"argv":command,"pid":proc.pid,"returncode":proc.returncode,"timed_out":True})
        raise
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(label+".stdout.log")).write_bytes(stdout)
    (OUT/(label+".stderr.log")).write_bytes(stderr)
    save(OUT/(label+".process.json"),{"argv":command,"cwd":str(OWN/owner),"pid":proc.pid,"returncode":proc.returncode,"timed_out":False,
        "wall_s":round(time.monotonic()-started,3),"stdout_sha256":hashlib.sha256(stdout).hexdigest(),"stderr_sha256":hashlib.sha256(stderr).hexdigest()})
    if result.exists():(OUT/(label+".response.json")).write_bytes(result.read_bytes())
    assert proc.returncode==expected_code, label+": actor failed; preserved stderr"
    return json.loads(result.read_bytes()) if result.exists() else {"process_exit":proc.returncode,"stderr":stderr.decode("utf-8")}
