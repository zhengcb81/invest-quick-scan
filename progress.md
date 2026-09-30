## 2026-09-23：G0 独立审查与外部只读核查
- 用户授权读取StockQAbyLLM、StockWiki、company-wiki及研究skill，并明确外部写入必须先询问；本轮没有外部写入。
- 已生成 `docs/implementation/reviews/G0/external-interface-snapshot.md`，用工作树文件SHA绑定实际接口观察，并更新G0预审包消除“本轮未重读外部仓库”的陈旧描述。
- 已启动独立审查agent；审查范围包含G0矩阵、全部P00/C01—C07契约/测试/回执/原始日志及最新外部接口快照。G0在其结论和问题关闭前继续保持pending。
- 外部事实确认了后续任务边界：Q01等StockQA修改和W01等StockWiki修改必须另行取得写授权；G0通过后可先继续本仓S01。

## 2026-09-23：Task C04 字段时效、待办键与状态转移
- 按最新进度表实施C04（M0，Owner iqs），仅修改invest-quick-scan；未改写其他项目。
- 发现已有C04草稿虽有schema/文档/8项测试，但scope key缺证券/分部身份，缺原请求不确定态；测试内自造规则不验证实际参考逻辑，且资料未知与导入状态混在同一状态机。
- 新增纯离线参考规则scripts/work_contract.py；更新schemas/quick_scan/work.schema.json及规范文档；扩展测试到15项，覆盖TIME-01—08及JOB-01/JOB-08。
- 固定不同时间字段、UTC/日期精度、到期严格边界、回溯发布时间、语义/路由/作用范围、题目代次与请求缓存键；同公司经营题和A/H证券估值题使用各自身份键。
- 明确pending/leased/uncertain/result_ready/delivered/failed/cancelled只表示执行/投递流程；insufficient_evidence是答案状态，deferred_unknown是冷却时调度决定。到期创建新字段generation，不改旧观察；结果不明按同一attempt对账。
- 15项C04定向测试全部通过，41项实施计划校验测试全部通过，计划清单校验通过（73任务/162场景，仍未运行生产case）。测试输出存于docs/implementation/contracts/validation-C04-2026-09-23.log。
- 创建receipt-C04，记录真实文件hash/命令/退出码；因当前没有独立审查回合，状态保留implementation_complete/review pending，不声称verified或G0。
- 未进行网络/LLM调用、数据库迁移或其他仓库写入。下一步应独立审查C04；审查通过后再做C05。

# 进度记录

## 2026-09-26 — Milestone review cadence clarified

- Audited the live implementation plan, test strategy, receipt contract, README, and handoff rules. Confirmed that recent execution already batches checks: P00 one focused check batch/one review; C01–C07 one shared regression/one combined review/one recursive verifier; Phase 27 one G0 review.
- Clarified in the strategy/README that atomic acceptance evidence does not imply one test process or log per assertion. A batch run and run ID may support many selectors/assertions; task-specific byte-identical log copies are allowed by the receipt path policy. The assertion mapping remains auditable.
- Clarified that the ordinary review cadence is G0–G6 and major interface/release gates. P01's pre-seal and post-seal pair remains a one-off evidence-hash requirement.
- Corrected Phase 27's stale plan-version references from 1.9.6 to 1.9.7. No task, case, or invariant counts changed. Validation: `python -X utf8 scripts/implementation_plan.py validate` returned planning_valid=true (103 tasks/327 cases/G6); the focused `test_implementation_plan.py` suite passed 79/79; touched-file `git diff --check` exited 0 with only existing CRLF notices. Next: continue the already-planned G0 candidate closeout.

## 2026-09-26 — G0 1.9.7 current candidate frozen

- Refreshed the C07 recursive verifier sidecar. It checks current v2 receipt dependencies through C01–C07/P00/P01 and returns `eligible_to_close=true` with no blockers; updated sidecar SHA-256 is `EC76ABF99AF020A4BB034D628944B59FADBAED77D5D75E54168E5599FC3FCDED`.
- Added current G0 review packet and invariant matrix with explicit local-contract versus production/live boundaries. Kept older packets/reviews as historical evidence; verified the prior candidate/final-review bytes match their archived copies before replacing the candidate.
- Regenerated and verified the G0 manifest for plan 1.9.7: 623 files, no omissions/extras/hash mismatches; persistent test fixtures, current G0 packet/matrix, and current scope log are included. Candidate SHA-256: `3F88A639BFC1F03D7460F161E8F9AA46B66F3B56AD74C90D23779FA91D348538`.
- One authorized independent reviewer is now reviewing this exact frozen candidate. No G0 receipt has been sealed; the final review path is excluded from the candidate to avoid a hash cycle. No external repository writes, live/API requests, or company-document downloads occurred.

## 2026-09-22：Task C03 评分回复与三值规则契约冻结
- 实施任务 C03 完成（Stage M0，Owner: iqs）。
- 交付规范文档 docs/implementation/contracts/scoring.md，冻结评分回复、检查等级与三值逻辑真值表规范（I05, I06, I15, I17, I19）。
- 交付 JSON Schema schemas/quick_scan/score.schema.json 与 schemas/quick_scan/rule.schema.json。
- 交付自动化单元测试 tests/test_scoring_and_rules_contract.py，全量覆盖关联场景：
  - `SC-02`：nullable score 与旧传输层默认 5 分彻底隔离，不进入正式均分；
  - `SC-03`：严格 1-10 整数分，拒绝非法边界值（0, 11, 浮点, bool, 字符串）；
  - `SC-04`：内外分数冲突或问题 ID 答非所问时明确报错，拒绝位置猜测；
  - `SC-05` & `SC-06`：模型自报 accepted_ids 或 search_verified 无法自签资格，保持 unverified_model_output；
  - `SC-07`：经审核 N/A 可从分母排除（7/9），未审核 N/A 和 unknown 不扣减分母（7/10）；
  - `SC-09` & `RULE-02`：三值逻辑真值表（all: fail>unknown>pass; any: pass>unknown>fail）及 critical risk 优先一票否决；
  - `RULE-01`：字段阈值比较（>8 失败，>=8 通过）；
  - `RULE-03`：缺失字段评定为 unknown，空 all/any 规则抛出配置错误。
- 执行 pytest 测试全量 116 项通过（101 subtests, 0 fail, 0 skip, 0 warnings）。
- 交付完成回执 docs/implementation/contracts/receipt-C03.json。
- 下一步进入 C04 任务（冻结字段时效、待办键与状态转移契约）。

## 2026-09-22：Task C02 指标映射与证据口径契约冻结
- 实施任务 C02 完成（Stage M0，Owner: iqs）。
- 交付规范文档 docs/implementation/contracts/metrics.md，冻结指标定义、可比性范围与证据口径规范（I05, I06, I07, I08, I20）。
- 交付 JSON Schema schemas/quick_scan/metric.schema.json，覆盖 MetricRegistryEntry, QuestionMetricMapping, MetricContractBundle。
- 交付自动化单元测试 tests/test_metrics_contract.py，全量覆盖关联场景：
  - `SC-08`：变质测试验证追加满分10分的杜邦、五力、恢复诊断题，质量/成长/估值均分严格不变；
  - `SC-09`：关键风险题（IQS_16等）得分<=3时一票否决质量门槛，不可被均分或OR规则绕过；
  - `SC-10`：核验通用核心模块包含完整24道买方核心题；
  - `SC-11`：跨群体指标（银行ROE与工业ROIC）判定为不可比，禁止跨行业混分混排；
  - `DUR-01` & `DUR-02`：护城河与变化证据要求说明前提与反证，新业务增长需核算股东净经济效果；
  - `DUR-03`：按需诊断规则遵循精简原则，not_applicable直接跳过，避免冗余题目。
- 执行 pytest 测试全量 108 项通过（101 subtests, 0 fail, 0 skip, 0 warnings）。
- 交付完成回执 docs/implementation/contracts/receipt-C02.json。
- 下一步进入 C03 任务（冻结评分回复、可用等级和三值规则契约）。

## 2026-09-22：Task C01 身份与名单契约冻结
- 实施任务 C01 完成（Stage M0，Owner: iqs）。
- 交付规范文档 docs/implementation/contracts/identity.md，冻结 Entity / Security / Segment 三层分层契约（I04）。
- 交付 JSON Schema schemas/quick_scan/identity.schema.json，覆盖 Entity, Security, Segment, VerifiedIssuerBridge, UniverseMember, UniverseManifest。
- 交付自动化单元测试 tests/test_identity_contract.py，全量覆盖关联场景：
  - `ID-01`：A/H 双重挂牌实体经营题生成 1 份待办、估值题针对 CNY/HKD 独立生成；
  - `ID-02`：母子公司虽同品牌但非同一发行人时严禁合并，保持双实体；
  - `ID-03`：ADR 未核实比例时 adr_ratio=null，严禁推测换算比率，实体经营画像安全复用；
  - `ID-04`：无 company-wiki 条目和 formal profile 时允许独立准入，无前置建档依赖；
  - `UNI-04`：2,000 家大池扩容至 2,003 家不自动挤出，退池为逻辑移除，恢复保留审计理由与版本递增。
- 执行 pytest 测试全量 102 项通过（101 subtests, 0 fail, 0 skip, 0 warnings）。
- 交付完成回执 docs/implementation/contracts/receipt-C01.json。
- 下一步进入 C02 任务（冻结指标映射及优势/变化证据口径契约）。

## 2026-09-22：Task P00 接口核实与基线报告
- 实施任务P00完成（Stage M0，Owner: iqs）。
- Git 初始化完成，记录了项目初始基线（commit `85162ec`）。
- 核实外部仓库 commit hash 与状态：StockQAbyLLM (`3c685dda`)、StockWiki (`f5b8526c`)、company-wiki (`f39bd5a6`)。
- 确认外部依赖与替代路径：CodeGraph 8080端口未开启（Transport closed），采用本地只读文本与代码结构检索替代（BASE-02）。
- 核实 StockQA 调用链与已知缺陷：AnswerGenerator 第58-61行固定 answer_score = 5 覆写模型返回的8分；LLMClient 仅传递基础参数未携带搜索工具/开关；ProviderCascade 当前为内存状态（BASE-01）。
- 核实本地题库规模（评分3.0共48模块222题，事实1.0共61题），运行 pytest 97 项测试全部通过（101 subtests, 0 skip）；记录了 test_question_sets.py:282 的 5/8 观察性断言。
- 交付产物：docs/implementation/baselines/baseline-report-2026-09-22.md 及完成回执 receipt-P00.json。
- 下一步进入 C01 任务（定义跨项目公司/证券两层身份及统一标识规范）。

## 2026-09-22：全局复核与题库标准化
- Phase 11完成；读取skill-creator并恢复planning-with-files，核查真实接口，保持外部仓库只读。
- 交付事实61题、评分3.0的字段/口径优化、固定24核心汇总、标准答案/不可变观察/三维比较、可重放虚构样板及用户模型顺序模板。模型配置只离线校验，未实现重复的LLM运行器。
- 完善首次setup、手动/自动准入、持续增量、单一写入归属、备份水位、三维UI及研究技能联动。计划1.4.0现有73卡/162验收规格/28约束；G6覆盖全部72前置任务。
- 独立前向审查与复测已完成题库/输出路径；修复身份与日期/期间比较问题。新增回归发现可变输入hash和配置null窗口问题，修复后全套97项离线测试通过，无skip。
- 题库、事实、配置模板、计划及skill校验通过，5个虚构观察与schema验证通过；已审查本地链接和全部任务阅读引用。审查详见docs/implementation/reviews/local-standardization-2026-09-22.md。
- 162项为未来生产验收，不是本轮已跑测试。StockQA搜索/8→5、持久化并行执行、StockWiki数据/UI及消费者接线仍待实施；未改外部项目、未付费搜索或下载公司文档。下一步从P00开始逐卡交付。

## 2026-09-22 — 企业结果 UI 规划
- 恢复同一根目录计划，新增Phase 10；本轮仅细化UI规划和验收。
- 已核查O05与X06，新增results-ui.md及U01列表、U02评分详情、U03事实/历史任务；O05负责组装，X09/G6要求真实浏览器操作验收。
- 新增UI-01—12固定场景，涵盖身份、阈值、缺失/过期、恢复观察、替代/汇总、安全来源、历史、2,000家分页、导航/故障、能力状态、关系和桌面/窄屏/键盘操作。
- 清单与关联文档升级1.2.0：70任务/136场景，最终依赖覆盖全部69个前置任务。41项规划工具测试通过；14份Markdown/40链接/14阅读引用与UI任务包检查通过。C06/W09已补接口前置要求，最终清单校验再次通过。
- Phase 10完成。本轮仅修改本项目计划/规格文档与JSON；未实现外部页面、未执行真实浏览器/在线验收。下一步仍从P00逐卡实施，UI是交付必需项。

## 2026-09-22 — 跨项目配套与统一启动计划
- 新增Phase 9，核查跨项目业务卡之外的安装、配置、启动与整体验收缺口。
- 计划中的一键开启以首次配置完成、明确模型顺序和预算为前提；日常运行不重复编辑多个项目配置。
- 已新增一键开启设计与各项目交付清单；首次设置、配套版本/实际加载、进程桥接、同一启动入口、导入ACK、停止/续扫、升级回退均有单一拥有者和验收任务。
- 计划升级为1.1.0：67任务、124验收规格、26约束、M0—M6/G0—G6。新增C07、X01—X12、G6，最终关口覆盖全部66个前置任务，包含G4事实/消费者和G5评分扩容。
- 规划工具支持按owner筛选，拒绝省略消费者、孤立任务分支、仅评分交付或用离线测试冒充真实启动验收。新增场景ID暴露旧正则限制，修复后41项规划工具测试全部通过。
- 完整清单校验、13份Markdown/32个本地链接/13个阅读引用检查、X05/G6任务包提取和M6仓库筛选均通过。文档联调顺序已与依赖图对齐：X09离线、X11升级回退、X10真实联网、X12交付、G6终审。
- Phase 9完成。本轮只更新本项目规划文档、任务/场景清单及规划工具/测试；未修改外部仓库、安装运行组件或发起付费扫描。124项为待实施验收规格，41项为实际运行的规划工具测试；下一步从P00逐卡实施。

## 2026-09-22 — 细粒度实施与验收包
- 已恢复原计划并新增Phase 8；按用户要求细化任务、测试和审查流程。
- 本轮保持现有产品代码与外部项目边界，重点交付可执行的任务说明、测试预期与审查证据要求。
- 已完成53张任务卡、99个规格场景、21条约束、六阶段审查及只读任务提取工具；未运行任何生产联网试点。
- 首轮27项计划工具测试通过；追加三项自查回归后发现非法case.kind导致TypeError，现修复类型检查并保留失败记录，准备复跑30项。
- 已检查11份Markdown、23个本地链接、11个任务阅读引用；无缺失。P00命令行任务包可正常提取。
- 类型安全修复后30项计划工具测试全部通过；53任务/99场景的清单校验通过。原99场景是未来验收规格，不是已运行的生产测试。
- 已完成结构化自查和依赖修正：备份恢复W12前置于L03/G3；普通产业/恢复查询不隐含质量gate；真实事实试点有独立LIVE-07验收，不能只用集成stub过关。
- Phase 8完成。后续从P00核实各仓真实接口、基线和命令，再按C01—C06/G0及后续任务卡实施；本轮未修改外部仓库或启动真实扫描。

## 2026-09-21 — 股票池名单、接续扫描与跨技能联动

- 恢复原planning-with-files计划，追加Phase 7。
- 已确认用户本轮要求是综合方案与计划；没有授权启动实际2,000家公司批量运行。
- CodeGraph暂不可用、两个研究skill安装入口失效，已切换到源项目只读核查；未改变已初始化索引。
- 已核查StockQA现有ProviderCascade与StockWiki runtime边界，从local-skills源目录读取两个研究技能的具体工作流，并核实官方证券名单入口。
- 已新增docs/universe-and-operations-design.md，同步总体设计及M0—M5路线。五项需求均有设计、拥有者、实施阶段和情景验收。
- 名单、接口和运行机制仍为待实施方案；本轮未改变题库/脚本、未创建真实名单、未调用收费问答、未修改外部项目。
- 文档一致性检查通过：7份Markdown、14个本地链接、既有示例JSON语法、分层示例总量及独立公司计数口径。未重复执行无代码变更的27项测试，也不将文档检查作为实际模型或队列验收。
- Phase 7完成；后续实施入口为M0契约与名单底座、M1 StockQA真实搜索/评分修复和有序模型接线，再按10/60/200家公司验证。完整事实问题和两个研究技能关系检索在评分闭环之后。

## 2026-09-19 — 不变优势与产业变化的设计讨论

- 已对照24道核心问题及恢复观察协议，识别优势有效条件、迁移能力与新旧业务净经济效果的设计缺口。
- 正在查阅战略/动态能力的原始研究并整理具体问题映射；本轮保持方法设计范围，不调整现有评分代码。
- 已完成docs/durability-and-change-design.md及总体设计/实施路线的链接与后续任务，Phase 6完成。
- 已检验3份设计文档的本地链接和代码围栏；只做文档校验，没有重复运行无需变更的代码测试。
- 当前题库2.1.0与既有recovery_watch实现保持原样；新的桥接问题、字段与变化标记均为待实施建议。

## 2026-09-19 — 周期低谷与困境反转补充

- 用户要求保留暂时困难但有优势公司的关注路径。
- 已读取skill-creator并继续使用原planning-with-files计划；CodeGraph检查了路由和结果关键风险逻辑。
- 正在核查相关题库，补充问题与独立观察标记，不改外部问答执行器或股票池数据库。
- 已完成4道recovery诊断、条件路由、独立观察输出和恢复观察说明；更新SKILL及股票池设计/路线，生成虚构recovery-profile。
- 27项测试通过。首次2项失败来自测试未使用实际类型替代题，已纠正；skill校验遇GBK默认编码，正在用UTF-8模式复核。
- UTF-8模式skill校验通过；题库校验48模块/222题；7份Markdown、20个已有本地引用与改动JSON校验通过。
- 已用虚构recovery-profile成功编排35题到runs/recovery-v2.1，未运行任何真实LLM问答、下载公司文档或改动外部项目。
- Phase 5完成。本次改动包含SKILL、题库catalog和恢复模块/反转锚点、question_sets.py、兼容主模板、测试、恢复profile与说明，以及相关规划文档。
- 本地恢复标记已实现；跨公司数据库、并行股票池查询和卡片展示仍是后续实施项。

## 2026-09-19 — 股票池总体规划

### 已完成
- 读取planning-with-files，解析计划目录并建立根目录task_plan.md/findings.md/progress.md。
- 确认用户目标从单公司快扫扩展为股票池筛选与产业链检索基础设施。
- 读取现有invest-quick-scan入口；发现company-wiki已有证券身份解析能力。
- 记录已安装深研skill入口读取失败，准备从源项目核查。

### 当前工作
- Phase 1已完成：已核查company-wiki、StockWiki、StockQAbyLLM及深研项目的实际边界。
- Phase 2已完成：根据用户新增轻资产约束修正存储与联动方案，去掉来源文档采集与归档依赖，已写入docs/stock-pool-design.md。
- Phase 3已完成：写出M0—M5实施路线与虚构结构化示例。
- Phase 4已完成：核查设计文档和示例一致性，规划可交付。
- 核心判断：快扫自给的问答数据闭环，与正式深研的来源资格流程分开；不让联动扩大快扫运行成本。

### 验证
- 本轮尚未执行采集、联网LLM调用、数据库迁移或批量公司建档。
- 上轮代码测试结果仅作背景，本轮文档更新不冒称已实现后续功能。
- 本轮离线文档校验通过：JSON语法、现有题目ID、5个规则案例、1个主题正例和2个反例、4个本地链接及Markdown代码围栏。
- 当前改动仅为本项目三份planning文件及docs下三份设计文件；问卷、现有代码和外部项目未修改。

### 下一实施入口
- docs/implementation-roadmap.md：先M0契约，再M1修复StockQA真实搜索与评分传递；评分闭环完成后才展开事实问卷。
- 不以本轮规划完成作为实际联网、数据库或全池任务已经完成的证明。

### 产物
- task_plan.md
- findings.md
- progress.md
- docs/stock-pool-design.md
- docs/implementation-roadmap.md
- docs/design-examples.json

## 2026-09-23：C04接续与C05模型策略/预算契约

- 用户已设定持续目标：按1.4.0计划逐卡实施；先完成invest-quick-scan本目录。其他仓库保持只读，写入前需用户明确授权。
- C04已实现时效、logical work key、attempt恢复和ACK状态契约，15项定向测试及41项计划工具回归通过，回执已提交本地工作树；状态implementation_complete，独立审查pending。
- 发现旧task_plan.md把C05误写为StockWiki SQLite schema。docs/implementation/README.md规定tasks.json和acceptance-cases.json为唯一清单；按1.4.0任务卡将C05纠正为模型顺序、故障分类与费用边界。未据旧标题写入StockWiki。
- C05交付本地策略契约、model-policy Schema 2.0.0、安全未配置模板、离线跨字段预算检查及契约测试。Schema新增搜索/结构化能力预检、失败类别、总预算/单次上限、未知费用暂停、比较子预算和组级单半开探针。没有调用模型/网络，也没有修改StockQA或其他仓库。
- C05验证：既有配置测试9项、新增契约测试16项、计划工具回归41项通过；模板CLI为`runtime_verified=false`、`network_used=false`；计划校验73任务/162场景/G6且`product_tests_executed=false`。原始输出在`docs/implementation/contracts/validation-C05-2026-09-23.log`。
- C05回执标记implementation_complete、独立审查pending；provider真实fallback、并发/跨进程额度、搜索和费用执行尚未实现。C04和C05均未verified，G0未通过。
- 下一步继续本目录C06/C07契约工作；任何StockWiki/StockQA等目录写入先向用户征求针对该任务的授权。

## 2026-09-23 — C06轻量交换、查询与深研交接契约

- 完成本地C06范围：新增exchange/query schema、虚构轻量观察包/ACK/查询样例、纯离线参考规则、契约说明及回执；未写StockWiki、StockQA或company-wiki。
- 冻结数据边界：StockWiki是轻量画像与名单唯一写入者，StockQA是唯一问答/费用/任务执行者；不共享可写库，不传文档正文、不伪造正式manifest/evidence span。
- 冻结Observation及item/package散列、ACK幂等/冲突/拒绝、能力及覆盖/水位、100实体分页固定snapshot、候选集版本、exact-scope补扫预览和独立确认、提名/身份冲突不自动处理、研究线索来源链防重复。
- 初次运行发现DB-03负例用“任意错误hash”配原payload，函数按契约先拒绝payload hash不符，未进入同key异hash冲突分支。已将fixture改成相同Observation ID的有效变更payload并重算hash，未削弱判定；冲突断言通过。
- 回执生成前的代码复核发现构包函数保留了调用方可变观察/版本引用；已深拷贝输入，并新增变更后仍保持item/package hash一致的回归测试。C06定向测试现为14项。
- 验证记录：C06契约14项、C04回归15项、C05 provider/budget 16项、model-policy 9项、计划工具41项均通过；`implementation_plan.py validate`显示73任务、162场景、G6、`product_tests_executed=false`。完整输出见`docs/implementation/contracts/validation-C06-2026-09-23.log`，SHA-256 `1084F3385922AA4DFC9C03A5E1E160EBB7255FA69E67899D3D21EAB328FCF91B`。
- C06回执状态`implementation_complete`、独立审查`pending`。G0未通过；真实SQLite事务、端点、浏览器UI、认证/用户确认与跨仓运行仍不属于本卡实际验证。继续本目录C07；其他仓库保持只读。

## 2026-09-23 — C07部署、启动生命周期与就绪协议

- 按真实C07任务卡补足本地可重放范围：新增部署/生命周期schema、纯离线参考策略、虚构release/doctor样例、行为测试、契约说明、完整输出日志与回执。C07任务卡的允许改动及测试交叉表同步明确为本地协议工作；没有增加生产启动器。
- 冻结StockWiki/StockQA配置引用拥有者、拟定setup/doctor/plan/start/status/stop/resume/verify_live请求、严格无密钥配置输入、doctor零网零付费、plan只预览、start/resume同workspace/profile幂等附着和费用连续、stop排空保留、company-wiki可选且不启动来源链。
- ReleaseSet要求5个核心组件及两个消费技能，保存实际工件/解释器/依赖/契约/能力；就绪依实际加载SHA而非版本文字。`full_release_verified`要求同一release的真实搜索/费用回执、G0—G6、消费者实际hash。进程管理身份包含workspace/profile/component/instance/PID/启动时点/解释器hash/cwd。
- 结构审查首轮发现响应schema把旧进程结构内嵌复制，修改后的绝对路径ref只作用于$defs而未约束响应；现已让安装记录和响应共同引用ComponentStatus/ProcessIdentity，并以相对路径负例验证拒绝。另验证release组件ID唯一、同版本异hash失败、能力/解释器/契约错配、doctor/setup不收费与full-release gate缺失。
- G0前向交叉审计另发现C07任务卡把E2E-05绑定到一个不存在的测试selector。现已改为实际测试`test_e2e_05_readiness_requires_evidence_from_same_release`；这属于证据映射修正，不改变行为预期。部署schema/model-policy版本命名修正后的C07定向13项、C06回归14项、C04回归15项、C05 provider/budget 16项、model-policy 9项、计划工具41项均重新运行通过；计划验证显示73任务、162场景、G6、`product_tests_executed=false`。Markdown相对链接3条均有效，代码围栏成对。
- 最新完整输出在`docs/implementation/contracts/validation-C07-2026-09-23.log`，SHA-256 `5544FC7AE4667718CF70D5187508E606E1B5983A2358B3EB92764FA3EF56C3CE`；更新后的文件快照和17项可追溯检查记入C07回执。上述均为本地契约/计划回归，不是生产集成验收。
- C07回执状态`implementation_complete`、独立审查`pending`。真实安装、公开CLI、跨进程互斥、SQLite/费用运行态、浏览器、真实搜索和消费者加载并未在本目录实现或验证；G0仍未通过，StockWiki/StockQA与研究技能源目录保持只读。

## 2026-09-23 — G0首轮独立审查整改

- 独立agent审查最新源码、schema、回执和原始输出，结论为`needs_revision`，报告落在`docs/implementation/reviews/G0/independent-review.md`。九项发现覆盖评分状态闭合、跨实体一致性、测试自实现/生产case误报、扩展逃逸、就绪自证、查询血缘、诊断混分、传递lineage和外部快照错误。
- 新增公共`contract_validation.py`，让C01—C03及G0回归调用实际生产候选校验逻辑；收紧score/metric/rule/exchange/query/deployment schema及release/lineage helper，并增加7组针对审查发现的负例。
- C05—C07任务改为只绑定新的`*-CONTRACT-*`离线场景；原LLM/BUD/PAR、DB/QUERY/CONS、DEPLOY/START/E2E运行场景明确留给外部owner公共入口，离线真值表不再冒充生产通过。
- 修正company-wiki外部快照：当前resolver确有issuer index和歧义失败关闭逻辑；其能力有助于别名/兄弟挂牌来源匹配，但仍不自动建立快扫发行人主档。
- 整改后定向契约测试93项、20个子测试通过；计划工具41项、13个子测试通过；最终全量181项、108个子测试通过。所有结果仍是本仓离线证据，G0须经最新快照复审后才能通过。

## 2026-09-23 — G0第二轮复审整改与真实数据E2E强化

- 第二轮独立复审关闭G0-02/03/04/06/08，继续阻断G0-01/05/07/09。新反例为可信回执跨对象重放、重复G0 gate伪造full readiness、嵌套裸规则导致执行器崩溃，以及候选范围漏绑直接依赖。
- 检查回执改为带hash的可信记录映射，并严格绑定entity/question/observation/授权等级/签发者/active状态；新增跨公司、跨题、跨观察、低等级升级和撤销回执负例。
- full readiness新增G0—G6各一次的Schema约束、每条gate的manifest hash，以及响应与预期ReleaseSet的公共语义校验；重复gate、错release、错manifest和重复consumer均拒绝。
- CompositeRule递归只接受包装叶子，裸threshold和嵌套policy拒绝；多层all/not有效树同时通过Schema与执行器。
- 新增完整范围manifest生成/验证器，要求声明范围与逐文件hash集合相等并标记`frozen_for_independent_review`；候选覆盖题库、Schema、helper、测试、fixture、契约、回执和原始日志。
- 计划新增E2E-06真实数据隔离/清理故障矩阵：唯一临时workspace/SQLite/目录、pre-state快照、run manifest、hash及owner保护删除、finally清理与零漂移断言。该live case尚未执行，须在外部owner实现及写入获授权后运行。

