# S06 只读实现预审与固定反例

日期：2026-09-26。审查者：独立 question_audit 子代理。范围：本仓现有路由、48 个模块及 S06 任务接口；不修改生产代码，不访问网络，不调用模型，不读写外仓。本文件是实施前建议，不是 S06 已完成或 S05 r3 已放行的证明。S05 正在收尾，以下定位以文末读取快照为准。

## 1. 可以复用的能力与必须保留的边界

- `scripts/module_registry.py:load_current/load_package` 已返回 `(package, modules, release, contexts)`，模块来源是经哈希验证的发布归档。新路由必须从这里取候选，不能重新读可编辑 catalog 决定实际派发。
- `scripts/question_sets.py:compose(profile, mode, output_dir, answer_format='legacy', *, package_id=None, route_decision=None, max_questions=None)` 已有接缝；`select_questions_for_route` 允许部分画像；`_select_from_module_ids` 已处理模块依赖/冲突、类型替代、关键属性继承、去重。
- `validate_profile` 必须继续严格处理旧完整画像。它要求一个类型、一个主阶段、来源、high/medium 置信度；即使 full 也只允许两个行业。不能为了部分路由删掉这些断言。
- `routing_question(company, ticker, exchange, as_of)` 仍产生兼容问题文件里的 `ROUTE_01`，要求模型给嵌套 routing 对象；它读当前库，只列类型/行业/阶段/属性的 ID 和名称，没有机器化 activation。保留这个旧入口；新发布版请求入口应独立，不能悄悄换旧题输出协议。
- `module_contract.validate_route_decision(decision, release)` 是结构/发布身份校验；它不判断经济分类、不验证真实搜索，也不检查执行当时的 TTL。不要把通过此函数称为“路由已核实”。
- 历史 manifest 验证必须保持离线、按原决策时点重现。到期的是未来派发权限，不是已经完成的观察和旧决策的可读性。切勿在历史校验函数中加入 `datetime.now()`，让昨天合法的快照今天无法读取。

本轮读取到 48 模块、222 题：common 1、types 8、industries 21、stages 7、overlays 8、diagnostics 3。所有 48 模块目前都没有 activation、dependencies、conflicts 字段；S04 对这些 legacy ID 的豁免不能当作 S06 自动选用许可。

## 2. 必须先明确的实现缺口

### A. 路由 v1 无法表示任务要求的无搜索和策略拒绝

当前 `route-decision.schema.json` 只允许 `deterministic|searched_llm|manual`。前两种 basis 无论 selected/rejected/uncertain 都要求非空 sources；每个发布模块必须有决策。因此“搜索未执行，其余模块 uncertain”“未请求 porter，按策略 rejected”都无法无来源表达。不能复制一条无关 URL 给所有模块凑 schema。

建议新增版本化路由 schema 2.0.0，并保留 v1 历史读取：

| basis / decision | 来源与执行条件 |
|---|---|
| policy / selected | 只允许 common 等明确无须分类证据的通用模块；必须有受信任的 rule_id。 |
| policy / rejected | 只允许未请求的可选诊断/投资视角、显式策略禁用等列举情况；不能把“没有证据”当作客观不适用。 |
| unavailable / uncertain | 可以 sources=[]，必须列 search_unavailable、missing_evidence 或 conflict 等 reason_code。 |
| deterministic 或 searched_llm / selected | 客观分类必须有截止日前、匹配实体/作用层的来源；searched_llm 还必须绑定真正执行器回执。 |
| deterministic / rejected | 排他类型、明确反证等必须绑定判断规则及其证据；不是空来源的否定事实。 |
| manual | actor/reason/UTC valid_until 来自受信任用户输入；不能由模型自报。覆盖事实证据不足时须保留 override 标记。 |

`status=resolved` 应指必要分类轴已经解决，不要求对宇宙中每个潜在新行业都证明为假。未涉及模块可按有证据的排他规则 rejected；缺证据者仍 uncertain，此时状态应 partial。此语义须写测试，避免为了 resolved 编造 47 个拒绝理由。

### B. 快照缺少会改变实际问题的输入，也缺少策略身份

