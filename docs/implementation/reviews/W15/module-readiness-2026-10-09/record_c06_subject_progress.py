"""One-time root PWF update for the actual private subject-binding checkpoint."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
CURRENT=(
    '**唯一当前动作更新（2026-10-10，以下快照均为历史）：** 在仍独占c15a接StockQA context2/实际before-send、可信固定OS CLI登记与持久receipt引用，'
    '再接consumer/route-refresh、TTL资格、公共query CLI/耐久snapshot及实际owner golden。原C06同节点两阶段owner primitive/事务绑定/读投影已私有23P/6.62s，'
    '历史读取回归33P/45.93s、纯契约65P/1.49s，各组均终态、不能相加为金融准确率。事前只登记本地attempt/主体/题目/版本与摘要，'
    '答案后在原Observation/ACK事务里关联原ID/hash/服务request_id；原JSON不改、旧答案不补绑。schema3复用原观察库，仅1原SW私有候选声明读取扩展点，'
    '177原SW/64原IQS依赖及guard保持，本段生产源未写、0API。原件subject-checkpoint-01/private-subject-01；真实HTTP发送前producer与公共authority adapter仍未接，'
    '不能从public request自填expected_dispatch。完整C06收尾才同一大节点集中审查，所有原证据门开放；c15a不能清，两内容施工包未派发，全计划active目标保持。'
)


def main():
    paths={name:ROOT/name for name in ('task_plan.md','progress.md','findings.md','docs/implementation/handoff-for-new-agent.md')}
    old={name:path.read_text('utf-8') for name,path in paths.items()}
    assert all('C06两阶段主体登记／事务导入及读取接续' not in text for text in old.values())
    task=old['task_plan.md']
    assert task.count('\n## Next Step\n')==1
    task=task.replace('\n## Next Step\n','\n## Next Step\n\n'+CURRENT+'\n',1)
    marker='- 当前私有原答案契约65P与真实SQLite合成历史/读取故障reader33P均已留执行原件；'
    line=next(line for line in task.splitlines() if line.startswith(marker))
    task=task.replace(line,'- 最新subject-checkpoint-01冻结两阶段owner primitive/事务绑定/当前读投影23P、旧历史回归33P、纯契约65P；各批独立合成软件范围，未审未发布。'
        'schema3旧writer不降级写，原答案不改/旧记录不补绑。仍待真实StockQA before-send/context2、公共authority/consumer/refresh、TTL/query CLI/耐久snapshot与实际golden，'
        '同节点收尾集中审查。只有1原SW私有候选声明读取扩展点，177原SW/64原IQS依赖保持；旧checkpoint不覆盖，0API，c15a仍在用。')
    progress=old['progress.md'].rstrip()+'''\n\n### 2026-10-10 C06两阶段主体登记／事务导入及读取接续
- 上一目标回合为progress，真实起点e0e50cb/uall仅原opencode和未知nul；根PWF sole writer，既有全授权有效。两个内容包不重做、不派发，生产QA/SW本段未写。
- 实查begin先prepare再mark，服务request_id及Observation ID/hash在回答后才有。subject-dispatch-interface固定两个不可变对象：owner事前receipt、本地attempt与完整SubjectRef/题目/模块/版本/摘要；事后binding在原Observation/ACK事务里引用前事件，另存bound_at。旧记录不补绑、原JSON不添加subject/身份字段。
- 原继承replay写死schema2，私有最小hunk提供READ_SCHEMA_VERSION（默认2），原迁移写上界不变；子类显式schema3。subject-candidate-inputs-01保存1原SW旧/新SHA，177原SW/64原IQS依赖保持。没有复制import/ACK/replay或改global常量让旧writer降级新库。
- owner-subject-red-01原5312终态2，1 collection error/0.64s，不称执行12漏洞。green01实际5P/7F（internal consumer enum），green02 6P/6F（继承reader拒3与fixture误用import_items而原名acked_items），green03 9P/3F（实现错误要求原schema没有的identity_revision），green04 9P/3F（共享validator调用漏payload_sha），失败原件全保留。green05原10360终态0，12P/4.32s。
- schema3投影projection-red01原10360终态1，3F/12P/5.23s；projection-green01原21772终态0，15P/4.14s。重复PID属于前进程已终态后的新进程，不能只据PID认作同handle。新增provider/题目逃逸、版本/prompt不符、触发器缺失和bound_at早于ACK反例；owner-subject-final-01原21772终态0，23P/6.62s/controller8.217s。按本地attempt+question冻结，不因provider改写或未登记题目逃逸成legacy。
- 同批必要回归因reader/QC分组有改动：owner-history-regression-01原10256终态0，33P/45.93s/controller47.285s；contract-subject-01原22488终态0，65P/1.49s/controller2.659s。三批源SHA稳定、guard abc0128d不变、0API/合成真实组件，各分母独立，不相加为金融准确率。
- primitive expected_dispatch只属于可信adapter独立输入，公共CLI不能由请求自填；实际StockQA context2/HTTP边界、owner authority/consumer/refresh、TTL/query CLI/耐久snapshot/真实golden仍待。原所有门保持，完整C06大节点结束才集中审查，不增加helper审查。
- subject-checkpoint-01/private-subject-01已冻结10候选、原SW旧基线/guard，绑定三final .sources/process SHA，旧档案不覆盖。PWF首次整批apply_patch因handoff长行只取前缀被原子拒绝，实查四文件均未写；改为完整读取/一次性具名更新，不重跑测试。c15a仍用，未知nul/opencode不读不动，正常Git待真实回执，不预报成功。
'''
    findings=old['findings.md'].rstrip()+'''\n\n### 两阶段主体来源的实际接线边界
- 原标准Observation1.1确实不含identity_revision/listing_id/analysis_subject，EntityId是bounded string，并非旧摘要猜的ENT无连字符regex。身份/挂牌从独立事前receipt/context冻结，不补原JSON；题目/模块/定义/语义、实际选择的provider/requested模型、prompt、cutoff等与原字段逐项匹配。
- 发送前只已有本地工作/attempt；服务request_id和答案hash在响应后才有，不能制造含这些内容的过去事件。实际owner事务已支持事后不可变绑定、重启精确重放和整批rollback；primitive合成测试不代替公共authority或真实HTTP前生产。
- provider/题目改写不能因查不到自己的pre-receipt降成legacy逃逸。当前按本地attempt+question关联并拒已登记attempt的未登记题目，未登记的真正旧attempt继续历史只读。当前availability仍不是TTL/白名单或金融准确性签收。
'''
    handoff='**唯一当前交接，后续均为保留历史：** '+CURRENT+'\n\n'+old['docs/implementation/handoff-for-new-agent.md']
    changed={'task_plan.md':task,'progress.md':progress,'findings.md':findings,'docs/implementation/handoff-for-new-agent.md':handoff}
    for name,text in changed.items():
        paths[name].write_text(text.rstrip()+'\n','utf-8')
    print('PWF current subject primitive and next production boundary recorded; no source publication.')


if __name__=='__main__':
    main()
