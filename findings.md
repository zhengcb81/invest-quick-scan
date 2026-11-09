# 当前发现、风险与决策

**2026-11-09 模块边界。** 工作台的跨仓 `-c` 源码桥导致实现和部署强绑定。把存储与写入操作移回所属仓库，读取使用固定公开命令。共享引擎需保持在 StockQA 原派发进程内，以维持原账本、lease 和已付收据语义。它通过公开能力、原始输入、回执和保存投影协作，产品进程无需新增第二套预算或审批。独立复核确认外仓回复即使协议正确仍可能串实体或缺少交付映射，绑定按原请求检查，业务上仍区分真实缺失和暂时不可用。2.8 既有改动及其私有边需单独并线。

**2026-11-07 job façade施工包环境发现（来自OWNERPKG-INVEST-QUICK-SCAN-01，分支交付）。** (1) 全仓环境风险：任何新clone/worktree在 `core.autocrlf=true` 下会把 `questions/releases/artifacts/*.json`（release锁hash锁定）转成CRLF导致锁校验失败（prepare套件16项红）；修法=按 `questions/releases/locks/*.json` 的artifact_sha256从主检出复制字节一致工件。根治建议未来加 `.gitattributes` 标记该目录 `-text`（未做，避免与施工包scope混淆，留给主线决策）。(2) 基线先存失败：test_dashboard_execution.py 32项、test_dashboard_unusable_recovery.py 1项在master主检出同现（2026-11-07实测），非任何施工包引入，待主线排查。(3) 真实formal付费演练按红线§3-1留待操作者确认预算边界（NOT_RUN NR-1）；job面的软件级全链证据与两轮独审记录在分支 `planning/iqs-job-facade-01/`。

**11/02 解耦七组已整改。** 公共结果字段由生产者定义，消费者不再复制供应商名单。服务短锁保护部署与配置，耗时工作保持原组件互斥。已付恢复使用原发布目录、原题义资源和原请求规则。UI 数据源故障留在受影响页面，迟到请求保留未保存表单。组件继续拥有状态、账本和投影。独立反例和本地、远端验证见[整改报告](docs/implementation/reviews/DECOUPLING-2026-11-02/remediation.md)。

**11/02 解耦整改前核查。** [原报告](docs/implementation/reviews/DECOUPLING-2026-11-02/report.md)记录了七组源码与离线反例，34 项和 39 子用例通过。当时的功能验收不能代替架构边界核查，后续整改状态以上方新报告为准。

**11/02远端CI已根修并实核通过：** 连续失败是StockQA原B608动态SQL，CI阻断后另查出同值重复旧断言及普通预算默认缺request hash的真实落盘漏洞；统一静态参数SQL、native绑定自动hash、正反测试和daily11例。文档新鲜解析另有插件不兼容，已固定支持3.10的5件版本。实现ee8f49a/0154726已推，最终CI41523660779与Documentation41523660825（build/deploy）均success。本地305P、非作者27/32及全新venv构建过，0API/TEMP清；normal hooks≠远端CI，曾漏核真实结果已纠正，不把Bandit加回每commit或新增门禁。见[CI根修](docs/implementation/reviews/CI-ROOT-CAUSE-2026-11-02/report.md)。

**11/02本次完整链路再复查已修复并通过独审：** limit按实际补封进度计数、有限候选ID快照；原codec原子发布避免中断损毁；终态job不复活/全entry只补本地标记；原storedACK先验证承接；派生cache仅凭原精确字节完整sha重建。实现IQSe24c359/QA4cffabc已推；原SDK两新进程冷恢复1P/323.82秒、0API、TEMP清，原服务/配置/历史/费用保持。原已发布history损坏仍报错，未新增审批或回执。详见[本轮全链整改](docs/implementation/reviews/GATE-SIMPLIFY-2026-11-02/full-chain-restart-remediation.md)，不是金融/规模全产品完成。

