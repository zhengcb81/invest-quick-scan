# 搜索供应商选项（供 owner 决策）— 2026-10-18

目的：为 search-backed 评分选择可准入的搜索 route。以下价格为公开页面摘录（外部数据，非本项目承诺），实际以供应商账单为准。

## 候选

| 供应商 | 免费额度 | 付费价格 | StockWiki 策略支持 | 备注 |
|---|---|---|---|---|
| Brave Search API | 免费 credits（"up to thousands of free queries per month"，取决于计划） | $5 / 1,000 requests（最高 50 qps） | kind: brave（schema 1.0） | 最适合现有策略；需 BRAVE_API_KEY |
| Tavily | Researcher：1,000 credits/月，免费 | Project 4,000 credits/月约 $3（页面表格） | kind: tavily | 免费额度够试点；需 TAVILY_API_KEY |
| Serper.dev | 2,500 credits 免费试用（无需信用卡） | $1.00 到 $0.30 / 1,000 查询（预付包） | 现有策略无 serper kind | 需新增 adapter，暂不推荐 |
| DeepSeek search/fetch | 未确认 | 报道约 ¥5 / 1,000 requests | 新版策略 schema 1.2/1.3 有 deepseek_search/fetch 端点 | 需确认账号与价格；报道 +5 QPS |

来源：
- Brave: https://brave.com/search/api/
- Tavily: https://docs.tavily.com/documentation/api-credits
- Serper: https://serper.dev （价格摘录 via https://raw.githubusercontent.com/api-evangelist/serper/refs/heads/main/plans/serper-plans-pricing.yml）
- DeepSeek: https://pandaily.com/deepseek-api-search-fetch-endpoints-5-yuan-per-1000-requests-5-qps-agents-rag

## 准入一个 route 需要什么

StockWiki 的 search policy 要求每条 route：
1. enabled=true；
2. credential_env（凭证只放环境变量，不进仓库）；
3. cost_bound_verified=true + pricing（basis/currency/unit_cost_micros，或 per_request_cap）；
4. storage_rights.confirmed=true + entitlement_ref（我们能否保存 snippet/URL 及其期限）；
5. owner 在 exposure 合同里给出查询上限与预算。

## 建议

- 试点：Tavily 免费额度（1,000 credits/月）或 Brave $5/1k；先 1 家公司 1 题、单次搜索。
- 需要你提供：选哪家、API key 的环境变量名、是否确认可存储 snippet/URL（storage rights）、以及一次试点的查询/费用上限。
- 没有这些，search-backed 评分无法真实执行；但代码侧的 S1–S5 方案已经就绪。

## 边界

- 以上价格为公开页面信息，可能变化；本项目没有采购或调用任何搜索 API。