v1 只封存 entity_id/as_of、release/router_version 和 module_decisions。它不能封存 cycle_position、recovery_rationale、业务边界、缺口、搜索/模型回执、用户策略等。现有 compose 只检查 route 与 profile 的 entity_id/as_of 相等；profile 里的类型、阶段和周期信息仍可与已选模块不一致，进而渲染错误口径。

建议 v2 封存 `profile_context`，compose 从该快照派生渲染 profile；外部另传相冲突值应拒绝。profile_context 不包含公司财报正文，只包含短标签、证据引用和必要身份/会计/分部口径。决策还应绑定 `module_package_id`，因为相同 release_id 可能对应不同 contexts/response resources 的 package。

router_version 目前由 `publish_library()` 写死为 1.0.0，release 只存版本字符串，没有规则正文或规则 hash。S06 不能只修改 Python 判断然后沿用同一版本。新策略应有唯一 `policy_version`、规范化 `policy_sha256` 与不可变策略工件；新发布包/锁绑定它，历史决策按对应策略读取。不得用当前规则重解释旧路由。

### C. 必须补全静态机器策略；现有文字不能直接执行

建议每个 legacy 模块对应一条策略记录，且机器检查恰好覆盖 48 个 ID，无未知 ID、无缺项：

| 轴 | 现有 ID | 最小规则 |
|---|---|---|
| common | common | 所有已核实实体必选，24 核心仍冻结。 |
| type | operating, bank, insurer, capital_markets, property_owner, property_developer, holding, pre_revenue | resolved 时恰好一个；业务经济实质优先，不由名称或挂牌地点推断。 |
| industry | software, internet, semiconductors, hardware, industrial, auto, consumer, retail, healthcare, medtech, resources, materials, utilities, telecom, transport, energy_transition, agriculture, professional_services, construction, leisure_media, other | 有主营/利润/资本占用/存续风险证据；other 只表示已知业务无匹配模板，未知业务为 uncertain。 |
| lifecycle | validation, commercialization, scaling, mature, turnaround, declining | resolved 时恰好一个；scaling 不由股价或“成长股”称号推出。 |
| cycle | cyclical | 物理文件仍 kind=stages，但策略轴独立，不能占用唯一主阶段名额。 |
| attribute | cross_border, controlled, listing_structure, concentrated, acquisitive, subsidized, distressed, recent_listing | 每个属性按实际经营或权利暴露判断；海外挂牌不自动 cross_border，股价下跌不自动 distressed。 |
| optional diagnostic | dupont, porter | 需要用户或受信任策略提出具体未解问题，不能自动全选。 |
| recovery diagnostic | recovery | 周期下行/低谷/初步修复、经营修复或衰退性质待辨；distressed/turnaround/declining 推导启用，但不改变当前分数。 |

新增模块的 activation.required_evidence/exclude_when 当前是字符串数组，仍是给研究者/LLM看的证据要求，不是可以直接 eval 的表达式。策略负责已知机械规则和门槛，LLM只提出带来源的候选。未知谓词、未注册策略或矛盾条件应 fail closed。

物质性阈值、路由迟滞目前没有数值或时间定义，不能把“合理判断”交给较弱模型随意实现。实施前必须冻结可配置的进入/退出门槛、重大事件例外与缺证据处理。收入份额不能成为唯一门槛；亏损分部、资本占用和关键生存依赖必须可以凭明确机制进入。证据不足时保留旧历史路由并标待复核，不把旧分类伪装成新核实结果。

### D. 多业务 full 与旧画像上限存在冲突

本轮实际调用 `select_questions(profile, 'full', ...)`，传三个行业得到 `ValueError: invalid number or duplicate industry_modules`。设计写“三个及以上重大业务拆分或转 full”，不能仅把 mode 改成 full 就声称实现。

建议：旧 validate_profile 不变；新路由路径允许 explicit full 下三个及以上已证实且有业务边界的行业，记录 multi_business coverage gap；quick 返回明确的 `requires_full_or_segments`，不静默取前两项。若分部的类型/主阶段互相冲突，必须拆分，不能用 full 合并成一个经济实体口径；母公司 holding 画像只作集团资金/资本配置层面解释。不得仅因第二条行业标签就自动改 holding，例如半导体设备与工业自动化可能属于同一经营机制。

