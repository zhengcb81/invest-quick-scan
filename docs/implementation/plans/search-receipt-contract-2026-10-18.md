# Search receipt contract v1 (S3 起点) — 2026-10-18

## 目的

把一次真实搜索的“查询 → 原始响应 → 结构化结果 → 费用”固化成可校验回执，绑定到 owner 的 search exposure。回执只证明“发生过什么”，不等于答案被接受。

## 协议

iqs.search_receipt/1.0.0（schemas/quick_scan/search-receipt-v1.schema.json）

必填：protocol、exposure_sha256、policy_sha256、provider、route_id、query、requested_at、completed_at、status（ok/empty/unavailable）、results、result_count、cost_micros、currency、response_sha256。

DeepSeek Search 响应映射：results[].title/url/snippet/summary/content/rerank_score；rerank_score 0..3。

## 构建与校验

scripts/search_receipt.py：

- from_response(raw, exposure=..., policy_sha256=..., provider=..., route_id=..., query=..., requested_at=..., completed_at=..., cost_micros=...)
  - 严格 JSON；results 必须为数组；
  - 生成 response_sha256（原始字节）与 exposure_sha256（canonical）；
  - 校验费用不超过 exposure 上限、币种一致、route 在 exposure 内。
- validate(receipt, exposure=...)：schema + 绑定检查。

状态规则：ok 至少 1 条结果；empty 为 0 条；unavailable 必须带 error_reason 且 cost=0。

## 测试

tests/test_search_receipt.py：5 passed（DeepSeek 响应、空结果、超费用、route 不在 exposure、result_count 不一致）。

## 下一步（S3）

1. runner 用 require_search=True 调用 DeepSeek /v1/tools/search，生成 receipt 并随答案写入 checkpoint；
2. checkpoint/seal 校验 receipt 存在且 exposure/费用匹配；
3. 搜索不可用 → status=unavailable，不伪造来源；
4. 仍需 owner 确认 storage_rights。
