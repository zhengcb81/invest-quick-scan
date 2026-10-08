# EVID-LAB-01 case-map（原三层次 + 2026-10-08 六组整改）

日志目录：原日志在 `logs/`（保留不动），整改日志在 `logs/remediation-2026-10-08/`。
selector 为 pytest 真实测试名；命令均在 Lab 根执行。

## 整改六组（remediation-2026-10-08 → RED/GREEN）

| 组 | 卡内要求 | RED 证据 | GREEN selector | 日志 | 状态 |
|---|---|---|---|---|---|
| EL-01 period | dict保留quarter/half；Q1/Q4、H1/H2 fail；缺year abstain；字典/字符串互比、缺字段具体理由 | stash回HEAD：`test_quarter_dictionary_conflict`、`test_half_dictionary_conflict`、`test_missing_year_abstains` 失败 | `tests/controller/test_controller_counterexamples.py::AcceptanceCases::test_quarter_dictionary_conflict`、`::test_half_dictionary_conflict`、`::test_missing_year_abstains`；`tests/test_semantic.py::test_half_vs_annualized_and_quarter_conflicts` | `logs/remediation-2026-10-08/RED-controller-counterexamples.log`、`GREEN-controller-counterexamples.log` | passed |
| EL-02 URL窗口/来源计数 | 无窗口abstain；比较列不fail；仅claim目标与全部引用冲突才fail；URL去重与片段hash分离 | `test_missing_source_window_abstains`、`test_same_report_comparison_columns_not_conflict` 失败（RED同上） | 同名两反例 + `tests/test_semantic.py::test_missing_source_window_abstains_with_specific_reason`、`::test_claim_target_conflicting_with_every_cited_window_fails`、`::test_same_report_comparison_columns_are_not_conflict`、`::test_source_counts_dedupe_urls_separately_from_fragments`、`tests/test_fixtures.py::test_catalog_validates_with_all_categories`（FX-017改造） | 同上 | passed |
| EL-03 严格JSON/追溯 | 公共JSON入口重复键/非有限值检查；historical复制chunk/answer绑定原归档全字段+canonical hash | `test_duplicate_fixture_source_category_rejected`、`test_historical_chunk_answer_tampering_rejected` 失败（RED同上） | 两反例 + `tests/test_remediation_2026_10_08.py::test_strict_loads_rejects_duplicate_keys`、`::test_strict_loads_rejects_non_finite_constants`、`::test_read_json_uses_strict_parser`、`tests/test_stats_recompute.py::test_duplicate_chunk_id_fails`、`tests/test_fixtures.py::test_historical_fixtures_cite_locked_archives` | RED/GREEN 同上 + `final-regression.log` | passed |
| EL-04 原子发布 | 第二文件写盘失败不得留半成品；staging写齐校验后发布；失败清本次staging、已存在目标不变、可重试 | `test_io_failure_does_not_leave_partial_output` 失败（RED同上） | `tests/controller/...::test_io_failure_does_not_leave_partial_output`（含同路径重试断言）+ `tests/test_cli_e2e.py::test_output_directory_is_exclusive`、`::test_output_outside_lab_root_refused`、`::test_unlocked_index_fails_before_write` | RED/GREEN 同上 + `public-cli-runs.json` | passed |
| EL-05 提案冻结 | 300计划槽分层分母；answered-only仅条件指标；题组/query/24共享/context与表头约束/逐模型token上界公式/缓存key与revision缺口；unknown预约不自动重发；Phase96差异 | （静态独审问题，按卡实现后由冻结断言看守） | `tests/test_remediation_2026_10_08.py::test_plan_slots_main_denominator_stays_frozen_at_300`、`::test_not_sent_slots_never_disappear_from_the_main_denominator`、`::test_preregistration_config_is_frozen_and_non_executable` | `experiment-proposal.config.json`（execution_enabled=false）+ `final-regression.log` | passed |
| EL-06 元数据/口径 | fixture原字节input SHA、答案canonical SHA、expected/observed定位；类别/agent标签；224校验≠文件数；34/42/350；pyproject声明jsonschema；EOL双hash口径 | （与EL-03同批实现；标签/定位/SHA由新增断言看守） | `tests/test_remediation_2026_10_08.py::test_fixture_replay_records_input_and_answer_shas`、`::test_semantic_records_carry_expected_observed_field_locations`、`::test_source_window_records_locate_both_sides`、`::test_synthetic_structure_records_are_not_labeled_historical`、`::test_agent_review_labels_never_masquerade_as_historical_or_synthetic`、`::test_input_verification_counts_checks_and_distinct_files`、`::test_fixture_counts_match_delivered_snapshot` | `final-regression.log`、`interfaces.md`、`artifacts.json`（worktree+blob双hash） | passed |

总控冻结9反例：**RED 8失败/1通过（0 error）→ 现9/9通过**；通过项
`test_wrong_locked_file_rejected_by_public_cli` 保持通过（新增索引内容校验：
schema必须为 `mimo_pilot_delivery/1`，路径比较改 posix）。原反例逐字保留于
`tests/controller/acceptance_cases.frozen.py`，适配说明在适配版文件头。

## 原三层次（2026-10-07 交付，选择器仍有效）

| 层次 | case | selector | 日志 | 状态 |
|---|---|---|---|---|
| 单元 | 显式矛盾定位/正确abstain/unit缩放不误判/unknown带claim仍诊断 | `tests/test_semantic.py`（9个函数，含整改新增4个） | `logs/final-regression-GREEN.log`（原54）、`logs/remediation-2026-10-08/final-regression.log`（现81） | passed |
| 集成 | 归档hash/分母重算一致；缺usage/重复ID/原件篡改失败；两分区非gold | `tests/test_stats_recompute.py`、`tests/test_inputs_verification.py`、`tests/test_diagnostics_and_review.py`、`tests/test_recoverability.py` | 同上 | passed |
| 离线CLI E2E | 三归档只读重放、输出exclusive、错误恢复、双根稳定、hash不变、网络/key/付费0 | `tests/test_cli_e2e.py`（9个） | `logs/remediation-2026-10-08/replay-index-a.log`、`replay-index-b.log`、`public-cli-runs.json` | passed |
| fixture目录 | ≥30场景、三类分层、provenance回链、expectation全命中 | `tests/test_fixtures.py`（4个） | `logs/remediation-2026-10-08/validate-fixtures.log`（34/42/350, problems=[]） | passed |

## 分母与口径（保持原义）

- 输入锁：**224次SHA校验、127个不同路径、含lock共128个独立文件**（校验次数≠文件数）。
- 历史：186模型/24搜索/396契约有效回答/70独立重复/326评审/191 scored/14有限依据、
  48次温度偏差、53被拒包/264包内题不可测——全部保持原义。
- 新提案：60请求×5=**300计划槽**主分母（answered-only仅条件指标）。

## 未执行（保持 not_run，留总控）

新真实搜索/模型实验（含60/24草案执行、Phase96重跑）、人类gold/inter-rater校准、
真实来源短片段抓取、生产采用、L02/G3/F05关闭、总控集中回验。
