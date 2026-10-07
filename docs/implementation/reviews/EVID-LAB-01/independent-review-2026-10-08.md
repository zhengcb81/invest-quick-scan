# EVID-LAB-01集中独立只读审查

agent evid_lab_acceptance_review，Lab HEAD d87cf718a0fa90f2d0929e902ad2faa70c39580a；只读文件与内存反例，网络/收费/下载/仓库写0。总控另运行公开CLI及隔离回归，不能把本静态审查当那些测试。

结论：暂不签收语义规则与冻结提案完成。semantic.py:131–135的dict period丢quarter/half；166–189缺year也pass。440–460 URL无window pass，同URL多年度报告比较列fail。proposal.md:64–65/config:94–99主item分母仅answered，失败包题位消失；config:22–45没有实际题组/query，56的0.85USD缺token/费率公式。前两项和分母为P1，冻结不足为P2。

其他需修：fixtures.py:75只比历史chunk state/parse_error/question_ids，FX031改答案score/rationale后verifier仍[]。cli.py:220 fixture input/answer hash为空，diagnostics.py:416 semantic location为空。diagnostics.py:139忽略evidence_kind，synthetic FX021结构错误标historical；563把FX032的agent标签依据标historical。fixture catalog有34case、42expectations产生350诊断，summary“350条期望”应纠正。

FX034为collected=false空槽，没有伪造真实来源证据；其余五historical是模型输出不能算来源原文。现有unit规则只比量纲/币种，不比归一金额；metric只比family，不宣称解决Phase96十倍金额、归母/扣非或完整投资判断。保留旧实现，按总控整改卡一批修复并提供真实版本/hash。
