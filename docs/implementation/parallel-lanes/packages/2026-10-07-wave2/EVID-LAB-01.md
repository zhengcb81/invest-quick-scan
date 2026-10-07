# EVID-LAB-01｜独立离线证据质量评测与下一轮实验设计

唯一工作目录：`C:/Users/郑曾波/Projects/iqs-evidence-lab`，本轮核对时未创建。用户授权该目录后新建独立Git源仓/`codex/evid-lab-01`分支；不创建remote/生产服务/数据库，不修改任何现有项目。先读[共同规范](handoff-rules.md)、[接口](interfaces.md)、[输入锁](inputs.lock.json)及[最新实验结果](../../../experiments/mimo-pro-results-2026-10-07.md)。本包是原L02的离线支撑交付，不重新宣称60家公司校准或启动L03。

## 要解决的问题

最近三家公司实验中326合法回答，191项给分，仅14项有有限方向/区间依据。结构通过掩盖了主体、期间、单位、指标层级和证据不足；开启思考没有稳定解决。建立可复现的离线质量工具，分别报告结构/每题有效、事实claim可核验程度、评分依据、速度、费用/套餐、缓存与失败，设计下一轮更有鉴别力的小样本实验。

完成本包不需要网络、付费模型、StockQA新接线或StockWiki新query。缺历史snippet不能造gold；质量诊断不能改公司分数或当正式研究接受。

## 唯一允许写入范围

Lab根内：`README.md`、`.gitignore`、`pyproject.toml`、`src/`、`tests/`、`fixtures/`、`schemas/`、`docs/`、`reports/`、`tools/`、自身`docs/handoff/EVID-LAB-01/`和manifest声明的独占临时测试根。不读key值，不创建.env，不使用用户下载/公司raw目录。已有同名目录非空或已有writer先停止认领，不覆盖。

其他仓全部只读。复用IQS schema/公共报告与StockQA现有工具；不得复制并另行维护HTTP客户端、搜索器、预算、缓存或outbox。测试需要固定旧工具时，在Lab自有临时根从锁定Git导出白名单原字节并核hash，结束删除；这叫测试runtime，不能提交fork工具或在原IQS模块ROOT下写临时文件。尤其原archive报告TemporaryDirectory在其模块ROOT，直接import原工具可能写IQS，必须在隔离副本运行。

## 固定输入与标签规则

只读IQS commit `5edf5eb497a0a8d5b3e1057f77fe9af76b14ec9a`三归档/326 review/join/价格/生成配置及input SHA。历史186模型/24搜索、396契约有效回答、独立重复70、支持审查326，不能混分母。provider温度48次实际0.7；数据不改，不为“修复”重发。

历史source snippets已清理。URL和snippet SHA不能重建当时正文：重放中只能核答案/引用/账本/已有agent标签，事实支持必须标`not_verifiable`或`agent_review_only`。不将已有review标签当人类gold，不从rationale反推证据。新fixtures分synthetic、历史真实模型输出、真实来源短片段三类；后一类本包没有新抓取权限，先留未收集，不能拿前两类冒充。

## 具体实现步骤

1. 首次建仓后固定起点commit，pin本包PWF；验证所有输入SHA，任何原件漂移失败，不自动重抓/重标。设计Lab自己的诊断schema（具名v1、字段有界），带input/answer hash、rule/metric版本、错误码与位置、支持来源类型、abstain原因。它是研究工具输出，不扩生产Observation。
2. 从历史归档离线重算每个run/stage/模型/思考/包大小的请求数、成功/失败/未知、原始严格与完整包装归一化、scored/unknown/N/A、三公司耗时中位数、sum block time、token公共参考和quota未知。按输入指纹配对，温度/上限/cache/执行时点混杂明示；不把套餐推成实扣，不把median乘公司数称实测总耗时。
3. 并列提供**整包成功率**和**逐项契约可恢复率**。某包一题坏导致整包拒绝时，只能从已保留item_inspection和原错误有根据地统计可恢复项；没有完整原输出时标不可测，不虚构额外有效答案。诊断不能改原state或把部分恢复当生产通过。
4. 建有限、明确的语义检查：只有输入显式提供了主体/期间/指标/unit/支持方向时才机械判矛盾，缺信息abstain。覆盖半年/全年/年化、利润vs收入、CFOvsROIC、百分比/比例/货币缩放、issuer融资vs客户承销、group/segment、同URL不同窗口、循环/转述来源和未知态仍带claim。不能靠一般关键词或模型score判事实正确，不自动补财务数或精确正确分。
5. 至少30个明确fixture场景，合并为一组单元/集成测试：每项提供来源类别、输入、预期diagnostic/abstain及为何；覆盖错主体/同名公司/多挂牌，期间单位，错误引用/题ID，duplicate JSON，缺snippet/缺usage，套餐未知，原温度偏差，循环来源与高分弱证据。重用旧复核例只作故障形态，不造真实来源正例。
6. 做只读重放CLI，建议公开界面 `python -m iqs_evidence_lab replay --input <index_or_fixture> --output <new_output_dir>`、`validate-fixtures`。输出目录必须尚不存在、input在写入前验证，输入/原件只读；不覆盖旧reports。用真实CLI跑三归档与negative fixture、重复运行不同新输出根，核统计稳定、原输入不变、网络/模型/下载0和临时清理。
7. 写下一轮proposal，标`execution_enabled=false`：沿用三市场已批准样本，冻结题意/锚点；比较混合五题包vs同证据主题分组，baseline片段vs带真实主体/期间/单位覆盖的片段，DeepSeek思考开关为主、Pro作为小额对照。准确生成矩阵请求/搜索数和保守费用/缓存方案、随机顺序、停止/接续、失败不补齐、逐题/整包/评分依据分母和未知支持规则。是否增加样本由用户决定，不自己扩大股票池。
8. 提案区分数据工程成功、结构恢复、来源支持与评分锚点依据；为短片段缺表头提供可执行改进：按题选择上下文、保留必要单位/期间、来源不足明确unknown。协议/工具是否支持生成参数，先列当前版本和缺口；不发新字段到生产执行器，也不移植新的网络调用器。

## 必须测试与交付

| 层次 | 验证 |
|---|---|
| 单元 | 有显式依据的矛盾能定位；证据缺失/不可测正确abstain；unit缩放不误判；unknown有错claim仍被诊断 |
| 集成 | 真实历史归档hash/分母重算一致；缺usage/标签/重复ID/原件篡改明确失败；现有两个review分区不当inter-rater gold |
| 离线CLI E2E | 三真实归档只读重放、新输出exclusive、错误后环境恢复、第二次新根统计稳定、input hashes不变、网络/key读取/模型/付费0 |

开发跑受影响测试，交付一次集中回归/审查。工具/30fixture/历史重放/实验proposal可complete；新真实搜索/模型实验、人类gold校准和生产采用始终not_run，留总控安排。没有新snippet不是阻止离线工具交付的理由，但必须abstain。

`docs/handoff/EVID-LAB-01/`交[模板](EVID-LAB-01.handoff.template.json)与共同规范附件，再加`metric-definitions.md`、`fixture-catalog.json`、`experiment-proposal.md`及非执行JSON配置。给分支、完整commit、调用命令和复现所需已冻结只读输入。新repo模板base_commit是占位，不可留到实际交付；换首次真实起点commit。回退只禁用Lab工具，原公司结果和生产策略完全不改。总控签收后决定是否拿其提案做下一轮小规模实验。
