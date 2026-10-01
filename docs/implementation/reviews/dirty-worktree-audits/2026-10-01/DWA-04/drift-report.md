# DWA-04 漂移报告 — revenue-forecast 快照核验未通过

按 [`task-packet.md`](task-packet.md) §状态冻结与并发保护 第 1/2 条执行：先重跑快照命令核对，**快照不一致 ⇒ 停止基于旧快照的逐条归因，只交付本漂移报告**，等待 owner 确认新基线。本报告未对仓库做任何写入/暂存/清理；RF 仓库全程只读。

核对时间：2026-10-01（快照捕获时间 2026-10-01T20:35:25Z 之后的会话）。

## 1. 一致项（HEAD/分支/快照自身完整性）

| 项 | 快照 | 重跑实测 | 结果 |
|---|---|---|---|
| 分支 | `fcap` | `fcap` | ✅ 一致 |
| HEAD | `ee0a82bfd1eec935cf4e567eb42f0ef79efa0226` | `ee0a82bfd1eec935cf4e567eb42f0ef79efa0226` | ✅ 一致 |
| 快照摘要自洽性 | `status_porcelain_sha256 = 086f4505…` | 按 `status_digest_canonicalization`（条目 LF 连接 + 单尾 LF、剔除 `#` 注释行）对 `snapshot-status.txt` 复算 = `086f4505c5bb6d22f0c095b0d9c37c63551bdfbd6620134782ad1df6cad8c452` | ✅ 复现规则正确，快照文件自身完整 |

## 2. 不一致项（状态）— 触发停止

按 `snapshot.json.status_command` 逐字重跑（含 `safe.directory`、`core.quotepath=false`、`--untracked-files=all`）：

| 项 | 快照（20:35:25Z） | 重跑（本次会话，开始与结束各一次） |
|---|---|---|
| 状态条目数 | 6124 | **416** |
| ` D` | 3778 | **0** |
| ` M` | 12 | 12 |
| `??` | 2334 | 404 |
| porcelain SHA-256 | `086f4505…` | **`fd4981c6202aae2e4a6e1dc491b01b329ff4f620426f7f8bae0753048de28e07`** |

审计期间本会话内开始/结束两次重跑均为 416 条、摘要同为 `fd4981c6…` ⇒ **本会话视角下仓库状态稳定，漂移发生在快照时刻与现在之间（或两次视角可见性不同）**。

## 3. 漂移分解（快捷对账，不构成归因）

- **` M` 12 条**：路径集合逐一相同（5×`.planning/2026-09-19-three-project-history-audit/*.md`、4×`assurance/runs/*.(jsonl/json)`、3×`assurance/unified_completion/uc|tests/*`）→ 此部分锚点目前有效。
- **`??` 差异 −1930（2334→404）**：
  - 快照独有 1985 条，其中 **1971 条位于 `.tmp-zr408-unit` / `.tmp-zr408-unit-final` / `.tmp-zr408-unit-retry`（各 657 条）**；本会话对该三个目录报 **`Permission denied`**（status 出现 3 条 warning），只能看到其存在、列不出内容。
  - 两条公共为 45×`.tmp-r41-mutation`（43 scripts + 2 tests）、`assurance` 2、`h2.log`/`h2.log.err`、312/353 此消彼长的 `.planning`（含引号路径条目的逐字差异）。
  - 本会话独有 55 条，全部位于 `…/execution_runs/DEF-I00C-GATE-NEG/a20260926-01/tmp/i17b_n3_*`（如 `11_implementer.json`、`13_reviewer_old.json` 等）——快照未列出、本会话可读。
- **` D` 差异 3778 → 0**：
  - 快照的 3778 条 ` D` 全部位于 `.planning/2026-09-19-three-project-history-audit/**`（含 40 条引号路径条目），多为 `execution_runs/*/…/scratch/…` 深路径。
  - 抽样 20/20 条 ` D` 路径**现在磁盘上真实存在**（如 `…/B3-I05C-delivery-fixes/a20260921-01/scratch/before_w05b/test_prepare_source_receipt_ha0/norm.txt`，8 B，mtime 2026-09-21）；快照把同类文件记为 `"hash_state":"deleted-at-snapshot"`（size/mtime/sha 全 null）。
  - ⇒ 快照的 ` D` 更像**捕获时刻的可见性/访问伪删除**（长路径 >260 字符、ACL、或在途的临时访问受限），**不能确认为真实删除**；同样**本会话 status 也带同类 warning**（1 处 "Filename too long"，I-07-D-REPRO staging cwroot；3 处 `reviews/revenue/scratch/*` 与 3 处 `.tmp-zr408-*` "Permission denied"），故本会话的 404/416 口径同样是**下界**，两边口径都不可直接采信。
- **文件哈希抽查**：从 `snapshot-files.jsonl` 2274 条 hashed 中随机抽 25 条重算：**6 条磁盘可读且 SHA-256 全部相同、19 条本会话不可读（未计为不匹配）、0 条内容不一致**。抽查过小，不足以盖章全部哈希，但未发现内容漂移证据。

## 4. 结论与等待事项

1. **按卡规则停止旧快照归因**：6124→416、3778 ` D`→0、摘要不同 ⇒ 本卡要求的"逐条解释 6124 条状态"当前**不可安全执行**。
2. 待 owner 确认/重建基线后，12 条 ` M` 锚点与少量可读 `??`（`.tmp-r41-mutation` 45 条、`assurance` 2 条、`.planning` 大部）可立即恢复归因。
3. **明确未知项（不推测）**：快照时刻 `.planning` 内 3778 条 tracked 文件为何被报 ` D`（真实瞬时删除 vs 可见性伪删除）——**未知**；`.tmp-zr408-*` 三目录在本会话 `Permission denied` 的原因（ACL/被占用/保留名）——**未知**；快照缺列 55 条 DEF-I00C tmp 文件的原因——**未知**。若 owner 在更高权限会话复核 `.tmp-zr408-*` 与 `.planning` 长路径后重出快照，建议同时修正 `status_command` 加入 `core.longpaths=true`，可消除假删除类口径。
4. 本会话对 RF 仅执行：`status`、`rev-parse`、`branch --show-current`、`rev-list --count`、`ls-files`（上一卡上下文）、文件 `ls/stat/读样例 jsonl` 均为只读；对 RF 写入 0 起。

## 5. 复算命令存根（复核用）

- 状态重跑/摘要：`git -c safe.directory="C:\Users\郑曾波\Projects\revenue-forecast" -c core.quotepath=false -C "C:\Users\郑曾波\Projects\revenue-forecast" status --porcelain=v1 --untracked-files=all` → 416 条；摘要 = `grep -v '^#' snapshot 条目` 去 CR 后 LF 连接 + 单尾 LF 的 SHA-256。
- 状态集合：`sed -n 's/^ D //p' …` 分类计数；`comm` 交集/差集得 −1985/+55/349。

— DWA-04 报告完 —
