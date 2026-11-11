# 九模块未提交与未并线盘点

2026-11-11。**盘点和有把握的清理/小修复并线已完成，剩余源码归拢已写入原9张MC卡。** 这不代表9仓的模块化/TDD已经实现完成。本轮没有新增施工包或回执系统。

用户已授权查明用途后删除无用改动、尽量合并可交付提交；总控与三个只读审计agent逐仓核Git工作树、分支祖先/patch等价和当前文件。审计与操作过程中存在其它writer，时间变化已保留；执行前只复核目标HEAD/路径，不重做全仓审查。

|模块|本轮确认的实际情况|已做/下一承接|
|---|---|---|
|IQS|master@5c8ba43，原28项tracked WIP；C38名单authority确实未并，其余多数祖先/摘取/重做|保留WIP；MC-IQS按公开owner版本归拢，承接C38消费者|
|StockQA|canonical77项tracked，1.8候选87项；两条旧G2分支已合|源码保留；MC-QA收成一个自包含实现，不继续两根分叉|
|Company Agent|API2.3已在master@793bfbc；无侧枝/remote|删一份生成board；MC-CA修测试输出污染并验证已有封装|
|Runtime|实际主线codex/agent-run-02，无main/master/remote；canonical与候选各有应保留的修改|MC-RT合并launcher独有改动与候选公开API，移出历史pin计数门|
|StockWiki|源码tracked clean，7项运行库/日志保留；C38@4532b0d还有实质未合功能|MC-SW先名单事务/公开接口，再归拢其余已交付能力；不迁移真实库|
|原UI|master@47d5354，无源码WIP；两份generated JSON变更|保留数据快照；MC-UI按C5改公开消费/启动，不误清用户结果|
|Dashboard|旧分支多数已吸收；3个漏合提交有明确当前缺口|**已摘取并快进main@0addea2**；29项测试和独立diff审查通过，6项功能WIP当时哈希不变；另一writer随后提交2049356，当前tracked clean|
|Theme|2项tracked源码/测试+1份新test harness；无待并分支/remote|删3份pyc；MC-TH三文件成套承接|
|Industry|tracked clean，但1份新边界测试未提交；旧report分支都已合|MC-IN保留并审查测试，不把tracked clean写成无WIP|

## 实际完成的操作

1. 删除71个已确认pytest临时目录：**20,728个物理文件、1,526,513,329字节**。包括IQS根52个、QA候选内10个、Runtime候选内9个。所有候选根/有效源码保留。另删除Theme三pyc、CA合成board、QA空stderr、IQS旧临时路径文本，共6个文件354,258字节；总计20,734文件，约1.53 GB（1.42 GiB）。精确目录见[清理清单](cleanup.md)。
2. Dashboard原`5d2a761/4b30e1d/8e3231c`在隔离main工作树摘取为`5a16ca7/c56e9ce/0addea2`。保留流式和buffered两个测试，修language数组与reconcile的配置。两组29项通过、非作者逐项核原diff通过。已ff主线，未包含其它WIP。
3. 9张原施工卡都增加本轮入场清单：真实基线、需保留文件、应并/不重并的分支、依赖顺序和针对性测试。没有用一批新卡替代旧卡。

## 收尾观察到的并行提交

20:21:44 UTC，Dashboard另一writer提交`20493562f86b1351d97bc164bbc254efacddacdf`（原6项有效WIP及其README，共7文件），当前tracked clean。已核本轮`0addea2`是真祖先；未跟踪probe/个人记忆/四个SQLite保持。MC-DASH基线已更新为2049356，要求继续验证该现有提交，不能重复实现或宣称本轮29项代验了它。其它八仓HEAD未改变；IQS的新增文档提交另行记录。全表是本次读取时间的快照，不锁住后续正常提交。

## 不能混作已完成的事项

- **未并线与未推送不同。** IQS bb20529等已在本地主线，但QA/RT依赖尚未收齐；Dashboard原19项本地提交、本轮3项和另一writer后续2049356合计23项尚未统一发布。不能为推几份盘点文档而意外发布尚未完整验证的源码组合。原授权继续有效，按各卡既有发布步骤处理，无需再问权限。
- **真待并线：StockWiki C38 + IQS C38。** Dashboard消费者已在main，供应者不能继续只留旧发布worktree。MC-SW→MC-IQS→Dashboard公开名单回放的顺序已明确，原C1是同一补丁来源，不重复合。
- **真待归拢：QA/Runtime有效WIP。** 两份独立.git候选不可删；旧快照中QA初版/v2还有25个内容差异作有限参考。Runtime canonical的launcher修复不能被候选覆盖。
- SQLite、原答、研究报告、历史验收证据、harness锁、个人配置以及用途未判定的`nul`都保留。旧partial checkout数千个D不并成源码删除；含junction的测试目录不盲删。

## 报告与核验范围

- [IQS源码、分支与工作树](iqs.md)
- [StockQA、Company Agent、Runtime完整路径与快照对照](execution.md)
- [StockWiki、Theme、Industry逐分支/工作树清单](store-consumers.md)
- [原UI、Dashboard及本轮小修复独审](ui.md)

原审计报告保留各自读到的时间；总控后续实际操作以本页和各报告“总控处理结果”为准。本轮是改动归属和并线审查，未对保留的全部WIP运行功能测试，也未宣称金融、规模、部署或模块化完成。

独立终核：[review.md](review.md) **PASS**。已核九模块承接、实际清理、合并日志和并行提交时点；三项表述歧义已修正，无开放发现。该结论不代签保留的源码WIP或后续2049356的产品质量。
