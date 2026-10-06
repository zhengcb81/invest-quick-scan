# Q09 独立审查报告 — 并发派发上限/费用预留/预算停止（含 ADV-1）

日期：2026-10-06。审查者：独立审查（与实现者无关）。两仓只读（本报告为唯一写入文件）；全程离线、无 LLM 调用、无网络、未读真实配置。
被审基线：StockQA 工作区 3 修改 + 1 新增测试；StockWiki 工作区 2 修改。审查方式 = 门独立复跑 + diff 审读 + 六 case 语义核证 + 独立探针复算（探针置于 `%TEMP%\q09_review`，不落被审仓）。

## 1. 范围

**StockQA（`C:\Users\郑曾波\Projects\StockQAbyLLM`，恰 4 变更面）**
1. `src/runners/llm_runner.py`（+56/-3）：policy 对接线（L1050-1079）、deadline 门（L177-183）、reason 带准入码（L212-215、L277-281）、own-reservation 旗置位/清位（L269-274、L327-333、L437-443）
2. `src/utils/quick_scan_work_transport.py`（+20）：`_OWN_RESERVATION` ContextVar + `own_reservation_held()`（L294-304）、`begin_quick_scan_send` 置位早退（L406-412）
3. `src/utils/llm_integration.py`（+10/-2）：`_preferred_route_busy` 同旗跳过（L1015-1019）
4. `tests/unit/test_q09_budget_concurrency.py`（新增 644 行，8 测试）

未动（符合卡"允许改动/预期 0 改动"）：`src/core/qa_engine.py` 0 改动 ✓、`src/utils/quick_scan_work_store.py` 0 改动 ✓（卡设计3 的"收编只读方法"未启用）、Q06/Q07 已验证面无语义变更（ctor 均为可选参数默认值，133 电池 + 897 全量绿）。untracked 杂物（`.codegraph/`、`.workbuddy-ai/`、`nul`、`pilot_runs/*`、`progress_update.txt`）不在 diff 范围。

**StockWiki（`C:\Users\郑曾波\Projects\StockWiki`，恰 2 文件）**：`stockwiki/quick_scan_refresh.py`（+8/-1，ADV-1）、`tests/test_quick_scan_refresh.py`（+2，company 断言）。无其他改动、无 untracked。

## 2. 门复跑（命令 + 实测数字）

StockQA（workdir=仓根）：

| # | 命令 | 结果 |
|---|---|---|
| G1 | `python -X utf8 -m pytest tests/unit/test_q09_budget_concurrency.py -q -p no:cacheprovider -o addopts=` | **8 passed** in 3.66s（含跨进程 PAR-01） |
| G2 | `python -X utf8 -m pytest tests/unit/test_q09_budget_concurrency.py tests/unit/test_q06_work_binding.py tests/unit/test_q07_checkpoint.py tests/unit/test_qa_engine.py tests/unit/test_llm_runner.py tests/unit/test_basic_runner.py tests/unit/test_quick_scan_work_store.py -q -p no:cacheprovider -o addopts=` | **133 passed** in 13.26s |
| G3 | `python -X utf8 -m pytest tests/integration/test_quick_scan_cli.py -q -p no:cacheprovider -p no:base_url -o addopts=` | **48 passed** in 4.21s |
| G4 | `python -X utf8 -m pytest tests/ -q -p no:cacheprovider -p no:base_url -o addopts=` | **897 passed, 4 skipped** in 72.88s，**0 errors**（889 基线 + 8 自洽 ✓） |
| G5 | `mypy src/runners/llm_runner.py src/utils/quick_scan_work_transport.py src/utils/llm_integration.py src/core/qa_engine.py main_with_llm.py` | **Success: no issues found in 5 source files** |
| G6 | `black --check -l100`（上述 src 4 文件 + 新测试文件） | **5 files would be left unchanged** |
| G7 | `ruff check`（同 5 文件） | **All checks passed!** |
| G8 | `git diff --check` | 干净（无输出）；`git status` 审后复核=审前（本审零写入被审仓） |

StockWiki（workdir=仓根）：

