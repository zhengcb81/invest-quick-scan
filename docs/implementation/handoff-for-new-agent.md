# 当前接手说明

更新于2026-11-01。本页只说明如何接手；唯一执行顺序是根[task_plan.md](../../task_plan.md)，实际阶段证据见[progress.md](../../progress.md)。更早长文已[归档](archive/pwf-through-2026-10-31/README.md)，历史日期段不能覆盖当前结论。

## 当前已经完成什么

原8766工作台、身份/215实体名单、组合基础36题、比较/名单维护、三市场各36有效题槽的真实入库与冷恢复均已接通。最近扫描真实复用与过期刷新已有正例。

早间节点已完成原UI共享gen6已付IQS_11的零API恢复、保存、StockWiki ACK及普通配置再次同题复用。当时总账86HTTP/US$2.024863，0在途/未结/active；同一原分数7、资料日2026-10-29与完成时间2026-11-01T07:33:28.670089Z不变。下方晚间gen7是保留它的新比较，未取得CP/ACK，不能混记为同一已完成任务。

原owner/SDK短证据软件E2E1P/701.62秒，实际出站body含excerpt/URL/published_at:null，保存和复用通过；只替换vendor wire。旧真实请求的原证据板仍空，未把新原数补进旧context。不得据此声明金融准确性通过或模型已在旧请求使用这些原数。

## 现在从哪里继续

**本次终态已读，不得重发：** [Dashboard NEW-6](reviews/DASHBOARD-NEW6-2026-11-01.md)最终候选定点复测通过，不代签其D00/E07。真实CATL IQS_11 gen7 comparison的`run-5a03133643e34e60b69d6b9b311b46c0`／`batch-a4a0514b51f04d9fa048f266500a7ec2`，work`WORK_ef7cfb7bd41740ab95e2d31af6c78548`：首两段均0HTTP发送前失败，相关根修已集中独审；第三段仅1次真实HTTP，safe完成23:44:40.990609Z、进程23:44:57Z exit1。两条第一方原数已被原payload hash证明实送，FCF算术正确；但未登记metric_id年份后缀导致slot invalid/answer_semantic_contract_rejected。CP/ACK=None，尚不能签该代次缓存。勿重做prepare/confirm/apply、清计数或另建work绕开。

普通policy11及prepare现已精确恢复，pack2/thinking/max32768、shared=null/refs=null，60包保留，doctor ready/无阻塞；**不要再次运行configure或release_unsent.py**。私有编排/原备份及final-ledger、ordinary-restored-check在`runs/quality-context-retest-2026-11-01/`。总账87HTTP/2053896micros，增1HTTP/US$0.029033；0在途/未结，但1个work仍leased/epoch2、attempt=response_available，不能写active=0。原safe/receipt/旧gen6四hash保持；下一步按根Next Step继续原共享顺位接线；本次invalid明确保留，不改raw求绿、不放开任意financial.*、不重问已付请求。canonical投影不是小修，不为此扩建协议或增加后续开发门。金融分红范围等限制见[真实复核](reviews/CASHFLOW-CORRECTION-2026-11-01/report.md)。

代码审查整改已完成并集中非作者审查通过，详见[核源与整改报告](reviews/CODE-QUALITY-2026-11-01/report.md)。已付safe保全不再要求新发送委托/租约/手动分类覆盖仍有效；主体/anchor/actor撤权/原response和物理回执/CAS仍严格。普通与共享恢复都只保存原回答；混合范围明确原登记/本次恢复子集。原budget/provider材料仍须存在可绑定，不重造历史。原parser外层日期仅缺key时沿原inner提取，不猜新日期。

共享资源按真实packs派生；旧CP保持原task/证据/控件。多期指标与比较、UI锁/草稿故障/超时、公开owner投影和work快照、模块元数据与import环均已修，旧生成器退役。早间59包/86HTTP是历史快照；当前60包/87HTTP及残余work状态以上段为准，不重做已交付对象。

下一工作仍按根计划：回答质量与原共享自动跨模型fallback（尚未接，不能循环client冒签），然后200家可靠性、事实F05、TH/IN正式消费、认可名单扩容与完整配套；不新发支线、不造门。此次工程收尾不是全项目完成。

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

|仓库|当前已核实版本|
|---|---|
|IQS|软件及NEW-6交付db0b432已推origin/master；晚间终态文档的准确commit见Git最新记录|
|StockQA|2e4f01b，正常hooks全过，已推origin/master|
|Company Lab|d1d92a2，本地提交、无remote|
|Runtime Lab|5839ef4，本地提交、无remote，原codex/agent-run-02分支|
|原UI|8fc9072，本地提交、无remote|
|StockWiki|本组719520b已被其他harness合入381811e，五个本组文件未改；无remote。该HEAD为本次快照，后续以Git实际状态为准|

原UI补封透传冻结shared配置和controls；StockQA原recover分支仅重放，缺原safe拒绝新model/search。缺密钥不改变policy eligibility，按原response_available attempt精确route恢复。新pending仍受原发送准入；已有坏检查点不跳过，真实缺文件才回读尚存原pending。来源闭包拒失效ID改名，HTTP只有原投影合格才接受。

## 测试、审查与未完成边界

本轮完整原owner/SDK E2E1P/744.04秒（仅vendor wire脚本化、0收费、TEMP移除），最后paid-only尾修用实际session/SQLite和原parser118P验证。最终完整UI执行模块154P，UI其它72P、题库87个不同测试、QA指标/原子快照117P、共享17P、Lab22P/Runtime6P；测试有重叠不加总。独审最终QA32P/1S与UI3P，关键过期override实际1P并非skip；其余详细命令/局限见progress。原701.62秒是前一节点证据，不冒签当前paid-only分支。

集中独审通过工程恢复/原ACK范围，不授金融准确性。只对大产品节点集中测试/审查；小修复跑受影响项，不跑小时全套、不建逐题凭证/组件资格审批/active全局ReleaseSet或第二派发许可证。原身份/作用域、预算、防未知重发和ACK保护保留。

用户已授权必要后续修复、独审及正常提交推送，不重复问权限。每仓单writer，保留根外来的`docs/implementation/parallel-lanes/packages/2026-10-10/README.md`改动与历史untracked，不使用git add全仓、reset或清理他人文件。

StockWiki其他writer状态会变化，不按本页旧清单清理；原static hook临时保存的外来patch已核实恢复。本轮只做相关测试及一次集中交叉独审，未新增许可证或逐assertion回执。
