# 本地题库与标准化审查记录

2026-09-22。范围：本skill题库、离线编排/标准输出/比较/模型策略校验，以及实施包1.4.0。此记录不是G0—G6生产放行，不表示StockQA、StockWiki或研究消费者已接线。

## 独立前向审查

审查者为本任务内独立子代理`/root/question_audit`，只读检查并用虚构A/H双挂牌、成熟周期设备企业走正常使用路径。未调用付费模型或修改外部项目。审查发现与处理：

| 发现 | 改动及复核 |
|---|---|
| 旧汇总把补充题混入维度，快/全模式权重漂移 | 新manifest使用core-constructs-v1，仅24个核心构念/类型替代参与主维度；旧manifest保留旧方法，加入模式不变性回归 |
| 事实题prompt缺少完整实体/证券/分部上下文 | 标准prompt写入身份与范围，独立代理重新检查同名公司/A-H上下文通过 |
| 模型对照未核对实际信息日期 | 比较同时约束截止日和信息日期，独立重测不匹配时拒绝差值 |
| 年度与半年观察可能连成时间变化 | 加期间节奏/结束月约束，不能把期间变化归为经营变化 |
| 模型版本未知与事实嵌套指标的比较限制不明显 | 明示revision未知和逐行事实不自动数值对齐；重新前向检查通过 |

独立重测范围为题库路由、事实prompt和三维比较；后加模型配置校验主要由以下本地测试验证，未冒称整个跨项目产品获得独立验收。

## 本地测试与修复

标准观察的新增方法/单位回归发现返回值引用了调用方的可变输入，修改输入会破坏旧观察hash。已在落hash前深拷贝，保留失败测试后通过。配置模板测试发现未知额度窗口null被schema拒绝，已修正为正整数或null；CLI校验错误仅显示字段位置/规则，避免回显误填凭据。

实际执行：

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 scripts/question_sets.py validate
python -X utf8 scripts/standard_answers.py validate-library
python -X utf8 scripts/model_policy.py --input examples/model-policy.template.json
python -X utf8 scripts/implementation_plan.py validate
```

97项测试通过，无skip：41项计划工具、27项既有评分行为/兼容、20项标准答案、9项模型配置。评分库48模块/222题、事实库61题、skill-creator quick_validate及标准schema检查通过。5个完全虚构的样板观察可验证。最终G6依赖覆盖全部72个前置任务；162项acceptance case仍全部为specified_not_executed，不能当作已跑生产测试。

## 尚待外部实现

实际上游离线检查仍为provider解析8分、AnswerGenerator返回5分；提示词请求搜索不能替代实际搜索回执。由Q01/Q02及后续接线修复并验收。持续派发、共享账户额度、两库交换、UI与两个研究消费者均属于后续生产任务；本轮未改这些仓库、下载公司文档或真实扫描股票池。

下一步从[实施入口](../README.md)的P00开始，复用本地已有问题/协议/配置模板，不重建LLM客户端或第二套权威存储。
