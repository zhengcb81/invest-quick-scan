# 分派状态（动态记录）

2026-10-13，用户明确告知三个施工包均已发出：ROUTE-COVER-02、CHAIN-CONTENT-02、SCORE-ANCHOR-02。总控不再次派发、不抢这些目录、不修改 worker PWF，不自动发送消息。

| 包 | 用户确认状态 | 独占根 | 总控下一动作 |
| --- | --- | --- | --- |
| ROUTE-COVER-02 | 已派出；实际进程/HEAD未核 | C:/Users/郑曾波/Projects/iqs-route-coverage-lab | 等完整交接后集中验收 |
| CHAIN-CONTENT-02 | 已派出；实际进程/HEAD未核 | C:/Users/郑曾波/Projects/iqs-chain-content-lab | 等完整交接后集中验收 |
| SCORE-ANCHOR-02 | 已派出；实际进程/HEAD未核 | C:/Users/郑曾波/Projects/iqs-score-anchor-lab | 等完整交接后集中验收 |

manifest、inputs.lock、validation 中 workers_dispatched=false 和根不存在均是编制时快照，不回写原证据。当前分派状态以此文档/最新PWF为准；用户确认分派不等于工具已证明进程在运行或产品已交付。主线仍由总控接 B01 控制刷新到原admission/runner。
