# FIN-CATL-02：宁德时代（300750）完整30题轻量核源

## 你在做什么

唯一工作根 **C:/Users/郑曾波/Projects/iqs-reference-catl-lab**；分支codex/fin-catl-02。编制时不存在；开工重查，不抢其他writer。关联B01/F05，研究范围只company_key=catl，不能写其他项目、生产库或收费API。用户选你执行本卡才开工，总控没有自动派发。

先读本目录common-rules.md和integration-contract.md、FIN-CATL-02.targets.json、inputs.lock.json、manifest.json与FIN-CATL-02.handoff.template.json。这些文件连同自身PWF足以独立运行，不需要聊天。最新背景：FIN R4软件已103P签收，原90题仍9已研究/9gap/72未开始；你做剩余内容，**不是R4/R5软件返工**。

本公司30题：5已研究、1gap、24未开始；保留已有六深核有效内容，同时补原24题与深核缺口。cutoff集合=['2026-10-11']（逐行targets优先，缺失不得补今天）。宁德时代（300750）名称/ticker是提示；法律发行人以targets和官方页面核验，不授owner ID或真实身份golden。

## 核源优先级（必须服从实际冻结题义）

- 电池/储能：动力与储能收入/量价/客户和地区结构，产品技术/认证与竞争优势；产能不等于出货、装机不等于公司全部确认收入，海内外比例口径单列。
- 周期：锂/材料价格、定价传导、产能利用率、库存/订单/现金回收；把暂时利润低谷与永久优势侵蚀分开，不因当期指标差直接排除。
- 财务：现金/短长债/营运资本/资本开支与ROIC合并口径，客户返利/价格下降与利润质量；人民币/外币、集团/子公司/分部、全年/季度不混。
- 优势与成长：成本/规模/研发/制造良率/客户认证/供应链与国际布局，下一曲线和结构性替代风险；每项有来源及反证，不能凭新闻标题抬评分。
- 旧6深核3已研究、3gap（实际以targets为准）；官方新闻可支持新闻里明确事实，不能自动覆盖现金流/负债/盈利口径。继续定位官方可在线读的披露/交易所摘要/IR页面，确实轻量不可得才逐题gap。

以上是查证方向，不是新增题集/固定答案；questions/anchors/evidence从自身冻结30题读取。每题记录实际所需证据、在线访问/locators、当时公开性、可支持claim、反证及残余缺口。Source多题复用允许，一页只支持该页含的具体事实；定性也要来源，不能只写“资料不足”。可按资料主题批量读页，但逐题覆盖保持30。

## 已冻结题位（不改ID、不重新路由）

| question_id | reference_id | 基线状态 | deep |
| --- | --- | --- | --- |
| IQS_01 | FR-CATL-IQS_01 | not_started | False |
| IQS_02 | FR-CATL-IQS_02 | research_completed | True |
| IQS_04 | FR-CATL-IQS_04 | not_started | False |
| IQS_05 | FR-CATL-IQS_05 | not_started | False |
| IQS_06 | FR-CATL-IQS_06 | not_started | False |
| IQS_07 | FR-CATL-IQS_07 | not_started | False |
| IQS_08 | FR-CATL-IQS_08 | not_started | False |
| IQS_09 | FR-CATL-IQS_09 | not_started | False |
| IQS_10 | FR-CATL-IQS_10 | research_completed | True |
| IQS_12 | FR-CATL-IQS_12 | not_started | False |
| IQS_13 | FR-CATL-IQS_13 | not_started | False |
| IQS_14 | FR-CATL-IQS_14 | not_started | False |
| IQS_15 | FR-CATL-IQS_15 | not_started | False |
| IQS_16 | FR-CATL-IQS_16 | research_completed | True |
| IQS_17 | FR-CATL-IQS_17 | not_started | False |
| IQS_18 | FR-CATL-IQS_18 | gap_terminated | True |
| IQS_19 | FR-CATL-IQS_19 | not_started | False |
| IQS_20 | FR-CATL-IQS_20 | not_started | False |
| IQS_21 | FR-CATL-IQS_21 | not_started | False |
| IQS_22 | FR-CATL-IQS_22 | not_started | False |
| IQS_23 | FR-CATL-IQS_23 | not_started | False |
| IQS_24 | FR-CATL-IQS_24 | not_started | False |
| OPERATING_01 | FR-CATL-OPERATING_01 | research_completed | True |
| OPERATING_02 | FR-CATL-OPERATING_02 | not_started | False |
| AUTO_01 | FR-CATL-AUTO_01 | not_started | False |
| AUTO_02 | FR-CATL-AUTO_02 | research_completed | True |
| ENERGY_TRANSITION_01 | FR-CATL-ENERGY_TRANSITION_01 | not_started | False |
| ENERGY_TRANSITION_02 | FR-CATL-ENERGY_TRANSITION_02 | not_started | False |
| SCALING_01 | FR-CATL-SCALING_01 | not_started | False |
| SCALING_02 | FR-CATL-SCALING_02 | not_started | False |

