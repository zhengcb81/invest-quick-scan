# 执行链未提交/未并线盘点

2026-11-11；只读盘点。范围：StockQA、Company Agent、Runtime canonical、各自注册 worktree，以及 IQS 下两份已有候选副本。未执行源码测试、merge、checkout、fetch、delete 或收费 API，未读取密钥/个人记忆内容。所有 Git 查询使用 `GIT_OPTIONAL_LOCKS=0`。这是盘点快照，不是源码质量验收；执行清理/并线前仅复核目标是否改变，不新增审批门。

## 结论与优先顺序

1. **没有发现需要立刻合并的遗漏 feature commit。** StockQA 两个旧分支都已真正进入 master；CA 公开 API 已在 master；Runtime 唯一长期分支就是当前实际主线，仓库没有另一个 main/master 可合并。不要只因分支名含 codex 就再建 main。
2. **真正未交付的是工作树源码。** QA canonical facade1.5 与候选1.8 分叉；Runtime candidate虽更完整，却没有 canonical 独有的 launcher 修复。两份 `.tmp-*` 根都带独立 `.git`，并非 canonical 注册 worktree，不能当垃圾删除或一份覆盖另一份。
3. **已明确识别可再生测试残留。** 候选内部19个 pytest临时目录，CA一份合成board、QA零字节stderr，以及Runtime两个已经只剩 `.git` 指针的旧验收worktree。总控可以按本报告具体目标清理；不得清理候选根。
4. 未验证的历史试验源码、个人本地配置/记忆、`nul`、`progress_update.txt`保留；“旧”或“未跟踪”不是删除理由。
5. 施工顺序沿原 MC-CA / MC-QA / MC-RT：CA验证既有公开接口；QA/RT分别归拢已有源码并自包含提交；总控再验证当前公开版本组合。旧交付pin/用例数改动不再要求刷新求绿。

## Git 基线与本地分支

|对象|HEAD / branch / upstream|未提交（逐文件、非忽略）|判断|
|---|---|---|---|
|StockQA canonical|`4c24789a2c2d93eb24cae8ef4dacb00d6f585c23`，master → origin/master|77 tracked修改；24 untracked；staged为空|本地origin/master同SHA，本轮未查远端网络|
|QA候选|`4c24789...`，master → origin/master|87 tracked修改；307 untracked（其中290为测试临时路径，17为源码/测试）|独立Git副本，不能用HEAD代表候选内容|
|Company Agent|`793bfbc239edc596c7edabeab48df97fdcc5e99f`，master，无upstream/remote|0 tracked；3 untracked|公开API2.3已提交，不存在待并分支|
|Runtime canonical|`5839ef4c4f3ec66c0994fb0531009d227631294d`，codex/agent-run-02，无upstream/remote|24 tracked修改；9 untracked；staged为空|唯一local branch；不是“未合main”的侧枝|
|Runtime候选|`5839ef4...`，codex/agent-run-02 → 本副本origin/codex/agent-run-02|49 tracked修改；5538 untracked（5526为测试临时路径，12为源码/测试）|独立Git副本；原owner并无remote|

非忽略路径统计与物理文件数不同：临时目录内部分sqlite、pyc等被原.gitignore忽略。目录物理计数在清理表单列。

### 所有 local branch 的真实并线判断

- StockQA `codex/g2-sqa-docs-main@0f8fbfa49c212b6bbcc986f876f80eb53e6bde5d`：
  `git rev-list --left-right --count master...branch` 为 **117 / 0**；`master..branch`无提交；`git cherry master branch`为空。它是真祖先，不只是patch等价；不用再merge/cherry-pick。
- StockQA `codex/g2-stockqa-checks@57dca677d505809e74cd50a57ce5475d2e2e1f82`：
  同样 **119 / 0**；unique log/cherry均空。其注册工作树 `C:/Users/郑曾波/Projects/_g2/StockQAbyLLM` 当前tracked/untracked/staged均为空。保留可供历史检查；若总控确需清掉冗余工作树，确认无活动writer后用该owner的worktree管理删除，不删源码历史。
- CA只有master，无其它local branch。
- Runtime只有codex/agent-run-02，无main/master。两个旧 detached 验收worktree的提交
  `c15ad9a2ff49fd20e9cb2c71ae960012a3ad8fe5` 和
  `cab51759299f86e1afdb897d42979f745b47b83a`
  都经 `merge-base --is-ancestor <sha> HEAD`确认进入当前5839ef4。没有独有commit需要并线。