**11/02上一节点接续整改结论：** 已修已付journal被无关diagnostic挡住、公共batch补封局部错误、交付resume重复全scope预检、缓存引用误计partial及ACK逐项接续遗漏。原authority目标匹配共用nativehelper；无新配置许可。123P整合、独审与原SDK冷恢复0API均过，见[接续整改](docs/implementation/reviews/GATE-SIMPLIFY-2026-11-02/persistence-chain-remediation.md)。不把软件通过当金融或全产品完成。


核对于2026-11-02。历史发现[原字节保留](docs/implementation/archive/pwf-through-2026-10-31/README.md)；本页不重复进度日志。

## 本次纠正的实质问题

**门禁清理最终处理：** 上轮有界签收不足以覆盖全部历史/跨操作依赖。本轮已按原真实响应根修发送配置、资源白名单、纯格式/单位误诊、singleton重复codec及只读/逐项交付依赖，定向回归与集中独审已过，原UI已获ACK。新发送仍核原预算/访问/租约，原题义/主体/真实冲突仍验证；历史保存不重做发送资格。具体边界见上方当前结论和终验报告。


**11/02原5/8/9/10四组软件整改已全部闭合：** 前端坏草稿、SDK研究能力失真、生产跨仓私有seam与旧工具错库/缺HTML/历史混淆均根修；原1.6确认冻结模型顺位，复用原SDK/lease/预算，已付fallback safe无CP窗口原owner/SDK E2E1P/656.77秒及非作者尾组28P通过。今日模型顺位/配置不再误阻原已付恢复，原scope和首cap跨模型/重启不重置。没有新客户端、预算/队列/许可证库，未新增真实收费；本轮工程通过不授金融准确性。完整范围和提交见[本轮结果](docs/implementation/reviews/CODE-QUALITY-2026-11-01/remediation-2026-11-02.md)，原6闭合/4部分是整改前快照。

以下编号是各阶段的发现和当时处理经过；出现“正在/待验”等旧状态时，以根task_plan和11/02核对表为准，不把原始过程当最新结论。

1. **PWF已失去单一当前状态。** 旧计划916195字节、进度1235030、发现901831、交接581158；大量相同日志、多代Next Step和旧权限/暂停/未派发混杂。已将当前计划、进度、发现、交接分工，原件hash留档；不再只prepend。
2. **已推送不再写待推送。** 旧顶部“准备元数据推送”已被实际origin/master `d2c575f`覆盖；当前入口改正，历史原件不篡改。
3. **已通的链不能说未通。** 10/25“单题/待ACK”、10/30“比较名单待挂载”、10/31早期ANSWER/PERF partial均有后续正式增量；当前状态按最终证据更新，旧日期报告标历史。
4. **新策略前置被扩大。** 原StockWiki W06依据information_as_of/valid_until/原兼容性判定，并不依赖新TIME的identity_revision/verification receipt。当前已取消独立多时钟核查凭证体系，不再把它列为新能力的必做前置；缺失不阻止原扫描/入库/只读查询。上次把它写成唯一下一主线过重，已改回原fresh实证与时效根因。
5. **G2局部通过≠60家完成。** 既有r2局部签收保留；实际缩为6家，原60+20配方仍有范围差异。G3的200家未见正式关闭，不从3家公司或合成负载推断。
6. **研究签收≠金融全对。** ANSWER完成63外部命题审计仍有25部分支持和16不可评；发现过错公司/错期间/截尾等问题。必须实质纠错，不能拿63软件测试、JSON、ACK替代事实核验。
7. **卡数不等于进度。** 当前1.10.19目录107卡/359场景是规格，无运行状态。大量Lab是研究、候选和测试资料，R版本也不是新增上线功能；不报虚构完成率。
8. **规模验收被错误用作软件开工门。** 已核清传递依赖，1.10.17解除25项人工排程依赖与QUERY-11对应前置。事实、消费者、小样本端到端和安装维护不必等200/2000家公司；真实接口依赖、规模运行O04及最终规模目标仍保留。
9. **运行路径也有冗余。** 内存preview/旧inspection摘要不是派发权限；纯缓存不应申请模型准入；只读预览不应重审全部历史；自动委托不应连续重建两次同样预览。已沿原路径精简，当前预算、撤权、防未知重发、身份/版本和ACK保留。详细变更和实际验证只记[本次报告](docs/implementation/reviews/SIMPLIFY-FRESH-2026-11-01/report.md)，不另造核查凭证。
10. **未知国家不是未知公司。** 已核实唯一实体、证券、挂牌和来源绑定时，注册国家null不应拒绝native compact读取。现允许未知值，未补造注册地，legacy兼容契约未放宽。

