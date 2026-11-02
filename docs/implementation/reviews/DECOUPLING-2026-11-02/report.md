# 模块解耦核查

日期：2026-11-02。结论：**职责划分已经建立，尚未充分解耦。** 当前不是一团无边界代码，也不是可以分别升级而互不影响的组件组合。剩余耦合已有可复现的使用影响，主要集中在公共结果兼容、服务锁、启动故障范围及历史恢复对当前实现的依赖。

本轮只做核查、离线反例和文档对齐，没有实施产品重构，没有修改部署、公司名单、真实回答、数据库或外仓源码，没有调用收费 API。此前真实扫描、保存/ACK和CI通过结论保持原范围；它们不等于架构已完全解耦。

## 范围与方法

主控审题库、组合、路由、评分、契约及历史资源；三名独立 agent 分别审核心执行/恢复、跨仓接口、UI/产品服务。检查当前实际源码和调用路径，区分生产、研究兼容与归档，不把归档副本或旧实验入口算作现行生产依赖。

核查基线：

| 仓库 | HEAD | 限制 |
|---|---|---|
| invest-quick-scan | `d4f9f24565e575f3c7a99198890f803202136266` | 本轮仅文档/忽略目录探针；原2026-10-10施工包README改动保留 |
| StockQAbyLLM | `0154726465a427f7b6b7e5f726bf5833841f73a7` | 跟踪文件干净；审公开输出/装配边界 |
| StockWiki | `f52f257d4343f9a785e5a338088a789393db7357` | 另有三个narrative/source-reader文件由其他writer改动，本轮未碰；不声称全面审完StockWiki内部 |
| UI Lab | `fa7ceb6e3218d3faa2229a4d0042a49ba22ea176` | 实际原服务使用的UI源码 |
| Company Agent Lab | `639582ad4b8a0e33271c9595f449ffb8cc90bd01` | 审IQS调用的运行/恢复接口 |
| Runtime Lab | `5839ef4c4f3ec66c0994fb0531009d227631294d` | 审原owner桥接边界 |

CodeGraph先提供结构导航；当前索引scripts仅93文件且context混入历史副本，故对已定位生产目录读取当前源码。当前scripts顶层123个Python文件、194条不同的内部静态import边，包含函数内静态import，无非平凡强连通分量。此统计不包括importlib、内嵌子进程脚本或运行时调用，**不等于全系统无循环或低耦合**。

调用扇出较高的是query_contract_cli(12)、question_sets(9)、standard_answers(8)；扇入较高的是module_contract(24)、query_contract(12)。契约被多处使用属于合理共享，文件长和引用多均不是单独判缺陷的依据。没有为了证明解耦运行小时级全套。

## 已形成的有效边界

| 模块边界 | 当前判断 |
|---|---|
| 题库/选择/提示词/标准答案 | 已拆出question_library、question_selection、question_prompts、question_manifest；互不反向调用UI，CLI不再是标准答案的底层依赖 |
| 路由、评分与计算契约 | 主要是确定性数据处理，不自行调用模型、搜索或生产数据库；题数从发布题库派生，不再依赖24题上限 |
| HTTP与产品操作 | dashboard_http负责传输，dashboard_service负责产品操作；浏览器不直接开数据库 |
| StockQA与IQS | StockQA仍拥有模型HTTP、费用、任务、原回答与逐题保存的事务权威；IQS负责编排与问答语义 |
| StockWiki与IQS | 身份、名单、观察、导入和ACK由原owner处理；IQS主要经隔离子进程和公共方法消费，没有新增一套实体/观察数据库 |
| 比较/名单/结果组件 | 已有mount与request/client/bank等注入边界，清理与页面异步响应隔离存在 |
| 公司agent执行 | 复用原Runner和Runtime桥，不再造第二套生产模型客户端/预算账本；公开company_scan_inputs投影已有效隔离活owner对象 |

合理约束应保留：主体/题义/期间一致、原请求绑定、预算与未知发送状态、防重复收费、不可变历史、写入事务及浏览器同源保护。解耦不要求取消它们，也不需要微服务、消息总线、插件平台或每层一个新抽象。

## 高优先：已有具体行为问题

### D1 / P1：公共搜索结果消费者复制了生产者的内部名单

位置：IQS `scripts/stockqa_adapter.py:95–100,140–143`，路由另在`routing.py:305`复用。StockQA生产者见`src/utils/quick_scan_work_store.py:743–768`、`src/core/models.py:553–561`、`src/config/quick_scan_search_policy.py:49–50`、`src/utils/quick_scan_external_context.py:288–295`。

