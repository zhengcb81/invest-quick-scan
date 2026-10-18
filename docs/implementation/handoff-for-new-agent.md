# Handoff 顶部更新（2026-10-18）

## 当前事实

- 外部包 EVIDENCE-TIMELINE-11 已验收（ACCEPTED，离线工具，非生产资格）。验收记录：docs/implementation/parallel-lanes/acceptance-2026-10-18/EVIDENCE-TIMELINE-11.md。另两包 COST-LEDGER-11、DELIVERY-AUDIT-11 未见 handoff，保持隔离。
- owner 观察 5 条：IQS_12/16/05/06（research-only）+ IQS_09（search-backed completed）。金融机械检查 5/5，引用溯源 pass 1 / research_only 4。
- 已完成 search-backed 运行：IQS_09（completed）、IQS_18（completed，但 observation 因 evidence=0 被 vendor preview 拒绝，已撤回，导出保留）。
- IQS_20 模型给出 scored=6，离线 validate_single_answer 与外部引用绑定 PASS；因 refresh_admission_plan_changed 无法重跑落库。审阅页：docs/implementation/reviews/search-scored-catl-iqs20-2026-10-18/。
- 观察导入前置检查：scripts/observation_import_preflight.py（score 一致、evidence 非空且 id=src_sha16(url)、executed 搜索需真实 hash+receipt）。

## 协议限制（未改）

1. security 题（22–24）被 refresh-v1.4 policy schema 排除（routes scope 只允许 entity/segment）。
2. 有历史 binding/attempt 的题重跑会 refresh_admission_plan_changed。
3. 旧 research-only 观察可能让 preview 报 subject_contract_output_invalid（vendor 合同比 1.2.0 导入更严格）。

## 最近提交

- IQS: 7b65a40 验收、069e84a scored 审阅页、c298457 preflight、4b186f2 撤回 IQS_18
- QA: 444395e fresh 成本、e49e54b DISPATCH 收紧
- lab: d9f5f49 external evidence ids、98aabc9 raw_decode


## 2026-10-18 — search-backed 真实运行与画像入口（最新）

### 已完成（真实付费调用）

- **IQS_09 完整 search-backed 运行**：DeepSeek 搜索 → external context（3 条 catl.com 来源）→ mimo 模型答案 → 引用/绑定校验 → slot completed（answer=insufficient_evidence）。导出：runs/existing-list-onboarding-2026-10-18/search-run-11/export-20261018T164946Z。
- 答案作为 1.2.0 observation 导入 owner workspace（search_status=executed、receipt=SEARCH_26f1…），CATL 画像可见。
- 观察库现有 **5 条**：IQS_12/16/05/06（research-only insufficient）+ IQS_09（search-backed insufficient）。
- IQS_19 曾产出 scored=6 的模型答案；因 answer 语义（forward period）不符合 query contract，未入库，只保留审阅产物。
- 看板：python scripts/one_click.py → 214 页画像、financial-check（5 条观察 5/5 pass）、2 个答案页索引。
- CATL facts：facts-context.json（ready 16/16）、facts-authority.json（valid），未注册真实 facts 执行入口。

### 已知限制（协议层，不是代码 bug）

1. security 题 IQS_22–24：refresh policy schema 的 routes[].scope 只允许 entity/segment，security 不能授权。
2. 同题重跑：已有 binding/attempt 的题，owner register 选 resume、session 选 dispatch → refresh_admission_plan_changed。
3. scored 答案若 period_end 是预测区间，query_original_answer_semantics_invalid（score 题不能带 fact items；forward 期间需谨慎）。

### 关键命令/路径

- 单测：QA tests/unit/test_owner_budget_continuation.py（41 passed，1 个已知 schema 版本失败）；lab tests/test_free_agent_tools.py（6 passed）。
- 搜索 policy/exposure：docs/implementation/reviews/deepseek-search-2026-10-18/
- CATL 观察导入脚本：runs/existing-list-onboarding-2026-10-18/import-0506.py（DIR 可切换 import-09/19）
- 金融机械检查：python scripts/financial_mechanical_check.py --workspace <ws> --json <out> --html <out>

## 2026-10-18 — search-backed 与 F05 的离线交付（最新）

### 已完成（全部离线，58 tests passed）

- S1：iqs.search_exposure/1.0.0（policy sha、路由、凭据存在性、货币、查询/费用上限、存储权利、approved_at）；cell 绑定校验；policy schema 校验。
- S2：scan_profile/shared_company_task 接受显式 search_exposure，默认仍 0 查询。
- S3：search_receipt/1.0.0；DeepSeek /v1/tools/search 客户端（endpoint allowlist、非 200 unavailable、费用 5000 micro-CNY）；receipt↔task exposure↔checkpoint 绑定。
- 独立审查：High/Medium 全部整改（空/全 unavailable、0 费、policy sha、checkpoint hash、币种、重复 route、endpoint、CLI 必填、时间顺序、inert policy），新增 12 回归测试。
- F05：facts pack 生成（CATL 16 题）、pack 校验、审阅页、索引、context 覆盖检查、draft context、draft authority（valid，coverage ready）。

### 仍阻塞（只差 owner）

1. **storage_rights**：DeepSeek 搜索 exposure 仍为 storage_rights_unconfirmed；确认后改 policy/exposure 的 confirmed + entitlement_ref 即可通过。
2. **CATL 分类**：profile.draft.json 为 operating / energy_transition / mature，需 owner 确认后才能提升为正式 profile。

### 真实运行门槛（未绕过）

- 2 题评分 run：admission 已 accepted，但 reviewed-deployment 门要求新的 CAS/reviewer，未 dispatch；owner policy 已恢复原 1.5。
- facts run：draft authority 未并入正式 c06 producer，未注册。
- 真实 API/模型调用：0。

### 关键入口

- search 计划：docs/implementation/plans/search-exposure-contract-2026-10-18.md、search-receipt-contract-2026-10-18.md
- DeepSeek：docs/implementation/reviews/deepseek-search-2026-10-18/README.md
- F05：docs/implementation/plans/f05-facts-pack-2026-10-18.md；CATL 证据 docs/implementation/reviews/catl-profile-2026-10-18/
- 看板：python scripts/one_click.py -> runs/existing-list-onboarding-2026-10-18/dashboard/index.html

## 2026-10-18 — fresh-budget 合同 + 2 题 admission + search exposure v1（最新）

