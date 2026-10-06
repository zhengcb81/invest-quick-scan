# 大股票池快速扫描与产业链检索：总体规划

## Goal
为用户逐批确认的上市公司池建立持续画像、字段评分白名单、产业链语义检索和深度研究交接，并逐卡实施跨项目方案。约2,000家及A/H/美股各600—800家只作长期容量规划，不是已批准的首批名单或发行人数承诺；当前首批输入是用户确认的216个带市场挂牌候选。本目录可写；用户已授权StockQAbyLLM全仓写入但须事先报备拟改文件/目的；StockWiki的W01及W02/W03精确范围已授权，W02/W03仅限8个名单身份/成员管理源码与测试文件，不含W05、UI或其他文件；company-wiki等其他仓库只读，写前另获许可。不批量下载公司文档，不把离线契约验收冒充生产上线。

## Ownership and Scope
- 计划所有者：当前任务 `/root`。
- 选定计划目录：本项目根目录（resolver返回legacy fallback；不存在已有命名计划）。
- 已有基础：24题核心评分模板、行业与阶段模块、StockQAbyLLM兼容导出和离线验证。
- 新目标：从单公司研究问卷升级为可持续维护的轻量股票池数据产品，同时与revenue-forecast/invest-*深度研究保持边界。
- 并行实施边界：每个独立项目目录仅归一条实现线；同仓库同一时间只允许一个写入harness。当前IQS总控同时拥有IQS仓库并维护计划/集成；外部线通过独立工作树、精确任务allowlist和结构化交接接入。并行任务的具体分组、接口与门槛见 `docs/implementation/parallel-lanes/README.md`。
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
- [x] S03: 优势条件与产业变化诊断取舍（题义、版本、导出及回归通过独立审查；DUR-01/02/03+SC-08 绑定 `tests/test_metrics_contract.py`、DUR-04 绑定 `tests/test_module_registry.py` 归档回归，2026-10-02 复跑 32 passed + question_sets 相关子集 12 passed/10 subtests）。**3.1.0 历史样本要求按用户 2026-10-02 改判 (a) 关闭**：接受真实 3.0.0 发布归档（48 模块/222 题）+ 既有合成错误版本头拒绝测试作为兼容证据，不再声称覆盖真实 3.1.0 回放（搜索 agent 已证实该样本本地不可得：catalog 从 3.0.0 直跳 3.2.0，3.1.0 从未落任何快照）。TIME-06/E2E-06 按 tasks.json 归属分别为 W06/X10，不再是 S03 阻塞项（历史回执误挂已纠正）。**S03 verified；L01（deps Q04/Q05/S02/S03）随之解锁**。
- [x] Q01: F01/F02及r2复审发现的F04均按获批parser范围修复；S02消费者兼容恢复。StockQA共享suite 276项、本地全量222项/139子用例及独立复审均通过；receipt绑定精确文件哈希，Q01离线范围verified。
- [x] Q02: 2026-10-02 verified（Phase 52）——`ced1faa`+`82f1794` 已推送；两个 MiniMax live E2E（responses+anthropic）在最终代码 PASSED；独立审查 changes_requested（payload 拆分无契约测试）→修复 `82f1794`→同会话复核 **approved** 并确认 LLM-02/LLM-11 完成判据满足。官方契约核实（ToolChoice 仅 auto/none、system 走 instructions、server-tool 超时指引）、中文 system 进 input 抑制搜索的实证修复、strict=唯一绑定对象（Q02+Q03 联合批次）均入提交。证据：`contracts/validation-Q02-MiniMax-live-E2E-2026-10-02.md`（含 ~20 次单题调用成本纪要）。历史 partial 叙述（下方 2026-09-26/27 条目）保留为档案，不代表当前状态；**用户 2026-10-02 决定：QAbyLLM 旧密钥不轮换**（暴露面限本机、未进 Git、报告 0 命中，残留风险由 owner 承担并已知悉）。
- Q02 current-snapshot hardening (2026-09-27): corrected two fail-closed gaps in MiniMax Anthropic search verification (`base_resp.status_code=false` and an unrecognized server tool coexisting with valid `web_search`). The seven-file code/test snapshot passed 160 isolated unit/provider/CLI integration tests with warnings-as-errors; Ruff and Black passed on the changed parser and its unit tests. Independent review matched all seven exact file hashes, reproduced the receipt semantics, and found no P0–P2. One authorized single-question live CLI attempt on the current code ended with `ConnectionError` before an HTTP response; it produced no search receipt or score and is not a successful E2E. The live harness's parent-side UTF-8 decode error is fixed, its changed-file review found no P0–P2, and the live selectors collect offline as four expected skips. No automatic retry was issued. Q02 remains partial until a current-hash live search receipt verifies the complete search/source chain; exact hashes and cleanup evidence are in `progress.md` and `docs/implementation/contracts/validation-Q02-fail-closed-hardening-2026-09-27.md`.
- Q02 latest endpoint/credential diagnostic (2026-09-27): a bounded one-query `.cn` live pass is recorded above, but a later same-route request returned HTTP 200/completed without a correlated search result and correctly remained unscored/unverified; two diagnostic calls to the official `.io` host returned HTTP 401 with the configured key. The live test now accepts `STOCKQA_MINIMAX_ANTHROPIC_BASE_URL` and uses safe UTF-8 diagnostics. Focused offline client/CLI tests passed 17/17; independent read-only review is pending. Q02 remains partial until a supported endpoint/key pair produces a verified current-snapshot search receipt. Evidence: `docs/implementation/contracts/validation-Q02-endpoint-region-diagnostic-2026-09-27.md`.
- Q02 test-review follow-up (2026-09-27): independent r1 found a P1 indentation error, P2 overconstraint on optional request_id, and P3 loss of the allowlisted web_search error_code in the safe summary. All three are fixed. Current live-test SHA256 `CC1423ECC7E5F24AE26ACF2F08067B3613F5AE9BDAE22AF6D8B5A9E8D10BA95F`; AST parsing passes, live selector collects without execution, and isolated focus passes 17/17. R2 review closed the P1/P2/P3 findings with no new P0-P2 (report SHA256 F5D7DC9413F6248DC9C87218558CB9665353F5C0E4EC8C33B506462D127A8113); Q02 remains partial pending a stable verified live search receipt.
- 2026-09-27 MiMo single-query live retest through the public CLI returned `error/unverified` with no HTTP status, model, response ID, or source URL. Its unique temp root was cleaned. Because the transport receipt cannot prove the request was not sent, this is an unknown outcome and must not be blindly retried; no cause or live-search success is inferred. See the detailed entry in `progress.md`.
- Q02首提供商切片于2026-09-30完成新快照验收：MiMo公开CLI真实Microsoft搜索E2E为1 passed，同快照离线测试159 passed并经独立复核；仅关闭该MiMo切片，不关闭G1、其他提供商能力、费用核对或跨仓接线。MiniMax最终快照仍无verified搜索receipt，故Q02整体保持partial。详见`docs/implementation/contracts/validation-Q02-MiMo-live-E2E-2026-09-30.md`。
- [x] Q03: F03重复JSON对象键在direct与Markdown兼容路径曾可绕过并从metadata误取9分；现只提取完整外层JSON并fail closed，direct/Markdown固定案例通过，r2独立复审verified。2026-10-02 随 Q02 关闭（Phase 52）：前置达成；且本批 strict 语义增量（唯一绑定对象+全绑定）经同一独立审查 approved、差分审计无安全回归——Q03 verified。
- [x] Q04: 2026-10-02 收口（Phase 50）——隔离快照 `fe11f63`（58 跟踪文件，含不可分割底座，写前报告披露）通过完整 pre-commit 链并推送；`q04_handoff.json` 刷至 `status=complete`、`result_commit` 就位、独立增量审查 **approved**、IQS CLI valid；246 责任批次与钩子链全绿。B1/B2/r7 历史修复记录保留。Q04 完成判据满足（case 全有实际结果+快照+独立审查最新版）。
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

- [x] S06: ROUTE_02已升级至router 2.3 / policy schema 1.3 / request protocol 3，保留2.0—2.2历史只读兼容。StockQA公开适配器逐项核验实体/搜索回执/答案SHA-256/实际模型归属，执行校验调用方独立 decision_id；09-29 修复新执行路径误用历史读取校验器并修正 renderer patch owner。**2026-10-02 收口 verified（Phase 56）**：收口独立复审 **approved**（两套件 147+20 passed/91 subtests 入隔离日志 `contracts/validation-S06-closeout-2026-10-02.txt`，**12 个源/配置/测试 SHA-256 与当前 HEAD 字节一致**并记档——补上09-29复审未留哈希的流程缺口）；五 case 全映射（MOD-01×8、MOD-04×9、MOD-05×19、MOD-18×4 含零派发、MOD-19×30）；MINOR2 被 `-k` 过滤的6个低分保留测试已按 node-id 补跑 6 passed；MINOR1/3（字面三元组类比覆盖）与 INFO×3 记录接受。**诚实边界不变：router2.1 仅合成兼容路径（真实历史样本待 owner）、StockQA→StockWiki 事务ACK与跨仓E2E 不在 S06 完成范围且不声称完成**。工程task receipt v2/P01已退役。
- [x] W01: 经用户精确授权，仅在StockWiki新增独立SQLite身份库/测试并更新`.gitignore`。真实分类YAML只读副本的隔离验证29项通过；独立首审的伪v1 schema、提交后验证和ADR错误基础引用三项均经固定反例修复、第二轮独立复审通过。`receipt-W01.json`绑定精确哈希与本地范围；生产库未迁移，W05仍待实施。
- [ ] W02: 在用户授权的StockWiki精确文件范围内完成安全主档快照预览/导入首段：只落不可合并的来源候选，按内容哈希幂等，拒绝名称/代码推断身份，来源URL仅保留HTTPS origin，不持久化路径/凭证/query/fragment；真实CN/HK/US主档复制到临时目录验收通过。59 passed、1 skipped隔离目标测试及静态检查通过；最终8文件独立哈希复审通过，无P0–P2，见[验证回执](docs/implementation/contracts/validation-W02-W03-stockwiki-first-segment-2026-09-27.md)。仍缺source-to-entity binding审批/事务桥接、可核实身份升级和生产名单自动接续，因此W02 partial；跨实体唯一性须由StockWiki owner事务实现，见W02方案与C01复审报告。
- [ ] Q08: Q08拥有持久冷却/半开探针及跨运行`retry_wait`恢复资格；首段provider-health状态与HTTP隐式POST重试、晚到拒绝时间修复已独立复审，离线unit+integration 617项通过，精确边界见`receipt-Q08-first-segment-2026-09-26.json`。当前仍缺有界dispatch-round持久化和与Q06 work lifecycle的生产接线。Q06持久待办/transport和Q09预算/并发账本第一段已实现；Q07逐题检查点仍缺生产接线与多题单次派发支持，Q09真实费用解析、公共runner完整预算接线及最终独立复审仍待完成，故Q08整体partial。
- [ ] Q09: StockQA持久预算账本与发包闸门第一段已实现，包含原子预留/结算、跨策略版本保留支出、未知费用/结果不明时保守暂停、与work send-intent同事务，以及同步/异步transport接线。独立复审发现“过期lease后的迟到HTTP回执会遗留在途预算槽”并已改为在同一SQLite事务记下late receipt和预算状态：HTTP已结束则释放并发槽，未知费用仍保留预留/暂停；没有收到HTTP响应仍保留不确定状态。相同late receipt重放现为同结果幂等、不同状态/费用来源冲突拒绝；费用解析器异常或无效用量也会保留预留、释放已结束请求的网络槽并暂停后续派发。预算对账重放也校验request-count语义，阻止`confirmed_not_sent`与`completed`互翻造成请求数漏记。全范围隔离回归436项通过，其中双进程+20请求真实HTTP-stub并发验收检查全局/组/路由上限；最终review follow-up待回。生产真实费用解析与完整runner预算配置仍未闭环；验证记录见[Q09首段日志](docs/implementation/contracts/validation-Q09-budget-first-segment-2026-09-27.log)。
- [x] W03 首段（2026-09-27 回执，历史）：范围内成员管理首段+59 passed+8文件哈希复审。**W03 剩余批次 2026-10-02 完成并 verified**（StockWiki 本地提交 `4fbda21`，无 remote 决定7）：schema v2（挂牌历史+身份事件表、增量迁移、v1 数据保留升级用例）、`add_security` 幂等/乐观锁、`record_listing_status` 追加历史、`apply_rename`/`apply_ticker_change` 文档化变更守卫（entity_id 恒稳、binding ticker 同事务一致、事件 old/new 双查）、`quick_scan_universe` 名单模块（仅显式移除、容量仅报告不驱逐、历史与理由全保留、**构造上零网络**）、9 个 CLI 子命令（规范 JSON stdout+命名拒收 exit 2）；26 个 W03 相关选择器（store22+universe4）覆盖全部六 case（UNI-04 字面构建 2003 成员、socket 炸弹零调用）；`check_all` 全绿（套件+覆盖率+框架）。**独立审查 approved**（无 P0–P2；10 条 low/info：`_save_prepared` 早退内部 commit 不可达路径、OR IGNORE 实为守卫冗余、dup 比较只遍历入参键、若干拒绝分支未测、UNI-04 staging 非字面、ID-15 以事件 dispatch_revision 代理 Work 绑定、黑化预存、handler 位置 deviation 已记录、W03 步骤5 按分离满足待 owner 确认、CLI 小卫生——全部记录接受不改码）。基线注册（`framework_validators_okf.py` 增 `quick_scan_store.py`，548→923 行、923<critical1000、Stage-3.2 拆分延后）经审查"accept-with-justification"：门的错误路径对非基线新大模块与超 critical 仍报错（实测验证），W03 禁新文件故注册是错误信息自带的唯一合规路径；**owner 签收 W03 时应显式确认此登记**。真实工作区 DB 已幂等迁至 v2（空库）。首段遗留的 C04 投影绑定/扫描观察导入/UI 分属 W05/C04/UI 线，不属 W03 case 域。
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

Status: complete_for_local_S04_scope; later owner tasks continue in subsequent phases

- [x] 按最新继续指令恢复完整实施目标；重新读取1.9.3任务包、当前工作树、回执和独立审查结论。外仓仍按既有授权边界处理。
- [x] 核对S04当前case集合；发现新增MOD-14未出现在此前S04回执/测试绑定中。
- [x] 在本仓增加真实module contract测试，覆盖重复release module ID、归档内容hash不匹配、依赖循环、退役ID仍被使用；S04定向测试15项通过。
- [x] 独立只读审查确认`validate_registry`拒绝循环，但hash自洽的归档循环在`validate_release`仍可通过；确认MOD-14/既有回执未覆盖该路径。
- [x] 随后已修复归档reader：`validate_registry`与`validate_release`共用依赖图校验；新增hash自洽归档循环反例。定向module contract 16项、registry 17项、question-set 60项与全仓350项/273子例曾报告通过。
- [x] S04/MOD-02与MOD-14当前源码hash绑定的26项/11子例隔离测试日志通过；MOD-14的10条atomic assertion、精确错误、hash自洽依赖环、墓碑冲突/遗漏、完整包原子返回及互斥备选正例均已覆盖。独立复审发现并促成修复`applies_when`同ID范围变更缺口；同ID拒绝与major successor迁移正例、两份契约均已更新。保存旧v1收据后生成当前v2 receipt，公开递归验证`eligible_to_close=true`。复审报告、验证sidecar和当前receipt均在`docs/implementation/`。
- [x] S05/MOD-17精确基线信任、父目录符号链接/junction防护及24项注册器测试已通过；共享恢复映射修复后，S05独立复审确认信任路径未受影响。更新S04依赖hash后，S05 v2 receipt递归验证`eligible_to_close=true`，无blocker。
- [x] S01因共享`question_sets.py`证据哈希/复审过期而仅为刷新回执短暂重开；发现并修复旧manifest恢复观察信任顶层`replacements`的P2，改为从题目`replaces`重建和交叉校验，不一致/不完整时标记`needs_verification`且不改核心汇总。相关批次70项/166子断言、最终定向6项/4子断言通过，独立复审无剩余发现，S01 v2 receipt公开验证`eligible_to_close=true`。
- [x] 本阶段S04及其S05/S01依赖范围已完成；后续逐卡实施转入Phase 32及其后续owner任务，只在大里程碑合并回归/独立审查。

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
- owner 常设调查纪律（2026-10-05）：遇到"同一公司出现不同股票代码"类异常（如上海医药 600849/601607），**先用搜索引擎查清前因后果**（代码变更公告、历史沿革、官方口径）再下结论/提请裁决——不要先本地推理再回头补搜；上海医药案的搜索时机滞后于本地诊断，作为反例记档。

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
| 2026-10-05 | PowerShell 双引号 here-string 把 `` `r `` 反引号当转义写成回车（progress.md 3 处内容损坏，`runner.py` 被吃成 `unner.py`），Add-Content 写入路径还将旧内容整体转为 CRLF；`git diff --check` 报 exit 2 | 字节级诊断（HEAD 纯 LF=1682 行 vs 工作树 1406 CRLF）→ 两文件 CRLF→LF 归一 + 3 处 `` `r `` 恢复 → --check 回 0、numstat 64/0 纯新增；**永久规则：PWF 文件只经 Python 追加（读改写用字节模式），禁用双引号 here-string/Add-Content，每次追加后必跑 `git diff --check`** |
| 2026-10-05 | G2 审查者执行 summarize.py 时把生产产出文件误作输出路径参数，out/primary/CN_A_000672.json（MiniMax 旧产 1,321,279 字节）被 4,737 字节汇总 JSON 覆盖且不可逆——根因是 summarize.py 的位置参数输出路径无护栏 | 立即加护栏（禁止写入 run 目录内、禁止覆盖已存在文件）+ G2 包比较组清单改 4 家 120 题（000672 仅剩 run-log 聚合与覆盖前 13s 复算日志）+ 事故入 progress/owner 签认待办；L02 校准集 6 份 sha256 完好、无须重跑 |
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

