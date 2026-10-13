# B01 同节点独立只读复核

审查agent `b01_downstream_review`，2026-10-13；同一B01大节点连续实现的集中审查，未测试、写文件或联网。源码范围为自有IQS/QA/SW候选，不复审PRIMARY/FIN。

初始三组：四个owner消费者固定旧query；QA inspection固定1.1；字段评估reader固定旧original。均采用显式2.6/1.2选择及既有算法复用，旧公开wire保持。内部已配置fixed contract声明original_query_schema_version2.6；旧trusted contract无该能力维持2.0，不伪称支持新版。

实现复核发现1.2无PRE可沿legacy分支accepted。候选现在只对旧1.0/1.1保留unbound历史兼容，新1.2无PRE明确拒绝并回滚Observation/ACK/binding。

终态/CNY最后复核发现：明确answer_generator_rejected_member被转成generic ValueError，未进入终态；终态锁前采now可能让等锁期间过期的lease通过。前者只在确定answer.status=error分支传明确reason，generic ValueError/storage错误不扩大；后者在获得写锁后取now，并用真实SQLite写锁＋受控时钟负例验证。

已核的设计边界：terminal只改当前logical work/event，不改物理attempt/response/预算/pack outcome，pack须费用settled/completed；旧17严格验证再添两个event不可变trigger升级18；CNY仅new1.1，request/policy/inspection方言精确匹配，quote与真实预算同币种、不换汇；旧1.0仍USD/query2.0；query2.6冻结/hash版本仍核；旧无绑定receipt形状保留。

最终测试证据及未部署/旧expired待对账范围见同目录vendor-profile-downstream-2026-10-13.md。本记录不是源部署签收、真实身份gold或金融准确性结论；审查后的精确代码字节以私有checkpoint48-candidate inventory及后续source交付核对为准。

## 2026-10-13 checkpoint49 — B01源码交付与正常本地提交

此前checkpoint47/48的“未源部署”是历史。本节点68个精确文件已部署：IQS20、StockQA32（含新schema的精确Git忽略例外）、StockWiki16。部署前逐文件及HEAD核对无目标并发漂移；原文件备份和实际交付SHA留在本机，当前68目标再次匹配。其他进程的2026-10-10 README不覆盖、不提交；生产数据库、名单、旧实验账本均未修改。

StockQA正常本地提交`21b2c5f9caa4db8adafb7bc74d69ce75aed4c9fe`；首次正常hook修正四个文件的混合换行而拒绝提交，保留日志后只重暂存同32文件，第二次black/isort/mypy/secret及其它正常hooks全通过。StockWiki正常本地提交`5b11f55909efdbd724fb07e1e7f298631c4200cb`，正常静态hook通过。独立源静态检查QA PID76912/exit0、SW PID34484/exit0；均未跳过检查。换行只改变raw bytes，原schema canonical SHA一致，候选镜像和交付摘要已同步，不把canonical相同声称为raw相同。

公开协议：Observation1.2/profile vendor-http-identity-v1；事前主体request1.2/binding1.1；query2.6/capabilities1.2；refresh显式1.1接受CNY、旧1.0继续USD；work store18。新旧整链、逻辑terminal、原件恢复与CNY admission的集中测试见[本节点报告](docs/implementation/reviews/B01/vendor-profile-downstream-2026-10-13.md)。同节点独审发现的缺PRE、typed reason、锁前clock已直接修复；最后源只读复核未发现这三处遗漏，不新增小审查门。

下一动作：只读核对原真实owner/work账本和当前公开恢复路径，保留13物理HTTP、26原生搜索、已settled CNY1.268162、30题分母、4旧blocked/26旧expired、0评分/ACK0。schema18升级需原账本备份及原生迁移；无答案的旧expired不能用新terminal强改，不补造事前记录或header ID。由原owner生成当前显式1.1 CNY quote/新的批准与admission后，才对固定IQS_01/02/04做pack3/32768→pack1真实小实验；旧approval不扩大、不重放one-shot控制器。

软件接线完成不等于答案准确：本轮API/付费搜索0，金融gold0，Financial/G3/F05/生产UI/一键/全池仍开放。PRIMARY/FIN已交付不重做。源码与本批公文只正常本地提交，尚未推远端；此前自动审批导出范围pending保持，私有日志/数据/golden/密钥不随公文发布。

