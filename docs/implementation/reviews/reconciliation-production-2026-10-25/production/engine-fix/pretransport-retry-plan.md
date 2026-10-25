# 原检索尚未进入 HTTP 的显式恢复计划

2026-10-25，仅计划与只读调查，本文没有执行任何结算、租约恢复、检索或模型请求，也没有改生产源码。沿用 `runs/r25-live/work.sqlite` 原账本、原 owner/action、原预算和原 work，不创建新库或重置限额。

## 已核实事实与边界

根总控确认第一次 cold 的实验包装 `ObservedWire` 只实现 `post`，但原 `ExternalSearchProvider.fetch` 调用 `session.request`。该属性解析抛出 `AttributeError`，没有调用底层 native HTTP；模型 attempt 为 0。这是实验观测包装错误，不是搜索服务拒绝。需由总控保留原 driver/source pin、异常类别和验证 native request 调用为 0 的离线测试证据后，才可用 `confirmed_not_sent` 结算；不可仅凭时间短、缺回答或网络超时推断未发送。

只读观察（2026-10-25T10:22:25Z）：

- 原 work 为 `leased`，epoch 1，真实租约到期时间 `2026-10-25T10:48:06.134260Z`；native attempt 0。
- 原 external operation 1；其预算为 `outcome_uncertain`、`request_counted=1`、`in_flight=1`、费用未定。
- `cancel_pending` 仅接受 pending 并变为 cancelled；`recover_expired` 未到期时原样返回 leased；`claim_refresh_action_batch` 仅接受 pending。当前公开 API 没有主动释放仍有效 lease 的方法。
- `resolve_known_response` 需要原 native response 且租约到期，不适用于 model 0；`record_owner_retry_decision` 不是释放 lease 的入口。
- 不增加 `restore_unsent` 或 lease 旁路；不改时钟、不改 SQLite、不重建 `services._handles`。

本次实际标识：

```python
WORK_ID = "WORK_aa08087ac3994ac4b0b814707a69d243"
OPERATION_ID = "SEARCH_2c4c57fbb9108efc2bbc6407cc4d6482ebd85e6f6a49d839f141d395a0e464cc"
BUDGET_ATTEMPT_ID = "DISPATCH_201eea6bde743e876f92d2bbc45b839f4e9bcd210c64ed0291124ecdff327441"
POLICY_ID = "shared-production-search-isolated-20261025-r2"
POLICY_VERSION = "external_budget/1.0.0:262ae594b27186391712503a2fa23e7bc4017e74710f4e0231d5bc48aaba5f55"
QUESTION_ID = "IQS_05"
ORIGINAL_QUERY_ID = "Q_IQS05_REAL_20261025"
RETRY_QUERY_ID = "Q_IQS05_REAL_20261025_LOCAL_NOT_SENT_RETRY_1"
ORIGINAL_TASK_SHA256 = "a524cb5be41d06afb6ab25d4bd469aa1c8d24574fb0696b12f745823ef227657"
```

## 1. 在原账本结算已证实的未发送

使用从原 `prepare_execution` 得到的 `owner.service.store`，不得重新指定其他 work store。结算前确认旧 operation、原 receipt、原 dispatch、预算和 work 仍对应上述标识，并留存薄 hash/计数。`audit_source_ref` 必须引用已落盘的本地 0-transport 证据及其 SHA，长度不超过 300；不要把示例占位符当证据。

