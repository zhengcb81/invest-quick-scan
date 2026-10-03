# G2b 证据补充检索报告（A/B/C/D 四类，2026-10-03）

依据：owner 授权「所有需要补充证据的，授权开 agents 找证据，然后我给予确认签收」。
执行：3 个只读 research agent 并行（tasks `ses_efd5465abffeAjexnL78bSIriy` A+C、`ses_efd543d02ffeEZAMh6JkAHwI5F` B、`ses_efd54167bffelW8x4zVP0AaomF` D）。全部 `mode=ro` 打开 sqlite、零网络、零写入、**未编造任何 URL/日期/回执**。本文件把三份报告的结论与"owner 必须提供"规格固化入盘供签收。

---

## 总表：四类证据现状

| 类 | 目标 | READY | CANDIDATE | 结论 |
|---|---|---|---|---|
| **A** 发行人核验回执 | `identity_state='verified'` + `IVR_` 回执 | **0** | 1（Alphabet GOOGL+GOOG）+ 16 条已激活 URL 池 | 缺回执记录与实体行，需 owner 确认候选并提供记录 |
| **B** A/H 权威桥 | 双边共享发行人数 | **0**（A/H）；US **READY**（CIK，653 组） | 0 | **彻底 MISSING**：0/151 对存在任何共享字段 |
| **C** 范围回执 | `subject@revision` + HTTPS 披露 | **0** | 3 条真实 HTTPS 合并范围披露 | 无 subject 记录、无生产者代码 |
| **D** 有效期日期 | 上市/退市结构化日期 | **0** | 2（申报散文、docling 表格单元） | security_master 零日期字段，目标表 0 行 |

---

## A 类：发行人核验证据

**机制确认**：`quick_scan_store._prepare:83` verified 必须有 `verified_issuer_receipt_id`；`identity_receipts.py:370-448` 要求 `same_legal_issuer=true` + security/listing **集合全等** + HTTPS `evidence_ref` + `^IVR_…$`。

**生产现状（只读实测）**：
- `StockWiki/data/quick_scan/` 只有 `scan.sqlite`（229,376B）。`identity_receipts.sqlite`、`scan_evidence.sqlite` **全盘不存在**。
- `quick_scan_entity` **0 行**；`quick_scan_security`/`quick_scan_source_binding`/`quick_scan_listing_history` 全 0 行；`quick_scan_candidate` 216 行全 `unresolved`。
- 全仓 `IVR_`/`same_legal_issuer` 命中**只在 tests + fixtures**（`IVR_fixture_issuer_1`、`https://example.invalid/…`）。
- `company-wiki/.source_catalog/catalog.sqlite3` → `source_metadata_assertions WHERE decision='verified'` = **18 行**（表无 `evidence_ref` 列，URL 在 `source_url`）：16 行 `evidence_basis='v2-normalized'`、`created_by='user-approved-2026-08-09'`、`activation_epoch='epoch-canary-2026-08-10'`，各带真实 HTTPS：Apple→sec.gov aapl-20250927.htm、NVIDIA→sec.gov nvda-20250126.htm、比亚迪 002594→cninfo announcementId=1222881496、阿里巴巴－Ｗ 09988→hkexnews 2026061800845_c.pdf、紫金矿业/安踏/美團/金山雲/壁仞 等。

**A 类最佳候选（A7+A8）—— Alphabet Inc.**：
- `source_metadata_assertions` 中唯一"一发行人多证券"实体：`Alphabet Inc.` → `nsec=2`，`secs='GOOGL,GOOG'`，两行（`sa-9328c6f4…` GOOGL、`sa-d81842c7…` GOOG）**共用同一 `document_id=urn:company-wiki:document:sha256:c2f6301004f3…`**。
- 该文档元数据（`documents` 表）：`Alphabet Inc. 10-K 2025-12-31`、`published_date=2026-02-05`、**`source_url=https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm`**（sec，权威）。
- 两行状态：`source_url=NULL`、`evidence_json='{}'`、`evidence_basis='security_master'`、`visibility_state='legacy'`、`accepted_at=NULL`、`activation_epoch=NULL`、`created_by='revenue-forecast-pilot-2026-08-01'` → **不在激活台账**。
- `security_master/us.json`：CIK `0001652044` 下实为 **4 只证券**（GOOG、GOOGL、GOOGM、GOOGN），全部 `source_record_id=0001652044`、`source_url=https://www.sec.gov/files/company_tickers.json` → 覆盖决策待定（GOOGM/GOOGN 无 assertion）。
- `activation_journal` 唯一回执 `d4e2a160…`（`reviewer='user-approved-2026-08-10'`）**不含**这两行 Alphabet 断言（16 个 assertion_ids 排除了它们）。

