# EVID-GAP-04：按题义补证据，不用财务数字代替所有判断

唯一可写根 `C:/Users/郑曾波/Projects/iqs-evidence-gap-lab`。先读共同规范与输入锁；所有源仓和其他Lab只读。不写StockWiki身份库/名单、不借已有多地ticker重新定公司。公司固定Alphabet和冻结真实主体上下文，cutoff2026-10-13；不擅自增加公司池或新评分题。

## 目标及交付

原公开10facts主要是财务值，不能充分回答客户价值、收入延续、竞争结构、护城河、管理执行和变化风险。为实际12题建立**缺口→可核命题→来源→覆盖程度**的资料包，并交可离线查询的覆盖工具/检索计划。不是给公司再打分，也不重复REF全部财务核源；优先增补原来没有的经营机制证据。资料不一定找全，诚实不可得也是交付。

Python包 `iqs_evidence_gap`：

```python
def coverage(questions: list, *, board: dict, context_ref: dict,
             mapping: dict, supplement: dict | None = None) -> dict: ...
def query_plan(coverage_report: dict, *, max_queries: int) -> dict: ...
def validate_supplement(document: dict, *, context_ref: dict) -> dict: ...
```

新protocol分别 `iqs.question-evidence-coverage/1.0.0`、`iqs.evidence-query-plan/1.0.0`、`iqs.company-evidence-supplement/1.0.0`。人工映射单独 `iqs.question-evidence-mapping/1.0.0`，绑定原context；每行有question_id、dimension_id、claim_ref（namespace=base/supplement及对应fact_id/claim_id）、direct/partial/proxy/missing/contradicted、理由。程序核引用完整性，不以此声称自动验证语义。CLI `python -m iqs_evidence_gap coverage|plan|validate`，coverage显式 `--mapping M` 与可选 `--supplement S`，默认离线，只读JSON/新输出。不要另写搜索客户端/缓存库/LLM SDK；query_plan是总控可转交原StockQA的声明式候选，不伪装已准入执行policy。

## 资料结构和核源范围

1. 先把每题原evidence要求/锚点拆成稳定dimension_id，原题id+dimension规则版本绑定；每维度列所需命题、已有source、direct/partial/proxy/missing/contradicted范围，不能因出现一个相似词就算覆盖。工人提供人工核查映射，程序只做一致性/聚合，不声称NLP自动验证真实语义。
2. 优先：广告客户价值/可验证客户经济结果、交易/续约机制与收入维持成本；搜索/广告/Cloud市场边界和竞争约束；客户迁移/渠道/规模机制及侵蚀；可核管理承诺与交付时间；AI变化/监管限制的已发生事实与尚未兑现假设。ROIC完整分母/税/资本成本，现金质量/债务期限/承诺/受限资金，披露质量另标确切缺口；找不到不代入行业平均或猜测。
3. 每项claim有claim_id、明确company、业务边界/期间、claim_text、事实/公司自述/第三方观点/推断类别、source_id及支持的题目维度、反证和限制。公司自述不是独立验证，多个转述同一原公告不得算多独立源。
4. source记录原官方URL、publisher/title、publication_date及其证明依据、accessed_at UTC、bounded_excerpt、excerpt_kind（quote/paraphrase）、content hash。日期未知或不能证明cutoff前可用则保留但eligible_for_context=false，不能用网页今天可访问推出当时已知；未来来源也不进入有效生成上下文。
5. 只读官方监管/公司公开网页；允许harness自带浏览搜索，最多20条主要查询、25个新增来源，足够则提前结束。不要用Brave/Tavily/ZAI API key；工具用量/费用未知时明确记录，不能宣称总成本0。若重要命题只能在二级来源找到，列candidate/gap并写需总控核源，不将其冒作官方已证事实。
6. 只存短摘录/必要数字与出处：同一来源直接引文合计≤25英文词（中文同样保持极短），转述明确paraphrase且有边界，不复制全文、不存财报/PDF/HTML正文。可读公开HTML有限内容核事实，不调用filing-fetch或下载文件。source访问失败也留事实状态，不能补假excerpt。

补充包保持原board原字节，**不直接改/替换原public board**。每个新增claim绑定原context/board hash、状态及来源；统一qualification_granted=false，不生成评分gold。实际喂生成模型前由总控决定可用范围，原T0/T1生成输入不回写。

coverage的before只用base映射；after在同一原board上，加入通过validate_supplement、匹配同context且eligible_for_context=true的supplement映射。缺supplement时，映射中指向supplement的条目保留为pending、不计已覆盖；传了包却引用不存在claim或越界公司/日期则拒绝或明确不合格，不默替换原board/hash。报告保留两类来源与mapping/supplement独立hash，使增补前后可复算。

query_plan按共享事实域合并查询（如客户价值与延续性可共享），每query有query_id、company、cutoff、目标维度、query文本、期望source域、top_k、locale、预算权重及未执行状态；max_queries为硬上限。不生成可执行shell，不自动执行检索或假装搜索服务已经成功。

## 测试和验收

- 单元RED：增长数字把留存维度自动算充分、重复同公告当多证据、发布日期未知/未来被纳入、同source_id冲突、其他公司同名、跨截止日、claim引用不存在维度/source、把公司宣称当独立证实、查询超cap。
- 集成：真实原12题全部保留，经营机制与财务维度分开，补证前后coverage可追溯且不虚构分数；至少一条官方已核新经营机制命题，若确实无可用增补则留完整查询/失败证据与逐维缺口，由总控按实证验收，不能编造正例。原10facts/6sources hash保持。
- 公开CLI E2E：coverage→有界query plan→验证本次补充包；坏日期/越界/已有输出非零；离线测试禁网，核源过程单独记录。临时文件/浏览器由自己创建的资源finally关闭清理，来源短摘录和报告留存。
- 交 `docs/handoff/EVID-GAP-04/`：新增命题/来源计数、每题剩余缺口、查询记录、日期资格证明、工具用量与未知费用、来源失败及清理、测试结果；不得宣称所有题已具备准确评分条件。一个包级审查节点。