**Phase 53 完成：W02 preview 入口已交付**（StockWiki `33dbf7f`），**真实 216 预览报告已产出**（`reviews/universe-identity-preview-2026-10-02.json`：216/216 unresolved 空库诚实状态、中信建投重叠组、零 membership/零 paid_work）——**当前第一等 owner 动作：审阅该报告并给出 216 导入写授权与消歧证据要求**。此前已闭环：Q02/Q03（Phase 52）、S03 改判(a)、ACL 解封+DWA-04 两未知组闭合（新基线 2401 条）、决定5/7/8。**Phase 54 完成：DWA 四仓 P1 处置**（rf `5319ee26`、SID `064a837`、QAbyLLM `ad389f8`、StockQA 无操作）。**Phase 55 完成：W03 verified**（`4fbda21`，六 case、37 测试、审查 approved、基线登记经审查接受）；DWA-04 扩盘分类归档（1985 条全为可重建 pytest 临时）——**owner 决策点：`.tmp-zr408-unit*`×3（各657条）与 14 scratch 删除或 ignore 二选一明示**。**Phase 56 完成：S06 verified**（收口复审 approved，147+20 passed 入隔离日志+12 哈希记档，五 case 全映射；诚实边界：2.1 仅合成、跨仓 ACK/E2E 归 W05/G1 域不声称）。**Phase 57 完成：L01 verified**（冻结钉版 IQS `51fbce1`；10 家真实探针 11 调用承载 20 请求=用满上限未超、41 搜索/388 源、18 题得分(4–9)、2 题 fail-closed、0 mock；试点包+三轮整改 StockQA `7a40a98..1f04a8f` 已推送；独立审查两轮 approved，四文件 SHA-256 记档，预算按问题级 20 请求口径修正）。**Phase 58 完成：G1 verified → M1 关闭**（独立复审 approved（ses_f0022a928ffewW1KsB6lHQRJE9），`reviews/G1/` 审查记录+60家范围说明+30检查脚本+三 log = IQS `f7860fb`；发现 F1 信息日期 20/20 null 与 F2 来源元数据缺失已绑定为 L02 进入条件）。**Phase 59 完成：W04/W05 双卡 verified**（StockWiki `5f2739a`+`aa3c6e6` 本地；两轮独立审查均 approved）+ **owner 八项决定已记录**（见 Phase 59 节：216 授权/1985 删除/账单通过含 5 小时限额/G2b 派 agent 后签收/StockWiki 全授权/34+2 清理/信息日期选 a/W03 签收）。**队列进度（2026-10-03）**：①②③④⑥ 中 ①②④ 已完成（1985 删+34+2 清理=Phase 60 前后、216 入库 Phase 60、W06=Phase 61）；**Phase 63 完成：W07 verified → M2 关键路径推进一格**（W08 现已解锁）。owner 第二批答复已入档：G2b A/C/D/B 全授权、补 W05/W13 CLI、7a 顺其自然、live 凭据预批、O01 不急、叙事三提交处置待定。**Phase 64 完成：CLI 批次 approved+committed（`cc7fc6b`）、G2b 证据检索归档（`5a7e996`，四类 0 READY 待 owner 签收）、W08 verified（`9fa8a7e`，差分 9646/0）→ W09 已解锁**。**Phase 65 完成：W09 verified（两轮审查）→ M2 主链 W01–W09 全齐**。L02 只剩自己的冻结条件（7a + 范围 §5 F1/F2 二选一），G2 只等 L02。**Phase 67 完成：W10 verified（两轮）→ W11 解锁；owner 第三批（B2/同意/按建议/保留）+ 通授全部入档；B2a 获批待执行**。**Phase 68 完成：B2a 全量跑完（216/216 分类 + 11/11 H股发现、3 提名；终账 406/420、771/840 在 caps 内；0 池写入）**。**Phase 69 完成：G2b-A 导入路径 approved+committed（`f701909`）+ Alphabet 首个真实 verified 样本入库（4 证券/回执/幂等复验，证据入 `G2b-alphabet-sample-2026-10-04.md`）**。**Phase 73 完成：两表六项决定全签（A/H 122 行按现态签+剔30+受纠偏；D 217 行信任 sha+排北交所+受 HK 注记 → `closes_g2b_d=true`，D 类证据闭合）**。当前队列：① **L02 冻结**（唯一剩余前置，owner 已批 2600/5200 内直接跑）→ ② L02 执行（live 分窗）→ ③ A/H bridge 导入批次（G2b 最后实物：issuer_bridge 表+导入+平安实体）→ ④ W11 → ⑤ W06 跟进。等 owner：MiniMax 对账（B2a 406/771）、叙事=保留（已定）。已完成：Phase 60 216、61 W06、62 W13、63 W07、64 CLI+证据+W08、65 W09、66 7a、67 W10。Q13 仍不可开工（Q06/Q07/Q09/Q10 partial）。L02 等 W07/W08/W09 且须先满足范围说明 §5 F1/F2 二选一。恢复工作时按[新接手模型工作指南](docs/implementation/handoff-for-new-agent.md)重核各仓 HEAD/工作树/handoff。等待（owner 侧）：216 导入授权、G2b owner 正样本、1985 条处置决定、MiniMax 账单核对（决定9，L01 本批 20 completions+41 searches）、QAbyLLM 34 项与 SID 2 盲区去留、W03 签收两点确认（基线登记+步骤5分离）。审查节奏沿用 G0—G6/高风险边界，不新增逐小节点review。

### 历史执行状态（截至2026-09-30）

- Q02首个提供商实现的任务级验收已在精确StockQA工作树快照通过：MiMo公开CLI真实搜索、LLM-02/LLM-11离线检查及同快照独立审查均已记录在`progress.md`和`docs/implementation/contracts/validation-Q02-MiMo-live-E2E-2026-09-30.md`。旧任务回执已退役、验收目录为规格；不刷新receipt或改规格状态。该结果不关闭G1或跨仓链路。
- company-wiki IQS独占施工卡本仓步骤1—4已完成，报告见`docs/implementation/reviews/IQS-lane/construction-card-closeout-2026-09-29.md`。StockWiki `72531b5` 已提供 W04 公开 `identity-export-g2b` 与 owner receipt/registry/source context；第5步/G2b 从“缺 producer 实现”转为 IQS 总控独立复现 golden、核查来源与正反例后签收，见`docs/implementation/reviews/IQS-lane/G2b-handoff-2026-09-29.md`。不得重复实现步骤1—4、伪造 verified/multi-listing 正例或代改StockWiki。
- 卡片SHA-256仍为`516077a6e9af3da41a121f5977225cc662035badcb3bc963dfb4dfe12f32be0a`。基线792条路径至delta快照843条：新增53、已有文件哈希变化22、缺失2；两项缺失均是退役活动receipt文件，已由原哈希归档副本解释。delta明细见`docs/implementation/reviews/IQS-lane/worktree-inventory-delta-2026-09-29.json`。
- 卡片隔离回归205 tests / 351 subtests、0 skip；计划校验107 tasks / 366 cases / G6 valid，临时根清理已确认，日志见`docs/implementation/contracts/validation-IQS-card-closeout-2026-09-29.txt`。
- 已恢复S06本地工作：将新执行route gate切到当前router执行校验器，保留历史manifest的历史校验路径；修正renderer失败测试的mock patch位置。S06聚焦回归57 passed、0 skip，独立只读复审无P0–P2，计划校验107 tasks/366 cases/G6 valid；日志见`docs/implementation/contracts/validation-S06-current-fix-2026-09-29.txt`，范围说明见`docs/implementation/reviews/S06/current-router-execution-fix-2026-09-29.md`。
- S06仍因StockQA→StockWiki真实事务ACK、router 2.1真实历史快照和跨仓端到端验收而partial。旧工程task receipt v2/P01签收机制已退役；不能以刷新C01—C07旧回执作为当前门槛。StockWiki本轮只读。

### 当前下一动作

- Q03首轮快照回归通过166项后，独立复核发现一个P1：JSON数组/对象类型的`status`使parser抛`TypeError`，导致公开CLI丢弃已完成搜索回执。已按TDD修复并补事件级回执断言，完整Q03隔离回归170项通过；两轮独立只读复核均未发现未解决项，最终复核匹配三份当前SHA。Q03解析与结果回执路径的任务级验收已通过。初始报告parser单测SHA有单字符笔误，已更正；精确命令、SHA与审查边界见`docs/implementation/contracts/validation-Q03-current-snapshot-2026-09-30.md`。该任务级验收不代表G1/全项目、其他模型或跨仓链路完成。
- G2b 的 provisional Entity + mapping 1.0.0 接口切片已由独立复审通过；完整 G2b 仍待 StockWiki 真实 verified/多挂牌/AnalysisSubject 与历史区间 owner 样本。S06 本地范围测试/复审已通过，整卡仍待 StockQA→StockWiki 真实 ACK、router 2.1 历史样本和获批跨仓 E2E。
- QA-04当前行为回归有246 passed证据，但handoff仍`partial`/`result_commit=null`；复验报告记录61条状态，随后DWA-06盘点记录63条（含`?? nul`），handoff仍记录55。SW-IDENT handoff因`changed_path_out_of_scope`被公开CLI拒绝，W02/W03生产入口仍有缺口。TH-01/IN-02只读预研归档有效，T01/T02仍not_started；详见2026-10-01复验报告和DWA审计报告。
- Projects股票池候选文件已完成只读清点，完整列表和来源hash在`docs/implementation/reviews/universe-source-inventory-2026-10-01.json`。用户已确认216个带市场挂牌候选作为首批输入；该确认不等于canonical universe导入授权或扫描授权，候选文件仍未写StockWiki、未扫描。

### 当前总控动作

- 下一项关键路径是让StockWiki owner完成W02/W03的可隔离挂牌候选身份预览入口。收到修正后的范围声明、可运行preview和真实歧义/挂牌状态样例后，总控复核公开CLI与隔离端到端，再报告精确写入范围供后续授权；未解析/歧义项不得进入扫描队列。
- QA-04只在owner提供安全隔离的当前快照、与其hash一致的handoff/review后复验并收口；当前StockQA共享工作树最新已知状态为63条，含`?? nul`。不整树暂存/提交，也不重复运行无变化的246项批次。
- 完整G2b仍需StockWiki真实verified、多挂牌、AnalysisSubject及历史有效区间owner样本；S06仍需真实StockQA→StockWiki事务ACK、router 2.1历史工件和获批跨仓E2E。provisional Entity/mapping接口切片已签收，不扩张其覆盖声明。
- TH-01/IN-02只读预研已归档验收；T01/T02仍受G3/F05/W11、生产query/golden及技能仓唯一owner决策阻塞。
- DWA-03/04/05可在满足各自基线、可见性和禁读条件后重新只读审计；DWA-06须先由owner确认63条状态中的`?? nul`并冻结新基线。七项盘点不等于七仓改动原因均已查清。
- MiMo首提供商live验收、Q03修复、S03真实3.0.0归档回归及DWA首轮审查均已分别留档；外部交付门未变。变更发生前不重跑相同大批次。

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
- [ ] 首批公司池已由用户确认为 216 个带市场挂牌候选（2026-10-01，见 `reviews/universe-source-inventory-2026-10-01.json`）；确认只覆盖候选范围，**仍不授权导入、不授权扫描**，也不自选名单。真实跨仓 E2E 样本仍另行等待。

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

Status: design_and_local_contract_v2_1_complete_cross_project_pending; legacy_receipt_gate_retired

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
- [x] [Superseded by Phase 43] 不再刷新P01/C01工程任务回执链；旧回执只读保留，不作为身份契约或当前里程碑的关闭门。
- [x] Phase 40执行本地身份与计划受影响回归并完成独立复审；170 passed / 160 subtests及36项身份专项证据见Phase 40记录。
- [ ] 同步完成后再继续 W01 红/绿修复和 W02/W03 实现；仍使用用户授权的精确 StockWiki 文件范围，不导入或扫描尚未确认的候选池。

本阶段只完成设计工件与只读上游核查，不代表身份 resolver、三层存储、UI 或跨仓接线已实现。StockInfoDLSimple CodeGraph 索引由用户明确授权后建立；Dayu/StockInfoDLSimple 业务源码均未改。

## Phase 40: 分离法律发行人与分析范围并修复身份契约复审发现

Status: local_contract_and_tests_complete; production_identity_registry_external_pending; legacy_receipt_gate_retired

- [x] 在身份设计中明确 `entity_id` 只代表法律发行人，新增独立 `analysis_subject_id + analysis_subject_revision` 标识快扫研究范围；普通经营题以并表/独立报告范围为对象，证券报价题仍绑定 Security/Listing。
- [x] provisional subject 仅锚定权威库确认的单一精确挂牌，禁止从暂定 issuer、集团控制关系或 LLM 建议推导合并报告范围；已核实 issuer 才能建立 standalone/consolidated subject。
- [x] C01 本地契约包升至2.2.0；Entity writer 仍只接受2.1.0，Subject 独立版本1.0.0。Work/Observation/C06消费的subject字段作为后续C04/C06/W05门槛，不静默迁移历史数据。
- [x] 独立身份复审与两轮follow-up的反例均已纳入本地修复/覆盖：全球市场代码与MIC辖区、verified claim证据/有效期、缺MIC重叠ticker失败关闭、security_added精确影响ID、退市与retired source binding、身份事件前后快照、AnalysisSubject并表范围回执和成员差异、v2.1 ID-02/08覆盖。
- [x] 针对两个最终边界追加回归：身份事件快照的foreign/dangling Security引用均失败关闭；primary issuer切换只允许原主/新主纯role互换，不能夹带第三方成员信息变更。
- [x] 本轮身份与G0/计划合并回归为170 passed / 160 subtests；新增foreign-Security专测后身份文件为36 passed / 50 subtests。identity schema Draft7、计划校验、Ruff、`py_compile`与`git diff --check`通过。
- [x] 独立只读终审未发现未关闭P0—P2；审查仅针对本地身份契约/修复快照，不代表外仓resolver或全链完成。
- [x] 同步 C01、C04、C06、W02、W03、W05 任务边界与新增 ID-18—ID-26；计划版本1.10.12，107任务/363验收场景/55约束。跨项目文件仍只读。
- [x] [Superseded by Phase 43] 不再按P01依赖门刷新C01 v2任务回执；保留历史P01/C01工件，不据此标记生产身份注册表或跨仓集成完成。
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
- [ ] 施工卡第5步/G2b：StockWiki `72531b5` 的真实 owner CLI provisional Entity 2.1.0 golden 和公有 snapshot/mapping DTO 四态 golden 已由 IQS 总控冻结；独立消费校验、错 ID/source/as-of/status 反例与临时根清理均通过，见 `G2b-owner-acceptance-2026-09-30.md`。独立审查的 P1 有效区间漏洞已在获批 StockWiki 两文件及 IQS 消费端修复并复审；**当前 provisional Entity + mapping 1.0.0 接口切片签收，完整 G2b 仍 partial**。真实历史区间、近名 resolver/import、verified/多挂牌/AnalysisSubject owner 正例仍待 W02/owner 交付，不能用合成探针替代。

本阶段按用户选择施工卡优先，C01—C07旧receipt刷新保持暂停；这些材料已作为历史工件保留，当前里程碑状态以`task_plan.md`、`progress.md`和大节点审查为准。

## Phase 44: 跨Harness并行施工包、路径所有权与集成接口

Status: plan_complete; QA-04_closeout_and_SW-IDENT_delivery_partial; downstream_dispatch_gated

- [x] 按107项任务的owner与依赖图聚合工作；每条实现线拥有不相交的项目目录，多个任务若共享脚本、存储或测试路径则留在同一线内顺序实施，不强行拆小。
- [x] 冻结IQS总控、StockQA执行、StockWiki权威存储/UI、主题研究消费者、行业研究消费者五条实现线；Theme与Industry虽目录分开，但共用`local-skills` Git根，须各用独立分支/工作树且只写各自技能子目录。
- [x] 为每条线写独立上下文包，包含owner任务、接口契约、允许/禁止路径、依赖门、TDD测试包、阶段审查标准、交接字段与已知授权边界；总索引引用各包，依赖顺序唯一以`tasks.json`为准。
- [x] 定义标准机器可读handoff schema与计划校验测试，检查任务owner覆盖无遗漏/重复、目录所有权不重叠、文档均存在及schema最低字段齐全。
- [x] 将完整跨项目X09/X10、付费B01/真实搜索实验与G2b真实StockWiki golden保留为后置门；handoff文档不授予外仓写入、真实API、用户名单选择或费用权限。
- [x] 规定大节点合并审查（G0—G6）和高风险边界复核；小任务按TDD自测并归入同一owner批次，不逐卡重复独立审查。
- [x] 标明施工包编制时必须隔离共享工作树：StockQA当时观测到55项未提交状态，StockWiki存在未跟踪`.claude/`目录；状态会随其他进程变化，开工前必须重新核验，不得清理、覆盖或把无关状态带入lane提交。
- [x] QA-04实施前的StockQA隔离基线门未能作为干净独立快照满足（2026-10-01 时点事实，记录保留）。**2026-10-02 解决路径**：用户全权授权下，先由 DWA-06R 独立盘点给出"可提交 57"分组证据，再以隔离提交 `fe11f63` 冻结（写前报告披露不可分割底座），handoff 刷新+CLI valid+独立增量审查 approved 收口（Phase 50）——**事前隔离要求未满足的事实作为豁免保留，事后收口链完整**。StockWiki后续W05/UI仍须另行精确授权。

## Phase 45: 可交给独立 harness 的下一段精细施工卡

Status: package_docs_complete; QA-04_and_SW-IDENT_first_segments_received; both_delivery_partial; TH-01_IN-02_prestudy_complete; downstream_gates_pending