- 两个IQS候选各只有对应owner的单一分支，没有候选commit领先canonical；价值全部在未提交文件。
- 未执行fetch/ls-remote；这里的upstream结论仅为本地ref，不能写成最新远端已核验。canonical CA/Runtime当前 `git remote`确实为空，旧文档中的“CA有origin但无tracking ref”不能继续作为当前事实。

## 未提交内容分类与承接

### StockQA → MC-QA

|组|路径范围/数量|分类与处理|
|---|---|---|
|canonical执行源码|53份 `src/`，`scripts/checks.py`|有效实现候选：lifecycle/owner ports、provider能力、已付响应恢复、公共store操作。保留；未测试不宣称都正确|
|canonical测试|23份tracked tests；4份untracked测试/支撑|与源码成套归拢，不能只提交测试或只提交已有tracked文件|
|canonical新接口|9份 `src/interfaces/`、`src/utils/` untracked|属于实际封装工作，必须保留并随依赖提交|
|候选新增|CompanyScanContract、task factory和其2份tests，仅候选存在|MC-QA必带入，canonical没有这些文件|
|候选更深修复|比canonical多docs、journal、并发/visible-output/recovery tests等|逐hunk合并；不能简单“最新候选全覆盖”|
|历史实验|6个 `pilot_runs/` 未跟踪文件（具体见附录）|runner/stratification/summarize是历史试验源码/记录；不因年龄删除。其中空stderr可单独删|
|个人/索引|2个 `.workbuddy-ai/memory/` 文件；`.codegraph/.gitignore`|保留；未读个人内容。CodeGraph是用户授权索引，不视为垃圾|
|待判定|`nul`、`progress_update.txt`|保留。NUL真实普通文件57字节；普通Path会误当设备显示0字节，不能按错误stat删除。progress_update为1005字节，未检查内容|

QA candidate与canonical对“改动路径并集”做CRLF归一后逐文件比较：53份相同，47份不同，4份只候选存在。**canonical没有候选未包含的独有改动路径，但47份内容差异仍需逐hunk归拢。**

候选独有源码/测试：
```text
src/interfaces/quick_scan_company.py
src/utils/_quick_scan_company_task_factory.py
tests/unit/test_quick_scan_company_contract.py
tests/unit/test_quick_scan_company_task_factory.py
```

与canonical相比，候选另外修改而canonical未改的已有文件：
```text
docs/architecture.md
src/utils/quick_scan_refresh_admission_journal.py
src/utils/quick_scan_subject_journal.py
tests/unit/test_paid_visible_journal.py
tests/unit/test_provided_answer_sources.py
tests/unit/test_q09_budget_concurrency.py
tests/unit/test_quick_scan_question_pack_store.py
tests/unit/test_quick_scan_work_store.py
tests/unit/test_research_visible_output.py
tests/unit/test_terminal_received_recovery.py
```

最小承接/验证：沿MC-QA把facade1.8及接口/适配/恢复源码归拢成自包含commit；先跑该卡公开边界短组，再按改动跑已付恢复、question pack、共享额度相关tests。未经代码验收不建议今天仅为清工作区仓促提交87份。

### Company Agent → MC-CA

- `793bfbc`已把api/public_port/task及两组test提交到master，0 tracked diff，无待合并feature branch。
- `.codegraph/.gitignore`、`.codegraph/config.json`：授权建立的索引配置，保留。
- `fixtures/locked/synthetic/boards/run-context-compact-2.board.json`：49270字节，顶层`protocol/synthetic/records`、8条合成记录。出处已定位：
  `tests/test_usage_cache.py:187–197`构造合成长摘录并调用`make_task(..., run-context-compact-2, board=board)`；
  `tests/conftest.py:63–76`的helper直接写入该locked fixture路径。
  此文件是可再生测试残留，可精确删除；MC-CA同时把helper的可写输出迁到pytest tmp_path/临时输入根，避免下次又污染source。
- 针对性验证：卡内public API/task port组，加`tests/test_usage_cache.py::test_context_compression_boundary_keeps_traceability`；测试结束应不再产生此未跟踪文件。无需新建remote或额外“并到master”。

### Runtime → MC-RT

canonical24份tracked：
- 9份src + launcher：实际API/薄桥/源装配改动，保留。
- 10份tests：对口回归，保留。
- README/content/integration-notes：接口说明/合同，审核后归拢。
- `tools/lock_inputs.py`：说明补上必须的`--wave-lock`，不是运行逻辑变化。
- 9份untracked：5份API/adapters +4份tests，属于有效封装候选，不删。

