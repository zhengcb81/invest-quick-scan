# G0 固定约束预审矩阵（实现者整理）

**状态：待独立审查。** 本矩阵用于定位证据，不构成 G0 结论。判定栏只描述本仓现有契约/测试能证明的范围。

| 约束 | 固定要求 | 本地对应证据 | 实现者预审结论 | G0 状态 |
|---|---|---|---|---|
| I01 轻资产 | 只保留结构化问答、短依据、引用与必要运行信息；不保存公司文档正文 | C06 exchange schema/fixtures/DB-07；C07 optional company-wiki / START-05；`docs/stock-pool-design.md` | 本地契约禁止document payload并说明不启动来源链；真实StockQA/StockWiki产物仍未核查 | pending |
| I04 身份 | company/entity、security、segment分层；多地挂牌的桥接必须核实 | C01 identity schema与ID-01—04、UNI-04；C06 Exchange/Query实体引用 | 样例表达一个实体多证券、母子隔离；真实issuer bridge数据及运行端尚未验收 | pending |
| I05 分数 | 正式分数为1—10整数；未知、不适用、错误和未联网不得冒充分数 | C02 metric；C03 score/rule与SC-02—09；C06 FACT-01 | 离线Schema与正反例有覆盖，事实观察score=null；真实AnswerGenerator结果未接入验证 | pending |
| I08 不可变性 | 观察、题义、锚点、时期与引用不可被后续导入/模型替换伪装成历史事实 | C04 work/time；C06 hash/DB-03/QUERY-04 | 时效、hash冲突与重新提问分离有离线检查；真实多进程持久化尚未验收 | pending |
| I12 持久任务 | 逐题待办可恢复；结果与导入分别幂等；外部不明不得假报零费用 | C04 JOB-01/08；C05 BUD/PAR；C06 DB-02/03；C07 START-02/03 | 契约跨卡覆盖重放、冲突、续扫和预算连续；尚无真实队列/费用账本联调 | pending |
| I17 审查纪律 | 固定预期不可为通过而降级；skip/旧日志/整体mock不能算通过 | 各卡 tests 与 receipts；G0 validation logs；全量174 tests | C01—C07 case IDs均与回执记录匹配；本包补充输出hash。是否存在语义弱断言仍需独立反例审查 | pending |
| I18 接口与写入权 | 接口先核实；跨仓一个任务一个写入拥有者 | P00 baseline report；C01 identity owner；C06 owner矩阵；C07 launch/release owner矩阵 | 2026-09-22接口快照仅为历史证据；本轮没有获准重读其他仓的当前状态，也没有外仓写入 | pending |

## G0 cases

| Case | 预期 | 当前证据 | 未完成项 |
|---|---|---|---|
| BASE-02 | 依赖/入口不符时只记录实际情况，不发明接口，不把skip算通过 | `baseline-report-2026-09-22.md`及P00回执；本地 CodeGraph可用、另有调用别名解析漏报说明 | 当前外仓接口未重新读取；历史 localhost:8080 探测不重放，独立审查者需判断其证据充分性 |
| REV-01 | 最新快照、每个case的真实结果、依赖、问题闭环和审查记录齐全后才verified | 候选快照、8份任务回执、本地完整性审计 | 独立审查与跨项目最新接口证据缺失，因此不能verified |
| REV-02 | 输出缺失/空白、测试未跑/关键skip或审查后改源码时保持pending/needs_revision | C01—C03本次复跑日志；C04—C07逐卡日志；全量本地测试日志与hash | 审查者应复现关键检查并核对版本绑定；当前为实现者运行 |
| REV-03 | 不得改固定预期、删负例、mock整条被测决策或用生成脚本自证 | 真实离线helper测试、schema引用审计、全量测试源码 | 独立审查者须查看差异与关键断言；实现者自查不能关闭此case |

本表的所有pending是刻意保留的审查状态。离线契约通过不代表真实搜索、数据库、预算、worker、UI、进程管理或消费者接口已完成。
