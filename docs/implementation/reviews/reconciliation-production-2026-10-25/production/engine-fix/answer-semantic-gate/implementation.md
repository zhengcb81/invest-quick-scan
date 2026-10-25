# 原标准答案语义门：生产共享执行复用，Company可组合接口

本包新增的是确定性语义检查，不是新的评分或来源资格。StockQA原validator没有改动。真实MiMo响应HTTP成功、与slot可精确同源匹配，但score题带3条fact items，不符合早已存在的IQS标准规则；不能清空items、改答案或放宽StockQA来宣称正式快扫完成。

## 根因和修复

原`standard_answers.validate_content`按原question的response_kind（默认score）判题：score禁止fact items和answered；fact不评分、成功必须有受限关系行；不可用状态禁止断言值；单位、metric命名、证据和截止日有确定性检查。Company先前只做schema/score-null/引用检查，漏了这些语义，错误把真实非法body记为completed；StockQA封存后来正确拒绝。

Company仅改`src/iqs_company_agent_lab/runner.py`，新增通用可选`answer_semantic_validator(answer_copy, question_id)`与`answer_semantic_rules`，冷启动与continue_from_checkpoint一致。旧研究不注入时保持原行为。回调仅判断，收到deepcopy且其修改会被拒绝；异常在原commit前转为既有invalid+answer_semantic_contract_rejected gap，保留修复空间，不增冻结状态枚举。

main原生产共享入口必须使用固定`_production_answer_semantics`/`_frozen_answer_semantics`，preflight/cold/resume/finalizer同门。工厂保留原task逐题完整question/cutoff快照，并把加载的原answer schema及metric registry的canonical JSON哈希与StockQA原冻结context比对，缺历史资源即拒绝，绝不静默用当前题库替换。真正的判题调用原`standard_answers.validate_content`，没有复制另一套规则。finalizer在原native matching/lease restoration/持久化前先做同样检查，错误为finalization_standard_answer_contract_requires_repair。

`question_prompts.py`仅新增独立typed_semantic_rules；原standard_prompt及renderer fingerprint涵盖的函数不变。生产新请求将score.items=[]/禁止answered、fact.score=null/禁止scored等规则插入原stable_prefix，并重新计算/校验SHA；完整原题对象保持不变。`renderer-compatibility.json`证明HEAD旧renderer与当前renderer规则fingerprint同为6b221598394f5c23a5f724c0b9bac895bcb44eee87c9189285eb605a6ebf21fe，未改旧冻结题面。新请求规则与源码需要纳入新执行pins，不能覆盖旧冷启动谱系。

## TDD、审查与实际边界

先留11项RED（缺原语义工厂/回调接口/typed rules）。第一次绿相46P/1F仅旧invalid-input guard优先级改变，已恢复原fresh_observer检查先行，再做语义资源检查。新增实际request捕获后12新用例+原finalization18+原engine18=48P/5.59秒。Company写入时曾仅换行变为CRLF，提交前恢复原HEAD LF；`company-line-endings.json`证明精确字节重构，diff从整文件噪声缩为33+/1-。最终LF字节48P/5.35秒，见final-lf.xml/.txt，8源SHA在测试前后不变（final-sources.json、cleanup-final.json）。旧字节/结果独立保留，不冒称raw SHA相同。没有重跑649秒E2E。

独立agent fix_bank21另行读码并以真实task-bundle/context/原body核验：旧输出被同一原规则正确拒绝，body/DB未变，新stable规则明确items=[]；原始独审证据由其留在engine-review，随后仅补Company LF精确等价绑定。

`real-readonly-rejection.json`读取实际原body与原context，保留精确拒绝理由score answer must use score/metrics, not fact rows；数据库SHA前后相同，CP/standard/delivery均不存在，不含答案正文/思考。它和上一native-bare-answer包的同源全等证明并不矛盾：**与原响应匹配不等于答案符合标准，更不等于金融正确。** root须通过原显式失败修答/新generation路线获取新合法样本，原safe输出、费用、receipt与不成功结论保留，不能自动重发或手工修改模型回答。

全部测试只用原离线规则和合成数据；TEMP/TMP/pytest临时根固定自有C:/Temp/iqs-sem25-*并自动清理，cleanup-final.json有精确目录/移除证明。实际诊断0API、0生产库写。root负责PWF、提交和推送；本子任务不操作这些文件或远端。

## v2：真实原生来源与截止日也在生产完成之前校验

v1 只补 IQS 题型语义仍不完整：格式合格的引用可能不属于这次真实检索，不能仅由实验 driver 标注失败而由生产 Runner 记 completed。因此 Company 接口明确版本：默认 version=1 继续兼容原两参数 callback；生产注入 version=2，额外只读传入当前 `_apply_answers` 的原生 attempt_ref 和当时 Runner 实际 EvidenceBoard 深拷贝。回调变更 answer/board 会被拒绝；不猜 latest attempt，不用构造的空 board 代替真实板。

main v2 先调冻结原题/原 registry/schema 的 v1 规则，再用同一精确 ref 调原 `OwnerResearchServices.inspect_attempt`，核 saved safe/native receipt/唯一 work member；按 Runner 原 `check_citation_closure` 规则只在副本重放 canonical citation ID，并与原 safe 整对象严格比对。随后核原 observation context 等于冻结 context，读取当前 native member 的原 external_context_use proof，调用原 `project_quick_scan_search` 从真实 store/work 投影来源，再调用原 StockQA `validate_standard_answer` 校验来源、日期与完整元数据。没有新增或拼造 source_urls，没有授予 board 来源资格，没有放宽原 StockQA validator，没有 DB 写入。冷、恢复和 finalizer 复用同一 v2 门；封存使用已验证原 checkpoint 的 board。

新增 6 类定向反例/接口单元涵盖错误 ref、无原生来源、未来日期、v1 两参兼容、v2 精确当前 ref/board 传递、只读 callback。先留 `v2-red.xml` 6F/12 deselected，再 `v2-green.xml` 54P/6.78s；这些是原规则和合成 store/projection seam 的单元证据，不宣称真实来源正例或新的金融正确性。最终 8 源 SHA 见 `v2-sources.json`，测试自有短临时根清理见 `v2-cleanup.json`。独立审查见同轮 `engine-review/answer-source-gate-v2-final.json`/`.md`，审查将原 attempt/member/context/use/project/原 validator 链闭合，未发现放宽。未重跑大型实际软件 E2E，也未发任何新付费请求。

下一代真实 driver 的 crash86 必须发生在 **同一生产 v2 门通过之后**；不合格原 safe 保留并正常导出 invalid，不能算生产成功或重发修答。该闭环由后续 generation2 实测证明，本文不以离线单元代替实测。
