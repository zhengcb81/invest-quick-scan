# QA-04｜StockQA 有序模型策略的运行时语义

**可单独交给 StockQA harness 的施工指令。** Owner：`C:/Users/郑曾波/Projects/StockQAbyLLM/`；任务 Q04，前置 Q03、C05；验收 LLM-03、LLM-04、LLM-06、LLM-10、PAR-11。2026-09-30 观察到 `master@3c685dd` 且有 55 项既有未提交状态；这是观察值，开工时重新测。用户已授权 StockQA 全仓修改，但**每个批次写前须报备精确文件和目的**；本卡不授权 live API 或费用。只写 StockQA，不写 IQS/StockWiki。

## 目标与非目标

通过公开 Quick Scan 调用链证明：按用户顺序选 provider/model；只有可判定的本轮路由拒绝才尝试下一顺位；低分/unknown 不切换；首选路由仅因并发槽满时有界等候该路由，释放后仍发给它；运行中策略热更新只作用于尚未派发的问题，旧回答保留原 policy/model/dispatch 边界。失败中已可能发送的请求不能被当作未发送而重付费。Q08 的跨运行冷却和 Q11 的全局公平并发属于另卡，不借 Q04 擅自重做；旧任务 receipt 引擎不恢复。

已有路径事实：`LLMRunner._run_single_company` 一次构造 `OrderedSearchProviderCascade`，一次绑定预算并调用 `QAEngine.process_questions`；后者逐题执行。`LLMConfig.save_quick_scan_model_policy` 原子写策略，但当前注释为“下一次运行生效”。`begin_quick_scan_send` 在容量满时轮询约 30 秒再延期；cascade 在 `QuickScanBudgetDeferredError` 时终止本题、未自动切 B。这些是起步定位，不是验收证明；harness 要按当前提交和工作树再次核实。特别要保留 Q03 对畸形 `status=[]/{}` 的 parser 修复与完整搜索回执。

## 必读与写入边界

先读 IQS [`tasks.json`](../../tasks.json) Q04、[模型策略契约](../../contracts/providers-and-budget.md)、[StockQA lane](../lane-stockqa.md)、目标仓库当前 `AGENTS.md`（如有）、公开 Quick Scan CLI/runner/QAEngine/cascade/config/budget transport。用目标仓的 CodeGraph 看真实调用关系；动态构造需以公开入口测试补证。不要把 legacy `ProviderCascade` 当成 quick-scan `OrderedSearchProviderCascade`。

可能触及 `src/runners/llm_runner.py`、`src/core/qa_engine.py`、`src/config/llm_config.py`、`src/utils/llm_integration.py`、`src/utils/quick_scan_work_transport.py` 及相应 `tests/unit`、`tests/integration`；**此列表仅供预检，不是自动写入许可或要求全部修改**。在任何修改前报告最终精确路径、每个路径的目的、当前 HEAD/status 与目标文件 SHA。55 项既有状态逐项保留；禁止 reset/checkout 清理、整树 stage、盲目从裸 HEAD 建不含 Q03 修复的分支。无法冻结包含当前修复的输入快照则返回 `blocked`，不要在旧基线重做。

## 施工顺序与 TDD 反例

1. **基线和入口**：记录 `git status --porcelain=v1`、HEAD、Q03 关键文件 hash；查清 CLI → runner → `QAEngine` → ordered cascade → transport 的实际路径和事件/策略版本在哪层写回。先跑目标 owner 现有离线测试，不把已有失败算成新变更。
2. **LLM-10 RED**：以同一次多题运行开始 A>B；第一题已按旧 revision 派发后，受控更新配置 B>A。测试同时覆盖 `next_run`（本次其余题仍旧顺序）与明确 `immediate`（只在下一未派发题边界切换，新 revision/生效边界写入结果）。旧题记录的 provider/model、policy hash、response/receipt 均不变；失败写配置或无效版本不得半应用。测试必须走公开 runner/CLI 或其真实执行边界，不只测 config helper。实现最小热更新与原子 snapshot；定义读取频率、并发可见性和不可变策略记录。
3. **PAR-11 RED**：用受控阻塞 HTTP/共享槽位构造 A 健康、容量 1、已有 1 个 inflight，B 空闲。第二题在等待期间 A/B 的 POST 计数均为 0；释放 A 槽后只向 A 发 1 次，B 为 0。另测 A 一直不释放：有界等待后明确 `budget_deferred`/`retry_wait`、零 POST、不会无故 fallback。故障型 A429 才可走 B；容量等待不是 provider 拒绝。
4. **相邻回归**：LLM-03 A429→B score8，C 未调用；LLM-04 A 返回低分或 unknown 后不调用 B/C；LLM-06 搜索能力不足、无效请求、临时拒绝与永久配置错误分别输出既有规定状态与 route trace。失败路径依旧保存已执行搜索的 request/response/source 回执，unknown/null 不被外层数字覆盖。不要引入新的不兼容公开字段而不经 IQS 合同变更。
5. **GREEN 与审查**：最小修改、逐组测试，再在相同冻结快照做 owner 定向 unit/integration 和一个公开 CLI 离线 E2E。真实 HTTP 全部用 mock/本地受控 stub；没有 API key/live opt-in、没有下载或公司文档写入。预算槽测试用独立临时 SQLite/进程根，最终 assert 根已删除。仅在 Q04 这一高风险边界做一次聚焦只读审查；不逐函数审查。

## 验收和交接

验收必须给出 LLM-10 两种更新模式的逐题时间线（旧/新 revision、dispatch boundary、实际模型），PAR-11 的等待/释放/POST 计数时间线，以及五个 case 的测试名、命令、passed/failed/skipped。若只证明 transport 在槽满时等待，而未证明 runner 不重选 B，不算 PAR-11 通过。若只证明配置文件可保存，而未证明同一运行中未派发题生效，不算 LLM-10 通过。

按 [handoff schema](../handoff.schema.json) 返回 JSON：`package_id=QA-04`，base/result commit 与 dirty manifest hash、精确变更路径及 SHA、policy schema/revision 版本、RED/GREEN 结果、隔离根清理、`network_calls=false`/`paid_calls=false`、review findings、未完项。只能提交本包自有、可归属的改动；共享脏树无法安全分离则不提交并说明。Q04 完成不等于 G1、Q08、Q11 或跨仓运行闭环完成。
