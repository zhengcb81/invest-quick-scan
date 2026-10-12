# PRIMARY-CATL-03：宁德时代 / 300750官方来源与经济口径核验

**可由一个独立harness认领并立即做限定研究**，不依赖另两包或主线B01完成。唯一可写根 `C:/Users/郑曾波/Projects/iqs-primary-catl-lab`，编制时尚不存在；不自动派发。与其它包唯一的共同项是只读冻结输入。先读本卡及同目录[共同规则](common-rules.md)、[接口/测试契约](integration-contract.md)、[PRIMARY-CATL-03.targets.json](PRIMARY-CATL-03.targets.json)、[43文件锁](inputs.lock.json)、[manifest](manifest.json)及[PRIMARY-CATL-03.handoff.template.json](PRIMARY-CATL-03.handoff.template.json)。这些文件是完整施工上下文；不要求阅读主线全部历史对话。

## 已有成果与本包目的

原FIN `codex/fin-ref-01@1e88d86754f6faa6959e1cc893ddbc8f6e5b374f` 已正式合并三公司90题；CLI/package1.5.0、财务参考pack1.2.0、ledger1.0.0，114项软件回归通过。旧1.0/1.1和原锁保持。90题72completed研究尝试/18具名gap，所有评分null和来源复核needs_revision。1009条包含历史的facts、104contradicted前序、8账项及62个具名母公司记录已保留；原公式/历史纠错不返工。

你的工作是核自己公司完整30题的现有事实、官方出处、会计/经济意义与反证，把可核/反证/仍欠信息有结构地交回，为后面的真实LLM回答评估建立更可信参考。不能拿结构通过或官网地址自签金融gold，不修改其它60题，不选择新公司，不能将候选参考变成评级/白名单或生产事实权威。财务参考1.2与主线Observation1.2是不同协议，勿混用。

固定主体 `宁德时代新能源科技股份有限公司`、挂牌 `XSHE:300750`、信息截止 `2026-10-11`。多市场/股份类别和金融口径边界从targets和冻结题集读，不能只靠简称匹配。新增ID只用 `SRC-RPC-* / FACT-RPC-* / CALC-RPC-* / PROOF-RPC-*`，不能改旧ID含义或引用别包的新记录。

## 本公司研究重点（优先主题，不改题）

1. 先核2025官方可读财务表/业绩说明中货币资金与现金等价物、受限/保证金/质押/期限限制，冻结候选333512927与299929741等单位为CNY千元，不能互换或将全部差额都称受限。这些是现有待验证数字，不是本卡认证的答案。
2. 完整selected借款/债券/租赁账面聚合119601197等、current/non-current边界与supplier finance分开。经验证可支持“所选账面借款义务”，不自动宣称全部有息债/全部经济负债。
3. OCF133219982、购建资本开支42344558及simple FCF90875424的官方佐证、期间/币种/角色。simple FCF不等于maintenance/distributable FCF；未认证官方原件的数字保持provisional。
4. 合并归母权益/集团资本分母、GAAP OP其它/投资收益、有效税率及NOPAT/ROIC正常化。旧错误平均资本分母已撤回，不能再复活或用表面利润/产能替代经济资本回报。
5. 减值8660164及存货/固定资产/其它明细：拆科目、期间、具体风险。不能将总减值都称产线过时；价格竞争/库存/供需低谷与技术结构性淘汰分开。
6. 电池/储能规模、技术路径、良率/认证、渠道/客户、原料供应、出海及第二曲线；官方新闻只支持明确声明，不变成外部客户确认或项目IRR。认证不证明现金回报，政策变动不证明不依赖补贴。全部30题有事实需求及反证，当前强项与周期恢复条件一起保留。

先按这些主题找官方可读材料，随后对下面30题逐一处理；目标问题文本/anchors/rubric来自43文件中的原20冻结输入和自己的manifest，不凭该重点列表新增或删题。资料可批量读，多题复用来源，但每一个confirmed_primary状态都必须覆盖该题所有当前非contradicted事实的支持范围与残余缺口，不以单条新闻代表全题。官方原件仍无法轻量读取就留gap，不强制下载PDF或造比例。

## 固定30题位