11. **全局预算余额不是本scope身份。** 无关公司结算释放额度会改变quote哈希，原逐字owner_state比较错误拒绝有效确认。现只屏蔽动态余额快照漂移，保留原批准cap、当前预算可用检查与原子reserve；主体/题义/代次/模型/政策等实质变化仍拒。
12. **最近扫描不等于资料最新。** 原W06把information_as_of与observed_at混作TTL，年度题真搜索后仍立即过期。显式policy9的successful_scan仅依据原已验成功搜索执行时间，资料日期/报告期/来源日期原样；旧默认规则不变。没有新增verification receipt，也不声称金融最新/正确。
13. **同文章的跟踪参数不该变成来源门。** 新真实题包完整回答、parser/schema都通过，却因新浪/东财同path缺营销query被拒。仅对已证实的有限host/文章路径忽略tracking，证券代码、ID、年份等仍保留；原引用和原receipt不改。
14. **保留原答还需要可用的恢复入口。** 原receipt和owner捕获都在，旧UI seal按钮却无后端。现沿原CLI/原store补同attempt零API重解码与封存，真正从原UI恢复两题，原时间/原失败历史/费用不变；不要求新spend、密钥或生成参数，不把诊断文件当权限。两种hash含义分别核验，不要求给旧捕获补签名。
15. **导出不应变成历史审计。** 纯读封存包曾使用writer初始化，重复深审全账，真实三包交付耗时约2分钟。改为已有只读视图，当前布局/目标包/实体/ACK仍核验；实际写入路径不变。缓存专用UI行也取消“下一步扫描”的矛盾提示，不再诱导重复启动。
16. **工程修复仍不等于金融修复。** 新答案旧年份/截尾分红两反例改善，但IQS11又出现2024 FCF跨年输入错配，必须保留未通过状态。原评分与原正文不篡改，缓存仅表近期扫描，不能抬成金融认证；实际原数和后续纠错见本次报告。

17. **内容错误不能伪称传输失败。** 已成功/入库但数值错误的答案要保留原历史，用既有comparison精确后继复核；不走retry_unusable伪造失败。已补原UI准备与两仓委托的遗漏枚举，并保持真实当前权限/预算。
18. **源工作已交付仍可能需要原bank。** comparison源已delivered被旧bank选择器漏掉，新准备移动current后原source metadata校验自然失败。只有精确原journal决议匹配时选择其原冻结bank，不能因“最新manifest”标签换掉旧物理绑定，也不能削弱原owner元数据校验求绿。实测只读原账本已命中原bank，新真实答仍待核。

