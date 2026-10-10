"""Publish only the private progress checkpoint using normal authorized Git."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[5]
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'
CONTROL=Path(__file__).resolve().parent
BASE='13d263ed85d1d7b0ba1caf0ce070d23a6d23605d'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    record=json.loads((OUT/'owner-reader-checkpoint-02.json').read_bytes())
    assert not record['source_published'] and not record['public_c06_envelope_validated']
    for row in record['source_candidates']:
        assert sha((OUT/row['snapshot_path']).read_bytes())==row['sha256']
    env={k:v for k,v in os.environ.items() if k.upper() in {
        'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    env.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=ROOT,env=env)
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert not git('diff','--cached','--name-only')
    owned={'task_plan.md','progress.md','findings.md','docs/implementation/handoff-for-new-agent.md'}
    owned|={(CONTROL/name).relative_to(ROOT).as_posix() for name in (
        'checkpoint_c06_history.py','publish_c06_history_checkpoint.py','query-projection-next.md')}
    prefix=OUT.relative_to(ROOT).as_posix()+'/'
    labels=('owner-history-red-01','owner-history-red-02','owner-history-green-01',
            'owner-history-fault-01','contract-snapshot-01')
    owned|={prefix+label+suffix for label in labels for suffix in (
        '.process.json','.sources.json','.stdout.log','.stderr.log','.junit.xml')}
    owned|={prefix+'owner-reader-checkpoint-02.json',prefix+'private-owner-reader-02/isolation-guard.py'}
    owned|={prefix+row['snapshot_path'] for row in record['source_candidates']}
    preserved={}
    selected=[]
    for row in filter(None,git('status','--porcelain=v1','-uall','-z').decode('utf-8').split('\0')):
        name=row[3:]
        if name in {'opencode.json','nul'}:
            assert row[:2]=='??'
            preserved[name]=row[:2]
            continue
        assert name in owned,row
        selected.append(name)
    assert set(selected)==owned
    selection=OUT/'git-selection-history-01.json'
    assert not selection.exists()
    hashes={name:sha((ROOT/name).read_bytes()) for name in selected}
    selection.write_text(json.dumps({'base':BASE,'files':hashes,'preserved_unknown_paths':preserved,
        'private_checkpoint_only':True,'public_source_changed':False},indent=2)+'\n','utf-8')
    selected.append(selection.relative_to(ROOT).as_posix())
    hashes[selected[-1]]=sha(selection.read_bytes())
    git('add','--',*selected)
    assert set(git('diff','--cached','--name-only').decode().splitlines())==set(selected)
    for name,expected in hashes.items():
        raw=(ROOT/name).read_bytes()
        assert sha(raw)==expected
        staged=git('show',':'+name)
        assert staged==raw or (name in owned and not name.startswith(prefix)
                              and staged==raw.replace(b'\r\n',b'\n')),name
    git('diff','--cached','--check')
    publication=OUT/'iqs-history-publication'
    assert not publication.exists()
    publication.mkdir()
    def invoke(label,*args):
        start=time.monotonic()
        process=subprocess.Popen(['git',*args],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        print(json.dumps({'label':label,'pid':process.pid}),flush=True)
        stdout,stderr=process.communicate()
        (publication/(label+'.stdout.log')).write_bytes(stdout)
        (publication/(label+'.stderr.log')).write_bytes(stderr)
        result={'label':label,'pid':process.pid,'returncode':process.returncode,
                'terminal_confirmed':True,'wall_s':round(time.monotonic()-start,3),
                'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr)}
        (publication/(label+'.process.json')).write_text(json.dumps(result,indent=2)+'\n','utf-8')
        print((stdout+stderr).decode(errors='replace')[-1600:],flush=True)
        assert process.returncode==0,result
    invoke('commit','commit','-m','Checkpoint owner original history and frozen query capture')
    current=git('rev-parse','HEAD').decode().strip()
    invoke('push','push','origin','master')
    remote=git('ls-remote','origin','refs/heads/master').decode().split()[0]
    assert remote==current
    remaining=git('status','--porcelain=v1','-uall').decode()
    result={'commit':current,'remote_head':remote,'selected_paths':len(selected),
            'private_checkpoint_only':True,'raw_evidence_staged_identical':True,
            'public_source_changed':False,'preserved_unknown_paths':preserved,
            'status_after':remaining,'owned_runtime_keep':'runs/c15a'}
    (publication/'result.json').write_text(json.dumps(result,indent=2)+'\n','utf-8')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    main()
