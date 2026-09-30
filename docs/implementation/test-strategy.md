# 测试策略与放行条件

2026-09-29，计划1.10.15。场景库是[acceptance-cases.json](acceptance-cases.json)，目前366个场景；它描述必须验证的行为，不代表已经执行的生产测试。任务卡引用case_id；实施者在目标owner范围内建立真实检查，并把测试选择器与结果记入同一批次日志和`progress.md`。复杂case按独立入口/失败路径拆成稳定assertion ID；一个宽泛测试或总通过布尔值不能代表整案。完整跨任务场景通过`requires_tasks`绑定必要owner，前置卡不能用局部验证冒充全链通过。下游卡可将上游case作为回归参考，但case只能由`owner_task`声明完成。

工程任务receipt v2、P01递归依赖凭证与双重人工签收已于1.10.15退役。每个实施批次记录当前HEAD、变更路径、受影响测试/命令/实际结果、样本SHA、临时测试根清理结果和未解项。历史receipt、review、sidecar与日志原件只读保留；归档副本见[task-receipts archive](archive/task-receipts-v2-legacy/README.md)，不再生成、刷新或用来关闭当前任务。独立审查集中在G0—G6等大节点及真实跨仓契约、迁移、收费/派发或安全边界变化时。

## 测试分层

| 层级 | 检查对象 | 替身边界 | 通过证据 |
|---|---|---|---|
| contract | 类型/状态/作用层/版本/错误码及正反样例 | 可用虚构实体，不能把产品解析器替换掉 | 实际schema validator结果，非法样例明确拒绝 |
| unit | 三值规则、映射、TTL、关键风险、费用计算等纯逻辑 | 固定时钟、固定输入；不模拟被测判定函数本身 | 参数化断言、边界/反例和失败原因 |
| integration | 真实类/CLI、数据库事务、生产者消费者、查询 | 网络使用边界stub；数据库用真实临时库 | 实际公共入口、落库行/回执/输出断言 |
| fault | 中断、租约、竞争、费用预留、导入失败 | 可控故障点、fake clock、受限并发；不靠随机sleep | 每个故障点的前后状态、调用次数与账本不变量 |
| live | 搜索真实性、真实成本、评分稳定性与覆盖 | 不mock所验能力；预设预算、有限样本 | 真实请求/搜索/费用回执、来源与原始结果摘要 |
| review | 经济含义、跨仓归属、证据独立性、结果真实性 | 审查者读取实际工件和实现快照 | 逐项审查、具体问题/修复引用，不以“看起来不错”替代 |

同一个case可同时有离线契约测试与在线探针，例如LLM-01。离线部分通过只能放行继续试点，不能替代G1真实搜索证据。review任务可以用审查表完成，不为文档改动编造单元测试。

## 组件边界与TDD执行顺序

系统按唯一数据拥有者和公开契约拆成六条责任链：StockWiki提供身份/名单快照；invest-quick-scan解析路由、题库发布和ScanRecipe；StockQA持有逐题任务、模型/搜索调用、执行回执、检查点与费用；标准观察/交换契约把答案交给StockWiki；StockWiki持有观察、ACK及只读查询；UI、analyze-theme-value-chain和industry-research通过查询/刷新接口消费。边界图和禁止的跨仓直连见[全局契约](../system-contract.md)。每条边单独做schema/错误语义验证；真正的相邻仓集成必须调用两端公开接口，不得以共享fixture函数或私有模块导入替代。
架构复审结论是“部分松耦合”：契约、注册、路由、交换等纯逻辑可独立测试，但生产跨仓闭环仍未完成。一个本地依赖方向问题是`standard_answers.py`直接调用`question_sets.py`的读取、URL校验、渲染、题库加载和profile校验helper；S07先拆出提示渲染契约并解除两个入口在提示生成上的双向导入，较宽的题库helper/API仍需以稳定契约逐步抽取，不能宣称已完全解耦。现有`test_actual_stockqa_cli_emits_manifest_question_receipt_and_is_accepted_offline`虽运行真实StockQA代码并stub传输，但仍导入上游内部实现，归为owner组件/兼容集成测试，不算StockQA与本仓公开入口间的跨仓验收。真实跨仓集成必须改走两端公开入口。

按TDD推进每个组件变更：

1. 先选任务owner、外部契约和固定失败/成功案例；先写一个能复现缺口的测试并看到它因目标行为失败，而不是因导入、环境或断言本身失败。
2. 只在目标owner实现最小逻辑令该测试通过，再补边界值、负例和错误恢复。单元测试替身只替换网络、时钟等外部边界，不能替换被测解析器、路由决策、事务或状态机。
3. 同一变更组内用目标owner的真实类/CLI及临时SQLite跑集成批次；验证公开输入输出、状态变化、回执hash、调用次数和副作用。跨仓测试使用真实两端公开入口；若其中一端接口未实现，停在当前owner契约测试并明确留待集成，不造一个假adapter宣称闭环。
4. 每个稳定里程碑跑本地离线producer-chain E2E及故障路径；真实搜索、真实数据库导入、浏览器UI和安装后启动另列live/system E2E，必须使用隔离run、有限预算、调用者批准的真实入口和零外部漂移审计。
5. 红测、绿测、回归按大节点合并留证；不要求每个小改动重跑全仓。审查修复后只重跑受影响测试及该里程碑集成批次，然后更新同一快照证据。

