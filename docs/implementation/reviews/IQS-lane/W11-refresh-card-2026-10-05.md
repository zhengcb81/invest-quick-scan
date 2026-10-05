# W11 定向补扫施工卡（写前报告 — owner 通授 2026-10-03 覆盖本批，条件=本报告+独立审查）

日期：2026-10-05（round-55）。任务卡 W11「接通有范围与预算的定向补扫」，deps 全满足（W06✓ W09✓ W10✓ Q06✓）。
case：QUERY-04 / TIME-05 / JOB-06 / DB-07；不变量：I09 / I13 / I18（定义见 decision-register.md L15/L19/L24）。

## 只读勘察结论（本轮完成）
- **W09**（StockWiki `ac5a653`）：`stockwiki/quick_scan_query.py`（501 行）五公共接口 `query_capabilities`/`coverage`/`search`/`get_profiles`/`export_candidate_set`+`reload_candidate_set`——缺口检测与范围校验的原料。
- **W10**（StockWiki `3a3d061`）：`stockwiki/quick_scan_delivery.py`（283 行）`project_runtime_status`/`ack_status`/`validate_ack`/`reconcile_delivery`——执行状态只读投影。
- **`request_refresh` 在 StockQA/StockWiki 源码均不存在**（grep 实证）——本批要新建的拥有者接口。
- **StockQA 执行入口现状**：`main_with_llm.py --require-search --entity-id ...`（Q06 后含 `--identity-snapshot`）+ Q09 预算绑定（`bind_quick_scan_budget`）——"复用同一执行入口"的现实基座已齐。
- Q06（Phase 78）已 verified：work-item 生命周期、claim/lease、诚实终态与不重派发（JOB-10/I12 基座）。

## 设计（尊重 I13/I18：消费者只读、补扫走拥有者接口、一任务一写入 owner）
1. **StockWiki 新模块 `stockwiki/quick_scan_refresh.py`（唯一写入 owner）**：
   - `request_refresh(request) -> RefreshTask`：
     - 输入 `{entities[], fields[], cost_cap, roster_version?}`；
     - **范围校验（QUERY-04 负例）**：实体 ∈ 候选集（W09 视图/导出）、字段 ∈ `query_capabilities` 字段——越界即具名拒绝；**无 SQL 面**（消费者拿不到写库通道）、**不扩全池**（只取 交集×真实缺口）；
     - **缺口检测走 W09 `coverage`**（I09：按字段与实际信息；阈值类规则变更→派生更新、模型调用 0——TIME-05 的两请求语义）；已覆盖字段**复用不重问**（QUERY-04「有效字段复用」）；
     - **费用上限**：估价超 cap 具名拒绝（QUERY-04「费用上限适用」）；
     - **增量语义（JOB-06）**：携带 `roster_version`（V1 未完成 + 新增 E_NEW → V2）→ 输出=增量：旧任务项**不重建**（同逻辑键保留）、新实体并入，版本与覆盖可追踪。
   - 输出：refresh task 工件（JSON，批号+版本+coverage 指纹）——**格式对齐 StockQA 现有入口可消费的题面/实体清单**，不发明第二套执行路径。
2. **StockQA 侧**：经**既有** `main_with_llm` 入口消费工件（题面=请求字段的问题清单、实体=白名单增量）；预算与用户模型策略由执行器（Q09 绑定+模型策略）统一落实（W11 step2 原文）——预期 **StockQA 源码改动=0**，若接线必须则仅限 `main_with_llm.py` 且在本卡具名。
3. **状态回读**：执行状态经 W10 `project_runtime_status` 只读投影，消费者不写库（I13）。

## 本批执行的 case
- **QUERY-04（W11 自有）**：3 家×2 字段部分有效 + 范围外实体/SQL 写入尝试 → 具名拒绝、cap 生效、无全池、有效字段复用（负例集成测试）。
- **JOB-06（W11 自有）**：V1 未完成 + E_NEW → V2 → 旧任务不重建、增量并入、版本/覆盖可追踪（集成测试）。
- **TIME-05（owner=C04，本批一并执行其契约测试）**：纯 `work_contract` 双请求——阈值改动模型调用 0、+3 新题恰产生 3 个逻辑待办键、旧观察不可变（无 DB/worker/HTTP）。
- **DB-07（owner=Q10）**：不在本批执行；其「消费者不写 SQLite」面向 I13 的部分由本批接口设计覆盖，durable block/outbox 语义留给 Q10。

## 允许改动（动工前按现状复核；I18：接入不重写）
1. **新增** `StockWiki/stockwiki/quick_scan_refresh.py` + `StockWiki/tests/test_quick_scan_refresh.py`
2. 视需要：`StockQA/main_with_llm.py`（仅接线，预期为 0；若改须具名+说明）
3. IQS：本卡、Phase 79、case 执行记录
4. **禁改**：`quick_scan_query.py`/`quick_scan_delivery.py` 内部（调用不重写）、W05 ledger、StockQA transport/policy/Q09、Q06 已验证面

## 门与证据
- StockWiki：`check_all.sh`（基线 923 passed + 新测试，framework 0 errors，coverage ≥73%）+ black -l100 + ruff
- StockQA（若触碰）：定向 + 全量 881 口径 + mypy/ruff/black
- IQS：plan validate（107 卡/366 场景/G6）
- 独立审查两轮（needs_revision→fix→approved）→ 各仓隔离提交 → PWF 记档
- 无 live 成本（纯离线接口与测试；不调用任何 LLM/网络）

## 风险与边界
- W09/W10 接口是**已验证的真实接口**（I18）——本卡只调用公共函数，不触 SQLite 内部。
- 「reusing the same StockQA execution entry」以现实为界：入口= `main_with_llm` 既有参数面；若覆盖某字段需要新题面，题面清单由工件携带，不改执行器。
- TIME-05 的「筛选派生更新」语义按其原文（纯函数、不启用 DB/worker/HTTP）实现与测试。