19. **显示快照不能成为恢复许可门。** 原控制动作已在锁内核实当前owner/进程；要求重启后先手动inspect、或用旧显示快照隐藏按钮都是重复步骤。现直接开放明确检查动作，未读进度仍为未知，真正执行仍拒在途/未知/错误输入。
20. **读旧任务不等于新准备。** 已有job凭准确ID/token关联，不再重验当前新准备配置；新job的完整验证、损坏记录/错误token拒绝和单次apply保留。旧applied可能触发登记，原冻结输入完整性仍有独立作用，不随意删。
21. **缓存预览已有原结果就直接显示。** 原只读缓存检查已得到观察ID与时钟，新增透传原cached_result并复用UI已有展示；不再强制确认/登记准备job。部分命中、多证券歧义或缺摘要的旧服务仍走原流程；不新建协议、权限凭证或队列。
22. **helper的新规则不等于冻结请求已带新规则。** generation5真实新答仍沿用546.45错误，已保留为未核实模型输出。只读检查本次原manifest与questions，均未含新增逐期间原始输入/二手来源规则；故这次不能用于证明新提示有效或无效。先核实际prompt路径并接入已有第一方原数，不继续盲问、不给旧bank补新签名。工程ACK和金融正确分开。
23. **共享引擎库存在不等于原UI已接。** 实际是main_with_llm→LLMRunner→QAEngine，原发送共用BaseLLMProvider规则才影响此路径。已补实际单题/pack载荷规则并10P；原evidence_board入口可复用，不另造手工搜索proof。此前两个Lab包不在默认Python搜索路径，现已由可选公共入口显式加载原包，并完成本节点原UI恢复/入库；失败不能退回legacy重问。
24. **原生搜索不该要外部搜索凭证。** shared_company_engine来源校验曾无条件要求external_context_use；现仅有实际external use行时检查它，native路径仍经原project_quick_scan_search核实已搜索/源URL/准确work member。缺真实搜索仍拒，坏external行不当作native放过。
25. **封存后恢复不能落回会发问的普通入口。** QAEngine.process_questions在hydrate缺失后继续claim/send。已增hydrate_questions只复用原reference/CP，缺失或恢复错误直接停止；复用原投影/时间，不建新恢复器。原模块23项隔离通过，未据此称完整共享引擎接线完成。
26. **同一路由的完整与compact表示不该误拒。** 原runner实际用route_id/provider/model_requested/quota_group，OwnerResearchServices却要求与完整route逐字相等。已仅接受原完整路由或其准确四字段投影，错值/额外字段仍拒；原policy、model resolution及后续SDK检查保留。真实临时owner单例有效RED后1P，不把表示适配当新授权或金融资格。
27. **过度设计仍藏在有效规格里。** 任务卡残留101处逐卡独审、逐断言回执或额外清理证明要求，与产品节点节奏冲突；1.10.18已统一清掉。108任务/368行为保留；G0—G6是验收范围，不是开工许可。无关HEAD/文档变化不重签，普通测试沿用临时目录和finally清理。
28. **本地预览的一小时不是实际权限期限。** 输入、身份和配置未变时，固定小时门只迫使重做准备；已取消，apply仍核当前原owner快照与原确认的真实有效期，未知apply不自动重试。
29. **原样保存和重复核查不产生新保护。** 已持久化相同配置直接返回，不写文件、不干扰任务；真实变更保一次运行检查与原CAS，不再写后重复核查。外部不同配置热加载仍按原检查。
30. **封存是逐题的，不应等整scope。** 导出取消全ready同步屏障，已有封存包可先入库。原检查器会省略未建work的题，现按原请求求差并保持not_exportable/partial，全部缺题也不误报完成；不造work ID、不重发模型，逐包身份/hash及原ACK保持。
31. **查看状态不用重读一次派发许可。** control(inspect)已只读原工作状态，不再跑额外_registered_permissions子进程或创建内存preview。返回inspected、can_start=false及权限not_checked；start/resume/seal和批次仍按原当前检查。原1.4/1.5范围选择的policy/exposure读取保留，不冒称绕过全部owner验证。
32. **共享final_json原先没有native搜索。** 原研究SDK只发聊天/函数工具，即使给出完整JSON也不产生真实搜索回执。新可选native分支复用原send_search_request的厂商请求、解析、预算与回执，并在同一record_response保存可恢复公开输出；普通工具会话/external默认不改。此接线正在原owner软件E2E及集中独审中，不能先宣称真实模型或金融验证通过。
33. **导出目录存在不表示完整。** 原export先建目录后逐文件写，中断可留下残缺目录。新公共入口只在原export完整返回后同根rename发布，残缺candidate保留，按原CP恢复；不重发已付attempt。原SDK可用的MiMo base/plan URL也不能被旧聊天allowlist挡住，native沿原能力解析；原密钥回显拒绝同时沿用。这三处均已定向修复/独审，基础长软件E2E与尾修短回归分开报告。
34. **可选精确路由接线不等于模型顺位降级。** 当时共享入口只有精确route client。11/02已沿原1.6确认和账本补齐顺位并完成原owner/SDK中断恢复验收；当前本轮软件已闭合，真实金融纠错与全池资格仍不能从接线推断。