**A 类 owner 必须提供（缺失规格）**：
1. 回执记录写入 `data/quick_scan/identity_receipts.sqlite`（文件目前不存在，需 owner 事务创建）：`receipt_id ^IVR_…$`、`kind='verified_issuer'`、`entity_id` UUIDv4、`identity_revision≥1`、UTC `recorded_at`、**`same_legal_issuer=true`**、`security_ids`/`listing_ids` 与实体**集合全等**、`incorporation_country`/`canonical_name` 字节相等、`evidence_ref` 权威 HTTPS、`security_attributes`/`listing_attributes` 映射、`verified_adr_ratios`；IQS 侧还需 `status='active'`+`effective_status='active'`。
2. 前置：`quick_scan_entity` ≥1 行 `identity_state='verified'`+回执 id（当前 0 行）、每挂牌 `quick_scan_source_binding` 行（当前 0 行）、**实体导入路径授权**（现只有 candidate staging）。
3. A/H 类：**无任何双边共享标识**（见 B 类）。
4. 候选 URL（本地已记录，owner 挑一个并确认为发行人核验源；合规 host：`www.sec.gov`、`www.cninfo.com.cn`、`www1.hkexnews.hk`、`www.hkex.com.hk`、`www.iso20022.org`）：
   - `https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm`（Alphabet，覆盖 GOOGL+GOOG；GOOGM/GOOGN 覆盖决策待定）
   - `https://www.sec.gov/files/company_tickers.json`（共享键=CIK，覆盖 653 美股多证券组）
   - `https://www.cninfo.com.cn/new/disclosure/detail?stockCode=002594&announcementId=1222881496&announcementTime=2025-03-24%2016:00`（比亚迪，单挂牌）
   - hkexnews 各单挂牌 URL（见 A6 清单）

---

## B 类：A/H 权威桥（**彻底 MISSING**）

**字段全集实测**：CN `identifiers={cninfo_category, org_id}`（6137/6137）；HK `identifiers={hkex_stock_id}`（2746/2746）；US `identifiers={cik}`（6959/6959）。**任何文件任何记录都不存在 `isin/lei/cusip/sedol/csrc_code/unified_code/group_id/parent_issuer/same_issuer_as/issuer_key/company_group`**。

**候选键测试矩阵（N=151 个按名字导出的 A/H 对）**：

| 候选键 | 命中 | 判定 |
|---|---|---|
| `org_id` == `hkex_stock_id` | 0 | 拒 |
| `source_record_id`/`security_id`/`ticker` 两边相等 | 0 | 拒 |
| CN `org_id` 作为子串出现在 HK 记录（反之亦然） | 0 | 拒 |
| `isin`/`lei`/`cusip`/`sedol` | **双边字段都不存在** | 缺失 |
| 规范名 NFKC 精确相等 | 15 | 仅名字 |
| 名字/别名重叠（双向） | 151 | 仅名字（= 上次检索的方法，禁用） |
| **推导**：`gshk`+7位 → HK ticker | 13 覆盖、**10 对 3 错** | 拒（8.6% 覆盖、77% 准确，非权威） |
| **推导**：org_id 数字后5位 → HK ticker | 0 | 拒 |
| **US 对照**：`identifiers.cik` GOOGL/GOOG | 1/1 = `0001652044`；653 多证券组 | **READY（仅美股）** |

