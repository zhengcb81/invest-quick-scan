# B01-b 前置导入批独立审查报告（数据批：宁德时代 300750 + 中信建投 H 06066 provisional 导入 + W04 双快照）

日期：2026-10-07。审查者：独立审查者（与执行者无关，全部结论基于本审独立 SQL / CLI 复算，不采信执行者描述）。
写前报告卡：`docs/implementation/reviews/IQS-lane/B01b-import-card-2026-10-07.md`；执行证据档：`docs/implementation/reviews/IQS-lane/B01b-prereq-import-evidence-2026-10-07.md`。
样本来源：`task_plan.md` Phase 84（owner round-81 两项结构化决定）；先例：`reviews/IQS-lane/G2b-alphabet-sample-2026-10-04.md`；契约：StockWiki `stockwiki/identity_import.py`（L149-169 provisional 分支）。

**裁决：needs_revision**（3 项 P1 需返工，0 项 P0）。详见 §7/§8。

---

## 1. 范围

### 1.1 本审的读写边界
- 只读：StockWiki / StockQAbyLLM / invest-quick-scan 三仓全部文件与两套 owner 库。
- 本审**唯一写入的仓内文件 = 本报告**（`docs/implementation/reviews/B01/prereq-import-review-2026-10-07.md`）。
- 本审被授权的写操作 = 幂等 CLI 重导。实际执行的全部副作用（均可复算）：
  1. `identity-export-g2b` ×2（只读导出，stdout 捕获到 `%TEMP%\b01b_review\reexport_*.json`）；
  2. `entity-import` 重放 ×4（catl/cncb 各 2 次）；
  3. 冲突测试 `entity-import` ×1（把 300750 的两处 market 改回 `CN-A` 后重导，预期被拒）；
  4. 隔离 temp root（`%TEMP%\b01b_review\temproot`）内的 registry/entity 导入与导出复现，结束已 `rmtree` 删除；
  5. 临时脚本与中间件均在 `%TEMP%\b01b_review\`，未落三仓。
- 全程零网络、零 LLM 调用、未读取任何真实配置/密钥。

### 1.2 三仓改动面复核（git）
| 仓 | 断言 | 本审复核 |
|---|---|---|
| IQS `21b645d` | 证据+卡+PWF | `git show --stat 21b645d` = 4 文件：`B01b-import-card-2026-10-07.md`(33)、`B01b-prereq-import-evidence-2026-10-07.md`(41)、`progress.md`(2)、`task_plan.md`(3±1) ✓；提交时刻 2026-10-06 20:56:53 +0100 |
| StockQA `f062903` | 仅 pilot_runs 产物 | 6 文件全在 `pilot_runs/b01_prereq_2026-10-07/`，无任何代码 ✓；提交时刻 21:01:26 +0100。**但** 4 个 JSON（两 payload、两 snapshot）被 `.gitignore:89 *.json` 忽略，未入库 → 见 P2-2 |
| StockWiki | 零代码改动 | `git status --porcelain` 空；HEAD `3fe5008`（2026-10-06 05:58，早于本批 19:52Z）→ 批内零提交 ✓ |
| 叙事三提交 | `3c20d4d..ae0b3e3` 未动 | 该区间在 **StockWiki**（本审定位）：`aa3c6e6`(10-03 10:59) / `3c20d4d`(10-03 11:05) / `4c3334e`(10-03 11:35) / `ae0b3e3`(10-03 12:15 merge)，全部 2026-10-03，区间外无本批提交 ✓ |
| B2a 资产 | 未触碰 | `pilot_runs/b2a_2026-10-03/` 全部 mtime ≤ 2026-10-04 08:53（`candidates.json` 本审算得 sha256 `0ab0e31145c8a1c745dc318c4a37d168b964575fd793cc329ea99421bd43a0fb`，13,683B，216 条）✓；`g2b_alphabet_2026-10-04/` mtime 全 2026-10-04 ✓ |

时间轴（本地 +0100；括号内为库内/回执的 UTC 事实）：`f62a98c` 样本冻结 20:48:14 → `8b4db6d` 侦察 20:50:48 → **卡落盘 20:52:06** → **首次导入 20:52:19（`imported_at=2026-10-06T19:52:19Z`，`identity_receipts.sqlite` mtime 同刻）** → e1/e2 20:53:31/20:53:48 + `market-registry-import` 20:53:48（`fetched_at=19:53:48Z`）→ `catl_payload.json` 末次写 20:54:34 → **`scan.sqlite` 末次写 20:55:31（纠正落库时刻）** → catl 快照 20:55:47 / cncb 快照 20:56:08 → 证据档 20:56:52 与提交 20:56:53 → 6 个 txt 落盘 21:01:14 与 `f062903` 21:01:26 → `ed35285` 21:04:46 / `d158a43` 21:12:47。

> 卡在磁盘上早于首次写 13 秒（写前报告成立），但卡与证据同在 20:56:53（写之后）才入版本控制 → LOW-4。

---

## 2. 库内复验（独立 SQL，`mode=ro` URI，两库）

### 2.1 行数与实体
| 对象 | 实测 | 断言 | 结果 |
|---|---|---|---|
| `quick_scan_entity` | **3** | 2×provisional rev1 + Alphabet verified rev1 | ✓ |
| `quick_scan_security` | **6** | 300750 CN/XSHE、06066 HK/XHKG、Alphabet 4×US | ✓ |
| `quick_scan_source_binding` | **6** | 同上一一对应 | ✓ |
| `quick_scan_segment` | 0 | 批内无分部 | ✓ |
| `identity_receipt` | **3** | 2×`provisional_scope` + 1×`verified_issuer` | ✓ |
| `identity_receipt_event` | 0 | 无生命周期事件 = active（与 G2b 先例一致） | ✓ |
| `quick_scan_candidate` / `quick_scan_issuer_bridge` | 216 / 121 | 既有基线（209 CN-A + 7 US / owner 签收 plan-A 表）未变 | ✓ |
| `market_registry_record` | 7 | fixture 记录数；市场集合 `{CN,GB,HK,US}` | ✓ |

实体明细（实测）：
- `ENT_99ebb735-…614f` 宁德时代新能源科技股份有限公司 / provisional / rev1 / `scope_attestation_id=ATT_bd730f17219941a0a422b1e322dbae70` / `verified_issuer_receipt_id=NULL` / `incorporation_country=CN`
- `ENT_1af6804e-…2c85` 中信建投证券股份有限公司 / provisional / rev1 / `ATT_a6be5f730d3247889affb583a09fee86` / NULL / CN
- `ENT_97bf6a65-…6e1e` Alphabet Inc. / **verified** / rev1 / `IVR_663efa0137144ccba0e6c88781da6752` / US —— 与 G2b 先例文档逐字段相符（4 证券 GOOG/GOOGL=ordinary、GOOGM/GOOGN=preferred、market=US、exchange_raw=NASDAQ、exchange=XNAS、currency=USD、`adr_ratio=NULL`；4 绑定 `company-wiki:security_master/us.json` / `0001652044:<ticker>`；回执 `evidence_ref`=SEC 10-K、`decision_ref=owner-2026-10-03-alphabet-sec-10k`、`recorded_at=2026-10-04T09:07:55Z`、coverage 4/4、`same_legal_issuer=true`）。**Alphabet 未被触碰** ✓（另：`identity_receipts.sqlite` mtime = 20:52:19 = 本批两行 INSERT 之后无任何写）。

两样本证券/绑定与 payload **逐字段比对：0 处差异**（`quick_scan_security` 12 列、`quick_scan_source_binding` 10 列全部相等）；全库 `security.market ≠ binding.market` 行数 = **0**；`security.market` 取值域 `{CN:1, HK:1, US:4}`、`binding.market` 同 → 与 `market_registry` 投影键（CN/GB/HK/US，ISO 10383 市场码）自洽。

### 2.2 回执逐项对 `identity_import.py` L149-169
| 契约行 | 要求 | 宁德时代 | 中信建投 H |
|---|---|---|---|
| L108-113/L150 | `kind=provisional_scope` 与 `identity_state=provisional` 配对 | ✓ | ✓ |
| L150-151 | `scope=listed_operating_company` | ✓ | ✓ |
| L152-153 | `negative_scope_flag is False` | ✓ | ✓ |
| L157-160 | `basis=user_exact_security_attestation` + 非空 `actor_id` | ✓ `owner-2026-10-06-b01-sample-freeze` | 同 ✓ |
| L154-156 | 非 official basis ⇒ **不要求** HTTPS `evidence_ref` | `evidence_ref=NULL`（如实，未伪造权威源） | 同 ✓ |
| L163-164 | 恰 1 证券 | 1 ✓ | 1 ✓ |
| L165-169 | `entity.scope_attestation_id == receipt.receipt_id` | ✓ | ✓ |
| L118-127 | `entity_id` / `identity_revision`(=1) 匹配；`recorded_at` 为 UTC ISO | ✓ `2026-10-07T00:00:00Z` | ✓ |
| L114-117 | `ATT_[A-Za-z0-9_]+` | ✓ | ✓ |

**provisional 不声称 verified**：两实体 `identity_state=provisional`、`verified_issuer_receipt_id=NULL`、回执 kind 非 `verified_issuer`、无 IVR、无 `evidence_ref`；快照 payload `identity_state=provisional/rev1`；证据档与卡均明示"不声称 verified" ✓。provenance 块（`purpose/entity_source/owner_approval/exchange_mic_source/build_at`）四键齐备，`exchange_mic_source=tests/fixtures/market_registry/iso10383_sample.csv` 实存（1,484B，7 记录，sha256 `a4f5d6aa9941d91a7867e74cd98f9e83f47f7f12762c95bea3bcaf4dab4fadc4` = 库内 `market_registry_meta.sha256` 全等）✓。

---

## 3. 快照字节（含重导 sha 比对）

| 文件 | 字节 | sha256 | UTF-8 | BOM | 解析 |
|---|---|---|---|---|---|
| `catl_snapshot.json` | 2979 | `4ce7ba5a808684297a317cdffbae0078ad90960780f7aec41df33e7010db9c07` | ✓ | 无 | ✓ |
| `cncb_h_snapshot.json` | 2938 | `2853cc982a91c9587b9daf213140771c9ab1ea157fc87dfdb82ec0bf3bcb4f0f` | ✓ | 无 | ✓ |

- 前 16 位与证据档 `4ce7ba5a80868429` / `2853cc982a91c958` 全等 ✓（两文件均含 CRLF，来自 CLI 文本 stdout 翻译，两份一致 → LOW-2）。
- **重导字节等同（本审实测）**：`python -m stockwiki.cli --root <StockWiki> identity-export-g2b --entity-id <eid> --as-of 2026-10-07T00:00:00Z`（stdout 原始字节捕获）→ catl 2979B `4ce7ba5a…9c07`、cncb 2938B `2853cc98…4f0f`，与在档文件**逐字节 `a == b` 为 True**，exit 0、stderr 空 ✓。
- 内容核验：`schema_version=2.2.0` / `object_type=entity`；payload `identity_state=provisional`、`identity_revision=1`；listings = `(CN,300750,XSHE)` / `(HK,06066,XHKG)`（`exchange_raw` SZSE / SEHK，currency CNY / HKD，`listing_status=active`，`security_type=ordinary`）；`trusted_context` 三键齐 = `market_registry` / `identity_receipts` / `source_bindings`（市场投影 `CN:[XSHE,XSHG], GB:[TSCD], HK:[XHKG], US:[ESPD,XNAS,XNYS]`，与 fixture 全等）✓。
- payload 文件字节：`catl_payload.json` 2240B sha `a772ebe4…38cb`、`cncb_h_payload.json` 2214B sha `923d33e9…c72d`（证据档未记 payload sha → 本审补记）。

### 3.1 下游可消费性（本审追加，非卡内必检项）
- **StockQA Q06 生产消费路径（`src/runners/llm_runner.load_identity_snapshot`）：两份均 OK**，返回 `identity_state=provisional`、`identity_revision=1`、单 `source_binding_ref`、`identity_snapshot_sha256` 与上表全等 ✓。
- **IQS 公共契约 CLI（`scripts/identity_contract_cli.py --schema-version 2.2.0`）：两份均 `exit 2`**：
  1. schema 层 `request_schema_invalid`：`source_bindings[*].binding_ref` / `listings[0].source_binding_ref` 需 `^BND_[A-Za-z0-9_]+$`，实际为 `BIND_<uuid4>`（前缀 `BIND_` 与连字符双重不符）；对照 golden `BND_fixture_acme_1` 通过。
  2. 仅把 binding_ref 规范化为 `BND_<hex去连字符>` 后：schema 通过，语义层两份都以 `identity receipt does not bind this active revision` 失败 —— 真因 `contract_validation._identity_receipt` L155 要求 `receipt.status=="active"`，而 StockWiki 真实导出回执只有 `effective_status`（golden 带 `status`，StockWiki 测试 fixture 也自带 `status:"active"`）。
  3. CATL 另有本批纠正造成的独立语义失败（见 §5）：`receipt.listing_id=LST_33c3643a-…` ∉ payload `listings=[LST_0e457e3e-…]`；`receipt.source_listing.market="CN-A"` ≠ 重算值 `"CN"`（两处 `False`，本审直接比对）。
  → 归因：1/2 为**跨仓既有缺口**（Alphabet 同路径同样中招，本批未引入），3 为**本批引入**。见 P2-5、P1-2。

---

## 4. 幂等复验（本审实跑）

方法：导入前对两库全部相关表做规范化 JSON 全量快照并求 sha（下称"状态哈希"=`e4ec6d0b9f6757bd60c23dfd10fbcc29cf50ec8e7cb035c0c4f52b95b278e63b`），每次 CLI 写后重算比对。

| 步骤 | 命令 | exit | 回执 | 行数 | 状态哈希 |
|---|---|---|---|---|---|
| 重放 1 | `entity-import --file catl_payload.json` | **1** | `receipt_id=ATT_bd730f…`、`phase_status=entity_saved_receipt_failed`、`error_code=receipt_duplicate`、`receipt_recorded=false` | 3/6/6/3 不变 | 不变 |
| 重放 1 | `entity-import --file cncb_h_payload.json` | **0** | `receipt_id=ATT_a6be5f…` 不变、`phase_status=entity_saved_receipt_recorded` | 不变 | 不变 |
| 冲突测试 | catl payload（两处 market 改回 `CN-A`） | **2** | stderr `{"detail":"source binding conflict for BIND_ae8146ad-…","error_code":"import_rejected"}` | 不变 | 不变 |
| 重放 2（复跑确认） | 两 payload 再各一次 | catl **1** / cncb **0** | 同上 | 不变 | **与批前完全相同** |

结论：
- **行数零新增 ✓、receipt_id 不变 ✓**（entity 3 / security 6 / binding 6 / receipt 3，四轮写后均不变；终态状态哈希 == 批前）。
- **cncb 幂等干净（exit 0）✓；catl 幂等重放在当前状态下不干净（exit 1，`receipt_duplicate`）** → 证据档 §2.3 的"同 payload 各再跑一次 ✓"是在 §3 纠正**之前**执行的，纠正后未复验即作为交付结论 → **P1-1**。
- 机制本审读码核实：`identity_receipts.record_receipt` L215-218 = 同 `receipt_id` 且 canonical bytes 相等→幂等返回；bytes 不等→`receipt_duplicate`。CATL 的派生回执含 `source_listing`（由 store 现值派生），纠正后由 `CN-A→CN` 使 bytes 变化，故拒绝；实体阶段因 fingerprint 相等走 `con.commit(); return`（`quick_scan_store.py` L283-295），不写库 → 无状态漂移（实测哈希不变）。

---

## 5. §3 批内纠正裁定（重点）

### 5.1 事实重建（本审独立）
1. **初始错误真实存在**：库内 `quick_scan_candidate.market` 惯例为段标签（`CN-A` 209 行 / `US` 7 行），侦察 round-82 因此断言"市场标签 CN-A/HK 与库惯例一致"（task_plan Phase 84 ③）；但 `quick_scan_security/quick_scan_source_binding.market` 的库惯例是 **ISO 市场码**（Alphabet=US、H 样本=HK），且 `identity-g2b` 导出用 `market_registry` 投影（键集 CN/GB/HK/US）校验 `listing.market`。
2. **拒绝机制属实（本审在隔离 temp root 复现）**：`market-registry-import iso10383_sample.csv`（exit 0，projection sha `94668570…e8e3` 与生产库全等）→ `entity-import`（`market=CN-A`，exit 0，导入器不查市场注册表）→ `identity-export-g2b` → **exit 2，stderr `{"error_code": "market_not_registered", "detail": "CN-A"}`**，与证据 §3.1 逐字一致（机制见 `stockwiki/identity_g2b.py` L100-108）。临时根已删除。
3. **"无修正类 CLI"属实**：`quick_scan` 子命令全集 = `universe-add/remove/restore/pin/unpin/list/diff/explain`、`entity-add-security`、`candidate-import`、`entity-import`、`issuer-bridge-import/report`、`analysis-subject-import`、`observation-import`、`maintenance-nominate/apply-auto/report`、`quick-scan-refresh-request/status` —— 无任何修改既有 security/binding 字段的入口；`entity-add-security` 只追加挂牌，`entity-import` 对同 binding 异数据被 L255-272 冲突检查前置拦截。
4. **"fail-closed 幂等拒绝重导"属实（本审复跑实证）**：§4 冲突测试 exit 2、`source binding conflict`、事务 `BEGIN IMMEDIATE`→异常 `rollback`，四轮前后状态哈希全等，**零改动** ✓。

### 5.2 四项裁定
- **(a) 纠正范围是否恰两行**：**状态层面可证，历史 diff 不可重建**。
  - 可证：① 两样本 `quick_scan_security` / `quick_scan_source_binding` 与（已更正为 CN 的）payload **逐字段 0 差异**；② 全库 security/binding market 0 失配；③ 3 实体均与各自基线（样本 payload / G2b 文档）逐字段相符；④ Alphabet 4+4 行与 10-04 文档逐字段相符；⑤ 终态状态哈希 == 批前（本审未引入任何漂移）。
  - **重要反向证据（本审发现）**：`identity_receipt` 中宁德回执 `source_listing.market` 仍为 `"CN-A"` —— 这是导入时由 store 派生的"纠正前快照"，客观证明 `quick_scan_security.market` 当时确为 `CN-A`、且**全库存在第三处承载同一事实的位置**（快照 `trusted_context.identity_receipts` 亦带该值）。因此"恰两行"作为**改动范围**陈述为真，但作为**一致性修复**为假 → P1-2。
  - binding 行的"纠正前值"无独立 before-image，只能由导出成功反推（`_verify_request` L213 要求 `binding.market == listing.market`，导出成功 ⇒ 两者现均为 CN）。
- **(b) 无修正 CLI、fail-closed 幂等拒绝重导**：**属实并已复跑实证**（见 5.1.3/5.1.4 + §4）。
- **(c) 层标签区分自洽**：**自洽，但根因未回填**。`security.market`/`binding.market` = ISO 3166/10383 市场码（CN/HK/US，与 registry 投影键全等）；`candidates.listing_key` 前缀与 `quick_scan_candidate.market` = 分层段标签（`CN-A`）；两者同名不同义属既有 schema 歧义（INFO-2）。task_plan Phase 84 ③ 的"库惯例一致"侦察结论对该列不成立，应补勘误（LOW-3）。
- **(d) 裁定：需返工（不可按现状接受）**。理由：纠正本身必要且机制诚实，但它把宁德实体推入**交付态不自洽**（P1-2 回执/快照互相矛盾）且**幂等门失效**（P1-1 exit 1），证据档对这两项后果均未披露；同时该 SQL 写入**超出写前卡"仅经授权 CLI 的数据写入"的允许面**，属卡外写（已在证据 §3 如实披露并请求裁定，程序上诚实）。
  - **可接受的返工路径（择一，均在现有 CLI 能力内）**：①（推荐）经 `entity-import` 把宁德推进到 `identity_revision=2` + 新 `ATT_` scope 回执（由纠正后 store 状态派生），重导快照、更新 sha 记档 —— 冲突检查对现值无冲突（本审已证）；② owner 书面豁免：保持 rev1，但在冻结清单中显式登记"回执 `source_listing` 为纠正前值、`LST_33c3643a…` 为悬空 listing_id"，并放弃该快照通过 IQS 契约语义校验的预期。**不得**再做第二次裸 SQL 改写。

---

## 6. 溯源与诚实

| 断言 | 实测 | 结果 |
|---|---|---|
| `source_namespace=iqs:b2a_candidates/2026-10-03` + `record_id=CN-A:300750` | `candidates.json`（216 条，sha `0ab0e311…`）`$[85] = {"listing_key":"CN-A:300750","name":"宁德时代"}` | ✓ |
| 同上 + `record_id=HK:06066` | `candidates.json` 段集合仅 `{CN-A:209, US:7}`，**无 HK 段、全文无 "06066"**；`quick_scan_candidate WHERE listing_key='HK:06066'` = 0；`quick_scan_issuer_bridge` `hk_ticker='06066'`/`hk_listing_key='HK:06066'` = 0，`cn_ticker IN (002168,601066)` = 0 | **✗ 不成立** |
| 06066 事实的真实出处 | 同批 `hk-discovery-results.json`（3,698B，sha256 首16 `eb38e6ce9968a9e2`）：`has_hk_listing=true`、`hk_ticker="06066"`、`evidence_url=https://www.hkex.com.hk/…sym=6066…`、`note:"中信建投证券股份有限公司 (CSC Financial Co…"`；`stratification-final.{json,md}` H 股提名行 `probe:CN-A:002168 → 06066` | 事实可溯，**键名/命名空间不实** → P1-3 |
| `record_id=listing_key`（卡 §14） | CATL 真；HK 的 `HK:06066` 是按 store 键格式（`issuer_bridge` 用 `HK:<ticker>`）**合成**的键，非任何数据集内既存 listing_key | ✗（卡面陈述对港股不真） |
| `actor=owner-2026-10-06-b01-sample-freeze` ↔ owner round-81 | `task_plan.md` Phase 84 标题"owner round-81 两项结构化决定"、L1232 样本冻结（A=300750 / H=06066 / 美=Alphabet GOOGL）；样本冻结提交 `f62a98c` 2026-10-06 20:48:14 +0100（同日） | ✓ |
| provisional 不声称 verified | 见 §2.2；payload `verified_issuer_receipt_id=NULL`、回执无 evidence_ref、无 IVR | ✓ |
| provenance 块如实 | 4 键齐、`entity_source` 与 namespace/record 对齐（HK 部分除外）、MIC 源实存且 sha 与库 meta 全等 | ✓（HK 部分见 P1-3） |
| 零网络零 LLM | 导入回执 `llm_calls=0/network_calls=0`（两份 + 本审 4 次重放均 0）；registry 走 `local://imported-csv` 离线导入；导出仅读三库；**但"导出回执"不存在**（见 P2-3） | 结论成立、表述不准 |

