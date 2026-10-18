# DeepSeek Search 作为首选搜索路由 — 2026-10-18

## 官方价格（owner 提供链接）

来源：https://api-docs.deepseek.com/zh-cn/quick_start/pricing/ （抓取日期 2026-10-18）

网页搜索与抓取价格：Search 和 Fetch 是独立的 API，按请求次数计费。Search 每 1,000 次成功请求 5 元；Fetch 每 1,000 次成功请求 5 元。

即单次 Search 成功请求 = 5 CNY / 1000 = 5,000 micro-CNY。

接口（官方指南 https://api-docs.deepseek.com/zh-cn/guides/search）：

- Search：POST https://api.deepseek.com/v1/tools/search
- Fetch：POST https://api.deepseek.com/v1/tools/fetch
- Bearer 鉴权，credential env：DEEPSEEK_API_KEY

## 已准备的文件

- search-policy-deepseek-2026-10-18.json：route deepseek-primary，kind deepseek，enabled，cost_bound_verified=true，pricing per_request / CNY / unit 5000 micros。
- search-exposure-deepseek-2q-2026-10-18.json：2 次查询，上限 10,000 micro-CNY，credential_env DEEPSEEK_API_KEY。

## 离线校验结果

status: rejected
errors: ["storage_rights_unconfirmed"]
credential_presence: {"DEEPSEEK_API_KEY": true}

owner 已确认存储权利（entitlement_ref=owner-confirmed-2026-10-18）。离线校验现在 status=valid，errors=[]。

## owner 已确认

2026-10-18：存储权利 confirmed，entitlement_ref=owner-confirmed-2026-10-18；exposure 与 policy 已更新并通过校验。
