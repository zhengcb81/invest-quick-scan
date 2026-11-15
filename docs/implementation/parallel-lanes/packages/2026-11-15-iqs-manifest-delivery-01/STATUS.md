# OWNERPKG-IQS-MANIFEST-01 · 中微36题 owner manifest 交付 · 状态与运行手册（2026-11-15）

> 回应：`investment-dashboard/handoffs/owner-requests/invest-quick-scan/MANIFEST-DELIVERY-01.md`。
> 本轮为**零 MiMo 预算轮**：重跑扫描按 §2.3 须先报操作者确认额度，未获确认前不派发任何付费请求。
> 本轮完成：交付链核清、数据缺口证实、形状离线验证（V2 PASS / V1 拒绝）、§2.1 可满足性证明、重跑 runbook。

## 1. 结论概览

1. **36 题完整正式观测在 IQS 侧不存在**——manifest §2.2 引用的 run-4205968 实为 1/36 题 scope run；
   交付必须先重跑（预算门）。
2. **§2.1"单 rubric + 36 题 construct_id 非空 + 不裁剪"三者联合在现行题库契约下不可诚实实现**
   （§4 证明）。SW 的 V2 协议（`stockwiki.company_assessment/2`）是可执行的诚实形状：
   本轮已用 IQS 真实冻结 manifest 离线构造并通过 SW 校验器（`evidence/v2-register-request-dryrun.json`）。
3. **V2 混尺度下 Dashboard `latest_formal` 仍为 null**（冻结 adapter 要求 `scale_version` 非空字符串）。
   §1 目标字面（SW read `company_result` 非 null）可达；§4 全链（E07 闭环）需 Dashboard 契约另行变更。
4. SW operator 三步的**可执行顺序与 manifest §4 不同**：`publish-release → import → record-authority → register`
   （import 入口先要求 release of record 已发布；代码引用见 §6）。

## 2. 数据事实（可复查）

| 事实 | 证据 |
|---|---|
| run-4205968bd06a48edbfd5b3ea1463fe9b 只答了 IQS_12（requested_question_count=1，whole_manifest_answered=false），answer_status=insufficient_evidence | `runs/dashboard-runtime/run-4205968bd06a48edbfd5b3ea1463fe9b/result.json.scope.json` |
| "delivered=1" 指 1 个交付作业（deliveryjob_f23a4709…，package_count=1），不是 36 题 | `runs/dashboard-runtime/delivery-jobs/deliveryjob_f23a4709e662a9c1ce810b00b4d71d99.json` |
| 11-08 完整批次 batch-598c4601… 失败：2 scored + 6 insufficient_evidence + 25 error（IQS_09/10 search_unverified 后 23 题 not_dispatched）+ security 3 题未跑，批次 blocked | `runs/dashboard-runtime/batches/batch-598c460180c9447cac423e5e117c93c6.json`；SW 侧 `StockWiki/docs/handoff/SW-COMPANY-PROJECTION-01/IQS-DEFECT-2026-11-08-run-cascade.md` |
| SW owner workspace（=IQS 侧 `runs/r25-live/owner-workspace`，见 §6）中微观测仅 1 条（IQS_12，insufficient_evidence，不可用） | 该 workspace `scan_observations.sqlite` 全表 120 条（跨 4 实体），其中 ENT_99deceb6（中微）实体观测 count=1 |
| SW register 可用门槛：publication_status=published ∧ answer_status∈{scored,answered} ∧ qualification∉{rejected,conflict}；insufficient_evidence 不可入 formal | `StockWiki/stockwiki/public_company_assessments.py:60-61`（`_USABLE_ANSWER_STATUS`/`_REFUSED_QUALIFICATION`） |

**推论**：中微 36 题 scored/answered 观测数为 0；任何"交付"都必须以真实重跑产出为前提，无捷径。

## 3. 形状离线验证（本轮完成，零预算）

