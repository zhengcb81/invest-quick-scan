# CHAIN-VERIFY-04 独立施工卡

唯一工作目录：**C:/Users/郑曾波/Projects/iqs-chain-verify-lab**。只创建/修改此新根，不写其他任何仓或共享PWF。准备时根不存在；开工重查唯一writer。分支codex/chain-verify-04。

必须先读[common-rules.md](common-rules.md)、[integration-contract.md](integration-contract.md)、[manifest.json](manifest.json)、[inputs.lock.json](inputs.lock.json)、[CHAIN-VERIFY-04.targets.json](CHAIN-VERIFY-04.targets.json)、[CHAIN-VERIFY-04.handoff.template.json](CHAIN-VERIFY-04.handoff.template.json)。本卡包含自己的范围/实现/测试/交接；不需要与其他harness聊天或等待它们结果。

输入仓：iqs, chain_source，逐条rawSHA复制到fixtures；冻结快照运输路径见锁，不能用现有原仓latest替代。新公开主协议iqs.chain_verification_delta_candidate/1.0.0，主文件content/verification-delta.json，module=iqs_chain_verify_lab。全部candidate-only，owner not_mapped、production not_run、qualification false；cutoff=2026-10-13。

## 要解决的实际问题

刚验收CHAIN-SOURCE保留36槽位、59 claims、52 gaps；29partial/6unverified/1N/A，45partial/10unverified/4corroborated。有些关系仅供应方宣称、计划未实绩、第三方转载或具名主体不清。本包用人工官方HTML独立核证关键缺口，不能重跑旧机械软件修复或把“未找到”视为反证。

## 实施步骤

1. 开工/PWF/锁，复制chain_source全依赖及它嵌套原CHAIN fixtures。读取content/chain-source-delta.json、claims.json、sources.json、gap-log.json、attempts.json、keyword-query-proposals.json和docs/coordinator/acceptance-2026-10-14/source-review.md。按targets保留36槽位/59原claim/52 gap精确ID、原序和原SHA；先做错issuer、日期/计划/历史股权/跨槽关系借证据的RED。
2. 建完整disposition ledger：每个原claim/gap的original_state、review_action、new_evidence、proposed_state及理由。旧状态只读。优先targets十个unverified、被错判反证后恢复partial的C016/C049/C056、Google/Apple C031与发起人7%当前资格缺口；不得只挑能成功的小子事实缩分母。给三公司各至少4个关键核证目标尝试，供应材料/设备/客户、主体/持股、计划实绩至少各有覆盖；找不到只报gap。
3. 用现有工具人工查官方HTML：发行人/交易所/监管/具名交易对手原页面优先。记录query、实际工具、UTC访问、response可读程度/失败原因、URL定位/必要短摘录、主/辅源独立性；不写自动采集器、不调用收费搜索/LLM、不得下载财报/PDF/网页全文。只能PDF、JS、403、超时可以停止同源重复，改另一官方可读路径；有证据的stop是合法partial。
4. 逐项核交易双方/法律主体/业务分部/地区/会计期间/单位/生效公开日期与cutoff。当前发起人旧表不是当前股权；框架合作/预计交付不是供货实绩；滚动网页公开日期不当成每条事实首次日期；供应商单方营销证词不等于客户确认采购金额。主题相关不等于收入贡献。供应商设备/材料类型与上市主体分别标，名称不能自动绑StockWiki ID。截止后的文件另列out_of_cutoff，不能回填旧资料支持。
5. 真实直接反证必须同主体/同期间/同关系，证明相反命题才contradicted；缺源/未证实/半年度对全年/计划未部署都是unknown或partial。每项新evidence同时给validity_scope/what_it_does_not_prove和是否独立确认；旧4corroborated复核也可降级。原有10unverified可以全保留，不为关闭率编造来源。未attempted明确标，不说搜索失败。
6. content增量只提案expected_old_raw_sha与旧claim/gapID，不覆盖旧侧车。source schema封闭并版本化；用冻结CHAIN-SOURCE validator检查能够复用的原引用/日期/主体规则，新delta通过薄wrapper自身closure。官方核证记录不是新评分器，不改formal taxonomy、query planner或原题。保持每一旧gap记录，不删closed gap；关闭提案列足以关闭的独立证据与残余问题。
7. validate/export真实公开CLI覆盖所有所选sidecar；可迁移离线重验依赖与引用。人工研究证据与软件测试单独列表。一次集中审查，再只复跑受影响集合。没有新的可靠证据也可partial交付，必须完整分母+真实尝试/停止记录，而不是重述旧报告冒新核源。

## 输出与验收

content/verification-delta.json主records为36原槽位，CV04-R001–036。payload严格{baseline_record_id,baseline_record_sha256,company_key,topic,claim_disposition_refs,gap_disposition_refs,attempt_refs,new_source_refs,proposed_state,remaining_limits}。额外sidecars包含59claim dispositions、52gap dispositions、新sources/attempts、可选query提案及before/after覆盖表；引用闭合，任何分母变化单独说明不替换原基线。

只允许原三公司Alphabet、CATL、中信建投，不新选2000股票池、不把A/H同公司独立计两家，不授owner ID。claims绝不能因为另一槽有一点弱事实而全槽corroborated。新源码/数据仅在独占新根，旧CHAIN、FIN、BLIND、StockWiki与PWF不写。

## 重点测试包（一个大节点）

单元：59/52/36完整分母与引用SHA，错公司/法律主体/分部、public_at>cutoff、滚动日期、计划/实际、当前/历史股权、金额/单位、同名主体、未尝试冒已搜索、unsupported误作contradicted、跨槽借claim/gap。

集成：冻结CHAIN函数实际调用spy；新sidecar选择真实消费，旧结构读取保持；每个source双向对应claim/attempt且无孤儿资格；公开短摘录/数据记录与测试日志分开，无全文/密钥/思考。

E2E：真实validate/export→独立新目录重验，三公司目标记录实际source核证或明确gap；错源/future/tamper负例零正式输出；中文空格/随机cwd/拒覆盖/路径穿越/junction/JSON重复及累计bytes上限。内容独审看具名证据与事实命题，不把CLI通过计为事实accuracy。

若只缺金融报表原件且不能HTML核实，明确停止，不违反本项目轻资产原则去下载文件；Financial/G3/F05门仍由总控管理。
