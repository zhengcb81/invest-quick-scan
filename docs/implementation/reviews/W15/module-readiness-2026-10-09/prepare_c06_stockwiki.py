"""One-time nonsecret StockWiki source freeze under the existing owned C06 root."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[5]
SOURCE=ROOT.parent/'StockWiki'
OWN=ROOT/'runs/c15a'
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'
EXPECTED='a5a97d6efbf5f0ee79122a1ec375def388700690'


def main():
    target=OWN/'sw'
    output=OUT/'stockwiki-inputs-01.json'
    assert OWN.is_dir() and not target.exists() and not output.exists()
    env={k:v for k,v in os.environ.items() if k.upper() in {
        'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    env.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0')
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=SOURCE,env=env)
    assert git('rev-parse','HEAD').decode().strip()==EXPECTED
    status=git('status','--porcelain=v1','-uall')
    assert not status
    files=[n for n in git('ls-files','-z','--','stockwiki').decode('utf-8').split('\0')
           if n.endswith('.py')]
    rows=[]
    for name in files:
        raw=(SOURCE/name).read_bytes()
        path=target/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(raw)
        rows.append({'path':name,'bytes':len(raw),'execution_sha256':hashlib.sha256(raw).hexdigest()})
    (target/'tests').mkdir()
    assert git('rev-parse','HEAD').decode().strip()==EXPECTED and git('status','--porcelain=v1','-uall')==status
    for row in rows:
        assert hashlib.sha256((SOURCE/row['path']).read_bytes()).hexdigest()==row['execution_sha256']
    output.write_text(json.dumps({'head':EXPECTED,'original_source_status':'clean','files':rows,
        'source_written':False,'production_database_access':False,'API_requests':0,
        'owned_runtime_keep':str(OWN)},indent=2)+'\n','utf-8')
    print(json.dumps({'StockWiki_private_source_files':len(rows),'source_written':False,'production_database_access':False}))


if __name__=='__main__':
    main()