candidate49份tracked +12份新源码/测试：
- 比canonical含更完整的当前公开DTO/opaque/frozen兼容和测试支撑。
- 8份旧`docs/handoff/AGENT-RUN-02/*`及9份tools多数围绕旧pin/计数/交付生成；按MC-RT保留历史，不把它们的“全绿”作为现在生产源码并线门。源码有关测试仍保留，文档核查分组不应误删业务测试。
- 来源比较：4份改动路径内容相同、57份不同，3份只candidate存在。**candidate不包含下面3项canonical WIP，必须有意识合并：**

|canonical独有改动|实质|处理/验证|
|---|---|---|
|`iqs_agent_runtime_lab.py`|移除launcher所在根的sys.path条目，再优先src，避免同名文件遮蔽包|保留，与candidate README/CLI文档一起对齐；验证脚本入口和installed `-m`入口|
|`src/iqs_agent_runtime_lab/__main__.py`|说明installed-package入口|随launcher归拢|
|`tools/lock_inputs.py`|usage补`--wave-lock`|保留正确说明，不需要运行会写fixture的lock工具|

candidate独有新文件：
```text
conftest.py
src/iqs_agent_runtime_lab/explicit_source_adapter.py
tests/runtime_test_support.py
```

推荐MC-RT归拢顺序：先CLI独有修复 → opaque API/port/services与Company兼容操作 → 对口tests/明确legacy隔离 → 取消历史pin/计数对当前suite阻挡。最后一次短路径当前功能测试及独审，再自包含提交到实际owner分支。不能把candidate完整拷回canonical，因为会丢上列launcher改动。

## 精确清理候选（本次未执行）

以下目录均位于已明确的候选根内，检查时无reparse/junction、无内嵌.git；一级子目录为pytest测试节点，内容为隔离sqlite、JSON/日志/pyc及搬迁源码副本。没有把来源候选根本身列为可删。总控执行前核根路径仍位于指定候选、没有正在使用该basetemp的进程；无须额外用户授权。状态变化时仅重新检查该目标。

QA父根：`C:/Users/郑曾波/Projects/invest-quick-scan/.tmp-stockqa-current-wt-20261110/`

|精确子目录|物理文件数|
|---|---:|
|`.pytest-temp-modularity-owner-factory`|32|
|`.pytest-temp-modularity-owner-factory-final`|32|
|`.pytest-temp-qpack-cap-green`|4|
|`.pytest-temp-qpack-cap-green2`|4|
|`.pytest-temp-qpack-cap-red`|1|
|`.pytest-temp-route-api-green`|3|
|`.pytest-temp-route-api-red`|1|
|`.pytest-temp-semantic-stockqa-port3`|3|
|`.pytest-temp-semantic-stockqa-port4`|3|
|`.tmp-stockqa-final-suite-20261110`|248|

Runtime父根：`C:/Users/郑曾波/Projects/invest-quick-scan/.tmp-modularity-runtime-20261110/`

|精确子目录|物理文件数|
|---|---:|
|`.pytest-t-ident`|141|
|`.pytest-t-safety`|1991|
|`.pytest-temp-docs-boundaries-20261110`|4|
|`.pytest-temp-runtime-boundary-final`|3|
|`.pytest-temp-runtime-integration-final2`|5|
|`.pytest-temp-runtime-integration-final3`|4|
|`.tmp-independent-harness-review`|4|
|`.tmp-runtime-final-suite-20261110`|2373|
|`.tmp-short-safety`|1999|

另可精确清理：

|目标|证据与注意|
|---|---|
|`C:/Users/郑曾波/Projects/iqs-company-agent-lab/fixtures/locked/synthetic/boards/run-context-compact-2.board.json`|上文已定位可重现测试写入；不删除目录或其它locked fixture|
|`C:/Users/郑曾波/Projects/StockQAbyLLM/pilot_runs/g2b_alphabet_2026-10-04/import-stderr.txt`|0字节普通文件，无内容；只删此文件，其它试验记录保留|
|`C:/Users/郑曾波/AppData/Local/Temp/iqs-acc-1866709051/wt`|旧已验收commit祖先；208条删除状态，0新增/修改，物理仅剩.git，无reparse|
|`C:/Users/郑曾波/AppData/Local/Temp/iqs-acc-1866709051/wt2`|旧commit祖先；215条删除状态，0新增/修改，物理仅剩.git，无reparse|

