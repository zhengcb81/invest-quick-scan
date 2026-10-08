# EVID-LAB-01 metric-definitions（metric-definitions/1）

本文件定义离线诊断工具输出的每个指标。所有指标都是**结构/过程量**，不是投资事实
正确率，不改公司分数，不构成正式研究接受。价格全部是公共价目参考，不是发票。

## 1. 分母（永不混用）

| 分母 | 数值 | 来源 | 用途 |
|---|---|---|---|
| 模型HTTP请求 | 186 | 三归档 ledger `reserved kind=model` | 请求层成功/失败/未知 |
| 搜索HTTP请求 | 24 | 同上 `kind=search` | 搜索计数 |
| 契约有效回答 | 396 | 三归档 `answers[]` 合计（266+115+15） | 回答层结构统计 |
| 独立重复行 | 70 | 396 − 326（重复臂只用于结构稳定性） | 不进评审分母 |
| 支持审查 | 326 | 196 primary + 130 extension（互斥） | 评审标签统计 |
| scored 回答 | 244（总）/ 191（已评审） | `status == scored` | 评分依据分母 |
| 评审依据 supported | 14 | join `basis.supported` | 有限方向/区间依据 |

规则：任何报告出现一个比例，必须标注它用的是上表哪一行。`14/191` 不得表述为
“准确率”；`326` 与 `396` 不得合并；两个评审分区不是 inter-rater gold。

## 2. 请求层（run 级，来自 ledger）

- **model_requests / search_requests**：`reserved` 事件按 kind 计数。
- **success**：对应 `finished` 且 `state == completed` 且 `http_status == 200`。
- **unknown**：`reserved` 无 `finished`，或 `finished.state ∈
  {outcome_unknown, search_failed_or_unknown}`。
- **failure**：其余 `finished`。
- **charged_upper_usd**：`finished.upper_usd`（缺省用 `reserve_usd`）之和，round6。
  这是保守上界，不是实扣；**上界与 token 参考不可相加**。
- **unresolved_attempts**：见 unknown 定义（原样镜像冻结账本口径）。

## 3. 整包（package）与逐项（item）

- **package = 一次模型请求**（如五题包）。一题坏导致整包拒绝。
- **packages_total / packages_success / success_rate**：`state == valid` 的请求占比。
- **requested_items / valid_items / valid_item_rate**：块 `requested` 合计 vs
  有效请求内 `answers` 合计。
- **raw_strict_rows**：`state==valid` 且 `normalization` 为空的行内回答数。
- **normalized_rows**：`state==valid` 且 `normalization` 含 `full_json_fence`
  的行内回答数（只去完整外层包装）。
- **逐项契约可恢复率**：仅当被拒请求保留了 `item_inspection` 才可测：
  `items_recovered / items_measurable`，其中 `items_measurable =
  recovered + rejected`。缺 `item_inspection` 的请求归入
  `no_preserved_inspection`，`item_inspection_error` 归入 `inspection_error`，
  两者都计入 `items_not_measurable`，**不虚构额外有效答案**。
  本轮三归档 53 个被拒请求、264 个在包项目全部 `not_measurable`
  （`abstain_reason = no_preserved_item_inspection`）。
- 可恢复率永远 `diagnostic_only=true`、`never_production_pass=true`。

## 4. 回答状态

- **scored**：`status == scored`（有 1–10 分）。
- **unknown**：`status == insufficient_evidence`（合法非评分，不逼模型补分）。
- **not_applicable**：`status == not_applicable`（本轮三归档为 0）。
- 未知态仍带 claim：单独出 `support.unknown_state_claims`（abstain，
  `agent_review_only`），**不免除诊断**。

## 5. 耗时

- **sum_block_seconds**：单元内 `block.wall_s` 求和，round3。
- **median_block_wall_s（已发布口径 median_company_seconds）**：单元内
  `block.wall_s` 的中位数（一个 cell 每公司一个 block 时等于“每司中位数”），
  round3。是**块中位数**，不是把 median 乘公司数当实测总耗时。

## 6. 费用与缓存

- **reference_usd**：`((in − cached)×input_rate + cached×cache_rate +
  out×output_rate)/1e6`，按归档 `route-snapshot.json` 冻结价目，round8/6。
  语义 = 公共 peak/undiscounted 参考，**不是发票**。
- **usage_missing / cached_usage_missing**：receipt 缺 usage 或缺 cached 计数 →
  该请求费用记 unknown，不补 0 冒充。
- **model_token_reference_usd**：三归档 by_model reference 求和（0.392538），
  与 charged_upper 分开报告。
