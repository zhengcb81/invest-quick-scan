# SCORE-ANCHOR-02：24核心构念的买方评分标尺与盲评案例

独占工作目录 **C:/Users/郑曾波/Projects/iqs-score-anchor-lab**，分支 codex/score-anchor-02。先读[共同规则](common-rules.md)、[接口](integration-contract.md)、[锁](inputs.lock.json)、[范围](manifest.json)、[模板](SCORE-ANCHOR-02.handoff.template.json)。仅本包写，无另外两包前置。

## 为什么需要本包

现有每题1/5/10锚点与未校准评分尺能约束方向，但6、8、9分需要什么证据、哪些公司不能同尺比较仍需要买方解释。本包交评分标尺研究与盲评资料，填补“结构通过不代表判断准确”；不重做 MATRIX 的公司/时间/模型比较器、不重复 FIN/PRIMARY 财务核证、不赋真实公司金融gold分数。

优先读 questions/common.json、scoring-contexts.json、metric-registry.json、types/stages/diagnostics 模块、references/scoring.md、common-framework.md、durability-and-change-design.md、scoring-rubric schema与唯一未校准rubrel候选。保持原24核心题/anchors/权重/metric/diagnostic_only原字节；当前没有经金融校准的活动评分尺，不能给白名单默认8分阈值背书。

## 研究产物与严格界面

1. 主 content/anchor-study.json，protocol=iqs.score_anchor_study_candidate/1.0.0，24条records按common原顺序，每条严格 {record_id,construct_id,question_ref,fixture_class,owner_mapping_status,production_execution,evidence_requirements,interpolation_notes,context_adjustments,disqualifiers,falsifiers,case_refs,proposals}。record_id 前缀 SA02-；fixture_class=synthetic。
2. evidence_requirements 严格 {minimum_support,preferred_history,peer_basis,counterevidence,insufficient_rules}；interpolation_notes 数组 {score_band,proposed_interpretation,necessary_evidence,not_sufficient,relation_to_original_anchors}，至少覆盖2–4、6–7、8、9，score_band 为整数数组。只是候选解释，不更改原1/5/10；相邻区间出现无法合理区分时写 limitation，不捏造小数精度。
3. context_adjustments 数组 {company_type,stage,scope,basis,applicability,reason,required_evidence}，明确通用构念与类型replacement的可比性，银行存款/券商客户资金/保险负债/地产维护资本/未营收公司等不能按工业口径机械打低分。低信心和低质量分开。任何新anchor建议放proposals {proposal_id,target_ref,expected_old_sha256,candidate_text,semantic_change,history_impact}，不原地改题。
4. content/blind-cases.json 至少32个合成情景，覆盖24核心构念，每个case严格 {case_id,question_refs,fixture_class,owner_mapping_status,production_execution,as_of,subject_scope,period,basis,evidence_packet,information_state,expected,reasoning_note}，三项标记固定synthetic/not_mapped/not_run。evidence_packet 是短合成事实、有时点与反证，不能伪装公开来源。expected {status,proposed_score_interval,required_rationale_points,forbidden_inferences,review_status}；status=scorable_candidate|insufficient_evidence|not_applicable|conflicted，非scorable分数区间null，scorable可给1–10闭区间但review_status固定candidate_not_financially_accepted。这是供盲评讨论的合成oracle，不是正式Score或真实公司golden。
5. 必须同组配对：低谷且品牌/渠道优势在 vs不可逆替代；增长快但单位经济亏损 vs健康再投资；当前利润弱/正常化证据强 vs只靠管理层愿望；现金能跨周期 vs资金耗尽；高杠杆工业 vs银行业务负债；客户集中但强切换成本 vs客户可自由替换；收费收入稳定但证据未知 vs足够留存证据；估值/股价因素不能影响经营质量；缺信息/搜索不可用不得默认5；低分高置信与高分低置信独立。仅改变一个事实的paired case写reason，保持截止日/范围一致。
6. 杜邦和五力及恢复模块另交 content/diagnostic-usage.json：原题引用、方向、需要的numerator/denominator/期间/basis、如何解释但不重复加总24题、哪些情况下unknown/N/A、案例关联。不发明ROE/ROIC计算器、不把正常化想象当实际值。actual/verified_normalized/hypothesis三层不能互相覆盖。
7. content/blind-review-plan.md 给后续B01实际答案的盲评办法：先隐藏模型/搜索方案和速度费用，用同scope/cutoff题义核claim/反证，再判评分依据与不确定；客观事实正确性、主观区间一致性、拒答/覆盖率分别统计。两位审核不一致需保留分歧/裁决理由，不用多数模型答案当真值，不先按谁贵决定正确。经济学/速度只在准确性达标后比。

## 工具和验证

实现 `iqs_score_anchor_lab` validate/export，只核候选研究完整性/原题引用/状态区间/诊断作用层及输入锁，不自动推导金融分数。主≤4MiB、cases≤100、引用必须闭合；未来协议拒而非猜读。

TDD先RED：unknown给5、周期低谷被全题一刀低分、区间0/11/倒置、bool当分数、错类型替代题、诊断重复加权、scope/期间/题义偷变。Unit检全部24与状态/区间/作用层；integration使用冻结原manifest/metric/rubric校验接口（若不适配明确候选边界），测试保留旧anchors/hash和另发proposal；公开CLI E2E及清理按共同规则。一次集中候选买方审查和相关测试，不按每个分数设门。

## 交接与接线

交研究、盲例、诊断用法、盲评计划、提案、schema/工具/测试及共同handoff至 docs/handoff/SCORE-ANCHOR-02/。不修改 FIN 的90个 null，不把合成期望记为 accepted_score。总控在 C02 评分尺候选/原B01准确性大节点消费；是否发布新评分尺、跨行业可比和白名单阈值由总控结合真实实验/人工核证决定。
