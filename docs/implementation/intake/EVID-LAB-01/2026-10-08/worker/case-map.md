# EVID-LAB-01 case-map（任务case → 测试 → 日志 → 状态）

日志目录 `logs/`；命令均在 Lab 根执行。selector 为 pytest 真实测试名。

## 单元（施工卡“必须测试与交付·单元”）

| 卡内 case | 反例/要点 | 测试 selector | 日志 | 状态 |
|---|---|---|---|---|
| 有显式依据的矛盾能定位 | 期间/指标/单位/主体/方向/口径/角色 | `tests/test_semantic.py::test_period_contradiction_located_with_explicit_evidence`、`::test_every_dimension_contradiction_has_error_code`、`::test_metric_family_contradictions`、`::test_subject_conflict_and_multi_listing_tolerance`、`::test_direction_scope_role_conflicts` | `logs/final-regression-GREEN.log` | passed |
| 证据缺失/不可测正确 abstain | 缺期间/缺关系/缺正文 | `tests/test_semantic.py::test_missing_inputs_abstain_never_guess`、`::test_circular_and_paraphrase_sources_fail_only_with_explicit_relations`、`tests/test_diagnostics_and_review.py::test_semantic_dimensions_abstain_on_archives` | 同上 | passed |
| unit 缩放不误判 | 50%≡0.5、亿/万换算 | `tests/test_semantic.py::test_unit_scaling_is_never_misjudged` | 同上 | passed |
| unknown 有错 claim 仍被诊断 | 未知态+期间冲突 | `tests/test_semantic.py::test_unknown_status_claim_contradiction_is_still_diagnosed`、fixture `FX-027` | 同上 | passed |
| fixture 覆盖≥30与来源分层 | 错主体/同名/多挂牌/期间单位/错误引用题ID/duplicate JSON/缺snippet/缺usage/套餐未知/温度偏差/循环/高分弱证据/未知态claim | `tests/test_fixtures.py::test_catalog_validates_with_all_categories`、`::test_required_fault_shapes_are_covered` | `logs/validate-fixtures.log` | passed |

## 集成（施工卡“必须测试与交付·集成”）

| 卡内 case | 测试 selector | 日志 | 状态 |
|---|---|---|---|
| 真实历史归档 hash/分母重算一致 | `tests/test_stats_recompute.py::test_published_matrix_recomputed_exactly`、`::test_answer_denominators_never_mix`、`::test_request_summary_success_failure_unknown` | `logs/final-regression-GREEN.log` | passed |
| 缺 usage/标签 → 明确失败 | `tests/test_diagnostics_and_review.py::test_scored_answers_without_gold_abstain_or_label`（177 fail/53 abstain） | 同上 | passed |
| 重复 ID 明确失败 | `tests/test_stats_recompute.py::test_duplicate_chunk_id_fails`、`tests/test_semantic.py`（fixture `FX-021` duplicate JSON、`FX-020` 错题ID） | 同上 | passed |
| 原件篡改明确失败 | `tests/test_inputs_verification.py::test_tampered_bytes_report_mismatch`、`::test_missing_bound_file_fails_closed`、`tests/test_stats_recompute.py::test_tampered_archive_bytes_fail` | 同上 | passed |
| 两个 review 分区不当 inter-rater gold | `tests/test_diagnostics_and_review.py::test_join_recomputed_and_partitions_not_gold`（196/130 互斥、`inter_rater_calibration=not_measured`、`not_human_or_world_gold=true`） | 同上 | passed |

## 离线 CLI E2E（施工卡“必须测试与交付·离线CLI E2E”）

| 卡内 case | 测试 selector | 日志 | 状态 |
|---|---|---|---|
| 三真实归档只读重放 | `tests/test_cli_e2e.py::test_replay_index_twice_is_stable_and_readonly` | `logs/replay-index-stdout.log`、`logs/final-regression-GREEN.log` | passed |
| 新输出 exclusive | `::test_output_directory_is_exclusive`、`::test_output_outside_lab_root_refused` | 同上 | passed |
| 错误后环境恢复 | `::test_output_directory_is_exclusive`（失败后文件清单不变）、`::test_unlocked_index_fails_before_write` | 同上 | passed |
| 第二次新根统计稳定 | `::test_replay_index_twice_is_stable_and_readonly`（payload 字节相同） | 同上 | passed |
| input hashes 不变 | 同上（`snapshot_input_hashes` 前后一致） | 同上 | passed |
| 网络/key读取/模型/付费 0 | 同上（summary environment 全 0）、`::test_network_guard_blocks_connections`、`::test_subprocess_replay_is_fully_offline` | 同上 | passed |

## 未执行（保持 not_run，留总控安排）

| 事项 | 状态 |
|---|---|
| 新真实搜索/模型实验（提案执行） | not_run（`execution_enabled=false`） |
| 人类 gold 校准 / inter-rater 校准 | not_run |
| 生产采用、发新字段到生产执行器 | not_run |
| 60家公司校准重新宣称 / L03 启动 | not_run（本包不涉及） |
| 总控联合验收（G3/F05 等） | not_run（worker 不自关） |
