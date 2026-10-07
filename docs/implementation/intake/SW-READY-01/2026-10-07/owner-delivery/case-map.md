# SW-READY-01 case 映射

图例：结果列取 `passed / failed / skipped / not_run`（case 级 = 其全部已绑定原子断言的最差结果）。日志文件的原字节 SHA-256 见同目录 `artifacts.json`（`kind=log`/`kind=golden` 条目）。测试选择器为 pytest node id（在源仓根目录执行）。

## W12

### DB-05（fault/integration，owner=W12）
> “写入过程中通过受支持方式备份数据库/配置，再在空临时目录恢复；恢复后成员、观察、规则、检查与 dataset 可重现；不能仅复制运行中主 db 文件忽略 WAL。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| 在写事务期间备份得到一致快照（未提交行不进快照，提交后不丢） | `quick-scan-backup create` / `stockwiki.quick_scan_backup.create_backup` | `tests/test_quick_scan_backup.py::test_db05_open_writer_transaction_does_not_leak_into_snapshot` | `logs/GREEN-w12-backup.txt` | passed |
| WAL 中已提交页必须进快照，裸拷主文件会丢（反例对照） | 同上 + `shutil.copyfile` 反例 | `tests/test_quick_scan_backup.py::test_db05_wal_pages_missed_by_raw_copy_are_in_the_backup` | `logs/GREEN-w12-backup.txt` | passed |
| 空目录恢复后成员/观察/ACK/subject/历史完整可重现 | `quick-scan-backup restore` + `QuickScanStore.get_entity/member_history` | `tests/test_quick_scan_backup.py::test_db05_backup_restore_roundtrip_preserves_history` | `logs/GREEN-w12-backup.txt` | passed |
| 真实库隔离副本同样往返成功（真实数据验收） | 同上，副本取自真实 `data/quick_scan` | `tests/test_sw_ready_01_real_data.py::test_w12_backup_restore_roundtrip_on_isolated_real_copy` | `logs/GREEN-real-data-acceptance.txt` | passed |
| manifest/逐文件 hash/水位/恢复前置/执行侧拒绝收费齐全 | `create` stdout / manifest | `tests/test_quick_scan_backup.py::test_db05_backup_restore_roundtrip_preserves_history`（manifest 断言段）+ `logs/golden/backup_create_ok.json` | `logs/GREEN-w12-backup.txt`、`logs/golden/` | passed |

### REV-04（fault/review，owner=W12）
> “先备份并按受支持迁移/版本回退；不盲目删除库或覆盖后续数据；受影响任务重新验收。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| 目标非空拒绝恢复，既有数据不被覆盖 | `quick-scan-backup restore` | `tests/test_quick_scan_backup.py::test_restore_refuses_non_empty_target` + golden `backup_restore_nonempty_rejected.json` | `logs/GREEN-w12-backup.txt` | passed |
| 校验不过不写目标（篡改备份被拒） | `verify`/`restore` | `tests/test_quick_scan_backup.py::test_restore_refuses_backup_that_fails_verification` | `logs/GREEN-w12-backup.txt` | passed |
| 创建失败不留“看似成功”的半份备份 | `create`（注入复制失败） | `tests/test_quick_scan_backup.py::test_create_is_atomic_on_failure` | `logs/GREEN-w12-backup.txt` | passed |
| 保留策略只删自有已验证备份，不删权威历史 | `prune --keep` | `tests/test_quick_scan_backup.py::test_rev04_retention_only_removes_own_verified_backups` | `logs/GREEN-w12-backup.txt` | passed |
| 未知 schema / 改 manifest / 缺文件 / 多余文件全部拒绝 | `verify` | `tests/test_quick_scan_backup.py::test_verify_rejects_tamper_missing_and_unknown_schema`、`test_verify_rejects_tampered_manifest_body` + goldens（tampered/missing） | `logs/GREEN-w12-backup.txt` | passed |
| 名称越界拒绝（路径参数绑定授权工作区） | `create --name ../escape` 等 | `tests/test_quick_scan_backup.py::test_names_outside_the_workspace_backup_root_are_refused` | `logs/GREEN-w12-backup.txt` | passed |

