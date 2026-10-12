# 所有harness必读：边界与工作方法

## 所有权和恢复

只拥有自己施工卡指定新根。第一次开工读取卡/targets/43文件锁，核路径解析后不包含任何已有仓，核已有目录/分支/status/writer；根已存在而归属不明时不要写或清理，报告总控。开工后的PWF固定到自身 `docs/handoff/<package-id>/planning/{task_plan.md,progress.md,findings.md}`，不修改IQS根PWF/共享active selector。此批三个根可以并行，不能互相发任务、共享可写缓存或临时目录。新根CodeGraph未初始化时遵照AGENTS.md询问；结构检索优先CodeGraph，纯文字与清单用rg。没有必要为创建目录自动改全局配置。

按照锁原件复制43份到自身fixtures/fin，字节/SHA/计数完整核实后只读使用。开工后的活动源仓变动不影响你：用已冻结快照继续，交接列当前源漂移供总控三方比对；不要回滚源、修全局ignore或换成latest。冻结丢失/不匹配不能靠模板或自造数据继续，报告具体路径。编制baseline是原FIN已提交HEAD1e88d867，非旧1.1或动态B01候选。

## 轻量来源研究

仅公开网页、官方IR/监管/交易所在线可读正文或结构化公开披露；检索仅导航。不调用收费模型/Brave/Tavily/ZAI等API，不读取环境key，不自动抓全站，不下载/保存财报/PDF/附件/HTML全文，不绕登录。可引用官方PDF入口为“定位未读”，不能把入口当已读原件。浏览工具若能直接展示官方正文，可记录工具/时间/定位与短摘录，不将原文件落地。遵守工具引用限制；数字/单位/期间/范围及短定位可留结构化事实。找不到在线原件时保留具体gap，不能退而将新闻或转载升为官方原件。

信息截止冻结为每家公司targets中的information_cutoff。今天抓取并不让截止后发生的事实进入当时参考。事实公开日未知→unknown，来源发布时间与数据期间、网页访问日分开；发生日/披露日不能互换。过去错fact/source保留原义与前序hash，新的primary佐证用新fact/source ID追加，不将旧source改URL/发行人/资格。历史contradicted不能悄悄删除。

逐主题批量读页面，但全部自身30题有独立coverage和证据需求。对关键缺口至少分别考察可用的官方发行人、监管/交易所入口；每个入口最多两次短暂重试，单题至少一次具名定向尝试。已读一页不能批量标30题confirmed_primary；一次超时也不等于全公司无资料。不要求强凑全完成，确实不可得写attempt结果、停止原因和仍欠的最小材料。

## 不自签权限或金融gold

本包所有scores保留null，review/status按输入保持needs_revision，不变为accepted_on_sources；official原件确认和金融结论候选写独立qualification-index供总控核验。软件passed、URL来自官网、原文含数字、同行指标高，都不能自动推出公司的分数/安全边际/困境反转。当前低谷、结构性恶化和恢复条件要分清，监管/经营/周期风险证据不被删掉。

不保存LLM思考文本、密钥、生产数据库或权威身份golden；不生成StockWiki正例/ID，不作第二永久公司库、模型客户端、评分/会计引擎。原FIN公开CLI和计算注册是依赖，本包仅研究资料、允许变化检查与来源候选报告。

## 测试、隔离和交接

先少量真实业务RED，实施到一个稳定候选后集中unit/integration/本包真实CLI E2E和一次包级来源审查；修复只回归受影响处，不为每题/helper设审批门。网络研究与离线测试分账；合成来源反例明显标synthetic，不能替代真实原件/owner/模型准确性。测试剥离key环境、禁止网络、只在自己独占随机temp运行；下载是禁止项，不以清理后下载为理由。测试临时库/导出/复制件/进程/端口结束后恢复，删除前验证绝对目标属于自己temp、无reparse、硬链接闭合；不动共享TEMP、系统设施或源Lab个人环境。保留必要小输入、最初RED/后续失败、JUnit/stdout/stderr/真实PID时间退出码；不能覆盖旧失败日志。

最后两个普通Git提交：产品→交接；自己的实际分支/产品commit/最终HEAD分别报。没有remote就正常本地提交，不造push或强推。manifest逐path/bytes/raw SHA包括产品、测试、冻结依赖、元数据和必要日志，排除自身以免循环；不以Gitblob SHA替代working bytes SHA。handoff.snapshot.result_commit引用产品commit，最终metadata HEAD在外部交接说明，不伪造自引用hash。真实目录/status/设施dirty/count照实报告。给用户指定handoff路径，不跨仓写总控/其他worker文档。
