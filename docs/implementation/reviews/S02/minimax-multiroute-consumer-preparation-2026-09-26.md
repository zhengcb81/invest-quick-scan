# S02 消费者对 MiniMax 与多路由回执的预审

日期：2026-09-26。范围是本仓 `scripts/question_sets.py` 的 `screening-1` 导入、相关 schema 与 `tests/test_question_sets.py`，并只读核对 StockQA 的公开序列化字段。没有修改生产代码、外仓或调用真实 API。本报告是修复前的设计与复现记录，不是 S02 新契约的通过回执。

## 现状与固定反例

`_check_screening_execution`（当前约 956—1030 行）要求每题 `request_id` 为非空字符串，并强制 `execution.provider == result.provider.name`。StockQA 的 `QABatchResult.to_quick_scan_dict` 已把逐题实际 `provider`、`requested_model`、`response_id`、`attempts` 和搜索回执写在 `execution_receipts[question_id]`；顶层 `provider` 可为 `{"name": null, "requested_model": null}`。StockQA 的 MiniMax 搜索在 HTTP 无 `x-request-id` 时保留 `request_id=null`，但仍提供本地 `attempt_id`、厂商 `response_id`、已完成搜索调用的 `search_receipt_id`。多路由尝试还含 `provider/requested_model/route_id/route_ordinal/policy_version/route_trace`。本仓 `schemas/quick_scan/score.schema.json` 约束标准化后的评分及核验等级，不定义 StockQA 的整个执行回执；`schemas/observation.schema.json` 是另一条 `standard-1` 观察协议。两个 schema 均不能代替当前 S02 的回执检查。

以下复现调用现有 `QuestionSetTests.make_screening_manifest/make_screening_bundle` 和 `normalize_screening`，所有问卷输出都在自动清理的 `TemporaryDirectory` 内，使用虚构来源，没有网络：

| 固定输入变异 | 当前实测输出 | 应有结果 |
|---|---|---|
| 顶层与逐题 provider 均为 `minimax`；`IQS_01` 的逐题与最终 attempt 都为 `request_id=null`、`actual_model=MiniMax-M3`，其余非空 `response_id/attempt_id/search_receipt_id` 与已完成搜索、来源、prompt hash 都保持一致 | `screening_status=unusable`，`execution receipt is missing request_id` | 在核实 MiniMax 实际路由与完整搜索链后 `screening_checked`；`request_id` 继续保持 null，不补造值 |
| 同批 `IQS_01` 由 OpenAI、`IQS_02` 由 MiniMax 回答，逐题 provider/model/最终 attempt 对齐；顶层 `provider.name=null` | 两题均 `unusable`，`execution provider does not match the scan envelope` | 两题分别按自身执行回执核验并保留实际 provider/model；顶层 null 只表示没有单一厂商，不能当作失败 |

顶层首选 provider 非空而某题经过 fallback 改由备用 provider 答复时，也会被相等条件拒绝；StockQA Q04 的公开结果将顶层配置偏好与逐题实际路由分开，消费者需要按这一语义解释。当前测试工厂只产生单一 `openai` 且所有 request ID 均为字符串，因此未覆盖这些合法输出。

复现所用的两处关键变异（`m, _ = make_screening_manifest()`、`b = make_screening_bundle(m)` 后分别在独立新 bundle 上执行）为：

```python
# MiniMax：先把整个 fixture 的 provider/model 改为 MiniMax，再改变第一题。
b["result"]["provider"] = {"name": "minimax", "requested_model": "MiniMax-M3"}
for receipt in b["result"]["execution_receipts"].values():
    receipt["provider"] = "minimax"
    receipt["requested_model"] = receipt["actual_model"] = "MiniMax-M3"
    receipt["attempts"][-1].update(provider="minimax", requested_model="MiniMax-M3", actual_model="MiniMax-M3")
r = b["result"]["execution_receipts"]["IQS_01"]
r["request_id"] = r["attempts"][-1]["request_id"] = None

# 多路由：另取干净 bundle，保留 IQS_01=openai，令 IQS_02=minimax。
b["result"]["provider"] = {"name": None, "requested_model": None}
r = b["result"]["execution_receipts"]["IQS_02"]
r["provider"] = "minimax"
r["requested_model"] = r["actual_model"] = "MiniMax-M3"
r["attempts"][-1].update(provider="minimax", requested_model="MiniMax-M3", actual_model="MiniMax-M3")
```

这只是**修复前复现**；修复后的多路由正例还要在最终 attempt 添加与 `route_trace` 一致的 `route_id/route_ordinal/policy_version`，以验证实际派发路线。

## 最小修订的 fail-closed 条件

