# IQS总控线：契约、题库、发布物与跨线整合

**Owner:** 主控 `/root`。

**项目目录:** `invest-quick-scan/`（本仓完整所有权）；这是唯一可同时维护planning-with-files与产品契约的线。不要另派harness在该仓并行写代码或计划。

**状态:** 可继续推进；另三仓worker只读本仓的冻结接口，不编辑IQS。

## 独立上下文

本仓是问题、schema、release、校验工具和协调计划的owner。它不是运行时数据库、provider客户端或研究UI。问题模块以加法版本演进；题目身份、评分尺/anchor、事实字段和routing各自有版本，旧结果按旧版本解释，不因新模块改写。真实公司文档、财报或网页正文不进入本仓夹具；测试公司须用合成数据或用户明确提供的样本。

## 任务范围与包内顺序

负责`tasks.json`中owner=`iqs`的40项任务：P00、C01–C07、G0、S01–S03、G1、L02、G2/G3、F01、G4/G5/G6、X07/X12、S04–S10、F06、V01–V05、V12/V13/V16–V18。任务清单只在此列便于定位，依赖与验收仍以`tasks.json`原条目为准。

同一线内按依赖顺序实施，重点冲突簇不得拆给不同harness：

- 问题模块/路由簇：S04–S10、F01/F06、V01–V05/V13，可能共享`questions/`、`scripts/question_sets.py`、模块registry与测试。
- 契约/版本簇：C01–C07、V12/V16–V18，可能共享`schemas/quick_scan/`、contracts、演进校验和测试。
- 本仓只保留纯规则/协议；StockQA执行语义归StockQA，权威名单/观察归StockWiki。

总控保留`task_plan.md`、`progress.md`、`findings.md`、`docs/implementation/parallel-lanes/**`、全局review封存与跨仓验证记录。若某task原计划要改`tasks.json`、`acceptance-cases.json`、`docs/implementation/README.md`或`test-strategy.md`，执行者先在handoff提供建议diff/具体内容，由总控合并，避免worker覆盖中央计划；任务本身仍需总控校验。

## 对外接口

发布物从本仓版本化路径读取，至少包括身份、metric/scoring/rules、question-module与release-lock、route decision、facts/ontology、screening lenses、refresh policy、ScanRecipe、component-release/compatibility/evolution-impact。StockQA和StockWiki须锁定实际schema内容hash与release ID；消费者只依公开query契约。

本线不读取StockWiki私有数据库、不产出伪造producer golden；不修改外仓schema来让IQS校验通过。G2b只能消费StockWiki真实DTO/serializer golden；S06跨仓部分只能用真实StockQA与StockWiki回执闭环。

## TDD测试包

- 题库/模块变更：相关`test_question_sets.py`、`test_module_registry.py`、`test_module_contract.py`、`test_standard_answers.py`、`test_routing.py`、`test_fact_registry.py`和`test_scan_recipe.py`；加法演进需回放冻结旧版本夹具。
- 契约演进：对应schema解析、`contract_validation.py`、`component_releases.py`、`evolution_impact.py`和compatibility fixture测试；旧版本历史reader与新writer分开验证。
- 本地大节点：`tests/test_implementation_plan.py`以及本线受影响测试组；执行README里各任务绑定的公开CLI验证。真实CI命令须用当前环境复核，不在lane包里硬编码过期配置路径。
- 离线端到端：仅使用独立临时发布根、合成issuer/listing/answers和mock API结果；确认失败不写正式公司库、不会删改测试前内容。

本线先RED后GREEN，变更相邻case聚合；只在G0–G6相应大门和高影响接口变化时做独立审查。

## 交接给总控

按`handoff.schema.json`提供：base/head commit或可复现工作树hash、精确变更路径、schema/module/recipe版本与hash、任务/case映射、RED/GREEN与最终测试统计、命令、temp root清理、review findings、向下兼容读取结果、未关闭跨仓依赖。IQS主控自己更新PWF和中央任务状态。
