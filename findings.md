# 设计调研与证据

## 2026-09-22：Task C02 指标映射与证据口径证据
- 证据与口径契约已固化：schemas/quick_scan/metric.schema.json 与 docs/implementation/contracts/metrics.md。
- 诊断不进均分（SC-08）：变质测试验证追加满分10分的杜邦/五力/恢复诊断题后，质量、成长、估值三个维度的原有均分绝对不变。
- 关键风险一票否决（SC-09）：IQS_16 或对应现金流替代题得分 <= 3 时，强制阻断质量通过，复合 OR 规则不可绕过。
- 全覆盖与替代映射（SC-10）：通用核心题库保持完整 24 道买方题结构。
- 跨群不可比性约束（SC-11）：银行资本回报（bank.cet1_ratio / bank.roe）与工业投入回报（financial.roic）被严格标记为不可直接排名混比。
- 优势条件与净效果口径（DUR-01, DUR-02, DUR-03）：强制要求优势成立前提、反向证伪证据以及新旧业务交替下的股东净经济效果核算，严禁概念热词盲目加分。
- 测试覆盖：tests/test_metrics_contract.py 6项测试全部通过，全量 108 项通过。

## 2026-09-22：Task C01 身份契约证据与验证
- 身份契约已固化：schemas/quick_scan/identity.schema.json 与 docs/implementation/contracts/identity.md。
- 实体多挂牌与母子分离验证（ID-01, ID-02）：比亚迪 A/H 样例验证了同 Entity 下 2 只证券（CNY 与 HKD），经营问题 1 次问答，估值独立分发；同品牌母子实体经 verified_same_issuer=false 强制保持为 2 个独立 Entity。
- 边界防猜验证（ID-03）：ADR 存托凭证未核实折算比例时强约束为 adr_ratio=null，禁止臆测换算比率，而实体经营事实可安全复用。
- 轻资产与无前置依赖验证（ID-04）：快扫实体在 company_wiki_ref 与 formal_stockwiki_profile 为 null 时结构完全合法，不产生外部目录建档或 worker 爬虫前置依赖。
- 动态大池版本与软限制验证（UNI-04）：股票池扩容至 2,003 家（>2,000）不自动淘汰老公司，删除采取逻辑移除，恢复必须伴随理由并递增版本。
- 测试覆盖：tests/test_identity_contract.py 5项测试全部通过，全量 102 项通过。

## 2026-09-22：Task P00 接口与行为基线核实
- 目标仓库 commit hash：StockQAbyLLM=`3c685dda28f67a00bd653ad257a121d3b8edebb8`，StockWiki=`f5b8526c78ef0bc7df27885da043ce5a2534fffb`，company-wiki=`f39bd5a64224cd0c7aa098f23f64bf3811fa8939`，invest-quick-scan=`85162ec`。
- 依赖可用性：CodeGraph不可用（8080端口Transport closed），确认使用本地只读文件检查替代（BASE-02）。
- StockQA缺陷核查：已直接在 `src/services/answer_generator.py`（58-61行）定位 `answer_score = 5` 强行覆写模型分数的代码；在 `src/providers/llm_client.py` 确认请求体未携带真实搜索参数（BASE-01）。
- 本地离线基线：`pytest -q` 运行 97 项测试全部通过（101 subtests, 0 fail, 0 skip）；`tests/test_question_sets.py:282` 处的 `assertIn(answer.score, (5, 8))` 作为上游缺陷观察保留。
- 交付基线报告 docs/implementation/baselines/baseline-report-2026-09-22.md 及完成回执 docs/implementation/baselines/receipt-P00.json。

