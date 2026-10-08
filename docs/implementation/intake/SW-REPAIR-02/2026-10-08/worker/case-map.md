# SW-REPAIR-02 case 映射

图例：结果列取 `passed / failed / skipped / not_run`（case 级 = 其全部已绑定原子断言的最差结果）。
日志文件的原字节 SHA-256 见同目录 `artifacts.json`（`kind=log`/`kind=golden`/`kind=screenshot` 条目）。
测试选择器为 pytest node id（在源仓根目录执行）。

- 基线 commit：`04dfc5190589a8bbe224a47e94b045779c884b80`
- 本包 commit：`9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f`
- 原冻结反例文件（未改一个字节）：`invest-quick-scan/docs/implementation/reviews/SW-READY-01/acceptance_cases.py`，sha256 `72b2e1250947a705f87426557ccdf8b09121d761ba09ae89da3df152db81d452`

## 原冻结 7 场景 → 本仓映射

| # | 原场景（`acceptance_cases.py`） | 基线结果 | 本仓映射 selector | 修后日志 | 结果 |
|---|---|---|---|---|---|
| 1 | `test_restore_accepts_already_existing_empty_target` | failed | `tests/test_swr_cases.py::test_swr1_restore_accepts_already_existing_empty_target` | `logs/red_swr_cases_vs_base_commit.log` → `logs/frozen_acceptance_post_fix.log` | passed |
| 2 | `test_foreign_manifest_directory_is_never_pruned` | failed | `tests/test_swr_cases.py::test_swr2_foreign_self_consistent_manifest_is_never_pruned` | 同上 | passed |
| 3 | `test_failed_final_rename_never_leaves_complete_partial_backup` | failed | `tests/test_swr_cases.py::test_swr3_failed_final_rename_never_leaves_publishable_partial` | 同上 | passed |
| 4 | `test_two_subjects_of_one_issuer_never_silently_collapse_into_one_score` | failed | `tests/test_swr_cases.py::test_swr4_two_subjects_of_one_issuer_never_silently_collapse` | 同上 | passed |
| 5 | `test_ui_supports_multiple_conditions_instead_of_single_leaf_static_contract` | failed | `tests/test_swr_cases.py::test_swr5_browser_must_not_hard_code_a_single_condition_leaf`（静态）+ 真实浏览器 `tests/test_e2e_quick_scan_ui.py::test_browser_two_conditions_add_remove_and_or_and_leaf_change` | 同上 + `logs/green_e2e_browser.log` | passed |
| 6 | `test_real_legacy_public_snapshot_remains_readable` | failed | `tests/test_swr_cases.py::test_swr6_real_legacy_public_snapshot_stays_readable_on_page2` | 同上 | passed |
| 7 | `test_sqlite_online_backup_preserves_committed_wal` | **passed**（保留） | `tests/test_swr_cases.py::test_swr_wal_committed_pages_positive_keeps_passing` | 同上 | passed |

- 基线 RED（用**最终版**测试文件对基线源码）：`6 failed, 1 passed` → `logs/red_swr_cases_vs_base_commit.log`
- 修后同一批原文件（sha 未变）对本包源码：`7 passed` → `logs/frozen_acceptance_post_fix.log`

## 六项反例（本卡）→ 真实测试 → 日志 → 结果

详细实现位置与断言见 `six-fix-closure.md`。

### SWR-1 恢复目标

| 原子断言 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|
| existing-empty 目标恢复成功 | `tests/test_swr_cases.py::test_swr1_restore_accepts_already_existing_empty_target` | `logs/green_affected_batch.log` | passed |
| absent 目标恢复成功 | `tests/test_swr_backup.py::test_restore_into_absent_target_succeeds` | 同上 | passed |
| 非空目标拒绝且历史原样保留 | `tests/test_swr_backup.py::test_restore_refuses_non_empty_target_and_keeps_history` + `tests/test_quick_scan_backup.py::test_restore_refuses_non_empty_target` | 同上 | passed |
| 复制途中并发新文件拒绝、只清自己的 staging | `tests/test_swr_backup.py::test_restore_refuses_target_filled_while_the_copy_runs` | 同上 | passed |
| junction 目标 / 父目录 junction 拒绝 | `tests/test_swr_backup.py::test_restore_refuses_a_junction_target`、`test_restore_refuses_a_junction_in_the_data_parent` | 同上 | passed |
| 目标解析越界拒绝 | `tests/test_swr_backup.py::test_restore_target_resolving_outside_the_workspace_is_refused` | 同上 | passed |
| 备份源是链接拒绝 | `tests/test_swr_backup.py::test_restore_of_a_link_inside_the_backup_source_is_refused` | 同上 | passed |
| 恢复中失败保留原目标并清 staging | `tests/test_swr_backup.py::test_restore_refuses_non_empty_target_and_keeps_history`、`test_restore_refuses_target_filled_while_the_copy_runs`（staging 断言段） | 同上 | passed |

### SWR-2 owner / prune

