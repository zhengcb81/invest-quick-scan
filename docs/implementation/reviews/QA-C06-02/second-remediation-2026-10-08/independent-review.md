# 原四链的集中独立复审

一次复审，由既有 `qa_c06_02_acceptance_review` agent 完成。审查冻结代码 `b6eaa082e6e1df1306fa144bd623aa6de68213a1`，没有运行测试、写文件、调用 API 或读取动态外仓。

结论：原四条整改链的有限软件范围内，没有发现剩余阻断。最终签收依赖总控实际测试，不能代替真实 StockWiki 联调、owner golden 或 G3/F05。

| 原边界 | 静态判断 |
|---|---|
| QR1B | `quick_scan_observation_context.py:232–241` 在共享 manifest 校验中绑定 security/segment ID；调用顺序在 key、HTTP、预算预约之前。 |
| QR2B | `quick_scan_work_store.py:852–864` 统一 run/scan 规则；prepare/supersede 的 `3220–3231` 与 seal 的 `quick_scan_delivery_seal.py:102–108` 使用同一规则。 |
| QR3B | `quick_scan_result_outbox.py:96–106` 在 float 解码时拒绝溢出，适用于嵌套和数组；有限数处理保留。 |
| QR4B | `quick_scan_work_store.py:3213–3218` 明确拒绝缺失 context/body 的新完整写入；`3232–3254` 核原 attempt、开始时间和完整重建；在追加 revision 前执行。历史 compact 写入和读取保留。 |

ACK helper 改成历史八字段 compact 后，原 ACK 精确匹配、字节稳定、事件链、拒绝/冲突终态、证据 URL 和 checkpoint 绑定断言仍保留。完整观察由 complete_seal 和新增 remaining mirror 覆盖，没有发现借改夹具削弱 ACK 测试。

复审建议仅补同 QR1B 的 segment 一正一反，不造大 fixture、不改冻结输入、不新增审查门。总控已在本批使用明确标为 synthetic 的内存副本完成两例：匹配通过，外部分部 ID 重签后 loader 具名拒绝。实测结果见 [验收](acceptance.md)。
