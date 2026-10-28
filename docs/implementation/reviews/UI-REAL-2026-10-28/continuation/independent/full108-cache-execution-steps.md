# Full108：原任务冷恢复与交付历史的精确验收步骤

2026-10-28。独立只读研究；本报告未执行真实 CLI、UI 控制、模型调用、数据库写入或服务重启。结论来自当前已知源文件及先前明确授权的元数据只读快照。本文不是 full108 已完成的证明。

## 结论

**ACK 前可用原 UI 的个体任务“暂停→核原状态→恢复”启动同一 run 的新进程，验证原完整检查点恢复；无需另造 CLI 或准备新代际。** 该流程有严格前提：本任务所有原注册工作都已有合法 CP，任务的原 bundle、登记与有效权限不变，UI 实际提供相应 allowed_actions。完成批次的“恢复批量”是 no-op，不能代替此验收。

ACK 后最小验收是原结果、封存包和 exact ACK 的历史持续可读，以及同一交付入口的幂等 attached。**不能承诺过期旧 scope 在 ACK 后仍全量 SDK hydrate，也不能把历史结果称为当前 fresh 缓存。** 普通新准备按实际 TTL 判 stale/missing_date 是正确行为。

## 1. 先冻结验收对象与前置条件

1. 等三个原 prepare 全部真正 registered，保存其原 execution bundle 清单。当前候选为 Microsoft `prepare_47976fb90e724fcbb757e885fa21e1b0`、Tencent `prepare_9d8f69c9fb844f55aa7d2f9cf85e964a`、CATL `prepare_bc31143f27cf4ed1a3c1298240da687a`。后两者本次研究开始时仍在准备，不能提前当作已登记。
2. 按原 registered C06/manifest/confirmation 确认实际 scope、题目、work ID 向量。预期三公司、六 scope、108 个字段，但必须由原清单验证；不得按 entity/question 的 latest generation 拼凑。M/T 原模式 full、C 原模式 quick，三者当前均36题；保留原模式和 `2026-10-25` 截止日。
3. 持续完成这些原任务，直至选择范围全部 `result_ready`、每题 CP/standard/context 完整且封存可读、原进程全部退出、0 在途、无 unknown/uncertain/未处理 lease。任何 failed、缺 CP、superseded 或 deferred 都不能冒称完整冷恢复。
4. **先不要 ACK 这六个范围。** 已经 delivered 的历史范围另列，不能退回 ready 或篡改状态。若选择清单混有原生 observation reference，而非已登记 work/CP，明确分开；不能为凑108制造工作。
5. 本轮固定配置、原 bundle、ledger/workspace、权限和准入；不切 cutoff、不延长 TTL、不修改 observed_at、不主动续旧 lease。检查原 grant 有效期；过期时按原能力处理，不绕过原权限。其他公司若仍运行，暂缓全局零增量比较。

## 2. ACK 前：用原 UI 个体任务进行真正冷恢复

对三家公司分别执行一次，逐项记录同一 run_id 与对应 frozen bundle_id。

1. 在任务列表定位**该原 run 行**，等其进程确实退出。初次记录 launch_attempt、输出引用、全部工作/CP/包/物理请求与费用元数据。
2. 只有行的 `allowed_actions` 含 `pause` 才点击“暂停（当前公司完成后）”。已退出任务会变成本地 `paused`；这不撤销工作，也不会中断原 HTTP。
3. 点击该行“核原状态”，等待原 native preview 完成，再刷新任务列表。普通 GET tasks 用缓存检查结果，不会自动执行每公司的完整原生核查，所以不要省略这一步。
4. 确认本次原 preview 的 `can_start=true`、原权限 passed、bundle fingerprint 不变、无活跃原进程/unknown，且该行实际 `allowed_actions` 出现 `resume`，才点“恢复”。如任一条件不满足，停止此项，保留原拒绝原因；不能换另一任务、改状态或直接调用低层 SDK 来绕开 UI。
5. 原控制会保留 **run_id**，增加本地 **launch_attempt**，产生新的 `result-N.json` 和 `process-N.log`，通过完整原 `_command` 启动新子进程。新 PID 无先前进程内存，已足够证明冷进程边界，无需在其他任务活跃时重启整套服务。
6. 等该新子进程退出。核完整题目覆盖、原分数/状态/理由仍来自同一 CP（这里只比较哈希与元数据，不复制真实答案），所有原工作仍 ready，且以下全部不新增：native work ID/generation、attempt、question pack、physical request/response、budget attempt/terminal、累计费用。原 CP ID、payload SHA、standard SHA、context SHA、answered/checkpointed 时间、封存包与 observation ID 均保留。
7. 三个原任务均完成后汇总六 scope/108字段；不是三个任意历史 run 各自成功即可。

