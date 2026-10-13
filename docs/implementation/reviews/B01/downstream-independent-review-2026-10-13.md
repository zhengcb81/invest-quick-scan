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
