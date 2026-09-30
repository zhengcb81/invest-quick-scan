# Q02 独立离线审查

审查日期：2026-09-25。范围是当前 `StockQAbyLLM` 工作树中 Q02（“接通首个提供商真实搜索与执行凭据”）的离线实现和测试；对照本仓 `tasks.json` 中 Q02 的步骤/完成门槛，以及验收用例 LLM-01、LLM-02、LLM-06。外仓 HEAD 为 `3c685dda28f67a00bd653ad257a121d3b8edebb8`；该仓已有未提交修改，本审查只记录当前文件快照，没有改动外仓。没有读取或打印任何密钥，也没有发起网络或真实模型请求。

## 结论

OpenAI Responses `web_search` 请求构造、执行回执保留、缺搜索执行证据时不计分，以及“不支持能力跳过 / 全局 400 不盲目 fallback”均有当前离线代码和隔离 mock 测试支持。选定的五个测试文件共 **110 passed**。LLM-01 要求的真实搜索工具事件仍未经过 live 验证；LLM-06 中“所有模型不可用时进入 `retry_wait`”没有实现或测试证据。因此 Q02 整体仍未完成，不能标为 verified。

## 验收对照

| 用例 | 证据与状态 |
|---|---|
| LLM-01 | 离线结构部分通过：`llm_client.py` 构造 `/v1/responses`、`web_search`、`tool_choice="required"` 和来源字段；mock 测试检查 `request_id`、response/model/search 元数据、attempt receipt 与来源 URL 能经 provider/CLI 输出。由于传输被 mock，不能证明真实服务确实执行搜索、其真实事件能被当前解析器解析，或 receipt 与真实 request 一致。**live 未验证**。 |
| LLM-02 | 离线通过：缺少真实传输执行凭据时，客户端标为 unverified；同步、异步 provider 和公共 CLI 路径保留 `score: null` / `insufficient_evidence`，不会仅凭模型自述或 URL 放行评分。 |
| LLM-06 | 部分通过：不支持 web search 的路由会在发送前跳过；HTTP 400 全局请求错误不会盲目尝试备用路由。所有路由均不可用时，集成层返回 `provider_unavailable` 错误；已尝试路由都失败时返回最后的失败结果。没有发现将该状态转换为 `retry_wait` 的状态机或持久化恢复路径，也没有覆盖此预期的测试。因此“结束本轮发送”有有限路由/attempt cap 的部分证据，进入 `retry_wait` 未通过。 |

### 发现（按严重程度）

1. **[P1] LLM-06 的全路由耗尽语义未完成。** [`llm_integration.py`](C:/Users/郑曾波/Projects/StockQAbyLLM/src/utils/llm_integration.py:772) 在没有可派发路由时返回 `status="error"` 和 `failure_type="provider_unavailable"`；所有实际请求失败时也将最后一个错误作为结果返回。该路径没有 `retry_wait` 或可恢复的派发状态。现有 CLI 测试分别覆盖能力缺失跳过和 HTTP 400 不 fallback，却没有验证全模型不可用时进入等待、停止继续派发且后续可接续。Q04 计划也将持久有界恢复列为仍开放事项。此差距阻止 Q02 的 LLM-06 完整通过。

2. **[P1 / 验收门槛] LLM-01 的 live 搜索证据缺失。** 当前正向测试用 mock HTTP 响应提供搜索事件，能验证适配器映射和输出合同，但不能作为真实 provider 的执行证据。任务计划明确规定 live 小样本且独立审查当前快照后方可 verified；本次按指令没有发起 live/API 请求，因此仍需后续有界 live 验收。

## 隔离测试

执行命令等价于（`$repo` 指 StockQAbyLLM 的绝对路径）：

```powershell
python -B -m pytest -o addopts= -p pytest_asyncio.plugin -p no:cacheprovider `
  --basetemp <唯一系统TEMP目录> -q `
  "$repo/tests/unit/test_llm_client.py" `
  "$repo/tests/unit/test_llm_provider.py" `
  "$repo/tests/unit/test_search_provider.py" `
  "$repo/tests/unit/test_llm_runner.py" `
  "$repo/tests/integration/test_quick_scan_cli.py"
```

