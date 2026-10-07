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

## 7. 语义诊断（semantic-rules/1）

只在输入**显式**给出期望侧与claim侧时机械比较；任一侧缺失即 abstain：

| 维度 | 等价归一 | 冲突错误码 |
|---|---|---|
| subject | 别名→canonical；ticker 交集视为同一发行人（多挂牌） | `E_SUBJECT_MISMATCH` |
| period | 半年/全年/年化/季度 + 年份归一 | `E_PERIOD_MISMATCH` |
| metric | 受限词表→family（利润/收入/CFO/ROIC/ROE…） | `E_METRIC_MISMATCH` |
| unit | 50% ≡ 0.5 比例；亿/万换算；跨币种/跨量纲才冲突 | `E_UNIT_MISMATCH` |
| direction/scope/role | 显式枚举比较 | `E_DIRECTION_MISMATCH` / `E_SCOPE_MISMATCH` / `E_ROLE_MISMATCH` |

来源侧：同 URL 不同窗口 → `E_URL_WINDOW_CONFLICT`；显式 derives/paraphrase/环
→ `E_CIRCULAR_SOURCE`；关系未提供 → abstain `source_relation_not_stated`。

事实支持：历史 snippet 已清理 → 每个回答的
`support.claim_fact_support` 一律 abstain（`snippet_not_available`，
`support_source_type=url_hash_only`）。已有 agent 评审标签只能以
`agent_review_only` 出现，**永远不是人类 gold**；`scored` 且评审
`score_basis=insufficient` → `E_SCORE_BASIS_UNSUPPORTED`（依据不足的失败形态，
支持来源标注 `agent_review`）。

## 8. 与已发布统计的一致性

`replay --input index` 输出 `metrics.json.published_comparison`，对
`final-statistics.json` 的 matrix / equal_cap_thinking / json_off_adaptive /
independent_repeat_g10 / aggregate_budget / model_token_reference_usd 六段做
逐字段比对；`equal_to_published=true` 仅表示离线重算与冻结发布一致，
不表示事实正确。
