# Search exposure contract v1 (S1) — 2026-10-18

## 目的

给“有界外搜”一个 owner 可批、可离线校验的暴露文档，作为 S1（owner 合同）的第一个落地件。它只声明：用哪份 search policy、最多几次查询、多少费用上限、哪些路由、凭据环境变量名、存储权利依据；不调用网络，不读取凭据值。

## 协议

`iqs.search_exposure/1.0.0`（`schemas/quick_scan/search-exposure-v1.schema.json`）

必填：consumer_id、search_policy_ref + search_policy_sha256、max_search_queries_per_session（1..20）、max_search_cost_micros、routes（enabled=true，credential_env 只写变量名）、storage_rights.confirmed=true + entitlement_ref、approved_by、approved_at。

## 校验（fail closed）

```
python scripts/search_exposure_contract.py --document <exposure.json>
```

检查项：JSON Schema；policy 文件 sha256 精确匹配；至少一个启用路由；每个启用路由的 credential_env 在环境中存在（不读取值）；路由 max_queries 之和覆盖 session 上限。输出 `iqs.search_exposure.validation/1.0.0`，失败退出码 2。

## 仍需 owner 决定

- Brave/Tavily 的实际单价与 cost_bound_verified 依据；
- 存储权利/条款引用（storage_rights.entitlement_ref）；
- 是否允许多路由 fallback。

没有这两项，search policy 只能保持 inert，exposure 文档也不能成为真实执行依据。

## 下一步接入

1. owner policy 1.6：把 search exposure 文档的哈希写进 cell 的 search_policy_sha256，替代 NO_EXTERNAL_SEARCH_POLICY 的硬编码相等；
2. shared task factory：显式 search 模式写入 limits/runtime profile；
3. runner：require_search=True + verified search receipt + v1/v2 checkpoint；
4. 先 1 公司 1 题试点，独立复核后扩大。


## 绑定到 owner policy cell（S1 第二件）

scripts/search_exposure_binding.py 校验：

- exposure 文档本身通过离线合同（policy sha256、路由、凭据存在性、存储权利）；
- owner policy 的 cell controls.search_policy_sha256 等于 exposure 文档的 canonical sha256；
- exposure 的 consumer_id 在 owner policy 的 allowed_consumer_ids 内。

输出 iqs.search_exposure.binding/1.0.0；失败退出码 2。这样在 preview/admission 之前就能发现“文档哈希没写进 cell”的问题。


## policy schema 校验（补充）

search_exposure_contract.validate 新增可选 policy_schema：policy 文件哈希匹配后再跑 QA 的 quick_scan_search_policy schema，失败记 search_policy_schema_invalid。CLI 增加 --policy-schema。DeepSeek 草案在该 schema 下通过，仍只报 storage_rights_unconfirmed。测试 7 passed。