- owner 批准 fresh-budget（$30）后，新增 `stockqa.owner_exposure_snapshot/1.2.0`（attempts=[]、fresh_budget、owner_ack_ref），QA + IQS schema 落地；独立审查无未授权绕过，已修 dialect/refs、quote enum [0,2]、docstring 边界；QA 6a32ac0 / IQS dd4f87f。
- CATL IQS_01/02：preview `rv1_ce80…` ready → confirm `rc2_3fdb…` → **admit accepted**（permission_authenticated、registered_with_executor、API=0）。
- dispatch 被 reviewed-deployment 门拦住：`controller_delivery.verify_deployment` 报 `engineering_reference_path_or_hash_changed`（controller CAS/reviewer 冻结，不能自签）。**未绕过、未付费**；owner policy 已恢复 1.5 备份（3239c35b…），新预算 policy 行保留（0 attempt）。
- S1 首个落地件：`iqs.search_exposure/1.0.0` schema + `scripts/search_exposure_contract.py`（policy sha256、启用路由、凭据存在性、查询预算、存储权利），6 单测通过。仍缺 owner 的 Brave/Tavily 单价与存储条款，policy 不能转 executable。
- 下一步：2 题 dispatch 需新 reviewed delivery 或另建经审查执行器；否则转 F05/G3/画像入口等不依赖该门的主线。

## 2026-10-18 — C 方向：产品入口就绪，原主线剩余项定义

用户选 C（回原 PWF 主线）后，产品入口已成型：

- 一条命令 `python -B -X utf8 scripts/one_click.py` 生成 dashboard：入口页 + roster（214 家、209 verified）+ 214 个公司画像页；roster 里每家公司名可点进画像页。
- CATL 画像页同时显示：机械检查 2/2、金融复核 `passed_with_caveat`（4/4 预注册事实、评分 gold 0/0、CATL-FIN-01 保留）。
- 金融复核 registry：`docs/implementation/reviews/financial-verdicts/catl-2026-10-18.json`。

原主线剩余项（定义与状态）：

1. **F05 事实链**：事实型 observation（当前是 standard-1 评分题；contract 文档明确“事实链仍待 F05”），未启动。
2. **G3**：context producer/gate（`docs/implementation/reviews/G3/` 下的交付/审查已存在），整门仍开放。
3. **B01 checkpoint30/31**：receipt/context 接续；与 000026 一样卡在 owner 侧 subject context 注册。
4. **search-backed S1–S5**：owner 合同 + 工厂/profile 放开 + runner 搜索回执；key（Tavily/Brave/DeepSeek）与 policy 准入已验证，代码未接。

本轮无模型调用、无业务库写入。

## 2026-10-18 — verified 身份批最终 PASS（节点已闭合）

独立复审最终结论：**PASS，身份批 closed**。209 verified / 5 provisional；CN 201/205、US 11/11、HK 0/1；receipt 424。证据：200 条 cninfo（200/200 official_short、name_gate 全 equal、原始差异 2 条 NFKC 等价）、7 条 SEC + 完整 submissions、pre-existing 具名（Alphabet IVR_663efa…/CATL IVR_d5c631…）。审计 `scripts/verified_evidence_audit.py`：207 通过/0 失败/2 pre-existing；name_gate 今日仅接受 equal（contains 需未来逐条记录理由）。5 家 provisional 见 verified-gap-register，均 scoring-ineligible。

**routing 探测（治理动作，未做真实发布）**：副本里 publish-routing 成功（pkg_b5a41d8c… / modrel_fc5de4…）；与历史包相比 **modules/contexts 完全相同**，仅 release/package 的路由元数据变化（schema 1.0→2.0、router 1.0→2.3、routing_policy_sha 新增）。000026 resolve-route 产出 route_327b3c77…（partial，common+risk），**minimum_questions=24**；max=1 compose 被 mandatory coverage 拒绝，max=24 成功。选项 A（发布 routing 包）技术上可行、确定性、不改题目，但属治理动作需 owner 批准；选项 B 手工 route 仍需 24 题覆盖或改 policy。

**search provider**：仍待 owner 选 route/单价/storage rights；选项见 search-provider-options-2026-10-18.md。

## 2026-10-18 — 现有列表身份批完成（209/214），生产入口卡在 route / search

**当前真实状态**：214 实体，**209 verified / 5 provisional**；identity receipt 424；观察 2 条（CATL）；真实搜索 0、模型调用 0。

- CN 201/205（cninfo 逐公司概况 API，194 批量 + 44 名称闸门修正 + 5 试点 + 万科A SZSE 年报）；US 11/11（SEC 逐公司 submissions）；HK 0/1（06066 仍 provisional）。
- 证据归档：`docs/implementation/evidence/verified-identity-2026-10-18/`（200 条 cninfo 概况 + 7 条 SEC + 7 份完整 submissions）；审计 `scripts/verified_evidence_audit.py` = 207 通过 / 0 失败 / 2 家早期证据不在本归档。
- 剩余 5：002013、300114（cninfo 空，疑似退市/重组）、688555（退市）、872808（北交所无免费源）、06066（HKEX 官方页未取得）。

**为什么还不能跑画像**：verified 只解身份闸门；共享引擎还要求每家公司有 owner route + ApprovedRefreshSession。真实 policy 里目前只有 CATL 一条路由，**208 家需要 owner 准入**。准入第一步（AnalysisSubject + perimeter receipt）已在副本跑通（000026，ASJ_67a1f0d0…，0 网络/0 模型）；第二步 route 被 “historical package has no executable v2 routing policy” 卡住，需发布 routing 包（治理动作）或 owner 手工指定 route。

**search-backed 评分**：S1–S5 方案已写（docs/implementation/plans/search-backed-scoring-2026-10-18.md）；供应商选项已列（Brave $5/1k、Tavily 免费 1k credits/月、Serper 试用、DeepSeek 约 ¥5/1k），需 owner 选定 route、key 环境变量名、storage rights 与限额。

**工具**：`scripts/roster_status.py`（看板，含 needs_owner_admission）、`scripts/profile_readiness.py`、`scripts/owner_admission_subject.py`、`scripts/verified_evidence_audit.py`、`scripts/financial_mechanical_check.py`。ROSTER 看板：runs/existing-list-onboarding-2026-10-18/roster.html。

**下一步顺序**：① 定 route 方案（发布 routing 包 / 手工 1 题 route）→ 副本演练 universe/policy/preview/admit → 真实 1 题非评分画像；② 定搜索供应商 → S1/S2 合同与工厂改造 → 1 家 1 题 search-backed 试点。

## 2026-10-18 — 真实研究型出版已完成；只剩施工包复审与归档