需要分部时返回待处理的 scope 建议，不能在 S06 自行创建 StockWiki entity/segment ID。分部 ID 和身份合并属于上游身份拥有者。

### E. 已选风险题仍可能被预算静默延后

本轮真实函数探针：operating+semiconductors+scaling+distressed+recovery 的 quick 为 34 题；`_apply_question_budget(chosen, 24)` 保留 24 核心，却把 DISTRESSED_01、DISTRESSED_02、RECOVERY_01—04 全部延后。这些题没有 critical，当前“已选重大风险不丢失”不能仅靠模块选中实现。

建议由受信任路由策略输出 `mandatory_question_ids`：已确认 distressed 至少保证 DISTRESSED_01/02；本版本若承诺“触发恢复即问四题”，同时将 RECOVERY_01—04 列为路由派发必需项。它们仍为 context/diagnostic，不加入核心分母，也不修改已发布题目的 critical 字段。预算不足返回必需题数及预算错误，不生成半成品问卷；可延期项目逐项保留原因。新 mandatory 集合必须可由冻结策略重算，不能由 LLM任意抬高预算。

### F. 任务允许文件范围不足，不能照四行范围直接完成

S06 当前 allowed_changes 仅 question_sets.py、routing.md、route schema、test_question_sets.py。上述行为至少还涉及：

- `scripts/module_contract.py`、`tests/test_module_contract.py`：新旧 schema 分派、policy/unavailable、历史校验与执行校验分离。
- 版本化路由策略工件及其测试；若采用独立 `scripts/routing.py`，应先在任务卡中列出，不能隐性塞入另一份执行器。
- `scripts/module_registry.py`、相应发布/锁 schema 和测试：策略版本/hash 绑定和新 router_version 发布；须在 S05 稳定快照后串行实施。
- `tests/test_module_registry.py`：真实 compose、预算、历史 manifest 与新路由集成。

这是实施范围需明确的依赖，不是建议现在编辑这些文件。本次仅产出本报告。上游 StockQA 回执适配和下游持久化/调度仍由 Q13/W15 拥有；S06 不能伪造“已联网”来完成本地测试。

## 3. 建议新增的公共函数与数据结构

名称为建议，不代表已存在。优先使用一个纯路由模块，question_sets 只提供 CLI 和组合接线；不在 skill 内新建 LLM client、provider fallback 或持久队列。

```python
build_route_request(identity_context, *, package_id, user_policy) -> RouteRequest
resolve_route_decision(route_input, *, package_id, candidate=None,
                       execution_receipt=None, user_policy,
                       previous_decision=None, now_utc) -> RouteDecisionV2
validate_route_for_execution(decision, *, package_id, user_policy, now_utc) -> None
profile_from_route(decision) -> dict
compose_from_route(decision, *, output_dir, answer_format, max_questions,
                   user_policy, now_utc) -> dict
diff_routes(previous, current) -> RouteDelta
```

- `build_route_request` 使用冻结模块的适用、排除、证据与版本化策略生成兼容 StockQA 的问题文件和请求 manifest；候选输出使用独立协议 ID，例如 ROUTE_02，保留旧 ROUTE_01。它不调用网络，不把身份合并交给 LLM。不要假设上游存在尚未验证的新 CLI flag。
- `resolve_route_decision` 是纯函数：显式 now_utc、固定输入得到确定输出；不读取系统当前时间，不从环境获得模型身份。identity/用户覆盖/真实执行回执由可信调用方传入；候选里的 actor、entity_id、search_receipt_id、决策时间不能覆盖这些输入。无法确认身份应报错；已确认身份但分类模糊可生成 partial。
- `validate_route_for_execution` 检查输入身份、包/策略兼容、当前人工覆盖 TTL、来源 cutoff、已核实候选、风险必需集和主轴冲突。`now_utc == valid_until` 必须过期。函数不得写回旧快照。
- `compose_from_route` 从 route 内的 profile_context 派生 profile，并调用现有 compose；直接 `compose(..., route_decision=...)` 同样必须经过执行门禁，不能留下绕过路径。历史 `_validate_published_manifest` 只运行归档验证，不运行当前时钟门禁。
- `diff_routes` 返回 entered/exited/retained/uncertain 模块及原因、旧新 decision ID、scope 差异；题目键必须使用稳定题 ID/语义/作用层，不能因为某个模块版本变动重问所有题。此函数只给增量建议，StockQA决定缓存/待办，StockWiki保存历史。

