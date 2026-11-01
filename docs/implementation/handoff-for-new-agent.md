# 当前接手说明

更新于2026-11-01。**先读根[当前计划](../../task_plan.md)，再按其唯一Next Step实施。** 本页不另列相互竞争的任务。旧长交接已[原字节归档](archive/pwf-through-2026-10-31/README.md)。

## 从哪里继续

原8766/原UI/StockQA/StockWiki已接通，三市场各36有效题槽、ACK、冷恢复和真实过期刷新均已验；不要重做这些。真实最近扫描单题复用正例本轮也已完成；当前先纠正已知答案质量，之后原200家可靠性、事实F05、TH/IN、全池与配套仍未完成。旧卡中的“待权限/未部署/未ACK/主线暂停”不是现在状态。

新TIME保留原结果页只读解释，不授权复用；取消另建独立核查凭证签发/续期系统，不再是必做计划。已有核查元数据仍可读，缺失不阻塞原扫描、入库、缓存或消费者；时效改进沿原字段/事件/成功搜索时间规则。原W06兼容链与显式新扫描时钟的真实单题正例已完成；勿重做或改旧日期造fresh。

本次已取消冗余内存preview/旧inspection摘要门、纯缓存的模型准入、只读全历史账复审、自动委托早期重复核查、未知注册国家阻断，以及事实/消费者/小样本配套等待200/2000规模验收的人工依赖。此前1.10.17解除串行依赖；当前规格1.10.19为107任务/359场景，规模验收本身没有关闭。源代码、测试和[集中独审](reviews/SIMPLIFY-FRESH-2026-11-01/independent-review.md)已交，不要重造旧门或逐条凭证；变更和实际运行以[本次报告](reviews/SIMPLIFY-FRESH-2026-11-01/report.md)为准。

原预算快照误门已由StockWiki`724f5b7`修复；本地owner policy9已显式采用successful_scan（TTL24h，预算不扩）。原information_as_of/报告期/发布日期不改，新缓存含义只是最近成功联网扫描，可按原执行时间跳过重扫。激活与正反例见本次报告。真实原UI复用已完成，原观察和资料日不变、0新增HTTP/费用，不重做或补凭证。

当前真实批全部三题已补封并完成原ACK2/2；同范围DUPONT02再次准备已cached1、执行包0。见根Next Step和native-cache-reuse.json，不再等IQS22或重启该批。原HTTP JSON digest与final文本digest属于两种对象，分别核验；原owner捕获文件自身不授予scope/恢复权限。IQS11已知FCF跨年问题未金融签收，工程恢复不改变它的资格。

当前现金流纠错仍沿根Next Step，详细状态见[现金流节点报告](reviews/CASHFLOW-CORRECTION-2026-11-01/report.md)。generation5真实单题已返回并原ACK1/1，仍沿用已知错误；不标金融通过、不再重发该请求。实际冻结bank/questions未包含新增逐期提示，实际请求规则/原数上下文的可选公共接线现已实现，下一步从原UI进行实际复核。原历史保持；现已复位普通policy11/1.1，专用refs移除、TTL24h和已登记包保留，不再按临时policy10继续配置。

03:39基础修复已保留。其后的公共接线现已由StockQA `07db665`（含`1825a14`）与原runtime桥`cb00e4e`实现，不要重新做下面的接线；源码阅读路径和实际边界如下：

1. 原设置`prepare.shared_company_config`→候选冻结配置→原CLI `--shared-company-config`→`LLMRunner._run_single_company.process_selected_questions`→新`src/utils/quick_scan_shared_company.py`。在同一ApprovedRefreshSession、lifecycle与预算中，从原route_providers/execution_routes精确取现成client；未选择此配置仍走原process_questions。
2. 新入口只构造一次create_company_scan_task，用同一公开native_company_projection取得证据引用。evidence_boards按原完整subject_ref匹配，短record不改源数字、时间、范围；原数在本机`runs/fresh-quality-2026-10-31/catl-primary-reference.private.json`。写seed前重核原subject是否合并范围和真实来源；该文件不是owner golden或金融认证。
3. 配置指定IQS、Company Lab与Runtime Lab根，动态加载原包并核模块位置。新native题包委托原send_search_request，原permit同时保存搜索回执与公开输出；默认工具会话/原external保持。当前native MiMo或原external单题；共享跨模型顺位降级未完成，不能冒称已复用cascade。
4. 原execute/resume/checkpoint保持，task身份来自原confirmation/题目，与UI输出文件名无关。候选export-NNNN完整后才rename发布export，残缺candidate保留并按原CP恢复；finalize后仅hydrate_questions输出原格式，缺CP不回退重问。finalize逐题幂等，不是全包单事务。
5. 控制沿原bundle与输入hash；共享单请求上限16384，一题comparison须实际pack1、思考开启。普通UI当前pack2/max32768，为新scope明确设置，不改旧grant。基础软件E2E1P/536.71秒先于尾修；尾修后SDK/配置/原CLI67P/4.75秒、独审通过，两套环境全清理、0新收费，未重跑长例。

