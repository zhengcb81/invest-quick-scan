# JR1/JR3 总控软件验收：待一个备份路径的写许可

**用户授权的四文件修复候选已完成，当前集中软件验收通过；StockWiki 源仓尚未发布。** 用户指定总控接管四个路径的授权已经生效，不重复申请。新增持久审计使观察库成为 schema2，备份 manifest 的上界必须同时由1升2；这第五路径的单行修改尚未获许可，因此保留整批可审候选，不发布已知无法备份的半批。

源基线 StockWiki `c40de21403720306ba21edbf71b9634a40ee58f8`，源码检查时 clean；StockQA 使用已发布 `bc41908e4cdc44c13fefda97f3118e5434aed5f8`。候选原字节与当前五 SHA 见 [机器验收](../../../intake/G3/2026-10-09-jr13/acceptance.json)、[最终执行锁](../../../intake/G3/2026-10-09-jr13/final-snapshot/execution-lock.json)；[完整候选补丁](../../../intake/G3/2026-10-09-jr13/source-candidate.diff)可以直接审阅。

## 已解决的行为

- 新 ACK 严格符合十字段公共 ImportAck 1.0.0，与观察一起在真实事务中落库；序号、内部原因和原导入引用进入单独审计表。公共错误码稳定，accepted/already_present 的 error 为 null。
- raw JSON 在对象/数组任意深度拒绝重复键、非有限值与数值溢出；direct dict 同样拒绝非法类型、循环及非有限值。坏批次在写入之前结束，不制造 fallback 地址。
- schema1→2 只加审计表，迁移在 BEGIN IMMEDIATE 内核版本；历史观察及 ACK 的 JSON、ID、时间、SHA不改，不回填历史审计。审计失败与观察/ACK整批回滚。
- already_present 新审计只引用原 accepted 的 package/item，不引用更早 rejected。冲突保留内部原因，同时输出冻结公共 taxonomy。
- 严格JSON/原包hash校验后的精确历史包，通过 SQLite mode=ro 四绑定对账返回原ACK，schema1数据库SHA零变、不升级、不补审计。旧短地址和 enriched wire 保真；legacy_wire_pending仅放receipt侧，QA仍strict拒旧wire，无虚假 delivered。
- mixed批次扫描全部已存槽，写事务再核不可变四绑定；顺序不影响拒绝，真实第二连接在快照后提交竞争槽也会触发整批回滚。

## 证据与边界

| 最终批次 | 结果 | 范围 |
|---|---|---|
| affected-final-04 | 113P，pytest14.88s | 观察、交付、备份、查询、新鲜度五测试文件；实际CLI坏输入、审计回滚、迁移/恢复和历史保真 |
| static-05 | 两命令exit0 | StockWiki原Ruff范围与框架static；原生Ruff单独执行，没有伪称Python guard覆盖Rust |
| joint-07 | 18P，pytest131.36s | 真正owner代码/公开CLI，31原包导入、事前consumer绑定、原ACK、QA严格应用、暖恢复零新HTTP、完整查询body与独立备份恢复 |
| 同次集中独审最终复核 | F1–F5全关闭，零开放software findings | 实际旧c40 serializer、双importer迁移、两顺序mixed及真实双SQLite连接交错；所有探针/线程终态 |

各批不机械相加成一次总测试数。原RED、两份旧审查和 reviewer 自身三次探针假设失败都保留；当前 SHA 不借更早103P/106P或joint05/06证明。母测试的竞争快照为模拟边界，独立探针另有真正双连接交错，分别标记。独立 QA 历史负例使用 rejected enriched原回执，保持send_uncertain及全dump SHA；没有声称旧accepted回执已跨owner成功。旧accepted保真在SW两个历史路径实证；正常新公共ACK的正闭环由joint07证明。

正式 [独立报告](compatibility-recheck.md) 与 [机器结论](compatibility-recheck.json) 固定当前五SHA；253原件逐字节匹配，实际核验索引。最终快照保留五候选、guard/adapters/fixture、两轮各31原包，480非秘密owner源依赖锁；不归档数据库或配置内容，不保存公司文档。62包来自模型HTTP替身，真实付费API/真实key/生产名单及数据库写入均为0，不能当作金融准确性、真实费用或owner身份golden。

## 发布与接续

读 [备份单路径许可](backup-scope-extension.md) 和 [接续规范](publication-handoff.md)。获得第五路径明确许可后才重核源树、精确复制五候选、正常外仓Git hooks/commit/push并追加实际PWF回执。原接收/测试source_written=false证据不能改写。自有测试环境清理以intake的cleanup-receipt终态为准；不碰外仓、共享TEMP或未知opencode.json。旧固定根/旧helper不可盲跑。

本签收限软件候选；G3/F05/L03、真实identity/facts/query owner golden、真实金融准确性/计价、TH/IN源写许可及全池生产启动继续按原门，不因这批软件通过自动关闭。目标尚未完成。
