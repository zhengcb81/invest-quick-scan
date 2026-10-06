# Q09 施工卡（写前报告 — owner 通授 2026-10-03 覆盖本批；纯离线无 live 成本）

日期：2026-10-06。任务卡 Q09「实现并发派发上限、费用预留与预算停止」，deps 全满足（Q06✓ C05✓ 已 verified）。
case：BUD-01 / BUD-02 / BUD-03 / BUD-04（owner=L01）/ PAR-01 / JOB-09；不变量：I11 / I12 / I50。

## 只读勘察结论（本轮完成）
- **store 预算机器已建成**（Q09 自身首段产物）：`_reserve_budget_attempt_tx`（L1047）含**全部准入门**——not_configured / version_stale / route_not_in_policy / **reconciliation_required（I50 对账门）** / **budget_cost_limit**（金额）/ **budget_request_limit**（请求）/ **三层在途槽**：global（L1111）/ quota_group（L1122）/ route（L1129），全部为**事务内 `COUNT(*) WHERE in_flight=1` 计数**（崩溃不丢内存计数 → PAR-01 崩溃安全性天然成立）；`quick_scan_budget_attempt` 状态机（in_flight/response_unpriced/failure_unpriced/**outcome_uncertain 保留 in_flight=1**（L1231 = BUD-03 保留预留）/settled）+ 部分唯一索引（L227）；`budget_totals`（L1403）守恒汇总；`reconcile_budget_attempt`（L1327）；`configure_quick_scan_budget`（L981，幂等+冲突门）。
- **transport**：`bind_quick_scan_budget`（L328，注册 policy + 上下文绑定）+ work-less 路径 `reserve_budget_attempt(DISPATCH_*)`（L482，与 CLI 路径不重叠）；`mark_send_intent(budget_policy, budget_route)`（L1670，两参数成对，调 `_reserve_budget_attempt_tx` L1704）= **reserve 的唯一 work 路径**。
- **cascade 侧**：`OrderedSearchProviderCascade._preferred_route_busy`（llm_integration L1009）已按 route 读 `quick_scan_budget_attempt.in_flight` 做路由级避让——与 mark 时预留同账本（读-写一致）。
- **Q07 已铺的缝**：lifecycle ctor 有 `budget_policy/budget_route` 成对参数（默认 None=Q06 语义）。
- **真缺口（本批核心）**：
  1. **runner 未接线**——`llm_runner` 构造 lifecycle 时**没有传 policy 对**，故 CLI 路径今日 **reserve-before-dispatch 实际未激活**（I11 缺口）；route 归因需定：以**首选路由意图**预留（cascade 实际选路在预留之后），route 槽计数=意图路由——单路由策略下意图=实际，多路由 fallback 的归因差异**如实披露**（总量账本不受影响，I11 核心=总额守恒）。
  2. **时间上限**：policy 投影无时间字段 → runner/lifecycle 侧 `deadline` 门（到点 before_question 拒绝=停止新派发、在途回执继续结算——step3 原文）。
  3. **六 case 测试**多为 store 已有机制的 Q09 级钉子 + PAR-01 跨进程实测 + JOB-09 owner 入口。
  4. **ADV-1**（W11 审查遗留，随本批）：`quick_scan_refresh` 工件 company 标签 entity_id → **canonical_name**（W09 投影已带）+ e2e 一行断言。
  5. **INFO 双预留接缝**（Q07 审查遗留）：CLI 路径=mark 唯一预留（bind 的 work-less DISPATCH_* 路径不重叠）；本批测试钉死"一 send 一 reserve"（reserves 计数=1）并把路由归因披露入 docstring。

## 设计
1. **reserve 接线（step1/step2/I11）**：runner 构造 lifecycle 时（quick_scan_policy configured 且 identity/snapshot 激活路径**或** policy 激活路径）传 `budget_policy=policy` + `budget_route={route_id, provider, model_requested, quota_group}`（取 policy 首选 route，字段与 mark 的四键校验对齐）；lifecycle 已成对校验。BUD-01 的原子性=store 事务（已有）；失败/搜索/备用同账本=quick_scan_budget_attempt 单表（已有，测试钉守恒）。
2. **时间停止（step3）**：lifecycle 增 `deadline`（monotonic，可选）——超点 `before_question` 返回拒绝 `time_cap_reached`（不 claim、不发新请求）；在途题的 after 照常结算（现有路径）。
3. **三层槽/崩溃安全（step4）**：已有 DB 计数——本批**跨进程测试**实证（PAR-01）；`_preferred_route_busy` 的直连 sqlite3 只读在本批**改为经 store 公共只读方法**（I18 精神自查：接入不重写，行为等价）或如实留档（动工前按现状定，若改=store 增一个只读 count 方法）。
4. **六 case 映射**：BUD-01=并发双预留原子（线程×2 同 store，恰一 admitted，totals≤budget，另一 pending）；BUD-02=cost_limit 拒 + 备用不破总额（同账本守恒断言）；BUD-03=outcome_uncertain 保留 in_flight + 先对账后重试序 + 无证据不承诺零重复费用；BUD-04=**owner L01**——本批只断言"policy 未配置/价格未知→准入拒绝（不无限跑）"并把上线计价版本/保守费用边界登记为 live 前置（随 B01/L03 live 成本声明模板）；PAR-01=两子进程 + 阻塞 stub + 真重叠 + 三层 ≤ 上限 + 崩溃不超发；JOB-09=owner 入口（mark/准入）在 in-flight+超支下原子拒、在途可结算、后续派发 0、账本守恒。
5. **ADV-1**：StockWiki `quick_scan_refresh.py`——`request_refresh` 从 profile 取 `canonical_name` 写入 item，`render_refresh_artifact` company=canonical_name（缺省回落 entity_id 并注释）；W11 e2e 补 company 断言。

## 允许改动（I18 接入不重写）
1. `src/runners/llm_runner.py` — policy 对接线、deadline 门、（如改）route 归因披露
2. `src/core/qa_engine.py` — **预期 0 改动**（拒绝面已通用）
3. `src/utils/quick_scan_work_transport.py` — 仅限既有接缝的一致性小改（先测后改）
4. `src/utils/quick_scan_work_store.py` — **仅限**：只读 in-flight count 公共方法（如决定收编 llm_integration 直读）；三层门/状态机**禁改**
5. `tests/unit/test_q09_budget_concurrency.py`（新增）— TDD 主战场（PAR-01 含跨进程子测试）
6. StockWiki：`stockwiki/quick_scan_refresh.py` + `tests/test_quick_scan_refresh.py`（ADV-1 两文件小改）
7. **禁改**：Q06/Q07 已验证面（生命周期契约/检查点/预检）、模型策略语义、输出 schema

## 门与证据
- StockQA：定向（新 Q09 测试 + Q06 15 + Q07 8 + 回归电池）→ 全量（基线 889 口径，`-p no:base_url`）→ mypy/ruff/black(100)
- StockWiki：定向（W11 4+ADV 断言）→ `check_all.sh`（基线 929 口径）
- 独立审查两轮 → 两仓隔离提交 → PWF 记档
- **无 live 成本**（全离线：线程/子进程/阻塞 stub/临时库；不调用任何 LLM/网络）

## 风险与边界
- 多路由 fallback 的 route 归因=意图路由（披露；总额守恒不受影响）——若审查要求实际路由归因，则需把预留移到 cascade 发送点（接缝变大，届时提请）。
- PAR-01 的"两进程"在 Windows 上用 `sys.executable -c` 子进程 + 同一 store 文件实现（busy timeout 已有）。
- BUD-04 是 L01 的 case：本批只交付"未知价格必拒"断言与 live 前置登记，不宣称 L01 本体。
