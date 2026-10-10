"""Record the actual approved checkpoint Git result, without another test batch."""
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[5]
PUB=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09/iqs-subject-publication'


def main():
    receipt=json.loads((PUB/'result.json').read_bytes())
    commit=receipt['commit']
    assert commit==receipt['remote_head']=='f4e05452656752f53f8973ac72b999a65a314d1e'
    assert receipt['selected_paths']==81 and receipt['private_checkpoint_only']
    progress=ROOT/'progress.md'
    text=progress.read_text('utf-8')
    marker='- 两阶段主体primitive私有checkpoint已实际正常提交推送'
    assert marker not in text
    progress.write_text(text.rstrip()+'\n'+marker+commit+
        '：81精确路径、staged原工件字节一致、origin/master与HEAD相同；commit5084/push9860均终态0。'
        '自动复核在已收新只读原码同目的地证据后放行同一正常动作，没有换目的地/绕钩子或强推。'
        'repo可见性仍未核，未虚称private。两未知nul/opencode保留、本段产品未发布、完整节点尚未审，c15a仍用于实际before-send接续。\n','utf-8')
    handoff=ROOT/'docs/implementation/handoff-for-new-agent.md'
    text=handoff.read_text('utf-8')
    marker='**实际Git补记：** IQS私有主体primitive checkpoint f4e0545已正常提交推送，81精确路径；'
    assert marker not in text
    handoff.write_text(marker+'未发布产品，完整C06/实际HTTP producer及各证据门不变。下一动作仍按下面唯一当前交接；正常Git回执见progress。\n\n'+text,'utf-8')
    paths=[progress.relative_to(ROOT).as_posix(),handoff.relative_to(ROOT).as_posix(),
           Path(__file__).relative_to(ROOT).as_posix()]
    logs=[p.relative_to(ROOT).as_posix() for p in PUB.iterdir() if p.is_file()]
    assert len(logs)==7
    env={k:v for k,v in os.environ.items() if k.upper() in {
        'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    env.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
    def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,env=env)
    assert git('rev-parse','HEAD').decode().strip()==commit
    assert not git('diff','--cached','--name-only')
    for entry in filter(None,git('status','--porcelain=v1','-uall','-z').decode('utf-8').split('\0')):
        assert entry[3:] in paths+logs+['nul','opencode.json'],entry
    git('add','--',*paths,*logs)
    assert set(git('diff','--cached','--name-only').decode().splitlines())==set(paths+logs)
    for name in logs: assert git('show',':'+name)==(ROOT/name).read_bytes(),name
    git('diff','--cached','--check')
    print(git('commit','-m','Record actual two-phase subject checkpoint publication').decode(errors='replace'),flush=True)
    current=git('rev-parse','HEAD').decode().strip()
    print(git('push','origin','master').decode(errors='replace'),flush=True)
    assert git('ls-remote','origin','refs/heads/master').decode().split()[0]==current
    assert set(git('status','--porcelain=v1','-uall').decode().splitlines())=={'?? nul','?? opencode.json'}
    print(json.dumps({'receipt_commit':current,'remote_head':current,'selected_paths':len(paths+logs),
        'public_source_unchanged':True,'whole_C06_complete':False,'owned_runtime_keep':'runs/c15a'}),flush=True)


if __name__=='__main__': main()
