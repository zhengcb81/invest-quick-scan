# 2026-11-21 中微未发送失败与门禁简化

本页记录已发生事实和本轮处置，不是扫描准入凭证。用户最新分工：本线程专注过度复杂设计、重复检查和接续；F4日志工作交其他harness。其他harness的三市场正式扫描与Dashboard返回卡不由本线程代做。

## 原始失败

|项目|实物事实|
|---|---|
|公司|中微公司，XSHG:688012；entity `ENT_99deceb6-f58a-48b1-bd6b-437621015d76`|
|原执行|`run-5305efa0a466482fa2a187ed2b37699e`，12:16:31 UTC启动|
|原准备|`prepare_a862db6646ce4fd3b8b148f407231063`；实体26题、挂牌2题，只重评原28个空分|
|失败题|`IQS_13`、`IQS_14`，同一 `PACK_95995090e3d54b89a04714c45873f5a2`|
|失败保存时间|2026-11-21 13:09:05 UTC。13:16是随后观察进程退出的时间，不能解释成一小时执行超时|
|已到阶段|原pack和attempt仅到`prepared`；主体登记分别于13:05:28.664、13:07:16.200成功|
|未发生|无send intent、预算attempt、physical outcome、response、visible-output journal；不能说模型拒答、搜索失败或已产生这两题费用|
|原错误|输出只有`QuickScanWorkPersistenceError`，原日志未保留更深cause。SQLite锁/权限错误均未证实，不能事后补成根因|
|当时租约|分别到14:00:07.893、14:00:55.943；13:09失败时尚未过期|
|其他工作|新IQS_03–12共10题已保存（8有分、2按原规则为空）；原8个有分题没有新增attempt。其余14实体题及2挂牌题尚未发送|

本机原件位于`runs/amec-rescore-20261121/execution/`：同名原run的`result.json`、`process.log`及实体范围`after-dispatch-dashboard-a862db6646ce4fd3b8b148f407231063-1.json`。原件和数据库不提交到Git，PWF只保留以上必要定位与事实。

## 已完成的安全接续

1. 原公开`tasks/{run}/seal`完成冷恢复，API=0、paid_dispatch_started=false。前10题原答仍在，没有给未发送两题补造答案。
2. 原公开store接口在同一事务内对IQS_13/14执行`release_unsent`；两题回pending。原pack字节投影和10个checkpoint哈希不变，无新attempt、API或policy变更。摘要在`runs/amec-rescore-20261121/released-unsent-summary.json`，不能把它当需重复执行的日常脚本。
3. 原`tasks/deliver`作业`deliveryjob_0fdf528869cce3d0cfe70eb40c7a3868`于14:05:35 UTC完成10/10封存包ACK，error_codes=[]，0模型调用。作业整体partial如实表示原范围其余16题尚未就绪；并非拒绝已有结果。
4. 本线程操作脚本首次错误使用不存在的GET单delivery-job入口，得到405后退出；修正为公开jobs列表并继续同一持久作业，没有新建模型调用或另起重复导入。这是操作脚本错误，不归咎产品。

当前实体10已入库+16 pending，挂牌2 pending；旧36题正式快照`cas_6cab1b94d8f45d42c750`和原8题/资料日保留。尚未登记本轮新完整快照、尚未完成28题/UI/冷恢复终验。

## 已证实的设计负担

真实生命周期、原生SQLite和owner CLI/HTTP替身的定向RED测得：普通两题包执行26次StockWiki CLI（10次current_permissions、14次anchor、2次必要register）。此前“约32次”是包含外围/首次加载的估计，本轮以该可运行计数为准；调用重复已证实，但不是13:09历史错误原因的证明。

收敛为固定绑定在加载/本地会话核验；两题各登记一次主体；收费intent前一次实时权限核查；原生账本原子处理预算、lease和防重复。同一permit消费不重新审批，下一次真实收费仍fresh检查。外搜/MCP在各自收费intent前核对，不漏计实际请求。

已付保存/水合/复用不查今日新发权限；明确未发送失败归还原任务；已发送或结果未知沿原attempt核对。清理应复用`QuickScanWorkStore.release_unsent`这个状态owner，避免在transport再复制一大份状态证明或依赖`prepare()`已经成功返回。

## 验证与仍在收口的部分