- [x] 以五条长线为上层 owner，只挑四个不重叠的下一段工作包：QA-04、SW-IDENT、TH-01、IN-02；机器目录和独立文档位于 `docs/implementation/parallel-lanes/packages/`，上层总文档已链接。
- [x] 将 QA-04 的 LLM-10 运行中策略边界和 PAR-11 首选路由槽位等待写成公开入口 TDD/POST 计数验收；施工包编制时保留当时观测到的Q03修复和55项既有StockQA状态作为基线信息，执行前仍需复核。
- [x] 发现 StockWiki 新合并 `master@c8cfb2e` 已含真实 `identity_snapshot.py` / `identity_mapping.py`，修正旧计划路径假设；SW-IDENT 要求先复核 W01/W02/W03 新基线，再补缺口并交真正 serializer golden，且不越过既有文件授权。
- [x] TH-01/IN-02 文档明确 G3、F05、W11 与生产 query/golden/写授权为硬门；两者当前只能做只读准备，不能用 IQS 本地协议定义冒充生产端点。
- [x] 新增包级机器 manifest 与回归，检查 owner/任务前置/写入 scope 无重叠、文档链接和只读门；包内只在大节点或高风险边界审查，worker 标准 handoff 交总控。
- [x] QA-04 和 SW-IDENT 已收到首段实现/测试交付并进入总控复核；这不代表交付完成。QA-04 handoff/hash仍过期且无result_commit，SW-IDENT handoff因声明路径越界被拒，W02/W03生产入口与完整G2b仍缺证据。总控只在真实StockWiki owner golden到达后做G2b跨仓验证。TH-01/IN-02只读预研已验收，实施继续等待G3/F05/W11，不抢跑。
- [x] IQS 总控只读复验 StockWiki 当前身份 producer：专项 29 passed；临时权威库的真实 serializer hash 与 owner 摘要相同；缺 `identity_receipts`/`market_registry` 导致 IQS CLI 诊断负例退出 2。已把精确差距交给 SW-IDENT，G2b 保持 pending。
- [x] 为 TH-01/IN-02 定义只读预研、handoff 与留档接口：harness 返回 Markdown+标准 JSON；IQS 总控核验后以内容 hash 命名保存，并维护 JSON Schema 校验的不可变索引。索引起初为空；2026-09-30 两份真实原件已验收归档。T01/T02 仍待 G3/F05/W11、生产 query/golden 和写授权。
- [x] 按用户要求把两条预研所需的只读步骤、字段/接口核查、完整 Markdown+JSON 交接与总控归档规则直接嵌入 TH-01/IN-02 各自文档；交给独立 harness 时无需依赖聊天上下文。两份后续交付已按本规则验收，见预研索引。
- [x] 收到 StockWiki `master@72531b5` 后更新 SW-IDENT：W04 owner `identity-export-g2b`、receipt、market registry 已实现；本包改为 W01–W03 逐 case 验收与最小缺口修复，G2b 最终签收由 IQS 总控。四个 StockWiki 定向文件在隔离环境 64 passed；旧 `c8cfb2e` 缺 context 诊断只作历史记录。
- [x] IQS 总控从 StockWiki 公开 CLI 独立生成并冻结 provisional Entity golden：两套隔离 owner store 导出字节相同、SHA 与 owner 记录一致，owner receipt/source/MIC 公开读核验及 IQS CLI 正例/五个负例通过，临时根清理；当前只签收此 slice。SW-IDENT 尚未分派，不借此次更新扩展 StockWiki 写授权。
- [x] 补 IQS 自有四态 mapping DTO 1.0.0 schema/消费合同、真实 owner 公共 API 产出的五态样本 bundle（四态加 source mismatch）与逆向反例；冻结 SHA `da3991c0d85ef9a0bce7c9152475b9184942df74c34fab4c5c935fb0e375a96f`，合并回归101 passed/63 subtests。
- [x] 对 G2b Entity + mapping 当前接口做独立审查并处理 P0–P2：P1 过期挂牌误映射与 P2 未知版本均已用 RED/GREEN 回归修复；复审无剩余 P0/P1，见 `docs/implementation/reviews/IQS-lane/G2b-independent-review-2026-09-30.md`。仅签收 provisional 单挂牌接口切片；verified/多挂牌/AnalysisSubject 与真实历史有效区间、近名导入仍标未覆盖。
- [x] 将总控遗留的 handoff intake RED 测试补成只读 `scripts/parallel_handoff_cli.py`：只验证 schema、package/lane/task、声明路径与临时根清理，不认证用户授权或测试事实；拒绝重复 JSON key、跨仓路径、未清理根和只读包变更。
- [x] 2026-09-30 接收 QA-04、SW-IDENT 及 TH-01/IN-02 预研交付并做大节点审查，见 `docs/implementation/reviews/IQS-lane/parallel-package-acceptance-2026-09-30.md`。QA-04 新 revision 损坏 quota group 反例先 RED 再修复 GREEN，当前功能批次 246 passed、Ruff 通过，独立复审无剩余 P1；但 StockQA 55 项共享脏树、旧 handoff hash/`result_commit=null`，正式交付仍 partial。SW-IDENT 43 项独立聚焦测试和 G2b golden 通过，但 handoff CLI 拒绝 `changed_path_out_of_scope`，W01–W03 生产链仍 partial。TH-01/IN-02 两份原件在用户随后给出的精确子目录找到，独立验收并按 SHA 归档为 `prestudy_complete`，T01/T02 实施仍未开始。
- [x] QA-04 收尾（2026-10-02 完成，Phase 50）：以隔离提交 `fe11f63` 冻结实现快照（不可分割底座经 DWA-06R"可提交57"论证并写前披露）；`q04_handoff.json` 刷新四文件 SHA、result_commit、worktree_after 与 verification；总控重验公开 handoff CLI = valid；独立增量审查 approved 后 `status=complete`。Q04 delivery gate 已标 complete。
- [ ] SW-IDENT 收尾：交付方修正 `authorized_paths` 与新增 evidence store/test 的授权出处，再逐 case 交付候选导入、裸 ticker、名单 CLI/身份历史等剩余公开路径证据；总控复核后才能关闭 W01–W03。完整 G2b 另等 owner 的 verified/多挂牌/AnalysisSubject 正例。
- [x] TH-01/IN-02 预研收尾：完整 Markdown + handoff JSON 通过公开 CLI/schema、关键文件哈希与独立只读复核；原报告/JSON 字节按报告 SHA 不可变归档并更新索引。实施仍需决定独立技能仓与 `local-skills` 镜像的唯一 owner、对已移动上游做增量核对，且不得将 T01/T02 标完成。

### 2026-09-30 — 本地检查点与规划文件同步

- [x] 将当前 invest-quick-scan 本地工作树进度提交为 `eb462d48321f3247eabf18daa57a4d4606405ca4`；共849个文件。提交涵盖本地实现、题库/发布物、契约、测试及已完成阶段证据，不代表所有跨项目任务完成。
- [x] 更新施工卡实施摘要与G2b交接：步骤1—4随检查点提交，版本/CLI/golden格式与测试记录不变；G2b仍需StockWiki真实公开DTO/serializer golden。
- [x] 计划校验复跑有效：107 tasks / 366 acceptance cases / G6；`tests/test_implementation_plan.py` 为80 passed / 53 subtests。
- [ ] StockWiki provisional Entity producer golden 与四态 mapping DTO 的 IQS 消费验收已完成当前接口切片；完整 G2b 仍等 W02 真实历史/近名、verified/多挂牌/AnalysisSubject owner 证据。S06 仍等待真实 StockQA→StockWiki 事务 ACK、router 2.1 真实历史样本和跨仓端到端验证。C01—C07 回执刷新继续暂停。
- [x] 第二笔提交 `5aec24044aabdbf5187725e51066cd21fc39bc33` 同步了实施摘要、handoff和进度记录；本次再同步 `task_plan.md`、`findings.md` 与 `progress.md`，不改外仓。

### 2026-09-30 — Q02 MiMo 实际搜索验收

- [x] 在StockQAbyLLM获授权范围内，对公开CLI MiMo live E2E运行一次真实Microsoft搜索。沙箱内两次请求在HTTP前ConnectionError；同一隔离测试在批准的联网执行环境成功，1 passed / 13.63s；临时目录不存在，测试前后StockQA Git状态条目数均为55。
- [x] 修正新增live E2E的失败摘要，使错误描述限长并脱敏MIMO_API_KEY/MIMO_PLAN_API_KEY；未记录密钥或原始响应。实际成功断言覆盖provider/model、response ID、search_status、绑定的search receipt、非空来源与URL citation basis。精确运行记录和源文件SHA见`docs/implementation/contracts/validation-Q02-MiMo-live-E2E-2026-09-30.md`。
- [x] 同一StockQA工作树离线回归`test_llm_client.py`、`test_llm_provider.py`和`test_quick_scan_cli.py`共159 passed / 17.45s；从唯一临时工作目录运行、关闭`base_url`插件及项目coverage/cache addopts，并把pytest basetemp置于临时根；运行后临时根不存在，StockQA Git状态仍为55项。
- [x] Q02首个提供商任务在精确StockQA工作树快照上完成验收：独立只读复核匹配五个源码/测试SHA，确认LLM-02/LLM-11所选离线覆盖并未发现P0/P1；MiMo公开CLI真实搜索1 passed / 13.63s，provider/model、响应关联搜索回执、来源与临时目录清理均有断言。复核提出的P2断言增强和无citation正文URL负例记录为后续测试改进，没有因此重复付费live调用。
- [x] 复核发现的旧receipt/验收目录状态按当前规则正确处理：task-receipt v2于2026-09-29退役，`acceptance-cases.json`声明其为规格而非运行结果；旧Q02 receipt保持只读，`specified_not_executed`规格值不改，当前结果写入`progress.md`及批次验证记录。Q02任务级验收对记录的StockQA工作树快照通过，但不等于G1、跨仓生产接线或全项目完成。StockQA工作树仍有既有未提交改动，本次未将其合并提交。


### 2026-10-01 — QA-04 / SW-IDENT acceptance revalidation

- [x] QA-04 在临时 cwd 复跑六文件离线批次 **246 passed**，Ruff 通过；增加 `next_run` 两题回执均无 `policy_transition` 的公开 CLI 断言。临时根删除，StockQA 55 项状态前后字节一致；未调用 API/网络、未下载公司资料。
- [x] SW-IDENT 在当前 StockWiki `b4f3846` 复跑身份、G2b、证据存储、MIC 与 IQS public CLI 跨仓 E2E 聚焦包，**113 passed**；临时 pytest/home 根删除，StockWiki 状态仍只有既有 `.claude/`。
- [x] 新复核报告记录精确文件哈希和 handoff CLI 结果：QA-04 CLI `valid` 仅表示自述格式/范围可解析，回执仍 stale、`result_commit=null`；SW-IDENT CLI `invalid/changed_path_out_of_scope`，新 evidence store/test 未列在 `authorized_paths`。
- [x] QA-04 交付快照和当前 handoff 尚未一致（2026-10-01 观察，已过时）：**2026-10-02 已收口**——`fe11f63` 隔离快照 + handoff 刷至 complete + CLI valid + 独立审查 approved（Phase 50）。SW-IDENT handoff 路径声明已修正（StockWiki `aa17f93`，CLI valid），W02/W03 生产证据仍在交付中。历史观察文件：`reviews/IQS-lane/parallel-package-revalidation-2026-10-01.md`。

### 2026-10-01 — 当前执行状态与首批候选来源

- [x] 重验 QA-04、SW-IDENT、TH-01/IN-02 handoff；独立结论见 `docs/implementation/reviews/IQS-lane/parallel-package-revalidation-2026-10-01.md`。QA-04运行行为有246项离线回归证据；该复验时观察到61条，随后DWA-06盘点为63条（含`?? nul`），handoff仍记55且`result_commit=null`。StockWiki `b4f3846`聚焦回归为113项通过，但handoff CLI因`changed_path_out_of_scope`拒绝，W02/W03完整公开入口与full G2b仍未完成。不能将格式有效或聚焦测试通过扩大为交付验收。
- [x] TH-01/IN-02 归档索引含两项，报告和 handoff hash 全匹配且均通过相应 schema；只验收只读预研，T01/T02 仍 not_started。
- [x] 本仓 S06 的本地范围已有 57 项焦点回归日志与独立复审；剩余真实 StockQA→StockWiki ACK、router 2.1 真实历史工件与跨仓 E2E 属于外部验收门。避免无变化地重复同一 S06 批次。
- [x] 按用户先前指定的文件名规则只读搜索 Projects：94 个可读匹配文本文件、12 种精确字节内容；六个有效来源产生 209 个 A 股挂牌候选、7 个美股挂牌候选及 331 个去重名称标签。名字/代码未被当作 issuer identity；`中信建投` 的两个不同代码保留为歧义。报告及完整逐行来源见 `docs/implementation/reviews/universe-source-inventory-2026-10-01.md` 和同名 JSON。未写 StockWiki、未导入股票池、未扫描公司。
- [x] 用户已确认首批输入采用审计报告中的216个带市场的挂牌候选；331个名称标签保留为待解析提示，不据此自动合并发行人或扩大挂牌成员。确认只覆盖候选范围，不等于StockWiki权威导入或扫描。
- [ ] 216 候选 owner 预览与导入授权（入口已交付）：**2026-10-02 W02 preview 入口已完成**（StockWiki `33dbf7f`，`stockwiki identity-preview`，11 选择器绑定 8 case，check_all 698 passed），并已产出首份真实预览报告 `reviews/universe-identity-preview-2026-10-02.json`（216/216 unresolved 空权威库诚实状态、中信建投重叠组、零 membership/零 paid_work、跑前后 DB digest 与成员表不变）。**剩余：owner 审阅该报告并给出 216 导入的明确写授权**（unresolved/ambiguous 不进付费扫描队列不变）；空 schema v1 建库已按宽授权执行并记录（仅建表零导入、可逆）。
- [ ] 下一批跨仓候选施工包：StockQA Q05 **已于 2026-10-02 完成并 verified**（`1318a2a`+`7ced082`，Phase 51）；StockWiki W05 仍等 W01、W02、W03、G1、S05 全部满足并取得 W05 精确写授权后才能开工。当前并行推进的是 StockWiki W02/W03 生产 preview 入口（216 候选 owner 预览前置，用户 2026-10-02 已授权）。
- [ ] QA-04 待交付方提供安全隔离的当前快照、刷新 hash 的 handoff 和 review；SW-IDENT 待交付方修正声明路径并交齐 W02/W03 生产入口。总控收到更新后重验；full G2b 仍需真实 verified、多挂牌、AnalysisSubject 与历史区间 owner 证据。

## Phase 46: 未提交工作树只读盘点与独立任务包

Status: intake_and_synthesis_complete; DWA-03_protocol_breach_DWA-04_visibility_stop_DWA-05_scope_breach_DWA-06_drift; followups_pending

- [x] 对 `Projects` 下顶层 Git 项目做只读状态扫描，以每个项目目录为 Git 根，排除嵌套测试夹具造成的伪项目发现；Git 安全目录只通过单次命令参数设置，不改全局配置。
- [x] 为本次发现的7个脏仓库固定 HEAD、分支、完整 `--untracked-files=all` porcelain 清单、状态摘要和可读取的非敏感文件哈希；每仓库任务卡均要求开始/结束复核，漂移则停止旧快照归因。
- [x] 任务包明确只读边界、凭据/本地配置脱敏、每条路径的来源/未提交原因/分类/处置建议/信心等级，以及禁止自行删除、提交或运行会改动数据的脚本。
- [x] 将 DWA-01 至 DWA-07 分派给独立只读 harness 并收回交付；逐项核对快照/状态漂移和任务边界。完成收件不代表每份审计均通过，例外结论见验收报告。
- [x] 总控汇总七份交付并形成验收结论；对违规、可见性不足、漂移或证据不足的项目明确保留待办，不推断文件可删除或可重建，也不据此清理或提交外仓改动。

独立任务包索引：`docs/implementation/reviews/dirty-worktree-audits/2026-10-01/README.md`。

- [x] 文档门槛：`tests/test_implementation_plan.py` 与 `tests/test_parallel_lane_plan.py` 共89 passed / 53 subtests；7份快照摘要、条目数量、卡片绑定与哈希清单完整性检查通过，`git diff --check` 通过。
- [x] 收到并审阅 DWA-01 报告：快照绑定与唯一疑似凭据路径处理符合只读边界；不检查凭据内容、不建议提交，外仓后续 ignore/迁移需 owner 决定。
- [x] 收到 DWA-04 可见性漂移报告并按规则停止逐项归因；owner 环境的只读复核为 6124 条、原状态摘要一致，2274/2274 个普通可哈希路径一致。该 harness 报告不构成逐条盘点完成证据。
- [x] 记录 DWA-07 owner 决议：采用有效全局忽略下的空状态（SHA-256 `e3b0c442…`）作为新基线；保留初始快照以供追溯，`.claude/settings.local.json` 仅记录路径元数据、不读取内容。
- [x] 收齐 DWA-01–DWA-07 全部交付并形成 `docs/implementation/reviews/dirty-worktree-audits/2026-10-01/acceptance-review.md`：DWA-01/02/07 通过；DWA-03 因未遵守只读/漂移停止拒收为合规审计；DWA-04 正确停止但未完成归因；DWA-05 读取受限 `config.json` 内容；DWA-06 披露新增 `nul` 漂移且逐路径状态表需细化。
- [x] 2026-10-01重查 DWA-03/04/05 的当前 HEAD、文件级状态数与 porcelain SHA 均匹配原冻结快照；DWA-03 的 `.dwa03v2.py` 不存在。DWA-04 为6124项且与原状态摘要相同。DWA-05 的 `config.json` 仍按未知处理，未读取内容。
- [ ] 后续动作保持只读：DWA-03/04/05 可按原任务卡重新派发，但接手者必须从头重核基线和结束状态；DWA-04需6124项的同等可见性，DWA-05不得读取`config.json`。DWA-06当前63项、含`?? nul`，不同于62项原快照；先冻结新基线并保留该路径为未知，再做逐路径报告。不得基于审计建议自行改动或清理外仓。

### Phase 47: V02独立评分尺本地候选收尾与暂停

Status: local_candidate_implemented_and_reviewed; overall_V02_partial; paused_by_user

- [x] 按Phase30允许接口冻结后连续推进的规则，实现本仓V02纯候选层；没有关闭G3或重排107任务依赖。schema、内容寻址候选、加载/API/公开只读CLI与兼容文档已落地。
- [x] EVO-05—07本地测试覆盖固定24构念/替代、分母和覆盖率、NA/等级/关键风险、权重并列派生和原观察不变、题义/作用层/期间/模型不可比、规则method/release绑定、字节hash及重复key拒绝、真实归档与隔离CLI。未连接生产数据库或模型。
- [x] 独立审查的严格int、附加critical缺轴、普通core追加critical三项漏洞已修复并补反例；119 tests / 84 subtests通过，Ruff通过，plan validate仍为107 tasks / 366 cases / G6。
- [x] 内容寻址归档在Windows autocrlf下以目录内JSON `-text`保持字节；真实临时Git add/checkout回归通过。最后V02定向15 tests / 27 subtests，PWF文档门93 tests / 241 subtests通过。
- [ ] G3校准、生产caller观察/等级认证、StockWiki持久化/CAS/历史重算与V16活动资格另行实施验收；候选`calibration_sample_refs=[]`，不可宣称已校准或已上线。
- [x] 首轮测试发现两项fixture与既定门槛不一致：NA需screening_audited、合法跨snapshot scope变化须在各快照内部一致。修正fixture并保留原校验要求。缺失`pyproject.toml`的字面搜索无产品影响；后续不再以该不存在路径作检查入口。
- [x] 用户要求手头工作完成后提交/推送/暂停。本仓`git remote -v`为空，保持未配置，不猜测远端地址；完成本地提交后暂停，不继续其他施工或外仓清理。源码/文档发布按本轮Git提交历史定位。

证据：[评分尺契约](docs/implementation/contracts/scoring-rubric-evolution.md)、[独立审查](docs/implementation/contracts/review-V02-closeout-2026-10-01.md)、`validation-V02-red-2026-10-01.log`及`validation-V02-green-2026-10-01.log`。

### Phase 48: 跨模型接手指引与状态时间口径

Status: documentation_complete; no_task_or_gate_change

- [x] 建立无聊天上下文的接手流程：唯一PWF计划解析、权威文件用途、当前事实与旧snapshot区分、依赖/owner/allowlist选择顺序。
- [x] 写明IQS、StockQA、StockWiki及只读外仓的历史授权范围和限制；要求每个handoff提供精确基线/结果、状态摘要、契约hash、分项测试结果、清理、网络费用、阻塞和单一下一步。
- [x] 将测试/审查明确保持在owner批次、G0—G6和跨仓/高风险门，不为小卡增加独立review或重复整套回归。
- [x] 从实施入口与并行施工包索引加入醒目链接；不改变任务数、验收case、任务状态、外仓权限或产品契约。

### Phase 49: 2026-10-02 只读状态重核与 DWA 复审重派

Status: reaudit_completed_accepted; awaiting_owner_dispositions_and_acl_unlock

