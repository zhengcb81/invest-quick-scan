# 固定交接接口：四个产物互不构成施工前置

本文件是总控接收接口1.0.0，原handoff保持1.0.0。以下业务协议均为Lab产物，不能自动发布为StockWiki/StockQA运行协议。缺值用null/unknown及reason，不猜字段；每份JSON都有protocol、input_lock_sha256、production_ready=false及limitations数组。

## TIME-SEMANTICS-30

产物：
- content/time-policy-catalog.json，protocol=iqs.temporal_policy_candidate/1.0.0。
- content/legacy-parity.json；content/time-casebook.json；schemas与integration/temporal-evolution.md。
- Python公开函数 assess_reuse(observation, question_policy, *, now_utc, information_cutoff, context, verification_verifier=None) -> dict。无I/O，真实clock由调用者显式给，不读浏览器今天；返回decision=reuse_candidate/refresh_required/not_assessable/not_applicable/blocked_context，reason_codes、actual_source_dates、policy_ref、legacy_equivalent、candidate_only=true。

catalog.entries每行必有question_id、field_id、module_id、question_kind=score/fact、knowledge_kind=market_sensitive/periodic_financial/structural/event_sensitive/mixed、required_clocks数组、policy_family、max_age_proposal_hours(nullable)、rationale、legacy_fallback、source_refs。字段来源明确；若一个问题混合多个时间，不能取一个最大日期掩盖旧数据。问卷集合从冻结catalog/facts派生，逐ID全覆盖、不硬编码数量。

time-casebook每例有case_id、synthetic、inputs、expected_decision、expected_reason_codes、rationale、oracle_kind，legacy差分必须调用冻结原实现；新proposal正例是明确合成，不是生产owner golden。

## ANSWER-AUDIT-30

产物content/audit-summary.json(protocol=iqs.live_answer_content_audit/1.0.0)、content/claims.json、content/sources.json、content/sample-verdicts.json、content/coverage.json及report.md。

sample-verdicts逐32个sample_id一行：observation_id、原question_semantic_sha256/module_package_id、original_status、date_semantics_status=consistent/ambiguous/contradicted/not_assessable、material_claim_ids、reasoning_status=consistent_with_bound_rubric/unsupported/rubric_unavailable/not_assessable、audit_status=supported/partially_supported/contradicted/not_assessable、rationale、source_refs、open_evidence_gaps。不输出新的公司分数，不把审计状态映射成买卖建议。

claims每例至多3个重要实质命题，原指针/有限原文、类型factual_numeric/factual_qualitative/judgment/absence_or_coverage、period/currency/unit/entity/security口径、原证据引用、独立核源和verdict。没有可核实命题时说明为什么，仍保留sample行和分母。sources记录原URL/最终URL、publisher、source_kind、published_at及precision/reason、实际read_at_utc、cutoff可得性、定位、bounded_excerpt、independence_group、支持/不支持范围、失败情况。时点未知保持未知，原答案中的URL声明不等于已读。

coverage给32总数、三市场/题族/原status/版本/审计状态的完整分母；模型输出完整性、事实支持率、可评分理由支持度分别报分子分母及不可评估数。若真值不足不评“准确率”。可修复的审计逻辑/错误引用必须修；真实资料缺口允许not_assessable而非造证据。

## IMPORT-PERF-30

产物bench/benchmark-summary.json(protocol=iqs.original_import_benchmark/1.0.0)、bench/raw-runs.json、bench/semantic-equivalence.json、integration/candidate.patch、integration/performance-design.md。候选可在本Lab baseline工作副本中实现，不直接编辑源仓。

每个measurement有scenario_id、dataset_kind=synthetic_native、packet_count、baseline_commit、candidate_source_manifest_sha256、runtime/hardware摘要、repetition、cold_or_warm、elapsed_ms、process_start_count、validation_call_counts、accepted/rejected/ACK counts、cleanup_ref、stdout/stderr hash。candidate_source_manifest_sha256只索引候选源码路径和原字节hash（清单不含自己、bench结果或未来handoff），最终payload C由外层handoff绑定，避免未来commit自指。至少1/3/33/36包、每组基线/候选3次，同机同数据同隔离条件，报告median和离散而非只挑最快值。

semantic-equivalence逐场景比较真实原导入/ACK结果及守卫。semantic_equivalence_passed与performance_improvement_observed分开；无加速不能声称生产提速。candidate.patch必须可应用到锁定基线，除候选优化外无清理/格式化全仓。

## RESULT-TRUST-30

产物src/result_trust_panel.js(ESM)、contracts/owner-field-map.json、fixtures/scenarios.json、demo/及integration/host-patch-proposal.md；业务protocol=iqs.result_trust_view/1.0.0。

export function renderResultTrustPanel({record, ownerState, onViewOriginal}) -> HTMLElement；export function describeResultTrust({record, ownerState}) -> {items, warnings, original_refs, unknown_fields}。record/ownerState遵循冻结原公开DTO的field-map，无新增生产required字段；调用者传原数据，组件不fetch/评分/重算新鲜度、不授予操作资格。onViewOriginal是只读原记录回调，缺引用时禁用，不猜新API。

field-map每行有source_component/source_path、source_protocol_version、meaning、nullable_behavior、display_role、conflict_behavior，opaque原值原样保留。UI展示生成日、信息截止、资料/指标时点、原freshness/签收/资格差异；缺项明确未提供，矛盾并列解释，不取“较新”覆盖。新字段未来可选显示，但当前缺字段必须兼容，不能假造verified_at。

## 共同兼容规则

总控按协议版本、input lock与实际artifact SHA消费，未知协议先拒/报not_supported，不猜版本。JSON自身schema required/nullable/enum清楚、additionalProperties=false；原owner opaque对象允许保留未知字段但不把保留当语义通过。原schema不改，proposal升级写显式版本/迁移/降级，旧结果不回写。

四条线只交自己的产物：TIME不核金融真值/造可信验证回执；ANSWER不定义生产TTL/新scorer；PERF不改判断/权限/ACK口径；RESULT不算资格/新鲜度或做第二套前后端。任何跨包建议写integration提案，由总控整合，不要求等待另包交付。
