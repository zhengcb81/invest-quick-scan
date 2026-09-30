# Q06 阶段 1：持久工作账本交接（2026-09-26）

状态：**只完成 StockQA 存储原语，不标记 Q06 完成**。本段实际写入限于 StockQA `src/utils/quick_scan_work_store.py`、`tests/unit/test_quick_scan_work_store.py`、`.gitignore` 的 `/quick_scan_work.sqlite*` 精确忽略行。未改 HTTP/CLI；未调用真实 API；未触碰真实 StockWiki 数据库。较早的只读审计报告写于 W03 v2 契约落地前；此处以已冻结的 v2 扩展工作键为准。

## 已实施的存储语义

- 独立 `quick_scan_work.sqlite`，`PRAGMA user_version=1`、严格完整 DDL/索引比对、foreign key 与 quick check，未知结构拒绝打开；每个连接 `synchronous=FULL`，`mark_send_intent` 事务提交后才返回 `SendPermit`。SQLite 保留工作控制、短的身份/题义/路由指纹与脱敏运输回执，不存公司主档、回答正文、网页正文、完整 prompt、URL 或密钥。
- v2 逻辑唯一键为 `(entity_id, question_id, generation, scope, scope_id, identity_revision, source_binding_version, identity_state, canonical_source_binding_refs)`；`run_id/scan_id` 多对一附着，模型和 attempt 不进入逻辑键。相同 Entity、题、代次及身份快照的 A/H 两个 prompt anchor 命中同一工作行，旧行保留首次 anchor 仅作展示；完整排序绑定集合才是键的一部分。身份修订或绑定版本变化产生新行，旧行/attempt 不重绑。相同键若题义、路由或身份快照 hash 不同则报冲突。临时身份拒绝多来源绑定。当前创建 API **并不验证**身份字段来自 StockWiki 权威投影，接入前必须由 W03/Q13 admission 做这个校验。
- `BEGIN IMMEDIATE` 原子领取、单调 `lease_epoch`/token 围栏；两进程并发仅一方成功。`prepared` 到期可在同一事务标记可审计的 `abandoned_unsent` 并回 pending；下一租约可实际 prepare 并提交 `send_intent`。一旦 `send_intent` 已提交，过期进入 `uncertain`，绝不自动回 pending；已知 408/5xx 保留 HTTP status、receipt hash、provider code、request id 作为对账证据，仍属 uncertain。旧 worker 的迟到回执仅可作为对账记录，不能覆盖新状态。
- 只有携带明确 provider 错误码及脱敏回执的 429 rate-limit/quota 拒绝可记 `confirmed_failure` 并允许同一工作行开启备用 attempt；任意 408/5xx 或无充分证据的 429 均不能作为该状态。`response_available` 尚不等于结果持久化。请求缓存键在整个账本内不可跨 WorkItem 复用，即使两行仅因 v2 身份修订而不同；同一 WorkItem 中证明未发送的重试可使用原键。未来 transport 必须先检查账本、再查询缓存/发包。

## 固定红绿回归与隔离

先增加反例后才修改实现：过期 `prepared` 在新 epoch 被旧阶段卡死；408/500/503 被误判可 fallback；429 不要求明确 provider 拒绝码；缺 `source_binding_version`/`identity_state`；v2 身份修订无法生成新 WorkItem；A/H anchor 变化导致冲突；跨身份修订复用请求键。最初核心 P1 红测 7 失败/10 通过；加入 v2 字段后旧实现 18 失败/1 通过；跨工作键缓存碰撞另有固定红测。最终本文件 **20 passed**。子进程竞争、发送意图后立即 `os._exit(0)`、注入 SQLite trigger 使意图提交失败、假 DDL、迟到回执均为真实 SQLite 测试，不 mock 事务。

全 StockQA 测试在唯一 `TemporaryDirectory` 作为 CWD/TMP/TEMP/basetemp 运行，清除 `*_API_KEY` 和 live 开关，禁 pycache、pytest cache、默认 coverage addopts，显式启用 `pytest_asyncio.plugin` 和 `pytest_benchmark.plugin`；最终 **659 passed, 2 skipped，退出码 0，临时目录已清理**。Black `--check`、Ruff `--no-cache` 均退出码 0。全仓回归中涉及系统 certifi CA 的只读访问，经隔离执行许可完成；无 live API。所有新测试数据库、子进程屏障文件、注入 trigger 都位于自动清理的临时目录。原 StockQA 工作树还有其他并行修改，本段未整理、覆盖或提交它们。

源码 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `src/utils/quick_scan_work_store.py` | `c21ea1a3b1f0c1f352578bdc4f865be4ccc150a037aa667cf534f11c276acaa2` |
| `tests/unit/test_quick_scan_work_store.py` | `8564160ee68a2fb8370143d9a2376f479c8963400ba4d4dcea2054f3c9a2829a` |

## 严格未完成的接线边界

1. `SendPermit` 是耐久意图的证明，**不是一次性 HTTP token**。当前公共 CLI/Provider 尚未调用本 store；调用方拿一个 permit 重复 POST，存储 API 本身无法拦截。下一段要在唯一 transport 边界一次性消费 permit，先持久意图后 POST，并使本地记账故障越过宽泛 `except`，禁止 fallback。所有 provider 与备用路径必须共用 WorkItem；不能仅凭此阶段声明“重启不重发”。
2. Q07 才能将回答内容、模型、时间、证据与 hash 原子 checkpoint 成 `result_ready`；Q09 预算/容量许可仍未接线；Q10/StockWiki W05 outbox、ACK、历史身份回执及观察权威入库仍未接线。此账本不能冒充公司数据库或结果库，也不能把 `response_available` 当已答。旧 `send_intent` 的人工/程序化对账及身份变更时旧未决请求如何影响新派发，还需 Q07/Q09/Q13 明确调度政策。
3. W03/StockWiki 必须提供真实可信的 `identity_revision`、`source_binding_version`、`identity_state`、完整绑定集合和资格回执；当前本地 API 只验证形状、版本与内部冲突，不能证明来源权威，也不能自动提高受影响题目的 `generation`。后续请求缓存键构造须覆盖完整 v2 逻辑键及题义/路由/搜索能力，不能仅依赖模型名；本段只拒绝已出现的跨 WorkItem 键碰撞。旧 v1 DB/交换物不能自动升级为可派发 v2。

真实资料 E2E 留待 W02/W03 + HTTP/CLI + Q07/Q10 接线后：复制 company-wiki 的 CN `002594`、HK `01211` 及 US `TSM` 的**只读**来源主档到临时目录，起临时 StockWiki 与 StockQA 库、fake provider 计数器，验证正式 issuer bridge 前后去重/身份修订、崩溃恢复、fallback 与 outbox ACK；前后比对原文件 SHA/mtime/size，结束关闭进程并清空整个临时目录。不下载财报、不写真实库、不用付费 API。此策略是计划，尚非已通过的 E2E。