35. **没消费者的预览票据仍在占状态。** ExecutionGateway.start早已不拿旧preview授权，但preview还生成ID并维护128项内存注册表；已删除这套死状态，保留兼容字段preview_id=null，启动仍实时核原owner。真正承载名单或准备选择的token不属于这个死表，不能一起误删。
36. **只读查看不需要新扫描输入。** 旧任务检查仍被questions/manifest/authority/owner_config/confirmation等文件缺失挡住。只读分支现只要原查询请求、实体匹配、账本/策略及可运行原CLI；不授予can_start。启动/封存/恢复仍核完整输入。
37. **新凭证系统与日常金融审核被过度前置。** 取消TIME另建独立核查凭证签发/续期的计划，已有核查信息保持只读兼容；普通扫描/入库/查看/缓存不要求逐题独立审核文件。重要数值与风险仍定向核来源，没有核实就如实显示未核实。已有分类/有效短证据可复用，不强制每次重新问LLM分类或每题另发搜索HTTP。


38. **可组合演进被扩成了第二个派发控制面。** 未上线的Q15/W16计划要求每次POST跨仓申请permit、消费并生成dispatch_commit，另有每组件资格revision/CAS和active全局ReleaseSet门，与原StockQA权限/租约/预算/attempt防重重复。1.10.19取消Q15及9个许可证专属场景，解除其任务/发布依赖及校验器硬编码。版本元数据、只读影响分析、原owner字段应用和停新派发后的升级回退保留；不承诺无停机跨仓热切。原attempt/unknown/fallback场景保留或归原任务，G3/G6实际目标不变；旧C07离线full_release标签只作兼容，不作为日常准入。


39. **给模型的证据没有完整接进答案保存。** 独立追查确认：EvidenceBoard能过citation closure，但engine、原lifecycle、checkpoint写/读及build_observation仍只用vendor source_urls，provided官方URL未被vendor返回就会误拒。原native软件E2E只回答N/A，未覆盖带provided-only来源的有效scored，这是实质覆盖缺口。现沿原research_intent绑定实际发送的短证据摘要，原vendor receipt/search状态不改；不伪external_context_use，不从运行config直接信任URL。先补真实保存/恢复的scored软件正例，再用原UI做第一方原数实验，仍未金融签收。

40. **第二轮仍有运行冗余。** 自动交付在同一操作两次预览；delivery目标包含模型/题包/标签等无关配置且setup把partial一律当活跃；TIME只读页模拟新核查许可，永远返回verification_missing；测试规范仍要求全仓零漂移和逐文件清理凭证。已分别去重、收窄新目标并兼容旧算法、允许同目标pending修改未来扫描设置、统一真实日期解释及普通临时目录清理。独审发现的原setup残留也已修，不拿类级正例冒充原UI设置可用；错库/原包/在途/未知发送/预算/ACK边界继续保留。

## 当前真实风险

- gen7现已保存CP并获accepted ACK，原score8/模型/响应保留；不再写无CP/ACK。未登记指标已可原样保存并保持未映射，不参加标准聚合。分红年度范围、合并CFO对归母净利、原方案最新状态等金融问题仍未全部解决，入库不代表金融正确。

- 共享1.6顺位软件已经完成，冻结有序目标并保留逐attempt实际模型；普通本机仍policy1.1，不因代码升级自动切配置。剩余问题是普通/共享同HTTP部分结果与内容语义不一致，不是还缺顺位循环。比较与paid恢复保持精确原模型。
- 本轮新反例已完成有界软件修复和独审；合法多期来源只表示不能仅凭年份断错，不证明公式正确。普通/共享公开正文默认同journal，旧无正文记录不能凭hash恢复；预测资料日/来源截止与实际值冲突检查继续。描述长度/事实展示数量不作整答门，ID和其他结构资源边界保留。
- Dashboard NEW-6在最终独立外包候选已复测通过；这是另一Dashboard项目的交付候选，不自动证明本仓原UI已加载它或E07整体通过。原UI不依赖其公司级authority或额外review回执才能日常查看/扫描。

