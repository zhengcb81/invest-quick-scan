# CHAIN-SOURCE-03：三公司产业链官方来源核证与具名缺口增量

独占C:/Users/郑曾波/Projects/iqs-chain-source-lab，分支codex/chain-source-03。读[共同规则](common-rules.md)、[接口](integration-contract.md)、[manifest](manifest.json)、[锁](inputs.lock.json)、[36槽位目标](CHAIN-SOURCE-03.targets.json)、[handoff模板](CHAIN-SOURCE-03.handoff.template.json)。只写新根，不等ROUTE/BLIND，不运行收费模型/搜索API。

## 为什么做

已修CHAIN4ea3579保留三公司36槽位、64claims/35sources：17supported候选、18partial、1N/A；官方不可达、动态公开日、具名供需等仍有缺口。现需真实正文核证的增量，不再造产业链模板、不用之前supported标签证明事实。只研究Alphabet、宁德时代、中信建投证券；company_key是候选研究定位，不是真实owner ID。同名发行主体、集团/母公司/子公司要分开，特别不能把中信建投混为中信银行。

## 实施步骤与范围

1. 验冻结iqs/chain，导入36槽位原记录和gap-log/source-review。保留旧36全部，给18partial及未独立核实支持边设优先级。旧标签不覆盖新研究结论，不修改旧worker handoff或旧内容。
2. 每槽位写原claim/source/公开日/期间/范围及本轮疑点；优先核CSC公司官方/交易所HTML、Google具名Broadcom/Apple关系与TPU/GPU角色、CATL动态profile与计划/协议/实际出货区别。核数据中心设备/材料/能源依赖时区分产业需要与该公司真实采购，供应商自述关系要标counterparty_statement，不冒发行人直接确认。
3. 使用现有浏览搜索人工读主源。每gap最多3条不同官方路径及合理2轮查找；收到403/仅PDF/无发布日期等记实际attempt，不无限重试。最多补120个claim，36槽位每条必须终态，即使没有新证据。不要下载任何文档、保存网页全文或使用环境key。
4. 一条claim一条明确支持边，来源阅读时点与公开日/事实期/计划截止不同字段。日期不知=null、未来事实不能当已发生；不可得=unverified/partial。法规证明制度，不能证明公司资管规模；协议规模不能证明已出货；托管/股东/经纪客户不能一律buys_input_from。人员变动区分公告日/生效日。
5. 对来源冲突保留双方及范围差异，不择一个数字强行关闭。每个关键词/查询提案必须指本公司本槽位的claim，不跨公司借证；relation使用被冻结原FACT允许值，不暗造新生产边类型。非工业公司缺BOM可解释N/A，但不得把所有IT供应方/客户描述也删成N/A。
6. 交结构化增量、来源清单、尝试与缺口、词条/查询提案及baseline CAS引用。消费方为总控F03–F06/B01；不导入StockWiki、不签金融分数、不发布词表。

## 精确交付

主content/chain-source-delta.json，protocol=iqs.chain_source_delta_candidate/1.0.0，36records原順序，payload严格{baseline_record_id,baseline_record_sha256,company_key,topic,review_status,claim_refs,attempt_refs,gap_refs,proposal_refs}。review_status=corroborated|partial|contradicted|unverified|not_applicable；corroborated表示本轮主源支持该具体候选，不是生产qualified。

content/claims.json，每claim含自有CS03-ID、原record/原claim（新claim原ID=null）、陈述、公司/法律主体、group|parent|segment范围、期间、actual|plan|hypothesis、relation_type、公开日、source_refs、support_status、反证/限制。仍用原question_ref，不改基础题；条目闭合由自有schema约束。

content/sources.json，每来源严格区分host/issuer/counterparty/regulator/third_party，URL、title、publication_date nullable、accessed_at_utc、body_read、locator、必要short_excerpt、read_limitations。不保存全文。attempts.json记真实访问动作/结果/stop_reason；gap-log.json保留全部未关项及下一证据；keyword-query-proposals.json公司/claim引用闭合。

复用已修iqs_chain_content_lab的题目/关系/引用校验，module=iqs_chain_source_lab薄适配validate/export；依赖sidecar显式参数或规范同目录，不能悄悄读原仓。主≤4MiB、sources≤160、claims≤120。生成新增量不要让旧builder覆盖已修链库；基线对象/hash与原件只读。

## 测试与审查

先RED：法规支持经营数值、事件年冒公开日、订单冒出货、第三方冒官方、客户托管冒采购、跨公司关键词、未读正文claim晋支持、删partial/N/A槽位、截止后事实、坏sidecar导出错对象。集中unit+与原validator integration+真实CLI E2E；一次买方内容抽样审查，逐项自审记录但不设逐claim外部审批。不能用schema绿替代正文。

交接可partial，但36槽位/18原partial和新未核边完整保留。report区分已读正文与只是线索、原已有标签与本次独立确认、实际新事实与依旧缺失。是否可进入真实评审由总控核定；不自封gold。