targets给了逐行binding SHA及baseline_row_sha256；另两公司60条原件从39文件FIN依赖中读取并核canonical摘要不变。新source/fact/calc前缀固定SRC-RFC-*/FACT-RFC-*/CALC-RFC-*；不得引用别包新ID。原Source记录只读；纠错用新fact版本＋changes.md说明，别让旧ID悄悄换含义。

## 实施步骤

1. sole-writer/Git/PWF pin与39文件完整冻结，保护原FIN.code/schema/20锁。创建自己的research-plan.md按全部30题标证据需求/已知来源/反证/缺口，不靠LLM推断数字。
2. 写少量真实业务RED：错发行人/截止污染/非本公司修改/账口径或无依据研究done。先确定预期，再只实现最小封装/报告器，调用现有FIN公开validator而非重写校验器。
3. 逐主题查官方公开页面；先事实/口径/相互冲突，再依据题义整理判断。补24未开始与deep缺口、复核六深核已有材料；每题真实完成或具体gap，not_started剩余要如实列开放项。默认分数null，候选区间也需来源与反证，不自签金融gold。
4. 产出content/reference-pack.json完整90候选与calculation-ledger.json，自己30行可更新、外60保持；references顺序沿baseline，source/calc范围按契约。调用原hash/summary函数，不偷减分母或改input lock。
5. 一个稳定候选集中unit/integration/公开CLI E2E与一次包级事实审查，留实际原日志。失败直接修，续跑受影响项，不新增逐题门；网页核查与离线软件测试分账，不声称本包跑了真实LLM/owner E2E。
6. 精确清理自己测试临时产物、进程/端口；产品commit→交接commit，填实际SHA/计数/源码与工件清单/输入快照、coverage、sources/changes/calc-notes/review/isolation/PWF。交回自身docs/handoff/FIN-CATL-02/handoff.json。

## 集中测试包和接受标准

| 层 | 具体正反例 | 必须观察到 |
| --- | --- | --- |
| Unit：允许变化 | 改别公司reference、旧Source内容、另一company的ledger、重新路由ID | 范围控制拒绝，不产生正式候选；自己的合法追加通过 |
| Unit：时点/事实 | cutoff之后网页、发布日未知却supported、Q1代全年、单位币种错、搜索摘要当正文 | 原validator/研究边界具名拒或真实unknown/gap，不填5 |
| Unit：经济含义 | OCF/capex标ROIC、期末当期初、客户现金当自有、零NOPAT合法 | 已注册数值计算调用原CLI守拒；行业不可比明确partial/not_applicable；合法零分子可过 |
| Integration | 30绑定+外60canonical不变、39冻结hash、90总分母、source/fact/calc ID隔离、summary重算 | 计数和hash可独立复现，不改原锁、不自签研究完成 |
| Integration：合并 | 一份模拟另一公司不相交增量、同源基线ID冲突、固定merge时点的两顺序 | 合法不相交结果相同；碰同旧ID先报冲突，禁止last-writer-wins；合成标synthetic，不说另一harness已交付 |
| 真实本包CLI E2E | 去key环境/随机cwd/中文空格路径：合法全90 validate/export；损坏ledger/schema拒、重复export拒覆盖 | 原公开CLI实际0/2/3；坏输入无正式输出，依赖39字节前后不变，无网络/下载 |
| 事实审查 | 30题各自所求与locator，已有六deep数字/期间/反证、不可得实际尝试 | 初稿与独立来源复核范围分开；未核行保留not_run，不能由测试绿写金融全对 |

测试不要求为每道题加一个helper审查；共享一份case-map/JUnit/log足够，一次包级review。资料成功获取率没有强制100%，真实缺口可partial，但24未开始不能批量换个状态就声称研究完。已有成果保护，不让软件修复压倒源核验。

## 最终交接给总控

必交：现有协议完整90候选/ledger、本公司30 coverage（原基线/新状态/新增来源/证据缺口）、六deep索引、短source访问摘要、changes.md（旧row/entry hash→实际变更原因）、calc-notes.md、正式handoff模板的实际化、接口/版本/SHA、工件清单、冻结快照、case-map、review、isolation、原logs/PWF。未开始/无法判定/cutoff/near-name风险单列，不假造company/subject/model请求身份。

总控只接你这一公司30行和专属来源/账增量，独立合并回原FIN，之后与B01答案严格题义/manifest join并盲评。你不写原FIN，不改B01收费账本/StockWiki/company-wiki，不自行关闭F05/G3/金融/生产/全池门。交接若仍有可修复问题，总控直接修，不再发整改施工卡。
