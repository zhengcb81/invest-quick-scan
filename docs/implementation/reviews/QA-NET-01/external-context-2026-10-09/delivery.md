# Phase111 外部搜索执行链：有限软件交付

本批已正式发布到 StockQA `master`，源码/交接提交 `bc41908e4cdc44c13fefda97f3118e5434aed5f8` 已推送既有 `origin/master`，远端HEAD实际核对一致。交付不是全项目完成或金融事实验收；默认不自动开启收费外部搜索，也没有迁移真实生产数据库。

## 功能和版本

- search policy / execution plan 1.1，显式外部或混合搜索；原native路径保持1.0。
- 外部检索→有界短context→实际同步/异步LLM→原HTTP来源→context-use proof→checkpoint2→公开结果1.1→标准C06/outbox；旧checkpoint1、HTTP哈希配方及native结果兼容。
- WorkStore源码提供schema8→13的事务迁移支持；本批只在合成隔离库验证，不声称真实库已经升级。
- Brave/Tavily/Z.ai REST及Z.ai Streamable HTTP MCP接线；MCP初始化/通知/发现/检索的每次HTTP分别沿用原Q09许可与预算，不当作一次免费握手。
- 同一轮、同generation、已结算且TTL内的短REST证据可以在新lease重核后复用；新generation必须新检索，旧worker不能推进新lease。未知发送不重发，迟到模型无有效答案proof，MCP旧控制session不能继续新lease。
- DeepSeek外部证据＋显式模型解析可用；不把Responses忽略原生搜索的行为说成已支持native web search，不由请求模型名回填actual。

38件精确路径见 `scope.json`。首次review原件和9个RED/中间失败均保留；`final-review-recheck.md/json`覆盖37源码及单独核验的第38件交接文档。实际发布38个Git blob全部与获批SHA一致；111个非发布范围文件的实际工作树字节和7个原未跟踪项不变。原scope/input中的not_published是历史状态，当前发布事实以 `intake/QA-NET-01/2026-10-09-external-context/publication/result.json` 为准，不改旧冻结输入来表示进展。

## 验证结果

| 独立批次 | 实际结果 | 范围 |
|---|---|---|
| whole-phase-static-04 | isort、Black、mypy全部exit0；mypy61源 | 37受审执行文件，111支持文件不变 |
| whole-phase-regression-02 | 861 passed，0失败/错误/跳过；stdout145.23s | 17套主回归，覆盖9个新边界反例 |
| whole-phase-adjacent-regression-01 | 128 passed | 未变化的邻接5套 |
| whole-phase-iqs-consumer-01 | 111 passed＋216子测试 | IQS消费者4套；JUnit327包含子测试 |
| 独立复验wrapper | exit0，网络尝试0 | 同一次集中复验，两P2关闭，无开放发现 |
| 正常StockQA提交 | 适用钩子通过 | 格式、类型、JSON、泄密等；无文件的YAML/TOML钩子原样Skipped |

批次不能相加为一个测试数。24个新OS CLI场景、11个实际强杀断点、完整standard body封包属于合成HTTP/身份/价格的软件验证，不是财务准确性或StockWiki事务ACK。测试命令、实际argv、执行源码/guard、JUnit及终态在对应 `verification/` 批次；普通小卡不再新增review。

## 留档、清理与后续复现

最终两主批的实际子进程日志/PID/HTTP轨迹按白名单复制到各批 `subprocess/`；独审实际inline程序的事后副本、stdout/stderr和第二次process回执留在 `independent-review/`。不保存synthetic数据库、配置、密钥或任意TEMP，不把事后程序副本声称为另一次执行。

精确自有 `runs/n111a` 已清除：20,025文件、8,999目录，真实os.lstat逐文件正面验证nlink==1、无reparse，PowerShell删除前实际CIM查询无匹配进程、文件集合及SHA全部核对。见 `cleanup-baseline.json`、`cleanup-lstat.json`、`cleanup-dry-run.json`、`cleanup-receipt.json`；不再运行这些一次性固定根helpers。Windows DirEntry.stat缓存link count=0的初始诊断已纠正为真实os.lstat，不把0视为通过。无共享TEMP、外仓未知项或生产库清理。

复现应新建独占测试根，从StockQA上述Git提交按 `source-snapshot.json` 的已知非秘密源码/测试allowlist导出，再覆盖被审执行快照、核对SHA，并沿用归档guard/剥离API key/独占basetemp。旧控制器的固定root和原命令路径不能在已删除环境中直接重跑；不要复制真实llm_apis、计价授权、名单或数据库。本次不重跑已通过且未变化的批次。

## 下一汇合点及保留的门

StockQA external生产dispatcher这一实施段已交付；QA-NET整包及G3保持partial。下一跨仓动作是先获得StockWiki四个精确路径许可，再修JR1/JR3并用两owner公开CLI验证导入ACK/旧封包/正反例；原卡见 `reviews/G3/joint-2026-10-08/remediation.md`，开工前重新核真实HEAD、唯一writer与接口，不照搬旧脏树状态。

仅待授权路径：`stockwiki/quick_scan_import.py`、`stockwiki/quick_scan_observations.py`、`tests/test_quick_scan_observations.py`、`tests/test_quick_scan_delivery.py`。本批没有取得新StockWiki权限，也未代写。

真实owner identity/facts/query golden、金融准确性、真实厂商计价互通、G3/F05/L03、TH-IMPL-01/IN-IMPL-01写授权、规模运维及一键启动均未由本批关闭。不刷新已退役C01–C07任务回执，不自动开始200家公司live或重复收费实验。IQS本批commit以最终Git回执和progress追加记录为准，文档不自造包含自身的commit。
