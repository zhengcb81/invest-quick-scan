# 全项目可组合演进与向后兼容实施设计

2026-09-26，计划版本1.9.5。本文把题库模块的发布锁思路扩展到快扫运行、身份路由、答案解释、评分、事实检索、数据迁移和结果消费。它是实施规格，不是功能已上线或测试已通过的声明。具体拥有者、依赖、文件边界和验收用例以同目录的 `tasks.json`、`acceptance-cases.json` 为准。

## 先固定边界

不可变的是 Entity/Security/Segment 的已核实身份事件、原始回答、问题/来源/时间/模型/执行回执、观察 ID 与内容 hash、费用和投递记录。可替换的是问题发布包、路由策略、聚合评分尺、事实词表、筛选 lens、逐字段刷新策略、提供商能力适配和查询投影。后者各由唯一 owner 发布独立版本；组合的结果再生成一次不可变 `ScanRecipe`/`RunManifest`。StockWiki 保管身份、股票池、已导入观察及派生视图；StockQA 保管模型配置、搜索执行、尝试、预算和待办；本仓保管题义和跨组件契约。company-wiki 仍是可选深研链接，不保存快扫镜像或公司文档副本。

版本升级遵循 **旧版可验证读取，新派发只用当前获准版本**。旧观察始终按当时发布包和回执解释；新规则可以重建只读投影，但不能改写旧观察、旧评分或 `information_as_of`。题义/锚点发生变化时用新题 ID 和显式 `supersedes`；只变综合权重时用新评分尺 ID；仅改别名或筛选阈值时不调用 LLM。无法证明新旧口径等价的比较必须返回 `incomparable` 和原因，不能画伪趋势或套用旧的“>8”阈值。

组合不是任意插件链。只允许少量经审查的声明式组件，并在发包前解析依赖、排斥、必答风险题、预算、提供商搜索能力、身份修订及输出版本；冲突就拒绝并保留未派发待办。每个组件只有一个发布者；其他仓库消费冻结的 ID/hash 或权威查询，不复制可写配置。公司可以同时有多个行业/阶段附加属性和筛选 lens，但不能按公司私下覆写题义或评分尺。对约 2,000 家的长批次，已领取/已发送的 work 保持原 recipe；新策略从新的 run 或明确的新 generation 生效，并只生成受影响字段的缺口。

## 一份可重放的扫描方案

`ScanRecipe` 是付费前的解析产物，不只是若干配置文件名。它至少绑定：目标 Entity/身份修订与证券/分部范围、信息截止日、评分题发布包及每道题的语义/prompt hash、路由决策和策略 hash、评分尺 release、启用的 lens release、字段刷新策略 release、证据解释/答案schema/解析器release、StockQA提供商能力/有序模型策略快照、搜索与证据要求、最大题数/费用/并发、输出/交换schema、组件发布集和兼容矩阵版本。第一段 `scoring_only` 将事实包显式记为 `absent/disabled`，任务V01/V09及评分扩容路径不依赖F06或G4；V13解析启用事实版的事实发布包、关系本体与词表release，V14复用StockQA现有执行/费用/回执链，V15在StockWiki权威库完成事实字段增量缺口、导入与ACK。敏感密钥、搜索正文和公司文件不进入recipe。解析结果规范序列化后计算内容hash；每个run持有`recipe_id/hash`，每项work/observation引用它以及实际派发版本。

解析顺序固定：从 StockWiki 读取权威身份与现有观察 → 根据已发布路由选择题目模块 → 逐字段计算有效/缺口和必答题 → 解析当前模式启用的评分、lens及可选事实/词表兼容版本 → 向 StockQA 查询真实模型能力及用户顺序/余额 → 验证搜索可执行、题量和费用上限 → 冻结 recipe 与待办集合。`scoring_only`不读取尚未发布的事实包；只有事实模式才检查其发布引用、关系/字段映射与独立事实预算。任何阶段遇到未知能力、缺失必需发布包、冲突题义、预算不足、旧身份修订或不兼容输出 schema，都在模型请求前拒绝相关待办，返回可操作的原因；绝不改用无搜索模型、默认 5 分或静默少问风险题。

同一个 `recipe_id` 不因配置热更新而改变。用户修改模型顺序、评分尺、词表、lens、TTL 或新模块后生成新 recipe；已发送尝试按旧快照结算、回执和入库。新增独立题仅产生新字段待办；旧题只有自身过期、已证实事件失效、题义/作用层/身份改变或用户明确强制刷新时才提升 generation。配置升级不等于全池重扫；规则/词表视图升级在库内重投影，模型调用数应为零。