本地生产者侧的离线E2E为`tests/test_producer_pipeline_e2e.py`：调用真实`question_sets.py compose`和`standard_answers.py build`子进程，以明确标记的虚构答复/回执作为StockQA边界替身，再运行交换schema与内容哈希验证。测试全过程仅写`LiveE2ESandbox`独占临时区，子进程不继承API密钥或live opt-in，下载目录必须为空，结束后逐项核验并清理。它证明quick-scan生产侧的拼装和序列化契约，不证明真实LLM搜索、StockWiki事务导入/ACK、UI、启动器或E2E-06已通过。

| 当前测试边界 | 已有/新增的代表性测试 | 不能据此声称 |
|---|---|---|
| 单元/模块 | `test_question_sets.py`、`test_routing.py`、`test_standard_answers.py`、`test_module_registry.py`、`test_module_contract.py` | StockQA实际调用或StockWiki实际写入可用 |
| 本仓CLI集成 | `test_producer_pipeline_e2e.py`中真实compose/build子进程及prompt-hash拒绝 | 实际联网、供应商搜索回执或真实provider fallback |
| 交换契约 | `test_exchange_and_query_contract.py`及新增producer-chain末端schema/hash校验 | StockWiki公开导入API、SQLite事务或ACK丢失恢复 |
| 测试环境安全 | `test_live_e2e_sandbox.py`中的真实临时SQLite/文件/进程清理与外部状态保护 | 真实公司数据或生产全链E2E |
| 跨仓/实网系统验收 | X09、E2E-06及G6门 | 在这些case实际运行并通过前，不得标记已验收 |

## 固定样例与精确断言

使用虚构E1/E2实体、S_CN/S_HK证券、example.invalid来源和固定UTC时钟；不要在离线测试里访问互联网、读取密钥或写真实公司目录。需要现有StockQA类时导入真实类，仅将传输替换成stub，并将日志导向临时目录。

| 关键行为 | 固定输入 | 必须断言 |
|---|---|---|
| 分数透传 | provider=8，inner=8 | parser、generator、CLI、消费者均等于8 |
| 未知分数 | score=null，旧外层兼容5 | 正式分仍null，不入规则/均分/恢复优势 |
| 到期边界 | valid_until=2026-09-22T00:00Z | 前1秒fresh，恰好到期和后1秒stale |
| 重新导入 | 三月信息，九月imported_at | 信息时间不变，不能续期 |
| 只改阈值 | 8分，>8改>=8 | fail变pass，但新增LLM调用为0 |
| 费用并发 | 余额10，两个请求各预留6 | 仅一个派发，spent+reserved<=10 |
| 模型顺序 | A失败，B有效，C可用 | 依序A/B；C调用数0 |
| 低分停止 | A有效2分或正常unknown | B/C调用数均0 |
| 部分成功 | 6题中4成功、2失败/缺失 | 保留4题，恢复只补2题 |
| 导入失败 | 模型结果已持久化、未ACK | 仅重投递；新增模型调用0 |
| 质量低谷 | quality=null且恢复有效 | 恢复/普通相关入口仍可见；质量门槛不伪装通过 |
| 关系方向 | 生产者、使用者、研发者同词命中 | strict按方向/阶段/时期区分，不仅匹配关键词 |

这些表格及JSON then字段是行为预期。不要为了方便把实现的当前输出自动记录为golden，再宣称测试通过。

## 必须跑的组合与故障矩阵

