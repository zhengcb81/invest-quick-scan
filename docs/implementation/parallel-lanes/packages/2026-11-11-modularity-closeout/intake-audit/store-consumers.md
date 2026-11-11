# StockWiki / Theme / Industry intake audit

Read-only snapshot: 2026-11-11T20:00:26.872877+00:00

No tests, merges, deletes, source edits, database content reads or paid calls. GIT_OPTIONAL_LOCKS=0. Branch ancestry and stable patch equivalence are separately checked; patch uniqueness does not prove a feature is absent after squash/manual port.

## 处置结论（供总控与 MC 卡接续）

### 可以直接清理的精确派生产物

仅以下三个未跟踪 Python 字节码缓存可认定为可再生临时文件；对应 `.py` 源码均存在。总控删除前复核这些精确文件仍未跟踪、父目录仍在 Theme 根内。不要递归删除整个测试目录。

- `C:/Users/郑曾波/Projects/analyze-theme-value-chain/scripts/__pycache__/quick_scan_client.cpython-313.pyc`
- `C:/Users/郑曾波/Projects/analyze-theme-value-chain/tests/__pycache__/test_quick_scan_integration.cpython-313-pytest-9.1.1.pyc`
- `C:/Users/郑曾波/Projects/analyze-theme-value-chain/tests/fixtures/quick_scan/__pycache__/quick_scan_fixtures.cpython-313.pyc`

本审计没有执行删除。以下情况不能仅凭 untracked 当垃圾处理：SQLite、原运行日志、CodeGraph 配置、harness 会话锁、审查提案/测试源码、整个注册 worktree。

### 所有未提交项分类

|位置|分类与原因|处置|
|---|---|---|
|StockWiki canonical 的4个 `data/.../*.sqlite`|Dashboard/source-link/onboarding/binding 运行状态；文件大小16–28 KiB，时间2026-11-01/07。没有读库内容，无法认定无用|保留，不提交Git、不删除；由数据owner决定忽略规则/备份，不并入源码提交|
|StockWiki `logs/stock_qa_20261110.log`|2026-11-10运行日志，1278 bytes；未读取内容，不能证明非验收证据或无敏感数据|保留，不随源码提交；本次不自动删除|
|StockWiki `runs/c16b/native-owner-alphabet-01/owner-workspace/...`两库|2026-10-18原实验owner库，24/184 KiB；不是可凭名称重造的编译缓存|保留在原实验位置，不提交Git、不删|
|Theme 两份 tracked 修改与新 `tests/fixtures/quick_scan/quick_scan_client_test_harness.py`|一组完整未提交实现：移除生产任意CLI module选择；测试改用隔离adapter；补边界检测。新harness被测试入口直接依赖|MC-TH接入完整三文件候选并运行相关测试；不能只提交tracked diff，也不能当临时harness删掉|
|Theme `.codegraph/.gitignore`、`.codegraph/config.json`|本地索引配置，不是业务实现；未读取config内容|保留本地，排除业务提交；可由owner精确ignore，不因untracked删索引|
|Theme 3个 `.pyc`|可再生缓存|只清理上列精确路径|
|Industry `tests/test_quick_scan_module_boundaries.py`|完整架构回归源码（AST扫描、反例），不是运行输出；此前“tracked clean”没有涵盖它|MC-IN审查/运行后提交或随能力域规则调整，必须保留；不再声称无WIP|
|SW b33 worktree `.test-runs/swrbase/` 的62个文件|名称与backup/restore单测一致的临时库和sentinel。含junction/reparse测试路径，故不可直接递归删|可列为清理候选，但先验证reparse目标与实际writer；不替总控授权外路径删除|
|SW b34 worktree `.test-runs/b34-sidr001-root-green.xml`|单测报告；同分支已提交 `docs/handoffs/B34-ID-NORMALIZATION/raw/sidr001-root-green.xml`|先比字节确认是重复报告才能删；未比，不列立即删除|
|SW b34 worktree `.mimosa/`4文件|harness会话/锁/状态记录，是否活动未知|保留，不动他人锁|
|SW return5 worktree `.d00-audit/`14文件|设计提案、模型、schema、测试和race probe结果；具有未提交研究/实现价值|D00确认纳入交接或归档；不得按隐藏目录当垃圾|
|两个旧 Temp SW worktree 2019/1991个 tracked deletions|几乎整个旧checkout的文件已缺，只有目录/缓存残留；它们的HEAD都已是master祖先|不是待合并“删除全部wiki”补丁。保留Git分支，若总控确认无活动writer及独有ignored输出，可用正常worktree清理；不要提交这些删除|
|其余已注册worktree|本次status无未提交项，详见完整表|clean不代表分支已合并；按下文祖先/patch归并关系处理|

### 分支收敛与具体并线顺序

StockWiki 共36个本地分支，其中18个不是master祖先；不能把这18个都依次合并。去掉祖先链后有5个最大tip，再按patch与最终源文件比较收敛为：

1. **主要实质待并线候选：`codex/dashboard-c38-sw-release@4532b0d`。** 包含早期公开research/identity/onboarding/proof/binding/source-link，以及名单request/analysis-subject接口。相对共同基线变更136个路径，其中129个在当前master缺失，另7个最终内容不同；需要owner集成，不能宣称已经在主线。
2. **C1不重复合：** `codex/dashboard-owner-sw-c1-authority@60a85ef` 的 `7be0c97`、`60a85ef` 在C38分别已有 `cc3e1a4`、`9349ced`。`git cherry C38 C1` 两项均为 `-`。C38还多 `4532b0d` 的历史快照pin和全部lookup selector绑定修复。C1保留历史引用即可，不能按commit ID不同重复移植。
3. **两条B03线不机械合：** `codex/d00-b03-stockwiki@652f6a4` 与 `codex/dashboard-owner-sw-b03-assessments@586b2f7` 的3个公司评估源码/测试最终blob完全相同，且对应12个B03 patch跨这两线等价。master已有独立移植 `c8d45a8`，后续 `27acd5d/6616613/bf3cf3d` 继续修复，公开CLI已只读，写入口拆到operator CLI；直接合旧B03会重新带回公开写命令和旧私有import。MC-SW以master当前投影为准，补release/authority/idempotency行为对照，确认旧功能已覆盖；不因缺祖先关系倒退实现。
4. **B34只剩独有证据文档：** `codex/dashboard-sw-b34-id-repair@07fbb8a` 相对C38仅多 `07fbb8a`，涉及handoff、SIDR001 manifest、XML三文件，无源码。总控/D00可在C38整合后按需cherry-pick该文档提交；不把文档是否并入设为产品运行门。
5. 已是master祖先的F05、identity、W04、G2、source-reader、permission-residue等无需再合。完整逐分支表与unique提交清单在下方，重复tip别名也已列出。

**具体和IQS配对的缺口：** StockWiki master没有 `dashboard_membership_request_cli.py`、`stockwiki/quick_scan_membership_read.py`、`stockwiki/quick_scan_membership_request.py`。C38的公开协议为 `stockwiki.membership_request/1.0.0`，命令 `apply/lookup/history --root <workspace>`，JSON走stdin。此owner实现对应IQS候选 `418bb94/8f6a5ee` 的名单request authority/read/history消费面；两端须固定版本组合验收。

