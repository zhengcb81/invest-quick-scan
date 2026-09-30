# 评分与回答协议

## 3.1 metric与作用层

每次`compose`生成的manifest都固定`metric_contract_version`和逐题`question_metric_mappings`。映射来自题库元数据并由C02 `metric.schema.json`校验：质量、成长、估值分别使用`quality_core`、`growth_core`、`valuation_core`，杜邦、五力和恢复题只能是`diagnostic_only`。证券作用域与实体作用域在manifest中显式分离；估值题以及挂牌权利、流动性等确属证券层的问题可使用security scope，不能把一个挂牌地的结论套到同实体另一证券。类型替代题保留`replacement_for`对应的24个核心构念。旧manifest仍按其原`aggregation_policy`读取，不回写或重新解释历史分数。

`main_questions.json`只是通用题的兼容导出，题库模块和生成manifest才是权威来源；不得手工修改兼容导出来建立第二套metric映射。

## 单题

- 1—10 整数，越高越有利于持续经济回报。题目各自定义 1／5／10 锚点；2—4 和 6—9 按证据位置插值，不能机械把 5 当缺省答案。
- 5 代表“表现中等且证据足够”；不知道是 `insufficient_evidence`，不适用是 `not_applicable`，未实际联网是 `search_unavailable`。后三者的正式 score 均为 null。
- 核心判断至少有一个直接支持的可打开来源，原则上交叉核对关键数字和不利事项。记录来源标题、URL、发布日期、财务期间与其支持的 claim。只有搜索摘要而未确认原文时降低置信度并标待验证。
- 截止日是可得信息边界。不能将之后公布的数据倒填进历史画像；未来预测明确为推断。估值需要报价时间，财务题用最近适用期间并参考三至五年；周期企业尽量覆盖一个完整周期。过时信息不能冒充当前状态。
- 高分必须能说明独立证据、相对谁优秀、持续多久、哪项事实会使分数下降。近期股价、知名度、强叙事不是证据。每题同时考虑最强反证。
- 置信度与质量分开。低分也可高置信度；低置信度不能通过压低质量分来代替。

## 新标准与旧接口兼容

新标准见[标准输出](standard-output.md)，使用固定字段/typed metrics和执行回执；下面的description示意仅用于旧score/description接口，不作为新事实/比较输出的自由格式。

## 兼容 StockQAbyLLM

现有解析器只保留整数 `score` 和字符串 `description`，且不支持 null。导出题明确要求 description 是 **JSON 对象序列化后的字符串**，其中保存正式结果，外层只作传输兼容。

内层对象示意：

```json
{
  "id": "IQS_04",
  "status": "scored",
  "score": 6,
  "confidence": "medium",
  "rationale": "竞争允许合理回报，但新增供给限制提价。",
  "evidence": [
    {"claim": "支撑事实", "title": "真实来源标题", "url": "https://来源页面", "published_at": "YYYY-MM-DD", "period": "FY20XX"}
  ],
  "counterevidence": "最强不利事实或尚未发现的说明",
  "sensitivity": "什么变化会使评分下降",
  "metrics": {"指标名": "数值、单位、期间和口径；没有则空对象"}
}
```

外层 `score` 在有效评分时等于内层 score；非评分状态只能为兼容传输使用 5，description 内仍必须 `score:null`，这个 5 永不进入画像或平均分。这是对既有接口的明确兼容约定，不是把未知评价为中等。未来上游原生支持可空分数时应直接使用，不保留哑值。

`normalize` 仅接受符合 manifest 的精确问题文本、ID 和内层协议。原始回复、无法解析、上游报错或默认值保留为错误，不进行正则猜分。外层分数与内层不符直接拒绝，因而上游“全部写成5”的问题不会悄悄通过。

## 新 screening-1 协议

快扫执行必须显式运行`compose --answer-format screening-1`。该模式输出带稳定`question_id`的StockQA结构化JSON问题，并只接受`stockqa.quick_scan_result/1.0.0`执行结果；不得把它自动改写成旧版`accepted_ids`审核文件，也不能把`standard-1`观察输入伪装成旧`score/description`答案。screening-1内层`description`必须是JSON对象字符串，含`id/status/score/confidence/rationale/information_as_of/period_start/period_end/basis/evidence/counterevidence/sensitivity/metrics`；内外题目ID、状态和分数必须一致，非评分状态的分数为null。