两个Temp目标是**已注册Git工作树**，应由Runtime owner用精确worktree移除处理目录和登记。不要把208/215个删除状态并入源码，也不要把删空目录误认成丢失的未提交实现。`_g2/StockQAbyLLM`是干净且已合并的历史工作树，不是测试残片；若当前无活动writer且总控要清理，可单独退役，但不影响本轮源码收口。

## 完整未提交路径附录（normal展示，临时目录内文件已聚合）

附录用于后续harness承接，不表示这些路径可以全部提交。`??`源码必须检查依赖；个人/实验/临时分类见上文；所有staged均空。

### StockQAbyLLM

```text
 M scripts/checks.py
 M src/__init__.py
 M src/config/quick_scan_search_policy.py
 M src/core/__init__.py
 M src/core/models.py
 M src/core/qa_engine.py
 M src/interfaces/__init__.py
 M src/providers/external_search_provider.py
 M src/providers/llm_client.py
 M src/providers/llm_provider.py
 M src/providers/llm_research_client.py
 M src/providers/llm_response_parser.py
 M src/runners/llm_runner.py
 M src/services/__init__.py
 M src/utils/__init__.py
 M src/utils/llm_integration.py
 M src/utils/quick_scan_c06_adapter.py
 M src/utils/quick_scan_c06_authority.py
 M src/utils/quick_scan_company_context.py
 M src/utils/quick_scan_company_runtime.py
 M src/utils/quick_scan_delivery_seal.py
 M src/utils/quick_scan_execution_inspect.py
 M src/utils/quick_scan_external_context.py
 M src/utils/quick_scan_external_continuation.py
 M src/utils/quick_scan_external_journal.py
 M src/utils/quick_scan_known_outcome_journal.py
 M src/utils/quick_scan_mcp_journal.py
 M src/utils/quick_scan_observation_context.py
 M src/utils/quick_scan_owner_budget_continuation.py
 M src/utils/quick_scan_owner_budget_continuation_v15.py
 M src/utils/quick_scan_owner_budget_permissions.py
 M src/utils/quick_scan_owner_refresh.py
 M src/utils/quick_scan_owner_refresh_journal.py
 M src/utils/quick_scan_owner_research.py
 M src/utils/quick_scan_prepaid_quota.py
 M src/utils/quick_scan_provided_context.py
 M src/utils/quick_scan_question_pack_journal.py
 M src/utils/quick_scan_refresh_admission.py
 M src/utils/quick_scan_refresh_batch.py
 M src/utils/quick_scan_refresh_consent.py
 M src/utils/quick_scan_refresh_execution.py
 M src/utils/quick_scan_refresh_inspect.py
 M src/utils/quick_scan_research_intent.py
 M src/utils/quick_scan_research_output.py
 M src/utils/quick_scan_research_session.py
 M src/utils/quick_scan_result_outbox.py
 M src/utils/quick_scan_saved_research_publication.py
 M src/utils/quick_scan_shared_company.py
 M src/utils/quick_scan_shared_routes.py
 M src/utils/quick_scan_uncertain_seal.py
 M src/utils/quick_scan_work_decision_authority.py
 M src/utils/quick_scan_work_decision_inspect.py
 M src/utils/quick_scan_work_store.py
 M src/utils/quick_scan_work_transport.py
 M tests/integration/test_owner_research_services.py
 M tests/unit/test_ci_checks.py
 M tests/unit/test_company_scan_public_seams.py
 M tests/unit/test_comparison_target_binding.py
 M tests/unit/test_controlled_generation_payload.py
 M tests/unit/test_external_research_continuation.py
 M tests/unit/test_known_pack_continuation.py
 M tests/unit/test_native_research_session.py
 M tests/unit/test_ordered_refresh_v16.py
 M tests/unit/test_owner_batch_adapters.py
 M tests/unit/test_owner_budget_continuation.py
 M tests/unit/test_owner_subject_readiness.py
 M tests/unit/test_quick_scan_external_context.py
 M tests/unit/test_quick_scan_question_pack_transport.py
 M tests/unit/test_quick_scan_refresh_execution.py
 M tests/unit/test_quick_scan_refresh_inspect.py
 M tests/unit/test_quick_scan_uncertain_seal.py
 M tests/unit/test_quick_scan_vendor_receipt_sqlite.py
 M tests/unit/test_research_controlled_generation.py
 M tests/unit/test_saved_research_publication.py
 M tests/unit/test_shared_company_entry.py
 M tests/unit/test_shared_company_routes.py
 M tests/unit/test_w15_owner_refresh_transport.py
?? .codegraph/
?? .workbuddy-ai/
?? nul
?? pilot_runs/b2a_2026-10-03/
?? pilot_runs/g2b_alphabet_2026-10-04/
?? pilot_runs/l02_2026-10-04/
?? progress_update.txt
?? src/interfaces/quick_scan_lifecycle.py
?? src/interfaces/quick_scan_owner_refresh.py
?? src/interfaces/quick_scan_result_proof.py
?? src/interfaces/sqlite_reader.py
?? src/interfaces/transport_outcome.py
?? src/utils/_quick_scan_owner_refresh_port.py
?? src/utils/quick_scan_company_api.py
?? src/utils/quick_scan_owner_refresh_api.py
?? src/utils/quick_scan_result_proof.py
?? tests/unit/owner_refresh_port_test_support.py
?? tests/unit/test_quick_scan_company_api.py
?? tests/unit/test_quick_scan_module_boundaries.py
?? tests/unit/test_quick_scan_owner_refresh_port.py
```

