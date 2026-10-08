# EVID-LAB-01 下一轮小样本实验提案（草案预注册，未签核、未执行）

**状态：`execution_enabled=false`、`live_not_run=true`、`status=draft_not_signed`。**
本文件与配套 `experiment-proposal.config.json`（schema `1.1.0`）是**未签核草案**：
未获用户对声明上限的预算授权、未获总控live放行与预注册签核前，翻动开关无效、
不产生任何请求。运行时复用 StockQA 执行/账本/搜索，不另建客户端、调度器、缓存或
outbox，不向生产执行器发新字段，不复制任何新的网络/预算/缓存实现。

## 1. 沿用的冻结样本（不自行扩大）

- 三市场：宁德时代 300750、中信建投 06066、Alphabet GOOGL（真实历史身份样例，
  identity_revision 2/2/1 原样；`identity_file_sha256` 已冻结进配置）。
- 每司10题：IQS_01/02/04/05/08/09/10/12/13/16；题面+锚点逐题
  `question_sha256`（canonical JSON SHA-256）、rubric 1.0.0、截止日 `2026-10-07`
  的 `cutoff.sha256` 全部冻结于配置 `sample.frozen_hashes`，由
  `tools/gen_proposal_config.py` 从锁定输入确定性再生。
- **题组（具体到题号）**：
  - mixed_1 = [IQS_01, IQS_09, IQS_04, IQS_13, IQS_10]；
    mixed_2 = [IQS_02, IQS_05, IQS_12, IQS_08, IQS_16]（两组并集=冻结10题，互斥）。
  - themed_customer_market = [IQS_01, IQS_02, IQS_05, IQS_08, IQS_04]
    （客户价值/需求延续/护城河/规模交付，共享“客户竞争+财务”证据包）；
    themed_governance_finance = [IQS_09, IQS_10, IQS_12, IQS_13, IQS_16]
    （组织/回报/披露/股东/义务，共享“治理+负债义务”证据包）。
  - mixed 打包：每司按 mixed_1、mixed_2 各打一个五题包；themed 打包：按两个
    themed 组各打一个五题包。每包一次请求。
- **是否增加样本由用户决定**；默认不扩股票池、不加题。历史 snippets 已清理，
  证据必须重新检索（快扫只用搜索短片段，不下载财报/网页正文）。

## 2. 研究问题与四层报告（严格分开）

| 层 | 问题 | 指标 |
|---|---|---|
| L1 数据工程成功 | 请求/包是否按协议完成 | 请求数、成功/失败/未知、整包成功率 |
| L2 结构恢复 | 一题坏是否拖垮整包、可恢复多少 | 逐项契约有效率、item_inspection 可恢复率（缺则 not_measurable） |
| L3 来源支持 | claim 是否被当次片段支持 | supported/partial/unsupported/no_claims（agent分区盲评，非gold） |
| L4 评分锚点依据 | 高分是否有方向/区间依据 | scored 分母内的 basis supported/insufficient（≠精确分验证） |

四层分母互不混用；历史 186/24/396/70/326/191/14 不并入本轮分母。

## 3. 逐题主分母：冻结300计划槽（EL-05修正）

60 计划请求 × 每包5题 = **300 计划槽**，是唯一主分母。每轮必须同时报告：

- `sent_slots`（实际发出）、`not_sent_slots`（未发送）、
  `in_failed_packages`（失败包内题位，**不会消失**）、
  `unknown_answers`、`structurally_valid_answers`、`answers_with_claims`；
- 主率 = `structurally_valid / planned_slots`；
- answered/sent-only 视图**只能**作为 `conditional` 指标输出
  （条件：`not_sent == 0` 才可比），永不替代 300 槽主分母；
- unknown 计入逐题主分母、排除出评分依据分母，带 claim 仍出诊断。

实现与口径见 `stats.plan_slots_denominator`（schema `iqs_evidence_lab.plan_slots/1`），
单元测试覆盖“失败一半仍可报150/150”和“未发送槽位不消失”两个反例。

## 4. 实验因素与矩阵

- **A 打包**：`mixed_five`（上节 mixed_1/2）vs `themed_five`（两个 themed 组）。
- **B 证据**：`baseline`（检索片段原样）vs `annotated`（带显式真实主体/期间/单位/
  表头覆盖标注；无法确定期间/单位的片段剔除并记 unknown，不编造）。
- **C 思考**：DeepSeek `off/on` 为主对照；MiMo Pro 仅 `off/on` 小额对照
  （固定 mixed×baseline）。

| 模型 | cells | 每cell请求数 | 小计 |
|---|---:|---:|---:|
| DeepSeek（A2×B2×C2） | 8 | 6（3公司×2个五题包） | 48 |
| MiMo Pro（A1×B1×C2） | 2 | 6 | 12 |
| **合计** | 10 | | **60 模型请求 = 300 槽** |

**检索共享规则**：3公司 × 4条冻结query × (Brave basic + Tavily advanced) =
**24 搜索请求**，在任何模型调用前执行一次，10个cell共享同一批片段
（query 原文、`result_count=5`、`freshness=none`、phase `targeted_v1`、
每请求 reserve 0.016 USD 全部冻结在配置 `retrieval`，由
`tools/gen_proposal_config.py` 从锁定账本确定性再生）。

**context 选择与单位/表头约束**（配置 `retrieval.context_rules`）：
1. 按题选择上下文：只注入与该题证据包匹配的片段；
2. 每个切片强制保留期间表头行与单位/表头行，保不住的片段不进 annotated 臂；
3. 期间/单位无法确定 → 结构化 unknown，模型应给 insufficient_evidence，
   诊断器 abstain 而非 fail。