旧库可能存在早于ScanRecipe的run/work/observation。它们只能以`legacy_without_recipe`只读适配，不能由迁移脚本补签看似历史真实的recipe。题义、身份、模型执行与费用证据足够时可只读复用已答；未决`send_intent`先对账；无法证明兼容者标`needs_review`，自动POST为零。V01验证本仓历史形状，V09验证StockQA旧attempt/费用/outbox，V10负责StockWiki身份与观察迁移，X05/X09从同一公开入口验证升级与回退；EVO-39—41把这条链的旧账本守恒固定为回归。

## 各层的职责与兼容规则

| 层 | 唯一 owner 与可组合部件 | 升级时保留什么、重算什么 |
|---|---|---|
| 问题/路由 | 本仓现有 S04—S06/F06 的发布包和证据路由；不建第二题库 | 旧题 ID/题义/归档包可读；新增题只补适用缺口。路由标签改变要保留前后证据与原因。 |
| 评分尺 | 本仓发布构念映射、同题篮、分母、权重、关键风险门及适用 cohort 的独立 release；StockWiki 构建得分投影 | 原始逐题 1—10/unknown 不改；新综合方法产生新 `method_id`/视图。只有同题义、同期间/作用层/模型口径且覆盖足够时才比较；缺题或锚点变更标不可比。 |
| 事实关系/词表 | 本仓V03冻结关系方向/角色/阶段/时期的本体；StockWiki V07发布别名、同义词、主题路径与映射release，V15承接事实增量缺口/导入/ACK | 原词、原关系、来源和信息日期不变；新同义词只重建索引/投影。`使用设备` 不自动等于 `生产设备`，供应者/客户/应用方不可互换。 |
| 筛选 lens | 本仓V04只定义schema、既有C03规则AST上的组合约束及固定示例；StockWiki V08发布质量、困境反转、主题候选等具体lens及名单快照 | 各 lens 独立返回 pass/fail/unknown、缺失原因和规则版本；合成页面视图不改基础分。质量 critical gate 不得被 OR 绕过，恢复候选不因当前低分被清除。 |
| 刷新策略 | 本仓定义字段级声明式策略与优先级；StockWiki 依据事件/阶段/TTL/人工强制生成待办 | 旧观察 `valid_until` 与策略版本不改。事件失效优先于 TTL；人工强制生成明确新代次；新模块只补新字段；未知日期不能因重新导入变 fresh。 |
| 身份/大池 | StockWiki 将来源候选、已核实 Entity/Security、成员身份和 manual pin/排除分层记录 | 身份合并/拆分、代码变更用有时间戳的映射事件；旧观察绑旧 revision，旧 work 不改写。多挂牌公司实体级只问一次，证券级保持分开。 |
| 提供商/搜索 | StockQA 发布模型能力和搜索回执适配；用户模型顺序及预算仍由 StockQA 管理 | 新模型只增能力/适配 release；必须先证明实际执行搜索。能力不等价的备用不接管已要求搜索的题；额度拒绝与结果不明分开，不重试可能已收费的 POST。 |
| 查询/UI/消费者 | StockWiki 发布带 `schema_version/capabilities/snapshot/watermark` 的只读投影；主题/行业技能只读消费 | 旧 API 在声明的兼容窗可读；新字段缺失回 `unavailable`，不伪装空列表。UI 可按公司/时间/模型/评分尺及 lens 切换，提示不可比与缺口，不在浏览器重新算分。 |

身份和 SQLite 结构本身不是每家公司可装配的插件。它们用明确的数据库迁移、备份、旧版只读适配和事务升级；任何迁移失败都保留原数据、费用和未决请求。安装/启动只接受已核对实际加载 hash 的配套发布集，不能靠相同版本文字认定兼容。

## 可演进组件的发布生命周期与组合边界

不同能力独立升版，但共用一个很薄的发布元数据外壳：`component_id`、稳定`release_id`、专属`schema_version`、规范内容hash、唯一owner、状态、生效时间、`supersedes`、读/写契约范围、能力声明和迁移/退役策略。外壳只统一身份、版本和兼容元数据；题库、router、答案解析、评分尺、事实本体、词表、lens、刷新策略、provider profile、查询API仍保留各自schema，避免把所有配置塞进一个万能插件格式。