## 2026-09-22：全局复核与标准化
- 已落实全局契约：StockWiki单一用户入口/名单/不可变观察与查询，StockQA唯一模型配置/任务/账户额度/费用/outbox，company-wiki只读可选关联；统一data_root下独立拥有者子目录，不共享可写数据库。
- 本地已实现61道事实题及类型/行业/阶段路由、评分3.0的稳定字段/口径/细分类、固定24核心汇总、标准schema和执行回执绑定、公司×时间×模型可比性检查与虚构样板。所有新增调用辅助均为离线，不复制上游客户端。
- 独立前向审查修复了补充题权重漂移、事实身份遗漏、实际信息日期/期间比较问题；后续回归又修复可变输入破坏观察hash的问题。详见docs/implementation/reviews/local-standardization-2026-09-22.md。
- 用户新增并行/五小时额度要求已纳入model-policy配置模板、严格schema和9项离线测试；StockQA生产卡明确三层并发、账户共享额度、按顺位切换、单题防重、结果不明对账、单探针与跨重启预算。模板顺序由用户填写，未自行选择真实模型。
- 实施包升级1.4.0：73任务、162个待执行验收场景、28约束、G0—G6；新增W13/Q11/W14及MAINT/STORE/MATRIX/PAR场景，设置/简洁UI/消费者均接入最终依赖。
- 最终97项离线测试通过，无skip；48评分模块/222题、61事实题、配置/skill/schema/样板/链接与计划依赖检查通过。未修改外部仓库、运行实际LLM/2,000家公司扫描或实现生产UI。
- 上游实际离线验证仍暴露8→5传递缺口，搜索执行也未就绪；本地测试将这些记录为已知上游问题，不等于生产修复。Q01/Q02等仍是上线前置。
- 旧skill仍声明scored_only/不提供纯信息集，与用户最新要求冲突，需升级。CodeGraph context仍Transport closed，采用已知文件只读检查。现有输出只约束score/description，metrics为自由对象，缺强制的模型/运行时间契约；应补版本化交换层而非把模型自述当执行回执。

## 2026-09-22：企业结果 UI
- 用户明确要求UI方便查看各企业快扫结果。已有O05仅概述公司卡片/筛选，X06主要是启动和状态；需补具体列表、评分依据、事实关系和浏览器验收。
- 继续由StockWiki提供结果界面，仅读取权威库和既有查询语义；浏览不触发LLM。UI不得将未知当低分、用恢复标记改写低分或将多挂牌重复列公司。
- 新增results-ui.md设计，拟拆U01列表、U02评分详情、U03事实/历史及跨页接线；保留评分先行、事实G4后启用的顺序，最终G6必须覆盖实际结果界面。

- UI已成为必交范围：U01/U02经O05/G5放行，U03依赖G4/X06并由X09/G6验收；C06/W09提前定义分页快照、详情依据和历史口径接口。
- 计划1.2.0现有70任务、136场景；41项规划工具测试通过，G6覆盖全部69个前置任务。14份Markdown、40个本地链接、14个阅读引用无缺失；U01—U03任务包提取成功。本轮未执行真实UI测试，也未改外部项目。

