# 中微 36 题 owner manifest 交付包（HANDOFF）

> OWNERPKG-IQS-MANIFEST-01 · 2026-11-16 · 目标 workspace：`runs/r25-live/owner-workspace`
> （= IQS worker_read 传给 StockWiki CLI 的 `--root config["workspace_root"]`，
> store_id qsobs_c2ce64820343a7b1 / registry qsca_9db1fe38dd82c631）

## 1. 已完成的 owner 动作（全部真实、可复核）

| 动作 | 结果 | 证据 |
|---|---|---|
| 36 题 formal 扫描 | 36/36 result_ready（entity 33 + security 3）；双 bundle 同批 owner_ready | `runs/dashboard-runtime/run-*/`、ledger `work.sqlite` |
| owner 交付 | 33 + 3 包，**0 错误码**，观测全部 published 入 owner store | `delivery/packages/`（36 个 C06 包） |
| `publish-release`（V2 owner manifest） | **published**，release_sequence=1，question_count=36 | `registry-state.json.published_release` |
| `import`（V1 source projection 绑定） | artifact recorded（sequence 1），ACK 无 error_code | `registry-state.json.imported_release_artifact` |
| `record-authority` | **recorded**，authority_sequence=1，question_count=36 | `registry-state.json.company_release_authority` |
| `register` | **拒绝**：`observation_answer_unusable` | `register-refusal.json` |
| 公开读面 | `company_result_not_registered`（已从 company_not_registered 前进） | `read-after.json` |

交付形状（owner manifest）：`release-v2-manifest.json` = protocol `stockwiki.company_assessment/2`、
schema 2.0.0、36 题、6 个 lineage group（1.0.0：diagnostic_only 12 / quality_core 15 / valuation_core 3 /
growth_core 1；2.0.0：quality_core 3 / growth_core 2）、source_release 绑定
pkg_0151…/modrel_9973、catalog 3.2.1、manifest_raw_sha256 459f1945…（逐字节复用 11-08 冻结 bank）。
`release-source-projection.json` = 同一 source_release 的 V1 投影（import/authority 绑定用）。
`register-request-v2.json` = 36 条真实 observation refs（observation_id + payload_sha256 + question_id）。

## 2. 未达成项：SW read 仍返回 result=null 的原因

`register` 被拒的**唯一**原因：`observation_answer_unusable`。SW 的公司结果权威要求 manifest 的
每一题都有 `answer_status ∈ {scored, answered}` 且 published 的观测；本次 36 题中：

- **scored 8 题**：IQS_01(7)、IQS_02(5)、IQS_24(5)、PORTER_01(6)、PORTER_02(7)、PORTER_03(7)、
  PORTER_04(6)、PORTER_05(6)
- **insufficient_evidence 28 题**：IQS_03–23（21 题）+ DUPONT_01–07（7 题）

这是 provider 的**诚实判定**，不是管道故障：每答仅带回 2 条证据，检索片段缺少题目要求的定量输入
（如 DUPONT_01 缺归属普通股净利润/平均权益/周转率/税率等杜邦分解输入；IQS_09 缺关键岗位梯队与
授权记录；IQS_17 缺客户集中度与单一来源替代认证成本）。模型据实留空（score=null）。

**不可用捷径（owner 规则主动阻断，已实测）**：裁剪 manifest 至 8 题 → `publish-release` 以
`release_of_record_conflict` 拒绝（store 已持有同家族 36 题观测）；放宽 SW 可用性规则 → 属于 owner
合同变更，非本包授权。因此 formal 结果只能由**真实可评分答案**产生。

## 3. 待操作者决策（唯一剩余开口）

| 选项 | 内容 | 代价与预期 |
|---|---|---|
| A（推荐） | **提高检索证据密度后重问 28 题**：当前每题仅 2 条证据；换检索策略（直取 2025/2026 年报 PDF、增加 search 调用、指定财务附注页）重跑，观察 insufficient_evidence → scored 转化率 | ≈$1（28 题 × ~18 包）；**转化率未知**，DUPONT 类可能仍不足 |
| B | 用**更新的信息截止日**（2026-11-16）重扫全部 36 题（新 manifest，但同 module release 家族，SW release of record 仍可绑定） | ≈$1.3；同样不保证转化 |
| C | 接受本轮结果为 **36/36 已交付 + 无 formal**，E07 保持未闭环 | 零花费；形态与覆盖目标已达成，仅 §1 字面目标未达 |

选项 A/B 都属于**研究质量**范畴（证据可得性），不是交付形状问题：形状、覆盖、权威、导入四项已闭环。

## 4. 文件清单

- `release-v2-manifest.json` / `release-source-projection.json` / `register-request-v2.json`
- `packages/pkg_*.json`（36 个 C06 交换包，consumer=StockWiki）
- `register-refusal.json` / `read-after.json` / `registry-state.json`
- `SHA256SUMS.txt`（42 个文件的 SHA-256）

复算：`python -c "import hashlib,os;[print(hashlib.sha256(open(p,'rb').read()).hexdigest(),' ',p) for p in ...]"`