| # | 命令 | 结果 |
|---|---|---|
| W1 | `python -X utf8 -m pytest tests/test_quick_scan_refresh.py -q -p no:cacheprovider -o addopts=` | **4 passed** in 3.89s |
| W2 | `bash scripts/check_all.sh` | ruff PASS；**929 passed, 15 skipped**；coverage TOTAL ≥73% PASS、ui.py 75% PASS；validate-framework **0 errors**（12 warnings，均为既有 OKF/模块大小告警）；**`=== ALL CHECKS PASSED ===`** |

独立探针（`python -X utf8 %TEMP%\q09_review\q09_probe.py`，临时库、双线程/单进程、零网络）关键输出：
```
p1_unconfigured_reason = attempt_intent_failed:BudgetAdmissionError:budget_policy_not_configured
p2_refusal_reason      = attempt_intent_failed:BudgetAdmissionError:budget_cost_limit
p2_refused_item_status_immediate = leased（未发送；totals reserved=6e6, in_flight=1）
p3_other_route_reason  = attempt_intent_failed:BudgetAdmissionError:budget_reconciliation_required（异路由同拒=policy 级全局门）
p3_after_reconcile_claimed = true（spent=2e6, reserved=6e6, unreconciled=0）
p4_busy_route_a_without_flag = true   → 无旗=30s 忙等自锁链（PREFERRED_CAPACITY_WAIT_SECONDS=30.0）
p4_busy_route_a_with_flag    = false  → 旗开=立即放行
p5_rows_after_mark=1 → 旗关 begin: QuickScanSendAttempt, rows=2（双预留复现）→ 旗开 begin: None, rows 不变（恰 1 reserve）
p6_begin_no_bindings = None（既有契约；llm_client L1024/L1137 None=照常 POST）
p7: reason=time_cap_reached；无 work 行；0 budget 行
p8_second_reason = attempt_intent_failed:BudgetAdmissionError:budget_request_limit
```

## 3. 双准入接缝审读（Q07 INFO-3 遗留闭环）

- **旗生命周期**：`before_question` 在 `mark_send_intent` 成功后、且仅当 `budget_policy is not None` 时置位（llm_runner L262-274）；`after_question`（L327-333）与 `after_question_failed`（L437-443）**顶部**清位且 try/except 包裹不抛。QAEngine 契约（qa_engine L247-297）：claimed 才派发 → 成功必走 `after_question`、(ValidationError|ProcessingError) 必走 `after_question_failed`、其余异常中止整批（同上下文不再派发新题）。进程崩溃 → ContextVar 随进程消亡。**泄漏窗口实际为零**；即便假想泄漏，被派发题必经 `before_question→mark`（pair 非空必预留），begin 跳过的只是同一发送的二准入、忙等跳过的只是自家槽的等待——**mark 准入仍是权威门，文档安全声称成立**（P4/P5 佐证）。
- **begin 置位返回 None=既有契约**：P6 探针（work/budget 双 None → None）+ `llm_client` L1024-1056/L1136-1169 仅在 `work_attempt is not None` 时 consume/record，None 照常 POST ✓。
- **双预留 = 本批核心闭环**：无旗时（同 store、预算有余量）mark 1 行 + begin 再插 DISPATCH 行 = **同一发送双计**（Q07 INFO-3 接缝，P5 实测 rows 1→2）；旗开 → begin None、**rows 恒 1**。生产侧：CLI quick-scan 走 cascade→search 适配器（begin 唯一两调用点 llm_client L1023/L1136），lifecycle policy 对与 `bind_quick_scan_budget`（llm_runner L1086）同上下文共存——旗正是消除该重叠的开关。
- **胶水 e2e 恰 1 条 reserve**：`test_runner_glue_reserves_before_dispatch` 断 `session.post.call_count==1` 且 `quick_scan_budget_attempt` **rows==1**、`requests>=1` ✓。该断言同时钉住忙等旗：无旗时自家路由（`_ordered_policy` 各 route `max_in_flight:1`）在 `_wait_for_preferred_capacity` 处 30s 忙等 → `budget_deferred` 零 POST → 测试必败（与卡记录"30s 自锁 32.9s→2.78s"机制一致；精确毫秒未复测——需还原旗，机制已由 P4 实证）。
- **对既有路径零破坏**：置位条件只由 lifecycle（policy 对非空）触发，唯一生产构造点 llm_runner L1070；无 identity 快照 → lifecycle=None、policy 未配置 → pair=None → 旗恒 False → begin/忙等行为与 Q06/Q07 逐字相同。CLI **48 passed** 覆盖非激活路径 ✓；diff 中 transport/llm_integration 均为纯增量早退，旗 False 时零语义变化 ✓。