**成功允许的变化：** 本地 launcher 的 launch_attempt、PID、执行日志/输出文件及外围生成时间。原公开结果中重现原 HTTP200/request_id 是原 provenance，不能再次当作真实新请求计费。公开结果不导出内存 `QAResult.metadata.answer_checkpoint.hydrated`，缺该 flag 不能判失败，也不能凭 HTTP200 flag 判重发。

**不能用批次完成状态替代：** `dashboard_batches.py` 对 `owner_ready` 批次不给 pause/resume，resume 返回未启动；必须使用个体任务原控制入口。若原行无法经 UI 分页找到或动作不出现，如实记录 UI 可达性/权限限制，不伪称验收通过。

**超时处理：** UI 某些控制请求30秒、个体 inspect150秒，原权限子进程可能约130秒。浏览器 timeout 不证明控制未执行。不要重复 POST、另起 CLI、kill worker；先等待原锁/控制完成，读原 run 的 launch_attempt、PID 与输出引用，确认原状态后再行动。

## 3. 然后正常交付：完整导入与 exact ACK

1. 使用原 UI “将已ready范围入库并对账”，保存**实际入口及精确 payload**（batch_id 或 bundle_id）、原有序 bundle/fingerprint 集合和返回 job_id。
2. 按原交付流程完成六 scope 的封存、StockWiki import 和 exact ACK。每个原 delivery 必须 delivered，ACK 与原 package/item/observation/consumer 绑定完整；不只看 UI 绿色汇总。
3. 元数据核准108字段原成功结果、原封存包、精确 ACK 与该次选择清单一一对应。各类 SHA 各司其职，CP payload SHA 不应被错误要求等于 observation payload SHA。
4. 如有 partial/needs_original_inspection，只使用原 allowed_actions 和原恢复流程；completed job 没有恢复动作，不绕过 UI 调隐藏 control。

## 4. ACK 后：历史持久性与幂等的最小验收

1. 刷新浏览器，重新进入原任务结果/交付历史，再读一次；原答案与时间轴可读，原包/ACK ID、SHA、consumer 与 delivered 数量保留，0新物理请求/费用。待所有原进程静止后，主线可另安排受控服务重启再读，不能在活跃 writer 期间为本报告强行重启。
2. 若原 UI 仍提供原交付提交入口，可用**完全相同入口/payload、有序 bundle 集合与配置**再提交一次。原 `submit` 在确定性 key 已存在时直接返回 `attached:true`、同 job_id、API_requests0，不启动新的交付 worker。这证明 coordinator 幂等附着；不宣称已重跑一次真实 importer。
3. batch 与 bundle 两种入口不是同一 key；partial 到 full 的 entry 集合变化也会产生合法新 job。不得换入口后期待 attached，也不得为了幂等篡改旧记录。
4. completed/history 的 allowed_actions=[]，只读历史不能借此获取新写权限。若配置/注册指纹已变，明确显示 historical_read_only/current_target_verified=false；历史 ACK 存在不等于当前 owner 又验证通过。

## 5. 与普通新扫描 freshness 的明确界线

原 registered `result_ready` 恢复可按同工作 CP 路径恢复；`prepare_execution._refresh_states` 对已 delivered 工作则仍看原 native decision，非 reuse 时会 deferred `original_delivery_historical_or_refresh_required`，此后 `restore_registered_checkpoint` 不保证返回答案。不能承诺 ACK 后同旧范围全量 hydrate。

