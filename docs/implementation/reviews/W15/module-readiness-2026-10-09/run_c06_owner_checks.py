"""Bounded private owner tests under the original C06 guard and credential allowlist."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[5]
OWN=ROOT/'runs/c15a'
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def files(root):
    return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}


def main():
    label=sys.argv[1]
    assert re.fullmatch(r'owner-[a-z][a-z0-9-]{1,65}',label)
    assert not (OUT/(label+'.process.json')).exists()
    for row in json.loads((OUT/'stockwiki-inputs-01.json').read_bytes())['files']:
        assert sha((OWN/'sw'/row['path']).read_bytes())==row['execution_sha256']
    for row in json.loads((OUT/'inputs-01.json').read_bytes())['IQS_nonsecret_inputs']:
        assert sha((OWN/'iqs'/row['path']).read_bytes())==row['execution_sha256']
    domains=json.loads((OUT/'guard-byte-domains-01.json').read_bytes())
    assert sha((OWN/'guard/sitecustomize.py').read_bytes())==domains['raw_execution_sha256']
    before={'StockWiki':files(OWN/'sw'),'IQS':files(OWN/'iqs')}
    sources=OUT/(label+'.sources.json')
    sources.write_text(json.dumps(before,indent=2)+'\n','utf-8')
    env={k:v for k,v in os.environ.items() if k.upper() in {
        'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',IQS_C06_OWN=str(OWN),
        PYTHONPATH=os.pathsep.join((str(OWN/'guard'),str(OWN/'sw'),str(OWN/'iqs/scripts'))),
        TEMP=str(OWN/'tmp'),TMP=str(OWN/'tmp'),TMPDIR=str(OWN/'tmp'))
    command=[sys.executable,'-B','-X','utf8','-m','pytest','-c',str(OWN/'pytest.ini'),'-q',
        '--basetemp='+str(OWN/label),'--junitxml='+str(OUT/(label+'.junit.xml')),
        'tests/test_quick_scan_query_v2.py']
    start=time.monotonic()
    process=subprocess.Popen(command,cwd=OWN/'sw',env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print(json.dumps({'label':label,'pid':process.pid}),flush=True)
    stdout,stderr=process.communicate(timeout=180)
    (OUT/(label+'.stdout.log')).write_bytes(stdout)
    (OUT/(label+'.stderr.log')).write_bytes(stderr)
    assert before=={'StockWiki':files(OWN/'sw'),'IQS':files(OWN/'iqs')}
    result={'label':label,'pid':process.pid,'returncode':process.returncode,'terminal_confirmed':True,
        'wall_s':round(time.monotonic()-start,3),'command':command,'source_unchanged':True,
        'sources_sha256':sha(sources.read_bytes()),'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),
        'actual_guard_raw_sha256':domains['raw_execution_sha256'],'source_written':False,
        'API_requests':0,'real_company_golden':False}
    (OUT/(label+'.process.json')).write_text(json.dumps(result,indent=2)+'\n','utf-8')
    print((stdout+stderr).decode(errors='replace')[-2300:])
    print(json.dumps(result))


if __name__=='__main__':
    main()