建议数据结构最小字段：

```text
RouteInput:
  identity_context = entity_id + identity_receipt_ref/hash + listings + scope + segment_id?
  as_of, requested_mode, event_refs[], verified_facts[], previous_decision_id?
  user_policy = policy_id/hash + enabled_lenses/reasons + requested_diagnostics/reasons
                + manual_overrides(actor, module_id, reason, valid_until)

Candidate:
  schema_version, question_id, candidate_modules[]
  每项 module_id + confidence + reason_code + 短依据/反证 + source_refs[]
  只提出分类候选，不自报最终 selected/hash/执行元数据。

RouteDecisionV2:
  schema_version, decision_id, module_package_id, release_id, router_version
  routing_policy_ref/hash, input_identity_ref/hash, entity_id, scope, segment_id?
  as_of, decided_at, status, previous_decision_id?
  profile_context:
    company/ticker/exchange/security_id/security_class/会计与报告口径
    company_type?, industry_modules[], stage?, business_subtype?
    cycle_sensitive(可未知), cycle_position + evidence_refs
    recovery_review + trigger_codes + recovery_rationale + evidence_refs
    overlays[], diagnostic_modules/reasons, investment_lenses/reasons
  material_businesses[] + coverage_gaps[]
  sources[]: source_id + title + URL + published_at + 短claim + entity/scope绑定
  execution: search_status + provider/model_requested/model_resolved/model_revision?
             + request/attempt/search_receipt_ref + prompt_sha256 + answered_at
  module_decisions[]: 全部发布模块各一条，按module_id排序
    module_id/version + selected/rejected/uncertain + basis + rule_id/reason_code
    confidence + rationale + source_refs[] + manual_override?
  dispatch_plan: requested_mode/resolved_mode + requires_full_or_segments
                 + mandatory_question_ids + deferred_modules/reasons
```

上述字段均应有类型、长度与封闭枚举/对象约束，来源只保留 URL 和短 claim，不包含正文。execution 是执行器回执的受验证投影，不是第二份事实数据库；未知实际模型版本保持 null 并禁止相应模型比较，不猜测。decision_id 对完整规范化快照计算，排序不依赖 LLM返回顺序。

cycle_position 应使用可判定枚举如 upturn/peak/downturn/trough/recovery/unknown，展示说明另存。不能用中文自由文本“好像低谷”触发恢复；已核实 trigger_codes 才启用。搜索不可用不抹掉仍有效的可信确定性事实，也不为新候选制造来源。

## 4. 五组先红后绿的固定公开入口反例

通用 fixture：虚构实体 E_SEMI/E_DIST/E_MULTI；证券 S_A/S_H 映射同一 entity；来源 example.invalid；信息截止日 2026-09-19；可信决策时钟 2026-09-20T12:00:00Z。固定执行回执只用于离线验证，明确标为 fixture，不宣称真实搜索。模型 transport 可 stub，schema、resolver、compose、预算与 manifest 验证不得 stub。

### T1：半导体扩张，包含未知 ID 和候选排列反例

- 输入：已商业化设计/设备收入，已验证客户复制和扩产证据；type=operating，industry=semiconductors，stage=scaling；无周期低谷、属性、诊断或投资视角。
- 公共路径：build_route_request → resolve_route_decision → compose_from_route quick/full → validate_manifest_metric_contract。
- 精确断言：本次 48 模块基线选择恰好 common/operating/semiconductors/scaling；quick=28，full=34；恰好24核心构念且无重复，两个类型替代规则保留；A/H同实体选择相同实体模块，不产生两个路由实体。
- 打乱候选和候选模块顺序，固定 now 后 decision ID、问题顺序、语义与方法指纹不变。添加不存在的 `ai_super_chip` ID 必须在写 questions.json 前报错；不能悄悄转成 other。
- 先红注入：放行任意候选 ID 或对候选列表不做规范排序，相关断言必须失败。