建议写回MC-SW/MC-IQS的intake步骤：先在独立集成树承接master `12c441e`，从C38挑出已完成的名单request/read/history及其事务/DDL/backup/universe依赖，保留master已交付的F05和公开模块边界。若选择全C38合并，应另列research/onboarding等范围并由D00/StockWiki owner审查，不可在本轮“清垃圾”顺手把全分支推进生产。本次只规划，不运行生产迁移。

名单合流针对性验证：`tests/test_quick_scan_membership_request.py`、`tests/test_quick_scan_universe.py`、`tests/test_quick_scan_store.py`、`tests/test_quick_scan_routes.py`、`tests/test_quick_scan_backup.py`与现有能力域边界检查；公开CLI覆盖同键同payload重放、同键改payload冲突、错universe/request/key、历史pin、提交后断线再lookup、并发变更不改分页快照。使用新临时库及已有旧schema夹具，不写真实库。

若合整个C38，再按受影响入口运行 `tests/test_dashboard_identity_bridge.py`、`tests/test_dashboard_issuer_proof.py`、`tests/test_dashboard_onboarding.py`、`tests/test_dashboard_research_binding.py`、`tests/test_dashboard_research_source_link.py`、`tests/test_public_research_*.py`、`tests/b34_id_normalization/test_normalization.py`、`tests/b37_subject/test_public_subject.py`，并保留master `tests/test_public_company_assessments.py` 的新只读CLI行为。上述部分文件目前只存在候选，不能在master缺文件时称测试通过。

Theme没有其它本地分支或worktree，无待合并commit；先收拢三文件WIP，依MC-TH运行 `python -B -m pytest -q tests/test_quick_scan_integration.py -p no:cacheprovider` 后形成自包含提交。该仓无remote，不新建remote。

Industry两条report-generation分支都已是main祖先，两个旧worktree干净，无新功能待合。main与本地 `origin/main` 都是 `7d49ca3`（未访问远端，不能称实时远端核对）；只剩上述未跟踪边界测试待MC-IN审查提交。相关五个快扫测试按MC-IN短组运行即可。

company-wiki不是本轮快扫并线owner；本次不扩大到其平台分支/数据库审计。先前边界检查已确认其SourceRef/export职责，MC包不写它的实现。

### 状态局限和清理规则

这是2026-11-11的只读快照，各仓有其他writer，操作前只复核受影响路径和HEAD即可；不需要重做整套审计或再询权限。没有读取任何SQLite/日志/CodeGraph config内容。没有运行测试，因此不把候选自报通过当新验收。Worktree的ignored文件不在porcelain清单内，清理整个worktree前必须单独核实；本报告只为三个明确`.pyc`提供立即可删证据。

初次大表输出过大，已改成一次ls-tree与内存blob对比；以下祖先/patch表是最终有效盘点。所有status前导空格按原porcelain含义保留，不把` M`误报为暂存`M `。

## StockWiki

- canonical: `C:\Users\郑曾波\Projects\StockWiki`
- main `master` at `12c441e86282135b49120112dcf21c17509bbdd0`
- remotes: `none`; upstream: `ERROR fatal: no upstream configured for branch 'master'`

### Canonical uncommitted paths

```text
?? data/companies/688012.SH/research_source_links.sqlite
?? data/dashboard_onboarding/evidence.sqlite
?? data/dashboard_onboarding/requests.sqlite
?? data/dashboard_research_binding/requests.sqlite
?? logs/stock_qa_20261110.log
?? runs/c16b/native-owner-alphabet-01/owner-workspace/data/quick_scan/analysis_subjects.sqlite
?? runs/c16b/native-owner-alphabet-01/owner-workspace/data/quick_scan/scan.sqlite
```

### All local branches

| Branch | tip | commits outside main | cherry unique / equivalent | final changed-path state: same / different / absent on main |
|---|---|---:|---:|---:|
| `codex/d00-all31-universe-stockwiki` | `194abedfca` | 41 | 39 / 0 | 0 / 1 / 53 |
| `codex/d00-b03-stockwiki` | `652f6a4899` | 12 | 12 / 0 | 0 / 3 / 0 |
| `codex/d00-return5-sw-audit` | `5dbcede6be` | 29 | 29 / 0 | 0 / 0 / 18 |
| `codex/d4-01-company-source-virtualization` | `23d84586dc` | 0 (ancestor) | n/a | n/a |
| `codex/d5-sw-processed-reader` | `6d1e40bcdc` | 0 (ancestor) | n/a | n/a |
| `codex/dashboard-b33-sw-binding` | `e22f15a6df` | 56 | 53 / 0 | 0 / 3 / 93 |
| `codex/dashboard-b33-sw-proof` | `aa0a69f09f` | 48 | 45 / 0 | 0 / 1 / 64 |
| `codex/dashboard-c38-sw-release` | `4532b0da00` | 66 | 63 / 0 | 0 / 7 / 129 |
| `codex/dashboard-owner-sw-b03-assessments` | `586b2f7e73` | 68 | 65 / 0 | 0 / 6 / 93 |
| `codex/dashboard-owner-sw-c1-authority` | `60a85efd53` | 58 | 55 / 0 | 0 / 7 / 97 |
| `codex/dashboard-stockwiki-b-integration` | `194abedfca` | 41 | 39 / 0 | 0 / 1 / 53 |
| `codex/dashboard-stockwiki-identity-bridge` | `9c47effec0` | 3 | 3 / 0 | 0 / 0 / 5 |
| `codex/dashboard-stockwiki-onboarding` | `042951b3f8` | 25 | 25 / 0 | 0 / 0 / 10 |
| `codex/dashboard-stockwiki-proof-read` | `eca69e1c46` | 30 | 30 / 0 | 0 / 0 / 18 |
| `codex/dashboard-stockwiki-public-research` | `f6c402cd96` | 4 | 4 / 0 | 0 / 1 / 22 |
| `codex/dashboard-stockwiki-research-scope` | `a4eb1a3982` | 9 | 9 / 0 | 0 / 1 / 33 |
| `codex/dashboard-sw-b31-release` | `aa0a69f09f` | 48 | 45 / 0 | 0 / 1 / 64 |
| `codex/dashboard-sw-b33-release` | `e22f15a6df` | 56 | 53 / 0 | 0 / 3 / 93 |
| `codex/dashboard-sw-b34-id-repair` | `07fbb8a116` | 61 | 58 / 0 | 0 / 3 / 110 |
| `codex/dashboard-sw-b37-subject` | `c73dd8b0e9` | 63 | 60 / 0 | 0 / 3 / 125 |
| `codex/f05-fact-ingest-20261109` | `93b25927f5` | 0 (ancestor) | n/a | n/a |
| `codex/f05-owner-runtime-01` | `3799b439cf` | 0 (ancestor) | n/a | n/a |
| `codex/g2-sw-daily` | `0b48919065` | 0 (ancestor) | n/a | n/a |
| `codex/identity-snapshot-w02-w03` | `ae11135cc1` | 0 (ancestor) | n/a | n/a |
| `codex/main-permission-residue-20261009` | `d98acdcdf1` | 0 (ancestor) | n/a | n/a |
| `codex/r3-null-retrieval` | `1ebe012adc` | 0 (ancestor) | n/a | n/a |
| `codex/r3a-current-material-read` | `42fba06878` | 0 (ancestor) | n/a | n/a |
| `codex/source-export-v2-reader` | `0b406832b7` | 0 (ancestor) | n/a | n/a |
| `codex/stockwiki-asof-20261007` | `9f552a6741` | 0 (ancestor) | n/a | n/a |
| `codex/stockwiki-g2b-owner-context` | `6f0c2c4abe` | 0 (ancestor) | n/a | n/a |
| `codex/stockwiki-lane-integration` | `52add7fd87` | 0 (ancestor) | n/a | n/a |
| `codex/stockwiki-narrative-consumer-20261003` | `4c3334ed41` | 0 (ancestor) | n/a | n/a |
| `codex/stockwiki-sw-ident` | `0c8603e43f` | 0 (ancestor) | n/a | n/a |
| `codex/stockwiki-w04-mic-relations` | `afa969226d` | 0 (ancestor) | n/a | n/a |
| `codex/sw-company-projection-01` | `27acd5d6ee` | 0 (ancestor) | n/a | n/a |
| `master` | `12c441e862` | 0 (ancestor) | n/a | n/a |

