# FIN-REF-01-R1：同包四组集中续做

唯一writer为原FIN harness，唯一写根 `C:/Users/郑曾波/Projects/iqs-financial-reference-lab`；读[原施工卡](../../../parallel-lanes/packages/2026-10-11-wave2/FIN-REF-01.md)、该目录共同规则/manifest/输入锁，再读[集中验收](FIN-REF-01-acceptance.md)。自包含续做，不需要聊天上下文。不要代改生产仓或其他Lab，也不要新开重叠writer。

验收基线HEAD `b5852aac5978a268dc4dd2eb795663c69b3ab9ca`、产品 `97e5a26dc4569a4cffef5c09b9791fb08b7dc0a1`，65跟踪文件、20原输入匹配。总控经用户授权新增CodeGraph（17文件/227节点/210边），索引设施保留，不视作业务越界。认领时再核当前HEAD/工作树，不覆盖之后的变动；有变动则报告真实差异和新基线。

## R1 补研究实质，修正事实与题义（P1）

现90行只有4行18个数字facts，72行仍skeleton；`gen_gap`拼题义＋公司通用渠道句，`mark_deep`仅加前缀。保留90固定分母及所有null；不要靠改标签或填分凑完成。

- 原每公司6题深核要有逐题实际来源查证、短事实/反证/不确定项和可判定范围；其余24题也有具体URL/定位/读取结果/所支持题义/缺口。允许多题复用一个实际来源或一次查证，但分别映射真实支持范围；不能把同一句公司渠道失败复制成30次独立研究。缺可用来源时深核可诚实结束为缺口，但必须有实际定向尝试和终止原因，区分研究完成、事实可判、独立复核状态。
- 原“deep_verified_count=18”改为据实的研究/核实/尚未复核计数；不要从字符串前缀授予证据资格。若改变closed数据形状，新版/具名profile明确登记，原1.0 schema和旧交接保留，不原地重写。
- 继续允许范围内的官方HTML查证，无LLM、付费搜索、财报/PDF或网页全文保存。CATL至少已存在[中文官方FY2025新闻](https://www.catl.com/news/9654.html)与[英文官方新闻](https://www.catl.com/en/news/6773.html)，可支持部分现金、收入、流动性、研发/行业资料；准确转换亿元，区分货币资金、金融资产、现金等价物及净负债，注明公司自述/来源局限，不能直接推成高分。
- Alphabet同accession的[官方HTML](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm)可查看Note 6/分部/营运资本，政策没有禁止在线读短定位。修正49085/12000含当期票据总面值与46547/10883非流动账面债务的区别，统一fact/来源/公式/notes；不把面值直接替成账面值而不说明定义。NOPAT中间值按未舍入税率复算，文本/结果一致。
- OPERATING_01简单历史FCF保留为partial；维护capex/必要营运资本/多年或中周期不足就列缺口。修正“维护占比更高必然低于已扣总capex的FCF”错误推理。中信建投通道失败保留为所尝试范围，不宣称全部资料只能PDF，不把分析句填official quote。
- 来源cutoff=2026-10-11沿原冻结profile，不用今天新公开资料回填；允许候选区间须事实/锚点/反证齐备，独立复核未做仍proposed，不能verified gold。

## R2 冻结题集、发行人、期间与分母闭合（P1）

- 校验已声明的所有实际输入：锁内FIN consumer20条、三个manifest与questions路径/raw SHA；路径必须在获准冻结根，不靠payload自己声明hash。每行manifest/definition/metric/rubric与正确公司对应，正好该公司30个唯一question_id，不允许重复某题＋换reference_id掩盖遗漏。reference_id生成规则和公司/题义绑定一致。
- source的`issuer_matches=true`是声明，不是跨公司可通用资格。增加具名可校验issuer/company/期间来源关联，或明确旧材料无法验证的支持只能unverified；CATL行不能用Alphabet财务来源支持。不新造StockWiki正式ID/身份签核引擎。
- 真实日历/UTC解析和期间先后、cutoff公开性校验；坏日期不能静默None。未知发布时间若无法由明确出版版本/申报记录等佐证截至时已公开，保持缺口/降支持；不能单靠布尔自报public=true。合法不涉及时点或明确partial仍可读，不一刀切所有nullable来源。
- supported财务fact不能来源空数组，available/missing/issuer/period状态须一致。unknown不可借score_interval绕过空分数；low<=high，无独立复核区间/评分保留提案属性，null不能视作评分校准。

固定RED：row-manifest-hash、questions-file-hash/path、rubric-version、duplicate-question-id-distinct-ref、supported-no-source、impossible-publication-date、unknown-publication-supported、unknown-cutoff-not-marked、catl-supported-by-alphabet-source、unknown-interval-candidate、reversed-score-interval。总控已正确重算内容摘要后公开CLI仍0，不能只补hash拒收测试。

## R3 计算账绑定、口径与可复算结果（P1）

- ledger.pack_id必须绑定实际pack，每个reference_id存在且issuer/metric/期间适配；每个输入source_fact_id的数值、unit、currency、period与原事实一致，支持状态满足该计算要求，未知输入不computed。余额/流量、平均期初期末、同比两年等分别具名处理，不把不同年份或单位混用悄悄接受。
- 当前四项公式用确定性Decimal/具名算术检查，单位/percent缩放和舍入明确，结果须可复算；不执行任意eval、不造评分引擎。未知未来公式保留not_computed/显式不支持，不靠含`/`字符串猜分母。
- 零分子和零分母分开，负值也有明确处理。总控合成内部一致零分子/非零分母控制被错拒；它是离线算术控制而非真实财务正例。真正零分母拒computed并保留缺口；合法partial/unresolved旧材料继续可读。
- 保留原四项输入口径下的算术结果及旧版本；新债务定义/事实更正需新材料、变更说明、摘要和计算，不覆盖旧失败或把原算术正确当经济口径正确。

固定RED：ledger-other-pack、ledger-unknown-reference、ledger-input-value-tamper、ledger-result-tamper、ledger-unit-mix、ledger-period-fact-mismatch、nonfinite-ledger-result；再有零分子正常/真实零分母/输入缺口对照。validate与export都要拒坏账，不能因optional ledger忽略已传ledger。

## R4 稳定CLI、工件与测试环境交接（P1/P2）

- 严格JSON重复键/NaN/Infinity拒收，结构错误先稳定exit2，不能结构失败后继续索引而TypeError/AttributeError。validate/export同一闭合路径，无正式输出；合法partial不因无法打分拒绝。读取采用文档化有界短结构输入，不增下载器。
- `bad-root-array`、`bad-reference-null`当前exit1；`duplicate-json-key`/NaN当前0且发布。新增真实CLI反例，保留原中文随机cwd/确定导出/90分母/拒覆盖测试，不把测试“出现任意错误”当业务规则命中。
- 原57工件里isolation.md实际3311 bytes/SHA cc652c24…与声明2265/53a53c30…不一致。原文件/清单保留作为第一轮记录；新交接按实际冻结字节建立无自引用artifacts，不假称第一轮锁已全匹配。changed_paths列实际逐文件，不用目录替代。
- 公共handoff CLI当前exit2/temporary_root_not_cleaned。结束后按精确自有资源清单清理测试/export临时根、无活动进程；持久开发环境若保留，真实说明为保留环境而非谎填cleaned=true，遵守公共handoff合同的临时根口径。不可清源外仓、其他harness、全局TEMP或B01账本。

## 一个集中交回节点

先固定四组RED再修，同一稳定候选一次unit/integration/真实本包CLI E2E及独立事实先于评分的包级审查；仅因新改动/原失败续验，不添加小节点审批。保留原31P和原日志，新增正反例不能靠修改测试期望绕过。

新交接 `docs/handoff/FIN-REF-01/remediation-01/`：README、interfaces/schema旧新版本、真实90 coverage/18深核索引和方法、定向source-attempts、短官方事实/反证、计算账、case-map、实际RED/GREEN日志/隔离清理、独立审查/PWF、实际base/result/分支/工件bytes/raw SHA。先产品commit后handoff commit，HEAD/result对应真实Git；无remote不自动新建或推送。原第一轮交接/锁/1.0 schema只读保留。

原公开handoff模板沿用，本次仍可partial、仍不关闭F05/G3或金融准确性；完成是交出可用且据实的参考材料，不是强制18题有分或全部90题可判。收到新材料后由总控同包集中续验，不自动派发、代写owner或运行模型实验。
