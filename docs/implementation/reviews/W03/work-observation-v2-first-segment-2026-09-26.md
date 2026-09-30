# W03 身份绑定 Work/Observation v2：本仓第一段交接

状态：**局部契约与离线参考验证已实现；W03 跨仓能力未完成。** 本段不修改 StockWiki、StockQA、company-wiki、中央计划或真实数据库，也不执行模型调用。

## 已固定的边界

- `WorkItem.schema_version=2.0.0` 必须显式带 `identity_revision`、`source_binding_version`、`identity_state`、排序去重的 `source_binding_refs`。新写入口 `validate_work_item_v2` 只接受来自 StockWiki 权威库的身份投影，按 Entity、Security 或 Segment 范围检查实际绑定和扫描资格。临时身份仅在 `eligible_provisional` 且单一来源证券时可派发；核实身份须 `eligible_verified`。缺失、撤销、冲突或旧修订均拒绝。旧 `validate_work_item` 与旧状态转移入口拒绝 v2。
- v2 逻辑工作键为旧五元组再加上述四项；因此身份修订或来源绑定集修订会改变工作键及派生的请求缓存键，即使模型、题目、刷新代次不变。StockWiki owner 应让 `identity_revision` 和 `source_binding_version` 单调递增；绑定变更还应给受影响字段提高 `generation`。这两个版本不能由模型、候选导入行或调用方自报。
- 新观察使用单独的 `urn:iqs:observation:2` 机器 schema。每条记录不可变地带工作 ID/代次、题义和路由指纹、作用范围、派发时身份状态/修订及来源绑定版本/集合。`validate_observation_identity_v2` 核对派发时身份投影和**已达到 `result_ready`/`delivered` 的 work**，并核对观察完整 payload hash、run/scan 归属、持久 attempt 的 ID/provider/model/request/prompt hash/时间及回答状态。`pending`、空 attempt 和虽答“已评分”却无 executed 搜索回执引用的记录不能通过。该入口证明的是身份与工作外壳的自洽，**不能单独证明来源、评分内容或当前可计分资格**；例如 `insufficient_evidence + score=8` 的 schema 合法旧外壳仍可留作历史，但不进入任何当前分。
- `observation_identity_is_current` 是故障关闭的**当前分资格门参考**：除外壳验证，还须从各权威库独立取得 delivered work/attempt、实际 executed 搜索回执、StockWiki accepted ACK、冻结题包与答案语义已验证的独立 content receipt，以及派发时和当前两份身份投影；任一缺失、ID/hash/版本不一致或非 `scored` 的 1–10 分均返回 false。不得从观察自身拼出这些“trusted”凭据。目前生产系统尚无 v2 content receipt/完整适配，因此此门默认不可放行；它不是已上线的白名单实现。旧身份晚到结果即使可接受为历史，也因当前 owner 版本不匹配而返回 false。
- 原 `urn:iqs:observation:1` schema 保持 1.0/1.1 历史格式，Exchange v1 仍只引用它。既有 S05 `standard_answers.validate_observation` 显式拒绝 2.0，既有 published-ingest 1.1 语义不变；不能因向旧 schema 扩充 enum 而误把 v2 当 v1 包。v2 身份验证只覆盖**身份外壳及 hash**，还不是完整的题目包、答案、来源、检查等级或 ACK 入库验证。

## 下一个实施者必须完成的依赖

1. **StockWiki W02 同库迁移与 owner 投影**：在唯一的 quick-scan SQLite 里持久化 provisional/verified、身份修订、来源绑定集版本、资格回执和双向归属；更新身份或绑定必须在一个事务中提高版本、记录事件、停派旧 work。跨 Entity 的来源键/证券唯一性、A/H/ADR 桥接的人工证据及旧成员 pin 沿革仍由 owner 事务保证。本仓纯验证器无法证明传入投影真来自库。
2. **StockQA Q06 派发/观察适配**：从 owner 取得带签名或持久回执的派发时身份快照并固定在 work 中；实际逻辑去重、缓存、租约、重试都用 v2 键。生成 v2 Observation 时使用该快照，不靠 LLM 改写身份字段；晚到回执可接收历史，但不能覆盖新的身份视图。新 v2 状态机入口应以相同可信上下文验证，不能复用旧 `transition_work_item`。
3. **StockWiki W05/S05 完整入库**：发布独立的 v2 模块包/答案语义与身份外壳联合验证，保持旧发布包及观察 ID 不变；在 SQLite 同事务校验派发时快照曾有效、观察 ID/hash、owner 版本及 ACK 重放，并由 StockWiki 持久签发可独立查询的 v2 内容/题包校验凭据。当前本仓 helper **不能**代替 S05 完整验证，也未证明某条临时身份具有全部提问所需属性。没有该 receipt 时当前分资格门保持 false。
4. **C06 Exchange/Query v2**：新增 v2 capability、交换包、查询/ScoreRef 版本。v1 交换包不得承载 v2 观察；v1 查询只能继续作为旧数据兼容视图。新查询须显式返回 `identity_state`、资格、身份修订、绑定版本及 `current_score_usable`，并按身份修订过滤排序与白名单。默认白名单仅取 verified；用户明确要求时才能纳入带标签的 provisional。若查询尚不能分辨修订，应停止提供“当前分”而不是继承旧分。
5. **一键启动门禁与真实副本验收**：首次批量扫描之前验证同库迁移、owner 资格和完整 v2 契约。否则只导入 `source_candidate`、返回待核数量，不静默声称 2,000 家可扫。真实 company-wiki 快照验收只读，SQLite/下载/观察输出仅在临时目录，结束清理并比对原路径 hash/mtime。

## 已跑的离线反例

`tests/test_identity_bound_work_observation.py` 覆盖旧入口拒绝 v2、缺必需身份字段、身份/绑定版本变化导致键与缓存分离、候选和不完整 owner 投影拒派、证券归属不符、多挂牌只取目标证券绑定、v1 Exchange 观察 schema 不收 v2、S05 不收 v2、待办未完成/attempt、run、scan、provider、model、prompt hash 不符、虽称已评分却未执行搜索、篡改后重算 hash 仍与派发 work 不符、无独立内容凭据或已损坏 observation ID/hash 不能作当前分、未知状态夹带 8 分仍只作历史、旧身份晚到观察仅可历史展示。旧 C04/S05/C06 定向测试仍需保持通过。所有样例公司、来源与模型均为离线虚构数据。
