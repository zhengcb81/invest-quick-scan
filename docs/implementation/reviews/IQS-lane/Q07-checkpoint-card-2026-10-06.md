# Q07 施工卡（写前报告 — owner 通授 2026-10-03 覆盖本批；纯离线无 live 成本）

日期：2026-10-06。任务卡 Q07「实现逐题检查点、部分回复与取消恢复」，deps 全满足（Q06✓ Q03✓）。
case：JOB-03 / JOB-04 / JOB-05 / LLM-07 / PAR-04 / PAR-09；不变量：I05 / I12 / I17。

## 只读勘察结论
- **store 侧 Q07 API 全部就位**（Q06 第一段已建）：`save_answer_checkpoint`（L2127，契约=归一化 answer{entity_id/question_id/status∈{scored,unknown,insufficient_evidence,not_applicable}/score(scored 必为 1-10 int=**I05**；非 scored 必须 null)/description≤5000} + 完整 execution_receipt{search_status=executed、provider∈{openai,minimax,mimo}、2xx、response_status=completed、completed_at、source_urls…}，同 attempt 同答案**幂等返回**=**I12**）、`get_answer_checkpoint`（L2327）、`note_late_receipt`（L1923，PAR-09 迟到回执）、`reconcile_budget_attempt`（L1327，PAR-09 预算不双结算）、`recover_expired`（Q06 已接）。
- **回执在运行时已存在**：`QAResult.metadata` 携带 execution 事实（`to_quick_scan_dict` L453-478 即从 `metadata`/`execution` 组装 per-question `execution_receipts`）——引擎缝隙**可以直接存检查点**，无需等输出期。
- **Q06 基座**：work-item 生命周期（claim/mark_send_intent/诚实 unknown 终态）、内容寻址逻辑键（PAR-04 新包不铸新题）、不确定不自动重派（JOB-04 发出后不明单列）。
- **W11 刚关**（`2ec3ff5`）：refresh 工件为 Q07 的"只补漏题"提供消费面。
- 现状：`save_answer_checkpoint`/`get_answer_checkpoint` **零调用**（grep 实证）——Q07 是把它们接进执行路径的批次。

## 设计（接线为主，store 尽量不改）
1. **逐题返回即持久化（step1 / JOB-03 / LLM-07）**：`qa_engine` 在 process_question 成功且结果具备可存回执（search_status=executed、2xx、completed）时调 `save_answer_checkpoint(work_item_id, attempt_id, answer, execution_receipt)`；回执从 `result.metadata` 按 `to_quick_scan_dict` 同源字段组装（单一事实源，不重复发明）。**不可存**（失败/无搜索/结构坏）→ 不存、题保持可补（LLM-07：修复预算内成功才存，无法修复单列；store 的 I05 契约天然拒绝猜分）。
2. **恢复即补水（step1 / JOB-03 / PAR-04）**：派发前先 `get_answer_checkpoint`——命中则**水合已存结果**（答案+回执直出，零新 attempt、零新 HTTP），仅未命中题走 Q06 claim 派发。歧义面：work_item 非 pending 时 Q06 现给 claim_refused error——本批改为**先查 checkpoint：有→水合（成功结果），无→保持 error 拒绝**。
3. **取消与停止（step2 / JOB-05）**：停止派发=不再新请求（现有循环天然），在途结果仍可存；"取消一个未运行对象"= **work_item → cancelled 状态变更**（store 状态机已有 cancelled 词；若缺 cancel 方法则补最小 API——事件照记、历史不删、可被 roster 重新纳入 pending 之外的显式流程）。cap 到达时保留待办（pending 保持）。
4. **崩溃恢复报告（step2 / JOB-04 / PAR-09）**：新增只读 `recovery_report(store)`（或 runner 内等价函数）：按状态分列——派发前(pending，无费用)、发出后不明(uncertain，单列等对账)、已存结果(checkpoint 存在→不再问)、未 ACK(仅重导入语义=Q10 域，标注)；迟到回执路径接 `note_late_receipt`（幂等只结算原 attempt）+ `reconcile_budget_attempt`（不双预留/结算）。无静默丢任务。
5. **默认逐题（step3）**：保持每请求一题现状（包内多题=质量对照后才启用的 B01 实验门，本批不启用、只在文档声明）；cap 只是上限不触发新行为。

