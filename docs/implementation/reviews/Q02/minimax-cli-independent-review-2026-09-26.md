# Q02 MiniMax-M3 公共 CLI 集成独立复核

复核日期：2026-09-26。范围为 StockQAbyLLM 当前工作树的四个文件：`src/providers/llm_client.py`、`tests/unit/test_llm_client.py`、`tests/integration/test_quick_scan_cli.py`、`tests/live/test_live_quick_scan.py`。本复核只读 StockQA；未发起真实 API 请求，未读取或输出密钥。实施者报告第二次 Microsoft 单题 live 测试 `1 passed/9.55s`、第一次搜索回执为 `unverified`；这是实施者的报告，不是本独立复核亲自运行或验证的 live 结果。

## 结论与验收边界

以当前四文件哈希为准，**MiniMax-M3 的公共 CLI 搜索适配离线测试通过；本报告不是最终通过回执**。正常 `minimax` 配置路径未发现 P1。端点与模型精确预检将 `api.minimaxi.com/v1/responses` + `MiniMax-M3` 识别为可搜索；请求发给该 Responses 端点。解析器只把同一响应里的已完成 `web_search_call`、该调用的 `action.sources` 或调用之后输出消息的 URL citation、响应 ID、实际模型及后续答案文本组合成 `search_status=executed`。缺事件、缺来源、事件未完成、响应未完成、实际模型错误或无响应 ID 均不放行；正文声称有 URL 不构成执行证据。MiniMax 未提供 HTTP `x-request-id` 时保留 `request_id=null`，以本地 `attempt_id`、provider 的 `response_id` 和 `search_receipt_id` 区分及关联一次返回。OpenAI 原有请求 ID 规则仍保留。

本人在唯一系统 TEMP 根作为工作目录、清除所有 API key/token/secret 与 live 开关环境变量、阻断非 loopback socket、禁用字节码/pytest cache/默认覆盖率写入后，运行 `tests/unit/test_llm_client.py` 和 `tests/integration/test_quick_scan_cli.py`：**75 passed in 1.70s，退出码 0**；临时根共 159 项，退出上下文后确认不存在。没有运行 live 测试。该离线结果可支持适配器和模拟公共 CLI 路径；不能独立证明 MiniMax 真实线上响应或真实计费结果。Q02 的 LLM-01 live 门槛需结合实施者的脱敏 live 输出与本次哈希核对；Q02 整体仍受 LLM-06 持久 `retry_wait`/恢复路径限制，不应因本次搜索成功而标为完整 verified。

## 发现

1. **[P2] 配置中的 provider 名可与实际搜索端点不一致。** `LLMClient` 按 URL 与 model 识别 MiniMax，`LLMProvider` 仍把用户配置键 `self.provider_name` 作为对外逐题 provider。本人另在唯一 TEMP 根，用 mock 传输调用现有公共 CLI 集成测试辅助函数复现：配置键为 `openai`、URL 为 `https://api.minimaxi.com/v1/responses`、model 为 `MiniMax-M3`；结果退出码 0，实际 `session.post` URL 为 MiniMax，公开顶层 `provider=openai`、逐题 `receipt.provider=openai`、score=8。该复现清除了凭据及 live 环境变量、阻断非 loopback socket，结束后 TEMP 根不存在；没有真实请求。正常 `minimax` 配置路径通过，但跨模型比较和费用归属可能误标。应在派发前校验 provider 名与允许端点相符，或统一从已验证的传输身份派生对外名称。依据：`src/providers/llm_client.py:56-83`，`src/providers/llm_provider.py:62-80`，`src/core/models.py:306-320`。
2. **[P2] Live 断言没有直接验证所选搜索调用持有被输出的来源。** `tests/live/test_live_quick_scan.py:254-266` 分别检查 `search_receipt_id` 指向 completed search、顶层 `source_urls` 非空；若将来解析器回归，把来源错误合并到其他调用，测试可能仍通过。建议断言所选 `web_search_calls` 条目的 `source_urls` 非空并与顶层来源相交，同时显式断言 `response_status=completed`。当前解析器本身按同一已完成调用绑定来源，单测覆盖了前置引用、缺引用、多调用以及失败调用的反例。

## 运行限制与风险

- MiniMax 单题 live 测试通过 `main_with_llm.py --company ... --entity-id ... --provider minimax --config <TEMP> --output <TEMP> --require-search` 真正进入公开 CLI；测试配置只有一个 provider、一题、`max_retries=1`、格式修复预算 0、160 秒 provider 超时和 180 秒进程超时。子进程工作目录、配置、输出、日志均在 `TemporaryDirectory` 下；成功或异常时上下文执行清理，成功路径另断言根已消失。
- MiniMax 请求体没有 `max_output_tokens` 或搜索工具次数限制；一次请求和超时不等于 token 或金额硬上限。先前直连探针一次用了 10,002 tokens、无金额回执。真实生产费用预留、跨运行预算和持久重试属于另一个未完成的门槛。
- 该 MiniMax 搜索端点先前有直连成功证据，但在已核对的官方文档中未见明确列为 Server Tools 端点；本复核不重新核验厂商文档或网络服务状态。

## 四文件快照 SHA-256

| StockQAbyLLM 相对路径 | SHA-256 |
|---|---|
| `src/providers/llm_client.py` | `9E7EBF8BB281F56BAE85894C6593D5504E8754DDB924D8F3255710B50114AD20` |
| `tests/unit/test_llm_client.py` | `5C8D69B9BB68C9B24E97547EEDB992DE8924800C984B99FCFF4C45C3679221CA` |
| `tests/integration/test_quick_scan_cli.py` | `EEB64AA3B013668590AD55DF4D5C86153539ACEF159CBE763129B2D4F1E2C4BA` |
| `tests/live/test_live_quick_scan.py` | `61ECE34E5D8D4777BEC846B2F0E0B4B61F5E3D42D35048082E5C9A248DAD83E9` |