## 2026-09-22：跨项目闭环与一键开启
- 用户进一步要求所有跨项目功能一并规划，使完整计划实施后可以一键开启。解释为首次完成配置后，统一入口能预检、启动/复用运行组件、扫描或续扫并展示状态；本轮继续完善计划，不伪造可用启动器。
- 现有53卡覆盖业务功能，但缺少配套版本、首次配置、安装/技能加载核对、统一启动生命周期和最终跨项目发布验收；需要单列集成阶段，不能把页面能打开当系统已就绪。
- StockWiki README已有doctor与本地UI入口，并说明runtime scheduler的现有正式研究流程；快扫入口应复用UI/runtime基础，但不能调用通用scheduler-cycle、来源采集或正式研究队列冒充轻量快扫。
- 已核实StockWiki pyproject提供stockwiki.cli:main且要求Python>=3.11；StockQA要求>=3.10。配套部署应核实各自依赖/解释器，避免把两个仓库内部模块混进同一sys.path。配置与持久化任务仍由各拥有者写入。
- 本轮CodeGraph仍Transport closed；StockWiki初次文件检索中的src目录不存在，已得到现有tests/test_ui_http.py、test_runtime.py和scripts/check_all.sh等入口线索。后续不能把src路径当既定布局。
- 已补C07早期启动契约、X01—X12跨项目接线/配置/安装/联调/升级交付与G6最终审查；计划1.1.0共67任务、124场景、26约束。G6依赖闭包要求覆盖所有任务，并同时具备G4事实消费者与G5评分扩容。
- 核心新增约束：StockWiki单一用户入口，StockQA独占模型配置/账本；doctor本地零付费，真实探针显式计费；重复点击/重启不重置额度；安装核对实际技能与资源hash；关闭页面、停止派发、崩溃恢复分开。
- 首轮扩展测试暴露E2E场景ID与旧正则不兼容，属于规划校验器命名契约扩展问题；已修正前缀规则并加入非法ID边界，未降低任何业务验收预期。
- 最终验证：计划1.1.0的67任务/124场景通过校验；41项规划工具测试通过。G6包含全部66个前置任务，无遗漏分支；13份Markdown、32个本地链接、13个阅读引用无缺失，X05/G6任务包与M6按仓筛选的实际CLI检查通过。
- 任务分工：invest-quick-scan 22、StockQA 17、StockWiki 26、主题技能1、行业技能1；company-wiki保持可选只读。各仓实际生产改动、安装器和在线整体验收仍按任务实施，不把124个规格场景当已执行测试。

## 2026-09-22：降低后续模型实施偏差
- 用户要求把任务拆细，增加足够测试和审查，使后续较弱模型能够按明确边界实施。本轮交付任务/验收包及必要的规划校验工具，不把尚未实现的生产测试声称为已通过。
- 原M0—M5是里程碑级路线，尚缺少单任务允许修改范围、具体输入与预期结果、依赖放行、失败回退和逐项完成证据。
- 本地AGENTS.md文件不存在，当前项目指令已由用户消息提供。planning-with-files安装入口本轮可读取，不沿用上轮失效假设。
- CodeGraph本轮status仍返回Transport closed，因此根据已知文件核查现有接口与测试，未重建索引。现有严格normalize协议使用独立accepted_ids；新增股票池screening协议必须显式分版，不能把自动检查伪装成人工accepted。
- 当前评分锚点/汇总边界包括：质量与成长/估值分开；杜邦、五力和恢复诊断不进均分；关键风险含类型替代；恢复观察保留低分。后续测试须直接验证这些边界，而非只检查JSON可解析。
- 实施包拟采用单一任务清单和测试场景库，提供只读任务提取/依赖校验命令；不会增加业务执行器、LLM客户端或自动跨仓写入能力。
- 已核实旧兼容测试assertIn(answer.score, (5, 8))仅记录旧上游缺陷；P00必须记录它，Q01修复后S02将其收紧为严格8。已有27测试通过不足以证明真实搜索/分数缺陷已修。
- 已形成53张单一拥有者任务卡、99个验收场景、21条固定约束与G0—G5阶段审查。场景为测试规格，未伪称生产已执行；新增只读计划工具的首轮27项测试通过。
- 自查发现原路线把备份工具放到M5、但M3试点已要求恢复验收。已将其提前为W12，成为L03/G3前置，避免隐含依赖导致较弱模型临时跨仓补实现。
- 最终验证：53任务/99场景的结构、依赖和覆盖校验通过；新增计划工具30项测试全部通过（包含非法类型、缺预期、未知依赖、循环、缺关口、无反例、用mock冒充live、伪造计划完成等）。工具只读，不执行任务或验证生产结论。
- 文档/任务阅读路径验证：11份Markdown、23个本地链接、11个阅读引用无缺失；P00任务包实际CLI提取成功。现有题库结构仍48模块222题，本轮未重复宣称既有27行为测试为生产联网验收。
- 交付文件：docs/implementation/内入口、固定约束、测试策略、审查交接、tasks.json、acceptance-cases.json；scripts/implementation_plan.py及tests/test_implementation_plan.py；原总体设计/路线和三份planning记录已关联更新。

