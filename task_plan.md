# invest-quick-scan 当前实施计划

本轮历史任务（2026-11-02）：[D1–D7 解耦整改](docs/implementation/reviews/DECOUPLING-2026-11-02/remediation.md)已通过定向测试和独立对抗审查。公共结果接受合法扩展，慢命令与读取隔离，旧任务选择原发布资源和原请求规则，UI保留未保存草稿，执行和存储投影由各组件负责。此前的实际业务验收范围以原记录为准。

执行状态：StockQA `01f20d6` 已推，GitHub CI 41532137887 已完成且成功，本地默认检查306项通过。上一节点的文档构建和发布通过证据见[CI根修](docs/implementation/reviews/CI-ROOT-CAUSE-2026-11-02/report.md)。

**2026-11-06 主线更新：** G3 合成批次接续工装已独立审查并接受（31 passed）；它只证明测试工装可用，真实200家公司试点/G3仍未完成。F05 IQS 消费端代码现已合入本仓 `master`，提交 `da34654`；新增 facts 查询契约/公开CLI、2.7 wire 能力声明及测试。F05 定向82 passed；加入相邻 exchange/query 回归共97 passed、7子测试通过。测试使用合成内容与冻结 owner 候选代码，不访问生产库或收费API。F05 仍为 partial：当前产品尚未接入实际 StockWiki owner runtime，也未完成真实 owner golden 与当前公开 CLI 互操作。旧全套离线计数仍未解决，不据此声称全套通过。

## 当前结论

**已到“小范围可用、规模化与研究联动未完”的阶段。** 原8766工作台能够维护名单、组合题库、真实扫描、入库、查看与比较结果并恢复历史任务；不是还没接通模型或数据库。原工作区明确为`isolated_research`，不是全池正式投产。

截至2026-11-04，B03公司结果读取代码已合入investment-dashboard main和IQS master；只读UI候选也已合入其UI仓master。代码链合入不代表原8766已重载或真实owner扫描已完成。本文件是唯一当前状态与执行顺序；[progress.md](progress.md)只记阶段证据，[findings.md](findings.md)只记结论/风险，[交接](docs/implementation/handoff-for-new-agent.md)只说明如何接手。原数千行记录已[原字节归档](docs/implementation/archive/pwf-through-2026-10-31/README.md)。历史日期报告和施工卡是当时的范围/证据，不能覆盖本表；也不能因本表更新而改签旧验收。

## 目标和不可变边界

为用户认可的公司池建立持续更新的评分与事实画像、可解释筛选、历史/模型比较、产业链检索和两个深研技能联动，并最终完成配套部署。约2000家是原长期目标容量，尚未完成，不能自主生成名单或假报覆盖。当前认可池215个实体不是2000家，也不是216个挂牌候选。

- 快扫只存结构化问答、时间/模型/版本/来源与必要执行记录；不下载保存公司财报、公告或网页全文。
- IQS管题库/路由/薄接线；StockQA管模型搜索、任务、费用与恢复；StockWiki管身份/名单/观察/ACK/查询。复用company-wiki能力，不另造客户端或数据库权威。
- 用户已有必要跨仓修复、独审、正常提交推送授权；不再逐文件重复问。每仓同一时间只允许一个writer，不覆盖其他进程内容。
- 准确性优先；未知不补分，低分不触发择高重问。软件通过、真实ACK、金融内容可信、缓存fresh及规模资格分别判断。

## 实际状态总表