用 IQS 真实冻结 manifest（`prepare_4283c570…`，36 题，来自 release 家族 pkg_0151/modrel_9973，metric contract 1.0.0）：

- **V2 构造**：`iqs_scan.questions.frozen_release_projection.create_company_assessment_v2(manifest, [])` 成功，
  6 个 lineage group 完整划分 36 题：
  `1.0.0×diagnostic_only(12) / growth_core(1) / quality_core(15) / valuation_core(3)` +
  `2.0.0×growth_core(2) / quality_core(3)`；12 个 diagnostic 题 construct_id=null（如实承载）。
- **SW 校验**：`stockwiki.public_company_assessments._validated_v2_manifest` → **PASS**（离线只读调用，未写 SW 任何文件）。
- **V1 反例**：同一 36 题 V1 投影 → SW `_validated_manifest_v1` → **manifest_invalid**（null construct 先触发；
  混 rubric 会触发 `scale_lineage_mixed`）——复现 SW-PROJECTION-01 的实测拒绝。
- 活动包 pkg_07dc0d62（metric contract 1.1.0，222 题）同构：214×1.0.0 + 8×2.0.0、162 个 score 题
  construct=null（其中 comparison_role=diagnostic 16 个、context 146 个，均为不可比构念，V2 中归入
  diagnostic_only/context_only 聚合组）——V2 分组语义正是为此设计；53 题 envelope 的隔离
  publish/readback 此前已通过（root PWF 2026-11-14 节）。

证据：`evidence/v2-register-request-dryrun.json`（V2 请求候选，observations 留空占位——重跑后按真实观测 refs 重建）、
`evidence/v1-projection-dryrun.json`（V1 反例）。

## 4. §2.1 不可满足三角（题库契约证明）

1. **IQS_06 从初始基线就是 rubric 2.0.0**（commit `85162ec`，2026-09-22）——其 1.0.0 定义从未存在；
   "统一到 1.0.0"必须伪造内容。
2. 题库契约（`docs/implementation/contracts/question-modules.md`）：同 ID 禁改 rubric/构念/锚点（须新 ID+supersedes）；
   "`common` 必须恰有 IQS_01—IQS_24"——核心题 ID 永久固定 → 31 题的 1.0.0 **永远无法合法变为** 2.0.0，
   反向亦然（5 题 2.0.0 无法合法降回）。单 lineage 36 题发布在现行契约下**结构性不可行**。
3. DUPONT_01–07 / PORTER_01–05 是 diagnostic_only 题（`questions/diagnostics/*.json` 权威声明
   `construct_id=null`、`comparison_role=diagnostic`）；补非空 construct = 改构念声明 = 同样触发契约禁令。
4. 裁剪捷径（如只发 19 题 1.0.0 core）被 manifest §2.1"不裁剪"与红线明确禁止（SW publish-release 也会以
   `release_of_record_conflict` 拒绝遗漏同家族已发布题）。

**三条合法出路**（11-08 `RUBRIC-LINEAGE.md` 留档，均需另行决策）：题库契约变更（大工程）；
按尺度拆两条结果（Dashboard 只展示其一，仍非本包可做）；改 Dashboard 契约支持 V2 `scale_versions`。
本轮默认执行 **V2 诚实交付**（SW read 达标，Dashboard 腿留待其契约变更），如操作者另选，runbook 相应调整。

## 5. 交付目标更正：SW workspace 的真实位置

IQS worker_read 调 SW CLI 用的是 `--root config["workspace_root"]`
（`scripts/iqs_scan/workbench/dashboard_company_projection.py:132`），即
**`C:\Users\郑曾波\Projects\invest-quick-scan\runs\r25-live\owner-workspace`**，
不是 StockWiki 仓库 checkout。验证：store_id/registry_store_id 哈希逐位吻合
（qsobs_c2ce64820343a7b1 / qsca_9db1fe38dd82c631 = SW-PROJECTION-01 实跑日志值）；
ENT_99deceb6 在该 workspace identity 已 verified 注册；company_assessments.sqlite 尚不存在（registry 全新）。
`stockwiki_root`（StockWiki 仓库）只提供 CLI 代码，其自带 data/ 与本链路无关。

