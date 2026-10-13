> 当前状态（2026-10-13）：本轮三个PRIMARY包已交回，总控直接修复并软件签收，有效增量合并原FIN；来源仍partial、评分null/金融gold0。[当前验收与交接](../../../reviews/parallel-packages/2026-10-13/PRIMARY-three-package-acceptance.md)列实际HEAD/测试/剩余gap。下面编制时的“目录不存在/可开工/未派发”均为历史，不再照它新建目录或重复实现。各源Lab当前说明在docs/handoff/<package-id>/controller-acceptance-2026-10-13/；新工作只按明确补证范围认领，不自动重新启动旧卡。原manifest/43锁是不可变编制证据，不是动态调度状态。

# PRIMARY-ALPHABET-03：Alphabet / GOOGL官方来源与经济口径核验

**可由一个独立harness认领并立即做限定研究**，不依赖另两包或主线B01完成。唯一可写根 `C:/Users/郑曾波/Projects/iqs-primary-alphabet-lab`，编制时尚不存在；不自动派发。与其它包唯一的共同项是只读冻结输入。先读本卡及同目录[共同规则](common-rules.md)、[接口/测试契约](integration-contract.md)、[PRIMARY-ALPHABET-03.targets.json](PRIMARY-ALPHABET-03.targets.json)、[43文件锁](inputs.lock.json)、[manifest](manifest.json)及[PRIMARY-ALPHABET-03.handoff.template.json](PRIMARY-ALPHABET-03.handoff.template.json)。这些文件是完整施工上下文；不要求阅读主线全部历史对话。

## 已有成果与本包目的

原FIN `codex/fin-ref-01@1e88d86754f6faa6959e1cc893ddbc8f6e5b374f` 已正式合并三公司90题；CLI/package1.5.0、财务参考pack1.2.0、ledger1.0.0，114项软件回归通过。旧1.0/1.1和原锁保持。90题72completed研究尝试/18具名gap，所有评分null和来源复核needs_revision。1009条包含历史的facts、104contradicted前序、8账项及62个具名母公司记录已保留；原公式/历史纠错不返工。

你的工作是核自己公司完整30题的现有事实、官方出处、会计/经济意义与反证，把可核/反证/仍欠信息有结构地交回，为后面的真实LLM回答评估建立更可信参考。不能拿结构通过或官网地址自签金融gold，不修改其它60题，不选择新公司，不能将候选参考变成评级/白名单或生产事实权威。财务参考1.2与主线Observation1.2是不同协议，勿混用。

固定主体 `Alphabet Inc.`、挂牌 `XNAS:GOOGL`、信息截止 `2026-10-11`。多市场/股份类别和金融口径边界从targets和冻结题集读，不能只靠简称匹配。新增ID只用 `SRC-RPA-* / FACT-RPA-* / CALC-RPA-* / PROOF-RPA-*`，不能改旧ID含义或引用别包的新记录。

## 本公司研究重点（优先主题，不改题）

1. 先按现有SEC 10-K/iXBRL/官方IR核现金与有价证券126843m等冻结候选、VIE可转移限制、notes-only净现金代理；指标含义与“全部可用现金”分开。这里数值只是现有候选核验目标，不是本卡认证的答案。
2. 把未来采购义务、未开工租赁、票息/信用担保及年度资本开支的期限/是否重复拆开。现有149100/113000m采购义务等不得套用为cutoff起未来24个月，不能因一个子集覆盖倍数推出整体偿付安全。
3. 年度TAC、Cloud RPO与group deferred revenue的范围；SBC现金流adjustment/费用、GAAP OP与R&D资本化代理、segment历史利润/完全成本/增量ROI。原有ROIC正常化仍待定义与可核分母，不能用expensed R&D=零资本。
4. FY2025结束、Jan2026未实现收益、Feb2026 Waymo融资、2026-10-11 cutoff分开。官方后续披露可在截止内补充风险，不能倒写FY2025；融资轮总额不等于Alphabet单体出资额。
5. 整理监管案支付/判罚/撤销/诉讼状态与相关代理说明、audit提案/结果、related-party已披露金额、CAP/实际现金薪酬、GOOG/GOOGL区别。市场价格缺口由真实历史报价处理，不把不同类别/时间当当前GOOGL价。
6. 广告渠道/分销依赖、AI对搜索与云业务的机会和替代、第二曲线归因：只记录官方明确事实及反证。不能以规模利润或用户增长自行证明护城河/补贴依赖为零。