- 原24小时信息日规则仍是legacy默认；显式新扫描时钟已激活，原UI单题真实最近扫描复用正例已完成（同一观察、0新HTTP/费用）。不得把最近扫描可复用误写成资料最新或金融正确。
- 原UI连的是隔离研究工作区，小范围可用不代表全池正式运行；61信息题不等于真实关系资料已采齐。
- PERF36包候选更慢、测量受桌面负载干扰；不装生产、不据它推2000家吞吐。
- 当前doctor就绪只证明本地部署可读，不证明厂商此刻联网畅通或任何新包已获原准入。
- 旧历史报告与冻结卡保留当时结论，不回写已签JSON或伪造golden。消费者不能因旧权限措辞再次索权，也不能因全授权跳过真实接口前置。

## 为什么拖延及如何收敛

有真实缺陷需要修：来源归属/时点、未知计分、入库接续、权限和ACK边界都不能靠测试数量掩盖。也有总控自身的问题：持续分支与支撑包扩张、多次实验/架构路线切换、过多证据维护、状态不收敛，串行集成投入不足。不能把延误全部归因外包模型。

原目标本来包含事实检索、研究技能联动、规模维护与一键配套；后续又加共享引擎、agent/搜索实验、UI、时间策略。前者保留为原未完范围，后者明确已接/未接和是否关键路径，不静默删范围也不无限抬高首版门槛。

