# 标准事实、评分与执行回执

本地已提供事实题库1.0.0（61题）、评分题库3.0.0（222题）、标准观察1.0.0和离线编排/验证。它们不调用模型；StockQA原有解析路径尚须Q03/F02适配原生score/fact，不能用外层默认5分装载非评分事实。

## 题库和字段

[facts.json](../questions/facts.json)含24道通用事实题：业务分部、细分行业、产品、上游、下游、设备、材料、设备供应方、材料/服务供应方、客户、渠道、第一曲线、第二曲线、管理层、控制权、地区、收费、成本、资产、竞争者、监管、资金安排、里程碑、产业变化。另有8种类型、21个行业、6个生命周期及周期/恢复模块。quick保留优先项，full展开；事实单列，不进入评分。

每题有稳定field_id、固定允许关系、适用条件及返回条数上限。标准事实行包含名称/别名、已核实ID或null、关系/角色、商业化阶段、分部、有效期、短描述、typed metrics和evidence_ids。未知供应商留缺口，不能使用常见供应商填空；只有部分已知时标partial，不把上限截断的名单叫完整。第一/第二曲线属于可检验描述，没有新业务不强迫创造。

评分的metric_id独立于题目显示名称；construct_id用于24核心权重，comparison_role区分core/context/diagnostic，rubric_version标题义变更，scope区分entity/security。行业和阶段口径由[scoring-contexts.json](../questions/scoring-contexts.json)统一；subtype可选，未知细分不能挑最有利指标。8—10分须有机制/多期证据，未知不是5分，趋势与优势强度分开。

## 一条标准答案

答案内容由[answer-content.schema.json](../schemas/answer-content.schema.json)定义，禁止额外自由字段。必含question_id、response_kind、status、score（事实恒null）、summary、information_as_of、期间、basis、trend、confidence、metrics、items、evidence、counterevidence、watch_triggers、missing_fields和coverage。

scored只能使用1—10整数；answered用于事实。无证据或不适用不用假分数和虚构列表。metrics固定metric_id/value/unit/currency/期间/basis/definition/evidence_ids；percentage按百分点表示，例如12.5代表12.5%，ratio按倍数。常用指标ID/单位/定义由[metric-registry.json](../questions/metric-registry.json)统一；未登记指标只能用custom.*，保留原值但不自动数值比较。原始币种不得无汇率依据换算；不得将归母/集团、当前/正常化/压力口径混列。

来源仅保存链接、标题、发布时间和短claim；日期不明为null。item与metric逐条关联来源；schema的字数/数组上限防止保存大段正文，但不证明来源真实性，仍需证据审核。

执行层另外提供回执，不从模型回答里读取模型标签。`standard_answers.build_observations`要求回执匹配manifest SHA-256、实际prompt SHA-256及题目ID，保留run/scan/inputset/比较组、provider/请求模型/实际模型/revision、request/attempt、UTC时间与搜索回执引用。观察默认`evidence_review_status=unreviewed`；结构有效不自动变成StockWiki正式accepted。

[observation.schema.json](../schemas/observation.schema.json)以URN引用唯一答案schema；本地验证器只用本地registry，不联网获取schema。method_id同时指纹化口径/schema和具体题目定义，防止只改题面却沿用同一版本标签。observation_id是内容hash；相同回执重打包得到同ID，重新导入不更新observed_at。回答/来源/入库/审核各时间由各拥有者保存，不能互相替代。

## 离线命令

依赖在[requirements.txt](../requirements.txt)。现有评分兼容命令仍可用；标准模式使用以下入口（均不发网络请求）：

```powershell
python -X utf8 scripts/standard_answers.py validate-library
python -X utf8 scripts/question_sets.py compose --profile examples/profile.json --mode quick --answer-format standard-1 --out-dir runs/score-standard
python -X utf8 scripts/standard_answers.py compose-facts --profile examples/profile.json --mode quick --out-dir runs/fact-standard
python -X utf8 scripts/standard_answers.py build --manifest runs/score-standard/manifest.json --answers answers.json --receipts execution-receipts.json --output observations.json
python -X utf8 scripts/standard_answers.py compare --left left-observation.json --right right-observation.json --axis model --output comparison.json
```

编排仍输出StockQA既有`[{category, questions:[字符串]}]`格式，不实现第二套调用器。标准answers输入是`{question_id: 内容对象}`，receipts由StockQA提供；参考[样板](../examples/standard-output.json)中的完整manifest/answers/receipts与标准观察。真实build要求经身份拥有者确认的entity_id，证券题另要求security_id。示例全部为虚构，搜索回执是明确的离线fixture，不证明实际搜索。

旧normalize使用score/description和独立accepted_ids协议，继续保留其证据门槛；未携带执行回执的结果标legacy_unattributed，model/answered_at=null。不能补上当前时间和猜测模型以冒充完整历史。标准观察当前用于验证/交换和逐项比较；StockWiki的入库、批次快照、筛选和UI仍按实施包接线。

## 比较和快照

compare仅输出可比性、原因、两个原观察及可比差值，不合成多个模型的平均“真值”。同公司比较历史时模型/题义改变会阻止直接差分；模型比较要求显式comparison模式、共同输入集和比较组，正常fallback不满足这个条件。实际模型未知、低置信度、缺信息日期都标不可直接比较。

公司横向默认严格限定可比cohort与期间。不同口径仍能并排查看，但不自动排名。时间比较保留期间标签与方法，来源集变化另外标记；回溯扫描不是当时实际做过的研究。事实关系并排显示增删候选，不能将“这次没搜到”自动判为关系终止。StockWiki存储每次快照的观察引用以保证重放，不能每次查询只取当前最新值拼成旧快照。

可直接阅读的[样板回答](sample-answer.md)展示字段与三种比较；JSON样板包含可重放的全部离线输入。

逐题执行/题包/尝试记录、并行及共享额度沿用[模型策略](model-policy.md)。观察只记录实际执行，不从配置顺位推测实际模型；混合模型的扫描必须逐字段标记。