- 首轮未发送恢复：作者65项通过；非作者另一组合63项通过并ACCEPT。二者不同，不相加。
- 初版去重及single/pack恢复：作者156项/67.20秒；专用31项通过，计数已为3次（2 register+1 permission）。该轮带着当时F4 core候选，F4现已安全拆出，最终组合仍需按现行源树验证。
- 独审又用3个真实native fixture复现`prepare`提交前抛、提交后返回前抛及begin输入失败：0HTTP但仍leased。归因是清理依赖已返回prepared对象、前置验证在清理边界外；正收敛到原binding和原public store统一判断，不增加异常名门禁。
- 该3项及provider在begin前失败已在同组38项转GREEN；直接相关181项通过。最终独审另用原生夹具+真实typed uncertain异常复现包装遗漏：`except Unknown: raise RuntimeError()`的隐式`__context__`未被沿`__cause__`的旧代码看到，导致本应保留的未知变为pending。0实际HTTP；修复方向是在既有interfaces放一处有界causal遍历供各层共用，而非按包装文字加规则。
- 公开1.3 Protocol曾把新`validate_session`列为required，旧结构端口会失去兼容性；当前原生实现未因此拒绝，但设计需保持旧合同。尾改已采用可选本地验证能力、旧`check`fallback，不抬版本门槛；统一有界cause/context遍历也已覆盖隐式/from None/双link，原支付未知保持。
- 最终尾改短组 **48 passed / 30.54秒**：两新daily文件43项、compat2、CIplan3。两套已进原默认CI，旧SQLite缺细节仍能归还。非作者此前17项、最后10项/5.48秒及public API3合法对照通过，最终**ACCEPT**，本节点无P1/P2；测试计数有重叠，不相加。
- 全部测试只用独占短临时目录、合成SQLite/传输替身，无API或生产库测试；已结束测试临时根清理成功。正常提交钩子规范行尾/格式后发现SQLite常量的3.10类型兼容尾项，改为已校验的原生名称分类；7例/12.05秒通过、非作者认可，随后所有原钩子通过，无跳过。
- 发布为StockQA `f69913c5f05205abc4f12e05d173a1a704ffec31`，20文件（10源码、7测试、3份模块PWF），既有`origin/codex/qa-content-filter-resolution-01`推送并核对同SHA。门禁软件节点完成；真实剩余题、新登记和UI尚未完成，不据此改签。

## F4交接边界

F4指定coverage/settlement/lineage场景已上线，不等于任意真实扫描异常都自动入反馈。已查明原core压掉原因链、部分owner CLI无本地错误定位、IQS进程收尾把可选日志与drain/wait绑在一起。这些发现不会在本线程扩成日志框架或扫描门禁。

已做但未签收的F4代码、测试和开放P2保存在[本机交接目录](C:/Users/郑曾波/Projects/invest-quick-scan/runs/amec-rescore-20261121/f4-handoff/README.md)。F4-only补丁经`git apply --check`通过，已从活跃QA源码剥离；当前core与恢复作者独立重构的SHA一致。IQS新增8个RED测试已移出活跃tests，StockWiki日志源码未修改。由其他harness接续，不把日志、追踪或审查收据齐全当本组交付或普通扫描前置。

## 发布后真实接续的新反例（仍在收口）

`f69913c`发布后，15:24:29 UTC从同一原run执行第3次launch（PID15564），15:26:15保存`result-3.json`并退出1。第一道原已付已入库题IQS_03被`resume_original_work_delivery_or_reconciliation_required`拒绝，其他25道显示前包待恢复。原10个checkpoint/已入库观察未丢，实体16个未发work保持pending，本范围未调用模型；不能把JSON的“26失败”说成26个原答案丢失。

独立源码和真正ACK隔离反例确认根因：`ApprovedRefreshSession._refresh_states`将原delivered工作能否恢复依赖于今天native plan是否decision=reuse且同观察出现于reused_observations。原action冻结时这些题是dispatch，今天重载还会提出新work/ttl_expired，于是旧paid被标deferred；restore因deferred直接None，才落到只许pending的claim兜底。ACK和新计划不应改写原已付答案的读取资格。正在按原checkpoint/context/subject receipt/原binding恢复，今天的route/projection/anchor只约束未付新派发，不新增grant或把delivered强塞进claim。

上述非作者隔离RED采用真实StockQA公开状态机及封存包，以原测试helper生成合法合成ACK，再调用原`apply_result_delivery_ack`产生delivered；不是mock状态，也不是StockWiki真实owner golden/跨仓验收。实物原10题入库ACK来自此前真实StockWiki，最终仍须原任务实际复验，不能用合成接收ACK代签。

同一操作器随后尝试独立security范围，公开`tasks/start`返回409：`refresh_admission_ledger_invalid`。原报价仍可用、两题pending，尚未启动模型进程；对应work为`WORK_9a6170328cdb43bab76276740d4103a0`/gen3和`WORK_d53c76088a03426e9fef7227836bba4b`/gen2。当前仅有公共短码，正在只读查原owner验证原因，尚不能声称是预算、数据损坏或SQLITE锁。测试/诊断只允许独占临时快照，不对生产库调用迁移构造器或变更配置。