- 路由：8个类型×6个生命周期；另测周期标记、物质性属性、银行关键替代、负利润/负净资产、多分部和显式诊断去重。保持已有24核心判断覆盖。
- 模块演进：在旧发布包上追加行业题与通用扩展题；旧题义/分母/分数保持不变。新增无关行业不得改变旧题语义指纹；共有渲染规则变化必须使受影响题不可比。旧manifest按锁定发布包可读，篡改/缺包拒绝；新增模块缺口径、事实覆盖或冲突规则应在付费前拒绝。MOD-01—13覆盖路由、升级、增量恢复、事实与UI；MOD-10须经真实入口和E2E-06隔离清理，不能用离线结果替代。
- 跨组件演进：EVO-01—82和LLM-13—18覆盖ScanRecipe、各域独立release、身份/路由、有限答案解析、评分尺/同题篮、事实关系/词表、筛选lens、字段刷新、提供商能力、兼容矩阵、查询协商、活动ReleaseSet、实际派发围栏、升级/回退及旧账本。V16把单调component lifecycle与workspace/profile active ReleaseSet指针分开；V17只生成绑定完整快照/组件hash的纯影响计划；StockWiki W16从固定V17实现与当前权威快照确定性重算、active release/pointer全量CAS，并唯一拥有dispatch fence schema；StockQA Q15必须先耐久记录`send_intent_prepared`，再调用W16 `consume_dispatch_permit`，且只有匹配的耐久`dispatch_commit`回执授权一次provider POST。EVO-76覆盖lease无permit、permit已签发但本地准备未耐久、准备已耐久但consume未提交、commit已耐久而transport未开始/结果未知四个崩溃点：前三态POST为0且旧permit不可重放；第四态最多允许原attempt一次POST，无法证明未发送时只对账、不盲重发或fallback。candidate只能预览，生产新work必须来自active ReleaseSet。Q14版本化有限答案解释且不保存原始HTTP/search正文；V18在隔离数据库回放候选拒绝、升级、回退和旧attempt结算。EVO-63/75以双worker屏障验证单plan原子性和发布指针切换；EVO-66拒绝自签hash伪造计划；EVO-65验证新门关闭仍能安全结算旧冻结attempt；EVO-73/74验证candidate在owner和公开入口均不产生生产副作用；EVO-77/78验证组件状态与指针回退资格。EVO-64/X07只验候选解析组件hash，EVO-68/X08验实际安装，EVO-69/X09验运行时实载hash。V17必须从V10真实只读快照推导精确范围；能通过V01证据适配的legacy_without_recipe继续只读复用。新增模块不得改旧题义；阈值/词表变化模型调用为0；同ID篡改、退役写入、不兼容调用及影响图不完整都失败关闭。升级样本须含周期低谷但仍有持久优势的公司，保留原低分和恢复观察。EVO-23/E2E-06仍只由X10在预算与隔离清理门通过后运行live。
- 分数：合法1/5/10，非法bool/0/11/小数/字符串；scored、未知、不适用、未联网、低置信度、未审核分别走完整链。
- 规则：all和any各自覆盖pass/fail/unknown的9组两两输入，再测嵌套、空规则、未知操作符及质量gate；N/A分母不能被未审核状态缩小。
- 时效：到期前/恰好/之后、换时区等价时间、未知信息日期、导入/检查时间改变、新事件、题义变化、仅标签变化、新增题和新run。
- 持久化：派发前、发出后结果未知、结果已写、导入前、导入后ACK丢失分别注入失败；再测两个worker、过期租约迟到提交、重复回执和同键异hash。
- 费用：并发预留、已计费失败、备用模型、搜索费用、未知结果、取消/重启、计价缺失。外部提供商不支持费用幂等时明确保留不确定性。
- 轻资产：成功、失败、解析错误、缓存、调试日志、交换包全部检查。不要只检查扩展名；正文可被藏进.json或.log。将唯一的长正文/密钥哨兵注入边界payload，验证所有持久化路径未包含哨兵，URL和短依据仍正确保留。
- 消费者：库内已有/缺失/过期、facts未上线、仅3家定向补扫、池外领导者、无company目录、评分量表不同、跨分部误拼、下游报告循环引用。

## 不以代码覆盖率代替正确性

可报告行/分支覆盖率帮助找漏项，但不设置一个百分比就宣布完成。重点是能抓住错误行为。对关键逻辑做一次有记录的故障敏感性检查：临时把>改>=、null改5、fresh边界改<=、移除预算原子预留、让导入失败重新问模型、忽略关系方向；对应测试必须失败。确认后恢复实现并重跑相关检查。

这种检查仅在临时分支/副本或受控测试注入中做，不修改真实运行数据，不把故障版本留在工作树。无需引入大型mutation工具；可记录局部patch和失败测试，但不得用与真实实现无关的小函数替代。

### 真实数据E2E的隔离与清理协议

真实联网、真实provider、真实下载和真实跨组件入口单列为live测试，不与默认离线pytest混跑。每次测试生成不可复用的`run_id`，在系统临时根目录下创建workspace、SQLite、下载、交换和日志子目录；通过公开配置把所有写入重定向到这些目录，禁止把用户默认profile或正式公司目录当fixture。测试开始时保存外部仓`git status --porcelain`、受保护目录逐文件路径/大小/SHA-256、数据库标识与相关进程完整身份；这些快照既是清理白名单，也是最终零漂移oracle。

所有副作用写入run manifest，至少包含规范化绝对路径、创建动作、创建后SHA-256、owner、run_id及数据库事务/进程身份。清理放在`finally`中，先停止由完整进程身份确认属于本run的进程，再回滚事务或关闭并删除临时SQLite，最后逐文件清理。删除前必须同时满足：路径位于本次临时根、manifest登记为本次创建、owner/run_id匹配、当前hash与登记值一致；不满足时拒绝删除、测试失败并保留隔离目录取证。禁止对计算路径做无边界递归删除，禁止清理测试前已存在或测试中被外部修改的文件。