## 4. 逐 case 语义证据

- **BUD-01**（`test_bud_01_concurrent_reserves_admit_exactly_one` L139-191）：Barrier(2) 双线程同时 `before_question`（budget=10、per-attempt=6）→ **恰一 claimed、一拒**（reason 含 BudgetAdmission）；`spent+reserved<=10e6`；被拒项无发送。探针 P2 补证：真拒因 `budget_cost_limit`——**成本门（store L1098-1102）先于路由容量门（L1123-1129）触发**，断言不是被路由槽"顺带"满足；totals reserved=6e6/in_flight=1。跨连接原子性另有既有测试 `test_quick_scan_budget::test_two_connections_atomically_admit_only_one_over_budget_reservation` 同批绿。
- **BUD-02**（`test_bud_02_backup_route_cannot_break_the_total_cap` L194-226）：settle 8e6 后 route 0/1 **两条路由均拒**（换模型不破总额=同 policy 账本）；spent 守恒 8e6、reserved 0。失败/搜索/备用共用单表：既有 `test_quick_scan_budget::test_over_budget_exact_settlement_blocks_fallback_under_same_policy`（confirmed_failure 对账 8 → 备用 route-a2 拒 `budget_cost_limit`，覆盖 case given 的 `previous_failures_billable:true`）、`test_async_search_settles_the_same_durable_budget_ledger`（搜索同账本）——均在 897 全量内绿；账本仅 `quick_scan_budget_attempt` 一表（三层门/结算唯一入口 `_reserve_budget_attempt_tx`）。
- **BUD-03**（`test_bud_03_uncertain_keeps_reservation_until_reconciled` L229-284）：outcome=unknown → 行 `in_flight=1`、status=outcome_uncertain（store L1229-1231 保留预留）→ 新 attempt 拒 → `reconcile(resolved_outcome=completed, actual_cost=2.0)` → `unreconciled_attempts=0`、spent 2e6、reserved 0 → **新 attempt 放行**——先对账后重试序 ✓。探针 P3 补证：真拒因 `budget_reconciliation_required` 且为 **policy 级全局门**（store L1084-1090，先于成本/容量，异路由同拒；I50）。措辞：测试 docstring "no zero-duplicate-cost promise is made"、卡 "无证据不承诺零重复费用"——**无过度声称** ✓。
- **BUD-04**（owner=L01，`test_bud_04_unknown_price_never_runs_unlimited` L287-312）：未配置 store → 拒（BudgetAdmission）；`max_requests=1` 首次 claimed、第二次拒且 reason 含 "request"（探针 P8 真因 `budget_request_limit`；探针 P1 真因 `budget_policy_not_configured`）。"价格未知不无限跑" ✓。**live 前置只登记不越权**：卡设计4+风险3（"不宣称 L01 本体"）+ 测试 docstring（"recorded on the Q09 card as L01's acceptance, not claimed here"）；全 diff **无任何具体 live 费用数字/准确费用声称** ✓。登记载体目前仅施工卡（B01/L03 模板尚不存在）——不越权，见 LOW-6 附注。
- **PAR-01**（`test_par_01_cross_process_three_layer_caps_and_crash_safety` L414-559，含于 G1 的 3.66s）：双**子进程**（`sys.executable` 脚本，X=route_a/g1、Y=route_b/g2）+ 阻塞 stub（sleep 0.4 + 事件 jsonl）；父进程 20ms 轮询 DB 派生 `in_flight`：**violations 空（任意时点 ≤4）**、**max_seen≥2=跨进程真重叠**（≥2 独立题 send_start）；X `os._exit(7)` 崩溃后 **attempt phase='send_intent' ≥1 且 budget 行 in_flight=1 ≥1**（DB 计数不随进程丢失）；未领/预算失败题结构上不写 send_start（`sent_with_budget >= len(starts)-1`）。returncode∈{0,7}。偏差与松处见 LOW-4；组/路由瞬时上限由既有 `test_group_and_route_concurrency_limits_are_enforced_independently` 独立钉住。
- **JOB-09**（`test_job_09_admission_entry_refuses_while_ledger_conserved` L315-376）：in-flight #1（reserved 3）+ prior settle 8 → 新 reserve 3 **原子拒**（8+3+3>10，cost 门）→ **在途仍结算**（spent 9e6、reserved 0）→ 拒绝题 `phase NOT IN (prepared, abandoned_unsent)` 的 attempt=0（**后续已发送为 0**）→ 账本守恒 ✓。
- **deadline 额外测试**（L379-411）+ 探针 P7：过点 → `reason=="time_cap_reached"`、不 claim（无 work 行，`create_or_attach` 回读 pending 证明未派发）、0 budget 行、**在途题照常结算**（L401-411）——三语义全中。生产接线现状见 LOW-6。