### Maximal outstanding tips (ancestor branches need no separate merge)

- `codex/d00-b03-stockwiki` → `652f6a48992b260cfb9fe25d6496341dc6ecba5a`
- `codex/dashboard-c38-sw-release` → `4532b0da00a38eb74d5464466a166dc38b890222`
- `codex/dashboard-owner-sw-b03-assessments` → `586b2f7e73688aef2c16e6881591953637a1cf32`
- `codex/dashboard-owner-sw-c1-authority` → `60a85efd536349ee7efb89744a3f4a79bbbcec4b`
- `codex/dashboard-sw-b34-id-repair` → `07fbb8a1169cca8dc17884002e78790219d906ca`

### Changed implementation paths still different or absent on main

#### codex/d00-b03-stockwiki

- `dashboard_company_assessment_cli.py`
- `stockwiki/public_company_assessments.py`
- `tests/test_public_company_assessments.py`

#### codex/dashboard-c38-sw-release

- `stockwiki/cli_registry.py`
- `stockwiki/identity_receipts.py`
- `stockwiki/quick_scan_backup_manifest.py`
- `stockwiki/quick_scan_schema.py`
- `stockwiki/quick_scan_store.py`
- `stockwiki/quick_scan_universe.py`
- `tests/test_quick_scan_routes.py`
- `dashboard_analysis_subject_cli.py`
- `dashboard_identity_bridge_cli.py`
- `dashboard_issuer_proof_cli.py`
- `dashboard_membership_request_cli.py`
- `dashboard_onboarding_cli.py`
- `dashboard_profile_sources_cli.py`
- `dashboard_research_binding_cli.py`
- `dashboard_research_source_link_cli.py`
- `dashboard_security_id_repair_cli.py`
- `docs/handoffs/dashboard-B31-owner-release/controlled_owner_fixture.py`
- `stockwiki/_public_research_view_content.py`
- `stockwiki/_public_research_view_project.py`
- `stockwiki/_public_research_view_refs.py`
- `stockwiki/_public_research_view_source.py`
- `stockwiki/_public_research_view_state.py`
- `stockwiki/_public_research_view_wire.py`
- `stockwiki/admin_security_id_normalization.py`
- `stockwiki/cli_parsers/public_research_view.py`
- `stockwiki/dashboard_identity_bridge.py`
- `stockwiki/dashboard_issuer_proof.py`
- `stockwiki/dashboard_onboarding.py`
- `stockwiki/dashboard_onboarding_contract.py`
- `stockwiki/dashboard_onboarding_owner.py`
- `stockwiki/dashboard_profile_sources.py`
- `stockwiki/dashboard_research_binding.py`
- `stockwiki/dashboard_research_binding_contract.py`
- `stockwiki/dashboard_research_binding_flow.py`
- `stockwiki/dashboard_research_binding_owner.py`
- `stockwiki/dashboard_research_binding_proof.py`
- `stockwiki/dashboard_research_source_client.py`
- `stockwiki/dashboard_research_source_link.py`
- `stockwiki/dashboard_research_source_projection.py`
- `stockwiki/public_analysis_subject.py`
- `stockwiki/public_research_view.py`
- `stockwiki/public_research_view_cli.py`
- `stockwiki/quick_scan_membership_read.py`
- `stockwiki/quick_scan_membership_request.py`
- `stockwiki/research_profile_keys.py`
- `tests/b34_id_normalization/test_normalization.py`
- `tests/b37_subject/test_public_subject.py`
- `tests/test_dashboard_identity_bridge.py`
- `tests/test_dashboard_issuer_proof.py`
- `tests/test_dashboard_onboarding.py`
- `tests/test_dashboard_research_binding.py`
- `tests/test_dashboard_research_source_link.py`
- `tests/test_public_research_canonical_scope.py`
- `tests/test_public_research_citation_window.py`
- `tests/test_public_research_excerpt_display.py`
- `tests/test_public_research_view.py`
- `tests/test_public_research_view_blockers.py`
- `tests/test_public_research_view_semantics.py`
- `tests/test_quick_scan_membership_request.py`

#### codex/dashboard-owner-sw-b03-assessments

- `dashboard_company_assessment_cli.py`
- `stockwiki/cli_registry.py`
- `stockwiki/identity_receipts.py`
- `stockwiki/public_company_assessments.py`
- `stockwiki/quick_scan_store.py`
- `tests/test_public_company_assessments.py`
- `dashboard_identity_bridge_cli.py`
- `dashboard_issuer_proof_cli.py`
- `dashboard_onboarding_cli.py`
- `dashboard_profile_sources_cli.py`
- `dashboard_research_binding_cli.py`
- `dashboard_research_source_link_cli.py`
- `docs/handoffs/dashboard-B31-owner-release/controlled_owner_fixture.py`
- `stockwiki/_public_research_view_content.py`
- `stockwiki/_public_research_view_project.py`
- `stockwiki/_public_research_view_refs.py`
- `stockwiki/_public_research_view_source.py`
- `stockwiki/_public_research_view_state.py`
- `stockwiki/_public_research_view_wire.py`
- `stockwiki/cli_parsers/public_research_view.py`
- `stockwiki/dashboard_identity_bridge.py`
- `stockwiki/dashboard_issuer_proof.py`
- `stockwiki/dashboard_onboarding.py`
- `stockwiki/dashboard_onboarding_contract.py`
- `stockwiki/dashboard_onboarding_owner.py`
- `stockwiki/dashboard_profile_sources.py`
- `stockwiki/dashboard_research_binding.py`
- `stockwiki/dashboard_research_binding_contract.py`
- `stockwiki/dashboard_research_binding_flow.py`
- `stockwiki/dashboard_research_binding_owner.py`
- `stockwiki/dashboard_research_binding_proof.py`
- `stockwiki/dashboard_research_source_client.py`
- `stockwiki/dashboard_research_source_link.py`
- `stockwiki/dashboard_research_source_projection.py`
- `stockwiki/public_research_view.py`
- `stockwiki/public_research_view_cli.py`
- `stockwiki/research_profile_keys.py`
- `tests/test_dashboard_identity_bridge.py`
- `tests/test_dashboard_issuer_proof.py`
- `tests/test_dashboard_onboarding.py`
- `tests/test_dashboard_research_binding.py`
- `tests/test_dashboard_research_source_link.py`
- `tests/test_public_research_canonical_scope.py`
- `tests/test_public_research_citation_window.py`
- `tests/test_public_research_excerpt_display.py`
- `tests/test_public_research_view.py`
- `tests/test_public_research_view_blockers.py`
- `tests/test_public_research_view_semantics.py`

