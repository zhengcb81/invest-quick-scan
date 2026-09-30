# StockWiki权威存储与产品界面线

**Owner:** StockWiki项目owner。

**项目目录:** `C:/Users/郑曾波/Projects/StockWiki/`；一个写入harness独占该仓，不能与另一个StockWiki agent并行改写。

**当前授权:** W01与W02/W03已获精确授权；W05、其余后续卡、UI与启动路径均不因本计划而获得写授权。每次写入先确认目标文件仍属获批范围。

**现状观察:** StockWiki工作树有未跟踪`.claude/`；原目录必须保留且不能带入产品提交。


## 独立上下文与职责

StockWiki是权威issuer/security/listing/analysis subject及用户确认股票池的来源，并保存评分答案、facts与最小来源回执的不可变观察和索引。它负责名单维护、identity resolver、导入ACK/查询/历史时间轴、UI、生命周期/备份恢复。运行引擎仍属于StockQA；题目和标准回答仍属于IQS。该系统不依赖财报/网页文档下载，不能增加第二权威公司库或允许LLM模糊名称直接合并。

## 任务范围与包内顺序

负责`tasks.json`中owner=`stockwiki`的39项：W01–W15、W16、F03–F05、L04、O01、U01–U04、O05、X02/X04–X06/X08–X11、V07/V08/V10/V11/V15。按依赖字段顺序；任务包可能共享store迁移、CLI注册表、projection与浏览器fixture，不拆给不同harness。

- **当前已授权窄包**：W01三文件及W02/W03的精确8文件，以先前用户授权记录为准；W02/W03 identity DTO/G2b golden必须来自真实公共serializer/API，绝不伪造。
- **后续存储/事实包**：W04–W16、F03–F05与V07/V08/V10/V15按schema与数据库migration owner顺序；新字段/版本使用加法式迁移，保留历史观察、旧recipe与attempt回放。
- **UI/控制包**：U01–U04/O05、X02/X04–X11须复用版本化read/query与runtime adapter；页面能力状态明确显示unknown/expired/unsupported，不能静默当成0或空列表。

## 对外接口

读取：IQS identity/observation/query/recipe/release与compatibility contracts；接收StockQA受控导入包、dispatcher permit消费、run状态与ACK。

输出：可核验的身份snapshot/mapping DTO、universe membership版本、field status/freshness、query capability/coverage、history snapshot、ACK与版本化只读consumer API/CLI。外部消费者一律不能直连SQLite写入。

数据只保存用户规定的结构化答案、分数/unknown、时间戳、模型/provider/recipe/module版本和许可范围内的最小来源元数据。不得保存公司文档、财报文件或搜索正文。证券/挂牌/发行人/研究范围必须分开并对身份歧义失败关闭。

## TDD测试包

- W01–W03：精确授权测试文件中跑临时SQLite迁移/写入；同一发行人多地挂牌、易混名、中微公司/中微半导体型候选、重复ticker、issuer/security误绑定、全局ticker和MIC辖区、撤销/退市、手工增删/保留/审计历史。真实golden单独验证serializer正例与错误版本/伪造字段反例。
- W05及观察链：用真实公开导入入口的临时库做事务回滚、重复包幂等、错误身份拒绝、原观察不可变、ACK精确关联测试；不能由fixture mock掉owner事务。
- 查询/规则/事实：短词/别名/关系方向/分部/时期、unknown三值、缺失与过期、分页快照、规则兼容及不产生私有SQL消费者耦合。
- UI：临时SQLite fixture与浏览器真实页面走查筛选、排序、详情、时间轴、模块版本、unknown与证据依据；fixture完成后清理。
- Lifecycle：子进程/临时profile/失败注入的首次设置、并发启动、停止/附着/续扫、备份恢复和升级回退；不覆盖用户现有配置。

按StockWiki自己的AGENTS与test harness确定命令；owner本地批次只测当前授权路径。全链X09/X10归G6，不能在W02/W03局部测试通过时提前宣称。

## 授权与交接

不在lane文档授权范围内的文件一律read-only。开始每个已批准包前，回报文件路径、行为、测试路径、当前状态文件是否干净；如目标路径与其他正在修改的进程重叠，保持暂停并只读交接。既有`.claude/`不清理、不暂存。

handoff需附base/head、精确路径与SHA、migration版本、DTO/serializer公开例子及来源、真实库/临时库区分、schema/API release、unit/integration/UI/E2E命令结果、数据/临时目录清理、未解问题和所需授权。`docs/implementation/reviews/IQS-lane/G2b-handoff-2026-09-29.md`是当前真实golden要求；收到owner产物后由IQS公开CLI交叉验证。
