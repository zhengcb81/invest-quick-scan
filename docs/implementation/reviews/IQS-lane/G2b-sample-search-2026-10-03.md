# G2b 真实样本搜索结果归档与 owner 签收（2026-10-03）

依据：owner 决定4（2026-10-03）「你调用一个 agent 去找需要的东西，我可以授权签收」。
执行：IQS 总控派发只读 research agent（task `ses_efeb4ef73ffeb04OTbpoo2e8c5`），全程零写入、零网络、sqlite 以 `mode=ro` 打开。本文件把该 agent 的检索结果**从会话固化入盘**（此前仅存在于会话上下文=证据缺口，现补齐），并记录 owner 签收。

## 1. 检索范围（只读）

- `invest-quick-scan`：`docs/implementation/reviews/IQS-lane/G2b-handoff-2026-09-29.md`、`tasks.json` 中 G2b/W04 相关判据
- `StockWiki`（canonical）：`stockwiki/identity_{mapping,g2b,receipts,snapshot}.py`、`analysis.py`、`data/quick_scan/scan.sqlite`（只读查询）、`data/`/`config/`
- `company-wiki`：`.source_catalog/catalog.sqlite3`（只读）、`security_master/` 主档
- 辅助 worktree（次级证据）：`StockWiki-identity`、`StockWiki-w04-g2b`、`StockWiki-lane-integration`、`StockWiki-sw-ident`
- 明确**不计为真实样本**：`contracts/goldens/stockwiki-g2b-72531b5-provisional.json`（provisional/合成）

## 2. 四类样本检索结果

| 类别 | 真实样本 | 计数 | 最强证据 |
|---|---|---|---|
| **A. verified 身份实体**（`identity_state='verified'` + `verified_issuer_receipt_id`） | **StockWiki 内：无** | 0 | `scan.sqlite` `quick_scan_entity` 0 行；`identity_receipts.sqlite` 文件不存在；`IVR_` 全部命中都在 `tests/` fixture；4 个辅助 worktree 无 `data/quick_scan`。近似物（不同模型）：company-wiki `source_metadata_assertions` 18 行 `decision='verified'`（文档级，非发行人回执）、`activation_journal` 1 条 `reviewer='user-approved-2026-08-10'` |
| **B. 多挂牌实体** | **company-wiki 主档内：有真实原料**（StockWiki 库内：无） | 美股同 CIK 组 **653**、A/H 对 **148** | `us.json`：GOOGL+GOOG 同 CIK `0001652044`（`company_tickers.json` 权威来源）；`cn.json`↔`hk.json`：601318↔02318 中国平安、600031↔06031 三一重工、688981↔00981 中芯國際。**注意**：A/H 关联仅名字/别名证据，**无共享权威键**（正是"缺真实权威 bridge"缺口）；美股 CIK 关联是权威的 |
| **C. AnalysisSubject 样本** | **全部位置：无** | 0 | `identity_snapshot.py:292-355` 的 `analysis_subjects` 仅透传；`issuer_states`/`listing_to_issuer`/`reporting_perimeter` 在 StockWiki 全仓 0 命中（无生产者）；所有 `ASJ_` 均为 fixture；company-wiki `analysis_subject` 0 引用 |
| **D. 历史区间**（`valid_from`/`valid_to` 实际日期） | **StockWiki 内：无** | 0 | `identity_snapshot.py:159/259` 硬编码 `valid_from/to: None`；`quick_scan_source_binding` 无有效期列；dated 表（`quick_scan_listing_history`/`identity_event`/`member_history`）全空；`scan_evidence.sqlite`（含 alias/claim 有效期列）文件不存在。近似物：company-wiki `document_retire_audit` 19,000 行真实 `created_at`（文档生命周期，非身份区间） |

**总结**：A/C/D 三类**真实样本在 StockWiki 内为 0**；B 类真实原料在 company-wiki 生产主档（653+148 组）但尚未进 StockWiki 身份库。