### STORE-03（fault，owner=W12）
> “恢复两库到不同水位，存在已付费请求、未ACK结果和新观察；先重放安全交换数据和对账，保留新观察及费用；不能把旧备份余额当未花额度；不确定时停收费派发。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| 备份后新观察/ACK 造成水位差；恢复只到备份水位 | `create` → 新 `observation-import` → `restore` | `tests/test_quick_scan_backup.py::test_store03_watermark_gap_replay_is_idempotent_and_frozen` | `logs/GREEN-w12-backup.txt` | passed |
| 重放交换包只产生 `accepted/already_present`，无 conflict/rejected、无重复观察 | 同上（公开 `import_package` 重放） | 同上 | 同上 | passed |
| 恢复回执禁止恢复费用/付费派发，双库非原子、需对账（水位一致性条件写入 manifest） | `restore` 回执 `executor_side`/`reconciliation` | 同上 + `logs/golden/backup_restore_ok.json` | 同上、`logs/golden/` | passed |
| `store_id` 路径派生差异写入恢复前置（跨根恢复提示） | manifest `restore_preconditions` | `tests/test_quick_scan_backup.py::test_db05_backup_restore_roundtrip_preserves_history`（preconditions 断言） | `logs/GREEN-w12-backup.txt` | passed |

### LLM-08（owner=Q05，跨 owner）
> 只引用已有证据，本包不签收：厂商正文/凭据不落盘、答案不改执行策略。

- 结果：`not_run`（非本包 owner）。
- 本包相关引用证据：所有新代码 socket 禁网（`_no_network`/loopback guard）、`quick_scan_*` 不含下载/正文逻辑（`--full` 中既有 `test_quick_scan_observations::test_modules_stay_offline_and_append_only` 等回归 passed，日志 `logs/check_all_full.log`）。

## U01

### UI-02（negative/integration，owner=U01）
> “E1 有效8分、E2 null；`>8` E1 未命中、`>=8` E1 命中；E2 始终待核实而非合格；页面与接口一致；不调用 LLM。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| `>=8` 命中 E1、`>8` 未命中（三值可逆） | `POST /api/quickscan/search`（conditions） | `tests/test_quick_scan_profiles.py::test_search_score_conditions_are_three_valued_and_reversible` | `logs/GREEN-u01-u02-projection.txt` | passed |
| null/证据不足 E2 永远待核实（unknown，不进列表） | 同上 | 同上（unknown 计数与 `status_insufficient_evidence` 叶原因断言） | 同上 | passed |
| 浏览器同一规则：`命中137/未命中137/待核实…`、行内 `命中` 标记 | 真浏览器列表页 | `tests/test_e2e_quick_scan_ui.py::test_list_conditions_views_and_2000_entity_pagination` | `logs/GREEN-u01-u02-browser-e2e.txt`、`logs/e2e/e2e-01-list-2000.png` | passed |
| 页面与接口一致、不调用 LLM | HTTP 层同一函数 + 浏览器离线断言 | `tests/test_ui_quick_scan.py::test_search_conditions_and_views_agree_with_the_query_layer`、`tests/test_e2e_quick_scan_ui.py::test_browsing_is_offline_and_never_writes` | `logs/GREEN-u01-u02-http-routes.txt`、`logs/GREEN-u01-u02-browser-e2e.txt` | passed |

### UI-08（boundary/integration，owner=U01）
> “2000 实体、命中 137，50/50/37 三页无重复漏行、稳定并列键、更新提示刷新；单次≤100、不带全部题目依据；记录环境/耗时；0 LLM。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| 2000 实体 + 137 命中，50/50/37、137 个 entity_id 无重复/漏项、下一页末页禁用 | 真浏览器分页 | `tests/test_e2e_quick_scan_ui.py::test_list_conditions_views_and_2000_entity_pagination` | `logs/GREEN-u01-u02-browser-e2e.txt`（含耗时：种子 22.8s、条件+分页 4.9s） | passed |
| 每页 100 上限生效 | 同上（page-size=100） | 同上 | 同上 | passed |
| 快照冻结：并发导入新观察只提示刷新、总数与快照 id 不变、不静默混页 | `POST /api/quickscan/search`（snapshot 回传） | `tests/test_ui_quick_scan.py::test_snapshot_page_two_prompts_refresh_when_a_new_observation_lands` | `logs/GREEN-u01-u02-http-routes.txt` | passed |
| 不携带全部题目/依据（列表行为紧凑行，详情按需） | `rows[].score_fields` 紧凑投影 + detail on demand | `tests/test_ui_quick_scan.py::test_search_paginates_on_a_frozen_snapshot_without_duplicates` | `logs/GREEN-u01-u02-http-routes.txt` | passed |
| 0 LLM 请求（浏览路径） | 浏览器 + loopback guard + payload `llm_calls=0` | `tests/test_e2e_quick_scan_ui.py::test_browsing_is_offline_and_never_writes` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |

