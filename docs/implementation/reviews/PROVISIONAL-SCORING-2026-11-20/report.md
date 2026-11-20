# 暂定评分：观点分数与证据强弱分开

2026-11-20，按用户最新要求完成。证据不足本身不等于不能判断公司。部分事实可以支持方向性判断时，保留1–10暂定分，同时明示低置信度、依据、假设及缺失信息，由用户判断。不用压低分数表达低置信度，不默认填5，也不为给分编造财务数字。

## 现有合同与行为

复用现有 `status=scored, confidence=low` 及 `missing_fields/coverage`。非评分状态的null含义不变，事实题不评分；完全没有判断依据和经济上不适用仍如实说明。没有新增评分体系、审批或准入字段。

|环节|修复|
|---|---|
|StockQA 普通/pack/修复提示|资料不齐不再强制整题空分；可用部分依据给暂定分，缺失的财务输入仍未知。相邻标准pack追加指令也已同步|
|IQS 新提示|新renderer 1.1与当前typed规则加入暂定评分指导；renderer 1.0及legacy规则保留，旧请求/恢复提示逐字不变|
|共享agent|low分可引用原board的partial/unverified资料表达观点，不把board改为supported；事实矛盾、伪引用、跨期/币种和计划冒充实际仍如实报错|
|汇总、比较、恢复关注|不再清空低置信度原分；既有数值汇总列暂定题，比较保留结构可比的差值并提醒，恢复线索也保留原confidence和暂定标记|
|StockWiki|保存数、可用分、暂定题和证据缺口分列；当前/历史同口径，public ref透传confidence，原记录/哈希/身份不变|
|原UI与Dashboard|逐题卡、比较主表、质量汇总和公司结果主层披露暂定性质；分数保留，证据缺口不因已有数值归零。原UI公司读面兼容1.x小版本|

生产工作台答案来自公开owner API，原payload包含confidence/missing_fields/coverage。展示snapshot未选择历史源时answers为空并说明原因，没有构造一批假历史；本轮未扩大旧离线adapter的格式。

## 质量验证

先复现清空低置信度分数、有限证据导致无分提示和UI缺提醒，再修实现。针对性结果：

- StockQA 207 passed，含实际SDK构造截点、1/5/10暂定分解析、原outbox请求字节接续；既有格式/类型/密钥检查通过。
- Company Agent 108 passed；公共validate_task_answers覆盖partial/unverified暂定分及事实冲突对照。
- StockWiki 117 passed，既有静态检查通过。
- 原UI 92 passed、9子测试；真实DOM的当前、静态逐题、比较表及小版本兼容对照通过。
- Dashboard 后端64项、QuickScan前端22项与TypeScript检查通过。
- IQS 提示/题库/发布组106项与182子测试通过；3个旧renderer测试错误地要求当前版本等于已发布旧版本，改为按原release选择后，相关9项定向通过。
- StockWiki公开CLI→IQS HTTP→Dashboard的隔离组113 passed、1个未改动浏览器用例未运行；含暂定分的最新/历史正例，数据库字节不变。
- Skill说明校验通过。首次工具按Windows默认GBK读取失败，改用UTF-8执行；一次测试默认沙箱临时路径过长，改为C:/Temp短隔离路径并自动清理，未改产品路径。

独立 `provisional_score_review` 最终ACCEPT，复核六域及公开链路；额外独立运行IQS11项/8子测试、CA16项、QA10项、SW7项、Dashboard3项、UI80项及跨仓低置信度正例。没有以测试数量替代实际行为验证。

## 历史与交付范围

本轮0收费模型调用，未给历史空分补数。原中微结果 `cas_6cab1b94d8f45d42c750`、资料日及8 scored/28 insufficient_evidence保持不变。8个有分答案中原本有1个confidence=low，现在显式显示为暂定；因此证据薄弱计数为28个空分加1个暂定，不能把29解释成又少了一题答案。旧28个空分需要新的分析判断才会产生新分，原记录继续保留。

|模块|已并线提交|远端|
|---|---|---|
|StockQA|d6dbb04|既有origin/codex/qa-content-filter-resolution-01已推送核对|
|Company Agent|9fb4b94|本地master，无远端|
|StockWiki|79c51e7|本地master，无远端|
|原工作台UI|4c64fb0|本地master，无远端|
|Dashboard|2b96c55|既有origin/main已推送核对|

IQS总控提交包含本轮提示/汇总/比较/公开投影及回归、SKILL/README/评分说明和PWF。五个自建隔离worktree及分支、临时依赖副本与调试日志已清理。其他harness的Dashboard计划/筛选/预测WIP及原UI两个生成JSON均保留。没有运行新的真实公司模型重评或新的浏览器用户走查，不宣称这两项已完成。