---

## 7. findings

### P0（阻断）
- 无。无状态损坏（终态状态哈希 == 批前）、无代码改动、无 verified 越界、无伪造 evidence。

### P1（阻断 → needs_revision）
1. **P1-1 宁德幂等重放在交付态失败**：`entity-import catl_payload.json` → **exit 1**、`phase_status=entity_saved_receipt_failed`、`error_code=receipt_duplicate`（cncb 为 exit 0）。证据 §2.3 的幂等结论早于 §3 纠正、纠正后未复验即交付；卡 §17 的"幂等重放"门在最终状态下对宁德不成立。（本审 4 次重放一致复现；行数与状态哈希零漂移，故是**门失效**而非数据损坏。）
2. **P1-2 宁德 identity 包内部矛盾（纠正第三处未处理）**：`identity_receipts.sqlite` 回执 `source_listing.market="CN-A"`、`listing_id=LST_33c3643a-ef19-4fac-b28f-542028b5505c`（悬空，payload listings 只有 `LST_0e457e3e-a036-4d75-b84e-40a0e0350721`），与快照 `payload.listings[0].market="CN"` / `source_bindings.market="CN"` 直接冲突；IQS 契约语义层拒绝该包。证据 §3"纠正范围恰两行、其余零改动"未披露第三处表征与该后果。
3. **P1-3 港股样本溯源不成立于所指命名空间**：`iqs:b2a_candidates/2026-10-03` 名指的 `candidates.json` 不含 `HK:06066`（连 HK 段都没有），staging 与 issuer_bridge 亦 0 行；事实只在同批 `hk-discovery-results.json`/`stratification-final.*`。需把 namespace/record_id 口径改实或给出等价溯源说明（不得再裸 SQL 改 binding：冲突检查会拦）。

