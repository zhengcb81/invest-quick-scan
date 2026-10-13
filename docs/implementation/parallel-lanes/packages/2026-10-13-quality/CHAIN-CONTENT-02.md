# CHAIN-CONTENT-02：三家公司真实产业链信息基准

独占工作目录 **C:/Users/郑曾波/Projects/iqs-chain-content-lab**，分支 codex/chain-content-02。先读[共同规则](common-rules.md)、[接口](integration-contract.md)、[锁](inputs.lock.json)、[范围](manifest.json)、[模板](CHAIN-CONTENT-02.handoff.template.json)。可独立做，不依赖 ROUTE/SCORE，也不修改已有 FACT/FIN/PRIMARY 包。

## 内容目标

FACT 旧包交的是61题语义与合成案例；FIN/PRIMARY 查的是30评分题的财务与经营证据。本包补真实的“产品—材料/设备—供应角色—应用行业—客户角色—商业化”内容，供产业链主题检索及 F05 内容验收。只研究原已选 **Alphabet、宁德时代、中信建投**，不另挑公司或改名单。真实 issuer 分别 Google/Alphabet 的上市集团、CATL/宁德时代、CSC/中信建投证券；关联上市供应商/客户仅关系目标候选，不新增宇宙成员，不以名称近似代替真实身份。

截止日固定2026-10-13。人工公开网页研究允许，短结构信息与URL足够；不下载财报/PDF、不存网页全文、不调用额外模型/付费API、不写任何生产DB。无法原文核实的具名客户/供应商留 unknown，不用行业常识补成交关系。

## 研究分母与交付

1. 从锁中 facts.json 选适用于产业链/业务的原 field/question ID，写 content/question-targets.json。每公司覆盖业务分部、细分行业、产品、关键材料、关键设备、上下游应用、客户角色、供应角色、第一/第二曲线、商业化状态至少十个主题；各主题显式绑定原 FACT 问题，不能新造正式题 ID。冻结后主records中三公司×十主题共30个槽位始终保留，可一个槽位多关系、N/A/缺口。
2. 主文件 content/chain-reference.json，protocol=iqs.chain_content_reference_candidate/1.0.0。records 每项严格 {record_id,company_key,subject_descriptor,topic,question_refs,fixture_class,owner_mapping_status,production_execution,status,claims,gaps}。status=candidate_supported|partial|unknown|not_applicable；subject_descriptor {issuer_name,listing_hints,scope,segment}，listing_hints 只供核对，owner映射仍 not_mapped，不分配真实 entity_id。
3. claims 每条严格 {claim_id,statement,relation_code,source_role,target,commercialization,period_start,period_end,public_at,source_refs,counterevidence,confidence}。relation_code 只用原 FACT 问题声明的 code；target {name,kind,disambiguation,identity_status}，kind 的有限枚举在schema中声明、identity_status=unresolved|descriptive_only。source_role 区分采购/制造/出售/应用/研发合作，商业化状态至少 commercial|pilot|research|unknown。未披露具体关系允许只有角色描述，不能填假 target 公司。
4. 独立 content/sources.json 每source严格 {source_id,url,title,owner_type,public_at,retrieved_at_utc,original_read_status,locator,evidence_note,excerpt_sha256,supports_claim_ids,limitations}。source_id/claim_id 前缀 CC02-。owner_type=official_issuer|official_regulator|official_exchange|third_party|unknown；原文未读或披露日不明不能 candidate_supported。excerpt_sha256 仅短 evidence_note UTF8 SHA，不声称网页全文hash。每个来源短摘录建议≤25词，中文简短必要引文；说明该链接具体支持哪条claim，不把同网页所有内容都挂全部关系。
5. 优先核查 Google/Alphabet 云和自研芯片的角色，区分设备使用与制造、商业云服务与研发、Alphabet 与独立企业；CATL 电池/储能/材料及应用，区分行业需要某材料与已证明采购某供应商、样品/合作与量产；CSC 经纪/资管/投行/自营，区分客户资产与自有资产、投行业务客户与产品下游，不强套工业BOM。
6. 每公司至少完成两个有实际正文支持的业务/产品/应用主题。材料/设备/具名交易方不可得仍交逐渠道的 gap-log.json：record_id、looked_for、channel/url、actual_result、attempted_at_utc、stop_reason、next_evidence_needed。足够定向尝试后结束，不无限搜索，不把入口失败当整公司没有业务。
7. 从真实 claims 推导 content/keyword-proposals.json：英文/中文名称、别名、产品/材料/设备/行业类型、候选层级、语境、不可等同项及来源claim。不得宣称词表已发布。再做 content/query-expectations.json 至少12个具名主题（AI硬件/云服务/电池材料/储能/证券资管等）：匹配/应排除/待核项及理由。不实现matcher，expected只为总控以后实际 strict/explore 查询提供内容基准。两个相似词不等于两家公司相同。

## 轻量工具与测试

实现 `iqs_chain_content_lab` validate/export，另明示只读 sources/targets 参数；schema/目标引用/来源声明闭合、日期和方向检验，禁止算法自签事实。主数据≤6MiB、claim≤300、source≤120、短摘录≤800字符。先RED：用设备误当生产设备、研发合作误当供货、转载自签官方、cutoff后内容、近名主体混淆、未来客户猜测、证据只导航、删unknown槽位。

Unit 验证三公司×十槽位、关系方向/角色/商业化/日期、dangling source/claim；integration 从真实短引用生成关键词提案并保持 unknown，篡改引用必须拒；离线公开CLI E2E验证中文路径、坏输入零输出、重复导出和清理。网络研究记录与离线测试分开；测试结果不能证明网页真伪。稳定候选一次集中来源/关系审查，区分支持、反证及实际缺口，不为凑全部已确认虚构关系。

## 接入责任

交上述content、schemas、工具/测试与共同handoff至 docs/handoff/CHAIN-CONTENT-02/。主record、keyword和query期望用同一claim_id闭合，不维护第二事实库。总控负责真实身份映射、F03/F04/F05/F06候选合并、主题/行业实际查询验证；本包不能关闭 F05 或给不存在的owner字段出golden。无法证实的关系作为可用缺口交付，整体状态诚实partial。
