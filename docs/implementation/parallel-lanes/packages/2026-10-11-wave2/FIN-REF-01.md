# FIN-REF-01：买方标准的独立事实与评分参考基准

## 唯一工作目录与职责

`C:/Users/郑曾波/Projects/iqs-financial-reference-lab`。关联 B01/F05；只建立可审计参考，不执行模型实验，不代签金融门。读 [共同规则](handoff-rules.md)、[manifest](manifest.json)、[输入锁](inputs.lock.json)。与 EVID 的证据工具、FACT 的信息题库、IDENT 的身份案例均分工不同：本包核正式评分题所依赖的具体事实/口径与评分判断，不改这些 Lab。

为什么需要：真实30题首轮可评分为0，格式/技术通过不等于金融正确。必须有独立于模型输出的核对基准，先看错公司、错期间、错单位、遗漏反证，再看评分是否有充分依据。LLM 自报置信度和多模型多数票不是事实真值。

## 研究对象、冻结题集与时点

只使用已选三样本：Alphabet/GOOGL；宁德时代/300750；中信建投 H/06066（不是中信证券）。用锁内三份正式30题 manifest/questions，不从24通用题自行猜剩余6题、不重新路由、不扩大名单。参考 `company_key=alphabet|catl|cncb_h` 为本包标识，不发正式 entity/subject/issuer ID。

每公司形成30条 reference，合计90条，question_id/text/metric/rubric/期间要求精确对应自身冻结 manifest；跨公司适用题可以不同。逐行保持来源输入hash。information_cutoff 优先以该冻结输入为准，缺明确 cutoff 则该行 `cutoff_unresolved`，不能拿今天资料回填历史。CATL/中信建投原owner subject资格尚缺，本包可查法律发行人公开事实但不能声称已产生 owner verified reference。

正式题集与当前通用题库/发布指针可能不同，核对以冻结 manifest 和 questions 内的实际题义/anchors 为准，不用今日 current 指针替换旧包。独立 rubric release 未登记时该版本/hash填null并说明，仅绑定原 manifest/题义摘要；不要选择一个未校准候选评分尺冒充活动评分规则。

人工使用公开联网搜索/浏览，优先监管/交易所/公司IR官方HTML；不调用 LLM/收费搜索，不保存财报/PDF/网页全文或大量原文，不开发爬虫/下载器。记录URL、标题、发布/读取时间、定位短语、简短转述及必要小段引用。只有PDF可核实而不能在线读时标 `source_unavailable_under_lightweight_policy`；不强行下载。主线轻资产边界保持。

## 交付的数据契约

协议 `iqs.financial_reference_pack/1.0.0`，闭合 schema、稳定 reference_id 与旧版只读校验。顶层 `protocol,pack_id,created_at,inputs,companies,references,sources,review_status,limitations`；pack_id 对实际内容规范化摘要，具体算法/排除自身规则留 interfaces。

每条 reference 至少包含：

| 组 | 必需字段与语义 |
| --- | --- |
| 定位 | reference_id/company_key/法律发行人名称/挂牌提示/question_id/question_text_sha256/manifest raw SHA/metric_id/rubric版本hash |
| 时点口径 | information_cutoff、period_start/end、scope（consolidated/segment/security）、会计口径、unit/currency；不可得填null并列原因 |
| 独立事实 | facts数组：稳定fact_id、claim、value或null、单位/币种/期间、sources、support_status、conflicts；数字和定性分开 |
| 证据边界 | required_evidence、available_evidence、missing_evidence、counterevidence、issuer/period匹配、来源截至当时是否公开 |
| 判断 | answerability=answerable/partial/insufficient_evidence/not_applicable/cutoff_unresolved；expected_score=null默认；score_interval可空；anchor_reason/assumptions/falsifiers |
| 复核 | drafted_by实际harness角色、independent_review=not_run/needs_revision/accepted_on_sources；限制和不确定性 |