## 2026-09-21：股票池运维与技能联动输入
- 用户要求：明确2,000家公司名单的产生和偶尔增补工具；按独立公司全覆盖，近期有效数据跳过，分次接续扫描；按用户指定LLM优先级依次故障切换；明确StockWiki/company-wiki分工；主题链与行业研究优先利用快扫数据库。
- 本轮继续头脑风暴并写计划，不立即建立真实名单、运行模型、修改外部项目或安装新skill。
- CodeGraph服务返回Transport closed，改用本地只读检索；两个研究skill的.agents/.codex入口失效，已从Projects/local-skills找到并读取源项目SKILL.md。
- 初步建议：名单维护做确定性小工具，并由现有skill调用；没有必要为增删与续扫再创建一套独立投资分析skill。
- StockQA本地文本检索发现src/utils/llm_integration.py已有_try_fallback，需要检查实际语义后扩展，不能默认“完全没有fallback”而重造。src/utils/http_client.py已有429/5xx重试。
- StockWiki README仍确认其持有研究状态和runtime jobs，company-wiki持有原件；已有任务队列不等于可直接接管StockQA问答级重试，需明确分层职责。
- 官方证券名单来源已核实：上交所股票列表、深交所公司列表、HKEX Securities Lists、Nasdaq Trader Symbol Directory。美股目录包含ETF/test issue等类型，名单必须区分证券类别，不能把所有代码都当普通上市公司。
  - https://www.sse.com.cn/assortment/stock/
  - https://www.szse.cn/market/stock/company/
  - https://www.hkex.com.hk/Services/Trading/Securities/Securities-Lists?sc_lang=en
  - https://www.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs
- 本轮只查看名单来源网页，不下载公司文档、不生成真实成分名单。主档/成分导入属于对象管理，不改变公司画像依赖LLM问答的边界。
- 已读取StockQA src/utils/llm_integration.py：ProviderCascade接收有序providers，维护当前索引、失败/成功计数与可选health_check；RequestCache和TokenUsage也已有底座。状态目前为实例内存字段；不能据此宣称跨进程续扫或持久化故障冷却已完成。
- ProviderCascade的备用成功后恢复逻辑需核查生产接线与健康检查策略；未来必须由冷却/探测判定主模型恢复，不能仅凭备用模型成功就频繁切回主模型。
- RequestCost默认价格为示例估算；未来预算应使用实际提供商配置和价格日期，不能沿用默认数字当准确账单。
- analyze-theme-value-chain源入口明确要求先从经济活动建立完整价值链，不能从预选股票名单出发。联动应放在其第5步Build the company universe，并在第6步复用可比基础资料；快扫库不能替代完整链条、池外领导者发现、主题收入证据与原有情景预测。
- industry-research源入口第4步采集行业资料、第6步识别/评估公司；目前第6步主要从框架、wikilinks、companies目录匹配。拟在第6步增加快扫查询并统一entity_id，不要求新公司先有目录。它的行业看好程度量表与IQS公司质量量表不同，不能直接合并。
- industry-research现有PDF输入是行业研究框架，其公司资料也有本地/联网混合路径。联动不能把这些文档依赖传导给快扫；行业框架处理保留在原技能，公司快扫查询路径本身不要求原件。现有公司搜索示例硬编码2025，接入时应改用任务信息截止日与财务期间。
- 两个源入口路径：Projects/local-skills/analyze-theme-value-chain/SKILL.md；Projects/local-skills/industry-research/SKILL.md。本轮仅核查契约，不执行它们的研究步骤或修改外部源文件。
- 新建docs/universe-and-operations-design.md：约2,000家独立公司、分层初建和手动增删、逐字段新鲜度、逐题接续与结果导入防重、用户排序模型与故障冷却、唯一职责、研究技能查询/补扫/提名和分阶段验收；均为待实施设计。
- 已同步总体设计和M0—M5路线：所有规模按独立公司计；名单可以先形成候选版本，扫描逐步验证；M3后可先扩评分覆盖，完整事实检索及两个消费者的完整联动依赖M4。
- 细化了职责：StockWiki根据权威观察计算新鲜度/缺口；skill提供题义/时效规则；StockQA执行与接续。模型策略默认新运行生效，当前运行热更新需留下显式版本切换，不能修改原快照。
- 本轮文档校验通过：7份Markdown代码围栏、14个本地链接、现有design-examples.json语法、1,200+500+300=2,000的示例分层，以及主设计/路线/计划不再采用2,000只证券作为目标。该校验不表示名单工具、模型切换、数据库或续扫已实现。