### T2：成熟周期低谷叠加恢复，而非改成 turnaround

- 输入：相同半导体经营实体，主业务成熟；有可核实的行业库存/订单下降和低利用率证据，cycle=trough；现金尚覆盖义务，没有违约证据。
- 断言：选 common/operating/semiconductors/mature/cyclical/recovery；不自动 distressed，不把主阶段改 turnaround；cyclical 不占主阶段名额。profile_context 保存周期与恢复原因，进入 decision hash；只改这些已核实原因产生新决策，不能仅保存在外部可变 profile。
- 该基线 quick=34、full=42；恢复四题为 diagnostic，核心分母仍24。预制低当前分和高恢复证据时，路由/组合不能改分或取消低分。
- 反例：唯一输入是股价下跌40%，但无经营/行业证据，不能因此选择 cyclical、recovery 或 distressed；“other”也不能兜底成已分类。
- 先红注入：让任何股价下跌触发 recovery，或把 cyclical 当主阶段，测试应失败。

### T3：困境成长与预算边界

- 输入：产品和客户扩张证据足以支持 scaling，同时有已核实 covenant breach/到期资金缺口支持 distressed；不是因为亏损就贴困境标签。
- 断言：保留 scaling，并叠加 distressed+recovery；不强制改 turnaround；完整 quick为34题。已确定的 DISTRESSED_01/02 与本版本承诺的四道 RECOVERY 进入 mandatory 派发集合，仍不进入24核心分母。
- `max_questions=24` 在导出前拒绝，并报告 mandatory 题数至少30；不得得到“已完成核心且困境风险全部延期”的问卷。`max_questions=30` 可延期半导体/阶段补充题，但不能延期这六道风险/恢复题。现有类型关键题仍继承为必需。
- 先红注入：恢复当前 `_apply_question_budget` 只看 core/critical 的行为，本组必须失败。另注入重复替代核心题，须在派发前失败。

### T4：三个重大业务，不静默截断；错分类与缺分部边界

- 输入：三个互不等价、有独立经济证据的半导体/软件/工业分部，全部超过配置的进入门槛，或其中低收入分部对集团存续具有明确重大风险。候选顺序轮换。
- quick 断言：返回 requires_full_or_segments，保留三项候选和各自缺口；不导出伪装覆盖完成的双行业问卷、不从池删除实体。full 分支仅在统一类型/主阶段可成立且边界明确时包含全部三行业；否则返回分部待处理，不自动创建 segment ID。
- 子反例：半导体设备+工业设备描述同一收入机制，不因两个标签自动 holding；另一集团子业务分别为验证期与成熟期，不能用一个 stage=平均/other 或复制全部行业口径到所有分部。
- 父公司资金画像与分部画像 scope 必须分离，24核心不能按三个分部机械求集团均分；现有 legacy validate_profile 对三个行业仍应保持拒绝。
- 先红注入：`industry_ids[:2]`、按最大收入忽略重大风险分部，或让 full 继续走旧 validate_profile，分别有精确失败断言。

### T5：缺搜索、证据冲突和执行 TTL，兼顾历史可读

- 输入A：身份已确认，无可复用有效业务证据，search_status=unavailable。结果仅 common selected（policy）；客观类型/阶段/行业 uncertain（unavailable，空sources）；未请求诊断/lens按列举策略 rejected。不得虚构 operating/mature/other，不补5分。
- 输入B：搜索失败但输入含仍有效、由可信通道导入的 distressed 证据；应保留 common+distressed+recovery，业务轴仍 uncertain。将相同证据放到未核实LLM自由文本中则不能获得同样待遇。
- 输入C：候选说模型已搜索，但可信 execution_receipt.search_status 不为executed，或 request/prompt/entity/cutoff不匹配，必须拒绝 searched_llm 选择；模型自报 actor/时间不能形成手工授权。
- 输入D：人工覆盖 valid_until=2026-09-21T00:00:00Z，在23:59:59Z可执行；恰好到期及之后均拒绝新导出。原已封存决策和旧 manifest 在到期后仍可历史验证。只拿 decided_at 比较应触发红测。
- 先红注入：为空来源填公共URL、信任候选自报search_receipt_id、以 decided_at 当执行时间、把 TTL 检查加到历史读取上；四种均要失败。

