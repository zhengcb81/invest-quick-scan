# FACT-CONTENT-01-R3：当前补丁已签收

总控结论：`accepted_on_frozen_bytes`。FR2-01、FR2-02、FR2-03 均已关闭，保留原有成果；不再要求本包返工或重跑原135项。此次接收的是软件与候选内容校验补丁，F05真实内容/owner oracle及整个项目验收仍按原计划推进。

## 接收对象

- 唯一源仓：`C:/Users/郑曾波/Projects/iqs-fact-content-lab`，交接 `docs/handoff/FACT-CONTENT-01/remediation-03/handoff.json`。
- 独立只读Git记录中的实际分支：`codex/fact-content-01-r2`；R3是交付轮次，不能据建议分支名改写实际分支。
- 产品commit：`3f1565fd235b457010aa0231b95d653d723df440`；tree：`7c432eff06403bfd57a859adfdf82c005e64bfaf`。
- 当前HEAD：`4ee03942a3f1936c747a32924de5890f5a59af73`。产品之后包含交接、README和.gitignore卫生变更，不能将HEAD与产品commit混称。
- 冻结167个受控源文件，raw SHA/bytes和HEAD在测试前后未变。源清单文件raw SHA：`6e547edbddfee98ff1cb2b3a43f0f03ccc6b1efea8ea2b611dcab73de0fb84b5`。
- R3工件清单29/29、原输入锁213/213均与实际字节一致。

## 同一次集中续验

独立总控使用原25例同构输入和冻结副本的公开CLI，**25/25符合预期**。实际控制器PID18108，exit0，用时19.308407秒。没有把交付者测试与本批相加，也没有重跑旧135项。

| 原缺口 | 本次实际正反例 | 处置 |
| --- | --- | --- |
| FR2-01 未来证据误伤 | 当前有效primary加非primary未来计划仍exit0；forward候选保留unknown仍exit0；未来primary伪装当前true及历史不相交仍exit4 | 关闭，保留周期/恢复候选和未来探索语义 |
| FR2-02 旧版嵌套路径测试被遮挡 | 中性根的真实1.0归档read-legacy exit0；仅改nested case_file并同步pack ID，exit6且实际命中secret-like路径保护 | 关闭，没有以根名或版本错误替代目标拒绝 |
| FR2-03 最后清单不一致 | R2指定两planning条目及R3全部29工件raw SHA/bytes匹配 | 关闭 |

源事实、主体与scope、membership闭合、验证后变异、schema override、真实Windows junction保护等原控制在同批保留。两个公开导出的48路径及raw SHA相同。没有生成真实金融正例或owner golden。

## 交接口径及隔离

旧R2产品与此前产品Git对象当前不可读；R2 tip与R3产品对象可读。因此只签收当前冻结字节，不声称旧Git历史完整恢复，不猜测丢失原因，也不修复源仓Git。交接自述27工件而实际29；R2剩余旧清单实际134/137，三个允许的差异是README和两产品/测试文件。新的接收记录保留这个准确口径，不修改旧handoff。这些说明不构成新的产品审查门。

全部CLI只用自有IQS隔离根、无凭据环境和原网络/SQLite guard加普通文件写审计。所有测试进程已终态；两个自有junction只删除链接自身、目标字节保留，再按精确路径/raw SHA核验删除361个自有文件。`runs/far3`已不存在。源仓写入、收费API、公司文档下载、生产库/名单写入均为0。

完整证据：[独立报告](../../../intake/parallel-acceptance-2026-10-11/fact-r3/review.md)、[结果](../../../intake/parallel-acceptance-2026-10-11/fact-r3/result.json)、[Git只读原件](../../../intake/parallel-acceptance-2026-10-11/fact-r3/git-readonly.json)。这些私有证据保留本机，不随本公文导出数据库、golden或密钥。

46案例仍为synthetic，production_mapping为not_mapped、production_case_status为not_run；4 proposals及7 unresolved保留。本签收不关闭金融准确性、F05、G3、正式题库/词表发布、C06/W15、TH/IN、B01、UI或全池目标。后续集成由原权威owner承担，不为本轮再创建整改任务。