## 2026-09-23 — G0放行与S01实现

- G0第三轮独立复审判定`verified_for_local_contract_scope`：冻结候选145文件集合/哈希一致，独立全量184项与108个子测试通过，G0-01—09和RR-01—04全部关闭。E2E-06仍为live/specification，未冒充执行。
- S01将C02 metric契约接入实际`compose`：manifest记录`metric_contract_version`、逐题`question_metric_mappings`及每题`metric_contract`；质量/成长/估值/诊断作用层由题库元数据确定并逐条经Schema校验。
- 类型替代保留`replacement_for`与核心construct，security/entity scope原样保留，诊断不可成为critical且不进入汇总；catalog升至3.1.0，旧manifest不回写。
- 新增银行替代、诊断隔离、证券scope和context高分不改变核心24题的S01回归。定向36项、72个子测试通过；全量复跑首次仅因G0冻结manifest正确检测到S01后文件变化而失败，测试现改为验证已审candidate字节/报告不可变，同时对当前范围执行内存render集合等值检查。

## 2026-09-24 — S01审查薄弱点回归闭环

- 第四轮独立审查重放出9种manifest问题输入：重复或删除selected question、题目与mapping集合不一致、重复/闲置mapping，以及profile路由、module、replacement和顺序漂移。新增闭合校验后，全部负例被拒绝，当前合法manifest与旧版无metric-contract manifest继续通过。
- 定向测试执行结果：`tests/test_question_sets.py tests/test_metrics_contract.py` 为40 passed、76 subtests passed；全量pytest为192 passed、112 subtests passed。`question_sets.py validate`通过（48模块、222题）；计划校验通过（73任务、172场景、G6）。
- S01回执已更新为当前源码/测试SHA-256，并绑定定向与全量原始pytest日志。独立审查报告及两份证据addendum确认snapshot和日志hash一致，最终判定为`verified_for_local_implementation_scope`；REC-04仍按边界记为`specified_not_executed`。
- 真实数据E2E-06保持live/`specified_not_executed`：场景规定唯一run_id临时workspace/SQLite/下载/交换目录、pre-state、文件hash/owner清理白名单和finally零漂移断言。它依赖StockQA/StockWiki真实入口及对应外部owner任务；本地测试不冒充真实provider或跨组件执行。
- 下一项本地任务为S03：只落实C02/G0批准的优势成立条件、反证与新旧业务净经济效果，不擅自新增评分题；重点覆盖机会和侵蚀并存、旧业务损失/转型投入/融资摊薄，以及低谷可恢复与结构性变化的区分。

## 2026-09-24 — S03 优势条件与产业变化评分口径

- 按C02/G0批准范围更新`IQS_05`、`IQS_18`、`IQS_20`、`IQS_21`和商业化前替代题`PRE_REVENUE_04`。新增业务边界/成立条件/失效信号、结构变化的分部利润敞口/替代速度/反证，以及旧利润损失、转型成本、融资摊薄后的净股东经济效果；24个通用core construct与题目ID不变，变更题rubric升至2.0.0，catalog升至3.2.0。
- 生成`main_questions.json`并把导出一致性改成逐字比较。题库说明明确不增加未经批准的桥接评分、不按AI/主题标签加减分，机会与侵蚀分开，周期恢复沿用独立recovery_watch；旧结果保留原rubric，不重新标注为3.2.0。
- 定向运行`tests/test_question_sets.py tests/test_metrics_contract.py tests/test_standard_answers.py`：65 passed、83 subtests passed；全量pytest：197 passed、116 subtests passed；无skip。原始输出及hash在S03回执。
- 第一轮定向测试有1个断言因预期错误文本与实际清晰错误消息不一致而失败；按实际稳定错误契约修正断言后复跑通过，没有放宽被测版本检查。
- `question_sets.py validate`及实施包校验通过（48模块/222题；73任务/172场景）。S03回执已提交独立审查；其最终结论记录于后续收口段。
- TIME-06的真实按题刷新选择依赖StockWiki W06，本地只证明新旧rubric不能静默混用，未冒充刷新规划通过。用户要求的真实联网/下载清理E2E-06继续使用唯一run目录、manifest/hash清理和pre/post零漂移标准，待X09/X10真实入口及对应跨仓写入授权后执行。

## 2026-09-24 — S03独立审查收口

- 独立审查报告`docs/implementation/reviews/S03/independent-review.md`，SHA-256 `CABD7C6D8DC7D5CEBB7EE2E4098115B5E7DC68261FA9BEE78DA42B19C9E49BE8`；结论`verified_for_local_implementation_scope`，0阻断/0非阻断finding。审查者独立复跑定向65项/83子测试、全量197项/116子测试，核对回执与日志hash。
- S03回执更新为verified，并绑定被审回执hash `D55F3EE6F62B4D36266E636B887CAFF63B421D83A5B343B5212352A8FBD61608`和独立报告hash。TIME-06与E2E-06仍未执行：旧manifest拒绝测试不能替代StockWiki逐题刷新，且当前项目尚无可调用的真实跨组件live入口。
- 按用户对真实E2E隔离的要求，在本仓增设只供测试使用的运行沙箱/清理回归：唯一系统临时根、逐文件owner与hash清单、完整进程句柄、前后状态观察、失败时保留取证目录；默认测试只用临时fixture，不访问网络。未来live用例只调用owner公开入口并单独opt-in，未有真实入口前保持`specified_not_executed`。

## 2026-09-24 — 真实E2E隔离支架与故障回归

- 新增`tests/live_e2e_sandbox.py`及`tests/test_live_e2e_sandbox.py`。17个隔离测试实际创建并清理run目录、SQLite、下载样本、交换文件、日志和仅由测试启动的子进程；覆盖路径穿越、专用子目录、run_id/owner、manifest篡改/硬链接、文件大小/hash、未登记数据、外部状态漂移、Windows junction、清理暂存失败、开放SQLite句柄、异常收尾、不碰无关进程，以及子进程相对路径输出留在run-local workspace、外部cwd在启动前被拒绝。清理依赖5个专用目录内的逐文件白名单，不做无边界递归删除。
- 独立审查指出Windows安全缺口：manifest可能是指向外部目标的硬链接、先删日志后因SQLite句柄失败会造成半清理、空NTFS junction可能被误当普通目录。现已改为先检查控制文件唯一性并原子替换manifest；所有工件先完整暂存验证，任一失败回滚；识别reparse point并在Windows真实创建空junction回归。外部状态检查移至暂存之后，检测到漂移会恢复所有暂存工件并保留完整run目录。
- 在首次提交独立审查后发现子进程默认继承当前cwd的风险，已收紧`start_process`：默认cwd固定至本次run的workspace，显式cwd必须先通过临时根路径校验；新增“相对写入留在workspace”和“外部cwd不启动进程”两项测试。首版报告绑定旧源码hash，未用于放行，已由审查者针对冻结后的最新快照重审。
- Windows定向pytest `17 passed`；全量pytest `214 passed, 116 subtests passed`。对应日志分别为`docs/implementation/contracts/validation-test-isolation-targeted-2026-09-24.log`（SHA-256 `44D1F711A6E18E759F839E6E57C54B9811BFBDBC7986BAD529D392DDE63CD8CE`）和`docs/implementation/contracts/validation-test-isolation-full-2026-09-24.log`（SHA-256 `6CDCCFDF325EFEF3665C8366C59B7D8D731667D83E0E14D5C5B75D8025EEEBDD`）。题库校验通过（48模块/222题）；实施计划校验通过（73任务/172场景/G6，`product_tests_executed=false`）；`git diff --check`通过，仅报告仓库换行风格提示。测试后无`iqs-live-sandbox-test-*`目录残留。
- 独立报告`docs/implementation/reviews/E2E-isolation/independent-review.md`，SHA-256 `3152CD7023B8A4F38113E7902F63B432013888113C40EC10FCB4B32DB345F5C3`，结论`verified_for_local_isolation_mechanism_only`，0阻断/0非阻断；报告核对了源码、测试、策略文档和原始日志hash，并独立重跑定向/全量测试及Windows三项原审查反例。
- E2E-06的隔离/清理支架已本地验证，但真实StockQA搜索、真实StockWiki导入/ACK及provider额度故障尚未执行。只读检查确认StockQA README及`src/services/search_service.py`明示真实网络搜索仍为占位实现；StockWiki `stockwiki/`与`tests/`暂未发现quick-scan observation/ACK入口。因此本仓尚不能合法地把本地支架接成真实产品E2E；E2E-06保持`specified_not_executed`，没有改写外部仓库。


## 2026-09-24 — StockQA Q01–Q03 implementation candidate

- 按用户明确授权，仅在StockQAbyLLM执行Q01–Q03外部改动；未写StockWiki或company-wiki。实现复核发现Q03必须扩展到parser/provider基础类、CLI runner、QuickScan receipt序列化和错误计数，才能满足真实公开入口的身份校验、部分失败非零返回与可追溯要求；变更范围及原因已向独立审查者说明。
- 快扫结果现在要求显式question_id、entity_id和目标公司名精确匹配；require-search只接受整段合法JSON；wrong-company、错题或格式失败不产分。格式错误不再借传输重试重复发包；预算最多1次格式修复，修复失败记为unknown/null并让CLI返回失败，同时保留有效题。
- 搜索adapter显式请求web_search来源字段；只有Responses整体completed、request/response ID存在，且同一completed search call含来源URL时才标记已搜索。输出保留每次attempt ID、起止时间、prompt SHA-256、request/response ID、实际模型和search receipt；不存prompt、API key或来源网页正文。异步错误日志/异常不暴露上游响应内容。
- 定向StockQA回归：63 passed、1 skipped；全量：479 passed、1 skipped；Black检查13个变更Python文件通过，AST解析通过，`git diff --check`通过。一次既有错题测试仍断言error，更新为新契约unknown后通过。运行时CWD、pytest basetemp、日志和临时输出隔离在唯一TEMP目录并已清理；只移除了此前确认由本轮测试生成的`logs/stock_qa_20260924.log`，其他历史日志未动。
- 真实live E2E已加入，但本机无`STOCKQA_OPENAI_API_KEY`或`OPENAI_API_KEY`，因此默认skip；未发起付费provider请求。live fixture将密钥仅注入子进程环境，不写入配置文件，结束后断言临时sandbox不存在。LLM-01仍须有凭据并真实执行后才算通过。
- Q01–Q03最新候选已冻结给独立审查agent只读复核；因此本地回执/状态保持review_pending，未将测试通过等同verified。


## 2026-09-24 — Q02独立复核整改与二轮候选

- 独立审查发现Q02未记录HTTP发送失败：timeout、限额响应或5xx在成功解析前没有attempt ID/时间/prompt哈希，全部失败时CLI结果也没有回执。现新增`LLMTransportAttemptError`携带仅含异常类型、HTTP状态/request ID（如有）、唯一attempt ID、起止时间与prompt哈希的脱敏回执。
- sync/async provider会在有限transport retry内累积每次失败；重试成功仍保存失败与成功attempt；重试耗尽生成同schema的null/error结果、完整attempt数组并返回CLI非零。格式修复失败的请求也被并入attempt history。新增client/provider/公开CLI回归覆盖sync/async timeout、HTTP 429/request ID、timeout后恢复、重试耗尽、error body/prompt/query参数脱敏。
- 修复后二轮定向验证`70 passed, 1 skipped`，全量验证`486 passed, 1 skipped`；原始日志分别为`validation-Q01-Q03-final-targeted-r5-2026-09-24.log`（SHA-256 `8C01B4AE2954BE4D10F762B97705D46AAF31522527DEB71136D78B226737EC68`）和`validation-Q01-Q03-final-full-2026-09-24.log`（SHA-256 `8B803EECD3D017F461518FA216BE8ECE2D624D76EFD616B6669EC3D8B7ED5910`）。所有运行仍在独立TEMP根，运行后TEMP根删除且StockQA logs没有测试生成文件。
- 独立审查者先前全量影子运行受certifi ACL限制；实现方全量通过。审查者现收到二轮冻结候选，只需重点复核失败attempt的全链路回执及之前阻断。Q01–Q03仍为review_pending，LLM-01 live因无API key保持specified_not_executed。


## 2026-09-24 — Q12/S02 离线与本地范围收口

- Q12只在此前获批的StockQA源码和测试路径完成：公开结果按实际`Question.text`计算SHA-256，同步/异步响应从真实HTTP对象回传状态码。owner-side定向64项通过；排除25项受Miniconda `certifi` ACL限制的HTTP client测试后，461项通过、1项live跳过。未过滤全套有13项同类环境失败，未把受限子集说成全套通过。无真实网络或费用调用。
- S02导入器对公开CLI回执闭合题目哈希和顶层/最终attempt的整数HTTP 200；定向`tests/test_question_sets.py`为45 passed、92 subtests，全量为220 passed、128 subtests。隔离TEMP根均清理；对应日志hash记录于`receipt-S02.json`。
- 计划校验有效（74任务/174验收场景/G6），题库校验有效（48模块/222题），`git diff --check`通过，仅有CRLF提示。独立审查报告`docs/implementation/reviews/Q12-S02/independent-review.md`及附录均无开放finding；附录将文档命名finding Q12-DOC-01关闭。
- Q12与S02仅在报告声明的离线/本地范围标为verified。Q01—Q03各自owner回执、真实OpenAI搜索、StockWiki导入ACK/UI和G6 live release仍未通过或未执行。Q12证据回执保存在本仓，没有向StockQA写入新增回执文件。
- 下一卡Q04为StockQA owner的有序模型策略；接下来完成只读调用链和测试方案核查，写入StockQA前依用户边界另行请求明确范围授权。


## 2026-09-24 — Q04 外仓只读预检

- StockQA CodeGraph索引健康；`ProviderCascade`定义在`src/utils/llm_integration.py`，没有生产调用者，现状是全局provider字符串索引和成功后恢复主provider，不具备逐题provider/model策略。
- 实际公开路径为`main_with_llm.py` → `LLMRunner.run()`/`_run_single_company()` → 单个固定`LLMProvider` → 每题`QAEngine`处理 → provider请求。`LLMConfig`读取已有`llm_apis.json`中的provider、model和密钥配置，但不提供按用户顺序选择模型或版本化policy的接口。
- 依据Q04及C05契约，外部实现至少要把有序provider/model对接到每题路径、在派发前做能力检查、按有限失败类型切换并让低分/正常unknown立即停止；还需保留策略版本、每题实际模型/attempt、首选槽满等待与请求总上限。PAR-08中的StockWiki设置UI由后续X03/X04负责，本任务不写StockWiki。
- 只读`git status`发现StockQA已有Q01—Q03修改覆盖`src/core/models.py`、providers、runner、CLI及相关测试，且存在`.workbuddy-ai/`、`experiments/`、`nul`、`progress_update.txt`等未跟踪内容。均为用户/既有工作区数据，不清理不覆盖。尚未向StockQA写入Q04内容。


## 2026-09-24 — 剩余审查卡接续

- 在不写外仓产品文件的前提下，已启动两个用户授权的独立审查：C04—C07核对本地契约回执和可重跑测试；Q01—Q03核对StockQA当前快照，只有在测试生成物可隔离且外仓前后状态不变时才运行离线测试。
- Q01—Q03审查者已确认StockQA现有工作树含Q01—Q03修改和预存未跟踪文件，正在先验证测试副作用边界。Q02的LLM-01明确需要真实联网，本轮不调用网络，因此会保持未执行/待审状态。
- Q04已在用户授权范围内写入StockQA指定六个文件，Black检查通过，隔离定向测试116 passed；无真实网络/provider调用，唯一pytest临时根已删除。Q04独立审查正在进行，PAR-03/PAR-08的运行态能力没有因这轮测试通过而宣称完成。


## 2026-09-24 — Q04 StockQA有序模型策略候选

- 在用户对Q04具体范围授权后，仅编辑StockQA的`src/config/llm_config.py`、`src/runners/llm_runner.py`、`src/utils/llm_integration.py`及三份对应测试；保留既有Q01—Q03修改和未跟踪文件，不写StockWiki/company-wiki。
- 配置层支持可选版本化有序模型策略、运行时provider可用性过滤、policy指纹、凭据字段拒绝及原子保存；公开require-search CLI启动时固定策略快照，并在每道逻辑题按顺序路由，只有显式可恢复HTTP失败才fallback，正常答案（含低分/unknown）即停；receipt保留策略版本、模型和路由attempt。
- Black `--check` 六文件通过；StockQA隔离定向suite `116 passed`，覆盖公开CLI的429切换、低分停止、400不切换、搜索能力预检、服务器失败attempt上限及配置版本/顺序快照。仅mock HTTP发送边界，不产生真实网络请求；pytest cwd/basetemp/log在唯一TEMP根隔离，结束后TEMP根无残留。
- 原始日志`docs/implementation/contracts/validation-Q04-stockqa-targeted-final-r2-2026-09-24.log` SHA-256 `ADD8A1AD723286E4237BD94F0F07A45AB145F85E43EC8AA0BF27F4B3F78E5FE3`。最终StockQA源码hash与六个目标文件状态已留待Q04回执绑定。
- Q04独立审查仍pending；现有候选仅默认下轮生效，没有证明PAR-03并发槽满等待、实时变更在派发边界作用于未派发题或PAR-08的StockWiki设置/CLI/runner共同配置闭环。以上未覆盖项继续开放，不能以116项通过标为Q04 verified。


## 2026-09-24 — C04/C06/C07 独立审查整改

- C04初审JOB-08反例已纳入固定测试：WorkItem公共semantic validator拒绝重复attempt ID及`uncertain_attempt_id`未指向唯一已持久化attempt；新增的transition入口先验证完整WorkItem，再从其attempt记录读取对账身份。
- C06初审内容寻址反例已纳入公开validator：对观察payload、observation ID、item ID、package hash与package ID逐项重算；针对正文、哈希、ID和package metadata的单点篡改测试均fail closed。
- C07初审full readiness组件hash反例已纳入响应validator：从组件实载状态、同release gate/live证据重新推导full readiness，拒绝少组件或实载hash不匹配的自报full响应。
- 三个新增固定反例在实现前复现失败；定向隔离测试`51 passed`，本地`tests/`全套隔离测试`222 passed`。定向日志SHA-256 `138C34445D2098C5E4561F199F43E3372FE1CB2B007D87503E4AECEDBC591361`，全套日志SHA-256 `CA1C95B5F75BE5422459B4C236071F3D321DDF33502511616CCE7F27EA514833`；红测日志也保留在contracts目录。两次测试的TEMP根均在完成后删除。
- 独立follow-up审查确认C04/C06/C07三项阻断均已关闭，复审范围内的本地离线契约可标记verified。回执现绑定审查报告SHA-256 `2798E10580F3A782535BB06738DB2ADB6C3187211B2D95FE682E413D0CDB91E5`；未声称生产worker、跨仓集成、数据库、跨进程协调或live E2E通过。
- C05初审亦确认可在本地离线契约范围标记verified，绑定报告SHA-256 `0E9C0A9E81C5E60D67851A97BC35EFD2D63FA34649C3B4469F2F88D202174301`；provider真实fallback与运行时预算仍由owner集成任务验收。


## 2026-09-24 — Q04 B1/B2修订与复审快照 r3

- 在用户明确扩大的StockQA文件范围内完成Q04复审阻断B1/B2修订：保存与加载均做完整v2策略校验并失败关闭；传输错误仅保留允许名单中的provider error code和解析后的Retry-After秒数，不落原始body/header；级联区分普通限流、已识别配额错误、认证失败与5xx重试，遵守Retry-After、attempt总上限，并在单次run中持续冷却配额组/禁用认证路由。
- StockQA隔离定向测试131 passed；Black检查8个源码/测试文件通过；git diff --check通过（仅行尾提示）。HTTP发送边界由mock替代，无真实网络调用/API费用；唯一TEMP/CWD/basetemp根已在测试结束后删除。最终日志：`docs/implementation/contracts/validation-Q04-stockqa-targeted-final-r3-2026-09-24.log`，SHA-256 `9AAAD87C77E0D11BAFB62949F4F79A2874C9EF961CB51FB15B1DB4CF91EBC76E`。
- 完整源码/测试/schema/log hash已绑定`docs/implementation/contracts/receipt-Q04.json`；StockQA外仓原有Q01—Q03和用户未跟踪文件仍保留。`src/providers/llm_provider.py`存在StockQA原有Q01—Q03差异，已纳入r3快照；本次Q04实现未改动该文件；未增加依赖。
- Q04仍为`implementation_partial`，follow-up独立审查精确快照pending。PAR-03跨进程共享容量/配额协调、LLM-10运行中policy热更新边界和PAR-08 StockWiki同一配置版本闭环仍未完成；未写StockWiki。


## 2026-09-24 — Q04 schema一致性修订 r4

- r3独立审查确认B2范围通过，并发现B1在`pricing_ref`条件、200字符上限和comparison启用预算三处仍接受schema拒绝策略；20个固定参数反例先复现20/20失败，再在修复后20/20通过。unit和public CLI两套测试policy fixture现通过Draft 2020-12 schema验证。
- validator现在要求verified_rate_card有非空pricing_ref、全部受约束ID/model/reference不超200字符、开启comparison时预算为正且请求数至少1；`.gitignore`仅为获批的`src/config/quick_scan_model_policy.schema.json`加精确例外，`git status`已展示该文件。
- 最终定向suite `151 passed`，Black 8个源码/测试文件与diff hygiene通过；无真实网络/API调用，唯一TEMP根已删除。日志`docs/implementation/contracts/validation-Q04-stockqa-targeted-final-r4-2026-09-24.log` SHA-256 `5E97508A494D8984E9B21F1C8AF03BFAD1ECBCC5566026ABE912086364FA6E2A`。
- r3独立报告`docs/implementation/reviews/Q04/follow-up-review.md` SHA-256 `4CBB3172D9332C2C16982E4A4E610F7CEE4BC124FC7AE4A430C3163B889DC263`；报告发现已整改，r4新快照等待独立复核。Q04整体继续partial，PAR-03、PAR-08、LLM-06剩余持久恢复/限时等待和LLM-10未声称完成。


## 2026-09-24 — Q04 r4 独立复审收口（限定范围）

- 独立reviewer确认r4所有列出的StockQA源码/测试/schema/.gitignore哈希与HEAD相符；B1三项schemafinding关闭，B2关键路由无回归；151项定向测试、8文件Black、schema fixture和diff hygiene通过，未改外仓。报告`docs/implementation/reviews/Q04/final-r4-review.md` SHA-256 `F61AD1B64652F0F72112AFAC72BD27D4AF46F8F08EB9A00095E9549867C59100`。
- `receipt-Q04.json`已绑定r4文件/日志哈希与r3/r4 review历史。仅将已授权B1/B2范围记为verified；Q04总体仍partial，不把schema校验与离线fallback测试等同于PAR-03/08、LLM-06/10或生产能力交付。
- 用户另授权Q01/Q03固定反例整改文件范围；下一步使用先红后绿的parser/公开CLI回归，并继续保持外仓限定范围。


## 2026-09-24 — Q01/Q03 parser反例整改 r1

- 按用户授权仅扩展StockQA parser、parser tests及公开CLI integration tests。原生协议只认顶层评分字段；description若是自带id/status/score的完整JSON旧答案对象则fail closed，不把外层兼容5分当成正式分数；direct JSON和regex兼容提取都用object_pairs_hook拒绝重复JSON键。无需修改AnswerGenerator/runner生产逻辑，结果仍通过既有null/error/receipt路径。
- 独立固定反例在实现前8/8 CLI/parser失败；另一个非strict重复键反例1/1失败。修复后9个固定反例全部通过，含4个公开CLI端到端测试；选定Q01/Q03加Q04共享回归suite 272 passed，Black 14 files、diff hygiene通过。没有真实网络/LLM/公司数据；运输边界mock，隔离TEMP根均删除。最终日志`docs/implementation/contracts/validation-Q01-Q03-regression-final-r1-2026-09-24.log` SHA-256 `1DFBECBAFD93214C556041D9B4A6260E09FD2548FF758F2575AD0FF0970867B8`。
- 新增`receipt-Q01.json`和`receipt-Q03.json`绑定当前源码/测试/日志hash；两卡保持implementation_partial，follow-up复审pending。Q04 receipt保留r4 review快照，并记录共享CLI文件后续Q01/Q03变化及272项复测。


## 2026-09-24 — Q01/Q03嵌套协议兼容与重复键绕过整改 r2

- 独立r1复审指出F04：parser拒绝了内外一致的标准嵌套评分答案，导致S02消费者接受E2E失败；并扩展F03：重复question_id外层JSON在默认兼容入口可被绕开，从metadata误取9分。新增3个StockQA parser固定反例和1个公开CLI反例；修复前parser反例3/3失败，本地S02 CLI到消费者E2E 1/1失败。
- parser现在校验嵌套answer的status、score、题目ID与外层一致，保留合法S02结构；兼容提取只扫描完整外层JSON，重复键候选停止fallback。只改动用户已授权的parser、parser tests和公开CLI test。
- StockQA parser/CLI定向文件51 passed；Q01/Q04共享suite 276 passed（显式加载asyncio插件）；本地全量222 passed、139 subtests通过。日志SHA：`0B8D0854B0D1F10112441911A89DD1A5668764EF72F862D1BE0FD1AB9FD4F04B`、`DB02BABCAC96766874A09AED514C35A1BDD9EAB6D695CD97785B1DA09D4F44F7`、`3B76F40C9E69BD51620F9E1E949DCB4C349B6F8F761154CDF6C2557BF03FCD1B`。
- Black目标文件与git diff --check通过；`-B`、pytest无缓存，测试CWD/basetemp放在唯一系统TEMP根并于运行后删除，无live网络、LLM请求或API费用。
- r2文件hash已写入Q01/Q03回执并请求独立follow-up；当前仍是实现候选，未标verified。Q02 live及Q04 PAR-03/PAR-08/LLM-06/LLM-10边界按原计划开放。


## 2026-09-24 — Q01/Q03 r2 独立复核通过

- 独立reviewer精确核对parser、unit test、public CLI test三项SHA，并对本仓r0/r1固定反例、StockQA owner tests及S02 CLI→consumer E2E独立重跑：166项selected和1项consumer通过。F01–F04均按固定反例关闭；结论仅覆盖获批的离线parser/CLI范围。
- 审查报告`docs/implementation/reviews/Q01-Q03/r2-follow-up-review.md` SHA-256 `39325AB05687514F4EFE1DDF7A3EE15ACA168BC33E870C4F3E545E375C703127`。纠正审查wrapper的Git dubious-ownership调用后，独立执行再次确认2,594条目哈希及Git工作树状态无漂移；唯一TEMP根清理完成。
- Q01依赖G0已完成，离线score/null parser验收及独立复审闭合，receipt-Q01标为verified。Q03代码修复范围review通过，但计划依赖Q02，故receipt-Q03保持implementation_partial。Q02真实OpenAI web_search未做；Q04其余PAR-03、PAR-08、LLM-06、LLM-10范围仍开放。
## 2026-09-25 — Q02离线核验与live门控

