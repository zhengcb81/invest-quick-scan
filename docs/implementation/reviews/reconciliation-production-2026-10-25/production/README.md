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
| 真实重试/摘要/缓存恢复 | 正在同账本准备；尚未签收，不能从本表前几行推出成功 |

首次真实首试的旧driver字节、pins与退出日志在`failed-pretransport-01/`；`pre-live-final`只证明当时的有界准入检查，不是完整driver实际运行成功。失败归因草稿与澄清均保留。部分早期软件失败XML被后续pytest同路径覆盖，实施报告已如实注明；当前软件XML只能证明最终一次通过，未补造旧日志。

重试计划见`engine-fix/pretransport-retry-plan.md`及`engine-review/unsent-retry-plan-review.json`。现有公开接口不提前释放有效lease；按真实到期后原recover_expired→原engine batchclaim，保留原任务/代际/预算，用明确新query_id与fresh session。不是清账或把重试叫缓存命中。

每个薄文件的原来源、字节数及SHA见`integrity.json`。本目录不包含数据库、回答正文、context全文、密钥或思考正文；完整本地隔离状态在`runs/r25-live/`，实际摘要与恢复最终证据到齐后补充本轮结论。

操作入口：[实操手册](../../../shared-engine-operations.md)。`ready`表示本地封包，不表示StockWiki已接收；费用估算不是账单，单题工程成功也不授予金融准确性或全池生产资格。