**映射表检索**：company-wiki `catalog.sqlite3` 全 `sqlite_master` 无 `cross_listing_map`/`same_issuer`/`ah_map`/`dual_listing`；`entities`(271) 按名字键。StockWiki `scan.sqlite` 只有 `quick_scan_candidate`；W02 曾提议的 `quick_scan_issuer_bridge`（`W02/implementation-proposal-2026-09-26.md:35`）**未实现**。`invest-quick-scan` 的 `identity.schema.json:146` 有 `VerifiedIssuerBridge` schema 槽位但**无生产者**。dayu-agent 只有市场内 id（`603993_SSE`/`9988_HKEX`），`tests/fins/test_ingestion_tools.py:286` **拒绝跨市场形式**。ISIN 双边假设**无法本地证实**（cninfo 结构上无 ISIN，HKEX 原始表未带 ISIN 落盘）；唯一单边 ISIN = 维基缓存页 `CNE1000003X6`（601318，无 HK 对应）。

**B 类 owner 必须提供（二选一）**：
- **A**：一个**双边都在场**的发行人数（如 LEI、统一社会信用代码、香港公司注册编号、交易所/监管发行人数），写入 `security_master/{cn,hk}.json` 的 `identifiers.issuer_id`（带命名空间，如 `LEI:<20字符>`），601318↔02318、600031↔06031、688981↔00981 一致，覆盖 ≥148/151 对，附来源 URL。（W03 架构文档 `W03/identity-resolution-architecture-2026-09-28.md:38` 已声明此要求。）
- **B**：owner 签字的映射表（文件或表），每对一行：`{cn_listing_key, hk_listing_key, issuer_id, evidence_url(HTTPS 交易所/监管/发行人申报), verification_source: exchange_filing|regulatory_master|manual_audit, verified_at}` —— 可直接落成 `VerifiedIssuerBridge` 行（`bridge_id=BRG_*`、`security_ids=[SEC_CN_…, SEC_HK_…]`、`verified_same_issuer=true`）。
- 美股**无需任何东西**：CIK 已是发行人数级（GOOGL/GOOG=`0001652044`，653 组）→ B 类美股 READY，仅 A/H 阻塞。

---

## C 类：范围（perimeter）回执

**机制确认**：`identity.md:36-38` + `contract_validation.py:769-815` → key `f"{analysis_subject_id}@{analysis_subject_revision}"`、`status='verified'`、非空 `receipt_id`、三 id 字节相等、`evidence_ref` 以 `https://` 开头、`perimeter_sha256` = 对 `{analysis_subject_id, analysis_subject_revision, primary_issuer_id, scope_kind, scope_as_of, perimeter_coverage, memberships(按 entity_id 排序)}` 的 UTF-8 紧凑 JSON（sort_keys、`,`/`:`、ensure_ascii=False）求 SHA-256。

**生产现状**：`StockWiki/stockwiki/analysis.py` **0 处 subject 引用**（无生产者）；`identity_snapshot.py:264-285,343-355` 只**透传** `analysis_subjects`（不查回执、不落库）；`reporting_perimeter`/`issuer_states`/`listing_to_issuer` 在 StockWiki（含 5 个 worktree）与 company-wiki **0 命中**；`perimeter_sha256` 只在 IQS 契约代码+测试里；`ASJ_` 全是 fixture，`acceptance-cases.json:5738` ID-23 `status="specified_not_executed"`。`scan.sqlite` 连 `quick_scan_observation` 表都没有（W05 的 observation 库在真实工作区从未建）。