每个live路径至少覆盖正常完成、provider超时/额度拒绝、导入前中断、导入成功但ACK丢失。快扫正常产品路径不得下载公司文档，必须断言下载目录为空；若某被测路径实际允许临时文件，则追加下载后解析失败与逐文件清理测试，否则在交换/缓存解析边界注入文件故障。结束后重新采集pre-state同口径快照，断言外部仓工作树、用户profile、生产数据库、正式公司目录及非测试进程没有变化。允许的临时文件用本次请求/响应摘要和文件hash证明，断言完成后清理。若清理本身失败，live gate失败且不自动扩大删除范围。

本仓测试支架为`tests/live_e2e_sandbox.py`。它只管理测试目录，不实现StockQA客户端、网络搜索或下载器。每次run先取调用方提供的只读外部状态快照，再在系统临时目录建立唯一run根；`workspace`、`sqlite`、`downloads`、`exchange`、`logs`分开。调用各拥有者公开入口前，用`assert_run_path`核实其解析后的写入配置；若需启动子进程，只能通过`start_process`，默认工作目录固定至run-local workspace，显式cwd必须处于本run目录。完成或发生故障后，关闭数据库/worker，再对五个目录逐文件登记。清理前必须同时通过manifest自校验、run_id/owner校验、文件路径归属、大小及SHA-256校验、无未登记文件、无符号链接/硬链接；所有工件先逐个暂存验证，之后再核对外部pre/post快照，若外部状态漂移则恢复暂存文件并保留run目录。删除仅对manifest列出的单文件执行，其余目录必须为空才逐级`rmdir`；任何不一致均保留run目录并使测试失败，不按临时目录名盲目递归删除。测试异常时上下文管理器仍会尝试受保护的清理；只有清理验证通过才移除run目录，清理失败则保留证据，不会触碰run根外的文件。

离线支架回归用`python -X utf8 -m unittest discover -s tests -p test_live_e2e_sandbox.py -v`，覆盖下载变更/中断残片、SQLite、外部文件保护、清单篡改、路径穿越、外部状态漂移、异常finally清理，以及只停止本次持有的精确子进程句柄。它们验证清理机制，不调用网络，不构成E2E-06的live通过。

## BENCH-01：真实搜索交接与30题调用策略对照

这项小样本实验在L03的200家公司试点之前执行，不等于X10最终live E2E，也不更改全池名单。预注册方案、输入冻结、搜索context结构、请求矩阵、缓存语义、评分盲评、计时/计价及隔离清理见[基准实验方案](experiments/llm-search-and-batching-benchmark.md)。

- 搜索阶段把Brave/Tavily结果规整为短、带source_id/URL/时点的证据context，显式标为不可信外部资料，再与相关题目一同发送；原始response和网页正文不落盘；run专属临时审计工件保留与实际模型输入完全一致的截断snippet（≤500字符/条、≤30,000字符/公司），G3审查后清理，长期报告只留hash/来源指针。供应商原生搜索只有真实执行凭据可验时才单列对照。
- 对固定30题分别测顺序逐题、并发逐题、每批3/5/10题、单批30题。准确性先过盲评和critical-claim门槛，再比较完整端到端耗时与真实计费；不预设“大批一定更省”。
- 搜索缓存、模型prefix cache和应用答案缓存分别做正交子实验：测搜索/模型缓存时绕过答案缓存，避免答案命中短路上游而被误计；完整全链另测cold、同输入warm和材料性hash失效。执行日官方价表与真实usage/账单用于成本；MiniMax套餐quota与现金费用分列，无法归因时不虚构单位成本。
- gold在解盲前由两名独立评审者依据冻结rubric和来源生成；非关键事实抽样support率≥90%，所有critical claims逐条审查且无未解决重大错误，gold可评分项目有效分覆盖≥95%、MAE≤0.75且±1一致率≥90%。不能完成盲评/复核的臂为inconclusive。
- 时延按每个公司×方法的完整run记录。三家单轮报告原始值/中位数/范围，不给run级p90或显著性；只有≥20个同口径完整run才报run级p50/p90。联合推荐搜索源和打包方法需完成2×2交叉，否则结论仅适用于固定context。
- 最终按质量约束后的Pareto前沿推荐；结论须经G3大节点审查。若无打包方案过线，L03继续逐题。离线mock不算BENCH-01完成。

真实入口就绪后，X10运行的live验收矩阵至少按以下顺序逐条运行并保留run回执。表中`E2E-06/A…H`是单个必需live case的子场景；只有所有必需子场景与清理审计通过，才可把E2E-06登记为passed。X10和其他生产/全链live样本只能由用户从其提供的股票池中指定；测试实施者不得自行挑选、补齐或扩展这些名单。唯一窄例外是本轮用户明确要求的BENCH-01：只允许为该配对benchmark选A股/港股/美股各1家公司；只有预注册差异规则触发才可扩至每市场各2家（最多6家），不得导入或改变大股票池。名单尚未提供或用户尚未指定生产样本时，其他live case保持`specified_not_executed`，只运行虚构fixture的离线测试。身份与挂牌映射可按用户指定样本固定断言；行情、经营数值、模型评分随时间变化，不能用脆弱的硬编码精确值断言。

