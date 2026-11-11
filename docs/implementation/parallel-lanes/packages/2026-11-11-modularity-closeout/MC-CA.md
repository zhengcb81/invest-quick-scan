# MC-CA：Company Agent公开执行与恢复验证

可独立交harness。先读 [总路线](README.md)、[契约/TDD](contracts-and-tdd.md)、[调查](architecture-audit.md)、[交接](integration-and-handoff.md)。此包以保留已有成果为原则；无缺陷时可只补关键测试和说明，不强制重构。

## 2026-11-11 入场盘点与并线清单

[实查](intake-audit/execution.md)：`master@793bfbc`已经包含公开API2.3，tracked clean，只有master；不存在待并feature分支。**canonical当前没有remote**，不新建远端，也不把无推送记作失败。

本轮已精确删除单测生成的`fixtures/locked/synthetic/boards/run-context-compact-2.board.json`。根因是`tests/conftest.py`的make_task把自定义board写入locked fixture；本卡把可写测试输入移到tmp_path，保留原静态fixture，并跑`tests/test_usage_cache.py::test_context_compression_boundary_keeps_traceability`及原公共API组。验证后源码树不得再生成这份board。

其余已有封装按原TDD验证，不强制重构。CodeGraph本地配置保留、不进业务提交。只有发现实际缺口才新增源码，不能以“必须有新commit”为验收标准。


## 目录与边界

- 唯一源仓：`C:/Users/郑曾波/Projects/iqs-company-agent-lab`；HEAD `793bfbc`已含API2.3、task1.1、opaque task/journal/runner。
- 独立实现树：`C:/Users/郑曾波/Projects/iqs-modularity-worktrees-20261111/MC-CA`；`codex/modularity-ca-20261111`，尚未创建。
- 允许：`src/iqs_company_agent_lab/`公开api、public_port、task/runner/recovery/schema资源加载及必要纯规则；相关tests、文档和本包PWF。本轮已核canonical无remote，不自行新增remote。
- 不写IQS/QA/RT；不动模型客户端/预算/正式响应；不扩研究策略，不重建12题历史实验。

## 架构与接口

公开api装配task/runner/recovery；领域通过runtime port执行效果。对外仅C2的DTO与句柄，不返回原task、Runner、EventJournal。已有slots/owner registry保留。公开DTO是语义来源，Runtime消费同一版本向量，不独立复制一份不同的任务资格规则。

## TDD实施步骤

1. 核793bfbc与当前工作树，仅归拢本域增量。画出api→task/runner/recovery→值规则的实际边，标明对runtime只依赖port的位置。
2. 先补public consumer测试：不读任何实现字段，只用公开创建、snapshot、执行、中断、恢复、export走通。使用只实现协议的runtime fake。
3. 验证task DTO深复制与roundtrip，明确封闭字段/扩展策略。未知破坏性版本拒绝；允许扩展不得误拒。若要变协议，先向总控说明差异，不能单方面改RT。
4. 动态生产题集与legacy12题隔离；保留历史checkpoint可读。schema资源在干净搬迁checkout可解析即可，不强制开发wheel发布平台。
5. 仅修失败根因；相关策略/恢复回归，一次不同agent审查，形成自包含提交/或明确既有提交加新增测试。

|必测|预期|
|---|---|
|task snapshot嵌套修改、句柄字段读取|owner不变，内部状态不泄漏|
|修改主体/问题集合/摘要|原真实不一致拒绝，不被兼容策略吞掉|
|动态1题/36题/新增模块子集、另一公司与日期|无实验公司/12题硬约束|
|runner字段改名或换fake|公开消费者无需变化|
|crash checkpoint、重复完成后的恢复|原事件和答案保持，调用者不读journal布局|
|与RT共用DTO向量|双方对支持/不支持语义结论一致|
|历史推导、嵌套指标、既有诊断答案|沿既有语义入口处理，不因本包重新加格式门|
|仅清洁源码、资源根迁移|public API可运行，缺真实资源报明确错误|

现有先跑：

```powershell
python -B -m pytest -q tests/test_public_api.py tests/test_public_task_port.py -p no:cacheprovider
```

从本仓实际测试清单选择受影响runner/recovery组并记录，不猜测试文件名，不为每个小变化跑全套。

## 交付

本仓命名PWF；`docs/handoff/MC-CA/handoff.md`写最终commit、API/DTO规则、公开使用示例、实际测试及独立agent结论。无需新JSON回执、测试计数签名或历史freeze刷新。本包完成不宣称当前QA/RT整体已通，整合由IQS负责。
