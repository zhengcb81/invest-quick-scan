# 实际架构调查与收尾根因

2026-11-11；总控和三个独立 agent 分别只读检查 IQS、执行链、存储/消费者、UI。未运行本轮产品测试或真实模型。行号是调查时位置。CodeGraph用于结构入口；部分外仓索引滞后，已对已知实际文件补读，不能拿旧索引证明新实现不存在。

## 实际版本，而不是旧 PWF 的推断

|对象|调查时 HEAD|工作树/候选状态|结论|
|---|---|---|---|
|IQS|`fbe5b39c40b37f4694465e6712f4be602c2afa3e`|题库、语义、共享引擎等未提交；本地含bb20529；ports要求QA≥1.7、CA2.3、RT1.4|旧文档1.5不是当前要求；不能只取HEAD丢掉已有工作|
|StockQA|`4c24789a2c2d93eb24cae8ef4dacb00d6f585c23`|正式磁盘facade1.5，HEAD无此文件；`.tmp-stockqa-current-wt-20261110`同HEAD但facade1.8、87份tracked diff另有新文件|候选分叉是实际接线阻力|
|Company Agent|`793bfbc239edc596c7edabeab48df97fdcc5e99f`|API2.3、task1.1已提交；远端本轮未查|保留实现，需组合验证|
|Runtime|`5839ef4c4f3ec66c0994fb0531009d227631294d`|HEAD无api；两工作树磁盘API1.4；`.tmp-modularity-runtime-20261110`含49份tracked差异和新文件|不能只提交测试|
|StockWiki|`12c441e86282135b49120112dcf21c17509bbdd0`|本轮tracked clean，已含边界重构提交|保留CLI，检查设计粒度|
|原8766 UI|`47d5354575b7561f278bed54e5eb29478574f103`|仓是`iqs-question-bank-ui-lab`；dirty状态未可靠确认|勿与历史viewer混淆|
|Dashboard|`b707473a1166d3f8740170dad77cb21aa09863ce`|较旧0dcf61f前进；有D00计划；dirty状态未可靠确认|旧提交不是当前全仓基线|
|Theme|`3352b580c781976be8b1d627e0fac7f4af9bd68a`|client/测试有tracked差异，另有test harness新文件|承接WIP而非覆盖|
|Industry|`7d49ca378bbbcf947eb2ce1d1bb6f7c3db8a0b70`|本轮tracked clean|重点兼容/边界验证|
|company-wiki|`08dfe8bf1ae97dff34b28976d532b3482d3ba358`|本轮tracked clean；未见IQS执行依赖|保留SourceRef，不加入改造关键路径|

上述是时间点快照；开工重读差异并保留有效增量，不因无关文档HEAD变化重新审一切。

## 设计调查总表

|能力域|已有实现应保留|确认不足/待验证风险|归属|
|---|---|---|---|
|IQS题库路由|module contract、release/package、manifest/selection已拆，数量由数据派生|脚本导入路径需集中；验证领域测试不依赖UI/owner环境；不要求每文件各自无环|MC-IQS|
|IQS语义/共享编排|公开answer_validation；task factory交给QA；engine不自建账本|须证明仅公开fake可运行；当前API floor与正式QA不符|MC-IQS/MC-QA|
|QA执行保存|opaque runtime/session、lifecycle Protocol、owner refresh API候选|facade校验操作后返回整个module；候选/正式分叉|MC-QA|
|CA task/runner|slots/owner registry、snapshot深复制|与RT的task规则需统一；动态题集不能受legacy12题限制（尚未证实当前生产有此问题）|MC-CA|
|Runtime薄桥|API1.4、四操作句柄、services1.0|协议/double混置；当前集成仍用locked fixture；根conftest装冻结facade|MC-RT|
|StockWiki|公开身份/名单/prepare/query/import/ACK、事务|publication拿整个control；两个跨能力循环；业务知道CA/RT源码布局|MC-SW|
|原8766 UI|API client、比较/名单/时间组件|双向源码加载，build理解IQS目录，历史alias映射末值覆盖风险|MC-UI/MC-IQS|
|Dashboard|ports→HTTP/CLI、generated DTO|应用构造SavedViewStore、注入过宽；缺方向检查；扩展字段拒绝需按真实协议判断|MC-DASH|
|Theme/Industry|公开CLI、capture根、分页快照|Theme字节误拒；Industry手写同wire常量，需统一公开语义向量|MC-TH/MC-IN|

## 关键证据和根修方向

### 扫描规则偏离设计目标

Runtime候选`tests/test_module_boundaries.py`约1657行，QA候选对应文件超过2300行，含别名、遮蔽、推导式与动态调用分析。StockWiki `tests/test_f05_module_api_boundaries.py:10,222,344`按所有quick_scan文件划边界，给8个叶子文件加exports/version。**域内helper过度公开，而宽对象/域间反向依赖依然存在。** 应用能力域依赖检查、窄对象、替换和状态隔离测试；不删光测试、不追恶意反射。

### Runtime旧交付材料挡住当前功能

`tests/test_document_claims.py:21`、`test_handoff_pins.py`、`tools/run_acceptance_checks.py:36–102`检查旧AGENT-RUN-02手工用例数和freeze/handoff/review pin。新用例导致218/219不符，与产品行为无关。停止为当前源码更新这些历史记录；移入显式legacy归档检查。当前测试结果自然产生，不手工制造passed总数。

### StockWiki宽对象和依赖环

`stockwiki/quick_scan_saved_research_publication.py:47`的`inspect_publication(control, outer)`读取control的config_reader、permissions、clock、executor_inspector、receipt_reader、contract；`:36–43`检查CA/RT的`src/<package>/__init__.py`。去掉下划线没有消除耦合。

只读AST发现67个quick_scan文件中两组SCC：import/observations/qualification/subject_dispatch；publication/work_decision_owner/work_delegation。不要求每文件无环；纯值规则下沉，装配上移，使五个能力域单向依赖。

### 相同语义schema被格式拒绝

Theme `scripts/quick_scan_client.py:358–370,954`固定原字节SHA。IQS `query-facts-v2.7.schema.json`为`cd3e0341…`，StockWiki `quick_scan_facts_query.schema.json`为`f00ad1ba…`；JSON解析后完全相等，$id相同。**普通schema兼容不能由文本格式决定**；原始答案/不可变题包完整性hash仍有用途。

### 两个UI被混为一谈

原UI `scripts/serve.py:158–169`把IQS/scripts加入sys.path并构造DashboardService；IQS `scripts/open_dashboard.py:28–36`反向依赖UI serve。UI `adapters/paths.py:27–49`识别questions/release布局与2026-10-18目录，`build_data.py:57–190`自己装题库和匹配公司。`answer_repository.py:49–60,128–159`名称/ticker映射风险仅确认在历史草稿路径，**不能据此断言正式身份库错配**。

Dashboard实际已为`adapters/iqs/`包；ports在`ports/protocols.py:192–241`。`application/service.py:18,81–96`直接构造存储、使用过宽Mapping。应收紧注入，不重建前端。

## 调查限度

本轮没有运行产品测试，没有宣称检查所有历史Lab；静态SCC不是直接的功能bug，额外字段检查也不一律删除。已证实误拒进入RED；风险先用TDD验证再改。专项范围是正常产品依赖图及列明能力域，不是任意Python程序的安全隔离。