真实零 HTTP 研究出版已在原 owner namespace 完成：preview wdp1_316c… → delegated confirm rc1_dcb42b… → inspect 1.1.0（API 0、writes 0、request 相等、1 anchor/2 item）→ apply（2 个 v3 checkpoint + 2 条 sealed delivery）→ 原 StockWiki observation-import → ACK accepted → 幂等重放相同 → 两 work 均 delivered。StockWiki 实写 2 条 observation（insufficient_evidence/null/unreviewed/unverified）与 2 条 binding。真实账本 schema 25，102 预算行与迁移前备份逐行一致，attempt 14，其余 12 work 仍 leased，0 新增预算/尝试/费用、0 HTTP。证据见 [real-publication-2026-10-18.md](reviews/real-publication-2026-10-18.md)。

提交：invest-quick-scan eaf96e7、4504962；StockQAbyLLM 39c150e、8c166a6、12aea00（已推 origin）；StockWiki 1fb9efa、dcc70ce（原仓无 remote）。

执行中的偏离已记录：仓库 black 格式化；schema25 的空 `_DDL_V25_ADDITIONS` 与历史 fixture 的 pre-v25 还原；事务内复用 publisher grant（`preauthorized_grant`，仅 publish 内部可达，仍校验存储 grant/request hash/confirmation）；原 IQS 合同新增默认关闭的 `research_only` 通道；原 CLI 是扁平 `observation-import`。post-execution CAS 绑定 base/reviewed/applied 与提交号，是描述性记录，不是执行前审查签收。

三张 2026-10-18 施工包已完成第三轮（最终）独立复审：verdict pass，26/26 冻结 blob 实核一致，N1–N7 全部闭合，文档归档提交 `b5f99b4`；仍未派发、未实施。至此本节点无剩余必做项：不重跑真实出版、不重发模型、不改已验证答案。三张外部 Lab（RELEASE-DIFF-10、SUMMARY-LOSS-10、RELATION-DELTA-10）均已完成。

## 2026-10-18 — 当前明确暂停，不自动恢复实施

用户最新指令是“手头做好了先暂停吧”。只在用户再次要求继续后恢复主线。已交付 IQS a05dc8b / StockQA c910ed9 的真实 CATL 两题缓存恢复，不重做、不重发模型；Runtime f8e251f 与 StockWiki 809b501 无 remote 仅本地。

先读 [完整暂停交接](reviews/pause-handoff-2026-10-18.md)，以及 `runs/shared-engine-production-2026-10-18/saved-research-publication-candidate/handoff-pause.md`。下一出版节点仅隔离候选，driver / 公开正例 / 整包独审 / 源应用 / 真库迁移 / 实际 ACK 均不能标完成；public01/02 的原 owner store-ID 拒绝必须保留，禁止改原 receipt 伪造通过。真实两 work 仍 uncertain，旧三笔费用未决保留。

完整文件：`docs/implementation/reviews/pause-handoff-2026-10-18.md`。三外包10号卡保持活动 writer 隔离；忽略与保留他人 README 四行改动。

## 2026-10-18 — 真实CATL研究恢复节点已独立验收，转原链非评分出版

当前节点已完成，不再重复实现/重跑付费样本：原safe至全新carrier02恢复75.0352秒、exit0、Company研究槽2/2 completed、新HTTP0、原native重放1次、报告与summary一致。工程最终独审a8362779.../open_findings=[]；金融一致性最终c6c0828e...确认两答逐对象与原答完全相同。实际31P、旧SDK59P、旧Runtime39P、root16+8、独立7分别有证据，不混成金融准确率。StockQA c910ed9已推origin；Runtime f8e251f无remote仅本地；累计源码/完整759文件已独立交付签收e73427d7...。原source/final/proof/config/checkpoint/0/2partial历史保留。

实际原101预算/12work/12attempt全行不变，总budget102（99 settled、2 unpriced、1 uncertain），本次公开价估算US$0.014537非现金账单。输入11001、输出含思考11208/cache0。原三笔未决不清；新CATL两条原StockQA work仍uncertain、lease_expires_at=None，不能把Company完成写作正式工单完成。两答仍insufficient_evidence/partial/null，4唯一事实支持、主观分数/完整构念gold均0/2；CATL-FIN-01措辞限制保留，金融/正式搜索资格均未授予。发布内容只含薄证据/代码，不含答文/完整context/库/准入凭证。

下一主线实际硬缺口已只读确认：现有标准checkpoint对所有状态要求verified search和原lease；当前只有research safe/固定board。共享engine未调用nativecommit；known_response_resolution只能将不可用结果close failed，不能当历史研究出版入口。不能补造搜索证明、续旧lease或改原body来强闯。复用原fixed owner/原库、C06/outbox和SW observation1.2，做显式默认关闭的publish_saved_research+research-only checkpoint版本，fresh publisher只负责已知safe的非scored/null/unverified出版与ACK，旧scored/search要求保持，最终SW review_pending/screening而非正式评分。

作者仅在saved-research-publication-candidate准备完整跨仓overlay/TDD/CAS，原源/库未动，无付费；同节点一次集中unit/integration/public-CLI/原库副本E2E及真正不同agent整包审查后才应用并实际激活。独立金融sidecar保持，原其他101账/旧12工单/费用不动。诊断post-recovery-formal-seam-readonly/有精确源引用。三外包10卡仍各自writer隔离。

本轮测试未下载文件；新3目录精确清理被policy在执行前拒绝，额外测试目录隔离保留且不绕过重试，旧8拒绝也保留，不能称环境全清。本节点PWF/规范/实验与独审薄证据正常提交、推送既有origin，实际提交以Git为准；不包含他人2026-10-10 README。

## 2026-10-18 — 批量运输整节点独审通过并已交付源码，待原响应0POST恢复

不同agent最终签收5de0225d...、open_findings=[]，累计6产品CAS dbe1546e...，原1.5/第一次修复全部历史保留。集中31P、旧SDK59P、旧Runtime39P、root16+8和独立7项风险检查通过；实际两答也由原validator/Runner只读验证来源/日期/epoch，未增加金融充分性。typed非batch用例仅未来选择谓词边界，现有Company没有因此获得agent_loop能力。

9产品/测试精确应用。Runtime f8e251f本地无remote；StockQA c910ed9常规hooks含mypy95全部通过。mypy暴露外部Runtime模块不在QA单仓类型路径：复用同文件已有固定import_module模式，两处固定模块/函数延迟加载，模块缺失仍拒绝，无type ignore或路径fallback；这属于显式交付调整，正由同一不同agent核查，不能冒称纯格式等价。最初跨仓pytest被Runtime原locked SDK conftest误收集而失败已保留；之后禁用该依赖conftest、实际已应用源码31项通过，开启同一禁网/写审计，真实缓存只读opt-in。旧59/39兼容分母另列。