- [x] 按接手指南恢复唯一 legacy 计划并重核各仓 HEAD/工作树/handoff：IQS `master@db22815`（无remote）；StockQAbyLLM `master@3c685dd` 63条含`?? nul`与 DWA-06 结束态 digest 一致；StockWiki `master@b4f3846` 干净；QAbyLLM `main@64ec7721` 66条（`.claude/settings.local.json` 被用户全局忽略吸收）；StockInfoDownloader 6条与冻结 digest 完全一致；company-wiki `master@f318b35` 前进5个文档/CI类提交、施工卡hash变`5b9101fa…`仅追加状态注记、范围未变。QA-04/SW-IDENT handoff 无新交付，Q05/W05/T01/T02 前置门未开。
- [x] 查明 DWA-04 基线漂移的可证实事实：冻结 6124 条（3778 ` D`）vs 当前 416 条（0 ` D`），HEAD 未变、` .git/index` mtime 仍是 09-27，抽样原 ` D` 文件仍在盘上且 mtime 早于快照；幻影条目/事后变更/混合无法只读区分，保持未知并列为复审第一问。修正超长相对路径下存在性探针假阴性的核查方法。
- [x] 生成四仓 2026-10-02 复审基线（snapshot.json/snapshot-status.txt/snapshot-files.jsonl，LF+尾LF 摘要规范，敏感路径 omitted、不可读 inaccessible）并编制 `docs/implementation/reviews/dirty-worktree-audits/2026-10-02-reaudit/` 四张任务卡与索引：DWA-03R 合规复审、DWA-04R 漂移归因+逐路径盘点、DWA-05R 零漂移禁读复审、DWA-06R 63条完整逐路径清单（`nul` 保持未知）。
- [x] DWA-04R 全面审查与修复：补 2 条超长路径漏哈希（`\\?\` 前缀，与 10-01 逐字节一致，manifest 416/416 hashed）；漂移归因经独立只读复核收口——3778 ` D` 为幻影条目（3778/3778 在盘、361 哈希 0 差异、ctime≤09-21、reflog 无恢复），`??` 2334−1971−14+55=404 精确闭合（55 条为 09-27 漏视旧文件；1971+14 在拒绝访问组，去留未知）。证据见 `2026-10-02-reaudit/DWA-04/coordinator-review-2026-10-02.md`；不清理/不恢复/不提交 revenue-forecast。
- [x] 本次全部写入限于本仓 DWA 目录与 PWF 文件；外仓只读，无网络/API/下载，无产品测试运行，无需新增授权。快照生成脚本为一次性，生成后已删。
- [x] 将四张卡交给独立只读 harness 执行并收回 `DWA-03R/04R/05R/06R` 报告；总控按验收审查后决定可接收范围。DWA-04R 归因未闭环前不得对 revenue-forecast 作任何清理/恢复/提交建议的执行。
- [x] 2026-10-02 四个独立 harness 并行执行完成：起止核验全 PASS 零漂移，目标仓零写入；四份报告归档 `2026-10-02-reaudit/DWA-0X/report.md`；验收 `acceptance-review.md` 四包全部接受（前次四项拒收原因均纠正）。DWA-04R 按收口归因执行（引用总控、5/5 抽样一致、未重做）。
- [x] P0 记录：QAbyLLM `simple_porter.py`（未跟踪、未进 Git 历史）含 `sk-` 形态硬编码密钥，归档报告密钥值 0 命中；需 owner 轮换+脱敏后才可提交。`.gitignore` `test_*` 隐藏测试待 owner 决策。
- [ ] 1985 条 ACL 拒绝组解封（`takeown` 因本 shell 非管理员失败；管理员命令已写入验收审查，owner 侧执行后重采 DWA-04 状态）。
- [ ] 各包 P1 处置建议（DWA-04 批次 A–D、DWA-05 还原/ignore、DWA-06 提交分组、DWA-03 分组）等逐项精确授权后执行；QAbyLLM 密钥脱敏已于 Phase 50 完成（轮换仍待 owner 服务商侧）。

### Phase 50: QA-04 正式收口与 Q05 解锁

Status: complete; handoff_complete_at_fe11f63; delta_review_approved; sw_ident_cli_valid_at_aa17f93; Q05_startable

- [x] P0 密钥脱敏：QAbyLLM `simple_porter.py` 硬编码 `sk-` 密钥替换为环境变量读取（值零回显、0 残留）；密钥轮换仍需 owner 服务商侧执行；`.gitignore` `test_*` 决策仍待 owner。
- [x] Q04 当前内容重验：246 责任批次 passed + Ruff 全过；确认四 Q04 文件与底座新模块 import 耦合、孤岛提交会断链，按 DWA-06R"可提交57"提交完整暂存体（写前报告精确列出）。
- [x] 钩子链修绿（未跳过钩子）：HEAD 基线实测 mypy 0/bandit 0，证明 93 mypy + 4 bandit 为本批引入；5 并行 agent 分文件修复（guard+raise 替代 bare assert、`# nosec B608` 纯占位拼接标注、局部标注/重命名），black/isort 归一，复验 mypy 0/bandit 0/246 再过。
- [x] 提交 `fe11f63`（58 跟踪文件：Q04 四文件+不可分割底座+pre-commit/-p no:base_url 与 .gitignore schema 豁免）通过完整 pre-commit 链（含 pip-audit 网络），推送 `github.com/zhengcb81/StockQAbyLLM`；提交后脏树 5 条未跟踪与 DWA-06R 分类一致。
- [x] handoff 刷新（result_commit/接口哈希/worktree_after/verification 增 5 项/network_calls=true/open_items 换代）→ CLI valid → 独立只读增量审查 **approved**（F1/F2/F4/F9 复验在位、行为保持无风险、118 案例测试、ruff 净）→ `status=complete` + `review.snapshot_commit=fe11f63` → CLI 复验 valid。Q04 完成判据全满足。
- [x] Q05（约束日志/缓存内容及完整请求键，deps Q03+Q04）已解锁，为下一实现批次（StockQA，需施工卡+写前报告）。
- [x] SW-IDENT handoff `changed_path_out_of_scope` 路径声明修正完成（StockWiki `aa17f93`，唯一文件 `.planning/sw-ident_handoff_2026-09-30.json`，补列 user-granted 两路径）→ IQS CLI **valid**；status 维持 partial（W01–W03 生产证据缺口未闭）。StockWiki 无 remote，仅本地提交。

### Phase 51: Q05 内容边界与完整请求键实现

Status: verified; commits_1318a2a_7ced082_pushed; review_blocker_fixed; LLM-08_09_16_all_green

- [x] 规格读取与勘察：Q05 三步/三 case/四不变量；定位日志 sink（无脱敏限长）、`RequestCache` 键缺维度、无公开答案序列化边界、两处 config WARNING 原始对象落日志。
- [x] TDD RED→GREEN：`tests/unit/test_q05_content_boundary.py`（14 例）+ outbox LLM-16（3 例）先失败；实现四文件后全绿；`get()` 体漏传维度的编辑缺口由 identical-hit 用例暴露并修复。
- [x] 实现：`ContentBoundaryFormatter`（脱敏+2000 字符限长，双 sink）；`REQUEST_CACHE_KEY_FIELDS` 8 维键+装饰器透传（TTL/LRU 不变、生产不接线、不决定 fresh）；公开 `serialize_answer_for_exchange`（9 字段白名单、伪造字段丢弃、描述限长 5000、无 I/O）接入 `to_quick_scan_dict`；config WARNING 结构化。
- [x] 验证：Q05+outbox 39、受影响回归 211、246 责任批次、mypy 0、bandit 0、触及 6 文件 ruff/black/isort 净；提交 `1318a2a` 过完整钩子链推送。
- [x] 独立增量审查 changes_requested（唯一阻断 ruff F401+F541）→ 修复 `7ced082` 推送并复验（ruff 六文件净、57 passed、静态门净）；LOW/INFO 观察（脱敏过度遮蔽、装饰器维度仅 kwargs）记录接受不改码。**Q05 verified**。

### Phase 52: Q02 MiniMax verified live receipt（Q02/Q03 关闭）

Status: verified; commits_ced1faa_82f1794_pushed; independent_review_approved; both_minimax_live_e2e_passed

- [x] live 门声明后执行两个 MiniMax E2E，首轮全败（search_call_count=0）；四轮 live+七轮单次探针分层定位，逐项对照官方文档（ToolChoice 仅 auto/none；system 属 instructions 字段；server-tool 慢请求需加大 timeout）。
- [x] 修复链：anthropic tool_choice 合规化；中文 system 行移出 input 进 instructions（实证 3/3 抑制 vs 4/4 正常）；_build_prompt 搜索强制令+JSON-first（前导 1297→139）；parser strict 升级为"唯一完整对象+全绑定"（Q02+Q03 联合批次，Q03 fail-closed 性质全保留）；3 处旧姿态测试契约更新；live 超时 300/360（官方 Tip）。
- [x] 证据：mypy 0/bandit 0/静态净；离线全量 854 passed/4 skipped；**两个 MiniMax live E2E 最终代码 PASSED**（累计约 20 次单题级调用，量级角位人民币）；`ced1faa`（8 文件）+ `82f1794`（3 文件）过完整钩子链并推送。
- [x] 独立审查 changes_requested（Medium：payload 拆分无契约测试；LOW×2）→ 修复 `82f1794`（锁 instructions/input 拆分的契约测试+零候选用例+docstring）→ 恢复同会话复核 **approved**（变异探针验证测试有效性；全量 854 passed；明确确认 case→test 映射与 live 结果满足 Q02 完成判据）。**Q02 verified；Q03 关闭条件随之满足**（r2 verified + 本批 parser 增量经同审查 approved，差分审计无安全回归）。
- [x] M1 剩余更新（2026-10-02）：**S03 已 verified**（用户改判 (a) 关闭 3.1.0 样本要求 + 5 case 测试复跑全绿 + 既有独立复审）。M1 仅剩 **S06**（等真实事务 ACK/router 2.1 工件/获批跨仓 E2E）与 **L01**（deps 已全满足，正式解锁——需真实搜索探针 live 成本声明后执行）→ G1（随 L01/S06）。

### Phase 53: W02 候选 preview 入口与真实 216 预览报告

Status: entry_delivered_stockwiki_33dbf7f; real_report_produced; awaiting_owner_review_and_import_authorization

- [x] 用户第1项授权（W02/W03 preview 施工）；explore 勘察确认零 preview 基建、216 输入文件位置、14 case 中仅 ID-02 已绑定。
- [x] 四文件写前报告批次：`quick_scan_identity.py`（ro 零写库/三态命名理由/规范 JSON/命名拒收）、`cli_parsers/quick_scan.py`、`cli_registry.py` 接线、`test_quick_scan_identity.py`（11 选择器覆盖 ID-01/02/03/UNI-02/UNI-06/ID-12/ID-13×2/ID-14 + CLI e2e + 只读证明）；handler 落允许模块的 deviation 已记录。
- [x] 验证：11 passed 首跑、ruff/black(100) 净、`check_all.sh` 698 passed + 覆盖率双 PASS + 框架 PASS；StockWiki 本地提交 `33dbf7f`（不加 remote，决定7）。
- [x] 真实预览：空 schema v1 前置建库（0 导入、仓内 ignore、可逆，宽授权下执行并记录）→ 216 报告 exit 0 落 `reviews/universe-identity-preview-2026-10-02.json`；零 membership/零 paid_work；跑后 DB/两仓状态只读复验不变。
- [ ] owner 审阅 216 报告 → 给出导入写授权与 ambiguous（中信建投组）消歧证据要求；此后才谈导入与扫描。
- [ ] W03 剩余公开路径（UNI-03/04、ID-05/06、UNI-08、ID-15 的 add/remove/pin/diff/explain CLI 与身份历史事件）为下一 StockWiki 批次。

### Phase 54: 决定6执行 — DWA 四仓 P1 处置全量落地

Status: complete; all_four_repos_disposed_and_pushed; unknowns_preserved

- [x] revenue-forecast：A=360 路径精确对账（`core.longpaths` 本地启用）、B=先测后提（17+全目录绿）、C=4 台账、D=ignore×4+删2空文件（mutation/bak/周志选 ignore 留盘）；推送经 pre-push 门三轮根因取证（外部瞬态写入+多进程时序+GBK 解码）后 `PYTHONUTF8` 缓解全绿推送 `5319ee26`；1985 未知集原样保留。
- [x] StockInfoDownloader：还原污染报告+html ignore（`88e37ea`）、映射与 e2e 报告结构审查后入库（`064a837`）；已推送；盲区 config/claude 未碰；orgid 真实性联网核验=记录残余。
- [x] QAbyLLM：F/B/A/C/D/E 六批（`8e79774`→`ad389f8`）推送完成；76 测试全绿；gitignore 手术解藏测试、13 处个人路径脱敏、porter 语法修复；E 仪表板 diff 安全审查通过；34 不建议提交项按审计保留未动；环境按 requirements 补装声明依赖（langchain 按代码 API 锁 0.3 线）。
- [x] StockQAbyLLM：无操作（`fe11f63` 已覆盖，决定8 保留四文件）。
- [ ] 队列剩余（均已授权）：S06 跨仓 ACK E2E、W03 剩余公开 CLI（UNI-03/04、ID-05/06、UNI-08、ID-15）、L01 真实搜索探针（先 live 成本声明）、DWA-04 2401 条新基线扩盘盘点（含1985解封组分类）。

### Phase 55: W03 剩余批次（名单 CLI 与挂牌/身份历史）

Status: verified; commit_4fbda21_local; review_approved; baseline_registered

- [x] 写前报告 6 文件批次：store v2 迁移+`_save_prepared` 拆分（与原体 diff 仅差内部 close）+7 个新方法；`quick_scan_universe.py` 新建（成员操作+diff/explain+CLI handlers，services/ 范围 deviation 已记录）；9 个 CLI 子命令；26 个 W03 选择器绑定全部六 case（UNI-04 字面 2003 成员、socket 炸弹零网络、v1→v2 升级保数据、CLI e2e+拒收）。
- [x] 门：ruff/触及文件 black(100) 净、`check_all.sh` 全绿（套件+覆盖率+框架）。基线注册后尺寸门降 warning、0 errors；实测非基线新大模块与超 critical 仍报 error（门未被削弱）。
- [x] 独立审查 **approved**：`_save_prepared` 与原体95/96行一致；六 case→selector 映射齐全；37 passed+ruff+black（预存债注明）；零网络双补丁验证；CLI 九命令+规范 JSON+exit2 实测；基线登记 accept-with-justification。10 条 low/info 记录接受不改码（owner 签收时显式确认基线登记与 W03 步骤5 分离满足）。
- [x] 真实工作区 `scan.sqlite` 幂等迁至 v2（空库、gitignored、工作树净）。
- [ ] owner 签收 W03 时的两点确认：基线登记（quick_scan_store.py，Stage-3.2 拆分延后）与步骤5 reporting-scope 分离式满足。

### Phase 56: S06 收口（证据化路由与多轴选择）

Status: verified; closeout_review_approved; hashes_recorded; honest_scope_boundaries_preserved

- [x] deps 复核：S05、S03 均已 verified → S06 正式解锁（其 tasks.json 完成判据本就允许 2.1 仅合成兼容路径，不强制真实 ACK/E2E——旧 PWF 叙述中"真实ACK为阻塞"的口径按权威判据纠正）。
- [x] 聚焦套件复跑（收口独立复审执行并落盘）：`routing+closure+adapter+module_registry+plan` **147 passed/80 subtests**、`question_sets -k mod19/composition/closure/MOD` **20 passed/11 subtests**，隔离日志 `contracts/validation-S06-closeout-2026-10-02.txt`（640 行，含命令/计数/时长/判定）。
- [x] 当前版本哈希记档（完成判据第2条）：12 个源/配置/测试 SHA-256 写入日志并与 HEAD 实测一致；厘清复审谱系——09-27 MOD18/MOD19 复审有哈希（现已过时，因 eb462d4 于09-30 首次入库）、09-29 修复轮复审无哈希（流程缺口，本轮补齐）。
- [x] 五 case→selector 全映射（8/9/19/4/30）+ 规格符合性逐点引用（validate_route_for_execution decision_id 锚、阈值门、确定性事实免疫、48 谓词激活、ROUTE_02 文档）；MINOR2 过滤缺口按 node-id 补跑 **6 passed**；MINOR1/3+INFO×3 记录接受。**裁决 approved**。
- [ ] 诚实边界固化进所有后续文档：router2.1 合成路径不称真实历史；跨仓 ACK/E2E 属 W05/G1 域，S06 不声称。

### Phase 57: L01 收口（10家公司真实搜索探针与小样本）

Status: verified; freeze_pinned_51fbce1; review_approved_two_rounds; budget_at_cap_honestly_recounted

- [x] 冻结先行：`reviews/L01-pilot-freeze-2026-10-02.json`（10 家 CN×5（含 STAR/BJ/GEM）/US×3/HK×2；`probe:<listing_key>` 仅为探测内绑定不称 issuer 解析；IQS_05+IQS_06 双题；caps 20 primary/40 attempts；rate_cards 空→零编造单价；LIVE-02 零搜索即全批止损门）。F5 整改：冻结文件已入库钉版（IQS `51fbce1`）。
- [x] 执行（live，成本已声明）：Phase A 茅台×IQS_05 先行（搜索 2 次/19 源，答案因模型输出平衡但非法 JSON → 严格解析 fail-closed → unknown，按 rollback 规则原样保留不重跑）；Phase B 其余 19 题。**11 次 CLI 调用承载 20 个问题级 primary requests = 恰好用满 20 上限未超**，HTTP 20≤40，41 次真实搜索，388 条来源，18 题得分（4–9），2 题 fail-closed unknown（茅台 phaseA、阿里巴巴 IQS_06），0 mock。
- [x] case 证据（LIVE-01/LIVE-02/SC-01/LLM-01/LLM-02/BUD-04）全部落 `StockQAbyLLM/pilot_runs/l01_2026-10-02/`：11 份回执 JSON + run-log + _score-rows + 冻结题面 + 试点报告；SC-01 双校验 20/20（status↔score、`answer_sha256` 对规范序列化 `ensure_ascii=False,sort_keys,compact` 逐字节绑定；ASCII 转义形式仅 2/20 非绑定形式）。acceptance-cases 状态字段不改（证据入 PWF/contracts 口径）。
- [x] 独立审查两轮（task `ses_f0057137dffew9k5XUUTgxLW0f`）：首轮 changes_requested（F1 预算按调用次数误计→须按 20 请求重述、F2 表格两格错、F3/F4 措辞、F5 冻结未钉版、F6 路径缺前缀）→ 修复后二轮 F8+info（"11 requests"分类学残留、phase-A 字样歧义）→ **approved**，四文件 SHA-256 记档（pilot-report `034c9d92…`、run-log `abecd559…`、_fix_budget `6108cdca…`、freeze `7e07998f…`）。
- [x] 提交推送：StockQA `7a40a98`（试点包）+ `a8650c0`/`cea6efc`/`1f04a8f`（审查整改）；IQS `51fbce1`（冻结钉版）。预算重算脚本 `_fix_budget.py` 随包入库（断言 11/20/20/41/388，可复算）。
- [ ] owner：MiniMax 控制台账单核对（决定9；本批 20 completions + 41 searches，另 Q02/Q03 早期单发诊断另计）。
- 下一步：**G1 审查**（deps L01+S02+Q05 全部 verified，G1 已解锁；invariants I01/I05/I15/I17/I19，cases REV-01/02/03、LIVE-02、SC-01、LLM-08、REV-05，allowed_changes=reviews/G1/ 新增）。

### Phase 58: G1 收口（M1 完成）

Status: verified; review_approved; scope_deliverable_published; M1_closed