组件release的生命周期事件只追加，状态单调经过`draft → candidate → active → deprecated → retired`；不可变的是release工件和hash，任何语义变化必须新建release。只有正反例、历史可读性、兼容矩阵和独立审查齐备后才可具备active资格。**workspace/profile的active ReleaseSet指针是另一条独立状态**：指针一次只指向一个已验证组合，可原子切换；指针切换本身不会隐式把旧release标为deprecated，也不能因指针切回而改写组件生命周期。deprecated由owner显式发布，表示不再接受新派发；retired只读。生产新扫描只接受active指针及仍有新派发资格的所有组件；candidate只做无副作用预览。deprecated组件可以解释历史和结算冻结的旧attempt，但本计划不默认允许其新派发。回退只有在目标ReleaseSet所有组件仍有新派发资格、兼容矩阵成立且隔离回放通过时才可切换；若目标已deprecated/retired或超过资格窗，则维持历史只读并阻断新work，后续只能通过显式审查和新release恢复，不能暗中“复活”。

跨仓`ReleaseSet`是一份不可变配套锁，记录各owner发布的精确release ID/hash、实际加载路径hash和producer/consumer兼容结论；它不复制题库/规则/模型配置，也不创建第二个可写注册库。另由StockWiki在每个workspace/profile维护一个带revision的active ReleaseSet指针；指针事件不改变ReleaseSet内容。X07只生成候选锁，X08只安装并记录真实工件hash，X09在隔离workspace中用stub网络验证实际加载，只有独立激活步骤才可切换生产指针。临时E2E可在自己的fixture中置入test-only active指针，但不能授权真实收费请求。单个owner发布工件仍是唯一权威来源。

组合入口只接受经登记、声明式、可哈希的部件；不支持任意Python插件或模型生成配置直接执行。路由器可由确定性规则给结论，也可由LLM建议行业、生命周期或公司类似属性，但建议要带来源、置信度、策略版本和决策状态；模糊分类回`needs_review`，用户覆盖单独记录。公司可叠加基础、行业、阶段、投资范式模块，必须处理depends-on/excludes、必答风险题、题目预算、重叠构念和作用层。模型无权静默启用新模块、改变题义或绕过困境/关键风险路由。

## 兼容矩阵与升级影响分析

每一对producer/consumer按动作分别声明支持：历史只读、派生重算、新写入、付费派发、迁移。兼容结果使用`supported`、`legacy_read_only`、`adapter_required`、`needs_review`、`blocked`，并说明适配器、版本范围与失败原因；单个semver相同不足以放行，运行组合仍核对实际schema和文件hash。缺能力的旧UI/API明确返回`unavailable`，旧数据走只读适配，新的不兼容写入/付费调用必须在副作用前拒绝。

变更分析沿依赖图传播：component release → 路由/适用公司 → 题目与有限答案schema → 原始观察 → 评分派生/lens → 查询和UI投影。解析器对每个公司/字段输出`no_op`、`projection_rebuild`、`selected_field_rescan`、`needs_review`或`blocked`。新增模块只补新字段；同一问题ID/题义/prompt hash不可原位改写，跨模块重复构念要以登记的去重/优先级规则处理，冲突须blocked而非静默双计分。路由版本变化保留当次候选、证据、置信度和人工覆盖，不能追改历史路由。评分权重、别名、lens阈值和展示升级只重建相应派生视图且LLM调用为0；题义、证据标准、身份或关系语义发生变化时只失效可证明受影响的字段/实体；依赖不全则停止并待审，绝不把“不知道影响范围”翻译成全池重问。

答案解释也需要独立版本。每题保存实际provider/model、题义与prompt hash、有限结构化答案、短依据/来源链接、搜索状态、信息日期、标准答案schema/解析release。完整HTTP响应、web_search结果正文、网页或财报文档不落盘。新解析器只有在旧有限答案确实包含所需信息时才可零收费重派生；缺少来源或期间时返回unknown/needs_review，不伪造事实，也不把旧分数改成新分数。基础观察永远只读；派生解读以新的parser/rubric/lens release并列呈现。