当前完整759文件delivery草稿082c012e...只含6累计产品delta，其余753不变；QA/Runtime共7个产品/测试commit blob核同当前源。实际仍原0/2partial，不以源码交付冒称恢复成功。下一动作签机械交付附录、生成version2 proof和仅proof变化的配置，再原cold cp至全新label目录0POST恢复；不新调用、不重发、不清未知、不延lease。3外包继续writer隔离。

## 2026-10-18 — 批量协议根修集中验证，原真实响应保持

同一节点的候选已覆盖未来final_json wire不带tools/tool_choice，以及历史单submit载体到原批量parser的严格转换；原工具外壳、重复JSON、声明题目、来源、安全围栏与原任务绑定都保留。原Runner白名单、原checkpoint、费用与600秒lease不修改。总控新增8项输出路径检查（4个真实CLI拒绝、4个旧partial保留），0.96秒通过；另16项既有proof测试不重复跑。四产品候选仍待作者最终冻结和不同agent整体签收，尚未应用/新调用API。

三张10号外包已发出，三个Lab继续活动writer隔离。当前唯一下一动作是收口这次运输适配，应用后以全新无key、核心禁网络进程恢复同一原响应到新的输出目录。原0/2 partial与失败历史不覆盖，不将4/4参考数字提升为完整投资准确性。

## 2026-10-18 — 原缓存已零POST读回，但批量运输与执行协议不一致，保留0/2现场

混合正文/工具回执修复已独立签收（supplement677ba937...、delivery0614e058...），Runtime正式26P并提交d96051a（原无remote）。语义修复保留原safe双通道和安全fence，原1.5final/proof/配置/checkpoint未改。新纠正配置只替换deployment_proof；fresh无key/核心禁socket读取同一原响应76.66秒、实际新增HTTP0、重放原native1次、报告与runtime-summary一致。

但实际all_slots_completed=false，2槽not_attempted，不能以进程0宣称完成：原module_packs的已签checkpoint allowed_tools=[]，Company request_context却把全部TOOL_PARAMETERS提供给Runtime/SDK，SDK因此返回submit_answers，原Runner按白名单正确拒绝。该诚实partial的recovered-session/export/report与0/2结果全部保留，不覆盖/改旧checkpoint/放宽白名单/重发LLM。

不同agent核语义后同意显式批量运输适配：只认真实绑定company-scan/module_packs/one_shot_packs；原SDK声明的唯一submit_answers、原始question_ids/answers严格验证且逐值映射为原batch parser要求的declared_question_ids/answers；不补缺声明、不解其他工具/多调用/截断，free_agent原样。未来wire同时修为显式final_json/no tools，避免继续制造同一协议错误。作者在batch-carrier-recovery-candidate准备4产品；总控另在batch-carrier-controller-candidate准备保留历史的proof2、全新recover-label输出、partial返回4，16元数据+4真实CLI拒绝测试通过。尚未应用新slice/新API。

独立金融评审原安全两答：4/4唯一参考事实受支持，2主观分数/完整构念gold均0；两答insufficient_evidence/partial/score null合理。1处历史资金总量被形容为较强流动性的表述越界保留为CATL-FIN-01，不能伪改原回答或自动授金融准入。实际账仍102、旧101逐行一致/原3未决保留，新增公开费率估算US$0.014537（非账单）；provider usage输入11001、输出含思考11208（思考7816）、cache0。没有策略总体赢家或缓存经济性结论。

## 2026-10-18 — 真实两题已安全保存且可计价，恢复格式缺口正在根修

CATL原生identity/query/quote/rc2/admission真正完成，真实MiMo Pro两题单包冷跑305.8697秒、安全保存后按计划exit86。原S1从101到102预算记录，新增1次HTTP200/actual_model=mimo-v2.6-pro；新增budget按公开费率估算14537micros（US$0.014537，published-ratecard-estimate-not-invoice），不是账单现金。原101行逐行一致、旧三笔未知不变。

全新无key、核心Python进程自启动bootstrap禁socket/audit的恢复68.55秒后失败于_restore_model_receipt→model-receipt SchemaViolation，尚无正式export/完成槽数；禁止将safe响应视为恢复成功。已保存可见输出仅一份submit_answers工具结果及可见文字，无隐藏思考，原DB payload rawSHA3f67b613...一致。金融agent按事前锁定4事实/2结构、score gold0/2独立评审；不把工程回执失败当金融答案错误。

当前原source作者只在priced-safe-recovery-candidate定位真实已定价回执的确切schema差异、补回归，不改原库/不调用模型；不同agent审当前实际恢复修复节点，原1.5最终签收及机械交付历史保留，语义补丁不得冒称格式等价。修复后只读同一原safe响应尝试0POST恢复，不自动重发、清账、延lease或伪造原回执。三外包10卡继续活动writer隔离。

## 2026-10-18 — 续行1.5原源码已发布，真实CATL准入启动

整节点真正不同agent签收final898c21a2...、open_findings=[]，源CAS36bf41d9.../controller1216ea80.../完整759文件55a7e6eb...绑定。独立8个native+9个controller检查通过。原公开合成链403.35秒：2题1包、1SDK POST→safe→86→fresh keyless禁网络0POST、两槽完成；当前新work的lease仍600秒，claim至POST76.68秒/安全落盘83.75秒/恢复159.10秒。旧错误全库MIN lease观察保留，按精确新work只读重算；旧101预算/12work/12attempt全行保持。新增合成响应仍未计价，不能称真实模型/现金结清/金融准确。

12产品+4测试已精确应用。QA常规31P/19项明确private opt-in跳过；候选50集中/109旧QA（1loopback明确排除）/59旧IQS另有实际证据，不混分母。普通hooks首轮仅换行/isort修格式、mypy过，第二轮全绿，StockQA6177b27已推origin；IQS03b644c已推origin；StockWiki809b501正常静态hook本地提交，原无remote，不新建远端。不同agent机械交付附录2f8e2fff...核全部759文件、16目标commit blob与5仓提交，差异仅换行/import，业务AST保持；未重跑403秒整链。

实际deployment proof已用共用checker验证完整闭包/公开资料/原题定义；当前原native CATL激活在运行，复用原S1预算与原owner、真实identity import/serializer/query/quote/rc2/admit。尚无已签收真实回答/缓存恢复，新HTTP尚待实际账本；不把启动当成功。三外包10卡保持活动writer隔离。

## 2026-10-18 — 续行1.5整包审查收尾，三外包继续隔离

用户已发出RELEASE-DIFF-10、SUMMARY-LOSS-10、RELATION-DELTA-10，三Lab按活动writer对待，不接管、不改写。总控继续当前跨仓节点。1.5候选16目标已冻结；49项新检查、109项旧QA回归（1项依赖真实loopback的异步用例因整进程禁socket明确不运行）、59项旧IQS契约通过。公开v03已走原SDK scripted单POST→原safe落盘→exit86，新进程keyless/禁网络恢复仍待最终结果，不能称真实模型或金融正确性。