- **package_quota**：`minimax = unknown`。套餐实扣**不能**由 token 推断。
- **cache_hits / cache_misses**：`chunk.cache_hit` 计数；provider 前缀缓存与
  应用缓存分开表述，53 个失败块不称缓存成功。
- **temperature_deviation_attempts**：`provenance-check.json` 的
  `inherited_default_attempts` 合计 = 48（实际 0.7 与声明省略不一致），
  作为混杂因子显式报告，不回写原记录。

## 7. 语义诊断（semantic-rules/3，2026-10-08 残余整改后）

只在输入**显式**给出期望侧与claim侧时机械比较；任一侧缺失即 abstain：

| 维度 | 等价归一 | 冲突错误码 |
|---|---|---|
| subject | 别名→canonical；ticker 交集视为同一发行人（多挂牌） | `E_SUBJECT_MISMATCH` |
| period | dict保留 `half/quarter` 子期间（str统一）；半年/全年/年化/季度+年份归一；kind冲突即矛盾；子期间或年份缺一侧→按具体理由abstain（`claim/expected_period_year_missing`、`claim/expected_subperiod_missing`），不靠关键词补年；**`kind=custom` 完整保留 `start/end`（ISO日期归一）并只比较双方明确提供的边界：全等→pass、任一明示边界不同→fail、任一侧缺边界或两侧都缺→abstain（`custom_boundary_not_stated`、`claim/expected_custom_boundary_missing`）、未知形态→abstain，任何缺边界情形都不得肯定一致** | `E_PERIOD_MISMATCH` |
| metric | 受限词表→family（利润/收入/CFO/ROIC/ROE…） | `E_METRIC_MISMATCH` |
| unit | 50% ≡ 0.5 比例；亿/万换算；跨币种/跨量纲才冲突 | `E_UNIT_MISMATCH` |
| direction/scope/role | 显式枚举比较 | `E_DIRECTION_MISMATCH` / `E_SCOPE_MISMATCH` / `E_ROLE_MISMATCH` |

来源侧（v3）：无期间窗口 → abstain `source_window_not_stated`；无claim目标期间 →
同报告比较列/同URL不同内容片段视为互补 → pass；只有 **claim目标期间与全部引用窗口冲突
且没有任何引用来源缺窗口** → `E_URL_WINDOW_CONFLICT`（有兼容窗口则 pass；
**已冲突+存在未知窗口 → abstain `unknown_source_window_present`，不伪造未知来源的窗口**）。
显式 derives/paraphrase/环 → `E_CIRCULAR_SOURCE`；关系未提供 → abstain
`source_relation_not_stated`。
来源计数：独立来源数=去重URL数，片段数按 `(url, content_sha256)` 计，URL复用**不增加**
独立来源数（`semantic.source_counts`）；来源缺窗口属于“未知”，**不因未知多给独立来源分**。

来源类别（structure-rules/3）：每条记录的 `support_source_type` 由 fixture
`source_category` 统一映射（synthetic→synthetic、historical→historical_model_output、
已收集 real_source_snippet→real_snippet、未收集→none），并对整个document全量校验；
输出里的 `input.answer_sha256` 只是**本次被回放输入**的 canonical SHA，
**不构成历史来源证明**——历史来源以 `archive_provenance_verifier` 独立回链
锁定归档为准（`case.answer` 有值就必然逐字比较，不受可选 `answer_sha256` 有无影响）。

事实支持：历史 snippet 已清理 → 每个回答的
`support.claim_fact_support` 一律 abstain（`snippet_not_available`，
`support_source_type=url_hash_only`）。已有 agent 评审标签只能以
`agent_review_only` 出现，**永远不是人类 gold**；`scored` 且评审
`score_basis=insufficient` → `E_SCORE_BASIS_UNSUPPORTED`（依据不足的失败形态，
支持来源标注 `agent_review`）。

## 7b. 逐题计划槽分母（iqs_evidence_lab.plan_slots/1，2026-10-08整改）

预注册主分母 = `planned_model_requests × questions_per_request` = **300 计划槽**。
必须同时报告 `sent`、`not_sent`、`in_failed_packages`、`unknown_answers`、
`structurally_valid_answers`、`answers_with_claims`；主率 = 结构有效/300。
`answered/sent-only` 视图仅作 `conditional` 指标（条件：`not_sent == 0`），
**永不替代300槽主分母**；失败包内题位与未发送槽位不会从分母消失。

## 8. 与已发布统计的一致性

`replay --input index` 输出 `metrics.json.published_comparison`，对
`final-statistics.json` 的 matrix / equal_cap_thinking / json_off_adaptive /
independent_repeat_g10 / aggregate_budget / model_token_reference_usd 六段做
逐字段比对；`equal_to_published=true` 仅表示离线重算与冻结发布一致，
不表示事实正确。
