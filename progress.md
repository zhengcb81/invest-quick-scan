# 当前进度与阶段证据

## 2026-11-14 能力域迁移与固定组合验证

- 保存前序 IQS 工作为 `e63cef4`，十个能力域迁移为 `465d567`。最终代码 `30c30c0` 由架构测试直接扫描实现包，核对方向和公开导出。原 CLI 保留，StockQA 经原 `answer_validation.py` 读取公开答案语义接口。冻结题包字段映射由题库提供。
- 固定 StockWiki `f2bc73f` 的第 7 版身份库被读路径的 `{5,6}` 误拒。独立隔离复现记录 `schema_unavailable`，将兼容性声明集中到存储域后，F05 原生测试 31 项通过（1 个需要 Git fixture 的历史项未纳入），5/6/7 兼容与未知版本拒绝 4 项通过。StockWiki 精确修复 `9a62022` 已入本地 master，无远端。并行的名单改动与研究来源适配分支保留。
- 固定 I1–I7 均通过，I1 为 196 项和 71 个子测试，I6 为 19 项通过，两个历史 VIEW 夹具未安装，I7 为 2 项。普通 31 题与共享原生执行、混合冷恢复、有效期与过期、公开事实消费的实际节点和来源见[联测报告](docs/implementation/parallel-lanes/packages/2026-11-11-modularity-closeout/fixed-combination-2026-11-14.md)。默认快速套件 1127 项、391 个子测试通过；最后一组事实能力负例及历史施工归档检查 27 项通过。
- 独立审查拒绝过动态导入、别名绕行和数据根误拒，修复后 `final_boundary_review` ACCEPT。Dashboard `b03e14b` 已推，远端 `e6a9efc` 包含该提交。未调用收费 API，未触及正式工作库或名单。

## 2026-11-14 原工作台与真实事实消费

- IQS 模块化交接 `3f4f7ee` 已推送并核对 `origin/master`。原工作台重新启动，首页、设置、doctor、任务和宁德时代结果均有公开 HTTP 成功响应。缺失展示快照用 `workbench_snapshot_cli.py` 生成；展示 48 模块、222 评分题、61 信息题、215 家名单。正式业务库与名单未写入，模型和搜索请求均为零。
- 使用 `3f4f7ee`、StockWiki `21cf489`、Theme `00e4fbd`、Industry `bb0c3b9`，从已有真实 `FACT_10` 原观察读取。Theme 查询首两页并保持 snapshot，导出 19 条候选；严格查询给出 `no_match_partial`、0 条已验证关系。Industry capabilities `ready`，采齐 4 页 19 条，导出 `ok`，生成独立报告栏目。档案原库文件哈希一致，临时捕获和报告已清理。事实范围仍限该题。
- W11 定向与增量回归 `test_explicit_subset_preserves_full_bank_and_registers_only_selected_native_question`、`test_multiple_questions_for_one_field_stay_distinct_and_scope_is_not_truncated` 和 `test_time05_scope_update.py` 合计 4 项通过。真实范围扩展仍见根计划。
- 已回收本轮两个 Git 工作树、测试副本和数据库。Windows 仍锁住一个空目录外壳，检查为 0 个文件。本地薄证据保留于 `runs/_modularity_20261114/evidence`。

## 2026-11-13 I1–I7 并行模块审查（历史快照）

按公开接口/状态矩阵分域并行审查并合并同源根因，避免逐个反例打补丁：I1公开facade和I7 Dashboard已有独立审查；I5 Theme/Industry已修复、独审和提交；I2普通31题恢复链通过；I3原生 intent 回执、付费回答恢复、unknown 暂停、未发送分类及入库 ACK 的隔离全链现已通过（见本文件 2026-11-13 I3 末尾记录），早期“缺原生 intent 查询”文字属于该修复前快照；I4、I6 已有定向通过记录。**仍未完成的是这些场景在固定提交组合上的复跑及一次独立总审。**

- **I2 普通/共享持久化：** 普通 `main_with_llm` 31题真实子进程链已逐题断言唯一attempt与work/question绑定、原生response、checkpoint/standard answer、ready delivery观察/模型/截止日；第二个冷进程撤掉HTTP stub后复用31题、model_calls=0、发送日志不变，attempt/checkpoint/delivery完整快照相同。隔离定向测试1 passed/31.55秒，owned runtime清理成功，付费API0。非作者审查认可测试覆盖结构；共享部分现有paid partial与12题native恢复例已核覆盖，但仍在I1–I7固定来源组合复跑时收尾。
- **I3 unknown 回执：** 初始公开CLI复现和首轮修复已证明unknown-only不重发，但独立审查发现它只查StockQA发送状态及StockWiki发送前subject receipt，没有调用CompanyResearchRuntime公开 `recover_intent()` 查询Runtime原生模型intent/response；当前新增E2E只手工构造StockQA uncertain attempt，不能证明原生回执可恢复/缺失时暂停。原生路径必须经版本化CompanyResearchRuntime、Runtime和Company Agent public facade，禁止 `.native` 或私有service穿透；补回执存在、缺失、mixed与never-sent场景，并保留ordinary checkpoint unknown-only拒绝。首轮1 passed/140.16秒只作为窄行为证据，I3仍OPEN。
- **测试隔离纠正：** I3 早期两次尝试错误地沿用了环境变量指向的两个预存 `.iqs-*` 源码测试根；只生成了两个零字节日志和两个PID attestation文件。按运行时间清单确认无数据库/名单变更，随后仅删除这四个本轮文件，两个旧根其余内容保留并核实本轮没有新文件。后续回归将把源码运行根、owner库、logs和attestation都放入本次pytest临时目录；未把这两次尝试计为验收。
- **I4 缓存：** 暂无证据表明freshness/TTL产品逻辑有误，仍缺fresh→过期刷新→持久化→只读查询不续期的组合闭环。StockQA continuation CLI原始输出 `status=ok, rows=[]`；此前路径错误因只读源仓日志CWD已解决。refresh preview拒绝在提权隔离执行后确认是Windows sandbox对临时owner目录 `os.link(staging,path)` 的PermissionError，不是业务拒绝；随后统一使用过去3天逻辑时钟又让synthetic response早于原始send/registration，正确触发 `subject_dispatch_response_time_mismatch`。当前正在使用跨子进程一致的test-only时钟，不改外仓源码，不放宽owner校验。
- **I5 Theme/Industry：** RED复现默认截止日下分页续页可返回自洽但不同日期的 query hash，旧实现会合并跨日期事实。首个成功页固定cutoff/query hash/snapshot，续页显式携带cutoff并对漂移页拒绝合并。非作者总复审 **ACCEPT**；Industry 95 passed/13 subtests，Theme 101 passed/1既有skip。Industry提交`bb0c3b9`已快进推送，`origin/main`实核到完整SHA `bb0c3b9255cca0944e5f127e42cd10a3797eae52`；Theme提交`00e4fbd`本地干净提交，仓库没有配置remote，未新建远端。两仓仅提交I5精确文件，外仓工作树干净。
- **I6 原工作台：** 新增真实 `open_dashboard.py --no-refresh`、当前UI/浏览器、任务页重开E2E；loopback受限执行环境中首跑被Windows socketpair限制，提权后用例1 passed/7.56秒，进程/资源清理。它使用未登记任务，启动按钮为disabled，因此只证明重开只读，不足以签收。已确认可用隔离正式bundle/WorkStore、临时StockQA兼容runner和确定性本地回答stub，补真实HTTP显式start→tasks状态读取→页面reload并断言不二次start。
- **I3/I7本轮真实隔离证据：** `test_unknown_intent_cold_native_e2e.py` 现有底层行为例为 **1 passed/0 skipped，410.519秒，付费API 0，外网拒绝，临时根清理**；另一次 shared native E2E **1 passed，551.48秒，付费API 0，临时源码副本清理**。后者从运行时各仓工作树复制文件且没有捕获当时 HEAD/diff/hash，故只作行为证据，不算固定提交组合通过；unknown 行为测试还需断言 `all_slots_completed=false`。相关运行记录在 `runs/test-reports/i3-unknown-final-20261113T021734Z/` 和 `runs/qa-public-seams-2026-11-02/shared-engine-native-current-final-20261113.log`。

**当时状态。** I1–I7 已有定向通过记录，I3 的通过证据见本文件末尾。固定来源与独立总审见上方 11-14 记录。

## 2026-11-13 平铺脚本、类封装与边界合同回归

- **设计裁定：** 不对每个脚本机械套类。类用于有状态、资源或生命周期对象；领域规则按能力域封装，跨域用版本化 facade/DTO/CLI，依赖在应用组合根接线。Python 的 `_private` 只是约定，类不会形成访问控制。若按域迁移目录，逐域新增包 facade并保留旧 CLI 薄入口，避免一次搬动136个脚本。
- **基线确认：** 本仓当前 `scripts/` 有 **136** 个 Python 脚本；源代码依赖检查曾计得 **226** 条直接导入边、未发现静态循环。无循环不代表低耦合；边界缺少完整归属和API操作声明，才让同类跨域访问能以普通公开 helper/对象成员出现。
- **架构测试根修：** 清单要求全部136项逐一归层，应用层有独立显式清单；API协议需是语义版本，公开导出必须实际绑定。扫描器支持无别名/有别名跨域导入、常见 importlib/__import__、简单变量链、导入类、构造实例与条件表达式来源合并后的私有成员、`getattr`、`vars`；冲突别名保守失败。冻结模块loader测试现在逐项核对“锁定模块名→loader函数→相同字面导入”，不再替换掉真实loader后只测字典调用。
- **实际暴露的问题：** RED阶段及独审逐步发现清单漏项、源文件/导入目标未归类会静默跳过、公开声明有未绑定名称、实验launcher的动态导入不透明、模块别名/对象别名/构造实例私有访问漏检、测试断言分支覆盖不足。已修复归属、API声明、延迟导入显式映射、扫描器和夹具；扫描器遇多来源赋值时改为稳定的ambiguous结果，不再循环传播。
- **验证：** `tests/test_shared_public_boundaries.py tests/test_company_agent_contrast_launcher.py` **80 passed**。受影响合同组合（question manifest、standard answers、routing、module/exchange/query/subject-dispatch/deployment）在具有正常临时硬链接权限的本机隔离路径 **158 passed、57 subtests passed**。一次沙箱内重复组合失败主要来自Windows临时目录硬链接权限，不是产品断言；提权隔离重跑通过。没有模型/搜索API、业务数据库或名单写入。
- **独审/范围：** 独立审查先后补出公开类无别名导入、构造实例和常量`getattr`三个漏检，均加入反例并修复。最终审查者从当前差异独立复跑 **80 passed（14.70秒）并 ACCEPT**，结论仅限常见显式导入、别名、构造、条件表达式与成员访问路径；不是运行时安全沙箱。固定来源I1–I7组合仍未复跑，不能据此宣称模块化专项完成。

## 2026-11-11 各模块WIP与未并线审查、精确清理及小修并线

总控及三个只读agent核9个源仓、各自注册工作树和候选副本，输出[四份详细报告及处理索引](docs/implementation/parallel-lanes/packages/2026-11-11-modularity-closeout/intake-audit/README.md)。分清真祖先、patch等价、手工重做、实质缺失与本地未推送；审查结果加入原9张MC卡，不新发一批。StockWiki/IQS C38名单authority确实未归主线，已写明版本/依赖/合流测试；QA/Runtime有效WIP和旧快照参考完整保留，Theme新harness/Industry边界测试不误删。

实际清理：71个pytest目录20,728文件1,526,513,329字节；另6个确认残留354,258字节，合计20,734文件约1.53GB。精确列表见cleanup.md。删除前检查根边界、无reparse/内嵌.git与活动进程；真实/原工作库、原答、配置、历史证据和原注册worktree未动；测试临时SQLite/源码副本属于已清产物。本轮自建Dashboard测试worktree完成用途后正常移除。

Dashboard在独立worktree摘取5d2a761、4b30e1d、8e3231c，测试hunk冲突保留streaming和buffered两例，不选边丢测试。最终5a16ca7/c56e9ce/0addea2经非作者完整diff核验，2个测试文件29项全部通过；随后canonical main由b707473快进0addea2，6项当前源码WIP前后哈希一致。其余19个原本本地未发布提交未推送，不借此次小修代签全D00发布。收尾时发现另一writer于20:21提交2049356，原6项WIP及其README已进入main；0addea2仍是其祖先。MC-DASH基线相应更新，未把这项新提交算入本轮29项验收。

环境/核查偏差也已处理：外部worktree的沙箱Git误报改用只读沙箱外Git；UTF-8路径用字节解码避免中文乱码；两次沙箱pytest卡在首个Windows asyncio测试，精确停止自有PID后相同离线命令沙箱外3.86秒返回29通过；初次并线保护因测试从tests/unit迁至m0-platform而停止，复核最新路径再ff，未覆盖writer。文档提交预检另检出执行链报告末尾多余空行，已规范后重检。上述失败未算成产品断言失败。未付费、未运行真实owner/下载、未修改生产名单或数据库。

本节点文档/操作独立终核PASS，三处措辞歧义已修复，无开放发现，详见intake-audit/review.md；不代签保留WIP或并行提交2049356的功能质量。

当前9仓核心TDD尚待实施；本次是归拢前的收账。下一步只按MC卡读取相关变动、收成真实自包含owner组合，不刷新旧回执。IQS已有未发布源码的QA/RT依赖仍未齐，本轮文档本地提交后不把它们悄然推送成可用产品。

## 2026-11-11 架构重新规划（未继续源码实施）

响应用户要求，使用planning-with-files，先读实际代码和各仓Git。三个独立agent分别审执行链、数据/研究消费者、两套UI，总控审IQS。确定9仓责任线和有限退出条件；计划、调查、公共契约/TDD、整合交接及9份施工卡在[同一目录](docs/implementation/parallel-lanes/packages/2026-11-11-modularity-closeout/README.md)。这一轮没有运行产品测试、真实模型、服务或写生产库。

发现并纠正的关键状态：QA canonical磁盘1.5与候选1.8分叉，HEAD均无facade；IQS最低已1.7。CA793bfbc已提交；RT的current_sources仍测locked fixture，旧218/219与pin校验将退出当前产品默认测试，不再更新历史回执。SW实际12c441e、Dashboard b707473，原8766为question-bank UI@47d5354；Theme3352b58有WIP、Industry7d49ca3。

确认设计缺口：宽control穿透、能力域循环、UI双向源码装配与硬编码历史目录、Theme同义schema原字节误拒；各包用公开替身/DTO隔离/域方向/实际保存恢复TDD收口。保留既有opaque句柄和公开CLI，不增加框架、授权或审查小节点。

三个非作者agent均已完成规划复核并通过。审查修正了：expired新发凭证、mixed pending与零API的区分、fake与真实owner绑定、公共2.7向量来源/closed字段、原UI单向启动/快照生成与partial状态、Dashboard短临时目录。详见[规划审查](docs/implementation/parallel-lanes/packages/2026-11-11-modularity-closeout/plan-review.md)。本轮源码实施未启动。后续交接必须区分源码提交、独立验证、组合发布，不能再用测试数/包数表示产品完成。

调查工具小问题已处理：PowerShell的rg路径glob改用-g；旧猜测测试清单名改为tests/suites.json；已知不存在的dashboard_query未继续追；一次apply_patch同路径Delete/Add失败后改Update，未改变源码。它们不是产品阻塞。

## 2026-11-09 F05 与 E12 收尾

起点 IQS `eec815f` 与 `origin/master` 一致。2.8 相关的七个已跟踪文件和一个新 schema 最近修改时间为 11 月 7 日，未观察到新的内容变化或 Git 索引锁，在并线前再次复验。另有一份 10 月 10 日历史 README，单独保留。F05 候选为 `18a8ad7`，E12 交付为 `23d20b8`。先冻结 2.8，再在隔离工作树合并 F05。E12 同期完成了只读核查。

F05 合并落账于 `3f085bc`，父提交 `19b5478` 保留 2.8 施工内容，另一父提交为候选 `18a8ad7`。并线前八份原件哈希和修改时间仍与冻结记录一致。原始字节在本地 `runs/f05-mainline-closeout-20261109/wip-2.8/`，无关 10 月 README 改动单独保留。独立复核发现公开能力误报和挂牌错配。修复后 2.7/2.8 共用挂牌范围检查，历史无挂牌元数据的实体记录仍可读，2.8 缺失挂牌与已有挂牌的矛盾会拒绝。新增三个反例先红后绿。定向和相邻 query 回归 **174 项通过**，独立复审 PASS。

实际 StockWiki `c2c65c6` 从配置的 owner 库通过公开 CLI 返回 CATL 客户事实覆盖不足，事实总数为零。公开 1.0 能力确认消费者已部署、生产者未就绪，1.1 与 1.2 对 2.8 请求返回缺版本，实际 2.8 请求拒绝。真实 2.7 响应经 IQS `facts-response` 验证。五个 owner 数据库前后 SHA-256 一致，六个公开命令零出站请求，独立临时捕获已清理。这是贯通原生生产者之前的空库基线。

