# Q06 同步持久化发包边界实现记录

日期：2026-09-27  
状态：第二段实现完成；首轮复审发现已修复，第二轮精确快照独立复审确认无开放P0-P2。Q06整体仍为partial。

## 范围和行为

本段只在用户授权的 StockQAbyLLM 仓库内修改以下文件；保留仓库内其他并行改动，不整理、不提交：

| 文件 | 变化 |
|---|---|
| src/utils/quick_scan_work_transport.py | 新增可选工作项/实际路由上下文、单次发送句柄、哈希化运输回执 |
| src/utils/quick_scan_work_store.py | 将可证实的401/403/404拒绝纳入明确失败状态；408/5xx和不明结果仍为uncertain |
| src/providers/llm_client.py | 同步搜索HTTP边界在POST前提交发送意图，POST后登记脱敏回执 |
| src/providers/llm_provider.py | 持久化故障与不确定状态越过宽泛错误处理，不触发provider内重试 |
| src/utils/llm_integration.py | 每次级联调用绑定确切route信息 |
| tests/unit/test_quick_scan_work_transport.py | 新增隔离SQLite/模拟HTTP集成回归 |
| tests/unit/test_quick_scan_work_store.py | 新增明确鉴权/模型拒绝与备用attempt回归 |

调用方必须先持有经身份入口验证的work item及当前lease，再进入 bind_quick_scan_work。级联为每个provider调用绑定route；无工作项的旧调用保持兼容。同步客户端先完成本地请求构造，再由事务提交 send_intent；只有发送句柄验证匹配attempt/lease并被消费后才调用HTTP。成功响应记录 response_available，不把它冒充答案检查点。已识别的401/403/404和带允许错误码的429可以按用户模型顺序转路；超时、5xx、不明429、lease过期、持久化失败均禁止盲目重发或fallback。

持久化记录只包含逻辑键、版本/指纹、运输状态和安全字段的回执哈希；不写完整prompt、回答正文、网页正文、来源URL或API key。显式格式修复仅在同一lease和相同route/provider/model下允许一次，且必须更换prompt hash与request key；SQLite通过当前lease下成功运输回执计数强制禁止第三次回答请求。无论迟到响应是2xx还是失败/拒绝，围栏失败后只保存late receipt hash并继续保持uncertain，不能接受答案或触发fallback。

## 验证

- 修复后的Q06 store + transport焦点批次：45 passed。
- 当前 provider、cascade、parser、work-store、transport和公开CLI unit/integration分组：274 passed，0失败。
- 真实本地SQLite运行于pytest唯一临时目录；HTTP使用mock fixture；测试子进程清除了*_API_KEY及live开关；未发起网络/API调用。pytest临时目录由TemporaryDirectory清理。
- Ruff、AST parse及选定文件Black：通过。共享的 `llm_client.py`、`llm_integration.py` 含早前已有实现的格式差异；没有整文件重排。
- 最终pytest日志：[validation-Q06-transport-boundary-final-2026-09-27.log](../../contracts/validation-Q06-transport-boundary-final-2026-09-27.log)，SHA-256 `7890D80AB17DBA8CE4211BF7D3DEC605D4968F60769F875208F12ABB83DFD5AE`。
- 最终静态检查日志：[validation-Q06-static-final-2026-09-27.log](../../contracts/validation-Q06-static-final-2026-09-27.log)，SHA-256 `09F6C89C5011EF87C965A151DDFE483E232C6626BF34777EA178C1C4A5DB6C46`。

## 第一轮冻结快照（历史）

独立审查人被要求先核对下列SHA-256；审查期间不得编辑或执行测试。

| StockQA文件 | SHA-256 |
|---|---|
| src/utils/quick_scan_work_transport.py | 6A7241DACC8DD93B39901B77113C88744C5ED64D14D95672881D5FDAC93E6ACC |
| src/utils/quick_scan_work_store.py | 765519B2DF2C1D0A414674F5DDA577E861C1EF0C1C3D494D693C4E12E6108FFE |
| src/providers/llm_client.py | C57136BDDAF1E77A1295BF99A30BED069748F3698FFD7DC36EDA7D69FF4CB77C |
| src/providers/llm_provider.py | F70A51434A803CE31816FC332AF16D368E00CC574DAE20D132F7B829947E8156 |
| src/utils/llm_integration.py | 81CD337258D49D54AA9D221E8BA650F6C2FBFAFB9C377708A27F142695884EAF |
| tests/unit/test_quick_scan_work_transport.py | 0A88F751AB7FE55B119B3345EADC7333AD42F22F64D043A4A662682E08FE0012 |
| tests/unit/test_quick_scan_work_store.py | 666E9208C8BBC5D96E394DE3EF8BC02D748068522E1B64544D64A6981F1BFB18 |

第一轮审查发现两项P2：迟到成功响应未留回执、格式修复请求被账本阻止。二者已在后续快照修正，不以此历史快照作为当前验证依据。

## 第二轮冻结快照与审查

第二轮审查前核对下列文件SHA-256全部匹配；复审为只读，没有改文件、运行测试或调用API。

| StockQA文件 | SHA-256 |
|---|---|
| src/utils/quick_scan_work_transport.py | 6382FEBDB1B166EE689CDD532B43E8460E92572DEC422EEE6D0924EA14D25A4C |
| src/utils/quick_scan_work_store.py | 7C2FBFF2B9AA10FE482810BB997713D98133D322DC898B524A375AAD2E2014CD |
| src/providers/llm_client.py | C57136BDDAF1E77A1295BF99A30BED069748F3698FFD7DC36EDA7D69FF4CB77C |
| src/providers/llm_provider.py | 88AD87BF02E04055B34EF0D627163C8104A4D02FB137A80545B8DB839ABC5081 |
| src/utils/llm_integration.py | 81CD337258D49D54AA9D221E8BA650F6C2FBFAFB9C377708A27F142695884EAF |
| tests/unit/test_quick_scan_work_transport.py | 5027BACFA382271064D8E815EB72935FCE8EA3D0FA916BC41BEC13691A9EF144 |
| tests/unit/test_quick_scan_work_store.py | B325E916326416120A72D2CE48AF0E1971C264F0C89E3DB4656E7394ED08C6D9 |

第二轮复审关闭此前P2/P3且未发现新的P0-P2：[independent-review-r2-2026-09-27.md](independent-review-r2-2026-09-27.md)。

## 未完成边界

- StockQA公共CLI尚未创建或绑定生产work item；需要W03提供权威身份修订、来源绑定及资格回执，不能把测试身份当作生产身份。
- Q07负责答案与来源结果的原子checkpoint；Q09负责预算；Q10/StockWiki W05负责outbox/ACK。
- 这里只覆盖同步公开快扫transport。异步客户端未接入本work-store context。
- 本段未写StockWiki、company-wiki，没有下载公司文档，也没有live API E2E。