生成参数：`explicit_only/2`、`stream=false`、输出上限10000、官方 thinking 开关；
`finish_reason=length` 记失败；披露 DeepSeek thinking 忽略 temperature、
MiMo 开启强制采样的服务端行为。

## 5. 预算：逐模型token上界 × 冻结价（可复算）

配置 `token_reference_formula`（零缓存信用、每请求按上限、冻结公共价，DeepSeek peak）：

| 模型 | 请求数 | 输入上限/请求 | 输出上限/请求 | 输入价$ /1M | 输出价$ /1M | 每请求上界 | 小计 |
|---|---:|---:|---:|---:|---:|---:|---:|
| deepseek-flash | 48 | 7000 | 5000 | 0.30 | 1.20 | 0.00810 | 0.38880 |
| mimo-v2.6-pro | 12 | 8000 | 5000 | 0.435 | 0.87 | 0.00783 | 0.09396 |
| **合计** | 60 | | | | | | **0.48276 USD** |

公式 = `(input_cap × uncached_input_rate + output_cap × output_rate) / 1e6 × requests`
（配置与测试里逐项复算；上限取 `token_reference_estimate_usd_max = 0.49`）。
现金封顶 `cash_usd_cap = 4.00`、`model_http_cap = 60`、`search_http_cap = 24`。
**token参考与现金封顶不可相加**；发票未知；MiniMax 本轮不涉及。

## 6. 缓存、停止与崩溃恢复

- 应用缓存冷启动（输入指纹与历史不同）：不给缓存预算；缓存键绑定
  题意/锚点/身份/日期/上下文/模型/端点/生成参数/parser/transport policy
  （配置 `cache.cache_binds`）；warm miss 拒绝发送；provider 前缀缓存单独报告。
- 检索缓存：`version=retrieval-cache/1`、`ttl_hours=24`、
  `key_fields=[company, intent, query, provider, params, cutoff, snippet_set_sha256]`。
- **已声明缺口**：provider 只返回模型别名、不返回不可变后台revision，
  账本/缓存无法绑定实际模型 revision（配置 `retrieval_cache.declared_gap`）。
- 随机顺序：`(cell, company)` 单元以 seed=`20261007` 洗牌，登记于预注册JSON。
- 停止/接续（修正版）：reserve-before-send；已归档 run_id 禁止 prepare；
  **crash resume 只能结算未完成 reservation；unknown 预约只列清单并要求
  人工/总控决定，绝不自动重发**（`unknown_reservations=
  report_and_require_human_decision`、`auto_resend_unknown=false`）；
  未知结果不重新收费。
- 失败不补齐：每请求一次机会，无格式重试、无换模型拼臂。

## 7. 报告与判读规则

- 逐题分母见第3节300槽；整包分母=60请求；评分依据分母=scored条目；
  claim 支持分母=含 claim 的回答；unknown 规则同第3节。
- 思考假设只允许表述为“来源支持与语义维度 abstain 率是否改善”，
  不得表述为投资准确率提升；高分弱证据单独列出。
- 结构通过 ≠ 来源支持 ≠ 评分锚点依据；三层各自出表。
- 评审仍是两个互斥分区的 agent 盲评，`not_human_or_world_gold`；
  inter-rater 校准与人类 gold 校准保持 `not_run`。

## 8. 与 Phase96 既有结果的关系（不重复、不覆盖）

- Phase96 已完成准确性优先实验（108模型HTTP/56搜索相关HTTP、
  保守上界 USD3.871962），有官方数值参照、增强证据与实操手册。
- 本草案只检验**打包方式（mixed vs themed 五题包）与证据注释**对
  claim 支持率、诊断 abstain 率的影响；数值准确性结论以 Phase96 参照为准，
  本设计不重发其矩阵、不替代其实操手册、不重复其付费调用。
- 本包的60/24草案在拿到独立授权前也永不自动执行
  （总控 handoff-for-new-agent 已明确：不自动跑 Lab 60/24 草案）。

## 9. 短片段缺表头的可执行改进（证据臂落地）

1. 按题选择上下文（见第4节 context_rules）。
2. 保留必要单位/期间：切片强制携带表头行与期间行；携带失败不入注释臂。
3. 来源不足明确 unknown → 结构化 `period/unit = unknown`，诊断 abstain。

## 10. 协议/工具生成参数：现状与缺口

- 当前版本：`mimo-pilot-generation-policies-2026-10-07.json`（thinking/
  response_format/上限/缓存键）；observer 已改 `explicit_only/2` 并离线验证，
  未再收费重跑旧臂。
- 缺口：历史固定客户端注入默认0.7（48次实际发生，已披露）；缓存键必须包含
  transport policy；provider 不返回后台模型 revision（见第6节）；
  `finish_reason=length`、reasoning token 缺失按未知处理。
- 不新增生产执行器字段、不移植新的网络调用器。

## 11. 执行门（全部未满足，故未执行）

1. 用户对 60/24/USD4.00 上限的明确预算授权；
2. 总控对 live 运行的当前明确放行（含样本、输入、价格、清理方案）；
3. 预注册签核后才允许把 `execution_enabled` 改为 `true`。

**本包不执行任何一项；新真实搜索、模型实验、人类gold校准、生产采用、
Phase96 重跑均 `not_run`。**
