# EVID-LAB-01 case-map（原三层次 + 2026-10-08 六组整改 + 残余整改六项）

日志目录：原日志在 `logs/`（保留不动），整改日志在 `logs/remediation-2026-10-08/`，
**残余整改日志在 `logs/remaining-repairs-2026-10-08/`**（两批各自保留、互不覆盖）。
selector 为 pytest 真实测试名；命令均在 Lab 根执行。

## 残余整改六项（remaining-repairs-2026-10-08 → RED/GREEN）

总控2026-10-08验收裁决 `changes_requested` 后的同批收口；六项合为**六处残余问题**
（LR-01/LR-03 各有重复公共证明，不称11独立问题）。适配说明在测试文件头
（仅换输出根为 lab 独占 pytest temp root、FX021 诊断改为现回放产生；
断言、真实CLI与真实归档文件未改）。

| 组 | 卡内要求 | RED 证据 | GREEN selector | 日志 | 状态 |
|---|---|---|---|---|---|
| LR-01 custom期间 | 不支持起止就abstain，或完整规范化并只比双方明示边界；缺边界不得肯定一致；非重叠/相同/缺边界/未知正反例 | `test_custom_nonoverlapping_ranges_never_publish_consistency_pass`（公开replay `semantic.period=pass`）、`test_custom_explicit_date_ranges_cannot_be_called_equal`、`test_custom_identical_ranges_are_the_only_positive_shape` 3项失败 | 同名3项 + `tests/test_semantic.py` 原 quarter/half/缺year 用例不回归 | `logs/remaining-repairs-2026-10-08/RED-remaining-repairs.log`、`GREEN-remaining-repairs.log` | passed |
| LR-02 历史答案绑定 | 有 `case.answer` 必与锁定归档指定答案完整比较，不能由可选hash决定是否校验；空/null/缺失/错误绑定一律拒 | `test_missing_historical_answer_hash_cannot_authorize_tampered_answer` 失败（公开replay exit0并发布） | 同名 + `test_tampered_historical_answer_with_hash_still_rejected`、`test_empty_or_null_answer_binding_is_rejected[]/[None]`、`test_wrong_question_id_binding_is_rejected`、`test_original_historical_fixture_still_replays`、`test_answer_sha_alone_is_not_history_proof`、`tests/controller/test_controller_counterexamples.py::…test_historical_chunk_answer_tampering_rejected` | 同上 | passed |
| LR-03 非有限数 | 统一JSON入口拒解析后非有限浮点（正/负指数溢出、嵌套、JSONL），具名 `NonFiniteJSONError`，fixture入口exit4且无输出/stage | `test_numeric_overflow_is_not_an_admissible_finite_json_value`、`test_numeric_overflow_is_rejected_by_actual_fixture_replay` 2项失败 | 同名2项 + `test_normal_numbers_survive_the_strict_parser` + `tests/test_remediation_2026_10_08.py::test_strict_loads_rejects_non_finite_constants`（旧NaN/Inf反例保持） | 同上 | passed |
| LR-04 未知来源窗口 | 已冲突+存在未知窗口→abstain并指出缺窗口，不伪造未知窗口；全明确冲突仍fail、一个匹配不误判 | `test_unknown_source_window_does_not_mean_all_sources_conflict` 失败（实际 fail） | 同名 + `test_every_cited_window_conflicting_still_fails`、`test_one_matching_window_is_never_reported_as_all_conflicting`、`test_all_unknown_windows_abstain`、`test_same_report_comparison_columns_and_no_window_cases_stay` | 同上 | passed |
| LR-05 来源类别 | 用 `evidence_kind` 统一映射并检查整个document所有记录；synthetic≠historical、agent≠gold、未收集≠real_snippet | `test_every_synthetic_fx021_record_keeps_synthetic_source_type`、`test_source_kind_verifier_rejects_category_morphing` 2项失败 | 同名2项 + `test_historical_fixture_records_never_claim_synthetic`、`test_uncollected_real_source_fixture_never_claims_real_snippet`、`tests/test_remediation_2026_10_08.py::test_synthetic_structure_records_are_not_labeled_historical` 等原标签用例 | 同上 | passed |
| LR-06 草案费用 | 统一生成上限/每模型上限/formula/totals/Markdown，并测实际generation上限进入公式；保持 draft_not_signed 非执行 | `test_draft_reference_fee_upper_bound_covers_its_generation_cap` 失败（`5000 == 10000`） | 同名 + `tests/test_remediation_2026_10_08.py::test_preregistration_config_is_frozen_and_non_executable`（含 `output_cap == generation.output_limit` 断言） | 同上 | passed |

保留的首批GREEN边界（同文件内必须继续通过）：
`test_changing_both_retained_answer_and_self_hash_still_rejected`、
`test_final_rename_failure_cleans_staging_and_same_path_is_retryable`、
`test_target_created_during_publish_is_preserved_on_this_windows_host`。

- 本批 RED：**10 failed / 17 passed / 0 error** → GREEN：**27 passed**。
- 全量回归 `logs/remaining-repairs-2026-10-08/final-regression.log`：**108 passed**
  （原81 + 本批27）。
- `validate-fixtures.log`：34 fixtures / 42 expectations / 350 records，`problems=[]`。
- `public-cli-runs.json`：index×2 + 34 fixture = **36/36 exit0**、双根五payload字节一致、
  128个输入文件前后SHA不变、无staging残留、输出根已删。
- `cleanup-receipt-p<pid>.json`：本批全部 `gaps=[]`/`verified_absent=true`/无link。

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