## 5. runner 胶水与 ADV-1

**runner 胶水**：
- 首选 eligible 路由=意图路由归因：接线注释（llm_runner L1050-1054 "route attribution is the intended route — disclosed on the Q09 card"）+ 卡风险节（"route 槽计数=意图路由…总量账本不受影响"）**披露一致** ✓；四键（route_id/provider/model_requested/quota_group）与 mark 校验（store L1693-1703）对齐、ctor both-or-neither 守卫（L157-159）✓。
- deadline 门：见 §4，语义正确。
- reason 带准入码：`store_error:{type}:{exc}` / `attempt_intent_failed:{type}:{exc}`——探针实测四类码（not_configured / cost_limit / reconciliation_required / request_limit）全部可见 ✓。
- 忙等同旗跳过：`_preferred_route_busy` L1015-1019 在预算绑定读取**之前**判旗（P4 实测：预算绑定 + 旗关=True、旗开=False）✓。

**ADV-1（StockWiki）**：
- 取数：`request_refresh` 的 `profile = by_id[entity_id]`，源自 `profiles_from_store`（quick_scan_query L86 `SELECT entity_id, canonical_name, …`，W09 投影确带该字段）→ `entry["company"] = profile.get("canonical_name") or entity_id`（quick_scan_refresh L196）✓。
- render 透传：`company_by_entity.setdefault(…, item.get("company") or item["entity_id"])` → `"company": company_by_entity.get(entity_id) or entity_id`（缺省回落 entity_id）✓。
- e2e 断言逐字（W11 r3 L359 建议）：`assert invocation["company"] == f"公司{invocation['entity_id'][-1]}"`——fixture canonical_name=`公司{末位}`（如 ENT_A→公司A），与 entity_id（ENT_A）**必不相等**，断言有效非恒真 ✓。
- W11 既有 4 测试：`test_quick_scan_refresh.py` 恰 4 个测试，W1 4 passed + check_all 929 passed **零回归** ✓。

## 6. 范围/诚实性扫描

- 范围：StockQA 恰 4 面、StockWiki 恰 2 面 ✓；`qa_engine`/`store` 零改动符合卡预期 ✓；无网络/LLM/密钥（mock session、`offline-fixture-key`、`-p no:base_url`、探针全临时库）✓。
- 过度声称扫描（diff+卡+测试 docstring，检索"零重复/绝不/never duplicate/保证"等）：**未发现"零重复费用"类绝对句**；BUD-03 两侧均以"不承诺"措辞 ✓；接缝注释均为条件式（"would double-count…"、"remains the authoritative capacity gate"）✓。唯"must never…"措辞与自身回落冲突 → LOW-5。
- 卡实施记录相符性：施工卡本体仅写前报告（43 行，无独立"实施记录"节），实施记录在 task_plan Phase 81（L1198-1205）——**数字全部复现相符**（897/4sk、133、48、mypy 5、black 0、ruff 0、StockWiki ALL CHECKS PASSED/929、8 tests）；两处不符/缺记 → INFO-2、LOW-3、INFO-4。

## 7. Findings

**P0 / P1 / P2（阻断）：无。**

