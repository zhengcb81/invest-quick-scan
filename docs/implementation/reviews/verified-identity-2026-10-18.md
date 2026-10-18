# 已验证身份（verified issuer）批 — 写前报告（round 2）— 2026-10-18

状态：**审查未通过；真实 workspace 不写**。本轮确认：当前证据与数据不足以诚实完成 verified 升级，需先决定“法人全称 + 逐发行人官方证据”的来源。

## 审查结论（round 1）

- **证据不足（blocker）**：公司目录 URL（cninfo `szse_stock.json`）只能证明“000002 在官方清单中叫万科A”，不能证明法人主体、不能把证券与法人绑定，也没有 ISIN/统一社会信用代码。B01b 先例对这一步用的是 SEC 10-K + owner 批准。
- 最低要求：一家公司一份**逐发行人官方文件**（年报/招股书/cninfo 或交易所发行人页）作为 `evidence_ref`，其中同时出现证券代码与**公司全称**；目录 URL 只作次级溯源；另需 owner_approval id。
- 因为 IVR 的 `canonical_name` 来自实体，verified 实体在 rev2 必须写**法人全称**（source_binding 保留万科A 作为交易简称），否则“verified issuer”用的是交易简称。
- 当前既有数据（company-wiki 安全主数据、companies.yaml）**没有法人全称**；逐发行人证据也未采集。因此 211 家的批量升级目前无法诚实执行。

## 已确认正确的部分

- `save_entity` 强制 revision +1，拒绝同 revision 不同内容；完全相同重放是 no-op；回执返回同一 id。
- 半写风险真实但可检测：实体先落 verified，回执失败时 G2b 导出会报 `receipt_missing/receipt_not_active`，无法产出 snapshot/checkpoint；仍要求写后检查 IVR 存在且 entity_id/revision 匹配，失败即停、重试或恢复。

## 批量语义（已修正，脚本已实现）

- 升级**修改既有行**：entity / security / binding 计数**不变**；receipt 每条 +1；verified 计数 +1。
- 每文件写后断言 `identity_state=verified、identity_revision=2、verified_issuer_receipt_id=IVR_`。
- 计数：当前 212 provisional；试点 1 家后剩 **211**（报告此前的 210 是错的）；再按 ≤60/批升级 211。
- 回滚：恢复两份 SQLite 字节；中途失败留下“部分已升级、可重跑”的混合状态，逐文件幂等。
- `verified-batch.py` 已在 workspace 副本整跑 211：entity/security/binding 不变，verified 2→213，receipt 217→428，每批与逐文件校验通过。

## 历史与边界（精确表述）

- rev1 的事实只保留在 `provisional_scope` 回执里；实体行在 rev2 被覆盖；**当前没有追加 identity_event**。报告不再写“完全不覆盖历史”。
- verified 身份只解除 checkpoint 的 identity 前置；**评分仍需要 search-backed checkpoint 与金融复核**，verified 本身不授予评分、准确性或投资结论。

## 下一步（需决策）

1. **证据与法人名来源**：允许从官方逐发行人页面（cninfo/SZSE 公司页、年报）采集法人全称与 URL（只存 URL/名称，不存正文），还是由用户提供法人主体清单/许可数据源？
2. 拿到来源后：先 1 家（万科A）试点 → 独立复审 → 5 家 → 211 家分批。
3. 在来源确定前，不写 verified、不批量、不把 provisional 说成可评分。

## 隔离预演（保留）

- 在副本上曾用目录 URL 完成一次 rev2 升级（IVR_33408e42…、重放幂等），仅证明**机制**可行；该证据不满足上述政策要求，不作为真实写入依据。
