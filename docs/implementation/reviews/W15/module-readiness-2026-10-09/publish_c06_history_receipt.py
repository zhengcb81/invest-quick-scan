"""Append actual checkpoint Git evidence, with no product re-test or release."""
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[5]
PUB=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09/iqs-history-publication'


def main():
    result=json.loads((PUB/'result.json').read_bytes())
    commit=result['commit']
    assert commit==result['remote_head']=='ccd3b464c34af2c810309e2ed57598fe4bb6e0b4'
    assert result['selected_paths']==41 and result['private_checkpoint_only']
    progress=ROOT/'progress.md'
    text=progress.read_text('utf-8')
    marker='- 历史/冻结捕获私有checkpoint实际正常提交推送'
    assert marker not in text
    progress.write_text(text.rstrip()+'\n'+marker+commit+
        '：41精确路径，原工件staged字节核对通过，origin/master同HEAD；原opencode与新未知nul均未读/未删除/未暂存。'
        '此为私有进度留档，产品未发布、整C06/W15原门不变，自有c15a仍保留。实际commit/push PID10988/11344均终态0。\n'
        '- 后续只读源码勘察发现事前receipt与事后Observation ID/hash必须分开：答案hash尚未产生时不能声称已在发送前保存；'
        '后续sidecar应链接真实事前冻结事件及事后原答引用，不能临时制造过去时间。原owner_refresh/transport只读当前文件确认，未改生产源。'
        '一次源码Get-Content工具只打印output而未保存返回handle，不能据半段输出认定完整读取成功；独立具名Python只读读取已终态0，'
        '后续全部exec返回session/exit metadata。沙箱CIM资源不可访问，未据此断言旧shell无活进程、未kill其他进程；无收费或数据写操作。\n','utf-8')
    handoff=ROOT/'docs/implementation/handoff-for-new-agent.md'
    text=handoff.read_text('utf-8')
    old='IQS起点13d263e，原Phase113/C06步骤4私有实施'
    assert text.count(old)==1
    handoff.write_text(text.replace(old,'IQS私有checkpoint已正常提交推送ccd3b46（41路径），原Phase113/C06步骤4私有实施'), 'utf-8')
    paths=[progress.relative_to(ROOT).as_posix(),handoff.relative_to(ROOT).as_posix(),
           Path(__file__).relative_to(ROOT).as_posix()]
    logs=[p.relative_to(ROOT).as_posix() for p in PUB.iterdir() if p.is_file()]
    assert len(logs)==7
    env={k:v for k,v in os.environ.items() if k.upper() in {
        'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    env.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=ROOT,env=env)
    assert git('rev-parse','HEAD').decode().strip()==commit
    assert not git('diff','--cached','--name-only')
    for entry in filter(None,git('status','--porcelain=v1','-uall','-z').decode('utf-8').split('\0')):
        assert entry[3:] in paths+logs+['opencode.json','nul'],entry
    git('add','--',*paths,*logs)
    assert set(git('diff','--cached','--name-only').decode().splitlines())==set(paths+logs)
    for name in logs:
        assert git('show',':'+name)==(ROOT/name).read_bytes(),name
    git('diff','--cached','--check')
    print(git('commit','-m','Record actual owner-history checkpoint publication').decode(errors='replace'),flush=True)
    current=git('rev-parse','HEAD').decode().strip()
    print(git('push','origin','master').decode(errors='replace'),flush=True)
    assert git('ls-remote','origin','refs/heads/master').decode().split()[0]==current
    remaining=git('status','--porcelain=v1','-uall').decode().splitlines()
    assert set(remaining)=={'?? nul','?? opencode.json'}
    print(json.dumps({'receipt_commit':current,'remote_head':current,'selected_paths':len(paths+logs),
        'public_source_unchanged':True,'whole_C06_complete':False,'owned_runtime_keep':'runs/c15a'}),flush=True)


if __name__=='__main__':
    main()