|链条|当前状态|证据/限制|
|---|---|---|
|题库与组合|已实现并接UI|48评分模块/222题；另61信息题。所有公司基础36题=核心24+杜邦7+五力5，数量派生，非硬编码24上限|
|身份/名单/比较/UI|原UI已接|215实体；手动增删/恢复、TXT/CSV审阅、模型/时间对比已接。并非全池有答案|
|Dashboard公司结果/B03|跨仓代码已并入各自主线|Dashboard main合同0.1.2-d、B03合并f501f32；IQS master已合入并推送B03代码fb262e0；只读UI仓master 47d5354。定向测试通过；原8766未重载，真实owner扫描未运行|
|原部署|当前可用|原GET doctor `ready=true`、`blocked_reasons=[]`，该GET不发模型；11/01 gen7的1次真实HTTP及11/02零API恢复/入库见本节点终验。入口`http://127.0.0.1:8766/`|
|远端持续集成|StockQA 最新 master 已绿|`01f20d6` 的 CI 41532137887 已完成且通过。上一节点的 Documentation 41523660825 构建与发布通过|
|模块解耦|D1–D7 已整改并独审|服务组件195项、原UI 228项通过（6项跳过）、历史独审72项及尾测135项，详见本轮报告。测试分组有重叠，按范围分别记录|
|共享引擎实际入口|已接原UI，真实单题恢复/入库/复用已验|gen6已付恢复/ACK及普通cached1保留；本轮gen7另已零API保存/ACK，新旧观察并存；默认配置保持。未证明共享全公司36题/规模/金融全对；显式1.6顺位/原已付窗口隔离E2E已验；普通配置仍原1.1|
|三市场真实工程闭环|已验收|微软/宁德时代/腾讯各36有效槽，共108；105原成功+3真实替代，原失败保留|
|入库与历史恢复|已验收|原ACK、同配置冷重启108槽元数据一致、0新增HTTP；不等于TTL命中|
|真实过期刷新|已验收|A/B两次单题刷新均原ACK；信息日旧，按原24h规则仍不fresh|
|有效期内真实模型最近扫描复用|本机单题正例已完成|CATL DUPONT_02原UI再次准备命中同一观察；无执行包、0新HTTP/费用，原扫描时间与资料日保持；不授予事实最新或金融正确资格|
|TIME/RESULT|已接原服务只读视图|10/30验收样本为112条clock-only/1旧release未绑定；只读时点解释保留，不再建设独立核查凭证签发/续期链|
|ANSWER-AUDIT-30|审计范围签收|51源全尝试，35可读/16不可读；63外部命题22支持/25部分/16不可评，不宣称评分金融全对|
|IMPORT-PERF-30|研究范围签收，未启用|68不同测试、24合成测量；36包候选更慢，不作为基线发布阻塞|
|评分校准/G2|受限范围已签|G2 r2 `verified_for_local_gate_scope`；原60家+20重复配方未全完成，实际为获准6家缩样，不能称60家校准完毕|
|200家可靠性/L03/G3|未完成|G3合成批次接续工装已验收（31 passed/0 failed/0 skipped），仅属软件支撑；不替代200家真实试点、真实 owner ACK 或正式G3|
|事实数据/关系查询/F05|部分基础存在，整体未验收|IQS 消费端已合入 `master`：`da34654`；facts/capabilities/public CLI 82项定向测试通过，连同相邻 exchange/query 组97项及7子测试通过。owner 候选 `63a6ffcf` 仍为 partial；实际运行时接线、当前真实 owner golden 与公开 CLI 互操作仍缺。旧全套离线数字未核清，不作为通过证据|
|主题/行业消费者|预研已签，正式集成未验收|依赖真实F05/W11等功能接口，不再等待200家G3；不是缺用户写权限|
|全池与完整配套/G4—G6|未完成|2000覆盖、事实/两消费、配套安装/升级回退不能由本机启动成功代签|

证据总入口：[本次对账](docs/implementation/reviews/PWF-RECONCILIATION-2026-10-31/report.md)、[三市场恢复](docs/implementation/reviews/UI-INTEGRATION-30-2026-10-30/native-three-market-recovery/cold-independent-final-review.json)、[真实TTL](docs/implementation/reviews/UI-INTEGRATION-30-2026-10-30/native-ttl-and-coverage/README.md)、[四包收口](docs/implementation/reviews/SUPPORT-CLOSE-2026-10-31/report.md)、[原TIME/RESULT接线](docs/implementation/reviews/TIME-RESULT-WIRING-2026-10-31/report.md)。