**LOW（非阻断，建议随提交或下批处置）**
- **LOW-1** `test_q09…::test_bud_04` L298 `assert "not_configured" in … or True  # reason carries the code`——**断言空转（永真）**。语义本身成立（探针 P1：reason=`…:budget_policy_not_configured`），但该行不设防；应删去 `or True` 直接断言码。
- **LOW-2** `test_bud_03` L258-260 拒因断言回退过宽（`or "BudgetAdmission"`，路由容量拒亦可通过）。真因已由探针 P3 实证为 `budget_reconciliation_required`（全局门，异路由同拒）——语义成立，判别力建议收紧为精确码断言。
- **LOW-3** 卡设计3 的二选一（`_preferred_route_busy` 收编 store 公共只读方法 **或** 如实留档保持直读）**两者均未见执行**：diff 保留直连 sqlite3（llm_integration L1038-1049），卡与 Phase 81 均无"保持现状"的决定记录。行为等价无碍，补一行留档即可。
- **LOW-4** PAR-01 与 case given 的偏差与松断言：given `pending_distinct_questions:20` 实为 6×2=12（且 Y 首题记 unknown 后受对账门 5 拒）；**组≤2/路由≤1 的瞬时值未轮询**（仅轮询 global≤4；组/路由由既有 store 测试独立钉住）；"未领/预算失败零发送"仅 `sent_with_budget >= len(starts)-1` 弱配对（结构上 refused 不写 send_start，方向正确）。跨进程重叠、崩溃安全、DB 计数三项实证充分。
- **LOW-5** ADV-1 请求侧注释 "a stable id must never enter the retrieval prompts as a company label" 与同一行 `… or entity_id` 回落**自相矛盾**（canonical_name 缺失时 id 仍作 company 标签进入 artifact）；render 侧两处回落无注释（卡称"缺省回落 entity_id 并注释"只在请求侧兑现）。建议注释改为"优先 canonical_name，缺省回落 entity_id"（render 侧补注）。
- **LOW-6** deadline 门**生产无注入点**：全 src 无 `deadline=` 调用（唯一生产构造点 llm_runner L1070 不传该参），时间上限目前为参数级交付、测试级验证。无 case 要求接线、卡明示"可选"、记录未过称，故**不阻断**；但 tasks.json Q09 step3 字面含"时间上限"——建议 Phase 81 补一行"时间上限来源随 L01/live 批次接线（本批交付参数级门）"或补最小 CLI 接线，避免 step3 半维度悬空。BUD-04 live 前置登记同此处置（载体现仅施工卡）。

**INFO（披露，无需改动）**
- **INFO-1** BUD-01 被拒项即时状态实测为 **leased**（claim 后 mark 拒、未发送；测试允许 {pending, leased}，租约到期 recover 回 pending）——与"另一个保持待办（从未派发）"相容，披露实测值。
- **INFO-2** task_plan Phase 81 L1205 "StockQA **5** 变更面：llm_runner/transport/llm_integration/test_q09" 与实况 **4 面**不符（笔误，提交清单时修正）。
- **INFO-3** 多路由 fallback 下 route/group 槽按**意图路由**计数（卡已披露归因差异）：fallback 实际路由的槽在发送时不再被占用（begin 被旗跳过），global/成本/请求守恒与 I50 不受影响；单路由策略零差异。建议注释/卡补一句"fallback 下实际路由槽不计数"的边界。
- **INFO-4** 施工卡无独立"实施记录"节（记录在 task_plan Phase 81，数字复现相符）；卡记录"30s 自锁 32.9s→2.78s"未逐毫秒复测（需还原旗），机制已由 P4 实证（旗关 busy=True→30s 链、旗开 False）。
- **INFO-5** 拒绝 reason 现含 `str(exc)` 全文（准入码 ✓ 为 step 需求），会进入 QAEngine 拒绝结果文本/元数据（qa_engine L259）——可能携带本地路径类细节；建议仅保留码或脱敏。
- **INFO-6** StockQA 仓根 untracked 杂物（`nul`、`.codegraph/`、`.workbuddy-ai/`、`pilot_runs/*`、`progress_update.txt`）不在本批范围；其中 `nul` 会使全仓 rg 检索报 os error 1，建议内务清理。

## 8. 裁决

**approved**（无 P0/P1/P2 阻断项；双仓全部门独立复跑绿；六 case 语义经测试断言 + 独立探针双重核证；Q07 双预留接缝（INFO-3）由胶水 e2e rows==1 + 探针 P5/P4 实证闭环；范围严格 4+2 面、零网络、无过度声称）。LOW×6 / INFO×6 为非阻断整改与披露建议，随提交或下一并批处置。