### iqs-company-agent-lab

```text
?? .codegraph/
?? fixtures/locked/synthetic/boards/run-context-compact-2.board.json
```

### iqs-agent-runtime-lab

```text
 M README.md
 M content/runtime-bridge.json
 M docs/handoff/AGENT-RUN-02/integration-notes.md
 M iqs_agent_runtime_lab.py
 M src/iqs_agent_runtime_lab/__main__.py
 M src/iqs_agent_runtime_lab/frozenlab.py
 M src/iqs_agent_runtime_lab/live_bootstrap.py
 M src/iqs_agent_runtime_lab/port.py
 M src/iqs_agent_runtime_lab/receiptmap.py
 M src/iqs_agent_runtime_lab/replay.py
 M src/iqs_agent_runtime_lab/report.py
 M src/iqs_agent_runtime_lab/services.py
 M src/iqs_agent_runtime_lab/task2.py
 M tests/conftest.py
 M tests/test_bridge_contract.py
 M tests/test_controlled_generation.py
 M tests/test_docs_integrity.py
 M tests/test_multi_strategy_e2e.py
 M tests/test_owner_scope.py
 M tests/test_preflight_before_claim.py
 M tests/test_recovery.py
 M tests/test_safety_portability.py
 M tests/test_search_s1_s2.py
 M tools/lock_inputs.py
?? src/iqs_agent_runtime_lab/_api_runtime.py
?? src/iqs_agent_runtime_lab/api.py
?? src/iqs_agent_runtime_lab/company_agent_api.py
?? src/iqs_agent_runtime_lab/frozen_adapter.py
?? src/iqs_agent_runtime_lab/frozen_company_adapter.py
?? tests/test_company_agent_api_compat.py
?? tests/test_module_boundaries.py
?? tests/test_public_api.py
?? tests/test_public_task_contract.py
```

### .tmp-stockqa-current-wt-20261110

