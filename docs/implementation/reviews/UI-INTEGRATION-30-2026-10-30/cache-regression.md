# 缓存、有效期与原工作接续：定向回归收口

**63个唯一case全部通过，实际执行68次**（保留初次5F；只复跑3个环境问题和2个控制器修正的过时测试fixture）。没有跑重型原生多轮fixture，没有调用真实模型/搜索，没有修改实际数据库、预算或名单。

| 范围 | 最终结果 |
|---|---:|
| StockWiki freshness（TTL内复用、精确到期、过期刷新、unfinished优先及语义/代际保护） |20P|
| StockQA frozen observation-context集成（实际SDK/SQLite，HTTP替身） |16P|
| W15持久binding/迁移 |6P|
| W15 owner transport/current permission/部分outbox恢复 |19P|
| 本次reviewer自有：ready CP重启+TTL与代际保护 |2P|

初次5F如实保留：3例是隔离环境漏普通IQS_ROUTE_TEST_CODE_ROOT，补为owned IQS副本后3P；2例是原测试只移除到DDL19却标成v13/v15，当前schema25的附加表、v21旧trigger、v25checkpoint CHECK尚在。总控只修改原测试，复用已有remove_c06_additions，未放宽生产schema；本reviewer独立核helper并只复跑2P。

本次新增的2个owned补测补齐了跨组件缺口：真实临时SQLite保有result_ready CP与原outbox，重开store、让观测值TTL真实过期后，原planner仍选resume且计划HTTP=0；新lifecycle不claim或增加attempt，CP原字节/原outbox请求及幂等键保持。相邻反例证明generation改变不能被旧CP遮蔽，也不能删除旧CP。该测试使用synthetic Q10 package，不宣称native授权或投资准确性。

309个冻结生产Python源在运行前与原仓字节完全相同。原源测试修正单独overlay并记录旧/新SHA；reviewer没有改任何源仓。各组真实UTC、完整argv、exit/计数、log/JUnit SHA以及最后用例去重表在cache-regression-final.json。首轮runner清理命令错误单列保留；后两轮使用安全单一PowerShell命令清理成功，三轮owned临时目录现均不存在。未把最初清理失败描述成成功。

总控新UI36题原生准入已成功，属于总控另行执行的真实证据，不并入上述63case，也不能据此说旧generic异常根因已找到。真实三市场扫描、原Store入库ACK、零新增HTTP缓存恢复及金融准确性仍由主线分别验收。


## 永久化与真实主线

StockQA原测试fixture修复a8ecb9d已正常提交/推送；原2个ready-CP/TTL场景已晋升永久集成测试，最终052f3f0也经正常hook提交/推送。不同作者reviewer实跑晋升后2例、hook格式改动后再2例，完整AST未变；均同2场景，不累加进63。最终测试SHA1c5e8bcaa460c5dc7bfbe09c4ccc236ef670ee7d7d48c74bd184ef14ed33f17b。缺StockWiki集成环境明确skip，实际本轮集成环境2P0skip；不弱化生产schema或native权限。

三个最新原UI准备均已完整applied36：Tencent73357、Microsoftd3e11、CATL8fda；六scope原生准入通过，旧generic未复现，历史原因保留未知。本轮0模型调用的前置快照确认71CP/71封存/0目标ACK、53历史settledHTTP、无未知请求。2026-10-30T10:37:50Z用户已授权的原UI批次batch-f03eda7de77e4a5ab23fb32c4d89f900启动3公司/6scope；33题原Tencent经营结果直接owner_ready且无重发，缺37题继续原原生流程。随后首次新HTTP已登记为in_flight，尚未计成回答或入库ACK。当前真实流程仍在进行，组件回归不替代它。