结果：`110 passed in 15.71s`，退出码 0。测试在唯一系统临时目录下的 `cwd` 运行，`TEMP`、`TMP`、`TMPDIR`、`PYTHONPYCACHEPREFIX` 和 pytest `basetemp` 均指向同一个唯一隔离根目录；禁用 bytecode、pytest cache 和仓库默认 coverage addopts；测试进程中 API key/token/secret 类环境变量已清除。临时 `sitecustomize` 阻止所有非 loopback Python socket 连接，允许 loopback 仅用于 Windows asyncio 事件循环；选定 HTTP 传输使用 mock。运行产生的 161 个临时目录项已在测试后删除，并确认隔离根目录不存在。没有执行 live 或外部网络测试。

原始证据保存在本仓：完整 pytest stdout [offline-pytest.stdout.txt](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/reviews/Q02/offline-pytest.stdout.txt)，SHA-256 `EC2939EBB39C818C307151239DF0A51239B24BB39CBD2343CB093CE6F7AE22EE`；完整命令 argv/display command、CWD/TEMP/basetemp、退出码、汇总、清理结果及复核路径哈希的 [offline-pytest-evidence.json](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/reviews/Q02/offline-pytest-evidence.json)，SHA-256 `66C8DB4CC933889EE62F079492A4C42B5218FF4897C0CFCEC64829793628D96B`。复跑后核对了本报告列出的全部 13 个外仓源码/测试文件哈希，均与审查快照一致；没有发现漂移，也没有扩大审查或改变结论。

## 审查快照 SHA-256

以下是被阅读或纳入上述测试选择的外仓源码与测试当前字节哈希；这些哈希绑定的是工作树快照，不代表本审查修改或拥有这些更改。

| 路径（相对 StockQAbyLLM） | SHA-256 |
|---|---|
| `src/providers/llm_client.py` | `207AE40383DA230AD544116DFB13CABC1963FADA117EE9C0670F601DFEAF099F` |
| `src/providers/llm_provider.py` | `542376B016C80F4175B93DBE9CE793391357A72767E650467F1DEEE546C27A97` |
| `src/providers/async_llm_provider.py` | `68B87001A2E03118E27C74933DCA8443DA999E3AAD18E33353B012705A17D3A3` |
| `src/providers/base_llm_provider.py` | `3553424F1C074B6E4C38CC2F376E809C509D503FEDBE9D380BE202E619972C9A` |
| `src/providers/llm_response_parser.py` | `9D5EB7D58DACFED1DFFB605ECA504D8A9EC6B6C39A5E2F4341D0A9B6F58AA867` |
| `src/runners/llm_runner.py` | `579CDE5A1FB21604E0A2BDCA5667C880E45E78864602E2BD664F23A2DBEDD2A4` |
| `src/utils/llm_integration.py` | `144212285E8E7BDDFAEE30907CE2D493471677DADF43591246C6701E31C2DC7C` |
| `src/config/llm_config.py` | `DD9257762DFDC0EC54538C653DCB057D58962901210607BDCB7D944A74D2B350` |
| `tests/unit/test_llm_client.py` | `29C7ECC54C9C32C8AEE6939F07BEA30F8F88FB5350679A78B26C92BF048BF32B` |
| `tests/unit/test_llm_provider.py` | `C08491434622CB9FDECCD9D9F08F3E7E6E48D1B9BD1092C3E85265DD0A935C6E` |
| `tests/unit/test_search_provider.py` | `24204047E9E52A9621AACD210B4AF85F968C45DCB9BB569101F6E87F67C17739` |
| `tests/unit/test_llm_runner.py` | `098A060E54AB6F2612EAA8B05CDBDA68DDA03F1CE95318FF60C8C6F74F94BB33` |
| `tests/integration/test_quick_scan_cli.py` | `E242EC7E6B1EA82C6AD056A644CC091901ACEBA3633E525EE2093B0D75955843` |

本仓审查依据文件哈希：`task_plan.md` `3D37272E1935956F9D09F2152110024FAA96265E6B61E8FCE788FBF7A99402B0`；`docs/implementation/tasks.json` `55DBB8D63A27A8D8A8ACD37C46322CD0FBDCE2D5113CEEC3E416E16AA401AC0F`；`docs/implementation/acceptance-cases.json` `38642BFDBEA9C3BEBB7272D13EED6D3C4C85BEBC99D5A9C7B372CC7400E557FA`。
