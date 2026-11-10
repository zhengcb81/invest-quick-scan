# 当前接手说明

**2026-11-10 当前模块边界状态。** 模块图与常见越界静态回归已建立，但共享引擎跨仓接线还未达到可发布状态：IQS 已提交边界测试 `4328208` 缺少其引用的两份源码；StockQA、Company Agent、Agent Runtime 的新 facade 仍仅在脏工作树，canonical HEAD 未包含。当前 IQS 聚焦组 177 passed、公共 task factory 合同 2 passed，模块/路由/题库回归 214 passed/236 subtests；恢复/答案相邻组也已覆盖（详见根 `progress.md`）；StockQA 配置/恢复组 37 passed、模块边界组 24 passed。它们读取未提交 owner 候选，不能作为 clean checkout 或生产集成通过证据。独立审查发现的 API 最低版本不一致、StockQA 私有文件布局检查和直接绕过 facade 的 Company Agent 调用已修正于候选工作树，尚未发布。详见根 [`progress.md`](../../progress.md) 最新模块化记录和 [`docs/architecture/module-boundaries.md`](../../docs/architecture/module-boundaries.md)。模块化主线保持 OPEN：owner commits 可用后固定版本跑干净跨仓正反例，再由新独立 reviewer 复核；随后才继续 F05/W11 技能入口 E2E。静态边界规则不是防任意反射的运行时沙箱。

**2026-11-09 F05/E12 交接。** IQS `7446b5f` 与 `59c1dd5`、StockQA `4c24789`、StockWiki `93b2592`。F05 使用真实宁德时代 `FACT_10`，原授权登记、MiMo、原观察、StockWiki 导入及原 ACK 接通。公开 2.7 查询和导出各有自己的快照，分页沿原查询快照，Strict 当前排除待审核的 19 条候选。原观察库保持原样。启用事实时可用 `python scripts/question_sets.py publish-facts --module-package-id <现有发布包>`，配置 `prepare.module_package_id`，通过既有准备入口选 `question_ids`。发布归档不切换评分默认包。需要临时真公司验收时新建观察库，不能搬用原库绑定。

Dashboard 公司页选择已登记包，通过 `iqs-job/1` 提交并核对原任务。中微浏览器实际返回成功和已交付一题，零新增模型调用。部署要配置同一 IQS 产品服务的 `DASHBOARD_IQS_JOBS_*`，以及可解析当前挂牌的 StockWiki `DASHBOARD_STOCKWIKI_IDENTITY_*`，其中已验代码根为 `dashboard-owner-stockwiki-b-integration`。实际模型新派发的 NR-1 和公司级正式完整结果单独看。Dashboard 授权清单中的119个提交/634个路径已发布；新增测试提交 `0dcf61f` 也已发布，远端 `origin/main` 精确核对为 `0dcf61f59595ebe4b64d9bd8ea490087ed62f7fd`。测试：后端61项+20子测试、QuickScan前端7项、TS类型检查、synthetic E2E 3项通过；前端全量75项通过、1项能力缓存旧响应用例因并行未提交的能力改动而失败，该文件不属于本次提交。此提交只增测试，不含生产代码；Dashboard 工作树其他并行改动未纳入推送。清单见 `runs/e12-dashboard-closeout-20261109/dashboard-pending-push.txt`。以根 [task_plan.md](../../task_plan.md) 与 [progress.md](../../progress.md) 的最新段为准。

**2026-11-09 并线前的模块边界进度（历史快照）。** StockWiki 工作台查询、B03 公司评估和原生准备已并入本地主线 `c2c65c6`。StockQA 交付与配置 `d5294fb`、原生生命周期 `7eebaae`，以及 IQS 查询方言 `9540ea8`、主实现 `25dc299` 均已推主线。部署先更新两个所有者，再更新 IQS 消费者。工作台旧 `--worker` 转发原 JSON 入口，StockQA 保持旧任务工厂兼容。339 项合跑、独立复核和原生零重发证据见 [progress.md](../../progress.md)。F05 公开接口候选已推 `18a8ad7`，根工作树 2.8 改动保持独立。外部 Dashboard 消费者在 `codex/iqs-public-reply-boundary-20261109`，任务命令实际接通仍依赖原 IQS `owner_job_cli.py` 包。