```text
 M docs/architecture.md
 M scripts/checks.py
 M src/__init__.py
 M src/config/quick_scan_search_policy.py
 M src/core/__init__.py
 M src/core/models.py
 M src/core/qa_engine.py
 M src/interfaces/__init__.py
 M src/providers/external_search_provider.py
 M src/providers/llm_client.py
 M src/providers/llm_provider.py
 M src/providers/llm_research_client.py
 M src/providers/llm_response_parser.py
 M src/runners/llm_runner.py
 M src/services/__init__.py
 M src/utils/__init__.py
 M src/utils/llm_integration.py
 M src/utils/quick_scan_c06_adapter.py
 M src/utils/quick_scan_c06_authority.py
 M src/utils/quick_scan_company_context.py
 M src/utils/quick_scan_company_runtime.py
 M src/utils/quick_scan_delivery_seal.py
 M src/utils/quick_scan_execution_inspect.py
 M src/utils/quick_scan_external_context.py
 M src/utils/quick_scan_external_continuation.py
 M src/utils/quick_scan_external_journal.py
 M src/utils/quick_scan_known_outcome_journal.py
 M src/utils/quick_scan_mcp_journal.py
 M src/utils/quick_scan_observation_context.py
 M src/utils/quick_scan_owner_budget_continuation.py
 M src/utils/quick_scan_owner_budget_continuation_v15.py
 M src/utils/quick_scan_owner_budget_permissions.py
 M src/utils/quick_scan_owner_refresh.py
 M src/utils/quick_scan_owner_refresh_journal.py
 M src/utils/quick_scan_owner_research.py
 M src/utils/quick_scan_prepaid_quota.py
 M src/utils/quick_scan_provided_context.py
 M src/utils/quick_scan_question_pack_journal.py
 M src/utils/quick_scan_refresh_admission.py
 M src/utils/quick_scan_refresh_admission_journal.py
 M src/utils/quick_scan_refresh_batch.py
 M src/utils/quick_scan_refresh_consent.py
 M src/utils/quick_scan_refresh_execution.py
 M src/utils/quick_scan_refresh_inspect.py
 M src/utils/quick_scan_research_intent.py
 M src/utils/quick_scan_research_output.py
 M src/utils/quick_scan_research_session.py
 M src/utils/quick_scan_result_outbox.py
 M src/utils/quick_scan_saved_research_publication.py
 M src/utils/quick_scan_shared_company.py
 M src/utils/quick_scan_shared_routes.py
 M src/utils/quick_scan_subject_journal.py
 M src/utils/quick_scan_uncertain_seal.py
 M src/utils/quick_scan_work_decision_authority.py
 M src/utils/quick_scan_work_decision_inspect.py
 M src/utils/quick_scan_work_store.py
 M src/utils/quick_scan_work_transport.py
 M tests/integration/test_owner_research_services.py
 M tests/unit/test_ci_checks.py
 M tests/unit/test_company_scan_public_seams.py
 M tests/unit/test_comparison_target_binding.py
 M tests/unit/test_controlled_generation_payload.py
 M tests/unit/test_external_research_continuation.py
 M tests/unit/test_known_pack_continuation.py
 M tests/unit/test_native_research_session.py
 M tests/unit/test_ordered_refresh_v16.py
 M tests/unit/test_owner_batch_adapters.py
 M tests/unit/test_owner_budget_continuation.py
 M tests/unit/test_owner_subject_readiness.py
 M tests/unit/test_paid_visible_journal.py
 M tests/unit/test_provided_answer_sources.py
 M tests/unit/test_q09_budget_concurrency.py
 M tests/unit/test_quick_scan_external_context.py
 M tests/unit/test_quick_scan_question_pack_store.py
 M tests/unit/test_quick_scan_question_pack_transport.py
 M tests/unit/test_quick_scan_refresh_execution.py
 M tests/unit/test_quick_scan_refresh_inspect.py
 M tests/unit/test_quick_scan_uncertain_seal.py
 M tests/unit/test_quick_scan_vendor_receipt_sqlite.py
 M tests/unit/test_quick_scan_work_store.py
 M tests/unit/test_research_controlled_generation.py
 M tests/unit/test_research_visible_output.py
 M tests/unit/test_saved_research_publication.py
 M tests/unit/test_shared_company_entry.py
 M tests/unit/test_shared_company_routes.py
 M tests/unit/test_terminal_received_recovery.py
 M tests/unit/test_w15_owner_refresh_transport.py
?? .pytest-temp-modularity-owner-factory-final/
?? .pytest-temp-modularity-owner-factory/
?? .pytest-temp-qpack-cap-green/
?? .pytest-temp-qpack-cap-green2/
?? .pytest-temp-qpack-cap-red/
?? .pytest-temp-route-api-green/
?? .pytest-temp-route-api-red/
?? .pytest-temp-semantic-stockqa-port3/
?? .pytest-temp-semantic-stockqa-port4/
?? .tmp-stockqa-final-suite-20261110/
?? src/interfaces/quick_scan_company.py
?? src/interfaces/quick_scan_lifecycle.py
?? src/interfaces/quick_scan_owner_refresh.py
?? src/interfaces/quick_scan_result_proof.py
?? src/interfaces/sqlite_reader.py
?? src/interfaces/transport_outcome.py
?? src/utils/_quick_scan_company_task_factory.py
?? src/utils/_quick_scan_owner_refresh_port.py
?? src/utils/quick_scan_company_api.py
?? src/utils/quick_scan_owner_refresh_api.py
?? src/utils/quick_scan_result_proof.py
?? tests/unit/owner_refresh_port_test_support.py
?? tests/unit/test_quick_scan_company_api.py
?? tests/unit/test_quick_scan_company_contract.py
?? tests/unit/test_quick_scan_company_task_factory.py
?? tests/unit/test_quick_scan_module_boundaries.py
?? tests/unit/test_quick_scan_owner_refresh_port.py
```

### .tmp-modularity-runtime-20261110

