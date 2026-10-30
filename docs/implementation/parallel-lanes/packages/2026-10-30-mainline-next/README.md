# 2026-10-30：四条互不写入对方目录的下一阶段施工线

四包已编制，**未派发、未实施、未验收**。用户可以现在同时交给四个不同harness；总控不自动启动。不要把上一篇R1的旧待办误当本次仍未验收，也不要重复做原比较/名单组件或108题签收。

| 施工卡 | 唯一可写工作目录 | 交付增量 | 联网 |
|---|---|---|---|
| [TIME-SEMANTICS-30](TIME-SEMANTICS-30.md) | C:/Users/郑曾波/Projects/iqs-time-semantics-lab | 按题义拆分时间语义、可版本化复用策略候选、旧规则差分回归；不改原TTL | 不联网 |
| [ANSWER-AUDIT-30](ANSWER-AUDIT-30.md) | C:/Users/郑曾波/Projects/iqs-answer-audit-lab | 对32份本轮真实回答做来源、数字、主体、时点和评分理由审计 | 仅harness自带公开网页阅读 |
| [IMPORT-PERF-30](IMPORT-PERF-30.md) | C:/Users/郑曾波/Projects/iqs-import-performance-lab | 原入库链剖析、语义等价加速候选、可重复离线基准与故障回归 | 仅本Lab可选loopback |
| [RESULT-TRUST-30](RESULT-TRUST-30.md) | C:/Users/郑曾波/Projects/iqs-result-trust-ui-lab | 在结果中清楚显示资料时点、生成/签收、旧结果、缺口及未知状态的只读UI组件 | 仅本Lab loopback，默认18794 |

四包没有相互开工依赖，不读取其他新Lab的未交付文件。共同依赖只有本批锁定输入；主IQS、StockQA、StockWiki、原UI、共享PWF、8766服务、原数据库/名单/预算均只读。每个Lab在编卡时不存在，开工仍须确认唯一writer。主线的原owner接线、新schema/策略发布、真实付费实验和最终集成只由总控执行。

## 每个harness先读

1. 自己的施工卡；
2. [共同交接与独审规则](handoff-rules.md)；
3. [固定接口与验收边界](interfaces.md)；
4. [输入锁](inputs.lock.json)、[机器可读包目录](manifest.json)；
5. 仅ANSWER包读取[samples.index.json](samples.index.json)列明的本机私有回答副本。

上述链接及卡内完整目录就是独立上下文，不需要历史聊天。不能仅发一个Lab路径而漏掉施工卡。

## 实际基线及还没完成的事

- 原UI：2f1f450；StockWiki：8527bc7；StockQA：0dc799a；IQS：092b1a2，完整40位见锁。
- 三市场各36题已签，精确口径原105成功+真实替代3；旧3failed不改。
- 原8766冷重启的108有效槽不变；A过期刷新、B新cutoff单题均真实入库。B真实第二进程是历史只读恢复、未完成新研究，不是fresh命中。
- 账本累计81 settled HTTP/$1.903319只是基线说明，**不是四包预算**。四包不得使用该账本或原密钥；不得自动补问gen4或扫描215/2000家公司。
- fresh真实正例、金融内容准确性和2000家吞吐未验收。当前24h/min规则保守失效符合实现，不先当作bug；新生成不等于最新资料。
- 原33题入库约19分钟是真实问题线索，不是本Lab基准，不能用不同机器合成测试的秒数冒称生产已提速。

旧SOURCE-TIME/EVIDENCE-TIMELINE/FIN参考包分别做来源案例、时间一致性、参考内容；TIME本包交的是新策略候选+原实现兼容差分，ANSWER本包审的是本轮真实32答，不重做旧案例/第二个评分器。IMPORT不是重复LOAD/CHAOS；RESULT不重复已有比较或名单。

## 只有三个大节点

输入/写根确认 → 小步TDD实现及有意义的单元/集成/端到端验证 → 最终payload的真实不同agent集中全面独审、作者修尽问题后交接。不为每个小函数新增审查门。

## 总控最终接收

每包交到自己Lab的 docs/handoff/<包ID>/handoff.json。采用原handoff 1.0.0，不扩顶层。其他产物见共同规则，业务索引见interfaces.md。

原公开CLI的预检示例（只有总控运行，不是worker执行源仓脚本）：

    python scripts/parallel_handoff_cli.py --input C:/Users/郑曾波/Projects/iqs-time-semantics-lab/docs/handoff/TIME-SEMANTICS-30/handoff.json --package-id TIME-SEMANTICS-30 --catalog docs/implementation/parallel-lanes/packages/2026-10-30-mainline-next/manifest.json --verify-references

另外三包将--input与--package-id替换为表中对应Lab/包ID，catalog不变。CLI exit0只表示其声明范围内的形状/引用预检；不代表来源真实、独审可信、性能提升、生产接通或金融准确。

总控可独立接收PERF/RESULT；TIME与ANSWER的结论由总控合并决策后才可能演进生产时效协议。任何一包迟交都不阻止其他包交接。