| question_id | reference_id | 当前研究状态（非来源认证） | 现有fact数（含历史） |
| --- | --- | --- | --- |
| IQS_01 | FR-CATL-IQS_01 | research_completed | 5 |
| IQS_02 | FR-CATL-IQS_02 | research_completed | 6 |
| IQS_04 | FR-CATL-IQS_04 | research_completed | 7 |
| IQS_05 | FR-CATL-IQS_05 | research_completed | 7 |
| IQS_06 | FR-CATL-IQS_06 | research_completed | 5 |
| IQS_07 | FR-CATL-IQS_07 | research_completed | 7 |
| IQS_08 | FR-CATL-IQS_08 | research_completed | 7 |
| IQS_09 | FR-CATL-IQS_09 | research_completed | 7 |
| IQS_10 | FR-CATL-IQS_10 | research_completed | 24 |
| IQS_12 | FR-CATL-IQS_12 | research_completed | 11 |
| IQS_13 | FR-CATL-IQS_13 | research_completed | 7 |
| IQS_14 | FR-CATL-IQS_14 | research_completed | 6 |
| IQS_15 | FR-CATL-IQS_15 | research_completed | 7 |
| IQS_16 | FR-CATL-IQS_16 | research_completed | 7 |
| IQS_17 | FR-CATL-IQS_17 | research_completed | 6 |
| IQS_18 | FR-CATL-IQS_18 | research_completed | 8 |
| IQS_19 | FR-CATL-IQS_19 | research_completed | 6 |
| IQS_20 | FR-CATL-IQS_20 | research_completed | 7 |
| IQS_21 | FR-CATL-IQS_21 | research_completed | 6 |
| IQS_22 | FR-CATL-IQS_22 | research_completed | 5 |
| IQS_23 | FR-CATL-IQS_23 | research_completed | 8 |
| IQS_24 | FR-CATL-IQS_24 | research_completed | 6 |
| OPERATING_01 | FR-CATL-OPERATING_01 | research_completed | 8 |
| OPERATING_02 | FR-CATL-OPERATING_02 | research_completed | 6 |
| AUTO_01 | FR-CATL-AUTO_01 | research_completed | 9 |
| AUTO_02 | FR-CATL-AUTO_02 | research_completed | 10 |
| ENERGY_TRANSITION_01 | FR-CATL-ENERGY_TRANSITION_01 | research_completed | 9 |
| ENERGY_TRANSITION_02 | FR-CATL-ENERGY_TRANSITION_02 | research_completed | 8 |
| SCALING_01 | FR-CATL-SCALING_01 | research_completed | 5 |
| SCALING_02 | FR-CATL-SCALING_02 | research_completed | 6 |

对应targets有每行baseline SHA、题文/manifest/metric/rubric/期间绑定、外60行摘要、原全部Source与8ledger摘要。当前已存在contradicted事实不算新发现，它们必须保留供追溯；原官方文章和受限网页定位可沿用导航，但每个重要claim要自己实际核读。不得用网页抓取失败推断全公司缺资料。

## 实施步骤

1. **开工准备**：在新根核唯一writer/路径和Git状态，初始化自己的Git/PWF，冻结43依赖为fixtures/fin，保留原bytes。不得将原FIN源码复制后当自己的新引擎修改；包中薄封装只调用原FIN公开CLI。fixtures/targets.json复制本卡targets原件，fixtures/dependency-lock.json保留原锁并明确本地路径映射；不要改IQS源锁或19旧访问摘要。
2. **先定义证据需求和RED**：content/research-plan.md列30题、当前可用事实、所需最小官方材料/口径/反证。编写允许自身30/禁止外60、假官方、截止污染、proof跨题引用、币种/单位/主体误配等少量会影响结论的失败案例；合成显式synthetic。不要为每题造一个helper或新验收门。
3. **实际官方研究**：按主题先查公开IR/监管/交易所可读内容，核发行人/股份类别/公布日/期间/单位/主体；存短定位和结构化事实，不保存附件/HTML全文。公司官网域名先由发行人法定名称/交易所公开主体页交叉核证；trusted host registry只导航/机械反钓鱼，不是官方内容认证。`evil.example?url=sec.gov`、`sec.gov.evil.example`、不同发行人CIK/证券代码不能借官网字符串通过。记录入口/正文/转载/未读/PDF-only差别，actual attempts及适用题明确。
4. **更新现有参考候选**：完整90pack只更新自己30；追加专属Source/fact和qualification proof，错误原fact有前序SHA/contradicted+新的fact，正确旧转载记录也不改Source。受影响本公司账项只用原公式/roles，未注册经济方法写calc-notes。旧母公司map和另一公司账不动，no_score与review needs_revision保留。用原hash/summary函数重算pack与ledger绑定，列精确changes JSON。
5. **一个稳定包集中验证**：自己的thin CLI支持validate/export；先实际调用冻结FIN validate/export核90题和ledger。集中unit/integration/真实本包CLI E2E、一次来源审查；修复只回归相关项。保留真实初次失败/最终日志/时间/PID/退出码，不能把结构/GREEN等同网页原件被认证或真实LLM准确率。
6. **交接与清理**：自己的test temp、端口和进程结束后准确清理，保留必要小反例/原日志；产品commit→交接commit，交完整原件清单、43锁、30coverage、source proofs/changes/calc/review/case-map/isolation和PWF。只写 `C:/Users/郑曾波/Projects/iqs-primary-catl-lab/docs/handoff/PRIMARY-CATL-03`；总控接收后独立合并/核证，不能写原FIN或代关金融门。

