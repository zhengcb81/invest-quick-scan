# Q04 r4 独立复审

复审日期：2026-09-24  
StockQAbyLLM 快照：`HEAD 3c685dda28f67a00bd653ad257a121d3b8edebb8`  
复审范围：Q04 的 LLM policy 配置、ordered fallback、attempt receipt 与公开 CLI 集成测试。StockQA 文件保持只读。

## 结论

**Q04 在本次授权范围内通过复审。** r3 报告列出的三类 B1 fail-open 缺口均已关闭：verified rate card 必须提供非空价格依据、受限标识符长度按 schema 拒绝、启用 comparison 时预算阈值有效。保存和读取路径都有负例覆盖，保存拒绝时配置文件字节保持不变。两套测试 policy fixture 均通过 Draft 2020-12 schema 和应用 validator。

schema 的精确 `.gitignore` 例外已生效：文件现在显示为 `??` 未跟踪文件，不再被忽略，普通 `git add` 可以纳入版本控制；它目前**尚未暂存或提交**。这不影响本次源码复审结论，但交付时仍需将新 schema 一并纳入 Git。

B2 的 429 分类与 Retry-After、同 run quota cooldown、401 route 禁用、5xx 有界重试并为 backup 保留 attempt、receipt 脱敏以及 configured preference 和逐题实际 route 的区分，未见回归。范围外的 PAR-03、PAR-08、LLM-06、LLM-10 仍保持开放；本报告不将这些项目视为 Q04 已完成。

## B1 复核

- [StockQA `llm_config.py`, lines 399–403](C:/Users/郑曾波/Projects/StockQAbyLLM/src/config/llm_config.py:399)：`pricing_basis=verified_rate_card` 时拒绝缺少或空白 `pricing_ref`。单元测试在 [test_llm_config.py, lines 687–700](C:/Users/郑曾波/Projects/StockQAbyLLM/tests/unit/test_llm_config.py:687) 覆盖 null 和空字符串。
- 同文件 line 328 及 route/quota/model 校验均执行 200 字符上限；策略、quota group、route、provider config 引用、model 与 quota group 引用不再只检查非空。schema 对应的长度边界由新的参数化约束用例覆盖。
- 同文件 lines 523–535：comparison 启用时要求 `max_cost > 0` 且 `max_requests >= 1`。单元测试 [test_llm_config.py, lines 703–708](C:/Users/郑曾波/Projects/StockQAbyLLM/tests/unit/test_llm_config.py:703) 覆盖两个边界。
- [test_llm_config.py, lines 712–728](C:/Users/郑曾波/Projects/StockQAbyLLM/tests/unit/test_llm_config.py:712) 将 schema 约束反例分别送入 load 和 save；保存失败时检查原文件字节不变。fixture 的 rate-card依据已改为有效的 `user_cap` 与非空 `pricing_ref`。
- 我独立使用 `Draft202012Validator` 检查 unit 与公开 CLI 两个 fixture，均无 schema 错误；应用 validator 也接受两者。新增 schema 与本仓 `schemas/model-policy.schema.json` 在 JSON 语义上相等。

有一个非阻断的契约细节：应用 validator 比公开 JSON schema 更严格，例如要求 `web_search` 和 `structured_output` 两项能力都存在，并拒绝某些 schema 允许的空白字符串或重复 ID。它不会让无效配置绕过 schema，但两边可接受输入集合尚非完全相同。如果未来要允许仅支持一项能力或完全依赖 JSON Schema 作为编辑器契约，应统一这类严格度；本轮列出的三项 B1 fail-open 缺口不受此差异影响。

## B2 抽查

公开 CLI 集成测试调用真实 `main_with_llm.main()` 与 runner；网络边界通过 mock session 隔离，没有调用真实 provider 或联网。

- `test_public_cli_respects_retry_after_before_rate_limit_fallback` 和 HTTP-date 参数化案例覆盖 429 Retry-After 秒数/日期格式及其规范化 receipt 字段。额度耗尽使用独立 provider error code 分类；quota group 内后续 route 在本次 run 跳过。
- `test_public_cli_retries_server_error_within_global_attempt_cap_then_falls_back` 验证 503 重试受总 attempt 上限限制，并留出一次 backup 机会。
- 跨题 401 案例验证认证失败的 route 在整个单公司 run 中禁用。401/403 归入同一分类分支；没有单独的 403 CLI 例子。
- receipt 仅保留规范化错误类别、状态码和 retry 秒数，不包含私有错误正文或原始 Retry-After 字符串。fallback 案例同时断言顶层 `provider` 记录 configured preference，逐题 `execution_receipts[question_id].provider/requested_model` 记录实际 route。

