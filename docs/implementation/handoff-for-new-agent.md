# 当前接手说明

更新于2026-11-01。**先读根[当前计划](../../task_plan.md)，再按其唯一Next Step实施。** 本页不另列相互竞争的任务。旧长交接已[原字节归档](archive/pwf-through-2026-10-31/README.md)。

## 从哪里继续

原8766/原UI/StockQA/StockWiki已接通，三市场各36有效题槽、ACK、冷恢复和真实过期刷新均已验；不要重做这些。真实最近扫描单题复用正例本轮也已完成；当前先纠正已知答案质量，之后原200家可靠性、事实F05、TH/IN、全池与配套仍未完成。旧卡中的“待权限/未部署/未ACK/主线暂停”不是现在状态。

新TIME目前只是原结果页只读解释，不授权复用；其identity_revision/可信核查凭证只在采用新多时钟策略时是必需条件。不要先把新凭证体系扩成原缓存和原只读消费者的额外门。原W06兼容链与显式新扫描时钟的真实单题正例已完成；勿重做或改旧日期造fresh。

本次已取消冗余内存preview/旧inspection摘要门、纯缓存的模型准入、只读全历史账复审、自动委托早期重复核查、未知注册国家阻断，以及事实/消费者/小样本配套等待200/2000规模验收的人工依赖。规格1.10.17仍108任务/368场景，规模验收本身没有关闭。源代码、测试和[集中独审](reviews/SIMPLIFY-FRESH-2026-11-01/independent-review.md)已交，不要重造旧门或逐条凭证；变更和实际运行以[本次报告](reviews/SIMPLIFY-FRESH-2026-11-01/report.md)为准。

原预算快照误门已由StockWiki`724f5b7`修复；本地owner policy9已显式采用successful_scan（TTL24h，预算不扩）。原information_as_of/报告期/发布日期不改，新缓存含义只是最近成功联网扫描，可按原执行时间跳过重扫。激活与正反例见本次报告。真实原UI复用已完成，原观察和资料日不变、0新增HTTP/费用，不重做或补凭证。

当前真实批全部三题已补封并完成原ACK2/2；同范围DUPONT02再次准备已cached1、执行包0。见根Next Step和native-cache-reuse.json，不再等IQS22或重启该批。原HTTP JSON digest与final文本digest属于两种对象，分别核验；原owner捕获文件自身不授予scope/恢复权限。IQS11已知FCF跨年问题未金融签收，工程恢复不改变它的资格。

当前现金流纠错仍沿根Next Step，详细状态见[现金流节点报告](reviews/CASHFLOW-CORRECTION-2026-11-01/report.md)。generation5真实单题已返回并原ACK1/1，仍沿用已知错误；不标金融通过、不再重发该请求。实际冻结bank/questions未包含新增逐期提示，下一步先修原UI实际请求的规则/已有原数上下文接线。原历史保持；现已复位普通policy11/1.1，专用refs移除、TTL24h和已登记包保留，不再按临时policy10继续配置。

03:39接续已完成实际provider规则与三个兼容修复：StockQA `76c9431`，IQS本轮shared来源校验只对实际external use附proof；单题/pack载荷10P、原语义20P、原QAEngine23P、原owner compact单例1P/149.11秒，副本清理、0新增收费。接下来继续公共入口，具体复用如下，不另发施工包或小节点审查：

1. 原UI当前仍调用`StockQAbyLLM/main_with_llm.py`，最后走`LLMRunner._run_single_company`的`QAEngine.process_questions`。新增显式共享引擎选择时，应在同一已初始化的`ApprovedRefreshSession`、`QuickScanWorkLifecycle`和预算内调用IQS原API，不另建owner/客户端/账本。原本地`route_providers`与`execution_routes`可精确匹配lifecycle路由取原client；cascade配置热加载时其公开providers/routes会被置空，不能据此新建client。
2. 复用`shared_company_task.create_company_scan_task(..., evidence_board=...)`，不用旧固定12题/10-13实验factory。原数用现有evidence record及原官方URL/真实刊日/期间/单位/摘录；issuer_ref须准确匹配该task的company_ref。先核原subject是否合并范围，不能将合并现金流移给仅法律发行人。已核原数在本机`runs/fresh-quality-2026-10-31/catl-primary-reference.private.json`，不是owner golden或自动金融认证。
3. 默认Python尚找不到`iqs_company_agent_lab`/`iqs_agent_runtime_lab`；公共接线要显式使用已交的两个Lab/src路径，缺依赖/配置变化/错误上下文在收费前明确停止，不回退legacy重问。原company-wiki有活动writer（文档及.githooks），保持只读。
4. 使用原`execute_shared_engine`/`resume_shared_engine`和已有checkpoint，不另造恢复状态机。session/export必须互不嵌套；同一次原工作恢复要保持原task及选中work集合，不能因输出文件换名创建新的付费会话。封存后先`finalize_shared_engine`，再用新增`QAEngine.hydrate_questions`输出原格式；缺CP直接失败，不能裸调用会发问的process_questions。finalize逐题幂等，并非全包单事务。
5. 新engine选择应沿原bundle/config路径及原输入hash冻结，旧bundle继续原方式。当前共享runtime单请求上限16384，且一题comparison按实际pack长度要求原controls.pack_size=1；当前普通UI为pack2/max32768。将来真实新比较须按新已选参数取得原批准，不修改旧grant、不假装降低请求上限是旧授权的静默扩展。思考保持开启。先完成真实调用链的隔离E2E，再以现有第一方上下文做一次有明确变化的真实复核，不盲问。

