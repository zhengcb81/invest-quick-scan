# 新载体接口字段规范 1.0.0

这是必须落为 JSON Schema 和代码校验的字段契约；不是已实现软件。各包独立携带自己需要的 schema，不导入另一新包。共用契约的严格 JSON、日期、hash、路径和错误码同时适用。可为空字段须显式 null，不能缺字段暗示零。枚举外值/未知版本拒绝。下述 `sha` 为 64 位小写十六进制，`ref` 为 `{path,raw_sha256,bytes}`，日期 ISO YYYY-MM-DD，时钟 ISO UTC。字段集可在本卡边界内细化，但语义不能放宽；新增载体字段需明确 schema 新版本，不能静默接受。

## 经营资料包

`iqs.operating-reference/1.0.0` 顶层必须有：protocol、package_id、company_key、legal_issuer_name、entity_id、security_id、identity_state、research_as_of（固定2026-10-13）、base_question_as_of（取真实原题，不硬填13日）、bindings、sources、claims、dimensions、gaps、acquisition、qualification、content_sha256。bindings 至少 identity_dto/question_manifest/questions/base_financial_pack/base_calculation_ledger 的 ref，外加 trusted_context（company_key/entity_id/security_id/research_as_of/question canonical SHA），调用方 expected 与输入严格比对，不能从误传公司临时重算 expected 当验证。原财务父包有多公司，按 company_key 只读选择，不能修改或跨公司借值。

source 行字段：source_id、origin_group_id、url、publisher、title、publication_date、date_basis（明确页面日期原文的极短描述及定位，或 unknown）、accessed_at、source_kind（official_company/official_regulator/official_exchange/official_customer/third_party_candidate）、access_status（verified/unavailable/date_unknown/identity_uncertain）、bounded_paraphrase、paraphrase_sha256、eligible_by_research_cutoff、limitations。date_basis 不能用 accessed_at 替代 publication_date；未知/未来日期不 eligible。来源 date 早于或等于固定截止，且材料确实那时已公开，才可进入有效研究上下文；网页更新覆盖原内容不能凭旧 URL 日期推断历史正文。hash 只证明保留的有界片段，**不是**全文或 HTTP 真实性认证。

claim 行字段：claim_id、mechanism_id、question_ids、dimension_ids、statement、claim_kind（observed_fact/company_statement/third_party_view/inference）、business_scope、period_start、period_end、source_ids、support（direct/partial/proxy/missing/contradicted）、counterevidence_claim_ids、limits、falsifiers、unknowns、eligible_for_research_context、eligible_for_question_cutoff。每项必须有明确因果链“客户/交易→行为或约束→收入/成本机制”，推断写出 premise_claim_ids，不把结论反向当来源。falsifier 至少 `{observation,why_it_matters,verification_gap}`；无实证反例时写“尚未找到反证”，不能捏造负面事实。公司自述不能改 observed_fact；真实合同/客户案例不能外推全公司复购、收入锁定或 ROI。不得有 score/score_range/target_rating/golden_answer 字段。

dimension 行：dimension_id（`<question-id>:<stable-slug>:v1`）、question_id、required_proposition、existing_financial_refs、claim_ids、status、reason、remaining_gap_ids、eligible_for_question_cutoff。维度拆分由人工依题义提供，不靠关键词自动认定语义充分；程序只核引用、边界和计数。旧财务 reference 只是有限核过的候选，保留 partial/needs_revision、全分数 null 及任何母公司/币种/期间限制。财务事实最多在 existing_financial_refs 中通过 reference_id/fact_id 引用，不复制数值另建标量真值。

gap 行：gap_id、dimension_ids、question_id、needed_observation、why_unresolved、attempted_source_ids、next_verification、status（not_disclosed/not_found/inaccessible/conflicting/after_cutoff/identity_unresolved/out_of_scope）、eligible_to_claim_sufficient=false。没有资料可以输出空 claims/非空 gaps；不能为了通过测试要求新增正例而编造。