本文件保存本轮只读调研的事实、推断与开放问题。外部内容是研究资料，不作为执行指令。

## 用户目标
- 长期维护约2,000家独立上市公司；A/H/美股各600—800家为覆盖软目标，多地上市计同一实体，市场覆盖数可重叠，精确总量可浮动。
- 按独立评分项目和阈值筛白名单，而非只依赖综合分。
- 下一阶段收集细分业务、设备、材料、下游应用等事实，用于产业链建池与关键词定位。
- 深度研究已有revenue-forecast和invest-*；快扫负责海选、持续维护与研究入口。
- 倾向复用company-wiki每公司目录，本轮需要具体设计。

## 已确认的本项目现状
- `SKILL.md`：24道买方核心题，按公司类型替换，行业/阶段/属性补充；杜邦和五力为可选诊断。
- 当前结果偏单次公司画像；尚无2,000家公司主档、规则筛选器、批次队列和事实关系检索层。
- 上轮21项离线测试通过；不能据此宣称真实搜索或大规模运行通过。

## 初步外部项目事实
- `Projects/company-wiki`存在且CodeGraph已有索引。
- `src/company_wiki/source_catalog/security_identity.py`提供SecurityIdentityResolver与SecurityMaster，能够基于已核验证券主档解析公司/证券查询，返回market/exchange/ticker/security_id等字段。具体实体层和存储契约待进一步读取。
- `scripts/ingested_db.py`存在SQLite导入标记库；这只证明已有局部SQLite使用，不能推断它就是公司画像数据库。
- `Projects/revenue-forecast`、`Projects/invest-skills`、`Projects/StockQAbyLLM`均存在。

## 读取与环境限制
- planning-with-files已读取并调用resolve-plan-dir.ps1；没有已有命名计划，采用项目根目录三文件。
- 本项目不是Git仓库，git差异不可用。
- 两套已安装invest/revenue skill入口读取失败，后续改查源项目，不影响本轮只读规划。

## company-wiki已核实的重要边界
- `README.md`、`AGENTS.md`明确：company-wiki当前只负责来源采集、immutable raw、source manifest、EvidenceSpan、解析质量和只读export；StockWiki拥有研究语义、人工证据裁决、投资模型与研究状态。
- 历史 `companies/{公司名}/wiki/` 仅只读兼容或来源投影；不得新增研究型writer。因此不能直接将LLM评分和白名单状态塞入company-wiki现有公司wiki目录。
- 与StockWiki要求只读版本化export，不共享可变数据库、不跨仓写文件。
- README说明2026-09-19 worker处于paused；本轮仅设计，不启动或恢复worker，不触发下载。
- 公司目录同时存在直接原件与旧raw层的兼容约定，未来应依解析器返回的路径/ID，不能假设新建目录布局就能被所有旧扫描器正确理解。
- 方案方向：复用来源主档与实体映射，但评分、产业链语义和规则结果应落在研究侧。进一步核查StockWiki已有契约后选定写入方式，避免新建第三套权威状态。

