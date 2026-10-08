# SW-REPAIR-02 第二轮修复验收

2026-10-08，总控 `/root`。结论 `partial_verified / changes_requested`：**原12固定反例均通过、原修复成果保持；剩一项同SR02-4损坏输入链P2。** 一次集中独审、一个受影响批次及局部证疑，不增加小节点门。原worker全套1032/1046与本轮269广域日志作为收到的证据，不重复泛跑。

## 固定交付与复现

实际StockWiki master/clean，基线 `6d1dddbc1289a17a2fb91d40a0d4f57494fa1bfd`，代码结果 `c83c148af35407a5ae01072314ba9bd17e59b3d9`，接收/收尾HEAD `1831a73b37a3ed1b67d3556f6425ed2b52594a24`。结果后28路径仅在 `docs/handoff/SW-REPAIR-02/`。本轮不写源仓、不代推外仓、不执行动态未提交代码。源码/测试/pyproject加原legacy producer共296文件按结果commit导出到IQS新独占根，配置仅复用空providers环境，没有生产库、名单、凭据或公司文档。

69/69工件工作树size/SHA与接收HEAD Git blob size/SHA全匹配，36仅CRLF/LF不同。公开handoff正确catalog exit0，仅是结构/范围接收，不是签整包。接口projection `quick_scan_profiles/1.1.0`；query/backup现有版本及多文件接口hash边界保留。工件note过宽地说全部git_blob来自结果c83c148：实际16路径当时不存在、11路径当时内容不同；运行源码属于c83c148、交接属于后续HEAD，已由总控两ref分开核验，需同批澄清文字。见[原字节/Git核验](../../../intake/SW-REPAIR-02/2026-10-08-remediation/artifact-verification.json)。

## 实际验证

| 范围 | 总控结果 |
|---|---|
| 受影响8个测试文件＋原SW-READY冻结7 | 96 passed /22.08s，进程wall22.768s；89当前worker相关方法＋7原冻结 |
| 原12固定边界文件，字节/断言不改 | 12 passed /2.61s，wall3.367s；segment/已结束period/basis、两junction、三registry、四JSON形状 |
| 追加同SR02-4非UTF8输入 | 2 failed /1.58s，wall2.358s；list/prune同一根因，非两个独立问题 |
| 真实Playwright浏览器 | 11 passed，wall87.115s；142 loopback请求、11临时端口、外部请求0；保留3截图 |
| IQS公共handoff CLI | exit0，原件未修改 |

96和12有重复ported案例，不能相加声称108唯一方法。测试真实public create/import/query/list/prune与浏览器，数据为隔离synthetic，不是实际owner身份/事实gold。原不可比2/9观察全部保留、默认ambiguous/null不入>=8；junction根/父拒绝、registry归属/版本无删除权、四合法JSON坏形状skip继续清理均通过。单变体“选择”正例是另workspace只导入一条，不证明同库查询期可选多变体；此能力仍不存在，保持默认ambiguous。variants截图实际查看可见2/9及不可比提示，不替代新维度全部UI断言。

[结果/命令/原stdout-stderr](../../../intake/SW-REPAIR-02/2026-10-08-remediation/verification/result.json)、[固定反例输入输出](../../../intake/SW-REPAIR-02/2026-10-08-remediation/counterexamples)、[一次独审](independent-review.md)留档。296导出源和130实际读取IQS输入在全批次与收尾SHA不变。

## 代码剩余：SR02-4B / P2

独审定位 `quick_scan_backup._read_manifest_object` 的UTF8 decode异常未归类。总控真实create两份备份，再在外来目录写单字节0xff manifest；公开list、prune都抛UnicodeDecodeError，而非invalid/skipped继续处理合法备份。外来字节和两合法备份保持，**没有证明越界删除或数据丢失**。完整原日志和两终态输入输出留档，[单项接续卡](remaining-repair.md)限定解码边界与明确错误处理，保留已通过组；无需重造其他能力或复跑无关全套。

## 清理与不可补造的历史边界

总控本轮全部临时路径在 `runs/sw-repair-remediation-2026-10-08-01`。子环境无key；Python audit限制写根、非loopback DNS/socket及child allowlist；浏览器route abort外部请求，关闭background网络/外部DNS，不称全OS/native-child隔离或系统抓包。

8个真实Windows junction先不跟随inventory、核两端精确绝对路径均在自有根、非递归只解节点并核目标仍在。严格CIM0/11端口无监听、814文件/654目录集合和逐文件size/SHA、单硬链/无reparse，dry-run后Apply逐项删除，根已不存在。[dry-run](../../../intake/SW-REPAIR-02/2026-10-08-remediation/cleanup-dry-run.json)和[Apply](../../../intake/SW-REPAIR-02/2026-10-08-remediation/cleanup-receipt.json)分别保留。run session1309、prepare-cleanup78132、Apply17690实际exit0，其余同步child已结束。源HEAD/clean及69工件收尾不变，外仓、旧Phase92、共享TEMP、opencode全部保留。

controller适配错误另列，不当产品RED：初junction被沙箱拒绝，部分marker/sentinel严格验证后提升只补建；首次resume的目录存在错误加Force于已核目录；cleanup首次把Target字符串[0]当路径，在删节点前安全停止，改显式数组后完成。没有篡改断言掩盖这些失败，没有覆盖旧验收日志。

worker R2清理回执明确没有逐文件SHA/硬链/正式port扫；已消失旧目录不能补取历史证据。本轮总控严格清理不能冒充worker过去已做。旧共享TEMP105/109/110/111消失但删除者不明，pytest retention只作可能解释，不作取证事实；不按编号/mtime代删其他lane文件。这些历史边界继续open，接续只要求新测试严格隔离，不要求伪造过去GREEN。

本轮有限软件复验完成，整包待SR02-4B；真实identity/facts golden、QA→W05→ACK→UI、双owner恢复、G3/F05/TH/IN/L03仍missing/not_run。PWF/接手说明记录此结论，原StockWiki writer接续，Lab/QA不接管，收到两端新正式交接后再按既有联合说明打通。
