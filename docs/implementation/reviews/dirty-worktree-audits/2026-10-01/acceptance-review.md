# DWA-01–DWA-07 只读审计交付验收

验收日期：2026-10-01。审阅对象是本目录内收到的七项交付。该验收只判断快照绑定、报告覆盖度、证据边界和审计纪律；不授权修改、清理或提交任何外部仓库。

## 结论矩阵

| 任务 | 交付 | 总控结论 | 主要后续事项 |
|---|---|---|---|
| DWA-01 filing-fetch | [报告](DWA-01/report.md) | **通过**。单条状态与 SHA 匹配；疑似凭据只按路径/元数据处理，报告没有尝试读取内容。 | owner 本地确认是否保留或加 ignore；不可把凭据文件提交。 |
| DWA-02 MeetingConverter | [报告](DWA-02/report.md) | **通过**。快照、`.coverage` 哈希与单条状态匹配；覆盖率数据库由 pytest 重写的解释有配置及提交历史证据。 | owner 决定是否停止跟踪 `.coverage` 并加入 ignore；此报告本身不执行删除/修改。 |
| DWA-03 QAbyLLM | [报告](DWA-03/audit-report.md) | **不通过审计纪律，结论仅作线索**。报告记录了初始状态摘要不匹配，却继续归因；还承认曾在目标仓库创建后删除 `.dwa03v2.py`。这违反任务卡只读及漂移即停止要求。报告的分类也没有逐项列全清单。 | 另派严格只读审计；先固定 owner 的有效全局忽略口径，逐条列 66 条有效状态，并说明旧 67 条快照中的个人 `.claude` 路径；不得创建仓库内临时脚本。 |
| DWA-04 revenue-forecast | [漂移报告](DWA-04/drift-report.md) | **正确停止，但未完成逐路径盘点**。受限 harness 看到 416 条而冻结快照为 6,124 条；不能据此解释数千条状态。owner 视图复核为 6,124 条、状态摘要与快照一致，可哈希 2,274 项全部匹配。 | 在与 owner 相同文件可见性的环境重新执行；不要清理或提交当前状态。 |
| DWA-05 StockInfoDownloader | [报告](DWA-05/report.md) | **部分通过，存在范围违规**。六条状态有逐路径记录且快照匹配；但报告承认 grep 了任务卡明确禁止读取的 `config.json` 内容。没有发现或输出密钥值，仍属越界读取；该文件内容在本验收中一律视为未知。 | 不再查看/引用 `config.json` 内容；`stock_orgid_mapping.json`、报告产物和 HTML 的保留/提交/清理由 owner 分别决定。 |
| DWA-06 StockQAbyLLM | [报告](DWA-06/audit-report.md) | **部分通过**。开始时 62 条与 62 个文件哈希匹配；报告披露审计窗口新增 `?? nul`，当前只读复查仍见 63 条，摘要 `d9951959…cacbebd` 与报告一致。分类表用范围和通配符汇总，不能替代逐文件状态/处置表。 | 保留 `nul`，先确认来源及是否有其他进程依赖；补齐精确路径/状态清单后再谈清理。0 字节本身不足以证明可安全删除。 |
| DWA-07 StockWiki | [报告](DWA-07/report.md) · [owner 基线决议](DWA-07/owner-baseline-decision.md) | **通过 owner 选定的新口径**。独立复核按生效全局忽略得到 0 条，摘要为 SHA-256 空字节值；`.claude/settings.local.json` 只保留路径元数据，未检查内容。当前受限 IQS shell 因无法读取全局忽略文件仍显示 1 条，这是已记录的视图差异。 | 后续 harness 先验证与 owner 一致的全局忽略环境，否则报告可见性差异并停止。 |

## 独立只读复核

- 七份活动快照/状态清单经 JSONL 解析，状态行数、规范化状态摘要、文件清单条数及已生成/省略哈希计数均相符。DWA-07 的原始一条状态快照也保留并复算通过；当前 owner 决议快照是 0 条。
- 本验收 shell 对 QAbyLLM 只读运行状态命令，当前得到 67 条、SHA-256 `cc17c9a7b641caa481f72e8958e200a1c7878b94c629a7901c8fa666749786b8`，包括 `.claude/settings.local.json`，没有 `.dwa03v2.py`。Git 同时报告无法读取用户全局 ignore 文件，故这不是 owner 有效忽略口径的复核；它显示 DWA-03 的环境差异仍未消除。
- 对 StockQAbyLLM 只读复核得到 63 条及 SHA-256 `d995195971295b7da6aff13dfe9a37a04605808219d27d2eccf64029dcacbebd`，含 `?? nul`，与 DWA-06 报告所述结束状态一致。没有读取 `nul` 内容或删除它。
- 对 StockWiki，本 shell 也因同一全局 ignore 权限限制看到旧的一条 `?? .claude/settings.local.json`；DWA-07 独立报告在 owner 有效忽略下重验为零条。按 owner 决议，采用后者作为 DWA-07 基线。
- DWA-04 的完整 owner 视图复核和 2,274 项哈希重核已由总控在本轮之前完成并记录于任务索引；受限 harness 的 416 条只作为视图差异报告，不用来推断工作树已清理。

收到的七份报告按下列 SHA-256 冻结；后续若交付方替换报告，应另作版本并重验，不覆盖本次验收对象。

| 任务 | 文件字节数 | 报告 SHA-256 |
|---|---:|---|
| DWA-01 | 4,903 | `41ca11eb018b519cce0725fdc1fc9721e680cc615a151bb73bb30943d08f37ca` |
| DWA-02 | 4,862 | `f64fdda82528cc8955343ada03ab384d9397de9ef4884f84c0398618e5ffb5d4` |
| DWA-03 | 9,508 | `0ff5abd78dc2d81b705877a85c407cc949a11bdc49c9e92ad10049e075c512bc` |
| DWA-04 | 5,670 | `4e9409a45e10772ed7ba87efc9ed268be0706e882f4ba4c139f1fc09ce3bd56e` |
| DWA-05 | 5,600 | `fc7441ab801afdca8c9ba29968a8fd1410a362a216488e888cdf2a5951766ca5` |
| DWA-06 | 10,856 | `a78d60c058f7d70e775b25d804f25295b54c6bbc3007ec42cff80c667b9cf27b` |
| DWA-07 | 5,259 | `a136b7bf0fc80766b831ecda7ffee883d87ff74f844f5c1d73f570853f8b24d6` |

## 不执行的外仓处置

报告提出了 `.coverage` untrack、StockInfoDownloader 配置/报告/映射数据的提交边界、StockQA `nul` 处理及 QAbyLLM 多项文件的清理/提交建议。它们都不是本只读验收授权的写入动作。当前没有对外部仓库做删除、暂存、提交或 ignore 规则修改；owner 决策和精确写授权仍是后续动作的前置条件。