**本轮公开接口整改。** IQS 工作台改为经公开交付操作、恢复引用解析、origin 解析和 TIME 包入口协作。运行 `python -B -m pytest -q tests/test_dashboard_module_boundaries.py` 可以看到越界文件、行号及访问名。该测试已纳入 `scripts/run_tests.py fast`，范围为工作台模块内的显式 Python 引用和常见局部别名。Theme `master@3352b58` 与 Industry `main@7d49ca3` 已使用独立查询捕获目录。Industry 已推送，Theme 仓无远端。真实数据入口仍按根计划验收。

**F05 旧候选核查。** IQS 2.7 候选 `16c7b1a` 与 2.8 WIP 已在隔离副本完成 87 项回归。三个重叠文件是 `scripts/query_facts_contract.py`、`tests/test_query_facts_contract.py` 与 `tests/test_f05_facts_cli_conformance.py`。三方合并基准为 `130dc31`。根工作树原 WIP 保持独立，合入时与其写入方协同。真实配置的 owner 能力探测认可 2.7 候选，事实观察为零，下一步沿原采集流程生成可绑定的事实观察并用公开 CLI 完成验收。旧 F05 集成测试仍引用缺失的外仓 Git 对象 `63a6ffcf`，在候选并入后由独立 CLI 回归接替。

**2026-11-09 本轮并线前的状态（历史快照）。** 本项目已可在小范围使用；当时认为全项目尚未模块化解耦，F05 真实数据闭环和 G4 也未完成。11-10 的模块边界工作已更新前一结论，金融/真实owner/规模事项仍按根计划开放。IQS `master` `3d2bf44` 已推送：修复兼容 query 接口允许模型答案自授 `check_level` 的既往缺陷，定向 106 passed、8 subtests passed，独立审查 ACCEPT。IQS F05 consumer candidate `codex/f05-query-paged-response-01`（`16c7b1a`，已推分支，74 passed）尚未并入 `master`，因为根目录存在重叠 2.8 WIP。StockWiki owner candidate `3799b43` 已快进并入本地 canonical `master`；六文件 F05/路由测试组 45 passed、2 skipped，StockWiki 无 remote。路由 manifest 完整性修复独立审查 ACCEPT。

**当时的实质阻塞（历史快照）。** CATL owner 公开 query 返回 `coverage_gap / no_bound_fact_observations`，没有事实正例 golden；F05 仍 partial。IQS 根工作树有别的并行 2.8 WIP，不要 reset、checkout 覆写或 `git add -A`；consumer 候选并线前先在单 writer 状态对齐依赖。Theme `master@e35ab39` 与 Industry `main@169c200` 已有 canonical 代码、tracked clean；需在稳定 F05/W11 接口上跑真实技能入口 E2E。随后真实 F05 单题已有进展；技能入口 E2E 与 G4、真实200家 G3、2000家覆盖和 G5/G6 仍未完成。

**设计结论：** D1–D7 只证明既定行为范围通过，不等于全仓解耦。跨仓只通过版本化公开 CLI/JSON schema/capability 协议；仓内模块经公开 facade/protocol 协作。Python `_private` 不会天然阻止调用，靠 CI AST/import 边界测试阻止越界，不给每个小改动新增人工审批。稳定接口后可让各仓分别维护自己的 PWF；根 IQS PWF 只做版本/依赖/集成协调，不另造回执或门禁系统。

**11/06 F05 进展存档。** 独立包 [F05-IQS-CONSUMER-01](parallel-lanes/packages/2026-11-05-f05-iqs-consumer/README.md) 的已审查 payload `08e5b4d6` 已合入本仓 `master`（`da34654`）。主线 facts/capabilities/public CLI 定向82 passed；加相邻 exchange/query 回归97 passed、7子测试。旧 query v2 的 `model_self_qualification` 冻结基线失败在合并前已出现，本轮仍保留为非本次引入的失败。**F05 仍为 partial**：主线有消费者契约和校验CLI，但普通产品/共享引擎尚未接上实际 StockWiki owner runtime，真实 owner golden 和当前公开 CLI 正反互操作也未完成；未运行生产UI、数据库写入或收费API。详情见根 [task_plan.md](../../task_plan.md)、[progress.md](../../progress.md) 和 Lab handoff `C:\Users\郑曾波\Projects\iqs-f05-iqs-consumer-lab\docs\handoff\F05-IQS-CONSUMER-01\report.md`。

