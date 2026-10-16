# RESUME-CHAOS-06：真实依赖下的故障与接续实验包

唯一可写根`C:/Users/郑曾波/Projects/iqs-resume-chaos-lab`，包`iqs_resume_chaos`。先读[共同契约](integration-contract.md)、[接口](interface-spec.md)、[独审要求](independent-review.md)、模板与输入锁。无需另一新包或主线最终结果，全部离线。只使用冻结StockQA schema20、SESSION1.0.2、CODEC1.0.1、原研究driver/validator；不追schema21/安全反馈候选，不开实际S1或生产库。

## 目标与范围

交可复用的fault casebook、执行薄适配、实际注入证据及接续报告。复用原StockQA SDK/permit/budget/store和SESSION状态机，仅原HTTP边界mock。每次测试的SQLite由原store在本Lab专属临时根创建；所有provider响应、key和usage清楚标synthetic。不得重写“等价状态机/账本/HTTP客户端”、伪造原permit、改原校验或把mock数据写正式库。

至少16个有因果差别的场景，覆盖下面边界；每个记录真实发生的failpoint、原HTTP计数与不重发证明，不以raise任意异常代替真正状态：

1. 发送前凭据缺失、预算不足、错误task/context/pack、未获准route：HTTP=0，不能误计已发或产生免费重试。
2. 已reserve但未consume，durable consume/POST边界附近退出：按原能力报告可恢复/inspection，不能自行释放预约或认定没发。
3. HTTP发出后timeout/断连/子进程退出：unknown与预约保留，重启不能再发相同case/原task，不能归零或换store/policy绕闸。
4. HTTP200但响应schema坏、tool args坏、缺/非法usage、实际型号错配：已知回执/用量和真正未知分清，不把结构失败当0token/0费用。
5. 已提交若干题、检查点前后退出；重复载入、checkpoint hash/版本/context/limits/pack变化，已完成题不再提问；私有会话无法恢复时必须诚实inspection/拒绝，不伪造完整resume。
6. 单题/三题多段都用同一公司累计额度；有效进展与连续无进展区分；重复question/tool call、atomic batch拒绝不留半份成功。
7. 原任务封存未知后仅独立新task可继续，旧attempt每列和预约保持；ordinary/owner不继承研究豁免。只使用原公开seal/amend及真正synthetic审计，不造全局许可。
8. 输出目录已占用、journal/checkpoint写失败、Windows路径/junction外跳及重启时旧runtime存在；不删除他人根/吞异常/报成功。

不支持的故障注入点要明确unsupported及原能力边界，不用随意monkeypatch业务方法或写SQL补状态。可用原HTTP fake/genuine临时store事务、原公开checkpoint/异常接口以及自己登记的测试子进程在已记录边界退出。强杀只针对自己PID，不能按进程名杀Python。源API确有缺陷则按共同契约blocked回报最小反例，总控修新锁前不能宣称正式完成。

## API/CLI

```python
def validate_casebook(casebook, *, source_capabilities, expected_context) -> dict: ...
def run_cases(casebook, *, inputs_root, owned_test_root, expected_context) -> dict: ...
def summarize(report, *, expected_context) -> dict: ...
```

validate不执行fault；run仅本根测试资源；summary只读实际observed字段。协议见interface-spec；每次运行新根，机器JSON不能用预期值填observed。公开CLI `--version/--help`、`validate --inputs ... --casebook ...`、`run --inputs ... --casebook ... --test-root <本Lab新根> --output <本Lab新根>`、`summarize --inputs ... --report ... --output <新根>`；锁及expected SHA参数必有。不开放收费/live模式。

## 必须验证

先写关键RED/注入计划，再写薄adapter；整组单元覆盖casebook/版本/路径及报告真假，集成至少分别触发“未发送”“已发且已知HTTP但协议失败”“已发结果未知”“已提交checkpoint”四类真实原依赖路径。至少一个原SDK→原临时native预算→SESSION→CODEC→原AnswerSink链的public CLI E2E，不能用只测自家计数器代替。若某原CLI不接受mock，使用Lab公开CLI注入原SDK允许的factory/HTTP边界，不修改上游源码。

最终证明：每个原HTTP mock实际调用次数；unknown仍保留、无自动重发；原checkpoint/已完成答hash保持；同公司额度不乘题数；失败不产生合格bundle；真实key不可见、网络0、外根写0。每次run结束清理自有temp/PID/端口，实际cleanup和必要审计日志保留，验证输入原hash不变。

最后**实际调用独立agent全面审查全部fault因果链、原依赖真实性、发送/费用/恢复语义、测试和清理**；修完各种有效问题后复审passed，按独审规范留证，再交`docs/handoff/RESUME-CHAOS-06/`。不以xfail/skip掩盖关键缺口，不替主线修源/迁库/部署，不给生产owner准入结论。