| 原子断言 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|
| 自洽外来 manifest（空 files）不被 prune | `tests/test_swr_cases.py::test_swr2_foreign_self_consistent_manifest_is_never_pruned` | `logs/green_affected_batch.log` | passed |
| 外来 schema / `1.garbage` / name 不符 / 重复路径 / 越界路径 / 改 executor_side 全部跳过 | `tests/test_swr_backup.py::test_prune_skips_every_foreign_shape_even_when_the_digest_matches` | 同上 | passed |
| 损坏 / 未知 / 链接目录跳过 | `tests/test_swr_backup.py::test_prune_skips_damaged_unknown_and_linked_directories` | 同上 | passed |
| 旧无 owner 备份可只读 verify/restore 且**不**被 adopt | `tests/test_swr_backup.py::test_legacy_backup_without_owner_record_verifies_and_restores_but_is_never_pruned` | 同上 | passed |
| owner 登记由真实 create 流程写入 | `tests/test_swr_backup.py::test_owner_registry_records_the_create_flow` + `logs/golden/backup_owner_registry_ok.json` | 同上 | passed |
| prune 不删 owner 登记 / partial | `tests/test_swr_backup.py::test_prune_never_deletes_the_owner_registry_or_partial_directories` | 同上 | passed |
| WAL 已提交正例保留 | `tests/test_swr_cases.py::test_swr_wal_committed_pages_positive_keeps_passing`、`tests/test_quick_scan_backup.py::test_db05_wal_pages_missed_by_raw_copy_are_in_the_backup` | 同上 | passed |

### SWR-3 finalize / partial

| 原子断言 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|
| 注入 rename 失败不留可发布 partial，登记回滚 | `tests/test_swr_cases.py::test_swr3_failed_final_rename_never_leaves_publishable_partial`、`tests/test_swr_backup.py::test_failed_final_rename_is_reported_as_backup_failed_and_rolls_back_the_owner_record` | `logs/green_affected_batch.log` | passed |
| list 显式区分 partial/complete | `tests/test_swr_backup.py::test_list_marks_partial_and_complete_explicitly` | 同上 | passed |
| 复制期失败仍原子（原正例保留） | `tests/test_quick_scan_backup.py::test_create_is_atomic_on_failure` | 同上 | passed |
| 名称越界拒绝 | `tests/test_swr_backup.py::test_create_refuses_a_name_that_could_escape_the_backup_root` | 同上 | passed |

### SWR-4 可比边界

| 原子断言 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|
| 两个 subject 变体均可见 + `>=8` 不靠 9 入选 | `tests/test_swr_profiles.py::test_swr4_two_subjects_stay_visible_and_the_high_score_never_wins_a_condition` | `logs/green_affected_batch.log` | passed |
| 倒序导入仍取信息时点最新 | `tests/test_swr_profiles.py::test_swr4_reverse_order_import_keeps_the_newest_information_not_the_last_write` | 同上 | passed |
| 旧高分不掩盖新 unknown | `tests/test_swr_profiles.py::test_swr4_old_high_score_never_masks_a_newer_unknown` | 同上 | passed |
| 不同模型同题不混合 | `tests/test_swr_profiles.py::test_swr4_two_models_on_one_question_are_not_blended` | 同上 | passed |
| 同 issuer 多挂牌仍一行 | `tests/test_swr_profiles.py::test_swr4_one_issuer_with_two_listings_stays_one_row` | 同上 | passed |
| 同名不同 issuer 不并行 | `tests/test_swr_profiles.py::test_swr4_two_issuers_sharing_a_display_name_are_never_merged` | 同上 | passed |
| unknown / N/A / 缺 facts 语义不变 | `tests/test_swr_profiles.py::test_swr4_unknown_and_missing_facts_keep_their_original_meaning` | 同上 | passed |
| 公开 import 路径产生 synthetic subject 观察（不手造 profiles） | 上述用例均经 `import_package`；原场景同 | 同上 | passed |

### SWR-5 UI 多条件（真实浏览器）

| 原子断言 | 测试选择器 | 日志 / 截图 | 结果 |
|---|---|---|---|
| 静态护栏：不再单叶子硬编码 | `tests/test_swr_cases.py::test_swr5_browser_must_not_hard_code_a_single_condition_leaf` | `logs/green_affected_batch.log` | passed |
| 两条件 + AND 不命中 / OR 命中（LEAD 一项过一项不过） | `tests/test_e2e_quick_scan_ui.py::test_browser_two_conditions_add_remove_and_or_and_leaf_change` | `logs/green_e2e_browser.log`、`logs/screenshots/e2e-05-multi-condition.png` | passed |
| 请求体带完整 leaf+combine；改 leaf 后旧 snapshot 不再发送，新 snapshot 重新签发 | 同上（`ctx.search_bodies` 断言） | 同上 | passed |
| 条件可增删、最后一条不可删、reset 清空 | `tests/test_e2e_quick_scan_ui.py::test_browser_conditions_can_be_added_and_removed` | `logs/green_e2e_browser.log` | passed |
| 刷新 / 前进后退 / 详情返回保留全部条件与分页 | `tests/test_e2e_quick_scan_ui.py::test_browser_multi_condition_context_survives_reload_and_navigation` | `logs/screenshots/e2e-06-multi-condition-context.png` | passed |
| unknown 显示待核实、详情 `无分`，绝不补 5 | `tests/test_e2e_quick_scan_ui.py::test_browser_unknown_is_never_rendered_as_a_score_of_five` | `logs/green_e2e_browser.log` | passed |
| 变体明确展示（两个 subject 并排 + `多口径` 标记） | `tests/test_e2e_quick_scan_ui.py::test_browser_shows_both_imported_subject_variants_explicitly` | `logs/screenshots/e2e-07-variants.png` | passed |
| 恶意短文本安全呈现、不执行 | `tests/test_e2e_quick_scan_ui.py::test_browser_malicious_short_text_never_executes`（另有既有 `test_unknown_na_and_xss_entities_are_displayed_safely`） | `logs/green_e2e_browser.log` | passed |
| 浏览 0 外部请求、0 LLM、不写库 | `tests/test_e2e_quick_scan_ui.py::test_browsing_is_offline_and_never_writes` + fixture 的 loopback 断言 | `logs/green_e2e_browser.log`（`loopback HTTP only: N requests to ['127.0.0.1:…']`） | passed |

