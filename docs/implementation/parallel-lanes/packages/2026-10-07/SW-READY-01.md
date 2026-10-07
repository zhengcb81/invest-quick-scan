# SW-READY-01｜可恢复的轻量数据库与实用结果 UI

可单独交给 StockWiki harness 的大包。唯一源仓 `C:/Users/郑曾波/Projects/StockWiki`，观察基线 `master@9f552a6741dd093dc760ad6965458989cd027251`、clean。覆盖 W12、U01、U02；W05、G2、W09、W11已有交付依据，开工时按最新 PWF/源码复查。读[共同交接规范](handoff-rules.md)与[输入锁](inputs.lock.json)。按实际 StockWiki 写授权先报告精确文件；本包不在生产库迁移/恢复，不写 StockQA、company-wiki 或安装目录。

## 目标及真实缺口

实现能演练恢复的快扫存储，和直接浏览已存观察的公司列表/详情。已有 identity/universe、不可变观察/ACK、规则/恢复标记、刷新与查询原语直接复用，不另建库或重做名单。

当前 `stockwiki/quick_scan_query.py` 的 `query_capabilities()` 声明 `quick_scan_query/1.0.0`、facts/relations=false；`profiles_from_store()`只投影身份与证券。UI不能只喂手工 profiles 通过测试：本包要把 W05真实已存观察和既有 W06/W07/W08/W10派生输出接到读取投影，保持原分、状态、模型/日期/版本和来源。没有已验证的汇总就显示分项/缺口，不在页面求平均编出质量分。

W12 是 L03/G3 的硬恢复前置；UI可以独立离线完成。本包不含 W15模块待办、F03–F05事实关系、W14全模型时间比较、X一键启动和U03/U04完整版，不能把评分UI做完当这些功能完成。

## 写入范围与复用

开工核实并报告确切路径，预计仅：

- `stockwiki/backup.py` 的既有备份复用面、必要新增 `quick_scan_backup.py` 等快扫备份/恢复模块及CLI注册；不把既有备份程序全部重写。
- `stockwiki/quick_scan_query.py` 与必要独立观察 profile 投影模块，W05公开读取API的最小补充；不修改不可变观察导入/身份决策/评分尺。
- 现有 `stockwiki/ui.py`、其实际UI路由/模板/静态资源或服务分层；按仓真实布局选路径，不创建第二个Web应用。
- 该仓测试、浏览器隔离fixtures、运维文档、`docs/handoff/SW-READY-01/`。测试临时数据库位于独立TEMP根。

先读该仓 AGENTS.md 的真实数据/模块尺寸与测试节奏规则。源码模块分层不能通过复制大文件绕过规模门。UI和CLI所有路径参数都绑定当前授权 workspace，不允许任意路径读写。禁止批量下载、生产恢复/删除、改公司文档、真实名单自动增删、浏览时探测LLM或联网补数据。

## 输入和输出接口

消费 StockWiki真实权威 identity/universe/observation/ACK，IQS题义/模块版本和 C06轻量包；外部 StockQA只通过公开工件/协议，不能用StockWiki操作其可写工作库。

产出两类 owner 接口：

1. 快扫备份/校验/恢复 CLI 与版本化 manifest。给schema路径、完整生成/校验/恢复命令、错误码和样例hash；manifest记录store身份、schema、文件hash、水位、名单/观察/ACK/规则版本、创建UTC和恢复前置。新接口只管StockWiki拥有的库；执行器数据库备份/恢复由StockQA owner提供，未提供时返回“执行侧未核验、禁止恢复收费”，不能代替其清空余额或写表。
2. 现有Web/读取接口接入后的评分阶段 `capabilities/search/get_profiles/coverage` 行为和 UI路由。明确当前协议是W09读取原语还是已经经schema校验的C06 envelope；不得把旧返回直接改标签冒充C06。交owner隔离golden、公开生成命令和反例，facts/relations继续false。需要公共协议加法时交总控冻结，不默默改变下游字段。

## 实施顺序