#### codex/dashboard-owner-sw-c1-authority

- `stockwiki/cli_registry.py`
- `stockwiki/identity_receipts.py`
- `stockwiki/quick_scan_backup_manifest.py`
- `stockwiki/quick_scan_schema.py`
- `stockwiki/quick_scan_store.py`
- `stockwiki/quick_scan_universe.py`
- `tests/test_quick_scan_routes.py`
- `dashboard_identity_bridge_cli.py`
- `dashboard_issuer_proof_cli.py`
- `dashboard_membership_request_cli.py`
- `dashboard_onboarding_cli.py`
- `dashboard_profile_sources_cli.py`
- `dashboard_research_binding_cli.py`
- `dashboard_research_source_link_cli.py`
- `docs/handoffs/dashboard-B31-owner-release/controlled_owner_fixture.py`
- `stockwiki/_public_research_view_content.py`
- `stockwiki/_public_research_view_project.py`
- `stockwiki/_public_research_view_refs.py`
- `stockwiki/_public_research_view_source.py`
- `stockwiki/_public_research_view_state.py`
- `stockwiki/_public_research_view_wire.py`
- `stockwiki/cli_parsers/public_research_view.py`
- `stockwiki/dashboard_identity_bridge.py`
- `stockwiki/dashboard_issuer_proof.py`
- `stockwiki/dashboard_onboarding.py`
- `stockwiki/dashboard_onboarding_contract.py`
- `stockwiki/dashboard_onboarding_owner.py`
- `stockwiki/dashboard_profile_sources.py`
- `stockwiki/dashboard_research_binding.py`
- `stockwiki/dashboard_research_binding_contract.py`
- `stockwiki/dashboard_research_binding_flow.py`
- `stockwiki/dashboard_research_binding_owner.py`
- `stockwiki/dashboard_research_binding_proof.py`
- `stockwiki/dashboard_research_source_client.py`
- `stockwiki/dashboard_research_source_link.py`
- `stockwiki/dashboard_research_source_projection.py`
- `stockwiki/public_research_view.py`
- `stockwiki/public_research_view_cli.py`
- `stockwiki/quick_scan_membership_read.py`
- `stockwiki/quick_scan_membership_request.py`
- `stockwiki/research_profile_keys.py`
- `tests/test_dashboard_identity_bridge.py`
- `tests/test_dashboard_issuer_proof.py`
- `tests/test_dashboard_onboarding.py`
- `tests/test_dashboard_research_binding.py`
- `tests/test_dashboard_research_source_link.py`
- `tests/test_public_research_canonical_scope.py`
- `tests/test_public_research_citation_window.py`
- `tests/test_public_research_excerpt_display.py`
- `tests/test_public_research_view.py`
- `tests/test_public_research_view_blockers.py`
- `tests/test_public_research_view_semantics.py`
- `tests/test_quick_scan_membership_request.py`

#### codex/dashboard-sw-b34-id-repair

- `stockwiki/cli_registry.py`
- `stockwiki/identity_receipts.py`
- `stockwiki/quick_scan_store.py`
- `dashboard_identity_bridge_cli.py`
- `dashboard_issuer_proof_cli.py`
- `dashboard_onboarding_cli.py`
- `dashboard_profile_sources_cli.py`
- `dashboard_research_binding_cli.py`
- `dashboard_research_source_link_cli.py`
- `dashboard_security_id_repair_cli.py`
- `docs/handoffs/dashboard-B31-owner-release/controlled_owner_fixture.py`
- `stockwiki/_public_research_view_content.py`
- `stockwiki/_public_research_view_project.py`
- `stockwiki/_public_research_view_refs.py`
- `stockwiki/_public_research_view_source.py`
- `stockwiki/_public_research_view_state.py`
- `stockwiki/_public_research_view_wire.py`
- `stockwiki/admin_security_id_normalization.py`
- `stockwiki/cli_parsers/public_research_view.py`
- `stockwiki/dashboard_identity_bridge.py`
- `stockwiki/dashboard_issuer_proof.py`
- `stockwiki/dashboard_onboarding.py`
- `stockwiki/dashboard_onboarding_contract.py`
- `stockwiki/dashboard_onboarding_owner.py`
- `stockwiki/dashboard_profile_sources.py`
- `stockwiki/dashboard_research_binding.py`
- `stockwiki/dashboard_research_binding_contract.py`
- `stockwiki/dashboard_research_binding_flow.py`
- `stockwiki/dashboard_research_binding_owner.py`
- `stockwiki/dashboard_research_binding_proof.py`
- `stockwiki/dashboard_research_source_client.py`
- `stockwiki/dashboard_research_source_link.py`
- `stockwiki/dashboard_research_source_projection.py`
- `stockwiki/public_research_view.py`
- `stockwiki/public_research_view_cli.py`
- `stockwiki/research_profile_keys.py`
- `tests/b34_id_normalization/test_normalization.py`
- `tests/test_dashboard_identity_bridge.py`
- `tests/test_dashboard_issuer_proof.py`
- `tests/test_dashboard_onboarding.py`
- `tests/test_dashboard_research_binding.py`
- `tests/test_dashboard_research_source_link.py`
- `tests/test_public_research_canonical_scope.py`
- `tests/test_public_research_citation_window.py`
- `tests/test_public_research_excerpt_display.py`
- `tests/test_public_research_view.py`
- `tests/test_public_research_view_blockers.py`
- `tests/test_public_research_view_semantics.py`

### Unique commit inventory across all branches (each commit once)