**C 类候选（真实 HTTPS 合并范围披露，本地已记录）**：
- **C7**：`StockWiki/data/companies/601318.SH/evidence_index.yaml:15261` → `ev_ffa9438f32dcaf86`、`source_date=2026-06-29`、**`https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0326/2026032600953_c.pdf`**（平安 A+H 双柜台年报业绩公告，片段含「本公司及附屬公…」）；同源镜像在 `wiki\companies\601318.SH\news\news_manifest.md:39`。属 StockWiki 自有研究库生产数据（quality_bucket=low）。
- **C8**：company-wiki `documents` 表三条权威年报（标准合并范围披露载体）：
  - 比亚迪 2024 年报，`published_date=2025-03-24`，`https://www.cninfo.com.cn/new/disclosure/detail?stockCode=002594&announcementId=1222881496&announcementTime=2025-03-24%2016:00`
  - 阿里巴巴－Ｗ 2026 財務年度報告，`published_date=2026-06-18`，`https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0618/2026061800845_c.pdf`
  - Alphabet 10-K（同 A8）
  - 注：全库无标题含 合并范围/合併範圍/scope-of-consolidation 的文档。
- **C9（不可用作 evidence_ref）**：`StockWiki/data/companies/688012.SH/evidence_index.yaml:5418` 中微公司 2019 半年报「纳入本公司合并范围」片段 —— 引用是**本地文件路径**，契约要求 HTTPS。

**C 类 owner 必须提供**：
1. **subject 记录**：`object_type='analysis_subject'`、schema `1.0.0`、`ASJ_…UUIDv4`、revision≥1、`display_name`、`primary_issuer_id`、`anchor_listing_id`（须解析到真实挂牌）、`scope_kind='consolidated_reporting_group'`、UTC `scope_as_of`、`perimeter_coverage`、`memberships[]`（每项 `entity_id` + `role ∈ primary_issuer|consolidated_subsidiary|equity_method_investee|related_not_consolidated` + `valid_from/valid_to` + `evidence_ref`，**恰一项** `primary_issuer` 等于 `primary_issuer_id`）。
2. **回执对象**注册于 `trusted_context.reporting_perimeter_receipts["<id>@<rev>"]`：`receipt_id` 非空、`status='verified'`、三 id 字节相等、`evidence_ref` 以 `https://` 开头（候选：上面 C7/C8 三条）、`perimeter_sha256` 按上述算法计算。
3. **`trusted_context.issuer_states` + `listing_to_issuer`** —— 每个非 primary 成员须先完成 **A 类**核验。
4. **owner 授权 StockWiki 实现**：AnalysisSubject 存储/生产者 + `reporting_perimeter_receipts` 可信上下文读取器（**均不存在**；`analysis.py` 0 处 subject）。
5. `complete_as_disclosed` 不得模型推断或手填。

---

## D 类：有效期（上市/退市）日期

**机制确认**：`identity_snapshot.py:159-160,259-260` 硬编码 `"valid_from": None, "valid_to": None`；`quick_scan_store.py:473-479` 的 `record_listing_history(... effective_at ...)` INSERT 存在但 **0 行**；`quick_scan_listing_history`/`identity_event`/`member_history` 全 0 行；`identity_g2b.py:164-165` 管道已就绪但喂的是 null。5 个 worktree **无 `data/quick_scan` 目录**。

**逐源实测**：