总控真实两题controller经独审发现三个根因：自选源码pins未与整包审查绑定、重签外来context可替换、实际冻结release未纳入完整锁。已复用同节点final/CAS/delivery-addendum形成共用纯工程元数据校验，不新增权限服务；公开短资料固定白名单、桥接身份在原prepare后按真实subject核对、实际release及原题定义锁定。32项集中测试10.58秒通过，子进程全部禁网络、写入约束自有目录。R2 CAS a8f464fa...、756文件runtime候选清单b4559df7...已交真正不同agent整包复核；尚未签收、应用或真实激活。

原CATL公开identity import/serializer→IQS验证→真实原route/compose仅在隔离原库副本验过；正式owner仍未写入。新真实公司模型请求0，旧101预算行/三笔未决保留；第一轮Alphabet真实失败不能被合成正例改成成功。独审后精确应用、走正常hooks提交，再真正原生准入跑两题/安全摘要/0POST缓存恢复。

## 2026-10-18 — 通用续行1.5候选实施中，真实两题driver已预备

IQS 91234d1已确认推送origin/master；StockQA 4d77ffb此前已推送。用户再次确认三个10号包已发出，三个外部Lab保持活动writer隔离，不代改、不索引。原README 2026-10-10的他人四行改动保留，不纳入总控提交。

当前一个完整跨仓节点：composition agent独占native-continuation-v15-candidate内overlay，实施原权限/quote/rc2/admission/原预算的显式1.5，不直接改源/真库；总控在另目录real-profile-smoke-candidate准备原company-scan/profile两题单包实测driver。沿用原Task/profile/SDK/price/evidence adapter；思考开启16384、1HTTP/0新搜索、原批量claim显式开启，原safe落盘后exit86与全新无key/禁网络0POST恢复。旧失败Task3 driver字节不改，19个本地资源/包数/源码pins等拒绝测试通过，仅是未准入的准备，不是原软件整链或真实答案。

金融独立参考准备只读选择已有CATL/中信建投真实StockWiki DTO及官方短来源；已知DTO仍provisional/formal_profile=null，不称verified或正式金融资格。私有gold不喂模型。本轮尚无新原生激活、付费请求或缓存恢复，原101账和三笔未决完整保持。完成候选后集中五类实质验收和不同agent整包审查，不增逐helper门；若失败继续根修并保留现场。

下一单项：完成并冻结1.5完整跨仓候选、整体集中测试和独审，随后应用正常源码并跑另一个真实公司两题实验。无新权限提问。

## 2026-10-18 — 原子批量领取已交付，转原通用续行1.5

批量claim独立整包签收（final SHA1b69e5...、CAS02726d...，open_findings=[]），精确4QA产品+4正式测试已应用，普通48P/1显式重型skip/8.70秒，正常hooks含mypy94全绿，StockQA已提交推送4d77ffb4e73232ef93b082900a74a731bdb256ba。原diagnostic receipt增量、旧singleton转换、600秒lease及每POST fresh权限保留。仅private helper返回Optional[Lease]注解/isort/换行修正由不同agent交付附录核等价；历史final/CAS不改。

32单测、5原回归、11独立反例；原软件同b02原owner/ledger的c01接续case607.78秒：12work同一原子claim、一次scripted SDK POST→原safe输出落盘→exit86→新进程12槽完成/新POST0。此607.78不含此前b02准入和失败准备，不能当冷启动全程；claim9.68vs旧91.57秒局部省82秒，但claim→POST359.09vs旧319.96秒更慢，未证实总体提速或真实模型600秒内足够余量。新夹具响应仍unpriced/NULL/预约100000：synthetic resolver的scripted-native-rate与原fixture-price-v1不匹配，原计价器正确不结清，不授价格资格。原真实Alphabet12题失败/第三笔未知/金融不可评保持，不能与本工程合成12答混用。

b01安装80秒timeout和b02副本漏scan_profile的失败均保留；完整闭包933+8重基后才通过c01。四产品实际运行字节可核；测试before-Black快照实际采于c01执行后，期间增加collection-only skip/SAFE_ENV，附录明确不能称完整harness启动前byte锁。原断言与原库独立只读观测支持工程范围，不为机械格式重跑607秒。私有测试库/输出留在runs，不归档；原真实DB/外包活动Lab不碰。

下一单项：按已落具体方案在原continuation/permissions/quote/rc2/admission增加显式通用1.5保留暴露列表+已有company-scan单包绑定；旧1.0–1.4不放宽、不新建ledger/服务。保留原真实101账和全部三笔未知，先另一真实公司2题1包的安全摘要/禁网络keyless恢复，不解锁旧Alphabet12。设计native-continuation-v15-candidate/design.md与post-smoke-authority-review/recommendation.md；只在完整跨仓节点集中五类实质测试与一个不同agent整包审查，不加微门。用户全部后续权限已覆盖，不再提问。

RELEASE-DIFF-10、SUMMARY-LOSS-10、RELATION-DELTA-10已由用户发出，三个Lab维持活动writer隔离，只接正式交接。

## 2026-10-18 — 下一真实样本复用原契约升级，不清账也不再堆临时特例

只读结构审查与原函数反例确认：原known-outcome要求settled及完整response_status，本次不满足；旧研究seal仅认budget-only/noHTTP，不能收pack/intent；原continuation1.4硬性两条budget-only且free_agent-only，不能接第三笔原native未计价或现有module_packs profile。实际mode=ro前后DB SHA同031de09...，101请求/3未决均保留。证据与具体最小路线见runs/shared-engine-production-2026-10-18/post-smoke-authority-review/，不是额外审批门。

在原continuation、固定namespace permissions/quote/rc2/admission里增加显式1.5通用保留暴露列表和已有company-scan profile单包绑定，保留旧1.0–1.4原行为；复用原ledger/cell/intent/owner，不增加服务、账本、调度器。源类型和原pack/work/receipt状态从原库推导，运输结果、可用答案、现金费用三维分开；任何新批准仍计入原101次/全部预约/旧inflight/原预算与并发上限。新控制只准新的明确独立action，不放行旧Alphabet12工单或用run/gen/profile改名重发。

完整profile hash作防篡改；语义去重另用subject/原题面模块/实际cutoff/包策略/route/思考输出搜索控制/明确replicate，避免既被改名绕过，又永久挡住真正新日期。首个新版本只做另一个原真实身份公司、2个原题、1包、0新搜索的真实摘要/原安全输出/禁网络keyless恢复。旧Alphabet logical disposition以后复用原work-decision扩展，不阻塞独立公司首跑。集中五项大节点测试及一个不同agent整包复核即可，详见recommendation，不加逐helper门；既有全部授权继续有效，不再次问用户。

