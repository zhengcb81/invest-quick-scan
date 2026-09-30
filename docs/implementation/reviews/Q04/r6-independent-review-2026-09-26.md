# Q04 route-recovery r6 独立复审

审查者：`/root/q04_r6_review_retry`。本轮为只读离线复审；先前审查代理在开始前遇到Codex后台HTTP 401，没有产生结论，本次已恢复。审查者在唯一TEMP副本中运行已选unit/CLI测试，**76 passed**，结束后删除副本，未调用真实API、未修改StockQA文件。

结论：**needs_revision**。现有绿测漏了两个最终成功回执反例：首选路由HTTP 429后备用模型成功给8分，公开派发状态却被标为`retry_wait_recommended`；首选路由运行时搜索不可用后备用模型成功给8分，却被标为`setup_required`。独立内存断言在当前代码上按预期红测（退出码1）。`_dispatch_outcome()`在判断最终成功前先解释历史失败；应在保留已发送后结果不明保护的前提下，使最终已接受答案优先于旧失败类别，并补两项单测。

另一P1：`QABatchResult.to_quick_scan_dict()`生成的公开`execution_receipts`遗漏`execution.dispatch_outcome`，内存探针确认字段缺失。需要在公开serializer及其模型单测中补字段；该文件不在此前明确的外仓写入范围，修复前须取得精确授权。以上均不等于持久化`retry_wait`、跨进程共享额度、热更新或StockWiki闭环通过；Q04整体保持partial。

审查输入快照SHA-256：

| StockQA文件 | SHA-256 |
|---|---|
| `src/utils/llm_integration.py` | `3C7F254FC23BC07417B706009272663E1966A96D6871ED76F7B481942D0A48C3` |
| `tests/unit/test_llm_integration.py` | `735603575B8D1791C242F18368FE97A65011230B86AF0E2B6C1CB32934450290` |
| `tests/integration/test_quick_scan_cli.py` | `0D61D7856707D3F20F0F7425C7F2A41389839F36E365D2772F434FF07FFAEF6A` |
| `src/core/models.py` | `3A2659B5A67E79F6CADD54571F87FA0AFE1E34B4D03FBE52EF667EF101456136` |
| `tests/unit/test_models.py` | `18CBD10F47E9DA821E8E542CB69E3D4CB57161229DC29E8CC8E5EDEB62AEE603` |

短`Retry-After`的单次有界重试、长等待快速切换和模型顺位仍在现有测试覆盖内通过；这不抵消上述两个P1。
