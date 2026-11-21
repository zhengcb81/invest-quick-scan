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