- [x] G1 解锁复核：deps L01+S02+Q05 全 verified；read_first 两设计文档通读（stock-pool §2/§5/§10/§11、universe §3/§4/§7）。
- [x] 三批离线证据（零网络、零源码改动、仅写 `reviews/G1/`）：`g1_verify.py` 30 检查 0 失败 + 2 FINDING（独立常量 41/388/20/11 推导，不反读报告）；70 passed 0 skipped（Q05 边界+parser/generator/CLI 分数链当前快照）；live 套件 2 passed+4 环境门 skip 逐条入 log；非 live 0 skip/0 xfail（唯一条件 skip 未触发）。log/脚本 SHA-256 入记录。
- [x] 七 case 逐项判定（每项引实测输出）：LIVE-01（20/20 executed+response_id、0 mock）、LIVE-02（止损门未触发=负向条件未现、rollback 合规）、SC-01（`==8` 精确相等断言三处 + 20/20 线上重放）、LLM-08（14 边界测试 + 正文/凭据/长度扫描 + 密钥文件未跟踪）、REV-05（L01/S02/Q05 材质矩阵：真实搜索事件、轻资产约束、当前快照测试回执、最新审查）、REV-01/02/03（可复现命令、skip 全列、旧审查不放行新代码、期望值独立推导）。
- [x] 发现：F1（medium）结构化信息日期 20/20 null→绑定为 L02 进入条件（二选一：补采集 or 正式接受 null=not-fresh，禁止 answered_at 顶替）；F2（low）来源仅 URL 无标题/日期→L02 冻结时决定；F3（info）receipt-S02 快照 3/4 哈希过时→以当前快照运行替代（REV-02 合规）；F4（info）18/388 http 旧链。
- [x] 独立复审 **approved**（task `ses_f0022a928ffewW1KsB6lHQRJE9`）：范围合规（两仓工作树核验、acceptance-cases 零改动）、脚本复跑与归档 log 字节一致、断言行号/计数 AST 复算、6 个文件 SHA-256 记档、L02 deps 与 tasks.json 一致、诚实边界原文在案。两条 non-blocking 观察（ruff 19 为引旧数、formatter 命令无独立 log）记录不改已批文件。
- [x] 交付物入库推送：`reviews/G1/{G1-review-2026-10-03.md, G1-60-company-scope-2026-10-03.md, g1_verify.py, 三份 log}` = IQS `f7860fb`；doc 门 89+53/valid/diff-check 全绿。
- [ ] **M1 全部 18 卡 verified → M1 关闭**。M2 现状：W04/W05 deps 齐（StockWiki 新路径需精确授权=当前唯一解锁候选）、L02 等 W07/W08/W09+冻结条件（F1/F2）。更正：Q13 deps 实为不齐（Q07/Q10 partial），原批误记已改。

### Phase 59: W04+W05 双卡收口 + owner 八项决定

Status: W04_verified; W05_verified; owner_decisions_2026-10-03_recorded

- [x] **W04 verified**（StockWiki 本地 `5f2739a`，无 remote=决定7）：`quick_scan_candidates.py`（494→570 行，分层候选 60/25/15 配置化、固定种子+稳定ID平局、缺口/重叠报告、ID-16 fail-closed 资格预检）+ 15 测试；独立审查两轮（`ses_eff7535c2ffeFZpJple3blTQQy`）首轮9发现（F1 输入指纹缺口、F2 付费门 fail-open 等）全整改后 **approved**，四文件 SHA 记档；`check_all` 728 passed。
- [x] **W05 verified**（StockWiki 本地 `aa3c6e6`）：`quick_scan_observations.py`（观察/ACK/冲突/更正四表追加式、单事务 apply、原回执重放）+ `quick_scan_import.py`（C06 内容寻址全复算、S05 冻结发布包重算题义/方法指纹、SC-05/06 自授予资格拒绝、DB-03 执行键隔离、ID-23 subject 双向精确绑定）+ 18 测试 + IQS 官方 fixture 哈希向量；独立审查两轮（`ses_efefdd575ffeEEGVWeBe9mGmVU`）首轮 1M+3L+2info（含递归禁用键、subject 单向校验、method-core 未钉、缺回滚测试）全整改后 **approved**（`87c77921…/c06f4c58…/28e75199…/fbd555de…` 记档）；`check_all` 748 passed、0 skip、框架 0 错。
- [ ] W05 遗留（记录接受，不改已批文件）：F6 `original_import` 未过滤 status（INFO 级、契约未定义该字段）——**下次触碰该文件时补 `AND status IN ('accepted','already_present')`**；F7 import 仅 Python API 无 CLI（契约 §6 端点另门）。
- [x] **owner 八项决定（2026-10-03，大白话答复原样记录）**：
  1. **216 导入：授权**（含推进消歧处理；中信建投标记按"歧义不强并"落地）。
  2. **rf 仓 1985 条临时文件：删除**（`.tmp-zr408-unit*`×3 + 14 scratch；删后重录 DWA-04 基线）。
  3. **MiniMax 账单：很便宜=核对通过**；运营事实记录：**MiniMax 有 5 小时调用限制**（L02 及后续批次派发须尊重该窗口）。
  4. **G2b 正样本：派 agent 搜索所需真实样本**（verified/多挂牌/AnalysisSubject/历史区间），找到后 **owner 授权签收**。
  5. **StockWiki 后续全部卡：一次性授权**（W06/W07/W08/W09/W13 及 W10–W16；沿用每卡写前报告纪律）。
  6. **QAbyLLM 34 项 + SID 2 盲区：清理**（按 DWA 精确清单执行，先报备后删）。
  7. **信息日期/来源元数据：选 a=补采集**（实现结构化 information_as_of 与来源标题/日期采集=L02 冻结前置）。
  8. **W03 签收两点：确认**（quick_scan_store.py 基线登记 + 步骤5 reporting-scope 分离式满足——owner 签收闭合）。
- [x] **决定2 已执行**：rf 1985 条全删、工作树 0 未跟踪、HEAD 不变（`reviews/dirty-worktree-audits/2026-10-03-owner-decision-executions.md`）。
- [x] **决定6 已执行**：QAbyLLM 34/34 删除（树全清）；SID html 已删、org_id 实测已==HEAD 无操作；SID 剩 2 条本地配置 M 不在范围。
- [ ] 依赖更新：W06（deps W05✓C04✓S01✓）与 W13（deps W03✓W04✓C01✓）**已解锁**（决定5 授权在手）；L02 仍等 W07/W08/W09 + 冻结条件（7a 选 a）。剩余队列：G2b 样本搜索 agent、216 导入、W06/W13 施工、7a 信息日期实现。

### Phase 60: W02 导入段（决定1：216 候选入库）

Status: batch_built; deviation_recorded; review_rerun_pending; real_import_pending

- [x] 写前报告（四改一增）：W02 allowed 内修改 `quick_scan_store.py`（v2→v3 加法迁移：`quick_scan_candidate` 表 + `apply_candidates` 单事务幂等/冲突计数；923→991 行守住 <1000 硬门）、`cli_parsers/quick_scan.py`（`candidate-import` 注册）、`tests/test_quick_scan_store.py`（版本断言改用 `SCHEMA_VERSION` + v3 表断言）、`tests/test_quick_scan_identity.py`（+5 导入测试）。
- [x] **范围偏离记录（复审 F1 整改）**：新增 `stockwiki/quick_scan_candidate_import.py` **不在** tasks.json W02 `allowed_changes` 枚举内——折进 store 会破 1000 行硬门、折进只读 preview 模块会破坏其字节级 DB 不变保证（复审亦独立确认两理由成立）。依据：**决定1**（216 导入授权）+ **决定5**（StockWiki 全卡授权，条件=每卡写前报告纪律），先例=W03 in-module handler deviation（`task_plan` Phase 53/55 两处）。同步动作：StockWiki `.planning/sw-ident_handoff_2026-09-30.json` `scope.authorized_paths` 追加该路径（11→12 条）且 `authorization_scope_ref` 引用决定1/决定5（先例 `aa17f93`）；模块 docstring 含 scope disclosure 句。
- [x] 语义与不变量：**仅暂存**——216 全 unresolved → `entities_created=memberships_created=paid_work_created=0`（测试加 DB 级 member/entity 计数=0 断言，复审 F2 整改）；同名（中信建投 002168+601066）分行不合并且各记 overlap 冲突组；内容哈希幂等（unchanged 保留原 batch/imported_at）；同行异容→`conflict` 只推进计数不覆盖原文；unresolved 带 `entity_id` 或 `scan_eligible=true` 直接拒收（命名错误码）。测试 16+22 全绿，`check_all` 813 passed/0 quick_scan skip/框架 0 错。
- [x] 独立复审（`ses_efe679da8ffearpOnLy0basq7Q`）：首轮 changes_requested（F1 记录缺失 + F2 测试加固；F3–F6 info）→ 三处记录落盘（Phase 60 本节 / handoff authorized_paths 12 条 / 模块 scope disclosure）+ DB 级 member 计数断言 → 二轮 **approved**；5 文件 SHA-256 记档（module `9fcf4113…`、store `ce88fce6…`、parser `fb868ab4…`、store-tests `5b34ef50…`、identity-tests `3f12dc3b…`、handoff `cf423a63…`）；`check_all` 813 passed 全绿复跑。
- [x] **真实 216 执行完毕（决定1 落地）**：`python -m stockwiki.cli --root <StockWiki> candidate-import --report reviews/universe-identity-preview-2026-10-02.json` exit 0 → 回执 `inserted=216, staged_total=216, entities=memberships=paid_work=0, overlap_groups_recorded=1, batch_c9aec572b56f6b91, report_sha c9aec572…/input_sha 2fd5f147…`（与复审 dry-run 哈希一致）；二次运行 `inserted=0/unchanged=216` 同 batch 同 `imported_at`。独立 DB 复验：`user_version=3`（v1 真库升 v3）、candidate 216 / entity 0 / security 0 / member 0 / universe 0、中信建投两行分立（unresolved、entity NULL、scan_eligible 0）、`SUM(scan_eligible)=0`、单 batch 单时间戳。
- [x] StockWiki 本地提交（叠加并行叙事消费道 `3c20d4d..ae0b3e3`，本批 6 文件：四改+一增+handoff 登记；不碰叙事道文件）+ 本 Phase PWF 推送。

### Phase 61: W06 verified（新鲜度与缺口计划器）

Status: verified; review_approved; followups_recorded

- [x] 写前报告：2 新文件 `stockwiki/quick_scan_freshness.py`（449 行，C04 `work_contract.py` 语义移植+缺口计划编排）+ `tests/test_quick_scan_freshness.py`（10 case 绑定）；零既有文件改动，allowed_changes 吻合。
- [x] 语义：纯函数计划器（fresh iff now<valid_until、缺日期=missing_date、事件提前失效、unknown 冷却→deferred→到期新代次、TTL/semantic/routing 分因、全局题库版本**永不**触发全量重问、请求身份五要素各改即换键且缓存绕不过新鲜度、only-planned-dispatch 计数、dispatch_started=false、零网络）；`source_available_as_of` 逐语义对齐 C04（TIME-07 截止日末边界）。
- [x] 独立审查 **approved**（`ses_efe3c002fffeAqlKqRsQDVvGSp`）：10/10 case 真绑定 0 skip、C04 差分比对（437 场景）边界逐行等价、`check_all` 823 passed 全绿、纯度/幂等/无网络逐探；两文件 SHA 记档（module `e4dfcf55…`、tests `3fdcfc14…`）。
- [ ] **审查跟进项（F1/F2，落在 W06 case 范围外，先于 work-item 存储落地前必修）**：F1=复用/恢复前缺 generation 对齐门（C04 `work_contract.py:160-162`：期望代次≠在途代次必须 dispatch）；F2=兼容性门在 resume/unknown 之后才判（C04 是 compat-first；要么前置、要么 docstring 写明"防重复派发"取舍）。F3=TIME-03 测试未真正变更 checked_at/imported_at 输入（行为已由审查探针证实正确，补测即可）。
- [x] StockWiki 本地提交 `d4779e6`（叠加 `01d6f17` 与并行叙事道基座）。

### Phase 62: W13 verified + G2b 检索签收

Status: W13_verified; G2b_sample_search_signed_off; G2b_card_still_open

- [x] **W13 verified**（StockWiki 本地 `d007a68`）：5 文件批次 = 3 新增（`quick_scan_maintenance.py` 472 行、`quick_scan_schema.py` 155 行、`tests/test_quick_scan_maintenance.py` 547 行）+ 2 修改（`quick_scan_store.py` 991→967、`tests/test_quick_scan_store.py`）。
  - **DDL 抽取守门**：W13 持久化需 v4 三表（nomination/intent/policy），store 已 991 行距 1000 硬门仅 9 行 → 把 v1/v2/v3 DDL 抽到新 `quick_scan_schema.py`（AST 逐体比对 vs `git show d4779e6` **完全一致**），store 只留数据操作与事务，967<1000。
  - **原子准入**：`save_member` 拆 `_member_txn`（供复用）+ wrapper；新增 `admit_with_intent` 单事务（成员+历史版本+增量扫描意图同落同滚）、`record_intent`（幂等 insert-once）。
  - **语义**：identity/user-exclusion 短路各给**唯一区分原因**（MAINT-03 四类分立）；quota 走 `soft_target_capacity`；`maintenance_report` 只读、永不因低分/单挂牌退市移出（MAINT-06/UNI-05）；LLM 发现=预算请求结构，零 LLM/网络。
  - 独立审查两轮（`ses_efe0f7da8ffeF8VM1wvirkbFHK`）：首轮 changes_requested（F2 空断言+缺 quota 覆盖、F3 MAINT-06 场景错配+2 处同义反复、F1 多余 @staticmethod、F4 already_member 精确匹配、F5 别名未建模、F6/F7 info）→ 全整改 → **approved**，5 文件 SHA 记档；`check_all` **832 passed**/0 quick_scan skip/框架 0 错；27 项对抗探针 + 10 项迁移探针全过。
  - 审批后仅 2 处**纯类型收窄**（`get_member(...)` 加 `is not None` 断言，LSP 噪音清理），行为不变、9 测试复跑绿——记录于此保 SHA 可追溯（审批版 test SHA `39d88b7c…` → 收窄后变化）。
- [x] **G2b 检索结果归档 + owner 签收**（决定4 落地）：`reviews/IQS-lane/G2b-sample-search-2026-10-03.md` —— agent（`ses_efeb4ef73ffeb04OTbpoo2e8c5`）四类样本检索从会话固化入盘：**A/C/D 真实样本 StockWiki 内 = 0**、**B = company-wiki 主档 653 美股同 CIK 组 + 148 A/H 对**（未进身份库）、可生成性分析、G2b 仍缺 5 项逐条列明。owner 口头签收本报告**完整性与诚实性**（2026-10-03）。
  - **签收 ≠ G2b verified**：A（发行人核验证据+建实体路径）、C（AnalysisSubject 实现+perimeter 回执）、D（schema 有效期列+外部带日期记录）各需新的 owner 决定；B 的 A/H 权威 bridge 待 owner 提供。G2b 卡保持未 verified。
  - 磁盘实测纠偏：`scan_observations.sqlite` 在真实工作区**缺失**（W05 只在 temp 建过表，从未真实导入 observation），`scan_evidence/identity_receipts/market_registry.sqlite` 均缺失；`scan.sqlite` 224KB（216 staging 在内）。
- [ ] 队列剩余：7a 信息日期/来源元数据补采集（决定7 选 a，L02 冻结前置）、Q06/Q07/Q10 partial 收尾（StockQA 报备制）、W06 跟进 F1/F2（generation 对齐门 + compat-first，先于 work-item 存储前必修）、W10–W16 其余卡（决定5 已授权）。

### Phase 63: W07 verified（三值规则引擎）+ owner 第二批答复

Status: W07_verified; owner_answers_2_batch_recorded; M2_critical_path_advanced

- [x] **W07 verified**（StockWiki 本地 `aa98848`）：2 新文件 `quick_scan_rules.py`（472 行）+ `tests/test_quick_scan_rules.py`（477 行），allowed_changes 吻合，零既有文件改动。
  - 语义：三值真值表逐行对齐 C03 `scoring.md` §四（all fail-first / any pass-first / not 交换）；**critical gate = 要求语义**（schema「此字段不满足时必须为fail」），门与复合体独立评估、`any`/均分不可绕过、unknown 门把 pass 降为 unknown；树内带 `critical_risk_gate:true` 的叶子**同样按门处理**并单列 `flagged_tree_gates`；SC-11 跨 metric/cohort/scope → `not_comparable` 拒绝排名；阈值改动仅重筛（上下文零改写、冻结 `rules_version`+`rules_sha256`+观察ID血统）。
  - 独立审查**三轮**（`ses_efdca8437ffejJRKG02OMvUp7F`）：首轮 changes_requested（F1 血统漏门字段、F2 description 类型、F3/F4 非有限数、F5/F6 未解析形态、F7 树内门惰性、F8 死分支、F9 测试卫生、F10 摘要漏血统）→ 全整改 → 二轮又抓出 A（F4 残留：5 条早退路径 NaN 仍进摘要）+ B（我修 F3 引入的 `float(10**400)` 溢出回归）→ 再整改（A=摘要前统一把非有限 actual 归 None；B=isfinite 只判 float + `_compare` 去 float() 转换走原生比较）→ 三轮 **approved**。两文件 SHA 记档（module `53afa69a…`、tests `a6f33e55…`）；`check_all` **842 passed**/0 skip/框架 0 错。
- [x] **owner 第二批答复入档（2026-10-03 会话）**：
  1. **G2b A/C/D/B 全部授权**——A=授权建实体导入路径、C=授权 AnalysisSubject 实现、D=授权 schema 加有效期列；（对应的**证据**仍需 owner 提供：发行人核验 HTTPS、perimeter 回执、HKEX/cninfo 日期、A/H 权威 bridge）。
  2. **补 CLI 入口**：W05 观察导入 + W13 维护准入两处命令行——超出两卡 allowed_changes，owner 明确"补"。
  3. **7a 顺序=顺其自然**：按关键路径 W07→W08→W09 推进，7a 仍作 L02 冻结前置排后。
  4. 叙事消费器三提交（`3c20d4d..ae0b3e3`）已向 owner 说明（独立分支 `codex/stockwiki-narrative-consumer-20261003`、基线=W04、非 107 卡计划内、58 测试绿、与我零冲突）——**处置待定**（保留/补审/回滚，等 owner 一句话）。
  5. **live 凭据+预算预先批准**（B01 30题对照 / L03 200家 / X10 真实全链）——执行前我仍按 live 规则先报成本与核验内容。
  6. **O01 扩容不急**（2000 家候选延后）。
- [ ] 队列（按序）：② 补 W05/W13 CLI（owner 已批）→ ① G2b A/C/D 实现路径（owner 已授权，证据仍待 owner）→ W08（W07 已解锁它）→ 7a。

### Phase 64: CLI 批次 + G2b 证据检索 + W08 verified

Status: CLI_approved_and_committed; G2b_evidence_hunt_archived; W08_verified; W09_unlocked

- [x] **W05/W13 CLI 批次 approved 并提交 `cc7fc6b`**（owner 决定"补"）。写前报告（F8 补记）：**改 4 文件** = `stockwiki/cli_parsers/quick_scan.py`（+107，注册 4 个子命令 + `run_observation_import` 薄胶水，SHA `9452753c…`）、`stockwiki/quick_scan_maintenance.py`（+112，3 个 maintenance handler + 元素级校验，SHA `e22de405…`）、`tests/test_quick_scan_maintenance.py`（+195，CLI e2e + 负向，SHA `d95c9a15…`）、`tests/test_quick_scan_observations.py`（+49，CLI e2e，SHA `f1776a6f…`）。**字面子命令名**：`observation-import`（W05，`--package`+`--release`）、`maintenance-nominate`、`maintenance-apply-auto`、`maintenance-report`（W13）。`quick_scan_import.py` 与 HEAD 字节一致（handler 加了又移到 parser 层守 <600）。
  - 审查两轮 approved（`ses_efd82e249ffeaqrw0zbiwxc7HM`）：首轮 F1/F2=畸形输入吐原始 traceback 退出码1（17 项实测探针）→ 整改为元素级/分值类型校验+universe 前置检查，F3–F7 同批修 → 二轮 **approved**（17 负向 + 17 原路径全 rc2/单行 JSON）；F10/F11（测试 socket bomb 覆盖、help 文案）随后收掉。`check_all` **849 passed**。
