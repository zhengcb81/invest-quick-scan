# 未提交工作树只读审计任务包与回收状态

初始快照生成时间：2026-10-01T20:35:25Z。这是一次性状态快照；各目标仓库可能由其他进程继续修改。七项交付均已收到；逐份验收结论见[总控审查](acceptance-review.md)。

每张卡带有 HEAD/分支、完整 porcelain 状态清单、状态摘要及可读取的非敏感文件哈希。接手者必须先核对快照；状态或哈希变化时停止旧快照归因，只回报漂移。所有任务均只读：不得在目标仓库编辑、删除、暂存、提交、清理，不能运行会改变状态的脚本/测试，也不能发起网络/API请求。报告返回给任务发起者，不写回目标仓库。

|任务|仓库|当前采用的状态基线|审计交付|任务卡|快照|
|---|---|---:|---|---|---|
|DWA-01|filing-fetch|1 条 `??`|通过；凭据疑似文件不读不提交|[报告](DWA-01/report.md) · [任务卡](DWA-01/task-packet.md)|[快照](DWA-01/snapshot.json)|
|DWA-02|MeetingConverter|1 条 ` M`|通过；`.coverage` 是否 untrack 由 owner 决定|[报告](DWA-02/report.md) · [任务卡](DWA-02/task-packet.md)|[快照](DWA-02/snapshot.json)|
|DWA-03|QAbyLLM|67 条快照；有效全局忽略口径下报告起始见66条|不通过：未遵守漂移停止，且曾在目标仓库创建/删除临时脚本|[报告](DWA-03/audit-report.md) · [任务卡](DWA-03/task-packet.md)|[快照](DWA-03/snapshot.json)|
|DWA-04|revenue-forecast|owner 视图 6124 条|收到的是有效停止报告；受限 harness 只看到 416 条，不能逐路径归因|[漂移报告](DWA-04/drift-report.md) · [任务卡](DWA-04/task-packet.md)|[快照](DWA-04/snapshot.json)|
|DWA-05|StockInfoDownloader|6 条|部分通过；报告读取了任务卡禁止读取的 `config.json` 内容|[报告](DWA-05/report.md) · [任务卡](DWA-05/task-packet.md)|[快照](DWA-05/snapshot.json)|
|DWA-06|StockQAbyLLM|62 条原快照，结束时63条|部分通过；`nul` 漂移仍存在，需 owner 查明；逐路径分类待细化|[报告](DWA-06/audit-report.md) · [任务卡](DWA-06/task-packet.md)|[快照](DWA-06/snapshot.json)|
|DWA-07|StockWiki|0 条|通过 owner 选定的有效全局忽略口径；本地配置只留元数据|[报告](DWA-07/report.md) · [基线决议](DWA-07/owner-baseline-decision.md)|[当前快照](DWA-07/snapshot.json) · [原始快照](DWA-07/snapshot-initial.json)|

本次扫描到的其他顶层 Git 项目在快照时干净，未生成审计卡。状态条目多不等于临时文件多；尤其 `revenue-forecast`、`QAbyLLM` 应逐项核实来源和其他进程的工作区归属，审计者不得自行清理。`filing-fetch` 有疑似 API key 路径，任务卡明确禁止读取或输出其内容。

## 已收到交付的总控判断

- **DWA-01：报告可接收。** 报告核对了唯一状态条目，并以路径/元数据而非内容判断疑似凭据；未提交或删除建议合理。后续如要新增 ignore 规则或迁移文件，需由仓库 owner 单独决定。本次不改 filing-fetch。
- **DWA-02：报告可接收。** `.coverage` 是已跟踪、pytest 可重建的覆盖率数据库；当前二进制 diff 不应再提交。是否 untrack + ignore 需 owner 批准。
- **DWA-03：报告拒收为合规审计。** 它自述开始状态与冻结快照不一致，却继续逐项归因；还在被审仓库中创建并删除 `.dwa03v2.py`。现有分析只作线索，需在不写目标仓库且使用一致忽略口径的条件下重审。
- **DWA-04：只验收“按快照不匹配停止”的纪律，不验收逐路径盘点。** 报告中的 416 条来自受限 harness；owner 视图复核仍为快照的 6124 条、原始状态摘要匹配，2274/2274 个可哈希路径的摘要匹配。故目前证据支持 harness 可见性差异，不能把 416 条归因成真实删除/清理，也不能声称 6124 条已逐项解释。需在可见性一致的 owner 环境重派审计。
- **DWA-05：报告快照有效，审计范围有违规。** 报告承认 grep 了被任务卡列为不得读取的 `config.json`；没有密钥值被报告，但该文件内容仍按未知处理。不得再读或据此处置。
- **DWA-06：已覆盖冻结的62项哈希，但出现第63项漂移 `?? nul`。** 当前只读复核仍见63项。因来源不明且其他进程并行运行，不依据零字节特征删除；报告的分组表还需补成逐路径状态/分类清单。
- **DWA-07：owner 已选定有效全局忽略空状态。** 原始 `?? .claude/settings.local.json` 观察仅作为历史快照留档；当前基线为零条。该本地配置只保留路径元数据，不查看内容。该决定和复现边界见 [DWA-07 基线决议](DWA-07/owner-baseline-decision.md)。
- DWA-04 的 harness 按规则正确停止，但其逐路径盘点尚未完成；应在可见性与 owner 一致的环境重派。完整判断和不执行的外仓动作见[总控审查](acceptance-review.md)。
