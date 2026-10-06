# B01 施工卡（写前报告 — owner 通授 2026-10-03 覆盖离线段；live 段 B01-b 另行成本声明+启动确认）

日期：2026-10-06。任务卡 B01「真实对照搜索交接、30题分组策略与缓存成本」，deps 全满足（L01✓ G1✓ Q05✓ Q09✓ Q10✓ Q12✓ W10✓）。
case：BENCH-01（live，owner=B01）/ BENCH-02（fault，owner=B01）；不变量：I01/I05/I11/I12/I17/I19/I21/I56。

## 两段拆解（本批=离线段 B01-a；live 段 B01-b 待 owner 放行）
- **B01-a（离线，本批 TDD）**：BENCH-02 预检门——公共入口在零/未知花费授权、缺价格快照、配额不可建立时，**在创建任何可派发 attempt 之前**返回显式 blocked/needs_configuration；**网络边界探针证明出站请求数=0**；无预算预留/无计费工作；生产名单/配置/数据库零漂移；有界原因可重试（审计性新 run id）。
- **B01-b（live，另批）**：BENCH-01 本体实验（样本 A/H/美各 1 家冻结、30 题与题库/路由/rubric/模型 revision/信息截止/搜索配置/方法顺序/gold/盲评 seed/预注册阈值/有限预算全部 manifest 冻结；Brave/Tavily 对照；顺序/并发≤4/3-5-10 分组/单批 30；两阶段模型比较；缓存正交子实验；双人盲评与门槛；Pareto；G3 审查）。**启动前置=成本声明（真实 Brave/Tavily/MiniMax 套餐口径）+ owner 明示放行**；未放行不执行。

## B01-a 设计（BENCH-02 四条 then 的钉子）
1. **入口级预检**：`main_with_llm` quick-scan 路径在 lifecycle 构造/预算预留之前：policy 未配置或 `budget.max_cost<=0` 或缺 `cost_policy` → 返回显式 blocked 结果（`needs_configuration` 有界原因，非裸异常），**不创建** work item/attempt/budget 行（现状 Q09 准入拒绝在 mark 时——预检前移至入口，语义一致、时点更早）。
2. **零出站证明**：测试级——harness 假传输 `session.post.call_count == 0` 且网络桩零请求（Q06 e2e 模式复用）。
3. **生产不漂移**：测试级——运行前后 workspace 快照比对（无新 work/budget/attempt 行、配置文件与正式名单未变）。
4. **可重试**：拒绝后以新 run id 重新入口可再走预检（审计性——断言新 run_id ≠ 旧 run_id 且原因有界）。
5. **缺口澄清**：B01-b 的成本口径（MiniMax 套餐 quota 单列、不虚构单价）与预注册阈值模板一并写入 B01-b 计划书骨架，随卡附上（占位）。

## 允许改动（I18）
1. `src/runners/llm_runner.py` — 入口预检（blocked 结果形态）最小增量
2. `tests/unit/test_b01_preflight.py`（新增）— BENCH-02 四条 then 钉子 + 零出站/不漂移
3. IQS：本卡、Phase 83、B01-b 计划书骨架（live 前置模板）
4. **禁改**：Q06-Q10 已验证面、模型策略语义、输出 schema、StockWiki

## 门与证据
- StockQA：定向（B01-a 新测 + 全回归电池 133+）→ 全量（基线 897→889+8… 以当时口径）→ mypy/ruff/black
- 独立审查两轮 → StockQA 隔离提交 → PWF 记档
- **无 live 成本**（B01-a 纯离线；B01-b 未启动故无 live 成本）

## 风险与边界
- 入口预检与 Q09 准入拒绝的语义分层：入口级=配置缺失/零授权（结构性）；准入级=运行中超支（运行性）——两层都 fail-closed，互不替代。
- B01-b 的全部 live 执行以 owner 放行 + 成本声明为硬门；本批不预支任何 live 行为。