**2026-11-07 三个独立施工包已验收：** [F05-OWNER-MAINLINE-02](parallel-lanes/packages/2026-11-06-mainline-consumer-wave/F05-OWNER-MAINLINE-02.md) 在隔离 StockWiki Lab 的实现提交 `6449917c` 已独立审查；交接状态 `partial`，真实 owner golden、IQS public CLI 正反互操作和 canonical StockWiki 合并仍未做。[TH-IMPL-02](parallel-lanes/packages/2026-11-06-mainline-consumer-wave/TH-IMPL-02.md) 的离线消费者提交 `54773536`（54项测试，CP936 默认编码独立复审通过）和 [IN-IMPL-02](parallel-lanes/packages/2026-11-06-mainline-consumer-wave/IN-IMPL-02.md) 提交 `ba54e00f`（161项测试，独立复审通过）已验收；两者还未整合进各自 canonical skill 源仓。三份 handoff 经 IQS CLI `--verify-references` 均为 valid。总控下一步按根 [task_plan.md](../../task_plan.md) 继续 F05 真实 owner 接线与 golden/互操作，再整合 TH/IN；不把离线包完成误报为产品闭环。

**11/02最新补充。** [解耦 D1–D7 整改](reviews/DECOUPLING-2026-11-02/remediation.md)已通过独立复核。恢复使用原登记发布根、原语义资源及原请求规则。以后新增 renderer 或答案资源时登记新版本并保留原版本读路径。UI 与 Company Lab 为本地组件仓，提交与 StockQA 版本见报告。接下来按根计划回到小池内容质量和事实主线。

**11/02 上一节点的 CI 证据。** [CI 连续失败根修](reviews/CI-ROOT-CAUSE-2026-11-02/report.md)在 StockQA `0154726` 的 CI 41523660779 与 Documentation 41523660825 通过，文档构建和发布均已核实。[完整链路混合与重启整改](reviews/GATE-SIMPLIFY-2026-11-02/full-chain-restart-remediation.md)仍是既有真实恢复证据。


更新于2026-11-07。本页只说明如何接手；唯一执行顺序是根[task_plan.md](../../task_plan.md)，实际阶段证据见[progress.md](../../progress.md)。更早长文已[归档](archive/pwf-through-2026-10-31/README.md)，历史日期段不能覆盖当前结论。

## 当前已经完成什么

原8766工作台、身份/215实体名单、组合基础36题、比较/名单维护、三市场各36有效题槽的真实入库与冷恢复均已接通。最近扫描真实复用与过期刷新已有正例。

早间节点已完成原UI共享gen6已付IQS_11的零API恢复、保存、StockWiki ACK及普通配置再次同题复用。当时总账86HTTP/US$2.024863，0在途/未结/active；同一原分数7、资料日2026-10-29与完成时间2026-11-01T07:33:28.670089Z不变。晚间gen7是保留它的新比较，11/02已独立保存并获ACK；两个代次均保留，普通cached1证据仍对应gen6。

原owner/SDK短证据软件E2E1P/701.62秒，实际出站body含excerpt/URL/published_at:null，保存和复用通过；只替换vendor wire。旧真实请求的原证据板仍空，未把新原数补进旧context。不得据此声明金融准确性通过或模型已在旧请求使用这些原数。

## 现在从哪里继续

**此前11/02原四组有界终态：** 前端启动、SDK能力、公开seam、旧工具和显式1.6共享顺位已根修。旧隔离E2E1P/656.77秒只覆盖当时边界，不改签；本次另有1P/298.03秒真正冷进程keyless/无预算部分恢复，以及下方原UI真实gen7 CP/ACK闭环。详见[本节点终验](reviews/GATE-SIMPLIFY-2026-11-02/report.md)，旧报告仍为[历史证据](reviews/CODE-QUALITY-2026-11-01/remediation-2026-11-02.md)。下一步只看根Next Step，不重开四组或重问gen7。