StockWiki 当前 TTL 截止为 `min(observed_at+TTL, information_as_of+TTL)`；缺 information_as_of 为 missing_date，`now == valid_until` 已 stale。不能拿 checkpointed_at 或之后的 seal 时间刷新它。此前只读快照57封存包中57个 observed_at 都等于原回答/receipt.completed_at，并非 seal 操作时刻；截止日均25日。按真实24h规则，57中41 stale、16 missing_date、0 fresh。该历史快照不代表现在全108状态。

因此主线最后可以做**一次有限的原普通新 prepare/preview**，确认旧25截止的 expired/missingdate 得到正确原生计划；不执行无限旧日重问。隔离动态 UTC、私有TTL72→24的原生验收已覆盖 fresh复用/过期刷新，不能用更改真实日期/TTL把本轮历史洗成 fresh。

## 6. 只读元数据 auditor：如何锁到原六 scope，而非 entity 最新行

此部分仅给定位设计，未执行。审计器应使用 SQLite URI `mode=ro`、`PRAGMA query_only=ON`，短一致快照 `BEGIN` 后立即取必要元数据、rollback/close，再在内存比较；不得构造会迁移/恢复过期工作的 Store。不得读取回答全文、lease_token 或完整授权体。真实 schema 如变动，应先 `PRAGMA table_info` 核列名，停止而非猜测。

1. 从三个**真正 registered** prepare 的 result 中取原 execution_bundles 与每 scope 原 confirmation_id，并锁 questions/manifest/identity/C06/owner/admission 配置的哈希与原 bundle fingerprint。保留 C06 的 subject_key/perimeter/anchor/decision、identity/scope 元数据，敏感授权只留不可逆哈希与公开标识。
2. 用这六个 confirmation_id 读 `quick_scan_refresh_admission` 的 `input_sha256/receipt_sha256`，以 `json_each(receipt_json,'$.items')` 提取 work_item_id/entity_id/question_id/generation/scope/scope_id。原 `input_json.specifications` 与 receipt 项按完整身份配对，不能按数组位置或 entity/qid latest 猜。references 单列，重复/缺失/额外 work 必须报告。
3. **只 JOIN 这些精确 work ID**：`work_item`、`answer_checkpoint`、`quick_scan_standard_answer`、`quick_scan_work_context`、`quick_scan_owner_refresh_binding`、`quick_scan_result_delivery`。核 receipt 的完整 tuple 与 work 行一致。记录 checkpoint_id/attempt_id/payload_sha256/checkpointed_at、answer_sha256、context_sha256、binding_sha256、package ID/SHA/bytesSHA、observation ID/payloadSHA、delivery state、ack_sha256/consumer_store_id。
4. 用 `json_extract` 只提取 CP `$.provenance.response_completed_at`、standard `$.information_as_of`、package `$.items[0].observation.observed_at`、`...execution.answered_at`、`...answer.information_as_of`、`...information_cutoff`；不 SELECT 全 payload_json/answer_json/package_json 回 Python。context 与原 C06 的 approved anchor 兼容要走原只读 guard，不能盲要求可合法复用的旧 CP context raw hash 等于新 C06 raw hash。
5. 精确 work→`attempt`→`quick_scan_question_pack_member.attempt_id`→`quick_scan_question_pack_send.pack_id`→`budget_attempt_id`，再 JOIN physical budget/terminal/outcome/response 元数据。先按 budget_attempt_id 去重；两个逻辑成员共用一个 physical 请求，不能重复计费。单题原 budget.work_attempt_id 另映射。不要输出 attempt.lease_token；可留 epoch、phase、ordinal、receipt/response SHA、request_id、HTTP 状态与原时间。
6. before/after 比较上述**同一选择锁**，要求完整题目/CP/封存覆盖且原 native attempt/物理 pack/budget/费用零新增。新本地 launch_attempt 不等于新的 native attempt。若其他范围仍 active，只能用所选 work→physical 集合做局部对比，不能声称全账本零增量；最稳是等全部本轮 worker静止后采 before/after。