## 6. SW operator 链路（可执行顺序，代码引用）

manifest §4 写"register→import→publish-release"，实际代码顺序不可逆：

1. `dashboard_company_assessment_operator_cli.py publish-release --root <r25-live> --release <V2 manifest>`
   ——import 入口先调 `require_published_release`（operator_cli.py:81），release of record 必须先发布；
2. `… import --root <r25-live> --package <C06 package> --release <V2 manifest>`
   ——观察进 owner store（publication_status=published），并持久化 release artifact；
3. `… record-authority --root <r25-live> --release <V2 manifest>`——对已导入 artifact 逐字节认证；
4. `… register --root <r25-live>`（stdin：`{entity_id, manifest, observations:[36 refs]}`）；
5. `dashboard_company_assessment_cli.py read --root <r25-live> --entity ENT_99deceb6… --require-identity`
   → status=formal，company_result 非 null。

## 7. 重跑 runbook（每一步的前置与预算门）

| 步 | 内容 | 门 |
|---|---|---|
| R0 | 操作者确认 MiMo 预算（现行政策 `runs/u25-live/budget-policy.json`：单批 cap $25、单请求 ≤$0.25、--require-search） | **§2.3 强制** |
| R1 | 试跑 1 包 2 题（新 prepare → bundle，pack_size=2），验证 mimo search 回执（search_receipt_id/source_urls 非空） | ≤$0.5；建议但可跳过 |
| R2 | 全量 36 题：new prepare（活动包 pkg_07dc0d62 会生成新冻结 manifest + 新 bundle id）→ batch → run | cap $25 |
| R3 | 交付：delivery pipeline 产出 C06 包（consumer=StockWiki）+ 用真实 36 refs 重建 V2 请求（§3 同法） | 交回附 SHA-256 清单 |
| R4 | SW operator 四步（§6 顺序）由 SW harness/操作者执行 | 红线：IQS 侧不代执行 |
| R5 | 验收：SW read formal → Dashboard `get_result` | 见 §8 已知边界 |

**级联风险（重跑前置告知）**：11-08 的级联失败根因在 StockQA `src/core/qa_engine.py`
（`stopped_reason` 一旦置位，后续全部 not_dispatched，批次 blocked 无恢复路径）。该仓不在本包授权内；
不修则重跑可能再次在首个 search_unverified 题包后级联中止（已消耗部分不退）。建议操作者决定是否
先立 StockQA 失败隔离专项，或接受风险直接重跑。

## 8. 与 manifest 条款的偏差登记

| 条款 | 偏差 | 依据 |
|---|---|---|
| §2.1 单 rubric | V2 lineage_groups 如实承载 1.0.0/2.0.0 两组（不假装同尺） | §4 三角证明；SW V2 协议即为混尺度设计 |
| §2.1 全部 36 题 construct_id 非空 | 12 个 diagnostic_only 题 construct=null（目录权威声明） | V2 语义：可比性由 aggregation_role 承载 |
| §2.2 数据来源 run-4205968 | 该 run 仅 1/36 题；须重跑 | §2 证据 |
| §4 三步顺序 | 可执行顺序为 publish-release→import→record-authority→register | §6 代码引用 |
| §4 E07 全链 | V2 混尺度下 Dashboard `latest_formal` 仍 null（`scale_version` 契约） | adapter `_map_company_result`（quickscan.py:409-411） |

## 9. 证据文件 SHA-256（交回清单）

见 `evidence/SHA256SUMS.txt`（本目录）。本轮未产出正式交付包（预算门未过）；正式交付时按 §2.4 附完整清单。