| 场景 | 真实路径与必须断言 |
|---|---|
| E2E-06/A 成功小批次 | 真实公开搜索返回可解析结果；实体、市场、问题、模型/版本、信息时点、状态和来源引用齐全；分数限1—10且`unknown/not_applicable/error`不冒充分数；调用与费用不超显式预算。 |
| E2E-06/B 多挂牌去重 | 仅当用户提供并指定的样本中包含同一公司的多地挂牌时，验证各证券映射到一个公司实体、分别保留证券标识，且批次不因多挂牌重复问同一公司级问题；否则该live子场景等待用户样本，不自行挑公司替代。 |
| E2E-06/C 真实额度拒绝与顺位回退 | 受控使用一个已知会拒绝/额度不足的首选模型，再由用户配置的下一个模型成功；检查拒绝分类、attempt/request ID、总预算、单逻辑题只采用一次，且不能为低分继续换模型。 |
| E2E-06/D 部分结果、停止与续扫 | 仅扫描用户指定样本和问题；中断后恢复相同run，已完成观察不重复收费；未完成/结果不明的请求先对账，不立即重复提交。 |
| E2E-06/E 写入ACK丢失与重放 | 真实StockQA结果经StockWiki公开导入入口；模拟只在ACK边界丢回执，再次投递同ID/hash只产生一个不可变观察，不重新调用LLM。 |
| E2E-06/F 文件/解析故障 | 正常快扫路径断言下载目录为空；在交换/缓存解析边界注入文件故障，并验证HTTP/LLM缓存、日志不写入正式目录。只有被测路径实际允许临时文件时，才重定向到本run目录并追加下载后解析失败、部分下载的hash登记与清理断言。 |
| E2E-06/G 外部状态零漂移 | 每条成功和故障路径比较测试前后的StockQA/StockWiki工作树、用户配置/凭据文件hash、正式数据库/公司目录、非测试进程身份；不匹配即失败并保留隔离根。 |
| E2E-06/H 清理拒绝破坏 | 在隔离run内篡改一个已登记文件、留下未登记文件或伪造owner/run_id；清理必须失败、保留证据，且绝不尝试扩大清理范围。恢复可信状态后才能再次显式清理。 |

X10-A/B/D/E/F/G每个live case只有在各仓真实公开入口齐备、预算/模型顺序已配置且本轮有显式live授权时才运行；X10-C还需已知拒绝路径可控且不触发不受限的付费调用。不能为了测试刻意消耗未知额度。X09只用真实组件、临时SQLite和网络边界stub做离线联调，不能承接E2E-06；X10才从X05统一入口执行有界真实联网。真实数据live矩阵在实际完成前保持`specified_not_executed`，不得把现存real-workspace测试或mock改名为E2E-06通过。

## 当前已有检查怎样使用

在invest-quick-scan根目录可执行：

```powershell
python -X utf8 scripts/question_sets.py validate
python -X utf8 -m unittest discover -s tests -p test_question_sets.py -v
python -X utf8 scripts/implementation_plan.py validate
python -X utf8 -m unittest discover -s tests -p test_implementation_plan.py -v
```

前两项为现有产品基线，后两项只检查实施包及其读取工具。现有`test_actual_stockqa_loader_parser_and_score_path_offline`目前容许输出5或8，且缺上游仓库时skip：这是记录旧缺陷，不是发布验收。Q01修复后，S02必须改成严格8并在具备上游的集成环境执行，任何关键skip都不能通过G1。

外部仓库的pytest/unittest/npm等入口须先核实，再把实际命令和结果记入`progress.md`对应批次。不得复制一条猜测的命令，再因“没有测试”退出码正常就报通过。新增测试要明确路径/测试名及case_id，确认实际被发现并执行；0个测试、关键skip、关键xfail都不能放行。

## 实测质量门槛

以下沿用路线图的试点目标，不是本轮实测成绩。G0记录其初始版本，校准后变更必须说明原因和重新运行范围。

| 阶段 | 必须报告与满足 |
|---|---|
| 10家公司 | 实体正确；真实搜索执行可验证；每题评分/状态/来源关联；实际费用；未联网和缺证据不伪装成功 |
| 60家公司 | 限定重试后逐题结构通过率目标≥99%；单列unknown/无来源。20家重复子集可比较有效分数至少90%相差≤1，同时完整报告缺失/状态变更和比较覆盖率 |
| 规则稳定性 | 同一冻结规则的入围状态一致率目标≥90%；单列7/8/9边界和各cohort/模型；unknown/unknown不能当“高质量稳定”掩盖无有效数据 |
| 重大错误 | 被抽查发现的实体、来源、关键事实错误全部修正并回归；没有未关闭的阻塞问题；不宣称样本外错误为零 |
| 200家公司 | 中断/租约/预算/导入恢复案例通过；真实费用/耗时/有效覆盖/失败/unknown分开；实际备份恢复可复现 |
| 事实检索 | 两个主题的预先标注正负样本；strict精确率目标≥90%，关键反例零误入；探索召回率及未核实比例另报，不存在真值的不混入分母 |
| 约2000家 | 独立公司数、证券数、市场重叠、已尝试/有效/过期/待办分别报告；普通对象不饥饿；评分和事实能力分别验收 |
| 配套一键启动 | 从干净授权部署目录完成setup，任意cwd快捷方式启动；真实组件离线联调+同一入口有界真实联网；G4/G5完整消费与评分证据齐备，实际加载hash一致，重复点击不加任务/预算，升级回退保留数据与费用 |