每一份公司结论都需能拆分四类变化：公司身份/经营事实变化、模块/题义/答案解释变化、聚合规则/筛选变化、模型/provider变化。比较页面按公司、时间、模型和release维度显示；新增模块不改变同一公司旧的核心构念，方法升级不得伪装成经营趋势。固定回放样本必须包含周期低谷但仍有持久优势的公司、多挂牌主体、模型fallback和旧版无recipe记录；系统版本更新不能清除这类观察对象。

## 分批实施与交接

1. 本仓先发布评分尺V02、lens契约V04和字段刷新契约V05；StockQA V06验证真实搜索/能力快照。V01据此解析`scoring_only`方案；这条评分路径不把F06、事实词表或G4变成前置条件。V09把该recipe固定到StockQA公开待办、attempt及费用路径，V10在StockWiki保存身份/刷新代次与recipe引用。旧题义、已答工作和费用账本的读取回归与新派发预检同时完成。
2. 事实模式分三段放行：本仓V03/F06及StockWiki F03给V13提供事实包、本体和词表，V13只解析事实版方案；StockQA V14复用F02、Q10和V09的逐题执行、预算及outbox；StockWiki V15经F04/W05真实入口生成适用事实缺口、导入不可变观察并幂等ACK。EVO-35—38及42—43验证评分旧题零重问、事实新增字段、作用层、多挂牌、结果不明、ACK丢失和冲突停写。任何一段未完成，不能把事实模式说成已上线。
3. StockWiki V07/V08发布词表映射及具体评分/lens名单投影，V11在V15完成后发布版本化查询。只有派生索引/名单可以重建，原始回答、观察和旧名单版本保持不可变；真实库迁移先在临时副本演练。主题研究、行业研究和UI经能力协商读取同一snapshot，缺能力明确返回`unavailable`，不以空列表冒充完成。
4. X05是页面、CLI、快捷方式的统一启动/附着/停止/续扫入口，只消费已解析recipe及权威身份/缺口。X09从这一入口运行真实组件、临时SQLite和网络边界stub，验旧版读取、版本混搭拒绝、增量补问、两个消费者及浏览器；它不能验收真实联网。X10在同一已安装入口、显式预算与隔离清理器下执行EVO-23及E2E-06的有限live全链。快扫正常路径断言零公司文档下载；文件故障优先注入交换/缓存解析边界，只有真实路径允许临时文件时才验证其下载与逐文件清理。

第一轮V01—V15/EVO-01—43落实扫描方案、评分、事实、筛选、刷新、提供商和查询投影；第二轮V16—V18、StockWiki W16、StockQA Q14/Q15及EVO-44—82/LLM-13—18补组件生命周期、版本兼容、变更影响、答案解析release、活动发布指针、组件资格CAS、两阶段dispatch commit和升级回放。V17只从V10真实公开只读快照和固定自身实现生成纯plan；W16只能用实际锁定的active V16 ReleaseSet及已安装、hash匹配的固定V17实现，对当前权威快照确定性重算完整计划，不接受调用方自报hash或本阶段未定义的签名回执。candidate ReleaseSet仅可预览，不能生成生产generation/work/费用/POST。W16在apply和consume_dispatch_permit事务中核对完整输入快照、身份/成员/范围revision、字段generation、recipe、active ReleaseSet ID/status/manifest/pointer revision、V17实现hash及精确组件集合中每个release的lifecycle/dispatch_eligibility revision。StockQA Q15先耐久写入send_intent_prepared，再调用W16单次consume；W16同一owner事务重新核验资格并记录绑定attempt的dispatch_commit receipt，只有该回执授权一次provider POST。资格在consume前改变则拒绝；commit后最多允许已承诺的单次POST。consume后崩溃若无法证明未发送，进入outcome_unknown、保留费用占用并禁止重放/新attempt。X07只核验候选工件，X08核验安装工件，X09核验隔离运行时真实hash；测试profile的active指针不能改变生产状态。V18在真实临时SQLite中回放升版、候选拒绝、切换、回退和旧attempt结算。G6收口完整包，W16/Q15仍须按逐仓授权执行。每卡先写反例、实施owner局部范围、跑受影响回归并独立审查；唯一owner case使局部验收不能冒充后置全链。测试默认虚构实体、固定时钟、真实临时SQLite、双worker屏障和stub网络；live子场景只有在真实入口、显式费用上限与隔离清理器就绪时执行。


## 1.9.3 全局复核补强：验收归属与派发线性化

