"""Publish only private progress/evidence, keeping public query v1 unchanged."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[5]
OWN=ROOT/'runs/c15a'
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'
CONTROL=Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    assert OWN.is_dir() and not (OUT/'git-selection-01.json').exists()
    check=json.loads((OUT/'checkpoint-01.json').read_bytes())
    assert check['state']=='private_in_progress_not_reviewed_not_published' and check['pytest_passed']==21
    original=json.loads((OUT/'inputs-01.json').read_bytes())
    for row in original['IQS_nonsecret_inputs']:
        assert sha((ROOT/row['path']).read_bytes())==row['execution_sha256']
        assert sha((OWN/'iqs'/row['path']).read_bytes())==row['execution_sha256']
    for row in check['snapshot']:
        assert sha((OUT/'private-source-01'/row['path']).read_bytes())==row['execution_sha256']
        assert sha((OWN/'iqs'/row['path']).read_bytes())==row['execution_sha256']
    paths=['.gitattributes','task_plan.md','progress.md','findings.md','docs/implementation/handoff-for-new-agent.md']
    paths += [(CONTROL/name).relative_to(ROOT).as_posix() for name in (
        'prepare_c06.py','run_c06_checks.py','build_query_v2_private_schema.py','query-v2-interface.md',
        'checkpoint_c06.py','publish_c06_checkpoint.py')]
    paths += [p.relative_to(ROOT).as_posix() for p in OUT.rglob('*') if p.is_file()]
    e={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    e.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=ROOT,env=e)
    assert git('rev-parse','HEAD').decode().strip()=='bc9ab49e5fd015c51cdc4d586d9398be6963cd7c'
    assert not git('diff','--cached','--name-only')
    for row in filter(None,git('status','--porcelain=v1','-uall','-z').decode().split('\0')):
        assert row[3:] in paths+['opencode.json'],row
    selection=OUT/'git-selection-01.json'
    hashes={name:sha((ROOT/name).read_bytes()) for name in paths}
    selection.write_text(json.dumps(dict(base='bc9ab49e5fd015c51cdc4d586d9398be6963cd7c',
            files=hashes,public_query_changed=False,private_checkpoint_only=True,owned_runtime_keep=str(OWN)),indent=2)+'\n','utf-8')
    paths.append(selection.relative_to(ROOT).as_posix())
    hashes[paths[-1]]=sha(selection.read_bytes())
    git('add','--',*paths[:11])
    git('add','-f','--',*paths[11:])
    assert set(git('diff','--cached','--name-only').decode().splitlines())==set(paths)
    for name,h in hashes.items():
        raw=(ROOT/name).read_bytes()
        staged=git('show',':'+name)
        assert sha(raw)==h
        assert staged==raw or (name in paths[:5] and staged==raw.replace(b'\r\n',b'\n')),name
    git('diff','--cached','--check')
    print(git('commit','-m','Checkpoint private C06 subject-bound query TDD and handoff').decode(errors='replace'))
    commit=git('rev-parse','HEAD').decode().strip()
    print(git('push','origin','master').decode(errors='replace'))
    assert git('ls-remote','origin','refs/heads/master').decode().split()[0]==commit
    assert git('status','--porcelain=v1','-uall').decode().replace('\r\n','\n')=='?? opencode.json\n'
    print(json.dumps(dict(commit=commit,remote_head=commit,selected_paths=len(paths),private_checkpoint_only=True,
                         raw_evidence_staged_identical=True,public_query_changed=False,owned_runtime_keep=str(OWN))))


if __name__=='__main__':
    main()
