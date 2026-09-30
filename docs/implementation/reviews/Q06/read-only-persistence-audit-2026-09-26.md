# Q06 持久逻辑待办：只读实施审计

状态：**设计/只读审计，未实施 Q06，未运行 Q06 测试或真实 API**。本报告只规划 StockQA 执行状态；公司身份、名单和观察仍由 StockWiki 唯一权威库拥有。当前 Q06 的计划前置 `G2` 尚需按原门槛验收，不得把本报告当作解除前置依赖的回执。

## 现有路径与必须补上的断点

- 当前公共快扫路径是 `LLMRunner._run_single_company` → `QAEngine.process_questions` → `OrderedSearchProviderCascade.search_question` → `LLMProvider.search_question` → `LLMClient.send_search_request`。`LLMRunner` 一次处理完全部问题后才 `output_results` 写一个 JSON；中途崩溃没有逐题可靠检查点。`--require-search` 只支持单公司入口，不能凭进程退出码判定每题完成。
- Cascade 已有按题顺位 fallback 和模型健康 SQLite；`quick_scan_health.sqlite` 仅保存 route/group 冷却及半开探针，不保存 `(entity, question, generation, scope)` 的逻辑任务、租约、run 引用或已付费的回复。其严格表结构校验也禁止直接在同一 DB 中偷加 Q06 表。
- HTTP 客户端在调用 `session.post` 前才生成临时 UUID，尝试回执要等请求返回才交给上层。Cascade 的 `sent_attempts` 也只在 `provider.search_question` 返回后汇总。因此仅在外层“调用前/调用后”包一层事务，无法分辨崩溃发生在网络发送前还是发送后，更无法安全地让 fallback 共用同一逻辑任务。
- C04 的逻辑键固定为 `(entity_id, question_id, generation, scope, scope_id)`，与包含实际 provider/model、prompt、题义、路由、截止日、搜索能力的 `request_cache_key` 分开；状态为 `pending/leased/uncertain/result_ready/delivered/failed/cancelled`。`run_id`、`scan_id`、model 与 attempt 不进入逻辑键。资料不足答案已投递后处于调度冷却，不能冒充 `uncertain` 请求。Q06 应在 StockQA 将这些规则落到 SQLite，而非复制 C04 纯函数作为“数据库实现”。
- 现有 C04 `work.schema.json` 尚没有 C01 v2 的 `identity_revision`/来源绑定。W02/W03 临时身份设计要求派发时冻结身份修订，旧身份合并后旧请求只能成为历史，不得把旧观察用于新 Entity 的当前白名单。因此**先由本仓契约 owner 升级 C04/交换字段，再验 Q06 的真实身份输入**；兼容 v1 的历史读取不得自动升级成可派发 v2。

## 边界与可执行状态机

StockQA 可有自己的 `quick_scan_work.sqlite`，但其中只存执行控制、短元数据和待投递引用，不是第二个公司主档或结果查询库。StockWiki 事务性提供具有 `identity_state`、`identity_revision`、准入理由、`entity_id/security_id` 与 `source_binding_ref` 的可信派发快照；StockQA 把快照的版本/哈希/必要键不可变地绑到 WorkItem。用户输入、LLM 回答、ticker、名称或 company-wiki 快照不能自行声明扫描资格。失去可信快照或身份被撤销时暂停**新**发送；已发送的原身份结果仍可按原修订结算为历史。

建议 Q06 首版数据表为 `work_item`（唯一逻辑五元组、冻结身份修订/来源绑定、题义和路由指纹、状态/lease_epoch/token/expiry、结果引用）、`work_run_ref`（多 run/scan 对同一 item 的幂等引用）、`attempt`（每次实际 HTTP 请求的唯一 ID、provider/model/route、请求键/prompt hash、`prepared/send_intent/response_recorded/uncertain/reconciled` 阶段、脱敏回执）、`work_event`（追加状态与围栏冲突事件）。版本化 DDL、事务内完整性校验和明确迁移/拒绝未知版；不存密钥、完整 prompt、网页正文、财报文档。Q08 的健康 DB 可继续独立存在，派发许可必须同时通过 work lease、健康状态和未来 Q09 预算槽；未取得全部许可时零 HTTP 请求。

一次原子 `create_or_attach` 以逻辑五元组唯一约束去重，给多个 run/scan 追加引用；同题不同刷新代次才是新 item。`claim` 使用 `BEGIN IMMEDIATE` 或条件更新加单调 `lease_epoch`，只一个进程成功。派发前先在持有租约的事务中固定 provider/model、attempt ID、prompt hash 和 request key，再**持久标记 `send_intent` 后才进入唯一一次 HTTP POST**。标记与真正发送之间崩溃虽可能未计费，也必须保守视作 `uncertain`；只在能证明 `prepared` 尚未进入发送意图时回 `pending`。未知结果不因租约超时而换模型竞速重发；须用同一 attempt 对账、明确无发送/无执行证据或人工处理。