```text
652f6a48992b260cfb9fe25d6496341dc6ecba5a feat(sw): publish the release of record and bind formal proofs to it (B36 HIGH-2)
f8b186cedf28f2d582c3c8953080d4431b6a1469 fix(sw): restore the authority no_update trigger after the v2 backfill (B36 NEW-2)
cf91052d74c1c39943bc8e0ce733842cd4fe37ba fix(sw): migrate schema-2 authority rows with a backfilled chain digest (B36 NEW-1)
f0b3c876ac5a798dec11adff714e00f6c7510768 fix(sw): bind the authority to the release artifact of a real import (B36 R1 GAP1/OPEN-2/3/4)
98bfd699de336c44b49b6b6e132363e3c8f2ddbb fix(sw): prove release completeness from the owner's authority, split formal from reference (B03-R1)
86879552ca43e85b5b55197eaafd96f6bd61581b fix(sw): refuse a company result whose observation lacks a run reference (B03 review RUN-REF-1)
dd7496a62b09637132172ede09a5f68fd7e4619f feat(sw): carry the original run/scan reference in the company result lineage (B03 reconciliation)
e4107beca55ad5e33a236bb519fbe1a104ca1fe4 fix(sw): leave no registry side effect on a refused first registration (B03 review)
d54e6f49696230ab8eb1a66a681150f33d482566 fix(sw): keep re-register idempotent and expose the bound subject revision (B03 review)
f44c5d31474fb39252b025d700427359fa2ad154 feat(sw): expose exact observation refs on company history summaries (B03 review)
12fa6494edb8bce4534fc895bb55397c38da2fc3 fix(sw): bind registry content and completeness to the published store set (B03 review)
b50f45e40f498c89d174372342251dc0040afe09 feat(sw): add public company assessment snapshot authority (B03)
586b2f7e73688aef2c16e6881591953637a1cf32 feat(sw): publish the release of record and bind formal proofs to it (B36 HIGH-2)
51dfc8b0b78edb92f6dda9a2d69f18d397358192 fix(sw): restore the authority no_update trigger after the v2 backfill (B36 NEW-2)
1f95973b21067dce0639070e3de15a9f8a076d06 fix(sw): migrate schema-2 authority rows with a backfilled chain digest (B36 NEW-1)
cd361224945b845cd1f9c732d6ac03e5fe186cdf fix(sw): bind the authority to the release artifact of a real import (B36 R1 GAP1/OPEN-2/3/4)
4532b0da00a38eb74d5464466a166dc38b890222 fix(owner): pin history snapshots and bind all lookup selectors
9349ced1a640bc2f738ed9f56b3efbbc0f5925b5 fix: honor an explicit universe when looking a request up by id
cc3e1a4da75ffb6fd936a1dbc76ae76aa1e5a257 feat: bind membership requests to receipts in one owner transaction
6e9069c10d17d4ee7f501b59d08dd7b5bdcc5aac fix(sw): prove release completeness from the owner's authority, split formal from reference (B03-R1)
c73dd8b0e9fe067a1767dc8c8f99663a4fe6fdef docs(stockwiki): hand off B37 exact-subject read projection and preserved tests
4bd49f8f19ee6585c5420589202167fe3c091e10 fix(stockwiki): fence all subject identity evidence stores on read
826ff6a3a60bd4bdcd6b2dc8411eb4b6ccf8a31d feat(stockwiki): expose exact native analysis-subject snapshots read-only
60a85efd536349ee7efb89744a3f4a79bbbcec4b fix: honor an explicit universe when looking a request up by id
7be0c970a2b608c621cdd26de812159e820ce180 feat: bind membership requests to receipts in one owner transaction
b3084ff3e7a7628cada90f6126f7e5b5292e5fbb fix(sw): refuse a company result whose observation lacks a run reference (B03 review RUN-REF-1)
7ae7c9ac55a36834a1a1fe0b975bab089df53673 feat(sw): carry the original run/scan reference in the company result lineage (B03 reconciliation)
4e034d66293ac794dddc979e8ab74d6874df9a32 fix(sw): leave no registry side effect on a refused first registration (B03 review)
1e552949070542164a0ce3ba41fc33b5e2743d30 fix(sw): keep re-register idempotent and expose the bound subject revision (B03 review)
aadf8afc30c729f642ded80f938c60b22ac464a4 feat(sw): expose exact observation refs on company history summaries (B03 review)
b7532c56f44dc59944b786f44e832b6dc7f3f5f9 fix(sw): bind registry content and completeness to the published store set (B03 review)
07fbb8a1169cca8dc17884002e78790219d906ca docs(stockwiki): retain independent SIDR001 repair evidence
a7b27d504f490252aaff576067af1102daa70043 fix(stockwiki): fence historical listing references during ID repair
778cd9d4ad40fa69b5af51929c9ae313a30e28b6 docs(owner): preserve raw validation artifacts as binary
d48ff8a7af80b830c706b1f565e5115d65daaa6e docs(owner): record B34 normalization validation handoff
4f6a4f14689836f9e71df12b84aa895d75daeadb feat(owner): add fenced security UUID normalization repair
2812d7093d1073ada658fe420c16e78de3501aaf feat(sw): add public company assessment snapshot authority (B03)
e22f15a6df23daef8403b783f5a36ee1bb115c1c fix: normalize legacy excerpt markup without altering verified source quotes
a8f69ac93492d4323142b74d127626e2e259d70f fix: keep returned claim citation metadata inside the bounded evidence window
58fc52ed4ab4a3151bd1fb96c4c61c58dc624481 fix: enforce source link deployment and semantic proof guards before I/O
91aac317533f9399101fbc328ce02a604332e6a6 docs: record fixed source link candidate affected regression
15ba3452413c5c261a88e248e66bc4b9f8e3e42e feat: admit current evidence source links with live issuer proof and exact citation projection
02151a8dd5a94dd29c4f09e9bed70c787c740834 fix: preserve live receipt authority and trusted profile claims across races
9189ebfff7c983481d2aa831904cf51b2508e264 fix: refuse absent registry during binding preview and record writer checks
f617f06edbbc1bd2cc4d408f1582f9b9fb803563 feat: implement owner research binding writer and atomic profile exclusivity
aa0a69f09f1f35bae2f9ea7a0498988069491faa docs: record B31 owner release validation and controlled CLI reproduction
309753db4ac749e1e3578a98a85b8115455385e2 merge: compose accepted issuer-proof read into Dashboard StockWiki release
eca69e1c463e472591c1b4cb1833d34e0f21b96d docs(handoff): record author-side command costs in delivery report
5dbcede6be50be6fdde7a317ce60c3e25d4a18a1 docs(handoff): record full-suite baseline comparison against base
3edbd1e9cb8b263f14481b02a5dbd7d564785bd9 docs(handoff): persist G-SW-ISSUER-PROOF-READ-01 delivery and review records
cf47ba7f8e316ab5250ebbfcbe508ab81da4c7cc fix(dashboard): name calendar-invalid as_of as invalid_as_of (reviewer M1)
2572593ae305f967c0aabbf967939950c3d2933d feat(dashboard): read-only issuer proof-read seam (G-SW-ISSUER-PROOF-READ-01)
194abedfcaa617dadb3cee90474606fbe3f1b0ad docs: hand off StockWiki B composition and UTF-8 self-check evidence
edcef4ec59a7cfe25e14764f2a51df2b59ab7d29 fix(identity-cli): keep public JSON UTF-8 under Windows codepages
23588bde724ab69cb0d243eb08747a2727338047 merge: compose accepted canonical research view with identity and onboarding
d44fc78ff6c4f00a4b6e35a5562c88b4708bcbe5 merge: compose accepted StockWiki identity bridge on onboarding base
042951b3f8ab5c9d0148d5542bb819633ffcbe08 docs(review): persist the round-8 reviewer record and bind the RETURN4 review
b760476e868c41ad53703f397c8570296603e074 docs(handoff): stop claiming a current SHA and document the host grammar
40ebbac6849d0ce3751744070c0cd32bdfa173f8 fix(onboarding): keep internationalised and trailing-dot hosts qualified
6c06bcccb670b425a0156e5fc9b25c2da7ecaef0 fix(onboarding): a URI needs a real host before it can exempt a path
74b023f5f3b57a50702260a72c9f6c8f99fee90c docs(handoff): list the round-7 machine record and note the 9-file scope
eebd2dc291ed1c13fb78d4a3bfd26edb52d22b7b docs(review): bind the round-7 RETURN3 review on 6fa6443 and apply F1-F3
6fa6443c7f70e90ca43f782ecc496c33e8d95962 docs(handoff): state the converse of the in-URI locator rule
92b42a1d627a3b1b5762b6743ebd31da9f6a5a81 fix(onboarding): a network URI is a context for its own colons and slashes
a10d158a67a6f150b8324ab9d9101bbc8a0f90b8 docs(review): record the final independent ACCEPTED close on 367993a
367993ac9e59fad3c9f078bb32240c56e63f08f4 docs(review): correct the R5-1 per-tree membership (round-6 finding F5)
8e482fa6e6204293d1f7e07084bba12b97b6343e docs(handoff): record a bare file: scheme as a known residual
e0dd1f9db5e21166feae1913a1916780195ce6df docs(review): bind the round-6 final verification and apply its four P4 findings
290ff003dd70de599ab71eb7536040a303e4c019 docs(review): bind the round-5 independent review on 7f8fb94 and fix R5-3
b77ce7ba84fa0c78d872b56eedd43d38ed5ea64d docs(handoff): record the two-layer locator rule and its four boundaries
7f8fb944b1a4f73c271f51e74616821816d28fcb fix(onboarding): a drive locator cannot hide behind a scheme prefix
d8d58aea2f9b76b815294c4b88cc563dd88ddb70 docs(handoff): document the URI-context locator rule and its boundaries
fb9443833de0ca35ed61647ac6f31d0b91e39eee fix(onboarding): read URI context in the physical locator policy
bc0146d1ca0248767bb72ff8a4b0f3c4e098db79 docs(review): bind reviewer-3 round-4 ACCEPTED replay on 80ab634
80ab63421d269b4323c1f9067de165353228c6b0 fix(onboarding): close review-round-3 findings GSW03-R3-1/R3-2
586333414b52329b69e314081499199e173d8f71 fix(onboarding): close D00 rework findings D00-SW03-001/002
7e29425041a0ad40692f92319c26cd4bccec5f21 fix(onboarding): close second-round review findings
a4eb1a39820718ca290df7aaeb8b7055a9ce2427 docs(handoff): finalize independent review PASS record and delivery binding (final candidate f71e7cd)
f71e7cdc3e5827120641b0ab18767ee65ac46550 fix(public-research-view): fail-closed market corroboration + genuine containment fixture
a78f44a27fa096c22caf556c63611000e20c95fd docs(handoff): update handoff to reflect final commit state and test count
ba8aac877e3e4cf30ff9ba4b6b8bd3da2b749b21 docs(handoff): add GREEN/static evidence files and independent-review protocol stub
58e1a89737fa44baee4a2bba77ce95501c75ad92 refactor(onboarding): move onboarding_schema to contract module
ee3bdd1154700e99ce99d2eba95f6257100c377d docs(handoff): record real-workspace base-vs-candidate comparison and baseline note
b5c0246af5e0f962f3fd2ca2b7fe85edc28bec60 fix(onboarding): close the G-SW-03 independent review findings
daf167e19c1a8cb623afe8eb103939eb0f4749e0 feat(public-research-view): canonical-scope guard for identity-to-profile linking
22343841c41dd41cfb32d29b896cd8cd5d22184f feat(onboarding): G-SW-03 public dashboard onboarding request/status facade
9c47effec043985da5df419e5713d6c5dc91b6ea docs: record independent closure re-test — SW-REV-1/2 closed (candidate 34c875d)
34c875d76e00ecfd32e024a2c2d0a3b349bef979 spec(identity): pin explicit listing selection semantics; record independent review (SW-REV-1/2)
6e306e7b130c269c9442b64f875785b7d8fc6772 feat(identity): public read-only dashboard identity bridge (G-RF-ID-01)
f6c402cd9685604204c488c89000775f283cd9be docs(handoff): record round-3 PASS, correct line-count basis
040541acb9aae75e176581f44db3477362a3e398 fix(public-research-view): close forward-slash path leak and review round-2 minors
5c1b8a676c167a1dbb99bb28b94be06777301554 fix(public-research-view): close all 25 independent-review findings
a89d6c5ae2dcaf28cd924547168aaccbfd007cc5 feat(public-research-view): add versioned pathless research view for dashboard
```

