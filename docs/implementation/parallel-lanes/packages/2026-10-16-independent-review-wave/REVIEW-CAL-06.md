# REVIEW-CAL-06：金融与证据评审的校准案例工具

唯一可写根`C:/Users/郑曾波/Projects/iqs-review-calibration-lab`，包`iqs_review_calibration`。读取[共同契约](integration-contract.md)、[接口](interface-spec.md)、[独审要求](independent-review.md)、模板及总控冻结consumer子集。全程离线，不依赖另两个新包；不看T4答案、模型/策略/成本或实际评审，不替主线做金融判定。

## 做什么

制作**至少48个有实质差别的synthetic校准case，至少12个成对反例**，以及接收独立评审标签、比较预期与漏判的薄工具。不是新金融判定引擎，不自动用关键词/多数票认定真实公司答案正确。基础题义/标准schema/metric registry/JUDGE标签/既有有限10标量参考只读；10标量不是所有公司gold，所有主观分数仍无唯一正确值。

每个case保留完整问题、锚点、候选答案或显式缺答、所需短证据、expected标签及详细理由。counterfactual/数值变换必须显式synthetic，source不是虚构“真实新披露”；不能把改变的Alphabet数字写回真实reference，不能借用CATL/CSC真实名称制造正例。允许纯合成公司/来源（`.invalid`且明确synthetic），不需要联网核源。

至少覆盖以下相互不同的family；优先“格式合法、数字看似正确、金融含义错误”的难例：

- OCF/FCF/全部capex/维护capex/营运资金前后；净利vs营业利润、Cloud收入vs利润，数值碰巧相同仍不等义。
- million/billion/币种/期间/合并vs分部/归母；期末余额vs期间流量，完整定义与否；已披露约数不冒充精确末位。
- 有source ID但命题不受支持；同源镜像不算独立；公司自述vs独立行为证据；复合句部分有据、冲突证据未处理。
- 收入增长不直接证明复购、议价权、ROI、份额或护城河；现金余额不单独证明压力偿债；框架协议不等于锁定收入。
- 暂时低谷/周期重启与永久损害分开；耐久优势与产业颠覆风险并存；过去增长不能充当未来第二曲线已证成功。
- 诚实不足、部分覆盖、真正充分、缺答四种不同标签；全部null不算高准确；有信息但给出过度自信8–10分的组合。

每个case可以有多个重要命题，不能只挑一个正确数字忽略错误结论。format-negative另外成组，不靠非法JSON冒充难的金融错误。expected由实际独立agent质疑/校正，不允许作者自己贴“专家gold”。争议可明确允许多个有理由的标签，但不得把所有结果都设可接受来获得100%。

## API及CLI

```python
def validate_casebook(casebook, *, questions, answer_schema, metric_registry,
                      reference, expected_context) -> dict: ...
def make_assignment(casebook, *, seed, expected_context) -> dict: ...
def score_calibration(casebook, imported_judgments, *, assignment, private_map,
                      expected_context) -> dict: ...
```

`make_assignment`返回`{public_assignment, private_map}`。公开包只用不泄露含义的匿名ID，保留完整问题/答案/证据和synthetic标记；不得含原case ID、family、pair ID、expected、理由、变换标签或“正确/负例”等提示性metadata。来源ID也不得暗示预期结论；匿名化不能改写实质内容。私有map另存，逐项绑定匿名ID与原case ID及问题/答案/证据指纹，并记录完整casebook、公开assignment的canonical SHA和映射指纹；不是公开评审输入，也不是现有JUDGE真实结果carrier。

`score_calibration`同时接收实际公开assignment、实际private_map和judgments，重算内容指纹，核对casebook→map→assignment→judgments绑定及一一对应，不能只相信judgments自报hash。错误map、内容替换、重复或外来ID拒绝；缺失显式计入未覆盖而不算正确。只比较实际输入labels与经过独审的synthetic expected，金融推断保持人工/agent判断，不另写自动语义scorer。可复用原standard_answers/JUDGE字段校验；原numeric reference无法判断的自然语义维度保持not_assessable，不为刷通过改原库。

CLI：`--version/--help`、`validate --inputs ... --casebook ...`、`assign --inputs ... --casebook ... --seed ... --output <新根>`、`compare --inputs ... --casebook ... --assignment ... --private-map ... --judgments ... --output <新根>`，共同锁/expected SHA参数均有。assign分别写`public/assignment.json`与`private/map.json`，评审者仅接收public；compare不得覆盖原assignment/map/labels。输出闭合schema、按family混淆/严重漏判/争议清单，不只一个总正确率。

## 实施与验收

先冻结case family/成对设计，写validators和薄工具，再完成全资料。单元反例覆盖答案结构合法但财务错、相同数值错定义/主体、引用无蕴含、同源计数、主观多解释、missing/duplicate/unknown case、wrong bundle hash、wrong private_map、assignment内容替换但自报原hash、匿名提示泄漏、合成标记缺失、expected泄漏、模型自报污染、非有限数/重复键/外跳/未知版本。必须显示成对样例只变一个关键含义仍被正确区分。

集成真用锁住的原validators；所有合法组原标准答案结构通过，但其financial verdict仍由expected/独立审查负责。用明确synthetic reviewer-label fixture跑compare，不能说真实LLM达到该准确率。公开CLI E2E validate→assign→compare，expected只在私有区，搬迁后稳定；篡改/缺输入/重复答/既有输出拒绝。禁网/secret隔离/清理同共同规范。

最终**独立审查agent须逐case全面审查expected、来源性质、金融语义、成对差异和工具行为**，不能仅抽查schema或跑测试。所有有效发现修复并复审通过，按独审文档留调用/round/fixes/final证明，再交`docs/handoff/REVIEW-CAL-06/`。仅一个整包节点；不逐case增人工审批。资格均false，synthetic校准结果不与真实准确率合并。
