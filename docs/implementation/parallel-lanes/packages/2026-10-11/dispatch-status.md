# 三个独立包的派发与接收状态

2026-10-11用户直接确认：“3个施工包都已经发出去了”。这是派发证据；尚未收到产品交接，不据此推断进程正在运行、已有测试通过或任务完成。各目录自此视为外部writer保留根，总控不创建、修改、清理或代实现。

| 包 | 独占工作目录 | 当前协调状态 | 预期交接入口 |
| --- | --- | --- | --- |
| MATRIX-CASE-01 | `C:/Users/郑曾波/Projects/iqs-comparison-case-lab` | human_dispatched; awaiting_handoff | `docs/handoff/MATRIX-CASE-01/handoff.json` |
| LOAD-CASE-01 | `C:/Users/郑曾波/Projects/iqs-load-case-lab` | human_dispatched; awaiting_handoff | `docs/handoff/LOAD-CASE-01/handoff.json` |
| IDENT-EDGE-01 | `C:/Users/郑曾波/Projects/iqs-identity-case-lab` | handoff_received; changes_requested（同包R1） | `docs/handoff/IDENT-EDGE-01/handoff.json` |

三卡的工作范围、CLI、schema、测试和交接规则保持原版。三个包彼此无交付依赖；不得写IQS、StockQA、StockWiki或另一个Lab。总控继续自己的B01公开生产链实验准备，接收各包后再按原包级节点验收、由权威owner集成，不增加小节点审查。

本次只读复核41个锁内文件：bytes与raw SHA全部匹配，输入锁SHA为`3ce74d8399e2bee7e163a8b1ecc32cf6335f26bb15d23071a367bdc144e0d46c`。这是输入稳定性核对，没有运行三个Lab的产品测试或收费API。后续开工仍按共同规则核自己的输入快照；源HEAD前进不等于锁内字节漂移。

`manifest.json`、`inputs.lock.json`、`validation.json`和verification日志记载编制时的历史状态，保持原字节。当前派发状态由本文件和总控PWF记录，不能把历史`workers_dispatched=false`误当用户尚未派发。

2026-10-11更新：用户交回IDENT，总控同一次集中原43P但3公开CLI错误放行及内容/交接缺口，状态changes_requested。续做卡`docs/implementation/reviews/parallel-packages/2026-10-11/IDENT-EDGE-01-R1.md`；不重新派发、不代写Lab。MATRIX/LOAD未收到交接，历史编制manifest/输入锁不改。
