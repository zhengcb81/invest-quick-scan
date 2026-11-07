# 交接与复审规则

适用于 TH-SOURCE-INTEGRATION-01 与 IN-SOURCE-INTEGRATION-01。两卡的专属范围优先；不得跨包写入。

1. 从 `inputs.lock.json` 中该包的精确 source commit 建全新隔离 Lab。先确认目标 Lab 不存在；若已存在，保留原目录并报告冲突，不覆盖、不清理。不得把源仓当前工作树复制进 Lab。
2. 若 allowlist 文件在冻结基线中已经存在，先读现有实现，只做本包所需的最小增量；测试文件只能追加或定向修改相关用例，不得整文件覆盖或删除现有断言。
3. 只读打开该包列出的已接受 consumer commit 与 IQS facts wire 2.7 锁定输入。不得使用 IQS 未提交/未发布 2.8 变更，不修改或写回 IQS、StockWiki、StockQA、另一个技能仓、company-wiki、用户配置或安装镜像。
4. 保留源技能原有流程。快速扫描数据是可选、只读的事实/关系补充；禁用或调用失败时原流程照常工作。strict、explore、unknown、partial、完整无命中、过期/unsupported 必须分别处理；不得把缺数据解释为没有公司/关系，也不得把线索变成研究结论或改动原评分。
5. 测试使用 fake public CLI、虚构公司/行业和临时目录。不得访问真实 owner root、生产数据库、股票名单、联网搜索或收费模型。只运行新增/受影响测试和目标仓明确要求的包校验；不跑小时级全仓测试。
6. 在交付前由**作者之外的独立 agent**审查最终候选 commit，覆盖真实 diff、接线调用路径、错误/未知/partial处理、旧行为兼容、测试和路径边界。修完所有 findings 后，让 reviewer 对最终 commit 再审并给出 approved；不要求每个小提交重复复核。
7. Lab 本地提交、不 push。交接目录为 `docs/handoff/<PACKAGE-ID>/`，包含 `report.md`、`handoff.json` 和必要测试摘要。`handoff.json` 使用 IQS `docs/implementation/parallel-lanes/handoff.schema.json` 1.0.0；review 必须指向最终 result commit。`status=complete` 仅表示隔离源仓候选完成，不授予真实 owner、G4、生产或金融结论资格。
8. 记录冻结 base/result commit、实际变更路径、输入协议版本与 SHA、逐项测试命令和原始 passed/failed/skipped 数、reviewer/最终审查 commit/findings 修复、网络/费用和临时目录清理、未完成项。若基线或上游契约不满足，返回 `blocked`/`partial` 并说清原因，不伪造完成。
