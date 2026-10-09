"""Guarded current SW static checks; no real workspace scans or pytest."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time
from ruff import find_ruff_bin

IQS=Path(__file__).resolve().parents[5]
OWN=IQS/"runs/r13a"
OUT=IQS/"docs/implementation/intake/G3/2026-10-09-jr13"

def main():
    label=sys.argv[1]
    dest=OUT/label
    assert not dest.exists()
    dest.mkdir()
    env={k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env.update(E97_OWNED_ROOT=str(OWN),PYTHONPATH=str(OWN/"guard"),PYTHONDONTWRITEBYTECODE="1",PYTHONUTF8="1",TEMP=str(OWN/"tmp"),TMP=str(OWN/"tmp"),TMPDIR=str(OWN/"tmp"),STOCKWIKI_PROJECT_PARENT=str(OWN))
    # Ruff is a native Rust read-only tool, not a Python child. Run it explicitly
    # with stripped credentials; do not weaken the inherited Python audit guard.
    files=["stockwiki/quick_scan_import.py","stockwiki/quick_scan_observations.py","stockwiki/quick_scan_backup_manifest.py","tests/test_quick_scan_observations.py","tests/test_quick_scan_delivery.py"]
    commands=([[find_ruff_bin(),"check","--fix","--no-cache",*files],[find_ruff_bin(),"format","--no-cache",*files]] if len(sys.argv)>2 and sys.argv[2]=="format" else
        [[find_ruff_bin(),"check","--no-cache","stockwiki","tests","scripts"],[sys.executable,"-B","-X","utf8","-m","stockwiki.cli","--root",str(OWN/"sw"),"validate-framework","--static"]])
    rows=[]
    for index,command in enumerate(commands):
        step_env=dict(env)
        if index==0 or len(sys.argv)>2:
            step_env.pop("PYTHONPATH",None)
        else:
            step_env["PYTHONPATH"]=os.pathsep.join([str(OWN/"guard"),str(OWN/"sw")])
        started=time.monotonic()
        proc=subprocess.run(command,cwd=OWN/"sw",env=step_env,capture_output=True,timeout=120)
        (dest/(str(index)+".stdout.log")).write_bytes(proc.stdout)
        (dest/(str(index)+".stderr.log")).write_bytes(proc.stderr)
        rows.append({"argv":command,"returncode":proc.returncode,"wall_s":round(time.monotonic()-started,3),"Python_guard":index==1 and len(sys.argv)==2,"real_API_calls":0})
        print(proc.stdout.decode("utf-8")[-3000:]);print(proc.stderr.decode("utf-8")[-1000:])
    (dest/"process.json").write_text(json.dumps(rows,indent=2)+"\n",encoding="utf-8")
    sys.exit(0 if all(row["returncode"]==0 for row in rows) else 1)

if __name__=='__main__':main()
