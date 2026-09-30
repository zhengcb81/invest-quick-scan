# 大股票池快速扫描与产业链检索：总体规划

## Goal
为约2,000家独立上市公司（A/H/美股各600—800家为可重叠覆盖软目标）的持续画像、字段评分白名单、产业链语义检索和深度研究交接，逐卡实施跨项目方案。本目录可写；用户已授权StockQAbyLLM全仓写入但须事先报备拟改文件/目的；StockWiki的W01及W02/W03精确范围已授权，W02/W03仅限8个名单身份/成员管理源码与测试文件，不含W05、UI或其他文件；company-wiki等其他仓库只读，写前另获许可。不批量下载公司文档，不把离线契约验收冒充生产上线。

## Ownership and Scope
- 计划所有者：当前任务 `/root`。
- 选定计划目录：本项目根目录（resolver返回legacy fallback；不存在已有命名计划）。
- 已有基础：24题核心评分模板、行业与阶段模块、StockQAbyLLM兼容导出和离线验证。
- 新目标：从单公司研究问卷升级为可持续维护的轻量股票池数据产品，同时与revenue-forecast/invest-*深度研究保持边界。
- 用户新增硬约束：只靠LLM问答（允许联网搜索）填充画像；不保存公司文档、网页正文或财报；company-wiki和StockWiki联动不得引入文档采集依赖。

## Phases
### Phase 1: 核查现有项目与数据契约
Status: complete
- [x] 核查company-wiki实体、目录、落库和索引机制。
- [x] 核查StockQAbyLLM请求、检索、结果与批量机制。
- [x] 核查revenue-forecast/invest-*存储与交接边界。
- [x] 记录可直接复用能力、接口缺口与数据风险。

### Phase 2: 总体架构与关键取舍
Status: complete
- [x] 设计issuer/security/listing三层身份、评分与事实分层、版本/时点/来源。
- [x] 设计白名单规则、缺失值、可比性与校准。
- [x] 设计产业链分类、关系、主题映射和关键词检索。
- [x] 设计company-wiki可选身份关联与轻量数据库的职责。
- [x] 设计批量、成本、刷新、人工复核与深研交接。

### Phase 3: 实施步骤与验收方案
Status: complete
- [x] 给出跨项目依赖顺序、每阶段产物和验收门槛。
- [x] 规划小样本、扩容、第二阶段事实采集、2,000家运维。
- [x] 提供示例数据、规则和AI硬件检索案例，标明仅为设计示例。

### Phase 4: 规划校验与交付
Status: complete
- [x] 核查事实与设计建议的区别、路径引用和架构一致性。
- [x] 更新findings.md、progress.md、后续实施清单。
- [x] 整理用户可直接阅读的关键决策、实施顺序与实施时待配置的偏好。

### Phase 5: 周期低谷与困境反转补充
Status: complete
- [x] 核查既有周期、反转和困境问题，识别遗漏。
- [x] 补齐低谷辨识、优势保全、修复证据、资金时限与股东受益问题。
- [x] 增加独立观察标记，保留低分和关键风险，不把暂时困难直接从研究范围删除。
- [x] 同步skill、题库、规划与必要的行为验证。

### Phase 6: 不变优势与产业变化的分析设计
Status: complete
- [x] 区分需求、解决方案、竞争优势、利润归属与每股价值，说明“不变”的条件和时限。
- [x] 对照24题及恢复诊断，提出复用与补充方案，避免重复评分和主题热度加分。
- [x] 形成轻量问答字段、触发条件、观察标记与验证情景的设计建议。
- [x] 更新方法设计和规划，形成投资逻辑讨论稿；本轮不改变生产评分规则。

### Phase 7: 股票池运维与研究技能联动规划
Status: complete
- [x] 核查证券主档/名单工具、StockQA提供商与批次能力、两个研究技能的接入点。
- [x] 设计约2,000家公司的名单产生、用户增删、去重与版本机制。
- [x] 设计按公司和问题的新鲜度、接续扫描及用户排序的LLM故障切换。
- [x] 明确各项目唯一职责与主题/行业技能的只读查询、补扫和反馈协议。
- [x] 写入总体设计、实施路线、可审查的流程与验收案例；本轮只规划。

### Phase 8: 面向后续模型的细粒度任务、测试与审查包
Status: complete
- [x] 将M0—M5拆为单一拥有者、明确输入输出和依赖的原子任务。
- [x] 固定不能擅改的设计约束、契约决策和任务接续/交接规则。
- [x] 为任务配具体正反例、边界/故障测试、预期结果和分阶段放行标准。
- [x] 提供实现者/审查者模板、问题修复闭环和可核验的完成证据。
- [x] 检查任务依赖、测试覆盖、文档链接和现有能力区分，完成交付。

### Phase 9: 跨项目交付与一键开启闭环
Status: complete
- [x] 核查现有跨项目计划与启动/配置入口，识别集成缺口。
- [x] 定义首次配置、安装/版本配套、统一启动、停止/续扫与故障状态。
- [x] 增加各项目交付清单、安装/联调任务及跨项目验收场景。
- [x] 将“一键开启”绑定真实端到端与发布审查，更新计划校验工具和回归测试。
- [x] 校验完整依赖图与资料引用，交付可供后续模型逐卡实施的完整计划。

### Phase 10: 企业快扫结果 UI 细化
Status: complete
- [x] 核查既有公司卡片与启动页面任务，定位结果浏览的规格缺口。
- [x] 明确列表、评分详情、事实关系、时效和恢复观察的UI行为。
- [x] 拆分界面任务，补充浏览器验收并接入G5/G6依赖。
- [x] 验证更新后的任务/场景清单、引用和规划工具。

### Phase 11: 全局复核、事实题库与三维可比输出
Status: complete
- [x] 复核首次启动、自动/手动名单维护与跨项目单一写入边界。
- [x] 实现标准事实题库和离线路由/输出校验，复用StockQA执行能力。
- [x] 优化行业/生命周期评分口径与稳定字段，保留恢复观察和关键风险。
- [x] 固定公司×时间×模型比较契约、示例及数据继承规则。
- [x] 同步启动/存储/UI/任务计划，完成离线行为测试和独立审查。
- [x] 补并行发包、五小时共享额度切换、逐题防重契约及用户模型顺序配置模板。

### Phase 12: 跨项目任务卡逐卡实施与生产落地
Status: historical_superseded_by_Phase_43_task_receipt_retirement

本阶段清单是当时的实施记录，不再定义当前动作或关闭门。Phase 43已退役任务回执刷新流程；C01—C07旧回执刷新暂停且不再需要，未完成的生产接线仍以当前任务状态和G0—G6证据判断。
- [x] P00: 核实各仓真实代码、commit hash、调用链与行为基线，产出基线报告与完成回执。
- [ ] C01: 本地身份契约当时已扩至2.2.0：发行人Entity v2.1保持不变，新增AnalysisSubject 1.0.0；这条历史记录中的P01/C01 receipt刷新要求已由Phase 43退役，不是当前关闭门。StockWiki权威subject映射及StockQA Work/Observation接线仍由后续W02/W03、C04/C06/W05负责。
- [x] C02: 冻结指标映射及优势/变化证据口径契约，完成Schema定义、规范文档与6个Case自动化测试。
- [x] C03: 结果筛选白名单与三值规则契约，完成Schema定义、规范文档与10个Case自动化测试。
- [x] C04: 字段时效、待办键、状态转移与接续契约（JOB-08阻断整改后独立复审verified；仅本地离线契约）。
- [x] C05: 冻结有序模型、故障分类及费用边界（独立复审verified；仅本地离线契约，不代表StockQA运行能力已实现）。
- [x] C06: 结果查询、UI分页与深研交接契约（exchange内容hash阻断整改后独立复审verified；仅本地离线契约）。
- [x] C07: 跨项目部署、启动生命周期与就绪协议（full-readiness组件实载hash阻断整改后独立复审verified；仅本地离线契约）。
- [x] G0: 跨项目契约与接口冻结审查（第三轮独立审查`verified_for_local_contract_scope`；生产live/E2E仍按后续gate执行）。
- [x] S01: metric与作用层编排（本地实现、原始测试日志及独立审查均验证通过；REC-04依赖StockWiki查询入口，仍未执行）。
- [ ] S03: 优势条件与产业变化诊断取舍（本仓题义、版本、导出及回归通过独立审查；TIME-06的StockWiki刷新规划和E2E-06仍未执行）。 DUR-04 review follow-up: current tests mutate a fresh manifest version header; this repository has no archived 3.1.0 metric manifest, so historical 3.1 compatibility remains unverified and must not be claimed.
- [x] Q01: F01/F02及r2复审发现的F04均按获批parser范围修复；S02消费者兼容恢复。StockQA共享suite 276项、本地全量222项/139子用例及独立复审均通过；receipt绑定精确文件哈希，Q01离线范围verified。
- [ ] Q02: MiniMax-M3公开CLI在较早代码快照有一次Microsoft单题真实完成搜索；配置别名/真实厂商错标已整改，302伪搜索HTTP响应已补真实Requests/HTTPX反例并独立复审，最终源码离线unit+integration 588项通过、独立焦点203项通过。最终代码的有限live重验：受限沙箱两次在HTTP前ConnectionError；经授权放行后两次HTTP 200/completed但无已完成搜索链，`search_status=unverified`且评分正确拒绝。故历史live通过不能作为最终哈希的LLM-01通过，Q02继续partial；脱敏证据及覆盖率产物副作用见`receipt-Q02-minimax-final-revision-2026-09-26.json`。MiMo和DeepSeek仍仅直连探针，运行级路由用尽归Q04、持久恢复归Q08。2026-09-27获批新增MiniMax-M3 Anthropic Messages适配；经初轮独立复核整改后，隔离unit+integration与live fixture suite最终为110 passed/3 expected skips；网络受限运行给出HTTP前ConnectionError，联网公共CLI两次均返回insufficient_evidence，最新回执仍为search_status=unverified，故未证明本次搜索事件和来源链，新增路径不能关闭LLM-01/Q02。脱敏日志见validation-Q02-Anthropic-offline-r3-2026-09-27.log及validation-Q02-MiniMax-Anthropic-live-E2E-final-2026-09-27.log。
- Q02 current-snapshot hardening (2026-09-27): corrected two fail-closed gaps in MiniMax Anthropic search verification (`base_resp.status_code=false` and an unrecognized server tool coexisting with valid `web_search`). The seven-file code/test snapshot passed 160 isolated unit/provider/CLI integration tests with warnings-as-errors; Ruff and Black passed on the changed parser and its unit tests. Independent review matched all seven exact file hashes, reproduced the receipt semantics, and found no P0–P2. One authorized single-question live CLI attempt on the current code ended with `ConnectionError` before an HTTP response; it produced no search receipt or score and is not a successful E2E. The live harness's parent-side UTF-8 decode error is fixed, its changed-file review found no P0–P2, and the live selectors collect offline as four expected skips. No automatic retry was issued. Q02 remains partial until a current-hash live search receipt verifies the complete search/source chain; exact hashes and cleanup evidence are in `progress.md` and `docs/implementation/contracts/validation-Q02-fail-closed-hardening-2026-09-27.md`.
- Q02 latest endpoint/credential diagnostic (2026-09-27): a bounded one-query `.cn` live pass is recorded above, but a later same-route request returned HTTP 200/completed without a correlated search result and correctly remained unscored/unverified; two diagnostic calls to the official `.io` host returned HTTP 401 with the configured key. The live test now accepts `STOCKQA_MINIMAX_ANTHROPIC_BASE_URL` and uses safe UTF-8 diagnostics. Focused offline client/CLI tests passed 17/17; independent read-only review is pending. Q02 remains partial until a supported endpoint/key pair produces a verified current-snapshot search receipt. Evidence: `docs/implementation/contracts/validation-Q02-endpoint-region-diagnostic-2026-09-27.md`.
- Q02 test-review follow-up (2026-09-27): independent r1 found a P1 indentation error, P2 overconstraint on optional request_id, and P3 loss of the allowlisted web_search error_code in the safe summary. All three are fixed. Current live-test SHA256 `CC1423ECC7E5F24AE26ACF2F08067B3613F5AE9BDAE22AF6D8B5A9E8D10BA95F`; AST parsing passes, live selector collects without execution, and isolated focus passes 17/17. R2 review closed the P1/P2/P3 findings with no new P0-P2 (report SHA256 F5D7DC9413F6248DC9C87218558CB9665353F5C0E4EC8C33B506462D127A8113); Q02 remains partial pending a stable verified live search receipt.
- 2026-09-27 MiMo single-query live retest through the public CLI returned `error/unverified` with no HTTP status, model, response ID, or source URL. Its unique temp root was cleaned. Because the transport receipt cannot prove the request was not sent, this is an unknown outcome and must not be blindly retried; no cause or live-search success is inferred. See the detailed entry in `progress.md`.
- [ ] Q03: F03重复JSON对象键在direct与Markdown兼容路径曾可绕过并从metadata误取9分；现只提取完整外层JSON并fail closed，direct/Markdown固定案例通过，r2独立复审verified。Q03仍因前置Q02未完成而保持partial；Q12/S02不替代Q02的LLM-01 live。
- [ ] Q04: B1/B2完整v2策略校验经r4独立复审verified。route-recovery r6复审发现备用成功仍误报等待，r7在用户新授权/提前报备的四文件内修复成功答案、终局无结果和公开JSON的`dispatch_outcome`；114项隔离unit/CLI及真实代码路径探针经独立复审通过。Q04整体仍partial：运行中policy热更新及同一路由容量满时等待（PAR-11）开放。LLM-06的本轮结果分类与停止fallback由Q04负责；持久冷却/跨运行`retry_wait`由Q08负责，共享全局容量PAR-03由Q11负责，StockWiki设置接线PAR-08由X09负责。
- [x] Q12: StockQA公开回执输出实际Question.text哈希和每次HTTP状态；64项定向、461项剩余全套通过/1项live跳过，独立复核无finding。对话中称作Q03R，但正式任务ID按计划校验器规则定为Q12。
- [x] S02: StockQA公开CLI到screening导入的离线隔离E2E得到8分；MiniMax空HTTP request ID、跨厂商最终真实provider及现代级联派发状态兼容增量经四类矛盾回执反例、49项/107子例和独立复审通过，精确快照见`receipt-S02-minimax-compat-2026-09-26.json`。真实跨厂商live仍未执行；S06后续改动须另行复审。

