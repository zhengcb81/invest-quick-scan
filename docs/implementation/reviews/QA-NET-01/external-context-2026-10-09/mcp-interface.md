# Phase111 MCP检索：私有实施与恢复接口

本段优先于旧接口中的“MCP尚未接通”描述；旧归档保持原字节。生产StockQA仍42a517c/schema8，本段schema13仅在IQS独占runs/n111a/qa。没有真实API调用、生产迁移或整Phase111签收。

## 实际调用与唯一账本

现有检索协调入口按用户搜索顺位运行；MCP使用同一个Q09预算与Q08健康库，没有新账本。initialize、notifications/initialized、tools/list各有私有不可变stage、预算预留及一次性dispatch；tools/call仍是原external operation的第四个HTTP。控制阶段不是LLM回答attempt，也不作为公司证据。发送前先持久保存许可；结果和已知费用同事务提交，保存失败回滚结算、保留已消耗dispatch，不能重复发送。

schema13仅增空表：quick_scan_mcp_stage、quick_scan_mcp_dispatch、quick_scan_mcp_result、quick_scan_mcp_search_binding。真实v12升级保留HTTP、native短事件、答案及费用，不补造控制请求历史；升级中断完整回滚。原schema8—12迁移仍按实际旧DDL测试，不能仅降user_version。

每个冻结query/发行人/身份/manifest/generation/route/policy组合冷跑需要三次协商＋一次搜索。同query可供多题复用，完整warm不要求搜索凭据且新增HTTP/费用均为零；不同query当前各自协商，不声称全股票池共享一次握手。后续成本实验必须计入这些控制请求。仅支持有核验来源的all_http_requests/per_request计价；不默认握手免费，也不把仅搜索或未核验套餐计价当完整控制费用。

## 协议、工具与轻量输出

官方[Z.ai MCP文档](https://docs.z.ai/devpack/mcp/search-mcp-server)给出Streamable HTTP endpoint和webSearchPrime；本项目[真实旧探针](../../../experiments/zai-mcp-connectivity-probe-2026-10-07.json)实际协商2024-11-05并发现web_search_prime。实现提供2025-03-26，明确支持这两个协议及这两个工具名；采用实际协商和发现值，不改名伪装。未知协议、名称歧义、不支持的必填参数或分页不执行搜索。

按[MCP lifecycle](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle)发送initialized通知，按[HTTP transport](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)接受202空body并使用实际session header。Session只留私有运行库，有限长度/ASCII、不能回显已知API key；不进入公司context、公共回执或答案。HTTP原body仅在有界内存中解析，持久只保留摘要和短控制字段，不保存网页/财报/完整响应。

输入schema由真实tools/list核验并保存hash，当前仅执行已验证的search_query参数；服务没有count时不猜造count，top_k在结果截断边界生效。JSON-RPC回应必须关联原意图的实际ID。JSON/SSE共用单次HTTP适配器；SSE在完整关联回应后关闭，不等无限流结束、不执行server request或另发GET/DELETE/旧SSE回退。工具result.isError拒绝作为证据，即便同时夹有看似正常条目。

最终搜索意图私有绑定三条已完成、已结算、未迟到控制记录及各自hash；在发送与恢复回读实际owner，重新计算hash不能把它换成外来控制记录。公共wire继续既有external版本，未制造native web_search_call或向公开输出泄露session。

## 故障与接续

任一实际HTTP发送结果unknown或价格不能核对都停止，保留原预留/已知费用；更换route、预算或重开库不消除同发行人范围的未知态。已付费的确认拒绝可使用下一个允许搜索route，但不能重复握手。迟到控制保留实际响应与费用，不能推进下一阶段；过期且未发送旧意图仍保守hold。MCP每步中断后恢复覆盖的是实际store/client路径，不是OS强杀任意断点或厂商当前互通认证。

## 当前实际证据与剩余工作

- 最初12F是缺begin_mcp_stage入口；第一12P后新增邻接批20P/5F，含unknown重用、冻结owner/time缺口、已有Q09阻断的诊断归属，以及一处claim测试参数错误。原日志都保留。
- mcp-journal-owner-affected-green-01四文件345P；协议/控制transport红批26P/9F后，两文件55P；完整检索红批35P/9F，第一次整链74P/1F是REST fallback测试误设超时，已更正fixture。
- 六文件mcp-retrieval-owner-affected-green-01为397P/1F，MCP文件47项全通过，wall54.618s。唯一失败为旧“MCP未实现所以零请求”断言；现在改验畸形初始化只收费一次、不预留搜索、warm不重发。mcp-old-blocker-fixture-green-01追加1P/wall2.089s，只有该测试文件改变，产品源码未变。两批不相加冒充一次398P。

仍待真正独立OS子进程CLI冷暖/中断恢复（含MCP→LLM→公开结果）、整批静态/受影响回归、一次集中独审、正常源Git发布和自有根严格清理。不是金融答案准确性、人类gold、真实厂商计价、StockWiki联合ACK/G3/F05/TH-IN或200家公司放行。