## 2026-10-13 checkpoint50 — 源码提交终态、真实旧账本备份迁移及owner恢复候选

checkpoint49源码交付已完成正常本地提交：IQS `29f49d3ff59974ecbe25ec9e7e7438a774cb1a63`、StockQA `21b2c5f9caa4db8adafb7bc74d69ce75aed4c9fe`、StockWiki `5b11f55909efdbd724fb07e1e7f298631c4200cb`。远端未推；不重做68文件部署或已签收PRIMARY/FIN。

真实实验原work.sqlite先只读核实，schema17、30个work/attempt、4 checkpoint、26 leased（已到期）、13 physical budget全settled/completed，原SHA60d4446d…。在自有实验目录做完整SQLite backup后，用已部署原生QuickScanWorkStore升级18，只添两个work_event不可变trigger；所有原表逐行摘要/计数完全保持，完整性及外键检查通过。原schema17备份SHA f3e6101f…，迁后236e5aa4…；没有改状态、答案、费用、旧context/PRE或补造header ID，也没有HTTP。备份与原件仅留本机，不上传数据库。

同节点只读审查未部署work-decision旧草稿，不能整树复用：草稿18与已交付18同号异构；旧native-currency profile不等于当前refresh1.1；当前PRE1.2不含回答后的payloadSHA；首次apply过期确认漏洞；comparison限制合法checkpoint导致旧26不可实验；retry时间/controls尚无planner/admission/runner消费。对无accepted answer只能作owner中性结案，不以诊断hash自证具体parser错误。全部纳入同一原B01实施，不新开小审查门。

仅自有runs/b01-engineering-2026-10-11-01候选复用原journal，显式schema19保留原18；未部署源、未迁真实账本19、未结束真实旧26。候选resolve取锁后clock，双读owner权限后以真实commit clock持久化，倒退拒绝；物理receipt/attempt/pack/预算保持，已有checkpoint拒绝resolve。独立comparison可接已授权failed-resolution，不伪造旧score/checkpoint或要求先伪造旧投递；只保存独立意图，尚未创造新work/HTTP。扩展projection显式include_owner_decisions=True，旧默认shape保持；新旧只读quote不偷偷迁18。

TDD与续测保留原分母：PID60796原目标RED1F（缺resolve方法）；移植脚本两次重复锚点断言零store写，先跑批次PID45108仍34F，不算已实现后的产品回归。真正当前移植后PID66732 31P/3F（漏显式投影）；直接修后PID62972 34P/5deselected。其余五项适配当前真实1.1/schema18→19及guard：PID56168 4P/1F，发现SQLite C层绕原open hook在runs创建空foreign.sqlite；已按实际创建时刻/绝对路径/0bytes确认仅该自有文件并删除，加sqlite3.connect有界审计后PID10648 1P。新commit-clock/旧默认shape/币种/迁移联合PID50592 9P/35deselected，含5项新控制和原4项，不相加冒充一次全绿或金融准确率。子进程无key、外部网络拒绝，原日志/PID/SHA保留。

下一步唯一动作：继续同一候选将真实owner预览/TTY确认/首次fresh-registration与既有精确决议重放接通当前refresh1.1/query2.6，随后将已授权retry/comparison引用、冷却时间、目标generation及固定controls贯通原planner→preview→admission→runner。需要扩展wire时用显式新版本，不暗改旧1.0/1.1。完成整个owner控制节点再一次集中原生CLI/SQLite/TDD与既有同节点独审、核源差异后交付；不要用FixtureAuthority处理真实26、重放旧one-shot、放宽旧批准或把4旧blocked补成新结果。之后才IQS_01/02/04 pack3/32768→pack1收费实验。

本轮金融gold0、已接受评分0/ACK0，原13HTTP/26搜索/CNY1.268162/30题分母保持；工程完成不授Financial/G3/F05/生产UI/一键/全池。私有候选、备份、日志和真实材料不随公文发布。

隔离清理已在实际CIM自有Python0后核绝对路径/reparse/硬链接闭合和逐文件SHA；删除自有temp 4176文件/3012目录，剩余0。保留候选/冻结输入/原日志/交付备份与真实实验；没有删除源仓或其他进程文件。旧长路径第一次清理在只读枚举阶段退出，改原生扩展路径后才执行。