### Phase 13: 组合式题库升级设计与计划增补
Status: complete

- [x] 只读审查现有48模块/222评分题、61事实题与`select_questions`组合/路由/历史校验，确认半导体扩张公司无需重建第二套题库。
- [x] 明确模块独立版本、发布锁、稳定题ID、事实模块、客观分类与投资视角分离、模糊路由/人工覆盖及重大风险不静默删题。
- [x] 固定核心24构念与同题篮/同题义比较，新增题分层展示；规划逐题增量续扫与旧版发布包读取。
- [x] 将本目录、StockQA、StockWiki与UI拆为S04—S06/Q13/W15/F06/U04七张任务卡，增补MOD-01—13固定正反/故障/live场景和G6依赖。
- [x] 运行计划校验、计划测试和diff检查；独立只读审查指出的版本与渲染缺口已纳入设计，产品实现状态仍待逐卡回执。

### Phase 14: S04模块注册与历史版本契约
Status: complete

- [x] 为既有题库建立模块/发布锁/路由决策schema及兼容规则，不重写现有题义。
- [x] 给MOD-02/03/04/07绑定本地正反校验；合成旧归档可读且伪造/篡改版本拒绝，真实manifest入口留S05。
- [x] 保存S04离线范围的测试与独立审查回执；独立复核无剩余P0/P1/P2，真实历史读取/运行时路由留后续卡。

### Phase 15: S05模块注册、确定性拼装与按版本读取
Status: complete_for_local_contract_scope

- [x] 将S04注册闭包接入现有`question_sets.py`公共问卷入口，保持48模块/222题和旧版行为。
- [x] 发布首个可校验的模块锁与归档；旧manifest按可信原版读取，缺失/篡改拒绝。
- [x] 固定24核心构念，新增扩展层、预算欠派发清单与每题有效语义/prompt指纹。
- [x] 跑MOD-01/02/03/04/07/08在S05拥有范围内的正反例、全量回归和独立审查，精确回执见`receipt-S05.json`；S05 v2回执对S04/S01当前依赖的公开递归验证为`eligible_to_close=true`；路由决策与困境必问题仍由S06负责。

### Phase 16: S06证据路由与StockWiki轻量身份库
Status: in_progress

- [ ] S06: ROUTE_02已升级至router 2.3 / policy schema 1.3 / request protocol 3，保留2.0—2.2历史只读兼容。新增StockQA公开`quick_scan_result/1.0.0`适配器，逐项核验实体、搜索回执、答案SHA-256与实际模型归属；执行仍须校验调用方独立保存的decision_id。2026-09-29修复新执行路径误用历史读取校验器的问题，并修正renderer失败测试的patch owner；S06相关聚焦回归57项通过、独立只读复审无P0–P2。S06仍为partial：真实StockQA到StockWiki事务ACK、router 2.1真实历史快照以及授权的跨仓端到端验收未闭环。工程task receipt v2/P01已退役，不再以刷新旧回执链作为门槛。
- [x] W01: 经用户精确授权，仅在StockWiki新增独立SQLite身份库/测试并更新`.gitignore`。真实分类YAML只读副本的隔离验证29项通过；独立首审的伪v1 schema、提交后验证和ADR错误基础引用三项均经固定反例修复、第二轮独立复审通过。`receipt-W01.json`绑定精确哈希与本地范围；生产库未迁移，W05仍待实施。
- [ ] W02: 在用户授权的StockWiki精确文件范围内完成安全主档快照预览/导入首段：只落不可合并的来源候选，按内容哈希幂等，拒绝名称/代码推断身份，来源URL仅保留HTTPS origin，不持久化路径/凭证/query/fragment；真实CN/HK/US主档复制到临时目录验收通过。59 passed、1 skipped隔离目标测试及静态检查通过；最终8文件独立哈希复审通过，无P0–P2，见[验证回执](docs/implementation/contracts/validation-W02-W03-stockwiki-first-segment-2026-09-27.md)。仍缺source-to-entity binding审批/事务桥接、可核实身份升级和生产名单自动接续，因此W02 partial；跨实体唯一性须由StockWiki owner事务实现，见W02方案与C01复审报告。
- [ ] Q08: Q08拥有持久冷却/半开探针及跨运行`retry_wait`恢复资格；首段provider-health状态与HTTP隐式POST重试、晚到拒绝时间修复已独立复审，离线unit+integration 617项通过，精确边界见`receipt-Q08-first-segment-2026-09-26.json`。当前仍缺有界dispatch-round持久化和与Q06 work lifecycle的生产接线。Q06持久待办/transport和Q09预算/并发账本第一段已实现；Q07逐题检查点仍缺生产接线与多题单次派发支持，Q09真实费用解析、公共runner完整预算接线及最终独立复审仍待完成，故Q08整体partial。
- [ ] Q09: StockQA持久预算账本与发包闸门第一段已实现，包含原子预留/结算、跨策略版本保留支出、未知费用/结果不明时保守暂停、与work send-intent同事务，以及同步/异步transport接线。独立复审发现“过期lease后的迟到HTTP回执会遗留在途预算槽”并已改为在同一SQLite事务记下late receipt和预算状态：HTTP已结束则释放并发槽，未知费用仍保留预留/暂停；没有收到HTTP响应仍保留不确定状态。相同late receipt重放现为同结果幂等、不同状态/费用来源冲突拒绝；费用解析器异常或无效用量也会保留预留、释放已结束请求的网络槽并暂停后续派发。预算对账重放也校验request-count语义，阻止`confirmed_not_sent`与`completed`互翻造成请求数漏记。全范围隔离回归436项通过，其中双进程+20请求真实HTTP-stub并发验收检查全局/组/路由上限；最终review follow-up待回。生产真实费用解析与完整runner预算配置仍未闭环；验证记录见[Q09首段日志](docs/implementation/contracts/validation-Q09-budget-first-segment-2026-09-27.log)。
- [ ] W03: 在用户授权的StockWiki精确文件范围内完成轻量股票池成员管理首段：新增/逻辑移除/恢复/保留/置顶、导入只补缺不自动删除、版本冲突保护和追加式事件历史，并注册CLI；v1→v2 SQLite迁移使用独立冻结的历史v1 SQL fixture，并比较确认entity/security/segment/universe/member五张基表均保留。与W02合计59 passed、1 skipped隔离目标测试（含真实证券源快照只读副本）、ruff和差异检查通过；最终8文件独立哈希复审通过且无P0–P2。恢复并置顶成员为单事务/单版本事件。该首段尚未把权威身份核验投影绑定到C04 work item，也未接扫描/观察导入/UI，故W03 partial。详见[验证回执](docs/implementation/contracts/validation-W02-W03-stockwiki-first-segment-2026-09-27.md)。
- [ ] Q06: 第一段隔离SQLite待办原语已独立复审；第二段同步HTTP传输边界通过45项store/transport焦点测试与274项相关provider/级联/parser/公开CLI分组，AST/Ruff/Black通过。首轮独立审查发现的迟到回执及格式修复账本缺口已修复；第二轮精确快照复审未发现开放P0-P2。最终证据见`validation-Q06-transport-boundary-final-2026-09-27.log`和`validation-Q06-static-final-2026-09-27.log`。公开CLI尚未绑定真实work item，需等待W03权威身份投影与Q07答案检查点；Q09预算和W05 ACK仍未接入，故Q06继续partial，不得标记生产完成。
- [ ] Q07: StockQA SQLite work store增加v1→v2原子迁移、不可变逐题答案checkpoint、搜索回执/身份/题目指纹绑定、幂等重放、run恢复列表及仅取消pending任务。独立复审发现的URL查询凭据泄漏风险已通过共享hash/持久化规范化修复，迁移测试改用固定v1 SQL fixture，测试SQLite句柄显式关闭；235项unit/integration/provider/CLI回归通过，ResourceWarning按错误处理且无警告，Ruff/Black/diff检查通过，follow-up复审无开放P0-P2。当前只支持默认每请求一题；PAR-04的一次多题dispatch与逐题attempt映射仍未实现/验收，公共runner还须等待W03权威身份投影，预算账本/ACK/异步路径另有独立门，故Q07仍为partial。最终证据见`validation-Q07-checkpoint-2026-09-27.log`及`reviews/Q07/followup-review-2026-09-27.md`。

- [ ] Q10: StockQA producer-side Q06/Q07 result outbox首段已在用户授权范围内实现SQLite schema v5/v4迁移、不可变单item C06 package、持久adapter阻断原因、稳定delivery key、send-intent/结果不明防盲重发、精确ACK消费及原子delivered；严格隔离回归79项通过，Ruff/Black通过，动态合成包另经本仓C06 full JSON Schema与语义校验通过。独立审查发现的证据URL来源脱锚问题已修复：每个evidence URL必须来自checkpoint canonical source_urls，`scored`还必须带至少一条证据；哈希重算篡改及空证据反例均被拒绝。最终精确哈希follow-up无P0–P2发现。当前package由调用方verified adapter提供，StockQA尚无完整Observation适配器、公共runner接线、真实W05 ACK/权威对账；因此Q10仍partial，不得声称真实跨仓导入完成。最新本地日志见 docs/implementation/contracts/validation-Q10-result-outbox-2026-09-27.md。

### Phase 17: 全项目可组合演进与兼容规划

Status: complete_for_planning_only

- [x] 对照现有题库发布、StockQA模型路由、StockWiki词表/规则/查询，明确只补跨组件解析方案和派生视图，不新建第二套客户端、事实库或筛选引擎。
- [x] 将评分尺、事实本体/词表、筛选lens、刷新策略、提供商能力和查询投影的独立版本及旧读新写规则写入`composable-evolution-plan.md`。
- [x] 增加V01—V15单owner任务卡与EVO-01—43固定正反/故障/live场景；评分尺、关系本体/词表、lens、字段刷新、provider能力、ScanRecipe、执行、查询/UI均有版本/兼容/回退责任人。
- [x] `scoring_only`可在F06/G4前扩容；V13—V15后置接入事实版解析、执行及StockWiki字段缺口/导入/ACK。pre-recipe旧数据只读、未决请求先对账，X05统一入口受recipe约束。
- [x] 计划1.8.0结构校验96卡/231场景通过；计划测试53项、全仓`tests/`回归332项/262子例通过。独立只读终审确认EVO-42措辞歧义已消除、无剩余P0—P2；本阶段完成只代表规划，不代表V01—V15任何生产实现。

### Phase 18: 全局组件生命周期、变更影响与版本回放规划

Status: complete_for_planning_only

- [x] 审查题库之外的动态演进缺口：身份/路由、有限答案解析与搜索回执、跨owner发布兼容、字段依赖/失效影响、升级/回退及历史比较。
- [x] 固定I34—I40：唯一owner不可变release、声明式安全组合、按动作协商兼容、精确影响范围、答案/派生分版本化、轻资产回放与发布前黄金样本/回退门槛。
- [x] 新增V16/V17/W16/Q14/V18五张owner卡及EVO-44—66、LLM-13—15共26个场景；本仓只产出版本影响plan，StockWiki事务应用并接入X05/X07/X09，周期低谷公司进入固定升级样本。
- [x] 同步全项目演进设计、决策约束、测试策略、开始实施说明和任务/案例清单，先形成1.9.1方案；纳入Q14实载hash绑定、双worker CAS、旧attempt安全结算。
- [x] 本阶段只完成计划增补，没有执行V16/V17/W16/Q14/V18，不代表新增行为已实现，也不扩大跨仓写入授权。

