# SW-REPAIR-02｜六项闭合表 + 版本 / 旧 snapshot / owner 兼容说明

> 本文是**第一轮**（结果 commit `9f9e0af`）的闭合记录，逐字保留。
> 2026-10-08 **第二轮**（结果 commit `c83c148`，SR02-1..5 五组整改）见本目录
> `case-map.md` 的「第二轮 12 固定边界反例」章节、`summary.md` 的「第二轮整改」章节
> 与 `interfaces.md` §10；第一轮六项在第二轮的回归结果为 89 passed（未回退）。

- 基线（原冻结）：`master@04dfc5190589a8bbe224a47e94b045779c884b80`
- 本包结果：`master@9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f`
- 原冻结验收：7 场景 = **6 fail / 1 pass**（`acceptance_cases.py` sha256
  `72b2e1250947a705f87426557ccdf8b09121d761ba09ae89da3df152db81d452`）
- 修后同一批原文件（未改一个字节）对本包代码 = **7 pass**
  （`logs/frozen_acceptance_post_fix.log`）

## 六项闭合表

| ID | 不可妥协断言 | 关键实现 | 真实测试 selector | 日志 / 证据 | 结果 |
|---|---|---|---|---|---|
| SWR-1 | absent 与 existing-empty 恢复成功；非空/并发新文件/junction/越界拒绝；检查到空不授予删目录权限；失败保留原目标、仅清自己的 staging | `quick_scan_backup.restore_backup` + `_refuse_unusable_target`：目标与父目录链接拒绝、解析越界拒绝、非空拒绝在写任何字节之前；发布前**再检一次**；唯一会执行的目标操作是复检后的 `rmdir`（OS 对非空目录必拒），失败把原空目标建回；全程无 `rmtree(target)` | `tests/test_swr_cases.py::test_swr1_restore_accepts_already_existing_empty_target`；`tests/test_swr_backup.py::test_restore_into_absent_target_succeeds` / `test_restore_refuses_non_empty_target_and_keeps_history` / `test_restore_refuses_target_filled_while_the_copy_runs` / `test_restore_refuses_a_junction_target` / `test_restore_refuses_a_junction_in_the_data_parent` / `test_restore_target_resolving_outside_the_workspace_is_refused` / `test_restore_of_a_link_inside_the_backup_source_is_refused` | `logs/red_swr_cases_vs_base_commit.log`（RED）、`logs/green_affected_batch.log`、`logs/frozen_acceptance_post_fix.log` | **closed** |
| SWR-2 | prune 仅处理真实 create 流程登记的受管完成备份；版本/结构/hash/名称/路径安全 + trusted owner 记录均核验；仅 created_by 字符串、自算 digest、目录名不算 owner；foreign/unknown/partial/损坏/链接全部跳过；旧无 owner 备份只读 verify/restore、不自动 adopt | `quick_scan_backup_manifest.validate_manifest_shape`（冻结 `SUPPORTED_MANIFEST_SCHEMAS` + 严格三段 `format_version` + `name`↔目录名 + `files` 非空/唯一/安全 + `executor_side`/`consistency` 禁改）；`_verify_dir` 先结构后字节、并扫全部链接；`backups/quick_scan/owner_registry.json` 由 `create_backup` 在发布前登记 `name↔manifest_sha256`，改名失败回滚；`prune_backups` 四道闸 | `tests/test_swr_cases.py::test_swr2_foreign_self_consistent_manifest_is_never_pruned`；`tests/test_swr_backup.py::test_prune_skips_every_foreign_shape_even_when_the_digest_matches` / `test_prune_skips_damaged_unknown_and_linked_directories` / `test_legacy_backup_without_owner_record_verifies_and_restores_but_is_never_pruned` / `test_owner_registry_records_the_create_flow` / `test_prune_never_deletes_the_owner_registry_or_partial_directories` | 同上 | **closed** |
| SWR-3 | finalize rename 在错误处理内；注入失败不留可被 list/prune 当完成的 partial；manifest 成功字段不早于真实最终提交；崩溃恢复明确 partial 状态 | `create_backup`：copy → manifest（最后写）→ 结构复验 → **owner 登记** → `staging.rename(final)` 唯一提交点且在 `try/except` 内，失败回滚登记 + 清 staging；`list_quick_scan_backups` 显式输出 `partial` / `complete` | `tests/test_swr_cases.py::test_swr3_failed_final_rename_never_leaves_publishable_partial`；`tests/test_swr_backup.py::test_failed_final_rename_is_reported_as_backup_failed_and_rolls_back_the_owner_record` / `test_list_marks_partial_and_complete_explicitly` / `test_create_refuses_a_name_that_could_escape_the_backup_root` | 同上 | **closed** |
| SWR-4 | 两个 accepted 导入的不同 subject/scope/模型/语义变体均可见；未唯一选择时 ambiguous 或全展示；不取最近/最高/最后一条静默合并；`>=8` 不靠错误高分入选；同 issuer 多挂牌一行、不同 issuer 不并名 | `quick_scan_rows._variant_key`（subject+revision / scope+security+listing / 题义版本 / provider+model）+ `_select_variants`（组内按**信息时点**取新，不按 import 顺序）+ `_judgment_entry`（多组 → `status='ambiguous'`、`score=None`、`variants` 全列）；detail 侧 `groups` 保留每个变体原始分数并打 `ambiguous` | `tests/test_swr_cases.py::test_swr4_two_subjects_of_one_issuer_never_silently_collapse`；`tests/test_swr_profiles.py::test_swr4_two_subjects_stay_visible_and_the_high_score_never_wins_a_condition` / `..._reverse_order_import_keeps_the_newest_information_not_the_last_write` / `..._old_high_score_never_masks_a_newer_unknown` / `..._two_models_on_one_question_are_not_blended` / `..._one_issuer_with_two_listings_stays_one_row` / `..._two_issuers_sharing_a_display_name_are_never_merged` / `..._unknown_and_missing_facts_keep_their_original_meaning` | 同上 | **closed** |
| SWR-5 | UI 可增删至少两条分项条件，AND/OR 由 W07 同一服务器规则执行；query/snapshot 绑定完整 leaf+combine；真实浏览器“一项过、一项不过”：AND 不命中、OR 命中；改 leaf 失效旧 snapshot；unknown 不补 5 | `index.html` 用 `#qs-conditions` 容器替代单条硬编码；`app.js` 状态改为 `conditions[]`，`qsStateKey` 包含全部 leaf+combine，URL hash 用可重复 `c=<field>~<op>~<value>`；`qsPayload` 只提交叶子，评分仍在服务端 W07；`quick_scan_query` 补发 `score_condition_outcome`，detail 渲染每个变体与 `多口径` 标记 | `tests/test_swr_cases.py::test_swr5_browser_must_not_hard_code_a_single_condition_leaf`（静态护栏）；真实浏览器 `tests/test_e2e_quick_scan_ui.py::test_browser_two_conditions_add_remove_and_or_and_leaf_change` / `test_browser_conditions_can_be_added_and_removed` / `test_browser_multi_condition_context_survives_reload_and_navigation` / `test_browser_unknown_is_never_rendered_as_a_score_of_five` / `test_browser_shows_both_imported_subject_variants_explicitly` / `test_browser_malicious_short_text_never_executes` | `logs/green_e2e_browser.log`（含 `loopback HTTP only` 请求计数）、`logs/screenshots/e2e-05..07-*.png` | **closed** |
| SWR-6 | 旧 `9f552a67` 实际 snapshot 在新版本继续读 page2、IDs/顺序不丢不重；错查询/错条件 snapshot 仍拒绝；不放宽匹配换绿 | `quick_scan_query._query_hash`：无条件时返回旧 `{text,filters,view}` 口径；带条件时才追加 `conditions`+`combine`。两形态互斥，故旧 snapshot 与带条件查询（或反之）仍 `snapshot_query_mismatch` | `tests/test_swr_cases.py::test_swr6_real_legacy_public_snapshot_stays_readable_on_page2`；`tests/test_swr_query.py::test_no_condition_query_hash_is_byte_identical_to_the_legacy_producer` / `test_current_no_condition_snapshot_is_the_exact_legacy_snapshot` / `test_legacy_snapshot_pages_through_without_loss_or_duplication` / `test_legacy_snapshot_is_refused_for_a_different_query` / `test_legacy_snapshot_is_refused_by_any_conditioned_query` / `test_multi_condition_snapshot_binds_every_leaf_and_the_combine_operator` / `test_conditioned_and_plain_hashes_never_collide` | 同上 | **closed** |