```python
old = store.get_external_search(OPERATION_ID)
assert old["work_item_id"] == WORK_ID
assert old["budget_attempt_id"] == BUDGET_ATTEMPT_ID
assert old["budget"]["policy_id"] == POLICY_ID
assert old["budget"]["policy_version"] == POLICY_VERSION
assert old["result"]["receipt"]["outcome"] == "unknown"
assert old["result"]["receipt"].get("failure_type") == "AttributeError"
assert store.list_attempts(WORK_ID) == []

# audit_source_ref: 总控已落盘审计证据的实际引用，不能伪造 provider 回应。
settled = store.reconcile_budget_attempt(
    BUDGET_ATTEMPT_ID,
    resolved_outcome="confirmed_not_sent",
    actual_cost=0,
    cost_source_ref=audit_source_ref,
)
assert settled["status"] == "settled"
assert settled["actual_cost_micros"] == 0
assert settled["request_counted"] == 0
assert settled["in_flight"] == 0
assert settled["cost_source_ref"] == audit_source_ref

kept = store.get_external_search(OPERATION_ID)
assert kept["context_sha256"] == old["context_sha256"]
assert kept["dispatch"] == old["dispatch"]
assert kept["result"] == old["result"]
assert kept["result"]["receipt"]["outcome"] == "unknown"
```

该原公开方法会写入 `quick_scan_budget_terminal` 的 `confirmed_not_sent` 记录，并将原预算行审计结算；这不是删除或重写原 unknown receipt。原 external operation/result/dispatch 都不可变、保留。以相同参数再次结算应幂等；换结算结论或引用应被拒绝。还应读取 `get_quick_scan_budget_status(POLICY_ID)`，确认保留原 policy/version/上限，当前请求计数和保留费用按原 API 结算，没有创建新的 policy_id 或库。

## 2. 审计后建立新的检索操作，预算身份保持不变

仅结算不足以重发旧 key。旧 receipt 仍 unknown，同 key 会命中不可用旧结果；原 dispatch 的一次性许可已经消耗，不能再次 consume。

保留原 search-policy 文件及其 SHA，生成单独的已审阅 retry search-policy 文件。仅将对应 query 的 `query_id` 改为 `RETRY_QUERY_ID`，其 query 文本、question_ids、实体/身份/manifest/cutoff、route、credentials env 名、pricing/metering/dispatch/limits 全部保持原值。将“已证实 local not-sent、修复包装后明确重试一次”与旧 operation/budget ID 绑定在薄审计记录；这不是对仍无法查明的付费请求重试。

```python
from src.config.quick_scan_search_policy import load_search_policy
from src.utils.quick_scan_external_context import build_shared_external_budget_policy

retry_search = load_search_policy(retry_search_policy_file)
assert retry_search.execution_plan["queries"][0]["query_id"] == RETRY_QUERY_ID
retry_composite = build_shared_external_budget_policy(model_budget, retry_search)
assert retry_composite == original_confirmed_composite_budget
```

原 `build_shared_external_budget_policy` 的 version basis 仅包含 model-budget SHA 和 external routes 的 route/kind/dispatch/pricing/metering。query、query_id、manifest、TTL 等属于每次检索，不进入预算 version。因此本次仅 query_id 修订可以得到不同 search policy SHA、cache key 与 operation ID，同时 **原预算完整字典/字节文件/身份/version/限额不变**。不得覆写已经 confirm 的 `budget-policy.json`。

原 `_assert_no_unknown_scope` 在旧 budget 已经通过上述 API 结算为明确 terminal 后允许新的检索 admission。新 `begin_external_search` 仍走原 reserve、同一共享账本和同一路由；新请求独立计数。旧 unknown 不可拿来构建成功 context，模型只能使用新操作的实际结果。

本路径不使用 `register_external_research_continuation`：该接口仅面向 sealed 研究任务的严格未派发差集、要求 research-only，并禁止把同一个已 dispatch semantic slot 伪装成新研究 slot；它不是本次生产 owner 的恢复授权。

## 3. 真实到期后恢复原 work，再交回原 batch claim

原 lease 有效期间不 claim、不取消、不续租、不改到期时间。等待真实时钟达到原到期时间；等待期间可以完成证据/PWF/交接和离线包装修复。

```python
import time

item = store.get_item(WORK_ID)
assert item["status"] == "leased"
assert time.time() >= item["lease_expires_at"]
assert store.list_attempts(WORK_ID) == []
assert store.get_external_search(OPERATION_ID)["budget"]["status"] == "settled"

assert store.recover_expired(WORK_ID) == "pending"
pending = store.get_item(WORK_ID)
assert pending["status"] == "pending"
assert pending["lease_token"] is None
assert pending["lease_expires_at"] is None
assert pending["lease_epoch"] == item["lease_epoch"]
assert pending["generation"] == item["generation"]
assert store.list_attempts(WORK_ID) == []
```

