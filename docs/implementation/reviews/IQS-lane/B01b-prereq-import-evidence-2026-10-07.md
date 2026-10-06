# B01-b 前置导入批证据 v2（宁德时代 + 中信建投 H，provisional，rev2 修复后）

日期：2026-10-07。执行者：IQS 总控。授权链：owner round-81 样本决定 + 2026-10-03 通授；写前报告=`B01b-import-card-2026-10-07.md`。路径=Alphabet 同款已验证 CLI（StockWiki `f701909` entity-import）。**v1 → v2**：独立审查（`prereq-import-review-2026-10-07.md`）判 needs_revision（3×P1）——本版为经 CLI rev2 修复后的最终态（**未再做任何裸 SQL**；v1 的一次性 SQL 纠正记录保留于 §3）。

## 1. 样本构成（rev2 最终态）

| 项 | 宁德时代 | 中信建投 H |
|---|---|---|
| entity_id | `ENT_99ebb735-f072-41e4-8545-823bc012614f` | `ENT_1af6804e-40c1-4c35-b190-ea691dba2c85` |
| canonical_name | 宁德时代新能源科技股份有限公司 | 中信建投证券股份有限公司 |
| identity_state / rev | **provisional / rev2**（rev1 历史保留） | **provisional / rev2**（rev1 历史保留） |
| 证券 | 300750 / CN / XSHE / CNY / ordinary | 06066 / HK / XHKG / HKD / ordinary |
| 活跃回执 | `ATT_591235a8dd2a454f83d5ebac9aef1ca0`（rev2，market=CN、listing `LST_0e457e3e…` 与 payload **MATCH**） | `ATT_88b518cb64e74bbd866256b2aa788630`（rev2，HK、listing `LST_cec43eda…` **MATCH**） |
| binding | `BIND_ae8146ad…` namespace=`iqs:b2a_candidates/2026-10-03`、record=`CN-A:300750`、market=CN | **新** `BIND_bd7bd199…` namespace=`iqs:b2a_hk_discovery/2026-10-03`、record=`CN_A_601066`（事实源=hk-discovery-results `eb38e6ce…` 的 CN_A_601066 记录，HKEX 证据 URL+全称）；**旧 `BIND_0608aa4d…`（错 namespace）留存为已披露残留**（0 证券引用=孤儿行） |
| basis / actor | user_exact_security_attestation + `owner-2026-10-06-b01-sample-freeze` | 同 |

provisional 诚实边界不变：**不声称 verified**；rev1 回执行（ATT_bd73/ATT_a6be，含 v1 的 before-image 如 CN-A）为**追加式历史**，导出与消费者均只取 rev2 活跃回执（trusted_context 实测仅 ATT_5912/ATT_88b5）。

## 2. 执行与验证（rev2）

1. **rev2 导入**：`entity-import --file *_rev2.json` ×2 → 均 exit 0、`entity_saved_receipt_recorded`、新 ATT 回执、0 网络 0 LLM。
2. **幂等重放（P1-1 修复）**：rev2 payload 各再跑 → **双双 exit 0**、同 receipt_id、零行新增（v1 的 catl `receipt_duplicate` exit 1 消除）。
3. **一致性（P1-2 修复）**：rev2 回执 `source_listing.market`=CN（v1 的 CN-A before-image 已被 rev2 取代）；payload listing_id 与回执 listing_id **逐字 MATCH**（`LST_0e457e3e…`/`LST_cec43eda…`）；trusted_context 仅含 rev2 回执。
4. **溯源（P1-3 修复）**：cncb binding namespace 改为 `iqs:b2a_hk_discovery/2026-10-03`、record=`CN_A_601066`（该 namespace 实档核过：hk_ticker 06066 + HKEX URL + 全称）；旧 BIND 残留=0 证券引用（孤儿，披露）。
5. **W04 重导**（market-registry-import 后，字节级捕获）：

| 文件 | 字节 | sha256（前16） | 内容 |
|---|---|---|---|
| `catl_snapshot.json` | 2976 | `6929f0868243a271…` | **rev2**、300750 CN XSHE、ctx 仅 ATT_5912 |
| `cncb_h_snapshot.json` | 2947 | `884855433a431292…` | **rev2**、06066 HK XHKG、ctx 仅 ATT_88b5 |

