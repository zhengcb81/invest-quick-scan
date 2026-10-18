# 现有公司列表导入批（写前报告，round 2）— 2026-10-18

状态：**写前报告；真实 workspace 尚未写入**。本批只做身份前置（provisional entity + 单证券 + 来源绑定 + provisional_scope 回执），给后续画像/评分铺路；不扩到 2000 家，不调用模型或搜索。

## 范围（已按 round-1 审查收敛）

- 候选表 216 行（CN-A 209、US 7），全部 `unresolved / scan_eligible=0`。
- **1 条已存在、跳过**：`CN-A:300750`（宁德时代）已有 verified 实体 `ENT_99ebb735…` 与证券，绝不重复建 provisional 身份。
- **4 条拒绝建档**（保持 unresolved，记录在 generation-summary）：
  - `CN-A:002168` 候选“中信建投” vs 目录“ST惠程”：**不同发行人**
  - `CN-A:688152` 候选“华卓精科” vs 目录“麒麟信安”：**不同发行人**
  - `CN-A:002122` 候选“天马股份” vs 目录“ST汇洲”：**未裁定的改名**，保守保留
  - `CN-A:603300` 候选“华铁应急” vs 目录“海南华铁”：**未裁定的改名**，保守保留
- **实际建档 211 条**：SSE 107、SZSE 96、BSE 1、NASDAQ 3、NYSE 4。
- 其余名称差异按“别名/改名”接受（如 万科→万科A、茅台→贵州茅台、*ST 前缀）；5 处同 ticker 改名（上峰水泥→上峰材料、中航电子→中航机载、锦江股份→锦江酒店、快克股份→快克智能、丸美股份→丸美生物）与华虹宏力↔华虹半导体走**显式改名表**，不靠模糊前缀。以目录 `canonical_name` 为准，候选名保留为 claim，不覆盖候选表。

## 来源与诚实边界

| 市场 | 来源 | 记录数 | 本批 |
|---|---|---|---|
| CN | company-wiki `security_master/cn.json`（cninfo） | 6137 | 204 建档（209 − 1 已存在 − 4 名称冲突） |
| US | `security_master/us.json`（SEC/NASDAQ） | 6959 | 7 |

- 证据是**目录级 source_url**（cninfo/SEC 发布目录），不是逐发行人页面；`issuer_receipt.evidence_ref` 如实使用该 URL，卡片不声称逐条引用。
- `incorporation_country` 使用目录字段；目录**没有** country，因此写 `null`，不再用上市市场冒充（NVO/TAL 不再被写成 US）。
- `listing_status` 由目录 `active` 字段与名称推导（含“退市”即 delisted）；`退市泽达 688555` 写 **delisted**，binding status 同步，不再宣称“全部 active”。
- provisional ≠ verified；本批不宣称评分、搜索或金融资格。

## 方法与冻结

1. 每条生成一个 payload：provisional、revision 1、`ENT_<uuid4>`、单证券 `SEC_<uuid4>`、MIC 仅 SZSE→XSHE / SSE→XSHG / BSE→XBSE / NASDAQ→XNAS / NYSE→XNYS（未知交易所直接失败，不静默 fallback）、CNY/USD、`ATT_<hash32>`、`provisional_scope`、basis `official_equity_category`。
2. **字节冻结**：`build_at/recorded_at` 固定 `2026-10-18T10:00:00Z`；id-map 记录每个 `payload_sha256`；生成器遇到已有 payload 字节不同即拒绝；每次生成后删除不在当前清单内的陈旧 payload（S2）。
3. **两阶段语义**（B6）：entity-import 先写 entity 再写 receipt；若 receipt 阶段失败，返回 `entity_saved_receipt_failed`/exit 1 且 entity 已落库。处理只有两种：用**完全相同**的 payload 重放（幂等），或按写前备份恢复；绝不跳过继续。
4. **迁移预演**（B5）：在真实 workspace 的副本上导入样本，scan.sqlite 与 identity_receipts.sqlite 的 user_version 均为当前版本（6/1，不触发迁移）；原有 3 entity / 6 security / 7 binding / 6 receipt 全部逐行保留，只各 +1；无 -wal/-shm。

## 隔离与预演证据（round-2 重跑，针对当前字节）

- 空 workspace `isolated-v2` 实际导入当前 payload 4 条：`万科A`（CN，country=null）、`NOVO NORDISK`（US，country=null）、`退市泽达`（**delisted**）、`MSFT`（US）；4/4 `entity_saved_receipt_recorded`，逐条重放 receipt 相同，库内 4 entity / 4 security。
- 真实 workspace 副本 `migration-rehearsal`：uv6/uv1 **不触发迁移**；原有 3 entity / 6 security / 7 binding / 6 receipt **逐行保留**，导入样本后只各 +1；无 -wal/-shm。
- **字节级冻结**：payload 以 `write_bytes` 写入（LF，无 CRLF）；id-map 记录文件字节 SHA-256；211/211 匹配；`CN-A_000002.json` 2379 字节。生成器遇到字节变化直接拒绝，并清理陈旧 payload。
- 证据：`generation-summary.json`、`id-map.json`、`isolated-validation.json`、`migration-rehearsal/`。

## 真实写入计划

1. 写前备份 `scan.sqlite` 与 `identity_receipts.sqlite`（字节 + 逻辑行），确认无 -wal/-shm。
2. **先导批 5 条**（每个交易所至少一条，含 1 条 delisted），逐文件回执；核对 entity/security/binding/receipt 各 +5、候选表不变、已有实体行不变。
3. 通过后按 **≤60 条/批**（不按交易所整批，SSE 107 会拆两批）导入剩余 206 条；runner 在每个文件前重新校验：payload 字节 SHA 与 id-map 一致、`(market,ticker)` 在库中不存在，否则立即中止。
4. 每批后强制校验 `after == before + 批大小`；全量后校验 entity 3→214、security 6→217、binding 7→218、receipt 6→217、candidate 216 不变、`quick_scan_member` 不变；任一不符即中止。再抽样重放，重放前后计数必须完全相同。

## 明确不做 / 后续步骤

- 不建 universe、不扩员、不评分、不搜索、不调模型。
- **候选↔实体链接不在本批**（S1）：候选表保持 unresolved，`candidate.entity_id` 仍为空；后续需单独评审链接步骤（用原冻结报告重算或显式 link），并把 300750 对到既有 `ENT_99ebb735…`，不得新建。
- 回滚：恢复两份写前备份；保留所有日志与回执。

## 审查状态

round-1：changes_requested（B1–B6 + S1/S2）→ 已处置。
round-2：changes_requested（C1 隔离验证过期、C2 字节冻结非字节级、C3 runner 未强制不变量；改名/分批两条非阻塞）→ 已处置：隔离验证按当前字节重跑 4 条；payload 改为字节写入并记录文件 SHA；runner 增加 sha/重复/批增量/总量/重放五道强制；002122/603300 标为“未裁定改名”，5 处改名走显式表；分批固定 ≤60。
等待 round-3 复审通过后再写真实 workspace。