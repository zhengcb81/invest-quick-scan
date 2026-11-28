# HISTORICAL-LISTINGS-ROSTER-20261128 交付报告

- **任务**：owner handoff `investment-dashboard/handoffs/owner-requests/invest-quick-scan/HISTORICAL-LISTINGS-ROSTER-20261127.md`
- **日期**：2026-11-28
- **角色**：IQS 名单 owner（共享名单 = `runs/r25-live/owner-workspace/data/quick_scan/scan.sqlite`，universe `UNI_IQS_APPROVED_214_20261025`）
- **结论**：两个历史证券行已按原实体核对完毕，公开状态更正与在池语义收敛均已落账；原资料、历史结果与既有固定快照零改动。
- **代码零改动**：本交付为 owner 数据治理（store 落账 + 文档），无任何源码/测试变更。

## 1. 名单语义核对（fix 依据）

| 层 | 存储 | 语义 |
| --- | --- | --- |
| 在池资格（可扫描） | `quick_scan_member` | 扫描门槛要求 `membership_status='active'` **且** `scan_enabled=true`（`refresh_member_not_scan_enabled`）；listing_status **不参与**门槛——这是 688555 "证券已 delisted 仍进冻结名单" 的根因 |
| 证券公开状态 | `quick_scan_security.listing_status` | 唯一合法更正通道 `record_listing_status`（ID-06）：目标证券行更新 + `quick_scan_listing_history` 追加一行，永不重写历史 |
| 成员进出池 | `quick_scan_membership_request`（schema 7） | 成员变更必须走 request journal（`apply`，成员行+历史+收据单事务原子）；`remove` 为显式逻辑移除（UNI-08），`logically_removed` 保留行、历史与原因 |
| 维护 | MAINT-06 | 维护报告 report-only：`single_listing_delisted_findings` 只报告不摘除，摘除是 owner 决定 |

## 2. 行一：688555 泽达易盛（ENT_5634bdde-af20-42b1-a8b6-51c42d77232c）

**核对前**：证券行 `listing_status=delisted`（与公开记录一致，无需更正）；成员 `membership_status=active` + `scan_enabled=1`，version 1 → 无活跃挂牌仍在池、可扫描。