每次明确的 provider 失败、429 或配额拒绝记录到同一 WorkItem 的新 attempt；健康状态和 fallback 顺序独立控制下一次尝试。成功/正常低分/已证实资料不足立即停止 fallback。`run_id`、`scan_id`、备用模型都不创建新逻辑 item；备用尝试的请求缓存键必须不同。客户端/Provider/Cascade 的回调必须显式传递可信 `work_item_id + lease_epoch/token`，不得从题目文本、模型输出或可编辑 JSON 推断。DB/围栏回调故障需抛出专用**禁止重试/禁止 fallback**错误；现有 Provider 的宽泛 `except Exception` 不能将本地记账故障变成第二次收费请求。

迟到的旧 worker 不能用旧 token 把新租约覆盖成 `result_ready`/`delivered`。若旧 attempt 确有真实响应，应单独保留其脱敏回执为对账候选，不抹掉已付费结果；后续由当前 item/身份修订校验决定是否采纳为**原身份的**结果。`result_ready` 必须在轻量观察和其哈希已经耐久保存后才出现；Q07 负责逐题成功负载检查点，Q10 负责版本化 outbox 与 StockWiki ACK。Q06 单独只实现任务/租约/尝试状态时，不得宣称已达“已回答题重启不重问”的生产闭环。

## 最小分段与 StockQA 精确文件范围

| 阶段 | 建议文件 | 可审查交付 |
|---|---|---|
| 0. 本仓先行契约（非 StockQA 写入） | `schemas/quick_scan/work.schema.json`、`docs/implementation/contracts/freshness-and-jobs.md`、`tests/test_freshness_and_jobs_contract.py`；按 C01 修订观察/交换契约 | 新 v2 work 绑定身份修订、来源键、派发快照版本；v1 仅历史读取；冻结字段后才锁 Q06 DB DDL。 |
| 1. Q06 存储核心 | 新增 `StockQAbyLLM/src/utils/quick_scan_work_store.py`；新增 `StockQAbyLLM/tests/unit/test_quick_scan_work_store.py`；修改 `StockQAbyLLM/.gitignore` 精确忽略默认 work SQLite | 唯一逻辑键、run/scan 引用、租约围栏、尝试意图、合法转移、未知态对账、故障注入和版本校验。与 Q08 `quick_scan_health.sqlite` 分库，路径可注入测试目录。 |
| 2. Q06 发包边界 | 修改 `StockQAbyLLM/src/providers/llm_client.py`、`src/providers/llm_provider.py`、`src/utils/llm_integration.py`；修改 `tests/unit/test_llm_client.py`、`tests/unit/test_llm_integration.py` | 从可信调用者显式传递 attempt observer；每个 HTTP POST 恰一个先落盘 attempt ID，回执先持久化再允许 fallback；围栏/存储故障不被宽泛重试吞掉。保持普通非快扫 API 兼容。 |
| 3. Q06 运行入口 | 修改 `StockQAbyLLM/src/runners/llm_runner.py`、现有 `tests/integration/test_quick_scan_cli.py`；必要时扩展 `tests/unit/test_llm_runner.py` | 仅 `--require-search` 接入持久 work admission、生成/显示 run_id、重复启动不重复领取、恢复只领取已证实未发送的可重试 item；现有单公司 JSON 仍是兼容输出，不把它视为 Q07/Q10 的正式逐题 checkpoint/outbox。 |
| 4. 后续卡的清晰边界 | Q07 持久逐题结果，Q09 预算/容量，Q10 outbox/ACK，W05 事务导入 | 这四项各自另验收；不得把 Q06 的 SQLite 行当作 StockWiki 权威观察，亦不得将 Q08 的 `retry_wait_recommended` 宣称为已调度。 |

如果先只做阶段 1，可验数据库事务与并发，但**不算公共入口完成**。阶段 2–3 需要同一独立审查快照：不应出现一个进程路径仍调用未受控的 `LLMClient.send_search_request`。默认 work DB 可放在 StockQA 配置旁，像 Q08 健康库一样让测试注入 `tmp_path`；若多实例共享同一工作池，须配置为同一受控文件并使用 SQLite 锁，而不是每个进程各建一份导致重复收费。

## 固定红/绿案例（红测先记录旧行为）

