# S02 MiniMax / 多路由消费端红绿验证

日期：2026-09-26。本回执只对应本仓 S02 消费端修复，不代表 S06、StockQA、真实搜索或跨仓全链通过。测试命令均在 `C:\Users\郑曾波\Projects\invest-quick-scan` 运行，`python -B -X utf8 -m pytest -q --no-cov -p no:cacheprovider --basetemp <唯一系统TEMP子目录> ...`；每次运行将 `TEMP/TMP/PYTHONDONTWRITEBYTECODE` 指向隔离根，验证根路径留在系统 TEMP 后在 `finally` 删除并恢复环境变量。未调用真实 API 或写外仓。

| 阶段 | 测试选择 | 原始结果 |
|---|---|---|
| 红测，代码未修 | `tests/test_question_sets.py -k 'screening_accepts_minimax_completed_search_without_http_request_id or screening_accepts_mixed_actual_providers_with_null_batch_provider or screening_new_route_receipts_reject_forged_evidence_or_execution'` | `2 failed, 1 passed, 45 deselected, 6 subtests passed`；MiniMax 被 `execution receipt is missing request_id` 拒绝，顶层厂商为 null 的混合批次被 `execution provider does not match the scan envelope` 拒绝。 |
| 绿测，修复后 | 同上 | `3 passed, 45 deselected, 9 subtests passed`。 |
| S02 文件回归 | `tests/test_question_sets.py` | `48 passed, 102 subtests passed`。既有单厂商真实 StockQA CLI mock 集成与清理测试同在该文件。 |
| 全仓回归 | `tests` | `273 passed, 158 subtests passed, 1 failed`；唯一失败为 S06 的 `tests/test_routing.py::RouteSchemaTests::test_v2_cannot_use_unavailable_to_select_objective_module`：测试预期 `ValueError`，实际由 route schema 抛 `jsonschema.ValidationError`。已报给 S06 拥有者，不在 S02 范围改动。 |

新增 S02 负例覆盖：伪造不在已完成搜索调用中的证据 URL、缺最终 attempt、最终 attempt 真实厂商与逐题回执不符、OpenAI 无 request ID、MiniMax 无 request ID 且最终厂商无证明、缺路由 ID、模型不符或未知、未完成 `dispatch_outcome`、未验证搜索。失败记录仍保留 reported 值但有效分数为 null，不签发 `screening_audited` 回执。旧单厂商 fixture 无 cascade 路由字段，仍可通过；新混合回执以最终 attempt 的真实 `provider` 核对逐题回执，`provider_config_ref` 只作别名。

静态核对：`scripts/question_sets.py` 与 `tests/test_question_sets.py` 均可 `ast.parse`；限定文件 `git diff --check` 退出码 0，仅有 Git 的 LF→CRLF 提示。初版文件 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `scripts/question_sets.py` | `3551AC9DF259C79293696EE9EEC392083E860B74E5EB1FD6C73C38E73C9F3A28` |
| `tests/test_question_sets.py` | `AC0D1E18EEFBE2DBDD13E664E7456CB13498441846102D0D3DA1A5F1D5557FA5` |
| `references/stockqa-integration.md` | `CDA1C5E8323964313F1873D61D89BF9C1E3416A230AA701A190B6B142700DB7E` |
| 预审报告 `minimax-multiroute-consumer-preparation-2026-09-26.md` | `E565D34AAB026684F584EDA5EF0E08FC576CE869CFE19E99BAD5BBCA7E38AB84` |

这是实施者验证；独立复审最新代码与 StockQA 最终公开序列化形状仍待完成。上游若变更字段，须按实际回执重新运行本组正反例与公共 CLI 集成。

## 补充对抗回归与真实直连兼容

复审准备时固定三个原可误收的回执：单厂商级联有路由标记但 `dispatch_outcome=null`；同类回执最终 attempt 缺真实 `provider` 或请求模型；混合厂商回执的最终 `route_trace` 为 `provider_failure` 却自称已完成。先补断言，首轮定向红测为 `4 failed, 2 passed, 47 deselected, 10 subtests passed`。另补“前一次 attempt 留有级联路由标记、最终 attempt 却删掉路由并声明直连”的反例，单测红测为 `1 failed, 1 passed, 48 deselected, 3 subtests passed`。这些红测失败均在预期的 `screening_checked` 误收断言上。

修复后，任一 attempt 的 `route_id`、`route_ordinal`、`route_trace` 都会触发级联验证；最终 attempt 必须同时给出真实厂商、请求模型及完整路由身份，公开 `route_trace` 的末项必须是与最终路由一致的 `accepted_answer`，`dispatch_outcome` 必须为 `completed`。非级联直连的 StockQA 真实公开形状只有 `provider_config_ref` 别名，且 `dispatch_outcome=null`、最终 attempt 无请求模型；该别名本身不触发级联验证。曾因将别名误作级联标记造成真实 CLI 离线集成 1 项失败，现以该集成用例和模拟 MiniMax 直连用例固定兼容边界。未知实际模型、未完成搜索、伪造证据依旧不计分。

最终使用唯一系统 TEMP 子目录、`--basetemp`、禁止字节码并关闭 live E2E，完整运行 `tests/test_question_sets.py`：`49 passed, 107 subtests passed`，退出码 0；TEMP 在 `finally` 删除，`TEMP_CLEAN=True`。无真实 API 请求、无外仓写入。`ast.parse` 两个 Python 文件成功，限定文件 `git diff --check` 退出码 0（仅 LF→CRLF 提示）。最终 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `scripts/question_sets.py` | `EA0B27D45EDDC1C43FD57B69DA69AB22545A67F87E475960E168FD5CDB5C3B35` |
| `tests/test_question_sets.py` | `7B9BA65164B09C2AA40993BDFD6E4233207247F237A3CA89F24E82630A0F5107` |
| `references/stockqa-integration.md` | `F09BBDF7DBC432E80E885124695D0DB9372E19BE9A5D946374A1885AE092EB87` |
