# EVID-LAB-01残余整改卡：六处问题同批收口

唯一writer仍为原Lab harness，工作目录`C:/Users/郑曾波/Projects/iqs-evidence-lab`。沿用[EVID-LAB-01原卡](../../../parallel-lanes/packages/2026-10-07-wave2/EVID-LAB-01.md)的owner授权/共同规范及[第一轮整改卡](../remediation-2026-10-08.md)。总控本轮只读，不给自己或新writer扩外仓写授权。IQS/StockQA/StockWiki/company-wiki/安装镜像全部只读，不reset/clean他人改动，不创建remote，不联网、收费、下载或扩大样本。

## 接手前事实

代码结果`62fe8b2f51bf498d0925b65e998c7b0a4dba7192`（实改f5149b9+版本提交），最新交接HEAD `380cb496f30c72128c2cc8e3c88e36924f3c4f2c`，codex/evid-lab-01/总控收尾实际clean、无remote。结果后只有handoff/证据/PWF和工件生成器tools/make_artifacts.py，src/tests/fixtures未再改。**这是时点快照，开工重新核实际HEAD/status及活动writer，不按旧快照覆盖新内容。**

原81方法、总控原9反例、公开34fixture/42expectation/350记录、三归档双新根稳定及34逐fixture CLI全部通过。它们保留且无需重做。总控新增首5例2fail3pass、集中follow-up6例全fail，合为六处残余问题；前两缺口重复公共证明，不算11独立问题。[验收](acceptance.md)、[counterexamples输入/实际输出](../../../intake/EVID-LAB-01/2026-10-08-remediation/counterexamples/)、[执行结果](../../../intake/EVID-LAB-01/2026-10-08-remediation/verification/result.json)可直接读。

## 实现范围与标准

本批主要沿原授权`src/iqs_evidence_lab/semantic.py`、`hashing.py`、`fixtures.py`、`diagnostics.py`、必要fixture/diagnostic schema、现有tests及docs/handoff/EVID-LAB-01/进行最小改动。保留CLI0.2.0原子发布实现和全部旧RED/GREEN，不修改任何IQS固定题库、历史归档/答案或标签。需要原卡外文件/迁移/新不兼容生产接口时先报具体范围；当前六项没有这些需求。

### LR-01｜自定义期间不得假装一致（P1）

公开synthetic最小输入是custom同2026年，expected start/end=2026-01-01/2026-03-31，observed=2026-04-01/2026-06-30。当前replay exit0、semantic.period=pass，normalize_period只保留kind/year而丢日期。

**不要求增加完整日期分析功能。** 如果不支持custom起止，明确abstain/custom_period_not_supported；若支持，完整规范化起止并只比较双方明确提供的边界。缺起止或不支持的字段不得肯定一致。不改旧quarter/half/year冲突及缺year测试，不从关键词补年。加非重叠、相同、缺边界/未知形态正反例；不靠删除case或将kind偷换成full_year过关。

### LR-02｜缺历史答案指纹不能绕过绑定（P1）

复制FX032，删除provenance.answer_sha256，修改case.answer.score=1及rationale，保留原run/chunk/question_id/review/expect。当前公开replay exit0并发布为historical_model_output，故不是静态假设。

凡历史fixture中有case.answer，必须与锁定归档指定答案完整比较，不能由可选hash字段决定是否校验。按case形态在schema/加载及verifier中拒绝缺失/空/null/错误绑定；或者始终独立从原归档计算和比对，声明hash仅作额外校验。完整chunk复制同样逐复制字段绑定真实归档，保留“改答案和chunk selfhash仍拒”的GREEN。输出本次答案SHA只记录当前输入，不构成历史来源证明。

增加原历史正例、删hash+改答案、空/null绑定、答案身份不匹配、带/不带hash时篡改的公共CLI负例。合法metadata-only历史fixture可保持已声明边界，但无答案不能冒称保留了历史答案或fact gold。

### LR-03｜拒绝数字词法产生的非有限值（P1）

strict_loads只用parse_constant，1e400经float解析成inf。无answer/chunk的synthetic `expected.direction=1, observed.direction=1e400`通过schema，公开replay exit0，semantic.direction=pass；canonical答案hash防线不会触发，输出不携带原inf，因此发布重解析也不会拒。