### All worktrees and uncommitted classification inputs

#### `C:\Users\郑曾波\Projects\StockWiki`

- HEAD 12c441e86282135b49120112dcf21c17509bbdd0; branch refs/heads/master
- status counts: `{"??": 7}`; roots: `{"data": 4, "logs": 1, "runs": 2}`
```text
?? data/companies/688012.SH/research_source_links.sqlite
?? data/dashboard_onboarding/evidence.sqlite
?? data/dashboard_onboarding/requests.sqlite
?? data/dashboard_research_binding/requests.sqlite
?? logs/stock_qa_20261110.log
?? runs/c16b/native-owner-alphabet-01/owner-workspace/data/quick_scan/analysis_subjects.sqlite
?? runs/c16b/native-owner-alphabet-01/owner-workspace/data/quick_scan/scan.sqlite
```

#### `C:\Users\郑曾波\AppData\Local\Temp\stockwiki-narrative-consumer-20261003`

- HEAD 4c3334ed412a6a6241eac307f20ad0593355f90f; branch refs/heads/codex/stockwiki-narrative-consumer-20261003
- status counts: `{" D": 2019}`; roots: `{".github": 1, ".gitignore": 1, ".planning": 19, ".pre-commit-config.yaml": 1, "AGENTS.md": 1, "README.md": 1, "config": 17, "data": 870, "docs": 12, "findings.md": 1, "framework": 23, "progress.md": 1, "pyproject.toml": 1, "runs": 79, "scripts": 4, "stockwiki": 157, "task_plan.md": 1, "tests": 95, "wiki": 733, "最初设想.md": 1}`
- 2019 tracked deletions are preserved as an incomplete/removed worktree finding, not endorsed removals; not a canonical source diff to merge. No cleanup authorized by this finding.
- physical root entries: `[".git", ".github", ".planning", "config", "data", "docs", "framework", "runs", "scripts", "stockwiki", "tests", "wiki"]`
```text
```

#### `C:\Users\郑曾波\AppData\Local\Temp\stockwiki-w04-mic-relations-20260930`

- HEAD afa969226dd56d1d0a729990eb6bd30912fd7a45; branch refs/heads/codex/stockwiki-w04-mic-relations
- status counts: `{" D": 1991}`; roots: `{".github": 1, ".gitignore": 1, ".planning": 18, ".pre-commit-config.yaml": 1, "AGENTS.md": 1, "README.md": 1, "config": 17, "data": 870, "docs": 11, "findings.md": 1, "framework": 23, "progress.md": 1, "pyproject.toml": 1, "runs": 79, "scripts": 4, "stockwiki": 145, "task_plan.md": 1, "tests": 81, "wiki": 733, "最初设想.md": 1}`
- 1991 tracked deletions are preserved as an incomplete/removed worktree finding, not endorsed removals; not a canonical source diff to merge. No cleanup authorized by this finding.
- physical root entries: `[".benchmarks", ".git", ".github", ".planning", ".ruff_cache", "config", "data", "docs", "framework", "runs", "scripts", "stockwiki", "tests", "wiki"]`
```text
```

#### `C:\Users\郑曾波\Projects\_g2\sw\StockWiki`

- HEAD 0b48919065a912f1da10d89d36bf6bf1e659db88; branch refs/heads/codex/g2-sw-daily
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\_harness_worktrees\cmrf-20261008\sw-permission-residue`

- HEAD d98acdcdf1a2feada2ae91f2f56aafaa74046728; branch refs/heads/codex/main-permission-residue-20261009
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\_harness_worktrees\d4-01-20261102\stockwiki`

- HEAD 23d84586dc2425961e953f5ab28aef867de6cb87; branch refs/heads/codex/d4-01-company-source-virtualization
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\_harness_worktrees\d5-20261105\stockwiki`

- HEAD 6d1e40bcdcde5e99488e22c38d57bd8e1b33c27e; branch refs/heads/codex/d5-sw-processed-reader
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\d00-b03-stockwiki`