## Next Step

**回到小池内容质量与事实主线。** 定向核原数和会计范围，补真实事实、查询与研究使用链。F05 的 IQS facts 合约/校验CLI已进入主线，但还需连接受支持的 StockWiki 只读运行时并用真实 owner golden 做正反互操作验收。原CPP保存、当前原authority目标封包、StockWiki ACK分别判断；原缓存引用不算新包，partial/subset回执只补缺口；旧ready不占补封实际进度额度，原stored ACK先恢复，终态job迟到worker不复活。私有暂存不作恢复依据，派生UI cache可由原精确字节重建。B03接口代码现已合入Dashboard与IQS主线，生产服务尚未重载，真实owner扫描/三市场UI验收仍待完成。

- **11/02 gen7新增终态：** 原`run-5a03133643e34e60b69d6b9b311b46c0`/work`WORK_ef7cfb7bd41740ab95e2d31af6c78548`已保存CP并delivered；ACK `ack_fd86eacd8b792b505a582f13`，原score8/MiMo Pro/11月1日响应时间不变。最后一次原UI恢复exit0、交付job completed，非重新提问；原响应及普通配置hash相同，账本无新增费用。
- 原UI任务`run-73ab08b815574449a6337c806a9bb2cc`的同一generation6已恢复并入库；原attempt、响应hash、时间、正文及score7保持。交付job`deliveryjob_275e156668c52d138ea84887f11626c8`在08:28:19Z取得原ACK，1/1 scope，不能重问这笔请求。
- 普通policy11/1.1、successful_scan/24h及prepare原字节设置已恢复；pack2、thinking=true、max32768，shared配置和comparison refs撤回。保留全部60个登记包及所有旧答（59为旧快照）。08:35:49Z原UI同实体/合并主体/截止日/模型再预览IQS_11，cached1、执行包0、0API、原owner未变化；复用同一`obs_37dc46500bdffc1cb28152df715fe576290af3cb8c6ca84db10f9036deed3188`，资料日10/29与原成功搜索时间07:33:28.670089Z不变。
- **短证据验证的准确边界：** 原软件E2E的新unknown-published短证据确实进入SDK实际HTTP载荷并通过intent/CP/封包/复用，仅vendor wire脚本化、0收费。gen6当时两条原数被过滤，旧板仍empty、provided_context_sources仍空，不能追认；后来的真实gen7已实送短证据且完成保存/ACK，两代不能混称。本节点不声明金融内容全部正确。
- 相关验证：IQS语义/引擎50P；QA入口15P；Lab四模块41P；seal11P；原252P/1F中的旧held_preview失败已修并定向通过（结果有重叠，不相加）。唯一完整owner/SDK短证据E2E最终1P/701.62秒，先前498.94秒失败和修复保留。自有临时环境已清理，未跑小时全套或新增凭证。
- 集中非作者审查已亲读原账本、CP、响应、ACK与旧/新证据板并通过工程范围；不授金融准确性。之前未定位的旧AppContainer临时目录没有擅删，本轮重新运行的隔离Lab/QA/E2E根均确认已清理。

本节点细节与历史已知金融错误见[原报告](docs/implementation/reviews/CASHFLOW-CORRECTION-2026-11-01/report.md)及[progress](progress.md)。不再按下方历史暂停、旧generation5或尚未真实启动的说法重新派发。

## 本轮继续减负

