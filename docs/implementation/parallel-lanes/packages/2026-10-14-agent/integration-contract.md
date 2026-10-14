# COMPANY-AGENT-01 研究端口与所有权

版本 `iqs.company-agent-research/1.0.0`；仅研究候选。实现必须补严格JSON Schema（所有对象additionalProperties=false，字段类型/枚举明确），未知版本拒绝。本文件是需实现的新Lab端口，**不是声称StockQA已经存在同名API**。真实适配只由总控在现有StockQA执行边界内接入。

## 边界

公司状态/策略属于本Lab；实际identity、准入、model/search调用、请求receipt、费用结算、重试/cooldown属于原运行时。策略只能提出intent，不能授予自己发送资格。研究事件是原运行时收据的只读投影，不得成为第二个费用或请求事实库。

研究task指定 `protocol, experiment_id, run_id, company_ref, information_cutoff, question_refs, evidence_epoch_ref, strategy_id, limits, runtime_profile_ref`。CompanyTask中的文件ref均为 `{path,bytes,sha256}` 相对输入根；运行时attempt/session引用另按原运行时协议，不冒充文件ref。company_ref所指原件须标 `synthetic` 或 `owner_public`，后者需要原生校验成功，不能由名称/ticker自行合成。question_refs所指target包含原question对象hash与模块/版本/题ID；不得用标题代替。limits来自冻结registration且只可更严。模型或顺位的secret不进入task。

## 候选端口（Python Protocol可等价实现）

`Strategy.next_action(public_state) -> ActionIntent`，策略枚举fixed3/free_agent/evidence_agent。

ActionIntent字段：`action_id:string, kind:model_step|search|read_evidence|patch_answers|finish, expected_state_sha256:64hex, question_ids:string[], payload:对应kind严格对象`。同run action_id唯一；重放不得新发物理请求。公共state只有本公司题/证据/已确认答案/公开缺口与剩余可用额度，不含hidden reasoning或评测gold。

`RuntimePort.model_step(intent) -> ModelReceipt`：运行时接受稳定前缀引用、动态指令、目标题ID、允许工具schema版本和opaque session_handle；验证实际模型/思考/输出上限后沿原client发送。Receipt包含 `runtime_attempt_ref, outcome, planned_model, actual_model, endpoint_profile_id, started_at_utc, ended_at_utc, final_content, tool_calls, usage, finish_reason, session_handle`。outcome枚举response_available/rejected/outcome_unknown；缺字段必须显式null且保留原因。final_content仅最终文本；tool_calls只含id/name/arguments。model_step不是任意HTTP入口。

`RuntimePort.search(intent) -> SearchReceipt`：intent含query、scope、cutoff、provider_profile_ref和最大短片段数/字符；receipt含原attempt_ref、实际provider/协议请求数、query计数、短证据对象refs、outcome与usage/费用引用。固定模型/搜索研究臂不允许透明fallback；生产比较臂须显式给顺位并保留原失败。

`RuntimePort.inspect_attempt(ref)`只查原收据；`RuntimePort.request_resume(ref)`请求原运行时决策，不自行删除unknown或改余额。SyntheticReplayPort实现这几个端口且默认禁网；receipt必须明确synthetic，不能套真实owner ID。live adapter不在本Lab施工范围。

多轮reasoning由运行时按provider协议仅在会话内存处理，策略拿opaque handle；缓存checkpoint不序列化handle背后的隐藏内容。重启失去session时创建新segment，从公开证据状态继续，记录previous_segment_id。不能删必需协议字段后照发旧history，也不能以保存思考正文换恢复便利。

## 证据、补丁与输出

EvidenceRecord必需字段：`evidence_id, issuer_ref, scope, period_start, period_end, unit, currency, accounting_basis, source_url, published_at, retrieved_at_utc, excerpt, excerpt_sha256, claim_kind, support_status, supersedes_id, limitations`。evidence_id、scope、source_url、excerpt为非空string，excerpt_sha256为正确的64hex，retrieved_at_utc为非空UTC；issuer_ref固定为与task.company_ref相同的三字段文件ref对象且原主体绑定必须有效，不可为null。period_start/end、unit、currency、accounting_basis、published_at允许string或null，未知时limitations必填原因；supersedes_id允许string或null。无主体/来源/原短片段不能建supported Evidence，应保留gap。claim_kind=fact|plan|management_claim|inference，support_status=unverified|supported|partial|conflict。excerpt短且保留表头/条件；schema上限按registration。source_url存在不自动支持结论；evidence表不能自行升级资格。其余枚举为string，limitations为string[]；非空period/date严格ISO，supersedes_id非空时须回指同run已有ID。

Patch payload含 `expected_answer_hashes:{qid:64hex|null}, replacements:[原answer_content完整对象], reason_codes:string[], evidence_epoch_sha256`。key集合必须与action.question_ids恰好相等，null仅原槽无答案时合法。修题不能修改其他槽；先全部验证后原子接受，保留旧版。score/status/evidence关系复用IQS语义检查，不靠新schema放宽。

最终ResearchRun顶层固定字段：`protocol, experiment_id, run_id, strategy_id, company_ref, information_cutoff, input_manifest_sha256, evidence_epoch_sha256, slots, event_refs, metrics_ref, limitations, qualification_granted`。qualification_granted恒false。slots按原题序，各恰含 `question_id, question_object_sha256, execution_status, answer, answer_revision, attempt_refs, gap_codes`。execution_status=completed|invalid|rejected|outcome_unknown|not_attempted；answer为原answer-content对象或null；completed允许不足证据状态，但不等于正确。其他状态不伪造unknown答案；盲评桥必须保留原槽分母。

events只记录意图/状态变化/耗时/安全摘要与原收据引用；不得落key、原始隐藏思考、HTTP Authorization、评测参考。最终内容若包含think标签或协议reasoning正文，按泄露/invalid处理并保留安全hash/错误码，不把全文写日志。被截断的回答保留invalid及attempt ref，不偷偷补成完整答复。

usage保持provider原字段（安全白名单sidecar）与归一化字段 `input_tokens, output_tokens, reasoning_tokens, cache_read_tokens, cache_write_tokens, cache_miss_tokens, reported_fields`，前六为非负整数或null；缺失不能推0。若reasoning已含output不重复计费；具体折算依对应价表版本。metrics含physical_model_http/search_query/search_protocol_http、各状态计数、token可观测分母、实际wall/request-duration-sum、费用币种及cash/plan/reference拆分。不能用generic默认单价充当实际账单。

## 冻结与搬迁

inputs.lock的repository/path/bytes/sha256定义原字节；snapshot_root只是当前运输地址，搬迁显式指定新根，同锁不重签。IQS与QA源码片段只用于合同和定位；不能视为完整runtime依赖。agent运行输入目录不含参考答案，即使offline测试fixtures为测试开发可见，真实研究进程也只挂载allowlist。研究者、评分者和策略调参进程分离。

BLIND-INPUT-04桥、FIN-PROVENANCE-03参考、CHAIN-VERIFY-04证据进入总控时各有独立版本/hash；本Lab只输出原格式及ref，不能消费“将来某包完成”当当前资格。总控在一次大节点验证真实端口接线与配对实验，所有源漂移通过差异提案处理，不直接复制覆盖源码。