### P2（应整改/应记录）
4. **P2-1 写前卡允许面未覆盖 `market-registry-import`**：本批新建 StockWiki `market_registry.sqlite`（7 记录，fixture sha 与库 meta 全等）属卡 §21"仅经授权 CLI 的数据写入（两实体+证券+绑定+provisional 回执）+ 只读导出"之外的写；证据 §2.4/§4 已披露，卡面未授权 → 下批把 registry 导入写进允许改动。
5. **P2-2 `f062903` 提交信息与内容不符**：commit message 声称含 "CATL/CNCB-H payloads … W04 snapshots 4ce7ba5a/2853cc98"，实际入库仅 6 个 txt —— 4 个 JSON 被 `.gitignore:89 (*.json)` 忽略；冻结快照只存在于磁盘 + 文档记录的 sha。建议对冻结资产 `git add -f` 或在证据中明示"JSON 资产不入库，以 sha 锚定"。
6. **P2-3 零网络零 LLM 的表述不准确**：导出路径不存在回执/计数输出（`stockwiki/services/identity_g2b.py` 无 `llm_calls/network_calls`）；导入回执里的 `0/0` 是 `identity_import.py` L308-309 的硬编码常量（结构性断言，非计量）。结论（零出站）成立，但"导入与导出回执均 llm_calls=0/network_calls=0"应改写为"导入回执字段为 0（结构性）；导出无回执，出站为零由代码路径证明"。
7. **P2-4 §3.1 的关键拒绝事件在产物档内零字节证据**：`e1.txt`/`e2.txt` = 0B，`*_export_err.txt` 内容是 `registry_not_imported`（早于 registry 导入的失败），**没有任何文件记录 `market_not_registered: CN-A`**。本审已隔离复现为真（§5.1.2），但证据档应补上原始 stderr 或引用复现方法。
8. **P2-5 跨仓既有：真实快照无法通过 IQS 公共契约 CLI**（两份 `exit 2`，原因见 §3.1：`BIND_`+连字符 vs `^BND_[A-Za-z0-9_]+$`；回执缺 `status=="active"`）。StockQA Q06 消费路径通过。**非本批引入**（Alphabet 同路径、StockWiki/IQS 测试 fixture 自带 `BND_`/`status` 才绿），但会在后续批次用 IQS 契约校验真实身份包时爆 → 建议单独开项（StockWiki 导出投影补 `status` + 双方对齐 ID 正则）。

