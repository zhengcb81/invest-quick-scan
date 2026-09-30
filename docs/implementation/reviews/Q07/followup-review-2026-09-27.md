# Q07 独立复审整改 follow-up

日期：2026-09-27  
范围：StockQAbyLLM Q07 storage/checkpoint/transport foundation 的精确快照复审  
结论：**通过所审实现底座，无开放 P0–P2；不构成 Q07 生产闭环验收。**

审查者确认六个目标文件 SHA-256 与提交复审时提供的快照完全匹配，并隔离运行 `test_quick_scan_work_store.py` 与 `test_quick_scan_work_transport.py`：64 passed。测试使用临时工作目录、SQLite 与覆盖率文件，结束后清理；未调用 API。父任务另运行 235 项受影响 unit/integration/provider/CLI 回归，0失败/skip，且将 `ResourceWarning` 设为错误后无警告；Ruff、Black 与 `git diff --check` 均通过。

复审确认：

- URL query 凭据经同一 `_sanitized_receipt` / `_canonical_source_urls` 路径从checkpoint持久内容与receipt hash中剔除；非敏感分页/地区参数保留，fragment不持久化。回归同时验证脱敏结果及hash绑定。
- 固定 v1 SQL fixture 实际进入schema v1验证和事务升级；成功迁移保留四张旧表的全部行，拒绝无checkpoint的完成态时保留v1版本并回滚新表。
- 测试连接通过 `closing(...), connection` 管理事务与关闭生命周期。
- checkpoint事务原子性、身份/题目/attempt/回执绑定及幂等冲突语义保持成立。

明确未完成的生产门槛：公开runner/CLI还没有调用 `save_answer_checkpoint`/恢复查询；其接线依赖 W03 提供的权威 StockWiki 身份投影。PAR-04 的一次多题 dispatch 与多条逐题work item/checkpoint映射没有实现，六题恢复测试使用六次独立单题请求。进程在transport成功后、答案checkpoint提交前崩溃时，答案正文不落盘，因此只能安全转入 `uncertain`，不能本地重建答案，也不能重发。Q07应保持partial。

## 精确文件哈希

| 文件 | SHA-256 |
|---|---|
| `StockQAbyLLM/src/utils/quick_scan_work_store.py` | `0824833D7465BE89DB8390482FA201BF211A4412913933463BD3E96EE338D61C` |
| `StockQAbyLLM/src/utils/quick_scan_work_transport.py` | `60BC146DF4AAF023C25F372F02600E71D0209488867FDF28A832D162C7636FF0` |
| `StockQAbyLLM/tests/unit/test_quick_scan_work_store.py` | `CDCA20CA6569977803D7985F37402B9F20E0BCEE8B0BA2D54C1E345F0C3F827D` |
| `StockQAbyLLM/tests/unit/test_quick_scan_work_transport.py` | `567F3CBE709B67A49896C0E1B127123B043B76C2D48025A7380A39E0825686B5` |
| `StockQAbyLLM/tests/integration/test_quick_scan_cli.py` | `006FFE66D6DF929A12F9C3C6ABE0B3993768AE1C642258ADFAB6D4CC02A0B5B9` |
| `StockQAbyLLM/tests/fixtures/quick_scan_work_store_v1.sql` | `FC426AB3E9D8AEF9C6F1DE2097590002D26AF74E22A573060497F24197443C60` |
