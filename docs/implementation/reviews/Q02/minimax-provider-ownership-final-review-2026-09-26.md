# Q02 MiniMax provider 身份候选版独立复核

日期：2026-09-26。StockQAbyLLM **只读**；未调用真实 API、未读取或打印密钥。结论：**needs revision（P1）**。本次复核绑定下方当前工作树哈希；实施者先前报告的 MiniMax live `1 passed/9.55s` 并非本人独立执行或验证。

## 范围与已通过检查

阅读 `llm_client.py`、`llm_provider.py`、`llm_integration.py`、`models.py`，及对应 unit/integration/live 测试。`LLMClient` 把公开 canonical provider 名与 allowlist URL/model 比较，`openai` 错指 MiniMax 或反向配置在发包前失效；有意使用 `primary`/`backup` 等 route alias 时，从传输回执记录实际 provider，并单独保留 `provider_config_ref`。混合厂商 fallback 的逐题回执选用最终实际厂商，公开顶层 `provider.name` 与 `requested_model` 置 `null`，不把首选模型冒充全程唯一模型。未发送的结果也不虚构厂商。MiniMax 不返回 `x-request-id` 时，`request_id` 保持 `null`，同时保留 provider response ID、本地 attempt ID、搜索调用 ID。公开 JSON 仍为 `stockqa.quick_scan_result/1.0.0`。

在唯一系统 TEMP 根运行五个离线文件（`test_llm_client.py`、`test_llm_provider.py`、`test_llm_integration.py`、`test_models.py`、`test_quick_scan_cli.py`）：`python -B -X utf8 -m pytest -q -o addopts= -p pytest_asyncio.plugin -p no:cacheprovider --basetemp <TEMP>/pytest <五个绝对路径>`，**201 passed in 16.24s，退出码 0**。子进程以 TEMP 为 `cwd`，清除 API key/token/secret/password/credential 及 live 开关环境变量，`sitecustomize` 阻断非 loopback socket，禁用 bytecode、pytest cache 和默认 coverage 输出。结束后 178 个 TEMP 项随唯一根清除，根不存在。未运行 live 文件。

## 阻断发现

**[P1] 同步 3xx 响应可被判定为已执行搜索。** `src/providers/llm_client.py:482-490` 调用 `requests` 时使用 `allow_redirects=False`，这避免自动跟随并带着凭据发到新地址；但随后只调用 `response.raise_for_status()`，而 `requests.Response.raise_for_status()` 对 302 不抛异常。若 302 响应体是符合 Responses 形状的 JSON，解析器可输出 `search_status=executed`，尽管 HTTP 请求并未成功。本人用真实 `requests.Response` 对象（`status_code=302`、`Location=https://example.invalid/redirected`）和 mock session，在相同隔离、断网 TEMP 中独立复现：`{"status_code":302,"verified":true,"search_status":"executed","redirects_disabled":true}`；退出码 0，TEMP 已删除。这是结果真实性缺陷，不是本复现中的密钥转发。修复应在同步与异步传输边界显式拒绝非 2xx 状态后才解析响应，并增加有完整伪造搜索 JSON 响应体的 3xx 回归测试。仅检查 `allow_redirects=False` 不足以覆盖它。

核心反例可在上述隔离 Python 进程中复跑，全部数据为虚构 fixture：

```python
import json
import requests
from unittest.mock import Mock, patch
from src.providers.llm_client import LLMClient

response = requests.Response()
response.status_code = 302
response.url = "https://api.minimaxi.com/v1/responses"
response.headers["Location"] = "https://example.invalid/redirected"
response._content = json.dumps({
    "id": "resp-redirect", "status": "completed", "model": "MiniMax-M3",
    "output": [
        {"type": "web_search_call", "id": "ws-redirect", "status": "completed",
         "action": {"type": "search", "sources": [{"url": "https://example.com/source"}]}},
        {"type": "message", "status": "completed", "content": [
            {"type": "output_text", "text": '{"score":8,"description":"fixture"}'}]},
    ],
}).encode("utf-8")
session = Mock()
session.post.return_value = response
with patch("src.providers.llm_client.http_client_manager") as manager:
    manager.get_sync_session.return_value = session
    result = LLMClient("offline-fixture-key", "MiniMax-M3",
                       "https://api.minimaxi.com/v1/responses",
                       provider_name="minimax").send_search_request("fixture")
    assert session.post.call_args.kwargs["allow_redirects"] is False
    assert result.search_verified  # 错误放行：HTTP 302
```

## 其他边界

- 对照当前代码和测试，没有发现正常配置路径把 provider alias 写成实际厂商的旧问题；按四文件结果，实际厂商、route alias 和 mixed top-level 已分开。上述 P1 修复后需按新哈希重跑并复审，当前候选版不能最终通过。
- 失败回执只保留分类、HTTP 状态、ID 等字段，不保存响应错误正文或 Authorization header；本次离线输出未出现完整 API key。`BaseLLMProvider` 的旧日志会打印脱敏 key 的首尾片段，若要求日志里连片段也不出现，应另行改为固定占位符；该文件不在本次变更范围。MiniMax live 测试的子进程日志位于自动删除的 TEMP 根。
- 本复核没有独立验证先前 live 成功，亦没有完成 Q02 的持久 `retry_wait`/接续、跨运行预算或美元硬上限。

## 工作树 SHA-256

| StockQAbyLLM 相对路径 | SHA-256 |
|---|---|
| `src/providers/llm_client.py` | `6B545419BDCC3BA1D45F67C3E25DDBFDE7CA398B1DF5A78856B55A90BC822374` |
| `src/providers/llm_provider.py` | `AD7452AEC809C6655A1124B614D2A6ABF95047918348182A90DB8291D4D0C377` |
| `src/utils/llm_integration.py` | `7A8CF9D415FDA121FA4A85685B5F389065BEF96988F6BCC966C3D962AB0526C6` |
| `src/core/models.py` | `117AE7B0FFB2EB5DD5361D8322F71558E0352E45BC75C2A704747D06A9C5148F` |
| `tests/unit/test_llm_client.py` | `B2BC11CBD3EA192CE2059AA5FB7DF3CD8BEA074323B527A6B92F96361B982881` |
| `tests/unit/test_llm_provider.py` | `F5D76C9F5AA1AEED70C85A15D2F4C0680763F2225D683552CE3029C73E573CC9` |
| `tests/unit/test_llm_integration.py` | `314395557D9F1FBC396788BAB8EF73E20E649F5B2992E5EDF7A0347F8BE7DB81` |
| `tests/unit/test_models.py` | `A9A6235DF061BA0AE2802799ED9268195CA6A2AD5C4E386223D4EEC191568FBA` |
| `tests/integration/test_quick_scan_cli.py` | `F1239A31B28AF7E0EC084EA9308E7E9C382AABB3D0A59C036BEF50518F761431` |
| `tests/live/test_live_quick_scan.py` | `61ECE34E5D8D4777BEC846B2F0E0B4B61F5E3D42D35048082E5C9A248DAD83E9` |