**公开记录**：上交所《关于终止泽达易盛（天津）科技股份有限公司股票上市的公告》，上证公告（股退）〔2023〕043 号，2023-05-31（[big5.sse.com.cn 公告原文](https://big5.sse.com.cn/site/cht/www.sse.com.cn/disclosure/announcement/listing/stock/c/c_20230531_89787014.shtml)）：依据证监会《行政处罚决定书》（〔2023〕29号）认定欺诈发行及其他信息披露违法，触及科创板上市规则 12.2.2 条第（一）项，实施**重大违法强制退市**，退市整理期（15 个交易日）届满后 5 个交易日内摘牌。

**处置（2026-11-28）**：
- 成员逻辑移除，request journal 收据 `REQ_9e5ad2e35e9e68a038b2ce04ec15bf9a`（idempotency_key `hist-roster-20261128-remove-688555`，payload_sha256 `e3b37edcce4a1e8842a9d75666ca5c64cc8abf6daff750d0f90fbd9c2f4ab9d9`），成员 version 1→2，`removed_at=2026-11-28T09:32:25Z`。
- **历史保留（明确）**：实体行、证券行（保持 delisted）、成员 v1/v2 历史（`quick_scan_member_history` 218→220）、全部历史扫描结果零改动；仅成员状态变为 `logically_removed`。
- **未来活动名单状态（明确）**：从活动名单排除（在池门槛失败：`membership_status != 'active'`）；再入池需凭新证据走显式 `restore` membership request。活动投影回到该池名义的 **214 家**。

## 3. 行二：002013 中航机电（ENT_8c755024-4ae0-4639-833d-1bfd7429436e）

**核对前**：证券行 `listing_status=active`（**错误**，与公开记录矛盾）；成员 active + `scan_enabled=1`。

**公开记录**：
- 深交所《关于中航工业机电系统股份有限公司股票终止上市的公告》2023-03-15（[szse.cn 公告原文](https://www.szse.cn/disclosure/notice/t20230315_599254.html)）：依据《深圳证券交易所股票上市规则（2023年修订）》第 9.7.1、9.7.9 条，中航机电股票**自 2023-03-17 起终止上市**。
- 吸收合并链：证监会《关于核准中航航空电子系统股份有限公司发行股份吸收合并中航工业机电系统股份有限公司并募集配套资金的批复》（证监许可〔2022〕3241号）——中航机电被**中航电子（600372）**换股吸收合并（换股比例 1:0.66，最后一个交易日 2023-02-07），合并完成后**中航机电法人资格注销**；合并于 2023-04 实施完毕，存续 600372 于 2023-08 更名为**中航机载系统股份有限公司**（证券简称"中航机载"，公告 2023-055）。

**处置（2026-11-28）**：
- **公开状态更正**：`record_listing_status`（ID-06）将 `SEC_7fb46dc8-e675-407b-87d3-5ac42a6aa8e1` active→delisted，`effective_at=2023-03-17`，`recorded_at=2026-11-28T09:31:34Z`；`quick_scan_listing_history` 0→1 追加行（previous=active），reason 逐字引用上述公告与批复。
- **成员逻辑移除**：journal 收据 `REQ_c2b772e216b520182ce1f39bcae8518e`（idempotency_key `hist-roster-20261128-remove-002013`，payload_sha256 `d55063f13a2541d8800a90b5997877ce7e5244e6d36c373ac8d8000583b49ddc`），version 1→2，`removed_at=2026-11-28T09:32:32Z`；理由与 MAINT-06 语义一致（无活跃挂牌不得留在可扫池）。
- **旧主体历史链（保留）**：实体行（identity_revision 仍为 1）、证券行、成员 v1/v2 历史、历史扫描结果零改动；未合并、未删除任何实体。
- **可证承继关系（记录在案）**：002013 → 被中航电子 600372 吸收（法人资格注销）→ 600372 更名中航机载。特别记录：同池成员 300114 中航电测（ENT_1b336470）是**另一家上市公司**，与本次吸收合并无关，**不是**承继方。

## 4. 验收读数（全部通过）

- 在池门槛：两实体 `scan_eligible=False`（membership=logically_removed），active listings 0/1。
- MAINT-06 维护报告：`single_listing_delisted_findings=[]`（两行均不再出现），成员计数 216（214 active + 2 logically_removed）。
- **Dashboard 同源读面（2026-11-28 复核补充，实测）**：经 owner 公开操作通道 `iqs.dashboard.owner/1.0.0` 的 `universe_list`（`run_dashboard_operation`，与 dashboard 消费路径同源）读回：688555 → `membership_status=logically_removed` v2、证券 `('688555','delisted')`；002013 → `logically_removed` v2、证券 `('002013','delisted')`（公开状态更正已在冻结名单读面生效）；member_count=216（active=214，`logically_removed` 行全量投影、携带 removal_reason，供下游按状态过滤）。原始读回全文存 `evidence/universe-list-owner-read-20261128.json`。
- 行级 diff（对照备份，逐行比对）：仅 `quick_scan_member` 2 行、`quick_scan_security` 1 行发生变化；`quick_scan_member_history` +2、`quick_scan_listing_history` 0→1、journal +2；其余表计数不变。
- 未动清单：`quick_scan_entity` 216 行逐字节不变（含两实体 identity_revision=1）、`quick_scan_route_snapshot`(27)/`route_current`(11)/`route_current_history`(30)（既有固定快照）、`quick_scan_identity_event`(0)、`quick_scan_candidate`(216)、`quick_scan_source_binding`(220)、`quick_scan_issuer_bridge`(121)、688555 证券行、300114 全部行、`identity_receipts.sqlite`、探针原文件 `dashboard-m7-gaps-20261127/coverage-gaps.json`。
- 落账前字节备份：`runs/r25-live/owner-workspace/backups/historical-roster-20261128/scan.sqlite.bak-20261128`，sha256 `7ac7b32bce1d259f748912f6b202e40d34b6005502e5b8cb284c57e332a7d2b5`（与落账前 live 一致）。

## 5. 边界与移交项

1. **identity 包未动（移交 identity owner）**：`identity_receipts` 的 rev1 暂定身份包仍按导入时（2026-10-25）快照携带 002013 `listing_status=active`——身份解析读面（`stockwiki_exact` 探针列）在此修复后仍会读到历史 active。身份包更正需 receipt 证据链 + 身份 revision 前进，属 StockWiki identity owner 流程，无现成 owner CLI；本交付严格限于名单层。
2. **dashboard 读面（已实测闭环）**：owner `universe_list` 投影不过滤状态，216 行全量投影（含两行 logically_removed 及其 removal_reason）；按 `membership_status` 过滤即得 214 家活动成员。§4 已记录修复后实测读回。冻结投影/固定快照按"保留原样"未重算。
3. 两个 request JSON 原文与收据存于 `evidence/`；成本：0 模型调用、0 付费调用、仅两次只读公开公告抓取。

## 6. 证据索引

| 文件 | 内容 |
| --- | --- |
| `evidence/membership-remove-688555.json` | REQ_9e5ad2e3 收据（journal 逐字导出） |
| `evidence/membership-remove-002013.json` | REQ_c2b772e2 收据（journal 逐字导出） |
| `evidence/listing-history-002013.json` | ID-06 挂牌状态历史行 |
| `evidence/requests-as-sent-remove-688555.json` | apply 的 stdin 请求原文 |
| `evidence/requests-as-sent-remove-002013.json` | apply 的 stdin 请求原文 |
| `evidence/acceptance-readout.json` | 门槛/维护/diff/备份 验收读数汇总 |
| `evidence/universe-list-owner-read-20261128.json` | 修复后 owner `universe_list` 读回全文（dashboard 同源） |
