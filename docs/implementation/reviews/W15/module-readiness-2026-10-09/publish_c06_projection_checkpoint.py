"""Publish private progress/evidence only through normal Git; no source release."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[5]
OWN=ROOT/'runs/c15a'
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'
CONTROL=Path(__file__).resolve().parent
BASE='f87f9ec3a3eb68eca267b2c02eebc6cbb0594063'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    record=json.loads((OUT/'checkpoint-02.json').read_bytes())
    assert record['pytest_passed']==62 and not record['full_C06_validated']
    original=json.loads((OUT/'inputs-01.json').read_bytes())
    for row in original['IQS_nonsecret_inputs']:
        assert sha((ROOT/row['path']).read_bytes())==row['execution_sha256']
        assert sha((OWN/'iqs'/row['path']).read_bytes())==row['execution_sha256']
    for row in record['snapshot']:
        assert sha((OUT/'private-source-02'/row['path']).read_bytes())==row['execution_sha256']
        assert sha((OWN/'iqs'/row['path']).read_bytes())==row['execution_sha256']
    env={k:v for k,v in os.environ.items() if k.upper() in {
        'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    env.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=ROOT,env=env)
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert not git('diff','--cached','--name-only')
    allowed={'task_plan.md','progress.md','findings.md','docs/implementation/handoff-for-new-agent.md'}
    allowed|={(CONTROL/name).relative_to(ROOT).as_posix() for name in (
        'query-v2-interface.md','extend_query_projection_schema.py','prepare_c06_metric_input.py',
        'checkpoint_c06_projection.py','publish_c06_projection_checkpoint.py')}
    prefix=OUT.relative_to(ROOT).as_posix()+'/'
    selected=[]
    for row in filter(None,git('status','--porcelain=v1','-uall','-z').decode('utf-8').split('\0')):
        name=row[3:]
        if name=='opencode.json':
            assert row[:2]=='??'
            continue
        assert name in allowed or name.startswith(prefix),row
        selected.append(name)
    selection=OUT/'git-selection-02.json'
    assert not selection.exists()
    hashes={name:sha((ROOT/name).read_bytes()) for name in selected}
    selection.write_text(json.dumps({'base':BASE,'files':hashes,'private_checkpoint_only':True,
        'public_query_changed':False,'owned_runtime_keep':str(OWN)},indent=2)+'\n','utf-8')
    selected.append(selection.relative_to(ROOT).as_posix())
    hashes[selected[-1]]=sha(selection.read_bytes())
    git('add','--',*selected)
    assert set(git('diff','--cached','--name-only').decode().splitlines())==set(selected)
    for name,expected in hashes.items():
        raw=(ROOT/name).read_bytes()
        assert sha(raw)==expected
        staged=git('show',':'+name)
        assert staged==raw or (name in allowed and staged==raw.replace(b'\r\n',b'\n')),name
    git('diff','--cached','--check')
    print(git('commit','-m','Checkpoint original-answer query integrity and private C06 TDD').decode(errors='replace'),flush=True)
    commit=git('rev-parse','HEAD').decode().strip()
    print(git('push','origin','master').decode(errors='replace'),flush=True)
    remote=git('ls-remote','origin','refs/heads/master').decode().split()[0]
    assert remote==commit
    assert git('status','--porcelain=v1','-uall').decode().replace('\r\n','\n')=='?? opencode.json\n'
    print(json.dumps({'commit':commit,'remote_head':remote,'selected_paths':len(selected),
        'private_checkpoint_only':True,'raw_evidence_staged_identical':True,'public_query_changed':False,
        'owned_runtime_keep':str(OWN)}),flush=True)


if __name__=='__main__':
    main()
