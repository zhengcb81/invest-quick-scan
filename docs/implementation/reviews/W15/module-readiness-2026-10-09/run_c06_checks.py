"""Bounded, credential-free C06 private checks, preserving exact execution bytes."""
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


def main():
    label=sys.argv[1]
    assert re.fullmatch(r'contract-[a-z][a-z0-9-]{1,60}',label)
    assert OWN.is_dir() and OWN.resolve().is_relative_to(ROOT/'runs')
    assert not (OUT/(label+'.process.json')).exists()
    frozen=json.loads((OUT/'inputs-01.json').read_bytes())
    for row in frozen['IQS_nonsecret_inputs']:
        assert sha((OWN/'iqs'/row['path']).read_bytes())==row['execution_sha256']
    guard=OWN/'guard/sitecustomize.py'
    guard_raw=guard.read_bytes()
    # prepare's string digest is LF-content; Windows write_text uses CRLF.
    assert sha(guard_raw.replace(b'\r\n',b'\n'))==frozen['guard_sha256']
    domains=dict(content_LF_sha256=frozen['guard_sha256'],raw_execution_sha256=sha(guard_raw),
                 normalization_scope='Only CRLF serialization of the same guard code')
    domain_path=OUT/'guard-byte-domains-01.json'
    if domain_path.exists():
        assert json.loads(domain_path.read_bytes())==domains
    else:
        domain_path.write_text(json.dumps(domains,indent=2)+'\n','utf-8')
    sources={str(p.relative_to(OWN/'iqs')):sha(p.read_bytes()) for p in (OWN/'iqs').rglob('*') if p.is_file()}
    (OUT/(label+'.sources.json')).write_text(json.dumps(sources,indent=2)+'\n','utf-8')
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        IQS_C06_OWN=str(OWN),PYTHONPATH=os.pathsep.join((str(OWN/'guard'),str(OWN/'iqs/scripts'))),
        TEMP=str(OWN/'tmp'),TMP=str(OWN/'tmp'),TMPDIR=str(OWN/'tmp'))
    command=[sys.executable,'-B','-X','utf8','-m','pytest','-c',str(OWN/'pytest.ini'),'-q',
             '--basetemp='+str(OWN/label),'--junitxml='+str(OUT/(label+'.junit.xml')),
             'tests/test_query_contract_v2.py']
    started=time.monotonic()
    p=subprocess.Popen(command,cwd=OWN/'iqs',env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print(json.dumps(dict(label=label,pid=p.pid)),flush=True)
    stdout,stderr=p.communicate(timeout=180)
    (OUT/(label+'.stdout.log')).write_bytes(stdout)
    (OUT/(label+'.stderr.log')).write_bytes(stderr)
    after={str(p.relative_to(OWN/'iqs')):sha(p.read_bytes()) for p in (OWN/'iqs').rglob('*') if p.is_file()}
    assert sources==after,'Executed source drift'
    result=dict(label=label,pid=p.pid,returncode=p.returncode,terminal_confirmed=True,
                wall_s=round(time.monotonic()-started,3),command=command,source_unchanged=True,
                sources_sha256=sha((OUT/(label+'.sources.json')).read_bytes()),
                stdout_sha256=sha(stdout),stderr_sha256=sha(stderr),
                actual_guard_raw_sha256=domains['raw_execution_sha256'],
                source_written=False,API_requests=0,real_company_golden=False)
    (OUT/(label+'.process.json')).write_text(json.dumps(result,indent=2)+'\n','utf-8')
    print((stdout+stderr).decode(errors='replace')[-2400:])
    print(json.dumps(result))


if __name__=='__main__':
    main()