```text
 M README.md
 M content/runtime-bridge.json
 M docs/handoff/AGENT-RUN-02/acceptance-response.md
 M docs/handoff/AGENT-RUN-02/acceptance-traceability.md
 M docs/handoff/AGENT-RUN-02/artifacts.json
 M docs/handoff/AGENT-RUN-02/delivery-freeze.json
 M docs/handoff/AGENT-RUN-02/handoff.json
 M docs/handoff/AGENT-RUN-02/integration-notes.md
 M docs/handoff/AGENT-RUN-02/report.md
 M docs/handoff/AGENT-RUN-02/tests.json
 M integration_tests/test_current_sources.py
 M schemas/runtime-bridge.schema.json
 M src/iqs_agent_runtime_lab/__init__.py
 M src/iqs_agent_runtime_lab/bridge.py
 M src/iqs_agent_runtime_lab/frozenlab.py
 M src/iqs_agent_runtime_lab/live_bootstrap.py
 M src/iqs_agent_runtime_lab/port.py
 M src/iqs_agent_runtime_lab/receiptmap.py
 M src/iqs_agent_runtime_lab/replay.py
 M src/iqs_agent_runtime_lab/report.py
 M src/iqs_agent_runtime_lab/services.py
 M src/iqs_agent_runtime_lab/task2.py
 M tests/conftest.py
 M tests/test_bridge_contract.py
 M tests/test_context_binding.py
 M tests/test_controlled_generation.py
 M tests/test_docs_integrity.py
 M tests/test_failures.py
 M tests/test_handoff_pins.py
 M tests/test_identity_versions.py
 M tests/test_multi_strategy_e2e.py
 M tests/test_owner_native_observers.py
 M tests/test_owner_scope.py
 M tests/test_preflight_before_claim.py
 M tests/test_real_sdk_path.py
 M tests/test_recovery.py
 M tests/test_safety_portability.py
 M tests/test_search_s1_s2.py
 M tests/test_tool_edge_cases.py
 M tests/test_tool_roundtrip.py
 M tools/_impl_commit.py
 M tools/assert_pin_ready.py
 M tools/build_delivery.py
 M tools/build_handoff.py
 M tools/point_pins.py
 M tools/run_acceptance_checks.py
 M tools/sync_metadata_latest.py
 M tools/verify_document_claims.py
 M tools/verify_fresh_checkout.py
?? .pytest-t-ident/
?? .pytest-t-safety/
?? .pytest-temp-docs-boundaries-20261110/
?? .pytest-temp-runtime-boundary-final/
?? .pytest-temp-runtime-integration-final2/
?? .pytest-temp-runtime-integration-final3/
?? .tmp-independent-harness-review/
?? .tmp-runtime-final-suite-20261110/
?? .tmp-short-safety/
?? conftest.py
?? src/iqs_agent_runtime_lab/_api_runtime.py
?? src/iqs_agent_runtime_lab/api.py
?? src/iqs_agent_runtime_lab/company_agent_api.py
?? src/iqs_agent_runtime_lab/explicit_source_adapter.py
?? src/iqs_agent_runtime_lab/frozen_adapter.py
?? src/iqs_agent_runtime_lab/frozen_company_adapter.py
?? tests/runtime_test_support.py
?? tests/test_company_agent_api_compat.py
?? tests/test_module_boundaries.py
?? tests/test_public_api.py
?? tests/test_public_task_contract.py
```

## 盘点局限

未检查个人记忆、密钥配置内容，未读取正式响应库。未fetch远端、未运行源码测试、未证明每份WIP正确。最初一次输出因临时目录逐文件列表过大被工具截断；随后改用Git normal聚合+完整计数重新读取，本文数字取后者。未遇Git worktree报错；两个候选的独立.git已核实。垃圾判断只适用于本文列出的具体目标，不能推广为对所有.tmp/pilot_runs的通配删除。

## 同日补查：旧隔离源码副本与清理后的状态说明

本节取代“仍待清理”的理解，不改写上文原始盘点快照。总控已明确反馈：本报告列出的19个内部pytest目录、CA生成board和QA空stderr已精确清理；两个带独立.git的有效候选根完整保留。更广的71个pytest目录清理属于总控记录，本agent未执行或独立核算其体积。Runtime两个Temp注册worktree仍保留登记：**物理文件仅剩`.git`，还有多级空目录壳**，不是整个根目录只有一个条目；不要把208/215条D提交。

### `.worktrees/stockqa-delivery-port-20261109`

