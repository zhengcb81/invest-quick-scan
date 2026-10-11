# MATRIX-CASE-01：公司×时间×模型与版本演进案例

唯一工作目录 `C:/Users/郑曾波/Projects/iqs-comparison-case-lab`；编制时不存在。可新建独立仓，分支 `codex/matrix-case-01`。本包是W14/V02/V17/V18/U03/U04的资料支撑，不代实现这些owner算法，不关闭其门。

先读[共同规则](handoff-rules.md)、[输入锁](inputs.lock.json)、[模板](MATRIX-CASE-01.handoff.template.json)。IQS/StockWiki/StockQA及其他两新Lab只读；不写EVID/FACT，不等它们产出。CodeGraph/AGENTS、PWF和唯一writer按共同规则执行。

## 目标与已有输入

交付一套能让弱模型准确理解“哪些能比较、哪些只能并排看、哪些变化来自业务或口径”的固定案例和离线工具。只用锁中的标准输出、评分尺候选/定义、身份、字段时效及版本演进契约。当前评分尺未真实校准，当前query是锁中历史边界；不能据此声称跨行业总分有效或新查询已支持历史。

不改问题文字、ID、anchors、权重、scope、版本或发布指针，不生成正式Observation/ACK/ScanRecipe。新资料不是第二比较引擎；期望可比性由case作者解释，工具只核引用/元数据/内部矛盾，真正比较器由总控后续接入。

## 交付接口

建立封闭 `iqs.comparison_case/1.0.0` 与collection/validation-report schema。每例至少含：

- case_id、family、fixture_class=synthetic、原输入文件/字节SHA引用；人工短理由，不使用真实公司成绩。
- left/right的研究对象引用/修订、entity或security/segment范围、期间/basis、metric_id/题篮/题义hash、unit/currency、rubric和module release；缺失明确null，不能补造绑定。
- requested_provider/model与实际provider/model/revision分开；information_as_of、observed_at、run/attempt来源时点分开。
- comparison_axes；expected分开列 `numeric_comparability`（comparable/not_comparable/unknown）、reason_codes、必须保留的原值/unknown/N/A、允许或禁止的派生动作、缺口。
- evolution子块可选：前后组件ref、变化类别、原观察保持、预计新增字段/仅投影/须复扫/人工核对；为候选预期，非owner签发的impact plan。
- `owner_mapping_status=not_mapped`、`production_case_status=not_run`。不能有qualified/human_approved/已认证公司正例字段。

期望动作只用有限结构字段，不写可执行表达式。每个案例引用冻结question/metric；未知字段保持不支持，不靠自造owner field_id让schema绿。

## 必须案例（建议36—48个，覆盖优先，不追数量）

| family | 正常控制 | 必须反例/边界 |
| --- | --- | --- |
| M01同口径 | 同对象/期间/basis/题义/评分尺/单位，可做分项比较 | 公司经营与单证券、并表与单体、不同subject revision范围变化不能静默混并 |
| M02时间 | 同题时间轴原值并排，标业务变化与时效 | 年度vs半年、当期vs正常化、信息晚于cutoff、过期回答不得当当前分数 |
| M03模型 | 同一题/范围/时点的实际模型差异并排 | fallback实际模型不等于requested；模型不同不能不说明就平均/据默认顺位覆盖旧答 |
| M04单位 | 同单位、同币种且口径一致才数字对比 | 百分点vsratio、元vs万元、无汇率不得换算、自定义指标未登记不能自动对比 |
| M05缺失 | unknown/N/A/insufficient保留，完整/部分覆盖分母独立 | 缺题不能缩分母，unknown不改5或0，partial空不能说没有业务 |
| M06评分尺 | 旧分数保持，只有新投影可并排 | anchors/权重/篮子改变不能套旧阈值；同版本hash冲突必须拒绝 |
| M07模块演进 | 新增模块只带新增字段缺口，旧问题原字节/答案保持 | 退役只读；改题义需新版本；不能把纯投影变化说成公司变坏/要求全公司重问 |
| M08周期/恢复 | 当前指标差、优势高、修复证据unknown可共存 | 临时低谷不能由低利润分一刀删除；不可逆需求/资金耗尽风险仍显式保留，不自动给反转加分 |

每类至少一个正常控制和一个具有具体错误来源的反例；数据只synthetic，reason给买方解释，不能以expected_labels自证模型/金融真值。覆盖同issuer多挂牌而研究范围不同、同范围多挂牌不重复算公司，以及题义变化和模型变化分别归因。

## 实施与测试

1. 新仓最小初始化并固定base commit/PWF。核锁；列现有validator/口径可复用项，不复制计算器。
2. 先设计上述case和几条坏输入：错题义hash、相反scope、错单位、缺模型实际标签、未知被填5、重复case_id、未来schema、被替换的nested文件。正常同fixture先可读。
3. 实现 `python -B -X utf8 -m iqs_comparison_case_lab validate --input ... --inputs-lock ...`、`export --input ... --inputs-lock ... --output ...`。validate只检案例有效性；报告固定 `validation_scope=case_artifact_only`、`owner_execution=not_run`，不得输出产品通过/排名。export只写本包新目录并保留全部case，禁止删难例。
4. 表格/时间模型案例说明与schema一起交，旧1.0字节按公开入口可读取；未来变更保持case_id、原版本归档，语义变更具名升版。
5. 定向unit（引用/范围/日期/三值/版本）、integration（真实文件hash/导出拒覆盖）、公开CLI E2E（中文/空格路径、随机cwd、两次确定导出、失败零正式输出）。稳定候选一次完整相关回归与一次集中review。

单元测试不要重写比较算法；断言资料契约能保留不能比较的案例和未知，不能因数据“不可比”就拒绝它本身。字段形状合法但比较结论是not_comparable应正常收录。

## 交回与总控接入

产物 `content/comparison-cases.json`、schemas、可执行CLI/测试，交接 `docs/handoff/MATRIX-CASE-01/`。另交每family到现有MATRIX/EVO验收ID的映射和缺少的owner输入列表。按[共同规则](handoff-rules.md)留下原命令/日志/真实commit和清理证明。

总控后续将同一份案例接W14/V17实际公开入口和U03/U04。当前case校验不等于实际比较/时间轴/UI通过，未有owner入口就明确not_run，不伪造真实owner golden、不代改生产仓。