进一步精简已取消重启后人工inspect前置、读旧job的新配置门、纯缓存预览的确认/job，以及只读轮询中的重复执行预检。恢复/补封/归档按钮表示明确检查动作；真正control仍实时核原owner/预算/进程，未知请求不重发。旧applied可能触发登记，冻结输入完整性检查仍保留，不误删有实际作用的保护。

## 固定对象与运行

|组件|本次核对基线|
|---|---|
|IQS本次起点已推送|`215804dada41148ea79011fbb483e02f9f8d1abe`，本次源码及文档在其后正常提交|
|IQS原接线|`c1ee64fd5a7cd1331e67d7ec7f3a242ff2ffc0b2`|
|IQS测试入口|`e8f184c47221a97f0eb1f0183b55c38d5f835a01` / `f16da24a5d78eb654a4a3e317e827d7e5cfe7bc0`|
|StockQA|`76c9431`正常hooks已通过；实际provider规则及共享接线兼容修复已提交推送，已核HEAD=origin/master|
|StockWiki|`1bde9e0`（含`af2a260`及预算`724f5b7`）已提交，无origin，不新建远端|
|原UI|`d3ec24a`（含`0212c5c`/`d6e0eb8`）已提交，无remote|

实际写前重核当前Git/唯一writer，不因无关HEAD变化重做历史。ANSWER/PERF最终C/M见[已签收口报告](reviews/SUPPORT-CLOSE-2026-10-31/report.md)，TIME/RESULT实际原接线见[报告](reviews/TIME-RESULT-WIRING-2026-10-31/report.md)，不把接线C的历史25文件manifest当当前README/测试字节。

入口`http://127.0.0.1:8766/`；配置`config/dashboard.local.json`；数据`runs/r25-live/owner-workspace`（isolated_research），执行`runs/u25-live/runtime`。配置文件不发布，密钥仅环境变量，不打印。当前doctor只读就绪，不等于新任务已有收费准入。启动方法见[总README](../../README.md)。不杀记忆PID；重启前核端口、真实argv/creationtime、未决任务。UI静态浏览不调用模型。

## 授权、边界和测试

- 用户已给必要后续跨仓修复/独审/正常提交推送授权，不重复问。仍须避开其他writer；特别保留IQS的`docs/implementation/parallel-lanes/packages/2026-10-10/README.md`改动及历史untracked。
- StockQA/StockWiki/原UI各管自己权威状态，不从IQS旁路写数据库，不复制另一套LLM重试器。发布新策略显式版本兼容，旧记录/费用/已收答案保持。
- 不执行历史PWF里的mutation/回执刷新helper。PERF两个旧generator已退役，不重造旧C1或裁清单；PERF优化未装生产且36包更慢。
- 测试按[分层说明](testing.md)和改动范围选择；大产品节点集中独审，不逐helper增门、不重复小时全套。真实金融/收费/规模测试与软件fixture分开。

```powershell
# IQS根：改到时间解释/HTTP时才执行
python -B -m pytest tests/test_dashboard_temporal.py tests/test_dashboard_entity_view_http.py -q -p no:cacheprovider
# 查看当前分层，不执行测试
python -B scripts/run_tests.py all --plan
# 原UI根 C:/Users/郑曾波/Projects/iqs-question-bank-ui-lab：改到可信面板时才执行
python -B -m pytest tests/test_result_trust_host.py -q -p no:cacheprovider
```

测试用自有短TEMP，结束清理自身临时库/副本/进程，保留最小证据；不清他人文件。pytest hook只放行字面IP TCP loopback，不是整进程树沙箱。不得将collect/shape CLI/自报passed替代执行或真实owner golden。

最新减负以规格1.10.18为准：101处逐卡独审/额外凭证已取消，不恢复五阶段逐卡状态流或逐断言证书。内容不变的候选不因本地一小时作废；原样保存配置不核活跃任务；真实变更只核一次；可先交付已封存答案，原检查器省略的题仍算缺口。141项相关测试、72子测试通过，独审遗漏行反例已修复；04:01:44Z原8766已加载，doctor就绪、账本85HTTP/US$1.999868无新增收费。不要以此宣称原UI共享引擎或FCF金融纠错已完成。

尾修另147P：control(inspect)只读原工作、不再跑独立_registered_permissions子进程，不建preview或要求新spend/模型配置；can_start=false、权限not_checked，不是准入。真正start/resume/seal/批次默认仍原检查；1.4/1.5原policy/exposure范围读取没有删除。04:06:54Z原8766已加载尾修，独审无未解问题；两批测试环境均已清理，无新收费。

## 交接完成标准

报告本次改变的功能、准确C/受影响文件、相关测试实际结果、真实模型/搜索费用及剩余边界；提交已完成工作并更新原计划表。历史验收原件不改签，当前入口只留一份状态，不再把同一长段复制进三份PWF。