## 跨项目启动的附加矩阵

DEPLOY-01—08覆盖安装、独立解释器、中文/空格路径、实际加载旧版本、协议不匹配、迁移失败/回退与安装边界；START-01—12覆盖首次配置、无缺口、重复点击、预算连续性、PID/端口身份、关闭页面、停止恢复、已答未入库、本地doctor与收费探针；E2E-01—05覆盖真实组件全链、helper假接线、真实联网与完整发布资格。

X05是页面、CLI与快捷方式共用的启动/附着/停止/续扫逻辑，消费已解析recipe和StockWiki权威身份/缺口。启动恢复先按旧冻结recipe、attempt和receipt安全结算已派发/已答未ACK work，再判断新release是否准入；不兼容时仅阻止新generation/work/费用预留/POST。X09从实际入口启动StockWiki/StockQA组件并用真实临时SQLite，仅模型网络边界stub；验证相同run/work/observation的recipe引用、旧`legacy_without_recipe`对账、两个worker争同一plan不重复generation、调用方伪造plan被拒绝、Q14解析器实载hash，以及重复启动不加付费待办。X09不能执行或登记E2E-06 live结果。X10通过安装后的同一X05入口运行有限真实试点。两个研究技能要经过实际加载入口查询同一库，不能只调用未被技能引用的测试适配器。启动时记录通用研究scheduler/source worker调用为0，避免一键入口悄悄扩大为资料采集。

G6要求安装、offline_ready、live_verified与full_release_verified各自有对应证据；缺失任何必要组件或G4事实/消费者验收时，不因评分能运行就把整个计划标完成。详见[统一启动设计](one-click-launch.md)。

## 企业结果界面验收

UI-01—12覆盖多挂牌身份、分项阈值、缺失/过期、恢复观察、题目替代/汇总、安全来源、可比历史、2,000家公司分页、导航/故障、能力降级、关系查询及桌面/窄屏键盘流程。U01/U02在G5前验收，U03及X09在G6前完成真实浏览器全链；不能只用接口测试、静态样图或HTTP 200代替。截图证明布局，具体值、页面行为、零模型调用和正确补扫范围必须由实际操作断言支持。详见[UI设计](results-ui.md)。

## 自动维护、权威存储与三维比较

MAINT-01—06覆盖手动/自动准入、歧义/排除、并发、断电、预算与多挂牌；STORE-01—04覆盖唯一拥有者、幂等导入、恢复水位与复用旧观察；MATRIX-01—08覆盖公司/时间/模型对齐、未知执行身份、固定核心权重和事实不评分。实际命令/测试仍由各owner绑定，已有本地离线测试不能替代生产试点。

## 失败后的处理

首先定位失败属于实现、契约、环境、样例还是模型/来源不稳定。实现错误修实现；契约确需改变则走设计变更记录并更新受影响case，不能在当前任务里偷偷改预期。环境或预算缺失保留not_run及确切原因。

修复后重跑失败用例、受影响邻接路径和相应阶段回归；没有新变更/失败或新风险，不反复重跑已通过的整个测试矩阵。保留第一次失败和最终通过记录，不能只展示最后一次有利结果。

## 验收节奏与大节点复核

每张任务卡仍须有明确场景、可核验结果和变更范围，但这不规定实施顺序必须逐卡停顿，也不意味着每个小步骤、case或assertion都要单独启动一次测试、独立审查和全仓回归。按自然边界合并同一owner或紧密相连的变更组，连续实现已具备稳定接口的卡；到组或阶段候选稳定时，一次运行覆盖本组相关验收的定向/集成测试。当前366个case是完整行为目录，不要求在每个小批次或每张卡后重复全量执行；每个owner的case在其所属大节点关闭前必须有可追溯结果，跨任务case只在其完整依赖到位的后续节点做全链验收。

一个测试批次的run ID和命令可供多个case/assertion及同组任务共同引用。批次记录应说明相关selector/子测试ID及预期和实际结果，但无需为每项重复运行或另造日志。只有批次输出无法区分某项结果时才补跑该项。开发中的快速自测无需每次都保存为验收工件。修复只重跑失败用例及受影响路径；无新变更、失败或风险时不反复重跑已通过全套。全仓/全项目回归放在阶段候选稳定或G6前运行，不在每张小卡后重复。