## StockWiki与深研契约
- `StockWiki/README.md`与`AGENTS.md`再次确认：原始资料默认可引用company-wiki外部公司目录；StockWiki拥有研究语义、证据资格/人工复核、knowledge state与投资工件。跨仓仅消费版本化来源契约，禁止共享可变数据库或互写目录。
- CodeGraph显示StockWiki `Company`目前以ticker为主要键，safe_id由ticker生成，包含exchange/industry/aliases/doc_root/tags。现有 `data/companies/{safe_id}` 与 `wiki/companies/{safe_id}` 有正式状态和派生视图的一致性校验。公司实体与多证券建模必须作为兼容扩展，不宜直接重命名目录。
- 已成功读取源项目 `invest-skills/invest-core/SKILL.md`：invest-core管理版本化工件、来源/claim/参数、hash与上游依赖；revenue-forecast独占收入驱动与情景计算；证据置信度不得转换为企业质量。
- 已成功读取源项目 `revenue-forecast/SKILL.md`：正式预测要求来源capture、输入口径、分部路径、验证与发布receipt；当前canonical schema标为3.7。快扫不能把LLM分数或粗估增长直接冒充正式预测输入。
- 设计方向：quick-scan工件标为screening/candidate层，进入深研时提交研究线索、证据引用和缺口；仍由深研自己的来源资格和输入验证决定能否采用。
- company-wiki `SecurityMasterStore`已采用分市场版本化JSON快照并原子替换；这可用于证券主档复用，但不等于已具备跨市场法律实体合并关系。
- StockWiki `WorkspacePaths`已有config/data/wiki/framework/runs/state等路径；`classification_state.py`在 `data/companies/{safe_id}/classification.yaml`保存类型、行业、生命周期、理由、confidence/citations/model等快照。缺失时可生成低置信度keyword_heuristic fallback；快扫不能把这个fallback当已核实路由。
- 实现应新增轻量screening命名空间与兼容映射，不覆盖现有正式classification或accepted evidence。
- `SecurityRecord`实际字段为canonical_name/market/exchange/ticker/security_id/aliases/active/source provenance/identifiers；没有显式跨市场entity_id。跨上市实体合并关系需要新增经核实映射，不能靠同名或相同ticker拼接。

## StockQAbyLLM重新核查
- `LLMClient.send_request`仍只发送model/messages/temperature/max_tokens；显式搜索开关和原始搜索执行metadata未见实现。
- `AnswerGenerator.generate_answer`仍在成功分支固定answer_score=5，未传递SearchResult.score。应在上游修复，不能规模化后靠后处理猜分。
- 已有AsyncLLMProvider与search_async/现有重试；只能说明存在异步底座，不证明已有适合2,000家公司、可恢复、按预算限流的批任务系统。
- 现有接口要求单个score+description，下一阶段纯事实/多题pack必须在StockQAbyLLM扩展结构化response_kind，不能用虚构评分承载非评分事实。

## 进一步契约核查与设计修正
- company-wiki的source-manifest-v1要求真实原始文件、内容hash、路径和采集信息；EvidenceSpan需要稳定定位与解析输出。LLM答案、引用URL不能冒充这些来源工件，模型推断也不是原始来源类型。
- invest-core artifact-contract中的部分说明仍写revenue schema 3.4，而revenue-forecast入口标为3.7。后续交接应核查运行时schema和validator，不能硬编码文档中某个版本并宣称已经兼容。
- 已查阅SQLite官方适用场景与FTS5文档：本机嵌入式筛选适合SQLite；单库同时只有一个writer，不适合多台机器直接并发写共享文件。复杂多writer需求出现后再考虑服务型数据库。
  - https://www.sqlite.org/whentouse.html
  - https://www.sqlite.org/fts5.html

