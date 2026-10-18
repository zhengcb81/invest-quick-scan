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


## DeepSeek Search 客户端（离线可测）

scripts/deepseek_search_client.py：

- 请求：POST https://api.deepseek.com/v1/tools/search，Bearer DEEPSEEK_API_KEY；
- 载荷：query、count（1..50，默认 5）、need_content（默认 True）、可选 ori_question（<=128）；
- 200 -> search_receipt.from_response，费用 5000 micros（5 CNY/1000 次成功请求）；
- 非 200 / 网络错误 -> status=unavailable、cost=0、error_reason=http_<code>；
- 不重试、不回退其他 provider、不记录 key。

测试：tests/test_deepseek_search_client.py 5 个（载荷、ok、empty、503、缺 key、count 边界），与 receipt 测试合计 10 passed。


## checkpoint 绑定（S3/S4 glue）

scripts/search_checkpoint_binding.py：

- 从 task 的 execution_profile.search_exposure 取 exposure；
- 校验每条 receipt 的 exposure/费用/币种/route；
- receipt 数 <= max_search_queries_per_session，总费用 <= max_search_cost_micros；
- 生成 receipts_sha256 = canonical([canonical(receipt)...])；
- 若 checkpoint 带 search_receipts_sha256，必须精确相等。

输出 iqs.search_checkpoint_binding/1.0.0；失败退出码 2。5 个单测通过。该模块只做绑定校验，不授权发送。


## 独立审查整改（2026-10-18）

- 空/全 unavailable 回执：checkpoint binding 现在要求非空且至少 1 条 status=ok。
- 0 费：ok/empty 回执要求 cost_micros>0；client 禁止 0 费。
- policy 绑定：receipt.policy_sha256 必须等于 exposure.search_policy_sha256。
- checkpoint：非 None 时必须含 64hex search_receipts_sha256。
- 重复回执：拒绝（duplicate_receipts）。
- client：endpoint 只允许官方地址；need_content 必须 bool；非 200 回执也走 validate。
- receipt CLI：--exposure 必填；raw 仅接受 bytes/str；rerank_score 必须数值；completed_at >= requested_at。
- exposure 合同：route_id 唯一；currency 必须匹配 policy pricing.currency；approved_at 必须是真实日期且不在未来。
- binding：owner policy 必须存在 enabled + cost_bound_verified + storage_rights.confirmed 的路由，且 exposure route 必须在 policy 内。
- schema provider enum 增加 zai。
- 仍未做：schema 层 result_count==len(results) 绑定（运行时 validate 已强制，文档要求必须调用 validate）。

测试：search 链路 44 passed。