### Phase 19: 全计划依赖、组合兼容与验收边界复核

Status: complete_for_planning_only

- [x] 独立复核任务图、owner本地验收与跨任务集成验收、评分/事实分阶段交付、可组合组件生命周期、活动ReleaseSet、旧账本结算、W16原子应用和Q15 POST前围栏；未发现任务依赖环。
- [x] 将前置卡误挂后置公开入口/live/导入/刷新行为的场景移回真实拥有者卡，并通过case `requires_tasks`把全链验收绑定到依赖完整的后置任务；为受影响前置卡保留可独立执行的本地用例。
- [x] 加固candidate只读预览、active指针/组件生命周期分离、完整CAS输入、确定性V17重算、租约后POST竞态、permit与send_intent之间崩溃、唯一回执owner和有资格回退；旧attempt按冻结recipe/receipt安全对账，不允许盲目重发。
- [x] 对齐W16本地case、移除重复围栏步骤、修正EVO-66信任根描述；同步任务清单、验收集、决策表、测试策略、跨项目交付、演进说明和本文件至计划1.9.2。
- [x] 新增跨任务依赖声明的未知任务/错误类型反例；运行计划结构校验和计划测试。所有验收case仍为`specified_not_executed`，这轮没有执行产品测试或跨仓写入。
- [x] 将详细独立审查发现、修复及仍未实施的边界写入`docs/implementation/reviews/PLAN-1.9.2-review.md`。按用户要求，本轮至此暂停，等待继续实施指令。

### Phase 20: 1.9.3全局计划再审、兼容收口与暂停

Status: complete_for_planning_only

- [x] 对整份实施计划复核公司身份/多挂牌、题包与多域组件组合、独立release/hash、兼容矩阵、精确影响分析、字段增量、横纵向可比性、周期低谷/恢复候选、UI及跨技能查询责任。
- [x] 重新核查StockQA与StockWiki各自数据库下的付费派发线性化。将两阶段流程固定为：StockQA先耐久写`send_intent_prepared`，W16在owner事务复核当前组件资格并消费permit/写`dispatch_commit`，匹配的commit回执才授权最多一次POST；结果不明不得重试或fallback。
- [x] 修正全局计划边界、启动流程、跨项目交付与测试策略中旧的单阶段permit措辞，并同步当前EVO/LLM验收范围。
- [x] 增加跨权威文档协议一致性回归测试；修正一项将字符串逐字符拼接的测试缺陷，未放宽行为预期。
- [x] 计划校验102任务/322场景/G6通过；计划单测68项通过；`git diff --check`退出0（有既存换行风格提示）。详细边界与未实施项见`docs/implementation/reviews/PLAN-1.9.3-review.md`。
- [x] 本轮没有产品功能实现、真实API/live E2E或外仓写入；所有验收case保持`specified_not_executed`。按用户要求审查完成后暂停。

### Phase 21: 恢复逐卡实施并补齐S04当前验收范围

Status: in_progress

- [x] 按最新继续指令恢复完整实施目标；重新读取1.9.3任务包、当前工作树、回执和独立审查结论。外仓仍按既有授权边界处理。
- [x] 核对S04当前case集合；发现新增MOD-14未出现在此前S04回执/测试绑定中。
- [x] 在本仓增加真实module contract测试，覆盖重复release module ID、归档内容hash不匹配、依赖循环、退役ID仍被使用；S04定向测试15项通过。
- [x] 独立只读审查确认`validate_registry`拒绝循环，但hash自洽的归档循环在`validate_release`仍可通过；确认MOD-14/既有回执未覆盖该路径。
- [x] 随后已修复归档reader：`validate_registry`与`validate_release`共用依赖图校验；新增hash自洽归档循环反例。定向module contract 16项、registry 17项、question-set 60项与全仓350项/273子例曾报告通过。
- [x] S04/MOD-02与MOD-14当前源码hash绑定的26项/11子例隔离测试日志通过；MOD-14的10条atomic assertion、精确错误、hash自洽依赖环、墓碑冲突/遗漏、完整包原子返回及互斥备选正例均已覆盖。独立复审发现并促成修复`applies_when`同ID范围变更缺口；同ID拒绝与major successor迁移正例、两份契约均已更新。保存旧v1收据后生成当前v2 receipt，公开递归验证`eligible_to_close=true`。复审报告、验证sidecar和当前receipt均在`docs/implementation/`。
- [x] S05/MOD-17精确基线信任、父目录符号链接/junction防护及24项注册器测试已通过；共享恢复映射修复后，S05独立复审确认信任路径未受影响。更新S04依赖hash后，S05 v2 receipt递归验证`eligible_to_close=true`，无blocker。
- [x] S01因共享`question_sets.py`证据哈希/复审过期而仅为刷新回执短暂重开；发现并修复旧manifest恢复观察信任顶层`replacements`的P2，改为从题目`replaces`重建和交叉校验，不一致/不完整时标记`needs_verification`且不改核心汇总。相关批次70项/166子断言、最终定向6项/4子断言通过，独立复审无剩余发现，S01 v2 receipt公开验证`eligible_to_close=true`。
- [ ] 按计划依赖继续逐卡实施；只在大里程碑合并运行回归和独立审查，不为每个小修复单独重复全套检查。

### Phase 22: 1.9.4全计划与可组合兼容专项复核

Status: complete_for_planning_only

- [x] 全面对照身份、模块/题义、路由、评分/事实、ScanRecipe、刷新、模型/费用、ReleaseSet、回退、跨技能查询/UI、启动和隔离E2E责任与任务依赖。
- [x] 将模块演进拆为S04注册/归档图校验、S05历史reader/可信legacy基线、S06当前组合依赖闭包三层，明确互斥备选可共存于release而冲突仅在选中组合拒绝。
- [x] 细化MOD-14/16/17固定反例，新增MOD-18并绑定唯一S06 owner；保持所有行为case `specified_not_executed`。
- [x] 同步权威模块契约、组合/路由说明、测试策略、README与审查报告至1.9.4。
- [x] 计划结构校验102卡/323场景/G6通过；计划回归69项通过；本次不改产品实现或外仓、不调用live/API。
- [x] 用户要求审查完成后暂停；恢复点与未关闭S04风险已写入`docs/implementation/reviews/PLAN-1.9.4-review.md`。

### Phase 23: 1.9.5组合演进与验收证据闭环加固

Status: complete_for_planning_only

- [x] 独立复核兼容声明发现未定义窗口的字段、动作、UTC边界与过期行为；新增V16/EVO-83并冻结精确producer/consumer/action及`[start,end)`语义。
- [x] 独立复核发现复杂case到测试selector/receipt只有流程文字；新增P01 receipt v2 schema/只读验证器规划，绑定任务定义、完整owner case/assertion、global boundary、源码/日志和独立review快照；旧receipt只作历史证据。
- [x] 拆分MOD-14/16/17/18与EVO-83、RCPT-01/02/03的atomic assertion IDs；增强本地计划校验器，拒绝缺字段、重复、乱序assertion ID。
- [x] 将P01置于C01—C07/G0前并接入G6；添加I51/I52/I53，计划当前为103 tasks、327 acceptance cases、53 invariants。
- [x] 独立审查提示旧v1依赖无法满足当前关闭门、P00 bootstrap易形成死锁，以及P01自验日志自哈希风险；明确唯一P01→P00只读context例外，P01后重跑P00、所有其他依赖要求当前v2，P01封存前实现review/receipt core、封存后sidecar与证据review分层且hash方向无环，并新增RCPT-03。
- [x] 计划校验通过（103/327/G6），计划单测74项通过，`git diff --check`退出0；仅有既存LF/CRLF提示。本轮只调整计划/规划校验器，不继续产品功能或外仓实施。
- [x] 独立审查最终确认allowlist双向一致、P01后重跑P00再重跑C01—C07、自验日志外置均无剩余P0—P2，且无依赖环；审查者未运行产品测试。
- [x] 计划专审报告已记录复核范围、修订、旧回执状态、S04/S05真实实施缺口和恢复顺序；按用户要求，计划收口后暂停产品实施。
## Decisions
- 本轮保持规划边界，此前纯信息问题集仅规划；用户本轮已明确要求补齐，现实施本skill事实题库与离线协议，外部运行/存储按跨项目任务实施。
- 对证券数量与独立公司数量分别统计，不能将A/H/ADR多挂牌默认视为独立公司。
- 不在本skill复制LLM客户端、检索、重试或财报下载能力。
- 来源URL、发布时间与简短依据属于轻量问答元数据；不抓取或归档链接目标，不伪造company-wiki的source manifest/EvidenceSpan。
- 不要求先在company-wiki创建公司目录，也不要求先完成StockWiki正式研究建档或人工证据资格审核才能快扫。
- 建议StockWiki独立quick_scan命名空间内的SQLite作为轻量股票池权威存储；交换包及页面只作导出，不维护第二套可写权威状态。
- StockQA承担唯一问答执行与批次运行机制；StockWiki承担结果导入与筛选。stock-pool-design.md已形成具体方案。
- 用户新增要求：周期低谷或经营暂时困难但仍有优点的公司，需有独立关注路径。当前低分不改写为高分；展示可恢复性、剩余优势、兑现条件与风险，防止质量白名单成为唯一入口。
- 名单管理先做StockWiki内的确定性小工具，由既有skill调用；以独立公司为长期成员，不新增重型选股skill，不按质量门槛清退大池。
- 复用逐字段有效观察，按逐题待办接续；信息时点、重新导入时间和unknown冷却明确区分。改变筛选阈值不触发问答，模型已成功但入库失败只重导入。
- 用户决定LLM顺序，StockQA扩展现有ProviderCascade并持久化故障/任务状态；成功即停止，不因低分换模型，所有备用共享总预算。
- 审查与测试按大节点集中：小任务保留逐case/断言的可追溯结果，但同一变更组可共用一批测试运行与日志；不为每张小卡单独全量测试或独立审查，阶段稳定候选再做一次全量回归和批量审查。
- 任务卡是owner/范围边界，不是逐卡停工点：接口冻结后可连续实施同一依赖链的下游卡；只在大节点封存回执并审查依赖闭包。开发自测可随手执行，不为每次自测产生日志/回执；正式结果按一批测试映射多个case/assertion。
- 2026-09-26用户授权修改StockQAbyLLM所有文件，要求事先告知拟改文件/目的；已报备Q04 r7四文件。StockWiki及其他外仓仍按原先逐次授权边界。
- 主题链第5/6步与行业研究第6步查询画像库，定向补缺并保留池外发现；不把原技能的PDF依赖、正式模型或评分量表搬进快扫。