### UI-09（fault/integration，owner=U01）
> “保存筛选/第二页/详情链接；刷新、后退、复制链接；无结果公司/不存在实体/故障页；故障不伪装空股票池。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| 刷新后筛选保留（URL hash） | 真浏览器 `page.reload` | `tests/test_e2e_quick_scan_ui.py::test_narrow_viewport_keyboard_reload_and_back_keep_context` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |
| 后退返回详情且上下文仍在 | 浏览器 back | 同上 | 同上 | passed |
| 返回列表保留筛选与行 | `返回列表` 按钮 | `tests/test_e2e_quick_scan_ui.py::test_ticker_search_dedups_and_detail_shows_originals` | 同上 | passed |
| 稳定链接以 entity_id 定位（复制链接可直达） | `#/quickscan/entity/<id>?…` | 同上 + `test_browsing_is_offline_and_never_writes`（直接 URL 打开详情） | 同上 | passed |
| 无命中/字段缺失状态区分（不伪装空池） | `empty_reason` 渲染 | `tests/test_e2e_quick_scan_ui.py::test_list_conditions_views_and_2000_entity_pagination`（quality 视图 `字段缺失`） | 同上 | passed |
| 不存在实体 → 具名错误（HTTP 层） | `GET /api/quickscan/entity?entity_id=ENT_nope` | `tests/test_ui_quick_scan.py::test_coverage_exposes_field_catalog_and_entity_detail` | `logs/GREEN-u01-u02-http-routes.txt` | passed |
| 未知字段/超限页/坏算子 → 400 具名错误（HTTP 层） | `POST /api/quickscan/search` | `tests/test_ui_quick_scan.py::test_search_rejects_unknown_keys_and_oversized_pages` | 同上 | passed |
| 未知路由 404 | `GET /api/quickscan/nope` | `tests/test_ui_quick_scan.py::test_unknown_quickscan_routes_stay_404` | 同上 | passed |
| 故障可注入的**浏览器级**错误页（服务端读取故障注入） | — | — | — | **not_run**（浏览器故障注入未实现；错误状态由上两行 HTTP 反例覆盖，见 summary 未解项 3） |

### UI-13（boundary/integration，owner=U01）
> “别名按 Entity 去重；链接稳定指向 canonical entity_id 并保留返回上下文；不假设详情页已实现，不调用模型或下载。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| A/H 两地挂牌 → 一行、一个 entity_id | 搜索 `600745` | `tests/test_e2e_quick_scan_ui.py::test_ticker_search_dedups_and_detail_shows_originals` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |
| 别名可搜索且不产生重复行 | `search(text=别名)`（投影 `alias`） | `tests/test_quick_scan_profiles.py::test_projection_keeps_score_status_model_dates_versions_and_sources` | `logs/GREEN-u01-u02-projection.txt` | passed |
| 链接/行以 `data-entity-id` 稳定定位 + 返回上下文 | DOM `data-entity-id`、hash | `tests/test_e2e_quick_scan_ui.py::test_narrow_viewport_keyboard_reload_and_back_keep_context` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |
| 不因名称合并歧义实体（同名 display 主体也分开） | 投影按 id 分组 | `tests/test_quick_scan_profiles.py::test_two_subjects_stay_distinct_and_legacy_subject_is_not_fabricated` | `logs/GREEN-u01-u02-projection.txt` | passed |
| 浏览 0 模型/0 下载 | 离线断言 | `tests/test_e2e_quick_scan_ui.py::test_browsing_is_offline_and_never_writes` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |

## U02

### UI-01（positive/integration，owner=U02）
> “E1 有 A/H/ADR 代码与中英文别名；E1 始终一行且导航到同 entity_id，全部挂牌可见；无 company 目录仍可浏览；查询路径模型/来源下载 0。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| 详情显示全部挂牌（600745+0700） | `GET /api/quickscan/entity` / 详情页 | `tests/test_e2e_quick_scan_ui.py::test_ticker_search_dedups_and_detail_shows_originals` | `logs/GREEN-u01-u02-browser-e2e.txt`、`logs/e2e/e2e-02-detail.png` | passed |
| 无 company 目录可浏览 | 详情页（fixture 无 `data/companies`） | `tests/test_e2e_quick_scan_ui.py::test_browsing_is_offline_and_never_writes` | 同上 | passed |
| 模型/来源下载 0 | loopback guard + `llm_calls/network_calls=0` + workspace 零写入 | 同上 + `tests/test_ui_quick_scan.py::test_browsing_performs_no_writes_and_no_offline_calls` | `logs/GREEN-u01-u02-browser-e2e.txt`、`logs/GREEN-u01-u02-http-routes.txt` | passed |
| 同发行人多上市公司行去重、别名保留 | 投影 `_entity_rows` | `tests/test_quick_scan_profiles.py::test_projection_keeps_score_status_model_dates_versions_and_sources` | `logs/GREEN-u01-u02-projection.txt` | passed |

