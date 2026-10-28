# Forward period：当前契约判断

2026-10-28。只读源码/当前schema/提示与测试审查；未运行模型、真实CLI、数据库操作，未读取真实答文。本次真实失败的字段与原错误来自总控提供的诊断：IQS19、basis=forward、top period 2026-10-25至2031-10-25、information_as_of=null、原validator报 answer information after cutoff。

## 建议：本轮澄清未来请求的prompt，保留当前标准时间守卫

当前 **standard-1 的实际契约**明确拒绝任何晚于cutoff的top `period_end`，无论top basis是否forward；未来预测指标期间则已允许 `metric.basis=forward`。因此本轮最小且向后兼容的方案是把这一区别清楚告诉模型，而非为接收该份旧答案改判定条件。

建议规则：

> 顶层 period_start/period_end 表示本次判断所用、截至信息截止日已能确认的证据或财务覆盖期间；未知用null，不要将未来三至五年的预测窗口填入顶层。未来预测窗口在相应 metrics 元素自己的 period_start/period_end 中表示，并明确 basis=forward、公式/假设及证据；定性未来窗口可在 summary说明。information_as_of 是支持本次判断的最新已验证事实/来源日期，必须≤cutoff，未知null；预测期间不能代替信息日期。所有 evidence.published_at 仍须≤cutoff。

这不会禁止IQS19研究未来需求，也不要求为定性判断捏造数值metric。对未知未来数值保持metrics=[]、在summary/coverage说明边界。旧真实被拒答案保持原状，不修改日期、不补分、不把本地改写当原始模型答文；原处置/重试仍由总控按原机制执行。

## 为什么不能仅凭forward枚举认定当前validator错误

- `schemas/answer-content.schema.json` 顶层period是date-or-null，basis含forward；metric也有独立period/basis。schema没有description定义顶层期间就是预测窗口，也没有定义forward可覆盖所有日期。
- IQS `scripts/standard_answers.py:70–74` 将top `information_as_of`、`period_end`共同限制≤cutoff；同文件约109允许metric future period仅在metric.basis=forward。StockQA `src/utils/quick_scan_observation_context.py:492–500、525–531` 同样处理，两个实际接受边界一致。
- `references/standard-output.md:15–17` 要求期间与basis并强调指标分口径，但未明确定义顶层期间是预测范围。现有 `tests/test_standard_answers.py` 和QA `test_quick_scan_observation_context.py` 覆盖future source/information与反向期间，没有明确“top forward future”正例。不能把缺测试视作已允许。
- `scripts/question_prompts.py:154–157` 的 **screening-1另一协议**确有“仅forward口径可描述截止日之后的期间”，前句又说期间不能晚于截止；该分支本身有歧义，不能据此静默拓展当前standard-1接受集合。
- 当前StockQA `base_llm_provider.py` 通用/题包提示只强调事实信息日期与financial periods分开，列出forward枚举，却没有解释top/metric的不同规则。题面 `questions/common.json` IQS19明确问未来三至五年。故本次更准确归因是**题义合理的未来窗口遇到未明示的标准字段语义**，不宜简单归咎模型不会遵守日期或伪造未来来源。

精确边界：当前代码独立限制的是top period_end；top period_start仅在两端都非null时核先后顺序，并非已有逐项start≤cutoff检查。本报告不把它夸称为已完整限制所有top未来日期。

## 最小长期正反测试

在IQS纯validate_content与QA纯validate_standard_answer各用相同合成fixture验证，不运行真实公司/收费请求：

1. **正例**：top period=null或真实历史期间；top basis=forward；一个future metric.basis=forward，信息与来源日期≤cutoff且证据绑定完整，接受且原body不被补写/改日期。
2. **反例**：top basis=forward但top period_end>cutoff，继续拒绝，锁住本轮旧契约。
3. **反例**：未来metric period配current/trailing/normalized/stress，拒绝；basisforward也不能接受反向period。
4. **独立时间反例**：top/metric均forward也不能放过future information_as_of或future evidence.published_at；cutoff当天仍允许，null仍保留null。
5. **提示回归**：单题与题包使用同一明确top/metric规则；不让forward提示覆盖事实日期守卫，不补未知metric数值。应检查真实提示生成函数，而非只对常量自测。

当前已存在的source-cutoff测试要保留；无需因此重跑小时全套。

## 如果产品将来确需顶层表示整个预测评价窗口

这是可合理设计的新语义，不等于当前已支持。应另立明确、可追溯的验证/输出语义版本与冻结资源：只有top basis=forward可future period，其他basis仍拒；period有序、information_as_of和source发布日期仍严格cutoff；future horizon不得刷新TTL或冒充已实现事实。两个原validator、提示、比较口径和归档资源必须同步，旧module package/旧观察继续按其冻结规则读取，不重判旧失败为成功。

同shape JSON schema不必只为改一个if机械增加字段，但接受集合变化必须有显式语义/资源版本与新hash；不能仅热改共享validator、沿用旧版本又宣称向后兼容。当前主线无需为这一个被拒结果展开此项产品变更。