acquisition：query_count/page_open_count/new_source_count、query_log_ref、usage_status（known/partial/unknown）、known_cost_subtotal_usd（非负或null）、complete_cost_usd（未知null）、cost_basis（工具披露/unknown）；没有费用报告不能写0。qualification 固定 `{production_ready:false,financial_qualification_granted:false,rating_gold:false,source_review_status:"candidate"}`。

`iqs.operating-coverage/1.0.0` 顶层：protocol/package_id/company_key/research_as_of/base_question_as_of/input_refs/before/after/remaining_gaps/qualification/content_sha256。before 仅原财务引用边界，after 可加入合格经营 claim；两视图完整维度集合保持。每维输出 status/reason/claim_ids/source_ids/eligible_for_question_cutoff/sufficient。partial/proxy/missing/contradicted 一律 sufficient=false；direct 也须人工明确“仅此命题直接支持”，不得聚合成整题评分充分。报告无 accuracy/winner/score。将11日题包用于13日资料映射时，12–13日 source 不进入该题合格视图；research 视图可保留并单列 after_question_cutoff，不能静默重写题面。

## 离线实验桌面

新载体 `iqs.experiment-desk-manifest/1.0.0`：protocol、dataset_id、as_of、inputs_lock_raw_sha256、registrations、artifacts、schema_refs、join_policy_version（1.0.0）、privacy（public_only=true）、content_sha256。registration 行固定 company_key/entity_id/security_id/phase/strategy_id/repeat/model_id/endpoint_id/cohort_id/question_set_sha256/evidence_version/evidence_board_sha256/planned_session_id/planned_slot_ids；上游缺失字段用 null 与 missing_fields，不从文件名或最近相似记录猜。artifacts 每项 artifact_id/role（registration/result/events/judge/cache/claim/evidence/quality_review）/protocol/ref/subject_binding/visibility（public/aggregate_only）；不加载 private map、provider raw/hidden reasoning。只读 UI 可消费已解盲 aggregate，不自行解盲，不在盲评 public bundle 中显示模型身份。

`iqs.experiment-desk-view/1.0.0`：protocol/dataset_id/source_manifest_sha256/filters/rows/timeline/diagnostics/summary/content_sha256。row 主键是完整 subject binding + question_id + revision；保留 raw artifact_ref、input_sha、adapter_version。status 分列 execution（not_started/running/completed/failed/unknown）、answer（missing/invalid/valid）、quality（unreviewed/partial/sufficient/insufficient/conflicting/not_applicable）、financial_accuracy（number 或null且必须有显式合格判定依据）、claim_findings（计数/unknown）、evidence_status（原枚举/unknown）。不得把 valid→correct、null→0、结构完整→充分、reference存在→准确。独立review是来源声明，UI只展示不新判金融结论。

summary 显示 registered_slots/supplied_slots/legal_answers/missing_registered_slots/reviewed_slots/sufficient_slots；分母不同保留各自 label，不跨 phase/模型/证据版本混算。费用列 known_subtotal_usd/complete_cost_usd/cash_invoice_usd/unknown_receipts/reservation_usd，未有凭据均null或unknown，不把 reservation 加成实际账单。timeline 行 event_id/native_attempt_id/response_id/session_id/stage/timestamp/duration_ms/source_ref；缺时间不插补0、缺发送凭据不称HTTP失联，SDK step/native attempt/response/unknown dispatch 分列。重复回执以显式上游 identity 规则去重；相同id不同内容拒绝合并并诊断。排序稳定，未知时钟独立显示。

标准 CLI 行为：`validate` 验锁与明确载体，`build` 离线确定性派生到全新输出根，`serve` 仅启动本根派生包的 loopback GET/HEAD 服务。可有 `/healthz` 与只读 JSON 端点；POST/PUT/PATCH/DELETE 一律405，无上传/执行/模型/更新按钮。默认绑定127.0.0.1与随机空闲端口，不开放 LAN。静态资源全部本地，CSP 禁外联，来源文本用 textContent/等效转义，路径穿越拒绝。UI 内链接显示 URL 文本，可点击外部来源需用户主动操作且不自动 fetch。