### UI-03（negative/integration，owner=U02）
> “当前8分、过期8分、未知、不适用、低置信度；分别展示真实状态与日期；null 不填 0/5；N/A 不混同缺数；过期不默认入有效筛选；置信度与分数分列；信息日期与入库时间分列。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| 未知（证据不足）与 N/A 分开展示、不填 0/5 | 详情页 | `tests/test_e2e_quick_scan_ui.py::test_unknown_na_and_xss_entities_are_displayed_safely` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |
| 时效状态与 `有效期未记录` 明示（不冒充有效） | 详情页 + 投影 | 同上 + `tests/test_quick_scan_profiles.py::test_projection_keeps_score_status_model_dates_versions_and_sources` | 同上、`logs/GREEN-u01-u02-projection.txt` | passed |
| 已知过期（stale）不通过条件、不计入命中 | 条件求值（W07 `fresh` 位） | `tests/test_quick_scan_profiles.py::test_stale_score_never_counts_as_a_current_hit` | `logs/GREEN-u01-u02-projection.txt` | passed |
| 信息截止/信息日期/扫描/入库时间分列显示 | 详情行 | `tests/test_e2e_quick_scan_ui.py::test_ticker_search_dedups_and_detail_shows_originals`（时间行断言） + HTTP `test_coverage_exposes_field_catalog_and_entity_detail` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |
| 置信度与分数分列（confidence 独立展示） | 详情行 `confidence` | `tests/test_quick_scan_profiles.py::test_projection_keeps_score_status_model_dates_versions_and_sources`（confidence 字段） | `logs/GREEN-u01-u02-projection.txt` | passed |
| **真实过期观察在浏览器中的展示** | — | — | — | **not_run**（TTL 策略未接入、无合法可导入过期样本；stale 分支单元覆盖，见 summary 未解项 1） |

### UI-04（negative/integration，owner=U02）
> “E1 质量3分+恢复观察有效+流动性风险；E2 质量未知+恢复观察有效；全部公司与恢复观察可见 E1/E2；质量白名单按原规则不凭恢复标记放行；详情保留原分与风险。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| 全部公司视图含全部实体；恢复视图含已评估者；质量视图空（无已验证汇总） | 四视图 | `tests/test_quick_scan_profiles.py::test_quality_is_never_invented_and_original_low_scores_survive` + 浏览器 `test_list_conditions_views_and_2000_entity_pagination`（四视图切换） | `logs/GREEN-u01-u02-projection.txt`、`logs/GREEN-u01-u02-browser-e2e.txt` | passed |
| 质量白名单不凭恢复标记放行（`whitelist_eligible=false`、`quality_gate_overridden=false`） | W08 `company_card` | `tests/test_quick_scan_profiles.py::test_quality_is_never_invented_and_original_low_scores_survive` | `logs/GREEN-u01-u02-projection.txt` | passed |
| 详情保留原低分（`2 / 10`）与恢复状态/风险同屏 | 详情页 | `tests/test_e2e_quick_scan_ui.py::test_ticker_search_dedups_and_detail_shows_originals` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |
| 不把低谷描述换算成高分（不产生均分） | 投影 | 同上（`averaged_score_emitted=False`、`quality_score=None`） | 同上 | passed |
| 恢复信号（资金/结构风险标记）来自 W08 评估 | `evaluate_recovery_watch` | 同上（`recovery_watch.criteria/flags` 断言） | 同上 | passed |

### UI-05（positive/integration，owner=U02）
> “银行现金题替代：替代题显示对应关系不重复计入；每题显示分数/状态、短依据、日期、模型及版本；汇总复用已验证指标，诊断不混入质量均分，不生成万能总分。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| 每题显示分数/状态、短依据、日期、模型、题义/锚点/模板/发布包版本 | 详情分组表 | `tests/test_e2e_quick_scan_ui.py::test_ticker_search_dedups_and_detail_shows_originals` + HTTP `test_coverage_exposes_field_catalog_and_entity_detail` | `logs/GREEN-u01-u02-browser-e2e.txt`、`logs/GREEN-u01-u02-http-routes.txt` | passed |
| 诊断题独立分组，不混入质量均分、无万能总分 | 题族分组 + W08 | `tests/test_quick_scan_profiles.py::test_detail_groups_rows_and_states_capability_gaps`（diagnostics 组）、`test_quality_is_never_invented_and_original_low_scores_survive` | `logs/GREEN-u01-u02-projection.txt` | passed |
| 替代题对应关系显示且不重复计入 | W15 路由快照 | — | — | **not_run**（W15 未实现；详情显示缺口 `replacement_mapping_unavailable`，不编造对应关系） |