保留的正例：`tests/test_swr_cases.py::test_swr_wal_committed_pages_positive_keeps_passing`
（WAL 已提交页进快照、快照回 `journal_mode=delete`、`verify` 通过）+ 原
`tests/test_quick_scan_backup.py` 全套。

## 原 / 新版本

| 对象 | 原（基线 `04dfc51`） | 新（`9f9e0af`） |
|---|---|---|
| manifest `format_version` | `1.0.0` | `1.0.0`（**未改**） |
| manifest `schema` | `stockwiki.quick_scan_backup_manifest/1.0.0` | 同（**未改**），但读取策略冻结为 `SUPPORTED_MANIFEST_SCHEMAS=(MANIFEST_SCHEMA,)` + 严格 `MAJOR.MINOR.PATCH` |
| manifest 新增字段 | — | 无新增；`name`/`files`/`executor_side`/`consistency` 等**从“写入”升级为“强校验”** |
| owner 登记 | 不存在 | `stockwiki.quick_scan_backup_owner_registry/1.0.0`（`backups/quick_scan/owner_registry.json`，新文件，用户单独授权） |
| `QUERY_RULES_VERSION` | `quick_scan_query/1.0.0` | `quick_scan_query/1.0.0`（**未改**） |
| snapshot 协议 | 隐式（无条件 hash 与带条件 hash 混用同一字段） | 显式 `quick_scan_query_snapshot/1.0.0`，两种互斥 hash 形态，见 `capabilities.snapshot_protocol` |
| `PROJECTION_VERSION` | `quick_scan_profiles/1.0.0` | `quick_scan_profiles/1.0.0`（**未改**）；语义新增：变体分组 + `status='ambiguous'` |
| UI 搜索 payload | `conditions` 恒为单叶子 | `conditions` 为完整叶子列表 + `condition_combine`；URL 用可重复 `c=` |

