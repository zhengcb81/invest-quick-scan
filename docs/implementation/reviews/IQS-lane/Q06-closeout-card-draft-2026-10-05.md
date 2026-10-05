# Q06 收尾批次施工卡（写前报告 — owner 已确认，2026-10-05 round-41；r1 needs_revision 整改中）

## 审查 r1（needs_revision，3×P0）与整改计划（2026-10-05）
审查报告 `docs/implementation/reviews/Q06/independent-review-2026-10-05.md`：门全绿复跑（872/0、mypy 0、定向 6、回归 97、反证 18 错=缺 `-p no:base_url` 旗标）+ R1 零注入等价通过 + golden 映射逐项一致；但：
- **P0-1**：`json.dumps(List[Question])` 构造即 TypeError（生产路径一题跑不到）；loader/CLI/构造段零测试。→ 修复：指纹改为题面文本规范 JSON 的 sha256（64-hex，兼修 P0-2a 的 `rf-` 前缀违规）；补 loader/CLI/runner 构造 RED。
- **P0-2b**：真实 `ENT_<uuid>` 连字符被 store `_ENTITY_ID` 拒 → **owner 已签认放宽（round-51 结构化决定「签认：放宽正则（推荐）」）** → 改 store 正则+反例测试+卡记签认；loader 补 `payload.entity_id` 与 `--entity-id` 互校（P1-2）+ provisional 多不同 refs fail-fast（P1-3）。
- **P0-3**：attempt 流缺 `mark_send_intent` → 终态永不落、租约过期重复派发（违反 JOB-10/I12）。→ 修复：before_question 补 `mark_send_intent`（transport 语义：prepare→mark 在发送前；`budget_route`/`budget_policy` 无预算上下文时成对 None，有则取真实 policy route/quota——runner 注入真实 route 字段替换占位常量）；after 成功仅在结果携带真实 response 事实时记 `response_available`+真 receipt_sha256，否则**如实记 `unknown`**（禁臆造 http 200）；after_failed 记 `unknown`（非 confirmed_failure，无 provider 拒绝证据）；补 RED：成功后 work_item=result_ready 且租约过期不重派发。
- **P1**：R3 改真并发（线程/子进程）、R6 改真 CLI 端到端（`--identity-snapshot` 路径到 work_item 回执关联）、lifecycle 支持 scope/scope_id 参数（JOB-11 绑定路径）、source_binding_version 硬编码=1 入 docstring+卡披露（W04 导出不含该字段，披露为已知限制）。
- **P2/LOW**：拒绝结果摘要计数（qa_engine 完成行区分成功/拒绝）、prompt_sha256 docstring 对齐公式、before_question 不得抛出契约入 docstring。

## 实施完成记录（2026-10-05，四重门全绿）
- **改动 4 文件**：`src/core/qa_engine.py`（可选 `work_item_lifecycle` 钩子：claim 拒绝→error 结果不派发、success→after、失败→after_failed；缺省 None 逐字节不变）、`src/runners/llm_runner.py`（`QuickScanWorkLifecycle` 类 = create_or_attach→claim→prepare_attempt→record_outcome 全生命周期 + `load_identity_snapshot` W04 导出映射 + `run(identity_snapshot=)` 校验与线程 + entity_id 收窄）、`main_with_llm.py`（`--identity-snapshot` CLI 参数 + 透传）、`tests/unit/test_q06_work_binding.py`（6 场景 RED→GREEN）。
- **门（最终字节）**：black(100) 0 · ruff 0 · mypy 0（3 源文件）· **全量 pytest 872 passed / 4 skipped / 0 errors**（`-p no:base_url` 旗标——缺旗标时第三方插件 ScopeMismatch 18 错，属命令旗标非代码回归）· Q06 定向 6/6。
- **设计要点**：prompt_sha256 = 题面+快照 sha 的渲染前代理（类 docstring 明示）；`--identity-snapshot` 必须与 `--require-search` 同用；identity 快照文件 sha256 钉进 work_item；provisional/verified 单绑定均支持（多 listing refs 去重取首）；生产接线消费 W04 公开导出（golden 形状 = `stockwiki-g2b-72531b5-provisional.json`）。

> **开工前置已全部满足**：`G2` r2 = verified_for_local_gate_scope ✓；**owner 卡确认（round-41 原话「Q06 卡确认，两取舍签认」）** ✓；附带完成 W06 两处取舍签认（case② 无 work_item reuse 豁免、F2 resume-first——原记"待签认"，现已取得，见 progress 同批记录）。C04✓。本卡自草案转正，允许文件清单于动工时按现状复核一遍。

## 授权与背景
- Q06 现状（tasks.json 卡 + Phase 16 记录）：第一段 SQLite 待办原语、第二段同步 transport 边界均已独立复审；**剩余缺口 = 公共题路径未绑定真实 work item（claim/lease 生命周期不进循环）+ step 5 issuer 级去重未验收**。完成后 Q06 partial→verified，W11 随之解锁。
- StockQA = owner 仓（报备制：本卡即拟改文件/目的报备）；完成后独立审查两轮制。