**原gen7当前终态：** `run-5a03133643e34e60b69d6b9b311b46c0` / work `WORK_ef7cfb7bd41740ab95e2d31af6c78548` 沿原UI第6次launch成功保存，CP `CHECKPOINT_1c5c5d9766b34ddcab8317ac34256b31`，交付job `deliveryjob_03aeb32cc6f07b1525d3a147fb893cc0` 完成；11/02 11:00:20Z accepted ACK `ack_fd86eacd8b792b505a582f13`。原实际模型mimo-v2.6-pro、score8、完成时间2026-11-01T23:44:40.990609Z与原响应hash保持，原gen6观察仍在；UI公司详情可读新旧候选，总览歧义不应强行合并分数。

11/01最初命名失败、11/02先后单位与singleton失败都是历史诊断；原safe/旧export保留，不代表当前仍leased/CP0。通用修复已允许未映射metric保存，去掉无证文字单位/自审误诊，并复用原binding codec完整覆盖provided context。分红范围、利润归属和日期状态等金融限制仍未全核，保存成功不把它变成金融通过。

普通配置hash未变、60包保持，总账87HTTP/2053896micros，0在途/未结；**不要再次运行configure或release_unsent.py**，也不要重做原comparison决议。原UI仅seal/recover及原receiver逐项ACK，无收费API。后续继续根Next Step的内容质量与既有范围。