| 源 | 结构化日期字段 | 示例 | 权威性 | 判定 |
|---|---|---|---|---|
| company-wiki `catalog.sqlite3` → `evidence_spans.raw_text` | 无（散文） | 金山雲 3896「上市日期」=**2022-12-30**；壁仞 6082=**2026-01-02**；实体1548=2015-12-30；航天发展摘牌 2017-12 | 官方申报（HKEX/A股） | **CANDIDATE**（缺口：仅散文、无列、退市日期稀少） |
| dayu-agent `workspace/portfolio/688031/filings/…_docling.json` → `tables[103]` | 表格单元 `上市日期`/`交易终止日期` | 上市 **2022-10-18**；交易终止 **"-"** | 上交所年报（权威）经三方工具解析 | **CANDIDATE**（缺口：仅发行期申报、非证券主档字段、1/13000+ 覆盖、无 HK/US） |
| company-wiki `security_master/{cn,hk,us}.json` | **零日期键**；全部 `active:true`（无退市行） | — | cninfo/HKEX/Nasdaq/SEC 清单 | **NOT-EVIDENCE** |
| `documents`/`source_metadata_assertions` 的 `published_date`/`filing_date` | 有值但是文档日期；**退市公告 `published_date=NULL`**（`终止上市` 命中 5 篇） | Apple 2025-10-31 | 申报 | **NOT-EVIDENCE（对 D 而言）** |
| StockInfoDB / DLSimple / Downloader(Old) | 无；股票表 `{code,name}` | — | — | **NOT-EVIDENCE** |
| StudyStock `biren_research/sources/*.txt` | 散文（权威招股书） | 「上市日期」2026-01-02 | 官方 | **NOT-EVIDENCE（散文）** |
| StockWiki `scan.sqlite` 三张 dated 表 | 有 `effective_at` 列、**0 行** | — | — | **NOT-EVIDENCE**（目标 schema 就绪、零数据） |
| worktree 三方抓取页（搜狐/腾讯/东方财富） | 散文 | 2019-07-22、1997-10-08、`-` | 三方门户 | **NOT-EVIDENCE** |
| StockWiki fixtures | `valid_from` | 2020-01-01 / 2026-01-01 | 合成 | **NOT-EVIDENCE** |

**READY：0。CANDIDATE：2。** 其余 NOT-EVIDENCE。

**D 类 owner 必须提供（覆盖三市场）**：

| 市场 | 权威源（须交易所/申报官方，非门户抓取） | 必需字段 | 格式 |
|---|---|---|---|
| HK | HKEX *List of Securities* / HKEXnews 活跃+非活跃清单、终止上市公告 | `market, exchange_mic=XHKG, ticker(5位), isin, security_name, event_type ∈ {listed,delisted,suspended,resumed,renamed}, effective_from(YYYY-MM-DD), effective_to(可空), reason, source_url, source_sha256, retrieved_at` | CSV/JSON 每状态转移一行 |
| CN（沪深北） | cninfo/交易所 上市公司基本信息（LIST_DATE）+ 终止上市/摘牌公告 | 同上，`exchange_mic ∈ {XSHG,XSHE,XBJE}` + `list_board`；A+H 每边各一行 | 同上 |
| US | SEC/Nasdaq 上市通知、Form 25/25-NSE | `market, exchange_mic, ticker, cik, first_listed, delisted_date, reason(25/Form25), source_url` | 同上 |
| 覆盖 | 至少 216 条 `quick_scan_candidate`；理想=6137 CN+2746 HK+6959 US 全量 | `effective_at` = **交易所生效日**（非公告日）；严格 `YYYY-MM-DD`；每行带源 URL+SHA | 不可变快照 + `retrieved_at` |
| StockWiki 接线（需另行授权） | — | 写 `quick_scan_listing_history(...effective_at...)` 并把 `identity_snapshot.py:159/259` 的硬编码 null 换成真实值 | W02/W03 schema+导入工作 |

**过渡选项（仍需 owner 签收）**：把候选 #1/#2 **抽取成结构化列**（evidence_spans → 挂牌日期表；docling `上市日期/交易终止日期` 单元 → 同表）——把散文转成结构化行，但仍是单发行人/逐报告爬取，**能播种 D 样本、不能关闭 D**。

---

## 四类共同结论（供签收时注意）

1. **没有任何一类达到 READY**（可直接签收为"已满足契约"）。全部是 CANDIDATE 或 MISSING。
2. **结构性阻塞不是给个 URL 就能解的**：A 需要先有实体/回执存储与导入路径；C 需要 owner 授权实现 AnalysisSubject 存储+回执读取器；D 需要导入路径把日期写进 `quick_scan_listing_history`/`valid_from`。这三项都是**实现授权**，与证据本身分开。
3. **B（A/H）是硬缺失**：0/151 对存在任何非名字共享键，`gshk` 推导 77% 准确不可用。必须 owner 提供双边发行人数或签字映射表。
4. **美股 B 类已 READY**（CIK），A 类美股也有强候选（Alphabet 双证券共用一份 10-K URL）——**这两条可以最先签收**，其余等 owner 补料。