1. W12 RED：WAL/在写事务的一致备份、hash篡改/缺文件/未知schema拒绝、恢复目标非空拒绝、历史/ACK/规则完整保留。SQLite用其备份能力或冻结后的合规快照，不直接拷贝活跃 `.sqlite` 文件忽略WAL。
2. 备份写到本次临时目标，校验成功再宣布完成；失败不能留下看似成功的半份manifest。只允许版本化保留策略清理本包调试/交换副本，不删除权威观察、身份/名单版本或费用历史。
3. 在另一个空临时workspace恢复，检查实体/挂牌/subject修订、不可变观察hash、ACK序号、名单pin/历史、规则/恢复状态及视图。双库是各owner独立快照：需明确停止新派发/完成在途对账或水位一致性条件；不声称跨进程原子备份。
4. 演练备份之后发生新观察/ACK的水位差，导入重放只产生accepted/already_present正确回执，未知费用/在途结果保持冻结与待对账。不能用恢复旧本地库抹去供应商真实费用，不能自动恢复paid dispatch。
5. 为U01/U02接真实观察投影，先在临时库用公开identity/observation导入生成fixture。实体/挂牌主键稳定；同发行人多上市公司行去重，经营subject范围不同要保留区别，歧义不得按名称合并。旧观察没有subject字段时明确历史未记录，不补造。
6. 列表提供名称/代码/别名、市场、可用行业/阶段、分项条件、all/quality/recovery/pending四个独立视图。默认50页大小、上限100、稳定ID排序和快照分页，保留筛选→详情→返回的上下文。未知/过期/N/A分开，不把低分/暂困公司从默认列表删掉。
7. 详情按通用/公司类型/行业/生命周期/诊断等已有模块呈现逐项结果、短依据、来源、信息截止/扫描UTC、实际模型/provider与题目/锚点版本；恢复信号/复苏条件与原低分同时可见。未实现事实/跨版本可比/历史query显示缺口；不用模型即时写摘要。
8. 真浏览器走临时StockWiki服务：键盘/窄屏、来源安全链接、输入转义、分页、导航、错误与缺口。浏览不调用LLM、不写观察/名单、不要求company目录、不要求StockQA在线。必要UI偏好只写自有偏好存储，不能假称全应用零写入。

## 测试与接收标准

| 层次 | 覆盖 | 必须结果 |
|---|---|---|
| 单元 | manifest/hash/schema/目标路径/保留策略；缺证据/unknown/stale/N/A映射 | 错数据拒绝；不删除权威历史；原分元数据保留 |
| 集成 | 真实SQLite备份→空目录恢复→原W05重放；ACK水位差/缺执行侧快照 | 观察/ACK不丢/不重；恢复不启动收费；只能访问本包临时根 |
| 集成 | 真实导入→projection→query，不人工补profile；两挂牌/两subject/旧缺字段 | 公司去重与范围准确；缺口真实；model/time/version可追溯 |
| 浏览器E2E | 分项AND/OR、四视图、未知/空/错误、50/100分页、详情返回 | 实际DOM值和快照一致；翻页不重复/丢行，过期不冒充有效 |
| 浏览器E2E | 低谷/恢复公司、无company目录、执行器离线、来源注入/窄屏/键盘 | 原低分保留且可见恢复特征；浏览LLM/搜索0；安全链接/可用导航 |

case-map覆盖W12 DB-05/REV-04/STORE-03、U01 UI-02/UI-08/UI-09/UI-13、U02 UI-01/UI-03/UI-04/UI-05/UI-06/UI-14。LLM-08、其他跨ownercase只引用已有证据，不在本包替owner签收。

定向测试选择器由实际实现填写；提交/大节点只运行一次 `bash scripts/check_all.sh`，其中已经包含完整pytest+coverage+real-workspace/data-contract，别另跑一次全量pytest。按该仓门要求用已有真实workspace数据的隔离副本补真实数据验收，synthetic正反例是补充，不代替真实链。无法做到不改变真实数据的门时记录partial并说明，不降低门槛。

交付 [SW-READY-01.handoff.template.json](SW-READY-01.handoff.template.json)及共同规范附件，附实际Web入口/临时启动与停止命令、浏览器选择器/截图/DOM断言、备份恢复正反例golden。review和跨仓恢复验收未做不得写approved；源仓无remote不添加remote。总控最终集中验收QA→真实导入/ACK→UI与双owner恢复，W12局部通过不能替代G3。