- HEAD 652f6a48992b260cfb9fe25d6496341dc6ecba5a; branch refs/heads/codex/d00-b03-stockwiki
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\dashboard-owner-stockwiki`

- HEAD f6c402cd9685604204c488c89000775f283cd9be; branch refs/heads/codex/dashboard-stockwiki-public-research
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\dashboard-owner-stockwiki-b-integration`

- HEAD 194abedfcaa617dadb3cee90474606fbe3f1b0ad; branch refs/heads/codex/dashboard-stockwiki-b-integration
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\dashboard-owner-stockwiki-identity`

- HEAD 9c47effec043985da5df419e5713d6c5dc91b6ea; branch refs/heads/codex/dashboard-stockwiki-identity-bridge
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\dashboard-owner-stockwiki-onboarding`

- HEAD 042951b3f8ab5c9d0148d5542bb819633ffcbe08; branch refs/heads/codex/dashboard-stockwiki-onboarding
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\dashboard-owner-stockwiki-proof-read`

- HEAD eca69e1c463e472591c1b4cb1833d34e0f21b96d; branch refs/heads/codex/dashboard-stockwiki-proof-read
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\dashboard-owner-stockwiki-research-scope`

- HEAD a4eb1a39820718ca290df7aaeb8b7055a9ce2427; branch refs/heads/codex/dashboard-stockwiki-research-scope
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\dashboard-owner-sw-b03-assessments`

- HEAD 586b2f7e73688aef2c16e6881591953637a1cf32; branch refs/heads/codex/dashboard-owner-sw-b03-assessments
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\dashboard-owner-sw-c1-authority`

- HEAD 60a85efd536349ee7efb89744a3f4a79bbbcec4b; branch refs/heads/codex/dashboard-owner-sw-c1-authority
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\invest-quick-scan\.worktrees\stockwiki-dashboard-ports-20261109`

- HEAD c2c65c60fa6ad3fe1d73a2ea9ee27747264c7fff; detached
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\invest-quick-scan\.worktrees\sw-f05-fact-ingest-20261109`

- HEAD 93b25927f58b129628776b349f8bda7f2f264dba; branch refs/heads/codex/f05-fact-ingest-20261109
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\investment-dashboard\.worktrees\b31-sw-release`

- HEAD aa0a69f09f1f35bae2f9ea7a0498988069491faa; branch refs/heads/codex/dashboard-sw-b31-release
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\investment-dashboard\.worktrees\b33-sw-binding`

- HEAD e22f15a6df23daef8403b783f5a36ee1bb115c1c; branch refs/heads/codex/dashboard-b33-sw-binding
- status counts: `{"??": 62}`; roots: `{".test-runs": 62}`
```text
?? .test-runs/swrbase/test_backup_root_and_parent_ju0/junction/root/foreign/sentinel.txt
?? .test-runs/swrbase/test_backup_root_and_parent_ju0/junction/root/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_backup_root_and_parent_ju1/junction/parent/foreign/sentinel.txt
?? .test-runs/swrbase/test_backup_root_and_parent_ju1/junction/parent/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_corrupt_bytes_owner_regis0/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_create_refuses_a_name_tha0/escape/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_create_refuses_a_name_tha0/escape/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_failed_final_rename_is_re0/rename_fail/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_failed_final_rename_is_re0/rename_fail/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_foreign_manifest_json_sha0/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_foreign_manifest_json_sha1/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_foreign_manifest_json_sha2/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_foreign_manifest_json_sha3/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_legacy_backup_without_own0/legacy/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_legacy_backup_without_own0/legacy/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_legacy_backup_without_own0/legacy_target/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_legacy_backup_without_own0/legacy_target/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_list_marks_partial_and_co0/listing/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_list_marks_partial_and_co0/listing/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_manifest_damage_family_is0/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_non_utf8_foreign_manifest0/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_non_utf8_foreign_manifest1/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_owner_registry_records_th0/reg/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_owner_registry_records_th0/reg/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_prune_never_deletes_the_o0/partial_guard/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_prune_never_deletes_the_o0/partial_guard/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_prune_skips_damaged_unkno0/mixed/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_prune_skips_damaged_unkno0/mixed/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_prune_skips_every_foreign0/foreign/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_prune_skips_every_foreign0/foreign/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_restore_into_absent_targe0/absent/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_restore_into_absent_targe0/absent/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_restore_into_absent_targe0/target_absent_ok/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_restore_into_absent_targe0/target_absent_ok/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_restore_of_a_link_inside_0/src_link/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_restore_of_a_link_inside_0/src_link/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_restore_refuses_a_junctio0/elsewhere/not_ours.txt
?? .test-runs/swrbase/test_restore_refuses_a_junctio0/jct_src/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_restore_refuses_a_junctio0/jct_src/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_restore_refuses_a_junctio0/target_jct_ok/data/quick_scan/not_ours.txt
?? .test-runs/swrbase/test_restore_refuses_a_junctio1/jctp_src/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_restore_refuses_a_junctio1/jctp_src/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_restore_refuses_non_empty0/ne/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_restore_refuses_non_empty0/ne/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_restore_refuses_non_empty0/target_ne_ok/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_restore_refuses_target_fi0/race/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_restore_refuses_target_fi0/race/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_restore_refuses_target_fi0/target_race_ok/data/quick_scan/concurrent.txt
?? .test-runs/swrbase/test_swr1_restore_accepts_alre0/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_swr2_foreign_self_consist0/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_swr3_failed_final_rename_0/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_swr4_two_subjects_of_one_0/workspace/data/quick_scan/analysis_subjects.sqlite
?? .test-runs/swrbase/test_swr4_two_subjects_of_one_0/workspace/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_swr4_two_subjects_of_one_0/workspace/data/quick_scan/scan_evidence.sqlite
?? .test-runs/swrbase/test_swr4_two_subjects_of_one_0/workspace/data/quick_scan/scan_observations.sqlite
?? .test-runs/swrbase/test_swr_wal_committed_pages_p0/walws/data/quick_scan/scan.sqlite
?? .test-runs/swrbase/test_truncated_multibyte_manif0/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_truncated_multibyte_manif1/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_undecodable_manifest_is_a0/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_unknown_registry_version_0/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_unknown_registry_version_1/workspace/data/quick_scan/marker.txt
?? .test-runs/swrbase/test_unknown_registry_version_2/workspace/data/quick_scan/marker.txt
```

#### `C:\Users\郑曾波\Projects\investment-dashboard\.worktrees\b34-sw-id-repair`

- HEAD 07fbb8a1169cca8dc17884002e78790219d906ca; branch refs/heads/codex/dashboard-sw-b34-id-repair
- status counts: `{"??": 5}`; roots: `{".mimosa": 4, ".test-runs": 1}`
```text
?? .mimosa/hook-state/sess_4889923d-dd84-42a5-a716-d64d41d86a67.json
?? .mimosa/hook-state/sess_4889923d-dd84-42a5-a716-d64d41d86a67.lock/owner.json
?? .mimosa/hook-state/sess_4889923d-dd84-42a5-a716-d64d41d86a67.lock/reclaim.json
?? .mimosa/hook-status/sess_4889923d-dd84-42a5-a716-d64d41d86a67-e082143602.json
?? .test-runs/b34-sidr001-root-green.xml
```