当前仍先收口正在跑的批量claim公开恢复链与源码交付，再实施上述一个连贯跨仓切片。

## 2026-10-18 — 首次真实原生12题请求失败，原始费用与状态保持

真实cold实际745.694秒、rc2，未到预期安全输出后退出86；原SDK新增1物理请求并收到HTTP200，实际模型mimo-v2.6-pro，但严格可见响应未形成安全输出、usage缺失、新账response_unpriced/actual NULL/预约100000保持。12个slot均answer=null/outcome_unknown，不是12份答案或合理unknown回答；金融准确性不可评，缓存恢复未启动。原100条预算记录完整一致，原两笔未知保持，新第三笔未知不清零、不自动重发。源码414 pins保持。证据可定位严格响应验证失败分支，但既有错误投影丢失具体安全诊断，不能猜为length、工具schema或服务商错误。

已定位的两处根因分别是严格响应错误码未落原receipt，以及Runtime按精确类名分类漏掉ResearchResponseValidationError；原pack实际members_uncertain=false，不能把本次失败归因于过期lease。修复候选仅固定code白名单/原record前写入/明确异常分类，集中RED6F8P、Runtime子类RED1F17P，最终分拆测试94P/37.92秒；独立8未见反例已通过，最终整节点审查尚待签。另原v22测试fixture漏删v24 continuation表并仍断言23已在候选根修；不改生产schema。不同仓测试保持独立，不以总控注入路径掩盖普通pytest依赖。

诊断修复整节点已独立签收6目标（final=open_findings=[]，状态明确actual_smoke_failed）；原源普通QA92P/31.29秒、Runtime自身旧failure+新taxonomy测试exit0。QA正常hooks首轮仅换行/black/isort修格式、mypy通过；第二轮全绿，已提交推送27d3373。Runtime使用IQS既有作者配置仅命令级提交f83a5be，未改global；该Lab仍无remote。实际旧回执不补写新code/usage，原真实失败不因代码修复改为成功。批量claim候选另跑隔离公开整链与不同agent审查，当前未签收、未应用。

下一步完成已准备的默认关闭、原owner原事务批量claim优化，整节点公开测试与独审后再应用；诊断修复已经交付，保留本次真实失败现场。真实答案与恢复需后续合法新实验，不能补写本次成功。三个10号Lab已由用户发出，保持活动writer隔离。

## 2026-10-18 — 真实Alphabet实验已原生准入并启动（结果待验收）

实际原namespace已完成备份、原S1 schema20→24迁移（所有旧表全部行保持、新表初始空）、原route13 current CAS version2、真实query/quote、dg1委托/rc2确认和原StockQA admission。原100请求及两笔费用未知/预约保持，未用新库或清旧账绕过。原生确认rc2_1535b0c624e43cbd43330d1c1fe87116ecc03ccf400126d3897d3b37106fd3b2，真实工作根runs/shared-engine-production-2026-10-18/actual-native-alphabet-01。源码交付IQS4481c56、QA961884d已推；SW03423ba、Company2561f56本地无remote。

已启动cold真实MiMo Pro原SDK过程；通过原Task3十二题/2026-10-13/free_agent/16384开思考/0新搜索，九条既有短来源作为context；尚无付费回答/实际完成数的签收。计划只允许新物理1次，收到原安全输出后退出86，再全新不含任何API_KEY环境且禁网络的进程恢复。任何未知/诊断拒绝都停止，不按预期填写成功。原工作时间600秒不扩大，剩余时间诊断不足则0POST退出。完整运行结果等实际原账本和两个独立reviewer（工程与金融分别）核定。

预先金融评审锁定：12题可审结构/理由/来源，精确1–10主观分数gold0/12，完整投资构念证据资格0/12；十个独立历史标量按唯一事实分母审覆盖、正确值、引用支持、合理unknown，缺项不算正确。没有用private gold喂模型，也不把九个短摘录自动升为已核实。当前真实样本是接线/准确性诊断，不与旧T4因果比较，不改变原逐题默认。

## 2026-10-18 — 三张10号施工包已由用户发出

用户已明确将RELEASE-DIFF-10、SUMMARY-LOSS-10、RELATION-DELTA-10交给外部harness。三个独占工作根分别为iqs-release-diff-lab、iqs-summary-loss-lab、iqs-relation-delta-lab，均视为有活动writer；总控不创建、不覆盖、不代改，只接收正式交接。原施工卡/65条固定Git blob输入/接口/独立agent全面审查修尽才交接的要求保持，状态不是实施完成。主线继续当前真实Alphabet原生准入和一次SDK/缓存恢复，外包不阻塞它。

## 2026-10-18 — 共享引擎两项生产接线已正式交付

native续行21路径与company-scan/profile22路径均经真正不同agent整包签收，open_findings=[]。StockQA正常hooks（含mypy94）提交并推送961884d；StockWiki正常静态hooks本地提交03423ba；Company本地提交2561f56，Runtime保持b732a49。后两Lab及StockWiki原无remote，不擅自创建。QA首轮hooks修格式后仅增加2局部容器类型注解，独审确认与原签CAS执行语义等价；没有跳过hooks。

native续行集中36P、旧预算42P+15subtests、独立8反例、原12题单POST/OS中断/新进程0POST恢复均通过；公开工程case719.63秒。原100请求、旧两笔actual NULL/预约/并发占用不改，真实原S1此前只读SHA保持。新增回归4路径已随StockQA源码交付，不只存在ignored runs；私有历史库迁移测试显式opt-in，普通单测不依赖私有DB。

company-scan/profile新增实际日期/明确题目子集/模块或维度小包，保留旧Task1/2/3协议和52锁定输入。F01–F04从协议派发、计划/实绩、SDK实际资源上限、统一epoch context根因修复。最终Company202P/1原skip、IQS24P、独审10项（至少2此前未见反例），真实软件原owner/SDK新fixture426.845秒：第一题已知价格settled后退出86，新进程缓存1/仅发另一题1次，2题完成/总2物理/正式checkpoint0。旧错误pricing-ref造成unpriced的原现场保留actual NULL，补验1/2完成、0POST，不能覆盖成全绿。

这两项是工程源码交付，尚非真实金融/全池/正式search-backed资格；native1.4仅MiMo/free_agent单cell，不因通用profile已发布就放宽原旧暴露续行的策略。所有正式结果/实际source bindings/独审/操作手册以本节点shared-production-archive.json精确归档（无回答正文、DB、密钥）。