`expected_score` 不因 anchors 存在就自动给数。确有充分证据可给“候选参考评分区间”，说明上下界分别对应哪些事实与锚点；主观竞争优势/成长判断不能当精确标准答案。无人工/独立复核时评分只 `proposed`，总控以后决定是否作为校准，不能自称 verified金融gold。

至少每公司6题做深入核对，优先现金/利润质量、资本效率或行业替代口径、负债/生存、收入结构/集中、持续优势、周期或结构性变化；具体题ID必须来自该公司30题。另24题也须逐条有来源尝试/缺口/反证，不用一句“资料不足”批量占位。

涉及数字计算，交 `content/calculation-ledger.json`：原值、实际来源fact_id、公式、期间、分子/分母口径、结果、单位与舍入；公式如ROIC须说明NOPAT/投入资本和期初期末平均，不拿银行ROE代工业ROIC；Q1不可替全年，HKD/CNY不得无FX转换，不确定分母不输出精确数。可用确定性算术辅助，禁止另写评分引擎。

## 实验盲评接口与完成产物

交 `content/reference-pack.json`、`content/calculation-ledger.json`、`docs/handoff/FIN-REF-01/blind-review-guide.md` 和受控样例。盲评 guide 固定两阶段：

1. 隐藏 provider/model/pack策略，只看每题实际最终答案及引用；按reference逐claim核 issuer/期间/数字/单位/依据/反证，分别记录 support/contradicted/unverifiable/not_assessable。
2. 事实核对后才看评分与参考区间。单独报告有效评分覆盖率、可判定事实准确性、弃答/错issuer率、缺失/格式失败；不把unknown计正确，不删除难题缩原30分母，多次回答保留版本与全部成本。

schema-valid仅说明材料有效，不能由reference自己证明源内容真实。与模型答案的自动join只能严格ID/题义/manifest绑定；本包没有真实新模型输出，所以不得交模型排行榜或准确率结论。

本包 CLI 必須实现：

```powershell
python -B -X utf8 -m iqs_financial_reference_lab validate --input content/reference-pack.json --inputs-lock fixtures/inputs.lock.json
python -B -X utf8 -m iqs_financial_reference_lab export --input content/reference-pack.json --output runs/export-01
```

validate exit0合法、exit2坏输入；保留合法 partial/unresolved，不因未能评分就拒绝材料。export 只写自身新目录、不覆盖，90行与缺口完全保留；默认无网，不能边校验边拉URL。报 `validation_scope=reference_artifact_only,owner_qualification=not_run,model_accuracy=not_measured`。

## 实施与集中测试

1. sole-writer/Git/PWF/锁冻结，90个稳定目标列表，先列可判定证据而非填分。
2. 先RED：近名错发行人、cutoff之后来源、全年与Q1混用、币种/单位误配、不存在来源fact_id、重复ID/JSON键、空分母、unknown填5、未来schema。
3. 查证与独立计算，每公司6深核＋其余完整覆盖；形成反证与无法判断的诚实记录。
4. 集中 unit（绑定/时点/数值/闭合引用）、integration（原锁/90分母/确定导出）、真实本包CLI E2E（随机cwd/中文空格/损坏输入拒发布/重复导出拒覆盖）；一次稳定候选review，尽量独立角色先核事实后核评分，不循环自证。

同一 sources 多行复用允许，但一条来源只支持它实际包含的事实；错公司和cutoff污染必须拒绝加入支持集合，可留 conflicts/counterevidence。默认 missing/null 不改5，不把not_applicable偷减分母，给全90条一个coverage表。

## 交回与接受边界

完整目录 `docs/handoff/FIN-REF-01/`、[模板](FIN-REF-01.handoff.template.json)、90行coverage、18题深核索引、URL短事实、计算账、复核范围、原测试/隔离日志、source查证实际次数和局限。无公司文档/网页正文。总控接 B01 真实答案后完成独立准确性验证与人工评分核对；当前交接不关闭F05/G3，不取得StockWiki身份/证据签核权。
