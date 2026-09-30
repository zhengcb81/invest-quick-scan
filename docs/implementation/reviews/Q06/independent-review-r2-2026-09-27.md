# Q06 同步传输边界独立复审（二轮）

日期：2026-09-27  
范围：StockQAbyLLM Q06 同步 transport 子阶段，只读源码与测试复审。  
审查者：独立审查 agent。  
结论：此前两项 P2 和一项 P3 已关闭；本轮未发现开放 P0–P2。此结论不代表公共 CLI durable resume 或 Q06 整体完成。

## 快照绑定

审查前七个目标文件 SHA-256 全部匹配；审查者未修改文件、未运行测试、未调用真实 API。

| 文件 | SHA-256 |
|---|---|
| `src/utils/quick_scan_work_transport.py` | `6382FEBDB1B166EE689CDD532B43E8460E92572DEC422EEE6D0924EA14D25A4C` |
| `src/utils/quick_scan_work_store.py` | `7C2FBFF2B9AA10FE482810BB997713D98133D322DC898B524A375AAD2E2014CD` |
| `src/providers/llm_client.py` | `C57136BDDAF1E77A1295BF99A30BED069748F3698FFD7DC36EDA7D69FF4CB77C` |
| `src/providers/llm_provider.py` | `88AD87BF02E04055B34EF0D627163C8104A4D02FB137A80545B8DB839ABC5081` |
| `src/utils/llm_integration.py` | `81CD337258D49D54AA9D221E8BA650F6C2FBFAFB9C377708A27F142695884EAF` |
| `tests/unit/test_quick_scan_work_transport.py` | `5027BACFA382271064D8E815EB72935FCE8EA3D0FA916BC41BEC13691A9EF144` |
| `tests/unit/test_quick_scan_work_store.py` | `B325E916326416120A72D2CE48AF0E1971C264F0C89E3DB4656E7394ED08C6D9` |

## 复审结论

- **P2，格式修复次数未由 SQLite 限制：已关闭。** `prepare_attempt` 只在前一 attempt 为 `response_available`、当前 lease epoch/token 未变、route/provider/model 完全相同、prompt hash 与 cache key 均不同，且当前 lease 恰有一条 `response_available` 时，接受显式 `allow_format_repair`。格式修复成功后该计数为二，第三次新 prompt/cache key 请求仍被拒绝。覆盖测试验证成功一次并拒绝第三次，以及提示词重复、跨 route/provider/model 的拒绝。（`StockQAbyLLM/src/utils/quick_scan_work_store.py:478`；`StockQAbyLLM/tests/unit/test_quick_scan_work_store.py:447`）
- **P3，迟到失败响应未保留收据：已关闭。** `record_failure` 遇到 lease fencing 时调用 `note_late_receipt` 保存安全 receipt hash，随后仍抛出 `QuickScanWorkUncertainError`；迟到的明确拒绝不会变成可 fallback 的 `confirmed_failure`。测试参数化覆盖迟到 200、401、429，并确认状态保持 uncertain、只请求一次且仅写入 late receipt hash。（`StockQAbyLLM/src/utils/quick_scan_work_transport.py:162`；`StockQAbyLLM/tests/unit/test_quick_scan_work_transport.py:358`）
- 前一轮的迟到成功响应 P2 也仍已关闭：迟到 2xx 仅登记 late receipt hash，不能作为已接受答案或触发备用路由。
- 本结论只覆盖绑定可信 work item 时的同步 HTTP transport。公共 CLI 尚未生产性创建/绑定 work item，仍需 W03 身份投影、Q07 答案 checkpoint，以及后续预算与 StockWiki ACK 集成。