- 只读检查StockQA现有工作树；未改外仓文件、未访问模型服务。OpenAI配置无有效凭据，`OPENAI_API_KEY`与`STOCKQA_OPENAI_API_KEY`均未提供；live测试显式依赖`STOCKQA_RUN_LIVE_E2E=1`和`STOCKQA_OPENAI_API_KEY`。
- 当前OpenAI官方文档确认Responses API应使用托管`web_search`；`tool_choice="required"`可要求调用搜索，`include=["web_search_call.action.sources"]`返回来源元数据。GPT-4.1 mini支持Responses端点及web search；搜索工具按调用计价，因此live测试是一条API请求，实际内部搜索调用数及费用可能变化。来源见`findings.md`。
- 本轮隔离运行`test_llm_client.py`、`test_search_provider.py`、`test_quick_scan_cli.py`共63项通过；HTTP边界使用mock，无实时网络。单独运行live文件时，清除相关credential/opt-in环境变量后按预期1 skipped；此skip明确不算LLM-01通过。两次唯一系统TEMP根均已删除。日志：`validation-Q02-offline-2026-09-25.log` SHA-256 `F7623C1C0A6A6AFC6BBF4B2739EC4A04740EDDF5530466C1D5FC0B09DB77246B`；`validation-Q02-live-gate-r2-2026-09-25.log` SHA-256 `DC83879A76E7EB4B215BF98EFC8A73426A12796A81004308A92ABCF6C453A9A0`。
- 独立审查报告`docs/implementation/reviews/Q02/offline-review.md` SHA-256 `532B1A52659B1C703F7D011BB656B90617F257A2D591C1A7E3662A0883048065`；独立审查选择五个StockQA测试文件报告110 passed。当前已请求审查agent补齐原始输出与执行元数据，完成后重绑报告哈希。
- 独立审查确认LLM-02离线行为、LLM-06能力预检及HTTP 400不fallback；发现P1：所有route不可用时只返回provider_unavailable/最后错误，没有retry_wait和持久恢复语义。LLM-01真实搜索事件仍无live证据，Q02保持`implementation_partial`。新增回执`receipt-Q02.json`记录当前外仓快照与未决项；Q03依赖不变。
- 追到契约层还存在状态归属差异：LLM-06要求运行级`retry_wait`，C05文本使用`waiting_for_provider`，C04 WorkItem enum不含`retry_wait`。实施前需冻结run/dispatch状态与C04 work状态的映射，并为暂时额度/限流和需要修改配置的不可用情形分别定义恢复资格，避免加一个无法兑现的通用定时器。

## 2026-09-25 — Q02继续：独立审查证据与MiMo探针

- Q02独立审查agent已补齐可复跑的原始stdout和隔离元数据；五文件独立suite为110 passed。最终报告SHA-256更新为`A1869A987B83BFF3FC7C972CF4A65DE44E3571BA9E0551E8190C6A8958B9BEA5`，stdout SHA为`EC2939EBB39C818C307151239DF0A51239B24BB39CBD2343CB093CE6F7AE22EE`，evidence JSON SHA为`66C8DB4CC933889EE62F079492A4C42B5218FF4897C0CFCEC64829793628D96B`。Q02回执尚待重绑这些最新哈希。
- 用户要求验证MiMo联网搜索后，使用环境变量内的密钥向指定Token Plan endpoint发出一次`mimo-v2.6-flash`、`max_keyword=1`的真实搜索请求。服务端返回400，明确指出账户`webSearchEnabled=false`；无回答、来源或搜索usage。该结果记录为配置阻塞，不作为LLM-01通过；未读取/输出密钥值。当前较大的实现目标已恢复，不等待插件配置才推进离线工作。
- 下一步先由独立审查确认run级`retry_wait`、`waiting_for_provider`和C04 WorkItem/`next_retry_at`的映射，再在已获准的StockQA Q04局部文件范围内修复可由provider层负责的派发结果语义并补充失败/无搜索能力边界测试。需要新的持久化拥有者文件时，另按既定外仓授权边界处理。