## 交付清单与命令

可从[PRIMARY-CATL-03.qualification.template.json](PRIMARY-CATL-03.qualification.template.json)与[PRIMARY-CATL-03.changes.template.json](PRIMARY-CATL-03.changes.template.json)起步；两个模板只表示未开始、全unconfirmed/无delta，必须写自己的实际研究后才可交付。它们不会使30题“已核”。

主产物：`content/reference-pack.json`、`content/calculation-ledger.json`、`content/qualification-index.json`、`content/changes.json`；细字段严格沿integration-contract。另需 `content/research-plan.md`，本包CLI薄封装、测试、依赖快照/原锁+路径映射、完整docs/handoff/PRIMARY-CATL-03/材料。Source/fact/proof不能dangling、重名、跨公司，给每个原非contradicted事实明确支持/反证/gap处置。

```powershell
# 在自己的目录执行；设置只读冻结FIN模块路径，不改系统PATH/全局配置。
$env:PYTHONPATH = 'C:/Users/郑曾波/Projects/iqs-primary-catl-lab/fixtures/fin/src'
python -B -X utf8 -m iqs_financial_reference_lab --version
python -B -X utf8 -m iqs_financial_reference_lab validate --input content/reference-pack.json --inputs-lock fixtures/fin/fixtures/inputs.lock.json --ledger content/calculation-ledger.json
python -B -X utf8 -m primary_reference_lab validate --candidate content/reference-pack.json --ledger content/calculation-ledger.json --qualification content/qualification-index.json --targets fixtures/targets.json --inputs-lock fixtures/dependency-lock.json
# tests与export均在本包自己的随机临时根运行；export必须指向不存在的新目录。
```

自己的CLI模块需要在src中按pyproject安装到本包隔离环境或将本包src与冻结FIN/src同时加入该子进程PYTHONPATH，不能安装进其它Lab/shared环境；上述先原FIN命令与本包命令分别运行时按此规则切换，不能误声称尚未实现的wrapper现在可用。所有CLI测试用剥key/断网子环境，不读工作机完整环境给产品日志。

最终交回：`C:/Users/郑曾波/Projects/iqs-primary-catl-lab/docs/handoff/PRIMARY-CATL-03/handoff.json`。泛型handoff1.0、实际新私有qualification candidate1.0、actual FIN1.5.0/pack1.2/ledger1.0版本分开；interfaces写方向/raw hash，snapshot结果指产品commit，README另报最终metadata HEAD。无法完成官方核读可partial，但要说明具体缺口、已尝试哪些官方入口及最小下一材料，不把全部难题改not_applicable。所有source reviews与scores资格不被自己升级。

## 验收边界

允许限定研究现在启动，强条件只是输入43字节齐全/新根唯一writer，不等B01或别包。测试组合完整见共同契约；本公司30条coverage无省略、外60/原Sources/外账不变、初始input locks未改、关键来源实际核读与失败可复查、所有新ID/引用/日期/口径闭合、合法0/非法2/拒覆盖3、隔离清理完成、普通产品与交接commit和清单一致，是本包可接收标准。source proof自报及测试无金融签收效力；实体/模型/正式事实/生产UI/全池由总控原节点接续。交付需修复时总控按用户授权直接修，不再发返工卡。
