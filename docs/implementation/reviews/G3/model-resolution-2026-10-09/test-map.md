# 本批集中测试矩阵

本表是本次Q10大节点的要求，不是逐项额外审查门。受影响套件与一次集中独审即可；590项阶段GREEN之后，同批审查发现并实测了MR08六项RED与MR03一项RED，修订源码正在最后受影响套件验证。最终计数、执行SHA和批准以本批验收文档为准，不将重复运行相加成独立测试数。

| ID | 入口与反例 | 期望结果 |
|---|---|---|
| MR01 | 严格独立配置：未知key/版本、重复条目、controls、空值、通配、错protocol/provider | 配置拒绝；原v2无alias指纹保持；alias变更改变非秘密指纹 |
| MR02 | 三个native协议 sync/async，A→A与注册A→B，未注册A→B或任意C | 注册只放行B且actual原样；其余不成功；保留搜索证据与费用来源 |
| MR03 | route requested=A而POST准备C；同alias属于其他provider或协议 | 发送前拒；零HTTP／零新send意图或费用保留变动 |
| MR04 | 成功HTTP canonical JSON digest与sanitize receipt同事务落库 | 独立重启可读取actual与原receipt；原body／thoughts不落库 |
| MR05 | response/model/hash/requestID/attemptID伪造或正文冒充模型 | 不能借另一次response；checkpoint拒绝且无部分状态变更 |
| MR06 | 派发后更改alias许可或scope/provider、重新读取配置 | 仍只依据当次冻结许可；新配置不追认旧请求 |
| MR07 | schema1–7迁移到8；有旧exact checkpoint与旧裸attempt | 历史读兼容；不由requested回填actual，不补alias；失败迁移rollback |
| MR08 | PRIMARY拒→backup注册alias成功，两次格式修复不同response | requested和actual取最终真route／attempt；中间来源不能抢占最终checkpoint |
| MR09 | lease已过时／late response／persist失败／不明HTTP | 迟到证据可留；不checkpoint、不无脑fallback、不重复发送 |
| MR10 | actual未知ratecard；不同requested价 | actual未知保留费用预留，不填0／不按requested计价 |
| MR11 | 公开CLI cold注册alias→独立warm/seal取消HTTP | 包requested=A/resolved=B；恢复HTTP0、同包hash和scope/run/question不变 |
| MR12 | 已封包actual篡改后重签package SHA，prepare/supersede | durable重建仍拒，head/revision不变；公共wire格式不改 |
| MR13 | JR2/outbox/checkpoint/预算受影响旧回归 | 事前消费者绑定、旧ACK精确重放与未知态保护仍保持 |

合成alias和协议替身只证明软件边界，不声称厂商允许任何真实别名，也不替真实身份／关系gold或事实准确性。三市场公司实验、G3/F05和200家运行继续按原授权与门槛。

## 实际用例定位与证据口径

下面的方法名均在交付的StockQA源码测试中，最终字节会按snapshot固定；不是新增运行命令或另设批准门。

