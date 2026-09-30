# P01 上游回归用例收据修复独立复审

检查日期：2026-09-27  
审查者：`agent:/root/p01_receipt_review`  
审查角色：独立实现审查者  
独立性：是。由单独的只读审查子代理执行；未实现或修改受审代码、测试、schema、示例或契约。

## 审查绑定

- 实现快照 SHA-256：`017318f72c0994b69f7a19355b629a6f2460d8fc2e2f6c74b47e1744222d905a`
- 测试日志：`docs/implementation/contracts/validation-P01-upstream-case-regression-r3-2026-09-27.log`
- 测试日志 SHA-256：`8933c4258588e08db3bab81fad2211968579632d72123c03101cda9e6bfe2a3d`
- 日志记载：29 tests passed。

## 审查范围与方法

只读检查以下文件及当前内容：

- `scripts/task_receipts.py`
- `tests/test_task_receipts.py`
- `schemas/quick_scan/task-receipt.schema.json`
- `examples/quick_scan/task-receipt-v2-example.json`
- `docs/implementation/contracts/task-receipts.md`
- `docs/implementation/contracts/validation-P01-upstream-case-regression-r3-2026-09-27.log`

审查重点为上游 case owner 是否必须位于任务的传递依赖闭包、引用 case 定义是否由独立哈希绑定、case 结果与 owned/reference case bundle 的边界、无引用旧 v2 收据的兼容性，以及此前发现的失败路径和测试缺口是否关闭。审查未运行测试、脚本、命令或网络/API 请求；本报告是唯一新增文件。

## 结论

结论：**approved**。上一轮 P2（哈希计算失败后的未赋值变量异常）和 P3（缺少多跳依赖正例及深层循环测试）已关闭。本轮未发现新的开放问题。

验证器现在要求非本任务 owner 的引用 case 属于当前任务的传递依赖闭包；未知 owner、无关 owner、非法依赖图及循环均失败关闭。上游引用 case 按确定顺序计算独立的 `referenced_case_bundle_sha256`；定义变化会使收据 stale，存在引用但缺少哈希会阻断。全部 `task.case_ids` 仍须有对应 case results，而本任务 owned bundle 只包含本任务拥有的 case。没有上游引用的旧 v2 收据仍可省略引用哈希。schema、示例、契约与验证器的条件行为一致。

专项测试日志记录 29 项测试通过，包括 malformed owned-case 集合返回 blocked、引用内容变化阻断、有效两跳 owner 和更深层循环失败关闭，以及仅本任务 owned cases 的旧 v2 兼容场景。审查者未自行重跑这些测试。

## 开放问题

无。