此原方法仅在 native attempt 不存在 send_intent/uncertain/response_available 时把到期 work 恢复 pending；若调查期间出现原 native attempt 或状态变化，停止并重新只读核查，不能按本计划硬推进。

随后重新执行原 public `prepare_execution`、原 task factory 和 `OwnerResearchServices(..., owner_batch_claim=True)`；lifecycle 的 external_retrieval 使用 retry search policy，model_policy 仍为未合成原 model budget，lifecycle/owner budget 仍为已 confirm 的原合成 budget。由 `execute_shared_engine` 的原 generation_scope 自动调用下列公开链路：

```python
# 原服务内部实际调用；不是让driver先手动claim。
owner.claim_registered_question_batch(
    [QUESTION_ID],
    run_id=owner.record["inputs"]["run_id"],
    scan_id=owner.record["inputs"]["scan_id"],
    lease_seconds=1800,
    dispatch_deadline=None,  # 原 r25-live lifecycle 未设置单独 dispatch deadline。
)
```

不要在 driver 提前调用这个 claim 后再进入 engine，否则 engine 的原 claim 会因 work 已 leased 拒绝；也不要把返回值写进私有 `_handles`。原实现仍会独立执行当前 owner 权限、预算、lease 和 transport 检查。

## 4. 使用 fresh session，不冒充已有模型缓存恢复

旧 `cold-session`、pending checkpoint/history、原 source pins 和 unknown receipt 完整保留。当前 native model attempt=0，没有可供 `resume_shared_engine` 重放的 safe response；原 resume 正确拒绝 `native_safe_output_required_never_resend_unknown`，不能改它放行。

修复并离线验证完整观测包装后，由 driver 的显式 retry phase 使用新的 session/export 路径（例如 `retry-cold-session`），原 owner/work/run/scan/task 保持一致。driver/source-pin 列表修订须留存原列表及新列表，新的真实 cold 与后续 recover 都绑定同一份 retry pin 列表。不要删除旧 session、修改其 checkpoint 或把 retry 当作原 cache hit。

新的真实 cold 产生原 native safe response 后，才能执行原 `resume_shared_engine` → `finalize_shared_engine` → repeated finalize 的断网恢复验收；原模型与搜索预算记录继续在同 `work.sqlite` 中计数。

## registered task 哈希核实

已按当前源码核实：

- `scripts/shared_company_task.py:create_company_scan_task` 不读取 `lifecycle._external_retrieval` 或 search-policy 文件；task.raw 中不包含 external query/query_id/search policy SHA。
- 它生成的 native pack group key 仅来自原实体、公司元数据、scope/scope_id/perimeter；不包含检索 policy，也不包含 lease token/epoch。
- `OwnerResearchServices` 以 `canonical_sha256(task.raw)` 注册 task。原 cold task bundle 中 task SHA 为上面的 `ORIGINAL_TASK_SHA256`。
- 因此仅更换 external query_id，并保持原 owner inputs、run/experiment/limits/questions/board/route 等 factory 参数一致，**不会改变 registered task SHA**。新 lease epoch 也不进入该 task SHA。

这项结论是源码与原 bundle 的只读核实，不冒充已经执行了真实重试。重发前必须用重建的原 task 再做运行时等值断言；不一致则停止：

```python
from src.utils.quick_scan_result_outbox import canonical_sha256

assert canonical_sha256(task.raw) == ORIGINAL_TASK_SHA256
assert task.task_sha256 == ORIGINAL_TASK_SHA256
assert retry_composite == original_confirmed_composite_budget
assert owner.service.store.get_item(WORK_ID)["generation"] == original_generation
```

本次一次性恢复无需增加生产接口。下一个验收仍是同账本、同预算、原授权 work 的真实检索/模型结果及正式封包，然后是无网络、无新增请求的缓存恢复。
