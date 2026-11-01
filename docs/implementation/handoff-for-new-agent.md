# 当前接手说明

更新于2026-11-01。本页只说明如何接手；唯一执行顺序是根[task_plan.md](../../task_plan.md)，实际阶段证据见[progress.md](../../progress.md)。更早长文已[归档](archive/pwf-through-2026-10-31/README.md)，历史日期段不能覆盖当前结论。

## 当前已经完成什么

原8766工作台、身份/215实体名单、组合基础36题、比较/名单维护、三市场各36有效题槽的真实入库与冷恢复均已接通。最近扫描真实复用与过期刷新已有正例。

本节点已完成原UI共享已付IQS_11的零API恢复、保存、StockWiki ACK及普通配置再次同题复用。总账86HTTP/US$2.024863，0在途/未结/active；同一原分数7、资料日2026-10-29与完成时间2026-11-01T07:33:28.670089Z不变。不是只有HTTP200，也不是只生成离线报告。

原owner/SDK短证据软件E2E1P/701.62秒，实际出站body含excerpt/URL/published_at:null，保存和复用通过；只替换vendor wire。旧真实请求的原证据板仍空，未把新原数补进旧context。不得据此声明金融准确性通过或模型已在旧请求使用这些原数。

## 现在从哪里继续

当前请求的工程收尾已完成并随本次提交发布；不再重复补封、重问、重建预算或新发支线。后续未完范围仍按根计划：回答质量及共享fallback、200家可靠性、事实F05、TH/IN正式消费、用户认可名单扩容与完整配套。当前小范围可用不等于2000覆盖或全套交付。

## 本机运行与普通配置

- 入口`http://127.0.0.1:8766/`，配置`config/dashboard.local.json`（忽略文件），原工作区`runs/r25-live/owner-workspace`明确为isolated_research；执行配置`runs/u25-live/runtime`。密钥只在环境变量，不打印、不提交。
- 本节点独审后已恢复普通policy11/1.1、successful_scan/24h及原prepare全部设置；pack2、thinking=true、max32768，无shared专用配置或comparison refs。保留59个已登记包和历史，不能整文件恢复到只有58包的旧备份。
- 同范围IQS_11新预览`prepare_16f75b1a321f4ee592459d7ea66e33ad`为cached1/执行包0/API0、owner未变；原UI直接显示原结果，无确认/登记job。资料日与最近扫描时间分别保留，查看/导入/重启不续期。
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
|IQS|本轮前已推25cad52；本次源码/PWF提交以Git最新记录为准|
|StockQA|a37d60c，正常hooks通过且已推origin/master|
|Company Lab|a37af8d，本地提交、无remote|
|Runtime Lab|f58fdb1，本地提交、无remote|
|原UI|8fc9072，本地提交、无remote|
|StockWiki|1bde9e0，本地提交、无remote|

原UI补封透传冻结shared配置和controls；StockQA原recover分支仅重放，缺原safe拒绝新model/search。缺密钥不改变policy eligibility，按原response_available attempt精确route恢复。新pending仍受原发送准入；已有坏检查点不跳过，真实缺文件才回读尚存原pending。来源闭包拒失效ID改名，HTTP只有原投影合格才接受。

## 测试、审查与未完成边界

相关IQS语义/引擎50P、QA入口15P、Lab41P、seal11P；原252P/1F的旧测试接口失败已修并定向通过，不将重叠结果相加。完整短证据owner/SDK E2E1P/701.62秒，前轮失败已记录；本轮自有临时根已清理。旧AppContainer目录未定位，没有擅删不明路径。

集中独审通过工程恢复/原ACK范围，不授金融准确性。只对大产品节点集中测试/审查；小修复跑受影响项，不跑小时全套、不建逐题凭证/组件资格审批/active全局ReleaseSet或第二派发许可证。原身份/作用域、预算、防未知重发和ACK保护保留。

用户已授权必要后续修复、独审及正常提交推送，不重复问权限。每仓单writer，保留根外来的`docs/implementation/parallel-lanes/packages/2026-10-10/README.md`改动与历史untracked，不使用git add全仓、reset或清理他人文件。