#### `C:\Users\郑曾波\Projects\investment-dashboard\.worktrees\b37-sw-subject`

- HEAD c73dd8b0e9fe067a1767dc8c8f99663a4fe6fdef; branch refs/heads/codex/dashboard-sw-b37-subject
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\investment-dashboard\.worktrees\c38-sw-release`

- HEAD 4532b0da00a38eb74d5464466a166dc38b890222; branch refs/heads/codex/dashboard-c38-sw-release
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\investment-dashboard\.worktrees\return5-sw-audit`

- HEAD 5dbcede6be50be6fdde7a317ce60c3e25d4a18a1; branch refs/heads/codex/d00-return5-sw-audit
- status counts: `{"??": 14}`; roots: `{".d00-audit": 14}`
```text
?? .d00-audit/design-6376103/01-source-matrix.md
?? .d00-audit/design-6376103/02-binding-proposal.md
?? .d00-audit/design-6376103/03-state-machine.md
?? .d00-audit/design-6376103/04-model-tests.md
?? .d00-audit/design-6376103/05-implementation-feasibility.md
?? .d00-audit/design-6376103/model.py
?? .d00-audit/design-6376103/proposal-examples-negative.json
?? .d00-audit/design-6376103/proposal-examples-positive.json
?? .d00-audit/design-6376103/proposal-schema.json
?? .d00-audit/design-6376103/test_binding_model.py
?? .d00-audit/design-6376103/validator.py
?? .d00-audit/design-race-probe-results.json
?? .d00-audit/design_race_probe.py
?? .d00-audit/design_race_probe_fullshape.py
```

#### `C:\Users\郑曾波\Projects\StockWiki-f05-mainline-wt`

- HEAD 3799b439cfd9808b428eca85b07d5e18b9b3370c; branch refs/heads/codex/f05-owner-runtime-01
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\StockWiki-identity`

- HEAD ae11135cc1160adc74cc1d307ca8bd73cb4fa832; branch refs/heads/codex/identity-snapshot-w02-w03
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\StockWiki-lane-integration`

- HEAD 52add7fd8710b6c7e4b4f4294b358cc10cd01ac8; branch refs/heads/codex/stockwiki-lane-integration
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\StockWiki-sw-ident`

- HEAD 0c8603e43f8fa42bc9a877d43715826c8a48c121; branch refs/heads/codex/stockwiki-sw-ident
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\StockWiki-v2-reader`

- HEAD 0b406832b744892df7b592ca5d5c0d9fe2a0e3da; branch refs/heads/codex/source-export-v2-reader
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\StockWiki-w04-g2b`

- HEAD 6f0c2c4abe9b70e0e9c48c32e80f883a14c40983; branch refs/heads/codex/stockwiki-g2b-owner-context
- status counts: `{}`; roots: `{}`
- no uncommitted paths

## analyze-theme-value-chain

- canonical: `C:\Users\郑曾波\Projects\analyze-theme-value-chain`
- main `master` at `3352b580c781976be8b1d627e0fac7f4af9bd68a`
- remotes: `none`; upstream: `ERROR fatal: no upstream configured for branch 'master'`

### Canonical uncommitted paths

```text
 M scripts/quick_scan_client.py
 M tests/test_quick_scan_integration.py
?? .codegraph/.gitignore
?? .codegraph/config.json
?? scripts/__pycache__/quick_scan_client.cpython-313.pyc
?? tests/__pycache__/test_quick_scan_integration.cpython-313-pytest-9.1.1.pyc
?? tests/fixtures/quick_scan/__pycache__/quick_scan_fixtures.cpython-313.pyc
?? tests/fixtures/quick_scan/quick_scan_client_test_harness.py
```

### All local branches

| Branch | tip | commits outside main | cherry unique / equivalent | final changed-path state: same / different / absent on main |
|---|---|---:|---:|---:|
| `master` | `3352b580c7` | 0 (ancestor) | n/a | n/a |

### Maximal outstanding tips (ancestor branches need no separate merge)


### Changed implementation paths still different or absent on main

### Unique commit inventory across all branches (each commit once)

```text
(none)
```

### All worktrees and uncommitted classification inputs

#### `C:\Users\郑曾波\Projects\analyze-theme-value-chain`

- HEAD 3352b580c781976be8b1d627e0fac7f4af9bd68a; branch refs/heads/master
- status counts: `{" M": 2, "??": 6}`; roots: `{"scripts": 2, "tests": 4, ".codegraph": 2}`
```text
 M scripts/quick_scan_client.py
 M tests/test_quick_scan_integration.py
?? .codegraph/.gitignore
?? .codegraph/config.json
?? scripts/__pycache__/quick_scan_client.cpython-313.pyc
?? tests/__pycache__/test_quick_scan_integration.cpython-313-pytest-9.1.1.pyc
?? tests/fixtures/quick_scan/__pycache__/quick_scan_fixtures.cpython-313.pyc
?? tests/fixtures/quick_scan/quick_scan_client_test_harness.py
```

## industry-research

- canonical: `C:\Users\郑曾波\Projects\industry-research`
- main `main` at `7d49ca378bbbcf947eb2ce1d1bb6f7c3db8a0b70`
- remotes: `origin`; upstream: `origin/main`

### Canonical uncommitted paths

```text
?? tests/test_quick_scan_module_boundaries.py
```

### All local branches

| Branch | tip | commits outside main | cherry unique / equivalent | final changed-path state: same / different / absent on main |
|---|---|---:|---:|---:|
| `codex/ir-report-generation-20261024` | `1e84336eda` | 0 (ancestor) | n/a | n/a |
| `codex/root-merge-ir-20261031` | `1e84336eda` | 0 (ancestor) | n/a | n/a |
| `main` | `7d49ca378b` | 0 (ancestor) | n/a | n/a |

### Maximal outstanding tips (ancestor branches need no separate merge)


### Changed implementation paths still different or absent on main

### Unique commit inventory across all branches (each commit once)

```text
(none)
```

### All worktrees and uncommitted classification inputs

#### `C:\Users\郑曾波\Projects\industry-research`

- HEAD 7d49ca378bbbcf947eb2ce1d1bb6f7c3db8a0b70; branch refs/heads/main
- status counts: `{"??": 1}`; roots: `{"tests": 1}`
```text
?? tests/test_quick_scan_module_boundaries.py
```

#### `C:\Users\郑曾波\Projects\_merge_ir`

- HEAD 1e84336eda1505748e5497b3910e29ba55cd43fe; branch refs/heads/codex/root-merge-ir-20261031
- status counts: `{}`; roots: `{}`
- no uncommitted paths

#### `C:\Users\郑曾波\Projects\industry-research-report-generation`

- HEAD 1e84336eda1505748e5497b3910e29ba55cd43fe; branch refs/heads/codex/ir-report-generation-20261024
- status counts: `{}`; roots: `{}`
- no uncommitted paths


## 总控处理结果（晚于只读快照）

2026-11-11，总控已精确删除本报告列明的三个Theme `.pyc`；源文件与新harness保留。StockWiki七份运行库/日志、旧分支和含junction测试目录均未删除，未迁移任何真实库。C38整体/名单配对和B34文档的承接顺序已加入MC-SW、MC-IQS；Theme/Industry源码候选已加入各自MC卡，未用文档更新冒充源码验收。