本节是当前计划版本的权威修订；若旧段落、旧回执模板或历史审查记录仍用单阶段permit/send_intent措辞，按本节和I46/I49/I50执行。历史报告保留其原始时点，不回写成当前结果。

### 任务与case的完成边界

每个验收case只有一个`owner_task`。owner必须把该case列入自己的`case_ids`；前置任务不能引用后置owner的完整行为。后续任务可以在依赖闭包内重复引用已完成case作为回归，但新结果要记录在自己的任务回执中。`requires_tasks`只列owner运行该完整case需要先完成的任务，不能把owner自身写成前置条件。规划校验器将拒绝无owner、owner未引用、非下游引用、owner依赖未闭合、任何没有本地case的任务，以及依赖环。纯契约参考测试须明确使用固定输入/纯函数；完整持久化、UI、安装、公开入口和多仓行为在第一个真实拥有者完成后才成为完整case。

复核已把前置卡的契约/模型边界与实际生产路径拆开：例如C03只验nullable schema，Q03验实际parser；C04只验纯刷新/状态参考函数，W06/Q06/W10各验其持久owner行为；S05验发布包，S06验路由，W14验跨期比较；F02/F03验事实回复和词表，F04/F05验导入与检索；X01—X07验各自API/UI/候选工件，X08安装，X09实际加载和公开入口。完整跨仓用例显式列出必要owner并留给后置任务，阶段review自身另有owner-local review case。

### ReleaseSet资格与资格快照

`active ReleaseSet`指针和其中每个组件的派发资格是不同状态。V16组件生命周期记录不可变、单调；workspace/profile可以原子换活动指针，但单个组件可在指针不变时被独立deprecated/retired。V17影响plan、W16 apply CAS、W16 consume permit都必须核验排序后的精确组件集合、release ID/hash/status、lifecycle revision、dispatch_eligibility revision、manifest hash和pointer revision。只锁pointer是不够的。资格revision变化且pointer没变时，旧预检必须零副作用失败：不建generation/work/outbox，不留费用预留，也不发permit或POST。旧已承诺attempt仍可按冻结recipe结算。

### 两阶段dispatch permit协议

StockWiki和StockQA使用各自owner数据库，不假定可跨仓原子事务。派发采用明确两阶段状态：

1. StockQA创建受控单调`attempt_id`，持久领取逻辑work，并向W16申请绑定work/attempt/recipe/active ReleaseSet和组件资格快照的一次性permit。permit签发本身不授权HTTP。
2. StockQA本地耐久写入`send_intent_prepared`，然后调用StockWiki W16 `consume_dispatch_permit`。W16在单一owner事务重新CAS活动指针与组件资格revision、核对范围和未消费状态，成功后写入唯一`dispatch_commit`回执并把permit原子标记为已消费。
3. StockQA只有在本地prepared记录和匹配的耐久dispatch_commit回执均存在后，才允许向transport交付**一次**provider POST。资格在consume前变化则拒绝；commit后资格退役不撤销此前已承诺的单次POST，但不允许创建任何后续attempt。
4. permit签发/本地prepared/consume任何一步崩溃都不能让旧permit重放。consume提交后若进程崩溃且无法证明provider未收到请求，必须标为`outcome_unknown`，保留费用预留并只允许同attempt对账；不得fallback或创建新attempt。只有明确未发送，或provider返回冻结策略认可且费用完成对账的retryable terminal结果，才可生成下一单调attempt，并重新进行资格和预算校验。

`send_intent_prepared`是必需的本地审计记录，不单独构成跨仓授权。真正的派发线性化点是StockWiki W16的原子permit consume/`dispatch_commit`写入。不得把历史的“send_intent写完即可POST”描述解释成能跳过consume的旁路。

### 版本兼容与扩展验证原则

新的行业/生命周期/投资范式题包仍按独立owner release组合，不改旧ID/题义/分母；新增字段只触发字段级缺口，schema/解释发生改变时用compatibility matrix区分历史只读、投影重建、增量重问、needs_review和blocked。新增能力不能要求所有仓库同步升版；consumer必须显式协商能力，缺失能力返回unavailable而不是空值。每次升级/回退固定同一组冻结样本，并比较旧答案/观察hash、题包/路由/解析release、模型、时间、费用、work、名单和恢复候选；只有能证明等价的派生可自动重建。计划测试仍不是产品测试，表中case未执行前保持`specified_not_executed`。

## 1.9.4 模块依赖闭包与可信历史读取

