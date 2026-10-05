# Q06 收尾批次施工卡（写前报告 — owner 已确认，2026-10-05 round-41）

> **开工前置已全部满足**：`G2` r2 = verified_for_local_gate_scope ✓；**owner 卡确认（round-41 原话「Q06 卡确认，两取舍签认」）** ✓；附带完成 W06 两处取舍签认（case② 无 work_item reuse 豁免、F2 resume-first——原记"待签认"，现已取得，见 progress 同批记录）。C04✓。本卡自草案转正，允许文件清单于动工时按现状复核一遍。

## 授权与背景
- Q06 现状（tasks.json 卡 + Phase 16 记录）：第一段 SQLite 待办原语、第二段同步 transport 边界均已独立复审；**剩余缺口 = 公共题路径未绑定真实 work item（claim/lease 生命周期不进循环）+ step 5 issuer 级去重未验收**。完成后 Q06 partial→verified，W11 随之解锁。
- StockQA = owner 仓（报备制：本卡即拟改文件/目的报备）；完成后独立审查两轮制。

## 只读勘察结论（2026-10-05，绑定点已锁定）
- `src/runners/llm_runner.py:479-491`：`QAEngine(llm_provider, answer_generator)` → `process_questions(questions)`，外层已有 `bind_quick_scan_budget(budget_store, quick_scan_policy, ...)` 上下文（Q09 预算已接，`QuickScanWorkStore` 实例已创建于 :398）。
- **缺口**：题循环（QAEngine 内部）没有逐题 `claim/lease` work item；`quick_scan_work_store.py`（2600+ 行）与 `quick_scan_work_transport.py` 的 send_intent/attempt 阶段机已存在但不经此路径被使用。
- 设计取向：**QAEngine 增加可选 per-question 生命周期钩子**（派发前 claim/lease、拿到响应后记录 attempt 终态），runner 注入 store 绑定；不开新平行执行路径。issuer 级去重靠 `logical_work_key(entity_id, question, generation, scope, scope_id)` 的存储唯一约束 + 同 issuer 不同 listing 的 scope_id 分立。

## 允许改动文件（仅这些；动工前按现状复核）
1. `src/core/qa_engine.py` — 可选 work-item 生命周期钩子（无注入时行为逐字节不变）
2. `src/runners/llm_runner.py` — 在 :479-491 seam 注入 store/钩子；不改预算/策略/级联既有语义
3. `tests/unit/test_q06_work_binding.py`（新增）— TDD 主战场
4. 视需要：`src/utils/quick_scan_work_store.py` 仅限补 issuer 去重所需的最小查询/约束缺口（若唯一约束已足则不改——先测后改）
5. **禁改**：transport 协议、Q09 预算上下文、Q07 checkpoint（下一卡）、任何 policy/CLI 参数面

## 语义边界（不变量）
- 零注入时 QAEngine 行为不变（现有全部测试必须原样通过）；
- claim 原子（同 logical key 并发只领一次）、租约过期可恢复、**迟到旧 worker 拒绝覆盖**（store 已有，需经此路径被实测）；
- dispatch 前未完成 claim → 不得发送；失败/未知按 C04 状态机，不盲重发；
- issuer 级题跨 listing 幂等一条；listing 级题各自独立；
- 不引网络、不改 prompt/评分语义、不动 frozen L02 资产。

## TDD（先红后绿）
- R1：无钩子时 process_questions 输出与现状逐字节等价（现有测试即证）；
- R2：注入后每题派发前存在 claimed+leased 项、响应后到达终态；重复 run 同 key 幂等；
- R3：并发双 claim 同 key → 一领一拒（子进程/线程级）；
- R4：租约过期 → 恢复路径 + 迟到 worker 的旧 token 写被拒；
- R5：同 issuer 两 listing 各派一次 issuer 级题 → 存储一条 work item；listing 级题两条互异；
- R6：公开 CLI 端到端（test_quick_scan_cli 现有入口）+ 回执含 work item 关联。

## 门与证据
- 定向 pytest → 全量 owner 批次（上次基线 846+ 口径）→ ruff/black/mypy（仓库钩子标准）→ 独立审查两轮 → StockQA 隔离提交（DWA-06R 分组纪律）。
- 完成判据按 Q06 卡：全部 case 有实际结果、提交快照/变更文件/复现命令/测试摘要、独立审查最新版后 verified。
