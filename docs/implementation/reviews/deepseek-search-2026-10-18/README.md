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

除存储权利未确认外，其余检查全部通过（policy sha256 精确匹配、route enabled、凭据变量存在、查询预算覆盖）。

## 需要 owner 的一句话

确认 DeepSeek API 的搜索结果/网页内容是否允许按本项目方式存储与引用（存储权利 / 条款引用）；确认后把 exposure 与 policy 的 storage_rights.confirmed 改为 true、填入 entitlement_ref，即可通过离线校验，进入 owner policy 1.6 绑定。