- 绝对位置：`C:/Users/郑曾波/Projects/invest-quick-scan/.worktrees/stockqa-delivery-port-20261109`。
- **没有`.git`文件或目录，不是Git工作树。** 在其中执行`git rev-parse --show-toplevel`返回上级IQS根；看到的IQS master/HEAD不属于此StockQA副本，不能用来证明它已合并。
- 物理545个文件（IQS非忽略路径清单约488个），无reparse；另含pilot日志、名单、配置模板和缓存。仅对src/tests/scripts/docs的409份文件作CRLF归一字节比较；没有读取根配置/名单或历史日志。
- 比较结果：315份同时等于QA canonical、1.8候选和canonical HEAD；10份等于canonical/HEAD；63份等于HEAD；21份与这三个当前版本不同。
- 对21份继续查Git历史blob：20份完整内容均存在于master祖先历史，最近相关变动涉及`005f7eb`（typed facts升级），不是遗落的新实现。剩余`tests/unit/test_quick_scan_dashboard_owner_ports.py`只是6个fault参数由多行改一行，AST完全相同。
- **结论：本轮检查的409份源码/测试/文档没有独有未归拢逻辑；不能从此推出剩余根文件/运行资料都可删。** MC-QA无需把此副本作为另一个候选实现合入；可作为历史参考，根目录本轮保留。

### 额外四份旧快照：源码/测试差异摘要

四者均无自己的`.git`，不是可merge的分支。只比较各自src/tests，忽略pyc；不检查其它历史资料，也不执行测试。canonical指原owner当前工作树，candidate指本报告的1.8 QA或1.4 Runtime完整候选。

|IQS下相对目录|比较文件数|与canonical及candidate同时相同|仅与canonical相同|与二者都不同|独有文件路径|
|---|---:|---:|---:|---:|---:|
|`.tmp-runtime-modularity-20261110`|48|14|34|0|0|
|`.tmp-stockqa-modularity-20261110`|338|275|38|25|0|
|`.tmp-stockqa-modularity-20261110-v2`|338|275|38|25|0|
|`.tmp-stockqa-modularity-20261110-v3`|343|290|53|0|0|

RT旧快照和QA-v3的src/tests全部已体现在canonical当前内容中，未发现新源码；本轮按总控要求仍保留目录，不将其它内容推定为垃圾。

QA初版和v2具有相同的25条不同内容路径；两版彼此仅`tests/unit/test_quick_scan_module_boundaries.py`、`tests/unit/test_shared_company_entry.py`不同。**无独有文件路径不等于所有旧测试行为都已被新实现覆盖**，故这些25条进入MC-QA候选归拢参考；本次不逐行审定语义替代，也不把旧版本覆盖到canonical。

```text
src/core/qa_engine.py
src/runners/llm_runner.py
src/utils/quick_scan_company_context.py
src/utils/quick_scan_company_runtime.py
src/utils/quick_scan_owner_budget_continuation.py
src/utils/quick_scan_owner_research.py
src/utils/quick_scan_research_session.py
src/utils/quick_scan_shared_company.py
src/utils/quick_scan_shared_routes.py
src/utils/quick_scan_work_store.py
src/utils/quick_scan_work_transport.py
tests/unit/test_company_scan_public_seams.py
tests/unit/test_comparison_target_binding.py
tests/unit/test_controlled_generation_payload.py
tests/unit/test_ordered_refresh_v16.py
tests/unit/test_owner_batch_adapters.py
tests/unit/test_owner_budget_continuation.py
tests/unit/test_quick_scan_module_boundaries.py
tests/unit/test_quick_scan_question_pack_transport.py
tests/unit/test_quick_scan_refresh_execution.py
tests/unit/test_quick_scan_uncertain_seal.py
tests/unit/test_research_controlled_generation.py
tests/unit/test_shared_company_entry.py
tests/unit/test_shared_company_routes.py
tests/unit/test_w15_owner_refresh_transport.py
```

v3相对v2另外加入已在canonical存在的5个owner封装文件：`src/interfaces/quick_scan_owner_refresh.py`、`src/utils/_quick_scan_owner_refresh_port.py`、`src/utils/quick_scan_owner_refresh_api.py`、`tests/unit/owner_refresh_port_test_support.py`、`tests/unit/test_quick_scan_owner_refresh_port.py`。这是早期快照向现有owner封装推进的证据，不是需要再次引入一套实现。

MC输入补充：MC-QA主输入仍为canonical+1.8完整候选，初版/v2的25路径只用于确认有效行为是否被吸收；v3和delivery-port作为已重合/历史参考。MC-RT主输入仍为canonical+完整Runtime候选，旧`.tmp-runtime-modularity-20261110`已与canonical源码测试重合。无需新施工包、审批或全仓hash门。
