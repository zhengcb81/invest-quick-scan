# 未提交工作树只读审计任务包

生成时间：2026-10-01T20:35:25Z。这是一次性状态快照；各目标仓库可能由其他进程继续修改。

每张卡带有 HEAD/分支、完整 porcelain 状态清单、状态摘要及可读取的非敏感文件哈希。接手者必须先核对快照；状态或哈希变化时停止旧快照归因，只回报漂移。所有任务均只读：不得在目标仓库编辑、删除、暂存、提交、清理，不能运行会改变状态的脚本/测试，也不能发起网络/API请求。报告返回给任务发起者，不写回目标仓库。

|任务|仓库|状态条目|状态概览|任务卡|快照|
|---|---|---:|---|---|---|
|DWA-01|filing-fetch|1|`??`=1|[DWA-01/task-packet.md](DWA-01/task-packet.md)|[DWA-01/snapshot.json](DWA-01/snapshot.json)|
|DWA-02|MeetingConverter|1|` M`=1|[DWA-02/task-packet.md](DWA-02/task-packet.md)|[DWA-02/snapshot.json](DWA-02/snapshot.json)|
|DWA-03|QAbyLLM|67|` M`=7, `??`=60|[DWA-03/task-packet.md](DWA-03/task-packet.md)|[DWA-03/snapshot.json](DWA-03/snapshot.json)|
|DWA-04|revenue-forecast|6124|` D`=3778, ` M`=12, `??`=2334|[DWA-04/task-packet.md](DWA-04/task-packet.md)|[DWA-04/snapshot.json](DWA-04/snapshot.json)|
|DWA-05|StockInfoDownloader|6|` M`=5, `??`=1|[DWA-05/task-packet.md](DWA-05/task-packet.md)|[DWA-05/snapshot.json](DWA-05/snapshot.json)|
|DWA-06|StockQAbyLLM|62|` M`=1, `??`=4, `A `=15, `AM`=14, `MM`=28|[DWA-06/task-packet.md](DWA-06/task-packet.md)|[DWA-06/snapshot.json](DWA-06/snapshot.json)|
|DWA-07|StockWiki|1|`??`=1|[DWA-07/task-packet.md](DWA-07/task-packet.md)|[DWA-07/snapshot.json](DWA-07/snapshot.json)|

本次扫描到的其他顶层 Git 项目在快照时干净，未生成审计卡。状态条目多不等于临时文件多；尤其 `revenue-forecast`、`QAbyLLM` 应逐项核实来源和其他进程的工作区归属，审计者不得自行清理。`filing-fetch` 有疑似 API key 路径，任务卡明确禁止读取或输出其内容。
