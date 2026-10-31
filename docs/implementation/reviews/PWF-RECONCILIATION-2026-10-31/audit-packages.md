# 外包交付与跨仓关口只读对账

核对基线：本仓已推送 d2c575f；本报告只读文档/已签证据，没有运行测试、源码、收费调用、数据库或新施工卡。下列“未完成”指未见正式完成证据，不把历史日志里的等待状态重算为新故障。

## 当前能由正式证据支持的状态

| 范围 | 当前判定 | 依据 |
|---|---|---|
| 三市场真实评分、入库 | 已完成小样本工程闭环，三公司各36有效槽 | task_plan.md 10/30 15:57与17:00；reviews/UI-INTEGRATION-30-2026-10-30/native-three-market-recovery/cold-independent-final-review.json：exact108 IDs与ACK元数据一致，原失败3保留；是105原成功+3真实替代，不是原108全部成功 |
| 原UI冷重启、持久化恢复 | 已独审通过 | 同cold-independent-final-review.json；79HTTP/$1.865393在该历史冷节点未变，非最新实时余额 |
| 过期后正常刷新 | 已通过真实单题A/B | native-ttl-and-coverage/README.md；A新gen2 ACK1/1，B新gen3 ACK1/1，共追加2HTTP；截止该节点81 settled/$1.903319/0在途 |
| 有效期内真实fresh复用 | 未完成 | 同README：A信息日08-12，B信息日04-09，真实cutoff30仍应dispatch gen4、reuse=null。B第二进程恢复API0但requested_scope_completed=false，是历史恢复，不是新鲜结果命中 |
| 共享引擎真实摘要与同检查点封存 | 单题已通过，后续小样本入库/恢复也已通过 | shared-engine-status-2026-10-25.md单题历史；10/30三市场证据是其后增量。不得继续称“下一步首次ACK” |
| TIME/RESULT | 候选签收且已接原8766只读视图 | TIME-RESULT-WIRING-2026-10-31/report.md、independent/final.json；112 clock-only/1旧release未绑定；不授予fresh复用许可 |
| ANSWER-AUDIT-30 | Lab范围已关闭 | SUPPORT-CLOSE-2026-10-31/acceptance-status.json：C2eb59d3/M65973fb；51源35可读16不可读，63外部命题22支持25部分支持16不可评。完成审计覆盖≠金融全对 |
| IMPORT-PERF-30 | Lab范围已关闭，候选未装生产 | 同acceptance-status.json：C99c350b/Mf581dcf；68不同用例与24测量，36包baseline/candidate=0.843，即候选更慢；未解决全池吞吐 |
| W11 | 原范围定向刷新能力已经交付且实用 | 2026-10-07/TH-IMPL-01.md当时已明确W11有交付；10/30真实单题query→preview→admission→UI→ACK是更晚端到端证据。但完整任务case-map签收不应只凭存在函数重建 |
| C06/W15软件查询链 | 已交付；不再是不存在query/capabilities | task_plan.md Phase113步骤4打勾、10/11 checkpoint26，query2.0–2.5/authority3/context2；真实owner serializer/query/capabilities输出已交付，不能沿用10/07旧W09-only描述 |
| F05 strict/explore关系检索 | 尚无正式通过证据，事实主线仍需完成 | tasks.json F05依赖F03/F04/W09/V07，需关系方向/分部/商业化/时点/证据过滤及严格/探索正反例。C06普通查询与事实题库61题不等于这一关系消费链完成 |
| L03/G3 | 200家公司可靠性试点与扩容关口仍未完成 | tasks.json L03/G3定义；没看到正式G3签收。三家108槽/合成36包/组件压力测试不替代200家真实试点 |
| L02/G2 | G2已在本地受限范围签收；原60+20配方未完成 | reviews/G2/G2-review-2026-10-05.md最终r2=`verified_for_local_gate_scope`，允许评分闭环/校准维度进入200家，不表态L03能立即跑；MiMo仅6家182题，repeat顺延、cohort n≤2。原60+20设计仍是未完成范围，不可改称完整60家通过，也不可抹掉已有G2签收 |
| TH-IMPL-01 / IN-IMPL-01 | 预研已签，正式消费者集成仍待F05/G3等原前置 | 2026-10-07两施工卡明确共同开工门；未发现后来正式实施签收，不能因为当前UI可用转绿。已有全局必要写授权不应再反复说等权限 |
| 约2000家全池 | 未开始，也不应总控自定名单 | tasks.json O01/O03及根PWF最新215池，按用户给定/认可池扩容；2000是目标容量，不是当前池规模或已扫描数量 |

## 明确过时的面向当前入口