## Errors Encountered
| 日期 | 错误 | 处置 |
|---|---|---|
| 2026-09-22 | 模型配置首轮测试发现schema将未知额度窗口null错误限制为integer | 修正为正整数或null，保留模板/未知窗口回归；校验错误脱敏避免输出误填的密钥 |
| 2026-09-22 | 新增方法/单位回归暴露build返回对象引用调用方可变答案/回执，后续修改使旧观察hash失效 | 在计算观察hash前深拷贝脱离输入，保留两个失败测试并复跑；不减弱不可变要求 |
| 2026-09-22 | 独立前向审查发现事实prompt省略证券身份、模型比较未对齐实际信息日期，并缺期间节奏/模型版本提示 | 补身份上下文、日期/期间可比性约束及版本警告，增加回归测试后复核 |
| 2026-09-22 | 新事实路由表达式漏闭括号，首次新测试未能导入模块 | 补齐括号，保留测试并重跑；未将导入失败当通过 |
| 2026-09-19 | 读取.agents/skills和.codex/skills中的invest-*、revenue-forecast路径均遇访问拒绝/不存在 | 改为读取已知Projects中的源项目；不继续重复尝试相同skill入口 |
| 2026-09-19 | 当前项目没有.git，无法获取git diff --stat | 已检查目录，按文件清单记录本轮仅规划文档变更 |
| 2026-09-19 | 补充计划的首个apply_patch上下文未匹配，未修改文件 | 改用实际标题作为定位，保留原有规划并追加Phase 5 |
| 2026-09-19 | 读取distress.json失败，实际模块ID为distressed | 依据catalog/路由列出的实际ID读取distressed.json，未新建重复模块 |
| 2026-09-19 | 新增测试中2例错误地给已被类型替换的IQS_11设置分数或断言 | 修改测试以manifest.replacements解析实际现金题，保留生产逻辑对类型替代的正确处理 |
| 2026-09-19 | skill-creator校验器以Windows默认GBK读取UTF-8的SKILL.md失败 | 使用python -X utf8运行同一校验器，不更改文件编码或校验器 |
| 2026-09-21 | StockQA/StockWiki的CodeGraph请求均返回Transport closed | 结构查询服务不可用，改用本地只读文件检索，不重建已有索引 |
| 2026-09-21 | 两个研究skill的.agents/.codex入口访问拒绝/路径不存在 | 已从Projects/local-skills读取源SKILL，避免重复读取失效链接 |
| 2026-09-21 | Codex open_in_codex returned Transport closed | Design file is saved; deliver a local file link instead of opening the preview |
| 2026-09-22 | 本地AGENTS.md文件不存在 | 使用用户消息中提供的项目AGENTS指令；不创建或猜测新指令文件 |
| 2026-09-22 | CodeGraph status返回Transport closed | 使用已知文件与本地只读检索核查接口和测试；不反复调用失效服务 |
| 2026-09-29 | 一次性工作树delta解析脚本最初把(状态,路径)记录方向建成dict，导致只得到两个伪路径；首次归档映射断言也使用了错误的活动example路径 | 对照PowerShell计数与Git NUL记录发现解析问题；归档断言阻止写出错误报告，随后读取实际legacy目录、修正路径映射并重跑；生成报告前校验792/843、53/22/2数量不变量 |
| 2026-09-22 | 新增恶意类型测试发现case.kind为dict时负例检查抛TypeError | 修复计划校验器的类型安全检查，保留反例预期并重跑；不将错误输入视为有效计划 |
| 2026-09-22 | 启动联调规划核查中CodeGraph仍Transport closed，StockWiki没有假设的src目录 | 使用已核实README/pyproject和实际测试入口；不重复检索不存在路径，不把建议布局冒充现有实现 |
| 2026-09-22 | 扩展联调场景E2E前缀后，旧校验器只允许纯字母前缀导致清单校验和4项测试失败 | 允许字母起始的字母数字场景族，保留固定两位编号及非法路径/分隔符拒绝；新增边界测试后复跑 |
| 2026-09-26 | Q04 route-recovery r6独立审查agent在开始审查前遭Codex服务401认证错误 | 本轮无审查结论，不标verified；主线程继续本仓工作，待服务恢复后重试独立复审 |
| 2026-09-26 | 组合式计划一次性增补脚本因既有F05任务ID冲突而断言失败，未写入计划文件 | 改用F06并重新运行；计划1.7.0校验为81卡/187场景，41项计划测试通过 |
| 2026-09-26 | S04初版合成事实模块测试原先预期在读取时拒绝，实际更早在发布封装时拒绝 | 将测试断言移到实际公开封装入口，保留假事实伪装通用模块的拒绝要求；全量回归通过 |
| 2026-09-26 | 自动审批复核拒绝StockQA Q04四文件首次外仓写入，理由是未识别到精确授权 | 未绕过拒绝；做完只读反例/最小修复设计，向用户列明四文件请求授权。用户随后明确授权StockQA全仓写入并要求事先报备，已报备后完成r7修复及独立复审 |
| 2026-09-29 | S06新运行的router 2.0/2.1决策未被拒绝；renderer失败关闭测试patch了已迁移的旧facade全局 | 将新compose切换到当前router执行validator，历史manifest继续走recorded validator；测试改patch真实持有规则哈希的question_manifest owner，并以隔离回归与独立复审验证 |
| 2026-09-26 | 首次调用`python -m unittest tests.test_task_receipts`时tests目录不是Python package | 改用仓库既有的unittest discover入口，不新增无关`__init__.py` |
| 2026-09-26 | P01 schema首轮加入含未转义反斜线的JSON Schema pattern，导致schema JSON无法解析 | 简化schema词法pattern，将完整路径安全规则留给校验器；增加Draft 2020-12 schema与实际CLI测试 |
| 2026-09-26 | 首轮快扫回执追加文档通过PowerShell管道传入Python时发生UnicodeEncodeError，目标未跟踪文档被截断 | 按此前读取的契约原文重建，并以直接patch写入完整增强版；后续不再用本机编码不确定的native pipe传中文 |
| 2026-09-26 | P01独立复审首轮拒绝：plan_version被误用作stale门、test_stage样例字段层级错误、受保护root/根内符号链接可绕过、sidecar缺逐条证据、真实CLI缺恶意命令哨兵 | 移除plan_version freshness比较；修正样例与core hash；限制敏感root、复查解析后目标并拒绝hardlink；增加逐assertion selector/path/hash投影及CLI命令哨兵 |
| 2026-09-26 | P01复审补充发现循环依赖分支可能访问未初始化变量，selector字段可能回显密钥 | 循环命中立即结构化blocked；疑似密钥selector拒绝且不回显。首轮secret selector哨兵发现规则漏掉`secret=`，修正规则后20项定向回归全过 |
| 2026-09-26 | 全仓376项曾在最终P01修订前启动并通过，不能作为冻结快照最终证据 | 保留中间日志，并对当前冻结候选重跑全仓测试；最终状态以新日志为准 |
| 2026-09-26 | P01独立复审发现畸形P00 manifest路径类型可触发TypeError，case sidecar显示输入自报passed，且日志被重复读取有并发不一致窗口 | 对历史manifest路径先严格做类型校验；case status由全部断言审计结果推导；缓存同一份日志hash审计并供门禁复用，新增反例与单次读取测试 |
| 2026-09-26 | P01最终边界复核发现通用receipt契约写入EVO-83兼容窗口语义，但v2 schema没有对应字段；登记根内普通路径仍可使receipt读取配置/任意日志 | 明确兼容窗口由专用EVO兼容评估器验证；receipt每类引用增加用途策略和任务范围检查，拒绝未列入allowed_changes的快照、非专用目录日志/审查报告及未获准的历史路径，并加入打开前拒读哨兵 |
| 2026-09-26 | P01复审发现用途策略只校验符号链接别名、未校验其解析后的普通根内目标；旧P00校验仅排除v2而将v3/未知版本降级为legacy | 对解析后的root-relative目标重跑同一用途/任务策略，新增允许日志/源码别名指向未授权文件且read_bytes不可达的回归；历史只接受无version的已知P00旧格式或显式1.0，拒绝所有其他声明版本 |
| 2026-09-26 | P00重验时发现BASE-01仍把早期5/8宽松断言写成当前行为，已与Q01/S02修复冲突 | 保留早期缺陷为历史基线，改为核实当前评分必须严格为8且unknown仍为null；新旧时点分开记录，旧基线文件不改 |

## Phase 24 checkpoint

### Phase 24: P01 receipt v2 verifier and isolated evidence

Status: complete

- [x] Implement canonical receipt-v2 schema, frozen hashing contract, and read-only verifier for task/case/assertion evidence, purpose- and task-scoped registered-root paths, legacy v1, dependencies, and review freshness.
- [x] Add hermetic temporary-root tests for positive, stale, malformed, skipped, tampered, path-escape, pre-open path-policy denial, no-write/no-execute, historical-bootstrap, detached sidecar behavior, and a real subprocess CLI path.
- [x] Generate P00 immutable context manifest; preserve the legacy receipt byte-for-byte (verified against the captured pre-implementation SHA before sealing).
- [x] Run P01 focused tests (23/23), implementation-plan validation (103 tasks/327 cases/G6), and diff whitespace check.
- [x] Batch-close independent-review findings; the final P01 focused suite passes 23/23 and one comprehensive pre-seal review approved the frozen candidate with no open findings.
- [x] Run the repository offline regression once against the clean frozen snapshot: 379 tests passed, 0 skipped; preserve the interrupted and earlier candidate logs as historical only.
- [x] Generate isolated evidence for every P01 test selector and bind run IDs, cleanup checks, commands, and hashes into the P01 receipt; all 23 selector logs passed, while 18 required assertions map to 14 reused logs.
- [x] Seal P01 core, generate detached self-check sidecar/log, then obtain the separate post-seal evidence review without modifying sealed artifacts.
- [x] Close P01: all RCPT-01/02/03 assertions pass, both review stages approved, and the public verifier returns eligible_to_close=true.

## Historical checkpoint (superseded by the current Next Step at the end of this file)

P01 and current-snapshot P00 are closed. The legacy P00 receipt remains byte-identical; the v2 P00 receipt is eligible at the canonical contracts path. Next inspect C01–C07 receipts and refresh only those whose current task evidence is stale or legacy, then advance to one batched G0 review. Keep milestone-level reviews and avoid repeating the full suite after unrelated small edits.

### Phase 25: P00 current-snapshot baseline revalidation

Status: complete

- [x] Correct BASE-01's stale expectation: preserve the old 5/8 assertion as historical evidence and verify the current strict-8 / unknown-null regression.
- [x] Recheck current local and external repository revisions/status; read external repositories only; record CodeGraph availability and exact relevant source hashes.
- [x] Run the current local score/fact-library validators, targeted strict score-pass-through integration test, implementation-plan regression tests and plan validation. The repository-wide suite already passed once on the final P01 code snapshot; do not repeat it for this documentation/baseline refresh.
- [x] Verify P01 remains `eligible_to_close=true` after the unrelated-owner BASE-01 correction; verify the original P00 baseline report/legacy receipt still match the P01 historical context manifest.
- [x] Obtain one read-only P00 baseline review for the frozen report/source-hash/log snapshot; all 17 source hashes match and no findings remain open.
- [x] Create current `docs/implementation/contracts/receipt-P00.json`; the read-only verifier returns `eligible_to_close=true`. Keep `docs/implementation/baselines/receipt-P00.json` byte-identical.
- [x] Record the one initial report-format binding failure and its resolution with a schema-compatible report from the same independent reviewer; preserve the blocked first self-check as historical evidence.
- [x] Run no repeated product suite: the phase used one focused evidence batch and the already completed P01 final full-suite result.
- [x] Close P00 after review and public verifier success; C01–C07 freshness and G0 preparation move to Phase 26.

Verification cadence for this phase: one focused baseline evidence batch and one milestone-level independent review; no external repository test suite, live provider request, file download, or external write.

### Phase 26: C01–C07 current receipt closeout

Status: complete

- [x] Read-only verification classified the seven old C01–C07 receipts as legacy history; no product suite was repeated for the status check.
- [x] Aligned the missing SC-15, SC-16, and TIME-09 coverage with their public local contract helpers and included the related tests in one shared C01–C07 candidate regression batch.
- [x] Ran that candidate batch once: 188 tests passed, 121 subtests passed, 0 skips; its unique temporary root was verified removed. The seven task-prefixed logs are byte-identical copies with one run ID.
- [x] Obtained one combined C01–C07 independent pre-seal review. All seven reports bind the current owner snapshots and have no open P0/P1/P2 findings.
- [x] Preserved the seven legacy receipts byte-for-byte under `docs/implementation/baselines/legacy/` with a hash manifest; issued current v2 receipts at the canonical contract paths.
- [x] Ran one public recursive verifier on C07, which recursively checked C01–C07 plus P00/P01 and returned `eligible_to_close=true` with no blockers. Detached chain sidecar: `docs/implementation/contracts/validation-C07-C01-C07-chain-r1-2026-09-26.json`.
- [x] Kept receipt evidence task-specific while grouping product tests and review at the milestone level; no test rerun was needed for the reviewer-side canonical-sort correction.

Verification cadence for this phase: one shared regression batch, one combined C01–C07 pre-seal review, and one recursive dependency-chain verification. No per-card review cycle or repeated full suite.

### Phase 27: G0 current-snapshot independent re-review

Status: complete_for_local_contract_scope

