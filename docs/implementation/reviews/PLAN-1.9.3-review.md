# 实施计划 1.9.3 全局复核与收口

日期：2026-09-26  
范围：invest-quick-scan 本仓的总体实施计划、验收依赖与归属、可组合演进/向后兼容规格、跨仓职责、运行边界、测试与恢复方案。此文是计划复核，不是产品功能验收。

## 结论

复核后，1.9.3计划的核心设计具备可执行的分仓顺序与明确的本地/集成验收边界，尤其补清了组件资格变更和两个独立数据库之间的付费派发竞态。本轮还发现并统一了若干仍沿用旧单阶段permit语义的活跃实施文档，并增加防止这些文档再次漂移的回归测试。

清单当前为102张任务卡、322个验收场景、50条固定约束，最终放行门为G6。**这些数字描述计划覆盖率，不表示对应产品能力已实现。**322个场景仍为`specified_not_executed`；StockQA/StockWiki跨仓生产链与X10/E2E-06真实联网验收均未因本轮而通过。

## 本轮核对并固定的设计

| 领域 | 复核后的规则 | 实施边界/失败行为 |
|---|---|---|
| 任务与验收归属 | 每个case唯一`owner_task`；每张任务卡至少有一个自己能完成的本地case。后续任务只能在依赖闭包中把前置case作为回归引用。完整跨仓case列明`requires_tasks`。 | 前置卡不能因尚未实现的UI、持久化、导入或live能力而无法关闭，也不能用局部测试冒充端到端通过。校验器拒绝无主case、前向引用、依赖缺口、孤儿case和循环依赖。 |
| 模块组合 | 题包、路由、答案解释、评分尺、事实本体/词表、筛选lens、刷新策略、provider能力和查询投影分别由唯一owner发布；一次扫描以不可变`ScanRecipe/RunManifest`锁定具体release/hash。 | 新模块显式声明依赖、排除、适用条件、重复构念优先级、题目预算与兼容范围。冲突或分类低置信度时暂停为`needs_review`；LLM不能自行改变题义、启用新模块或绕开关键风险门。 |
| 演进与兼容 | release内容不可变，语义变化发布新release；兼容按历史读取、派生重建、新写入、付费派发和迁移等动作分别判定。影响分析输出精确受影响字段。 | 新题/新字段只补缺口；分数权重或lens变化只重算派生视图，不调用模型。答案/身份/题义变更只使可证明受影响的记录不可比或重问；影响图不全时`blocked/needs_review`，不得全池重问。 |
| 纵向与横向比较 | 原始回答/观察、信息日期、问题与路由版本、模型/provider和评分方法均可追溯；核心观察不覆写。周期低谷样本与仍存竞争优势、恢复条件、风险单独保留。 | 不把低谷时的低分抬高，也不让质量白名单成为唯一入口；跨方法、期间、作用层或模型口径不同的结果标为不可比，恢复候选可单独筛选。 |
| 轻资产与责任分工 | 本仓定义题义/契约，StockQA唯一执行模型/搜索/attempt/费用，StockWiki唯一拥有公司身份/名单/观察库/结果查询；company-wiki只可选关联深研身份。 | 不下载或保存公司文档、网页正文、完整prompt或HTTP正文；来源仅保留必要URL/标题/日期/短依据。外仓写入仍按各自授权实施。 |
| 两仓派发授权 | StockQA先持久化`send_intent_prepared`，再调用W16 `consume_dispatch_permit`。StockWiki在单一owner事务重验active指针、组件资格revision和work范围，原子消费permit并持久写入`dispatch_commit`。 | 只有匹配的耐久commit回执授权一次provider POST。consume前资格变化/崩溃必须POST=0且旧permit不可重放；commit后若不能证明未发送则`outcome_unknown`，仅对账，不fallback、不创建新attempt。明确未发送或对账后的允许终态才可用新单调attempt并重新核验预算/资格。 |
| 版本、回退与恢复 | 组件单调lifecycle与workspace/profile的active ReleaseSet指针分开；安装和实载hash分层核验。旧冻结attempt按原recipe安全结算。 | candidate只预览；指针不变但组件资格revision变化也必须CAS失败。deprecated/retired release不因回退静默复活；不兼容新版本不得拦截可安全结算的旧请求。 |
| UI与研究消费者 | 页面展示公司、证券/挂牌、时间、模型、模块/评分方法、缺口与可比性；主题链/行业研究按能力协商读同一权威查询投影。 | 页面不重复算分、不发模型请求、不维护第二套可写库；能力缺失明确返回`unavailable`，不能用空列表冒充无结果。 |

## 本轮发现及处置

1. 一个刚加入的计划测试把JSON的`given`字符串当成字符串数组拼接，造成字符间插入空格而误报。现改为直接验证字符串内容，没有弱化业务预期。
2. 交叉阅读发现全局任务边界、启动流程、跨项目交付、测试策略仍残留“permit与send_intent一起耐久提交”或相反顺序的旧写法。已统一为`send_intent_prepared → consume_dispatch_permit/dispatch_commit → 一次POST`，并明确commit后不确定结果的attempt不可重试。
3. 测试策略仍写旧范围`EVO-01—78 / LLM-13—17`。已更新为当前计划的`EVO-01—82 / LLM-13—18`，并把四个崩溃窗口、POST计数和permit重放预期写清。
4. 增加计划回归测试，读取7份当前权威实施文档，要求均声明`consume_dispatch_permit`和`dispatch_commit`，阻止单阶段授权措辞回归。

历史审查报告保留各自审查时点与原始结论；本报告是当前计划权威的1.9.3复核记录，不把历史文本改写成当时已具备的新协议。

## 验证和边界

- `python -X utf8 scripts/implementation_plan.py validate`：通过，报告102 tasks、322 acceptance cases、G6，且明确`product_tests_executed=false`。
- `python -X utf8 -m unittest discover -s tests -p test_implementation_plan.py -v`：68项计划包测试通过；包含验收case owner/依赖闭包、向后兼容、派发协议跨文档一致性等回归。
- `git diff --check`：退出码0；Git输出现存LF/CRLF风格提示，不是空白错误。
- 本轮没有调用外部LLM/搜索API，没有运行真实数据E2E，没有修改StockQA、StockWiki、company-wiki或其他外仓。

## 尚待实施而非计划复核阻塞

- 102项任务及其跨仓能力仍须按owner、依赖、阶段门逐卡实现和审查。计划测试不是StockQA/StockWiki产品测试。
- X10/E2E-06需等统一入口、预算和隔离清理器就绪后按live门执行；目前未运行、未通过。
- StockWiki超出此前已授权的W01文件范围的任何写入，仍需另行授权；StockQA写入按已有全仓授权继续时仍须事先报备拟改文件和用途。
- 真实双进程/数据库/网络传输组合须在后续owner任务的临时环境中验证；本轮只检查规格闭合与计划自检。

按用户明确要求，本轮计划审查收口后暂停，不继续实施功能卡。