随后只读backup实测（源库0写）：schema27，结构校验通过0.005秒，相同快照的全历史深审计也通过，却耗时91.037秒。未复现持久坏行或busy；历史底层原因仍未知。已证实的是准入`_ledger_ready`默认audit_records=True、current-schema constructor也深扫全部历史答案，而preview明确False，造成错位且高成本的前置。正在把普通就绪/当前库打开改为结构校验，具体work/lease/预算/ACK仍由各自原事务核验；显式全audit和旧schema迁移验证保留，不靠每个caller记得选择特殊快路，也不删除真实资金约束。

## 两处职责根修的最终软件验证

实现删除原paid读取对今天native plan/reuse/deferred的依赖；原entry/context/subject receipt/checkpoint/response绑定照旧检查，今天anchor/plan仅在原reactivated新派发边界核实。正常current-schema constructor及admission只检查必要结构，不扫描无关历史正文；当前work/lease/预算/ACK由原状态事务处理，显式完整审计和旧schema迁移仍深查。SQLite/IO不可用另报`ledger_unavailable`，不冒充结构坏库，也不在账本不可读时放行收费。没有新增协议、版本、授权或题号特例。

- paid混合恢复：新4个真实native/SDK替身行为例，加3个经`f69913c`内存基线证实的旧断言，最终7 passed/110.94秒；此前29个相关合法状态断言已绿，不重复跑。原getter不再查权限，拒绝测试移到实际收费前并验证0HTTP/0attempt，不为测试加回门禁。
- readiness：14新例先RED后GREEN，SQL authorizer实际禁止读取无关历史response/checkpoint；显式audit仍会读，坏结构/当前绑定/租约/额度/ACK及旧迁移回滚仍拒错。首轮81绿，6个原离线CLI helper固定25秒超时；仅临时测试harness等候60秒重跑这6项，全部原断言通过（385.40秒），未修改业务或永久测试超时。合计87个不重复用例，新14已含其中。
- 非作者终审：一次12项组合12 passed/113.42秒，含独立合法合成ACK反例RED→GREEN及两类操作边界，结论ACCEPT。第一次临时harness未注册辅助模块的asyncio marker而收集失败，修正临时marker后才执行上述12项，0例收集失败没有冒算通过。
- 新14例进入既有daily；原CI选题断言先真实RED缺目标，配置一行后1 passed/1.57秒。不新建job/门禁、不重跑已通过全套。全部验证使用独占短TEMP、合成数据库及传输替身，测试0收费/生产库0写，已结束临时根已清。

发布剔除另一个harness的F4与业务hunk，特别是同一work_store后部reason/lease字段；其源码与结果不由本组代签。以上是软件修复验收，原10个真实paid的再重开、剩余题派发、新登记和UI仍需原任务实际验证。

发布前在仅含本组12条指定路径的干净临时工作树补验3项（ACK后原paid+pending、constructor不读历史、delivery按原绑定/ACK），3 passed/81.83秒。该树的work_store只包含current-schema函数hunk，不包含另线后部改动；测试临时根已清，正常原提交钩子继续执行，不通过skip或在共享树临时stash其他writer来发布。

## 发布与原任务实际冷恢复

StockQA `ca7900d249b8a5f1d9b5fa891b92028c773a9a9d`正常原钩子提交并推送原origin，同SHA核对。isort首次只调整一处测试导入顺序，重提后全部原钩子通过；mypy和secrets均通过，无skip。干净发布树已删；接回原分支不回写源码，逐文件核对其他harness WIP字节保留。

原`run-5305efa0a466482fa2a187ed2b37699e`第4次launch显式seal实际完成exit0，recovery_mode=received_original_response、status=partial、recovery_errors=[]。API_requests/model_calls/new_attempts/new_generations全部0，dispatch_started=false；10个原paid挂回，10个work/package绑定与第2次冷恢复完全相同；仍16个实体pending。挂牌2题原公开preview返回200/can_start=true、blocked=[]、API0，用时14.292秒（含原CLI）。不把这次冷恢复算作剩余18题已经扫描。

本次第一次复验另有明确的**操作环境失败**：默认受限shell下外仓CLI的read_request→strict_json_loads→包eager imports→logger FileHandler._open抛PermissionError，fallback先变`owner_confirmation_permissions_rejected`、再变`seal_permissions_blocked`。同一公开service直接调用通过，正确原授权环境seal也通过；0收费，未删除seal任何校验。安全类型/代码位置trace留本机`gate-paid-permissions-cli-trace.json`，不记录异常全文/密钥。此cause只解释本次复验，不能倒推13:09历史原因；F4另harness处理错误揭示和日志副作用。

另有源码确认的相邻职责耦合仍在本组TDD收口：普通preview/start/resume对全paid scope仍要求new-send权限/配置。应复用既有paid恢复命令、环境和原record输入，混合pending继续原新派发与收费intent校验；不靠清空错误、改标签或绕原paid证据解决。