**先完成已在运行的原owner带provided-only来源的scored软件正例，再做原UI真实复核，不重复实现上述接线。** 前例N/A没有覆盖这个保存缺口；StockQA `8791c0e`已沿原intent/attempt贯通provided来源，原vendor回执不变；runtime `f58fdb1`修复显式one_shot profile删除空tool_results造成的动态hash偏差。前两次长例仍记录失败，修后结果以根progress增量为准，不能用已有软件结果代签金融准确性。 精确源为IQS_11 generation5 `WORK_df168ba95e824103ad4cf3678c88c638`（delivered但FCF错误）；用原comparison准确后继，不伪作失败重试。先核原主体、配置/账本及官方同表原数，再配置短evidence和新pack1/max≤16384，从原UI准备/启动一次有明确变化的复核。核2024/2025各自OCF−购建长期资产现金，原ACK、旧答保留和0HTTP复用；若仍错，查实际已发上下文/证据，不盲重问或择高分。company-wiki有活动writer，继续只读。共享模式尚未在原UI真实激活，软件通过不替代此验收。

进一步精简已取消重启后人工inspect前置、读旧job的新配置门、纯缓存预览的确认/job，以及只读轮询中的重复执行预检。恢复/补封/归档按钮表示明确检查动作；真正control仍实时核原owner/预算/进程，未知请求不重发。旧applied可能触发登记，冻结输入完整性检查仍保留，不误删有实际作用的保护。


本轮进一步减负的当前规则（规格1.10.19，107任务/359场景/52约束）：不要重建Q15或W16的第二派发许可证、consume/dispatch_commit、组件资格审批或active全局ReleaseSet启动门。V16只版本元数据、V17只影响分析、W16只原owner字段应用，收费/防重仍由原StockQA管理；停新派发后升级，不新增无停机热切控制面。ExecutionGateway执行preview不再保存票据，旧preview_id兼容忽略；查看旧工作不要求新扫描输入。已取消的是重复机制，不是原预算/身份/未知发送保护和真实规模/事实/消费者/安装目标。

## 固定对象与运行

|组件|本次核对基线|
|---|---|
|IQS当前实现已推送|`2970499`，含可选共享接线、runtime减负和1.10.19规范；后续PWF记录单独提交|
|IQS原接线|`c1ee64fd5a7cd1331e67d7ec7f3a242ff2ffc0b2`|
|IQS测试入口|`e8f184c47221a97f0eb1f0183b55c38d5f835a01` / `f16da24a5d78eb654a4a3e317e827d7e5cfe7bc0`|
|StockQA|`8791c0e`正常hooks提交，含provided来源贯通；此前`07db665`已推，最新远端状态见根progress|
|原Runtime Lab|`f58fdb1`已本地提交（codex/agent-run-02），无远端，不新建origin|
|StockWiki|`1bde9e0`（含`af2a260`及预算`724f5b7`）已提交，无origin，不新建远端|
|原UI|`d3ec24a`（含`0212c5c`/`d6e0eb8`）已提交，无remote|

原8766已于2026-11-01T05:19:09Z加载上述精简，launcher29892/服务15444；这只是定位线索，任何进程控制仍核实际身份。原配置保持、shared模式未激活，doctor就绪且新增HTTP/费用0。

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


第二轮减负已实施：自动交付同操作只预览一次；新交付目标不含未来扫描参数，原UI同目标partial可修改这些设置，原包/状态目录变化仍拒；旧任务保持原算法匹配，不伪造迁移。TIME只作日期解释，不重建核查凭证或第二套缓存许可。测试不再全仓快照或逐文件hash清理；普通临时目录/finally即可。历史strict夹具与旧元数据只读兼容；这些精简不改变原StockQA预算、未知请求防重、身份与ACK。