## 只读勘察结论（2026-10-05，绑定点已锁定）
- `src/runners/llm_runner.py:479-491`：`QAEngine(llm_provider, answer_generator)` → `process_questions(questions)`，外层已有 `bind_quick_scan_budget(budget_store, quick_scan_policy, ...)` 上下文（Q09 预算已接，`QuickScanWorkStore` 实例已创建于 :398）。
- **缺口**：题循环（QAEngine 内部）没有逐题 `claim/lease` work item；`quick_scan_work_store.py`（2600+ 行）与 `quick_scan_work_transport.py` 的 send_intent/attempt 阶段机已存在但不经此路径被使用。
- 设计取向：**QAEngine 增加可选 per-question 生命周期钩子**（派发前 claim/lease、拿到响应后记录 attempt 终态），runner 注入 store 绑定；不开新平行执行路径。issuer 级去重靠 `logical_work_key(entity_id, question, generation, scope, scope_id)` 的存储唯一约束 + 同 issuer 不同 listing 的 scope_id 分立。

## 开工侦察发现二（2026-10-05，owner 已选**选项 1 一次收口**）
`create_or_attach` 需要 15 参数的 **C04 身份载荷**（entity_id ENT_ 格式、identity_revision≥1、source_binding_version≥1、identity_state provisional/verified、source_binding_ref(s) BIND_ 格式、identity_snapshot_sha256、question/routing 指纹、run_id/scan_id）——现行 quick-scan CLI（L02 模式）用 `probe:*` **零身份**跑法，不携带这些字段。因此"CLI 绑定"存在设计分叉：
- **选项 1（owner 选定，机制优先）**：Q06 落地**机制**（QAEngine 可选生命周期钩子 + store 全语义，测试用注入载荷证明 claim/lease/去重/恢复）；CLI 增 `--identity-snapshot <file>`（消费 W04 公开导出的身份包 `identity-export-g2b`，结构校验后映射为载荷）作为**生产激活路径**；无 snapshot 的 probe 式运行生命周期关闭、行为与今日逐字节一致。L02 可复现性不受影响。
- ~~选项 2~~（未选）：Q06 仅机制 + 测试（注入载荷收口），`--identity-snapshot` 生产接线另立小卡。
- 附带事实：W04 公开导出 `identity-export-g2b` 已存在（StockWiki 公共 CLI），身份包 2.2.0 含 Entity 2.1.0 全字段——生产接线的原料是现成的；工作量主要在 StockQA 侧的映射与校验。

## 允许改动文件（仅这些；动工前按现状复核）
1. `src/core/qa_engine.py` — 可选 work-item 生命周期钩子（无注入时行为逐字节不变）
2. `src/runners/llm_runner.py` — 在 :479-491 seam 注入 store/钩子；不改预算/策略/级联既有语义
3. `tests/unit/test_q06_work_binding.py`（新增）— TDD 主战场
4. 视需要：`src/utils/quick_scan_work_store.py` 仅限补 issuer 去重所需的最小查询/约束缺口（若唯一约束已足则不改——先测后改）
5. **禁改**：transport 协议、Q09 预算上下文、Q07 checkpoint（下一卡）、既有 policy/CLI 参数语义（选项 1 **新增** `--identity-snapshot` 为加法，不动既有参数）

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

## r1 整改批记录（2026-10-05 round-52/53，14/14 测试）
- **P0-1**：`routing_fingerprint_for(questions)`（题面文本规范 JSON → 64-hex）替换 json.dumps(Question) 崩溃；loader 补 golden 形状断言测试。
- **P0-2**：store `_ENTITY_ID` 放宽含连字符（**owner round-51 结构化签认**，注释入 store）；构造点 rf- 前缀去除；`load_identity_snapshot(expected_entity_id=)` 与 `--entity-id` 互校（P1-2）。
- **P0-3**：`before_question` 补 `mark_send_intent`（transport 语义 prepare→intent，预算 policy/route 成对 None 并在 docstring 披露 Q09 配对待接）；成功/失败均如实 `outcome="unknown"`（禁臆造 200/回执——response_available 需真 2xx+回执、confirmed_failure 需可识别拒绝）→ attempt=uncertain、work_item=uncertain 清租约：claim 永不可领、C04 视 uncertain 为 resume；R4 重写为**双恢复路径**（未发送→pending 重领；已发送→uncertain 永不重派 + 迟到 fenced）。
- **额外发现（审查者未列）**：`request_cache_key` 未含 work_item_id → 同题跨 scope 键冲突被 store 全局检查（L1620-1635）拒绝——按 transport 同一公式（work_item_id+route_id+provider+model+prompt_sha）修正。
- **P1**：R6 真 CLI 端到端（monkeypatch run 接线，无 LLM 调用）；lifecycle 增 `scope/scope_id`（JOB-11 绑定路径测试）；provisional 多 ref loader fail-fast（verified 放行）；source_binding_version=1 披露（W04 导出不含，待权威版本替换）。
- **P2/LOW**：拒绝计数独立摘要（refused 不入"成功 N/N"）；docstring 全对齐（prompt_sha=`sha(identity_sha|题面)` 渲染前代理、run_id=UTC 派生、scan_id="scan-l02"、before 不抛出契约）。