1. 顶层 `result.provider` 必须仍为对象；`name/requested_model` 可以同为 null，或同为非空字符串。若非空，它们表示配置偏好，不应作为逐题实际厂商的硬性相等条件。每个成功题的 `execution.provider`、`actual_model`、`response_id`、`attempt_id`、`prompt_sha256`、`input_question_sha256`、`search_receipt_id` 仍必须非空且格式正确；新多路由逐题 `requested_model` 也必须非空。空、空白、数组和数字不能视为合法路由值。
2. 保留旧单厂商兼容分支：当顶层 provider 名与逐题 provider 一致，而且最终 attempt 没有 route 字段时，沿用现有的 request ID、最终 attempt、搜索调用、时间、来源绑定检查。这个分支不能让顶层 null 或实际 provider 与首选 provider 不同的记录越过路由核验。
3. 对顶层 null 或逐题 provider 不等于顶层首选 provider 的新路由分支，要求最终 attempt 的 `provider`、`requested_model`、非空 `route_id` 与逐题回执相符；`route_trace` 中该路由必须是最终获接纳的 `accepted_answer`，且其 provider/model/route ID 与最终 attempt 一致。`attempt_id`、response ID、实际模型、prompt hash、搜索状态/ID、HTTP 状态与逐题回执保持现有逐项相等；不能仅凭顶层 null 就信任任意 provider 字符串。若上游未提供足以证明实际 route 的字段，该题保持 `unusable`，不授予 `screening_audited`。
4. `request_id=null` 仅对已验证为 MiniMax 路由的完成答复放行，且最终 attempt 的 request ID 也必须为 null；其他 provider、空字符串、缺失字段、逐题与最终 attempt 不一致都拒绝。MiniMax 的非空 `response_id/attempt_id/search_receipt_id`、HTTP 200、completed、`search_status=executed`、唯一已完成搜索调用与答案证据 URL 的交集/包含检查继续全部执行。以后别的厂商若证明 HTTP request ID 可合法缺失，应扩展版本化能力表及测试，不泛化为任意 provider 都可缺失。
5. 若新的 `dispatch_outcome` 存在，只有 `scope=provider_dispatch,state=completed` 能支持成功题；`uncertain`、`retry_wait_recommended`、`setup_required` 等不能授予核验等级。旧单厂商回执尚无此字段，可沿原证据链兼容。不要由模型回答自报的 check level 或仅含 URL 的正文替代执行回执。

这些条件只提升有完整执行证据的题。缺回执、来源错绑、模型题目不符、HTTP 未成功、最终尝试与逐题回执不一致时，仍只留下 `reported_score` 并使有效 `score=null`；不得生成 `screening_audited` 回执。S02 无法仅凭结果 JSON 独立证明配置 provider 名与实际 HTTP 端点同属一家厂商；这一生产侧身份绑定仍需 StockQA 的 Q02/Q04 上游校验，不能在本仓假设已解决。

## 固定测试矩阵与最小文件范围

在 `tests/test_question_sets.py` 复用现有 screening fixture，并在唯一临时目录内增加以下 case；正例需断言分数 8、`screening_checked`、有受信 check-level 回执，负例需断言 `unusable`、有效分数 null、无新签发回执：

- MiniMax `request_id=null` 且最终 attempt 同为 null、其他 IDs/搜索来源/route_trace 完整：正例。把 provider 换成 OpenAI、把 response ID 或 search receipt 置空、把最终 attempt request ID 改成字符串、把 `route_trace` 的最终 route 改为其他厂商：分别为负例。
- 同批两题 OpenAI + MiniMax、顶层 `name/requested_model=null`，两题最终 route 与逐题回执一致：正例。删除任一题的最终 provider/route ID、交换两题 final attempt、把 source URL 绑定到另一题搜索：分别为负例。
- 顶层首选 OpenAI、某题最终 MiniMax fallback 且逐题/最终 attempt 及路由 trace 一致：正例；route trace 仍指首选 OpenAI 时为负例。
- 原有单 OpenAI 顶层/逐题一致且历史 fixture 最终 attempt 不含 route 字段：仍为正例。`dispatch_outcome` 为 `uncertain` 但响应字段伪造 completed：新回执负例。

生产最小修改预计仅 `scripts/question_sets.py::_check_screening_execution`；测试只增 `tests/test_question_sets.py`，契约说明可在 `references/stockqa-integration.md` 更新。若要让 JSON Schema 本身描述 StockQA 导入 envelope，可另立版本化 `schemas/quick_scan/screening-import.schema.json` 并在导入前验证；当前仓内没有这一 schema，不能误改现有评分或观察 schema 来解决。新 schema 不是这两个固定反例的最低必要范围。任何实施完成后必须运行本仓 screening 定向/全量离线测试和现有 StockQA 公共 CLI mock 集成，重新审查最新代码；本预审不计为通过。
