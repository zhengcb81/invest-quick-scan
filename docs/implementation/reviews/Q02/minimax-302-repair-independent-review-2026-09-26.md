# Q02 HTTP 302 修复独立复审

日期：2026-09-26。结论：**前次 P1 已修复；本次修复范围未发现新 P1/P2**。StockQAbyLLM 只读，未发起真实或付费 API 请求。本结论限于离线 HTTP 状态门与当前文件快照，不替代 Q02 整体或 MiniMax live 的独立验收。

新代码在同步 `requests` 与异步 `httpx` 搜索请求中均关闭自动跟随重定向，并在解析任何 Responses JSON 前调用 `_require_successful_search_status`。该函数只接受 `type(status_code) is int` 且 `200 <= status_code < 300`；其余状态由已存在的异常边界转换为脱敏 `LLMTransportAttemptError` 回执。旧版真实 `requests.Response(302)` 携完整 `completed web_search_call`、来源和回答正文会被误判 `executed` 的反例，现在回执为 `search_status=unverified`、HTTP 302、无 response ID/来源，且没有跟随 `Location`。

本人在唯一系统 TEMP 根、TEMP 工作目录、清除 API key/token/secret/password/credential 与 live 开关、阻断非 loopback socket、禁用 bytecode/pytest cache/默认 coverage 后独立运行：

```text
python -B -X utf8 -m pytest -q -o addopts= -p pytest_asyncio.plugin -p no:cacheprovider --basetemp <TEMP>/pytest <StockQA绝对路径>/tests/unit/test_llm_client.py <...>/tests/unit/test_llm_provider.py <...>/tests/unit/test_llm_integration.py <...>/tests/unit/test_models.py <...>/tests/integration/test_quick_scan_cli.py
```

结果：**203 passed in 16.27s，退出码 0**。另用真实 `requests.Response` 和 `httpx.Response` 对象构造携完整假搜索 JSON 的独立传输反例，mock 唯一外部 HTTP 边界。同步与异步分别得到相同结果：`None`、`bool(True)`、102、302、400、500 均拒绝验证，回执保留正确的整数 HTTP 状态（缺失和 bool 记 `null`）；200、201、299 有效响应体得到 `search_status=executed`。302 的回执与异常字符串均不含 fixture key、响应正文或 `Location`。两个请求参数分别为 `allow_redirects=False`、`follow_redirects=False`。测试与探针后 178 个 TEMP 项及其唯一根已自动清理，根不存在。

状态门适用于 **搜索请求**；普通非搜索 `send_request` 保持原行为。接受所有 2xx 是当前实现的显式边界，仍须由响应结构与搜索事件校验决定能否计分。未验证真实服务状态、实际费用、Q02 持久 `retry_wait` 或生产预算门。

| StockQAbyLLM 文件 | 本次复核 SHA-256 |
|---|---|
| `src/providers/llm_client.py` | `9977B097B1EB8870C0DA7FD8F61E6D7318A63C050FF6E506C1D8B9724DECBD3B` |
| `tests/unit/test_llm_client.py` | `07E431CFF3C30ADF9DCE3EBDF00377970CC078782EC62DC39E5B4FEDFB406589` |

两文件在测试前后哈希一致。其他 provider 归属文件的前次审查见 [minimax-provider-ownership-final-review-2026-09-26.md](minimax-provider-ownership-final-review-2026-09-26.md)；其中 P1 已由本次新快照解决，该旧报告的结论只绑定旧哈希，不可当作当前阻断结论。
