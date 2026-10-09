"""Resume the exact IQS selection after a transient foreign index-lock refusal."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import publish_iqs as original

ROOT, OUT, REVIEW = original.ROOT, original.OUT, original.REVIEW


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    number = '02' if sys.argv[1:] == ['--after-diff-check'] else '01'
    assert sys.argv[1:] in ([], ['--after-diff-check'])
    e = {k:v for k,v in os.environ.items() if k.upper() in {
         'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    e.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=ROOT,env=e)
    target = OUT/'iqs-publication'
    before = json.loads((target/'selected-before.json').read_bytes())
    assert git('rev-parse','HEAD').decode().strip()==before['base']==original.BASE
    assert not (ROOT/'runs/w15a').exists() and not (ROOT/'.git/index.lock').exists()
    assert json.loads((OUT/'cleanup-receipt.json').read_text('utf-8-sig'))['applied']
    assert json.loads((OUT/'source-publication/result.json').read_bytes())['source_published']
    previous = before['selected']
    # Original archived inputs/outputs remain immutable; only root PWF gains facts.
    assert all(sha((ROOT/name).read_bytes())==h for name,h in previous.items() if name not in original.PWF)
    expected_names=set(previous)|{(target/'selected-before.json').relative_to(ROOT).as_posix(),
                                  Path(__file__).relative_to(ROOT).as_posix()}
    if number == '02':
        failed=json.loads((target/'diff-check.process.json').read_bytes())
        assert failed['returncode']==2 and failed['terminal_confirmed']
        expected_names |= {(target/name).relative_to(ROOT).as_posix() for name in
                           ('resume-selection-01.json','diff-check.process.json','diff-check.stdout.log','diff-check.stderr.log')}
    for entry in filter(None,git('status','--porcelain=v1','-uall','-z').decode().split('\0')):
        assert entry[3:] in expected_names|{'opencode.json'},entry
    staged=set(filter(None,git('diff','--cached','--name-only','-z').decode().split('\0')))
    assert staged <= expected_names
    assert not (target/f'resume-selection-{number}.json').exists()
    expected={name:sha((ROOT/name).read_bytes()) for name in sorted(expected_names)}
    selection=target/f'resume-selection-{number}.json'
    selection.write_text(json.dumps(dict(base=before['base'],previous_selection_sha256=sha((target/'selected-before.json').read_bytes()),
                  selected=expected,partial_staged_paths=len(staged),foreign_lock_deleted=False,
                  original_frozen_non_PWF_files_unchanged=True,preserved_unknown='opencode.json not read'),indent=2)+'\n','utf-8')
    expected[selection.relative_to(ROOT).as_posix()]=sha(selection.read_bytes())
    paths=sorted(expected)
    for offset in range(0,len(paths),75):
        # Exact verified paths only; -f is solely for the existing ignored logs.
        batch=paths[offset:offset+75]
        for attempt in range(3):
            p=subprocess.run(['git','add','-f','--',*batch],cwd=ROOT,env=e,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            if p.returncode==0:
                break
            if p.returncode!=128 or b'index.lock' not in p.stderr or attempt==2:
                raise RuntimeError('exact stage failed: '+p.stderr.decode(errors='replace'))
            time.sleep(1)
            assert git('rev-parse','HEAD').decode().strip()==before['base']
            assert set(filter(None,git('diff','--cached','--name-only','-z').decode().split('\0'))) <= set(paths)
            assert all(sha((ROOT/name).read_bytes())==h for name,h in expected.items())
        else:
            raise RuntimeError('bounded exact stage retries exhausted')
    assert set(filter(None,git('diff','--cached','--name-only','-z').decode().split('\0')))==set(paths)
    oids={}
    for entry in filter(None,git('ls-files','--stage','-z').decode().split('\0')):
        meta,name=entry.split('\t',1)
        if name in expected:
            _,oid,stage=meta.split()
            assert stage=='0'
            oids[name]=oid
    p=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,env=e,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    data,error=p.communicate(('\n'.join(oids[n] for n in paths)+'\n').encode(),timeout=120)
    assert p.returncode==0,error
    cursor=0
    for name in paths:
        end=data.index(b'\n',cursor)
        oid,kind,size=data[cursor:end].decode().split()
        cursor=end+1
        blob=data[cursor:cursor+int(size)]
        raw=(ROOT/name).read_bytes()
        assert oid==oids[name] and kind=='blob' and sha(raw)==expected[name]
        assert blob==raw or (name in original.PWF+original.PUBLIC and blob==raw.replace(b'\r\n',b'\n')),name
        cursor+=int(size)+1
    assert cursor==len(data)
    def recorded(label,args):
        assert not (target/(label+'.process.json')).exists()
        started=time.monotonic()
        p=subprocess.Popen(['git',*args],cwd=ROOT,env=e,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        print(json.dumps(dict(label=label,pid=p.pid)),flush=True)
        stdout,stderr=p.communicate(timeout=600)
        (target/(label+'.stdout.log')).write_bytes(stdout)
        (target/(label+'.stderr.log')).write_bytes(stderr)
        (target/(label+'.process.json')).write_text(json.dumps(dict(pid=p.pid,returncode=p.returncode,terminal_confirmed=True,
              wall_s=round(time.monotonic()-started,3),normal_hooks=True,stdout_sha256=sha(stdout),stderr_sha256=sha(stderr)),indent=2)+'\n','utf-8')
        print((stdout+stderr).decode(errors='replace')[-1600:])
        assert p.returncode==0
    recorded('diff-check' if number=='01' else 'diff-check-resume-02',['diff','--cached','--check'])
    recorded('commit',['commit','-m','Deliver modular quick scan refresh foundation and reviewed cross-repo handoff'])
    commit=git('rev-parse','HEAD').decode().strip()
    assert set(filter(None,git('diff-tree','--no-commit-id','--name-only','-r','-z',commit).decode().split('\0')))==set(paths)
    recorded('push',['push','origin','master'])
    remote=git('ls-remote','origin','refs/heads/master').decode().split()[0]
    assert remote==commit
    (target/'result.json').write_text(json.dumps(dict(commit=commit,remote_head=remote,selected_paths=len(paths),
             normal_hooks=True,force_push=False,foreign_lock_deleted=False,preserved_unknown='opencode.json',
             artifact_staged_bytes_identical=True,whole_W15_complete=False),indent=2)+'\n','utf-8')
    print(json.dumps(dict(commit=commit,remote_head=remote,selected_paths=len(paths))))


if __name__=='__main__':
    main()
