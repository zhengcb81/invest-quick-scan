# 共享引擎生产接线：本轮证据

当前阶段以根PWF为准。本归档同时保存成功软件验证和失败真实首试，不能把二者合并成真实生产验收通过。

| 项目 | 实际状态 |
|---|---|
| 原标准答案显式封存接口 | IQS `23a05c8`，StockQA `8af0c86`（已推送）；复用原owner/lease/native response/checkpoint |
| 定向回归 | 主仓29项、StockQA36项通过；hook只整理新测试import后该文件14项通过，数字有重叠不相加 |
| 原软件scored端到端 | 1 passed / 649.21秒；合成身份、脚本wire，正式CP/ready封包；不是实际金融回答 |
| 原合成库与源码 | 不同agent只读复核8源SHA、正式CP和搜索证明；自有临时库已清理 |
| 实际CATL首cold | 本地实验观察器漏request，原transport未进入、模型0attempt；原账本保守unknown |
| 本地失败处置 | 独审归因后，原公开reconcile记录confirmed_not_sent；原unknown回执/dispatch/operation均保留，同一预算与上限不变 |
| 修复观察器 | 只重绑模型SDK module facade；原搜索manager保持，4项离线反例通过 |
| 后续前置/语义/来源门 | StockQA `f88b53e`/`24fc22f`、IQS `1730023`/`854ed55`、Company `73d342b`；59/92/54项分别对应其批次，23项格式后重跑为92的子集 |
| 实际generation1 | DeepSeek搜索成功，MiMo Pro HTTP200/112.245秒并安全保存；回答score混入fact items，被原标准门拒；原owner resolution/retry已实际完成，费用保留 |
| 实际generation2 | 最终56源锁、原预检通过，新增搜索1次/模型1次；思考开启、HTTP200/75.337秒，原IQS语义合法，但模型去掉2条来源URL的query，被原StockQA正确拒绝；正式检查点0 |
| 真实摘要/缓存恢复 | generation2无合法crash-proof/result；R3/R4仍开放，正在按原控制准备明确新代次，不能从工程回归或HTTP200推出成功 |

首次真实首试的旧driver字节、pins与退出日志在`failed-pretransport-01/`；`pre-live-final`只证明当时的有界准入检查，不是完整driver实际运行成功。失败归因草稿与澄清均保留。部分早期软件失败XML被后续pytest同路径覆盖，实施报告已如实注明；当前软件XML只能证明最终一次通过，未补造旧日志。

重试计划见`engine-fix/pretransport-retry-plan.md`及`engine-review/unsent-retry-plan-review.json`。现有公开接口不提前释放有效lease；按真实到期后原recover_expired→原engine batchclaim，保留原任务/代际/预算，用明确新query_id与fresh session。不是清账或把重试叫缓存命中。

后续原known-response控制与上段首试未发送恢复是不同路线：已保存但无效的safe，须等真实lease到期后原resolution，再原retry_unusable_answer开启新generation并准入；不直接清行或先fail绕过。generation2原context的5条URL及合成prompt、messages text各自hash已实际复算；原参数确实完整传给模型。该反例与独立诊断见`generation2/safe-diagnosis.json`、`engine-review/generation2-source-diagnostic.json`。当前累计公开价估算19129micros，账单未知，原四个身份源库SHA未变。

本次归档包含真实后续9项controls RED/GREEN及cleanup。最初6项driver协调测试的原XML曾被后续同路径RED覆盖，只有当时工具输出和`engine-fix/generation2-controls-fix/evidence-scope.txt`记录，未补造原件；该历史限制不等于最终9项未跑。各项真实负例、代码修复和独立审查分开保留。

每个薄文件的原来源、字节数及SHA见`integrity.json`。本目录不包含数据库、回答正文、context全文、密钥或思考正文；完整本地隔离状态在`runs/r25-live/`，实际摘要与恢复最终证据到齐后补充本轮结论。

`integrity-first-42files.json`是最初42文件归档时点的历史清单，不是当前索引；当时retry-1预检原字节已从Git已提交的blob/filters中按旧声明SHA精确找回，另存`retry-1/preflight-first-frozen.json`，不伪造缺失日志。后续前置能力修复后的预检留在`retry-1/preflight.json`，当前索引明确记录两者。

操作入口：[实操手册](../../../shared-engine-operations.md)。`ready`表示本地封包，不表示StockWiki已接收；费用估算不是账单，单题工程成功也不授予金融准确性或全池生产资格。
