# 正式 search-backed 评分路径 — 差距与分阶段实施 — 2026-10-18

状态：设计/差距分析，未改代码、未调用模型。目标是让公司 scan 从“零外搜研究型”升级为“有界外搜 + verified search receipt + 正式评分 checkpoint”，而不是绕过现有闸门。

## 现状（只读核实）

| 层 | 事实 | 位置 |
|---|---|---|
| 公司 scan profile | 资源上限硬编码 `max_search_queries_per_session = 0`，非零直接拒绝 `scan_bounded_zero_search_limits_required` | `iqs-company-agent-lab/src/iqs_company_agent_lab/scan_profile.py:21-37` |
| 共享任务工厂 | 强制 0 查询；非零拒绝 `bounded_registered_limits_required` | `invest-quick-scan/scripts/shared_company_task.py:170-181` |
| owner 暴露合同 | `assert_research_task` 要求 `search_service is None`、0 查询、control 中的 `search_policy_sha256` 等于 `NO_EXTERNAL_SEARCH_POLICY` | `StockQAbyLLM/src/utils/quick_scan_owner_budget_continuation.py:700-735` |
| QA runner | **已支持** `require_search` + `search_policy`，并有策略加载/路由准入（拒绝未准入路由，fail closed） | `StockQAbyLLM/src/runners/llm_runner.py:1574,1669,1902-1933`；`src/config/quick_scan_search_policy.py` |
| 搜索供应商 | 已有 external search provider、策略 schema、报价/配额解析 | `src/providers/external_search_provider.py`、`config/quick_scan_search_policy*.json` |
| checkpoint | 标准 v1/v2 路径要求 verified search；v3 是 research-only，不适用 | `StockQAbyLLM/src/utils/quick_scan_work_store.py`（checkpoint/validate） |

结论：**底层能力在，卡在“owner 合同 + profile/工厂 + 评分闸门”三处有意为之的零外搜限制。**

## 分阶段实施

### S1 owner 合同（先决）
- 新增强制显式的 search 暴露合同（建议 refresh_request 1.6 / policy 1.6 或独立 search-exposure 文档），字段至少：search_policy_ref+sha256、max_search_queries_per_session、max_search_cost_micros、route ids、information_cutoff、cell 绑定。
- 取消对 `NO_EXTERNAL_SEARCH_POLICY` 的硬编码相等判断，改为“引用必须精确等于本 cell 批准的 search policy 文档哈希”；无 search 的旧合同保持原行为。
- 预算：搜索费用与模型费用分开记账，先预约后结算；搜索未准入时 fail closed。

### S2 profile + 共享工厂
- `scan_limits` 允许显式 0 < queries ≤ LIMIT_CAPS["max_search_queries_per_session"]，并要求同时提供 search policy ref；默认仍为 0。
- `create_company_scan_task` 接受显式搜索模式：把 policy ref/hash 与 query 上限写入 task limits 与 runtime profile；没有 policy 时仍拒绝非零。
- 保持旧 1.4/1.5 任务字节行为不变（显式版本分支，不隐式升级）。

### S3 runner + 搜索回执
- 任务携带 policy 文档；runner 以 `require_search=True` 启动，加载策略、准入路由；任何路由未准入即停止，不回落到 native search。
- 记录每次搜索的 query/来源/时间/费用回执，生成 `search_receipt_id`，绑定到答案与 checkpoint。
- 搜索证据仍要满足来源/日期/截止日规则；不可用即 `search_status=unavailable`，不能伪造。

### S4 checkpoint / seal / publication
- 走标准 v1/v2 checkpoint（要求 verified search + 原 lease），复用既有 seal/outbox/StockWiki import/ACK；不把 v3 research-only 混入评分。
- 失败/未知保持原状态，不重发、不清费用。

### S5 金融与质量闸门
- 评分答案仍需金融复核（来源、口径、反证、缺失）；search-backed 不等于准确。
- 先做 1 家公司 1 题的评分试点，人工/独立复核后再扩大。

## 试点建议

- 对象：CATL（已 verified、已有 owner policy/route 与预算），1 题（IQS_12 或 IQS_16 中的一题），单 pack。
- 前置：一份可执行的 search policy（已准入 route、明确费用上限、凭据环境变量存在但不在仓库）、owner 新 exposure 合同、预算预约。
- 验收：1 次真实搜索 + 1 次模型调用、verified search receipt、v1/v2 checkpoint、seal + import + ACK、费用与旧 102 行预算的可解释增量；失败则保留现场。
- 成本：搜索按 provider 计价 + 模型 MiMo 单题约 US$0.007–0.01（以实际 usage 为准），在预算政策内。

## 风险与不做

- 不做：绕过 owner 合同直接开搜索、伪造 search receipt、把 research-only 结果当评分、自动重发未知请求、无准入路由时回退 native。
- 风险：搜索供应商条款/费用、路由凭据、评分口径与金融复核、预算并发；都需要在同一大节点审查。
- 代码改动必须带 RED/GREEN 与旧 1.4/1.5 兼容回归；新合同用显式版本，不改旧字节。

## 下一步

1. 确认试点公司（CATL）与可用搜索 route/凭据（只记录存在性）。
2. 先写 S1 合同与 S2 profile/工厂的候选，跑离线回归；不调用外网。
3. 独立审查后，再开一次真实搜索评测试点。
