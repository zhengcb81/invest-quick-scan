"""Once-only actual foundation publication/cleanup bookkeeping for root PWF."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT/'docs/implementation/intake/W15/module-readiness-2026-10-09'


def main():
    publication = json.loads((OUT/'source-publication/result.json').read_bytes())
    cleanup = json.loads((OUT/'cleanup-receipt.json').read_text('utf-8-sig'))
    assert publication['source_published'] and cleanup['applied']
    assert not (ROOT/'runs/w15a').exists()
    sw, qa = (publication['sources'][p]['commit'] for p in ('StockWiki','StockQAbyLLM'))
    plan_path = ROOT/'task_plan.md'
    text = plan_path.read_text('utf-8')
    start = text.index('**2026-10-09 最新授权与唯一下一动作：**',text.index('## Next Step'))
    end = text.index('\n',start)
    next_line = ('**2026-10-09 当前唯一下一动作：** 全部计划内必要跨仓写入、测试及正常Git已授权，root唯一writer，'
        '其他进程工作、216挂牌候选和轻量不下载文档保持。W15基础软件步骤1–3已由同一次集中审查签收，'
        f'StockWiki {sw}本地提交、按决定7无remote，StockQA {qa}已正常推送；'
        '36受审候选和受影响测试/失败分类已归档，自有runs/w15a已严格清理，旧一次性helper不能盲跑。'
        'IQS本批交付以progress与iqs-publication/result.json实际回执为准，未提交前不预报成功。'
        '下一步接续原W15步骤4：[正式query/refresh与真实owner golden](docs/implementation/reviews/W15/module-readiness-2026-10-09/c06-next.md)，'
        '先在新独占根定义显式query v2及主体/范围/水位语义，保留v1/UI原协议；随后owner公共只读producer、受控刷新、真实serializer golden和公开CLI正反例。'
        '基础软件不关闭整个W15、L03/G3/B01准确性、facts/F05、TH/IN或200家公司live，已通过未改范围不重测全仓/UI、不增小节点审查。以下旧状态仅为历史。')
    text = text[:start]+next_line+text[end:]
    old = '- [ ] 完成受影响单元/集成和公开入口E2E、一次集中审查、正常源交付与自有清理；不得由此关闭L03/G3/F05/金融准确性。'
    new = '- [x] 基础范围完成受影响单元/集成和公开入口E2E、同一次集中审查、正常源交付与严格自有清理；整个W15/C06/L03/G3/F05/金融准确性仍开放。'
    assert text.count(old)==1
    plan_path.write_text(text.replace(old,new),'utf-8')
    handoff = ROOT/'docs/implementation/handoff-for-new-agent.md'
    history = handoff.read_text('utf-8')
    cut = history.index('**2026-10-09 最新授权与唯一下一动作：**')
    current = ('**当前交接（2026-10-09，优先于全部历史）：W15基础软件已交付，整个W15仍in_progress。** '
        f'StockWiki master/{sw}正常静态hook本地提交，按既有决定7无remote；StockQA master/{qa}正常钩子提交并推送origin/master。'
        'IQS本批归档提交看progress最新实际回执；受审candidate02及同次review已归档，36候选匹配、开放软件发现0。'
        'IQS18P、SW91P与profiles90P是独立/重叠批次；QA主批307P/1F保留，唯一Q07 fixture修正后8P，不能拼成一次308GREEN；'
        '原完整SW1063P/64F/18skip/21error及分类仍保留。真实API/公司文档/生产库迁移/名单写入0。'
        'runs/w15a已按真实lstat/set/SHA/CIM严格清理，不盲跑旧固定根；原opencode及QA11未知项不读不动。'
        '用户全部后续必要授权持续有效，root唯一writer，只在大节点集中审查。'
        '\n\n唯一下一动作按[c06-next.md](reviews/W15/module-readiness-2026-10-09/c06-next.md)接续原步骤4，'
        '新独占根实施显式query v2/主体范围/水位/缺覆盖，保留legacy v1与W09/UI；随后owner只读CLI、受控刷新和实际serializer golden/生成命令。'
        '当前c06_envelope_validated=false，不能仅翻标记；facts answered/relations、F05、L03/G3/B01准确性和TH/IN前置未关闭。'
        '看[基础交付](reviews/W15/module-readiness-2026-10-09/delivery.md)、task_plan的Next Step和progress最后记录。'
        '\n\n以下均是保留的历史快照；其中等待授权、未发布、活测试根或旧“下一动作”不覆盖本段。\n\n')
    handoff.write_text(current+history[cut:],'utf-8')
    marker = '## 2026-10-09 W15基础软件实际交付与严格清理（当前）'
    progress = ROOT/'progress.md'
    old = progress.read_text('utf-8')
    assert marker not in old
    progress.write_text(old+'\n\n'+marker+'\n\n'
        f'- 同次集中审查开放软件发现0；StockWiki正常提交{sw}、15路径/本地无remote，StockQA正常提交及推送{qa}、16路径/远端同HEAD。'
        '原未知项与保护源码保留，真实API/公司文档/生产名单或数据库迁移0；正常钩子未跳过。\n'
        '- QA首正常提交communicate600s超时，CIM精确核原PID/父子链/UTC创建时间后仅结束自有遗留进程；原控制器没有TimeoutExpired原stdout/stderr落档分支，'
        '不伪造其未捕获日志，工具终态与timeout-descendants实际回执分开留档。复用五组既有准确版本hook缓存，安装metadata SHA前后一致。'
        '接续01全部静态通过、仅mixed-line-ending规范化.gitignore失败；raw受审/新LF/Git三域已记录，02正常钩子/commit/push终态0。\n'
        '- 三项控制器误差均在实际动作前拒绝：PowerShell DateTime本地/UTC比较、只读cache SQLite缺uri=True、Git文本过滤使EOL-only不出现在diff；'
        '按实际口径修正，没有错杀外来进程、读密钥、放宽产品校验或重复测试。只读cache查询的两次失败及最初谓词拒绝保留在progress，不称产品RED。\n'
        f'- 自有runs/w15a实际清理{cleanup["files_deleted"]}文件/{cleanup["directories_verified"]}目录，真实lstat单硬链/无reparse、精确集合与SHA、CIM0，dry→Apply；'
        '根已不存在。20件真正OS producer合成原文已归档，不归档真实SQLite/公司metadata克隆/配置，不清共享TEMP或其他仓未知项。\n'
        '- 更新Next Step/Phase113基础步骤与唯一当前handoff；下一项原步骤4正式query/refresh及真实owner golden继续实施。'
        '本仓IQS正常Git/push实际回执待本批工具完成，暂不写虚构commit；不由基础软件关闭W15/G3/L03/B01/F05/TH-IN或200家live。\n','utf-8')
    findings = ROOT/'findings.md'
    with findings.open('a',encoding='utf-8') as handle:
        handle.write('\n- W15正常源发布实际完成：QA6aafc32远端同HEAD、SWa5a97d6本地无remote。'
          '钩子安装超时属于控制/工具故障，精确结束自有树后复用已安装同版本hook；.gitignore唯一变化为正常hook换行规范化，原审字节与新执行/Git摘要明确分域。'
          '既有cache不删除/恢复覆盖，公共安装metadata前后SHA相同；隔离测试与TEMP仍自有，不能把工具故障改称产品测试通过。'
          '基础软件及自有清理完成，真实query v2/owner golden、金融准确性与facts仍未完成。\n')
    print(json.dumps(dict(updated=['task_plan.md','progress.md','findings.md','docs/implementation/handoff-for-new-agent.md'],
                          source_published=True,owned_runtime_absent=True,whole_W15_complete=False)))


if __name__ == '__main__':
    main()