- [x] Refresh the G0 review packet and invariant matrix to plan 1.9.8, current v2 dependency receipts, shared test runs, and historical G0-01–G0-09 findings; label old packet/review artifacts as historical evidence.
- [x] First independent review found a read_first-scope omission; fixed it in one batch by including both named design documents, adding a fail-closed drift regression, and running one focused G0+plan batch (94 passed, 55 subtests, 0 skips). No full product suite was repeated.
- [x] The next review found ID-02 tested a local branch rather than the public identity validator. Fixed it in one affected-path batch: the public `cv.validate_entity` rejects a merged candidate with a precisely bound issuer receipt stating `same_legal_issuer=false`; the C01 identity file passed (16 tests, 31 subtests, 0 skips) and C01 r2 independent review approved.
- [x] Reissued C01 and dependent C03–C07 receipts for the corrected source/evidence chain; archived superseded r1 receipts and recursive sidecar byte-for-byte. The current C07 recursive verifier reports C01–C07 plus P00/P01 eligible with no blockers.
- [x] Final receipt audit found BASE-02 was listed on G0 although P00 is its unique case owner; corrected G0 to own only REV-01/02/03 and keep BASE-02 strictly as upstream evidence. Bumped the plan/catalog to 1.9.8 and added the structured final-review JSON to the explicit manifest exclusions.
- [x] Run one focused G0+plan regression batch and plan validation on 1.9.8; the 94-test/55-subtest batch passes with zero skips. Exclude the canonical post-seal G0 sidecar path and test the exclusion; regenerate and verify the C07 recursive sidecar and final G0 candidate.
- [x] Final independent review approved the exact 646-file 1.9.8 candidate at SHA-256 `e6ada748839aee76c725653cc04af52789ccf63fe8fbeef20756587f414c2e7a`; report bound to the candidate and one-file receipt snapshot, with no open P0–P2 findings. The public manifest verifier reports zero errors.
- [x] Created the G0 v2 receipt for only REV-01/02/03 and ran the public recursive receipt verifier. It returns `eligible_to_close=true`, no blockers; receipt core SHA-256 `fc0f170294bdf71bec7cafdc69ba19ea8157be596a8f9860d916747435b88e7d`; detached sidecar SHA-256 `263787ac8f89f632f1d72f3dbdcd7390f51fbb34550aeb31a20f0751f6e398df`. External live/provider/runtime behavior remains pending its planned owner tasks.

Verification cadence for this phase: reuse the existing shared C01–C07 regression and G0 candidate/plan regression; after the reviewer found the ID-02 semantic-test defect, rerun only the affected C01 identity test file and its independent owner review, then refresh the hash-dependent receipt chain and perform one final G0 review. Do not repeat the full product suite or add per-card reviews.

当前计划版本1.10.8，107卡/340场景/53条约束/G6。2026-09-27 P01回执语义修复后，P01、P00、C01—C07依赖链及G0候选均已按新快照重封。当前G0 671文件候选SHA-256 `468cf1335811fc735068e7d88761ea166f3dbd4710c0d7b36ae665884c08263e`，manifest零错误；独立里程碑复审无开放发现，G0 v2回执与公开递归验证均`eligible_to_close=true`。S01最新回执也已在修复旧manifest恢复映射问题后刷新并公开验证eligible。本地合同范围已闭环；外部写入、live E2E和生产运行能力仍待后续owner任务。G0的BASE-02唯一归P00拥有；G0仅拥有REV-01/02/03。

### Phase 28: S01 metric映射与作用层编排

Status: complete_for_local_implementation_scope

- [x] Phase 29已刷新P01下游回执及G0候选并通过公开验证；确认S01本地实现快照包含metric映射、24核心构念/类型替代、证券scope、诊断与恢复独立展示，以及确定性编排/兼容导出。
- [x] 保持单一权威题库来源和旧manifest读取行为；对历史形状兼容、核心分数不被附加题稀释、关键风险不被均分冲淡补齐回归。
- [x] 新增MATRIX-07 quick/full矩阵场景和8×6公司类型/生命周期组合回归；SC-08/10/11与兼容导出一并在最终定向批次验证，7项通过、0跳过。
- [x] 相关回归批次91项通过、0跳过；题库校验48个模块/222题；两批pytest临时目录均确认清理。
- [x] 独立里程碑审查通过且无开放发现；S01 v2回执绑定当前实现快照、测试日志和G0依赖，公开递归只读验证`eligible_to_close=true`、无blocker。

本阶段只关闭本仓确定性实现/兼容范围；StockQA真实模型搜索、StockWiki刷新接续、UI、生产批量运行仍由后续任务验收。

### 当前证据刷新状态（2026-09-27）

- S01当前快照已重新封存：恢复观察从题目级`replaces`重建映射；旧索引漂移或题目元数据缺失时显式`needs_verification`，原评分摘要不变。70项/166子断言回归通过，6项/4子断言具名验收通过，独立复审无开放发现，public receipt verifier返回`eligible_to_close=true`。
- S05/MOD-17的24项当前注册器测试与独立复审通过；v2 receipt已更新并只剩S04当前receipt依赖阻塞。基线文件SHA及48模块信任列表未改变。
- S04/MOD-14仍需补齐完整atomic断言、当前快照日志/独立审查及v2 receipt；完成后刷新S05依赖并再次递归验证。


### Phase 29: P01上游回归引用语义修复与依赖链重封

Status: complete_for_local_contract_scope

- [x] 区分任务自有case与上游回归引用case；约束引用owner必须在传递依赖闭包，并以独立hash绑定引用定义。
- [x] 覆盖无关owner、缺少引用hash、定义变更、畸形依赖图、多跳依赖与旧v2 owner-only兼容；29项P01专项测试通过，计划结构校验为103卡/327案例/G6。
- [x] 独立实现复审批准，无开放发现；以当前实现快照更新P01 v2回执，14个唯一验收选择器均独立运行、零skip并验证临时目录清理；公共只读回执校验eligible。
- [x] 完成独立封存后证据复审并保存不回写receipt的报告：`docs/implementation/reviews/P01/postseal-evidence-review-r2-upstream-case-2026-09-27.json`。
- [x] 基于新P01 core检查P00并逐项刷新C01—C07递归依赖证据；公开验证均eligible，C07 r5递归sidecar无blocker。
- [x] 重建G0候选并通过manifest校验：671文件，SHA-256 `468cf1335811fc735068e7d88761ea166f3dbd4710c0d7b36ae665884c08263e`。
- [x] 当前G0候选独立里程碑复审通过，无开放发现；重签G0 receipt并运行公开递归校验，receipt与detached sidecar均绑定当前快照，结果eligible_to_close=true。

本阶段只关闭本地计划/契约范围；不代表live搜索、外部仓库集成、生产队列或UI已验收。旧G0候选仅保留为历史证据；S01当前已解除依赖链门控。

### Phase 30: 实施验收与审查节奏收敛

Status: complete_for_planning_only

- [x] 核对当前入口说明、测试策略、审查交接和receipt v2契约，识别“每卡先关闭再开始下游”的误读及正式证据与开发自测混用风险。
- [x] 明确任务卡仅限制owner/改动范围；接口冻结后允许连续推进下游实现，未通过者保持未关闭，不越过里程碑依赖门。
- [x] 统一大节点节奏：变更组定向/集成批次、G0—G6合并审查；复杂case仍逐断言留证，一批日志可映射多条断言；修复仅回归受影响路径。
- [x] 保留P01封存前/后的专用审查例外和真实联网/费用/迁移的高风险定向验证；不把该例外推广为每张任务卡的门槛。
- [x] 同步README、test-strategy、review-and-handoff、task-receipts及进度记录；未增删任务/验收场景/固定约束，未更改外仓授权。

## Next Step

### 2026-09-30 当前执行状态

- Q02首个提供商实现的任务级验收已在精确StockQA工作树快照通过：MiMo公开CLI真实搜索、LLM-02/LLM-11离线检查及同快照独立审查均已记录在`progress.md`和`docs/implementation/contracts/validation-Q02-MiMo-live-E2E-2026-09-30.md`。旧任务回执已退役、验收目录为规格；不刷新receipt或改规格状态。该结果不关闭G1或跨仓链路。
- company-wiki IQS独占施工卡本仓步骤1—4已完成，报告见`docs/implementation/reviews/IQS-lane/construction-card-closeout-2026-09-29.md`；第5步/G2b仍等待StockWiki真实公开身份snapshot/mapping DTO及serializer golden。交接包列明当前分支/commit、schema/CLI版本、校验命令/结果、golden格式与跨仓正反例，见`docs/implementation/reviews/IQS-lane/G2b-handoff-2026-09-29.md`。不得重复实现步骤1—4、伪造StockWiki正例或代改StockWiki。
- 卡片SHA-256仍为`516077a6e9af3da41a121f5977225cc662035badcb3bc963dfb4dfe12f32be0a`。基线792条路径至delta快照843条：新增53、已有文件哈希变化22、缺失2；两项缺失均是退役活动receipt文件，已由原哈希归档副本解释。delta明细见`docs/implementation/reviews/IQS-lane/worktree-inventory-delta-2026-09-29.json`。
- 卡片隔离回归205 tests / 351 subtests、0 skip；计划校验107 tasks / 366 cases / G6 valid，临时根清理已确认，日志见`docs/implementation/contracts/validation-IQS-card-closeout-2026-09-29.txt`。
- 已恢复S06本地工作：将新执行route gate切到当前router执行校验器，保留历史manifest的历史校验路径；修正renderer失败测试的mock patch位置。S06聚焦回归57 passed、0 skip，独立只读复审无P0–P2，计划校验107 tasks/366 cases/G6 valid；日志见`docs/implementation/contracts/validation-S06-current-fix-2026-09-29.txt`，范围说明见`docs/implementation/reviews/S06/current-router-execution-fix-2026-09-29.md`。
- S06仍因StockQA→StockWiki真实事务ACK、router 2.1真实历史快照和跨仓端到端验收而partial。旧工程task receipt v2/P01签收机制已退役；不能以刷新C01—C07旧回执作为当前门槛。StockWiki本轮只读。

### 当前下一动作

- Q03首轮快照回归通过166项后，独立复核发现一个P1：JSON数组/对象类型的`status`使parser抛`TypeError`，导致公开CLI丢弃已完成搜索回执。已按TDD修复并补事件级回执断言，完整Q03隔离回归170项通过；两轮独立只读复核均未发现未解决项，最终复核匹配三份当前SHA。Q03解析与结果回执路径的任务级验收已通过。初始报告parser单测SHA有单字符笔误，已更正；精确命令、SHA与审查边界见`docs/implementation/contracts/validation-Q03-current-snapshot-2026-09-30.md`。该任务级验收不代表G1/全项目、其他模型或跨仓链路完成。
- 当前下一步进入Q04剩余运行语义：先沿StockQA公开CLI和adapter追踪`OrderedSearchProviderCascade`的实际构造/调用路径，再围绕PAR-11同路由槽满等待及LLM-10运行中policy revision边界补行为测试；不要把旧`ProviderCascade`或配置保存单测当作生产路由接线证据。不访问网络、不读密钥、不修改未报备的StockQA文件。

## 2026-09-29 — S06 路由执行门与测试owner修复

- 新的v2问卷组合误用`validate_recorded_route_execution`，该validator用于读取已存历史记录，不能授权新执行；现改为`validate_route_for_execution`。旧manifest历史读取仍保留recorded validator，避免把历史兼容和新派发资格混为一谈。
- renderer历史版本失败关闭回归测试在校验helper迁移后仍patch旧facade，未命中实际owner；已改为patch `question_manifest` 中的规则哈希绑定。独立只读审查核对新执行/历史读取两条路径、router 2.0/2.1拒绝、输出未写入断言及renderer owner，未发现P0–P2。
- 当前S06聚焦回归命令覆盖routing、StockQA adapter、依赖闭包、RouteCompositionTests及历史renderer拒绝测试；验证日志：`docs/implementation/contracts/validation-S06-current-fix-2026-09-29.txt`。该离线回归不证明真实StockQA到StockWiki ACK、真实router 2.1归档样本或跨仓运行完成。

### 2026-09-27 执行状态历史快照（已由上方2026-09-29状态取代）

- P00、P01、C01–C07当前receipt已逐项通过public verifier；G0候选因版本/依赖回执更新而需要重封，旧G0→S01/S04依赖引用不能沿用。
- G0候选manifest现根据`tasks.json`动态排除G0所有传递后代的receipt与`validation-{task}-*`输出，保留前置receipt及实现/测试文件，以避免G0与下游回执的哈希循环。
- 独立复审发现依赖ID fail-closed、验证通配符实际匹配及下游审查产物稳定性三项问题；均已修复并经独立复审批准。当前13项隔离G0测试通过、0跳过、临时目录清理已验证；535文件候选manifest零错误。
- 最新G0候选SHA `106f3e94...`、receipt aggregate `f8a20a7e...`；独立报告SHA `ca9ccbf9...`。S05 MOD-17五文件当前快照（包含S01/S06后续变化）也已独立复审批准并重签。
- 公共verifier当前已依次确认P00/P01/C01–C07/G0/S01/S04/S05 eligible。下一步恢复不依赖未授权外仓路径的Q02/Q06剩余实现，并按大节点测试/复审；StockWiki后续写入仍限于已明确授权路径。

S03/DUR-04的独立复审已完成：当前3.2.0归档包回放与错误版本头拒绝有隔离测试，但仓库及当前git历史均未找到真实3.1.0 metric manifest；复审将此列为P2范围限制。因此不能据此签发宣称覆盖真实3.1.0兼容性的verified回执，也不应再把它写成“待复审”。保留S03局部实现完成、历史数据验收未证实的状态；后续若找到可信历史样本，再补充真实回放验收。