## 用户追加的轻资产硬约束（优先于此前方案推断）
- 画像信息只由LLM问答（允许联网搜索）提供；不保存网页正文、财报、研报、公告副本等公司文档。
- 快扫只留结构化结果、简短判断依据、来源URL/日期、模型/提示词/问题版本、调用与成本状态等小型记录；不把网页capture或PDF下载设为评分前提。
- company-wiki身份主档/现有目录映射仅可选复用；新增证券不要求先创建原件目录或启动来源worker。
- StockWiki仅接收轻量screening数据，正式研究的accepted evidence、原件与模型链条仍在用户启动深研时按原有流程处理。
- 修正此前研究方向：不为每个快扫引用建立source manifest/EvidenceSpan，不把逐题人工accepted_ids要求照搬到2,000家公司筛选；另设明确的screening校验等级，且不等于正式研究验收。
- 联网调用metadata证明搜索执行，与链接是否真正支持结论是两回事。独立复问和人工抽查可改善可靠性，但不声称达到原文归档后的审计能力。
- SQLite FTS5官方说明trigram全文查询无法匹配少于3个Unicode字符的词；“AI”“液冷”等需走受控术语/别名表的精确匹配，不能只建立全文索引就认为支持产业链中文检索。
- 现有scoring.md要求运行者逐题填写accepted_ids；这是现行单公司验证协议。股票池版本应另外设计screening校验等级，不能悄悄把LLM自报结果填入accepted_ids或宣称代码已支持自动验收。

## 本轮建议的权威存储选择
- 采用一个轻量SQLite库作为结构化股票池的权威存储；JSON/CSV/Markdown均是导出或交换包，不另建同等权威的逐公司文件状态树。
- 推荐由StockWiki在独立quick_scan命名空间管理这个库，与正式研究状态隔离；StockQA独立产出问答交换包，StockWiki缺席不影响单公司问答执行。
- 此选择取代此前考虑过的“逐公司多文件快照+重建索引”方案，以减少文件管理、双份状态和复杂迁移。SQLite自身必须备份，不能当可随意删除的缓存。
- 批次执行、搜索、限流、重试和调用费用放在StockQA；StockWiki负责轻量结果导入、规则查询、页面展示和导出；skill只维护问题、路由、评分协议及离线编排。

## 设计已落盘
- docs/stock-pool-design.md：轻资产约束、身份、评分、三值规则、主题关系、SQLite权威库、跨项目边界和刷新预算。
- docs/implementation-roadmap.md：M0—M5职责/依赖/产物/验收，先评分闭环再事实问题与检索。
- docs/design-examples.json：全部虚构，包含四条核心评分、五种规则结果、六条业务关系、两地挂牌复用和纯线索深研交接。
- 词表/业务关系只是未来数据契约示例，不是已经生成纯信息问卷；SQLite/批次/主题查询也尚未实现。

## 规划验证结果
- JSON语法、4个现有核心问题ID引用、两证券共用实体、5种规则情形均通过离线一致性检查。
- 主题示例1个正例、2个反例与设计一致：生产并量产的相关设备公司入围；使用者、研发阶段不入围。
- 两份设计Markdown的代码围栏和4个本地链接有效；来源URL仅留链接，未抓取或归档文档。
- 深研示例formal_evidence_accepted=false，source_manifest_ids/evidence_span_ids为空；没有伪造正式来源工件。
- 这些检查验证文档示例的内部一致性，不代表生产规则引擎、真实模型、事实准确性或2,000家公司运行验收。

## 周期低谷与反转补充调研
- 用户要求：不能因暂时差指标完全漏掉仍有优秀特征、可能周期重启或经营反转的公司，至少保留关注标记和理由。
- CodeGraph已确认现有routing区分生命周期与cycle_sensitive/cycle_position；normalize的关键风险gate会令综合质量分为空。新增观察输出必须与质量分独立，同时保留原风险gate。
- 参考Damodaran关于正常化盈利和困境公司的原始方法说明：恢复能力不能直接用低谷当期利润评价，但正常化过程有时间成本，生存风险不能略去。本次仅参考方法，不建立估值模型或采集公司资料。
  - https://pages.stern.nyu.edu/adamodar/New_Home_Page/valquestions/normearn.htm
  - https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/distresspaper.htm