IQS独立列出可接受的native receipt字段和四种搜索route_kind；StockQA已经增加DeepSeek Search/Fetch，以及请求payload、可见原答、研究intent三个SHA字段。原公开输出会保留这些合法扩展，IQS却拒绝。

独立agent的纯内存反例使用本仓`tests/test_external_search_result_contract.py::external_result`，每次更新route_kind或原回执可选字段后按原fixture重算相关hash：

| 变体 | 实际结果 |
|---|---|
| Brave、Tavily、ZAI REST、ZAI MCP | 接受 |
| deepseek_search、deepseek_fetch | `external retrieval reference or time mismatch` |
| 增加request_payload_sha256 | `invalid external original receipt` |
| 增加research_visible_output_sha256 | 同上 |
| 增加research_intent_binding_sha256 | 同上 |

准确范围是**ROUTE_02分类结果及路由回执消费**，不是声称所有普通评分入库都失败，也不是本轮真实供应商测试。根因是上下游共同维护同一协议细节，不能独立演进。

建议由StockQA既有公共结果层提供稳定、供应商无关的搜索投影和兼容规则；IQS只依赖所需字段，保留完整原回执hash及必要语义核验。不要简单删除全部校验，或只在此处再加两个供应商名后宣称根修完成。补一组实际producer→consumer测试覆盖可选字段和新搜索实现即可，不新增运行门禁。

### D2 / P1：一个慢命令仍会阻塞全部产品读取

位置：IQS `scripts/dashboard_service.py:522–535,705–711`。

服务总RLock中执行所有非只读请求，仅把prepare/preview特殊放出锁。tasks/preview、start及inspect/resume/seal等仍可能同步等待原owner子进程。GET虽在锁外处理，却要先取得同一把锁捕获读取视图。

独立离线探针用Event暂停实际服务所调用的execution.preview，同时请求GET setup；200ms内读取不能返回，释放preview后两者才返回200。真实owner预检可达分钟级，浏览器普通读取超时为30秒。现有慢GET测试不能覆盖这个反方向。

建议以很短临界区捕获不可变配置和组件引用，耗时命令在总锁外执行；原组件/工作范围锁、配置切换一致性和防重发继续保留。需要慢POST并发GET、配置切换与同work互斥的针对性测试，不需要新队列系统。

## 中优先：故障隔离与独立演进仍有缺口

### D3 / P2：静态快照失败扩大为整个UI不能启动

位置：UI Lab `src/app/main.js:62`、`src/app/store.js:101`、`scripts/serve.py:133`。

main先await整份store.load，再connect和注册路由；bank/versions/roster/manifest用Promise.all绑在一起。独立探针仅让versions JSON失败，真实ESM加载与原boot即得到connected=false、routed=false。服务启动还要求静态构建和bank成功。

此前optionalDrafts隔离有效，此处是更大的剩余故障域，现有`test_optional_draft_boot.py:47`甚至固化了其他快照失败时全站失败。应先使壳、设置、doctor和独立正式查询可用，各页面分别报告缺少依赖；不可把失败数据伪装成空列表成功。

### D4 / P2：恢复编排跨入其他仓库私有函数与状态布局

生产共享链的`shared_company_engine.py:396,542,601,797`直接使用Company Lab的`_evidence_origin`、`_verify_snapshot_against_history`、`_receipt_from_event`；同时理解pending_intent、历史receipt_model事件和slots细节。Company内部重构会迫使IQS接续实现同步修改。

另有产品配置适配器`dashboard_execution.py:212`直接调用StockQA的`LLMConfig._validate_quick_scan_policy`。这与此前生产company_scan_inputs/private transport整改已完成并不矛盾：此前范围不能外推为所有跨仓私有接口清零。

建议在原owner/Lab收拢少数公开操作：加载并验证恢复快照、取得原事件回执、读取最终答案、读取/验证模型策略。IQS仅编排，不再复制内部状态机。不要把`services.store`所有公共调用一概判错，也不要为了一个调用新增一层类。

### D5 / P2：旧任务与题包仍绑定当前代码/资源

有两个相关但不同的耦合点：

1. `shared_company_engine.py:134–160`读取当前源码目录的answer schema和metric registry，再验证原任务；resume/finalize共用。独立探针保持旧task/context/答案不变，仅让读取函数返回新增必需字段的新schema，原本通过的答案即ValidationError。这是未来版本升级时的确定性风险，不证明当前真实历史已损坏。应按原任务发布版本选原资源，复用已有冻结发布与兼容reader；不重新加入整库hash相等门。
2. `question_prompts.py:187–191`把Python函数源文本加入renderer fingerprint；`question_manifest.py:134–138`、`question_sets.py:219–220`要求当前代码hash与旧包完全相同。主控在自有临时目录生成并验证真实standard-1 manifest，仅在内存向getsource结果加注释（不改函数或prompt输出），原manifest即报`historical renderer implementation unavailable for prompt verification`；恢复原getsource又通过。无语义改动的重构也会影响旧包读取，违背独立演进目标。

