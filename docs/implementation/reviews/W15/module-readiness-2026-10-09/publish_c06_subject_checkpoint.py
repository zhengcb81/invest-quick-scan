"""Normal exact-path Git publication of private progress, no product release."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[5]
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'
CONTROL=Path(__file__).resolve().parent
BASE='e0e50cbce431b787056ae43e280e4ac5a9f687a2'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    checkpoint=json.loads((OUT/'subject-checkpoint-01.json').read_bytes())
    assert not checkpoint['source_published'] and not checkpoint['public_C06_validated']
    for row in checkpoint['source_candidates']:
        assert sha((OUT/row['snapshot_path']).read_bytes())==row['sha256']
    env={k:v for k,v in os.environ.items() if k.upper() in {
        'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    env.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
    def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,env=env)
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert not git('diff','--cached','--name-only')
    owned={'task_plan.md','progress.md','findings.md','docs/implementation/handoff-for-new-agent.md'}
    owned|={(CONTROL/name).relative_to(ROOT).as_posix() for name in (
        'subject-dispatch-interface.md','run_c06_owner_checks.py','freeze_c06_subject_input.py',
        'checkpoint_c06_subject.py','record_c06_subject_progress.py','publish_c06_subject_checkpoint.py')}
    prefix=OUT.relative_to(ROOT).as_posix()+'/'
    labels=('owner-subject-red-01',*(f'owner-subject-green-{n:02}' for n in range(1,6)),
        'owner-subject-projection-red-01','owner-subject-projection-green-01',
        'owner-subject-final-01','owner-history-regression-01','contract-subject-01')
    owned|={prefix+label+suffix for label in labels for suffix in (
        '.process.json','.sources.json','.stdout.log','.stderr.log','.junit.xml')}
    owned|={prefix+'subject-checkpoint-01.json',prefix+'subject-candidate-inputs-01.json',
        prefix+'destination-source-check-01.json',
        prefix+'private-subject-01/isolation-guard.py',
        prefix+'private-subject-01/StockWiki-original/stockwiki/quick_scan_observations.py'}
    owned|={prefix+row['snapshot_path'] for row in checkpoint['source_candidates']}
    selected=[]
    for entry in filter(None,git('status','--porcelain=v1','-uall','-z').decode('utf-8').split('\0')):
        name=entry[3:]
        if name in {'nul','opencode.json'}:
            assert entry[:2]=='??'
            continue
        assert name in owned,entry
        selected.append(name)
    assert set(selected)==owned
    selection=OUT/'git-selection-subject-01.json'
    assert not selection.exists()
    hashes={name:sha((ROOT/name).read_bytes()) for name in selected}
    selection.write_text(json.dumps({'base':BASE,'files':hashes,'private_checkpoint_only':True,
        'public_source_unchanged':True,'preserved_unknown_paths':['nul','opencode.json']},indent=2)+'\n','utf-8')
    selected.append(selection.relative_to(ROOT).as_posix())
    git('add','--',*selected)
    assert set(git('diff','--cached','--name-only').decode().splitlines())==set(selected)
    for name in selected:
        raw=(ROOT/name).read_bytes()
        staged=git('show',':'+name)
        assert staged==raw or (not name.startswith(prefix) and staged==raw.replace(b'\r\n',b'\n')),name
    git('diff','--cached','--check')
    publication=OUT/'iqs-subject-publication'
    assert not publication.exists()
    publication.mkdir()
    def invoke(label,*args):
        start=time.monotonic()
        process=subprocess.Popen(['git',*args],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        print(json.dumps({'label':label,'pid':process.pid}),flush=True)
        stdout,stderr=process.communicate()
        (publication/(label+'.stdout.log')).write_bytes(stdout)
        (publication/(label+'.stderr.log')).write_bytes(stderr)
        result={'label':label,'pid':process.pid,'returncode':process.returncode,'terminal_confirmed':True,
            'wall_s':round(time.monotonic()-start,3),'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr)}
        (publication/(label+'.process.json')).write_text(json.dumps(result,indent=2)+'\n','utf-8')
        print((stdout+stderr).decode(errors='replace')[-900:],flush=True)
        assert process.returncode==0,result
    invoke('commit','commit','-m','Checkpoint two-phase subject dispatch and atomic owner binding')
    current=git('rev-parse','HEAD').decode().strip()
    invoke('push','push','origin','master')
    remote=git('ls-remote','origin','refs/heads/master').decode().split()[0]
    assert remote==current
    result={'commit':current,'remote_head':remote,'selected_paths':len(selected),
        'raw_evidence_staged_identical':True,'private_checkpoint_only':True,'public_source_unchanged':True,
        'owned_runtime_keep':'runs/c15a','preserved_unknown_paths':['nul','opencode.json']}
    (publication/'result.json').write_text(json.dumps(result,indent=2)+'\n','utf-8')
    print(json.dumps(result),flush=True)


if __name__=='__main__': main()