S06路由信任边界已推进至router 2.3：答案内容hash绑定执行回执，StockQA公开结果经适配器接入解析/组合；12项隔离信任边界测试、14项CLI集成测试及3项离线生产链E2E通过。旧router 2.0真实归档可读，2.1仍只有合成兼容路径。S06仍未生产闭环：当前回执/依赖链、StockQA/StockWiki真实事务ACK与用户授权的跨仓端到端验证未完成。

当前优先推进Q02与Q06中可在既有授权内完成的部分。Q02：MiMo OpenAI-compatible Chat Completions联网搜索适配已落入StockQA当前工作树，严格绑定同一响应的`url_citation`、模型ID和response ID；同步/异步路径及CLI回执均有离线覆盖。初始焦点unit+integration批次151项通过；一次付费MiMo公开CLI联网E2E通过并确认搜索引用和临时目录清理。独立复审发现异步route alias可能污染真实provider归属；现已从已证实receipt归一真实provider，并以`provider_config_ref`保留route alias，新增回归后受影响unit+integration批次171项通过，整改follow-up确认无遗留问题。Token Plan endpoint仍返回`webSearchEnabled=false`，此次成功仅证明pay-as-you-go endpoint/key路由；MiMo变更及回执仍未封存，不因此关闭Q02。测试执行需关闭本机pytest `base_url`第三方插件，以免其session fixture与测试参数重名；项目配置未改。DeepSeek官方示例中的tool calls由调用方执行工具，不把它当作内置联网搜索备用模型。最新MiniMax Anthropic快照已修复布尔status与未知server tool误验收，160项隔离unit/provider/CLI集成测试通过，精确哈希复审无P0–P2；一次当前快照live CLI请求在HTTP响应前ConnectionError，未生成可验证搜索回执且未重试，所以Q02仍partial，细节见validation-Q02-fail-closed-hardening-2026-09-27.md。

2026-09-27只读回执审计发现当前闭环的首个依赖阻塞是P01 receipt stale：其实现快照仅`docs/implementation/contracts/task-receipts.md`哈希从081ffa...变为e6dc...，其余schema/CLI/example/test快照一致，导致`evidence_hash_mismatch`与`review_stale`。P00仍`eligible_to_close=true`；P01阻塞C01–C07，再传递阻塞G0和S01。S04的MOD-02和MOD-14.A01–A10有逐原子selector/log/hash/临时环境清理证据、旧快照独立review `approved`，但复核又发现当前`route-decision.schema.json`相对S04封存快照已变更（旧hash 1bca...，当前9c40...），所以S04除依赖失效外也存在自己的`evidence_hash_mismatch`/`review_stale`，不能只刷新依赖就关闭。下一步先复核并刷新P01，再在同一里程碑批次里重新验证S04受影响schema边界、更新其独立review/receipt，并批量刷新必要的C01–C07/G0/S01链；之后回到不依赖W05/UI外仓写入的任务。

搜索引擎应与回答模型解耦，并拥有独立的、可版本化的搜索供应商策略/配置模板（不能复用回答模型优先级文件来表达搜索额度）。用户提供的套餐额度为Brave最多50 requests/second、月请求不限，以及Tavily每月1,000 credits；因此Brave适合作为批量快扫主检索后端，Tavily应按月度credit预算用于复杂/歧义问题或选择性补源。路由器分别执行Brave速率限制和Tavily月额度预留/结算；“月请求不限”不等于无速率限制，“1,000 credits”也不得在尚未核实套餐计费规则前擅自折算为1,000次搜索。仅采用供应商明确返回的用量/重置元数据结算；未提供时使用用户可设的保守月度预算上限并标记估算/未知，额度耗尽时保留待办并按策略切换或暂停。保存供应商身份、策略版本、额度来源/核验日期、用量和最小来源回执；密钥只通过环境变量引用，不写入配置、日志或计划。在核实对应套餐对保存搜索内容的授权前，不长期保存原始搜索响应，快扫持久化限于结构化结论与最小必要来源元数据。该策略、去重与回执契约纳入后续Q02/Q06设计。