- [x] **G2b A/B/C/D 证据检索（决定"开 agent 找证据"）**：3 个只读 agent 并行，结论固化 `reviews/IQS-lane/G2b-evidence-hunt-2026-10-03.md`（IQS `5a7e996`）。**四类 0 READY**：A=强候选 Alphabet 双证券共用 SEC 10-K URL（但回执/实体存储不存在）、**B=A/H 硬缺失（151 对零共享键，`gshk` 推导 77% 准确不可用；美股 CIK READY）**、C=3 条真实 HTTPS 合并范围披露可作 evidence_ref（无 subject 生产者）、D=日期只在申报散文/docling 表格（security_master 零日期字段）。附 owner 必须提供的逐字段规格。**待 owner 签收清单已交付。**
- [x] **W08 verified**（StockWiki `9fa8a7e`）：2 新文件 `quick_scan_recovery.py`（319 行）+ `tests/test_quick_scan_recovery.py`（253 行），allowed_changes 吻合。
  - 语义：`recovery-watch-1` **逐字移植**（阈值全是代码字面量、无任何配置旋钮可改门槛；`policy_version` 回显 + 外来版本拒收 + `rules_version` 供漂移可见）；公司简表在 `quality_score=null` 时仍显示优势/低分/催化/资金摊薄/结构风险/缺口；三入口 `all_relevant`/`quality`/`recovery`，**永不按质量从大池删成员**；`reported_score` 永不晋升为已验证优势、`quality_gate_overridden`/`cycle_restart_claimed`/`pool_removal_performed` 恒 False。
  - **跨仓差分证据**：`%TEMP%/w08_diff3.py`（复用 IQS 测试类造合法 manifest + 缓存 `load_library`）**9613 例 / 0 不匹配**（policy_version/status/flags/weak/missing/strengths/gate_overridden/criteria 逐字段）；复审自建补测 **33 例 / 0 不匹配** → 合计 **9646 / 0**。复审一轮 **approved**（info×3：差分覆盖缺口已由其补测闭合、错误模式分歧系任务要求、`rules_version` 为有意新增键）。SHA `35046d29…`/`dea14e46…`；`check_all` **855 passed**。
- [ ] 依赖刷新：**W09 已解锁**（deps W07✓W08✓）→ W09 完成后 **L02 只剩自己的冻结条件**（7a 信息日期/来源元数据 + F1/F2 二选一）。队列：W09 → 7a → L02 冻结与执行。

### Phase 65: W09 verified（只读查询+冻结候选导出）→ M2 主链 W01–W09 齐

Status: W09_verified; M2_core_chain_complete; L02_pending_only_its_own_freeze

- [x] **W09 verified**（StockWiki 本地 `ac5a653`）：2 新文件 `quick_scan_query.py`（501 行）+ `tests/test_quick_scan_query.py`（457 行），allowed_changes 五接口齐全（`query_capabilities`/`coverage`/`search`/`get_profiles`/`export_candidate_set`+`reload_candidate_set`）。
  - 语义：**冻结快照稳定排序分页**（首查冻结 entity_id 顺序，翻页只切冻结窗，数据变化→`refresh_recommended` 而不重排；默认 50/硬顶 100，越界带错误码）；四视图（all_relevant/quality/recovery/pending）互不内含质量门；空态四分因 + `scope=query_only` + `market_wide_claim=False`（绝不宣称全市场无标的）；导出集哈希冻结（query/rules/observation_ids/hit_reasons/entity_ids），重载校验、画像更新不改历史集；行级只给短依据+安全 http(s)+口径标识，`facts_available=False` 全程；ID-04 轻画像可查且**零目录创建**（`export` 无 path 参数=纯内存）。
  - 独立审查两轮 approved（`ses_efce2a6e7ffe6BtkqH7TkOKHGv`）：首轮 F1（伪造 snapshot 骗出假 total）+ F2（filters/text 裸 AttributeError）两个 MEDIUM + F3–F6 四 LOW → 全整改（snapshot 元素级校验、入参形状校验、模型字段透出、reload 诚实标志、docstring 去掉不存在的写能力、QUERY-01 补 get_profiles/coverage + 新增 A+H 去重测试）→ 二轮 **approved**（62 项回归探针 0 失败；INFO=无态快照下"构造良好的伪造 snapshot"属设计固有，已接受）。SHA `271b1ba2…`/`4613839b…`；`check_all` **866 passed**/0 skip/框架 0 错。
- [x] **M2 主链 W01–W09 全部 verified**（W01/W02导入/W03/W04/W05/W06/W07/W08/W09 + W13）。
- [ ] 依赖刷新：**L02 现在只差自己的冻结条件** = 7a 信息日期/来源元数据补采集（决定7a 选 a）+ 范围说明 §5 F1/F2 二选一；G2 deps = L02+W09（W09✓）。W10（M3，已解锁）可并行。队列：① **7a**（StockQA 报备制，L02 硬前置）→ ② L02 冻结（live，先报成本）→ ③ L02 执行 → ④ G2 审查 → 另并行 W10。
- [ ] 仍等 owner：G2b A/B/C/D 签收清单（A/H 桥必须 owner 提供）、叙事三提交处置、1985/QAbyLLM 等已闭项外无新增。

### Phase 66: 决定7a 落地（信息日期+来源元数据补采集）→ L02 进入条件齐

- [x] **owner 第三批决定（2026-10-03 会话）**：
  1. **L02 分层口径 = B2**（授权 LLM 分类，按 W13 纪律走 StockQA 预算请求，caps+预算+owner 复核，产出仅算建议）。
  2. **L02 live 预算 = 同意**（原则批准；执行前仍按 live 规则报具体成本与 5 小时窗分片，此为纪律不豁免）。
  3. **G2b 四类证据 = 待 owner 对我的建议逐条确认**（建议随会话交付：美股 B 按 CIK 签、Alphabet 全 4 只签、A/H 桥选 b 签字映射表、D 走"过渡播种+官方表"两步、C 按 subject 配对且首个建议比亚迪、A/C 两个实现授权建议都建）。
  4. **叙事三提交 `3c20d4d..ae0b3e3` = 保留**（不补审不回滚；继续零接触）。
- [x] **B2 前置澄清已答 = B2a**（H 股候选并入本批 LLM 发现，产出 nomination→owner 复核入池；caps=primary≤230/HTTP≤460/搜索≤460，3 窗×≤80 顺序跑，撞限即停）。
- [x] **G2b 四类 = owner 按我的建议执行**：美股 B 按 CIK 签收；Alphabet A 全 4 只签；A/H 桥选 b（owner 签字映射表，**数据待 owner 提供**）；D 两步走（过渡播种我做 + 官方登记表待 owner）；C 按 subject 配对、首个建议比亚迪；**A（实体导入路径）与 C（AnalysisSubject 存储+回执读取器）两个实现授权=都建**。
- [x] **叙事三提交 = 保留**（不补审不回滚）。
- [x] **owner 通授（2026-10-03）**：「给你全部需要的授权」= **全部剩余卡/批次一次性授权**（含 W10 及后续 W11/W15、G2b A/C/D 实现与播种、B2a 执行、W06 跟进），条件不变=每批写前报告+独立审查+live 前成本声明。


Status: 7a_verified_and_pushed; G1_F1_F2_dispositions_satisfied; L02_entry_conditions_met

- [x] **7a verified 并推送 StockQA `5fdcc2c`**（18 个 pre-commit 钩子全过：black/isort/mypy/pylint≥9/detect-secrets/bandit/pip-audit/pytest-unit）。
  - 写前报告六文件+一新测试（报备制）：`base_llm_provider`（prompt 加 `information_as_of` 字段+第5条规则"所引事实之日、非今天、拿不准给 null、绝不猜"）、`llm_response_parser`（`ParsedLLMAnswer.information_as_of` + `information_date()` 只认真实日历日、坏日期→null+警告且**不丢答案**）、`llm_provider`/`async_llm_provider` 双胞胎 metadata 透传、`llm_client`（`_extract_sources` 采集 url+title+published_date，**四处回执点**接线：Responses action.sources/minimax 注释合并/Anthropic tool_result/mimo url_citation；`source_urls` 逐字节兼容——5000 输入属性测试 0 差异）、`models` 信封**去掉硬编码 None**（`information_as_of` 走校验、`published_date` = 回执里恰一个日历有效日期否则 null）。
  - 独立审查两轮 approved（`ses_efc9e2358ffethLtnNyW0dr37N`）：首轮 10 项全过 + 2 LOW（信封只查正则放行 `2026-13-45`、聚合日期不查格式放行 `March 2026`）+ 1 INFO（格式修复 prompt 漏字段）→ 全整改（抽 `_real_iso_date` 统一"正则+真实日历日"、修复 prompt 列字段）+ 2 条覆盖测试 → 二轮 31/31 探针全过 **approved**，9 文件 SHA 记档。
  - 测试：新文件 12 条；钩子式 `tests/unit/ -p no:base_url` **757 passed**；全量 **848 passed/0 failed/4 skipped/18 errors**——那 18 个 errors 全是 `pytest_base_url` ScopeMismatch，**经 stash 在干净 HEAD 复现=既有环境问题**（仓库钩子本身用 `-p no:base_url` 所以钩子里不出现）。
  - 既有精确断言更新3处（`web_search_calls == [...]` 新增 `sources` 键，值与夹具逐字段核对）+ 1 处潜伏（当时因 base_url error 没跑到，也一并修）。
- [x] **G1 F1/F2 处置条件满足**：F1=结构化 `information_as_of` 已采集+校验（决定7a 选 a）；F2=来源标题/发布日期已随回执采集（`sources[]`，per-source 原样留痕）。**L02 的范围说明 §5 两条进入条件双双落地。**
- [ ] **L02 现状**：deps W07/W08/W09 全 verified ✓、F1/F2 条件 ✓ → **只剩自身冻结**（样本分层、题面/锚点版本、caps、止损/回滚规则写入 `reviews/` 冻结文件并钉版）+ live 成本声明（按 MiniMax 5 小时窗口分片派发）。
- [ ] 队列：① **L02 冻结**（先写前报告+冻结文件）→ ② L02 执行（live，先报成本）→ ③ G2 审查；并行 W10（已解锁，StockWiki）。等 owner 不变（G2b 签收清单、A/H 桥、叙事三提交）。

### Phase 67: W10 verified（导入ACK+执行状态只读投影）+ owner 第三批/通授入档

Status: W10_verified; third_batch_recorded; blanket_authorization_recorded; B2a_authorized

- [x] **W10 verified**（StockWiki 本地 `3a3d061`）：2 新文件 `quick_scan_delivery.py`（283 行）+ `tests/test_quick_scan_delivery.py`（340 行），allowed_changes 吻合、W05 ledger 零改动。
  - 语义：`ack_status` 只读回执（错误回执显式 `error_receipt=True`，永不伪装 delivered）；**5 状态合法转移守卫**（50 对全探：acked/delivered 必须有 ACK、delivered 只能从 acked、非法边全拒、幂等 no-op 不伪造状态）；`validate_ack` 必须匹配精确 item+hash；`reconcile_delivery` = 无调用方 ACK 时**先消费台账精确回执**推进（JOB-07）、无回执保持 unknown、**错 ACK 拒绝并保持状态+具名错误码**（JOB-08，不崩溃）；`project_runtime_status` 显式区分 `import_attempts` vs `distinct_companies`（执行次数≠公司数）、`facts_available=False`、零 LLM/网络；读路径=公开 `database_path`+`PRAGMA query_only`+表存在性检查（空库文件也出 `store_not_migrated` 而非裸 traceback）。
  - 测试夹具**全部走真实 W05 `apply_decisions` 事务**（非手插 SQL 非 mock ledger），socket 炸弹，闭环=accepted→回执→投影→重复ACK幂等。
  - 独立审查两轮 approved（首轮会话连返两次空 → 换新会话 `ses_efbc83bd5ffev8fZFRwck5S5fT`；low=空库文件漏裸错误 + 3 info → 全整改含新探针）→ 二轮 **approved**，2 文件 SHA 记档（`27208402…`/`83590abb…`）；`check_all` **871 passed**/0 skip/框架 0 错。
- [x] **owner 第三批**：L02 分层=B2、L02 live 预算=同意（原则）、G2b=按我建议执行、叙事=保留 → 已记于 Phase 66 节下。
- [x] **owner 通授**：「给你全部需要的授权」= 全部剩余卡/批次一次性授权（条件不变：写前报告+独立审查+live 成本声明）。
- [x] **B2a 获批**：216 家分类 + H 股提名发现（LLM 建议性质、复核后才入池）；caps=primary≤230/HTTP≤460/搜索≤460、3 窗×≤80 顺序、撞限即停。
- [ ] 依赖刷新：**W11 已解锁**（deps W09✓W10✓）。队列：① **B2a 执行**（live，先冻结题面+回执核验清单）→ ② G2b A 类实体导入路径 + C 类 AnalysisSubject 存储/回执读取器（通授已给）→ ③ D 过渡播种 → ④ W11 → ⑤ W06 跟进 F1/F2。等 owner 数据：A/H 桥映射表、D 官方登记表、B2a/H提名复核。

### Phase 68: B2a 执行完毕（216 分类 + H 股发现）

- [x] **owner 指示（G2b 收尾两按推荐）**：① **A/H 先跳过**——美股 B（CIK）与 Alphabet A（全4只）按既有批准先行落地，A/H 桥挂起等 owner 交映射表；② **D 走过渡播种**——我先抽申报散文/docling 日期成结构化行，官方登记表后补，**D 卡在官方表到位前保持 open**。

Status: B2a_complete; within_final_caps; zero_pool_writes; owner_signoff_package_ready

- [x] **冻结+两次修正案均经 owner 批准**：初版（caps 230/460/460）→ 修正案A（`可以`→280/560/600，实测每有效家 2.1 请求后我主动报数修正）→ **终批（`可以`→420/840/840）**。题面 v1（嵌套JSON，首过率67%）→ v2（外层结构+示例，repair=1 救回23）→ **v3（标签纯文本行）**，全部记入 `L02-B2a-freeze-2026-10-03.json` 修正案。
- [x] **216/216 有效分类**（102 JSON + 114 标签文本口径）；**H 股发现 11/11** → **3 个提名**（万科→02202、中信建投×2→06066，均带交易所/官网证据 URL）+7 个明确无 +1 重试后完成。**全程 0 池写入、0 成员创建、未删任何记录**（所有被拒/被覆盖输出均隔离保留于 `rejected_*/` 目录）。
- [x] **预算终账（诚实含修正）**：文件实测 395 请求/750 搜索 → **+11 请求/+21 搜索遗失回执修正（估算，批次均值）→ 真实 406/420 请求、771/840 搜索，均在终批 caps 内**；账单以 owner MiniMax 控制台为准（决定3）。
- [x] **事故与恢复（记档）**：runner 初版输出路径未分相 → HK 阶段覆盖了 11 份分类回执。恢复=路径改为 `out/<phase>/`、被覆盖 11 家**重跑**（11/11 成功）、预算+11 修正写入 run-log、覆盖输出全部保留于 `out/hk/`。教训入 findings。
- [x] **交付物**：`pilot_runs/b2a_2026-10-03/` = `stratification-final.md/json`（216 家行业/类型/生命周期/盈利四维分层表）、`hk-discovery-results.json`（11 家逐条+证据）、`budget-final.json`（终账）、`run-log.json`（逐次执行+rejected 隔离台账）、冻结文件两修正案（IQS reviews/）。
- [x] **owner 已一次性签收 B2a**（2026-10-04 指令「B2a签收」）：`stratification-final.md/json`（216 家四维分层）+ `hk-discovery-results.json`（3 提名：万科02202、中信建投×2→06066）获批 → **L02 冻结可引用这些分层**；提名仍按"复核前不入池"执行（签收=对分层与提名清单的确认，非建员授权）。
- [ ] 队列：① owner 签收 B2a → ② G2b A 类实体导入路径 + C 类 AnalysisSubject 实现（通授已给）→ ③ L02 冻结（引用分层+7a 条件已齐）→ ④ W11（已解锁）。

### Phase 69: G2b-A 实体导入路径落地 + Alphabet 首个真实样本

Status: G2bA_batch_approved_committed; alphabet_sample_imported; owner_dispositions_recorded

- [x] **G2b-A 批次两轮审查 approved 并提交**（StockWiki `f701909`）：3 文件（NEW `identity_import.py` 389 行、MOD `cli_parsers/quick_scan.py` +12 行注册、NEW `tests/...` 381 行 11 测试）。
  - 语义：**两阶段诚实导入**（实体 save → 回执 record，跨两库不假装原子；回执阶段失败=显式 `entity_saved_receipt_failed`+可重试）；写前门挡全部 payload 形状/证明规则（kind↔state 配对、UTC recorded_at 完整解析、verified 必带回执、HTTPS evidence、coverage/ID 一致）；**派生≠证明**（coverage/属性映射仅在 owner 未提供时从 store 投影注入，owner 提供的值原样送校验、错了就报错不改写）；幂等重放同回执同记录。
  - 首轮 3 LOW/INFO（kind/state 绕过写前门、UnicodeDecodeError 漏出 CLI、docstring 夸大）→ 全整改+4 新测试 → 二轮 **approved**，3 文件 SHA 记档（module `832b391d…`、tests `b3fe4941…`、parser `1f5efb28…`）；`check_all` 883 passed。
- [x] **owner 两项决定入档（Phase 68 节）**：A/H 先跳过、D 走过渡播种。
- [x] **Alphabet 首个真实样本入库成功**（G2b A 类 + 美股 B 类实物）：
  - 4 证券（GOOG/GOOGL=ordinary、GOOGM/GOOGN=preferred）、MIC=XNAS（iso10383 fixture 权威）、binding×4、`identity_state=verified`、回执 `IVR_663efa0137144ccba0e6c88781da6752`（coverage 4/4、same_legal_issuer=true、evidence_ref=批准的 SEC 10-K、decision_ref 持久化、adr_ratios={} 诚实为空）。
  - 执行链：首次因 `IVR_` id 含连字符被**写前门拒绝（exit2 零写入）**→ 修正 id 字符集 → exit0 `entity_saved_receipt_recorded` → 库内只读复验（1 entity/4 证券/4 binding/1 回执）→ **幂等重放同回执、计数不变**。
  - 证据固化 `reviews/IQS-lane/G2b-alphabet-sample-2026-10-04.md`（含 payload/receipt 路径、逐项复验、边界注记：share_class/ordinary_security_ref 诚实置空不编造）。
  - **G2b 效果**：A 类（美股）与 B 类（美股多挂牌）从 0 READY → 有可签收实物；C/D 仍待（C=AnalysisSubject 实现，D=过渡播种+官方表）；卡保持 open。
- [ ] 队列：① **D 过渡播种**（owner 已批两步走的第一步：申报散文/docling 日期抽结构化行）→ ② G2b C 类 AnalysisSubject 存储+回执读取器（通授已给）→ ③ L02 冻结（B2a 分层已签收可用）→ ④ W11。

### Phase 70: G2b D 类过渡播种（第一步落地，D 保持 open）

Status: D_transitional_seeding_done; D_card_still_open_pending_official_register