独立审查以G0—G6及少数重大风险边界为节点。一次审查会批量检查该节点内多个任务、当前依赖快照、测试批次和问题关闭情况，并按任务留下可追溯的结论；不要求每个任务各开一个审查会或每次修复后重新完整审查。遇到错误实体、分数被篡改、重复收费/丢任务、身份或存储迁移、付费派发围栏、跨仓契约、安全边界等高风险改动时，可在大节点外加一次定向审查。review发现后的常规闭环是“修复→受影响回归→纳入下一次节点审查”；只有修复改变契约/资格判定或涉及阻塞级风险时才安排一次额外复审。保留任务级原子验收证据，不把它误解为每个小节点都要独立走完整流程。历史P01封存前/封存后审查只作为旧流程的迁移记录，不再作为当前任务门槛。

实际批次建议按大节点组织，而不是机械地按任务ID拆开：本地题库/模块/路由相关改动合为一个代码回归批次；同一提供商链路的请求、解析、故障切换与费用检查合为一个批次；身份/持久化/导入接线合为一个跨仓批次；UI与研究消费者合为一个用户路径批次；G0—G6只在各自放行前做一次相应的大范围检查。跨仓写入权限和真实付费/live请求仍按owner及授权边界单独控制，不能因批量审查而扩大。


## 1.9.3 唯一完成owner与兼容/派发竞态矩阵

每个case必须有一个`owner_task`，且所有task至少拥有一个本地case。owner任务对该case的实际结果负责；下游任务引用时必须处于owner的传递依赖闭包并记录独立回归结果。case的`requires_tasks`列出owner所需的前置卡，不能用它代替owner字段，也不能把局部contract case写成跨仓验收。`scripts/implementation_plan.py validate`必须拒绝missing/unknown owner、owner未引用、前置卡引用future owner、要求未闭合、task无owner-local case以及依赖环。

升级/兼容回放按每个独立组件检查read-old/write-current、能力缺失、candidate/active/revoked状态、增量字段与历史固定样本；同一题语义、hash或模型变化不得伪装经营变化。schema和兼容矩阵测试包含旧manifest读取、新字段追加、旧题篡改拒绝、consumer能力缺失、路由候选顺序变化不影响历史、只改lens/别名零LLM、无法判定影响范围时blocked/needs_review。

跨owner派发必须通过双worker屏障覆盖：组件资格revision变化但active指针不变；permit签发后、consume前资格改变；本地send_intent_prepared和consume之间崩溃；consume/dispatch_commit已提交但provider transport尚未或可能已开始时崩溃；明确的retryable拒绝与unknown-after-send；重复claim、伪造/重放attempt_id及预算迟到结算。每个分支分别断言generation/work/lease/permit/dispatch_commit/HTTP POST/费用预留/ACK，不只比较最终分数或状态。consume之前必须POST=0；consume成功后最多一条POST；outcome_unknown不得产生新attempt；资格被撤销不得影响旧已承诺attempt按原recipe结算。

以上只固定测试设计。本阶段本仓运行计划校验器和其单测，不运行StockQA/StockWiki产品测试、live API、下载或跨仓迁移。

## 1.9.4 模块归档图与组合/legacy反例

`MOD-14`必须把循环图、缺失/自引用依赖、同模块依赖/冲突矛盾、active与retired tombstone冲突放进**归档reader入口**，并让攻击归档的字节hash和release_id都正确，证明拒绝来自结构校验。`MOD-16`在S05真实历史reader复测归档图完整性；`MOD-17`分别验证可信基线精确hash允许的旧metadata省略，以及新增/改写模块省略必需字段或自报legacy时拒绝；`MOD-18`验证S06只对本次选中组合闭包依赖、无依赖环并按对称语义阻断conflicts，发布目录含互斥备选本身允许。

三个测试层分别断言：release目录可包含互斥候选，归档依赖图必须闭合且无环；依赖字段缺省只有精确命中可信legacy artifact时可在内存适配为空；实际组合须展开完整依赖且没有selected conflict。不能用仅调用`validate_registry`的测试代替历史`validate_release`，也不能把release自哈希当可信旧基线证明。

## 1.9.5 原子断言、兼容窗口与批次追溯

`acceptance-cases.json`可在复杂case下列`assertions`。每项ID按`<case_id>.A01`递增，必须写清真实入口和独立预期；未显式拆分的简单case按`then`数组顺序对应`.T01`等稳定ID。case只有在所有必需断言均有真实测试选择器、命令、实际结果和隔离证据时才可标passed。一个批次可支撑多个case，记录必须能定位每条断言的结果；不再要求任务级递归回执、逐任务日志副本或人工双签。

模块演进的逐项oracle如下；测试需要调用各owner真实公开入口，不能只在registry或schema旁路测相似小函数。

