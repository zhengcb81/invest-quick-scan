# G0 最终独立复审报告

- reviewer: `agent:/root/g0_current_review`
- review_date: `2026-09-26`
- reviewed_candidate: `docs/implementation/reviews/G0/candidate-snapshot.json`
- candidate_sha256: `7F291C298C36A64DD2795892B2D8A294F78B1E3E952382B44B31D5A6C887BE89`
- plan_version: `1.9.7`
- packet: `docs/implementation/reviews/G0/current-review-packet-2026-09-26.md`
- packet_sha256: `2A6BC9B3D8FFAB2130A485B0040624212C4149151E87248AB0E3620B2D4D72AF`
- invariant_matrix: `docs/implementation/reviews/G0/current-invariant-matrix-2026-09-26.md`
- invariant_matrix_sha256: `51FC769E82909FF40119BF78CEA122FBBCA9D6DB2214F99BA4E657D736F0B66F`
- declared_scope_files: `639`
- decision: `verified_for_local_contract_scope`
- findings: `P0=0, P1=0, P2=0`

## 结论

本轮冻结候选通过G0独立复审，范围限于本仓题库、schema、离线契约与校验器、计划和证据链。此前发现的候选遗漏已通过显式绑定G0的两份`read_first`文件及fail-closed回归关闭；C01 `ID-02.T01`也已从测试内手写分支改为调用公开`cv.validate_entity`，并用同一实体、两个证券及owner-held `same_legal_issuer=false`回执验证拒绝。当前C01 r2独立审查、回执和测试日志均绑定修订后snapshot。

候选不代表生产就绪、真实搜索已完成、跨仓集成已通过或2000家公司扫描可用。当前未证明项见本报告末尾。

## 实际检查

| 检查 | 结果 |
|---|---|
| 冻结候选原始SHA-256 | 与委托值完全一致：`7F291C298C36A64DD2795892B2D8A294F78B1E3E952382B44B31D5A6C887BE89`。 |
| `python -B scripts/g0_candidate_manifest.py verify` | `scope_files=639`，`errors=[]`；逐项重算hash均匹配，声明集合与实际范围一致。 |
| G0 `read_first`范围 | `docs/stock-pool-design.md`与`docs/universe-and-operations-design.md`都在manifest中；生成器验证当前read_first必在期望集合与候选内，回归覆盖未来路径漂移时拒绝。 |
| C01 `ID-02.T01`定向反例 | 当前测试调用`cv.validate_entity`。独立重跑`python -B -X utf8 -m pytest --rootdir=<repo> --basetemp=<unique-temp> --no-cov -p no:cacheprovider -q tests/test_identity_contract.py::IdentityContractTests::test_id_02_parent_subsidiary_cannot_merge_without_verified_issuer`：`1 passed`；隔离临时根已移除。 |
| C01 r2 snapshot / review / 日志绑定 | C01 snapshot `14d9d5c4b5c0f6e5f9b24e7848e69adf5f3cf189d26a6db19b2d5ff9d7b06c45`与r2 reviewer报告和C01 receipt一致；报告SHA与receipt相同，报告、日志均由当前候选manifest固定。r2审查`approved`、无开放finding；批次为16 passed、31 subtests、0 skip。 |
| 公共receipt验证器 | 对当前C07执行`python -B scripts/task_receipts.py verify --receipt iqs:docs/implementation/contracts/receipt-C07.json --plan iqs:docs/implementation/tasks.json --cases iqs:docs/implementation/acceptance-cases.json --root iqs=.`：`eligible_to_close=true`、`blockers=[]`；递归包含当前C01—C07、P00、P01。 |
| C07递归sidecar | 当前r2 sidecar SHA-256 `FB444E4A1E44216CA87BC6B9CDB17C6E38F9D8E20CAC4C0939AA5B762D7CDEB8`，记录eligible且无blocker；文件hash与候选一致。 |
| 归档r1链 | `archive/id02-receipt-chain-r1-2026-09-26/manifest.json`列出的7个旧回执/sidecar哈希均匹配归档字节；原始候选及旧final report也保存在历史归档。 |
| 已有集中批次 | 检查了候选内绑定的C01—C07共享离线批次（188 passed、121 subtests、0 skip）和G0范围/计划批次r4（94 passed、55 subtests、0 skip）；本轮未重跑这两个已有效批次。r4日志另记plan validator `planning_valid=true`、103 tasks、327 cases、G6，`product_tests_executed=false`。 |

## G0案例、历史发现与约束

- `BASE-02`：P00当前只读基线报告记录了仓库快照、接口观察、测试/工具边界及未执行事项。它没有把静态读取描述为生产验收；本轮无外仓写入、测试或API调用。
- `REV-01`：当前P00/P01/C01—C07 v2回执、对应日志、C07递归侧车和冻结候选可独立检查；本报告绑定当前候选SHA。
- `REV-02`：manifest集合/文件hash/计划版本/声明范围均通过；read_first、持久化fixture与需排除的mutable journal、自身manifest、未来G0 receipt及最终review范围符合当前生成器声明。C01 snapshot和receipt依赖经公共验证器递归复核。
- `REV-03`：G0反例调用公共validator，保留结构schema与语义校验的区分；本轮单独重放了修订后的ID-02关键负例。集中批次未被重复执行，测试日志区分实际离线契约与live/provider行为。
- `G0-01`至`G0-08`：当前候选中的评分/可信检查receipt、实体与scope校验、公共实现调用、交换正文逃逸防护、readiness证据闭包、query状态/lineage、规则语言与执行器及祖先闭包反例仍有当前源码和定向回归支持；本轮重点验证了G0-03中被发现的ID-02缺口已修复。
- `G0-09`与`RR-04`：issuer-index描述以当前P00只读基线为准；候选完整性现包含G0 read_first文档、`tests/fixtures/**`、计划版本及当前声明范围，并由生成器/负例测试保护。
- `RR-01`至`RR-03`：可信检查回执对象/等级绑定、readiness与同release/manifest闭包、规则schema与公共executor一致性的当前回归仍纳入候选，未见回归。
- `I01/I04/I05/I08/I12/I17/I18/I52/I53`：矩阵证据和边界与当前候选、回执及测试日志相符。明确区分本地schema/契约验证与未执行的外仓、并发、持久化及联网能力。

本轮无P0、P1或P2开放发现。

## 范围限制

本轮只读检查`invest-quick-scan`快照，没有修改外部仓库、运行外部仓库测试、调用真实LLM/web search/API或下载公司文件。离线fixture和stub不能证明实时搜索或实际provider额度切换。

仍待后续owner/live验收的事项包括：真实web search与完整provider轮换/额度拒绝、StockWiki真实导入和SQLite并发、生产持久队列/费用账本/崩溃恢复、UI、安装后的实际加载版本核验、2000家公司运行、analyze-theme-value-chain/industry-research联动及live E2E-06。不得将G0本结论扩展到这些范围。

历史final review原件在`docs/implementation/reviews/G0/archive/independent-final-review-2026-09-23.md`保留，SHA-256 `7F05BFCDF6980B3D03EA9A1734B7E717A24C797D337FE4EBD5F210F793876F38`；归档原候选SHA-256为`3DE13B1596CEB1EEA0A9A66B46E957334DBE245DB094476C07527564A23C1EB3`。