| 案例 | 固定输入与故障注入 | 绿线断言 |
|---|---|---|
| `JOB-01` | 两个 `run_id`、同一 Entity/Question/generation，第二次用备用模型；另建下一代及同 Entity 的证券级题 | 第一组只有一 WorkItem，run 引用两条；下一代新 item，证券作用域不相撞。 |
| `JOB-02` | 两进程 barrier 同时 `create_or_attach/claim`；时钟推进到租约过期，旧进程迟到提交 | 仅一有效 token；`lease_epoch` 增长；旧 token 零状态覆盖，冲突事件可查。 |
| `PAR-05` | 两 run 并发启动同题，唯一 fake HTTP endpoint 原子计数；重启后再点 start | 最多一次原始 POST；第三次 0 POST，fallback 不新建 primary work。 |
| 发送前崩溃 | `prepared` 已提交，尚未写 `send_intent` 就杀子进程 | 租约过期后可证实未发送，回 pending 后由新租约发送一次。 |
| 发送意图崩溃 | `send_intent` 提交后、HTTP 前或 HTTP 已受理后杀进程 | 两种均 `uncertain`，重启无自动 POST/fallback；保留同一 attempt/request key 待对账。 |
| 明确拒绝后 fallback | A 返回可分类的 HTTP 429/配额拒绝，B 搜索且评分 8；两次发送共用一 item | A/B 各独立 attempt、实际模型/时间/失败类别完整；B 成功后不再发 C，不把 A 的冷却清掉。 |
| 非明确错误 | socket timeout/连接断开，HTTP 是否到达不可证 | attempt 为 `uncertain`，不立即 fallback；未来预算预留不释放。 |
| `JOB-08` | 错 item/hash ACK、重复 ACK、直接 pending→delivered、旧 lease 试图 delivered | 全部拒绝非法跃迁；正确 ACK 只由 Q10 在结果已落盘后终结。 |
| 已答/未知区分 | 收到联网核实但资料不足、`next_retry_at` 未到；另有未返回的 uncertain 请求 | 前者仅调度 `deferred_unknown`，后者必须先对账；unknown 不能自动变 5 分或 fallback。 |
| 身份修订 | 临时 `ENT_A@r1` 在工作中被 W03 桥接至 `ENT_B@r2` | 停止新发旧对象；旧 attempt/结果仅按 `ENT_A@r1` 历史保存；`ENT_B@r2` 不继承旧分数/待办 ID。 |
| 失败注入 | SQLite `COMMIT` 失败、未知 schema 版本、伪造 DDL、损坏外键 | 发送前 fail closed，零 POST，原数据库字节/行可恢复；不生成“成功”回执。 |
| Q07/Q10 交接 | 已落盘 `result_ready`，StockWiki 不可用/ACK 丢失；随后重启 | 仅重投完全相同的 item/hash/outbox，不重新发模型；同键异 hash 隔离冲突。 |

本段最后一项属于 Q07/Q10 联合验收，不应拿 Q06 单卡测试冒充完成。以上用真实 SQLite + `multiprocessing`/子进程屏障，fake HTTPS 响应只替换网络边界；不能 mock 掉 `claim`/事务/状态机后仍宣称并发通过。测试还需证明旧单公司 CLI 和非快扫模式结果不变。

## 隔离的真实资料 E2E 路线

后续 W02/W03 提供可信临时身份投影后，取 company-wiki 真实证券主档快照的**只读副本**做一次无网络系统测试：CN `002594` 与 HK `01211` 来源行确实存在，但在官方 bridge 核实前应各自独立，不能靠同名或号码合并；US `TSM` 可作为第三市场边界样本。先核对原快照 SHA-256、mtime、大小，复制到 `TemporaryDirectory`；在其中建立 StockWiki 临时 SQLite、StockQA 临时 work/health SQLite 和隔离配置，明确写入可审计的临时准入声明。fake provider 返回真实结构的 `web_search_call`/来源 URL/评分，真实执行公共 CLI 两次并在指定边界杀子进程、再恢复；统计 HTTP POST、WorkItem、attempt、run 引用、身份修订和结果 hash。结束后重核原快照哈希/时间，关闭连接与子进程，再由临时目录自动清理所有副本/SQLite/WAL/SHM/输出。**不执行 `--refresh`、不下载、不调用付费 API、不写真实 StockWiki 库**。W02/W03 未实现前只能做使用冻结可信身份 fixture 的 StockQA 离线集成，不能声称跨仓真实资料 E2E 已通过。

StockQA 的 pytest 默认附带 coverage 输出；隔离命令应覆盖 `addopts`、禁用 cache、把 `--basetemp` 与 `TMP/TEMP` 指到新目录，并设 `PYTHONDONTWRITEBYTECODE=1`。不要在外仓真实目录重用 `.coverage`、`coverage.xml`、`htmlcov` 或已有 output 文件。记录开始/结束的外仓状态和临时目录清理结果；只写上述获授权文件，回执和审查报告留在本仓。

## 审查判定

Q06 的难点不是 SQLite 行能否保存，而是 **HTTP POST 前的耐久尝试意图与租约围栏贯通到每一个 provider/fallback 分支**。任何一条公共快扫路径若绕过该钩子，或把超时/崩溃当作确定未发送，就仍可能重复计费。C01 身份修订、G2 前置门槛、Q07 检查点、Q09 预算和 Q10/W05 outbox 导入都尚须各自验收；本报告只提供可执行边界和反例，不标记 Q06 完成。