| Case | 必须分别断言 |
|---|---|
| MOD-14 / S04 | Registry与归档reader各自覆盖重复ID、错误归档hash、未知/自引用依赖、依赖环、依赖/冲突矛盾；release路径必须有hash与release_id均正确的循环攻击；分别测active ID撞模块/发布墓碑、遗漏模块级墓碑；完整包不可部分返回；合法互斥候选可共存。 |
| MOD-16 / S05 | 精确可信历史包可只读；自洽hash循环、缺依赖、篡改各自拒绝；不回退当前catalog、不激活、不查公司观察/派发。 |
| MOD-17 / S05 | 精确旧`module_id + artifact_sha256`才可走legacy适配；同ID改字节并重算所有hash仍拒绝；自报legacy/未知基线/断链拒绝；旧manifest与观察不重释。 |
| MOD-18 / S06 | 多层依赖完整确定闭包；缺失、rejected、uncertain和环分别失败；选中冲突按无向规则阻断而目录备选允许共存；乱序不变hash/题序；任何拒绝前模型调用数为0。 |
| MOD-19 / S06 | 分类总置信度分数6/7/10分边界贯穿解析、回执、冻结快照和派发；低总分只降级LLM候选，不影响确定性事实；高总分不越过单模块证据门；自计算快照哈希不充当来源认证，新执行必须匹配调用方独立保存的decision_id；真实归档router 2.0 fixture可读，router 2.1仅测合成兼容路径，不宣称有历史fixture。 |
| MOD-20 / S07 | 提示渲染契约是纯模块；导入图不得形成question_sets↔standard_answers双向边；score/fact代表输入逐字稳定；旧standard_prompt调用兼容。 |
| MOD-21 / S07 | 真实compose、归档manifest reader和answer validator共同验证prompt/resource hash；纯结构拆分保持旧renderer版本与哈希，新提示语义才独立升版；使用临时目录且拒绝网络。 |
| MOD-22 / S07 | 本地离线producer E2E贯穿compose→answers→observations→exchange hash，校验密钥、网络、下载路径和临时清理；不宣称StockWiki/UI/live已闭环。 |
| MOD-23 / S08 | `json_io`是唯一通用UTF-8 JSON实现；题库与提示层共享，question_library无上层导入；standard_answers只保留一条静态可见的manifest语义CLI边；干净子进程双顺序导入。 |
| MOD-24 / S08 | 新契约、旧question_sets兼容入口与standard_answers真实fact接口验证同一catalog/profile规则；唯一临时ROOT中的专属facts版本必须被读取，不能回落仓库目录。 |
| MOD-25 / S08 | 隔离离线producer E2E贯穿题库读取到观察/交换hash；拒绝网络、密钥和下载副作用，成功失败路径都只清理本次登记的临时根。 |
| MOD-26 / S09 | 独立指纹契约保留旧格式缺省版本标记时的1.0.0算法输出；2.0.0继续绑定答案格式资源；旧question_sets签名只作委托兼容层。 |
| MOD-27 / S09 | 标准观察读取继续接受已发布版本并拒绝伪造manifest；standard_answers对question_sets只保留manifest语义验证边。 |
| MOD-28 / S09 | 本仓离线producer E2E经过稳定指纹契约完成compose、观察与交换hash校验，并证明无网络/密钥/下载副作用。 |
| MOD-29 / S10 | manifest/selection模块和standard_answers不反向导入question_sets；兼容wrapper与发布renderer hash保持稳定。 |
| MOD-30 / S10 | 发布观察仍可校验，伪造manifest在观察生成前被拒绝；答案构建器直接消费question_manifest契约。 |
| MOD-31 / S10 | 本地离线producer E2E贯穿compose、StockQA适配、观察和交换hash，并清理独占临时根，不宣称网络或StockWiki ACK已验收。 |
| MOD-07 / W15 | SQLite原样往返保存router 2.2分类status/score/threshold/eligibility与搜索模型/时间；派发前从可信存储取expected_decision_id并阻止被重封的其他路由ID；旧router 2.0/2.1不合成缺失字段；损坏或包不匹配失败关闭。 |
| MOD-13 / U04 | 浏览器将ROUTE_02分数明确展示为路由分类置信度而非公司质量；阈值、模型、时间和uncertain候选可见，已核实模块不误降级；旧router缺失置信度显示历史未记录；浏览器模型调用数为0。 |
| EVO-83 / V16 | 用注入UTC时钟测`[valid_from_utc, valid_until_utc)`两端；精确producer/consumer/action独立；缺字段、倒置/重叠、naive时间失败关闭；无到期必须显式声明；过期历史reader不可用时`needs_review`，绝不重释/删除旧观察。 |

兼容窗口是每个精确producer/consumer release对和动作（历史读、派生重建、新写、付费派发、迁移、回退）的独立声明。UTC开始包含、结束不包含；`valid_until_utc=null`只有同时显式`expiry_policy=non_expiring`才表示无到期。无效时间、无匹配行或多行歧义在任何副作用前失败关闭。兼容窗失效限制该动作，不删观察或重写历史；历史解释能力不足时标`needs_review`。

任务进度由`task_plan.md`、批次验证结果与里程碑审查共同追踪。历史receipt与P01校验材料只读保留，不能作为当前完成状态的权威来源；产品运行中用于搜索、派发、结果导入和费用结算的执行回执仍按各自产品契约验证。
