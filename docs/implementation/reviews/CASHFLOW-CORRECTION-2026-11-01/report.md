# 现金流期间错误与原生定向复核接线

本节点继续根PWF答案质量主线，不重做已完成的最近扫描缓存正例，不新增客户端、账本或逐题核查凭证。真实结果完成度以本页更新和原job为准。

## 已核实的问题

原CATL IQS_11把2024粗略FCF写为546.45亿元。官方2025年报合并现金流量表的2024比较列为：经营现金流96,990,345千元，购建长期资产现金31,179,943千元；同式应为658.10402亿元。原2025同式908.75424亿元。维护/增长资本开支未拆分，不能把该代理口径称作完整所有者收益。[公司原披露](https://www.catl.com/uploads/1/file/public/202603/20260310105829_c5p2l3q9ll.pdf)。只在线核对，不下载保存文档。

二手文章的算后结果不能独立证明原始输入正确。新请求提示要求先逐期间列出原始输入、单位、公式和evidence_ids，再算指标；优先核对公司/交易所原披露及同表比较列，缺证据删去对应数字/趋势并列缺项，不凑年度序列。旧题面、renderer fingerprint、旧答案/分数/时点不改。

## 接线修复

- 原native comparison机制已支持保留原答、精确N+1及模型/题包/思考/预算绑定；IQS自动准备此前只接1.2不可用恢复。现在显式1.3加精确原工作决议refs，默认普通准备和1.2恢复不变。
- StockWiki及StockQA的原单动作agent委托目的枚举同步支持comparison；保持完整原request/preview/permission/policy/主体/工作/attempt哈希、期限、撤权和幂等。载体本身不能替代native权限或费用预留。
- 原UI识别既有1.1 subset中的comparison，显示“受控复核子集”，仍单列1题/完整36题，不冒称全公司更新或金融认证。
- 真正准备时又暴露source-bank选择遗漏：源工作已delivered，却有精确比较后继决议，旧代码只找unfinished而新造bank，导致原source metadata自然拒。现仅精确匹配原journal comparison决议的已交付源也选择其原binding/bank；普通completed无ref/错ref不选择，当前StockWiki实质metadata检查不放松。已对真实账本只读验证命中原bank `route_3eeac9ccf8dc5852d48fe1059d3f712a9998dfd79a7705cdbf584f6575afeb01`。

## 验证与独立审查

提示组8通过及8 subtests；IQS定向/原1.2短组最终5通过，含实际reader代码的只读port替身，明确不代真实owner；UI原实际ESM相关3通过。StockWiki原模块22项通过后，新增用例读错install摘要的fixture已修正，新增1项通过，共23个不同用例覆盖；不虚称同次23绿。StockQA有效RED后在独占禁网、去密钥的源码副本13项通过，TEMP全部清除。StockWiki本轮已核实的三个合成pytest目录亦已删除，其他会话与共享目录保留。

非作者`/root/fresh_ui_route`在同一产品节点完成源码、测试实际日志和source-bank尾修复核，passed/open_findings=[]，未重复运行大套或写真实库。它确认逐期规则经原shared engine的prompt_rules实际注入新请求，不是闲置函数；原renderer与历史prompt保持。hooks全部保留：QA正常行尾/Black/isort修正后mypy/其余hooks通过；SW新测试导入排序修正后原static hook通过。

## 当前真实运行

原source工作`WORK_3a5fefcc7c6f4876bc1166c7e0ee49fe`实际generation4，比较目标5。初始原控制已recorded但未派发；原UI准备`prepjob_81fcdad6c4714567a310938957d398db`在scope preview因source-bank遗漏退出，0模型HTTP。已从原UIabandon保留，再经原route activate+精确CAS恢复原bank，保留新旧route历史。旧控制窗口已过，未改旧记录；修复后重新取得当前范围的显式控制，仍同一目标代次，非模型回答择高重问。

初记84HTTP/US$1.974640是调用前快照；实际后续如下，不把初记误作当前阻塞。

原UI准备`prepjob_ac48559e48864ddba7f3e588c26e2af9`登记了`WORK_df168ba95e824103ad4cf3678c88c638`（generation5）。启动时原inspection仍只接受两类retry的已登记后继、漏掉comparison，以`refresh_control_source_work_changed`拒绝正常接续；已补原目的枚举，generation和原owner_control准确绑定保留，无关generation3仍拒。合成原SQLite正反例有效RED1F/1P后，两相关模块18P/0skip，禁网去密钥副本已删除，非作者尾审通过。

修复后从原UI接续同一`batch-42b5379fe5b54655a63f853df3ec582a`，实际`run-292caf2b061348b4ae4c53c15c4c7ea8`只发1次MiMo Pro请求。原HTTP200/search executed，02:57:07.849238Z至03:00:17.536037Z约189.69秒，03:00:18Z完成回答；增量US$0.025228，累计85HTTP/US$1.999868，0未结/在途。原UI交付`deliveryjob_b8c59f9d3c02c4d5db9cc6358c57e55d`于03:04:25Z完成scope1/1、原包1/1 ACK，仅存隔离研究库中的未核实模型输出。

**金融纠错未通过。** 新模型分数8仍引用二手文章的2024 FCF546.45亿元，未用官方比较列重算，不择高分、不改原score7或新score8。只读查本次冻结manifest和questions，未含本轮新增逐期原始输入/二手来源提示；因此不能把helper的新规则或软件通过当这次实际请求已使用新规则。下一步先核实际请求接线并带入已核第一方原数，不继续盲目重问；不会因已有ACK给它金融资格。

原任务结束后已复位普通owner policy11/1.1，successful_scan、TTL24h、模型及预算不变，移除专用refs并保留新登记bundles。经原validate_policy离线验证与当前字节CAS确认后保存，未覆盖登记期间新增包；原8766已安全重载，doctor ready=true/无缺项。未改任何旧时间、答案或原控制历史。

### 实际请求接续修复（同日03:39）

原UI实际命令是main_with_llm→LLMRunner→QAEngine，尚非shared_company_engine。现将逐期间原始输入/第一方披露/同年FCF公式/缺原数不猜的要求加到StockQA原单题、题包共同发送规则；实际pack SDK载荷有效RED2F后原模块10P/0skip，含单题SDK边界、原文本不改及模式恢复。没有据此重新付费，金融纠错仍未过。共享引擎的现有evidence_board可携带已核原数；standard_answer_transport只有布尔模式，不能假装已有传数接口。

为接原公共入口，独审又定位并根修三个真实兼容点：

- 原native搜索没有external_context_use很正常。共享来源校验现走原native receipt+work member+project_quick_scan_search；只有实际外部use存在时附proof，坏proof仍拒。原语义模块有效RED后20P；新增两例是边界替身，非真实搜索或原owner golden。
- 原runner的budget_route是四字段compact，原OwnerResearchServices要求与完整原route逐字相等。现只接受完整原route或其准确四字段投影，不接宽松字段集合。原临时owner单例有效RED1F/107.82秒后1P/149.11秒，包含四键漂移及额外字段拒绝；0skip、0收费、唯一runtime删除。最初复制漏一个旧producer的夹具错误已单独记录，没有冒充产品RED，也未复制历史docs/runs大树。
- 普通process_questions在缺CP时会claim/send。新增原QAEngine.hydrate_questions，仅在原已准入调用链复用reference/CP，缺项即停，不回落派发；复用原输出投影与执行时点。有效RED5F后原模块23P，禁网去密钥副本清理。不会把这个通用方法宣传成任意无owner lifecycle均无副作用。

非作者`/root/fresh_ui_route`在同一产品节点完成上述源码与覆盖方向审查，未发现阻断，未代写实现/触真实服务或库。当前StockQA `76c9431`正常hooks通过（仅Black/isort排版后重提），原已付结果不变。**公共UI→共享引擎及第一方原数board仍待接线**，两个Lab包尚未加入原默认Python搜索路径。不得仅凭这些前置修复称原UI已用共享引擎或重新问模型；细节见当前交接。

## 提交范围

StockQA `3fd35a1`（含`c6854fd`）已推既有origin/master，正常hooks全部通过，仅Black规范新增测试后重提；StockWiki `1bde9e0`、原UI `0212c5c`为本节点接线基线，后续UI精简另提交，两仓无remote不创建新远端。IQS本节点源码/文档由根正常提交。原服务、原库、原失败事件与已发生费用保留；不提交私有配置、原回答或捕获正文。