| ID | 主要直接用例 | 补充边界 |
|---|---|---|
| MR01 | `test_model_resolution.py`的`test_invalid_policy_cannot_authorize_even_an_exact_response`、`test_published_schema_matches_native_validation_for_scoped_mapping`、`test_model_resolution_length_boundary_matches_schema_and_durable_limit`；config的`test_absent_and_empty_aliases_preserve_the_original_policy_fingerprint` | 新许可max160；无真实厂商alias背书 |
| MR02 | client的`test_q10_native_protocols_share_exact_or_registered_resolution`，四provider/protocol配对×sync/async×四许可状态 | native矩阵用parsed payload替身；任意非映射C由helper直接反例覆盖 |
| MR03 | transport的`test_q10_route_model_mismatch_precedes_budget_reservation_and_post`；client的`test_q10_async_model_mutation_after_begin_cannot_change_frozen_http_request` | 后者真实await窗口RED后固定local；不宣称provider构造前未读取合成key |
| MR04 | store的`test_q10_response_insert_and_outcome_transition_are_one_transaction`、`test_q10_durable_response_stores_only_sanitized_receipt_and_http_json_digest`；transport的`test_q10_http_source_is_durable_with_or_without_work_and_without_usage` | canonical JSON SHA不是raw网络bytes；body不保存，thoughts丢弃由sanitize allowlist覆盖 |
| MR05 | store的`test_q10_changed_checkpoint_receipt_rolls_back_without_partial_answer`（含request_id）、`test_q10_durable_response_summary_tamper_fails_closed_on_restart`、`test_q10_new_exact_checkpoint_cannot_strip_durable_marker` | 不把六／七字段参数反例称为每种完整跨响应替换均实测 |
| MR06 | integration的`test_q10_next_run_alias_snapshot_stays_frozen_through_factory_and_http`、`test_q10_current_factory_config_cannot_register_alias_for_frozen_empty_route`；store的`test_q10_permission_changed_before_response_cannot_authorize_old_dispatch` | legacy after_question独立alias成功入口仅邻近覆盖；不是热读取新配置授权 |
| MR07 | store固定v1/v2、明确v4/v6/v7迁移；`test_q10_v7_migration_adds_empty_tables_without_backfilling_bare_attempt`、`test_q10_v7_exact_checkpoint_remains_readable_without_new_response_rows`、`test_q10_failed_v8_migration_rolls_back_original_v7_schema` | 起点3/5仅通过共同升级链经过；不得写七起点全直接实测；历史fixtures不是生产golden |
| MR08 | store的`test_q10_checkpoint_requires_final_attempt_without_downgrading_after_repair`（六phase）、`test_q10_latest_unregistered_response_cannot_downgrade_to_earlier_success`、`test_q10_checkpoint_read_cannot_rebind_to_intermediate_attempt`、`test_q10_latest_registered_repair_response_can_checkpoint`、`test_q10_unsent_repair_after_prior_response_remains_uncertain_without_replay`；transport的`test_q10_refused_primary_then_registered_backup_uses_final_attempt` | 正反例覆盖不同requested备用；已发未checkpoint且新repair仍prepared保持uncertain与费用预留，不重问；sync/async repair两attempt独立定位，旧exact历史不追溯 |
| MR09 | transport的`test_late_response_receipt_is_retained_but_never_accepted_or_failed_over`、`test_failure_to_persist_response_receipt_never_dispatches_backup`；sync/async provider的repair uncertain／persistence传播反例 | alias专属late仅通过共享exact路径邻近覆盖；无盲目第三POST |
| MR10 | cost的`test_q10_missing_actual_rate_card_never_uses_requested_price_or_zero`、`test_q10_resolved_rate_card_wins_when_requested_and_actual_have_different_prices`、`test_q10_unpriced_alias_actual_retains_budget_reservation_and_pauses_dispatch` | spent账面0不代表实际费用0；缺usage直接用真实`usage`字段断言 |
| MR11 | `test_qa_c06_02_subprocess_cli.py::test_q10_real_subprocess_alias_cold_then_independent_warm_and_seal` | 三独立CLI进程；seal前移除当前alias，原包bytes不变且0新增HTTP；不称真实公司或vendor联网E2E |
| MR12 | C06的`test_supersede_rejects_each_forged_complete_observation_field`（model_resolved）、`test_prepare_refuses_a_forged_complete_observation_before_any_head_exists`（started_at/model_resolved） | 重签hash仍拒，head/revision不变，公共wire格式保持 |
| MR13 | 既有q10_delivery／result_outbox／store／C06seal／transport／cost和原QA E2E回归 | 仅受影响14文件；不声称全仓、UI、真实双owner恢复、价格准确性或G3F05验收 |

原始RED、阶段GREEN、最终测试分别保存于`intake/G3/2026-10-09-model-resolution/verification/`不同label；没有原执行源的最初两轮不得补填后来源码当原证据。