### SWR-6 快照兼容

| 原子断言 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|
| 无条件 hash 与旧 producer 逐字节相同 | `tests/test_swr_query.py::test_no_condition_query_hash_is_byte_identical_to_the_legacy_producer` | `logs/green_affected_batch.log` | passed |
| 当前无条件 snapshot == 旧 snapshot | `tests/test_swr_query.py::test_current_no_condition_snapshot_is_the_exact_legacy_snapshot` | 同上 | passed |
| page1→2→3 无丢无重 | `tests/test_swr_query.py::test_legacy_snapshot_pages_through_without_loss_or_duplication` | 同上 | passed |
| 错查询仍拒绝 | `tests/test_swr_query.py::test_legacy_snapshot_is_refused_for_a_different_query` | 同上 | passed |
| 带条件查询对旧 snapshot 仍拒绝 | `tests/test_swr_query.py::test_legacy_snapshot_is_refused_by_any_conditioned_query` | 同上 | passed |
| 多条件 snapshot 绑定每个 leaf + combine | `tests/test_swr_query.py::test_multi_condition_snapshot_binds_every_leaf_and_the_combine_operator` | 同上 | passed |
| 两种 hash 不碰撞 | `tests/test_swr_query.py::test_conditioned_and_plain_hashes_never_collide` | 同上 | passed |

## 原有回归（本包保留，未回写）

| 范围 | 选择器 | 日志 | 结果 |
|---|---|---|---|
| 备份/恢复/保留全套（DB-05/REV-04/STORE-03） | `tests/test_quick_scan_backup.py` | `logs/green_affected_batch.log` | passed（12） |
| 投影/条件/恢复 | `tests/test_quick_scan_profiles.py` | 同上 | passed |
| W09 查询层 | `tests/test_quick_scan_query.py` | 同上 | passed |
| HTTP 路由 | `tests/test_ui_quick_scan.py` | 同上 | passed |
| 本包新增集中用例 | `tests/test_swr_{cases,backup,profiles,query}.py` | 同上 | passed（36） |
| 受影响批次合计 | 上述 8 个文件 | `logs/green_affected_batch.log` | **passed 74 / failed 0 / skipped 0** |
| 真实浏览器 E2E | `tests/test_e2e_quick_scan_ui.py` | `logs/green_e2e_browser.log` | **passed 11 / failed 0 / skipped 0** |
| 全量门（本包 commit `9f9e0af`） | `python -B scripts/checks.py --full` | `logs/check_full_at_9f9e0af.log` | **passed 1032 / failed 0 / skipped 18**，exit 0，coverage 81%（诊断项） |
| 全量门（并行 narrative 提交合入后的合并树） | 同上 | `logs/check_full.log` | **passed 1046 / failed 0 / skipped 18**，exit 0，coverage 81%（诊断项） |
| 静态门 | `python -B scripts/checks.py --static-only` | `logs/check_static_only.log` | passed，exit 0 |

按施工卡要求，**没有**为每个小 hunk 重复原 990 套件；`--full` 只在交付时跑（因并行 worker 的无关提交合入而各跑一次，共 2 次）。

## not_run（不得伪造）

| 项 | 状态 | 说明 |
|---|---|---|
| TTL / 字段时效策略、replacement（W15） | not_run | `freshness_policy_available=false`、`GAP_REPLACEMENT_MAPPING` 仍为显式缺口 |
| 真实 QA C06 → W05 import/ACK → UI 整链 | not_run | 跨仓，归总控 G3 |
| 双库（跨 owner）恢复对账 | not_run | 归总控联合 E2E |
| F05 / 真实身份与事实 golden | **missing** | `logs/golden/identity_golden_status.json`；不合成 verified 填空 |
| G3 / F05 关闭 | not_run | 超出本包权限 |
| 独立审查（review） | not_run | 交总控派发；`handoff.json.review.status=not_run` |
| 原 990 逐 hunk 重跑 | not_run | 施工卡明确禁止；以一次 `--full` 代替 |