下一步只沿[计划中的五个剩余产品节点](task_plan.md#剩余实施顺序与退出条件)推进；不新发卡、不添加小节点审查。进一步PERF/更多案例/更多agent实验不默认挡住原可用链。独审按产品大节点，文档对账采用链接、字节hash、证据与状态一致性检查，无需跑产品全套。

## 11/01本节点的最终判断

共享引擎已从原UI真实调用，并完成已付回答的零API重放、原保存/StockWiki ACK和普通配置同题复用；不再写“未接原UI/未真实启动”。恢复读原scope不应依赖新请求密钥、当前首选模型或新spend；原attempt精确route及原权限、预算、原答绑定继续保留，新pending仍受原eligible与发送守卫约束。

http和https都可能是供应商真实返回的来源；原投影精确成员校验有意义，按scheme误拒没有意义。资料日允许早于检索截止日；发布日期未知仍保持null，可用已知检索时点与限制说明决定新scan上下文，不伪造出版日期。旧板/事件维持原接受策略，不追认已付旧请求从未看到的原数。

此段记录11/01判断：SDK出站短证据软件链1P/701.62秒并非供应商金融准确性的对照结论。随后11/02共享跨模型顺位软件及gen7保存/ACK已完成，不再列作未实现；现金流质量、200家试点、事实与消费者仍未完成。最新开放问题见本页当前风险与根Next Step，不新增支线或核查凭证。

## 2026-11-05 F05 / G3 支撑包验收发现

- G3 合成200主体批次接续工装交付与独立审查通过，但不代表真实200家公司试点、真实入库链或生产 G3 已完成。
- F05 owner 查询候选的代码与定向测试可用，仍缺 IQS 消费端事实契约/公开入口互操作和受支持的真实 owner golden 来源；因此保留 `partial`，不拿 synthetic runtime 当真实 golden。
- F05 历史全套离线计数记录存在差异：1519+55+39=1613，另有“10 errors”说法；总控 collect-only 得到1616项。精确的19个导入错误模块列表已复核，但未重跑整套以核对旧运行数字。旧全套结果保持 failed/unresolved，不扩大门禁，也不宣称与基线的运行结果已由总控重验。

## 2026-11-05 F05-IQS-CONSUMER-01 总控验收

- 原交付的 `verify_export()` 只重算导出体自哈希，不能证明候选来自请求绑定的 owner profile；即使攻击者改候选后重算自哈希，也缺少公开 presenter 响应校验入口。总控直接补 `validate_export_response()` 与公开 CLI `facts-export-response`：用请求、owner provenance 和 profile 重新构造 sealed query result，再构造 expected export，比较完整响应；自哈希只作为一层，不能替代来源/查询绑定。
- 独审另发现 capability 1.2 把 wire 2.7 排在 2.6 前；现按版本顺序输出并精确测试。
- 施工卡曾要求 operation 改变时查询哈希也改变，与冻结 owner 的规范化规则冲突。已改为明确：query_facts 与 export_facts 是同一逻辑查询的两种呈现，共用 query hash；冻结 owner 与测试作为依据。
- 继续相邻场景复审时发现：`information_cutoff=null` 的跨日 snapshot replay 应取已存 snapshot cutoff。现新增 `_materialize_for_response()` 从 response watermark 取 cutoff，再让重建 query hash/snapshot id 绑定验证它，普通响应验证共用同一规则。独立审查已要求重点复核被篡改 cutoff 不能借此绕过旧 snapshot ID。
- 独立审查确认导出来源/查询/快照绑定和跨日 cutoff 回放均未发现实现阻断。审查员建议直接覆盖保留原 snapshot ID、篡改 cutoff 并重算所有导出哈希；该反例已在最终提交 `08e5b4d6` 中加入且 targeted test 通过。审查员受 Lab Git ACL 限制不能自己执行 `rev-parse`，总控已核实本机 HEAD 与 handoff 一致。
- 最终 facts/capabilities/public CLI 为82 passed；exchange/query+deployment为30 passed、7 subtests passed；旧 query v2 为64 passed、1 failed，仍为冻结基线已知 `model_self_qualification`。隔离代码包可签收，F05整体仍partial，待正式产品接线/真实owner golden/公开CLI互操作。

## 2026-11-06 F05 消费端主线接入

- 消费端 payload 已并入 IQS `master`（`da34654`），事实契约、公开校验CLI和2.7能力声明不再只是隔离Lab代码。主线 F05 专项82 passed；加相邻 exchange/query 回归97 passed、7子测试。
- 合并没有接入 StockWiki 当前部署或实际 owner query runtime。测试中的 owner wrapper 来自冻结候选 Git 提交，临时归档后清理；它证明协议/CLI合约可互通，不等同当前 owner 真实运行、真实 golden 或生产接线。F05 状态继续为 `partial`。
- `model_self_qualification` 旧 query v2 失败在合并前的隔离验证已出现，当前主线合并回归再次出现；它不是本次增量引入的错误，仍应作为独立历史缺口跟踪。


## 2026-11-07 主线消费者施工包接收结论

- IQS 的中心 package catalog 漏登新包，是三份正式 handoff 首次被拒绝的根因；现在登记了 F05-OWNER-MAINLINE-02 / TH-IMPL-02 / IN-IMPL-02，并用一条参数化回归防止重复。13项 intake CLI 单测通过。
- 三份 handoff 的结构、范围与已引用提交/哈希现均通过公共 `--verify-references`。这只证明接收资料可复核，不代替 reviewer 审查或真实产品集成。
- F05 owner 隔离代码包已接受但仍 `partial`：真实 owner golden、受支持的只读 runtime、当前 IQS public CLI 正反互操作、canonical StockWiki 合并和部署仍未完成。Theme 与 Industry 只完成固定 facts 2.7 合同下的离线消费者代码包，尚未写入各自 canonical skill 源仓。
- F05 Lab 中发现的临时 junction、额外 baseline clone 和 `f05-capture-0qtex5ju` 均经精确归属核对并清理；报告/JSON保留其历史创建事实。后续验收若再次发现外部临时产物，应先核归属并只清理本包明确创建的目标。


## 2026-11-08 TH/IN source-integration acceptance findings

- TH capability routing assumed every JSON `operations` array member was a string before converting to `set`; valid JSON with a non-string member could raise `TypeError` and abort discovery. The isolated source Lab now validates the list element types first, returns an explicit unsupported/gap result for malformed entries, and still finds later valid entries. Regression suite: 59 passed.
- IN handoff described three delivered skill files with one combined hash. The public verifier hashes actual delivered files and could not resolve that aggregate. The handoff now exposes each produced file as a separate interface, pinned to the result commit and exact Git-blob SHA-256; public verification passes.
- These are distinct from F05/W11 production integration. Both accepted outputs remain isolated skill-source candidates; neither canonical skill tree was modified.

## 2026-11-09 当前独立复核结论

- **已关闭的具体缺陷：** 之前 PWF 标记为冻结兼容基线的 `model_self_qualification` 失败，经本轮复现后确认不是“无害的旧失败”。答案 schema 对新增字段的向后兼容策略让模型自报 `check_level` 穿过语义校验。现从答案校验的公共入口拒绝等级和回执字段，增加两种重封装反例；66项 query v2 全文件及答案语义组合 106 passed、8 subtests passed，独立审查通过。路由集成测试原先仅比较返回列表和返回总数的内部一致性；已改为按 manifest ID 检查题目覆盖、重复与集合差异，定向 3 passed、独立审查 ACCEPT。
- **没有全部关闭：** StockWiki owner 代码已进入本地 canonical `master@3799b43`，但无 remote；IQS consumer 候选仍在已推送隔离分支、因主线 2.8 WIP 尚未并入。真实 owner 查询仍无事实行（`coverage_gap / no_bound_fact_observations`），所以还缺真实正例 golden 和当前 canonical owner/consumer 的端到端互操作。
- **解耦并未全仓完成：** 现阶段已建立版本化 IQS/StockWiki F05 JSON CLI、capability declaration 与对应范围的 AST 防回归，但各仓所有模块的 public facade、私有调用/导入规则和依赖方向还没有一张完整且可执行的边界图。旧的私有导入数量是历史快照，不作为本轮精确统计。Python `_` 不是访问控制；适当保障是在 CI 用 AST/import-layer 规则阻止跨边界访问，再用公开 CLI 的契约/集成测试验证。
- **过度审查/门禁：** 当前没有证据表明已修问题被额外的重复审批或逐文件验收阻断。身份/作用域绑定、来源与时点、费用预留、未知请求防重、锁与 owner ACK 属于业务不变量，应保留。重复的许可库、资格审批/续期回执、每个小节点的独立审查仍不应恢复。主要治理缺口是 PWF 过时，而不是门禁太少。
- **第一性原理收敛：** 项目慢在“真实数据接口是否能产生可绑定 facts、接口版本是否被两端同样理解、候选如何安全进入主线”，并非缺更多施工卡或更大测试数量。所有仓库先各自拥有数据/实现，通过小而稳定的公开 DTO+schema/capabilities/CLI 通讯；中心 IQS 只协调依赖版本、验收状态和剩余阻塞。单仓单 writer、契约前置、单元/合同/集成/少量真实 E2E 分层，避免把测试报告与接收回执做成第二审批系统。

## 公开接口整改后的边界

- 工作台应请求完整的交付范围、接收方查询和时点解释，底层解析、传输和资源文件由各模块拥有。架构回归对常见静态越界报告文件、行号和符号。Python 动态反射和跨对象传播需要在后续实际场景中单独覆盖。
- StockWiki 的事实读取命令可以把查询快照写盘。消费者明确传入自己的 capture root，持久到下一次翻页、回放和导出。查询与导出各自绑定原操作的快照。验证响应必须同时核对请求 ID、操作、快照和导出水位。
- 还有跨仓源码路径耦合。IQS 交付读取的内嵌进程仍加载 StockQA 的 projection 函数，适合迁移到 StockQA 自有的公开命令。B03 仍直接加载 StockWiki 公司评估模块，可改用已有的 `dashboard_company_assessment_cli`。查询版本适配目前还依赖基础校验模块的内部函数，适合用一个版本化入口收敛。