仍需保留的运行时限制：普通 429 的 `Retry-After` 目前直接等待且没有最大时长；quota cooldown 和 auth route 禁用状态只保存在当前 run 内存中。持久化 `retry_wait`、跨 run/进程恢复与跨 worker 容量排队不在本轮可验证范围。

## 隔离与验证

独立复跑的 CWD、`TEMP`、`TMP`、`TMPDIR` 和 pytest `--basetemp` 都位于唯一短 TEMP 根。执行时禁用了 pyc、pytest cache、coverage，并使用 mock transport：

```text
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -q --no-cov -p no:cacheprovider \
  --rootdir <StockQAbyLLM> --basetemp <unique-temp>\p \
  tests/unit/test_llm_config.py tests/unit/test_llm_integration.py \
  tests/integration/test_quick_scan_cli.py
```

结果：**151 passed**。测试日志、pytest 临时目录及 benchmark 输出都限制在临时根内；结束后确认并删除了整个临时根。独立 Black `--check --no-cache` 对8个 Python 文件通过，`git diff --check` 通过。审查前后 StockQA 工作树状态一致，没有新增测试产物或其他副作用。

独立验证日志 SHA-256：

- 定向测试：[final-r4-independent-validation-2026-09-24.log](final-r4-independent-validation-2026-09-24.log) — `53F657BF22D006FE3F5890D8756F1B5D9E4628DAA034790E07ABB99CD6ACBB92`
- fixture/schema 校验：[final-r4-schema-fixtures-2026-09-24.log](final-r4-schema-fixtures-2026-09-24.log) — `63ECAB95EA6E245155A7CEA43923CD75E4D2616382E1A9DA061A6EAECD9FAAB5`
- 委托方最终验收日志 — `5E97508A494D8984E9B21F1C8AF03BFAD1ECBCC5566026ABE912086364FA6E2A`（151 passed、Black 8 unchanged、两份 schema fixture 通过、diff-check 通过）。

## 仍开放的跨项目边界

- **PAR-03**：跨 worker 容量槽与满载等待调度尚未实现。
- **PAR-08**：StockWiki 设置 UI/API 以及 UI、CLI、runner 共享生效策略版本的闭环尚未实现。
- **LLM-06**：全 route 不可用后的持久化 `retry_wait`、有界恢复和半开探针尚未实现；任意长 `Retry-After` 仍可令当前 run 长时间等待。
- **LLM-10**：正在执行的 run 采用启动时快照；尚未实现对尚未派发题目的实时策略热更新及成功题不重跑保证。

## r4 快照文件 SHA-256

| 文件 | SHA-256 |
|---|---|
| `.gitignore` | `3B1043A72691DF59C077F0DB4297096ABB21D482E3421C550DB3F239D9059550` |
| `src/config/llm_config.py` | `DD9257762DFDC0EC54538C653DCB057D58962901210607BDCB7D944A74D2B350` |
| `src/runners/llm_runner.py` | `579CDE5A1FB21604E0A2BDCA5667C880E45E78864602E2BD664F23A2DBEDD2A4` |
| `src/utils/llm_integration.py` | `144212285E8E7BDDFAEE30907CE2D493471677DADF43591246C6701E31C2DC7C` |
| `src/providers/llm_client.py` | `207AE40383DA230AD544116DFB13CABC1963FADA117EE9C0670F601DFEAF099F` |
| `src/config/quick_scan_model_policy.schema.json` (untracked; now addable) | `E6188237EF0FD07C4EE63C1EAB25AB250426BA7C12E6D0BC71A9D4AB1D7D0455` |
| `tests/unit/test_llm_config.py` | `B82B96FC9FA094664F91AE22885CC164108E67CC7C18E12D7B35C936DC5ED5CE` |
| `tests/unit/test_llm_integration.py` | `D03B9DADB0A52F7F1D434F201F19AE43DE9B4DEF35AA61483DF81D5E25290860` |
| `tests/integration/test_quick_scan_cli.py` | `1AB925583B035DBE2FF28F38518A6825F738435FA610AAC7827519A49C9BE692` |