- 删除已不参与授权的ExecutionGateway预览票据及内存注册表；兼容返回preview_id=null。只读任务检查不再要求新扫描才用的题包、模型或授权文件，仍核原查询实体/账本；真正派发和恢复保护不放宽。
- 取消未上线的Q15和逐POST跨仓permit→consume→dispatch_commit、组件资格审批/CAS、必须active全局ReleaseSet等重复门。原StockQA的主体/题义/权限、租约/attempt/send_intent、预算原子预留和未知请求防重足够承担派发职责，不另造第二授权系统。
- V16保留版本/兼容声明；V17只读分析影响；W16只沿原owner幂等应用字段缺口/投影，保留必要字段CAS；升级采用停止新派发后切换/回退，不承诺当前不需要的无停机跨仓热切线性化。G3、事实/消费者和安装/回退等真实产品目标仍保留。
- TIME凭证签发/续期体系取消；逐题人工/独立审核文件不是日常前置。重要数值和冲突仍定向查证；未核实不标金融通过。分类和真实短证据能复用就复用，不机械重问分类或逐题搜索。

第二轮实查并删除：自动交付同一操作重复调用import_preview；新交付指纹只保七个实际owner/接收路径字段，原UI等待交付时可改后续模型/题包设置，接收目标和原包不变即可接续。旧1.0/1.1按原算法兼容，无法证明的旧配置不自动迁移。TIME统一只展示原日期，不再构造captured-context复用判定或verification_missing门；真实复用仍由原owner决定。测试沿自有短TEMP和finally清理，不再要求全仓快照、逐文件hash/owner清单或单独清理证明；历史夹具及记录保留兼容。

现行规格1.10.19为107任务、359行为场景、52约束；删除的Q15/9项许可证专属场景是范围取消，不是验收通过，历史原件不改签。只做相关测试和同节点独审，不生成新的审查回执。当前真实金融复核、规模、事实与消费者等未完范围仍如上；本轮共享顺位软件已另行完成，不因减负代签金融或全产品资格。

## 剩余实施顺序与退出条件

不是新增任务或新门；把现行任务目录与后续交付收敛到下列产品节点，原全目标不缩减。

1. **完成小池使用闭环与质量修复。** 已完成上述fresh正例；先按Next Step统一逐题保存/恢复和共用语义，再处理ANSWER已发现的错期间/错公司/复合命题支持不足。按字段/命题保留缺口与定向查证，不把质量标签再次变成整答保存门。原历史不覆写，不承诺样本外零错误；原校准配方不足要如实报告，不拿测试数量换准确率。
2. **批量可靠性与G3。** 复用已绿的软件和已认可池，核L03原前置/预算，分批累计原200家真实试点、中断恢复/导入幂等/额度切换/成本与时效证据；合并一次正式审查。三家真实流程不重做成新成果。200家是规模验收目标，不再作为事实、消费者和小样本配套功能开发的前置。
3. **事实与F05。** 按原F任务补真实事实及方向/分部/商业化/时点/证据关系查询，取得真实owner query/capabilities/golden与可重复生成命令；严格与探索正反例完成后签收。IQS 消费端 [F05-IQS-CONSUMER-01](docs/implementation/parallel-lanes/packages/2026-11-05-f05-iqs-consumer/F05-IQS-CONSUMER-01.md) 已完成独立复审并合入 `master`（`da34654`）；新增公开导出校验、跨日快照回放、facts CLI/capability 2.7 均已在本仓测试。下一步不再是重复合并，而是把主线消费者接到受支持的真实 owner 只读运行时，并由总控用真实 owner golden 对公开 CLI 做正反互操作验收。可与G3独立实施，不必先完成200家试点；真实功能验收保留。
4. **TH/IN正式消费与G4。** 只接原查询/固定快照分页/画像/元数据/原补扫，保留池外发现和各自研究方法；核实源仓及实际加载镜像，实际原入口E2E。原包中的G3串行门已由1.10.17取消，按真实F05/W11接口准备实施，不能因此声称G3/F05已关。
5. **扩容、运维和配套G5/G6。** 用户认可名单逐步扩至目标容量，完成覆盖/费用/维护与配套安装、加载、升级回退、统一操作入口的实际验收。当前本机一键开UI不等于全部安装发布已验。