## 本批执行的 case
- **JOB-03**（fault）：6 题 4 成 1 缺 1 坏 → 中断恢复：4 存、只补 2、pack 不整体丢弃也不假装全成。
- **JOB-04**（fault）：四点崩溃注入（派发前/发出后/持久化后/导入 ACK 前）→ 派发前无费用、发出后不明单列、已存不重问、未 ACK 只重导入、无静默丢任务。
- **JOB-05**（boundary）：cap 到达+在途请求+取消未运行对象 → 停新发、在途可存、待办保留、取消=状态变更不删历史。
- **LLM-07**（fault）：漏题/重复 ID/错公司/非法 JSON → 修复预算硬顶、成功存、无法修复单列、不猜分（I05）、不合成成功。
- **PAR-04**（fault）：pack 返回后崩溃+换模型续扫 → q1-q4 各唯一成功检查点含原执行时间/模型、只重组 q5/q6、原 4 题发送不增、新包 ID 不铸 6 个新逻辑题、attempt/pack/prompt hash 保留、混合模型逐字段来源。
- **PAR-09**（fault）：预算预留+结果不明+迟到回执 → 不并行/不盲目重复 POST、预算不双预留/结算、迟到回执幂等结算原 attempt。
- （I05 经 store 契约测试钉死；I17=预期不为迁就实现降级——审查核。）

## 允许改动（动工前按现状复核；I18 接入不重写）
1. `src/core/qa_engine.py` — 检查点存/水合钩子（Q06 钩子的自然延伸；零注入行为不变）
2. `src/runners/llm_runner.py` — 恢复路径（checkpoint 先查）、recovery 报告、取消接线
3. `src/utils/quick_scan_work_store.py` — **仅限**：cancel 方法与 recovery 辅助的最小缺口（先测后改；现有 save/get/late/reconcile 不动）
4. `tests/unit/test_q07_checkpoint.py`（新增）— TDD 主战场（含 JOB-04 故障注入、PAR-04/09 走真临时库）
5. 视需要 `src/core/models.py` — 仅限回执组装抽共享函数（单一事实源）；若能不改则不改
6. **禁改**：transport 协议、Q09 预算语义、Q06 已验证面（生命周期契约）、既有输出 schema

## 门与证据
- 定向 pytest（Q07 新测 + Q06 回归 15 + qa_engine/llm_runner/basic_runner/work_store）→ StockQA 全量（基线 881 口径，`-p no:base_url`）→ mypy/ruff/black(100)
- 独立审查两轮（needs_revision→fix→approved）→ StockQA 隔离提交 → PWF 记档
- **无 live 成本**（全离线：假传输/临时库/故障注入；不调用任何 LLM/网络）

## 风险与边界
- checkpoint 需完整回执——**只在回执可信时存**（search_status=executed + 2xx + completed），缺回执的"成功"不落检查点宁可重问（诚实优先）。
- 水合路径不得伪造 `answer.created_at`/执行时间——PAR-04 要求原执行时间，水合时保留 checkpoint 内时间戳并注明来源 provenance。
- Q10（outbox/ACK 导入）不在本批：JOB-04 的"未 ACK 只重导入"标注为 Q10 域承接。

## r1 findings 处置记录（2026-10-06 round-63，needs_revision→整改）
- **P1-1（record 成功→save 失败劈叉）**：新增 `_preflight_checkpoint`——**用 store 自己的校验器**（_safe/_safe_text/_sanitized_receipt/_timestamp/_canonical_source_urls/quick_scan_receipt_sha256/全套答案与回执面）在**任何状态记录之前**跑完 save 的确定性校验；预检拒绝→零状态降级诚实 unknown（探针三类：6001 字描述/`` 控制字符/空 source_urls 全部落 uncertain+checkpoint=0+claim 拒，**且真 save 对同样输入也拒**=漂移探测对）。record 后不可预检的异常按 `recorded` 标志诚实分流（已收执→交恢复流程，不再双记录）。
- **P1-2（水合伪造 created_at + 信封丢回执）**：水合 Answer 现从 provenance `response_completed_at` 解析**原始执行时间**（解析失败保留默认并注释）；新增 `_provenance_metadata`——把 provenance 重建为信封期望的 answer.metadata（execution/provider/attempts/search_status/source_urls）→ `to_quick_scan_dict` 对水合题输出原回执（provider=mimo、search_status=executed、answered_at=原时间、http 200）。回归测试断言 created_at==原时且 provider 调用 0。
- **P2-1**：JOB-04 测试强化——C 精确 ∈persisted、D 实例化（result_ready 无 checkpoint → import_ack_pending）、E 实例化（cancel_pending_work → cancelled 桶）、预算行=0（派发前无费用）、分区断言现跨 5 项。
- **P2-2**：`to_quick_scan_dict` 内联 provider 选择已**接线**到共享 `final_transport_provider`（行为等价、48 CLI 集成测试与全量 887+2 佐证），docstring 过度声称消除。
- **LOW**：JOB-05 走公共 `cancel_pending_work` 包装（零调用变有测试）、JOB-03 增 fresh 2 题非水合断言、PAR-09 settle `>=1`→`==1`、hydrate docstring「read-only」改「幂等 attach+只读查询」。INFO：Q09 接线时注意与 transport `begin_quick_scan_reserve` 的双预留路径（随 Q09 批处理）。
- **门（整改后）**：Q07 定向 **8 passed**（+P1-1/P1-2 回归）、回归电池 **125 passed**、mypy Success、black/ruff 0；全量后台复验。