- [x] **owner 决定「D 两步走」第①步执行完毕**：可复跑提取器 `reviews/IQS-lane/G2b-D-seed-extract.py` + 播种数据 `G2b-D-transitional-seeding-2026-10-04.json`（**59 行**：listed58/delisted1，22 文档）+ 报告 `G2b-D-transitional-seeding-report-2026-10-04.md`。
  - 三重负门过滤（法律实体噪音17+、**财政报告噪音17**、无上市动词）；**归属诚实**：窗口含实体名才填 entity_names（实测仅2条 sentence_confirmed，其余 document_level_unverified——绝不把文档主体强挂日期）；每行 `confidence=transitional_pattern_unreviewed`、`closes_category_D=false`。
  - 真例：金山雲「上市日期」=2022-12-30（定义式）、贝壳纳斯达克2020-05-08、**英方股份 2017-12 新三板摘牌**（全库唯一退市）。
  - **关闭 D 唯一路径不变**：owner 交交易所官方登记（字段规格在 evidence-hunt §D），到货后与种子交叉核对再签。
- [ ] 队列：① **G2b C 类 AnalysisSubject 存储+回执读取器**（通授已给，最后一个 G2b 实现项）→ ② L02 冻结（分层已签收、7a 条件已齐）→ ③ W11 → ④ W06 跟进 F1/F2 → ⑤ 7a 补采已完（不再排队）。等 owner：A/H 桥映射表、D 官方登记表、L02 live 成本（冻结后报）、MiniMax 对账、叙事处置已定保留。

### Phase 71: G2b-C AnalysisSubject 批次 approved + C 类草案待签

Status: G2bC_batch_approved_committed; C_sample_draft_dry_run_passed; awaiting_owner_signoff

- [x] **G2b-C 批次四轮审查 approved 并提交**（StockWiki `b25a34e`）：3 文件（NEW `quick_scan_analysis.py` 579 行、MOD `cli_parsers/quick_scan.py` +注册、NEW `tests/...` 10 测试）。
  - 语义：Subject+回执**同库单事务**（无实体导入的两阶段问题）；`perimeter_sha256`/snapshot/key **逐字节移植 IQS `contract_validation` 并用离线权威向量钉死**（单成员 `2aa1d799…`、双成员 `a35118d8…`，IQS 与 StockWiki 双侧复算一致）；schema 条件全对齐（consolidated **anchor 必须 null**+coverage 三选、provisional 锚须属本发行人派生挂牌、standalone null）；回执换字节=receipt_conflict 不静默；成员窗口按**完整 UTC 半开区间**与 IQS 9/9 一致；不可哈希枚举/空 scope_as_of 全部具名拒绝（CLI exit2 零 traceback）；append-only（无 UPDATE/DELETE）；IQS `_require_trusted_reporting_perimeter` 交叉验证通过。
  - 审查四轮：R1 F1(anchor 条件写反,HIGH)+F2–F9 → 全整改；R2 N1(日期截断) → 全精度半开区间；R3 N2(`scope_as_of: null` 裸崩) → 显式拒绝 → **R4 approved**。SHA `305b06ca…`/`5b6bbe45…`/`f09fb160…`；`check_all` **894 passed**。
- [x] **C 类样例草案 + 只读干跑（零写入）**：Alphabet consolidated subject（primary=真实 verified 实体、anchor=null、coverage=not_enumerated 诚实不枚举子公司、evidence=批准的 SEC10-K、scope_as_of=FY2025 期末）→ `validate_subject`/`validate_receipt` 对真实库干跑 **PASS**（`perimeter_sha256=bf0bdda6…`）；payload 存 `StockQAbyLLM/pilot_runs/g2b_c_alphabet_2026-10-04/alphabet_subject_draft.json`，provenance 标 `DRAFT — awaiting owner sign-off`。
- [ ] **等 owner 签收 C 草案**（成员清单=仅 primary 一条 + not_enumerated 覆盖口径）→ 签收后执行真实 `analysis-subject-import` → G2b C 类有实物。
- [ ] 队列：① owner 签 C 草案 → ② 真实导入+证据文件 → ③ **L02 冻结**（分层已签收、7a 已齐、deps 全绿）→ ④ W11（已解锁）→ ⑤ W06 跟进 F1/F2。等 owner 其余：A/H 桥表、D 官方表、L02 live 成本（冻结后报）、MiniMax 对账。

### Phase 72: C 类签收入库 + 两张证据表取回（owner 授权 LLM agent 联网取表）

Status: G2bC_sample_imported; AH_bridge_draft_ready; D_register_draft_ready; both_awaiting_owner_signoff

- [x] **owner 三答复执行**：①C 草案签收 → 真实导入成功；②L02 直接跑（冻结成本在 2600/5200 内不再等）；③**授权 LLM agent 联网取 A/H 与 D 两张表**（首次突破"只读离线"惯例，owner 明示）。
- [x] **G2b C 类真实入库**：`analysis-subject-import` exit0 `write_status=imported` → `analysis_subjects.sqlite` 1 subject（consolidated/not_enumerated/anchor=null/hash=`bf0bdda6…`）+ 1 回执（verified/SEC 10-K/`PRC_47da94…`）+ 幂等重放 `unchanged`。decision_ref=`owner-2026-10-04-g2b-c-alphabet-signoff`；provenance 块被 F8 校验正确拒绝后移至 sidecar 文件。**G2b A/B(US)/C 三类均有真实实物**；D 等签收、A/H 等签收。
- [x] **A/H 桥草稿表取回**（agent `ses_ef8525271ffe…`，联网）：`G2b-AH-bridge-draft-2026-10-04.json` — **122 行全 high 置信**、逐行 cninfo A股年报双代码披露（HTTPS+sha256+UTC 溯源 122/122 完整）、优先清单覆盖 12/13、全宇宙 122/151；HKEX 前缀 API 交叉核对 H 代码 122/122 匹配；**4 处我方 brief 的 H 代码被证据纠正**（太保01601→02601、中免06881→01880、紫金01899→02899、药明02269→02359）；002142 宁波银行 H 股证伪（06882=東瀛遊）。`issuer_id` 122/122 `not_found_in_sources`（披露里无 LEI，单腿 org_id/hkex_stock_id 不可用）→ **待 owner 补 issuer_id 或按现态签**；30 对 dual_code 未确认。
- [x] **D 官方登记草稿表取回**（agent `ses_ef8522388ffe…`，联网）：`G2b-D-official-register-draft-2026-10-04.json`(+csv) — **217 行**（CN210/US5/HK2；listed215+delisted2）、**207 结构化+10 官方散文**、**池覆盖 213/216=98.61%**、全行 HTTPS+sha256+UTC、来源=SSE/SZSE 列表+cninfo PDF+SEC filings+HKEXnews；对59 条过渡种子交叉核对：可绑定的 5 条中3 一致（60%），**2 条种子假阳性被抓**（002747=H股申请受理日、000547=英方股份摘牌串台）；3 个缺口（872808 北交所 MIC、GENB、NVO 首日）。`closes_g2b_d=false` 待签。
- [ ] **等 owner 签收两表**：A/H 表要定 issuer_id 来源（补 LEI 或按 not_found 签）+ 裁 30 未确认对 + 接受4处纠偏；D 表要抽样复核 sha + 裁3缺口 + 接受2条 HK "expected to commence" 注记。签后各自导入（VerifiedIssuerBridge / 官方登记→替换过渡种子地位）。
- [ ] 队列：① **L02 冻结**（owner 已批"2600/5200 内直接跑"）→ ② L02 执行 → ③ W11 → ④ W06 跟进。两表签收与 G2b 关卡并行等 owner。

### Phase 73: 两表签收（六项决定）→ D 类证据闭合

Status: both_tables_signed; D_evidence_closed; AH_evidence_signed_bridge_import_pending

- [x] **owner 六项决定执行完毕**：
  1. A/H issuer_id = **b 按现态签**（122/122 保持 null + `not_found_in_sources`，后补 LEI 等双边 id）
  2. 30 对 `dual_code_not_confirmed` = **剔除**（核验确认本就未入 rows，gaps 清单留档并标 `owner_disposition=excluded_from_rows`）
  3. 4 处 H 代码纠偏 + 002142 证伪 = **接受**（表内已按源纠正：02601/01880/02899/02359；002142 不在表内，断言加固）
  4. D 表 sha = **信任**（agent 重取重哈希审计采信）
  5. 三个缺口 = **排除北交所**（872808/XBSE 记为 owner 排除）；GENB/NVO 记为未覆盖缺口（不编造首日）
  6. 2 条 HK "expected to commence" 注记 = **接受**（行保留+reason 注记）
- [x] 两表写入 `decision_ref` + `owner_signoff` 块 + `status=SIGNED`：A/H 122 行（`closes_g2b_ah_evidence=true`）、D 217 行（**`closes_g2b_d=true`**）。
- [x] **G2b 类别现状**：A(US)✅ 实物、B(US)✅ 实物、**D ✅ 签收闭合**（官方登记表取代过渡种子地位）、C ✅ 实物；**A/H 证据已签但实物待建**（`quick_scan_issuer_bridge` 表+导入+平安 A/H 实体——通授覆盖，下一施工项）。
- [ ] 队列：① **L02 冻结**（owner 已批 2600/5200 内直接跑——表格已签不再阻塞）→ ② L02 执行 → ③ A/H bridge 导入批次（G2b 最后实物）→ ④ W11 → ⑤ W06 跟进。等 owner：MiniMax 对账（B2a 406/771）、叙事=保留（已定）。

### Phase 78: Q06 收尾批次（公共 CLI 绑定真实 work item + issuer 去重）

Status: card_confirmed_and_recon_done; paused_by_owner_before_implementation

- [x] 施工卡转正：`reviews/IQS-lane/Q06-closeout-card-draft-2026-10-05.md` —— **owner round-41 确认**（「Q06 卡确认，两取舍签认」，连带关闭 W06 case② 豁免与 F2 resume-first 两处取舍签认）。开工前置全绿：G2 r2 verified + C04✓。
- [x] 开工侦察：绑定点锁定 `src/runners/llm_runner.py:479-491` seam（QAEngine 构造与 `bind_quick_scan_budget` 上下文之间，budget_store 已在 :398 创建）；QAEngine 题循环 = `process_questions`（qa_engine.py L131-171，逐题 process_question、失败→error 结果继续）；Store 生命周期 API 面清点：`create_or_attach`(L1419)/`claim`(L1538)/`prepare_attempt`(L1562)/`record_attempt_outcome`(L1730)/`recover_expired`(L1867)/`note_late_receipt`(L1920)——钩子取向：QAEngine 可选 per-question 生命周期（零注入行为逐字节不变），runner 注入 store 绑定。
- [x] **恢复点已执行（2026-10-05 晚，目标恢复）**：QAEngine 题循环（L131-171，逐题 process_question→QAResult，失败→error 结果继续）与 Store API 面全部读完——`create_or_attach`（九元逻辑键原子建/挂、frozen 字段防漂移）、`claim(work_item_id, lease_seconds)→Lease|None`（仅 pending 可领、竞态 fenced）、`prepare_attempt`/`record_attempt_outcome`（attempt 记录）、`recover_expired`/`note_late_receipt`（过期恢复/迟到拒覆）。Q06 case_ids=JOB-01/02/PAR-12/JOB-10/11，不变量 I02/I12/I54。
- [x] **RED→GREEN（2026-10-05 深夜）**：`tests/unit/test_q06_work_binding.py` 11 测试全绿（R1 零注入等价/R2 claim→response_available 终态→幂等重放/R3 双领拒绝/R4 租约过期+recover+迟到 fenced/R5 issuer 去重 vs listing 分立/R6 身份载荷映射）；实现 = qa_engine 可选 `work_item_lifecycle`（claim 拒绝→error 结果不派发；success→after；失败→after_failed）+ llm_runner `QuickScanWorkLifecycle` 类（store 生命周期 + 题面哈希代理 prompt_sha256，已在类 docstring 明示）+ `--identity-snapshot` 待接线。回归 102 passed（qa_engine/llm_runner/basic_runner/work_store）、ruff/black 净。
- [x] **CLI 接线（选项 1 生产激活路径）**：`load_identity_snapshot`（W04 导出包→create_or_attach 身份字段映射 + 快照文件 sha256）+ `run(identity_snapshot=)` 校验（需 --require-search）→ `_run_single_company` 生命周期构建（budget_store 或独立 work store）→ QAEngine 注入；回归 108 passed（Q06 11 + qa_engine/llm_runner/basic_runner/work_store 97）、ruff 净。全量门后台跑。
- [x] **CLI 接线 + 四重门（最终字节）**：`--identity-snapshot`（main_with_llm + run() 校验/线程 + `load_identity_snapshot` W04 映射）+ entity_id 收窄 → black 0 / ruff 0 / mypy 0（3 源文件）/ **全量 872 passed·4 skipped·0 errors**（`-p no:base_url` 标准旗标——首跑 18 插件 ScopeMismatch 系命令缺旗标非回归）/ 定向 6/6。
- [x] **审查 r1 = needs_revision（3×P0）→ 整改批完成（2026-10-05 round-52/53）**：P0-1 `routing_fingerprint_for`（题面文本→64-hex，json.dumps(Question) 崩溃修复）+ loader 覆盖；P0-2 store 正则放宽（**owner round-51 签认**，ENT_ 含连字符）+ rf- 前缀去除 + `--entity-id` 互校（P1-2）；P0-3 `mark_send_intent` 前置（transport 语义）+ 诚实 `unknown` 终态（禁臆造 200/回执）→ work_item=uncertain 清租约不可再领（JOB-10 不重派发）+ **R4 重写为双恢复路径**（未发送→pending；已发送→uncertain 永不重派+迟到 fenced）。
- [x] **额外发现（审查者未列）**：request_cache_key 缺 work_item_id → 跨 scope 键冲突被 store 全局检查拒绝——按 transport 同一公式（work_item_id+route+provider+model+prompt_sha）修正。
- [x] **P1/P2/LOW 收尾**：R6 真 CLI 端到端（argparse→run 线程接线，monkeypatch 无 LLM 调用）+ scope/scope_id 参数与绑定路径测试（JOB-11）+ provisional 多 ref loader fail-fast（verified 放行）+ source_binding_version=1 docstring 披露 + 拒绝计数摘要（P2-2，refused 不计入成功）+ docstring 对齐（prompt_sha 公式/run_id·scan_id 派生/before 不抛出/uncertain 语义）。测试 14/14。
- [x] **r2 = approved（2026-10-05）**：门独立复跑全对（880/0、14 定向、R3×10 稳定、black/ruff/mypy 0、store diff=正则 1 行+注释 3 行），三 P0 修法逐项对上 §7 建议，审查者自建 RUN1/RUN2/RUN3 真 CLI 端到端复证（1 次 HTTP 落库、重跑 0 重复派发、entity 不符 fail-fast）。
- [x] **StockQA 隔离提交 `5b0d024`**（恰 5 文件，pre-commit 全钩子链通过：black/isort/mypy/pylint/detect-secrets/bandit/pip-audit/pytest-unit）。
- [x] **残余 P2-3/P2-4 关闭（owner round-54 选项 b + r2 建议的入口 e2e）**：卡 R6 措辞修订（回执含 work item 关联 → **Q10 outbox 小卡**，依据 r2 消费分析：IQS adapter 不读、linkage 属 observation-v2/Q10，当前无契约消费者；本批不碰 models.py）；`_invoke` 加 `extra_argv` 扩展 + `test_e2e_public_cli_identity_snapshot_glue_no_redispatch`（RUN1 1 次 HTTP+work item 落库非 pending；RUN2 拒绝且 0 HTTP = JOB-10 回归固化）盖住 P2-4 胶水层与 R6 入口。定向 63 passed、全量 881 passed/0 errors、black/ruff/mypy 0。
- [x] **Q06 = verified；W11 解锁**（2026-10-05 round-54）：StockQA 两笔提交 `5b0d024`（主批 5 文件）+ `6416f57`（残余关闭 2 测试文件，全钩子链过）；IQS `0534975`+`f27918c`；门（终字节）全量 **881 passed/4 skipped/0 errors**、mypy 0、ruff 0、black 0、定向 63 passed。下一批 = **W11 定向补扫接线**（deps 全满足：W06✓W09✓W10✓Q06✓）。
- 禁改提醒：transport 协议、Q09 预算上下文、Q07 checkpoint（下一卡）、frozen L02 资产、叙事三提交。

### Phase 77: G2b A/H bridge 导入批次（G2b 最后实物）

Status: COMPLETE — committed_StockWiki_01a4289; two_round_review_approved

- [x] 施工卡：`reviews/IQS-lane/G2b-AH-bridge-import-card-2026-10-05.md`（owner 通授覆盖；5 文件范围+TDD 矩阵+零副作用边界）。
- [x] schema v5 + `quick_scan_issuer_bridge.py` + CLI 双子命令 + 11 测试 RED→GREEN；全量门 check_all 首轮 907 passed。
- [x] **真实导入被数据缺陷 fail-closed 拦下**（签收表上药双行同 sha 异 pair）→ 联网查证现代码 601607（SSE/HKEX/cninfo）→ owner round-38 方案A。
- [x] **方案A 修正**：原件备份（FA9CE0B9…）→ 删 (CN-A:600849,02607)、行派生 stats 全重算（121/80.1）、owner_signoff 追加（修正版 55B79EB9…，已提交 2e96e61）。
- [x] **真实导入**：121 行 exit0（batch AHB_55b79eb9…）、replay 0/121 幂等、DB 全核验（601607 恰1/600849 零/216 候选/零副作用）。
- [x] 独立审查 **approved**（P0/P1=0；根因独立证实=原件恰1个重复 sha 3b556e17…；DB↔源 0 差异；check_all 917）。
- [x] **整改批**（P2×3+LOW 全处置，含 handoff 12→17 在册、LOW-1 接受留档理由）→ 复跑 17/17 + check_all ALL CHECKS PASSED → 卡片整改节入档。
- [x] 跟进复审（原审查者）**终裁 approved**（独立全量 check_all 923=917+6 自洽、真实库只读 report --source diff_zero、范围恰 6 文件、LOW-1 不改理由确认、handoff 17 路径与 Phase 77 引用确认）→ 测试头 INFO-4 顺手修正 → **StockWiki 隔离提交 `01a4289`**（6 文件：本批 5 + handoff 在册 12→17）。**本 Phase 关闭；G2b A/H 桥实物收口（G2b 最后实物）。**

### Phase 74: L02 冻结实装 + 冒烟 + 窗口1（含中断与恢复，进行中交接）

Status: L02_frozen_smoke_passed_window1_done; execution_in_progress; DO_NOT_INTERRUPT_LONG_WINDOWS

- [x] **L02 冻结已钉版推送**（IQS `a27f42b`）：60 家分层样本（CN51/US7/HK2）+ 20 家 repeat 子集 + 真实题库题面/锚点版本 + caps=primary 2600 / searches 5200（owner 批准上限内直接跑，不再等成本报批）。
- [x] **Runner 冻结并就位**：`StockQAbyLLM/pilot_runs/l02_2026-10-04/runner.py`；冻结配置副本 `llm_apis.json`（MiniMax-M3 + `/v1/responses` + format_repair_budget=1）；`companies.json` + 按分层预生成的 `questions_*.json` 题库 + `repeat_subset.json`。
- [x] **冒烟完成并修复假告警**：上峰水泥（31答）、视觉中国（29答）端到端通过；run-log 中视觉中国手动补跑记录已修正入档。冒烟消耗 primary 64。
- [x] **窗口1 重跑完成**（此前被会话消息两次打断，不损失产出——runner resume 跳过已有输出）：12 家公司、计划 354 题，run-log 逐家记录 statuses/search_status/response_id/question_attempts/耗时；**预算累计 636/2600 primary、651/5200 searches**（caps_ok=true）；输出 `out/primary/` 21 份；止损原因=window_question_budget（正常窗口切片）。
- [x] **诚实注记**：部分公司 exit=1（上峰水泥/视觉中国本题面含 unknown/insufficient_evidence 答案，按 Q01—Q03 契约 CLI 对含失败答案的题返回非零）；京东方 exit=0。**exit 非 0 ≠ 未产出**——均有完整输出文件；最终判定以 L02 校准报告对 unknown/修复预算的统计为准，执行期不逐家干预。
- [ ] **进行中（关键交接）**：L02 primary 共 60 家 + repeat 20 家；窗口1 已完成 12 家。**继续方式=循环重跑同一命令，runner 自动跳过已完成公司**：
  `cd C:\Users\郑曾波\Projects\StockQAbyLLM\pilot_runs\l02_2026-10-04`
  `python -X utf8 runner.py --phase primary --max-questions 325 --provider minimax`
  每窗口约 50 分钟；primary 跑完再 `--phase repeat`；预计还剩约 8 个窗口（半天到一天）。**恢复会话第一动作=发起下一窗口，并声明"长任务请勿发消息打断"。**
