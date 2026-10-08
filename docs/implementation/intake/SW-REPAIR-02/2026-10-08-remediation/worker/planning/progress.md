# SW-REPAIR-02 progress

## 2026-10-07

- [x] 读施工卡 SW-REPAIR-02.md、handoff-rules.md、interfaces.md、inputs.lock.json
- [x] 读原整改卡 remediation-card-2026-10-07.md、独立报告 intake-review-2026-10-07.md、acceptance_cases.py
- [x] 核 StockWiki HEAD=`04dfc5190589a8bbe224a47e94b045779c884b80`，worktree clean，与 inputs.lock 一致
- [x] 向用户取得写授权（唯一 writer + 卡列路径）；新源码文件/store 修改未预授权
- [x] 建 planning 目录 `docs/handoff/SW-REPAIR-02/planning/`（pin PLAN_ID=SW-REPAIR-02）
- [x] 只读复核 6 处源码定位，确认与原整改卡一致
- [x] 从真实 Git 提取旧 producer `9f552a67` 的 `_query_hash` 口径
- [ ] 写 `tests/test_swr_cases.py` 映射原 7 场景并跑 RED

### 状态
Phase 1 in_progress；尚未修改任何源码/测试。

- [x] 写 `tests/test_swr_cases.py` 映射原 7 场景 → **6 failed / 1 passed**（与原冻结一致）
      日志 `logs/red_swr_cases_baseline.log`（sha256 60a007d25374a6e4d03b88d5ff4313d49622241e95eca26ac5f3651e07aaa526）
- [x] SWR-1/2/3：`quick_scan_backup_manifest.validate_manifest_shape` + `quick_scan_backup` 恢复/owner/partial 三项
      （`owner_registry.json` 经用户单独授权），新增 `tests/test_swr_backup.py` 15 例全绿
- [x] SWR-6：`_query_hash` 无条件时保留旧 `{text,filters,view}` 口径；新增 `tests/test_swr_query.py` 7 例全绿
- [x] SWR-4：`quick_scan_profiles` 变体分组 + 显式 ambiguous；新增 `tests/test_swr_profiles.py` 7 例全绿
- [ ] SWR-5：UI 多条件（进行中）
- [ ] 受影响测试批 + 真实浏览器 E2E
- [ ] 全量门 + 清理 + 交接

### 状态
Phase 4 in_progress。源码改动：`stockwiki/quick_scan_{backup,backup_manifest,profiles,query}.py`；
新测试 `tests/test_swr_{cases,backup,profiles,query}.py`；新数据文件 `backups/quick_scan/owner_registry.json`（仅运行时产生）。

- [x] SWR-5：`index.html`/`app.js`/`styles.css` 多条件控件 + `qsStateKey` 绑定 leaf+combine
- [x] 受影响批次 74 passed（`logs/green_affected_batch.log`）
- [x] 真实浏览器 E2E 11 passed、loopback 142 请求/0 外部（`logs/green_e2e_browser.log`）
- [x] `--static-only` exit 0；`--full` 1032 passed / 18 skipped / exit 0 / coverage 81%
- [x] 原 `acceptance_cases.py`（sha 未变）对本包源码 7 passed（`logs/frozen_acceptance_post_fix.log`）
- [x] 最终版 `test_swr_cases.py` 对基线源码 6 failed / 1 passed（`logs/red_swr_cases_vs_base_commit.log`）
- [x] 代码 commit `9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f`
- [x] golden 6 件 + `identity_golden_status.json`（missing，未合成）
- [x] 导出根 `runs/swr02-acceptance-*`、`runs/swr02-red-*` 逐路径删除
- [x] handoff 全套（handoff/summary/interfaces/case-map/isolation/six-fix-closure/artifacts）

### 状态
六项反例全闭合，本地 complete。not_run：TTL/W15、真实 QA 导入与双库恢复、F05/golden、
独立审查。pytest basetemp `pytest-{109,110,111}` 未手工删除（见 isolation.md）。

## 2026-10-08 第二轮整改（SR02-1..5）

- [x] 只读核基线 `6d1dddb` clean；12 固定反例移植进 `tests/test_swr_{profiles,backup}.py`
      → RED **12 failed / 25 passed**（`logs/red_swr02_12_boundary_at_6d1dddb.log`）
- [x] SR02-1：SQL 读 `segment_id` + 字段投影 `period_start/period_end/basis` + `_variant_key`
      纳入 segment/期间/口径（缺失≠显式）；歧义行四键置 null；`PROJECTION_VERSION → 1.1.0`；
      UI 变体/字段行显示口径；正例（选低不中、选高才中、单条正常观察查询正例）
- [x] SR02-2：`_refuse_managed_reparse` 在 create/list/prune/verify/restore 任何 I/O 之前
      lstat 拒绝受管路径重解析；两条真实 Windows junction 的 create + list/prune 反例
- [x] SR02-3：`validate_owner_registry` 未知版本 fail closed、`_registry_add` 不再静默重建、
      `owner_record_grants_deletion` 四绑定（版本/owner/workspace/digest）
- [x] SR02-4：`_read_manifest_object` 结构判定 `manifest_shape`，`[]`/`null`/`0`/`files:null`
      不再以 AttributeError/TypeError 中断 list/prune
- [x] SR02-5：authorized_paths 用真实文件名（不扩 validator）、独占 basetemp + 两个独占根已清
      （回执 `logs/cleanup_receipt_r2.json`）、接口 hash 改 git blob/多文件 manifest 并写明重建办法、
      公开 handoff CLI **exit 0**（`logs/handoff_cli_precheck_r2.log`）
- [x] `--static-only` exit 0 → 结果 commit `c83c148af35407a5ae01072314ba9bd17e59b3d9`
- [x] 受影响批次 **89 passed**、更宽家族网 **269 passed**、原冻结 **7 passed**、
      真实浏览器 **11 passed**（loopback 143 请求 / 11 端口 / 6 张 `r2-*` 截图）
- [x] golden 重生成 2 件；`export-manifest.json` 重建（工作树 + git blob 双口径 + 反例输入 hash）
- [x] 独占根 inventory → 解除 48 个自有 junction 节点 → 删两根 → `lstat` 不存在（`applied=true`）
- [x] 上一轮共享 TEMP 105/109/110/111 现状如实报告（absent、非本 writer 删除、取证缺口交 owner）
- [ ] 总控核新 commit/工件 + 受影响回验 + 一次集中独审（`review.status=not_run`）

### 状态
五组整改对本包 complete；G3/F05、TH/IN/L03 仍未放行，共享 TEMP 取证缺口保持 open。