（v1 sha `4ce7ba5a…`/`2853cc98…` 已被取代；**本表 sha=归档文件字节=运行时 load_identity_snapshot 所取**——CLI stdout 为 CRLF、git EOL 归一为 LF 入库，两口径已双向复算、内容零差异（r2 R2-P1-1 处置）；stdout 口径值：catl `9960b7e0…`(2977B)、cncb `4d30c311…`(2948B)、alphabet `a4c6eeef…`(8690B)。）

产物目录：`StockQAbyLLM/pilot_runs/b01_prereq_2026-10-07/`（原+rev2 payload、导入回执、快照）。**JSON 产物经 `git add -f` 入库**（repo `.gitignore` 的 `*.json` 忽略规则不适用于证据档——审查 P2-2 处置）。

## 3. 批内纠正记录（v1 一次性 SQL + rev2 正式修复路径）

- **v1 一次性 SQL（已披露、已审查、不重复**：初始 payload 的 300750 `market` 误用候选段标签 `CN-A`；导出按注册表（ISO CN/GB/HK/US）拒绝 `market_not_registered: CN-A`（审查者在隔离 temp root 复现为真；本档 v1 的 e1/e2 为 0 字节——拒绝事件字节证据以审查报告复现为准，P2-4 处置）。无修正 CLI + fail-closed 幂等拒绝重导（审查者复跑实证 `source binding conflict` exit 2 零改动）→ v1 以**操作者一次性 SQL** 纠正 security/binding 两行 CN-A→CN（此即审查判定"需返工"的卡面外写）。
- **v2 正式修复（本版）**：经 **CLI rev2**（`identity_revision=1→2`，store 原生"bump the revision to change identity facts"路径）重建两实体——catl：同 binding（store 已 CN）+ 新 ATT 回执（market/listing 从纠正后 store 现算）；cncb：**新 BIND 引用**绕开绑定冻结守卫写入正确 namespace + 新 ATT。**未再做任何裸 SQL**；幂等/一致性/溯源三面复验全过（§2）。层标签口径勘误（Phase84 侦察③"与库惯例"失实——security.market=ISO 码、candidates listing_key=段标签）在 task_plan 勘误行记档。
- **残留披露**：旧 BIND_0608aa4d（0 引用孤儿）、v1 rev1 回执两行（含 CN-A before-image，消费者不取）。

## 4. 边界

- 全程零网络零 LLM（导出无回执；导入回执 0/0 为导入器实现事实——v1 曾笼统称"导入与导出回执均 0/0"，P2-3 据此更正为仅导入回执）。
- market-registry 用既有 iso10383 fixture（Alphabet 同源，7 条；**已补入写前卡允许面**——P2-1 处置）。
- 时间戳：名义 `2026-10-07T00:00:00Z`（快照 as-of）；实际导入窗口 19:52–20:29Z——名义/实际差异如实在此声明（LOW）。
- 快照含 CRLF（两份一致、导出器既定输出）；`load_identity_snapshot`（StockQA 消费面）两版均通过；IQS 公共契约 CLI 的 `BND_`/`status` 兼容项=P2-5 单独开项（非本批引入，Alphabet 同路径）。

## r2 处置补记（round-88）
- **R2-P1-1（sha 口径对齐，修法 ii）**：manifest §1 与本档 §2 三行全部改为**归档文件字节 sha**（=运行时 `load_identity_snapshot` 所取）：alphabet `5ad1a45e287c9456…`(8689B)、catl `6929f0868243a271…`(2976B)、cncb `884855433a431292…`(2947B)；CRLF（CLI stdout）↔ LF（git 归一入库）关系与双向复算注明；提交信息口径以本节更正（历史提交不改写）。**验收双值已核**：三文件 Get-FileHash == load_identity_snapshot 返回值（逐一相等）。
- **P2-1**：cncb rev2 payload `provenance.entity_source` 改为 `iqs:b2a_hk_discovery/2026-10-03 (CN_A_601066)`（与自身 binding/revision_2_note 一致；catl 的 candidates 源属实保留）。
- **P2-2**：Phase 84 侦察③**真勘误行**写入 task_plan（原句「与库惯例一致」失实——security.market=ISO 国家码、CN-A=候选层段标签，两层不可混用）。
- **P2-3**：rev2 回执归档——`catl_rev2_import_out.txt`/`catl_rev2_replay_out.txt`/`cncb_h_rev2_import_out.txt`/`cncb_h_rev2_replay_out.txt`（四份均 rc=0、receipt_recorded=true、幂等重放零新增）。