先按这些主题找官方可读材料，随后对下面30题逐一处理；目标问题文本/anchors/rubric来自43文件中的原20冻结输入和自己的manifest，不凭该重点列表新增或删题。资料可批量读，多题复用来源，但每一个confirmed_primary状态都必须覆盖该题所有当前非contradicted事实的支持范围与残余缺口，不以单条新闻代表全题。官方原件仍无法轻量读取就留gap，不强制下载PDF或造比例。

## 固定30题位

| question_id | reference_id | 当前研究状态（非来源认证） | 现有fact数（含历史） |
| --- | --- | --- | --- |
| IQS_01 | FR-ALPHABET-IQS_01 | research_completed | 4 |
| IQS_02 | FR-ALPHABET-IQS_02 | research_completed | 12 |
| IQS_04 | FR-ALPHABET-IQS_04 | research_completed | 9 |
| IQS_05 | FR-ALPHABET-IQS_05 | research_completed | 9 |
| IQS_06 | FR-ALPHABET-IQS_06 | research_completed | 24 |
| IQS_07 | FR-ALPHABET-IQS_07 | research_completed | 5 |
| IQS_08 | FR-ALPHABET-IQS_08 | research_completed | 6 |
| IQS_09 | FR-ALPHABET-IQS_09 | research_completed | 8 |
| IQS_10 | FR-ALPHABET-IQS_10 | research_completed | 21 |
| IQS_12 | FR-ALPHABET-IQS_12 | research_completed | 11 |
| IQS_13 | FR-ALPHABET-IQS_13 | research_completed | 10 |
| IQS_14 | FR-ALPHABET-IQS_14 | research_completed | 11 |
| IQS_15 | FR-ALPHABET-IQS_15 | research_completed | 15 |
| IQS_16 | FR-ALPHABET-IQS_16 | research_completed | 21 |
| IQS_17 | FR-ALPHABET-IQS_17 | research_completed | 7 |
| IQS_18 | FR-ALPHABET-IQS_18 | research_completed | 9 |
| IQS_19 | FR-ALPHABET-IQS_19 | research_completed | 11 |
| IQS_20 | FR-ALPHABET-IQS_20 | research_completed | 14 |
| IQS_21 | FR-ALPHABET-IQS_21 | research_completed | 12 |
| IQS_22 | FR-ALPHABET-IQS_22 | gap_terminated | 8 |
| IQS_23 | FR-ALPHABET-IQS_23 | research_completed | 15 |
| IQS_24 | FR-ALPHABET-IQS_24 | research_completed | 12 |
| OPERATING_01 | FR-ALPHABET-OPERATING_01 | research_completed | 11 |
| OPERATING_02 | FR-ALPHABET-OPERATING_02 | research_completed | 13 |
| INTERNET_01 | FR-ALPHABET-INTERNET_01 | research_completed | 8 |
| INTERNET_02 | FR-ALPHABET-INTERNET_02 | research_completed | 12 |
| SOFTWARE_01 | FR-ALPHABET-SOFTWARE_01 | research_completed | 10 |
| SOFTWARE_02 | FR-ALPHABET-SOFTWARE_02 | research_completed | 12 |
| SCALING_01 | FR-ALPHABET-SCALING_01 | research_completed | 12 |
| SCALING_02 | FR-ALPHABET-SCALING_02 | research_completed | 8 |

对应targets有每行baseline SHA、题文/manifest/metric/rubric/期间绑定、外60行摘要、原全部Source与8ledger摘要。当前已存在contradicted事实不算新发现，它们必须保留供追溯；原官方文章和受限网页定位可沿用导航，但每个重要claim要自己实际核读。不得用网页抓取失败推断全公司缺资料。

## 实施步骤

