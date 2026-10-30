# TIME-SEMANTICS-30｜按题义演进信息时点与复用策略，保留旧规则

唯一工作目录：C:/Users/郑曾波/Projects/iqs-time-semantics-lab
分支：codex/time-semantics-30。本地Python包：iqs_time_semantics。
只读总控入口：C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-30-mainline-next/README.md。
先读同目录handoff-rules.md、interfaces.md、inputs.lock.json及manifest.json中本包条目；这些是完整独立上下文。

## 问题与范围

原规则取min(observed_at+TTL, information_as_of+TTL)，保守地避免“重新导入就变新”。本轮A生成于10月30日而info08-12，B新cutoff30而info04-09，均stale；这符合原契约，**不要修成导入时刻续命**。但稳态判断/财务期间/披露时间/真实复核混一字段，会给2000公司反复重问。

本包实现一个**可组合、可版本化、兼容旧数据的策略候选与离线解释器**，不改StockWiki/StockQA/IQS生产schema或TTL，不迁移库，不造实际verified_at/owner验证回执。样本元数据可读samples.index；不得读私有回答正文或原数据库。

## 应交成果

1. 逐问题覆盖冻结全部评分与信息题，来自真实catalog/facts及模块声明；稳定ID不改，数量动态派生。按知识节奏与组合依赖分类，混合题拆必要时钟，不能以唯一“今天”代表价格/报告期/来源发布。
2. 提出metric_period、evidence_published_at、fact_valid_as_of、searched_at、verified_at的明确意义/精度/可信来源；特别说明“查无更新”需什么真实覆盖回执，空搜索/模型自称/网页mtime不算。
3. 按interfaces.md实现纯函数assess_reuse、catalog/casebook/schema和实际可运行离线CLI。默认legacy路径与冻结原_matching_meta实际实现差分一致；new candidate需显式policy版本选择，旧数据缺核查证据继续保守，不自动变fresh。
4. 可按field/题族组合策略，显式处理身份/主体revision、证券/市场、口径、模型/provider、题义/模块版本、cutoff、事件失效、来源撤回/更正、unknown日期与缺覆盖。不能用当前模型判断覆盖旧模型的历史答。
5. max_age是有依据的提案，不以“设长些即可缓存”代替分析；拿不准保留null并说明所需实验/owner裁决。新正例合成并标记，不能宣称取得真实fresh正例。
6. integration/temporal-evolution.md列最小原仓修改点、版本协商/旧读者行为/渐进切换/回滚、如何使新旧规则并存而不改旧观察；不得新建owner、队列、时间账本或复制既有时间审计工具。

## TDD与验收重点

- 单元：UTC边界、date-only/时区/缺精度、未来信息超过cutoff、非法/bool/重复键/NaN、未知策略版本、误把观察/导入当验证、价格新但财务过期、原核查receipt缺/过期/撤回或scope错、事件触发、null保守。
- 集成：在本Lab固定源码副本中调用原_matching_meta/相关时效函数做legacy差分；不是自己再实现一份当oracle。重用原相关tests的合成helpers，实际文件/hash记consumed-inputs。
- E2E：本Lab公开CLI读严格JSON→选显式策略→产出schema合法解释及完整ID覆盖统计→再次读旧版本仍保守；未知版本/不兼容输入必须非零且不写旧输入。
- 至少包含A/B日期元数据的明确合成边界再现；不是把真实资料日期改成今天制造正例。不得访问8766或付费模型。

先有效RED→实现GREEN→最终不同agent集中全面独审；修尽后才交接。无须每小步单独审查。产物/真实调用/测试/清理/提交分层见共同规则。

## 交接

docs/handoff/TIME-SEMANTICS-30/handoff.json，原handoff1.0.0/lane iqs，业务文件按interfaces.md。
独审特别核查：有没有给旧观察补日期、用LLM自报当验证、把candidate当已发布生产、漏题ID、把新策略正例冒原owner golden。任何此类问题修复后复审。