- [ ] **水位检查点（每窗口后）**：读 `run-log.json` 尾部 + 预算（caps 2600/5200 触顶前主动报数），progress.md 记一行。
- [ ] **全部跑完后**：出 L02 校准报告（LIVE-03/04 判定：题面成功率、unknown 率、修复预算命中、每题成本）→ 独立审查 → G2 门审查 → Phase 75+ PWF。
- [ ] **不要动**：并行叙事道三提交 `3c20d4d..ae0b3e3`（owner 已裁保留，零接触）；B2a 资产（已签收批次，不可覆盖）。
- [ ] 等 owner（不阻塞 L02）：MiniMax 对账（B2a 406/771；L02 跑完同样以控制台为准）。

### Phase 75: L02 试点执行（MiMo 链路逐题基线）与校准报告

Status: report_chain_complete (r2 approved); G2_verified_for_local_gate_scope; M2_gate_dimension_closed; Q06_unlocked

- [x] **中断恢复与根因闭环**：会话切换丢失 key（MINIMAX_API_KEY 在用户级，子进程须显式注入）+ workspace 沙箱拒绝外仓写（已切 danger-full-access）+ MiniMax 5h 窗耗尽（chat 429/responses 500 实锤）→ owner 决策切 MiMo；两次失败窗口的 27 份废产出隔离归档（rejected_error_2026-10-05/，含 manifest 与 run-log 备份），done-set 修复。
- [x] **amendment-3/4 入档**：provider 切 mimo-v2.6-flash（搜索白名单内，Q02 验证型号）；owner ≤1h 约束 → 样本 60→6 分层（原 60/20 签名归档 companies_60_full_signed.json / repeat_subset_20_signed.json）、repeat 顺延、编排并发 ≤6 不改变提问方法；方法论对照归 B01（Q09/Q10/PAR-04 前置），L02 数据即 B01 的 MiMo 逐题基线区组。
- [x] **执行完成**：探针（002122，29 题 0 error）+ 主批 5 家（真 UTC 21:31:46Z–22:11:58Z，40 分钟；原稿"45 分钟"系本地钟口径，G2-F3 更正）+ 000738 重跑成功（首跑 MiniMax 窗口1 失败、MiMo 批被 stale done 跳过——r1-F5 口径，原稿"第三跑"隐含两次失败已更正）；全量 6 家 182 题：scored 111 (61.0%)、insufficient 60、unknown 11、error 0；搜索执行 88.5%；来源 1,096 条；预算 940/2600、897/5200（caps 内）；零池写入。
- [x] **校准报告回填**：`docs/implementation/reviews/L02/L02-calibration-report-2026-10-05.md`（LIVE-03 分层明细、LIVE-04 分母完整性=缩减在开跑前冻结、REV-06 等六项 G2 case 映射、000738 单次失败+stale 跳过与 ≈29 请求账本缺口披露——r1-F5 修正后口径）。
- [x] **owner 费用发现入档**：MiMo 搜索插件费 > 模型费（本批搜索 218=1.20 次/题 + 探针 28 = 246；请求 239+36=275——G2/r1-F7 口径，原稿"~246 搜索/182 题"混入探针）→ B01 评比必须综合搜索费用（报告 §2.5 + findings.md + progress.md 三处）。
- [x] 独立审查闭环：r1 **needs_revision**（F1 口径混杂/F2 探针门未入冻结 两个 P2 + 5 LOW + 4 INFO；数字与分母本身复算全对）→ 全项修订（6 家口径 239/57/46.9s、amendment-5 补录、UTC 时间戳 local=UTC+1 纠正、summarize provider 过滤、000738 单次失败叙事修正）→ **r2 approved**（五核查点含实跑复现命令）。审查报告 `reviews/L02/independent-review-2026-10-05.md`；证据 `L02-summary-6mimo-2026-10-05.json`。
- [x] **G2 审查包组装**（`reviews/G2/G2-review-packet-2026-10-05.md`：依赖证据表、逐 case 图、可用比较组清单草案、r2 INFO 补注、诚实边界）+ G2 独立审查完成：**needs_revision**——实质检查全过（复算逐字段相等、unknown 不进均分 6/6、总账 940 对平、零池写入 7/7），阻断项=审查者自曝事故（G2-F1 P1：误覆盖 out/primary/CN_A_000672.json 1.3MB→4.7KB 不可逆，6 家校准集 6/6 完好）+ 比较组 2 声明失效（G2-F2 P2）→ **修复批 R1/R2/R3+F3/F4/F5 全部完成并提交 `1c761d6`**（事故三处入档、清单改 4 家 120 题、summarize 护栏+stdout 模式实测、台账同步）。
- [x] **G2 r2 = verified_for_local_gate_scope（2026-10-05，M2 关门维度放行）**：owner 事故签认（round-38「已知悉，接受」）后 r2 复核——r1 双阻断（G2-F1 事故、G2-F2 比较组）按其自设条件全闭、6 家校准 sha 6/6 未变、比较组终版逐条一致；对"评分闭环与校准门槛"维度**允许进入 200 家运行验证**（L03 另有 Q08/Q09/W10/W11/W12/W15 前置未齐，本审查不表态；B01 前置未满足不构成方法结论）。r2 非阻断 LOW×3（F6 包 §3 命令同步、F7 filter 口径差异 7/4 vs 6/5 须写明、F8 台账签认标记滞后）已同批落实。报告 `reviews/G2/G2-review-2026-10-05.md`。**Q06（deps G2✓ C04✓）正式解锁。**

### Phase 76: W06 审查跟进批次 F1/F2/F3（代次门与兼容门）

Status: implementation_and_gates_complete; review_deferred_to_milestone_group

- [x] 写前报告：`reviews/IQS-lane/W06-followup-F1F2F3-card-2026-10-05.md`（owner 通授覆盖；跨 StockWiki+IQS 两仓的精确文件清单与语义边界）。
- [x] TDD：RED 2 失败（F1 代次对齐门缺失、F2 兼容门在 unknown/冷却之后）+ F3 IQS 测试补真实输入变化（17+9 直接过——行为本正确、纯补测）→ GREEN 16/16。
- [x] 实现：`quick_scan_freshness.py`——F1 resume 前 C04 语义代次门（期望≠在途→dispatch_new_work/generation_mismatch）；F2 兼容门前置到 unknown/冷却分支（新身份不继承旧冷却）+ in-flight resume 保持最先并在 `_field_decision` docstring 记录审查者认可的"防重复派发"取舍（Q06 链的执行器 logical-key 去重为终局方案）；决策词汇表/plan_sha256/零网络不变。
- [x] 门：ruff/black 净、StockWiki `check_all.sh` **ALL CHECKS PASSED**、IQS 定向 17+9 过（ruff 3×E402 为该文件既有结构、非本批引入、不动）。
- [x] **独立审查两轮收口（2026-10-05，不等 A/H 单独收）**：r1 needs_revision（P2-1 原 finding 字面"复用/恢复"只做了 resume 半边 + LOW×4）→ 整改批（reuse 门+反例、case② docstring 豁免留签认、LOW-1/2/4 全修、LOW-3 SHA 记档、INFO nul 清理）→ **r2 approved**（P0/P1/P2 归零；审查者独立复跑 20/20、ruff/black、check_all **917 passed ALL CHECKS PASSED**、IQS 17+9、SHA Get-FileHash 实测相符）。报告 `reviews/IQS-lane/W06-followup-review-2026-10-05.md`。
- [x] **两仓提交**：StockWiki `0d6adf3`（仅本批 2 文件，A/H 5 文件未触碰）、IQS `e234cff`（卡修订+审查报告+Q06 草案+台账）。**W06 F1/F2/F3 批次 verified**。
- [ ] 非阻断遗留（owner）：case② 豁免与 F2 resume-first 两处取舍签认——docstring/施工卡已留档，建议随 Q06 收尾卡一并签认。

### Phase 79: W11 定向补扫接线（Q06 解锁后的下一批）
Status: card_written; ready_for_implementation
- [x] **W11 解锁确认 + 只读勘察（round-55）**：deps W06✓W09✓W10✓Q06✓；`request_refresh` 在两仓源码均不存在（grep 实证）=本批新建；W09 `quick_scan_query.py`（coverage/export 五接口）与 W10 `quick_scan_delivery.py`（状态投影）为只读基座；StockQA 执行入口（main_with_llm + Q09 绑定）为复用对象。
- [x] **写前报告卡已写**：`reviews/IQS-lane/W11-refresh-card-2026-10-05.md`（设计=request_refresh 拥有者接口（范围校验/cap/增量版本）+ W09 coverage 缺口检测 + 复用既有执行入口；允许改动=StockWiki 新模块+测试，StockQA 预期 0 改动；case=QUERY-04/JOB-06/TIME-05（DB-07 归 Q10）；不变量 I09/I13/I18 按 decision-register 原文）。owner 通授（2026-10-03）覆盖本批，条件=写前报告+独立审查+live 前成本声明（本批纯离线，无 live 成本）。
- [x] **TDD RED→GREEN（round-56/57）**：RED = StockWiki `ModuleNotFoundError: quick_scan_refresh` ✓ + IQS `field_freshness_preview` 入参形状错→修正后 2 passed（TIME-05 既有契约侧执行）；GREEN = `stockwiki/quick_scan_refresh.py`（RefreshError 具名 code、严格字符类 SQL 形输入先拒、profile 字段非空判覆盖→复用、离线估价×cap、RFR_ 内容寻址 task_key 与 roster 版本无关→JOB-06 自动增量、derive_scope_update 纯函数）+ `tests/test_quick_scan_refresh.py` 3 passed。**字段词汇按真实契约调整**（profiles_from_store 只承载 canonical_name/identity_state 等，QUERY-04 测试改用 canonical_name+industry——卡实施记录已档）。
- [x] **门**：StockWiki `check_all.sh` **ALL CHECKS PASSED**（framework 0 errors/12 既有 warnings）、W11 定向 3 passed、black/ruff 净；IQS TIME-05 2 passed + plan 80 passed/53 subtests + ruff 净 + `git diff --check` 0。卡修订（IQS 测试文件入允许清单+实施记录）。
- [x] **独立审查三轮收口（570d7cb3）**：r1 needs_revision（1×P1+7×P2，无 P0）→ owner 决定 P1-1=a 补接线、P2=修5留2（P2-4/P2-6 书面接受延后）→ r2 needs_revision（4×P2 记录可信度/契约一致性，10 行量级）→ 四条件整改 → **r3 = approved**。三轮门数字：check_all **929 passed/15 skipped/coverage 81%/framework 0 errors+12 warnings**、定向 4 passed、IQS 2+80/53、black/ruff/diff-check 全 0；范围恰 3 文件（cli_parsers 纯加法 73/0）、StockQA 0 改动、I09/I13/I18 无回归。
- [x] **P1-1（a）接线四件套**：`render_refresh_artifact`（gap 分实体 bundle：entities_file 白名单簿记 + questions_file 恰合 --config 形状 + company 字段 + 逐 invocation 配方 docstring）+ CLI `quick-scan-refresh-request`/`quick-scan-refresh-status`（W10 只读投影不自建库）+ 集成级 e2e（真 CLI+真 store：ENT_D 永不出现、格式逐字断言、stdout canonical JSON）。
- [x] **隔离提交**：StockWiki（3 文件，钩子链过）+ IQS 记档；**W11 = verified（本行）**。
- [ ] **ADV-1 记档（随 Q09/live 批次）**：`company` 标签现取 entity_id（自洽不致失败但把稳定 ID 当公司名进检索题面）——**任何 live 补扫前换 `canonical_name`**（W09 投影已带，CLI 一行可得）+ e2e 补 1 行 company 断言。r2 LOW×6 备案（可选）。
- **队列状态**：④ W11 关闭 → 下一批 = Q07（逐题检查点，deps Q06✓）/ Q09（并发预算）——M3 余项 Q07→Q09→Q10→B01→L03。

### Phase 80: Q07 逐题检查点/部分回复/取消恢复
Status: card_written; ready_for_implementation
- [x] **目标恢复 + 轮次预算 120**（owner「恢复目标，继续做不要停」round-61；blocked(round-limit)→edit max→resume，objective 更新为当前队列 Q07→Q09→Q10→B01→L03→余项）。
- [x] **只读勘察**：Q07 store API 全备（save/get checkpoint、note_late_receipt、reconcile_budget_attempt——契约恰合 I05 1-10 int/I12 同 attempt 幂等）且**零调用**；回执在 `QAResult.metadata` 已有（to_quick_scan_dict 同源组装，引擎缝隙可直接存）；Q06 生命周期与内容寻址键为 PAR-04/JOB-04 提供基座。
- [x] **写前报告卡**：`reviews/IQS-lane/Q07-checkpoint-card-2026-10-06.md`（接线设计五点、六 case 映射、允许改动 5 文件+禁改、门、风险边界；纯离线）。
- [x] **RED（round-61）**：`tests/unit/test_q07_checkpoint.py` 六 case 就位，**5 failed / 1 passed**（LLM-07 的 store 校验层预满足=已存在契约；其余真红：`recovery_report` 缺、补水未接、原检查点未保、取消语义未接、迟到回执未接）；ruff 净。实现面已定型（勘察结论）：**store 零改动**——`cancel_pending`/`list_run_items`/`save+get_answer_checkpoint`/`note_late_receipt`/`reconcile_budget_attempt` 全部已存在；接线件 = lifecycle `hydrate_question` + 引擎补水 + `after_question` 有真回执→`save_answer_checkpoint`（否则维持 Q06 honest-unknown）+ llm_runner `recovery_report` 四态分区 + 取消包装。
- [x] **GREEN + 四重门（round-62）**：实现 = `models.execution_receipt_for_checkpoint`+`final_transport_provider`（回执单一事实源）· lifecycle `hydrate_question`（派发前查 checkpoint）+ `after_question` 扩展（**verified 身份+回执完整+答案形状+model 匹配**四前置全过才走 record response_available→save，否则回 Q06 honest-unknown——预检查保证 record/save 不劈叉）+ `budget_policy/budget_route` 对（Q09 缝）· qa_engine 水合分支（getattr 守卫=Q06 钩子契约不变）· `recovery_report`（五桶无重叠分区+Q10 注记）· `cancel_pending_work`。测试修正记录：seed 需先 record response_available（store L2235 契约）、verified 身份（save L2225）、模型匹配、provenance 键=`response_completed_at`、policy 需 `configure_quick_scan_budget` 注册、max_cost 数值型、raw attach 用 lifecycle 一致指纹。
- [x] **门**：Q07 定向 **6 passed** · Q06+引擎回归电池 **123 passed（Q06 零破坏）** · 全量 **887 passed/4 skipped/0 errors**（881+6 自洽）· mypy Success（4 源文件）· black/ruff 0。
- [x] **独立审查三轮收口（fb6ba165）**：r1 needs_revision（2×P1 劈叉/水合伪时 + P2×2 + LOW×4，无 P0）→ 整改（`_preflight_checkpoint` 零状态回退+漂移探测对、水合原时+信封回执重建、四桶精确成员、信封接线共享函数、LOW 全清）→ r2 needs_revision（唯一阻断=P2-r2-1 注释绝对化+"已删"假声称）→ 注释/收窄/卡内更正留痕 → **r3 = approved**。三轮门：全量 **889 passed/4sk/0 errors**、电池 125、Q06 15、CLI 48、mypy/black/ruff/diff 全 0；范围恰 4 变更面、store 零改动、Q06 契约与 I05/I12/I17 无破坏。
- [x] **StockQA 隔离提交**（恰 4 面：models/qa_engine/llm_runner/test_q07，全钩子链）+ IQS 记档；**Q07 = verified（本行）**。
- 非阻断遗留（已入审查报告）：LOW-3（builder-None 引擎级用例后续建议）、INFO Q09 双预留接缝（随 Q09 批）、recovery 双查备注。
- **队列状态**：Q07 关闭 → 下一批 = **Q09（并发预算，含 ADV-1 company=canonical_name live 前换、Q09 双预留接缝）** → Q10 → B01 → L03。

### Phase 81: Q09 并发上限/费用预留/预算停止
Status: card_written; ready_for_implementation
- [x] **只读勘察（round-66）**：store 预算机器已建成（三层槽 DB 计数/成本请求门/I50 对账门/不确定保留预留/budget_totals 守恒，全为 Q09 首段产物）；mark_send_intent=work 路径唯一预留（L1704）；cascade `_preferred_route_busy` 同账本读；Q07 已铺 policy 对参数。**真缺口**=runner 未接 policy 对（reserve-before-dispatch 今日未激活=I11 缺口）+ 时间 deadline 门 + 六 case 测试（含 PAR-01 跨进程）+ ADV-1（W11 company→canonical_name）。C05 依赖已 verified（L105）。
- [x] **写前报告卡**：`reviews/IQS-lane/Q09-budget-card-2026-10-06.md`（接线/时间门/三层实证/六 case 映射/ADV-1/允许改动 6 项+禁改/门/风险含多路由归因披露与 BUD-04=L01 边界）。
- [x] **TDD 测试层 GREEN（round-67，7 passed）**：`tests/unit/test_q09_budget_concurrency.py`——BUD-01（Barrier 双线程恰一 admitted、totals≤budget、拒绝项 pending）/BUD-02（spent=8 后任意路由均拒、同账本守恒）/BUD-03（uncertain 保留 in_flight=1→对账门拒新 attempt→reconcile(resolved_outcome=completed) 后守恒且放行）/BUD-04（未配置拒+max_requests=1 耗尽后拒，live 前置归 L01 登记）/JOB-09（新预留原子拒、在途仍结算 spent 9e6/reserved 0、已发送 attempt=0）/deadline（time_cap_reached、pending 保留、在途照常结算）/**PAR-01 跨进程**（双子进程分路由、DB 轮询在途≤4 无违例、max_seen≥2=真重叠、X 崩溃后 attempt 仍 send_intent+budget 行仍 in_flight=崩溃安全）。
- [x] **实现（deadline 门 + reason 准入码）**：lifecycle `deadline` 参数（monotonic，超点拒 `time_cap_reached` 不 claim）；store_error/attempt_intent reason 带上 `str(exc)`（准入码如 budget_request_limit 可见）。
- [ ] **余下**：runner 胶水（构造点传 policy 对=reserve 真接线 + 胶水 e2e 断 budget 行）→ ADV-1（StockWiki company→canonical_name+断言）→ 双仓全门 → 独立审查两轮 → 隔离提交 → Q09 verified。