在统一JSON入口拒绝解析后的非有限浮点，包括正/负指数溢出、嵌套object/array和JSONL行；保留重复键及NaN/Infinity拒绝。采用受控parse_float或等价验证，返回具名NonFiniteJSONError，公共fixture入口exit4且无最终输出/stage。不要仅在json.dumps关闭allow_nan或semantic.direction里打补丁；所有入口遵循同一规则。正常有限值、小数和合法整数保持，不要求引入未授权的全局数值范围政策。

### LR-04｜混合未知来源窗口不能判全部冲突（P2）

claim period=2026，来源A period=2025，来源B只有URL；当前删未知B后“usable全冲突”得到E_URL_WINDOW_CONFLICT。不能证明B也冲突，整体应abstain并指出缺窗口，可另外保留A的明确冲突诊断，不伪造B窗口。

覆盖全明确冲突→fail、一个明确匹配→不误判全部冲突、全未知→abstain、已冲突+未知→abstain；正常同报告比较列和无窗口原反例保持。URL独立来源数与片段窗口/内容hash仍分开，不因未知多给独立来源分。

### LR-05｜每条diagnostic保留真实来源类别（P2）

公共FX021的题包记录是synthetic，但structure.duplicate_json硬编码historical_model_output。用传入evidence_kind等统一来源映射，检查整个document所有记录，不只package子集。synthetic不能变成historical，agent_review_only不能变成human gold，real_source_snippet collected=false保持未收集。

加现FX021全部记录来源断言及对应historical/agent标签正例。旧原始报告不回写，新规则/工具版本与变更说明明确，使历史输出和本轮修正可按版本比较。

### LR-06｜草案费用必须与生成上限相同（P2 / 签核前）

generation.output_limit=10000，两模型费用公式按5000；使用已冻结官方价格快照和输入上限，Decimal重算模型参考上界0.82296 USD，超过0.48276及0.49。无需上网取新价格或执行实验：统一生成上限、每模型上限、formula、totals和Markdown，并测试实际generation上限进入公式。可以明确调整草案上限或上界，不能只改一处展示数字。

保持draft_not_signed/execution_enabled=false/live_not_run=true；300计划题槽、失败/未发送主分母、cached/套餐实际未知规则、unknown预约不自动重发保持。接收草案不等于预注册已签核。按现版本记录参数兼容/actual model revision缺口；不复制第二个budget/cache/HTTP实现，不重复Phase96矩阵。

顺带更正isolation.md旧225项为224次校验/127绑定路径/含lock128文件，“未读取他仓”为按输入锁只读IQS、未写他仓；不为文案另建审查节点。双hash104工件/84EOL已核对，保留真实口径，不全仓换行或把差异叫篡改。

## 一批TDD、版本及隔离

先固定本卡六项RED，复用[counterexample源码](followup_cases.py)及[首批GREEN边界](boundary_cases.py)；在Lab自己的获批test目录适配路径，owner计算/公共CLI保持真实。修后一次受影响回归+六项/必要正例、三归档公共重放、34fixture及版本/schema/标签验证，原发布重试/目标排他/归档篡改拒绝保持。无需每改一个helper再申请审查，也不重复收费/旧大矩阵。

旧总控harness固定绑定已删除的runs/evid-lab-remediation-2026-10-08-01与旧HEAD，仅用于复现说明，**不可原地重跑覆盖旧intake**。writer使用新独占根并设TMP/TEMP/TMPDIR、pytest basetemp及Python子进程guard。不要直接运行带输出的IQS原ROOT脚本；需要IQS旧工具仅在自有副本按锁原字节运行。

修改规则/工具版本和更新docs/interfaces/artifacts，确保新诊断能和旧结果区分；公共结构兼容的错误修复不必升级生产Observation。尽量复用原6组施工，不增加平行任务或改其他库接口。测试后严格核真实子进程终态、root归属、无link/junction/硬链、精确文件set/size/SHA；失败即停清理，不按mtime/pytest编号删共享TEMP，不自称恢复。总控本轮266文件已经清，只能证明本轮，不替代你原历史清理证据。

## 交回与签收

交新源码result commit（先commit再handoff）、当前HEAD/准确before-after状态及并发差异归属、版本/schema/rule、六项RED/GREEN命令日志、公共CLI结果、保留旧正例、严格清理回执和更新artifacts双字节。保留历史所有日志、旧数据和not_run，不创建remote、不写IQS PWF。

总控只验新受影响范围和实际归档一次集中大节点。原已确认的重算/原子发布继续有效；六项GREEN后可签本包有限工具范围。提案仍单独待签核，完整事实/人类gold、L02完整校准/G3/F05、TH/IN/L03和live不自动变绿；不因“所有测试过了”声称评分准确性已证明。
