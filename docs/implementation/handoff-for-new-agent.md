# 当前接手说明

更新于2026-11-01。**先读根[当前计划](../../task_plan.md)，再按其唯一Next Step实施。** 本页不另列相互竞争的任务。旧长交接已[原字节归档](archive/pwf-through-2026-10-31/README.md)。

## 从哪里继续

原8766/原UI/StockQA/StockWiki已接通，三市场各36有效题槽、ACK、冷恢复和真实过期刷新均已验；不要重做这些。真实最近扫描单题复用正例本轮也已完成；当前先纠正已知答案质量，之后原200家可靠性、事实F05、TH/IN、全池与配套仍未完成。旧卡中的“待权限/未部署/未ACK/主线暂停”不是现在状态。

新TIME目前只是原结果页只读解释，不授权复用；其identity_revision/可信核查凭证只在采用新多时钟策略时是必需条件。不要先把新凭证体系扩成原缓存和原只读消费者的额外门。原W06兼容链与显式新扫描时钟的真实单题正例已完成；勿重做或改旧日期造fresh。

本次已取消冗余内存preview/旧inspection摘要门、纯缓存的模型准入、只读全历史账复审、自动委托早期重复核查、未知注册国家阻断，以及事实/消费者/小样本配套等待200/2000规模验收的人工依赖。规格1.10.17仍108任务/368场景，规模验收本身没有关闭。源代码、测试和[集中独审](reviews/SIMPLIFY-FRESH-2026-11-01/independent-review.md)已交，不要重造旧门或逐条凭证；变更和实际运行以[本次报告](reviews/SIMPLIFY-FRESH-2026-11-01/report.md)为准。

原预算快照误门已由StockWiki`724f5b7`修复；本地owner policy9已显式采用successful_scan（TTL24h，预算不扩）。原information_as_of/报告期/发布日期不改，新缓存含义只是最近成功联网扫描，可按原执行时间跳过重扫。激活与正反例见本次报告。真实原UI复用已完成，原观察和资料日不变、0新增HTTP/费用，不重做或补凭证。

当前真实批全部三题已补封并完成原ACK2/2；同范围DUPONT02再次准备已cached1、执行包0。见根Next Step和native-cache-reuse.json，不再等IQS22或重启该批。原HTTP JSON digest与final文本digest属于两种对象，分别核验；原owner捕获文件自身不授予scope/恢复权限。IQS11已知FCF跨年问题未金融签收，工程恢复不改变它的资格。

当前现金流纠错仍沿根Next Step，详细接线与真实状态见[现金流节点报告](reviews/CASHFLOW-CORRECTION-2026-11-01/report.md)。只复核原IQS_11，不重扫整公司；原成功答案通过既有1.3 comparison后继保留历史。切勿把软件提示/接线通过当财务已纠正。临时专用refs和原普通配置的恢复说明均在该报告，未决原任务须先核实，不盲目复位或重复POST。

## 固定对象与运行

|组件|本次核对基线|
|---|---|
|IQS本次起点已推送|`215804dada41148ea79011fbb483e02f9f8d1abe`，本次源码及文档在其后正常提交|
|IQS原接线|`c1ee64fd5a7cd1331e67d7ec7f3a242ff2ffc0b2`|
|IQS测试入口|`e8f184c47221a97f0eb1f0183b55c38d5f835a01` / `f16da24a5d78eb654a4a3e317e827d7e5cfe7bc0`|
|StockQA|`c6854fd`已推既有origin/master，含`65b3711`原答恢复与有限URL修复|
|StockWiki|`1bde9e0`（含`af2a260`及预算`724f5b7`）已提交，无origin，不新建远端|
|原UI|`0212c5c`（含`d6e0eb8`/`ffed6ca`）已提交，无remote|

实际写前重核当前Git/唯一writer，不因无关HEAD变化重做历史。ANSWER/PERF最终C/M见[已签收口报告](reviews/SUPPORT-CLOSE-2026-10-31/report.md)，TIME/RESULT实际原接线见[报告](reviews/TIME-RESULT-WIRING-2026-10-31/report.md)，不把接线C的历史25文件manifest当当前README/测试字节。

入口`http://127.0.0.1:8766/`；配置`config/dashboard.local.json`；数据`runs/r25-live/owner-workspace`（isolated_research），执行`runs/u25-live/runtime`。配置文件不发布，密钥仅环境变量，不打印。当前doctor只读就绪，不等于新任务已有收费准入。启动方法见[总README](../../README.md)。不杀记忆PID；重启前核端口、真实argv/creationtime、未决任务。UI静态浏览不调用模型。

## 授权、边界和测试

- 用户已给必要后续跨仓修复/独审/正常提交推送授权，不重复问。仍须避开其他writer；特别保留IQS的`docs/implementation/parallel-lanes/packages/2026-10-10/README.md`改动及历史untracked。
- StockQA/StockWiki/原UI各管自己权威状态，不从IQS旁路写数据库，不复制另一套LLM重试器。发布新策略显式版本兼容，旧记录/费用/已收答案保持。
- 不执行历史PWF里的mutation/回执刷新helper。PERF两个旧generator已退役，不重造旧C1或裁清单；PERF优化未装生产且36包更慢。
- 测试按[分层说明](testing.md)和改动范围选择；大产品节点集中独审，不逐helper增门、不重复小时全套。真实金融/收费/规模测试与软件fixture分开。

```powershell
# IQS根：改到时间解释/HTTP时才执行
python -B -m pytest tests/test_dashboard_temporal.py tests/test_dashboard_entity_view_http.py -q -p no:cacheprovider
# 查看当前分层，不执行测试
python -B scripts/run_tests.py all --plan
# 原UI根 C:/Users/郑曾波/Projects/iqs-question-bank-ui-lab：改到可信面板时才执行
python -B -m pytest tests/test_result_trust_host.py -q -p no:cacheprovider
```

测试用自有短TEMP，结束清理自身临时库/副本/进程，保留最小证据；不清他人文件。pytest hook只放行字面IP TCP loopback，不是整进程树沙箱。不得将collect/shape CLI/自报passed替代执行或真实owner golden。

## 交接完成标准

报告本次改变的功能、准确C/受影响文件、相关测试实际结果、真实模型/搜索费用及剩余边界；提交已完成工作并更新原计划表。历史验收原件不改签，当前入口只留一份状态，不再把同一长段复制进三份PWF。