导入器接收版本化screening bundle：`schema_version=invest-quick-scan.screening-import/1.0.0`、当前manifest的规范SHA-256、每个题目prompt的SHA-256，以及StockQA公共CLI原样输出。每题执行回执必须由StockQA公开结果带回其实际输入题目SHA-256，并与manifest prompt逐字节匹配；全量完成回执不能由本地bundle包装器伪造。导入会核对实体ID/名称、question ID、信息截止日、日期期间、可打开HTTP(S)来源、search receipt ID与唯一已完成搜索调用、最终attempt字段链和证据来源与该调用的绑定、执行模型与时间。任何回答自报`accepted_ids`、`search_verified`或高级check level都不会授权；内层出现自签字段会使该题不适用screening。来源、时间或执行回执不合格时仍保留`reported_score/reported_status`供排查，但正式screening `score`为空。

通过这些结构与执行校验的结果标`screening_checked`，对应C03的`screening_audited`级别，并在本导入结果中留下绑定entity/question/observation的本地检查回执。该分数可用于快筛比较；`formal_research_status`仍固定为`not_accepted`，不会写入StockWiki或替代正式证据接受。低置信度的分数保留为reported值但不参与汇总；N/A先按unknown保留在覆盖率分母中，只有独立审核后才能从分母剔除。

## 验证与覆盖率

模型不能自行证明执行过搜索，也不能自行批准自己的证据。运行者检查实际搜索配置／调用记录，以及每个来源是否支持 claim 后，另写审核文件：

```json
{
  "company": "与manifest完全相同的公司全名",
  "as_of": "2026-09-19",
  "search_verified": true,
  "search_basis": "实际提供商搜索执行记录的文件或请求标识；不填模型自述",
  "accepted_ids": ["IQS_04"]
}
```

审核文件是旧strict协议运行者的记录，不是加密证明。不要把上述示例当已验证结果。旧strict无审核时保留 `reported_score`，正式 score 为 null、状态为 review_pending；未审核的 N/A 也不能用来减少覆盖率分母。新screening-1不接收该文件，使用自己的执行/检查回执。

经审核的N/A从适用题分母剔除；未知、错误、缺题、待审核留在分母中。置信度low的评分可展示为初步观点，但正式score留空，不进入汇总。每维 `coverage = 已验证有效评分题数 / 适用评分题数`。另报全部已选问题（含可选诊断）的完整率，不能用少数高分掩盖重大空白。

## 汇总

默认先逐题画像，汇总是辅助。固定企业质量维度：商业模式20%、竞争优势20%、执行组织15%、财务质量20%、治理配置15%、风险韧性10%。这些是便于展示的启发式权重，未经回测验证，不代表收益预测模型。3.0的core-constructs-v1只在24核心构念及其类型替代题内等权；行业、阶段、属性题单列专题结果，不再混入核心均分。杜邦、五力与恢复诊断都不进入汇总。旧2.1的legacy-all-questions保留原规则，但不得与3.0接成可比趋势；这避免quick/full题数不同造成权重漂移。

每个维度至少 70% 适用题已有有效评分才显示维度均分；全部六个质量维度达到门槛且总体适用质量题覆盖率至少 80%，才按固定权重显示质量分，否则为 null 并列缺口，不跨维度重分配权重。成长机会与估值独立按同一 70% 门槛展示，不参与质量分。不同模板、成长阶段或模式的结果仅供各自画像，不能无校准跨行业排名。

质量综合分还要求三个关键核查全部通过：IQS_12财务真实性、IQS_13股东权益、IQS_16资金生存，及其类型替代题。已验证1—3分时记 `material_concern`；缺题、低置信度、证据不足、未审核甚至N/A均记 `unresolved`。任何一项存在这些状态，就将质量综合分置null，维度分和逐题证据仍展示；不跨问题平均掉重大损失风险。

1—3分的其他有效题也单列薄弱项。上述标记用于确定核查优先级，不自动等于卖出结论。没有买卖建议、仓位、目标价或精确预测的推导。

## 恢复观察与质量分独立

2.1版本另输出`recovery_watch`，规则和状态见[恢复观察](recovery-watch.md)。新增4道1—10分恢复诊断不进入任何维度均分；已验证的优势和恢复依据可在质量分低或为null时展示。原低分、关键风险、未审核状态保持不变，不把“可能反转”当成分数上调理由。

旧strict画像仍使用本页独立审核协议；screening-1可以为满足条件的有效答案填入screening score，但绝不设置正式深研接受。观察标记不使用reported_score绕过相应协议。公司既可质量白名单不通过，又在恢复观察中显示优势；资金不足、结构性受损或普通股难获益要与优势同时展示。进入质量白名单与保留研究线索是不同结果。
