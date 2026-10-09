"""New, exclusively owned C06 runtime; preserve delivered W15 snapshots."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

import run_checks

ROOT=Path(__file__).resolve().parents[5]
OWN=ROOT/'runs/c15a'
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    assert not OWN.exists() and not OUT.exists()
    assert not (ROOT/'runs/w15a').exists()
    e={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    e.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1')
    def git(repo,*args):
        return subprocess.check_output(['git',*args],cwd=repo,env=e)
    states={}
    for name in ('invest-quick-scan','StockWiki','StockQAbyLLM'):
        repo=ROOT.parent/name
        states[name]=dict(head=git(repo,'rev-parse','HEAD').decode().strip(),
                         branch=git(repo,'branch','--show-current').decode().strip(),
                         status=git(repo,'status','--porcelain=v1','-uall').decode().replace('\r\n','\n'))
    assert states['invest-quick-scan']['head']=='bc9ab49e5fd015c51cdc4d586d9398be6963cd7c'
    assert states['StockWiki']['head']=='a5a97d6efbf5f0ee79122a1ec375def388700690'
    assert states['StockQAbyLLM']['head']=='6aafc32eae5339668e893b8a2b246d0655075584'
    assert states['StockWiki']['status']==''
    # This newly created controller is the only IQS addition, besides old unknown.
    assert set(line[3:] for line in states['invest-quick-scan']['status'].splitlines()) == {
        'opencode.json',Path(__file__).relative_to(ROOT).as_posix()}
    names=git(ROOT,'ls-files','-z','--','scripts','schemas').decode().split('\0')
    names=sorted(n for n in names if n)
    OWN.mkdir(parents=True)
    OUT.mkdir(parents=True)
    for name in ('guard','tmp','iqs/scripts','iqs/tests'):
        (OWN/name).mkdir(parents=True,exist_ok=True)
    rows=[]
    for name in names:
        source=ROOT/name
        state=os.lstat(source)
        assert state.st_nlink==1 and not getattr(state,'st_file_attributes',0)&0x400
        raw=source.read_bytes()
        dest=OWN/'iqs'/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(raw)
        rows.append(dict(path=name,bytes=len(raw),execution_sha256=sha(raw)))
    guard=run_checks.GUARD.replace('IQS_W15_OWN','IQS_C06_OWN').replace('W15 offline:','C06 offline:')
    (OWN/'guard/sitecustomize.py').write_text(guard,'utf-8')
    (OWN/'pytest.ini').write_text('[pytest]\n','utf-8')
    (OUT/'inputs-01.json').write_text(json.dumps(dict(states=states,IQS_nonsecret_inputs=rows,
             guard_sha256=sha(guard.encode()),root=str(OWN),source_written=False,production_DB_access=0,
             API_requests=0,real_company_golden=False,authorization='全部后续所需的授权',
             schema_versions_unchanged=True),ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(dict(owned_root=str(OWN),frozen_files=len(rows),source_written=False,API_requests=0)))


if __name__=='__main__':
    main()
