"""Record the actual foundation publication, then commit only its final receipts."""
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[5]
OUT=ROOT/'docs/implementation/intake/W15/module-readiness-2026-10-09'
PUB=OUT/'iqs-publication'


def main():
    receipt=json.loads((PUB/'result.json').read_bytes())
    commit=receipt['commit']
    assert commit==receipt['remote_head']=='929d76226dc2efa8b02e094312baa51fe71076c8'
    assert not (ROOT/'runs/w15a').exists()
    progress=ROOT/'progress.md'
    marker='### W15基础归档实际Git回执'
    text=progress.read_text('utf-8')
    assert marker not in text
    progress.write_text(text+'\n\n'+marker+'\n\n'
        f'- IQS正常提交推送{commit}，555精确路径，远端origin/master同HEAD；冻结工件staged原字节与工作树SHA核对通过，原opencode保留。'
        '原-uall目录折叠拒绝在stage前停止；随后index.lock竞争在535项暂存后停止，只读确认锁自行消失，无删锁/杀外来进程。'
        '精确续收保留原selection/失败记录；diff检查发现交接PWF尾空行，只修该文档，原raw证据不动，正常commit/push终态0。\n'
        '- 本条与实际提交/推送日志仅补记已完成交付，不改candidate02、受审产品或清理回执，不再次测试/审查。'
        'Phase113步骤4继续按c06-next实施，整个项目目标active；下一IQS提交仅包含本PWF补记及实际Git日志，不预报其commit。\n','utf-8')
    task=ROOT/'task_plan.md'
    text=task.read_text('utf-8')
    old='IQS本批交付以progress与iqs-publication/result.json实际回执为准，未提交前不预报成功。'
    assert text.count(old)==1
    task.write_text(text.replace(old,f'IQS基础归档{commit}已正常推送，555精确路径/原字节核对通过；后续仅PWF与实际Git回执补记不改变受审产品。'),'utf-8')
    handoff=ROOT/'docs/implementation/handoff-for-new-agent.md'
    text=handoff.read_text('utf-8')
    old='IQS本批归档提交看progress最新实际回执；'
    assert text.count(old)==1
    handoff.write_text(text.replace(old,f'IQS基础归档{commit}已推送，后续仅PWF/实际Git回执补记时HEAD以Git为准；').rstrip()+'\n','utf-8')
    delivery=ROOT/'docs/implementation/reviews/W15/module-readiness-2026-10-09/delivery.md'
    text=delivery.read_text('utf-8')
    old='| invest-quick-scan | 本批实际提交以intake/iqs-publication/result.json及progress回执为准 | 5公共代码/schema、PWF和原字节证据 | 正常提交/推送进行时不预报成功 |'
    assert text.count(old)==1
    delivery.write_text(text.replace(old,f'| invest-quick-scan | master / {commit} | 555精确路径，含5公共代码/schema、PWF和原字节证据 | origin/master已核与commit相同 |'),'utf-8')
    paths=[str(p.relative_to(ROOT).as_posix()) for p in (progress,task,handoff,delivery,Path(__file__))]
    logs=[str(p.relative_to(ROOT).as_posix()) for name in ('diff-check-resume-02','commit','push')
          for p in (PUB/(name+'.stdout.log'),PUB/(name+'.stderr.log'),PUB/(name+'.process.json'))]
    logs.append((PUB/'result.json').relative_to(ROOT).as_posix())
    e={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMDRIVE'}}
    e.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=ROOT,env=e)
    assert git('rev-parse','HEAD').decode().strip()==commit
    assert not git('diff','--cached','--name-only')
    for entry in filter(None,git('status','--porcelain=v1','-uall','-z').decode().split('\0')):
        assert entry[3:] in paths+logs+['opencode.json'],entry
    git('add','--',*paths)
    git('add','-f','--',*logs)
    assert set(git('diff','--cached','--name-only').decode().splitlines())==set(paths+logs)
    for name in logs:
        assert git('show',':'+name)==(ROOT/name).read_bytes(),name
    git('diff','--cached','--check')
    print(git('commit','-m','Record actual W15 foundation publication and cleanup handoff').decode(errors='replace'))
    current=git('rev-parse','HEAD').decode().strip()
    print(git('push','origin','master').decode(errors='replace'))
    assert git('ls-remote','origin','refs/heads/master').decode().split()[0]==current
    assert git('status','--porcelain=v1','-uall').decode().replace('\r\n','\n')=='?? opencode.json\n'
    print(json.dumps(dict(receipt_commit=current,remote_head=current,selected_paths=len(paths+logs),
                         source_and_raw_evidence_unchanged=True,whole_W15_complete=False)))


if __name__=='__main__':
    main()