修正方向是把不可变题义、实际prompt字节/资源与可版本选择的renderer/validator接口绑定，而不是把旧任务绑定“此刻源码的文本”。历史真实冲突仍需拒绝；不要为消除此耦合直接信任任意prompt或解除主体/题目绑定。验证应覆盖无行为重构、兼容追加资源、新版本与旧任务并存。

### D6 / P2：比较页再次实现通用必答模块规则

UI Lab `src/app/ui/product_extensions.js:39–45`写死common/dupont/porter，而构建结果已经有`always_applicable_modules`，`store.js:157`也在使用。独立探针增加声明为必答的new_required/NEW_01，比较分组仅返回BASE_01、D_01、P_01，遗漏NEW_01。

现有36题未因此自动丢失；问题是未来新增通用模块必须同步改前端。比较应消费现有相同数据契约，旧数据缺字段才走兼容路径，补一个新增模块用例即可。

### D7 / P2：产品服务窥探组件字段和存储文件名

`dashboard_service.py:193–194`直接修改execution.bundles/config；`:207–212`按prepjob_*.json、deliveryjob_*.json、batch-*.json判断持久化组件是否存在。`dashboard_delivery.py`与`dashboard_prepare.py`的内嵌脚本还掌握owner记录/输入布局。

事务权威仍在原组件，未发现IQS因此另造真实数据库。但若组件换字段或存储实现，公开操作方法即使没变，服务也须跟着改，可能漏查历史活动工作。这是替换风险，不声称当前已丢任务。

应把更新登记包、查询持久化活动、读取交付快照等能力归还原组件的小型公共方法，沿功能维护逐步收口；不要求一次性重写全部适配器。

## 低优先：保持与主线区分

研究/兼容`thin_scan.py`仍有自有HTTP、搜索/重试/模型配置实现，`applic_llm_probe.py`与`applic_llm_compare.py`会调用。当前dashboard/shared/one_click未调用它，README仅示dry-run。其维护成本确实重复，但**不能据此声称原UI绕过StockQA**；后续维护实验入口时迁回原客户端即可。

`tests/test_shared_answer_semantics.py:14–30`的纯语义测试依赖相邻仓库及其tests/conftest.py布局。轻量fixture可留在本仓tests/support；真正跨仓原owner/SDK测试继续留在集成层。无需为了让所有测试单仓运行而替换掉真实集成测试。

## 验证结果与限制

- 题库/提示词/manifest/评分边界原测试四文件：**34 passed，39 subtests passed，15.59秒**。子测试单列，不累加成73个不同测试。
- 主控渲染源码注释探针：原manifest通过 → 输出不变但源码指纹变 → 历史manifest拒绝 → 还原后通过。
- 独立agent另完成搜索协议6种route/3种字段、慢命令并发读取、UI坏versions启动、必答模块扩展、共享schema升级的上述离线反例。它们证明各自边界，不冒充真实模型或生产恢复验收。
- 主控日志在忽略目录`runs/decoupling-audit-2026-11-02/`。第一次测试包装器过宽拦住本机gethostname；修正后曾遇Windows长TEMP路径复制失败（33通过/1环境失败），改用C:/Temp自有短目录后四文件全过。两次环境问题均非产品架构反例，日志保留。
- 所有自有临时目录清理，API调用0。只读跨仓git最初被沙箱拒绝，经已有授权的沙箱外只读命令取得上表准确HEAD；未把空输出当版本或干净证明。
- 本轮没有跑收费样本、整个跨仓测试集或200家公司；没有全面检查每个外仓的全部内部实现。结论是IQS全体脚本的静态结构加现行产品关键链路的深入核查。
- 汇总报告另由跨仓独立审查agent复核，确认D1影响范围、D4生产/研究区别、D7风险措辞与收敛建议均与证据一致，无需更正；此确认不代表上述缺陷已修复。

## 建议收敛顺序

1. 先修D1公共结果兼容和D2全局锁，解除已复现的误拒与跨功能阻塞。
2. 将D4公开恢复接口与D5历史资源选择作为同一恢复边界整改，保留原已付回答、原请求绑定与事务所有权。
3. 收口D3页面依赖、D6数据驱动比较、D7组件状态接口；低优先研究入口随原功能维护处理。

以上是审计后建议，不是新建支线、运行门禁或本轮已经实施的重构。不改写原测试与真实扫描签收，不用新增证明系统代替实际兼容与故障隔离测试。