本轮原四组已收口：共享原1.6确认/targets/binding5保留实际模型与原scope/cap，复用原SDK、lease/CAS和预算；已结明确拒绝才换下个模型，未知/内容错误不重问，已完成CP不重复恢复或计费。QA与SW按原successful_scan规则统一缓存时钟，资料日与原来源仍不改。配置见[实操](shared-engine-operations.md#共享扫描的模型顺位)。旧1.0–1.5、comparison、原已付记录保持原合同；本机普通配置不自动升级1.6。

本轮未扩专用人工work-decision为1.6，也不冒称金融质量、200家、事实F05、TH/IN或配套完成。这些仍按根计划推进，不新发支线、不造门。

## 本机运行与普通配置

- 入口`http://127.0.0.1:8766/`，配置`config/dashboard.local.json`（忽略文件），原工作区`runs/r25-live/owner-workspace`明确为isolated_research；执行配置`runs/u25-live/runtime`。密钥只在环境变量，不打印、不提交。
- 当前已恢复普通policy11/1.1、successful_scan/24h及原prepare全部设置；pack2、thinking=true、max32768，无shared专用配置或comparison refs。保留60个已登记包和历史，不能整文件恢复到只有59或58包的旧备份。
- 早间08:35的gen6历史同范围IQS_11预览`prepare_16f75b1a321f4ee592459d7ea66e33ad`为cached1/执行包0/API0、owner未变；不是晚间gen7的缓存正例。原UI当时直接显示原结果，无确认/登记job；资料日与最近扫描时间分别保留，查看/导入/重启不续期。
- 正常启动见[README](../../README.md)。不按记忆PID杀进程；重启前核实际argv、创建时间和原费用/任务状态。看页面与预览不发模型。

## 不要重复处理的原对象

|对象|已完成的原记录|
|---|---|
|运行/批次|run-73ab08b815574449a6337c806a9bb2cc / batch-8e527bf6bd6a45f58e908cc9ea3837b3|
|原work/代次|WORK_3bfb09edaec248aca717f561b20d68cf / generation6，delivered|
|原attempt/SDK|ATTEMPT_a0a4f2329acf4a3483ca11bb6f41ba8e / 3c660196-d0f7-44ff-9467-e789305992b8|
|原CP|CHECKPOINT_91c41d78927d4330ba74001ff783442e|
|交付|deliveryjob_275e156668c52d138ea84887f11626c8，completed，scope1/1；ACK accepted，08:28:19Z|
|观察|obs_37dc46500bdffc1cb28152df715fe576290af3cb8c6ca84db10f9036deed3188|

原safe与失败重放诊断继续保留；session0003从原pending恢复并发布export，不删除或覆写原session0001。原时间/receipt/response hash、旧板与原ACK已由非作者亲自只读对账。详细原报告见[现金流/共享接线节点](reviews/CASHFLOW-CORRECTION-2026-11-01/report.md)。

## 实现边界与实际版本

IQS负责题库/路由和薄接线；StockQA负责原客户端、搜索、预算、任务、检查点与outbox；StockWiki负责身份/名单/观察/ACK/查询。不复制数据库或重试器；company-wiki及其他活动writer保持隔离，不下载财报或网页全文。

|仓库|本次复核的实际基线（不等于全仓新验收）|
|---|---|
|IQS|e24c359完整链路源码/测试，PWF与文档最终提交见Git，已推原origin/master|
|StockQA|0154726（ee8f49a源修+文档依赖兼容），正常hooks/完整default/最终远端CI与文档成功，已推原origin/master|
|Company Lab|639582a，本地提交、无remote，tracked clean|
|Runtime Lab|5839ef4，本地提交、无remote，原codex/agent-run-02分支|
|原UI|fa7ceb6，本地提交、无remote|
|StockWiki|本轮只读看到9e8e308后又变f52f257；上轮本线程提交e5a1be6仍在历史。有活动writer，不覆写、不把本轮只读检查当新HEAD全仓验收|

原UI补封透传冻结shared配置和controls；StockQA原recover分支仅重放，缺原safe拒绝新model/search。缺密钥不改变policy eligibility，按原response_available attempt精确route恢复。新pending仍受原发送准入；已有坏检查点不跳过，真实缺文件才回读尚存原pending。来源闭包拒失效ID改名，HTTP只有原投影合格才接受。

## 工程检查如何交接

日常每commit继续轻量hooks；一个实现节点使用StockQA原 `python -B scripts/checks.py` 默认短包（black/isort/mypy/Bandit/daily pytest/smoke）。不要用正常hooks或push成功冒称CI通过：查看对应commit的GitHub Actions真实结论，pending明确写pending。README/pyproject变化还可能触发Documentation，须看实际build/deploy结果；不重跑旧commit消除历史红。只有新变化、失败或覆盖问题才追加相关测试，不机械重跑小时full。

## 测试、审查与未完成边界

本轮11/02四组以[最终报告](reviews/CODE-QUALITY-2026-11-01/remediation-2026-11-02.md)为准：QA授权216P/独审32P、执行独审79P与paid尾28P、SW/IQS合同独审105P、准备作者23P及非作者16P、UI独审7P/16子例；重叠不加总。两个原owner/SDK E2E分别491.08秒与656.77秒，最后一个才覆盖新增1.6无CP已付窗口，临时五仓副本自动移除。以下744秒/154P等是前一节点证据。

本轮完整原owner/SDK E2E1P/744.04秒（仅vendor wire脚本化、0收费、TEMP移除），最后paid-only尾修用实际session/SQLite和原parser118P验证。最终完整UI执行模块154P，UI其它72P、题库87个不同测试、QA指标/原子快照117P、共享17P、Lab22P/Runtime6P；测试有重叠不加总。独审最终QA32P/1S与UI3P，关键过期override实际1P并非skip；其余详细命令/局限见progress。原701.62秒是前一节点证据，不冒签当前paid-only分支。

集中独审通过工程恢复/原ACK范围，不授金融准确性。只对大产品节点集中测试/审查；小修复跑受影响项，不跑小时全套、不建逐题凭证/组件资格审批/active全局ReleaseSet或第二派发许可证。原身份/作用域、预算、防未知重发和ACK保护保留。

用户已授权必要后续修复、独审及正常提交推送，不重复问权限。每仓单writer，保留根外来的`docs/implementation/parallel-lanes/packages/2026-10-10/README.md`改动与历史untracked，不使用git add全仓、reset或清理他人文件。

StockWiki其他writer状态会变化，不按本页旧清单清理；原static hook临时保存的外来patch已核实恢复。本轮只做相关测试及一次集中交叉独审，未新增许可证或逐assertion回执。