2026-09-27核对供应商官方文档：Brave按key/套餐返回`X-RateLimit-Limit/Policy/Remaining/Reset`并以一秒滑动窗口执行速率限制，超限返回429；文档示例明确monthly limit为0可表示unlimited。当前公开Pricing页显示Search为预付按请求计费、50 req/s，与用户报告的“月请求不限”可能是账号/旧套餐差异；不得据公开页替用户改写其真实权益，也不得把用户文字硬编码为无限额度，应在首次连通时读取脱敏响应头并允许用户填写控制台确认的account entitlement。Brave官方FAQ还要求计划明确授予storage rights才可保存全部或部分API结果；确认授权前，搜索结果、snippet及从结果中抽取的URL都只在内存中使用，落库按供应商条款允许范围执行。Tavily官方Pricing确认1,000 credits/月，官方帮助页说明Basic Search为1 credit、Advanced Search为2 credits；预算必须按实际模式或供应商usage字段预留/结算，不能按调用次数估算credit。来源：[Brave限流文档](https://api-dashboard.search.brave.com/documentation/guides/rate-limiting)、[Brave当前公开Pricing](https://api-dashboard.search.brave.com/app/plans)、[Brave存储权说明](https://brave.com/search/api/)、[Tavily Pricing](https://www.tavily.com/pricing)、[Tavily Basic/Advanced计费说明](https://help.tavily.com/articles/6938147944-basic-vs-advanced-search-what-s-the-difference)。

Q06：SQLite待办/租约与同步transport边界实现、测试及独立复审已完成；公共CLI尚未绑定生产work item。该绑定必须消费W03提供的权威身份投影，不能以CLI输入或StockQA本地推断替代。Q07现已增加逐题持久检查点和基础续跑原语，但真实runner接线及PAR-04单次多题dispatch映射未完成；Q09预算/并发底座已有第一段实现及436项隔离回归，真实供应商费用解析、完整runner策略接线和最终独立复审仍开放；Q06还依赖W05 ACK和异步路径。StockWiki W02/W03的精确8文件首段已通过最终哈希独立复核且无P0–P2；候选身份仍未晋级为权威身份投影，因此Q06生产runner接线仍需后续精确桥接范围。继续推进不依赖该桥接的本地与已授权StockQA工作；W05、StockWiki UI及其余外仓路径仍须先取得精确授权。



### Q09更新（2026-09-27，替代前文阶段摘要）

- 已在获批的StockQA范围内完成同响应provider usage规范化、脱敏回执持久化、空费率卡schema/template、精确provider/model/pricing-reference/currency匹配的Decimal费率解析器，以及公共runner到既有预算账本的解析器接线。没有硬编码供应商价格；缺失或无效用量/费率继续保守保留预算并暂停派发。
- 首轮独立设计审查发现三个P2：无id搜索事件少计、JSON rate literal经float损失精度、budget reconciliation replay可更改终态。已修复并增补固定反例：可分类的无id事件纳入usage，无法分类或显式usage小于观测时保留unknown；rate card直接Decimal解析并用整数精确算术/向上微单位舍入；work-store v4新增不可变终态账本，同结果重放幂等、不同结果拒绝，旧settled历史迁移为`legacy_unverified`。
- 修复后受影响回归provider/runner **371 passed**、budget/store **86 passed**，严格拆分进程且warnings-as-errors，两个TEMP根均清理；Ruff、Black无缓存、费率配置JSON及限定diff检查通过。独立follow-up复审核对8个核心源文件/测试/文档哈希，未发现P0-P2；Q09仍partial。
- Brave 50 requests/second、月请求数不限及Tavily 1,000 monthly credits是用户给出的搜索服务预算输入，与LLM token/内置工具搜索费用分开管理，且Tavily credits未核验前不折算成请求数。正式账号费率卡和账单核对、生产预算闭环仍未完成。详见[Q09 usage/rate-card验证日志](docs/implementation/contracts/validation-Q09-usage-and-rate-cards-2026-09-27.log)。


### Phase 31: G0依赖回执刷新与股票池输入权确认

Status: complete_for_local_receipt_scope

- [x] 使用planning-with-files解析器确认当前采用仓库根目录legacy计划；检查`git diff --stat`并从现有计划恢复状态。
- [x] 复核P00、P01、C01–C07与G0公共回执；当前均为`eligible_to_close=true`。G0候选manifest为536项、`errors=[]`。
- [x] 查明G0回执更新后的字节hash导致S01/S04/S05的依赖引用过期；三个任务自身实现快照、测试日志和独立review均未发现哈希漂移。
- [x] 只刷新S01→G0、S04→G0/S01、S05→S04/S01的当前回执引用和core hash；公开递归校验三者均为`eligible_to_close=true`，未重跑产品测试或改动实现。
- [x] 记录用户指定的股票池输入边界：约2000家公司只是覆盖目标，初始池名单由用户提供；进入O01前必须使用用户给定的池子，不由实施者自行挑选公司。名单尚未提供，因此不启动选股或批量扫描。

当前本地回执链推进至S05；真实搜索、生产StockWiki导入/ACK、UI与跨仓端到端状态不因本阶段而改变。

### Phase 32: MiniMax 官方区域端点修正与 Q02 当前 CLI 诊断

Status: in_progress

- [x] 在用户已授权的 StockQAbyLLM 范围内，将 MiniMax Anthropic Messages 中国区端点和相关有效测试样例从错误的 `api.minimax.cn` 更正为官方 `api.minimaxi.com`；保留 `api.minimax.io` 全球端点及错误域名负例。
- [x] 为 live E2E provider 断言补充已有脱敏摘要，并让 `insufficient_evidence` 的安全原因进入摘要，避免 provider 兼容性失败只留下空泛断言。
- [x] 在 API key 和 live 开关均移除的独立临时目录中运行 MiniMax/MiMo provider、CLI 集成焦点：34 passed / 125 deselected；live 文件非联网辅助测试：2 passed / 4 deselected；覆盖率文件哈希保持不变且 TEMP 根清理。
- [x] 使用临时配置与 stubbed HTTP 的公开 CLI 路径确认当前代码解析 `minimax / MiniMax-M3 / api.minimaxi.com/anthropic/v1/messages`，能力检查为 true，成功产出执行搜索状态和来源回执；此项是离线集成证据，不是供应商 live 验收。
- [x] 在精确复刻 Anthropic live fixture 的公开CLI临时子进程中，保留空配置key并只继承 `MINIMAX_API_KEY`；HTTP由本地stub替代。子进程判定 `supports_web_search=true`、路由到 `api.minimaxi.com/anthropic/v1/messages`，stub请求与来源回执成功。`STOCKQA_MINIMAX_ANTHROPIC_BASE_URL` 未设置；该项排除了基本CLI参数/环境key导致能力检查为false，但不证明供应商联网。
- [x] 在此前用户授权下，对同一单题live CLI做了一次受控全球端点验收（`api.minimax.io/anthropic/v1/messages`）。pytest确实启动目标live节点，但项目级 `--cov-report=html` 在收尾时因写入 `StockQAbyLLM/htmlcov/style_cb_ed8d5379.css` 权限错误触发internal error，遮蔽单项断言摘要；该次结果记为 `outcome_unknown`，可能已发送请求，不重试。临时测试根已移除；项目内 `.coverage`/`htmlcov`时间戳仍为当天08:38 UTC（早于约22:55 UTC测试），未发现本次写入迹象。
- [ ] 重跑 StockQA 精确差异检查和当前快照独立审查；Q02/LLM-01维持 partial，不将离线stub、历史live回执或此次outcome_unknown标为搜索通过。后续live pytest命令须以 `-o addopts=`隔离项目级覆盖率HTML输出，且须先有不重复派发的充分理由。

当前用户仍掌握初始股票池名单；Phase 32 与选池、O01导入及批量扫描无关，不推断或生成股票名单。

### Phase 33: S03归档评分锚点回归补强

Status: complete_for_local_test_scope

- [x] 在 `tests/test_question_sets.py` 的真实不可变发布包回放测试中，明确断言归档运行仍产出原评分；对同一题目ID的prompt或rubric版本篡改均要求拒绝，不允许把已保存分数按改写后的题义解释。
- [x] 使用独立 pytest basetemp、关闭仓库级 addopts/覆盖率输出和 warnings-as-errors 运行焦点测试：1 passed、2个篡改子用例通过；唯一临时测试目录已清理。
- [x] 保留历史范围限制：仓库虽有初始提交的3.0.0题库源，但无真实3.1.0评分manifest；本测试强化当前归档契约，不宣称证明真实3.1.0迁移兼容。
- [x] 再次确认 O01 未开始：首批名单由用户提供。已请求用户指定现成文件路径/市场或后续发送名单；不自行创建、扩充或扫描股票池。

这项本地测试补强不改变S03整体partial状态；StockWiki刷新计划和跨项目E2E仍未执行，真实3.1.0历史回放仍未验证。


### Phase 34: S06原始答案绑定与路由版本兼容

Status: complete_for_local_test_scope

- [x] 以红测复现resolver拆分候选/答案hash/执行回执可被错配，以及schema漏拦截状态/分数矛盾。
- [x] resolver边界改为只接收单一完整原始答案，由同一答案解析候选、分类置信度和SHA-256；StockQA公开结果回执与答案必须绑定。
- [x] router 2.3 schema 1.3/protocol 3向后兼容同协议后续2.x router版本；更新MOD-19与文档。
- [x] 定向负例4 passed / 3 subtests；完整路由单测33 passed / 23 subtests；隔离S06 CLI集成14 passed；适配器单测5 passed。离线producer E2E在该阶段3 passed。
- [x] 完整计划校验valid（S07加入前103任务/328案例；现已升至104/331）。无真实API、公司扫描或外仓写入。

### Phase 35: S07题库提示渲染单向化与分层回归

Status: complete_for_local_test_scope

- [x] 新增S07、MOD-20—22，将提示纯模块、公共接口集成和本地离线producer E2E列为不同owner case；计划增加`e2e`层级。
- [x] 写依赖方向红测并复现：question_sets延迟导入standard_answers生成prompt，缺少独立纯提示模块。
- [x] 将提示渲染函数移到`question_prompts.py`；question_sets/standard_answers共享它，两个旧入口保留兼容名。保持active release的renderer 1.0.0和SHA-256不变，不产生无语义差异的新package。
- [x] 提示单测4 passed / 4 subtests；标准答案单测23 passed / 3 subtests；计划结构单测82 passed / 58 subtests；本地producer E2E 3 passed。首轮明确检测到renderer hash漂移并修复。
- [x] `tests/test_question_sets.py`完整回归67 passed / 170 subtests；S07后S06 CLI集成14 passed、0失败/错误/跳过、`TEMP_CLEANED=True`。标准答案23 passed / 3 subtests；producer E2E 3 passed。
- [x] 依赖方向与提示模块Ruff检查通过；当前计划validator valid（104任务/331场景），计划单测82 passed / 58 subtests。
- [x] S08已将UTF-8 JSON、source catalog、URL与profile helper下沉为共享契约；不可变manifest验证和历史fingerprint仍是明确的后续拆分边，不能宣称全项目已完全松耦合。
- [ ] 用户尚未提供首批公司池或真实E2E样本；不自选名单、不导入、不扫描。

计划当前为1.10.9，107任务/354场景/54约束/G6。更改计划版本与owner场景后，旧的G0/G6快照审查不能自动视为覆盖本版；在相关大节点重审前保留旧报告作为历史证据。

### Phase 36: S08题库契约下沉与答案构建器依赖收敛

Status: complete_for_local_test_scope

- [x] 以MOD-23红测固定当前`standard_answers`经`question_sets`访问JSON、catalog、URL和profile helper的边，并将仅存的manifest/fingerprint边白名单化。
- [x] 新建无上层依赖的`question_library.py`接管source catalog、profile和URL；以单独的`json_io.py`供题库/提示层共享UTF-8 JSON读写；`question_sets`保留签名兼容且正确传递可注入ROOT。
- [x] `standard_answers`改为依赖question_library的稳定helper；复杂不可变manifest验证与question fingerprint仍是显式后续拆分边，不用动态导入隐藏。
- [x] 同一大节点批次执行纯库单测、CLI/答案接口集成、离线producer E2E和计划校验；确认renderer与历史观察未漂移，密钥/网络/下载目录未触碰、临时根已清理。
- [x] 首批股票池由用户提供；本阶段不选公司、不导入、不扫描。


## Phase 37: S09已发布题目指纹契约下沉

- [x] 先写S09依赖边界红测；确认答案构建器经question_sets直接调用历史指纹，记录旧格式缺省版本标记与当前2.0.0包的原始基准；仓内没有真实归档1.x包，不将投影测试说成历史回放。
- [x] 抽出`question_fingerprints.py`唯一实现；question_sets保留旧签名委托入口，standard_answers改为直接依赖下层契约。
- [x] 为本卡增加MOD-26/27/28三个验收场景，覆盖单元、集成与本仓离线E2E，并将S09接入G6依赖。
- [x] 运行S09大节点受影响回归：首次长回归189项通过、237个子断言通过，唯一失败是S08边界测试仍要求旧fingerprint边；更新预期后复跑13项通过/2个子断言通过，包含观察集成与离线producer E2E。计划validator有效（106任务/337场景/G6），新模块与边界测试Ruff通过。
- [x] 独立只读复审发现MOD-27对旧包覆盖描述过宽；已改成仅声明当前包观察验证、固定不可变package ID，并补齐旧包装器原签名/关键字/缺省版本分支测试。Follow-up确认P2关闭，无未关闭P0–P2。无真实公司、网络/API、文档下载或外仓写入。

## Phase 38: S10清单/选择契约与答案构建器依赖拆分

- [x] 将模块选择和question budget规则迁入question_selection.py，manifest metric映射与语义校验迁入question_manifest.py；question_sets保留旧签名兼容入口。
- [x] 将screening renderer及其renderer hash归入question_prompts.py；standard_answers静态依赖manifest/library下层契约，不再导入question_sets。
- [x] 增加MOD-29/30/31，分别锁定单元依赖方向与兼容签名、发布观察集成与伪造manifest拒绝、离线producer端到端及临时根清理；修正renderer验收选择器以指向真实测试。
- [x] 大节点定向回归完成：计划单测85项、prompt边界4项、manifest边界3项、发布观察集成3项、producer E2E 3项通过；Ruff、py_compile和限定范围diff检查通过。qsets长全套曾有两条精确错误文案断言，修复后分别通过，但未重跑整套。
- [x] 无公司池导入或扫描、无网络/API、无财报下载、无外仓写入；首批股票池仍由用户提供。

## Phase 39: 公司、证券与挂牌身份解析设计补充

Status: design_and_local_contract_v2_1_complete_cross_project_pending

- [x] 只读核查 Dayu ticker 规范化/局部 company_id 与 StockInfoDLSimple A股代码/CNINFO orgId 映射的边界；不把任一来源 ID 当全局发行人主键。
- [x] 设计 opaque、不可变 issuer ID；namespaced 外部编号 claim；非唯一、带类型/有效期/来源的名称 alias；venue/time-qualified listing；unresolved/provisional/verified/conflicted/superseded 状态和独立扫描资格。
- [x] 规定发行人、股份/工具 Security、交易 Listing 三层；同名/同品牌/裸ticker/模糊模型结果不自动合并；LLM只能推荐并整理证据；历史身份修订不回写 Observation。
- [x] 将架构和反例矩阵写入`docs/implementation/reviews/W03/identity-resolution-architecture-2026-09-28.md`并链接到W03既有设计。
- [x] 同步到 C01/W01/W02/W03/W04/W05、C04/C06/Q06 的任务case和 I54 约束；设计同步时计划版本1.10.9共107任务/354场景/54约束，旧C01回执不再覆盖新契约。
- [x] 本地 identity schema 发布2.1.0：Entity/issuer、Security、Listing分层；v2.0.0显式保留为历史读取格式。
- [x] `validate_entity` 只接受2.1.0新写入；历史v2.0.0走`validate_identity_v20_read`，不再授权写入/扫描。
- [x] 将Entity/Security/Listing IDs约束为类型前缀UUIDv4，挂牌绑定有效区间并拒绝反向/重叠时段；增加不可误写为issuer等价的集团关系及单步递增、带来源证据的追加式身份事件契约。
- [x] 加强挂牌、证券归属与引用、来源绑定、provisional范围回执、verified发行人/挂牌回执、ADR关系和ticker/MIC歧义的契约回归。
- [x] 同步本地C01契约文档、C01准确允许文件范围和ID-02/ID-08验收预期；计划升至1.10.10（107任务/354场景/54约束）。
- [ ] 在完成最终快照和独立复审后刷新C01 v2 receipt；当前P01 v2 receipt因global boundary hash陈旧而阻断依赖关闭，不能用历史C01回执代替。
- [ ] 运行本轮完整身份/计划受影响回归，并在复审后记录当前测试与源码快照证据。
- [ ] 同步完成后再继续 W01 红/绿修复和 W02/W03 实现；仍使用用户授权的精确 StockWiki 文件范围，不导入或扫描尚未确认的候选池。

本阶段只完成设计工件与只读上游核查，不代表身份 resolver、三层存储、UI 或跨仓接线已实现。StockInfoDLSimple CodeGraph 索引由用户明确授权后建立；Dayu/StockInfoDLSimple 业务源码均未改。

## Phase 40: 分离法律发行人与分析范围并修复身份契约复审发现

Status: local_contract_and_tests_updated_receipt_chain_pending

- [x] 在身份设计中明确 `entity_id` 只代表法律发行人，新增独立 `analysis_subject_id + analysis_subject_revision` 标识快扫研究范围；普通经营题以并表/独立报告范围为对象，证券报价题仍绑定 Security/Listing。
- [x] provisional subject 仅锚定权威库确认的单一精确挂牌，禁止从暂定 issuer、集团控制关系或 LLM 建议推导合并报告范围；已核实 issuer 才能建立 standalone/consolidated subject。
- [x] C01 本地契约包升至2.2.0；Entity writer 仍只接受2.1.0，Subject 独立版本1.0.0。Work/Observation/C06消费的subject字段作为后续C04/C06/W05门槛，不静默迁移历史数据。
- [x] 独立身份复审与两轮follow-up的反例均已纳入本地修复/覆盖：全球市场代码与MIC辖区、verified claim证据/有效期、缺MIC重叠ticker失败关闭、security_added精确影响ID、退市与retired source binding、身份事件前后快照、AnalysisSubject并表范围回执和成员差异、v2.1 ID-02/08覆盖。
- [x] 针对两个最终边界追加回归：身份事件快照的foreign/dangling Security引用均失败关闭；primary issuer切换只允许原主/新主纯role互换，不能夹带第三方成员信息变更。
- [x] 本轮身份与G0/计划合并回归为170 passed / 160 subtests；新增foreign-Security专测后身份文件为36 passed / 50 subtests。identity schema Draft7、计划校验、Ruff、`py_compile`与`git diff --check`通过。
- [x] 独立只读终审未发现未关闭P0—P2；审查仅针对本地身份契约/修复快照，不代表外仓resolver或全链完成。
- [x] 同步 C01、C04、C06、W02、W03、W05 任务边界与新增 ID-18—ID-26；计划版本1.10.12，107任务/363验收场景/55约束。跨项目文件仍只读。
- [ ] 依据P01先后依赖门刷新有效receipt链，再生成当前C01 v2回执并通过公开递归验证；当前历史P01/C01回执不覆盖1.10.12语义快照，C01仍partial。
- [ ] 身份registry本身仍需owner接线：从受控、版本化来源加载完整ISO/MIC市场映射和有效期/撤销语义；consolidated scope receipt由权威存储事务维护。当前validator只对注入的可信映射/回执做语义校验，不证明注册表完整、签名真实性、全库唯一性或并发CAS。
- [ ] 之后按既有批准文件范围推进StockWiki W01修复及W02/W03；C04/C06/W05消费者实现仍需沿本地契约分开推进，不能提前声称跨仓完成。


## Phase 41: 搜索context、30题打包、缓存与成本真实对照

Status: experiment_specified_waiting_for_M3_prerequisites

- [x] 将用户要求拆成检索器/context交接与多题调用两类独立对照，避免混合变量。
- [x] 冻结小样本范围：A/HK/US各1家，只有预注册规则触发才扩展至每市场2家、总计不超过6家；不改变用户大股票池。
- [x] 设计30题顺序逐题、并发逐题、3/5/10题分组与30题单批；正确性先过门槛，再比较端到端耗时及真实价格/套餐额度。
- [x] 把缓存拆为搜索结果、provider前缀、应用答案三层，并规定冷启动、warm复用、材料性输入变化失效测试。
- [x] 新增B01/BENCH-01/BENCH-02并设为L03前置；更新I56、测试策略和执行日价格核验/隔离条件。
- [x] 缓存归因采用正交子实验，避免应用答案命中短路搜索/模型请求后被错误计为上游缓存命中。
- [x] 固定双人gold、相对逐题基线容忍度、claim抽样数量/模块分层、限长审计snippet、小样本时延口径及联合策略2×2门槛。
- [x] 加入分层模型对照：M3作请求粒度锚点，之后在MiMo Flash、DeepSeek Flash等各自独立匹配逐题基线/合格打包候选；按按量价格与MiniMax套餐quota分别核算，禁止混合模型补题。
- [x] 执行计划采用官方价目线索，已于2026-09-28复核Brave、Tavily、MiMo、MiniMax与DeepSeek官方价格/额度页面；执行日仍需冻结账户实际计划和页面快照。
- [ ] 前置Q09、Q10、W10及真实搜索/解析门均当前有效且预算/配额获批后，执行真实API对照并在G3大节点复核。
- [ ] 未完成实验前不宣称逐题或打包为胜者；L03失败门控时保持逐题基线。

## Phase 42: P00/P01回执续验与计划工件边界修正（历史阶段）

Status: historical_superseded_by_Phase_43_task_receipt_retirement

- [x] 只读公开校验器确认旧链状态：P00/P01因当前全局边界hash过期阻断；C01另有任务/case/assertion、证据和复审过期；C06/G0依赖阻断；W01回执仍为legacy_historical。
- [x] 修正P00任务卡：明确当前v2 receipt、校验sidecar/隔离日志和独立复审报告的允许路径；明确历史v1只读保留，不覆盖。
- [x] 修正receipt契约文档中过期的计划版本引用，改为以tasks.json当前版本为准，并明确P00新旧回执路径。
- [x] 增加计划回归，锁定P00当前回执工件的精确allowlist及旧v1保留约束。
- [x] 进一步修正P01任务卡：单列detached `validation-P01-current-*.json` sidecar允许路径，并增加回归测试。
- [x] 修复P00工件allowlist的真实glob：日期报告用`baseline-report-????-??-??.md`，JSON sidecar与log拆为独立模式；测试验证真实日期/sidecar/log可匹配且历史P00 v1不匹配，并固定旧回执SHA-256。
- [x] P00/P01计划与回执回归：117 passed / 105 subtests；plan validate为108 tasks / 365 cases / G6；Ruff通过；`git diff --check`通过（仅有仓库CRLF提示）。
- [x] 独立预封存审查当前P01实现快照：r8通过、无P0/P1/P2，确认P00真实glob匹配与历史回执哈希保护；报告绑定当前快照。
- [x] 在不改写旧P00 v1的前提下更新P01 v2 core并通过公开只读验证器，签发detached sidecar；当前推导`eligible_to_close=true`。
- [x] 由不同审查者完成P01封存后证据review：3 cases/19 assertions通过，receipt/core/sidecar及当前validator hashes一致；P01 current v2已eligible。
- [x] 依据P01关闭门重跑P00 BASE-01/02：写入2026-09-29日期化基线、重核历史manifest、运行隔离离线CLI+unknown/null校验、题库/事实库/计划验证，并记录四仓只读状态与CodeGraph快照。
- [x] 独立P00封存前复审r1指出ProviderCascade语义混淆P2；已据当前调用链修订，r2绑定更新快照并通过，无未关闭P0/P1/P2。
- [x] 签发P00当前v2 receipt与detached sidecar；公开只读校验器得到`eligible_to_close=true`、0 blockers，2 cases/4 assertions通过；旧P00 v1仍保持原SHA-256。
- [x] 不同审查者完成P00封存后证据review：公开校验器投影除`evaluated_at_utc`外与sidecar相同，4 assertions通过，pre-seal快照与旧P00 v1 manifest哈希均匹配，无自引用/循环。
- [x] 原计划中的C01—C07回执刷新已被Phase 43按施工卡退役的决定取代；不刷新旧链，也不以旧回执作为当前关闭门。原件继续只读保留。

## Phase 43: IQS harness lane 接管与轻量交接

Status: complete_for_local_IQS_lane_scope_external_G2b_remains_open

- [x] 用户将 `company-wiki/docs/plans/narrative-evidence-pilot-2026-09-26/harness_lanes/invest_quick_scan.md` 设为当前优先工作；仅读取该外仓文件，固定其SHA-256 `516077a6e9af3da41a121f5977225cc662035badcb3bc963dfb4dfe12f32be0a`，StockWiki/CWP/RF/FF/ET仍只读。
- [x] 按施工卡要求完成当前IQS工作树盘点，基线为 `master@25b8d14316c06390450e5a1d8883583bfd039d0d`；盘点了792条Git状态路径（47条已跟踪工作树修改、745条未跟踪；无暂存修改、删除或重命名），按文件保存SHA-256与保留分类，见 `docs/implementation/reviews/IQS-lane/worktree-inventory-2026-09-29.md` 及同名JSON清单。忽略文件未枚举；候选历史证据和当前内容均未删除、移动或重置。
- [x] 执行一次离线C01—C07共享回归：216 passed、149 subtests、0 skipped，隔离临时根已清理。用户选择施工卡优先后，不将此次结果封存到旧回执链；七份任务命名日志均保留为未封存工件，SHA-256 `420b9d9e7b521c812703d988400dbb2d80195fd105ad629215b538ed3100a870`。
- [x] 把身份CLI四组契约场景（ID-27—ID-30，6个固定断言）加入C01计划和验收目录，计划版本升至1.10.14、369 cases；测试预期覆盖Entity/AnalysisSubject正例、错绑定不回显、未知版本退出码、重复JSON键和输入大小上限。
- [x] 冻结身份包2.2.0（Entity 2.1.0、AnalysisSubject 1.0.0）现有schema/参考校验器/夹具；新增有界只读公开JSON CLI及子进程正反例：有效退出0、内容无效退出2、未知版本退出3，stdout仅输出单行结构化状态/error code/JSON pointer，不回显输入内容。
- [x] 仅在本仓和CodeGraph核验当前调用/引用后，退役 `scripts/task_receipts.py`、任务回执契约/计划依赖/专属测试中的递归任务签收部分；保留哈希校验的历史归档及原始审查材料，CLI只返回退役状态，未改动产品执行回执。
- [x] 将计划状态、批次日志和大节点审查设为当前进度记录方式；清除活动文档中过时的逐任务回执门槛，保留历史报告原文。
- [x] 重跑受影响计划、G0候选、退役CLI/身份CLI测试和只读计划校验：80个计划单测通过；15个G0/退役用例及186 subtests通过；7个CLI用例通过；计划校验107 tasks / 366 cases / G6。每组独占临时根均清理。G0第一次将输出日志误纳入自校验快照，第二次因捕获文件放在pytest basetemp触发Windows清理锁；将输出移出basetemp后最终批次通过。批次输出见`docs/implementation/contracts/validation-IQS-LANE-*-r{3,4}-2026-09-29.txt`。
- [x] 按当前计划测试边界验证CLI、身份错配和部署/可信证据语义；新增proof字段错issuer/state/hash/join矩阵。没有伪造StockWiki生产者golden或四态mapping DTO。
- [x] 将deployment `verify_live` 更新为明确外部动作、固定单模型/单搜索上限、输入/输出token上限并绑定当前release/policy revision；替代弱的布尔确认与审批字符串。TDD先红后绿；最终15个deployment契约测试通过。
- [x] 逐项审计 `contract_validation.py` identity/work/attempt/search/ingest/content proof。没有发现可安全移除的重复proof：这些字段指向不同owner记录或不同时间点；新增/保留issuer、security、period和伪造信任等级反例。审计同时确认本地validator仅校验owner-shaped mapping，不认证StockWiki/StockQA来源，详见`docs/implementation/reviews/IQS-lane/trusted-field-audit-2026-09-29.md`；故不改字段，真实producer证明留待G2b。
- [x] focused proof回归35 tests / 62 subtests通过（identity-bound、G0 trust、freshness period），临时根清理；日志见`validation-IQS-LANE-trusted-field-regressions-r2-2026-09-29.txt`。
- [x] 完成本地unit、身份CLI子进程集成、部署request-to-decision集成及producer-chain离线golden E2E；合并回归75 tests / 248 subtests通过，临时根已清理。未运行live API、未下载公司资料，IQS未进入CWP Worker DAG，也未写StockWiki/company-wiki/其他外仓。
- [x] 输出本仓base/branch/commit、2.2.0 schema/validator/fixture hash、主要本地写入路径、受影响测试、临时根清理结果、186项迁移保留清单和未解hold，见`docs/implementation/reviews/IQS-lane/implementation-summary-2026-09-29.md`。真实StockWiki producer golden/G2b仍未通过，未宣称跨仓完成。
- [x] 独立复审收尾：README、测试策略和Phase 12历史状态移除过期活动回执门；归档manifest完整性增加固定SHA/条目数/分类测试；verify_live集成样例改用独立活动策略fixture并验证过期revision被拒绝。
- [x] 补充施工卡工作树增量快照：792基线→843当前状态路径，53新增、22哈希变化、2个计划退役路径；逐文件哈希与两份原哈希归档映射见`docs/implementation/reviews/IQS-lane/worktree-inventory-delta-2026-09-29.json`。快照明确排除自身与其后的最终规划改动，忽略文件未枚举。
- [x] 按施工卡第1—4步逐项交叉核对并完成最终隔离回归：205 tests / 351 subtests / 0 skips；107 tasks / 366 cases / G6计划校验有效；测试临时根已清理，无网络/API/下载。最终报告见`docs/implementation/reviews/IQS-lane/construction-card-closeout-2026-09-29.md`，原始日志见`docs/implementation/contracts/validation-IQS-card-closeout-2026-09-29.txt`。
- [ ] 施工卡第5步/G2b：等待StockWiki真实身份snapshot/mapping DTO与producer serializer golden，通过其公开接口做跨仓正例验收。合成本地夹具不替代producer golden；本步骤未获跨仓写授权且本仓无可验真实产物。

本阶段按用户选择施工卡优先，C01—C07旧receipt刷新保持暂停；这些材料已作为历史工件保留，当前里程碑状态以`task_plan.md`、`progress.md`和大节点审查为准。

### 2026-09-30 — 本地检查点与规划文件同步

- [x] 将当前 invest-quick-scan 本地工作树进度提交为 `eb462d48321f3247eabf18daa57a4d4606405ca4`；共849个文件。提交涵盖本地实现、题库/发布物、契约、测试及已完成阶段证据，不代表所有跨项目任务完成。
- [x] 更新施工卡实施摘要与G2b交接：步骤1—4随检查点提交，版本/CLI/golden格式与测试记录不变；G2b仍需StockWiki真实公开DTO/serializer golden。
- [x] 计划校验复跑有效：107 tasks / 366 acceptance cases / G6；`tests/test_implementation_plan.py` 为80 passed / 53 subtests。
- [ ] 继续等待StockWiki producer golden以完成G2b；S06仍等待真实StockQA→StockWiki事务ACK、router 2.1真实历史样本和获批跨仓端到端验证。C01—C07回执刷新继续暂停。
- [x] 第二笔提交 `5aec24044aabdbf5187725e51066cd21fc39bc33` 同步了实施摘要、handoff和进度记录；本次再同步 `task_plan.md`、`findings.md` 与 `progress.md`，不改外仓。

### 2026-09-30 — Q02 MiMo 实际搜索验收

- [x] 在StockQAbyLLM获授权范围内，对公开CLI MiMo live E2E运行一次真实Microsoft搜索。沙箱内两次请求在HTTP前ConnectionError；同一隔离测试在批准的联网执行环境成功，1 passed / 13.63s；临时目录不存在，测试前后StockQA Git状态条目数均为55。
- [x] 修正新增live E2E的失败摘要，使错误描述限长并脱敏MIMO_API_KEY/MIMO_PLAN_API_KEY；未记录密钥或原始响应。实际成功断言覆盖provider/model、response ID、search_status、绑定的search receipt、非空来源与URL citation basis。精确运行记录和源文件SHA见`docs/implementation/contracts/validation-Q02-MiMo-live-E2E-2026-09-30.md`。
- [x] 同一StockQA工作树离线回归`test_llm_client.py`、`test_llm_provider.py`和`test_quick_scan_cli.py`共159 passed / 17.45s；从唯一临时工作目录运行、关闭`base_url`插件及项目coverage/cache addopts，并把pytest basetemp置于临时根；运行后临时根不存在，StockQA Git状态仍为55项。
- [x] Q02首个提供商任务在精确StockQA工作树快照上完成验收：独立只读复核匹配五个源码/测试SHA，确认LLM-02/LLM-11所选离线覆盖并未发现P0/P1；MiMo公开CLI真实搜索1 passed / 13.63s，provider/model、响应关联搜索回执、来源与临时目录清理均有断言。复核提出的P2断言增强和无citation正文URL负例记录为后续测试改进，没有因此重复付费live调用。
- [x] 复核发现的旧receipt/验收目录状态按当前规则正确处理：task-receipt v2于2026-09-29退役，`acceptance-cases.json`声明其为规格而非运行结果；旧Q02 receipt保持只读，`specified_not_executed`规格值不改，当前结果写入`progress.md`及批次验证记录。Q02任务级验收对记录的StockQA工作树快照通过，但不等于G1、跨仓生产接线或全项目完成。StockQA工作树仍有既有未提交改动，本次未将其合并提交。
