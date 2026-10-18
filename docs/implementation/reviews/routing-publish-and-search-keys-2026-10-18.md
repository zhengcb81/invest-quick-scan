# routing 包已发布 + 搜索 key 实测 — 2026-10-18

## 1) routing 包（选项 A）

- 真实仓执行 `python scripts/question_sets.py publish-routing --activate`：
  - package `pkg_b5a41d8c9f89adba8d57cce1792b1cac8db5378509996f6614472a691cfb5fba`
  - release `modrel_fc5de4a3dcce55866c8a2a83d82cdaa8caf8a3c59b6406d3a0ea75e7c9e01e74`
  - 48 模块 / 222 题；`questions/releases/current.json` 已切换。
- 发布后对比历史包：**modules 完全相同、contexts 完全相同**；仅 release 元数据变化（schema 1.0→2.0、router 1.0→2.3、routing_policy_sha256=05f2cf6c…）。
- 当前路由策略版本 2.3.0；新公司 route 最小覆盖 **24 题**（common + critical risk）。

## 2) 搜索 key 实测（User 环境变量，未写入仓库）

从 `[Environment]::GetEnvironmentVariables('User')` 读取并只在子进程注入：

| 供应商 | 实测 | 结果 |
|---|---|---|
| Tavily | POST /search | HTTP 200，3 条结果 |
| Brave | GET /res/v1/web/search | HTTP 200，3 条结果 |
| Z.AI（GLM） | POST /api/paas/v4/web_search | HTTP 429：余额/资源包不足 |
| DeepSeek | POST /v1/tools/search | HTTP 200，返回 35KB 搜索结果 |
| MiniMax | POST /v1/search | HTTP 404（端点不对，未继续） |

结论：Tavily、Brave、DeepSeek 的 key 可用；Z.AI 需要充值；MiniMax 端点待查。

## 3) 可执行 search policy（Tavily 试点）

- 文件：`runs/existing-list-onboarding-2026-10-18/search-policy-tavily-pilot.json`（不含密钥）
- 字段：kind=tavily、credential_env=TAVILY_API_KEY、enabled、cost_bound_verified、pricing 8000 micros/request、storage_rights.confirmed + entitlement_ref `owner-2026-10-18-search-pilot`
- 导入结果：route `tavily-primary` **已准入**；policy_receipt 显示 `admitted_routes=["tavily-primary"]`。
  - receipt 里 `external_dispatch_enabled=false` 是 `policy_receipt()` 的默认参数，实际 runner 以 require_search 打开时才会置 true；policy 本身已通过准入。

## 4) 下一步（未做）

- 把 search 接入正式 run：S1 owner 合同（search exposure）→ S2 共享工厂/profile 允许非零查询 → S3 runner 搜索回执 → S4 v1/v2 checkpoint → S5 金融复核。
- 或者先走 owner 准入：routing 包已发布，000026 可生成 route（最小 24 题）→ universe/policy/preview/confirm/admit → 24 题 run。

## 边界

- 本轮没有调用模型、没有执行付费搜索（只有一次各供应商的探测请求，约 5 次 API 调用）。
- 发布的 routing 包不改题目；旧 release 仍可按 id 读取。
- 搜索 key 未落盘、未进 git。