每组应保存第一次失败及最终通过日志、固定输入/预期和实际调用选择器。不能以新函数尚不存在的 ImportError 作为充分红测；实现骨架后仍需验证这些错误行为会被断言捕获。所有输出写唯一临时根，清理后核对 repo 未产生缓存/测试产物；默认离线测试禁止网络。

## 5. 建议实施顺序与放行点

1. 先等 S05 明确放行并锁定 source/package hash；不要在进行中的 S05 文件上并发落代码。补齐 S06 精确允许文件范围和 policy 归档方案。
2. 定义 route v2、policy/unavailable 来源规则、可信时钟/回执边界以及 legacy v1只读策略；先完成 T5 schema/TTL 正反样例。
3. 冻结覆盖48模块的机器策略表、模块轴例外、物质性/迟滞规则与 mandatory 风险集合；验证无遗漏、无未知规则、无依赖冲突。
4. 实现纯 resolver、候选请求/回执解析、profile投影和 route diff；先跑 T1/T2/T3，不连接实际LLM。
5. 接入真实 compose 及新 CLI；保留旧 routing/validate_profile；明确 full/segment 特殊分支，跑 T4、预算、未知ID、直接入口绕过和历史回归。
6. 用独立审查重跑五组反例并核对原始结果。S06 只宣称本仓离线路由与导出就绪；实际搜索、持久化、增量执行、UI由对应后续任务完成。

## 6. 实际只读探针与快照

CodeGraph context 成功读取了 routing_question、validate_profile、validate_route_decision 及关联发布身份验证器；之后读取具体文件与 JSON。执行命令为内存 Python 脚本 `python -B -X utf8 -`，仅调用现有纯选择/校验函数，没有生成生产文件或网络调用。

实际结果：

```text
SEMICONDUCTOR quick: 28 questions / 24 core / common,operating,semiconductors,scaling
SEMICONDUCTOR full : 34 questions / 24 core / common,operating,semiconductors,scaling
DISTRESSED quick  : 34 selected; budget24 retains0 distressed/recovery questions
deferred          : DISTRESSED_01/02, RECOVERY_01/02/03/04
legacy full3      : ValueError invalid number or duplicate industry_modules
unavailable route : ValidationError [] should be non-empty
```

读取时 current package 为 `pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f`，router_version仍为1.0.0。S05正在收尾，因此这是范围明确的预审快照，不声称其他代理未继续修改代码。

| 文件 | 读取时 SHA-256 |
|---|---|
| scripts/question_sets.py | b6c6ad4219be1ae8a87af44a40cd2199fd2e33a90a5afbc56bc14b04d342bb9b |
| scripts/module_registry.py | 4ae0fd4359a5c2e583f85a790ba8ac929190bc97d1f9111687bfe78a74a35e0b |
| scripts/module_contract.py | 069d14199239bbfc0b38aad88f360228d5fc0a2f6ca324c037850fd2fa183a97 |
| schemas/quick_scan/route-decision.schema.json | 2ac2fa46d445779d30f7cafcf834cd69df0fa9bcc9cd5722bd6baf3799306071 |
| questions/catalog.json | 252dab9e3f71868a71147ecb7dac64cc187d7d56002b28b266a74f406facaf10 |
| docs/implementation/tasks.json | 8ef8a7266fb618c95201a612e2298a40f6906e6d37d3bc99c375b84c351eb8bb |
| docs/modular-question-bank-design.md | 5f5a204a4010328d1c6da8ccc84588f51b2c14215224bde1af044588bf9d7359 |
| references/routing.md | cf1b03bbb0af086d6bf5da0c990f001d3b4c8ce09c8ce50f89225b2f008b1761 |

本报告新增建议函数和字段尚未实现；T1—T5是建议固定验收设计，只有第6节标注的现有函数探针已经执行。