以下为基于已核 schema 的**元数据定位 SQL 示例**，不是权限/数据完整性验证器；参数来自原已核六 confirmation，不允许临时任意挑 ID。完整性仍由原 native read guards 验证：

```sql
WITH selected AS (
  SELECT a.confirmation_id, a.input_sha256, a.receipt_sha256,
         json_extract(j.value,'$.work_item_id') AS work_item_id,
         json_extract(j.value,'$.entity_id') AS entity_id,
         json_extract(j.value,'$.question_id') AS question_id,
         json_extract(j.value,'$.generation') AS generation,
         json_extract(j.value,'$.scope') AS scope,
         json_extract(j.value,'$.scope_id') AS scope_id
  FROM quick_scan_refresh_admission AS a
  JOIN json_each(:confirmation_ids_json) AS chosen
    ON chosen.value = a.confirmation_id
  JOIN json_each(a.receipt_json,'$.items') AS j
)
SELECT s.*, w.status, w.identity_snapshot_sha256, w.question_fingerprint,
       c.checkpoint_id, c.attempt_id, c.payload_sha256, c.checkpointed_at,
       sa.answer_sha256, wc.context_sha256, ob.binding_sha256,
       d.delivery_id, d.package_id, d.package_sha256, d.package_bytes_sha256,
       d.observation_id, d.payload_sha256 AS observation_payload_sha256,
       d.state AS delivery_state, d.ack_sha256, d.consumer_store_id,
       json_extract(c.payload_json,'$.provenance.response_completed_at') AS original_answered_at,
       json_extract(sa.answer_json,'$.information_as_of') AS standard_information_as_of,
       json_extract(d.package_json,'$.items[0].observation.observed_at') AS observed_at
FROM selected AS s
JOIN work_item AS w ON w.work_item_id=s.work_item_id
LEFT JOIN answer_checkpoint AS c ON c.work_item_id=s.work_item_id
LEFT JOIN quick_scan_standard_answer AS sa ON sa.work_item_id=s.work_item_id
LEFT JOIN quick_scan_work_context AS wc ON wc.work_item_id=s.work_item_id
LEFT JOIN quick_scan_owner_refresh_binding AS ob ON ob.work_item_id=s.work_item_id
LEFT JOIN quick_scan_result_delivery AS d ON d.work_item_id=s.work_item_id
ORDER BY s.confirmation_id, s.scope, s.scope_id, s.question_id;
```

SQL 返回行需再次核 `w` 的实体/题目/代际/scope tuple 与 `s` 全等；示例只为薄元数据输出未重复 SELECT 那些 work 字段。不得把此 query 的存在等同真正执行了原只读授权/封存校验。

## 源码依据与证据边界

- IQS `scripts/dashboard_execution.py`：tasks约574–644、preview507–542、control812–899、_command647–668；`dashboard_service.py` GET tasks449–453、task control563–568。
- IQS `scripts/dashboard_batches.py`：owner_ready batch无恢复动作；`dashboard_delivery_jobs.py` submit139–173、get213–222、control256起。UI `src/app/ui/product.js/product_core.js` 依据当前 allowed_actions 与 fresh snapshot。
- StockQA `src/utils/quick_scan_refresh_execution.py` _refresh_states237–267、restore_registered_checkpoint396–454；`src/core/qa_engine.py` _hydrate_pack_checkpoint417–447；public输出由 quick_scan_owner_refresh/build_refresh_result 与 core/models 紧凑序列化。
- schema依据原 `quick_scan_refresh_admission_journal.py`、`quick_scan_owner_refresh_journal.py`、`quick_scan_question_pack_journal.py` DDL及前次只读 PRAGMA，未执行新真实 DB 查询。
- 先前时间元数据见同目录 `full-cache-freshness-preparation.md`、`full-cache-time-metadata.json` 与 `full-cache-freshness-pure-rule-check.json`。

本文不签收 full108、金融准确性、实际0HTTP冷恢复、实际全量ACK或生产重启；这些须由主线按上述原能力实测并记录。