正式事实使用公开入口启用独立观察库。复制原观察库会把旧 PRE 收据带到新 `store_id`，44 条旧收据在原身份有效，新库会正确拒绝；因此只读复用真实身份、主体、名单和路由，用 `stockwiki.quick_scan_subject_dispatch_cli --operation initialize` 初始化原生 schema 3。原生准备仅登记 `FACT_10`，沿原 StockQA 预算运行。`run-e4966e9be5294168a03ecea72c8055f8` 返回 `answered`、`fact`、空分数。封存原包、StockWiki `imported`、StockQA `delivered`，共一条原观察。执行 1 次 MiMo HTTP、1 次原生搜索。19 条候选由同一观察投影。官方年报验证特斯拉等历史客户披露，[原文](https://static.cninfo.com.cn/finalpage/2022-04-22/1213027750.PDF)。尚未逐条审定这 19 条的持续有效性。

StockWiki 2.7 的真实 Explore 查询、每页 5 条的第二页重开、独立导出快照及再开均通过 IQS `facts-response` 或 `facts-export-response`。改字段复用游标拒绝 `snapshot_query_mismatch`，跨操作快照拒绝 `facts_snapshot_operation_mismatch`。Strict 为 `empty`。读操作前后隔离库和正式 owner 库的 SQLite 摘要一致，查询临时目录清理。薄结果 `runs/f05-real-facts-20261109/fact-query-summary.json`，原回答与数据库留本机。

F05 定向消费者 174 项，补 vendor 1.2 后兼容读取组 101 项，独立 IQS 142 项及 8 子测试通过。StockQA `4c24789` 独立 185 项、相邻 137 项通过，已推主线。StockWiki `93b2592` 本地主线，独立核对首次导入和混合 1.1/1.2 原记录重开，无远端。三个保护场景先红后绿，包括篡改简版事实交付、漏报事实题、真实 vendor 观察被旧查询漏掉。整体测试计数不相加。

E12 `59c1dd5` 和 Dashboard 浏览器实际 `POST /api/v1/commands` 202、接续动作 200。中微原任务 `run-4205968bd06a48edbfd5b3ea1463fe9b` 从未知到成功，原任务的一题已交付，原模型结果 SHA-256 保持 `c748cd4c265cf9023f27802ef40fed28f78ef27af2016026b583856531047cae`。只写隔离命令账本，测试服务未携带模型密钥，`process_started=false`。用户界面的公司级完整总评仍显示未登记。独立 IQS 201 项执行与作业回归和最终 39 项定向通过；Dashboard 后端 45 项及 27 子测试、前端 52 项和静态构建通过。本机证据 `runs/e12-dashboard-closeout-20261109/summary.json`。

最终 IQS 主线接口合跑 **180 项通过**。旧题库版本标签兼容和两条仅核 24 道评分构念的旧路由断言修复后，题库和路由 **77 项及 31 项子测试通过**。宽测试组中，原有双作用域登记曾在第二作用域返回非 JSON；固定两个 owner 的版本后单独重跑原生 **36 题双作用域 1 项通过**，347.44 秒，未再现故障。独立 agent 用原授权账本和隔离 owner 的 SQLite 核对 F05 一次执行、同一条绑定观察与 ACK，并核对 E12 原运行的启动次数仍为一。未把候选关系当作逐条通过金融审查。

Dashboard 保留并行增加的 `beeba6c` 及其父提交，E12 验收代码与隔离部署一致。首次推送因历史范围未获确认被自动审批拒绝。用户于 2026-11-09 明确授权后，逐项核对 `ced8b88..efad14f` 的 119 个提交和 634 个跟踪路径（含生产演练证据），按锁定 SHA 将既有 `origin/main` 非强推快进至 `efad14ff6292924b90a030d8ab87365ca66db8b4`，并以 `git ls-remote` 核对。清单冻结后新增的本地 `main@0dcf61f` 留在本地。本机原清单 `runs/e12-dashboard-closeout-20261109/dashboard-pending-push.txt`。IQS 和 StockQA 已实际推送，StockWiki 无远端。

## 2026-11-09 Dashboard M6 测试包验收与发布

复核 Dashboard `0dcf61f59595ebe4b64d9bd8ea490087ed62f7fd`：父提交为 `efad14f`，改动恰为18个测试/交接文件、零生产代码。隔离定向验证结果：后端 QuickScan+smoke **61 passed、20 subtests passed**；QuickScan 前端 **7 passed**；TypeScript `--noEmit` 通过；synthetic 浏览器 E2E **3 passed**。全量前端测试另有 **75 passed、1 failed**：失败位于并行未提交的 `apps/web/src/shared/capabilities.test.tsx` 旧响应覆盖断言，当前同一工作树的能力缓存实现正在并行修改；它不在 `0dcf61f` 的文件范围内，本次未改动该并行文件。

推送前确认 Dashboard `origin/main` 为父提交 `efad14ff6292924b90a030d8ab87365ca66db8b4`，随后只将 `0dcf61f` 非强推快进推至 `refs/heads/main`。推送后 `git ls-remote origin refs/heads/main` 返回 `0dcf61f59595ebe4b64d9bd8ea490087ed62f7fd`。Dashboard 工作树中的能力/UI相关并行改动未纳入此次推送。E2E 为 synthetic 测试，不代表真实 owner 链验收。

## 2026-11-09 模块边界整改候选

先从反例复现工作台外仓源码依赖、串公司回复、错误 pin、B03 溢出数字、交付映射部分改写和共享引擎穿透 owner 内部状态，再修改公开边界。IQS 查询与刷新 309 项及 53 项子测试通过，`9540ea8` 已推 `master`。StockWiki 公开查询与公司评估 `bf3cf3d` 已快进本地主线，该仓无远端。B03 独立复测 61 项 IQS 和 69 项 StockWiki 通过，包含本机 HTTP 和超过 50 条参考记录后仍能选中正式结果。StockQA 交付、接续和配置 `d5294fb` 已推 `master`，原仓 hooks 全通过。交付初轮 StockQA 196 项及 IQS 216 项通过，随后独立复查发现并关闭 ACK 缺失、串单和汇总状态不一致。最新共享任务与最终保存定向 138 项通过。

真实配置经候选 StockWiki 代码只读查到 215 个实体，宁德时代详情 42 条时间视图记录，五个原 SQLite 文件哈希相同，收费调用为零。原生共享引擎测试发现旧缺陷，答案和交付封存完成后，回执从逐题投影索取 `run_id` 导致失败。修复使用已核对的任务 ID，定向反例红转绿，独立复核通过。原生保存、封存及原响应再用用例复测通过，471.35 秒，测试临时目录已清理。StockQA 内部生命周期候选的组合验证继续进行。

F05 公开边界补丁在冻结的 2.8 副本先发现 33 处私有或间接访问，修复后通过 154 项测试。既有分支 `codex/f05-query-paged-response-01` 已接入公开方言接口并推送 `18a8ad7`，四个定向文件 100 项通过。根目录原有 2.8 改动保持原样。原冻结材料见 `runs/query-facts-public-ports-20261109/`。在更新后的根目录可用 `git apply --check --exclude=tests/test_vendor_subject_dispatch.py` 检查该补丁的源码部分，测试边界按新版与分支合并。

Windows 新检出曾改变发布题库的原始字节，导致编译前的档案哈希检查失败。逐一对照原发布锁确认 48 个 3.0.0 归档为 CRLF，3 个后续归档及 5 个路由策略保留 Git 字节。IQS `7321e71` 已推送。最新归档规则实测两种 `core.autocrlf` 设置的 56 个文件均符合发布哈希。Dashboard 的公司实体核对及任务协议解析在独立分支 `codex/iqs-public-reply-boundary-20261109` 的 `b1aca35` 已推送。65 项测试和 33 项子测试通过，独立 agent 已验证主要协议反例。Dashboard 原主线按其 D00 归属并线。

StockWiki 扫描准备、原生路由快照及请求局部委托 `c2c65c6` 已并入本地主线。公开准备与路由定向 23 项通过，独立复测覆盖 7 个正反例。旧委托文件内容保持不变，新增 stdin 模式仍检查原 OS 身份、预览摘要、范围、到期和不可变授权记录。旧日期夹具修正后 56 项通过。原生准备单题用例通过。完整 36 题按实体 33 与证券 3 登记，当前路由变化后继续用原题库，以及发行人补建作用域后的双范围登记，两项全链用例通过，1377.81 秒。隔离测试目录已清理。

StockQA 原生生命周期 `7eebaae` 已推 `master`。作者定向 121 项、独立生命周期 33 项通过。新版任务工厂只拿到受限端口，旧版工厂兼容，明确声明未知版本时在调用前拒绝。现代原生入口的短证据、保存封存及零重发复用用例通过，536.79 秒，测试临时目录清理。旧十二题冷恢复曾复现已付诊断被发布口径误拒。未评分且无引文的原诊断可在研究阶段恢复，正式发布仍要求已核来源和原生分数类型。独立定向 12 项通过。最终两进程复测 1 项通过，638.44 秒。首次仅一笔脚本模型响应，保存后进程退出，第二进程从原回执恢复全部 12 题，新增请求为零，临时目录已清理。

集成层独立 agent 核对了本机实际配置与两个所有者的公开命令，27 项边界测试通过。正式配置只读复测仍返回 215 个实体及宁德时代 42 条时间视图记录，五个 SQLite 文件摘要均一致。隔离合跑曾有 305 项通过和一个 HTTP 夹具失败，原标准库监听器启动时触发了反向 DNS。复用已有字面本机地址夹具，保留测试运行器的 DNS 拒绝规则，最终合跑 **339 项通过**，142.11 秒，测试目录已清理。IQS 主实现 `25dc299` 已推 `master`，提交范围排除八个在途 2.8 相关已跟踪文件及新增 2.8 schema。下一步并线范围见计划。

执行顺序见 [task_plan.md](task_plan.md)。早期完整日志保存在[历史原件](docs/implementation/archive/pwf-through-2026-10-31/README.md)，其中的状态按当时记录解释。

## 2026-11-07 OWNERPKG-INVEST-QUICK-SCAN-01 job façade施工包（分支交付，未并线）

交付于独立worktree分支 `codex/iqs-job-facade-01`（基线 `fb0a254`，head `23d20b8`）；本主线PWF此节为§8-3-2交接登记，分支上另有一份逐G条目详细progress（并线时随分支带入）。摘要：Dashboard命令→既有ExecutionGateway.start授权链的公共job面（HTTP四路由+iqs-job/1 CLI+语义契约文档），durable命令账本/12字段JobView投影/命令级幂等/有界JobPage/深链绑定。定向40项通过；§8-1独立重审两轮后 0 OPEN P1/P2/P3；真实formal付费演练=NR-1 NOT_RUN（红线§3-1待操作者预算确认）。基线先存失败登记：test_dashboard_execution.py 32项与 test_dashboard_unusable_recovery.py 1项在本主线（无本包）同样失败。交接文件：分支 `planning/iqs-job-facade-01/handoff.md`/`handoff.json`；Dashboard消费候选commit `4d420a0bb524da886db85ad344c67721e3d5de5e`。

## 11/02 模块解耦 D1–D7 整改

按原审计优先修复分类结果误拒和服务锁阻塞，随后收口 Company 恢复、原题库和请求规则、UI 启动与比较、任务活动和 StockQA 只读投影。独立对抗审查复现并关闭原发布根、规则漂移、损坏异常被包装、迟到数据重绘草稿及慢构建阻塞等相邻问题。原服务195项，交付投影15项，跨仓结果119项及42子用例，历史独审72项和最终尾测135项，原UI 228项（6跳过）。三种原出题格式的6份产物逐字节一致。StockQA 默认306项及原静态检查通过。范围、提交与实际CI见[整改报告](docs/implementation/reviews/DECOUPLING-2026-11-02/remediation.md)。隔离临时环境清理，收费API为0。

原生准备另通过 3 项，1403.81 秒。原单题、36 题登记和路由变动后精确复用原 36 个工作 ID 均验证。此组是本节点原生验收。StockQA `01f20d6` 远端 CI 41532137887 已核实成功，UI `46f86d5` 与 Company `d0280f5` 已本地提交。

## 11/02 模块解耦核查（整改前记录）

用户要求全面核查。主控与三名独立agent分别审题库/契约、核心恢复、跨仓与UI，当前scripts123文件/194静态内部边无非平凡SCC；动态加载不在此无环证明内。确认7组耦合：分类结果复制供应商/回执字段造成实际误拒；慢POST占总锁阻塞GET；静态快照绑全站启动；Company私有恢复及QA私有策略接口；旧任务/题包依赖当前schema与源码文本；比较页复制必答规则；产品服务窥组件字段/文件布局。详见[总报告](docs/implementation/reviews/DECOUPLING-2026-11-02/report.md)。正确的纯域、唯一事务owner、隔离子进程和组件注入边界保留，不因报告新增平台或门禁。

本轮只读产品源码/状态，四文件离线34P、39子测试/15.59秒；真实standard-1 manifest仅在内存修改getsource注释即可复现历史拒绝，再还原可通过。独立agent另有供应商/可选字段、慢命令并发、坏versions、必答扩展和schema升级反例。首次测试包装器误拦本机gethostname、之后长TEMP复制失败均为测试环境问题；修正到短C:/Temp后全过。自有TEMP清理、0API、未改真实配置/库/名单或外仓源码。保留其他writer改动；此前功能/远端CI签收不改签为架构全解耦。

## 11/02 远端CI连续失败根修完成

亲读StockQA三代实际GitHub日志：black/isort/mypy过、Bandit3处B608阻断pytest。源改固定SQL/绑定JSON列表或固定UNION ALL，不加nosec/关规则；新增实际SQLite11例并入既有daily包。完整default随后实际5F/286P揭露陈旧同值重复负例4项和默认预算绑定未捕获请求指纹导致公开正文落盘失败1项。改真冲突负例+同值CP正例，任何原work/pack/budget绑定共用自动hash，sync/async默认均实际post/journal/费用一次通过，未绑定legacy保持。实现ee8f49a正常hooks过已推；完整default305P/54.73秒（总105.10秒）、非作者SQL/native27P/38.03秒及小尾32P/11.07秒，重叠不加总。

ee8f49a真实远端CI41522697950通过302P/3个Windows cmd平台skip/33.78秒；同提交Documentation失败源于Python3.10解析mkdocstrings1.0.6+pymdown12.3接口不兼容。按上游及官方PyPI核不抬Python基线，pyproject docs5项与原lock固定兼容组合，修复0154726两文件正常hooks过已推。全新自有TEMPvenv安装+pipcheck+Highlighter+完整离线MkDocs11.65秒通过（wrapper109.56秒），API HTML存在；本机3.13不代签3.10。非作者核源码/实际日志与依赖兼容通过，无开放问题。

**最终远端亲核：** 0154726的CI41523660779、Documentation41523660825均completed/success；文档Build及Deploy to GitHub Pages两job均success，实际工作流Python3.10。旧红记录保留，不重跑旧提交伪改历史。详情/链接见[CI根修报告](docs/implementation/reviews/CI-ROOT-CAUSE-2026-11-02/report.md)。先前只核hooks/推送而未追远端是本线程遗漏，README和交接已纠正；不增加hook或新凭证。

所有测试用自有隔离源码副本、去密钥；实际pip安装仅官方依赖，venv/下载和构建文件结束清理，无真实公司文件或收费API/生产DB/配置变动。首guard误阻Windows socketpair后只允许loopback；首组件copy漏IQS纯合同依赖后独立27例覆盖，不算产品失败。IQS本轮仅PWF/报告/交接，原独立README及其他仓活动writer保留。回根Next Step既有主线。

## 11/02 保存—补封—入库—回执完整链路再复查完成

根修5组：补封limit被旧匹配ready/不可修复项占用而后项饥饿；共享固定staging/直接checkpoint写的中断窗口；迟到worker复活终态与全entry确认后本地标记中断；远端stored ACK被缺release/cache阻挡；派生内容地址缓存半截不能重建。沿原Store有限ID快照、原codec原子发布、原接收库/StockQA ACK逐项验证和原字节缓存修复，不加调度器/许可/数据库或核查回执。实现IQSe24c359（8文件）、QA4cffabc（4文件），均已推原origin，QA正常hooks过。

作者QA61P/25.77秒、共享3模块36P/16.86秒，错误类型收窄后新4P/1.67秒；IQS jobs30P/2.80秒、最终相关focused48P/43.07秒。非作者fullchain_peer QA19P/12.54秒、root5P/1.61秒另真实os._exit、IQS主链40P与最终archive10P/1.75秒，最终无开放阻断。组间有重叠不加总，不冒称最终94全模块跑过。AppContainer3项hardlink权限错误在授权C:/Temp重跑全过；新增fsync mock和无效CLI参数的fixture错误已修，不当产品RED或放宽产品规则。

原SDK五组件两个新冷进程1P/323.82秒（runner325.38），副本生产源码与最终提交字节相同，去密钥并删除当天model/budget配置后恢复原回答/CP，未问项仍缺；0新API，TEMP已自动删。vendor wire脚本化，不是新真实公司内容测试。storedACK定向正反/重复使用原SQLite/原验证器，远端读取为明确port，不冒称本轮重跑真实StockWiki服务。所有自有TEMP均清理，真实库/名单未写。

原UI确认37任务exited/stopped及0在途后精确重载，doctor ready，新旧观察可读，原配置hash相同；账本仍87HTTP/2053896micros、0在途/未结。详情/命令/局限见[本轮全链整改](docs/implementation/reviews/GATE-SIMPLIFY-2026-11-02/full-chain-restart-remediation.md)。本节点完成，回根Next Step，不重问gen7、不扩支线。

## 11/02 保存、补封、入库接续复查及整改完成

实际发现并修复：旧diagnostic路径提前阻DBjournal恢复；公共batch typed补封中断/旧ready错判当前目标；job.resume重复全entry预检；cached引用误计待入库包；ACK坏/缺成员阻合法回执。保存/目标封包/ACK分层，局部问题仅保本项，原receiver/绑定/全局权限仍保留。QAe5a2781正常hooks过并推原origin，IQS源码d7ec166由总控集中提交（10代码/测试文件），StockWiki/Company/UIlab未写。

作者QA15P/31.48秒、IQS最终相关五模块123P/308.20秒；非作者QA12P/34.92秒、IQS22P/180.90秒均过，分组重叠不加总。原SDK五组件禁网冷E2E1P/419.97秒，两新进程删除当日model/budget且无key时恢复原CP/响应，0新API，自有副本清理。core wire脚本化，非金融证明。QA4F3P、resume3F、cached2F及ACK4F原反例均有效；AppContainer长路径、测试辅助漏API_requests信封等setup问题已在短TEMP/合法fixture修正，不算产品RED。peer首logger句柄延迟清理已进程退出后精确核实删除；root/author其他自有TEMP均自动清。

未扩任意getter typed防御（核源码后撤回候选），不加许可或新回执体系。原服务精确重载，ledger仍87HTTP/2053896micros、0在途/未结，配置与旧答保持。新结果status按实际持久化且符合原目标的包，不用错误日志作完成门。详见[本轮范围/命令/局限](docs/implementation/reviews/GATE-SIMPLIFY-2026-11-02/persistence-chain-remediation.md)，回根Next Step既有主线。

## 11/02 三个问题的相邻复查及整改完成

**保存/补封/入库接续的新一轮独立检查进行中：** 仅沿本链查相邻状态，不扩日期或模型研究。QA核原journal恢复是否仍被无关旧diagnostic路径及批量补封边界阻断；IQS核多entry交付job恢复是否存在重复全范围预检。候选以实际复现为准，真实库/名单/收费API均未动；由非作者peer_persistence_chain在最终代码上集中审查，当前尚未签本轮完成。

新独立agent发现：普通/共享单题补封冲突会阻后项，实际成功后的诊断可能误报pending，已有CP快捷路径漏原绑定；期间只有end判断漏未来start/倒序，以及父forecast给未知日期子指标回填造成误拒。沿原单题工作边界、实际持久化状态及共用期间语义修复，无新许可/平台/收费调用。实现IQS7a241ba、QA9b66f10已推原origin、Company639582a本地无remote。

作者root最终139P+8subtests/13.95秒，逐题delivery fixture尾8P/1.34秒；Company75例，QA87P/136.93秒及成功后诊断尾2P/5.63秒。非作者终审Company56、root65P/1.56秒、QA28P/32.60秒，无开放阻断；重叠不累加。去密钥禁网，自有TEMP均清理。根共享先6个typed反例RED；旧测试缺claim与新finding字段读取的fixture问题已修，不放宽产品规则。未跑小时全套或不覆盖本节点的旧单包长E2E。

原服务核PID/创建时间/argv且无任务子进程、0在途后精确重载；配置不改，原账本87HTTP/2053896micros。操作与局限见[相邻整改](docs/implementation/reviews/GATE-SIMPLIFY-2026-11-02/adjacent-remediation.md)，不能据此宣称金融内容/规模已完成。回根Next Step既有主线。

## 11/02 三个残留整改完成

**相邻场景复查/直接整改正在进行：** 新独立agent发现保存后的逐题补封中断，以及缺结束日的实际值未来起点/倒序、父forecast总览回填未知子指标日期等相邻遗漏；沿原单题边界及共用期间判断修复。Company639582a已独审本地提交；总控共享finalizer先6个typed冲突RED后修逐题handle/commit/已保存但未封分开，并以实际已持久化状态决定完成度，诊断错误本身不作门。QA正同步补封与期间端点测试，最终节点未收口。不加许可或收费调用。

按work/physicalpack隔离恢复范围与局部错误，remaining按wanted减实际saved求差；未发送/未知仍不派发，坏包不伪造CP。Company用统一指标遍历修nested引用/alias/自审，并让forward输出期间独立于历史输入。实现QA79746de、Company2f3718e；IQS入口回归9b62b7f。

作者QA55P/99.72秒、typed尾4P/18.52秒及含同包中间成员的6P/16.85秒（重叠）；Company50P/0.95秒；IQS74P+8subtests/21.12秒。独审Company/生产入口29例、QA19P/44.27秒及typed尾4P/11.51秒、最终member尾2P/5.05秒，无开放阻断；互相重叠不加总。去密钥禁网、自有TEMP清理，QA正常hooks未skip。新第二包fixture初漏subject dispatch和原假时钟，已用原API及正确时点修fixture，未放宽生产证明；文档首patch未命中原文，读取定位后更正，无产品影响。没有跑小时全套或新付费实验。

原doctor ready，账本仍87HTTP/2053896micros、0在途/未结。真实库、普通配置及原回答保持；[完整范围与局限](docs/implementation/reviews/GATE-SIMPLIFY-2026-11-02/three-residuals-remediation.md)。回根计划原内容/事实主线，不新发卡或新增门禁。

## 11/02 实施后独立复核

**三个残留的后续整改已启动：** QA按原work/物理包隔离恢复候选，Company共用输入/输出期间及嵌套指标遍历，总控补IQS实际语义入口的预测/嵌套引用一致性测试；独立review_three_residuals集中审查。IQS新增及原共享语义模块31P/2.63秒，TEMP已清理。当前仅此部分验证通过，未先签其他整改完成，无新收费API。

由三名新独立agent核恢复、内容和运行/审查门；原39P/43.22秒与19P短模块通过，自有TEMP均清理。总控重跑原反例均绿，并亲复现历史基数forward年份误拒。另scope混入claimed但无attempt的未发送题使原完整3题paid包CP0，独立真实SQLite/parser组件反例已确认；不冒称真实owner事故。Company嵌套item metric证据缺失在独立组件被接受，生产IQS会拒，属于一致性缺口。详见[本次独检](docs/implementation/reviews/GATE-SIMPLIFY-2026-11-02/post-implementation-independent-check.md)。

本轮只检查并纠正文档，未改产品或收费调用；doctor ready，账本仍87HTTP/2053896micros、0在途/未结。现行B01/V18逐断言/逐文件清理残留已删，手册lease范围澄清，任务卡数/行为范围不变。最新开放项覆盖下方有界终验的外推，不撤销其原通过实例。

## 11/02 收敛实施完成

普通/共享已付公开正文复用原SQLite journal，写入与receipt/费用同事务；normal/replay共用成员解释、逐成员事务。Company按题处理缺/坏/重复回答，共用binding_findings处理跨期与预测。IQS/QA兼容读规则有一致性测试，旧schema不改，资料日与预测期间分别核验。实现IQS209d9dc、QA9648aef已推原origin、Company0af8902无remote本地提交。

作者IQS最终72P+8subtests/12.49秒；Company94P/4.97秒及补事实21条后新模块10P；QA70P/51.14秒。非作者Company19P、QA35P/48.37秒与预测尾4P/0.93秒均过，集中独审无开放阻断。测试有重叠不加总。冷CLI原五仓隔离1P/206.91秒、两个新进程在无当日模型/预算配置下保原CP/响应，0API、TEMP removed；副本早于QA预测尾修，该尾项由独立4P覆盖，不混称同次全链。既有schema迁移测试陈旧fixture已修，不改生产迁移逻辑；QA正常hooks含101源码mypy通过，未skip。所有自有TEMP已清理。

上轮原内容反例总控亲跑现均通过；原UI重载只核验精确PID/创建时间/argv，未改配置或重新问模型。真实账本仍87HTTP/2053896micros、0在途/未结。详情及局限见[本节点实施](docs/implementation/reviews/GATE-SIMPLIFY-2026-11-02/implementation-convergence.md)。这是软件范围完成，金融内容、规模/事实/消费者仍按根计划推进，无新施工包或门禁。

## 11/02 效果复核与整体收敛判断（审查完成，新增问题待修）

**后续实施已启动：** 用户要求按收敛方案直接修复。QA单writer统一原公开响应journal及普通逐题恢复，Company单writer统一槽/语义校验，总控负责IQS兼容读、跨层验证与PWF。独立review_convergence同步核设计并在最终代码上审查。IQS首轮相关测试72P+8subtests/14.93秒，自有TEMP已清理；其他部分仍实施中，尚未签完成，不新增收费请求。

按用户要求重新核原UI、Git、代码和证据，并由三个独立agent分别核恢复、内容和整体结构。原doctor就绪、新旧gen6/gen7观察均可读，原响应hash/普通配置不变，账本仍87HTTP/2053896micros、0在途/未结。IQS相关3模块69P+5subtests/34.76秒；QA原3模块独立28P/31.97秒，自有TEMP清理、禁网去密钥。CodeGraph命中历史副本/外仓索引滞后后读取已知实际源；外仓Git初次沙箱只读拒绝后升级只读完成，没有改代码。

新增实证：普通pack恢复2有效/1missing仍全拒且CP0；共享同HTTP2题只答1题因可选声明推断而全拒；合法同比跨年引用误拒；明确forward计划需固定文字前缀；单位说明80字及事实items20上限仍整答拒。总控亲跑内容四组与事实20/21边界，正常对照均成立。上轮paid1/未问1是pack_size1，不能代替同HTTP半包测试。普通pack公开正文默认仍可选capture，本机已enabled，不夸大成真实丢失事故。

只更新PWF、交接及[效果复核](docs/implementation/reviews/GATE-SIMPLIFY-2026-11-02/effectiveness-and-convergence.md)，没有改产品或收费调用；新问题未标完成。修正findings旧gen7 CP0/顺位待补及交接旧版本表。StockWiki期间HEAD由9e8e308变f52f257，视为活动writer，不作全仓新签收。下一主线按原任务收敛公开响应持久化、逐题解释及保存/质量/比较边界，无新施工包或审查凭证。

## 11/02 再次清理过度门禁（已完成）

**本节最终终态覆盖下方实施快照：** 通用门禁/单位自审/短证据singleton codec已全部根修并集中独审。原UI第6次launch零API恢复gen7成功exit0，CP `CHECKPOINT_1c5c5d9766b34ddcab8317ac34256b31`；交付job`deliveryjob_03aeb32cc6f07b1525d3a147fb893cc0` completed，原work delivered、11:00:20Z accepted ACK `ack_fd86eacd8b792b505a582f13`。原响应hash/score8/实际mimo-v2.6-pro/原完成时间23:44:40.990609Z保持，原新旧观察在公司详情公开接口并存。总账仍87HTTP/2053896micros，0在途/未结；原普通配置字节hash相同、60包保持、doctor ready。不得再按11/01 CP0/leased或本节早期失败快照重发。

单位/state尾修118P、非作者89P；singleton共享codec54P、独立新旧hash和8篡改负例过；原冷公开CLI1P/298.03秒及各相关组详见[终验报告](docs/implementation/reviews/GATE-SIMPLIFY-2026-11-02/report.md)。没有重写原答或授金融准确性，分红/利润归属等原内容限制仍保留。QA正常hooks已过并推e2850bd；IQS实现79b94ce，Company360c7df、SW e5a1be6、UI fa7ceb6已本地提交。PWF/交接本次统一收口，回既有内容质量主线。


本轮原owner冷公开CLI最终1P/298.03秒，删今天budget/model后冷进程重复恢复paid1/未问1、原CP/响应不变、0新增HTTP；自有副本已清。集中非作者审查root/A54P、B15P与C尾部均过；QA正常hooks通过后6eecce7已推origin/master，IQS实现79b94ce已本地提交；SW e5a1be6、Company 937454b、UI fa7ceb6本地提交（无远端）。随后原UI真实gen7零APIseal实际发现thousand/千元人民币及派生比率纯文本单位误拒，最后同因校验/自审修复在进行，不提前签CP/ACK。原普通配置与87HTTP/US$2.053896、原响应保持。


集中回归已实际通过root边界260P/55.44秒、后续部分导出99P/15.11秒（有重叠不累加），内容域421P含1平台junction skip，dashboard阶段262P和DOM56P后仍在收最后独审反例。新原公开CLI冷启动实验首轮是fresh夹具遗漏模型配置，第二轮实际揭露StockWiki历史委托仍读今天预算文件；已补原记录有效RED并仅改原预算hash读取，不绕当前OS账户/consumer/撤销检查。曾拟放宽这些访问边界被自动审批拒绝，未执行；采用保留访问校验的更安全替代。本机0新增收费、0生产数据写，冷实验最终版及独审未完成时不提前记通过。


用户再次要求全面核查并清除。已读现行PWF、Git与原真实/隔离报告；CodeGraph root search命中历史副本，QA指定project search无结果，后续读取已知源，不反复查旧索引。仅保留外来10/10 README未提交改动。三名已授权agent分别只读核：QA已付依赖/partial；UI/导出/StockWiki逐item；内容格式与命名。已复现预算文件变化令read_registered recovery idempotency_conflict、同一已付Q1旁边未问Q2导致整批paid_required；其他明确候选为旧1.4/1.5 control时效泄漏、seal全bundle fingerprint、outbox导出依赖今日budget/inspect、部分导入all-can_apply与analysis文本/未知metric_id。均尚未签修复或生产恢复，无收费/原库写入。


## 11/02 四组整改完成（原软件范围）

**最终终态：** 四组已按原软件范围闭合、独审通过。新增safe无CP→无当天模型配置的paid-only零发送恢复/原hydrate/普通owner冷重建E2E1P/656.77秒（总runner661.77秒），TEMP五仓副本移除，0收费。最终peer亲读log/最终测试及28P尾项，无未解阻断。该例仅脚本化vendor wire，复用已有client，不授真实供应商/全新进程keyless SDK/ACK/UI三市场资格。IQS代码e20e1b5与前段d168425/da0fbd5、QA58fb6ce（此前d1d22cc）已推各自origin；SW dc857a5/UI77d372c无remote，本地提交。正常hooks曾自动修行尾/Black，精确重暂存后全部通过，未跳过。原服务精确核无子任务后按旧参数隐藏重载，GET doctor ready/阻塞空，main实际store.js 200含新逻辑；配置60包/原普通参数保持。重载后账本仍87HTTP/2053896micros、0在途/未结，gen6 delivered/CP1、gen7 leased/CP0不变。参见[最终结果](docs/implementation/reviews/CODE-QUALITY-2026-11-01/remediation-2026-11-02.md)。以下保留同日各阶段过程，待验/正在运行仅是当时快照，不能覆盖本终态。

按用户最新要求实施原5/8/9/10。第一阶段QA能力与公开薄接口已独审通过并正常提交推送d1d22cc（原8文件精确范围）；有效RED4F，相关124P/4.47秒、非作者93P/4.51秒及原transport28种输入/上下文返回/异常一致。hooks首轮isort改两文件后精确重暂存，重试全部通过含mypy/secrets。研究通道由原SDK单一纯能力函数与constructor共用，普通搜索不冒称native研究可用；tools16k/final_json32k保留。公开context/transport/validation供原engine复用，不复制规则、不新权限。

主控IQS生产private边界有效RED2F后改接公开seam，含原1.5 task验证的私有穿透一并收口；相关71P/2.56秒，独立公开/旧工具最终81P/8.70秒（重叠不加总）。语义单位fixture刻意无QA私有字段。旧工具原6F及HTML缺失1F已修，原17P；独审追加实际CLI相对路径错位RED后，主控resolve caller四路径，新增真实CLI回归至18P/7.00秒。两次包装器导入错误/Windows父进程chdir阻止TEMP删除已纠正，不冒作产品失败；所有本轮自有TEMP确认移除。

UI嵌套容器及未知正文尾项经实际ESM有效RED5F后修复，作者37P/51子测试，非作者最终7P/16子测试，五个实际页面反例均无crash/假无记录，必需bank损坏与原子load保留。UI精确7文件正常提交77d372c，无remote未造远端。IQS公开边界/旧工具精确8文件正常提交并推送d168425，外来README/其他未跟踪保留；QA d1d22cc已推送。

共享顺位仍实施中：IQS新1.6有效RED6F/1P后原合同组51P；SW原W06多模型组合/preview/权限/CLI已冻结，作者53P及原permission7P，非作者SW+IQS合同105P/17.79秒，额外SQLite8反例验证active/unknown优先及fallback原模型/时间与TTL边界；原SQLite bytes均不变。只签规划/contract范围，不冒签真实共享fallback整链。QA正在补1.6 inspector/consent/binding5，主控接原SDK共享控制器/原lease/预算；UI准备仅显式1.6启用targets，旧请求/comparison/paid恢复不放大。未调用收费API或改生产库；原gen7 raw/safe/CP不变。

顺位阶段增量：IQS1.6四文件已独审提交推送da0fbd5；SW六文件dc857a5正常hooks通过，本仓无远端。准备1.6四文件作者23P/248.26秒（含原36题双scope/重放、恢复和比较），非作者新16P；原沙箱PermissionError在外层同一隔离环境消失，没有改产品绕过。根主控新增原Store只读物理计数有效RED1F→10P；binding5已结拒绝原lease接续有效RED1F后与原组48P。原预算事务内检查总scope请求上限，物理pack DISTINCT计一次，跨重启不归零；原route单调CAS阻止并发重发已拒模型。新增过期epoch、未结拒绝、并发不同work争1个cap及2题pack计1次通过。组合117例116P/1F（94.32秒），唯一失败是旧v16夹具漏删24/未还原25 CHECK，复用原历史helper修后定点1P；不是新迁移DDL。本轮没有新增表或schema版本。

独审预读提出已付fallback任务根、unsent顺位、原scope顺序与cap来源，主控已纳入修复：原1.6按批准scope固定顺序，已收答优先原route零发送恢复，任务limits固定且原预算原子检查。尚待完整两模型原owner/SDK scripted-wire E2E与集中终审，不预报整组闭合。一次sandbox测试包装器无child/TEMP卡启动，经精确PID核对停止，外层9P；未计有效RED。root初版staticmethod self错误已定向修正，不冒作历史产品错误。

最终同节点验证增量：root公共/entry/route投影110P/4.86秒；授权新25P及原216P/125.48秒，非作者consent策略漂移等7新增反例合32P/5.14秒。共享执行非作者79P/6.38秒；已付尾修又28P/6.53秒，属于重叠组不累加。首次唯一两模型原owner/SDK E2E1P/491.08秒（两题pack2，a401→b两CP、原outbox ready、原owner冷重建0HTTP），五仓自有副本自动删除；不是真实供应商/金融/ACK或三市场新验收。新增safe尚无CP中断→keyless paid恢复/原hydrate最终E2E正在运行，等真实结果，不借前一次通过冒签。

正常QA commit首轮停于isort格式与2个Optional类型问题，另因部分暂存stash导致未跟踪新routes引用旧shared的6个假错；未绕hooks。root修真实类型问题、将耦合执行接线最终一起提交，现all-files原mypy通过。探针第一轮编码别名/字段/doctor路径错误已纠正，最终公开GET /api/product/doctor ready、blocked空；普通1.1 successful_scan24h、pack2/thinking/max32768/shared/refs为空、execution_bundles60。原账本只读87HTTP/2053896micros、inflight/未结0；gen6 delivered/CP1、gen7 leased epoch2/CP0保持，未收费或写生产库。

## 11/02 整改清单逐子项核对

用户要求原整改一个不漏地核对。主控亲读原报告1—10、实际实现和测试，三名非对应作者交叉查源；复读原124P/154P、两份原owner/SDK E2E及独立尾修日志，按子项区分软件、真实金融与产品范围。完整表见[checklist](docs/implementation/reviews/CODE-QUALITY-2026-11-01/checklist-2026-11-02.md)。原10组有6组按原软件要求闭合，5/8/9/10仍部分完成；此前“整改已完成”表述过宽，已同步根计划、发现、交接和原报告，不改签历史测试或旧原件。

实际遗漏：5后端草稿故障已隔离但UI store启动Promise.all仍要求answers正常，坏JSON/坏结构令main在connect/router前退出；8普通web_search能力被误当研究native final_json能力，OpenAI capability声明true但真实研究构造拒；共享fallback仍未接。9公开task/snapshot/delivery/import环已完成，但生产engine仍读私有context/transport及_assert_registered_inputs。10 one_click未给provenance传两库，仍读旧Alphabet/10月实验；financial_mechanical_check接受--html但不生成，旧入口却链接它；固定10/18 preflight也未标历史。低优先额外限制：旧rubric补同义critical字段聚合不变，但same-method升级仍按原dict差异要求新method_id；旧读取与原风险修复通过，不扩大成当前UI门。

主控纯内存SDK构造探针0HTTP重复确认能力误报；独审直接import实际UI store并mock fetch，合法runs成功、坏JSON/answers数组/runs对象均拒，未改源文件或生产草稿。指标/元数据定向20P/32.07秒（本次工具结果，无独立文件日志），自有C:/Temp/iqs-audit67-*已自动清理，去密钥/禁自动插件/禁pycache；包装器没有额外禁socket，不能称网络隔离经拦截证实，所选测试没有调用模型/搜索/服务。选择为MetricCoordinatesTests、新critical/旧rubric、新diagnostic、三行业route及QA三项实际标准验证。NEW-6再内存核5scope和6条实际TS/JS深链均精确解析，不替代D00/E07/浏览器。

另一个UI/旧工具13函数定向pytest尝试没有得到有效收集/断言输出，已停止，**不报通过**，自有TEMP无遗留；改以实际Node反例、当前源码和已存在针对性测试核对，不能拿旧154P执行模块证明前端boot已测。未再跑小时全套。前次未定位AppContainer临时目录的清理限制保留，原报告全清措辞已收窄。

本次只读原账本仍87HTTP/2053896micros、0在途/未结，gen6 delivered/CP1，gen7 leased/response_available/CP0；无新收费/配置/观察库写入。源版本与工作树已核，原UI实际仓是iqs-question-bank-ui-lab 8fc9072。QA/SW沙箱git status曾误报非worktree，外层只读核实干净；不回滚并发writer。根10/10 README保持。

## 11/01 接续与 Dashboard NEW-6

**本节后续终态（23:54Z）：** 第三段原请求已返回，23:44:57Z进程退出，原safe/receipt保存成功；仅新增1模型HTTP、29033micros（US$0.029033）。原账本87HTTP/2053896micros、in_flight=0/unsettled=0，work仍leased/epoch2、attempt=response_available、CP=None；不得写已入库、active=0或新缓存通过。普通原policy11及prepare已精确恢复，doctor ready/无阻塞、pack2/thinking/max32768/shared=null/refs=null，全部60包保留。后文“第三段待终态/临时配置/86HTTP”为先前执行快照，由此覆盖。

非作者从原pre-send checkpoint和实际SDK纯构造重建HTTP JSON，hash与原research_intent的`36568c62…`精确相同；2554字节board/hash`fdcb5d…`包含2024/2025两条原短证据、原URL/hash及published_at:null。真实request thinking enabled/max32768/json_object，不保存完整上下文或中间思考。证明证据实送，不只配置存在。原gen6的provider attempt/receipt/response/CP payload四hash仍等于初始原快照。

真实回答审查：两年CFO/购建现金/代理FCF及同年算术与官方原表一致；2024为658.10402亿元、2025为908.75424亿元，改善了旧跨年错误。仍有CFO合并总额/归母利润归属范围差、优先用了每股截尾推算分红而非原披露总额、2.88倍只覆盖末期方案（全年分配约2.52倍）、3月“尚待股东会审议”未核后来状态等内容限制；不能称整答金融全对或所有者收益已算明白。原答/分数不改。

该回答未保存CP的确切原因经独立纯内存重放为`unknown metric must use custom namespace`：模型用了`financial.fcf_2024/2025`，原registry要求同一`financial.fcf`用各自period字段分年。只在内存临时映射这两个ID后标准内容层通过，未改safe/库，亦未据此宣称来源闭包或整条入库通过。原slot保持invalid/answer_semantic_contract_rejected；不能伪成transport未知、重发收费或把当前分数8当改进依据。只读评估确认完整canonical投影牵涉Runner不改输入/原safe exact-match及非pending已付重处理合同，不能顺手改parser补绿；本轮不扩建协议、不以这个invalid样本阻塞后续原共享顺位开发，不造本公司特例。

本组软件提交：IQS `db0b432`与StockQA `2e4f01b`均已推既有origin/master；Runtime Lab `5839ef4`本地原分支、无远端。QA正常hooks全部通过，无绕过；保留IQS外来10/10 README。以下保留真实前后顺序，不改写早期失败。

非作者最终再次只读核普通prepare与备份对象相等、owner policy原字节相等、gen6四hash及gen7receipt/response/safe三hash不变；6份当前文档无CP/ACK/金融误签。3处措辞（付费测试历史、早间gen6缓存标记、cap1与counter0→1）已顺手修正。原UI本次仅核状态，显示leased逻辑工作在途1，不代表供应商HTTP仍在途；画面在忽略目录`runs/quality-context-retest-2026-11-01/ui-terminal-state.png`。未再次收费或写观察库。

亲读外包B03最终交接及原独审报告，另派未参与实现agent复测最终Dashboard代码e7ce9ae（文档HEAD edd964b）/service3eb99cd/UI6f0391e/SWb3084ff。5类scope判断、6条实际UI模块深链均通过，原StockWiki32P/11.28秒覆盖run/scan引用与缺run拒绝；0收费/0服务/0生产写，自有TEMP移除。[定点结论](docs/implementation/reviews/DASHBOARD-NEW6-2026-11-01.md)不代签E07、浏览器或D00并线，也未把外包owner authority合入本仓。

本次原8766最初停止：sandbox网络Win10013，外层只读确认10061无监听后才启动原no-refresh配置，未杀其他PID；新launcher18544为当时记录。doctor ready/无阻断、账本仍86HTTP/2024863micros且0在途/未结/unknown。只读核原gen6真实回答：明确原数不足，未继续断言错误FCF，旧板仍空，不能追认为短证据实送。

继续原质量节点：仅在线核公司原2025年报合并现金流量表2024/2025原数，不下载保存文档；原CLI派生gen6→7 comparison与两条原短证据，独立run目录`runs/quality-context-retest-2026-11-01/`，原owner临时policy11→12/1.3（TTL/预算不变）。原决议`owd1_0e16517c7b2dc2d8513a6743b18508b99638ab99c269e35eed43e4feedfcc294`已confirmed/recorded；原UI准备job`prepjob_f2edee1be7f94e2eac7b836ef6108276`已登记，60个原包保持，新冻结shared配置与两条原记录逐对象相等。23:00:19Z开始`run-5a03133643e34e60b69d6b9b311b46c0`，batch`batch-a4a0514b51f04d9fa048f266500a7ec2`，只选一个公司组/一题、pack1/thinking/max32768/request cap1；不是重复gen6已付恢复。开始后原账本尚86HTTP，终态另记，不预先宣称金融准确通过。完成或安全失败后须恢复普通prepare/policy11并保留60包与新历史。

独审预执行发现的wrapper DTO读取已在执行前按`applied.decision.decision_id`更正；恢复脚本补仅覆盖本次仍相等的prepare，避免覆盖并发writer。检查冻结配置时最初误要求路径仍指private源文件而assert失败，实际原准备按契约复制为冻结配置；已比较实际JSON与预期完全相等，没有改产品规则求绿。

真实首段在SDK研究会话构造报`research_limits_invalid`（原共享/Runtime已32k，实际ResearchChatSession仍硬限16k），0新API/费用却先claim了gen7。已有效SDK RED2F/7P→完整40P/6.13秒；生产final_json沿原SDK32k应用上限，旧tools16k保持；Runtime构造/控件校验前置于generation_scope，实际step仍当前owner/budget/send guard内，RED2F/7P→9P。原Store新增精确Lease的release_unsent；独审13P后将真实`WORK_ef7cfb7bd41740ab95e2d31af6c78548`/gen7/epoch1、attempt0/CP0由leased→pending，epoch/原历史不变，0未结/在途。

原UI同run第2段接续仍在发送前拒`native_safe_output_required_never_resend_unknown`，0新API/费用，原pending保持。根因是旧resume把账本明确已释放的未发送意图也当unknown；同一作者正在原Store只读分类与原engine分支窄修，不能用重建work或新代次绕开。当前比较未通过，不先称真实短证据已发送。

上述尾修随后完成：Store公开`is_released_unsent`只在原RO事务核同epoch原释放/到期事件、pending空lease、无任何send/safe/CP/未结/nativeintent；原确认/原输入不变，不新增凭证。Owner优先原native intent/safe/unknown，只有整范围原分类真才返回not_sent；engine仅无receipt且非replay_only时继续正常claim/send。真实counter0→1/原cap1和旧CP保持；最终六个相关文件124P/17.47秒，独立not_sent63P/14.35秒和getter27P/8.40秒通过（均有重叠）。调用者自报布尔不能放行、畸形原记录安全拒绝并关闭事务、读后新claim仍由CAS挡住。源码行为已冻结，原UI同run第三段接续已明确提交，终态另记；不改前两段的失败。

相关共享部分保存根修已主树82P/3.81秒：后续题包明确拒绝时，先沿原safe/receipt/CP保存已成功成员，原entry仍incomplete、不发布完整export。原owner/SDK两pack/32k隔离E2E1P/396.47秒，仅vendor wire脚本化，第一包CP/ready、次401无CP、部分重入0HTTP且原CP不变。非作者SDK/inspection63P、partial59P及4个实际函数反例均通过（重叠不累加）。所有外层自有TEMP移除；首沙箱包装器未得终态、精确停止后未定位其AppContainer临时根，未称清理完成。不得把该软件E2E代签真实金融准确性。

共享fallback只读根因确认：底层work库已有明确拒绝后的下一attempt和unknown阻断，但上层原preview、owner binding、research intent与共享task都锁单模型。必须演进原有序目标/逐attempt实际route，不能把client循环称已完成；comparison和paid恢复仍固定原模型。未改外仓源码、未新造许可/队列。

本轮CodeGraph context在大混合索引长时间无结果后已停止，窄search无结果，沿已知源文件补足；全Projects literal搜索过宽已停止并改定点外包路径。没有把工具错误或未跑项记成测试通过。

## 11/01 代码审查整改收口

沿原小池节点完成[审查整改](docs/implementation/reviews/CODE-QUALITY-2026-11-01/report.md)，无新施工卡、许可注册表或逐题凭证。恢复仅保全原paid safe，分开发送委托/租约/手动分类期限；actor/撤权/原scope与anchor/原response/physical proof及CAS保持。SDK原初始化不再把已知safe误回收为uncertain；普通leased capture也走原parser与事务；混合登记明确原2/本次恢复1，缓存引用和原日期不变。原budget/provider材料删除仍拒，不重造历史。

共享生产资源按实际packs派生，不改冻结实验；旧CP沿原task/board/控件，后续32k不污染原8192/16k。多期指标统一坐标、比较不丢年；UI慢读锁外且冻结部署，坏草稿局部降级，超时统一。中性诊断与critical元数据兼容旧包；StockQA公开任务投影/原子work快照，delivery显式参数，纯routing/error边界解除两组import环。旧实验默认与subject生成器退役，身份审计取消公司名/000002的无证据豁免。

|验证|实际结果/边界|
|---|---|
|原owner/SDK/共享引擎完整E2E|1P/744.04秒；实际HTTP载荷含短证据，CP/封包/0send复用。只有vendor wire脚本化，0收费；临时根已删除。随后paid-only尾修另以真实原类/SQLite验证，不假称该快照覆盖后写分支|
|恢复最终parser与capture|完整两文件118P/91.98秒；字符串/对象description省outer date，只有outer缺key才继承原inner日期；显式null/冲突/非法日拒|
|独立恢复复验|QA32P/1S、UI3P；另单跑真实IQS过期override/SQLite1P确认关键正例非skip（与32重叠）。actor撤权、anchor/scope漂移、unknown/pending/无safe拒，混合scope与原cutoff保持|
|最终完整UI执行模块|154P/76.44秒；自有短TEMP清理。此前147P/5F的旧断言/包装器路径已修，不再保留未闭合失败|
|其它相关回归|UI72P；题库87个不同测试，14项Windows环境失败换短TEMP/外层后通过；指标/原子快照QA117P、IQS36P；共享入口17P、Lab profile22P、Runtime6P；共享/交付42P、旧CLI/资料反例25P等。有重叠不加总|
|集中独审|三个agent交叉审他人源码。残留DTO.check、旧CP控件、初始化顺序、错误事件、分类期限、混合分母与日期问题均已根修；本轮工程范围passed，无未解项，不授金融准确性|
|原提交检查|StockQA正常hooks全通过（black/isort/mypy100源文件/secrets等）；格式自动修后精确重暂存，无绕过。StockWiki原static hook通过，临时保存的外来patch已只读核实原样恢复|

工具/环境问题如实保留：一次4模块组合超过300秒，临时根已清理，未算通过；随后分层选相关模块和最终execution154P。包装器初始语法/路径、测试夹具provider/response_kind错误已修，不计产品RED。自动审批拒绝泛化放开leased的未执行方案后，改用原read_registered同次实际safe核验范围标记，无第二凭证且未重复问用户权限。

IQS最后暂存检查发现两个新增纯模块的EOF多空行，已作纯空白尾修，AST不变；没有重跑功能测试。

StockQA6447225已推origin；StockWiki719520b、Company Lab d1d92a2、Runtime4241d79本地提交、均无远端。本仓源码/PWF同次正常提交推送。原8766按实际argv/父子关系及无在途账本安全重载（新launcher17624，仅为当时记录）；doctor ready/无阻塞、原obs37dc465可见，普通pack2/thinking/max32768/shared=false、59包保持。账本前后均86HTTP/2024863micros、0在途/未结/active。没有新的真实公司扫描或金融核准，原错误历史不覆写。

最终只读检查时，StockWiki其他harness已将本组719520b合入381811e；祖先包含关系及本组五文件未改已核实，tracked当时干净，不回退其HEAD。

保留根外来10/10 README，以及StockWiki source-reader/checks相关并发修改和各仓历史untracked；它们会随其他进程变化，接手者以实际git状态为准，不reset/清理或并入本组。共享自动跨模型fallback仍未接；200家、事实、消费者及完整配套继续原计划。

## 11/01 全面代码质量审查

完成题库、UI/编排与跨仓owner/共享引擎三路独立只读审查，主控核源汇总于[代码审查报告](docs/implementation/reviews/CODE-QUALITY-2026-11-01/report.md)。IQS基线dfb831c；StockQA a37d60c、StockWiki1bde9e0、Company Lab a37af8d、Runtime f58fdb1、UI8fc9072均实际Git核对，外仓tracked干净，根外来10/10 README改动保留。

126个tracked scripts Python文件AST解析无错误；10组内存反例确认恢复期限、共享默认额度、UI锁/超时/草稿、指标/模块泛化与旧工具误检。没有运行全套测试、实际模型、服务或数据库操作；部分反例为原源码抽取纯函数，不宣称跨仓E2E。三个agent的源码证据与范围界限已并入一份报告，不另建审核回执。

结果为发现待修：有职责分工但未充分解耦；未发现现行生产按公司名/ticker打分；仍有实验默认、private对象穿透、重复动态校验。过期委托阻断已付保全是新确认边界，不否定上轮有效期内恢复/ACK/cache的真实成功。完整整改顺序回到原小池质量节点，没有新增支线或开工门。此次只更新报告/PWF/交接，业务源码和普通配置保持。

工具限制：CodeGraph status/files可用、context未及时返回后停止，已知源码+AST补足；Git外仓受限读取失败后以已授权外层只读方式完成。首次报告patch采用同路径删除/新增被工具拒绝，未写入；改成单次Update成功。未清理他人文件。

## 11/01 本节点最终收口

用户07:56Z恢复后只收尾同一共享已付回答。原UI补封先暴露leased提前报告、缺钥route selector和指标https-only遗漏，均在原入口根修；原失败诊断保留。恢复仅重放原safe，任何新model/search调用在原port前硬拒，不新增队列、预算或恢复凭证。

- **真实恢复/原ACK：** 同一WORK_3bfb09edaec248aca717f561b20d68cf generation6、ATTEMPT_a0a4f2329acf4a3483ca11bb6f41ba8e、provider attempt3c660196-d0f7-44ff-9467-e789305992b8。原CP CHECKPOINT_91c41d78927d4330ba74001ff783442e，work与delivery均delivered；原job275e156668c52d138ea84887f11626c8 completed，scope1/1、原ACK accepted/received_at08:28:19Z。obs37dc46500bdffc1cb28152df715fe576290af3cb8c6ca84db10f9036deed3188，StockWiki store qsobs_c2ce64820343a7b1。原score7、资料日2026-10-29、response_completed/observed/answered时间07:33:28.670089Z保持。原receipt和response hash一致；总账86HTTP/2024863micros，0inflight/unsettled/active。
- **短证据软件实送：** 原owner/SDK/engine E2E增加published_at=null以及实际HTTP body动态evidence中excerpt、URL、null断言。首轮1F/498.94秒发现provenance遗漏原board时间策略；小反例RED1F1P后修复，最终1P/701.62秒，含原CP、封包、重新打开及0send复用。只替换vendor wire，0真实收费，临时根移除。原真实这笔的旧板仍empty/allow_undated=false、provided来源空，未追认当时未发送原数，不声明金融纠错通过。
- **针对性回归：** IQS语义/引擎50P/13.25秒；QA入口最终15P/5.47秒；Lab最后41P/2.07秒；seal11P/8.84秒；此前14定向中已包含旧held_preview修复。前轮252P/1F的唯一失败已定向通过，不加总为重复测试数。HTTP指标及失效ID改名反例均有效RED后修复；旧/新board snapshot/replay/summary兼容通过。不存在但可读的历史pending可仅重放回读，存在但坏文件/目录/断链不静默跳过。
- **独审：** fresh_semantics_review为非作者，亲读原SQLite/job/CP/响应hash/ACK及旧板与最终export，对工程恢复/交付范围passed，无未解项；金融准确性仍false。没有新增review JSON或逐节点许可证。
- **普通配置与缓存：** 审查后恢复原policy11/1.1成功扫描时钟TTL24h；prepare与原备份完全相等，pack2/thinking=true/max32768，无shared专用配置/比较refs，59个包保留。原UI08:35:49Z新预览prepare_16f75b1a321f4ee592459d7ea66e33ad缓存同一IQS_11观察，status cached/count1/执行包0/API0/dispatch false/owner_state_changed false，无确认或新job。资料日10/29、原成功扫描07:33:28.670089Z与有效至11/02 07:33:28Z分列。前后账本不变。截图保存在忽略的runs/shared-ui-catl-2026-11-01/normal-cache-reuse.jpg，不发布回答正文或DB。
- **源码与清理：** StockQAa37d60c正常hooks（black/isort/mypy/secrets等）通过并已推origin；首轮hooks格式与两处类型错误已修，不绕过。Company Lab a37af8d本地提交、无remote；原UI8fc9072/runtime f58fdb1/StockWiki1bde9e0保持。Lab保原各文件行尾，不混入整文件伪差异。所有本轮QA/Lab/native E2E临时根清理；旧AppContainer目录未定位，不擅删未知路径。根外来10/10README及旧untracked保留，本仓本轮进展正常提交推送。

## 11/01 07:52Z 暂停交接

- 用户把目标设为paused，已调用目标工具确认paused；停止实施和自有测试，不继续真实请求。当前IQS最后已推`25cad52`，本轮新增代码/文档改动均未提交、未加载原UI服务；外来10/10 README改动继续保留。
- 用户要求再减负：已修改现行README、test-strategy、dashboard-product-contract、one-click-launch、shared-engine-operations、bank-run-playbook，删日常人工inspect、全仓零漂移、active ReleaseSet/组件资格、历史72源码锁/transition凭证等要求；原身份、预算、防未知重发、来源与ACK不取消。批启动首层不再重复原权限子进程，实际start仍即时完整核验；252P/1F（76.70秒），唯一失败是旧测试held_preview缺内部keyword，尚未收尾，不报全绿。
- 真实原UI批`batch-8e527bf6bd6a45f58e908cc9ea3837b3`、run`run-73ab08b815574449a6337c806a9bb2cc`已退出1；唯一新attempt`ATTEMPT_a0a4f2329acf4a3483ca11bb6f41ba8e`/work`WORK_3bfb09edaec248aca717f561b20d68cf` generation6，原HTTP200及safe输出存在，CP0。累计86HTTP/US$2.024863（本次$0.024995），0在途/未结，leased1；不能重发。原lease当时到08:28:48Z，用户恢复时须核实际状态，不假造续租。
- 实际误门已定位并修源码：vendor真实http URL被https-only拒；资料日10/29被强制等截止日11/01；provided两条原数published_at=null被intake丢弃。最后一点意味着本次实际没有发送第一方原数，不能称金融纠错完成。原答保留、不补写context。IQS语义+引擎46P/6.82秒；初始6个新增反例4F/2P有效RED；中途测试设置/ref及异常类型错误已修，不能算产品RED。
- Company Lab五源码文件answers/evidence/runner/replay/events未提交（原HEAD803ff51、起点clean）。HTTP只沿当前原attempt已核来源集合；较早/未知资料日保持原值；新scan未知published只在已知检索时点不晚于cutoff且有limitations时接入。旧board/event缺可选allow_undated_retrieved字段仍false，旧拒绝证据不追认，新true纳入原epoch，旧新重放正反例通过。独审指出的多响应原文查找尾修已实现，最终尾审未关闭。
- 独立Lab回归包装器`runs/shared-ui-catl-2026-11-01/test_lab_isolated.py`长时间无结果，暂停时精确停止本轮PID19724（无子进程），未得测试/清理终态；未定位其`C:/Temp/iqs-lab-*`根，不能宣称清理完成。另一pytest已终态252P/1F。所有审查agent均已完成只读调查，无活动writer。
- 原UI“检查并恢复”已实际被owner_work_unknown拒，费用未变。原CLI recover_checkpoints仅处理failed旧pack，shared pending无入口；不能仅放开leased。下一步最小修复：复用原seal动作透传冻结shared配置，QA原recover分支接原shared resume；在既有`_pending_port`加仅重放选项，找到原safe才能恢复，缺失直接拒新model/search send，然后原finalize/hydrate。不造第二恢复状态机或许可证。
- 临时policy12/1.3、pack1/max16384/shared_company_config及精确comparison refs仍在。备份位于`runs/shared-ui-catl-2026-11-01`；恢复普通policy11、prepare旧设置时必须保留当前59个bundle/原历史，不能整文件回滚旧58包配置。当前暂停不擅自变更原工作区；下次先零API恢复收尾。未提交不推送这组尚未通过最终验证的改动。

|日期/阶段|已完成的实际工作|尚未证明的范围|
|---|---|---|
|10/05 G2|获准6家缩样与局部G2签收|不是原60家+20重复全配方完成；不是200家G3|
|10/18 薄草稿|历史草稿/对比路径成立|不是原StockWiki正式评分/金融认证；旧12份/11家公司与正式库分母不同|
|10/25 共享引擎|真实单题搜索/思考模型/摘要/检查点恢复已签|当时未含多公司ACK；此限制后来由10/30增量推进，不重做单题|
|10/30 原UI与三市场|比较/名单接入；微软、宁德、腾讯各36有效槽；105原成功+3真实替代、真实ACK、冷恢复0HTTP|未证明金融全对、全池吞吐或TTL fresh命中|
|10/30 TTL A/B|两个真实过期单题刷新均ACK，旧记录保持；B恢复0新HTTP|真实信息日旧，fresh正例未关闭|
|10/31 四支撑包|ANSWER审计和PERF安全/研究缺口已根修独审；TIME/RESULT接原8766只读视图，三市场浏览器通过|PERF未启用，TIME不接管派发/复用；不是金融/规模/全目标完成|
|10/31 测试入口|遗漏6文件登记，114文件分层54/57/1/2；65相关及19独审、UDP2/DNS4验证通过（重复不加总）|不是全套重跑或进程树网络沙箱|
|本次状态对账|三位独立只读调查；原doctor ready=true/无部署阻塞；四份巨型PWF/交接与旧并行入口原字节归档，当前状态收敛|本次无新扫描、无新金融结论、0付费请求/0库写/0文档下载|
|10/31—11/01主线减负|缓存/定向补题、直接单包启动、身份未知国家修复；StockQA只读全账复审取消；自动委托重复核验取消；1.10.17解除人工规模开工门；批次同类门一并收尾|小样本软件通过不代签实际模型fresh或金融准确性；详见本次报告|

## 可复查基线

- 本次起点IQS已推送`215804dada41148ea79011fbb483e02f9f8d1abe`；接线代码`c1ee64f`、测试基础设施`e8f184c`/`f16da24`。本次源码与文档进展另作正常提交。
- 当前StockQA `a37d60c`已推送；Company Lab `a37af8d`、StockWiki `1bde9e0`、原UI `8fc9072`、runtime `f58fdb1`已本地提交，后四仓均未配置remote，不新建远端。IQS当前基线25cad52，本轮提交另见Git；早期日期段不冒作当前HEAD。
- 215为本机名单独立实体；108为三家公司目标有效题槽；113为原三公司含历史版本的观察；32为回答审计抽样。互不充当对方分母。
- 81HTTP/US$1.903319为10/30 TTL-B历史；84HTTP/US$1.974640为首次fresh复用；85HTTP/US$1.999868为generation5历史。当前86HTTP/US$2.024863，0在途/未结/active；本轮零API恢复、ACK和普通配置复用增量均0，不能把历史数字当当前快照。

## 证据入口

- [本次对账与修正清单](docs/implementation/reviews/PWF-RECONCILIATION-2026-10-31/report.md)
- [三市场原库冷恢复独审](docs/implementation/reviews/UI-INTEGRATION-30-2026-10-30/native-three-market-recovery/cold-independent-final-review.json)
- [真实过期刷新](docs/implementation/reviews/UI-INTEGRATION-30-2026-10-30/native-ttl-and-coverage/README.md)
- [ANSWER/PERF最终收口](docs/implementation/reviews/SUPPORT-CLOSE-2026-10-31/report.md)
- [TIME/RESULT原接线](docs/implementation/reviews/TIME-RESULT-WIRING-2026-10-31/report.md)
- [G2局部签收原件](docs/implementation/reviews/G2/G2-review-2026-10-05.md)

## 当前工作与阻塞

本轮先从原UI完成中微688012单题与原ACK1/1，证据不足保留null；随后CATL正确三题DUPONT_02/IQS_22/IQS_11完成真实模型调用。原错误映射准备已从UI结束，原记录保留。预算快照误门、有限URL tracking误拒和同attempt原答恢复已根修；不是重问付费失败题。

- **01:26Z**：原UI补封恢复DUPONT_02/IQS_11，原score7、资料日10/27、回答完成00:45:07.932157Z保持；83HTTP/$1.947570前后不变。
- **01:48Z前**：IQS_22真实HTTP200/搜索答已收到，仅行情导航query误拒，有限例外修复后从原UI补封为result_ready。未重问；累计84HTTP/$1.974640，0未结/在途。
- **01:55:00Z**：原交付job `deliveryjob_16886fe886925566121f1ca2fcc68b5c`完成2/2范围、3/3原包ACK。
- **01:57:26Z**：原UI同范围DUPONT_02再次准备，job `prepjob_907362f371a048b38a2e3dd32be7800a`直接复用同一观察，cached1、执行包0、原owner未变化；前后84HTTP/$1.974640不变，最近扫描00:45:07.932157Z与资料日10/27分列。真实正例关闭，不再写pending。

实际费用本轮共3次新HTTP（中微1、CATL包1+证券1），增量US$0.071321；原已付三题补封、原入库与再次缓存准备均0新增模型调用。未下载保存公司文档。[真实缓存薄结果](docs/implementation/reviews/SIMPLIFY-FRESH-2026-11-01/native-cache-reuse.json)。

金融质量仍有已证实未关项：IQS_11的2024 FCF跨年输入错误，IQS_22估值证据尚未独立证实。下一主线按根计划定向纠正，不篡改原答或把工程可复用写成金融认证。当前没有待用户回答的权限项；没有新发外包支线。

尾修纯导出5项隔离验证与缓存文案2项handler验证通过，非作者集中复核passed；原服务同配置重启、页面已显示新文案。02:03:54Z只读doctor ready=true，缓存原job仍在、费用仍84HTTP/$1.974640。当前源码/文档正常保存，外仓无origin不新建，别的writer及历史untracked保留。

11/01接续：亲读最新PWF和工作树；前轮为实质进展。核对官方2025年报合并现金流2024比较数，确认FCF应为658.10402亿元，原546.45不可沿用。新请求提示增加逐期间原始输入/单位/公式及第一方来源核对；有效RED后8项及8 subtests通过，旧release renderer hash保持。CodeGraph context无响应已终止该等待，改读已定位原文件，非产品阻塞。下一步复用原owner既有comparison后继控制做定向纠错；当前UI只接unusable recovery子集，需核实该既有比较类型接线，不新建客户端/账本或改旧答案。尚未发新收费请求。

11/01 02:24阶段：既有comparison目的已补入原UI准备1.3、展示及StockWiki/QA原单动作委托枚举。IQS4相关+新增status类型2项、原UI3项实际handler均通过。SW原22项绿后新增测试读错install摘要已纠正，新增1项通过；QA在唯一禁网/去密钥临时源码副本有效RED后13项通过、复制全清理。原control真实preview/agent确认已完成，源工作generation4→5；首apply被QA重复enum拒绝，原SQL确认未写决策后才修复接续同幂等键。第二次原apply仍有live handle49397，未发新收费请求，不重启/重复执行。permissions request改用原冻结query真实子集，未编造snapshot。

02:31后实际进展：原比较控制已recorded（owd1_934f7c66132ee46492b6dbf4e078e3cd81c1e1ecb7f60fc58adda9ebf6b2ff8d，4→5），源model/预算不变。StockQA c6854fd已推、StockWiki1bde9e0与UI0212c5c已提交（后两仓无远端）；hooks未跳过。原UI准备job prepjob_81fcdad6c4714567a310938957d398db在scope1原preview时以subject_dispatch_owner_metadata_mismatch退出，0新HTTP，尚未登记后继work。根因：原bank_reuse只收unfinished，忽略已delivered但有精确comparison决议的源工作，因此错误创建了新bank并移动current，原source metadata无法匹配。将补source-bank选择，保留StockWiki实质metadata检查；旧job/旧决议保持。当前本机policy10/1.3比较模式+精确refs仍在，原普通配置备份于runs/cashflow-correction-2026-11-01；必须收尾后恢复普通模式，不提前宣称金融纠错或新模型调用已完成。

02:44实际接续：source-bank读漏已有效RED后相关5P、非作者尾审通过；真实只读原ledger命中原bank，原UI已abandon旧81准备。原route公开activate+CAS恢复原bank，新当前control owd1_28ceb4f4f4dfa390c58ae466c4aa6b6c06069e1ef1a4efcee56020fe2f49f6b9已recorded（仍4→5），旧控制/route历史保留。原UI新准备prepjob_ac48559e48864ddba7f3e588c26e2af9正在后台，尚无新模型HTTP；不要重发该job。IQS507e930已推；StockQA c6854fd已推；StockWiki1bde9e0与UI0212c5c已提交。临时policy10/1.3及新精确refs仍在，原配置备份保留，收尾后恢复普通模式。

02:55实际推进：原单题已登记generation5/WORK_df168ba95e824103ad4cf3678c88c638，首次启动被原inspection漏comparison后继阻断（0新HTTP）；原函数只读追出source_work_changed。新增准确后继/无关新代次原临时SQLite正反例，有效RED1F/1P后两相关模块18P/0skip，禁网去密钥副本已全清理，非作者同节点尾审通过。源判断只增加comparison，准确generation及原owner_control全等仍保留。已原UI恢复同batch-42b5379fe5b54655a63f853df3ec582a，实际run-292caf2b061348b4ae4c53c15c4c7ea8正在执行，不重复创建请求。另落实用户取消过设计：已找出重启后强制人工inspect才能恢复、读旧job重验当前新准备配置及纯缓存还要求确认登记三处冗余，正在原接口内精简。

03:12收尾：三类去冗余已落地：原任务直接检查并恢复/补封/归档，旧job只读attach不验新配置，纯缓存preview直接显示原结果不确认/登记job；缓存轮询亦不跑执行预检。jobs全9P、execution受影响23P及尾部相关3P（重叠不累计）、原cache透传1P；UI5个不同实际ESM例通过，原错token/未知/混合/多挂牌保护保持。独审指出importPanel无关hidden重置已删，实测CSS覆盖hidden已用1行.btn[hidden]修正。普通policy11/1.1重载后原UI真实DUPONT02预览直接复用1题，确认按钮实际不可见、原结果链接可用；重启后0新job，模型账本保持85HTTP/US$1.999868、0在途/未结。
现金流真实后继本轮新增1HTTP/US$0.025228，原研究ACK03:04:25完成1/1，但仍沿用错值546.45，新score8非金融通过。另发现实际冻结bank/questions未带新增逐期规则，不能称该规则真实生效或无效。Next Step已改为先修实际规则/原数上下文接线，不继续盲重问；旧答/日期保持，临时比较模式已安全撤回，保留新登记包。StockQA3fd35a1已推、原hooks通过；原UI d3ec24a已本地提交，IQS b66ee7a已推。当前根只保留此主线，不开新包/凭证/小节点审查。

03:35接续：前轮为有效进展，根PWF仍是唯一计划。CodeGraph context再次无响应，终止该只读等待后按已定位源码核实实际入口；没有业务进程重启。真实入口规则从IQS闲置分支接到StockQA原共用provider提示，实际pack发送RED2F后全10P（含单题SDK边界），唯一去密钥/禁网副本已删除。独审确认原evidence_board可复用、standard_answer_transport并无手工context接口，不伪造external proof或再盲问。

同节点兼容：原shared来源校验强制external proof的误门已有效RED2F后原语义模块20P；native无真实搜索及坏external行仍拒。原QAEngine新增明确hydrate_questions接口，缺CP/恢复错/重复或无ID均不claim/send，RED5F后原模块23P/0skip，隔离副本清理。最后核compact路由：第一次隔离native夹具因未复制单个旧produce_bundle.py失败（不是产品RED），已只补该明确源码，当前同一选中case在新自有临时运行，不跑整套。尚未新增收费调用；原85HTTP账本/原服务不动。company-wiki存在活动writer，保持只读。

03:39原native终态：补齐唯一producer后真实原owner在compact构造有效RED1F/107.82秒；准确四字段等价投影修复后同case1P/149.11秒、0skip，内含四键漂移与额外字段五个拒绝反例，临时runtime全清理。没有复制历史docs/runs大树、没有真实模型/搜索；原账本仍85HTTP/US$1.999868且0在途/未结。非作者已集中静核发送规则及三处兼容源码/测试边界，无未解产品问题；未把这些前置修复签成原UI已使用共享引擎，公共调用与原数board仍接着实施。

04:02进一步取消过设计：规格1.10.18清掉101处逐卡独审/额外凭证，108任务/368场景/56约束及产品行为保持；审查后无关HEAD/文档变化不重签，普通测试无需逐断言或清理证明。运行路径取消本地预览固定一小时、已持久化相同设置保存时的活跃门，以及实际变更重复状态核查；导出取消全scope ready屏障，原检查器省略未建work时也保留not_exportable/partial，不冒报完成。独立agent合并审查反例已直接修复，无未解阻断，不生成新审查工件。

新增定向先有效RED7F/4P，三项最小修复后11P；扩围在沙箱遇localhost10013及长TEMP超过Windows路径上限，并非模型或业务失败。改用去密钥原Python、唯一短C:/Temp，执行`pytest tests/test_dashboard_http.py tests/test_dashboard_delivery.py tests/test_dashboard_product_prepare_api.py tests/test_dashboard_prepare.py::test_old_local_preview_uses_current_inputs_and_owner_not_an_arbitrary_hour tests/test_implementation_plan.py -q -p no:cacheprovider --tb=short --basetemp <own-temp>/p`，最终141P/72子测试/0skip，45.13秒，临时环境清理True。导出单独执行的10例亦通过，不能重复加总；测试边界替身不宣称真实模型或金融认证。

04:01:44Z确认准备全部registered/abandoned、交付completed/历史只读、无模型子进程且原账本0在途/未结后，核实原8766进程argv/创建时间并重载；新launcher27116。doctor ready=true、blocked_reasons=[]，仍85HTTP/US$1.999868，本轮新增收费0。StockQA `76c9431`已核HEAD=origin/master；主线仍待共享公共入口和第一方上下文金融纠错，不以此次减负签成已完成。保留其他writer README原hash与全部旧记录。

04:07同节点尾修：只查看旧任务改走preview(read_only=True)，省掉独立_registered_permissions重复子进程、不创建preview凭证、不需新spend或模型配置；明确未检查派发许可，真正start/resume/seal/批次仍原逻辑。有效RED1F后原执行模块147P/0skip，43.19秒；去密钥短TEMP全部清理，独立agent静核无未解问题，不新增审查凭证。此前141P与本批分开报告，不把子测试或重复用例累加为产品完成度。04:06:54Z空闲核实后原8766已加载尾修（launcher33104），账本仍85HTTP/US$1.999868；源码/PWF前一提交`6259d75`已推既有origin/master，尾修及此记录随下一正常提交保存。主线范围不变。

04:29继续主线（上轮为实际进展，非等待）：IQS原设置/准备包已加可选shared_company_config并冻结文件；StockQA原CLI/LLMRunner已贯穿该选择，复用原route client/owner/预算，shared封存后只hydrate。源码尚在本轮验收中，未激活原服务的shared模式，也未新增收费。新增共享配置模板已放examples，旧配置默认保持原工作流。

实查新根因：原ResearchChatSession final_json只声明普通聊天、不请求native搜索。现可选native_search由原runtime桥传入，委托原LLMClient.send_search_request；同一原permit原子保存搜索回执及research_visible_output，非另造厂商请求/账本。默认工具会话和原external路径保持。StockQA/原runtime Lab写前已核无其他源码writer；company-wiki保持只读。SDK/配置定向42P/0skip（4.53秒；仅未选择async标记警告）、原UI透传2P（1.46秒），去密钥禁网副本清理。原owner+SDK+Runner的单个软件E2E正在唯一隔离runtime运行（已核真实进程），只vendor wire脚本化；真实金融纠错仍未通过，不把软件case冒称真实公司或生产成果。独立agent正集中审查此产品节点，不生成新的审查凭证。

本轮终态增量：该原owner+SDK+Runner软件E2E已1P/536.71秒，真实SQL/SDK/engine、只vendor wire脚本化，验证原生搜索工具、思考、原证据摘录进入实际payload、两题原封存/hydrate与第二次0重发；临时五组件runtime已全清理、收费0。此快照先于尾修，未冒称当前完整源码重跑。独审发现并直接修了残缺导出存在误判完成、native复用旧工具端点allowlist和密钥回显三处；现在完整候选导出才同根rename发布，恢复走原CP，原SDK能力与key保护保持。另去掉构造两次完整owner任务的重复，沿同一公开issuer serializer取引用，只构造一次task。

尾修受影响47P后，正常提交钩子发现类型/可选依赖导入问题，已修复而未跳过钩子；最终SDK/配置/原CLI定向66P/0skip（4.88秒），短TEMP去密钥/禁网并清理。早期42/47和子例不累加。StockQA `1825a14`已正常提交/推origin，HEAD同步；原runtime Lab `cb00e4e`已提交且无远端。该Lab未配置Git身份，本次用命令级Codex本地身份，未改全局/仓库配置。独立agent集中尾审无未解阻断；共享跨模型顺位降级是未完功能，README/PWF明示。没有新增收费、未改原数据库/名单/生产配置，下一步只有原UI第一方原数复核及原ACK/缓存验收。

同节点导出尾修另覆盖“原engine完成输出但仍缺题”的情况：只发布all_slots_completed，保留未完成candidate供原CP恢复；最终67P/0skip、4.75秒，副本清理。StockQA尾修`07db665`原hooks全通过且已推origin、0/0同步；此处不把更多测试数或源码提交冒称真实UI/金融完成。


继续减负（同日用户新要求）：删除ExecutionGateway已无授权消费者的preview内存票据，原字段保留null兼容；只读检查取消与新扫描有关的题包/manifest/identity快照/authority/owner配置/确认/模型配置前置，原查询实体/账本/策略与原CLI保持，真正start/seal/resume不放宽。原UI调用和批次兼容由不同agent静审，无未解阻断。同步取消TIME另建核查凭证签发/续期计划；SKILL纠正重复LLM分类、逐题独立来源审核文件及旧“UI尚未接通”等误导，搜索说明允许同公司题包共享真实检索。

运行回归：原执行/批次/准备三个模块264P、0失败/错误/skip，pytest59.72秒、含启动清理64.662秒；去密钥、公网拒绝、唯一C:/Temp夹具已清理，新增API/费用0，不改原库/名单/配置。首轮在沙箱内尚未启动pytest即卡在隔离目录准备，已停止该自有会话，按相同用例在授权隔离环境执行上述有效结果；空run目录已删除，不算两轮产品验收。未重跑长native/小时全套，未新增审查凭证。


计划减负同步完成：1.10.19退役Q15及9个第二许可证专属场景，现107任务/359场景/52约束；同步任务依赖、最终发布要求、校验器/规格测试与当前设计文档。V16仅版本/兼容元数据、V17仅影响分析、W16沿原owner字段应用/必要CAS、V18停新派发升级回退；原attempt/unknown/fallback场景及真实规模/消费者/安装目标保留。计划定向83P、70subtests、5.05秒，去密钥禁网TEMP清理；不合并成产品测试通过，也未新增日志凭证。校验器planning_valid=true，product_tests_executed=false。

集中独审确认上述取消未削弱原身份/权限/预算/租约/unknown/ACK保护。指出的三项文案尾巴已关闭：test-strategy不再逐任务原子凭证，C07前半页明确旧只读兼容，SKILL --review例明确历史strict；跨项目/作业/一键启动及两通用lane旧授权/许可证说明也已对齐。原冻结施工卡/验收报告不改签，无未解阻断，不新增审查回执。只读原8766仍doctor ready=true、无阻断；账本85HTTP/US$1.999868、0在途/未结/未知工作，准备33 registered+10 abandoned、交付11 completed+2历史只读。本轮未重发模型或修改名单/原观察/配置；真实金融复核继续按唯一Next Step，不拿减负代验收。


上述33文件已正常提交并推送既有origin/master：`2970499`，包含先前可选共享入口接线、此次runtime精简及1.10.19规范；未带入其他writer的10/10 README或历史untracked。05:19:09Z在只读核清无准备/交付/模型在途后，确认原argv/父子身份并只重载原8766（新launcher29892、服务15444），原dashboard.local配置保持、shared模式尚未激活。重载后doctor ready=true、blocked_reasons=[]，账本仍85HTTP/US$1.999868、0在途/未结/未知，新增付费0；本轮精简已实际加载。没有因不可靠端口PID停止其他进程。真实原数纠错/共享fallback仍待主线，不改签为通过。


继续真实共享主线：读取当前源树及原部署，StockQA仍07db665且干净，原runtime亦无未提交；doctor ready=true，账本85HTTP/1999868micros、0在途/未结/未知。在线核官网2025年报的合并现金流量表2024/2025两列，确认原分析主体consolidated_reporting_group/ASJ_02f60cec@1；仅保存两条139字以内短原数摘录草稿，未提供预期FCF或分数，未下载报告、未激活配置。旧用户标签页claim API不可用，按同浏览器支持接口新开后台验收页，原页面保留。

付费前独立追查发现provided来源误拒贯穿engine→lifecycle→checkpoint写读→observation：现有native E2E N/A没有测到有效带来源评分。根负责IQS engine和将原软件E2E升级为provided-only来源scored6/原vendor回执不改/再入0HTTP；fresh_ui_route独占StockQA修原intent可空来源摘要与保存投影，非作者fresh_semantics_review负责同产品节点独审。只沿原表做可选列兼容，不新建许可证/权威库。尚未运行新长例或收费，不以接线/检查代金融通过。


11/01第二轮取消过设计：原自动交付省一次重复StockWiki preview；新delivery profile1.2只绑定实际owner/接收位置，旧1.0/1.1按实际旧算法兼容且不改写旧job。独审指出setup仍把partial一律活跃，已根修原load/setup：仅同目标、保留旧包/状态目录且停止I/O的新partial可改未来扫描设置；真正运行、未知、错库和旧不透明目标仍拒。TIME从双轨captured-context决策缩为原日期解释，删除verification_missing合成，UI不再提示另取核查凭证。规范取消全仓快照和逐文件清理清单，使用自有短临时目录、先等worker结束再finally清理。

测试先有效RED6F；短TEMP扩围86例中85P，1例既有HTTP loopback Win10053，单独复查1P/0.70秒，未修改HTTP权限代码。审查尾修新增原PUT反例先RED1F，再原prepare/delivery与相关HTTP36P/2.30秒；与前86重叠不累加。原UI Node13P，所有自有TEMP已清理。首轮长沙箱TEMP导致4个500已由短路径运行澄清；诊断时一个自有临时job锁未及时释放，进程退出后仅清理确切自有目录，未碰用户文件。独立agent集中复核与同节点尾修关闭，无新审查文件/凭证、无收费API、未改原库或名单。

主线另记真实未关状态：provided来源的StockQA修复已正常hooks提交8791c0e；原runtime完整dynamic修复f58fdb1本地提交（无远端）。QA原intent/标准答案/观察111P，以及独审尾部9P与runtime实际SDK wire6P分别验证，重叠不累加。原owner scored长例前两次各1F（218.26/221.57秒），不是已通过：第一处SDK消息封装和未来期指引日期误门已修；随后定位bridge删空tool_results导致实际发送hash变化，修复只作用显式one_shot profile，旧协议保持。修后第三次隔离原owner例正在运行，付费0，不能先签成原UI真实扫描或金融纠错完成。

StockQA8791c0e已推送既有origin/master；原UI文案8fc9072已本地提交（无远端）。本轮取消的不是原安全权限或预算检查，不扩运行授权、不开新收费请求。


第二轮减负14文件已正常提交并推既有origin/master `4526eb7`。原8766只读核空闲后，按实际argv/父子/创建时间重载（新launcher27636），doctor ready=true、无阻断；13旧交付保持11 completed+2历史只读，原85HTTP/US$1.999868、0在途/未结/未知。没有改原部署JSON或重做已付扫描。

原owner scored第三次终态1F/386.86秒，临时五组件runtime已清理、0付费。发送与两题CP已通过；原sealer末端仍仅认vendor URL，报exchange package evidence URL is not bound to checkpoint，继而hydrate缺CP。保留失败，已交原StockQA同一writer沿原provided来源投影补末端短反例和根修，不把删除空tool_results的前置修复宣称端到端已全通。软件缺口修好后才做原UI真实金融复核，不盲发新模型。

原CUA结果页已重新加载并展开宁德时代真实记录，实际显示“仅展示原记录时点；实际缓存复用和刷新以原服务预检为准。”旧已加载JS曾显示旧文案，完整刷新后确认新内容；未提交表单或发模型。搜索实操规范遗留的permit/consume/dispatch_commit指令亦已删除，对齐原StockQA防重/预算，并说明provided_context独立来源语义。


主线原封包尾修已有效RED1F/3.04秒→原seal/get/reopen/hydrate正例1P/2.68秒；provided/outbox/Q10三模块68P/0skip/10.15秒，唯一去密钥禁网副本清理。原validate_checkpoint_binding默认仍严格，只有Store同事务_checkpoint_record重读原intent/receipt后显式传合法provided来源；prepare/supersede及完整observation重建、原厂商回执均保持。原hooks首轮仅修换行/import排序，重跑正常hooks全过；StockQA756eee6已提交推送origin。不同agent集中审三个QA与三个IQS主线文件，无未解阻断，不新建审查凭证。

第四次原owner完整软件例provided-v4现用新唯一五组件临时副本运行（原exec handle72879），只vendor wire脚本化、0收费，等待真实终态后才执行UI comparison；不是重发前三次请求或覆盖其失败。实际原owner政策11原字节与准备的备份一致，候选12仅1.3方言/quote和单调版本变化，TTL24h与successful_scan保持；尚未激活原配置。


provided-v4终态1F/374.72秒，临时副本已清理、0收费。两题C06包均sealed，末端封包修复确已生效；旧ApprovedRefreshSession.restore_registered_checkpoint重新验证标准答案时仍只认vendor来源，异常被hydrate的DEBUG捕获后表现missing CP。原restore短例已有效RED1F/3.13秒，明确是真生产来源投影遗漏；未改decision guard（原_refresh_states本会正确转resume）。只补已由原Store复核的来源合集，不放松原主体/模型/绑定校验；修后短回归正在原writer唯一隔离环境执行。未因长例失败去收费试错或删断言。


原恢复尾修保持decision/registered_scope/self.check/binding/题义/主体/model/日期与原回执，仅合并已Store复核的provided来源。provided+refresh_execution原两模块81P/0skip/24.30秒，临时副本清理；不同agent同节点静审关闭，原hooks规范换行/import后全过，StockQA7b3814f已正常提交推送。第五次原owner完整软件用例provided-v5现handle89150唯一隔离运行，只scripted vendor wire、0真实API。原UI仅准备内存设置草稿和只读操作页，未保存shared/比较配置；尚未做新真实金融结论。


provided-v5原owner整链1P/468.81秒、0skip、0付费，唯一五组件runtime已清理。覆盖实际SDK native search+thinking+provided-only来源两题scored、原封包/水合、原回执不改及再入0POST；原前四次失败保持。开始真实原UI复核：只读原账本85HTTP/1999868micros且0在途/未结/未知后，保存当前dashboard备份并原字节CAS临时policy11→12/1.3（TTL与预算不变）。首原work-decision preview返回refresh_owner_preview_rejected，0新模型HTTP；正在追原公开服务详细拒绝原因，不盲重复请求。当前policy12仍临时，须本轮完成或失败收尾后回退普通policy11。


首comparison预览的拒绝来自实验编排错误：请求草稿漏permission_request；随后取scope原query.json时其snapshot尚为null。已改从gen5原refresh.json读取真实冻结source_query，题目/主体选真实子集，同时通过原_work_request和refresh.validate_request两校验，不伪造snapshot或改产品校验。期间误把缺文件的输入准备失败与下一CLI放在同一调用导致一次无效重试，0费用；已改为先检查exit_code再执行依赖。新原CLI preview现handle80391运行，旧failed日志保留；不是新权限缺失或需用户再次授权。


原comparison控制已真实ready→原委托confirmed→StockQA apply recorded：owd1_b19b257a3b5982b4613dfa660a90b64ca98c2bb89c82d1f9c5884e7e4fa09f03，gen5→6、0模型HTTP。IQS25cad52已提交推送，QA7b3814f已推。实际首次writer将原work库25→26，之前用SQLite backup保存一致私有备份；只核相关原列，85预算attempt、244原响应、0旧research intent全保留，未做全仓快照。

从原UI保存prepare.shared_company_config、pack1/thinking/max16384及精确新refs，58原执行包保留，原账本仍85HTTP/$1.999868。初次填定向IQS11与原受控范围选择冲突，按公开契约清空可选字段，由原决议确定IQS11单题；没有改产品校验。原UI确认预览本次1/完整36、group ASJ_02f60cec@1、唯一真实SZSE300750后，点击登记得到prepjob_490615d422a3424497cb16fa609f1432（preparing，原后台在运行）。登记未启动模型，勿重复提交。当前临时policy12/1.3与专用prepare仍在，完成或失败收尾后恢复普通配置并保留新登记包。

## 2026-11-03 B03 Dashboard服务配套收尾

在独立D00分支完成Dashboard公司结果接口配套：精确pin防止静默跳到其他最新结果；/link对空值、重复result/result_id及两别名同时出现给出明确拒绝；按精确owner snapshot返回结果ID及可用listing/subject路由范围。服务定向测试37项通过。整体D00 UI/服务/Dashboard候选通过独立非作者审查，最终history链接回归关闭。未做生产部署、数据库写入、真实模型/API调用或真实owner扫描；需与Dashboard候选一并进入实际产品发布后再做真实UI验收。

## 2026-11-03 B03提交与远端

IQS服务候选已提交ec86605，并推送至既有origin分支codex/d00-b03-iqs-service；Dashboard候选04756ca和UI候选47d5354已提交在各自本地隔离分支。Dashboard/UI仓没有配置远端，且canonical Dashboard主工作树未改动。三项仍属于待产品main整合/部署的候选，不代表原8766或真实owner端到端已更新。

## 2026-11-04 B03跨仓主线合并与主线复验

Dashboard候选合入investment-dashboard main（merge f501f32，合同0.1.2-d）；IQS服务分支以快进方式合入master（5211f00→fb262e0）；只读UI候选合入iqs-question-bank-ui-lab master（47d5354）。没有改变生产部署配置或原8766进程。

合并后复验：IQS核心公司结果接口37 passed；核心加owner/HTTP/实体视图相邻测试103 passed；UI结果页、返回链接、深链、pin和服务运行时来源测试29 passed。Dashboard定向适配/历史链接和相邻身份测试通过，OpenAPI生成检查通过，synthetic smoke 27 checks PASS，TypeScript typecheck与生产build通过。生产build在隔离临时目录运行成功；提示JS包体超过500KB。分类测试分组存在覆盖重叠，不累加为全项目测试总数。

独立非作者复审在并入前已针对最终payload关闭。真实owner/API扫描、原8766重启、数据库正式写入未做，因此真实扫描到入库/缓存恢复链路仍是主线未完成项。工作区其他未提交/未跟踪文件保留，没有加入本次提交。

## 2026-11-04 独立施工包准备

编制 F05-FACT-QUERY-01（StockWiki 隔离克隆，基线 `d8d3303`）与 G3-BATCH-RESUME-HARNESS-01（独立 IQS 合成测试工装，基线 `da557350`）。确认复用 LOAD-CASE-01（SHA-256 `99E7A7D3…35E2431`），避免重复建设负载场景。两包尚未实施；测试工装不能代替真实200家公司 G3，F05需总控验真实 owner golden 与 IQS互操作后签收。

## 2026-11-05 F05 / G3 支撑包验收

- **G3-BATCH-RESUME-HARNESS-01：工装交付通过，生产 G3 未关闭。** payload `c9fd6c54274ef05f40676db2cce5a13c20bcfc04`，冻结基线 `da557350b0dd11ea92382ad22479f874026d4ad8`。修复 subprocess 捕获的 UTF-8 解码问题后重跑完整工装：31 passed、0 failed、0 skipped，无解码告警；独立审查通过。另一个冻结产品回归控制 `tests/test_dashboard_batches.py` 为101 passed/1 failed，失败在冻结基线可复现，记录为 failed 而非工装通过。合成工装仍不代表真实200公司试点或生产 G3。
- **F05-FACT-QUERY-01：部分交付，未关闭 F05。** payload `63a6ffcf23f8d16f47acf44bdbcf3e567a85458e`，新增声明运行依赖 `jsonschema>=4.21`。独立审查后复跑定向测试34 passed、0 failed、1 skipped（该集成模块因本次未提供三组件 owner runtime 而跳过）。owner 侧 schema/handoff 校验通过，精确19个导入失败模块已由 collect-only 复核：未过滤时19 collection errors，精确忽略后0 errors、1616 tests collected；没有执行这些测试体。
- F05 的历史离线全套记录为1519 passed、55 failed、39 skipped并另称10 errors，旧运行原始日志未保留；字段计数合计1613，与1616 collect-only不一致。总控尝试整套复跑后因长测超出聚焦验收范围而中止，临时目录已清理。本项继续标 failed/unresolved，不宣称总控复现其基线等价结论。
- F05 保持 `status=partial`，阻塞是预期的实际产品前置：没有受支持的只读真实 owner 数据入口/真实 owner golden，IQS 侧 facts 查询契约尚未部署并做公开消费端互操作。G3 handoff 标 `status=complete` 仅指工装；`production_G3_status=not_closed`。两份 handoff 的详细路径和最终元数据见 `task_plan.md` 的2026-11-04支撑包段落。

## 2026-11-05 F05 IQS 消费端施工包准备

针对 F05 handoff 明确遗留的 IQS consumer contract，已编制独立包 F05-IQS-CONSUMER-01。冻结 IQS 输入为 `aca0f4be5adcb96f0c7d8f58e0c4a205e6c17981`，F05 owner 输入为 `63a6ffcf23f8d16f47acf44bdbcf3e567a85458e`；owner facts schema SHA-256 为 `CD3E03417289A99F5194263603EAD6D954FD601B875CD3D5C08A74505BA8CBAD`。目标 Lab 为 `C:\Users\郑曾波\Projects\iqs-f05-iqs-consumer-lab`，当前状态为已备妥、未分派。

施工卡把范围限制在 IQS facts 合约/CLI/capability 声明和离线契约测试；明确四种 F05 调用、2.7.0 wire、旧 2.0–2.6 兼容、strict/explore 与 unknown/empty 区分、最终独立 agent 审查及交接字段。不得访问生产 owner、真实 golden 或收费 API。代码包完成只关闭该包，不关闭 F05；总控仍需后续真实 owner 公共 CLI 互操作和真实 golden 验收。施工卡与索引见 `task_plan.md`。

## 2026-11-05 F05 IQS 消费端交付验收

施工包最终提交为 Lab HEAD `08e5b4d660bd09cfbb6fe9cba0d7ec7aad31d388`（本地隔离分支，无 remote），状态为隔离代码包完成。验收在原范围内直接修复：导出自哈希原先不能绑定原查询与 owner profile；公开导出 presenter 响应现在由 `facts-export-response` 重建 profile 投影与导出体后比对。导出跨日 snapshot replay 原先会按新请求日期误算 cutoff；现在在 request cutoff 为空且带 snapshot 时沿用响应所绑定的历史 cutoff，并由 query hash 和原 snapshot ID 校验。capability 1.2 的 2.6/2.7 wire 顺序已修正，施工卡也纠正了与冻结 owner 冲突的哈希表述：query_facts/export_facts 共用逻辑查询哈希。

独立代码审查未发现实现阻断；审查员提出的“保留原 snapshot ID、改 cutoff 并重算 query/dataset/candidate 哈希仍应拒绝”反例也已加入并通过。最终 facts/capabilities/public CLI 定向套件 82 passed、0 failed/skip；exchange/query 与 deployment 相邻套件 30 passed、7 子测试通过。旧 query v2 套件为64 passed、1 failed，失败仍是冻结基线的 `model_self_qualification`，本包未触及其逻辑，报告原始失败，不称全套通过。所有测试使用合成数据，无生产数据、网络或收费 API。

F05 整体仍为 `partial`。下一步仍是正式产品接线，取得受支持的真实 owner 只读入口/真实 golden，再由总控跑 StockWiki 公共 CLI 的真实互操作；此隔离包的通过不能替代这项验收。

## 2026-11-06 F05 IQS 消费端并入主线

已将隔离 Lab 的已验收 payload `08e5b4d660bd09cfbb6fe9cba0d7ec7aad31d388` 合入本仓 `master`，代码提交 `da34654`。只纳入 F05 consumer 的11个文件；未暂存工作区内其他外包材料、运行记录或未提交README。实现包括 owner facts 2.7 schema 的字节锁定副本、IQS facts 查询/响应与导出响应校验、CLI operation 路由，以及 capability wire 2.7 声明；1.2 vendor wire 2.6/2.7 按版本排序。没有改 StockWiki 或生产数据。

主线重跑：`tests/test_query_facts_contract.py`、`tests/test_query_capabilities_facts_wire.py`、`tests/test_f05_facts_cli_conformance.py` 为82 passed；加 `tests/test_exchange_and_query_contract.py` 后97 passed、7 subtests passed。Windows 运行需 `PYTHONPATH=scripts`、`PYTHONUTF8=1`；冻结 owner wrapper 测试需读取 StockWiki F05 隔离候选 Git 对象，并把代码归档到测试自动清理的临时目录。测试全用合成输入，不写 owner 数据、不联网、不调收费 API。

旧 `tests/test_query_contract_v2.py` 的 `test_bad_original_answer_remains_bad_with_new_self_consistent_presentation[model_self_qualification]` 仍失败；本轮合并前的隔离验收已记录同一失败。本轮不把它算成本次回归，也不将旧兼容组说成全绿。F05 从“消费者代码仅在 Lab”推进为“消费者契约/CLI在 IQS 主线”，仍为 `partial`：尚未把普通产品/共享引擎流程连接到真实 StockWiki owner 只读运行时，也未完成真实 owner golden 与当前公开 CLI 正反互操作；真实UI扫描、数据库写入及生产部署都未执行。

## 2026-11-06 独立主线施工包准备

准备了三份可以交给不同 Harness 的独立施工卡，均为可分派、尚未开工：F05-OWNER-MAINLINE-02（StockWiki owner producer）、TH-IMPL-02（analyze-theme-value-chain consumer）、IN-IMPL-02（industry-research consumer）。每包使用新建 Lab、独立分支和单一 owner；本仓 IQS `master@acb03e3c084f61ca2b49181180195118077d43e3` 只作只读协议输入，facts wire 2.7 schema SHA-256 `cd3e03417289a99f5194263603ead6d954fd601b875cd3d5c08a74505ba8cbad`。

开卡时核实 StockWiki 当前 `master@6d1e40bcdcde5e99488e22c38d57bd8e1b33c27e`，tracked tree clean，但存在四个需保护的 untracked data 路径：`data/companies/688012.SH/research_source_links.sqlite`、`data/dashboard_onboarding/`、`data/dashboard_research_binding/`、`runs/c16b/`。owner 包必须从锁定 tracked commit 建孤立克隆，不读/复制/改动这些路径。Theme 源 `master@3c9a49c7ce86f3e60eb9a6c8e6c835164cb8a903`、Industry 源 `main@98640a9a1f52fc87ba9813676a3cc5ab9bf045c9` 均 clean。三个 Lab 编卡时都不存在。

新卡明确：TH/IN 可依固定合同和 synthetic response 独立完成消费端开发，不再被真实200家 G3 或真实 owner golden 阻挡；不得把 synthetic 测试写成真实互操作。Owner query 可能持久化 snapshot/capture，因此测试只能把 owner root 指向各自临时目录。本批不分派真实 G3 扫描，该流程需要总控独占原 UI/额度/运行库。每个包交付前做一次独立 reviewer 大节点审查并修完 findings，不要求小节点重复审查。具体边界、测试案例、操作命令与共同交接规则见 [施工包索引](docs/implementation/parallel-lanes/packages/2026-11-06-mainline-consumer-wave/README.md)。

独立 agent 对本批施工包的依赖口径、目录边界、隔离和交接完整性复审通过（`approved / open_findings=[]`）。复核限制：子代理沙箱无法读取 StockWiki/Theme/Industry Git 元数据；这些冻结提交和工作树状态由总控在编卡时只读核实。README、六份交付文件及相对链接均已核验；IQS facts schema 哈希与锁值一致。


## 2026-11-07 三个主线消费者施工包验收

- **正式接收：** F05-OWNER-MAINLINE-02、TH-IMPL-02、IN-IMPL-02 已登记到 IQS package catalog；三份 handoff 经 `python -B -X utf8 scripts/parallel_handoff_cli.py --input <handoff.json> --package-id <id> --verify-references` 均返回 `status=valid, errors=[]`。登记回归 `python -B -m unittest discover -s tests -p test_parallel_handoff_cli.py -q`：13 项通过。
- **F05 owner：** 隔离 Lab 实现 `6449917cfe38a5c3abb53c056d654ee876182ebe`，交接元数据 `4911b7e117cb462ee5ad36dde0f4a2e48cc02c7b`。验收记录82项定向、226项受影响回归、static-only、日常337项及公共CLI隔离E2E 9步；独立非作者 agent `/root/review_f05_owner02` 对最终增量复跑E2E并通过。旧wire哈希已改为锁定源码文件可复算锚点。确认并清理Lab junction、E2E/TEMP根、baseline clone和 `f05-capture-0qtex5ju`；报告与JSON保留历史外部临时克隆创建事实。F05产品状态仍partial：真实owner golden、IQS public CLI真实正反互操作和canonical StockWiki合并/部署未完成。
- **Theme：** 实现 `5477353649bd86385bc9261bdb2a9f2b30ef63a1`，交接文档提交 `14039094521ba13bba3a43392d426326326dbc8d`。总控按独审意见修复非法UTF-8处理、stale_owner_data文档、无用常量与cursor预传输反例。默认Windows CP936环境54项通过；非作者 agent `/root/review_theme02` 对最终提交独立复核通过。仅离线消费者实现，未声称真实owner接线。
- **Industry：** 实现 `ba54e00f5356831b9bb3ded952c06d43c4c01606`，handoff/report元数据提交 `0ab50e9eefbe23fda2d46dea2952b0e532456a7e`；161项隔离测试及独立delta review通过。仅离线消费者实现，未整合至canonical技能源仓。
- **边界与下一步：** 三个Lab各自本地提交且工作树clean；本轮没有改写StockWiki、Theme、Industry canonical源仓，没有真实公司扫描、数据库写入、模型/搜索请求或费用。接下来按根task_plan先只读核实当前源仓HEAD/工作区是否有并行writer，再把F05 owner适配到当前StockWiki主线，建立受支持只读runtime与真实golden、完成IQS公开CLI真实正反互操作；接口稳定后再整合TH/IN并跑各自技能入口E2E。离线包交付不等于F05/W11/G3/G4产品完成。
- **提交流程：** 默认沙箱无法创建 IQS `.git/index.lock`，未产生暂存或提交；将在核对精确暂存范围后按既有授权重试提交。

## 2026-11-07 主题/行业源仓接线施工包准备

新增 TH-SOURCE-INTEGRATION-01 与 IN-SOURCE-INTEGRATION-01 两张并行卡，分别将已验收的离线消费者移植进各自冻结源仓的隔离副本。它们仅共用 IQS 已提交 facts wire 2.7 只读输入，不写 IQS、StockWiki、StockQA 或对方技能仓；目标 Lab 各自唯一。独立只读审查确认边界可并行。卡片与冻结输入清单见 `docs/implementation/parallel-lanes/packages/2026-11-07-source-integration-wave/`。

IQS 的未提交 2.8 改动被明确排除；卡片交付只代表离线源仓候选，真实 owner、F05/W11互操作与G4仍由总控验收。编卡时两个 canonical skill 仓的 `git status` 都报“must be run in a work tree”，无法确认最新工作树状态；因此要求从精确锁定 commit 建立全新隔离 Lab，不覆盖已存在 Lab，不写 canonical source。编卡时两包已备妥、尚未分派；最终交付状态见下方2026-11-08更新。

## 2026-11-08 TH/IN 源仓接线施工包查收

TH-SOURCE-INTEGRATION-01 与 IN-SOURCE-INTEGRATION-01 均已由总控验收并在独立 Lab 内修正缺口；最终独立 reviewer 均 ACCEPT，IQS 公共交接 verifier 两包均为 `valid / errors=[]`。TH 最终 commit `dde51cdd1431a106af2a3f03467bd3423511256b`、59项通过；IN 代码结果 commit `ce7434bd46a9c74b2c1156e61ca56fc670d62c9`，整目录176项通过并另复跑 CWD 用例1项通过。IN 回执原有的单一组合 hash 无法指向实际交付文件，现以三个精确 commit-bound 文件 hash替代。交接文件 SHA-256、测试范围、审查人结论见 `task_plan.md` 的同日验收条目及对应隔离 Lab handoff。

本轮未改 canonical Theme/Industry 技能源仓、StockWiki、StockQA或生产数据库；未做真实 owner、收费模型/搜索或真实公司扫描。隔离交付通过不等于 F05/W11、G3/G4 或真实主线接线完成。主线仍按 task_plan 的 F05/W11 稳定接线和真实技能入口互操作验收推进。

## 2026-11-09 当前主线复核、F05 候选与解耦审计

- **真实代码和历史问题复核：** IQS canonical `master` 从 `130dc31` 增加精确提交 `3d2bf44` 并成功推送；只改 `scripts/standard_answers.py` 与 `tests/test_query_contract_v2.py`。重跑发现旧失败确实仍存在：模型答案可通过扩展字段伪造 `check_level=independently_checked`。根因是答案 schema 为向后兼容接受扩展字段，但答案语义校验没有把信任等级与可见答案隔离。现在通用可见答案校验递归拒绝 `check_level` 与 `check_level_receipt_id`；新增自授等级与伪造回执两种反例，并在重新封装、重算观察ID/owner引用后检查拒绝。最终 `tests/test_query_contract_v2.py` 66 passed；与 `tests/test_standard_answers.py` 合跑 106 passed、8 subtests passed。独立审查 ACCEPT。普通模型答案不承载审批/资格，信任等级继续由本地受信 observation envelope 控制。
- **IQS F05 消费端候选：** 隔离分支 `codex/f05-query-paged-response-01` 的提交为 `8b7d80f`（分页/响应验证）、`1df3bdd`（语义能力声明）、`16c7b1a`（移除对 StockWiki 私有模块及缺失 Git 对象的 IQS 测试依赖，改用 F05 公共 CLI 边界测试），分支已推到 origin。候选专测 74 passed。此分支不等于并入 canonical master。
- **StockWiki F05 owner：** 独立分支 `codex/f05-owner-runtime-01` 提交 `3799b43` 已由总控 fast-forward 并入 canonical `master`。公开能力声明、分页及 snapshot 绑定校验、公开 export-response CLI、旧消费者回退、范围内 AST 边界防回归均进入主线；路由集成以 manifest question IDs 检查题目数量、唯一性和集合相等。候选较广测试组 92 passed、ruff 检查通过；合并后 canonical 六文件 F05/路由组 **45 passed、2 skipped**；最终路由测试独立审查 ACCEPT。StockWiki 没有配置 remote，所以只完成本地 canonical 并线，不能推远端；既有运行数据 untracked 保留。
- **真实 owner 的限制：** 对 CATL 的公开查询得到 `coverage_gap / no_bound_fact_observations`、0条事实观察、无 owner 引用、0 API 请求。这说明当前 owner 没有可供本接口消费的事实行；不构成 positive golden，也不能伪造 F05 正例。F05 仍 partial，接下来需要真实可绑定的 owner facts、公开 CLI 正反互操作和按协议复用恢复。
- **跨仓实际版本：** Theme canonical `master` `e35ab39`、Industry canonical `main` `169c200`，本轮只读看到两个 tracked tree clean；之前 PWF 所写“整合仍待办”已过时。真正未验的是 F05/W11 可用后的技能入口端到端调用，不是源代码尚未合入。
- **解耦与门禁检查：** D1–D7 的具体行为整改仍按其当时范围有效；它们不是全项目解耦证明。F05 有限域静态规则只防该边界中的内部导入，不可外推为整个 IQS/StockWiki 架构已封装。没有必要恢复此前移除的重复许可/审核链；保留身份、owner 来源、预算、幂等/未知发送、锁和 ACK 等正确性/经济安全约束。Python 私有命名不能运行时阻止访问；应以明确 facade、版本化协议和静态边界测试实现。
- **当前主要卡点：** 真实 owner 没有事实行；IQS consumer 候选尚未并入，而 IQS canonical 根目录含其他并行 2.8 WIP，因此不能整目录回滚或直接覆盖。第一步是在单写者下解决 IQS 候选与 WIP 的版本衔接，再获得真实 owner facts 完成 F05；随后做 TH/IN 技能入口实服务 E2E 和 G4。200家真实 G3、2000家覆盖、G5/G6 配套仍未完成。

## 2026-11-09 公开接口与测试整改

- IQS 工作台走 `describe_delivery_scope`、`read_delivery_receivers`、`parse_recovery_refs`、`normalize_loopback_origin` 和 TIME 包公开读取、解释操作。交付模块负责构造原范围请求，TIME 包负责时点计算及目录资源的读取。原注册指纹、接收方与日期语义由相邻测试复核。
- TDD 首次复现工作台调用私有符号和运行器遗漏 14 个已有测试文件。新增边界测试后将全 130 个文件归入现有分组，`fast --plan` 正常列出 60 个文件。离线回归最初暴露旧测试夹具仍模拟 StockQA 内部类、准备目标参数形状过时，以及后台校验被错误断言为同步抛出。更新夹具后，最终 13 个文件 366 passed、1 skipped，耗时 179.65 秒。跳过项需显式原三方恢复环境。Windows 沙箱的硬链接及环回限制用现有离线测试器在正常本机权限下复核，正式回归的自有临时根已清理。
- Theme `3352b58` 本地快进进入 `master`，无 remote。独立审查发现 Python 入口可绕过目录检查，且文件硬链接可改写 owner 工件。修复覆盖预检、解析实际路径、原子发布、失败时去除上一轮响应及导出标签。76 项定向测试通过，无跳过。
- Industry `7d49ca3` 已进入并推送原 `origin/main`。独立审查复现错快照的首屏和导出结果可被接收。修复验证主水位和导出水位的快照 ID，拒绝页不参与事实聚合，已校验的前页仍可用。全套 186 passed、5 subtests。两仓均以独立子进程验证公开 CLI 参数及消费者目录的复用，独立复审通过，隔离候选目录已清理。
- F05 基准 `130dc31`，主线 `30a841c`，候选 `16c7b1a`。三个重叠文件在冻结 2.8 WIP 的隔离副本三方合并无冲突，87 项 IQS 定向用例通过，临时副本清理。真实配置的 owner `--capabilities` 认可候选，`API_requests=0`。只读观察库计数为 120 条总记录、120 条主体绑定、0 条事实。2.8 尚需原写入方并线，真实正例仍待原采集和入库。旧 F05 离线集成组的六条用例仍需原缺失外仓对象，由候选的独立 CLI 回归接替。

## 2026-11-10 模块边界扫描器补洞与独立复审

- 根据 2026-11-09 独立基线，把真实生产入口对应的边界测试覆盖到 IQS、StockQA、StockWiki、Company Agent、Agent Runtime、Dashboard、Theme 和 Industry。现有实现包含版本化公开 facade/CLI/协议、跨模块 API 导出声明、层间私有成员扫描及 owner 数据路径检查；本轮未改生产数据库、名单、API key 或任何模型/搜索接线。
- TDD RED 证明普通赋值别名曾绕过 IQS、StockQA、Runtime、Dashboard 与 Theme 的动态 import 检查；独立 reviewer 再发现“嵌套 `getattr(importer, "import_module")(... )` 直接调用”和 `builtins.__import__` 同类旁路。两轮失败反例均已加入各 owner 的现有边界测试，并修复 AST 扫描器。Reviewer 初轮 `NEEDS_FIX` 指向该遗漏，复修后同一独立 reviewer 对最终改动复验为 `ACCEPT`，未留 P1/P2。
- 最终定向测试：IQS 两套边界 `50 passed`；StockQA `24 passed`；StockWiki `9 passed`；Runtime `9 passed`；Dashboard `2 passed`；Theme `2 passed`（仅运行边界选择器，75 项未选）；Industry `4 passed + 12 subtests passed`；Company Agent public API `2 passed`。独立 reviewer 另外逐一扫描七仓的直接动态导入探针，七处均被检出。
- 日常入口核实：IQS `scripts/run_tests.py fast --plan` 返回 62 个 fast 文件（总测试清单133），包含 `test_shared_public_boundaries.py` 与 `test_dashboard_module_boundaries.py`；本轮只做 plan 模式，没有跑完整 fast 组。StockQA `scripts/checks.py` 的 `DAILY_TEST_TARGETS` 包含模块边界文件；StockWiki `SHORT_TESTS` 包含对应边界文件；Dashboard `pytest` 默认 testpaths 包含 integration。没有把定向测试说成整仓全套通过。
- 两项相邻独立复核已结案：StockQA WorkStore 的跨模块导入逐项落在 owner 的 `MODULE_API_EXPORTS` 中，180 个 AST 导入名无遗漏；StockWiki 先前指出的下划线导入和日常测试漏项在当前树均已消失。其余未登记 StockWiki helper 是同 owner 内部协作，不属于逐文件版本化的跨仓合同；边界规则和版本化范围已明确补入模块图。
- 模块归属、公开接口、版本与允许依赖方向已归档至 [`docs/architecture/module-boundaries.md`](docs/architecture/module-boundaries.md)，根计划已据此将下一步切回真实 F05/W11 技能入口 E2E。
- 范围限制：本轮关闭的是 PWF 定义并登记的活跃生产模块边界回归缺口，不等于项目金融准确性、F05真实owner全量覆盖、G3/G4/G5/G6、真实技能入口或整个产品 E2E 完成。Python 下划线命名本身不是运行时访问控制；静态规则覆盖已声明依赖与常见直连/别名路径，不声称阻止任意反射或任意 `exec`。

## 2026-11-10 共享引擎 facade 复核与主线状态修正

- **根因复核：** 已提交的 IQS 边界测试 `4328208` 依赖尚未提交的 `scripts/answer_validation.py` 与 `scripts/shared_company_ports.py`；IQS 本地引擎/任务重构也调用 StockQA、Company Agent、Agent Runtime 的版本化 facade，但这些 owner facade 当前不在各自 canonical HEAD。故之前的“模块边界已完成”只适用于边界图及静态扫描器回归，不能代表跨仓生产接线可干净检出或发布；已在 `task_plan.md`、`docs/architecture/module-boundaries.md` 和本交接页纠正。
- **本地根因修复：** capabilities CLI 改为返回消费者本地声明的最低 owner API 版本，不要求 provider 仓库先装入 `sys.path`；实际执行时仍动态读取并校验 owner 声明版本。共享引擎 preflight、扫描 preflight、原生恢复统一通过 `_company_runtime`，把 StockQA facade 的 `TypeError/ValueError` 映射为引擎公开拒绝类型；扫描静态资源上限在创建 owner runtime 前校验，避免无效请求触碰 owner 绑定。
- **TDD 验证：** 首次合跑出现 34 failed/105 passed；独立只读审查将其拆成 3 个真实根因（capabilities 子进程缺 provider import、拒绝异常泄漏、scan 静态上限检查太晚）和旧测试夹具绕过新 Runtime facade 的问题。修复后三组共享引擎/语义/finalizer/scan guard/模块边界测试为 **177 passed**。新增语义协作者版本拒绝反例。原始 owner facade 拒绝任意 `SimpleNamespace` 的反例保留；纯组合测试改用实现公开 Runtime DTO 的狭窄替身。
- **模块/题库相邻回归：** `test_module_contract.py`、`test_module_registry.py`、`test_question_manifest.py`、`test_question_sets.py`、`test_routing.py`、`test_batching_benchmark.py`、`test_question_fingerprint.py`、`test_question_library.py`、`test_question_bank.py`、`test_question_prompts.py` 为 **214 passed、236 subtests passed**。沙箱内初跑受 Windows 硬链接权限限制而无法进入部分断言；使用正常权限重跑后通过。测试 fixture 使用 `TemporaryDirectory` 并自动清理；未调用网络/模型或生产数据。
- **公共 task facade 合同与相邻回归：** 新增 `tests/test_shared_company_task_api.py`，用 synthetic owner API 验证真实版本协调先于任务构造，公开 `create_owner_task` 返回值继续交给 StockQA `validate_company_scan_task`，低于 Company Agent 2.3.0 会在创建前拒绝；2 passed，已登记在 `tests/suites.json` integration。`test_shared_semantic_replay.py` 6 passed；`test_standard_answers.py` 41 passed、8 subtests；`test_question_prompts.py` 8 passed、8 subtests；test suite manifest 14 passed。manifest测试在隔离权限下遇 Windows 本机回环 socket 限制，授权正常权限重跑通过；没有外网或模型请求。
- **canonical HEAD 核实（只读，2026-11-10 起始快照）：** StockQA `4c24789` 缺 `quick_scan_company_api.py`，该快照有 66 个已跟踪改动和 19 个未跟踪文件；Company Agent `d0280f5` 缺 `api.py`，1 个已跟踪与 7 个未跟踪；Runtime `5839ef4` 缺 `api.py`，另有 23 个已跟踪与 8 个未跟踪。之后本轮在 StockQA 仅改 `src/utils/quick_scan_shared_company.py`、`src/utils/quick_scan_company_api.py`、`tests/unit/test_shared_company_entry.py` 三个精确文件，没有整理其他变更。
- **当前判断与剩余步骤：** 本机工作树候选逻辑已通过上述定向组，但不构成 owner facade 版本的正式发布证据。等待各 owner 在自己的写入上下文完成接口提交后，固定 owner commit，在干净隔离检出进行协议版本兼容/不兼容正反例与公开 capabilities/运行接口集成；再由新的独立 agent 审查最终 payload 和相邻依赖。此项未完成前，模块化主线保持 OPEN，不切回 F05/W11，也不把 4328208 单独视作可发布完成。

### 2026-11-10 独立复审问题整改

- 独立 reviewer 指出 IQS 声明的 Company Agent 最低 API 为 2.0.0，但 StockQA facade 候选明确要求 2.3.0，造成 2.0–2.2 版本可能先通过 IQS 再被 provider 拒绝；StockQA/Runtime 更低最低版也没有 canonical 兼容矩阵证据。IQS 现将最低版本收敛到当前已观察到的候选版本 StockQA 1.5.0、Company Agent 2.3.0、Agent Runtime 1.4.0，并测试精确下限接受、低一个 minor 拒绝及更高兼容 minor/patch 接受。定向共享引擎、语义、finalizer、scan guard 与边界组 **177 passed**。
- 同一复审发现 StockQA `read_shared_company_config` 用 `task.py`、`port.py` 等私有实现文件存在性判定 provider 可用，内部重命名会在公开 API 不变时误拒。已改为校验配置根目录；证据校验、共享扫描、checkpoint loader 均经版本化 `company_agent_public_api` facade，缺失 API/owner 包统一报稳定错误，运行时仍核对导入来源。新增配置根、错误版本/缺操作、恢复 loader 和 source-origin 正负例。StockQA `test_shared_company_entry.py` 在 `%TEMP%` 隔离工作目录 **37 passed**，`test_quick_scan_module_boundaries.py` **24 passed**（合计61）；临时日志/pytest cache 已清理。
- **仍未关闭：** 上述 StockQA 修复还在未提交 owner 工作树，不能视作 canonical 发布；StockQA、Company Agent、Runtime API facade 也尚未进入各自 HEAD。根 IQS 的 clean checkout 仍缺 `scripts/answer_validation.py` 与 `scripts/shared_company_ports.py` 所对应的可发布闭环。不能推送或宣称全项目模块解耦完成，需等 owner 正式提交后再做锁定版本的 clean integration 和独立复审。
- **独立复审结果：** 新 reviewer 对 IQS/StockQA 本轮候选代码及补充合同测试 ACCEPT，未发现剩余 P1/P2；它核对了版本正反例、public facade 调用、错误归一、空根目录、owner 来源正反例、语义版本拒绝、任务工厂消费链及隔离测试。该 ACCEPT 仅覆盖候选代码与当前工作区，不替代 owner canonical 提交后的 clean checkout 集成审查。
- **补充合同测试复审：** 针对 reviewer 提出的语义协作者版本拒绝和 task factory/public consumer 组合缺口，已增加两个语义版本拒绝参数、owner task 合成正反例及 integration-suite 登记；聚焦组复跑 177 passed、任务 API 2 passed。独立 agent 对补充增量 ACCEPT。

## 2026-11-10 owner facade 候选联测与提交

- **IQS 本地提交：** 将共享引擎 ports、答案验证拆分、版本协调、任务 facade 合同及对应测试/PWF 精确提交为 `bb20529`（19 个文件）。`git diff --cached --check` 通过；只暂存本项路径，工作区其他并行文件未纳入。由于 owner facade 尚未固定提交，此 commit 暂留本地，未推送到 `origin/master`。
- **owner 工作树快照：** StockQA `master@4c24789`、Company Agent `master@d0280f5`、Runtime `codex/agent-run-02@5839ef4`。当前均有未提交变更；三份 facade 分别在 StockQA `quick_scan_company_api.py`、Company Agent `api.py`、Runtime `api.py`，协议为 `1.5.0/2.3.0/1.4.0`。它们仍不属于 canonical HEAD。
- **隔离候选测试：** 从系统临时工作目录运行，关闭 pytest cache 和字节码写入、各自使用独立 `basetemp`。StockQA `test_shared_company_entry.py` + `test_quick_scan_module_boundaries.py` **61 passed**；Company Agent `test_public_api.py` + `test_public_task_port.py` **11 passed**；Runtime `test_public_api.py`、`test_public_task_contract.py`、`test_company_agent_api_compat.py`、`test_module_boundaries.py` **38 passed**。早先默认 `%TEMP%` 中有非本项目的 `pdb.py` 造成 pytest 启动 INTERNALERROR；改用新建空临时工作目录并禁用 debugging 插件后通过，源仓无测试输出写入。
- **跨仓 smoke：** 以只读 `PYTHONPATH` 同时加载当前三 owner 候选和 IQS adapter；`current_owner_api_protocols()` 返回 StockQA 1.5.0、Company Agent 2.3.0、Runtime 1.4.0，且 adapter 中所需的公开函数均可解析。未创建 owner task、未访问公司数据库、模型/API 或网络。
- **扩大离线回归与夹具修复：** 19 个 IQS 测试文件整组通过 **454 passed、244 subtests passed**。其中 `test_actual_stockqa_cli_emits_manifest_question_receipt_and_is_accepted_offline` 在全新临时 cwd 首次揭示 StockQA logger 预期 `logs/` 已存在；只在该隔离测试的 `TemporaryDirectory` 中建目录，单测 `1 passed`，再跑完整组无失败。该改动只使测试在干净环境稳定，不修改外仓 logger；日志与其他临时结果自动清理。
- **结论与下一步：** 本机候选在单工作站组合可导入且定向测试绿，但 owner 工作树仍有并行改动，不能据此提交/推送他人全部改动，也不能宣称干净部署完成。独立跨仓 reviewer 已复审三 owner facade 和总控消费者，候选接口/测试 ACCEPT、无 P1/P2；整体接线仍 OPEN。待取得固定 owner commit，再在新建干净临时检出中运行版本协商、公开调用与拒绝不兼容版本的正反例，最后独立复审集成结果。

## 2026-11-10 Runtime/StockQA 模块边界复审整改

- **Runtime 复审指出的根因已修：** 发布脚本原来在测试内部、fresh checkout 和最终发布门重复启动单元/集成套件。现把完整套件的唯一执行点收敛到最终临时 clean clone；pin 回归和 fresh-checkout 子流程只核对元数据，不会嵌套重跑套件。clone 保留 `.git`，Git 绑定测试不再静默跳过；gate 按 handoff 中记录的通过数核对实际结果，并拒绝任何 skipped。README 也改正为默认命令只跑 `tests/`，集成套件独立运行。
- **Runtime 边界探针补齐：** private facade 检测现在覆盖 `vars(module)[...]`、`vars(module).get(...)`、`__getattribute__`、lambda 捕获/参数、推导式目标作用域和导入别名在模块级重新绑定的情况。共享词法作用域映射替代两套不一致的局部判断。Repository-wide offline fixture 同时屏蔽 `create_connection`、`connect`、`connect_ex` 和 UDP `sendto`。
- **测试清单恢复真实覆盖：** 交付 JSON 原来统计完整216单测，却只列出15组且漏列13个已收集模块。现在按职责把全部28个单元测试模块纳入16组；`verify_document_claims.py` 检查每个模块恰好出现一次、各项数量准确且总和匹配。`sync_metadata_latest.py` 改为以结构化 handoff 为源更新文档，不再用正则改写生成器源代码。当前收集数为216单元、7集成；文档声明验证通过。
- **StockQA owner API 候选补全：** 版本化导入边界检查纳入 known-outcome journal 和 owner-budget-continuation 两个现有 owner；公开导出清单涵盖消费者实际使用的 DDL/操作/投影，并提高对应次版本。star import 也不能绕过合同检查。Research Output 的精确表依赖恢复了 session DDL 引用的 `work_item` 外键。
- **测试证据：** Runtime `test_module_boundaries.py` 与 `integration_tests` 合跑退出码0（13+7项）；`verify_document_claims.py` 退出码0；运行时/元数据脚本 `py_compile` 通过。StockQA `test_quick_scan_module_boundaries.py` **49 passed**，`test_research_visible_output.py` **34 passed**。没有调用模型、网络搜索、数据库或生产名单。
- **仍开放：** 上述都是隔离候选工作树。Runtime/StockQA facade 及 Company Agent facade 尚未全部进入 owner canonical HEAD；下一步先由独立 reviewer 对本轮整改复审，再在 owner提交固定后运行一次 clean-clone 全单元+集成验收。模块化主线尚未完成，不能把候选绿测称为已发布跨仓接线。

## 2026-11-10 Runtime 边界复审补充与当前状态

- Runtime 独立复审对边界扫描器提出了三轮相邻反例：`builtins.getattr` 的导入/赋值别名、模块级函数/导入/普通赋值重绑定、函数本地及条件分支中的 facade import；并指出推导式目标若被当作外层模块别名会产生误报。均先增加反例复现，再改为按模块/函数/控制流顺序传播可识别别名，并单独跟踪推导式目标作用域。
- Runtime 候选验证：`tests/test_module_boundaries.py + integration_tests` **22 passed**；当前完整收集为 **218 unit / 16 groups / 28 modules + 7 integration**。`tools/verify_document_claims.py` 现检查摘要、命令输出和集成数字之间不能互相矛盾，运行通过；`git diff --check` 和相关脚本 `py_compile` 通过。没有运行整套单测/发布门，也未调用模型、搜索、生产数据库或真实公司流程。
- StockQA 同一候选边界/答案恢复组合 **84 passed**，独立复审 ACCEPT；版本化 `known_outcome_journal`、`owner_budget_continuation` 已进入导入/导出检查。StockQA 和 Runtime 当前改动仍在 owner 工作树候选状态。
- **当前结论仍 OPEN：** Runtime 最后一次独立复审待回；StockQA、Company Agent、Agent Runtime 的 facade 还未同时固定为可干净检出的 owner commit。上述边界测试通过只证明当前已登记源码路径及反例，不代表 Python 运行时沙箱，也不代表跨仓发布/生产接线完成。

## 2026-11-11 Runtime namespace boundary 末轮整改

- **新的独立反例：** reviewer 在源码扫描器上复现了 `vars(api)`、`api.__dict__`、`getattr(api, "__dict__")` 先取模块命名空间、再读取私有项时不报违规。TDD 先增加这些反例并确认 RED，再让 namespace 获取本身成为违规；同时识别 `from builtins import vars as ...`、`builtins.vars` 及其简单别名。
- **接口合同：** `CompanyAgentOperations` 新增精确 dataclass field 顺序断言；Runtime `api.__all__` 新增精确 allowlist 断言。候选 Runtime `acceptance-traceability.md` 将“private implementation isolation”改为源码级 import/access 边界，并注明它不是运行时沙箱。
- **最终定向验证：** `tests/test_module_boundaries.py`、`integration_tests/test_current_sources.py`、`tests/test_company_agent_api_compat.py`、`tests/test_preflight_before_claim.py`、`tests/test_public_api.py` 合计 **36 passed**。反例首次 RED，修复后全绿；DTO 精确字段断言并入既有测试，未额外增加测试节点。
- **独立审查：** `/root/runtime_full_diff_audit` 对该整改 **ACCEPT**，其复跑时为包含独立 DTO 字段测试的37项版本；随后将同一字段断言并入既有测试，最终定向组合为36 passed。审查其 alias vars 与 dunder getattr 相邻场景，未发现本轮残余 P1/P2。审查限定于当前候选差异，不代表 full owner suite、canonical 发布或 clean-checkout 跨仓集成通过。
- **跨仓最新快照：** Company Agent 本地 `master@793bfbc` 已含 `api.py`，计划里的 `d0280f5` 已过时；当前本地 refs 没有 `origin/master`，远端发布待确认。StockQA `master@4c24789` 的 HEAD 不含其 facade；Runtime `codex/agent-run-02@5839ef4` 的 HEAD 不含 `api.py`，仅候选工作树存在。故完整模块化结论仍 OPEN。
- **范围说明：** Company Agent DTO 是常规消费者使用的有界操作集合，不是恶意 Python 隔离设施；底层函数对象仍可被 Python 反射。静态边界回归保护已声明的源码访问方式，不宣称阻断任意 `exec`/introspection。
- **较大测试组复核：** Runtime `tests/` 完整套件曾尝试运行但未通过。根因包括：fixture 调用 `import_frozen_modules()` 却未导入（已修）；集成收集已是 7 项而断言仍写 6（已修，15 项关联测试通过）；handoff 记 218 项而当前实际收集 219 项；当前冻结 pin `28d20b2` 与分支 HEAD `5839ef4` 及未提交交付差异不一致。Windows 默认深层 temp 下 4 个 copy/relocation 反例触发长路径错误；改用 IQS 根下短 basetemp 后，这 4 个反例全部通过。未将整仓 suite 报为通过，也未刷新未冻结候选的发布 pin。
- 独立 reviewer 对测试 harness 收尾另外核验 `integration_tests` **7/7 passed**，确认 root conftest 初始化和 socket denial 生效；此项不替代完整 owner suite 或冻结 pin 验收。

## 2026-11-12 八个外仓包并线与合并后验证

- **逐包合入并回收工作树：** StockWiki `f2bc73f`、Company Agent `ba54694`、Industry Research `2b2fc54`、Theme `99ac207`、StockQA `749f6e1`、Runtime `f58e0c4`、UI `3ed6391`、Dashboard `3e401cf`。均在真实源仓做 fast-forward；未做 cherry-pick 后重复叠加，也未创建新远端。
- **验证：** StockWiki 169 passed/1 skipped；Company Agent 38 passed；Industry Research 232 passed/105 subtests，独立 reviewer ACCEPT；Theme 合并后 96 passed；StockQA 合并后 100 passed/1 skipped；Runtime 合并后四组分别为 210 passed/1 设计 skip、current 25 passed、legacy 7 passed/1已知历史 skip、integration 6 passed；UI 298 OK/6 skipped，静态边界 22 passed/1 skipped；Dashboard 公共替换/边界组 367 passed。
- **总控定位到并修正 Runtime 本地字节不一致：** `tests/test_batch_carrier.py` 和 `tests/test_research_response_taxonomy.py` 工作区有 CRLF，提交 blob 为 LF；仅归一为已提交字节，未改语义。另把 pytest TEMP/TMP 放进各仓忽略的隔离目录，解决自测临时目录导致字节完整性测试误跳过；四套 Runtime 测试最终全部通过。
- **只清理本轮包树与本轮测试根。** StockWiki 数据/日志、StockQA 10 个个人或历史 untracked 项、UI 两份生成 JSON 与 `.codegraph`、Dashboard 的 SQLite、probe 与 memory 文件均保留；Theme/QA/RT/UI/DASH 合并后源仓已有状态逐项核过。没有动生产数据库、名单或调用收费 API。
- **尚未完成：** MC-IQS 主线还有 28 个已知 tracked WIP，尚未执行最终组合；Dashboard 交接诚实披露 C38/I7 组合依赖和 4 个相邻场景的显式覆盖欠项。八个包并入只是准备好可检出的 owner 版本，不是全项目解耦完成。下一步先由 MC-IQS 集成 StockWiki C38，再实现 C5 snapshot/启动公开边界，接着做 QA/CA/RT 真实组合和 I1–I7，补上 Dashboard 相邻场景测试，最后进行一次独立集成审查。

## 2026-11-12 I5 研究消费者正向组合接续

- **误拒根因：** I5 首次集成输入把 Industry 的 `consumer_id` 写成测试专用后缀 `industry-research-i5-test`。StockWiki 内部为 facts 查询复用的 `get_profiles` wire 正确按 `schemas/quick_scan/query-v2.schema.json` 限制消费者 ID；Industry 的生产默认值是 `industry-research`。将夹具改为规范 ID 后，未发现 StockWiki 对真实 Industry consumer ID 的产品误拒。
- **实际消费者修复：** StockWiki 当前 capabilities `1.2.0` 返回版本化 `schema_version/protocol/result.supported_query_wires` envelope，而 Industry 之前只读旧 `additional_query_wires`。Industry `tools/quick_scan_client.py` 现识别新旧 envelope、校验版本与协议、要求 facts query 和 export 两个操作均声明，并从 result 读取 producer readiness；保留旧格式兼容。TDD 补非字符串版本、版本不匹配、protocol 不匹配三例（修复前 **1 failed / 2 passed**）；修复后 `tests/test_quick_scan_client.py` **86 passed / 11 subtests passed**。
- **跨仓真实接口验证与发布：** `tests/test_research_consumers_owner_integration.py` 通过真实 StockWiki CLI、Theme 与 Industry 当前公开客户端，使用同一隔离合成事实库完成 capabilities、查询、分页、关闭并重开 consumer 后按 snapshot 回放及导出；测试前后 owner workspace 全文件 SHA-256 一致。I5 集成 **1 passed (60.42s)**。独立 reviewer `/root/review_modularity_current` 接受 consumer ID 夹具修正；独立 reviewer `/root/review_i5_industry_capabilities` 对 Industry 修复 diff 返回 **ACCEPT**。Industry 提交 `67e078b` 已推送既有 `origin/main`，远端 `refs/heads/main` 核对为同一完整 SHA `67e078b9fbab47a5d237e628752814071dbfa57f`；owner 工作树 clean。无模型/搜索请求、生产数据库写入或名单变更。
- **剩余范围：** 已完成 I5 正向 query/cursor/capture replay/export 的当前 owner 组合。I5 错身份/错 operation 反例及其他 I1–I7 场景仍需逐项确认；这不代表全项目模块化收尾。

## 2026-11-13 I3 根因修复与复跑

- 隔离诊断确认历史语义读取调用实时权限 CLI。已分离历史归档读取和任务构造，工作范围校验沿原注册工作项读取。StockQA owner port **18 passed**，任务工厂 **11 passed**。两组均先复现针对性反例。独立审查确认原输入与归档绑定、owner 替换反例、领取和实际请求前检查仍在。
- SQLite 原注册复用同一写入逻辑，去除重复权限调用，保留提交前撤权整笔回滚。注册与并发组修复前 **2 failed / 23 passed**，补上回调不可篡改原输入的反例后 **26 passed**。独立复审通过。隔离样本注册阶段由约 **70 秒降到 41–50 秒**。
- 第一轮混合态隔离 E2E 在约 215 秒进入共享引擎并得到未完成结果。此轮使用的是历史读取修复后的快照，尚未包含任务工厂和注册事务改动。脚本环境无付费 API，临时运行根已清理。待同一用例验证原生回执、封包、公开导入和 ACK 幂等后再签收 I3。
- 后续端到端在原生 MiMo SDK 实际使用的 HTTP 入口注入脚本，首题已收到并完成。第二题被未结算预算拦下，夹具此前没有传计价函数。补上已核实用量的合成计价，超时请求仍保持未结算。相关回归组合 **116 passed**。恢复路由身份、只读投影与原 checkpoint 重封的 **11 项**另行通过。
- 第三轮隔离 E2E 在 **229 秒**复现完整中断状态：首题回答已保存，第二题原生请求超时并持久化为未知，Agent 检查点仅有第二题待处理 intent，后两题尚未派发。恢复准备随后拒绝生产者写出的 `provider@…` 端点标识，因为旧读取方只接受 `model@…`。这轮临时根已清理，付费请求为零。接续仍须验证兼容旧记录，以及在 Agent 回执尚未写入时从 StockQA 已持久化回答恢复。
- StockQA 将脱敏端点标识与原生回答、回执一起落盘，保留旧版已验证的端点标识，Runtime 从公开 owner 接口取同一标识。下一轮已确认两边记录一致。修正 Windows 子进程审计后，公开恢复 CLI 返回 0，已恢复首题、将第二题列为未知暂停、后两题列为未发送，`API_requests=0`。该轮断在隔离夹具将 Windows 内部 loopback 初始化计作网络尝试，尚未进入 StockWiki 导入。Runtime 相关定向 **37 passed**，StockQA 有序恢复与发布定向 **66 passed**，覆盖范围可与早期组合重叠。下一轮复测只忽略该系统初始化事件，外层仍禁止套接字。
- 同一隔离库的 I3 公共路径最终 **1 passed / 240.24 秒**。真实 StockQA/Company Agent/Runtime/StockWiki 代码，只有 MiMo HTTP 脚本化。首题从原生回答恢复后封包并导入，第二题的原生未知 intent 触发暂停，后两题仍未发送，其中一题已准备但无发送意图。重复恢复及同一包导入、ACK 均保持原回答、包字节、观察和回执，StockWiki 只有一条原入库回执。两次恢复模型请求均为 0，隔离目录已清理。StockQA 端点和恢复相邻组 **55 passed**，公开合同组 **32 passed**。Runtime 本地提交 `369a44b`，无远端。StockQA 注册事务与任务构造修复 `b1e9be7` 已核实推送到既有 `origin/master`。固定来源 I1–I7 仍待复跑。
- 独立复审发现旧 `model@` 空端点标记会被拒绝。现按原样兼容已验证的历史标记，新的原生回执仍只保存脱敏标识。旧记录回归单独通过，独立复审确认无发布阻断。StockQA 较宽定向组合 **237 passed / 1 skipped**，跳过项是需要 IQS 纯合同运行环境的既有组件用例。StockQA I3 提交 `f6897ac5c437f6baa36bae336d2c47a7e1722ad1` 已推送并核对 `origin/master`，提交钩子通过。固定来源组合复跑时使用该提交和 Runtime `369a44b`。

## 2026-11-14 Dashboard owner 改进项接入与分仓实施启动

- 读取两份 2026-11-09 汇总：`investment-dashboard/handoffs/owner-requests/invest-quick-scan/IMPROVEMENTS.md` 与 `investment-dashboard/handoffs/owner-requests/stockwiki/IMPROVEMENTS.md`。原始文件保留，未复制过时结论覆盖现状。
- 与当前主计划、模块测试及 StockWiki Phase 40 记录交叉核对。SW-2 仍有旧 universe 写路径需要核对 schema-7 request authority；SW-4 的旧符号 `SCHEMA7_ROOT` 当前源码搜索未命中，交给 owner 代理进一步核实，不先改；SW-5 已有完成记录。IQS-3 当前 Dashboard 执行测试已经显式选择并验证 `bundle_id`，需要确认公开 IQS wire 端到端形状后再决定是否仍需实现。SW-1/IQS-1 的旧公司结果存在完整性/manifest 问题，但历史 36 题实跑只有 2 个 scored，不能制造齐全假象。SW-3 是真实研究数据缺失，非查询读链故障。
- 已将条目按 StockWiki membership owner、StockWiki company-result owner、IQS question/result owner、IQS execution owner 四条分离工作线写入 `task_plan.md`，明确测试、非重叠目录和未完成状态。四个独立 agent 已启动；本轮不运行收费 API、不改业务数据库/名单。
- 首轮代码对账发现两项需要扩大准确测试/源文件范围：StockWiki schema7旧 mutation 绕行涉及多处既有调用用例；IQS诊断题缺 `construct_id` 是正式诊断语义，不能由 projector 伪造。已按最小必要范围允许相关测试/诊断题定义和版本化 release lifecycle 文件参与，仍禁止跨 rubric 混合或真实数据/API操作。
- StockWiki 当前状态在并行进程中有变化：最初只读快照含两项 membership tracked edits，owner agent 再查时这些 tracked edits 已不在；其 untracked 研究数据库、UI 绑定数据、日志及 `runs/c16b` 均保留。两个时间点如实记录，不推断变动归属。
- IQS execution 线确认 IQS-3 已解决，IQS-2 的 bundle preparation 软件路径已有而实际主体登记状态需通过 owner identity 查询，IQS-4 的 paid sample 尚待真实运行。IQS-5 的完整目标组合 `tests/test_dashboard_execution.py tests/test_dashboard_unusable_recovery.py` 以隔离 TEMP 复跑 **169 passed / 1 skipped**；仅显式 UTF-8 读取 fixture 的测试修复，无产品代码变化。所有临时目录已回收，未发送模型/API请求。
- StockWiki membership 线首轮回归时核心套件 **45 passed**，随后完成最终复跑：Universe/candidates/maintenance/backup **46 passed**、UI E2E **11 passed**、static checks 全通过。SW-4 当前 `--root` 参数和隔离 `tmp_path` 用法已找到，旧固定 checkout 依赖未复现；query-v2 因缺 C06 runtime 被环境跳过。
- StockWiki company-result v2 线与 IQS producer 线已确定精确 wire：owner request manifest 带原 frozen release及canonical SHA，按 `(rubric_version, aggregation_role)` 生成分组，每条 observation ref 绑定原 package/release/question hashes；无跨组或公司汇总。StockWiki agent 正在为 v2 正反例写 RED 测试，尚未改生产实现；IQS producer 等 exact wire 已交付后实施。
- V2 双仓实施已统一 `construct_id=null` 的合法语义：`diagnostic_only`、`information_only`，以及仅由新冻结题库 `comparison_role=context` 映射产生的 `context_only` 可为空；三者都不参加任何评分聚合，core scoring roles 必须有非空构念。双方已固定 `lineage_provenance` 字段和 hash 的绑定原则，分别实施/测试；保持 `source_release` 原样，完成后总控做跨仓契约验证和独立审查。
- IQS producer 已实现冻结 metric schema 1.1.0，并通过临时隔离路径验证 publisher 在 elevated 环境下可成功写不可变内容。生成新 package `pkg_07dc0d62fd89a008c474ffae0cb9be5ad7411f67333e81f1a12751cb4693a703`；旧 package/release 未改。接下来核对新包及 current pointer 的实际 diff/hash，完成 producer/owner端 GREEN 后再做跨仓测试与独立审查。
- StockWiki membership 首轮 wrapper 改动的专项结果为 **46 passed + UI E2E 11 passed + static checks PASS**。随后独立复审在 `QuickScanStore.save_member()` / `save_member_in_transaction()` 发现尚可绕过 schema-7 request receipt 的公开写口，因此 SW-2 重新标为 OPEN，owner 正按 TDD 把防线下沉到 store transaction 边界；首轮结果不再作为最终验收。未改业务库/名单，StockWiki 外仓数据及并行工作树保留。
- SW-2 第二轮独审还识别到 `admit_with_intent()` 这一自动纳入路线。当前唯一生产调用是已显式启用的 `apply_auto()`，其策略/身份判定及member/history+scan-intent原子写与手工 membership request 分离；本线按独立自动 authority 保持，不把它改成手工request，并需验证裸store入口不能绕过条件。另有6个C06/owner测试文件9处 `save_member` fixture已获总控最小范围扩展授权；自动审查首拒系旧范围声明，若再拒将停止并报告。
- **证据更正（2026-11-14）：** 旧记录中的 `124 passed / 184 subtests` 属于先前 2026-11-04 的其他 query/compatibility 回归，不覆盖本轮 V2 producer 改动，不能作为本项验收证据。当前 producer 独立复跑见本页末尾 2026-11-14 收口记录。
- V2 独立复审又发现 P1 跨仓冲突：真实 IQS score source projection不含 `comparison_role`，StockWiki初版却强制该字段存在并等于provenance，现有合成owner fixture错误地手工填充而漏测。StockWiki V2 owner正在补真实producer形状RED/GREEN；因此此前22/90 owner结果不作为验收，待修复后重跑并做公开接口跨仓验收。

## 2026-11-14 Dashboard owner 改进项分仓实施验收进度

- **IQS question/result owner（IQS-1代码侧）：** 新的 metric contract 1.1.0 与 package `pkg_07dc0d62fd89a008c474ffae0cb9be5ad7411f67333e81f1a12751cb4693a703` 已通过 `load_package`；旧 1.0.0 frozen package/release lock 保持原样。新增 `company_assessment/2` 投影绑定原 source release、逐题 metric/role/hash provenance 和非重叠 rubric×aggregation-role lineage groups；不写回 source release，也不计算组间/公司总分。`tests/test_company_assessment_v2_projection.py` **13 passed**；与 `tests/test_question_manifest.py` 合跑 **16 passed、2 subtests passed**。独立复审 ACCEPT，新增递归反例确认 `comparison_role` 只能出现在 `manifest.lineage_provenance.question_mappings[*]`。`tests/test_question_sets.py` 在正常权限下用项目内唯一 basetemp **70 passed、174 subtests passed（142.60s）**，临时目录已自动清理。旧笔记的124/184是此前其他回归，已纠正，不能当本轮证据。
- **StockWiki company result owner（SW-1代码侧）：** 完整 owner 文件 **107 passed**；独立审查 ACCEPT。将当前 IQS active package 经真实 `create_company_assessment_v2()` 生成53题 envelope，在隔离 StockWiki workspace publish 并读回成功；score source未人为增加comparison_role，role分布 quality_core18/growth_core3/valuation_core3/diagnostic_only12/context_only17，内外 SHA 相符。没有生成或导入答案、没有写生产workspace。**这只关闭协议/owner代码互操作，不关闭真实36题历史数据缺口**：旧 owner 观察仍仅1/36、另一历史结果2个 scored，不伪造或重绑定历史输出。
- **StockWiki membership owner（SW-2）：** TDD最终组合 **75 passed/66.08s**、static-only ALL CHECKS PASSED；schema6自动准入正例与schema6/7意图失败回滚先由旧守卫复现RED，再完成修复。最终独立reviewer对新增六例复跑 **6 passed** 并 **ACCEPT**：手工schema7仍需request receipt；自动准入支持schema6/7且member/history/intent原子；schema5/future8同事务拒绝且零写；save_member迁移竞态与四个universe旧入口保护均通过复核。最终23个精确文件已提交StockWiki本地 `0450506fc94adbfecd33001c244221a42ba0a00d`。
- **SW-2 UI E2E最终验证：** 普通沙箱里 `sync_playwright().start()`停在driver握手；以正常本机权限在新的隔离 `.tmp-sw2-ui-final-run` 执行同一个2000实体分页用例，最终 **1 passed/27.73s**。Seed 15.2s，2000实体筛选/分页断言4.9s；总计17条loopback HTTP请求，无外网。测试生成的截图和临时数据库随唯一basetemp一起清理。故之前180秒中断是沙箱对子进程/driver的限制，产品浏览路径已通过，不是业务失败。
- **StockWiki SW-3/查询部署范围：** 真实 research 生产数据本轮未重查/未写；不得用合成记录替代，须由owner正常研究流程产生。SW-4 的固定 checkout 路径问题未复现；query-v2测试因缺C06 runtime仍为环境skip，未当作通过。
- **IQS execution 审计：** bundle preparation路径存在；本轮未读取正式主体映射来证明药明/阿里/MDB的实际bundle登记，IQS-2保持未核实。IQS-3的显式bundle选择及其绑定关系已在IQS侧通过；IQS-4真实付费formal sample未运行。测试可移植性IQS-5已修复（Dashboard execution/recovery组合169 passed、1 skipped）。审计另发现固定Dashboard `3e401cf` 的 M8 恢复查询在 owner_job_id/command_id 格式重叠时会误接受未知任务且无原command链接；这是Dashboard owner侧新的I7集成缺口，未在本分仓实施中修改，需列入后续收敛。
- 本轮均未调用收费模型/搜索、未读密钥、未写生产数据库/名单。提交与远端状态以紧随其后的提交记录为准。

### 2026-11-14 IQS producer发布与SW-2最终复审

- **IQS提交/推送：** `a8df5b99a600cc698a100d4d8bbe7ae15178615d` 将公司结果V2 producer、1.1.0冻结题包/current指针、字段唯一位置测试及本PWF精确提交；已普通快进推送至既有 `origin/master`。`git ls-remote` 与本地HEAD均为该SHA。提交前 `git diff --cached --check` clean，current/package JSON可解析。其他并行修改（包括 `docs/implementation/parallel-lanes/packages/2026-10-10/README.md`、`tests/test_question_sets.py`）和大量untracked研究/运行材料未暂存、未清理。
- **SW-2最终独立结论：** 第三轮reviewer **ACCEPT**。schema6/7自动准入、schema5/8拒绝、schema7手工request receipt、`BEGIN IMMEDIATE`内版本检查和迁移竞态保护均有直接测试/复审；6项新反例复跑6 passed，核心Store/Universe/Candidates/Maintenance/Backup组合75 passed，static通过。
- **E2E环境纠正：** 普通沙箱尝试时，2000实体seed正常、Playwright同步driver的 `.start()` 卡在Chromium之前，因此该次只能记“未执行”，不能判业务失败。随后以正常权限在唯一隔离basetemp运行同一个2000实体UI用例，**1 passed/27.73s**、17条loopback请求；截图/数据库随basetemp清理。SW-2 UI浏览路径现有最终正向证据。
- **StockWiki提交：** 已将SW-1 V2 owner、SW-2 membership根修、两份子PWF、golden和精确测试文件提交为 `0450506fc94adbfecd33001c244221a42ba0a00d`（master）。只暂存本轮23个文件；untracked公司研究SQLite、Dashboard onboarding/research-binding、logs及runs/c16b均未触碰。StockWiki当前没有配置remote，所以仅本地提交，不创建新remote。