## 产品入口同一次整域回归（历史失败，后续已收口）

本组仅修改现执行网关与既有测试文件。统一原引用后，新20个定向case通过17.40秒；独审又以同一原record+future账本复现普通preview漏用原context，已统一默认preview，显式原run仍优先。随后在内存中仅去除他线lease hunk、其余包与资源ROOT不变，完整`tests/test_dashboard_execution.py`一次实跑**158 passed / 17 failed / 104.00秒**。新case均绿，TEMP清理，无API或生产库读写；失败不归给他线hunk，也不掩成通过。

|共因|原失败selectors/范围|本节点收敛方式|
|---|---|---|
|旧fixture未表达原scope或只读模式|`test_stalled_owner_preview_does_not_block_another_registered_start`；`test_start_uses_latest_allowed_work_instead_of_requiring_old_snapshot_equality`；`test_optional_preview_cannot_bypass_current_native_refusal[budget/unknown_work]`；`test_budget_block_is_not_zero_success`|对齐既有reader要求的question_ids/readonly标记；原拒绝含义及0付费worker断言保留|
|操作分类与收费参数指纹时机|`test_invalid_work_lease_never_reaches_native_launch`10参数；其中inf/nan在分类前被全配置hash抛ValueError|原引用/paid材料不序列化无关未来controls；确认pending后验证实际收费参数再构本次快照。不是NaN特判或放宽JSON|
|缺失证明与原引用职责顺序|`test_explicit_legacy_prelaunch_uses_original_namespace_scope_and_current_native_guard[prior_ref]`|有任何原ref就不能证明缺失，应先返回None；不必把极小旧ref当可附着记录审查后再报错|
|最终原owner状态选择效果|`test_native_keyed_work_items_and_g2b_envelope_do_not_require_fixture_flat_shape`|先统一fixture同一题IQS_05，验证合法pending→paid后按最终原work快照选择恢复，不沿用旧False、不绕不同题scope|

这4组由同一作者一次收口，只复查原17失败和必要新边界，同一非作者作有限尾验，未重跑已通过158项或扩其他领域。当时未签收，最终结论以下节为准。

## 2026-11-23 最终交付与实物复验

两文件源码提交 `b845b1fca198c71553433fb58a3d98bbdf89da66` 已推送既有origin并核对同SHA。11-23接续前核对当前源码/测试字节与先前已审的最终版本一致；他线lease hunk已不在当前树，本线程没有替对方回滚或签收其工作。

最终设计使用现有字段：公开原引用与paid材料指纹只投影既有恢复字段；pending确认后才验证收费controls、生成本次执行快照。类内同一preflight先分类再快照，原权限检查一次，核查期间真正收费输入变化仍阻止新进程。最终原owner同题状态变化重新选择paid效果；原ref存在时不生成“缺失”证明。没有NaN特判、额外协议/存储或新门禁。

验证结果：作者只复查原17失败及必要边界，**34 passed/23.59秒**；同一非作者有限尾组 **9 passed/9.72秒，ACCEPT，无本范围未修P1/P2**，并独立验证权限核查期间max_output_tokens变化不会被公开原引用掩盖，仍阻止新Popen，当前权限仅1次。原158通过项不重复；这些重叠计数不相加，也不声称最终源码重跑了整文件。全部测试独占TEMP已清，0API/生产库。

11-23再用原公开产品服务验证真实纯附着：只在本线程独立配置副本改变future pack/tokens/thinking并指向不存在的future spend文件，start仍返回attached同一原run，process_started=false，launch次数及任务数不变。原部署、原账本和原答未修改，未启动模型。摘要留本机`runs/amec-rescore-20261121/gate-original-attachment-summary.json`；它是操作事实记录，不是后续扫描准入凭证。

门禁/设计本组结项。原10题已付恢复和此次纯附着均通过；剩余18题、新完整快照和UI未在本次完成。13:09原故障深层cause仍未知，不以本次成功或后来的sandbox日志错误倒推。F4及另一个harness的三家公司仍按既定分工继续。

StockQA模块三份PWF已同步。文档提交首次遇宿主Windows嵌套Git丢失空配置值，原样保留全部注入配置并改用本次命令内的参数传递后，原钩子全部通过；未修改全局设置或skip检查。推送时发现远端已有另一harness发布的F4提交e95befd，保留其全部内容并只合并本次三段计划更新，最终以`e64c3e5f684c3cacce45b4a7c7ebe45af7b50c0b`正常推送核对。主工作树只做快进；两个仅行尾标脏文件先验证内容等于HEAD，再恢复Git本身checkout表示，未丢弃语义WIP。临时文档工作树已删。这是已有发布内容与PWF的整合，不是本线程重做或代签F4质量。