## 3. 可生成 vs 需外部证据（agent 结论）

- **B — 可生成（大部分）**：真实输入已在 company-wiki 主档，`entity-add-security` CLI 可挂第二挂牌。**阻塞点**：无公开建实体/导入 CLI（`save_entity` 只有测试调用方）→ 缺的正是 W02 候选导入路径（**已于 Phase 60 落地为 `candidate-import`**，但该入口按决定1 只做 staging，不建实体）。A/H"同一发行人"声明还需权威 bridge 记录：美股 CIK 可用，A/H 需 owner 提供关联证据（仅名字匹配按 G2b 负例3 必须保持 unresolved）。
- **A — 部分可生成，需外部证据**：机械在（`IdentityReceiptStore`、`_validated_verified` 要求 `same_legal_issuer=true` + 全挂牌覆盖 + HTTPS `evidence_ref`）；但**发行人核验的 HTTPS 证据与置 verified 的决定是 owner 提供的外部记录**，且实体播种仍需导入路径。
- **C — 当前不可生成**：需新的 owner 授权实现（AnalysisSubject 存储/生产者 + `issuer_states`/`listing_to_issuer`/`reporting_perimeter_receipts` 可信上下文，均不存在）**加 owner 提供的 perimeter 回执**（`contracts/identity.md:36` 要求 HTTPS 披露）。B 类真实 A+H 数据可作输入但不能自我授权范围。
- **D — 当前不可从库生成**：`quick_scan` schema 无有效期列、投影硬编码 null；需 owner 授权的 W02/W03 schema+导入工作把外部带日期记录（HKEX/cninfo 上市/退市日期）喂给已写好的 evidence-store 表。

## 4. G2b 仍缺（签收后仍客观存在的缺口）

1. 任何真实 `quick_scan_entity` 行 `identity_state='verified'` + `identity_receipts.sqlite` 中真实 `IVR_` 回执（当前 0 行/文件不存在）。
2. 任何真实 StockWiki 多证券实体（一个 `entity_id` 2+ `quick_scan_security`）带权威同一发行人 bridge 证据（653/148 原料只在 company-wiki，未进身份库）。
3. 任何真实 `ASJ_` 记录（id+revision+成员区间）及其 owner perimeter 回执（无生产者代码）。
4. 任何 StockWiki 身份挂牌/绑定/别名/声明的非 null `valid_from`/`valid_to`（投影硬编码 null、evidence-store DB 缺失）。
5. 保留性工件状态（2026-10-03 实测磁盘，`StockWiki/data/quick_scan/`）：真实 ISO 10383 CSV **缺失**（只留 `tests/fixtures/market_registry/iso10383_sample.csv`）；`market_registry.sqlite` **缺失**；`scan_evidence.sqlite` **缺失**；`identity_receipts.sqlite` **缺失**；`scan_observations.sqlite` **缺失**——W05 的 `QuickScanObservationStore` 代码已在，但其表只在临时测试目录建过，**真实工作区从未跑过 observation 导入**（本会话 W05 全部 18 测试用 tmp_path 隔离）。`scan.sqlite` 存在且 224KB（Phase 60 的 216 候选 staging 在此）。

## 5. owner 签收

- **签收对象**：本检索报告的**完整性与诚实性**（A/C/D=0、B=company-wiki 内 653+148 组、可生成性分析）。**签收 ≠ G2b 卡 verified**，也不等于对 A/C/D 缺口的豁免。
- **签收状态**：✅ owner 于 2026-10-03 口头签收（会话指令「签收」）。
- **后续归属**：A/C/D 的补齐各需新的 owner 决定——A=提供发行人核验证据并授权建实体导入路径；C=授权 AnalysisSubject 实现+提供 perimeter 回执；D=授权 schema 有效期列+提供外部带日期记录。B 的 bridge 证据（尤其 A/H）待 owner 提供。
- G2b 卡保持 **未 verified**，缺口如 §4 所列，不得因本签收而声称完成。