- 纠正上条MiMo解释：用户确认联网服务插件早已开通，Token Plan调用返回`webSearchEnabled=false`与用户设置相矛盾，根因仍未明，不能归因于用户未开通。官方条款还明确Token Plan套餐key限编程工具使用、禁止用于非编码自动脚本/自建后端；不将`MIMO_PLAN_API_KEY`用于公司快扫。[条款](https://mimo.mi.com/docs/tokenplan/subscription)
- 改用环境中已存在的按量付费`MIMO_API_KEY`，向官方`api.xiaomimimo.com`发出单关键词真实联网搜索请求，HTTP 200并返回Microsoft 2025 Annual Report来源，`web_search_usage`显示1次工具/1个页面；因220 token上限返回`finish_reason=length`且内容为空。该直连探针证明搜索来源能力可用，不等于StockQA CLI的LLM-01 E2E通过。脱敏记录为`validation-Q02-MiMo-paygo-probe-2026-09-25.log`。

## 2026-09-25 — MiniMax-M3 实际联网搜索探针

- 用户重启Codex后，当前进程可读取`MINIMAX_API_KEY`；key值未显示、写盘或加入请求日志。
- 首次尝试`api.minimax.cn/v1/responses`返回HTTP 200和M3文本，但响应无`web_search_call`与引用注释，故只算文本接口通过。按MiniMax官方Server Tools接口试`api.minimax.io/v1/responses`，服务以401 `invalid api key (2049)`拒绝当前凭据。
- 按公开开发者报告核对区域key/host匹配后，使用大陆兼容host `api.minimaxi.com/v1/responses`成功：HTTP 200、`completed`、output含一个`web_search_call`，并返回Microsoft官方FY2025业绩来源；M3答复FY2025营收2817亿美元。response报告9739 input、263 output、10002 total tokens，无货币费用receipt。
- 公开报告指出大陆key发往国际host会因区域不匹配返回2049；这与本机实测一致。[CodexBar issue #1615](https://github.com/steipete/CodexBar/issues/1615)。MiniMax官方Server Tools说明响应应包含搜索调用与引用结构：[Server Tools](https://platform.minimax.io/docs/guides/server-tools)。另有用户针对MiniMax Anthropic Messages端点报告web_search调用问题，但这是不同接口，不能外推到本次成功的Responses-compatible路径：[MiniMax-M3 issue #23](https://github.com/MiniMax-AI/MiniMax-M3/issues/23)。
- 脱敏API测试结果记录在`validation-Q02-MiniMax-probe-2026-09-25.log`。这是直接provider live smoke，不是StockQA CLI集成或完整单公司快扫；Q02/LLM-01仍保持未验收，直到获批路径上的公开CLI E2E跑通。

## 2026-09-25 — 提供商配置与 DeepSeek Anthropic 搜索

- 新增`examples/provider-connectivity-profiles.json`和严格schema，按端点记录MiMo、MiniMax、DeepSeek模型名、协议、区域、环境变量名、能力状态、脱敏调用回执与官方文档。未写入任何key值；模型优先级继续单独由`examples/model-policy.template.json`管理。
- DeepSeek官方文档确认Anthropic兼容地址为`https://api.deepseek.com/anthropic`，模型为`deepseek-flash`；Anthropic兼容API对`server_tool_use`和`web_search_tool_result`有支持声明，Claude Code集成文档明确说明可通过DeepSeek API执行服务端网页搜索。OpenAI Responses API列出的内置`web_search`仍被忽略；两种协议的能力不可混为一谈。
- 用户问是否尝试Anthropic兼容接口后，向`/anthropic/v1/messages`发送一次公开DeepSeek API文档查询，HTTP 200并返回2个`server_tool_use`和2个搜索结果块，来源包含DeepSeek官方文档；usage报告4,808 input、436 output及2次搜索请求。请求只设`max_uses=1`但观察到2次服务端搜索，限额未验证通过，且无货币费用receipt。
- DeepSeek `chat/completions`文本探针返回HTTP 200、1 output token；此前OpenAI `responses`内置搜索探针没有搜索事件。脱敏调用记录合并在`validation-Q02-DeepSeek-probe-2026-09-25.log`。
- 新增provider配置schema/回执文件绑定测试、密钥字段/字面值拒绝测试，并确保所有profile不能标为StockQA CLI通过；定向测试现为8项。
- 本仓`tests/`完整suite最终230 passed、139 subtests passed；默认从仓库根收集时会误收两个留存的StockQA复审测试副本并因缺少其上游`main_with_llm.py`/`src`路径而collection失败。Q02回执仍将直连搜索和StockQA集成分开记录。
- 按此前r5独立审查的P2意见，在已授权的StockQA route文件内用回归测试覆盖短`Retry-After`：先见一条隔离红测（primary本应重试却fallback），再实现每路由一次、最多2秒的非长阻塞内联重试；24小时Retry-After仍快速fallback。精确文件SHA绑定的独立TEMP suite 76 passed，API变量/Live opt-in已清除，sandbox完成删除；Black与git diff --check通过。
- 当前Q04 r6候选待同一独立审查agent只读复核；r5的P2不再是当前已测行为。P1公共JSON serializer遗漏dispatch_outcome、LLM-06持久化恢复、PAR-03跨worker额度和PAR-08 StockWiki接线仍开放，未扩大外仓写入范围。

## 2026-09-26 — 组合式题库设计与计划1.7.0

- 用户提出基础、行业、成长/困境及未来投资视角模块的按公司组合、单模块扩题与路由器。只读审查确认现有48模块/222评分题和61事实题已经有基础组合；半导体扩张公司基线quick 28题/full 34题、24个核心构念均保留。无需另起第二题库。
- 新增`docs/modular-question-bank-design.md`，固定客观分类与投资视角区别、独立模块版本/发布锁、题义与prompt指纹、旧版可读、诊断/扩展分层、模糊路由、人工覆盖、跨期同题篮比较、按新增/失效题补扫及跨仓职责。
- 计划增补S04/S05/S06/Q13/W15/F06/U04七张卡和MOD-01—13十三个正反/故障/live场景；L03/W14/F02/U03/X07/X09/G6的依赖接通，X10绑定有限真实模块E2E。计划版本1.7.0，81卡/187场景。该包仍是spec，不代表七卡已实施或真实数据已测试。
- 一次性计划脚本首次遇到既有F05 ID冲突，断言在写入前退出；改为F06后成功。`scripts/implementation_plan.py validate`返回planning_valid=true；`test_implementation_plan.py`原41项通过，新增计划保护测试待最终复跑；`git diff --check`无补丁错误。临时增补脚本将在校验后移除。
- 独立只读题库审查指出：新增行业只登记catalog会在渲染时缺口径而失败；当前旧manifest强制当前全局版本；全局口径文件hash会使无关模块影响方法标记，公共prompt变化又可能漏出可比判断。这些都被加入新设计和MOD反例。Q04 r6独立复审代理在启动前遭Codex服务401，未产生结果；不能算审查通过。

## 2026-09-26 — S04 模块发布离线契约完成

- 新增评分模块、不可变发布锁和路由决策三个schema及`scripts/module_contract.py`，对现有48模块保持兼容；冻结24个核心ID、类型替代与退休题墓碑，同ID任何题文/锚点修改均拒绝，新增题用新ID和`supersedes`。
- 14项模块契约测试覆盖MOD-02/03/04/07的离线部分、真实现有模块形状、合成归档读取及篡改拒绝。独立审查指出并复核修复了同ID改题、退休ID复用、核心污染、重复替代、人工覆盖TTL与发布锁结构校验等绕过；最终独立14项测试及22项内存行为验证均通过，无剩余P0/P1/P2。
- 本仓最终全量`246 passed, 148 subtests passed`，无跳过、无网络；日志`validation-S04-final-full-2026-09-26.log` SHA-256 `5FACD077F4E115C841778F816034575D8592E56EAB20EA2C3D7CAF759654CEAC`。题库校验仍为48模块/222题，计划校验为81卡/187场景。精确源码哈希和审查边界见`receipt-S04.json`。
- MOD-03真实manifest比较链、MOD-07实际历史入口、可信`decided_at`/墓碑运行时绑定仍属于S05/S06；S04只标记离线契约完成。现并行推进本仓S05，外仓保持只读。

## 2026-09-26 — S06路由预审、计划1.7.1与Q04复审重启

- S06只读预审发现旧`validate_profile`必须有完整类型/阶段/置信度，不能直接表示不确定路由；保留旧入口，计划新增以已验证发布包和路由决策驱动的部分问卷入口。现存`cyclical`虽在`stages`题库目录，路由时须算正交周期属性。旧模块缺机器化`activation`，需发布版本化规则，不能无规则自动选用。
- S04路由schema还不能表达未请求投资视角的政策性拒绝、搜索不可用时的无来源`uncertain`；执行历史人工覆盖须按当前UTC时间重新检验到期。设计文档、S06任务和MOD-01/04/05场景已细化，计划修订为1.7.1，仍为81卡/187场景。S04审查回执保留其原快照；后续schema变化由S06审查。
- Q04 r6独立复审已从此前Codex服务401恢复。原76项隔离测试通过，但新红测复现首选429或搜索失败、备用模型实际成功得8分后`dispatch_outcome`仍误为`retry_wait_recommended`/`setup_required`。审查者仅使用唯一TEMP副本、已删除，没有仓库写入或真实API。原获批StockQA路由源码/单测内做r7修复；公开serializer遗漏字段的`src/core/models.py`不在原授权范围，暂保持只读并单独处理。
- 对上述StockQA四文件的首次写入被自动审批复核拒绝，理由为未识别到精确授权；代理未改文件。随后用户明确授权修改StockQAbyLLM所有文件，只需事先报备。我已在对话中报备`src/utils/llm_integration.py`、`src/core/models.py`及对应两份unit tests，现继续r7修复，不扩大到StockWiki/company-wiki。
- 获批后的Q04 r7仅改报备的四文件：备用模型最终接受答案优先于首选路由旧失败，公开`execution_receipts`保留`dispatch_outcome`。新增3条反例先红后绿，相关unit/CLI隔离suite 113 passed；Black与diff检查通过，无live API，唯一TEMP根已删除。当前为实现候选，独立r7复审进行中；Q04整体仍partial。
- S05本仓实现候选现有48模块/222题内容寻址基线归档、冻结上下文/答案/评分schema、逐题定义/语义/prompt哈希、显式路由入口和预算延期清单。首轮全量发现旧standard-answer manifest缺资源hash字段，修复后20项目标回归及全量258 passed/148 subtests通过；题库校验48/222。历史渲染器代码不可用时归档元数据可读，但prompt验证失败关闭。当前独立S05审查进行中，尚不标verified。
- Q04 r7审查确认原两个P1在113项快照下关闭，但补出P2：首选429、备用`no_results`形成终局`insufficient_evidence`时仍被旧失败标为等待。依C05有效未知应结束本轮fallback，已在同一四文件范围补红测并整改；旧r7复审快照作废，等待新哈希复审。
- Q04 r7最终四文件hash独立复审通过：隔离114项、真实代码路径的评分8/无结果/超时不明公开回执探针均符合终局状态；报告`docs/implementation/reviews/Q04/r7-independent-review-2026-09-26.md`。Q04整体仍partial，后续持久化恢复等未被此次结果覆盖。
- S05独立只读审查在候选258项绿测外复现五个缺口：跨公司standard观察误报方法变化、standard builder接受篡改后重算哈希的题面、旧归档答案被当前schema拒绝、连续两次major退役被发布器误拒绝、LLM候选擅自启用manual lens。当前S05保持`needs_revision`，待固定红测与新快照复审，不标verified。
- S05 r2新增红/绿回归后全量264 passed/148 subtests；独立复核确认原五项均关闭，但又复现2项P1/1项P2：答案协议资源变化未改变语义方法、观察自报semantic可伪造且全删绑定可降为legacy、旧包仍能导出新standard问卷再在build阶段失败。候选日志`validation-S05-r2-full-2026-09-26.log` SHA-256 `395B30F1675484B2D733ED851360DFA85F7D1FEBE544387955795C73B0EC7572`。S05继续needs_revision；后续要明确自包含记录无法在无外部可信ID时识别全面重写，生产接入需严格发布模式。

## 2026-09-26 — F06事实模块发布预审与计划1.7.2

- F06只读预审确认`facts.json`为61个唯一字段（24通用+37专用）。S04/S05评分锁要求24核心和评分锚点，不能将事实题伪装成评分common；F06需另建factrel_/factpkg_不可变发布锁，复用安全归档/版本原语，在manifest关联S06评分路由并由X07统一发布集绑定。
- 计划1.7.2扩充F06允许文件范围、独立事实发布/历史兼容/分部边界/外部省略score内部null规则，细化MOD-11/12、FACT-01、MATRIX-08固定正反例；F01改为只审查既有61题与兼容导出，不提前建另一套catalog。81卡/187场景结构校验、43项计划测试及diff检查通过。F06实际实施仍需G3/F01/S05依赖通过，本次未改事实题或调用模型。

## 2026-09-26 — S05 r3、MiniMax公开CLI与计划1.7.3

- S05 r3修复前轮独立审查的2项P1/1项P2：标准回答协议资源纳入题义指纹；观察从冻结发布包和上下文重算语义；新导入要求published模式和独立保存的预期观察ID；旧包不能先导出注定无法入库的新standard-1问卷。最终还阻止v1包冒充schema1.1观测。新current包为`pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f`，旧包保持字节不变。主代理对最终快照跑本仓全量`267 passed, 148 subtests passed`；日志`validation-S05-r3-final-full-2026-09-26.log` SHA-256 `C0B7C99D7A2A7DC49CA392065FAD3D3293A8E6363C8E1BE4FCF22B5B3883F2D4`。独立r3复审中，S05暂不标verified。
- MiniMax-M3第二次、最后一次Microsoft单题公开CLI live由实施代理报告`1 passed/9.55s`，确认completed web_search_call、来源、response/attempt/search回执及唯一TEMP清理。第一次为`search_status=unverified`；两次之间题面明确要求搜索官方FY2025年报，不能把成功单独归因到解析器。脱敏实施摘要`validation-Q02-MiniMax-cli-live-2026-09-26.json`标明未独立重跑、无原始响应/费用回执；配置样例现把大陆MiniMax端点记为单题CLI已实测，不推导批量可用。
- Q02独立只读复核在唯一TEMP根跑75项离线测试通过，无live；复现配置键`openai`指向MiniMax实际端点时公开结果仍错标`openai`，并指出live断言未直接要求选中搜索事件与公开来源相交。报告`docs/implementation/reviews/Q02/minimax-cli-independent-review-2026-09-26.md` SHA-256 `3D6017F1EAFA430ACB6C15BE6CA3D50C0E3B160ED4AAFA0A57620D8D26DE9FD5`。已向用户报备StockQA追加源码和测试范围，实施代理正在离线修复，当前Q02仍partial且无新live。
- S06只读预审报告`docs/implementation/reviews/S06/preparation-2026-09-26.md`发现旧路由schema无法表示无搜索空来源，三个行业full仍被旧profile拒绝，预算24会把困境/恢复六题全延期，48模块无机器activation。按报告扩充S06允许文件/五组反例、冻结默认物质性和必问题策略；W05计划增加published严格导入与逻辑执行键对账，版本升1.7.3（81卡/187场景）。`implementation_plan.py validate`通过，计划/提供商配置定向53项和22子例通过，`git diff --check`无补丁错误。
- StockQA实施代理进一步指出本仓S02消费者仍强制逐题provider等于顶层provider且request_id非空；这会拒绝MiniMax无HTTP request ID和多厂商批次。已启动独立只读预审，待S05复审后在本仓以固定反例修复，不能把当前MiniMax CLI live通过误称跨仓导入通过。
- S05 r3独立复审最终通过：54项定向测试、31个独立反例均通过；132文件审计中S05关联130项未变，另两份计划文件因主代理并行更新单列。报告`docs/implementation/reviews/S05/r3-independent-review-2026-09-26.md` SHA-256 `26C0343F53BA9B10926148FB629D2BEA6E62C684ECB532FA4EE69882750E4FBD`；`receipt-S05.json`仅标本仓离线发布、归档、拼装、观察比较通过。严格入库的外部ID可信锚和跨仓接线不在此范围。S02消费者和S06路由分别由代理在不重叠文件上推进。
- 计划发现Q02早于Q04/Q08，却共用LLM-06“所有模型不可用→retry_wait”整条验收；若把持久恢复当Q02门槛，将产生阶段依赖环。计划1.7.4新增LLM-11并由Q02负责首提供商能力/坏请求/真实厂商回执，LLM-06留给Q04运行级结果和Q08持久恢复；81卡/188场景结构校验、46项计划测试通过。S05回执保留其1.7.3审查快照，不重写历史。

## 2026-09-26 — Q02/S02增量、S06首段与W01落地

- Q02 StockQA真实厂商归属改为从可信端点/响应逐题记录，跨厂商fallback批次顶层厂商/模型为null；同步`requests` 302伪完成搜索被独立发现并修复，异步HTTPX同样显式要求2xx。StockQA隔离unit+integration 588项、独立焦点203项通过，前次P1关闭。最终代码的MiniMax单题live在受限沙箱两次HTTP前ConnectionError；网络放行后HTTP 200/completed但未给出可验证搜索链，正确保持unverified。Q02仍partial；结构化profile升级1.1.0区分旧版live通过与最终版未验收，证据见`receipt-Q02-minimax-final-revision-2026-09-26.json`。
- S02消费端支持MiniMax空request ID及混合厂商逐题实际归属，现代级联缺dispatch、缺末次真实厂商、route trace失败却声称完成、前序路由伪装直连等反例均拒绝；StockQA单厂商直连旧形状仍可用。目标49项/107子例及独立复审通过；`receipt-S02-minimax-compat-2026-09-26.json`为S06后续改动前的精确快照。
- S06冻结策略/证据路线首段完成70项隔离测试、五组故障注入，候选v2包归档但未激活；15%行业入选、20%战略投入、10%连续两期退出及困境恢复必问题已入路由策略。现接入公共问卷与CLI，未将首段误标为完整S06。
- 用户批准W01仅在StockWiki三个文件写入。新增独立SQLite身份/证券/分部/成员基础库，不碰正式YAML或company-wiki；真实TSM.N分类YAML仅只读复制到TEMP测试。独立首审的无约束伪v1库、提交后校验失败、ADR错误基础引用三项先红后绿关闭；目标+旧schema 29项和独立复审通过，`receipt-W01.json`仅标本地迁移/身份范围。W02主档导入、W03成员工具和生产库迁移仍开放。

## 2026-09-26 — W02预案与MiniMax最终版重复验收

- W02只读勘察和四文件精确实施方案见`docs/implementation/reviews/W02/implementation-proposal-2026-09-26.md`。真实company-wiki三地快照有6137/2746/6959条证券，但缺普适跨市场发行人ID、注册国和证券类别；W02先做来源候选、版本化映射和核实桥接，不靠名称/代码自动合并，也不对真实库迁移。已向用户请求StockWiki四文件写入授权，获答复前继续只读准备。
- MiniMax最终源码单题live再做一次获批网络重验，仍为HTTP 200/completed而`search_status=unverified`，没有使Q02通过。官方Responses API只列`tool_choice=none/auto`，当前MiniMax请求按其Server Tools示例仅声明`web_search`，搜索由模型选择；连续失败不能被历史一次成功覆盖。脱敏记录追加到`validation-Q02-MiniMax-final-live-2026-09-26.json`。
- 此次StockQA pytest默认覆盖率配置更新了原已存在且被忽略的`.coverage`、`coverage.xml`、`htmlcov`，旧字节未备份，故保留现状且如实记录副作用。后续运行须禁用coverage输出或在独立副本执行，不能把该次测试称为完全无本地副作用。

## 2026-09-26 — C01 v2、Q08与S06独立审查整改

- C01 v2本仓单对象校验先红后绿：必须由权威来源绑定反查来源命名空间/行键/实体/证券/挂牌字段，verified回执覆盖代码和原始交易所，普通/优先股不能有ADR比率；全仓隔离313项/214子例通过。独立复审局部放行，但不同BND指向同一真实来源行仍需StockWiki owner库事务唯一约束，故跨仓扫描准入未完成。
- Q08第一段持久模型组冷却、跨进程单探针及崩溃保守等待获独立复核；复核又发现共享Requests对付费POST暗中重试和晚到429破坏截止时间。四个固定反例先红后绿，StockQA离线unit+integration 617项通过、独立选定194项通过，唯一TEMP根清理；`receipt-Q08-first-segment-2026-09-26.json`仅限第一段，Q06/Q09和热更新仍开放。
- S06独立复审关闭伪搜索URL及可信困境事实被伪候选压掉的问题。新发现旧router 2.0搜索快照和manifest历史读取受新回执规则误伤，而旧包又可重新导出；已用真实旧发布包固定反例并分离只读验证与新派发门。路由/组合/模块契约94项及127子例通过，独立终审20项通过、无剩余P0/P1/P2；见`receipt-S06.json`。候选包仍未激活，真实跨仓接续另验。

## 2026-09-26 — 可组合演进计划1.8.0

- 用户要求把题库模块化进一步扩展至运行、评分、事实、刷新、提供商、查询和UI；本仓新增`composable-evolution-plan.md`，将不可变观察/费用账本与独立可升级的发布组件分开，并固定每次付费派发前的ScanRecipe/RunManifest。
- 计划清单扩为96张单owner任务卡、231个验收场景（V01—V15/EVO-01—43）。`scoring_only`生产链不依赖F06/G4；后置V13本仓解析事实版、V14 StockQA执行、V15 StockWiki生成事实缺口并导入/ACK；pre-recipe旧账本只读适配且不伪造recipe，未决请求先对账。X05统一入口依赖V09/V10，X09离线与X10真实联网E2E-06边界分清。
- 独立只读审查发现并已整改验收倒挂、事实版StockWiki owner缺口、具体lens发布者不清、旧无recipe运行和正常零下载路径。计划校验`96 tasks/231 acceptance_cases/G6`，53项计划测试/34子例通过；本仓正式`tests/`全量`332 passed, 262 subtests passed`（302.99秒），`git diff --check`退出0。根目录不受限的pytest会错误收集历史StockQA审查脚本并因缺StockQA模块中止；正式本仓回归限定`tests/`，不把该收集错误误记为产品失败或通过。
- W03本仓v2身份绑定work/observation和StockQA Q06隔离SQLite待办各完成第一段并经独立局部复审，均未接完整生产链。此次计划变更不执行V01—V15、未调用真实模型、未迁移StockWiki正式库；E2E-06继续`specified_not_executed`。
- 最终只读追核确认EVO-42“新启用3字段且无有效观察”措辞歧义已消除；版本、owner、任务/案例计数一致，终审无剩余P0—P2。Phase 17仅以`complete_for_planning_only`关闭，V01—V15实施状态仍未完成。

## 2026-09-26 — 计划1.9.0增补完成

- 更新tasks.json、acceptance-cases.json至1.9.0：新增V16生命周期、V17纯影响计划、StockWiki W16权威应用、StockQA Q14答案解析、V18升级回放，共5卡22场景；接入G6及X05/X07/X09。
- 更新全项目演进设计及I34—I40；补V17真实V10只读快照输入、legacy_without_recipe证据适配、attempt/search-call/URL归属最小回执，并将跨仓副作用交StockWiki owner卡。
- 独立复审问题已纳入W16与EVO-57—62，且将V16/V17案例限定为各自owner可完成的纯校验/计划输出；更新后implementation_plan.py validate通过（101卡/253场景），test_implementation_plan.py 57项通过，git diff --check退出0。Phase 18仍等待对最新快照的独立只读复审。
- 本轮实际只改invest-quick-scan计划/校验文件；W16和Q14描述未来外仓实施，未改StockWiki或StockQA。未来W16实施仍需用户另行授权。

## 2026-09-26 — 计划1.9.1审查补强

- 独立复审指出Q14解析器release未锁入X07/X09、双worker窗口缺少CAS反例、兼容门可能挡住旧attempt结算，且W16信任自签plan hash不足。均已细化任务边界、验收预期和跨任务依赖。
- 新增EVO-63双worker屏障竞态、EVO-64实际解析组件hash闭包、EVO-65旧冻结attempt安全结算、EVO-66伪造plan扩域反例；约束新增I41—I43。
- W16现在要求实际release与当前权威快照重算影响范围或核验绑定完整输入的可信owner回执，并在单一事务CAS重验水位；新兼容门仅阻止新付费work，先安全结算旧账本。
- 计划清单更新为101任务/257场景/43约束、版本1.9.1。`implementation_plan.py validate`通过；计划定向单测59项通过；`git diff --check`退出0（仅有工作树既存CRLF提示）。对最新快照的独立复审仍在进行；未执行外仓写入或生产/live测试。

> 上述记录反映1.9.1阶段结论。其中“可信owner回执”替代确定性重算的表述由1.9.2纠正：当前W16必须使用hash匹配的固定V17实现和当前权威快照重算，不存在未定义的签名回执替代路径。

## 2026-09-26 — 全计划独立复核与1.9.2收口

- 对最终102张任务卡/289个场景的依赖与引用做全量校验；独立复核并重点审查owner本地验收与后置全链归属、可组合演进、release lifecycle/active pointer、W16事务CAS、Q15 POST前围栏及旧attempt恢复。没有发现依赖环；复核发现并修正了多处前置任务完成门依赖后置集成行为的问题。
- `acceptance-cases.json`为跨任务用例增加`requires_tasks`约束；校验器验证任务存在且所有声称该用例的owner任务必须依赖其所需前置任务。新增未知任务/非法形状反例，避免将局部测试标作完整行为通过。
- 固定W16只由已安装hash匹配的V17实现及当前权威快照确定性重算，不接受自签hash/未定义签名回执。候选发布只读预览；active指针单独原子维护，指针切换不隐式改变component lifecycle。回退资格和CAS全量输入均有具体验收。继续审查发现在W16 fence与Q15本地send_intent间存在分布式崩溃窗口，现明确W16唯一拥有permit schema、permit按attempt单次绑定；permit后/send_intent前崩溃POST必须为0且不能重用，send_intent后响应未知只做对账。
- W16去掉重复Q15围栏步骤，owner-local完成描述不再绑定易错的文字case计数；EVO-66的信任根描述与决策表/演进说明对齐。版本和数字统一为1.9.2 / 102 tasks / 289 cases / 48 invariants。
- 验证：`python -X utf8 scripts/implementation_plan.py validate`通过（102卡/289场景/G6）；`python -X utf8 -m unittest discover -s tests -p test_implementation_plan.py -v`为63项通过；`git diff --check`退出0，只有既存文件换行风格警告。这只是计划结构/回归，不是产品验收；没有外仓写入或live API调用。审查报告：`docs/implementation/reviews/PLAN-1.9.2-review.md`。
- 根据用户本轮指令，实施工作暂停。恢复后从任务清单的未完成项继续，重新确认任何新增跨仓文件的精确授权。

## 2026-09-26 — 计划1.9.3全局复核与收口

- 按用户要求只做计划与实施规格再审；复核模块组合与release演进、各层兼容动作、字段级影响分析、身份/多挂牌、模型/时点可比、低谷/恢复候选、跨项目权责、一键启动、UI和真实数据E2E隔离。当前1.9.3为102任务、322场景、50条约束、G6；全部场景仍为`specified_not_executed`。
- 发现当前任务边界、启动/跨仓交付/测试策略中有旧的单阶段派发措辞，并且测试策略的EVO/LLM场景范围落后一版。统一为`send_intent_prepared → W16 consume_dispatch_permit / durable dispatch_commit → 单次provider POST`，commit之后未知结果阻断新attempt/fallback；将场景范围改成EVO-01—82与LLM-13—18。
- 增加当前实施文档跨文件协议一致性回归；更正一条测试将`given`字符串按字符拼接的误写。过程中新增的反例先失败，按契约补齐任务边界/文档后通过。
- 最终证据：`python -X utf8 scripts/implementation_plan.py validate`通过（102/322/G6，`product_tests_executed=false`）；`python -X utf8 -m unittest discover -s tests -p test_implementation_plan.py -q`通过（68项）；独立清点确认无任务缺少case owner且322项均未执行；`git diff --check`退出0，输出仅为已有文件的LF/CRLF提示。
- 本轮未运行真实公司/搜索API/live E2E，未写StockQA、StockWiki、company-wiki或其他外仓；未把计划检查称为产品验收。完整复核范围、canonical派发语义、未实施风险与后续授权边界见[`PLAN-1.9.3-review.md`](docs/implementation/reviews/PLAN-1.9.3-review.md)。按用户指令，本轮收口后暂停。

## 2026-09-26 — 恢复完整目标并推进S04

- 最新续接上下文恢复原完整实施目标，目标状态为active；不再沿用上轮用户提出的暂停。重新查看当前1.9.3计划、任务回执、S04/S05/S06 owner范围和CodeGraph索引。
- 当前计划S04增加了MOD-14，但S04既有receipt仅覆盖早期MOD-02/03/04，与最新任务case集合不闭合。只在本仓补充`test_mod_14_s04_release_static_contract_fails_closed`，以虚构模块/内存release/artifact fixture固定重复module ID、归档hash不符、module依赖循环、已使用题ID同时声明退役四个反例。
- `python -X utf8 -m unittest discover -s tests -p test_module_contract.py -v`通过，15项，0 skip。独立只读审查agent已启动，回执与任务关闭仍待其结论及整体核验；尚未更新S04为verified。
- 未写StockQA/StockWiki/company-wiki或其他外仓，未调用live/API。下一步完成S04审查闭环，再检查S05/S06当下case是否均有实际测试覆盖。

## 2026-09-26 — 计划1.9.4模块演进与全局边界复核

- 用户要求对完整计划及实施细节做一次深入复核，尤其检查可组合、可演进、向下兼容，并在收口后暂停产品实施。
- S04独立只读审查确认`validate_registry`能拒绝依赖环，但`validate_release`会接受模块归档hash和release hash均自洽的循环依赖包；这是归档读取路径的实现缺口，不能用仅测试registry的MOD-14覆盖。
- 补充明确trusted legacy规则：`module_id + artifact_sha256`须精确匹配受信任固定基线；旧可选`dependencies/conflicts`只在只读适配时按空集合解释。新对象/新字节不可自报legacy，未知基线或历史链断裂时needs_review/blocked。
- 将S04/MOD-14、S05/MOD-16/17、S06/MOD-18拆成归档图、历史reader/legacy链、运行时组合闭包三层。定义`dependencies`为必需传递闭包，`conflicts`为选中集合的无向互斥；release可同时存互斥备选。明确排序稳定与冲突/缺依赖前零模型派发。
- 全局复核矩阵重新核对身份/多挂牌、评分/事实、ScanRecipe、逐字段刷新、model/费用、ReleaseSet、CAS/permit、回退、UI/下游消费者、首次启动和隔离E2E；未发现新的任务依赖环或owner越权问题。
- 计划升为1.9.4：102任务、323场景、50约束/G6。结构校验通过，计划回归最终结果记录在审查报告；所有新旧验收case仍`specified_not_executed`。产品代码、外仓、live/API本轮均未改/未用。
- 复核报告：[`PLAN-1.9.4-review.md`](docs/implementation/reviews/PLAN-1.9.4-review.md)。用户要求本轮结束暂停；恢复从S04归档reader修复开始。


## 2026-09-26 — 1.9.5计划审查收口

- 更新计划证据闭环：receipt普通依赖须为当前v2；仅P01→P00允许只读历史bootstrap context，P01之后重跑P00并生成新v2，不篡改旧v1。P01封存前实现review进入receipt core；封存后sidecar绑定core/validator hash，封存后证据review再绑定core/sidecar，三者不回写封存内容。新增I53、RCPT-03和validator规则测试。
- 结构校验通过：103任务、327验收case、G6；计划单测79项通过；`git diff --check`退出0（仅显示已有LF/CRLF提示）。独立终审确认allowlist双向校验、P00/C01—C07重验顺序与自验日志外置已收口，无剩余P0—P2或新增依赖环。
- 本轮停止于计划/规划校验修改，没有继续产品实现、外仓写入、公司数据、下载或真实API。用户要求终审完成后暂停；最新独立复核和回归均已完成。
## 2026-09-26 — Resume P01 receipt v2 implementation

- User resumed the previously paused end-to-end implementation. Goal status is active; this phase is limited to invest-quick-scan's explicit P01 allowlist. No external repository writes, live model/API calls, or financial-document downloads are in scope.
- Confirmed the project plan is 1.9.5 and P01 owns RCPT-01/02/03. Existing P00 v1 receipt is `docs/implementation/baselines/receipt-P00.json`; it must remain byte-identical and only serve as legacy context.
- Existing `task-receipts.md` defines the required one-way evidence flow: source-bound pre-seal review → sealed receipt core → detached read-only validator sidecar → post-seal evidence review. Sidecar and post-seal review must not be hashed into or written back to the core.
- Inspected existing canonical JSON helper: UTF-8, sorted object keys, compact separators, arrays retained, NaN forbidden. Implementation will give the receipt algorithm an explicit version and use decimal strings for numeric financial values as the contract requires.
- Worktree has extensive pre-existing changes across product/docs/tests. They remain untouched; implementation will use only P01-owned files and will not clean/reset the repository.
- Next: capture exact P00 context hashes, then add v2 schema/verifier and temporary-root tests.


## 2026-09-26 — P01 verifier first implementation and test cycle

- Added the v2 core/wrapper JSON Schema and a stdlib-oriented verifier with canonical SHA-256, exact owner case/assertion checks, source/review binding, dependency handling, legacy v1 classification, and local-root path containment. The detached validation result is emitted only to stdout.
- Added a temporary-root unittest fixture and 15 initial cases. First discovery: the schema regex used an invalid JSON escape; fixed it and added Draft 2020-12 validation in the actual verifier. Second discovery: full plan/catalog provenance hashes were incorrectly compared as freshness gates; removed those comparisons so unrelated task/case additions remain eligible while task/case/global-boundary hashes remain gates.
- The first test command, `python -X utf8 -m unittest tests.test_task_receipts -v`, failed because `tests` is not a Python package. Switched to the repository's actual supported entrypoint, `python -X utf8 -m unittest discover -s tests -p test_task_receipts.py -v`.
- Initial red tests also refined expected behavior: log emptiness must be tested with the referenced hash matching the empty bytes; a stale hash correctly blocks earlier. Updated the test so it reaches the empty-log check.
- Current result: all 15 P01-focused temporary-root tests pass. No real company material or API/network calls were used.
- Next: broaden the matrix, exercise CLI as a subprocess with a stripped environment, finish the contract/examples, then run plan and repository regressions.


## 2026-09-26 — P01 contract and CLI regression expansion

- Expanded hermetic coverage to 17 tests, including the public CLI in a subprocess with an environment stripped of API keys; exact input-tree hashes stay unchanged and the JSON output contains only the detached sidecar fields.
- Tests pass: `python -X utf8 -m unittest discover -s tests -p test_task_receipts.py -v` (17 tests, exit 0). CLI help smoke test also exits 0.
- Tightened the P00 historical-context route to require exactly one plan-allowlisted edge and exact manifest path, a context-only eligibility effect, matching hashes for all entries, and exactly one non-v2 receipt for that dependency.
- Added a fictional, schema-valid v2 example and rewrote/expanded the contract with the exact JSON wrapper, hash rules, output behavior, CLI, path restrictions, and two-stage review process.
- Incident: a PowerShell→Python native pipe passed invalid Unicode while appending Chinese documentation and the untracked contract file was truncated. I rebuilt its full prior contract content from the preceding read and applied the expanded version directly; this is recorded in `task_plan.md`. P00 source files were unaffected.
- Next: validate examples/current P00 manifest, map all 18 RCPT atomic assertions to actual selectors/logs, run relevant plan and full local regressions, then freeze and request independent review.

## 2026-09-26 — P01 expanded verification and full offline regression

- Plan package validation passed: 103 tasks, 327 acceptance cases, G6; validator reports product tests were not executed by the plan validator.
- Full repository offline suite passed: `python -X utf8 -m unittest discover -s tests -v`; 376 tests, 273.498 seconds, exit 0. The suite used existing temporary sandbox/stub tests; no live API or document download was run.
- After one final isolation improvement (the mocked symlink target now lives in its own unique TemporaryDirectory, never a shared temp sibling), P01-specific suite passes 20 tests in 1.721 seconds. Persistent focused log: `docs/implementation/contracts/validation-P01-focused-suite.log`; SHA-256 `ac3b6807a773f5d9566086b535a7bd6a0cecb1feef8e47954c9f86f14330c09e`.
- Verified P00 context manifest entries match current immutable files, including the previously captured original P00 receipt SHA; v1 receipt bytes are unchanged.
- The pre-seal read-only independent review agent is reviewing the implementation. No receipt core is sealed yet; selector-specific logs and snapshot hashes are still pending.


## 2026-09-26 — P01 independent review repair and frozen-candidate retest

- The first independent pre-seal review rejected its then-current candidate with five concrete findings: `plan_version` incorrectly invalidated unrelated receipts; the fictional example placed `test_stage` at case level instead of assertion level and kept an old core hash; protected roots/in-root symlink targets bypassed path restrictions; successful CLI output lacked per-assertion selector/evidence/hash audit data; and the actual subprocess CLI did not include the malicious-command sentinel.
- Fixed those findings; also reject hard-linked evidence before reading. Follow-up review caught a cycle branch that could reference uninitialized task data and possible secret leakage through a crafted selector. Added fail-closed cycle handling, selector redaction/blocking, and actual CLI regressions. A first selector-secret test exposed that `secret=` was not matched; the pattern was corrected and the direct regression now passes.
- Current frozen-candidate focused suite: `python -X utf8 -m unittest discover -s tests -p test_task_receipts.py -v` — 20 tests, exit 0. Plan package validation: 103 tasks / 327 cases / G6, exit 0. `git diff --check` exits 0 with only pre-existing LF/CRLF notices.
- P00 context manifest rechecked: both captured source hashes match; the legacy P00 receipt is unchanged and remains `context_only`. Schema and fictional example pass Draft 2020-12 validation.
- Further final review found a malformed P00 manifest entry could raise `TypeError`, case audit status could mirror a false input claim, and assertion logs were read twice. The verifier now validates manifest path types before set operations, derives case status from assertion validation, and reuses one log audit/read for both sidecar and close gate; regressions cover all three.
- Current frozen five-file implementation snapshot digest: `884d10f9c97a03e1a3ad80044fe2443c8038583341833e377824c52e31667806`. The independent reviewer has been asked to re-read this digest under a new report filename. No P01 core has been sealed.
- A full-suite run remains active but started before this last compact adjustment; the current focused suite and plan validation pass. The full-suite result is intermediate for one-read/status/manifest changes. Next: collect isolated selector-specific logs, incorporate the final reviewer report, then seal and verify the receipt chain.

## 2026-09-26 — P01 path-purpose policy and contract-scope repair

- Reopened final candidate after review identified unconstrained reads inside an otherwise registered root and a generic receipt clause that claimed EVO-83 validation without schema support.
- Implemented read-before-open purpose checks: snapshot refs must match the owner task's `allowed_changes`; test logs use `docs/implementation/contracts/validation-<task_id>-*.log`; review JSON uses `docs/implementation/reviews/<task_id>/`; history and dependency refs use exact allowlisted paths. Sensitive credential filenames are rejected before resolution. Existing safe-root, symlink, hardlink, traversal, type, and size protections remain active.
- Expanded P01 with `test_reference_purpose_and_task_scope_reject_unapproved_files_before_read`, which guards `Path.read_bytes` against ordinary config, provider credentials and `evidence/body.log`. Updated fixture and example paths to meet the purpose policy; clarified in `task-receipts.md` that EVO-83 window metadata belongs to its specialized evaluator.
- Validation: focused suite 21/21; full offline suite 377/377 in 833.870 seconds; plan validator 103 tasks / 327 acceptance cases / G6; `git diff --check` exit 0. No external repository writes, live model/API calls, or financial-document downloads occurred.
- P01 is still unsealed. Next: regenerate isolated per-assertion logs for this exact source/test snapshot, request a new independent review digest, and continue with core, detached sidecar and post-seal review.
- The subsequent r3 independent read-only review found two additional P2 edge cases: policy checks were not repeated on an in-root symlink's resolved ordinary target, and P00 version checking rejected only v2 while accepting v3/unknown as legacy. Both are fixed with fail-before-read resolved-target checks, known-legacy classification, and isolated counterexamples. P01 focused tests pass 21/21. A full-suite attempt on the pre-fix candidate was intentionally interrupted and is not evidence; regenerate isolated logs, freeze a new digest, and rerun the full suite before sealing.

## 2026-09-26 — P01 validation cadence review and sidecar path redaction

- User asked whether the plan causes too many repeated reviews/tests. The shared test strategy already says to rerun the failed case, affected adjacent paths, and the relevant stage regression, not the entire matrix after every fix. Kept atomic acceptance cases, but changed Phase 24 to batch review findings, perform one comprehensive pre-seal review, then run the repository-wide suite once after the candidate is clean. The post-seal evidence review remains a separate major gate because it binds different artifacts.
- The independent review found a possible secret in a test-log filename could be copied into the public validation sidecar. The first sentinel regression was red because applying the selector detector to a whole path treated normal slash-separated segments as one base64-like token; changed it to inspect individual path segments, blank unsafe paths, and return stable `test_log_path_unsafe`.
- Targeted CLI regression and P01-focused suite pass: 22 tests, 0 skips. The repository-wide run started against an earlier candidate and was interrupted after the review finding; its log is not final evidence and will not be counted.
- Current candidate is frozen pending one comprehensive read-only pre-seal review. After all review findings are closed, run the full repository suite once on that exact candidate, then generate assertion-specific isolated logs and continue the receipt closeout.
- The comprehensive review then found one additional ambiguity: duplicate JSON object members were accepted with Python's last-value-wins behavior. `_json_from_bytes` now rejects duplicate keys with a stable blocker; a raw duplicate assertion-status object is covered through both the public verifier and subprocess CLI. Contract text now states the unambiguous-JSON rule.
- Final evidence is complete: P01 focused tests pass 23/23; the final frozen-candidate offline suite passes 379 tests with 0 skips; the plan validator passes 103 tasks / 327 cases / G6. The assertion-specific isolated evidence covers all 23 test methods (18 receipt assertions reference 14 logs), each with a unique run/selector, exit 0, skip 0, and verified cleanup.
- The comprehensive pre-seal implementation review and separate post-seal evidence review both approved with no open findings. The public read-only verifier returns `eligible_to_close=true`; core SHA-256 `950d2c22c29ba279288816a754fd84b7870e3b0fd226a3aadeb8fee56a9fb872`, sidecar SHA-256 `d00f37e16af8c3f505510f8b38e48524a66f4c6e3f5b93330752979696bc880a`, post-seal review SHA-256 `5c6a9759c458d763a5a8d2ee33c1e45732e489ad8eaa63cc95dc646168b8c588`.
- P01 is closed. Next is current-snapshot P00 baseline revalidation; preserve the historical baseline receipt at `docs/implementation/baselines/receipt-P00.json` unchanged and issue current v2 evidence at `docs/implementation/contracts/receipt-P00.json`. No external repository writes, live APIs, or company-document downloads were used.
- To apply the user's cadence guidance consistently, clarified the shared test/review instructions: group related small tasks, run targeted checks per change group, do one full regression after the stable milestone candidate, and batch independent reviews at G0—G6 or other major release/interface gates. Fixes get affected-path retests; added independent reviews are reserved for high-risk or cross-contract changes. The per-task evidence remains auditable, without requiring a separate review round for every small step.

## 2026-09-26 — P00 current-snapshot revalidation

- P01 is closed: the public verifier still returns `eligible_to_close=true` after the P00-owner acceptance correction; the independent pre-seal and post-seal reviews are approved, and the P00 context manifest still matches both original legacy files.
- Corrected the stale BASE-01 expectation. The old 5/8 assertion remains historical; current offline Q01/S02 regression strictly transmits score 8 and keeps unknown/null unscored. The local end-to-end test passed 1/1 using an in-memory HTTP session and an automatically cleaned unique temp root; it did not make a live web search.
- Current local validators pass: score bank 48 modules/222 questions, fact library `ok=true/network_used=false`; implementation-plan focused tests pass 79/79; plan structure validates at 103 tasks/327 cases/G6. The once-per-candidate full local suite is the P01 final log: 379/379, 0 skips.
- Read-only snapshot records dirty repository revisions/status, CodeGraph availability, relevant current source hashes, API ownership and incomplete production boundaries. No external project tests or writes, live model calls, company documents or financial downloads were used. A StockQA `--help` probe was blocked at logger file creation before CLI entry; no external file was created.
- P00 deliverable is `docs/implementation/baselines/baseline-report-2026-09-26.md`; all 17 representative source hashes were rechecked against their paths. Review and receipt closure are recorded below.

## 2026-09-26 — P00 closure and C01–C07 freshness check

- P00 independent baseline review approved with no open findings; all 17 listed source hashes matched. The receipt-v2 verifier initially rejected the report because its snapshot hash was nested under `subject`; the reviewer issued a new report with the required top-level binding fields without changing the reviewed snapshot or the earlier report.
- The public read-only verifier now returns `eligible_to_close=true` for `docs/implementation/contracts/receipt-P00.json` (core SHA-256 `eae2676dc29de7eacdda1f8c496aa0d5957cafc73cf39726d487435d0315e95e`). The first blocked self-check is preserved separately; the historical P00 receipt remains unchanged.
- No product tests or external repository commands were repeated for this receipt-format correction. Next: batch-check C01–C07 receipt freshness; reuse eligible evidence and only refresh specific stale or missing evidence before one G0 review.

## 2026-09-26 — G0 candidate-scope repair and final re-review

- Rebuilt the frozen G0 candidate after the first independent review identified that the previous 623-file scope omitted `docs/stock-pool-design.md` and `docs/universe-and-operations-design.md`, both explicitly required by G0 `read_first`.
- The generator now declares those exact paths and validates that every current G0 `read_first` input is within and present in the frozen scope. A regression verifies both inclusion and fail-closed behavior if the declaration drifts.
- The candidate now contains 627 files, includes both required documents, and passes the public verifier with zero errors. SHA-256: `10747CD8316FFCE3EA0984445981FDCA6808F60D5705A19B5B20BDC31E7370CE`.
- The single focused post-fix batch passed 94 tests and 55 subtests with zero skips; the earlier r3 collection error is retained only as a diagnostic attempt. No full product suite or 188-test C01–C07 batch was repeated.
- One final independent read-only G0 review is in progress against the frozen hash. G0 remains pending until that review and its v2 receipt verifier close successfully.

## 2026-09-26 — G0 ID-02 semantic-evidence repair

- The final G0 reviewer found that C01 `ID-02.T01` previously asserted the prohibited-merge outcome in a test-local conditional instead of calling the public identity validator. The selector now retains its bridge schema check and additionally places both listings under one candidate entity, binds the matching owner-held receipt/source records, sets only `same_legal_issuer=false`, and asserts that public `cv.validate_entity` rejects the candidate.
- The affected C01 identity file passed once in an isolated temporary root: 16 passed, 31 subtests passed, 0 skips; run ID `dedaf7c1-3c0e-4cd3-91b7-269270f03dfa`; cleanup verified. Its log SHA-256 is `5017a5ca3bc720fb5874cbbc66765e1d5b53142465f369c19d0461454e3e274a`.
- Independent C01 review r2 approved snapshot `14d9d5c4b5c0f6e5f9b24e7848e69adf5f3cf189d26a6db19b2d5ff9d7b06c45`, no findings; report SHA-256 `4e907e6c67b07456fb054bec0826bfdd6ad0f86e29098d96b72aaf385be1a224`.
- Reissued C01 and dependent C03–C07 receipts and preserved the previous C01/C03–C07 r1 receipts plus old C07 chain sidecar byte-for-byte under `docs/implementation/reviews/G0/archive/id02-receipt-chain-r1-2026-09-26/`. Public verification returns eligible for each C01–C07 receipt; recursive C07 sidecar r2 is eligible with no blockers (SHA-256 `fb444e4a1e44216ca87bc6b9cdb17c6e38f9d8e20cac4c0939aa5b762d7cdeb8`).
- The earlier G0 candidate became stale after the C01 evidence update. The review packet/matrix are synchronized and the new 639-file candidate is frozen at SHA-256 `7f291c298c36a64dd2795892b2d8a294f78b1e3e952382b44b31d5a6c887be89`; manifest verification reports zero errors. The final G0 independent review is now in progress against this hash. No unrelated full-suite run, external repository write, live/API call, or company-document download was performed.

## 2026-09-26 — G0 owner-boundary repair and batched closeout

- Before sealing G0, the public task-receipt verifier rejected the planned case bundle because G0 claimed BASE-02, which is uniquely owned by P00. Corrected the plan so G0 seals only REV-01/02/03 and reads P00's BASE-02 receipt as upstream evidence; bumped plan/catalog provenance to 1.9.8 and synchronized the G0 packet, matrix, implementation docs, and test expectation.
- Added the structured `independent-final-review.json` to the candidate manifest exclusions, keeping both final review formats outside the frozen snapshot and avoiding a hash cycle. Archived the prior final G0 Markdown report with its original SHA and labeled the previous candidate stale.
- Following the user's cadence preference, the focused G0/plan batch passed 94 tests and 55 subtests with zero skips (run `96369f76-f9a8-447f-93bf-8d5ca1e6d546`, log SHA-256 `ffa47072c8d77a1957ac5de754d9cc093239aee697828a4121ddc7638249b909`); the 103-task/327-case/G6 plan validator also passed and its isolated temp root was removed. A wrapper-only r5 attempt did not start pytest because `--basetemp` was parsed empty; retained as diagnostic evidence.
- Re-ran the public recursive C07 receipt verifier against plan 1.9.8; all C01–C07 plus P00/P01 remain eligible and the new detached sidecar is `validation-C07-C01-C07-chain-r3-2026-09-26.json` (SHA-256 `9d532000bc2889944d36ba83598e681410c8723f7ace0a579bc8618a98b2f1d1`). A final focused G0/plan batch after adding the post-seal sidecar exclusion passed 94 tests / 55 subtests / 0 skips (run `8a43f950-ad0d-457e-9667-ea17d5818354`, log SHA-256 `c0c384333ca462ce3c1acbb409b373fc8a288d2a846abd1760b0e2f47da5caf4`); plan validation remained 103/327/G6, and the temp root was removed. Next: freeze the corrected G0 candidate, obtain one final independent milestone review, and close G0 only after its public v2 receipt verifies.
- That r3 sidecar was superseded after the reviewer reran the recursive verifier and surfaced stale C02/C03 document hashes. Restored the exact two Markdown hard-break spaces that I had removed, and individually verified C02–C07, P00, and P01 all eligible; the fresh C07 r4 sidecar is eligible with zero blockers (SHA-256 `644bc2c4d392eb38e92167eb1584145c57f84bd57652802b895de27e192491e9`). This will be the dependency-chain evidence for the final G0 candidate.
- Final G0 review approved candidate SHA-256 `e6ada748839aee76c725653cc04af52789ccf63fe8fbeef20756587f414c2e7a` (646 files, manifest errors=0), with no open findings. The structured report SHA-256 is `39dd352897420febe53059bb2e62a56390562d86b0c7080a2648ab1faecfe33e`; Markdown report SHA-256 is `2b4ef70a846b5e2d31bff489143b194eb8af989a41e78fa974df8af2b01760fb`.
- G0 receipt v2 now owns REV-01/02/03, uses the final independent report and current P01/C01–C07 dependencies, and passed public recursive validation: `eligible_to_close=true`, blockers empty. Receipt core SHA-256 `fc0f170294bdf71bec7cafdc69ba19ea8157be596a8f9860d916747435b88e7d`; detached sidecar SHA-256 `263787ac8f89f632f1d72f3dbdcd7390f51fbb34550aeb31a20f0751f6e398df`. The sidecar path was excluded before review so writing it did not alter the frozen candidate. M0 local-contract gate is closed; next local task is S01, followed by S03/S04 as dependencies permit. No live provider or external-repository action occurred.

## 2026-09-27 — P01 receipt regression-reference repair

- During S01 revalidation, the v2 receipt verifier treated a downstream task's upstream-owned regression references as if they had to be owned by that task. Fixed the distinction: `case_results` now covers every declared `case_id`, while the owned-case freshness hash covers only cases whose `owner_task` is the current task.
- Independent review found two additional P2 gaps: referenced owners were not required to be in the transitive dependency closure, and upstream case definitions could change without staling a downstream receipt. Added fail-closed owner-closure checks and an additive `referenced_case_bundle_sha256`; receipts with upstream references must bind them, while owner-only legacy v2 receipts remain compatible.
- Added isolated regressions for valid upstream references, unrelated owners, changed referenced definitions, missing reference hashes, and owner-only v2 compatibility. The P01-focused offline suite passes 27 tests; plan validation remains 103 tasks / 327 cases / G6, and `git diff --check` passes. Test log SHA-256: `df17fadc171bd7c5e095bd40b112659d15130b3252b8f904fc484fa8a82ad768`.
- A second independent read-only P01 review is in progress. The previous P01 receipt now correctly reports stale evidence/review against the changed implementation snapshot; after review, refresh P01 evidence and its dependent receipt chain/G0 candidate before resuming S01 closure. No live API, download, or external-repository write occurred.
- That review then found a P2 exception path (`_hashes` failure could leave a local unset) and a P3 multi-hop coverage gap. Initialized/guarded the hash result, added a public-verifier regression proving malformed ownership returns a blocked sidecar, and added a two-hop owner acceptance plus deeper dependency-cycle rejection case.
- The revised P01-focused suite now passes 29/29 tests in 3.713 seconds; log SHA-256 `8933c4258588e08db3bab81fad2211968579632d72123c03101cda9e6bfe2a3d`. `git diff --check` exits 0. A third read-only review is requested for this exact snapshot; P01 receipt refresh and dependent-chain/G0 reseal remain pending its outcome.


## 2026-09-27 — P01 current receipt re-seal

- Independent P01 implementation re-review approved the exact snapshot `017318f72c0994b69f7a19355b629a6f2460d8fc2e2f6c74b47e1744222d905a`; report: `docs/implementation/reviews/P01/independent-review-upstream-case-r3-2026-09-27.json` (SHA-256 `378a1416f193a578ba84394e05849266941731ae5b63a0a9c8170aa9c560b0c5`).
- The current 29-test P01 regression log matches the independent report. Re-ran the 14 distinct selectors referenced by the 18 P01 assertions in unique temporary roots: all exit 0, skip 0, and cleanup verified.
- Preserved the previous stale P01 receipt and self-check artifacts under `docs/implementation/reviews/P01/archive/upstream-case-r3-2026-09-27/`; reissued P01 v2 for plan 1.9.8 and public verification reports `eligible_to_close=true`, blockers empty (core SHA-256 `42f3f8e540cd236dc4aa02f188ded03515fb11ec6e1374ea78dd490674f68ebf`).
- The independent post-seal evidence review is pending. P01-dependent P00/C01–C07/G0 evidence must be refreshed before S01 resumes; no full repository suite, external repository write, live API, or document download was used.


- P01 post-seal evidence review approved the new core and sidecar with no open findings; report SHA-256 `0f99ea5c65a62ac1f5a74d2ab563722872ea2eae025cb1be8cf1a9ff6a968f1d`. P00 remained eligible. Refreshed C01–C07 current-receipt dependency evidence in topological order and preserved prior receipts under `docs/implementation/reviews/G0/archive/p01-upstream-case-recertification-2026-09-27/`; individual public verification passed for all seven. The new recursive C07 sidecar is `docs/implementation/contracts/validation-C07-C01-C07-chain-r5-2026-09-27.json` (eligible, blockers empty). G0 review packet/candidate/receipt remain to refresh; S01 is still gated.

- Refreshed the G0 packet/matrix to the new P01/C01—C07 chain, archived prior G0 candidate/review/receipt outputs, and froze a new 671-file candidate. `python -B scripts/g0_candidate_manifest.py verify` reports errors=[]; candidate SHA-256 `468cf1335811fc735068e7d88761ea166f3dbd4710c0d7b36ae665884c08263e`. The independent G0 milestone reviewer is checking this exact snapshot; its final report and the new G0 receipt/sidecar are not yet issued.

- The first G0 re-review caught a packet/matrix state contradiction: the manifest was frozen while both included documents said it was still being rebuilt. Updated both status lines, regenerated the exact 671-file candidate, and verified manifest errors=[]; no report was issued for the prior hash.

## 2026-09-27 — G0 current candidate re-sealed; S01 unblocked

- Independent G0 milestone review approved the exact frozen candidate `468cf1335811fc735068e7d88761ea166f3dbd4710c0d7b36ae665884c08263e` (671 files); manifest verification returned zero errors and the report has no open P0/P1/P2 findings. Review outcome is `verified_for_local_contract_scope`, with live/provider/runtime behavior explicitly outside scope.
- Reissued `receipt-G0.json` for the current plan and candidate snapshot; the public recursive verifier returned `eligible_to_close=true`, blockers empty. Receipt core SHA-256 `62a423c179b09a88324220840602fc2c7551c7afd84e2806541407d2f403fb73`; detached sidecar SHA-256 `efc1c044ce7e6cf2c1d28e574a3bdf93beeddd435d3ed1f1478ed6e41a1ef51b`; independent JSON review SHA-256 `aaa42e771e4e1c1785359c73fa6886d00b9dfaf13004530428eba726a09f433c`.
- Refreshed the current plan status: Phase 29 is closed for local contract scope and S01 is no longer gated. Plan structure validation passes at 103 tasks / 327 acceptance cases / G6. Next action is to re-read S01 task/card inputs and continue its unfinished implementation; external writes and real-provider/production behavior remain pending their separately authorized owner work.


## 2026-09-27 — S01 local implementation closeout

- Revalidated the current S01 implementation snapshot: metric-to-question mapping, fixed 24 core constructs, type/lifecycle replacements, security scope, optional diagnostics, recovery observations, deterministic composition, and compatibility export are present in the permitted local source/catalog paths.
- Added a quick/full MATRIX-07 integration regression and an 8 company-type × 6 lifecycle-stage composition matrix. Final isolated selector batch passed 7/7 with 0 skips; the related S01 regression batch passed 91/91 with 0 skips. Both temporary pytest roots were verified absent afterward. Catalog validation reports 48 modules / 222 scoring questions.
- Independent S01 milestone review approved the exact snapshot `c696d6307b550ea3cec884644e2fe69bf65450d1bd90665b968d58e5bde3134e`, with no open findings. The report records one non-blocking limitation: the legacy-shape test is synthesized from current selection data rather than a frozen historical release fixture.
- Issued `receipt-S01.json` against the current snapshot and the G0 v2 dependency. Public recursive verification returns `eligible_to_close=true`, blockers empty; detached sidecar `docs/implementation/contracts/validation-S01-receipt-r1-2026-09-27.json` has SHA-256 `b93b8d12ba4b65f9e93bf36a90bfb0bfe1e428ecb859a12f7893c2f784055dd9`.
- Closed Phase 28 for local implementation scope. This does not close live StockQA search, StockWiki query/refresh, UI, or production-scale operations; those remain with their downstream tasks.


## 2026-09-27 — Q02 live reproduction after S01 closeout

- Re-ran exactly one isolated MiniMax-M3 public-CLI E2E using the existing Microsoft FY2025 annual-report question and process-scoped `MINIMAX_API_KEY`; no provider key or raw model response was printed or saved.
- The current adapter again received HTTP 200 with top-level response status `completed` and model `MiniMax-M3`, but the required completed-search receipt assertion failed (`search_status=unverified`). This reproduces the latest-code gap; it does not establish that the provider did not search versus that its returned event shape lacked the fields needed for verification.
- The pytest run used `--no-cov`, disabled the cache provider, and an outer unique `TemporaryDirectory`; the exact temp parent was verified absent. The bounded sanitized log is `docs/implementation/contracts/validation-Q02-MiniMax-live-reprobe-2026-09-27.log` (SHA-256 `ac16270bfde3fada6ee5f7f6b692ae69106c1be136f199a44a34afb4d8a02179`).
- No StockQA source or test files were changed. Q02 remains partial; the next investigation should use existing non-sensitive evidence and avoid repeating the same company/model request without a concrete diagnostic change.


## 2026-09-27 — Q02 MiniMax Anthropic Messages route validation

- Under the previously approved StockQA scope, added the MiniMax-M3 Anthropic Messages route, correlated server-search result IDs to the matching server_tool_use, and kept search qualification fail-closed. Only the approved four files were touched: src/providers/llm_client.py, tests/unit/test_llm_client.py, tests/integration/test_quick_scan_cli.py, and tests/live/test_live_quick_scan.py.
- Final isolated regression suite: 102 passed, 3 credential-gated live tests skipped. An initial run hit a local pytest-base-url fixture-scope conflict before 10 cases executed; disabling that unrelated plugin produced the clean 102-pass run. The copied repository and pytest basetemp were removed.
- The default sandbox blocked outbound calls with ConnectionError before HTTP. Two network-enabled public-CLI attempts reached MiniMax-M3 and returned a conservative insufficient_evidence answer with no score. The final receipt remained search_status=unverified; therefore this run does not prove a completed server-search event with source URLs. The test now accepts insufficient_evidence only with a null score but still requires a verified search receipt, so it correctly fails closed.
- git diff --check and live-test syntax/trailing-whitespace checks passed. No raw provider response or API key was saved. Each outer temporary repository and inner CLI sandbox was cleaned; cleanup was verified.
- Evidence: validation-Q02-Anthropic-offline-r7-2026-09-27.log; network-enabled live outcomes: validation-Q02-MiniMax-Anthropic-live-E2E-network-enabled-2026-09-27.log and validation-Q02-MiniMax-Anthropic-live-E2E-final-2026-09-27.log. Independent follow-up review approves the offline changes only and has no remaining diagnostic finding. Q02 remains partial pending a verifiable live search event.


## Q02 MiniMax Anthropic bounded live E2E — 2026-09-27

- Checked MiniMax's official Server Tools and text-generation documentation plus Anthropic's web-search response semantics. Added an explicit Anthropic `tool_choice` for `web_search` to the already-authorized StockQA client; unit and public-CLI request assertions cover the exact request shape.
- Isolated unit + integration rerun passed 110 tests, 0 skips. The initial harness run hit an unrelated auto-loaded pytest-base-url fixture scope collision; disabling plugin autoload and explicitly retaining pytest-asyncio produced the clean result. Temporary test root was removed.
- The first real request did search (HTTP 200, one completed call/10 sources) but ended `pause_turn` with a second pending call; parser correctly marked it unverified. Narrowed the live test to one explicit query, then the public CLI E2E passed 1/1. It asserted a completed correlated search receipt with one call and nonempty source URLs; it does not certify that the investment score itself was produced.
- The live test's inner sandbox and outer temporary root were removed. No answer body, source URLs, or key were retained. Pytest emitted a non-fatal Windows GBK subprocess-output decoding warning after the successful test; recorded as a test-harness limitation.
- Evidence: `docs/implementation/contracts/validation-Q02-MiniMax-Anthropic-live-E2E-single-query-2026-09-27.log`. Latest StockQA snapshot hashes and both live outcomes are recorded there. Q02 remains partial until the exact modified StockQA snapshot is reviewed and the current task receipt is renewed.
- Current local checklist count before MOD-17 closeout sync: 161 checked / 11 open; plan validator remains 103 tasks / 327 acceptance cases / G6. The Q02 follow-up supersedes earlier claims that no MiniMax Anthropic live search event has been verified; it does not supersede the failed multi-search pause_turn result.

## 2026-09-27 — S05/MOD-17 completed; dependency evidence reopened

- Implemented exact raw-SHA legacy trust across historical package reads, release publishing, and current question-library validation. Added a pinned 48-module legacy baseline and rejected same-ID edits, recomputed archive/package hashes, unknown legacy modules, and caller-claimed legacy markers. Path validation now rejects symlink/junction parents under the configured root.
- The affected regression batch passed 106 tests plus 177 subtests; the S05 registry batch passed 24 tests with no skips. Independent follow-up review approved the exact implementation snapshot with no remaining actionable findings. Evidence is in `docs/implementation/contracts/validation-S05-MOD17-module-registry-2026-09-27.log` and `docs/implementation/reviews/S05/independent-review-MOD17-2026-09-27.json`.
- S01's evidence was refreshed after a reviewer-found P2 in the legacy recovery panel: replacement links now derive from per-question metadata and mismatches or missing fields produce `needs_verification` without changing the core summary. The affected 70-test/166-subtest batch and six named S01 acceptance selectors (four subtests) passed; all pytest temporary roots were verified removed. The independent review approved the exact snapshot and the public S01 verifier returns `eligible_to_close=true`.
- Re-ran all 24 S05 module-registry tests on the shared-file snapshot; all passed, and the follow-up independent review confirmed exact legacy trust is unchanged. S05's receipt now validates its own assertions and snapshot; only S04's historical-format dependency blocks closure. No external repository was changed.
- Plan is now 1.10.0 / 103 tasks / 327 cases / G6. This version clarifies S04's allowed source files so its implementation snapshot can bind the actual public registry/release validator. Next: finish S04/MOD-14 review and v2 receipt, then refresh S05's dependency reference and verify the chain.


## 2026-09-27 — S04 scope-immutability fix and final review in progress

- Added a dedicated MOD-02 selector that checks same-ID question edits and duplicate core replacement, while retaining a metadata-only patch example. The final reviewer found that a module-level `applies_when` edit could still keep old question IDs.
- Tightened `validate_upgrade`: retaining any published question ID while changing `applies_when` now fails; changing applicability requires a major version that retires all old IDs and maps each to a unique successor. The module contract and overall modular design docs now state the same policy.
- The isolated S04 module-contract batch passes 26 tests / 11 subtests with zero skips; its unique TEMP pytest root was deleted and absence verified. The current log is `docs/implementation/contracts/validation-S04-MOD02-MOD14-current-2026-09-27.log` (SHA-256 `91a892a167df2621db2f9ec1521bff84c475927d603260cd61dfc35185478231`).
- The prior S04 v1 receipt was copied byte-for-byte to `docs/implementation/baselines/legacy/receipt-S04-v1.json`. Independent review approved the final seven-file snapshot (`8e46ac17463771df142a4346ff50c81d5073f10d86a08feb50b8f38e09cef4dc`). The S04 v2 receipt binds MOD-02.T01 and MOD-14.A01–A10; public recursive validation returned `eligible_to_close=true`, no blockers (core SHA-256 `f7d403566390c0527cef16a9e757e2ca26d810bff3d88751ba5ef89bb3b27aa0`).
- Refreshed S05's S04 dependency receipt hash without changing its implementation snapshot. Public recursive S05 verification now returns `eligible_to_close=true`, no blockers (core SHA-256 `eabeae6e5c2aa0301fb733240b362e97e66e75fee205d24605980d9d70ce8f0a`). Detached verification sidecars are saved for S04 and S05 under `docs/implementation/contracts/`.
- Current active task-plan checklist: 164 checked / 9 open. Structural plan remains version 1.10.0 with 103 tasks / 327 acceptance cases / G6.

## 2026-09-27 — Review and test cadence consolidated

- Reviewed the current execution entry, test strategy, handoff rules, receipt contract, and task plan. The intended milestone cadence existed in places, but per-card wording and receipt dependency semantics could still force unnecessary stop/review cycles.
- Clarified that task cards define ownership and scope, not a required pause: implementations may continue after upstream interfaces are frozen; dependent tasks remain unclosed until the milestone gate is satisfied.
- Consolidated official checks at stable change groups and G0–G6: one shared test batch can support multiple case/assertion records, one milestone review covers related tasks, and ordinary fixes rerun only impacted paths. Full-suite reruns and independent review are not required after each small card.
- Kept exact case-level outcomes and high-risk/live gates. P01 pre/post-seal review remains a one-time verifier-specific exception. No task/case/invariant counts, product behavior, or cross-repository permissions changed.
- Plan validation passed (103 tasks / 327 cases / G6); the focused implementation-plan test batch passed 79/79. No product tests, network requests, or external repository writes were run. Next: resume S06/MOD-18.

## 2026-09-27 — S06/MOD-18 dependency closure implementation

- Implemented deterministic transitive module dependency closure, symmetric selected-conflict checks, fail-closed `needs_review`, and an empty eligible-module list for invalid compositions. Updated the route-decision schema and routing contract without changing `question_sets.py` or S05-owned tests.
- An earlier grouped local S04/S05/S06 regression batch completed with 137 tests and 194 subtests passing; the isolated outer temporary workspace was removed, but its output was not persisted and is only historical progress evidence. The formal current MOD-18 acceptance batch was then run in three groups: 24 passed / 17 subtests, 11 passed / 7 subtests, and 6 passed; 0 skips, no temporary leftovers, outer root removed. Full log: `docs/implementation/contracts/validation-S06-MOD18-batch-2026-09-27.log`, SHA-256 `b971f49255b155f7af308f417f29c4895599b3d316a61c3adc94a389d2966734`. No live API or external repository was used.
- An independent read-only review approved the exact current four-file snapshot with no P0–P2 findings; report: `docs/implementation/reviews/S06/independent-review-MOD18-2026-09-27.md`. The review did not run tests and makes no claim about production StockQA or StockWiki behavior.
- The existing S06 receipt is bound to the pre-MOD-18 route/schema hashes and remains stale; S03 is also a legacy-format dependency receipt. S06 stays open pending a current receipt and dependency-chain validation, plus its production StockQA/StockWiki E2E gates. No task/case totals or external write permissions changed.
- Read-only inspection hiccups: one receipt-inspection snippet assumed a hash snapshot was an object (it is a list), and a PowerShell-invoked Python one-liner included literal newlines; both were corrected without file mutation. One initial progress-document patch had stale context and was reapplied with the current text. The accompanying git status reported inaccessible user-level ignore/cache paths; no workspace changes were caused by those warnings.


## 2026-09-27 S03/S06 closeout follow-up
- Overall implementation plan: 103 task cards / 327 acceptance cases / G6; checklist now 168 complete / 10 open after reopening S03 for DUR-04 evidence. M0/G0 and S01-S05 local contract work are evidenced; production/live and cross-project work remains partial or pending.
- Independent S03 review found DUR-04 was overclaimed: the old test only changed a fresh manifest header, and this repository has no real catalog 3.1.0 metric manifest. Renamed that negative test and added a separate isolated test that copies the actual immutable package release into a temp root, omits mutable catalog/module sources, composes and normalizes against the frozen package, and rejects a mismatched catalog header. The new archive regression plus all S03-selected tests pass (6 tests); implementation-plan suite passes (80); plan validation is valid. No API/network used. Independent re-review is pending.
- Corrected S03 allowed_changes to exact source paths and added a plan regression test. Bumped current plan/case version to 1.10.1 without changing task/case counts.
- S06 MOD-18 narrow review is clean; the broader S06 snapshot has a separate unresolved P2: overall route confidence is discarded before dispatch/snapshot. S06 stays open.


## 2026-09-27 — S06/MOD-19 route confidence gate implemented; milestone review pending

- Updated the implementation plan to 1.10.2: 103 task cards / 328 acceptance cases / G6. S06 now has an exact local allowlist and MOD-19 defines nine atomic assertions for outer-score preservation, 6/7/10 boundaries, independent facts, per-module gates, resealed tampering, unscored routes, and archived router compatibility.
- Implemented router 2.2 with routing-policy schema 1.2 and protocol `stockqa-route-confidence-2`; the policy freezes a minimum classification-confidence score of 7. Parsing returns the score separately from candidates; the CLI passes it through; execution receipts and immutable route snapshots retain it. Scores below 7 demote only applicable `searched_llm` candidates to uncertain. Verified facts remain independent, and a score at/above 7 does not bypass any module evidence/materiality gate.
- Snapshot validation recomputes threshold eligibility and receipt consistency, checks the low-score coverage gap, and rejects selected below-threshold model candidates even after the caller reseals the route hash. Router 2.0/2.1 snapshots remain readable; current resolution, execution, and composition require the 2.2-compatible policy protocol. Candidate packages are published only in temporary test roots; the workspace active pointer was not changed.
- Verification: full `test_routing.py` passed 25/25 (log SHA-256 `38681D4B9543C14D654AB84247A40571A9CCA48E1A2332E7AC1A1AFA7FE813A3`). Grouped `test_question_sets.py`, `test_module_registry.py`, `test_module_contract.py`, `test_s06_dependency_closure.py`, and `test_implementation_plan.py` passed 200 tests total, 0 skips (log SHA-256 `A3555EEDB7C84C5894A8172ABC4AA1444DC6FA2669E5B4FC63FA94D4B22F7C9F`). Plan validation passed at 103/328/G6 (log SHA-256 `9A45761D95DCEF5FD893FC1DCA05F0D55140BC0360568AC897AEF312DEBF0E0C`). Python compilation and scoped `git diff --check` passed.
- Temporary-root audit found one S06 fixture from 2026-09-26, outside this batch; verified it was the exact `iqs-s06-*` test copy with no reparse points and removed it. Afterward no `iqs-s06-*` temporary roots remained. The new tests used only isolated temp roots; no live API or external repository was used.
- An independent read-only review of the exact confidence implementation is pending. The old S06 receipt remains stale, and S03's historical 3.1 compatibility evidence/dependency closeout plus production StockQA/StockWiki E2E remain open, so S06 stays partial.

## 2026-09-27 — S06/MOD-19 execution trust anchor and downstream contract follow-up

- Addressed the independent review's P1 finding that a self-resealed route could change a model candidate's mutable `basis` label. Current execution now requires a caller-supplied, independently stored route decision ID. MOD-19.A06 covers a coordinated rewrite of the candidate basis, total score, execution receipt, coverage gap, and status; the self-consistent resealed snapshot is rejected at execution against the original expected ID.
- Clarified the trust boundary in `references/routing.md`, the S06 task and acceptance contract: content hashes detect changes but do not authenticate provenance. W15 must supply the independently stored ID; W15 and U04 contracts now also preserve and display router 2.2 classification confidence distinctly from company-quality scores, including historical missing-field behavior and the low-score/verified-fact distinction.
- Corrected the router 2.1 evidence claim: router 2.0 has a real archived fixture; router 2.1 is currently only a synthesized compatibility path and still lacks a preserved historical snapshot. The plan is now 1.10.3 (103 tasks / 328 cases / 53 invariants / G6).
- Verification after the fix: `test_routing.py` passed 25 tests and 20 subtests; grouped S06/plan regression passed 225 tests and 259 subtests; fresh `test_implementation_plan.py` passed 81 tests and 58 subtests. Plan validation remains valid. Logs: `validation-S06-MOD19-confidence-anchor-2026-09-27.log` SHA-256 `5F93B516CA735557C114BD5F84F388034DA5F7BDF41E0A433F07907F752DE79D`; `validation-S06-MOD19-plan-tests-2026-09-27.log` SHA-256 `45181DC8C39569DEBEFE7EA70A941F0E37B61CDB428D756F597EC3DD7D179638`; plan JSON SHA-256 `9A45761D95DCEF5FD893FC1DCA05F0D55140BC0360568AC897AEF312DEBF0E0C`. `py_compile` and scoped `git diff --check` passed; no `iqs-s06-*` temporary directories remain.
- The independent follow-up review and current S06 receipt are still pending. The 2.1 fixture limitation, S03 historical evidence, production StockQA/StockWiki E2E, and package activation remain open; S06 is not production-closed. No live API call or external-repository write occurred.

## 2026-09-27 — S06 downstream acceptance gaps closed in plan

- Follow-up independent review confirmed the required-decision-ID execution gate and coordinated-reseal test, then identified two acceptance omissions. MOD-07.A02 now requires W15 to fetch `expected_decision_id` from trusted stored route state and reject a resealed mismatch before output/provider work. MOD-13 now requires U04 to render router 2.0/2.1 records without confidence as “historically not recorded”, without inventing score, threshold, model, or time.
- Updated W15/U04 task steps, MOD-07/MOD-13 acceptance cases, the plan regression guard, and test strategy. Plan version 1.10.4 remains 103 tasks / 328 cases / 53 invariants / G6.
- Fresh plan validation passed; `test_implementation_plan.py` passed 81 tests / 58 subtests. Plan log SHA-256 `3A35D410834DCD64D780ABF294698466DA1566B4C1D3F165215A1098A15554CB`; validation JSON SHA-256 `9A45761D95DCEF5FD893FC1DCA05F0D55140BC0360568AC897AEF312DEBF0E0C`. The larger S06 regression remains 225 tests / 259 subtests, with routing 25 / 20 subtests. Final independent review of the added W15/U04 cases is pending.
- Production S06 remains partial pending that final review, actual router 2.1 historical artifact coverage if one becomes available, S03 evidence closure, and authorized StockQA/StockWiki integration E2E. No live calls, external-repository writes, or residual test temp roots.

## 2026-09-27 — S06 confidence follow-up independently reviewed

- Final read-only review confirmed MOD-07.A02 and MOD-13.A01 are correctly owned by W15/U04 and their test-plan guards now require the trusted-storage anchor, pre-dispatch rejection, historical-not-recorded display, and no fabricated confidence metadata. No additional P0–P2 finding was reported for those acceptance changes.
- Review: [independent-review-MOD19-downstream-confidence-2026-09-27.md](docs/implementation/reviews/S06/independent-review-MOD19-downstream-confidence-2026-09-27.md), SHA-256 `FAA34D6582F5AB2DB935F2B55534CF6C0EFFDBB339477A45CB18F3ED4527B4C2`. It confirms plan validation at 103 tasks / 328 cases / G6; the review itself did not run tests.
- Targeted plan suite after the final guard passed 81 tests / 58 subtests; validation passed, and scoped whitespace checks passed. The reviewer explicitly retains the limitation that router 2.1 has only synthesized compatibility-path coverage and no preserved historical fixture. A targeted search across StockWiki, StockQA, company-wiki, and invest-skills JSON artifacts found no router 2.1 snapshot or catalog/template 3.1.0 manifest; no external files were changed.
- The S06 implementation fix and prior 225-test grouped regression remain intact. Current S06 receipt refresh, S03 historical-evidence closure, router 2.1 real-fixture availability, production cross-project E2E, and package activation remain open, so S06 is still partial.


## 2026-09-27 — Q06 持久化同步传输边界第二段

- 在用户已授权并已提前报备的 StockQAbyLLM 范围内，新增 src/utils/quick_scan_work_transport.py，并在同步 LLMClient.send_search_request、OrderedSearchProviderCascade、LLMProvider 接入可选的待办/路由上下文。没有上下文的旧调用保持原行为；有工作项时先构造请求，再持久化 prepared → send_intent，然后才允许单次 HTTP POST。
- 回执只在内存中筛选安全字段后计算哈希；持久化记录不含完整 prompt、答案正文、网页正文、来源 URL 或 API key。401/403/404和带已识别错误码的429可确认为提供商拒绝并按既有优先级转路；超时、5xx、歧义429、迟到/围栏失败及记账错误按uncertain/fail-closed处理，不能盲目重发或切换。
- 新增临时真实SQLite + 模拟HTTP路径测试：send_intent先于POST、明确拒绝后备用路由、超时和5xx阻断备用、过期lease在HTTP前拒绝、回执写库失败不转路、同一发送句柄不能重复消费、旧调用兼容。焦点批次35项通过；最终相关unit/integration分组264项通过、0失败；日志SHA-256 91fb3cf7658a290a8b77a8d0d37d8e6d2f817b0362e2cc069ac3b67cb13e1282。AST/Ruff与新transport/store文件Black检查通过，静态日志SHA-256 2369fcbf9e6e4a3f08e914abbbe8c221e08dc8ba3f23f9099eccd503f09832f3。pytest使用自动删除的唯一临时根，子进程移除provider key环境变量，无live API。
- 只改获批StockQA代码/测试范围；未写StockWiki或company-wiki。独立只读审查正在检查冻结快照。Q06仍partial：当前公开CLI尚未接入权威StockWiki身份回执；Q07答案checkpoint、Q09预算、Q10/W05 ACK仍未接入，异步客户端也不在本阶段传输钩子范围内。


## 2026-09-27 — Q06 同步传输边界二轮审查整改

- 第一轮独立复审确认了两个账本/回执边界缺口：过期lease后的迟到响应未留hash，格式修复请求缺第二次attempt通道；整改后第二轮又指出“一次修复”应由SQLite状态机本身强制，且迟到失败响应也需留痕。
- 当前 `prepare_attempt` 仅允许同一work item/lease/route/provider/model下的一次显式格式修复，且prompt hash与cache key必须改变；lease下已经有两条成功运输回执后，第三次请求会被拒绝。迟到2xx、401、429只保存脱敏receipt hash并保持uncertain，不接受答案、不fallback。
- 焦点store/transport回归45 passed；相关LLM client/provider、级联、parser、work store/transport、公开CLI分组274 passed。AST/Ruff/Black通过。API keys与live开关均从测试子进程环境移除，HTTP mock、SQLite与配置均隔离于唯一临时目录，测试后临时根已验证清理。
- 验证日志：`validation-Q06-transport-boundary-final-2026-09-27.log` SHA-256 `7890D80AB17DBA8CE4211BF7D3DEC605D4968F60769F875208F12ABB83DFD5AE`；静态检查日志 SHA-256 `09F6C89C5011EF87C965A151DDFE483E232C6626BF34777EA178C1C4A5DB6C46`。
- 第二轮独立审查核验精确7文件哈希，关闭先前P2/P3且没有新的P0-P2；详见 `docs/implementation/reviews/Q06/independent-review-r2-2026-09-27.md`。该审查仅覆盖同步transport，StockQA公共CLI尚未绑定生产work item，Q06整体仍partial；W03权威身份投影、Q07答案checkpoint、Q09预算、W05 ACK及异步路径仍待实施。


## 2026-09-27 — Q02 endpoint/credential follow-up

- MiniMax `.cn` returned HTTP 200/completed without a correlated web-search result; the public CLI correctly returned an unscored, unverified answer. The official global `.io` endpoint returned HTTP 401 with the configured key. Treat a credential/endpoint region mismatch as a hypothesis, not a proven root cause; do not weaken search validation or repeat identical calls.
- Updated the StockQA live test to accept `STOCKQA_MINIMAX_ANTHROPIC_BASE_URL`, default to the existing `.cn` route, capture subprocess output as UTF-8, and report only safe response metadata. The change is in the already-authorized StockQA scope; no other StockQA files were edited in this follow-up.
- Isolated client/CLI focus tests passed 17/17 (93 deselected); test and live-run temporary roots were cleaned. Evidence is recorded in `docs/implementation/contracts/validation-Q02-endpoint-region-diagnostic-2026-09-27.md`.
- First independent review found and reported a P1 indentation error, P2 optional-request-ID overconstraint, and P3 lossy error-code summary. Fixed all three; the corrected file passes AST parsing, the live selector collects without execution, and the focused offline batch passes 17/17. Current live-test SHA-256 is `CC1423ECC7E5F24AE26ACF2F08067B3613F5AE9BDAE22AF6D8B5A9E8D10BA95F`.
- The second read-only review matched both corrected hashes, closed the P1/P2/P3 findings, and reported no new P0–P2 issues; see `docs/implementation/reviews/Q02/independent-review-endpoint-diagnostic-r2-2026-09-27.md`. Q02 remains partial until a currently supported endpoint/credential pair yields a verified search receipt and the acceptance receipt is refreshed.

## 2026-09-27 — 进度同步与Q02提供商协议核验

- 复核开放项后更正 `task_plan.md` 的 Next Step：S06 router 2.2置信度与执行decision_id问题已完成并独立复审，不再列作待修；S03/DUR-04当前只证明3.2.0不可变归档回放，真实3.1.0 metric manifest仍缺失，故保持范围限制，不签发超范围verified结论。
- StockQA只读核对表明Q06持久化store及同步transport边界的测试/复审已完成，公开CLI仍未绑定生产work item。该绑定依赖W03权威身份投影，不能由StockQA自行猜测；Q07答案检查点、Q09预算、W05 ACK和异步路径仍开放。未写StockWiki/company-wiki。
- 检查MIMO/DEEPSEEK/MINIMAX环境变量时只记录存在性，没有读取或输出值。依MiMo官方联网搜索文档，以`MIMO_PLAN_API_KEY`与用户给出的Token Plan endpoint尝试了隔离搜索调用，HTTP 400；只输出结构化错误码和字段名，返回参数指出`webSearchEnabled=false`，没有搜索回执。一次pay-as-you-go endpoint探针未获得可判定的工具结果，因此不把它计为通过或失败；不重复调用，待获得可读回执后再决定。
- 官方协议核对：MiMo文档描述OpenAI兼容Chat Completions、`type=web_search`、`force_search`及URL引用；StockQA当前`_search_endpoint`没有MiMo搜索协议分支。DeepSeek官方tool-calls示例要求调用方运行自有函数工具，没有证据支持其作为内置联网搜索提供商。Q02先实现MiMo可验证适配/离线回归，再安排一次隔离真实搜索；DeepSeek保留模型用途，不冒充搜索能力。
- 本轮只读StockQA与官方文档、做一次Token Plan探针并更新本地计划状态；没有外仓文件写入，也没有下载公司财报或留下本地API临时文件。
## 2026-09-27 Q02 MiMo联网搜索适配与验证

- 按先前用户授权，在StockQAbyLLM完成MiMo联网搜索协议分支、模型/主机/path allowlist、响应绑定`url_citation`解析、同步/异步提供商与公开CLI回执，以及隔离单次live测试。没有改写用户key，也未把key值放入文件。
- MiMo相关焦点离线unit+integration测试151项通过。一次Microsoft单题公开CLI真实联网E2E通过：收到当前模型响应、已执行搜索回执、至少一个来源URL和时间戳；唯一临时sandbox在测试退出后清理。该live通过只适用于pay-as-you-go route/key；Token Plan仍已知返回`webSearchEnabled=false`。
- 首次离线批次受全局安装的pytest `base_url`插件影响（19个fixture ScopeMismatch），并发现一个错误的测试断言；关闭该非项目插件、修正断言后，批次全绿。未修改StockQA pytest配置。独立只读审查发现异步provider alias会误写为实际provider；修复后以`provider_config_ref`保存alias、execution receipt保存实测provider，新增回归。受影响unit+integration批次171项通过，独立follow-up确认该问题关闭、无遗留发现；当前MiMo/Q02回执未封存前不标记Q02关闭。
- 用户提供搜索供应商额度：Brave 50 requests/second、月请求不限；Tavily 1,000 credits/month。记录为额度/架构输入，不含key；未调用这两个搜索API。建议将搜索供应商配置与回答模型配置分离、Brave批扫、Tavily按需补源，并在确认套餐保存权前不持久化原始搜索响应。

## 2026-09-27 — Q07 逐题检查点与崩溃续跑

- 在获批StockQA范围内为SQLite work store增加schema v1→v2事务迁移与不可变 `answer_checkpoint`；答案、verified identity/question/routing指纹、真实provider/模型与搜索来源回执、回答及完成时间在一个事务中绑定。transport共用同一脱敏回执hash allowlist，来源URL和完成时间纳入hash，原始provider/网页响应不保存。
- 新增原子result_ready转换、checkpoint读取/按run恢复列表、相同答案重放幂等、异答案冲突、仅pending取消。区分store attempt与provider transport attempt，也区分combined work prompt hash和provider prompt hash，避免把不同层的标识/指纹误判为相同。
- 隔离的实际调用边界测试走LLMClient→mock HTTP响应→真实响应解析→SQLite checkpoint；加上版本迁移、损坏hash、事务故障回滚、response_available后崩溃保持uncertain、4题保存/2题续跑、in-flight取消保护。随后新增URL查询参数凭据脱敏与固定历史v1 SQL fixture回归，并将测试SQLite连接明确关闭。最终受影响unit/integration/provider/CLI批次235项通过，0失败/skip；`ResourceWarning`提升为错误仍无警告，Ruff、Black、git diff --check通过。测试在临时工作目录运行，TEMP/TMP/pytest basetemp和日志均隔离并清理；未调用API、下载文档或写StockWiki。最终文件hash、独立复审见 `docs/implementation/contracts/validation-Q07-checkpoint-2026-09-27.log` 与 `docs/implementation/reviews/Q07/followup-review-2026-09-27.md`。
- Q07仍partial：默认每次模型请求一题；现有4+2恢复测试使用六条独立question work item，不代表PAR-04所需的一次多题dispatch可逐题落checkpoint。公开runner需等待W03权威身份投影；Q09预算、W05 ACK/导入和异步transport也仍是独立接线项。独立follow-up复审已基于最终哈希确认无P0-P2发现，但该结果只覆盖存储/迁移/传输底座，不表示生产runner闭环。

## 2026-09-27 — Q09 持久预算与并发闸门第一段

- 在用户已授权的 StockQAbyLLM 范围内实现SQLite预算账本：原子费用/请求预留、模型组/路由/全局并发槽、价格引用与策略版本固定、失败与搜索同账、保留已结算支出跨策略升级；超预算在HTTP前拒绝，超时/未知成本保持预留并暂停新派发，等待同一attempt的可验证对账。send-intent与预算reserve同事务，避免账本拒绝后留下可发包状态。
- 将预算上下文接入同步及异步LLM search transport。未知HTTP结果不会因原始400/429/5xx状态码而被乐观判定为未执行；不自动重试或fallback，回执保留脱敏attempt信息，要求先对同attempt reconciliation。生产provider实际费用仍须来自可核验用量/价格记录；测试中确定的cost resolver和rate card仅是隔离fixture，不能代表正式费率。
- 双进程、20个并发调用的真实SQLite+本地阻塞HTTP stub集成测试验证全局最多4、每组最多2、每路由最多1，并确认存在真实发送重叠；另覆盖并发超预算竞态、未知费用暂停、超额fallback阻断、策略升级沿用支出、预算拒绝前不POST及异步结算。初始全范围离线回归 **430 passed** 后，独立审查发现迟到HTTP回执与预算槽状态不一致；补充原子late receipt+预算结算、“无响应仍保留在途槽”对照测试、重复回执冲突检查、费用解析器异常/NaN用量回归，以及预算对账重放中`confirmed_not_sent`/`completed`请求计数语义一致性测试后，当前全范围回归为 **436 passed**。运行开启 `ResourceWarning` 视为错误、禁用全局pytest base_url/cache插件并使用唯一临时工作目录，无真实API调用、无文档下载。此次修改的5个Python文件 `ruff check`、`black --check`通过，StockQA限定`git diff --check`通过。
- 迟到HTTP响应的work attempt仍保持uncertain，未接受答案也不fallback；预算attempt则在同一SQLite事务记录晚到receipt并关闭网络并发槽。未知费用仍保留预留并阻止后续发包；若没有收到HTTP响应，则保持`outcome_uncertain`并占槽，直到人工/外部对账。
- reviewer指出当前cost resolver只接收脱敏receipt，不含token usage；因此token计价必须等可信provider usage lookup或人工/外部对账，缺失信息时保守暂停，不根据提示/响应自行估价。另发现费用解析器本身异常或返回NaN曾阻断HTTP结果落账，现已改为unknown-cost fail-closed并加测；对账重放也已固定请求计数语义。新快照follow-up独立复审待回，Q09仍partial；生产费用解析/runner完整预算配置和验收未完成。
- 搜索API额度仍是独立搜索供应商策略，不混入LLM费用账本：用户提供Brave 50 requests/second及月请求不限、Tavily每月1,000 credits。额度未做账户核验；Tavily credit与请求数的换算未经证实，不擅自折算。两者额度、实际用量及搜索来源留存与模型预算分开记录。

## 2026-09-27 — Q10 StockQA producer-side outbox首段

- 按既有授权仅修改StockQAbyLLM的src/utils/quick_scan_result_outbox.py、src/utils/quick_scan_work_store.py、tests/unit/test_quick_scan_work_store.py和新增的tests/unit/test_quick_scan_result_outbox.py；同步本仓Q10任务卡、JOB-07/DB-07/PAR-10语义及实施进度。未写StockWiki/company-wiki，也未调用Brave/Tavily/LLM API或下载文件。
- work store升级到schema v5，支持v4原子前滚迁移；新增一题一包耐久outbox、adapter不可用/字段不足时的持久block reason、规范化完整package字节与hash、稳定delivery key、append-only投递事件。已封存package不能换包；ACK必须精确匹配C06 package/item/observation/payload及StockWiki namespace/store。只有accepted/already_present在同一事务保存ACK并转成delivered；拒绝/冲突终态不会把答案工作标记已交付。
- 发送意图提交后保持send_uncertain且续启时禁止自动POST；只有明确证明请求字节未发送才能用相同字节/key重新派发。精确ACK可幂等重放；错ACK、未知状态、终态改写和包字段漂移均拒绝。结果交付失败不创建新LLM attempt。
- 使用真实临时SQLite work store、动态合成单项package、重启及ACK/状态故障注入，StockQA两文件严格隔离回归78 passed，ResourceWarning和PytestUnraisableExceptionWarning作为错误；Ruff/Black通过。动态生成的完整Observation另经本仓C06 exchange+observation JSON Schema和语义validator交叉验收通过。Root计划结构校验103 tasks/328 cases/G6通过，计划测试81 tests/58 subtests通过；StockQA、计划及pytest临时根均隔离并清理。
- 独立Q10复审发现Observation证据URL可以偏离已保存搜索来源；现要求每条evidence URL精确匹配checkpoint内规范化来源URL列表（允许只引用其子集），并增加重算payload/item/package全部哈希后仍应拒绝的回归。进一步核实本仓C06语义要求成功评分至少有一条证据，因此producer也拒绝空证据scored答案（insufficient_evidence仍可为空）。修复后两个受影响单测文件共79 passed（warnings-as-errors）；Ruff/Black和C06全量schema+语义交叉验证通过；最新四个文件精确哈希follow-up无P0–P2发现。Q10验证证据见`docs/implementation/contracts/validation-Q10-result-outbox-2026-09-27.md`。
- Black formatter对StockQA外仓目录原位写入受文件系统权限阻止；已使用black --diff逐项手工应用等价格式，最终Black --check --no-cache通过。Q10最终验证报告待独立follow-up回执后封存。
- Q10仍partial：checkpoint自身没有完整C06 Observation所需的已验证cohort、题/模板版本、information cutoff及完整证据字段；本段只接受verified adapter提供的完整包，不编造元数据。完整Observation adapter、公共runner接线、W05真实ACK/查询对账和跨库端到端均未完成，不能宣称真实StockWiki导入闭环。见docs/implementation/contracts/validation-Q10-result-outbox-2026-09-27.md。

## 2026-09-27 — Q02 MiMo live 验收重试记录

- 在此前用户授权的测试范围内，重新执行MiMo单题公开CLI联网E2E。用例返回非零，公开结果仅能确认`answer_status=error`、`search_status=unverified`，缺少HTTP状态、model/response ID及来源；无可验证成功回执。
- 临时目录放在invest-quick-scan的唯一临时根下并由finally清理；输出未包含或读取API key值。环境配置使用默认pay-as-you-go主机`api.xiaomimimo.com`与既有`mimo-v2.6-flash`测试配置；根因未从安全摘要中确认。
- 因无可靠传输回执，无法证明请求字节未发送；将本次结果按outcome-unknown处理，不自动重复调用，不能用于证明供应商拒绝或联网插件失效。Q02仍partial；后续只有检查账户侧用量/请求记录确认本次未产生请求后，或用户授权一笔新的独立尝试，才适合再次live验收。

## 2026-09-27 — Q09 provider usage与费率卡接线

- 在已授权的StockQA范围内完成OpenAI Responses、Anthropic Messages、MiMo Chat Completions用量字段归一化；receipt只保留allowlist计数，不保留provider原始payload。新增本地无密钥费率卡schema与空模板、Decimal计价resolver，按provider/model/pricing reference/currency精确匹配，并接入公共runner现有Q09 budget binding。
- 目前不含任何账户实价。缺少卡、匹配失败、用量缺失/畸形或resolver异常时，预算保持unknown-cost并fail-closed。CLI E2E通过mock provider response验证解析、receipt、runner、费用计算到持久预算结算，金额256,850 micros。
- 扩展受影响测试418项分两组运行：provider/runner 285 passed，预算组133 passed；两组均将ResourceWarning及PytestUnraisableExceptionWarning当作错误且干净退出。合并运行的418项断言全通过，但pytest-asyncio Windows临时Proactor loop fixture清理socketpair失败，令进程退出码1；tracemalloc定位到pytest fixture teardown。该合并运行不记为全绿，隔离分组结果作为当前严格验收证据。
- Ruff、Black、schema/template JSON与diff检查通过；每个测试进程使用唯一临时根目录并已清理。无真实LLM/API调用、无Brave/Tavily调用、无文档下载。精确快照哈希和剩余门槛见docs/implementation/contracts/validation-Q09-usage-and-rate-cards-2026-09-27.log；Q09精确快照的独立复审待回。
- 本目录计划校验通过（103 tasks / 328 cases / G6）；计划回归81 tests与58 subtests通过。此次仅追加规划与验收记录，没有修改计划JSON或产品逻辑。

## 2026-09-27 — Q09 独立审查问题修复与复验

- Q09首轮独立设计审查提出三个P2：Responses搜索事件没有id时可能少计、费率JSON数字先转float造成精度损失、预算对账重放未绑定终态。均在StockQA获批范围内修复：按可分类事件计数且矛盾用量改为unknown；费率JSON用Decimal直接解析并以整数精确舍入；新增work-store v4不可变终态记录，同终态幂等、不同终态拒绝，旧历史结算迁移后标为`legacy_unverified`。
- 固定反例先失败后通过。最新严格隔离回归provider/runner **371 passed**、budget/store **86 passed**；分别使用独立TEMP根，把ResourceWarning和PytestUnraisableExceptionWarning提升为错误，关闭live E2E并清除key环境变量，均退出码0且清理临时根。Ruff、Black无缓存检查、费率schema/template JSON解析及限定StockQA `git diff --check`通过；未调用任何API、搜索服务或下载文档。
- 修复后独立复审确认8个核心源文件/测试/文档哈希一致，未发现遗留P0–P2；结论见`docs/implementation/reviews/Q09/followup-review-2026-09-27.md`。Q09仍partial：没有账号实价费率卡或账单对账，生产部署门槛仍未全部完成。精确哈希和测试环境记录见`validation-Q09-usage-and-rate-cards-2026-09-27.log`。

## 2026-09-27 — StockWiki W02/W03 首段实现与复审通过（仍partial）

- 用户授权仅覆盖 StockWiki 8 个文件：独立 quick-scan store、来源身份候选导入、universe 成员管理、CLI 注册及相应测试；没有改 W05、UI 或其他 StockWiki 文件。真实公司主档仓库只读。
- W02 当前仅预览或保存哈希锁定的证券来源快照与候选，精确代码/交易所碰撞只提示身份复核，不会创建/合并 Entity 或 Security。空白必需字段会被标记；来源 URL 只保留 HTTPS origin，路径、凭证、查询串和片段从公开预览和SQLite中剔除。重放只比较来源不可变字段，保留首次导入时的匹配上下文，避免新增上市记录导致相同文件哈希重放失败。
- W03 支持初始化股票池、新增、逻辑移除、恢复、显式保留、置顶、列举、历史查看和名单reconcile。名单reconcile仅补成员并报告缺项；软容量从不淘汰成员；人工置顶需显式覆盖才可删除。SQLite v1→v2事务迁移使用独立冻结的v1 SQL fixture，比较并确认 entity/security/segment/universe/member 五张基表数据均保留；恢复已移除成员并置顶现在由一个事务、一个版本化恢复事件原子完成。
- 数据库不可变历史除了UPDATE/DELETE trigger，也增加冲突式INSERT/REPLACE护栏；独立数据库连接关闭recursive triggers时仍有回归覆盖。Store实现拆为identity/universe mixin，维持`QuickScanStore`既有方法接口，核心新模块均低于600行。
- 三个StockWiki目标测试文件在隔离临时目录运行，测试只读取CN/HK/US真实证券主档并复制到临时路径，未下载/改写公司主档；SQLite与pytest临时数据测试后清理。当前结果 **59 passed, 1 skipped**（skip是原有可选分类YAML测试未配置输入）；Ruff lint、核心新增模块format check与限定文件`git diff --check`通过。未发起LLM/API请求或下载公司文档。
- 独立复审核对最终8文件哈希，关闭event_id边界、路径凭据和动态v1夹具三项风险；来源URL仅保留HTTPS origin，冻结v1 SQL fixture被实际迁移并逐表对照。最终follow-up定向回归4 passed，未发现P0–P2。完整验证与精确哈希见`docs/implementation/contracts/validation-W02-W03-stockwiki-first-segment-2026-09-27.md`。W02仍缺身份绑定与晋级桥接，W03仍缺权威身份投影到StockQA扫描待办的生产接线，因此两卡保持partial，当前验收不表示2000家公司已扫描或UI可用。
- 本地实施计划结构验证通过（103 tasks、328 acceptance cases、G6），计划单测81 tests/58 subtests通过；这些只是计划完整性检查，不是产品完成证明。

## 2026-09-27 — Q02 MiniMax Anthropic current-snapshot recheck

- Read-only comparison found that the earlier one-query live-success log binds four hashes that differ from the current StockQA worktree. The old search receipt is therefore not attributed to the current implementation; no new live call was made during this check.
- Current isolated offline regression across LLM client/provider unit tests and public quick-scan CLI integration: **158 passed**, warnings-as-errors. Test process ran from a unique temporary working directory with `PYTHONPATH` pointed at StockQA; API-key environment variables and live E2E flag were removed, and log/pytest outputs were contained in and removed with that temporary root. An initial collection attempt from the repository cwd hit the expected read-only `logs/` permission boundary before tests or network activity; it left no repository artifact and is not counted as a test run.
- Ruff passed on the changed client/provider sources, client tests, CLI integration, and live test. Black passed on five focused source/client/integration files; older formatting in the provider/live test modules was not applied wholesale. `test_llm_provider.py` also has existing unrelated F401/F841 findings outside the added Q02 assertions, so its full-file Ruff result is not claimed clean.
- Final current seven-file SHA-256 snapshot, submitted for read-only independent review:
  - `src/providers/llm_client.py` `5D410CCBEE307E62A4C9999B681957822EB8EC6EE5ED89284D71FA5116CFFA8F`
  - `src/providers/llm_provider.py` `03B6D303311F211FF4D0AA7FD95C8BDA749446CDD558EE51812BCADCB737FCAF`
  - `src/providers/async_llm_provider.py` `CD0A56C7025D48F26038217F3BEE0ED228ECA42939F3F9092D21027667051F8F`
  - `tests/unit/test_llm_client.py` `4BBC4EF78CFC250AB7419173B48BC3C37B200D62E2071669D277E19859770A81`
  - `tests/unit/test_llm_provider.py` `1A4656711F00A86F21E3BDFA197B9369238818DBEB117560451B1C20F8032EF3`
  - `tests/integration/test_quick_scan_cli.py` `BA4817474BEBF3BAFA7415471B578DAF826285D6385450D9E3AE54E407D20E15`
  - `tests/live/test_live_quick_scan.py` `EA9394EB5358BC1A77261F519F948BE7918728A83F27B34B4A85CD87FB6C9E58`
- Current snapshot remains Q02 partial until independent review and, if the review confirms the live fixture still represents the code path, one hash-bound live acceptance. Previous `pause_turn` remains intentionally unverified; no continuation request was issued.

## 2026-09-27 — Q02 fail-closed corrections and one live attempt

- Independent current-snapshot review had reproduced two parser gaps: Python treated `base_resp.status_code=false` as integer zero, and the Anthropic parser ignored an unrecognized `server_tool_use` such as `web_fetch` alongside an otherwise valid `web_search`. The parser now requires an exact integer zero and rejects any unrecognized server tool before certifying the search receipt. Fixed regressions assert `search_status=unverified` and `search_receipt_id=null`; provider/CLI behavior remains `insufficient_evidence`/unscored.
- Final isolated suite across `tests/unit/test_llm_client.py`, `tests/unit/test_llm_provider.py`, and `tests/integration/test_quick_scan_cli.py`: **160 passed**, warnings-as-errors. The targeted Anthropic tests were 17/17 before the final suite. Ruff and Black no-cache checks passed for `src/providers/llm_client.py` and `tests/unit/test_llm_client.py`.
- Independent read-only review verified the exact seven-file StockQA code/test hash set, ran eight focused unit/CLI cases, confirmed sync and async fail-closed dispatch behavior, and found no P0–P2. Afterward, the live harness test file received only explicit `encoding="utf-8", errors="replace"` for captured subprocess output; an additional exact-hash review confirmed this changes decoding only, not CLI calls, attempts, or request count.
- One authorized, bounded MiniMax-M3 public CLI live attempt was made against the current fixture. The transport ended with `ConnectionError` before an HTTP response; the structured result was `error` / `unverified`, with no HTTP status, response/request ID, search call, source, or score. This is a failed attempt, not a successful live receipt. It was not retried. The first pytest collection had failed before making any request because the temporary pytest config omitted the `live` marker; the subsequent live run reached the child CLI but pytest's parent process tried to decode its UTF-8 output as GBK. The harness decode was corrected; the subsequent offline live suite collected **4 expected skips**, and Ruff passed. Whole-file Black check for the existing live test file still reports formatting differences in unrelated earlier test blocks; no broad reformat was applied.
- Every pytest/TEMP sandbox created for this work was under a unique directory in the authorized invest-quick-scan workspace and removed in `finally`; a post-run directory check found no `.q02-*` leftovers. API key values were neither read into output nor written to files. No further live calls or document downloads occurred.
- The live-result JSON contains no raw model answer or provider payload and is unverified; the temporary result and CLI logs were deleted with the sandbox. The exact current hashes, commands, review status, live failure semantics, and remaining gate are recorded in `docs/implementation/contracts/validation-Q02-fail-closed-hardening-2026-09-27.md`. Q02 remains partial because there is no current-hash verified search/source receipt.
- After these documentation updates, the local plan validator returned `planning_valid=true` (103 tasks/328 cases/G6); the plan regression file passed 81 tests plus 58 subtests. Scoped `git diff --check` returned no whitespace errors; only the repository's configured LF-to-CRLF notices were emitted.

## 2026-09-27 — Receipt-chain freshness audit

- Ran the public read-only verifier against P00, P01, C01, C07, G0, S01, and S04. P00 remains `eligible_to_close=true`. P01 is the earliest current blocker with `evidence_hash_mismatch` and `review_stale`; C01/C07 and G0/S01/S04 are consequently ineligible through current dependency edges.
- Compared P01's five-file implementation snapshot. Only `docs/implementation/contracts/task-receipts.md` differs (receipt expected `081ffa75...`, current `e6dc311c...`); the schema, CLI, example, and test hashes still match. The prior approved review binds the old implementation snapshot `017318f7...`.
- S04 already has specific evidence for MOD-02 and MOD-14.A01–A10: each assertion has its own actual test selector, shared test-log hash, zero skips, cleanup evidence, and an approved review for the prior S04 snapshot. A direct current-file comparison found an additional S04 snapshot drift: `schemas/quick_scan/route-decision.schema.json` is now `9c4035da...` vs the receipt's `1bca5d2b...`. Therefore S04 itself also has stale evidence/review; refreshing only dependencies is insufficient. No S04 files were changed during this audit.
- A new read-only review of the current P01 snapshot is pending. After it returns, refresh P01's exact snapshot/review binding. Then revalidate the affected S04 route-decision schema boundary and refresh S04's review/receipt, followed by only the downstream receipt/manifest chain affected by these tasks in one milestone-level batch. Reuse unchanged isolated logs unless the review identifies a semantic gap; do not rerun unrelated product suites.
## 2026-09-27 — G0 candidate dependency-cycle repair (follow-up pending)

- Fresh public verification confirms P00, P01, and C01–C07 are currently eligible; the receipt hashes are recorded in their current files. Older G0/S01/S04 dependency bindings are stale and are not reported as closed.
- Fixed `scripts/g0_candidate_manifest.py` so the G0 candidate dynamically excludes mutable receipt and validation outputs for every transitive task descendant while retaining prerequisite receipts and implementation/test sources. This removes the G0→downstream-receipt hash cycle as the task plan evolves.
- Independent review found two P2 gaps: malformed/unknown dependency IDs were silently ignored, and tests checked wildcard declarations without exercising actual validation paths. Both were fixed with explicit fail-closed validation and a temporary-root candidate render that contains predecessor and descendant artifacts.
- Isolated command `python -B -X utf8 -m pytest -p no:base_url -p no:cacheprovider --basetemp <unique TEMP> -W error -vv tests/test_g0_manifest.py`: **13 passed**, zero skips, cleanup verified; no provider/API/network access. Evidence: `docs/implementation/contracts/validation-G0-downstream-receipt-exclusions-r2-2026-09-27.log` (SHA-256 `98f7d3441f39b1752470dd2614c717f8c2a05f336b1de9391fc352280226a373`).
- Re-rendered candidate contains 612 scoped files; manifest verify reports zero errors. Candidate file SHA-256 `95037c1f1fcc1cc999c407ba030fd5d9abb78ee3228a59386c5a03c6369e7d4d`; receipt snapshot aggregate `226e37a69e36ea19758924c29e794899326550f51390f8d1026933829307f1bd`. Independent targeted follow-up review is pending; do not refresh G0/S01/S04 receipts until its report is finalized.

## 2026-09-27 — G0 descendant review artifact boundary (re-review pending)

- After G0/S01/S04 temporarily passed the refreshed public verifier chain, checking S05 exposed two changed files inside S05's declared snapshot (`scripts/question_sets.py` from S01 and `tests/test_routing.py` from S06). They require a new S05-bound independent review before S05 can close.
- A new S05 review report would itself be a G0-descendant artifact. The G0 candidate now also excludes each transitive descendant's `docs/implementation/reviews/{task_id}/**` directory, so new downstream review reports do not invalidate the frozen G0 candidate. Upstream review evidence remains included. A temporary-root test checks upstream retention, downstream exclusion, and a neighboring task-name directory boundary.
- Isolated G0 regression batch: **13 passed**, no skips; TEMP/TMP/pytest root removed and verified. New evidence log SHA-256 `c69417f8578c189a09f43627a4ccba175aace8eb268d3a2a2128e80c587f118a`.
- Candidate was re-rendered to 535 files and `g0_candidate_manifest.py verify` returns zero errors. Current raw candidate SHA-256 `106f3e94cb648d089f3f9bb40e22fbf3b4279eed670c2985ce8429252c3520c3`; receipt snapshot aggregate `f8a20a7e67053e1c3346eac6acd37733e513325036b656bacef4a752728c65bf`. The prior G0 receipt and its S01/S04 descendants are stale against this new candidate and must not be represented as currently eligible. Targeted independent G0 re-review and current S05 snapshot review are pending.

## 2026-09-27 — G0/S01/S04/S05 receipt chain refreshed

- G0 follow-up review approved the additional dynamic exclusion of all 93 transitive descendants' review directories. The current 535-file candidate SHA-256 is `106f3e94cb648d089f3f9bb40e22fbf3b4279eed670c2985ce8429252c3520c3`; aggregate receipt snapshot SHA-256 is `f8a20a7e67053e1c3346eac6acd37733e513325036b656bacef4a752728c65bf`; report SHA-256 is `ca9ccbf902f961cf4cdac71c3fda147c5c4900f8e26eda6b228699ad70cd7f6e`. Manifest verify remains 535 files / zero errors after downstream reports were added.
- G0 receipt was rebound to the final candidate and r3 isolated log, then the public verifier returned `eligible_to_close=true`, zero blockers. Its core SHA-256 is `408d67cd52dcc8bd4bc018c1689f065dc9e902e2dd57cf373551de81e9c939f5`.
- S01 and S04 dependency receipts were rebound to current G0/S01 receipts and each public verifier returned eligible. Current raw receipt SHA-256 values: S01 `8c80d6ffaf1a7cf94bb13e6f95dc070cf5198b759b596491cb58fbad740757af`; S04 `5a47f30f46156dd0be899f9cb53105472b477eb22dde36d01fd27c2f1aa904d1`.
- S05 required a current-snapshot review because its declared files `scripts/question_sets.py` and `tests/test_routing.py` had changed in dependent S01/S06 work. The independent review approved aggregate snapshot `8eee2a911978139fe60f4ec44765e6dfd17dbe095f676e069f6fa09154b5b4bb`; the receipt was rebound and public verification returned eligible. Current raw S05 receipt SHA-256: `80861875b8edb6443baf93c8b9004284909d0af54fc7ea65974dd0055fe1e9fb`.
- The public chain P00, P01, C01–C07, G0, S01, S04, and S05 is current and eligible. These local evidence refreshes did not use provider APIs, web search, or downloads.



## 2026-09-27 — Q02 current MiMo live gate attempt

- After the prior offline hardening and review, ran exactly one selected current-worktree public CLI live E2E for MiMo (`mimo-v2.6-flash`) on Microsoft. It failed closed: CLI return code 1; answer `error`; search `unverified`; no HTTP status, response ID, search-call ID, or source URLs. No retry was issued and no successful provider receipt is claimed.
- This result is recorded at `docs/implementation/contracts/validation-Q02-MiMo-current-live-2026-09-27.log` (SHA-256 `12c5f406935be9eac953add1a8daf7bd1e1eec944213367a53dee9c9eaa3afde`). The bounded pytest root and nested live-test sandbox were both removed; the log was checked against the current `MIMO_API_KEY` value and contains no key. The test used no downloaded documents and no persistent company data.
- Q02 stays partial until the provider failure is diagnosed without unsafe retries and a current public CLI run yields a verifiable search receipt. An independent read-only milestone review is in progress; no StockQA source changed during this live attempt.


## 2026-09-27 — Q02 independent current-gate review

- Independent read-only review of the current StockQA implementation found no P0–P2 in the offline Q02 implementation. It checked LLM-02 and LLM-11 source-bound evidence, canonical provider attribution, route alias separation, unsupported-route preflight, invalid-request behavior, and negative-search receipt cases.
- Q02 cannot be sealed: the current LLM-01 live CLI gate has no successful response/search receipt. The MiMo error with no HTTP status/request response identity remains outcome unknown; the reviewer explicitly advises against treating it as pass or blindly retrying. Existing 160-case offline evidence remains valid for its unchanged snapshot but cannot replace live acceptance.
- The user-provided Brave/Tavily quotas remain recorded in `task_plan.md` as an independent search-service budget input, separate from model priority and LLM usage accounting. No Brave/Tavily requests were made in this turn.

- A final public read-only receipt check returned `receipt-Q02.json` as `legacy_historical`; the Q02 receipts currently present are v1 and do not provide a current v2 eligible-to-close record. The current task must remain partial pending a valid current-version live receipt and subsequent sealing.


## 2026-09-27 — Q02 live acceptance follow-up and harness regression

- A distinct Amazon public-CLI MiMo request returned scored/9, HTTP 200, `search_status=executed`, one search event, six sources and response/search receipt presence. The one-off logger retained only counts/presence flags, not the exact response/search IDs or source URLs; this is a useful live smoke result but is insufficient as a fully auditable sealed receipt. Evidence summary: `docs/implementation/contracts/validation-Q02-MiMo-Amazon-current-live-2026-09-27.log` (SHA-256 `ae980bd599c6a4fd9a9b7de7ad7fe51dd7210b270d6266f8fa696c9c48afe2b9`).
- A later Apple public-CLI invocation did not create `result.json`; the one-off wrapper raised before retaining subprocess diagnostics. It is explicitly recorded as `outcome_unknown`, not pass or definite pre-send failure, at `docs/implementation/contracts/validation-Q02-MiMo-Apple-outcome-unknown-2026-09-27.log` (SHA-256 `3f4e5b150a5f9cbf5243bb6c4f451e1afd2f4d92e120b2c0aa9656adbb46b597`). No retry was made.
- This exposed a live-test harness gap. In the already authorized StockQA repository, only `tests/live/test_live_quick_scan.py` changed: all five CLI-result reads now use a secret-safe loader that reports bounded metadata for missing/invalid result files without echoing process output or payload; two offline regression tests cover those cases. Isolated run: 2 passed, 4 opt-in live tests skipped; no API keys/live opt-in in the test environment, no network, and pytest TEMP root cleanup verified. Ruff and local Black line-range check passed. Test log SHA-256 `c0b32a670e36998184c4f53163d945dfaf0f90ad3e19ef6065a495fc2506c929`. Whole-file Black remains intentionally unclaimed because pre-existing blocks need unrelated formatting.
- Q02 remains partial: no current v2 receipt exists; the present receipt is v1 `legacy_historical`. The previous independent review found no P0–P2 in the production implementation, but it predates this test-only hardening and did not replace the live gate.

## 2026-09-27 — 松耦合边界与TDD测试补强

- 新增 tests/test_producer_pipeline_e2e.py：一个隔离单元测试确认离线子进程剥离所有provider密钥/live opt-in；两个真实本仓CLI的离线集成/E2E测试分别证明question compose→standard answer build→exchange schema/hash有效，以及prompt哈希错配被拒绝且不产生观察文件。
- 更新 docs/system-contract.md 明确数据拥有者的契约边界与跨仓流向；更新 docs/implementation/test-strategy.md 明确红/绿/回归节奏，并区分本仓离线producer E2E与真实跨仓/实网E2E。
- 验证：新增E2E 3 passed；标准观察组23 passed；交换/query契约15 passed；隔离清理17 passed。题库校验48模块/222评分题通过；实施计划校验103任务/328场景/G6通过；downloads目录为空，E2E隔离目录与中途诊断临时目录已清理。
- 一次全仓unittest运行超过5分钟持续高CPU，本轮中断；不把它记作通过。运行输出中的StockQA S02为既有虚构fixture CLI路径；临时目录事后核实不存在。本轮没有发起真实模型或搜索请求。
- 仍未验收：实际StockQA公开执行与Q02联网搜索、StockWiki观察事务/ACK、UI与启动器、主题/行业消费者全链。新增本地E2E不替代X09/E2E-06/G6。


## 2026-09-27 G0依赖回执刷新与用户股票池输入边界

- 按planning-with-files解析器恢复根目录legacy计划并核对当前git差异。公共回执P00、P01、C01–C07、G0均`eligible_to_close=true`；G0候选manifest验证为`scope_files=536, errors=[]`。
- G0回执更新后，S01、S04、S05仍引用此前的回执字节。逐个比较发现失效点只在依赖回执引用；实现快照、日志及独立review引用均未漂移。按依赖顺序更新S01、S04、S05的dependency evidence hash与receipt core hash，公开只读递归验证依次返回eligible，无blocker。
- 本步骤没有改动产品源码，没有触碰StockQA/StockWiki/company-wiki外仓；未调用网络/API。仅重验收据链，不需重跑产品测试。
- 记录用户的股票池来源指示：初始几百家公司池由用户提供，2000家是后续规模目标，工具不得替用户自行选出名单。O01必须基于用户提供的池进行导入、去重、覆盖报告；当前未收到名单，未执行公司筛选或扫描。
- 上一阶段的离线生产链路E2E仍为3/3通过，独立复审边界仅限本仓离线producer；全量unittest此前因高CPU被中断，仍不得标记为通过。

## 2026-09-27 — Q02 MiniMax Anthropic 官方区域端点与 CLI 诊断

- 按此前用户授权，仅在 StockQAbyLLM 已报备范围内更正 MiniMax 有效 Anthropic Messages fixtures 和能力 allowlist：中国区从错误的 `api.minimax.cn` 改为官方 `api.minimaxi.com`，全球端点 `api.minimax.io` 保留；错误域名继续作为拒绝用例。live E2E 默认值同步为中国区官方端点。
- 诊断断言现输出已有脱敏回执摘要，包括 `insufficient_evidence` 的安全原因；摘要不含prompt、原始响应或API key。四个被改文件当前 SHA-256：`src/providers/llm_client.py` `C762F12D44251682BFEE43DE5CA1AD2A4C64C1C4F73B25BD91776BE3813F7D88`；`tests/unit/test_llm_client.py` `0DBDD8FF46C93C6F5575FF54809D403F645BCB77AC8BD858AD922115851CD4A7`；`tests/integration/test_quick_scan_cli.py` `F9597744B051581843D999E9050DDD9AB81DF8600CFB58953F8CA83EDD27AF5B`；`tests/live/test_live_quick_scan.py` `398EC188D835F4DAE3EA6C2D1CD97E2A6B6B1B73CF6DE2130D19B3B28201A4EB`。StockQA工作树还含大量此前已存在的更改；没有重置或覆盖它们。
- 无密钥/live opt-in 的隔离回归为 34 passed / 125 deselected；live 测试文件非联网辅助用例为 2 passed / 4 deselected。离线精确 CLI 注入测试加载正确provider、模型和端点，`supports_web_search=true`，stub响应经公开CLI形成`search_status=executed`与来源回执。TMP/pytest根已删除；预存`.coverage`哈希未变；API key值未打印或写入。
- 两次修正后 MiniMax Anthropic live CLI 均在HTTP发送前返回 `insufficient_evidence` / `search_status=unavailable`，无provider、无attempt、无HTTP/response/search receipt、无来源，故不是搜索成功，也不是MiniMax服务端拒绝。相同provider/模型/端点的离线能力解析为true，live子进程却表示不支持，具体配置路径差异仍未解释。为避免对同一问题盲目重复调用，不再发live请求；Q02/LLM-01保持partial。
- 官方区域端点依据：[MiniMax Server Tools](https://platform.minimax.io/docs/guides/server-tools) 与 [MiniMax Anthropic-compatible API](https://platform.minimax.io/docs/guides/text-generation)。脱敏测试细节和精确命令见 `docs/implementation/contracts/validation-Q02-MiniMax-CN-endpoint-2026-09-27.md`。

## 2026-09-27 — Q02 全球端点单次验收的隔离故障

- 精确复刻当前 Anthropic live fixture 的离线公开CLI诊断通过：配置API key留空、子进程沿用环境key读取路径、官方中国区主机/路径；安全审计显示能力检查为true、HTTP stub在正确路由被调用、最终仅包含合成`example.invalid`来源。端点覆盖环境变量未设置。
- 此前授权下只启动一次 `api.minimax.io/anthropic/v1/messages` live pytest节点。测试进程运行约12秒后退出3；节点显示FAILED，pytest-cov全局HTML报告收尾因StockQA `htmlcov`写权限触发internal error，遮蔽实际断言和结果回执。视为可能已派发的`outcome_unknown`，没有再次调用。
- 外层与内层临时测试目录已清理。覆盖率文件及HTML报告时间戳为当天08:38 UTC，早于测试约22:55 UTC；未发现本次改写证据。今后live测试需用 `-o addopts=` 禁止项目全局HTML报告路径污染仓库根目录。
- Q02仍partial；此项离线诊断不证明真实搜索。当前没有收到用户提供的初始股票池，因此不选池、不导入、不扫描；继续推进与名单无关的本仓工作。

## 2026-09-28 — S03归档评分锚点回归补强与股票池边界

- 在真实不可变发布包归档回放测试中增加两项反篡改子用例：变更同一题目ID的prompt或rubric版本后，旧manifest必须被归档契约拒绝；同时显式断言未篡改历史运行仍保留原7分。焦点pytest结果为1 passed、2个子用例通过，`-W error`，仓库级 addopts已关闭；临时basetemp已按仓内路径校验后清理。
- S03仍partial：这补强的是当前归档包契约，不是不存在的3.1.0真实历史manifest验收。初始股票池不由实施者挑选；已通过输入问题请用户提供文件路径/市场范围或后续名单，等待期间不启动O01导入和扫描。


## 2026-09-28 — 用户股票池输入边界、S06 router 2.3与TDD边界复核

- 用户再次明确不由实施者决定约2000家公司名单；首批几百家的池由用户提供，真实E2E样本也由用户从该池中指定。已从live验收计划中移除预选公司和挂牌样例，未收到名单时只跑离线fixture，不执行选池、导入或扫描。
- S06本地路由信任边界推进至router 2.3 / routing-policy schema 1.3 / request protocol 3。新增StockQA公开`quick_scan_result/1.0.0`适配器，把答案SHA-256绑定到逐题执行回执，核验实体、问题、真实模型、搜索完成状态及来源归属；新执行仍需调用方独立保存的decision_id。补入S06 allowlist与MOD-19；S06仍partial。
- TDD验证：S06隔离security batch 12项通过，CLI集成batch 14项通过，本仓离线producer E2E 3项通过（固定fixture，不是真实公司）；StockQA答案回执单测1项通过，真实StockQA公开CLI形状集成1项通过。StockQA pytest由独立子进程在唯一临时工作区运行，日志锁释放后临时目录自动清理；StockQA正式`logs/`未变化。无真实API/搜索调用，无外仓写入。
- 独立架构审查确认契约/纯函数局部松耦合，但生产跨仓链尚未闭环；本地`standard_answers.py`对`question_sets.py`多个helper的依赖是后续应按owner卡逐步拆分的具体耦合点，详见`findings.md`。已有本仓离线E2E不得冒称StockWiki、UI、启动或实网验收。


## 2026-09-28 — S06完整路由回归与S07提示契约解耦（进行中）

- S06红测复现后将`resolve_route_decision`限定为接收单一完整原始ROUTE_02/StockQA回答，并从同一值派生候选、置信度和答案hash；schema拒绝状态/分数矛盾。独立回执与原答案不匹配、旧拆分字段API均有负例。路由策略schema 1.3/protocol 3接受router 2.3.0及之后的2.x兼容版本；历史2.0—2.2行为不变。
- 当前S06验证：完整`tests/test_routing.py` 33 passed / 23 subtests；S06隔离CLI集成14 passed，临时根已清理；StockQA公开适配器5 passed；本地producer E2E在S06阶段3 passed。真实公司、网络、API、财报下载和外仓写入均未触发。
- 已新增S07和MOD-20—22，正式计划升级到1.10.5：104任务/331场景/53约束，计划校验有效；`tests/test_implementation_plan.py` 82 passed / 58 subtests。计划validator新增`e2e`测试层级。
- S07依赖方向红测先复现question_sets延迟导入standard_answers及缺少独立prompt模块。首轮完整测试进一步发现搬动函数会改变active package的renderer hash并令旧包拒绝compose；恢复旧renderer函数的精确源文本并放入独立纯模块后，当前renderer版本1.0.0和SHA-256 `6b221598394f5c23a5f724c0b9bac895bcb44eee87c9189285eb605a6ebf21fe`保持一致。
- S07当前绿色批次：提示契约单测4 passed / 4 subtests；`tests/test_standard_answers.py` 23 passed / 3 subtests；本地producer E2E 3 passed。`tests/test_question_sets.py`完整回归正在运行；该组红测定位到renderer hash漂移后已中断避免重复无意义运行，当前快照结果待回归确认。
- 所有测试关闭仓库级pytest addopts/coverage输出；测试fixture仅使用example.invalid与独占临时目录，子进程无API key/live opt-in，无网络/下载。首批真实股票池仍由用户提供，未导入或扫描。


## 2026-09-28 — S07本地提示契约与三层回归完成

- S07 dependency boundary完成：question_sets不再延迟导入standard_answers；`question_sets.py`与`standard_answers.py`通过`question_prompts.py`共享提示规则。`tests/test_question_prompts.py` 4 passed / 4 subtests，child process两种导入顺序均成功，子环境不继承API key/live opt-in。
- 向后兼容已实测：评分/事实题提示仍字节稳定，active renderer version 1.0.0及SHA-256仍与当前发布包相同；不生成或激活新发布包。`tests/test_standard_answers.py` 23 passed / 3 subtests；`tests/test_question_sets.py` 67 passed / 170 subtests；`tests/test_producer_pipeline_e2e.py` 3 passed。
- S07后当前快照公共CLI集成14 passed，0失败/错误/跳过，隔离runner `TEMP_CLEANED=True`。计划validator valid（104任务/331验收场景/G6）；计划单测82 passed / 58 subtests。
- 新增提示模块与边界测试通过Ruff；宽范围Ruff调用在周边旧文件报告41条既有格式/导入风格问题（主要为原有分号单行代码），未作无关改写。`git diff --check`对改动tracked文件无空白错误，仅有CRLF归一化警告。
- 本阶段仅在invest-quick-scan写入；无API/联网、真实公司、财报下载或StockQA/StockWiki外仓写入。用户提供股票池与指定live样本尚未收到。

## 2026-09-28 — S08题库契约下沉（本地验证完成）

- 首批股票池边界已按用户要求固定：用户提供前不选公司、不导入、不扫描；离线测试只用固定虚构fixture。
- MOD-23红测先复现：旧答案构建器没有question_library导入，且保留广泛`question_sets` helper访问；清洁子进程无法导入缺失的新模块。新增计划S08/MOD-23—25，版本1.10.6（105任务/334场景/53约束/G6），计划validator通过。
- 独立审查发现MOD-24最初没有直接验证standard_answers的备用ROOT、提示层仍有重复JSON reader。现已新增`json_io.py`作为唯一UTF-8 JSON实现，由`question_prompts`和`question_library`共享；MOD-24在临时ROOT写入专属facts版本标记，直接调用`standard_answers.validate_fact_library/select_facts`验证没有回落仓库目录。
- `question_library.py`承接source catalog、URL语法和profile校验；`question_sets.py`保留旧签名并从可覆盖ROOT传递路径；`standard_answers.py`改用下层契约，AST确认仅保留manifest验证与历史fingerprint两条显式CLI边。
- 最终整批回归覆盖question library、prompt、完整question sets、standard answers、producer E2E和implementation plan：186 passed / 237 subtests。新下层模块Ruff通过；计划validator有效（105任务/334场景/G6）；改动范围`git diff --check`无空白错误。
- 测试只用仓库fixture与唯一临时目录；未调用真实API/网络、未选择或扫描公司、未下载文档、未写StockQA/StockWiki外仓。独立只读复核确认原两项P2均已关闭，无未关闭的S08审查问题。
- 无真实公司、搜索/API、下载或外仓写入；测试用临时目录和无密钥子进程。


## 2026-09-28 — S09题目指纹契约下沉

- 按TDD先加入历史/当前指纹基线、兼容包装和导入边界测试；初次运行因`question_fingerprints`契约尚不存在而失败。
- 新建`question_fingerprints.py`并将唯一算法迁出`question_sets.py`；旧`_question_fingerprint`签名保留为委托入口，`standard_answers.py`改为直接消费下层契约。
- 固定缺省版本标记时的旧算法哈希`30d2fe7d…c814a3c9`与当前2.0.0哈希`64961bb9…c8edb2a`；当前格式资源变化会改变2.0.0指纹。
- 新增S09及MOD-26/27/28，计划同步至1.10.7、106任务/337场景，并加入G6依赖。计划validator通过；计划+指纹单测87 passed/58 subtests。
- 大节点回归第一次执行189 passed/237 subtests，唯一失败为S08测试仍预期旧fingerprint边；修正该过时预期后，聚焦重验13 passed/2 subtests，涵盖题库边界、发布观察校验与producer E2E。新模块、相关新测试Ruff通过。
- 独立只读复审指出MOD-27覆盖措辞过宽；已按实际证据收窄为当前发布包观察验证，并补强固定package ID、旧包装器原签名/关键字及缺省版本分支测试。follow-up确认该P2关闭，无未关闭P0–P2。测试仅用仓内发布fixture、虚构profile和隔离临时目录；无真实股票池导入/扫描、网络/API、下载或外仓写入。

## 2026-09-28 — Q04/Q08验收责任边界校正

- 对照`tasks.json`与`acceptance-cases.json`核实责任：Q04验证LLM-06本轮dispatch结果和停止fallback，Q08持久化冷却、半开探针与跨运行`retry_wait`；Q04剩余PAR-11与LLM-10分别是容量等待和运行中策略更新。
- 共享并发PAR-03由Q11负责，StockWiki设置接线PAR-08由X09负责。修正`task_plan.md`当前摘要并在`findings.md`记录来源；未改写旧receipt、实现代码或外仓文件。
- 计划验证通过（106任务/337验收场景/G6）；`tests/test_implementation_plan.py` 84 passed / 58 subtests；限定`git diff --check`通过。pytest自动清理其独占临时根，核对后没有临时目录残留。此文档收敛不改变任何已验收范围，也不关闭Q04/Q08。

## 2026-09-28 — S10 module boundary closeout

- Split selection/budget ownership into question_selection.py, published-manifest semantics into question_manifest.py, and screening renderer/hash into question_prompts.py. question_sets retains legacy wrappers; standard_answers no longer imports the orchestration module.
- Added MOD-29/30/31 for unit, integration, and isolated offline producer E2E coverage; added a plan regression test to keep S10's exact ownership, levels, and G6 dependency explicit. Corrected the renderer assertion to an existing compatibility test.
- Focused module/library/fingerprint/standard-answer/producer checks passed 41 tests plus 9 subtests; final MOD-29/30/31 selection passed prompt boundary 4/4, manifest boundary 3/3, published-observation integration 3/3, and producer E2E 3/3. The prompt boundary regression also caught missing question_sets.applied_contexts and ANSWER_RULE compatibility aliases; both now delegate to question_prompts and all four prompt tests pass.
- The broad test_question_sets.py run passed 65 tests and 170 subtests but initially failed two exact error-message assertions. After restoring compatibility wording, those two tests passed in a focused rerun; the full file was not rerun. Plan validation passes at 107 tasks / 340 cases / G6; test_implementation_plan.py passes 85/85, Ruff and py_compile pass, and the scoped git diff --check exits 0 (only repository LF/CRLF notices).
- No company list was selected, imported, or scanned; no real model/search/network request, download, or external-repository write occurred.

## 2026-09-28 — S03 local durability regressions revalidated

- Re-ran the six S03-focused question-set regressions: durability preconditions/falsifiers, net economics after legacy loss and financing, pre-revenue replacement, no unapproved bridge or automatic diagnostic, archived-package isolation, and rejection of a fabricated older header; all 6 passed.
- Re-ran the mature-company cyclical-trough recovery composition regression; it passed and confirmed recovery diagnostics do not alter the core score.
- Rechecked source availability: the only local Git commit's catalog is 3.0.0 and there is no configured remote or authentic catalog 3.1.0 metric manifest. The archived 3.0.0 module assets/current package replay is verified; no 3.1.0 history is inferred from a changed version header.
- S03 remains partial for the documented missing historical artifact plus StockWiki refresh and live E2E gates. No genuine-company list, import, scan, or network request was used.

## 2026-09-28 — Pause checkpoint: candidate-pool discovery and W01 review

- User directed discovery of existing `*companies*.txt` / `*list*.txt` files under Projects; no 2,000-company universe was self-selected. Accessible scan enumerated 96 matching files (88 company-list names); some generated cache directories denied traversal. Eight unique selected source snapshots yielded 547 exact-deduplicated candidate rows and 209 possible name overlaps, preserved separately. Outputs: `docs/implementation/universe-inputs/company_pool_candidates_2026-09-28.csv`, `possible_name_matches_2026-09-28.csv`, and `company_pool_inventory_2026-09-28.md`.
- These are unverified discovery candidates only. No pool import, company scan, LLM/API/search request, or document download occurred. Await user review before selecting/importing a scan universe.
- Reconciled current StockWiki checkout: W01 store/test/gitignore files were absent despite stale earlier progress receipts; the previously authorized three-file W01 scope was implemented. Isolated store tests passed 7/7 and Ruff passed; temporary test root was removed. No live DB or company data was touched. Existing unrelated `StockWiki/.claude/` remains untouched.
- Independent read-only review found five P2 W01 integrity/robustness findings (details in `findings.md`); W01 is reopened/partial. Next resume: fix those findings with isolated regressions, then run scoped milestone checks before proceeding to the already authorized W02/W03 files.
- User requested pause. No further implementation is authorized in this turn.

## 2026-09-28 — Issuer identity resolution design checkpoint

- Responding to the user's identity-uniqueness concern, inspected Dayu and StockInfoDLSimple read-only using CodeGraph. Dayu normalizes tickers with market/exchange, but `ticker_to_company_id()` derives a venue/ticker-local key and its source comments reserve cross-market issuer mapping for future work. StockInfoDLSimple normalizes six-digit A-share codes and maps them to CNINFO `orgId`; that is an A-share/provider crosswalk, not a global issuer ID.
- Added `docs/implementation/reviews/W03/identity-resolution-architecture-2026-09-28.md` and linked it from the W03 provisional identity design. The proposal separates source candidate, issuer, tradable security/listing, and namespaced identifier/alias claims; assigns opaque internal IDs; makes matching evidence-tiered and fail-closed; leaves name-only and ambiguous rows unresolved and unscanned; treats LLMs as candidate/evidence assistants only; preserves identity revision/history through rename, ticker reuse, merge, and split; and specifies a seven-part test matrix.
- At this checkpoint the identity architecture was only a proposal; the subsequent Phase 39 synchronization and Phase 40 local C01 v2.1 work below supersede that status. No Dayu or StockInfoDLSimple business source was written. StockInfo CodeGraph index initialization was explicitly approved by the user and completed (46 files indexed).
- W01 regression cases had been appended to its already authorized StockWiki test file before this identity-design steering; they are still unrun. No StockWiki implementation fix has been made for the five P2 findings yet. The local C01 contract and plan are now aligned; next resume with the authorized StockWiki W01 red/green fixes, preserving the user's repository write boundary.

## 2026-09-28 — C01 local identity contract v2.1

- Converted the identity model to three explicit layers: opaque issuer `entity_id`, security/share-class `security_id`, and venue/time-qualified `listing_id`. Names and tickers remain sourced claims, never primary keys. Parent/subsidiary identity stays separate; group relationships do not imply issuer equivalence.
- `validate_entity` now accepts only v2.1 new writes. v2.0.0 uses `validate_identity_v20_read` as a historical compatibility reader and cannot authorize writes or scan eligibility. The v2.1 validator checks issuer/security/listing ownership, source bindings, exact provisional listing receipts, full verified issuer/security/listing receipt coverage, ADR links/ratios, duplicate IDs and venue-qualified listing keys.
- The contract document and alias/identifier schema now describe non-unique names, namespaced identifier claims, and exact security/listing subject IDs. Regression coverage exercises same ticker on separate venues, source raw/normalized field mismatch, ambiguous scope receipt, extra/missing verified receipt IDs, foreign references and historical-v2 write rejection.
- Focused regression batch: 125 passed / 138 subtests across identity contract, identity-bound work/observation, G0 and plan tests. Identity schema validation, targeted Ruff and `py_compile` passed.
- This closes only the local C01 schema/validator/documentation slice. StockWiki authoritative storage, resolver, import/UI, identity-event history, cross-project E2E, and identity-bound production work/observation migration remain pending. No company pool was imported/scanned; no model/network/API/download or external-repository write occurred in this slice.

## 2026-09-28 — C01 identity contract 2.2 / analysis subject boundary

- Re-read the current local identity contract before continuing. The important gap is that `entity_id` identifies a legal issuer while a company-level scan may describe a consolidated reporting perimeter. Preserved the issuer meaning and added an independently versioned `AnalysisSubjectV10` (`analysis_subject_id` + `analysis_subject_revision`) with explicit scope kind, primary issuer, as-of date, evidenced effective memberships, and coverage completeness.
- A provisional issuer can only form a subject anchored to one exact listing and cannot claim consolidated scope. Verified issuer subjects can be standalone or consolidated. Parent/control relationships alone do not establish consolidation. This affects later Work/Observation and query contracts, so C04/C06/W05 and W02/W03 task cards now carry the dependency; historical records are not assigned synthetic subjects.
- An already authorized read-only independent review of the local v2.1 identity contract found six defect classes. Fixed locally: worldwide ISO alpha-2 market codes; verified alias/identifier evidence and valid interval checks; fail-closed overlapping ticker cases when either MIC is missing; required security-added event target IDs and exact before/after snapshot application checks; active vs retired source binding consistency for delisted listings; and direct v2.1 coverage for similar-name IDs and immutable revision transitions.
- Added contract regression tests for each class. `pytest -q -p no:cacheprovider tests/test_identity_contract.py` passes **36 tests and 50 subtests**. Draft7 identity schema validation and `py_compile` pass.
- Synchronized local identity, freshness/Work, exchange/query, and system contract docs. Plan version is now 1.10.11 with 107 tasks, 360 cases, and 55 invariants. No external repository was written, and no live company/model/network request or document download occurred.
- Still pending: run the merged affected C01/G0/plan regression batch; obtain a second independent review of the corrected snapshot; refresh the now-stale P01/dependency receipts and verify a current C01 v2 receipt. StockWiki consumer work remains confined to explicitly authorized files and is not represented as complete.

## 2026-09-28 — C01 identity boundary final follow-up

- Added the independent review's final uncovered negative fixture: identity-transition snapshots that point a Listing at a Security owned by another issuer are rejected even when the referenced Security exists. The adjacent phantom/dangling Security reference remains covered as a separate case.
- Ran the merged identity/G0/implementation-plan/freshness/exchange-query regression batch after that addition: **170 passed / 160 subtests**. The focused identity file passes **36 tests / 50 subtests**; Ruff, `py_compile`, plan validation (107 tasks / 363 cases / G6), Draft7 schema validation through the identity tests, and `git diff --check` pass.
- Independent read-only final review confirmed the snapshot reference checks and pure primary-issuer role-swap rule; it found no remaining P0–P2. No cross-project source was changed and no company/live search/API/document download was used.
- Formal C01 receipt remains blocked by historical task/case/global-boundary hashes, missing/changed assertion closure, stale evidence/review and ineligible P00/P01 dependency chain. The read-only public verifier was run and confirmed this; no receipt was edited or backfilled. Therefore this closes local contract/test work only, not C01 or cross-repository identity delivery.
- Remaining owner work is explicit: load and version a complete trusted ISO/MIC registry, persist and authenticate consolidated-perimeter receipts with transaction/CAS and global uniqueness, integrate StockWiki W02/W03, migrate compatible C04/C06/W05 boundaries without assigning synthetic history, then refresh the approved receipt chain.
- Checked the next W01 task card before any external write: it depends on C01, C06 and G0, whose current receipts are blocked, so the gate is not open yet. Read-only receipt status is P01/P00 blocked on stale global-boundary hashes; C01 also has stale task/case/evidence/review closure and ineligible dependencies. The W01 authorization remains unused.
- Re-ran P01's verifier tests with the repository-rooted module invocation (`python -m pytest --rootdir=. -p no:cacheprovider -vv tests/test_task_receipts.py`): **29 passed / 30 subtests**. A direct `pytest` entrypoint first failed collection because this Windows environment resolved a conflicting `scripts` namespace; the explicit Python module invocation imported the repository module and passed. This was a diagnostic run only; no receipt/log was sealed from it.


## 2026-09-28 — BENCH-01基准实验设计纳入计划

- 将“搜索结果如何交给LLM、30题逐题还是合并、准确度/耗时/价格及缓存影响”设计为独立真实配对实验，不先验决定逐题或打包胜出。Brave/Tavily输出统一成短证据context，附稳定source_id、URL和时间字段并视为不可信输入；原始检索响应及公司文档不落盘。
- 设计六种调用臂：逐题顺序、逐题并发、每批3/5/10题和单批30题；打包与搜索源分别对照，防止混淆变量。固定题库、rubric、公司身份/报告范围、信息截止时点和同一配对组的实际模型revision。
- 分别测搜索缓存、provider前缀缓存、应用答案缓存的冷/热/失效；盲评问题覆盖、来源支持、评分误差及critical claims，另报端到端耗时、尾延迟、搜索/模型/重试真实支出。MiniMax套餐quota与额外现金成本分开，不虚构单位成本。
- 新增计划任务B01、live验收BENCH-01及I56；BENCH-01先于L03，并要求实验结论在G3大节点审查。3家样本结论标为pilot；无打包策略通过冻结质量门槛时保留逐题方案。
- 依据官方价格/能力页面形成的运行前快照线索已写入实验设计，实验执行日必须重新核验；本轮只更新设计与测试计划，没有调用公司真实API、搜索或消耗额度。

- 独立只读计划审查提出了缓存归因、阈值/盲评、来源复核快照、小样本时延统计和检索器×打包交互五项改进。本轮已将前三层缓存改为正交子实验；预设双人盲gold与明确误差门槛；保存与实发内容一致的限长snippet；以公司级run报告时延，小样本不报虚假p90；联合推荐增加2×2交叉门。
- BENCH-02作为真实入口的零花费fail-closed前置回归，价格、额度或硬预算不明时必须零外发/零预留。它是验收规格，尚未执行。
- 二次独立审查后再锁定三项：打包方法相对逐题基线MAE容忍≤0.25分、source support/可评分覆盖各不低5个百分点；claim审计按每公司×方法至少max(10题、2题/模块)分层抽样、每方法≥30条事实主张，样本不足结论为inconclusive；方法执行严格按manifest随机顺序。同步写入任务卡和BENCH-01断言。

## 2026-09-28 — P00/P01续验与任务工件边界

- 公开receipt verifier当前复核：P00因task_spec/global-boundary hash过期而阻断；P01因global-boundary、P01文档实现快照及preseal review过期而阻断。C01另有ID-02 case/assertion与证据/复审闭包差异，并依赖未关闭的P00/P01；C06/G0依赖也未关闭；W01只有legacy_historical，不得声称完成。
- 修复P00任务卡与receipt契约文档不一致：任务现在允许在contracts目录签发当前P00 v2 receipt和校验日志/sidecar、在reviews/P00放对应独立review，同时保留baselines里的旧v1字节。文档不再硬编码过期的计划版本。
- 新增计划回归用例检查上述精确路径与历史文件保护。第一轮用例发现路径字符串过于合并，已拆成回执与校验日志两项后重跑通过。
- 续查还发现P01任务卡没有明确允许其实际生成的`validation-P01-current-*.json` detached sidecar。已将receipt core、日志、sidecar JSON分列，并新增receipt测试锁定sidecar路径。
- 实际验证：`python -B -X utf8 -m pytest --rootdir=. -p no:cacheprovider -q tests/test_implementation_plan.py tests/test_task_receipts.py` = 117 passed / 98 subtests；`implementation_plan.py validate` = 108 tasks / 365 cases / G6；Ruff通过；`git diff --check`退出码0（Git报告既有的LF/CRLF规范化提示）。
- 新测试日志保存在`docs/implementation/contracts/validation-P01-revalidation-2026-09-28.log`。独立P01预封存复审已启动，回执core尚未重封；当前receipt仍保持blocked，不能将以上测试通过等同于P01/P00任务关闭。

## 2026-09-28 — BENCH-01官方计价复核与模型对照分层

- 用户要求以后对A/HK/US各取1—2家公司真实比较搜索context传递、30题逐题/并行/分组策略、准确度、总耗时、总费用和缓存。总体方案已在Phase 41/B01预注册，当前只补强方案，没有发起本轮真实公司模型请求或API付费实验。
- 实验说明已新增模型分层：MiniMax-M3作粒度锚点；逐题基线和通过质量门槛的打包候选再分别在MiniMax-M3、MiMo Flash、DeepSeek Flash独立匹配区组复现。禁止跨模型拼答案；次阶段预算不足时不把单一模型结论外推。
- 2026-09-28核对厂商公开信息：MiMo-V2.6-Flash按量价及联网搜索单独计费；MiniMax Token Plan是共享额度，有5小时/周窗口，套餐标称吞吐不能伪装成每题边际成本；DeepSeek Flash区分cache-hit/miss并按峰/非峰时段定价；Brave公开页面的请求价与用户说明的实际账户不限量计划需分列；Tavily按credit和请求深度计量。所有值只是计划期官方线索，BENCH执行前还要冻结页面、账户计划与本run usage。
- 继续整改P00/P01路径边界后重跑：`tests/test_implementation_plan.py`与`tests/test_task_receipts.py`共**117 passed、105 subtests**；plan validate为**108 tasks/365 cases/G6**；Ruff通过；diff check退出码0（只有既有CRLF提示）。验证日志`docs/implementation/contracts/validation-P01-revalidation-2026-09-28.log`已更新。
- 收窄P00日期报告到可执行glob、将JSON sidecar和日志拆成真实glob；增加真实路径正反匹配和历史`receipt-P00.json`固定SHA保护。独立r8复审正在核验该快照；P01/P00 receipt尚未重封，公开校验器仍报告当前回执blocked。
- r8最终复审通过，无P0/P1/P2：报告`docs/implementation/reviews/P01/preseal-review-independent-r8-2026-09-28.json`，SHA-256 `d30cdc9f3dc69076b226feaadde2657ecc4980a3620ab76fa0182db37edfd241`，绑定实现快照`6cbc52ee7015724e721702e1526eb8fc44262c0c5e72001885890195cede4f6a`。审查者运行范围测试为118 passed/105 subtests；当前主进程重跑为117 passed/105 subtests（多出的1项是reviewer额外执行的ID-02 selector）。P01 core和回执验证仍未重封，当前P01/P00关闭状态仍为blocked。
- P01已按当前receipt v2契约重封：刷新当前任务/case/global-boundary hashes和5文件实现快照；补入`RCPT-03.A05`的独立测试日志证据；绑定r8 pre-seal review。公开verifier现输出`eligible_to_close=true`、无blocker；detached sidecar位于`validation-P01-current-2026-09-29.json`，文件SHA-256 `8ee20fe4a1b0bb32083b13347473beb7c9c95d15e098cd1cec98602ce438efc1`，core SHA-256 `11714c14554f82f4a7a08cbbf9fd8f6ba1e38a758d6c0d02ff174d19a700aff9`。不同审查者的post-seal evidence review已启动；完成前不标P01正式关闭。
- P01封存后复核已批准：`docs/implementation/reviews/P01/postseal-evidence-review-independent-r1-2026-09-29.json`，SHA-256 `3447a3d9ac4d92fe92c2c7cc81782b37e6e0239d1eaf67fef30fb18719aa7421`。复核者独立重算receipt/core/sidecar/validator哈希，重新运行只读validator，确认输出除evaluation timestamp外与sidecar一致、3 cases/19 assertions均通过，历史P00依赖仍为context-only。P01至此按v2关闭包验证通过；下一步按契约重跑P00 BASE-01/02。

## 2026-09-29 — P00 BASE-01/02 current-v2 refresh

- Re-ran the P01-manifest integrity comparison. The preserved 2026-09-22 baseline report and legacy P00 receipt still match their pinned SHA-256 values; the legacy receipt remains byte-for-byte unchanged.
- Wrote `docs/implementation/baselines/baseline-report-2026-09-29.md` and captured current local/StockQA/StockWiki/company-wiki revisions, dirty-state counts, relevant source hashes, CodeGraph health, current storage/API boundaries, and test scope. All external repositories remained read-only.
- Ran the actual StockQA CLI integration path against its isolated in-memory HTTP fixture: one test passed and fixture-scored answers stayed exactly 8. An explicit parser probe confirmed `unknown` keeps `score=null`. The external worktree status and representative source hashes were unchanged, and the complete temporary root was removed. No live provider call, company data, API fee, or download was used.
- The scoring catalog validated at 48 modules / 222 questions; the fact library validated with network unused; the current plan validated at 108 tasks / 365 cases / G6.
- P00 pre-seal independent review r1 identified a P2 conflating quick-scan `OrderedSearchProviderCascade` with legacy stateful `ProviderCascade`. The report now traces `LLMRunner._run_single_company` to the quick-scan cascade, distinguishes the legacy class and its different fallback semantics, and records the runner source hash. Independent r2 approved the updated snapshot with no P0–P2.
- Updated current P00 v2 receipt (kept separate from legacy v1) and saved detached sidecar. Public verifier: `eligible_to_close=true`, no blockers, 2 cases / 4 assertions passed. Receipt core SHA-256 `7fb22e43fa54ed4223a29dc68d5723d59fb23020ed19c2ee46a80a823478b43b`; sidecar SHA-256 `1dd382c80c2956ad1b78f8c3a43d7613f686d8a26d57c40145ece57eb2baabdc`.
- P00 post-seal evidence review approved with no findings: `docs/implementation/reviews/P00/postseal-evidence-review-independent-r1-2026-09-29.json`, SHA-256 `fd623f7244ce5c282665fd61e6bd8f35a5a1346d9e18c5412263a7814a41c636`. The reviewer recomputed receipt/core/sidecar/validator hashes, reran the public verifier, matched the complete projection except `evaluated_at_utc`, confirmed all four assertions, the current pre-seal snapshot and unchanged historical P00 v1, and found no evidence cycle. P00 is closed under the v2 receipt contract. C01–C07 and G0 still need fresh receipt-chain validation; W01 remains gated. No other task was started.
## 2026-09-29 — IQS harness lane 接管与活动文件盘点

- 用户将 company-wiki 的 IQS harness lane 施工卡设为当前优先事项，并明确暂停 C01—C07 旧回执刷新。施工卡只读，SHA-256 `516077a6e9af3da41a121f5977225cc662035badcb3bc963dfb4dfe12f32be0a`；未写StockWiki/company-wiki或其他外仓。
- 已冻结本地工作树盘点：`master@25b8d14316c06390450e5a1d8883583bfd039d0d`，792条Git状态路径，47条已跟踪工作树修改、745条未跟踪、0暂存、0删除/重命名；逐文件SHA和保留分类在 `docs/implementation/reviews/IQS-lane/worktree-inventory-2026-09-29.json`，摘要见同名Markdown。
- 本次盘点把question release artifacts视为内容寻址的有效产物，把plans/contracts/tests/source视为活动内容，把旧receipt/review/baseline/log视为需保留的证据。可能过期/被覆盖的工件还没有完成引用图核验，未删除、移动或重置；忽略文件未枚举。
- 同步运行了一次隔离离线C01—C07共享回归：216 passed、149 subtests、0 skipped，run ID `acefba39-32ec-4dfc-82af-4b0cb7b0dec6`，临时根已移除。7个同哈希日志留存但未封存，SHA-256 `420b9d9e7b521c812703d988400dbb2d80195fd105ad629215b538ed3100a870`；没有刷新任何C01—C07回执或引用这些日志声明关闭。
- 下一步按施工卡先交付IQS自有身份包2.2.0公开只读JSON验证CLI和子进程测试，然后在做引用核验/保留备份后退役旧receipt引擎与P01双签流程；四态mapping与跨仓真实golden仍由StockWiki owner产出，G2b之前不写外仓也不自造生产者正例。
- 已将CLI合同拆成ID-27—ID-30四个case、6个atomic assertion并同步至C01计划；当前计划1.10.14为108 tasks / 369 cases / 56 invariants。实现与测试仍待完成，C01—C07 receipt refresh明确暂停。

## 2026-09-29 — IQS lane：身份CLI与任务回执退役收口

- 完成身份包2.2.0只读JSON CLI：Entity 2.1.0和AnalysisSubject 1.0.0按对象/版本校验，读取有界、拒绝重复JSON键；有效/无效/未知版本分别退出0/2/3，stdout为单行结构化状态，不回显输入。计划目录现为1.10.15、107 tasks、366 cases、54 invariants/G6。
- 完成任务receipt v2/P01任务签收退役；当前计划、README、测试策略与交接文档改用批次记录和G0—G6大节点审查。历史receipt、sidecar、review、日志保持原路径/原文；归档副本经manifest hash固定。CLI保留为无输入读取的退役提示，产品provider/search/dispatch结果receipt未变。
- 计划单测80项通过；G0 manifest与退役审计15项/186 subtests通过；身份及退役CLI子进程7项通过。计划校验通过：107 tasks、366 acceptance cases、G6。最终pytest批次采用独立basetemp且确认清理，日志在`docs/implementation/contracts/validation-IQS-LANE-*-r{3,4}-2026-09-29.txt`。
- 过程诊断也已保留：第一次G0回归因本轮`.log`意外被纳入自身manifest而失败；第二次输出捕获文件放在pytest basetemp，Windows清理时遇文件锁。把报告输出移到临时根之外后，最终G0批次通过。没有刷新C01—C07旧回执，没有运行live provider、公司数据、下载或外仓写入。
- 完成`verify_live`明确动作/硬预算契约与可信字段逐项审计；合并最终离线回归75 tests / 248 subtests通过，包括producer-chain golden E2E。trusted identity/search/ingest/content fields无安全可删项；StockWiki/StockQA owner记录的来源、修订和hash仍须由真实producer DTO与公开入口证明，等待G2b，未宣称跨仓闭环。实施边界、2.2.0 hash、测试及保留清单已汇总于`docs/implementation/reviews/IQS-lane/implementation-summary-2026-09-29.md`。

## 2026-09-29 — 独立复审意见收尾

- 修正README、测试策略和Phase 12历史清单中的过期活动回执表述；Phase 12明确标记为被Phase 43取代，C01旧回执刷新要求不再作为当前关闭门。C01—C07刷新仍按用户要求暂停。
- 归档完整性新增固定manifest SHA-256、186条目总数和类别计数检查，防止删掉manifest条目后仍通过；部署request-to-decision集成夹具使用独立活动policy fixture，并断言请求带旧revision时被阻断。此离线fixture不代表生产控制面的真实接线。
- post-review合并离线批次105 passed、298 subtests；G0 manifest/receipt retirement聚焦批次16 passed、186 subtests；计划测试80 passed、53 subtests，validator为107 tasks/366 cases/G6 valid。各批次临时根清理完成；没有网络调用或下载。合并和计划测试只有pytest缓存目录不可写警告；专项G0重跑关闭cache plugin后无该警告。
- 原始输出：`docs/implementation/contracts/validation-IQS-LANE-combined-final-r2-2026-09-29.txt`、`validation-IQS-LANE-g0-final-r8-2026-09-29.txt`、`validation-IQS-LANE-implementation-plan-final-r7-2026-09-29.txt`。

## 2026-09-29 — 用户要求先收尾IQS施工卡

- 重新读取 company-wiki IQS独占施工卡，SHA-256仍为`516077a6e9af3da41a121f5977225cc662035badcb3bc963dfb4dfe12f32be0a`。卡片明确分为本仓步骤1—4与依赖StockWiki真实producer golden的步骤5；本轮暂停S06主线，先逐项验收施工卡。
- 只读检查StockWiki后仍未发现identity snapshot/mapping DTO或真实serializer golden；当前可见`quick_scan_store.py`负责存储identity/security/source binding，但无公开snapshot exporter/mapping状态合同。故G2b仍待owner产物，不使用IQS合成夹具冒充producer正例，也未写StockWiki。

- 卡片范围隔离回归已执行：identity contract/owner-binding/G0 regression/公开CLI子进程、工程receipt退役、deployment/provider failure/freshness、G0 manifest及计划校验合并为205 passed / 351 subtests；未见skip，计划校验107 tasks/366 cases/G6 valid。测试自有TEMP/TMP根清理后不存在；无网络、API或下载。原始日志：`docs/implementation/contracts/validation-IQS-card-closeout-2026-09-29.txt`。
- 已完成施工卡本仓第1—4步收尾报告：`docs/implementation/reviews/IQS-lane/construction-card-closeout-2026-09-29.md`。delta快照为792基线、843当前、53新增、22既有文件哈希变化、2个旧receipt路径已按原哈希归档；详见`worktree-inventory-delta-2026-09-29.json`。完整跨仓卡片仍因真实StockWiki producer golden缺失而保留G2b pending。本轮不继续S06。
- 收尾文档修改后的计划回归80 passed；计划校验107 tasks / 366 cases / G6 valid；delta JSON数量不变量及两份归档原哈希复核通过；`git diff --check`通过（仅有既有CRLF规范化提示）。隔离计划测试临时根已自动删除并确认不存在。

## 2026-09-29 — G2b 交接包

- 按用户要求停止重复实现施工卡步骤1—4并保留现有交付；G2b 继续pending，不伪造StockWiki正例、不写StockWiki。交接文档为`docs/implementation/reviews/IQS-lane/G2b-handoff-2026-09-29.md`。
- 核对共享工作区为`master`，HEAD `25b8d14316c06390450e5a1d8883583bfd039d0d`；相关实现仍是未提交工作树交付，交接文档明确区分HEAD与当前文件快照。身份包2.2.0、Entity 2.1.0、AnalysisSubject 1.0.0、CLI请求schema 1.0.0。
- 交接包记录已验证的identity CLI 6 passed、施工卡批次205 passed / 351 subtests / 0 skips，及公开golden输入格式、StockWiki owner读接口要求、正反验收路径和隔离清理要求。暂不触碰G2b实现，等待StockWiki真实DTO/golden。

## 2026-09-29 — S06恢复与执行门修复

- 本地route composer此前把新运行资格交给历史recorded-route validator，导致自洽的旧router 2.0/2.1决策可走新执行入口；现改用当前router执行validator。历史manifest仍走recorded validator以维持只读兼容。
- 一个renderer失败关闭测试在规则哈希helper迁移后仍patch旧facade；已改为patch真实owner `question_manifest`，避免测试假绿。
- 隔离聚焦回归重跑：`tests/test_routing.py`、`tests/test_stockqa_adapter.py`、`tests/test_s06_dependency_closure.py`、`RouteCompositionTests`、historical-renderer refusal，共 **57 passed / 0 skipped**，209.44秒。唯一TEMP/TMP与pytest basetemp结束后均清理。日志为`docs/implementation/contracts/validation-S06-current-fix-2026-09-29.txt`；未发网络/模型请求。
- 独立只读复审覆盖新执行/历史读取验证器分离、router 2.0/2.1拒绝、失败时不写输出及renderer patch owner，无P0–P2。计划验证仍为107 tasks/366 cases/G6。S06不据此关闭：真实StockQA→StockWiki事务ACK、真实router 2.1历史样本及跨仓E2E尚缺。
- 本次日志封存后重跑工程计划回归：80 passed，计划validator为107 tasks / 366 acceptance cases / G6 valid；临时根清理确认，`git diff --check`通过（仅既有LF/CRLF转换提示）。结果见`docs/implementation/contracts/validation-S06-doc-sync-2026-09-29.txt`。

## 2026-09-30 — 本地进度检查点提交

- 已将当前完成的 invest-quick-scan 本地交付提交为 `eb462d48321f3247eabf18daa57a4d4606405ca4`（`Checkpoint completed local quick-scan work`），共849个文件；提交包括题库与可组合路由实现、契约/工具、隔离测试和实施/审查证据。
- 提交后复跑计划校验为107 tasks / 366 acceptance cases / G6 valid，`tests/test_implementation_plan.py`为80 passed / 53 subtests。施工卡步骤1—4已有205 passed / 351 subtests / 0 skips记录，S06本地修复57 passed / 0 skipped记录。
- 仅完成本仓检查点提交；G2b仍等待StockWiki真实DTO/golden，S06仍等待StockQA→StockWiki事务ACK及跨仓真实样本。没有修改外仓、刷新C01—C07回执或宣称关闭这些门槛。
- 同步更新IQS lane实施摘要与G2b交接文档，明确提交边界和待办；对应提交为 `5aec24044aabdbf5187725e51066cd21fc39bc33`。
- 随后更新 `task_plan.md`、`findings.md` 与本进度文件，记录两笔提交、验证结果及仍未关闭的跨仓门槛。

## 2026-09-30 — Q02 MiMo真实联网验收

- 在获授权的StockQA工作树运行 `tests/live/test_live_quick_scan.py::test_live_mimo_search_runs_public_company_through_cli_and_cleans_local_artifacts`。两次沙箱运行在HTTP前返回ConnectionError；获授权的非沙箱执行通过：**1 passed / 13.63s**。
- 该E2E对Microsoft Corporation通过公开CLI执行`mimo-v2.6-flash`联网搜索，断言provider/model/response ID、`search_status=executed`、与响应关联的search receipt、非空source URLs和`url_citation_annotations`。答案可为scored或insufficient_evidence；本测试不证明分数本身正确。
- 测试自身确认唯一临时目录已清理；调用前后StockQA Git状态均为55项，无测试下载或残留输出。没有保存原始响应、来源URL或token用量；费用未知。错误路径添加密钥脱敏/限长诊断，不记录API key。
- 同一源码快照三文件provider/parser/public-CLI离线回归 **159 passed / 17.45s**；运行于独立临时CWD与basetemp，关闭第三方`base_url`插件及project coverage/cache addopts，临时根删除且StockQA状态仍为55项。
- 当前准确的StockQA源码/测试SHA和命令记录在 `docs/implementation/contracts/validation-Q02-MiMo-live-E2E-2026-09-30.md`。独立复核已完成；其结论与当前任务状态裁定见本文件末尾的同日记录。

## 2026-09-30 — Q02独立复核与状态裁定

- 独立只读复核匹配本次测试所用五个StockQA文件SHA，确认所选LLM-02/LLM-11覆盖；无P0/P1代码问题。建议加强source URL集合/搜索调用ID绑定、有效host记录及“正文含URL但无citation”的P2负例，不是已观察缺陷；没有为此重复发送付费请求。
- 当前计划已于2026-09-29退役工程任务receipt v2；`acceptance-cases.json`明确是规格、不是运行结果。因此不刷新只读旧Q02 receipt，也不改`specified_not_executed`规格状态。执行和复核证据留在本进度及MiMo批次报告。
- Q02首个提供商任务级验收对该精确StockQA工作树快照通过。G1更大样本、评分准确性、引用对主张的支持、实际费用、MiniMax真实搜索和跨仓生产闭环仍未被本次实验验证。StockQA中存在的55项工作树状态不属于本仓提交范围。

## 2026-09-30 — Q03当前快照定向回归

- Q03的Q02前置现已完成任务级验收。我在StockQAbyLLM只读核对现有工作树与CodeGraph后，在唯一TEMP/CWD/basetemp执行parser、answer-service、runner、models、main CLI、QuickScan CLI和QA pipeline测试：**166 passed / 4.91s**。
- 命令隔离了第三方`base_url`插件、项目coverage/cache addopts及所有live/API凭证变量；HTTP边界使用测试fixture，未做任何真实网络/API调用。独立临时根清理完成，StockQA HEAD未变化且Git status仍为55项。
- 关键快照SHA：`llm_response_parser.py`=`9D5EB7D58DACFED1DFFB605ECA504D8A9EC6B6C39A5E2F4341D0A9B6F58AA867`；`answer_generator.py`=`B59840DA063D00D7BCAAB4BA960B88797F6466A4EAD868BA0A7110E4D8FD44F4`；`llm_runner.py`=`E63FDD5890DBCE16A057D0140170E3E1E95C9227E45BD8CC1CD14ABCD8ED0ACC`；`test_quick_scan_cli.py`=`2D146FACE169DD130722DFF182982BCDA9FF7AC9CBCE022F80CE310EA553DD90`。完整14文件清单及复现命令见`docs/implementation/contracts/validation-Q03-current-snapshot-2026-09-30.md`。
- Q03精确快照的独立复审尚未完成；在其结论出来前不改标verified、不改StockQA，也不触碰历史receipt。无复审之外的产品失败。