- 已读原文：正常化盈利需考虑业务规模变化和恢复所需时间；企业资产有价值不代表普通股在融资/重整后一定受益。只留方法摘要和URL，不保存原文。
- 既有CYCLICAL_01/02已覆盖中周期回报、低谷投资和存续，TURNAROUND_01/02覆盖领先改善和修复资金，DISTRESSED_02覆盖债权/摊薄后股权价值。
- 明确缺口：没有独立的恢复观察输出；TURNAROUND_04的1分锚点把“周期反弹”本身作负面，需要改为不可持续低基数/会计反弹或结构性需求消失。
- 实施方案：新增4题recovery诊断（可逆性、优势保全、恢复路径/催化、普通股受益），独立1—10分，不进入质量均分；按路由触发，并输出带风险和缺口的观察状态。
- 不改既有关键风险gate或未审核分数规则。高质量白名单未通过仍可进入恢复观察，但观察标记不是买入或恢复已确定。
- 现已实现：题库2.1.0，48个模块222道评分题，其中通用24题不变；新增recovery四题是诊断，不进入维度/综合分。
- normalize新增recovery_watch，包含优势、弱项、缺口、资金/结构性/股权风险及状态；类型替代题按manifest映射，不硬编码通用资金或现金题。
- 27项单元/离线兼容测试已通过，包括低质量评分仍保留恢复潜力、催化改善不抬高原分、关键风险不被覆盖、结构性衰退、未审核/低置信度不被采用及银行替代题。
- 上游离线兼容检查仍发现AnswerGenerator把8分写成5分；本轮不修改StockQA，不宣称真实联网已经可用。

## 不变优势与产业变化：讨论输入
- 用户提出：品牌、渠道、规模等优势有较强持续性；AI等产业变化可能帮助公司上台阶，也可能颠覆原有行业。要求独立判断并讨论如何反映到skill。
- 既有通用题已有部分覆盖：IQS_01客户价值、04利润归属、05优势复制成本、06优势趋势、07/09执行组织、18永久损害、19可触达需求、20增长转化、21增量回报、22价格预期。
- 本轮仅形成方法与设计建议，不未经讨论把“不变/变化”变成新的机械总分或改变已校验的生产问卷。
- 需要补的联系：原优势成立的前提，产业变化是否破坏前提，旧能力能否迁移到新利润池；正面机会与负面替代应分别保留，不能净额抵消。
- Teece原始论文将企业应对变化的能力联系到识别机会、调动资源和重新配置资产/组织；不能把现有业务执行良好直接等同于新技术转型能力。
  - https://sms.onlinelibrary.wiley.com/doi/10.1002/smj.640
  - https://onlinelibrary.wiley.com/doi/10.1111/j.1467-6486.2012.01080.x
- 已核实IQS_19/20/21/22分别覆盖可触达需求、从采用到盈利的证据、增量资本回报和价格隐含预期。设计应复用这些题，而非重复增加“AI前景”总分。
- Harvard五力官方说明明确将替代界定为不同方式满足同一底层需求，并讨论技术、监管、渠道等变化对竞争结构和利润分配的影响；只保存方法摘要和URL。
  - https://www.isc.hbs.edu/strategy/business-strategy/Pages/the-five-forces.aspx
- 已写docs/durability-and-change-design.md：优势的有效条件、需求与手段区别、利润归属、能力迁移、新旧业务净效果、并存风险与机会，以及与恢复观察的区别。
- 建议先深化24题；最多三道按需诊断草案为能力迁移、组织调整、新旧业务净股东利益，含1/5/10锚点但尚未加入catalog。
- 3份相关设计文档链接及代码围栏校验通过；本轮未改题库、评分代码、现有模型结果或外部项目。
