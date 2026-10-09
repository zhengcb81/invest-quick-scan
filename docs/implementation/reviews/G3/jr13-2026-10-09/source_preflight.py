"""Read-only external source drift evidence before exact scoped publication."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

IQS=Path(__file__).resolve().parents[5]
SW=IQS.parent/"StockWiki"
OUT=IQS/"docs/implementation/intake/G3/2026-10-09-jr13"
PATHS=["stockwiki/quick_scan_import.py","stockwiki/quick_scan_observations.py","stockwiki/quick_scan_backup_manifest.py","tests/test_quick_scan_observations.py","tests/test_quick_scan_delivery.py"]

def main():
    output=OUT/sys.argv[1]
    assert not output.exists()
    env={k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    env["GIT_OPTIONAL_LOCKS"]="0"
    def git(*args):return subprocess.check_output(["git",*args],cwd=SW,env=env)
    head=git("rev-parse","HEAD").decode().strip()
    assert head=="c40de21403720306ba21edbf71b9634a40ee58f8"
    status=git("status","--porcelain=v1").decode()
    assert not status.strip(),"Owner drift: must not publish over another process"
    rows=[]
    for name in PATHS:
        raw=git("show",head+":"+name)
        work=(SW/name).read_bytes()
        rows.append({"path":name,"Git_blob_sha256":hashlib.sha256(raw).hexdigest(),"worktree_sha256":hashlib.sha256(work).hexdigest(),"candidate_sha256":hashlib.sha256((IQS/"runs/r13a/sw"/name).read_bytes()).hexdigest()})
    assert git("rev-parse","HEAD").decode().strip()==head and git("status","--porcelain=v1").decode()==status
    output.write_text(json.dumps({"source_head":head,"branch":git("branch","--show-current").decode().strip(),"status":status,"paths":rows,"source_written":False},indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"source_head":head,"clean":True,"source_written":False}))

if __name__=='__main__':main()