### LOW
9. **LOW-1 时间戳晚于实际事件约 4h**：payload `build_at`、回执 `recorded_at`、导出 `--as-of` 均为 `2026-10-07T00:00:00Z`，实际执行为 `2026-10-06T19:52:19Z–20:01Z`；契约只查 UTC 形态（L128-136），合法但应在证据中注明"名义批次日"。
10. **LOW-2 快照含 CRLF**（CLI 文本 stdout 翻译），两份一致；与既有 golden CRLF/LF 差异口径相同，StockQA 以精确字节 sha 锁定。
11. **LOW-3 task_plan Phase 84 侦察③"市场标签 CN-A/HK 与库惯例一致"不成立**（`security.market` 惯例为 ISO 码），是 §3 纠正的根因，建议在 Phase 84 补勘误行。
12. **LOW-4 写前卡磁盘早于首次写仅 13 秒（20:52:06 vs 20:52:19），且与证据同提交入库（20:56:53）**——"写前"在文件系统层成立，在版本控制层不可独立自证；下批建议卡先提交再执行。

### INFO
13. **INFO-1 本审副作用全清单**（§1.1）：2 次只读导出、4 次 entity-import 重放（2×exit0/2×exit1）、1 次冲突测试（exit 2）、1 个隔离 temp root（已删）；三仓既有文件零改动。**终态复算**（本审全部操作结束后再跑同一状态哈希）= `e4ec6d0b9f6757bd60c23dfd10fbcc29cf50ec8e7cb035c0c4f52b95b278e63b`，与批前/审查前基线全等；`git status`：IQS 仅新增本报告（`opencode.json` 为 2026-10-02 既有未跟踪件）、StockQA 未跟踪集合与审查前一致、StockWiki 干净且 HEAD 仍 `3fe5008`。
14. **INFO-2** `quick_scan_candidate.market` 与 `quick_scan_security.market` 同名双语义（段标签 vs ISO 码）为既有 schema 歧义；建议写入身份契约文档。
15. **INFO-3** 空文件 `e1.txt`/`e2.txt` 已随 `f062903` 入库；IQS 未跟踪 `opencode.json`（mtime 2026-10-02，非本批）；StockQA 未跟踪目录 `b2a_2026-10-03` / `g2b_alphabet_2026-10-04` / `l02_2026-10-04`（mtime 2026-10-04，批内未触碰）。
16. **INFO-4** Alphabet verified 实体的 `scope_attestation_id=ATT_fb2f731c…` 在 `identity_receipt` 中无对应行（既有 G2b 状态；verified 分支按 `verified_issuer_receipt_id` 取回执，导出不受影响）。

---

## 8. 裁决

**needs_revision。**

- 数据主体到位且可复算：3 实体 / 6 证券 / 6 绑定 / 3 回执（2 provisional + 1 verified）与契约 L149-169 逐项相符；两份快照 UTF-8、字段、`trusted_context` 三键齐、**重导 sha256 逐字节等同**（`4ce7ba5a…9c07` / `2853cc98…4f0f`）；fail-closed 与"无修正 CLI"经本审复跑证实；范围与叙事三提交零触碰；provisional 诚实边界守住。
- 但交付态存在 3 项必须先修的 P1：**宁德幂等门失效（exit 1）**、**宁德回执/快照自相矛盾（CN-A 残留 + 悬空 listing_id）**、**港股 `HK:06066` 溯源不成立于所指 namespace**；§3 纠正因此裁定 **需返工**（首选：经 CLI 推 rev2 重建回执并重导快照；次选：owner 书面豁免并在冻结清单登记缺陷）。
- 复审范围建议收窄为：P1-1/2/3 的整改证据（新回执 + 新快照 sha + 幂等 exit 0 复验 + 溯源口径更正）与 §3 记录补正；P2/LOW/INFO 记档即可，其中 P2-5 单独开项。