1. `parallel-lanes/packages/STATUS-BOARD.md`标题和开头仍为10/25，声称generation2未成功检查点、等待lease；与10/30已108有效槽及10/31接线冲突。应换当前摘要，原表改历史、保留证据。
2. `shared-engine-status-2026-10-25.md`自称“当前”，图止于单题/下一步多题和ACK；它只应是10/25历史快照。更新入口或加明确已被10/30与10/31取代。
3. `status-2026-10-18.md`与`reviews/roster-status-2026-10-18.md`仍容易被当前说明链接当实时数字；两个当日文件verified计数本身不同（209与2），且非同口径/工作区，不能合并成当前唯一身份数。保留历史，标来源/工作区和已被当前状态取代，别据它重开身份研究或Storage rights权限门。
4. `parallel-lanes/packages/2026-10-07/README.md`早晚“可开工/六阻断”仅旧基线，应将页首标历史；不能重做QA-NET/SW-READY，也不能沿用W09-only/facts=false描述否认已交付C06查询。但G3/F05未闭是真实剩余，不能整张卡标完成。
5. `cross-project-delivery.md`“任务细节与依赖唯一来源tasks.json”成立于计划规格，不是当前实施状态；其theme/industry `local-skills`作为源目录已被10/07新卡明确改为Projects独立源仓（local-skills是镜像）。应区分计划规格与最新执行/验收，修正当前owner路径。
6. 旧`OUTSOURCE-ALL-2026-10-31/acceptance-status.json`两partial是20:28历史记录；23:01 SUPPORT-CLOSE与最终独审已修。应加上层当前链接或索引，不改写旧独审/immutable证据JSON去伪装旧轮已通过。

## G2/G3与消费者的精确边界补记

- `reviews/G2/G2-review-2026-10-05.md`不是60家全验收；其r2真实签收限评分闭环校准局部门。MiMo6家完整产出未损；MiniMax旧组5家151题中000672原1.3MB误被审查summarize覆盖，只剩4家120题可原始复算，旧聚合保留而不造正文。当前不能拿这一损失要求重跑全部旧组，也不能把该组用于跨模型准确率比较。
- 当前T01/T02最小消费接口就是原公开能力/覆盖→search→固定query/snapshot分页→batch get_profiles、原subject/listing/field/release/model/time/coverage元数据；可选request_refresh只展示原preview与后续用户入口，不从消费者写SQLite或自己调LLM。F05还需实际严格/探索关系状态、词表版本、可解释命中及owner真实golden。两卡及`tasks.json`原定义未要求“每条结果须新型可信核查receipt才允许只读显示”；不能把后来fresh动态复用的receipt设计加成所有原始只读消费者的前置。
- C06/W15原公开serializer/query/capabilities交付存在，不应重造。F05/G3仍开放是既定扩容/事实门，不代表这批已交软件无用或“所有数据均无法读取”。

## 为什么外包很多仍未全完（证据支持的原因）

- 卡完成的分母经常是独立Lab组件、测试工具、参考案例、研究报告或候选方案，不是原部署里的端到端功能。最近四包的三层尤其清楚：Lab通过→总控接原代码→真实UI验收；PERF研究结果有效但实测负收益，不能算优化已上线。
- 主线串行集成是瓶颈：原服务/原StockQA/StockWiki共享状态、费用与原工作的恢复，不能让不同Lab并发改这些真实状态。10/25单题后至10/30三市场确有多个原生接续、来源与ACK根因修复；大量组件绿色没有替代这一链。
- 质量门确实发现了真问题。ANSWER的63外部命题并非全支持；源可读性不足、年份/公司归属问题、模型时点字段过旧，不能因JSON和测试通过宣布评分可用于全池白名单。
- 多次返工/版本交接偏差和叠加审查消耗了时间。BASIC生产扩张6根因、UI比较名单R1/R2、四包后补安全/审计闭环都有正式RED/GREEN；根PWF重复保留多个“当前唯一下一步”增加后手重读/重开已完成项风险。
- 总目标已从最初“问卷快扫”扩至跨项目唯一身份、关系事实检索、组合演进、真实费用/缓存对照、安装/升级回退、两个深研消费者和200/2000扩容。应清楚分“可用小样本版”和“全目标完成”，不能把二者混成永远差最后一步。

## 建议收敛（不擅自变更既定完成门）

1. 当前可用版：已能名单/题库/比较/三市场真实评分与入库、冷恢复、日期解释。当前发布说明明确“研究工具，未证金融准确率、未全池吞吐”，不要再说整个引擎未接通。
2. 下一真实产品缺口：将信息期间/披露日/核查覆盖/结论时效分清并形成原owner可验证字段，补一个真实fresh复用正例；并把已发现的金融critical错误处理成可验证纠错/重问策略。不得用新导入时刻或放大TTL造正例。
3. 接着事实生产/关系F05→两消费者TH/IN→稳定批量/200试点/G3→用户认可池逐步扩容及配套安装/发布收口。原卡把G3作为TH/IN前置，但F05技术依赖本身不依赖200家数据；若要调整这一串行排程，应由总控明确改计划，不暗中称G3已关。
4. 性能进一步候选、更多金融参考公司、更多打包策略对照可后置，不应每交一批支撑Lab就让已完成主链重开；不再为小节点增加审查。最终只在产品里程碑集中验收。

包数量：本报告不报“所有包通过率”。10/31原盘点55个catalog ID、50个直达handoff只是历史索引；嵌套R1/R2和同卡多仓、研究范围不能与上线功能一一对应，不能把它当55个新完成功能。