**2026-11-04 主线支撑包（2026-11-05 已验收交付）：** [F05-FACT-QUERY-01](docs/implementation/parallel-lanes/packages/2026-11-04-mainline-support/F05-FACT-QUERY-01.md) 在 StockWiki 隔离克隆交付 owner 侧事实/关系查询候选，`status=partial`；[G3-BATCH-RESUME-HARNESS-01](docs/implementation/parallel-lanes/packages/2026-11-04-mainline-support/G3-BATCH-RESUME-HARNESS-01.md) 合成200主体批次接续工装已交付，工装包完成但生产 G3 `not_closed`。handoff 分别位于 `C:\Users\郑曾波\Projects\iqs-stockwiki-f05-query-lab\docs\handoff\F05-FACT-QUERY-01\handoff.json` 与 `C:\Users\郑曾波\Projects\iqs-g3-batch-resume-harness-lab\docs\handoff\G3-BATCH-RESUME-HARNESS-01\handoff.json`。两包均不改 canonical StockWiki/IQS 产品代码、不调用收费 API；详情见[施工包索引](docs/implementation/parallel-lanes/packages/2026-11-04-mainline-support/README.md)及[进度记录](progress.md)。

**2026-11-05 F05 IQS 消费端施工包：** [F05-IQS-CONSUMER-01](docs/implementation/parallel-lanes/packages/2026-11-05-f05-iqs-consumer/F05-IQS-CONSUMER-01.md) 使用冻结输入 IQS `aca0f4be5adcb96f0c7d8f58e0c4a205e6c17981`、F05 owner `63a6ffcf23f8d16f47acf44bdbcf3e567a85458e`，在独立 IQS Lab 完成事实查询合约、四个 owner wrapper CLI、消费端公开导出验证入口与 2.7.0 能力兼容。总控修复了导出自哈希与原查询/owner profile 解绑、跨日 snapshot cutoff 误拒，并纠正了 query/export 共用查询哈希的施工卡语义；能力1.2 wire 现在按版本排序。最终 Lab HEAD `08e5b4d660bd09cfbb6fe9cba0d7ec7aad31d388`，定向82 passed、相邻/部署30 passed+7子测试；旧兼容组仍有1个冻结基线失败，不冒称全套绿。独立复审未发现实现阻断。该交付只关闭隔离代码包，不改变 F05 partial：正式产品接线、受支持的真实 owner 只读入口、真实 golden 与公开 CLI 互操作仍待完成。包索引见[施工包目录](docs/implementation/parallel-lanes/packages/2026-11-05-f05-iqs-consumer/README.md)，交接报告在隔离Lab `docs/handoff/F05-IQS-CONSUMER-01/`。

**2026-11-06 F05 消费端并入主线：** 隔离 payload `08e5b4d6` 已整合进 IQS `master`，主线提交 `da34654`。新增5个文件并修改6个现有文件：facts 2.7 schema/本地消费契约、CLI operation 路由、能力声明及兼容测试；冻结 owner schema SHA-256 保持 `cd3e03417289a99f5194263603ead6d954fd601b875cd3d5c08a74505ba8cbad`。本仓事实/能力/owner wrapper CLI 测试82 passed；加相邻 exchange/query 回归97 passed、7子测试。旧 query v2 的 `model_self_qualification` 仍有1个已知基线失败，未由本包引入。上述 owner wrapper 测试读取冻结候选提交并用自动清理的临时目录；没有访问正式 StockWiki 数据、收费API或生产 UI。F05 仍 partial，待实际 owner runtime 接线、真实 golden 和当前公开 CLI 正反互操作。

PERF再优化、更多参考公司、更多agent/打包实验是支撑研究；现有结论可用，不再让每批支撑交付重开已完成主线。TIME独立核查凭证体系已取消；真正需要的字段时效改进沿原缓存策略实施，保持旧版本和真实日期。