真实Alphabet12题即将运行：真实身份/原route13 manifest/原public authority1.2导出预检成功；真实激活和运行脚本经同节点7项独立边界测试与整包复核通过。修掉相对cwd旧worker漏检；原预算精确pricing_ref、思考开启/16384、网络240秒、原lease600保持，scope后剩余<360秒则0POST停止。此诊断不是wire时剩余证明，SDK最后原权限/lease守卫仍有效。真正cache读取无需延lease，但正式答案checkpoint仍不得越过期守卫。当前还未实际激活/调用付费API。

下一动作：实际备份原namespace/S1→原生20→24迁移保持所有旧行→原route CAS→真正query/quote/rc2/admit→一次MiMo12题，原安全响应后退出86→禁网络keyless进程缓存恢复；随后同一大节点独立复核真实摘要、费用/未知与时间，固化实操手册。不得从失败状态自动重发。独立10卡已可交harness，不自动派发。

## 2026-10-18 — 真实运行输入准备与并行生产载体

委托节点已提交推送IQS10e69d9、StockQA aaddcd6，StockWiki无remote本地3fad36d。native续行正在新源精确重基后的公开原链实施，不重复原已签工程节点。并行production-task-candidate只写Company/IQS carrier候选，实现显式company-scan task/profile、实际日期与动态小包；首轮19用例通过但旧全套载体/独审未完，不宣称交付。

真实准备核对发现旧owner-stage的14.4USD/144请求配置已过时；真实S1 ledger为t2-reviewed-v2-20261016/25USD350，原匹配配置是real-contrast-2026-10-16-03/inputs/budget-policy.json。两实际模型环境变量可见，只记录存在性、不导出值、未发API。10-18官方公开MiMo费率与旧T2相同；DeepSeek别名现在标为DeepSeek-V4.1-Flash-1017，跨日期后台版本不能当同模型同版本，旧T4不重新改价。观察及来源URL见本节点official-pricing-observation-2026-10-18.json。

旧实际T4公共board为18 facts/9 sources，不能直接当Company records。root在actual-evidence-projection候选显式适配原9短摘录，原URL/pub/retrieved/limitations/正文保持，未知维度保留unknown/null且unverified；18派生fact无明确source边，不自动制造支持关系。初测发现旧3源使用content_hash而非excerpt_sha256，独审又用重封hash反例确认原别名与eligible_for_context不可忽略；已修所有原digest别名一致验证和显式bool True资格，最终20回归与2未见反例合计22项独立复验通过（原9短source仍完整）。无原生owner正例/授权/金融资格。真实首跑将明确为新的输入配置、接线与准确性诊断，不能与旧T4作单一策略因果对比。source input原字节保持，0新下载/收费API。

## 2026-10-18 — 委托原生运行大节点正式交付

独立不同agent整包签收15精确路径：passed_for_exact_delegated_owner_engineering_scope、open_findings=[]。最终31契约、103 StockQA旧回归、22 StockWiki旧回归、1真实软件public E2E（248.322秒）、10独立未见反例通过；分母分别保留、不相加冒称金融正确率。实际隔离SQLite只读核对：两work、一原发送/一预算/一admission，timeout的actual NULL与reserved1000000保留，另work在撤销后0POST。rc2/record2.0与原撤销记录存在；原rc1/TTY保留。mypy92源文件通过。

精确应用后走原正常hooks：StockQA `aaddcd6be6f506ca58791d7ecc375bbffa7b0c70` 已推既有origin/master；StockWiki `3fad36d1ae82333d9d1ed1eb4c55ee775d35b0df` 已本地提交，原仓无remote，push origin安全失败，未新建远端。首轮ruff测试import布局、QA CRLF/black/isort由原工具修正，第二轮正常hooks全绿；独审机械等价附录绑定最终源，不重复未变4分钟整链。真实v18只读预算缺新quota表的版本分支已修复；当前schema损坏继续拒。

能力只表达当前本机OS owner固定namespace中的单action委托，不能冒称TTY或密码学agent认证；没有清理旧S1未知费用、真实公司金融资格或正式search-backed checkpoint。实际源码交付不写真实namespace/原DB，0收费API。

下一主线：native-continuation候选在上述新HEAD/SHA上精确重基，完成原policy1.4 permissions-only→真实quote/原委托确认→同一原账本发送的整节点；旧S1两笔预算暴露保留actual NULL/预约/累计请求，新cohort精确绑定，旧B01的30work另留原状。随后实际公司摘要/暖缓存/进程恢复与准确性成本速度实测。真实激活准备见本节点runs/real-activation-preparation.md，旧2026-10-15 DeepSeek staging不能冒充MiMo Task3或新policy。三张独立10卡已就绪，无主线目录重叠。

## 2026-10-18 — 续行方案精简与真实旧库兼容修复

原只读设计中的“独立暴露决定install＋三表”提案已撤回，不作为施工要求。已确认原StockWiki current_permissions的permissions_only路径在调用executor inspector前返回原owner_policy/owner_state，可以先读取真正原受控策略，打破quote循环。当前native-continuation-candidate实施owner policy1.4内精确budget_exposure_acceptance＋原固定部署permissions-only端点读取，真正quote及原确认继续绑定完整policy/request/quote；仅保留必要单cell→原action/work不可变关联，物理计数/费用仍复用原表。不能信caller字典、任意部署路径或enable布尔值，旧默认暂停保持。旧design.md留作历史，后续以implementation-notes.md及最终CAS为准；不为未发布三表草稿增加迁移兼容。

委托节点广回归将真正v15/v18旧schema构造正确后，定位get_quick_scan_budget_status在已声明只读v18上无条件读取后续quota表的真实缺陷。由owner_services18在delegated候选修最小版本能力分支，保留unknown/reserved，当前schema缺表继续拒；native-continuation后续对该大文件必须在其source交付后按新HEAD/SHA重基。原真实S1/StockWiki namespace仍未写、0收费API。当前工程节点f9f83ca已通过不重做。

## 2026-10-18 — 后续两项主线切片已具体化

1. `native-continuation-design/design.md`（本节点runs下）完成只读根因设计并转独占native-continuation-candidate实施：原S1实际100次，98已settled/已知USD0.655435，2笔budget-only原未决/预约USD0.2；没有原work映射，不能猜不同公司或以hash自证独立。使用quote前原固定owner控制先安装精确旧暴露接受决定，再生成新真实quote及原确认。原单一ledger保留旧状态/actual NULL/计数和累计限制；仅明确新cohort/cells，不放行旧intent重发或原native未决work。旧版本默认继续暂停。现有25USD/350请求上限已有空间，不需扩大。
2. `generic-task-design/design.md`已具体列明研究入口不能限制生产：Task3保留冻结12/日期/策略；后续新增显式company-scan task/profile，先支持原批准任意题目子集、实际截止日和动态小包/单题，复用同一Runner。不能只移除工厂12题检查，EvidenceBoard publication边界及answers计划/实绩判断、fresh/replay/resume须统一真实日期。首个真实12题小实验不等待generic扩展；扩展未实施，不宣称全池已能运行。