全局可演进模型的模块层分为三道不同校验，不能用一次schema校验互相替代：S04 `validate_registry`校验新模块注册图和元数据；S04 `validate_release`在读取归档字节、SHA、模块身份/版本、逐题语义锁和退役墓碑后，必须重新校验从归档对象重建的依赖图；S05历史reader再以可信基线逐版验证真实manifest链、legacy身份和退役ID累计。后者不可仅凭release自带的`release_id`或hash认定来源可信。

`dependencies`代表组合的必需闭包；其引用必须在同一个完整release中存在、无自引用、无环。`conflicts`代表问卷选择时互斥，发布目录可包含互斥备选；组合阶段按无向语义检查，任一选中模块声明另一选中模块为冲突即拒绝。依赖缺失、未决或依赖闭包引入冲突时，S06返回`needs_review/blocked`，不得输出半成品问卷或发生模型派发。模块数组/图遍历顺序必须规范化，避免仅因声明顺序改变manifest、问卷hash或任务键。

历史兼容不通过“字段缺失就按旧版猜测”。仅当归档`module_id + artifact_sha256`精确匹配固定、受信任基线中的legacy对象时，reader才可在内存中把当时不存在的可选`dependencies`/`conflicts`视为空集合；原归档字节与hash保持不变。新引入模块、新归档字节、未知release链或自报legacy标记都不能走该适配，必须字段齐全，或失败为`needs_review/blocked`。S05应对连续release逐版检查这一差异及累计墓碑；S04提供静态图验证，S05 MOD-16/17提供历史reader/基线验证，S06 MOD-18验证运行时选择闭包。

本次全计划复核新增MOD-18这一S06 owner场景；该历史计划快照为102任务、323场景、50条约束。上述数字与当时未修复状态只代表1.9.4时点，现行范围与实施状态见1.9.5附录。

## 1.9.5 兼容窗、测试断言与回执有效性

兼容矩阵的每一行必须绑定精确producer release ID/hash、consumer release ID/hash和唯一动作：历史读取、派生投影重建、新写、付费派发、迁移或回退。生效时间按UTC半开区间`[valid_from_utc, valid_until_utc)`；字段必须显式存在，`valid_until_utc=null`仅在`expiry_policy=non_expiring`时代表无期限。缺少匹配声明、窗口之外、倒置/重叠声明、naive时间或当前UTC不可判定，均在副作用前`blocked/needs_review`。compat window约束的是对应动作；读权限不能借给派发。过期不会删除历史，若无当前可核验旧reader则标`needs_review`，不能套当前schema重释旧观察。

1.9.5曾为复杂case定义稳定atomic assertion ID，并为每条断言设计receipt v2、递归依赖凭证和两轮P01人工签收。2026-09-29依据IQS harness lane审计后，工程任务回执引擎、P01任务和这些关闭门在计划1.10.15中退役。旧任务、receipt和review原件保持只读，校验器/schema/规范/专属测试副本留在`archive/task-receipts-v2-legacy/`；不再刷新或把历史`eligible`投影解释成当前产品完成。

atomic assertion和TDD仍保留，用同一批受影响测试验证owner case；`progress.md`记录HEAD、变更路径、测试命令及结果、样本hash、测试根恢复和未解项。普通任务连续实现，独立review集中在G0—G6和重大接口/迁移/收费/派发/安全边界变化。V16的EVO-83兼容窗边界仍在计划中；当前计划为107任务、366验收case、54约束、G6，所有行为case仍是`specified_not_executed`。

### 本轮代码与证据状态（不得当作计划验收）

在1.9.4审查报告之后，S04的`validate_release`已接入独立依赖图校验；定向module contract/registry/question-set测试及全仓测试曾报告通过。但独立复核发现MOD-14列出的未知/自引用、依赖冲突矛盾、活动ID与退役墓碑、合法互斥备选共存等oracle尚未全部成为固定自动测试，原S04回执仍是计划1.7.0且不包含MOD-14；因此S04不能关闭。S05现存loader还用模块ID而非`module_id + artifact_sha256`精确可信基线授权旧字段兼容，MOD-17已经规定正确行为，但实现仍有P1缺口。全量350 passed结果尚无绑定当前源hash的持久日志/receipt，本记录不将其作为S04验证凭证。完整审查见[PLAN-1.9.5-review.md](reviews/PLAN-1.9.5-review.md)。