### UI-06（negative/integration，owner=U02）
> “短依据含 `<script>` 哨兵；来源含 https、javascript:、data:；配置密钥哨兵；文本转义、脚本不执行、仅安全 HTTP(S) 可跳转；页面/URL/前端持久化无密钥哨兵。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| `<script>` 哨兵以惰性文本呈现、不执行（无 dialog、`window.__pwned` 未定义） | 真浏览器详情 | `tests/test_e2e_quick_scan_ui.py::test_unknown_na_and_xss_entities_are_displayed_safely` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |
| `javascript:` 来源不渲染为链接；仅 http(s) href；合法来源保留 | 同上 + 投影过滤 | 同上 + `tests/test_quick_scan_profiles.py::test_projection_keeps_score_status_model_dates_versions_and_sources`（javascript: 被丢弃） | 同上、`logs/GREEN-u01-u02-projection.txt` | passed |
| 来源 `target=_blank rel=noopener`、不内嵌抓取 | 详情链接 | `tests/test_e2e_quick_scan_ui.py::test_ticker_search_dedups_and_detail_shows_originals` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |
| 浏览全程离开 localhost 的请求为 0（不探测外部来源/LLM） | 路由拦截器 | `tests/test_e2e_quick_scan_ui.py::test_browsing_is_offline_and_never_writes` + fixture teardown 断言（5 个 E2E 全部） | 同上 | passed |
| 页面/URL/前端持久化无密钥哨兵 | URL 只含筛选参数（hash）、无 localStorage 密钥；workspace 快照前后一致 | 同上（零写入断言覆盖前端持久化） | 同上 | passed |

### UI-14（negative/integration，owner=U02；requires U01）
> “评分结果已存在且 facts 未启用：评分/依据/来源/恢复标记可读；事实页明确 unavailable 不编造；纯浏览模型/搜索 0。”

| 原子断言 | 公开路径 | 测试选择器 | 日志 | 结果 |
|---|---|---|---|---|
| 评分/依据/来源/恢复可读 | 详情页 | `tests/test_e2e_quick_scan_ui.py::test_ticker_search_dedups_and_detail_shows_originals` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |
| 事实页 `unavailable`、不编造关系 | `查看上下游信息` 面板 | 同上（facts 面板断言） | 同上 | passed |
| capabilities 明示 facts=false | `GET /api/quickscan/capabilities` | `tests/test_ui_quick_scan.py::test_capabilities_declare_w09_protocol_not_c06` + golden | `logs/GREEN-u01-u02-http-routes.txt`、`logs/golden/` | passed |
| 纯浏览模型/搜索 0 | 离线断言 | `tests/test_e2e_quick_scan_ui.py::test_browsing_is_offline_and_never_writes` | `logs/GREEN-u01-u02-browser-e2e.txt` | passed |

## 跨 owner / 依赖（只引用，不签收）

| case / 门 | owner | 本包状态 | 引用证据 |
|---|---|---|---|
| G2（评分闭环审查） | iqs | 引用（已有交付依据，开工复查源码+回归） | `tests/test_quick_scan_rules.py`、`tests/test_quick_scan_recovery.py` 在 `--full` 通过（`logs/check_all_full.log`） |
| W05 观察导入（DB-02/03/06 等） | stockwiki（既有交付） | 引用：本包只读消费，未改导入路径 | `--full` 中 `tests/test_quick_scan_observations.py` 全绿（`logs/check_all_full.log`） |
| W09 查询（QUERY-01…03、ID-04） | stockwiki（既有交付） | 引用+加法扩展：原查询测试保持通过 | `tests/test_quick_scan_query.py` 11 passed（`logs/GREEN-u01-u02-projection.txt`） |
| W11 补扫（QUERY-04 等） | stockwiki（既有交付） | 引用：`quick_scan_refresh` 未改，回归通过 | `tests/test_quick_scan_refresh.py`（`logs/GREEN-u01-u02-projection.txt`） |
| W15 / F03–F05 / W14 / U03 / U04 / X / G3 | 各 owner | not_run（明确不在本包范围） | summary 未解项 |