## 旧真实 snapshot（SWR-6）

旧 producer 由 Git 真实字节加载，**不手算 hash**：

```bash
git show 9f552a67:stockwiki/quick_scan_query.py
```

旧口径（原文件第 212-213 行）：

```python
def _query_hash(text, filters, view):
    return _canon_sha({"text": text, "filters": filters or {}, "view": view})
```

本包 `tests/test_swr_query.py` / `tests/test_swr_cases.py` 用
`importlib` 执行该文件得到 `legacy.search(...)` 的**真实** `snapshot`（含
`snapshot_id`、`query_hash`、`ordered_ids`），再交给当前 `search(...)`：

- 无条件查询：当前 `snapshot == 旧 snapshot`（逐字段相等），page1→2→3 覆盖
  101 个实体，`ordered_ids` 全程不丢不重，page4 `next_page is None`；
- 错查询（改 `text` / `filters` / `view`）：`snapshot_query_mismatch`；
- 任何带条件查询：`snapshot_query_mismatch`；
- 新多条件快照：改任一叶子、改 `combine`、删叶子、去掉 `conditions` 全部
  `snapshot_query_mismatch`。

旧 producer 字节：`legacy_quick_scan_query.py` bytes `20260`、sha256
`271b1ba2434123180d27a64437e3f14487d390ffb5c6276471e5302a06c0639a`
（记录在 `export-manifest.json`）。**旧对象含义未改，只是无条件口径被显式保留。**

## owner / 旧备份兼容说明（SWR-2）

| 备份形态 | `verify` | `restore` | `prune`（能否被删） | 依据 |
|---|---|---|---|---|
| 本包 create 流程产生，owner 登记存在且 digest 一致 | 通过 | 通过 | **可参与保留策略** | 四道闸全过 |
| 旧版本产生、结构完整但**没有** owner 登记 | 通过 | 通过 | **跳过（不删除、不 adopt）** | `test_legacy_backup_without_owner_record_verifies_and_restores_but_is_never_pruned` |
| 外来自洽 manifest（含空 `files`、外来 schema、`1.garbage`、`name` 不符、重复/越界路径、改写 `executor_side`） | 拒绝 | 拒绝 | 跳过 | `validate_manifest_shape` |
| 未知目录 / 损坏 JSON / symlink 或 junction | 拒绝 | 拒绝 | 跳过 | `_is_link` + `_load_manifest` |
| `.name.partial-<id>` 崩溃残留 | 名称即拒绝（`backup_name_invalid`） | 同左 | 跳过且 `list` 标 `partial=true` | `_is_partial_name` |

**证据边界（必须与实现一起阅读）**：`owner_registry.json` 是放在现有备份区内的
版本化溯源记录，由 `create_backup` 单向写入。它可以证明“该目录由本模块的
create 流程产生且可核验”，也使“只凭自算 digest / 目录名 / `created_by`
字符串就能被删”这条路走不通。它**不是签名、不是凭据**，也**不能**阻止一个
具有同样文件权限的本地恶意进程同时伪造目录与登记文件；本包不作此类宣称。
登记过程没有在投资库之外创建第二研究数据库，也没有改动 `data/quick_scan/`
下任何 sqlite（迁移：无）。

## 明确未完成（not_run，不能伪造）

- TTL / replacement 策略与 W15 replacement mapping：`not_run`
- 真实 QA C06 → W05 import/ACK → UI 整链、双库恢复：`not_run`
- F05 / 真实身份与事实 golden：**missing**（本包不合成 verified 填空）
- G3、F05 关闭：不在本包权限内