## 实施和审查节奏

只在上述产品大节点集中测试/独审；小修复仅重跑受影响项。不重复小时级全套、不生成逐assertion回执、不反复审交接格式代替真实功能。不因无关文档/HEAD变化重签已验功能，旧交接原件只作历史，不要求补新格式。已有准备job按原ID/token只读关联不重验新配置；恢复、补封、归档在明确点击时核实原状态，不强制先人工inspect；纯缓存预览直接显示原结果，无需确认或登记job。真正写入/派发仍检查主体、题义、预算、幂等和未知请求。本次文档对账不跑产品回归或收费API。

原任务范围/依赖以[任务目录](docs/implementation/tasks.json)为规格，当前版本1.10.19共107卡、359场景；它没有运行status，不能算完成率。此前解除25项人工排程依赖及QUERY-11对应前置；本轮进一步取消101处逐卡独审/额外凭证要求，统一为相关测试和产品大节点集中验收。不削减产品行为，G0—G6只标验收范围，不是正常开发或使用的人工许可。小样本端到端/安装维护不再等200或2000规模完成；规模目标仍保留，未完成项目不自动转绿。

11/01进一步精简已落地：内容未变的预览不再因本地一小时作废（原owner身份/权限及其真实有效期仍核）；保存完全相同的已持久化设置直接返回，实际变更只核一次运行状态；已封存答案可先导出，未完成/未建工作的题保持not_exportable/partial，不等整scope完成。141项相关测试、72子测试通过，独审反例已修复，唯一短TEMP已清理。04:01:44Z原8766已重载，doctor ready、无阻塞，账本仍85HTTP/US$1.999868且0在途/未结。本轮没有新的收费调用，下一主线动作仍按上方Next Step，不另开支线或新凭证。

保留其他writer的`docs/implementation/parallel-lanes/packages/2026-10-10/README.md`，不清理历史未跟踪文件。

同节点尾修也已完成：查看旧任务状态不再重复运行独立派发许可检查或创建preview凭证，明确标记未检查启动权限；真正派发/恢复仍原检查。原执行模块147P、短TEMP清理、独审通过。04:06:54Z原8766已重载，费用无新增；不因本次精简追加小节点验收材料。

## 2026-11-03 B03 Dashboard公司结果服务接入

服务端精确结果pin与主体范围路由已在B03合入IQS master：显式请求pin与owner返回ID必须一致；/link拒绝空pin、重复参数及别名冲突；精确结果链接携带结果ID和owner snapshot的listing/subject范围。只读映射不写生产库。独立Dashboard/UI组合复审已关闭；原8766服务未重载，未运行真实owner扫描。

### B03交付引用

服务代码ec86605及收尾提交fb262e0已合入IQS master（master从5211f00快进）；Dashboard合并f501f32，合同0.1.2-d；UI lab master合入47d5354。IQS原8766服务仍未重载，真实owner扫描未运行。

## 2026-11-04 B03跨仓主线合并状态

- Dashboard：investment-dashboard main已合入f501f32，合同0.1.2-d。
- IQS服务：master从5211f00快进至fb262e0，包含精确公司结果pin、链接范围和查询投影；目前原8766未重载。
- 只读UI：iqs-question-bank-ui-lab master快进至47d5354；该仓没有配置远端。
- 合并后验证：IQS公司结果核心37项通过；公司结果、owner、HTTP及实体视图相邻组103项通过；UI公司结果/返回链接/深链/pin/运行时组29项通过。Dashboard适配与身份回归、OpenAPI生成检查、27项synthetic smoke、TypeScript与生产构建通过。分组有重叠，不将计数相加。
- 真实owner调用、真实公司扫描、数据库新增写入均未发生。剩余主线是原8766实际入口接线与真实三市场扫描、入库、恢复验收。
