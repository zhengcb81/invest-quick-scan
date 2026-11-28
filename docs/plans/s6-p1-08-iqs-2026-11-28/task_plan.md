# IQS S6 P1-08

状态为候选待验收。上级计划为 company-wiki 的 `ecosystem-quality-audit-2026-11-27`，本卡只改 IQS。基线为 `master@b4aee7fb05671b162ef7f6d8e270ef3cb2692e52`，正在运行的工作台另线维护。

1. 在 Windows 和 Ubuntu 独立收集 `tests/` 与共用检查工具测试，从真实 pytest call 记录逐节点执行。收集器与执行器使用同一已审策略、各自运行，绑定同一个干净提交。禁止附加路径、关键字或选择器的替代收据。
2. 对历史故障走真实回路。供应商仅用系统分配端口上的截断 HTTP 夹具，两个题目同类错误不得合并成一次；使用真实原 owner 冷读。准备作业经真实 HTTP 入站，持有约 200 ms 内核文件锁后仍须保留原失败并附接同一作业。工作台隔离启动及 Windows 原生 Console API 组合都保留实测。
3. 按 `tools/ci_test_policy.json` 复核自主离线范围，源树扫描覆盖整个 `scripts/`。代码基线数量仅用于阻止新增，后续架构整改才处理存量。原开发分组继续用于快速查错。
4. 原 8 个在收集期就需要外部源码或实验输入的模块、5 个需要冻结 C06 运行配置的模块和少数节点进入显式 owner 范围。各 owner 提供同版源码、合成输入和必要运行时后，在隔离目录补齐原组合，保存节点身份、依赖 SHA 和清理回执。台账中分别保存自主套件与 owner 组合结论。
5. 由独立审查员检查路径迁移是否改变测试语义、owner 依赖是否真实、夹具是否走正常业务入口。通过实际 Ubuntu、Windows 以及适用的 owner 组合复验后方可签收。

工作入口为 `python -B scripts/ci_tests.py collect --revision FULL_SHA --output .s6-evidence` 和同参数的 `run`。无窗运行工具复用 `scripts/run_tests.py` 的临时 profile 和句柄隔离。记录用输出目录只承载 pytest 日志、回执和 JUnit。开发者预览为 `python -B scripts/run_tests.py fast --plan`。