1. **开工准备**：在新根核唯一writer/路径和Git状态，初始化自己的Git/PWF，冻结43依赖为fixtures/fin，保留原bytes。不得将原FIN源码复制后当自己的新引擎修改；包中薄封装只调用原FIN公开CLI。fixtures/targets.json复制本卡targets原件，fixtures/dependency-lock.json保留原锁并明确本地路径映射；不要改IQS源锁或19旧访问摘要。
2. **先定义证据需求和RED**：content/research-plan.md列30题、当前可用事实、所需最小官方材料/口径/反证。编写允许自身30/禁止外60、假官方、截止污染、proof跨题引用、币种/单位/主体误配等少量会影响结论的失败案例；合成显式synthetic。不要为每题造一个helper或新验收门。
3. **实际官方研究**：按主题先查公开IR/监管/交易所可读内容，核发行人/股份类别/公布日/期间/单位/主体；存短定位和结构化事实，不保存附件/HTML全文。公司官网域名先由发行人法定名称/交易所公开主体页交叉核证；trusted host registry只导航/机械反钓鱼，不是官方内容认证。`evil.example?url=sec.gov`、`sec.gov.evil.example`、不同发行人CIK/证券代码不能借官网字符串通过。记录入口/正文/转载/未读/PDF-only差别，actual attempts及适用题明确。
4. **更新现有参考候选**：完整90pack只更新自己30；追加专属Source/fact和qualification proof，错误原fact有前序SHA/contradicted+新的fact，正确旧转载记录也不改Source。受影响本公司账项只用原公式/roles，未注册经济方法写calc-notes。旧母公司map和另一公司账不动，no_score与review needs_revision保留。用原hash/summary函数重算pack与ledger绑定，列精确changes JSON。
5. **一个稳定包集中验证**：自己的thin CLI支持validate/export；先实际调用冻结FIN validate/export核90题和ledger。集中unit/integration/真实本包CLI E2E、一次来源审查；修复只回归相关项。保留真实初次失败/最终日志/时间/PID/退出码，不能把结构/GREEN等同网页原件被认证或真实LLM准确率。
6. **交接与清理**：自己的test temp、端口和进程结束后准确清理，保留必要小反例/原日志；产品commit→交接commit，交完整原件清单、43锁、30coverage、source proofs/changes/calc/review/case-map/isolation和PWF。只写 `C:/Users/郑曾波/Projects/iqs-primary-alphabet-lab/docs/handoff/PRIMARY-ALPHABET-03`；总控接收后独立合并/核证，不能写原FIN或代关金融门。

## 交付清单与命令

可从[PRIMARY-ALPHABET-03.qualification.template.json](PRIMARY-ALPHABET-03.qualification.template.json)与[PRIMARY-ALPHABET-03.changes.template.json](PRIMARY-ALPHABET-03.changes.template.json)起步；两个模板只表示未开始、全unconfirmed/无delta，必须写自己的实际研究后才可交付。它们不会使30题“已核”。

主产物：`content/reference-pack.json`、`content/calculation-ledger.json`、`content/qualification-index.json`、`content/changes.json`；细字段严格沿integration-contract。另需 `content/research-plan.md`，本包CLI薄封装、测试、依赖快照/原锁+路径映射、完整docs/handoff/PRIMARY-ALPHABET-03/材料。Source/fact/proof不能dangling、重名、跨公司，给每个原非contradicted事实明确支持/反证/gap处置。

```powershell
# 在自己的目录执行；设置只读冻结FIN模块路径，不改系统PATH/全局配置。
$env:PYTHONPATH = 'C:/Users/郑曾波/Projects/iqs-primary-alphabet-lab/fixtures/fin/src'
python -B -X utf8 -m iqs_financial_reference_lab --version
python -B -X utf8 -m iqs_financial_reference_lab validate --input content/reference-pack.json --inputs-lock fixtures/fin/fixtures/inputs.lock.json --ledger content/calculation-ledger.json
python -B -X utf8 -m primary_reference_lab validate --candidate content/reference-pack.json --ledger content/calculation-ledger.json --qualification content/qualification-index.json --targets fixtures/targets.json --inputs-lock fixtures/dependency-lock.json
# tests与export均在本包自己的随机临时根运行；export必须指向不存在的新目录。
```

自己的CLI模块需要在src中按pyproject安装到本包隔离环境或将本包src与冻结FIN/src同时加入该子进程PYTHONPATH，不能安装进其它Lab/shared环境；上述先原FIN命令与本包命令分别运行时按此规则切换，不能误声称尚未实现的wrapper现在可用。所有CLI测试用剥key/断网子环境，不读工作机完整环境给产品日志。

最终交回：`C:/Users/郑曾波/Projects/iqs-primary-alphabet-lab/docs/handoff/PRIMARY-ALPHABET-03/handoff.json`。泛型handoff1.0、实际新私有qualification candidate1.0、actual FIN1.5.0/pack1.2/ledger1.0版本分开；interfaces写方向/raw hash，snapshot结果指产品commit，README另报最终metadata HEAD。无法完成官方核读可partial，但要说明具体缺口、已尝试哪些官方入口及最小下一材料，不把全部难题改not_applicable。所有source reviews与scores资格不被自己升级。

## 验收边界

允许限定研究现在启动，强条件只是输入43字节齐全/新根唯一writer，不等B01或别包。测试组合完整见共同契约；本公司30条coverage无省略、外60/原Sources/外账不变、初始input locks未改、关键来源实际核读与失败可复查、所有新ID/引用/日期/口径闭合、合法0/非法2/拒覆盖3、隔离清理完成、普通产品与交接commit和清单一致，是本包可接收标准。source proof自报及测试无金融签收效力；实体/模型/正式事实/生产UI/全池由总控原节点接续。交付需修复时总控按用户授权直接修，不再发返工卡。
