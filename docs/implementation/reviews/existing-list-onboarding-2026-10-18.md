# 现有公司列表导入批（写前报告）— 2026-10-18

状态：**写前报告，未写入真实 workspace**。目标是把已确认的 216 家候选从“未解决”推进到“有 provisional 身份与证券”，为后续画像/评分铺路；不扩到 2000 家，不调用模型或搜索。

## 范围

- 仅现有候选表：`quick_scan_candidate` 216 行（CN-A 209、US 7），全部当前 `unresolved / scan_eligible=0`，原因均为 `listing_not_in_authoritative_store`。
- 不新增候选、不改 name claims、不删除任何候选、不做 universe 扩员以外的名单写。
- 本批只做身份前置（provisional entity + 单证券 + 来源绑定 + provisional_scope 回执）；不做评分、不做搜索、不产生费用。

## 来源与覆盖

| 市场 | 来源文件 | 记录数 | 本批匹配 |
|---|---|---|---|
| CN | company-wiki `.source_catalog/security_master/cn.json`（cninfo） | 6137 | 209/209 |
| US | `us.json`（SEC/NASDAQ） | 6959 | 7/7 |

- 216/216 全部命中，无缺失、无多义；交易所分布：SSE 109、SZSE 99、BSE 1、NASDAQ 3、NYSE 4。
- 25 家候选名与目录名不同（如“万科”→“万科A”）：以目录 `canonical_name` 为准，候选名作为 claim 保留，不覆盖、不改写候选表。
- 证据：每条记录的 `source_url`（cninfo/SEC 官方 https 地址）写入 `issuer_receipt.evidence_ref`，basis=`official_equity_category`；无 https 证据的记录才退回 `user_exact_security_attestation` 并写 actor。

## 方法

1. 每个 listing_key 生成一个 payload：`entity`（provisional、revision 1、`ENT_<uuid4>`、单证券 `SEC_<uuid4>`、market CN/US、exchange MIC：XSHE/XSHG/XBSE/XNAS/XNYS、currency CNY/USD、security_type ordinary、listing_status active）、`source_bindings`（company-wiki namespace + source_record_id）、`issuer_receipt`（`ATT_<hash32>`、kind=provisional_scope、scope=listed_operating_company、negative_scope_flag=false）。
2. ID 映射一次生成并冻结在 `runs/existing-list-onboarding-2026-10-18/id-map.json`，重跑 payload 不产生新实体。
3. 真实导入按交易所分批（每批 ≤60），逐文件 `entity-import`，任何非零退出立即停批并保留现场；不重试未知状态、不覆盖已有实体。
4. 导入后只读复验：entity/security/source_binding/receipt 行数各 +N，候选表不改；再对每批做一次完全相同 payload 的幂等重放，receipt_id 必须一致且零新增。

## 隔离验证（已完成）

在空 workspace `runs/existing-list-onboarding-2026-10-18/temp-workspace` 上实际导入 4 条样本（SZSE/SSE/BSE/NASDAQ 各一）：4/4 `entity_saved_receipt_recorded`，各自重放 receipt_id 相同；库内 entity=4、security=4、receipt=4，无重复。证据：`isolated-validation.json`、`generation-summary.json`。

## 允许改动

- 真实 workspace：`scan.sqlite`（entity/security/binding）、`identity_receipts.sqlite`（provisional receipts）新增 216 条；不改候选表、不改已有 3 个实体、不改政策/路由/观察。
- 自有 staging：`runs/existing-list-onboarding-2026-10-18/`（payloads、id-map、隔离验证、导入回执）。
- 本卡与 PWF。

## 必须拒绝

- 用 provisional 身份冒充 verified、用候选名覆盖目录名、补造 IVR 回执。
- 写真实 workspace 前未完成独立审查；导入失败后跳过错误继续。
- 把本批当作“可评分/可搜索”资格；评分仍要求 verified 身份与正式 search-backed 路径，另行评审。
- 调用模型/搜索/下载公司文档。

## 闸门与交接

1. 本卡由真正不同 agent 审查（范围/来源/ID 稳定/provisional 诚实性/幂等/回滚），open_findings=[] 后才写真实 workspace。
2. 写入后提交导入回执、行数复验、幂等重放证据与 PWF 更新。
3. 回滚：真实 workspace 的扫描/回执库在写前做字节备份；失败时按备份恢复并保留日志，不删其他实体。