委托确认仍在同一大节点完成撤销/timeout测试和不同agent整包审查；不额外增加helper门。新能力只在各自独占候选，不写原真实库/namespace；研究用脚本响应不能冒充实际公司金融正例。

## 2026-10-18 — 共享引擎工程节点已验收，转真实运行入口

**工程节点完成：** 独立reviewer在同一节点关闭F01–F07，final.json状态为engineering_source_and_scripted_restart_accepted、open_findings=[]。最终12题使用原public owner/SDK/原SQLite/同一个Company Runner，cold脚本POST1次，原安全输出落库后os._exit86，全新进程恢复12题、新POST0、原物理预算attempt仍1；435.193秒，原600秒lease未扩大。907执行源码和5overlay已绑定，Task3另有8个独立拒绝/恢复反例。此为实际软件＋合成身份/同意/响应，不能当真实公司金融正确性或付费模型成本速度。

最终源码已按精确CAS应用。Company恢复Task3描述绑定提交2f853bc（含之前F07 acae964）；StockQA历史fixture正常hooks提交推送d739619（包含之前owner d5cfe50/核心52330ab），格式化后完整AST相同；Runtime b732a49原本地分支/no remote。IQS新增共享Task3工厂与12题E2E，本批正常提交推送；其他writer的2026-10-10 README不动。所有独审报告和薄证据可复核，原DB/回答正文/密钥不归档。

**下一大段实施中：** delegated-owner-candidate补明确agent委托确认，保留旧TTY且不冒称人工；不重复问既有权限。真实S1旧账仍有unknown/unpriced，原预算禁止将独立研究排除规则用于owner work；新委托不是清账授权，不用新库/改费用/盲重发绕过。需在原ledger中显式保留预约与累计上限的后续能力，再推进真实公司摘要、冷暖/恢复及模型准确性费用速度对照。正式search-backed checkpoint、金融/G3/F05/UI/一键/全池未完成。

清理记录真实保留：相关自有临时目录被自动策略在执行前拒绝删除，未绕过；原始日志/CAS/薄结果保留，本地临时DB和响应不发布。三张独立10包已发布、未自动派发，入口见2026-10-18-mainline-support/README.md。

## 2026-10-18 — 修复真实金融文字被密钥检查误拒

原Company event/receipt检查把risk-adjusted、task-output、mask-based、disk-failure中的裸sk-子串当凭证拒绝。不能靠改测试ID掩盖真实金融叙述错误：新增共用credential_marker，只对sk-要求左侧token边界，其他原标记/短前缀拒绝与隐藏思考守卫保持。先RED4F/10P，修后14P；原整套加新测试171P/1原Windows skip，独立24个未见自然词/真实凭证边界反例全部通过，同一整节点独审已签3路径。已正常本地提交Company `acae964c7a2fc99104b479636bdd79e789860422`，Lab无remote不新建。

完整12题原owner链路继续使用原冻结t04源，不把本次源变动冒充其受测版本，也不为无关guard重复昂贵批准fixture。secret-boundary-candidate/owned-temp的精确清理被自动审批在执行前拒绝，仅blocked by policy；未删除、未换方法。cleanup.json记录保留文件，不能报告全清理。0真实模型请求/0生产DB或名单写入。

## 2026-10-18 — 后续真实运行的明确委托确认（隔离候选实施）

用户已给予全部后续授权；当前原生公共接口却只编码native_owner_terminal，不能把agent执行谎标为人类TTY，也不能使用测试confirmer冒充真实grant。只读调查确认StockWiki confirmation record/1.0与StockQA inspection验证两端均固定此方法。因此后续生产接线在独占 `runs/shared-engine-production-2026-10-18/delegated-owner-candidate/` 实施显式委托分支；不是再次索取用户权限，不写真实namespace或扩旧确认。

施工范围：原rc1/record1.0/inspection1.1/TTY保持；新rc2/record2.0/inspection1.2表达native_owner_delegated_agent，single-action grant从固定owner路径读取，绑定原preview/request/scope/policy/quote/原账本、真实OS owner principal、consumer/deployment、SubjectRef/题目模块锁/模型/cohort、期限及撤销。agent来源只作可核来源记录，不能宣称同OS账户中的进程已被密码学鉴别。原预算/未知费用/当前权限/每次POST守卫保持；无消费者authorized=true、无--yes、无新费用账。未有公开原生grant前不得对真实批次发送。

测试集中覆盖旧TTY兼容、缺grant/改grant/跨主体或题目模型、过期撤销、并发幂等、错误namespace、POST前撤销、已收答案与真实费用保留及公开跨仓整链。先失败再实现；完成整个委托能力节点后由不同agent整包复核，修尽有效问题再应用源码，不增helper小门。当前12题旧流程工程验收继续单独完成，不因新候选延后签收；批量claim性能问题先记录真实数据，不缓存权限或默认延长lease来掩盖。

## 2026-10-18 — owner/Runtime精确接线范围已交付

StockQA owner服务5路径已正常hooks提交并推送 `d5cfe50e5d1f0377a754a2a94e491c6b44f6f783`；原SDK/原owner/原工作预算SQLite继续是唯一执行与计费来源。Runtime两路径正常本地提交 `b732a496d5dbfd904da1acca7482df4beb521e4c`（原分支codex/agent-run-02，无remote）。同一独立审查者签收7路径，45个未见漂移反例及19个最终guard回归通过；原软件批准/SDK脚本3P、Runtime31P、observer5P各保留自身分母和受测版本，不能相加当金融正确率。正常hooks仅换行/测试import整理，独立附录核等价后再次正常提交全部hooks通过。

另已用真实S1账本只读backup验证原生20→23迁移：每张旧表计数/完整行摘要保持、新9表零行、integrity/FK通过，原SHA保持；没有迁移原库或回填旧回答。完整12题原public owner＋Task3＋同Runner＋OS中断恢复仍在隔离验收；本轮真实模型请求0。来源、实际代次、缓存复用、未知费用和金融判断必须分开。

15个明确自有测试目录的删除被自动审批拒绝（仅返回blocked by policy），没有执行或换方式重试；路径与保留状态在cleanup-external-temps.json，不能报告环境全清。候选/DB副本不提交。下一步只完成当前12题整链及Task3独审，修有效根因，再推进真实公司运行入口；不重跑未变整套、不新增小节点门。

## 2026-10-18 — 唯一共享Runner组合入口已应用（精确两路径）
