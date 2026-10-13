# ROUTE-COVER-02：组合路由与问题适用性覆盖

独占工作目录 **C:/Users/郑曾波/Projects/iqs-route-coverage-lab**，分支 codex/route-cover-02。可独立开工；只写该新根。先读[共同规则](common-rules.md)、[接口](integration-contract.md)、[输入锁](inputs.lock.json)、[manifest](manifest.json)、[handoff 模板](ROUTE-COVER-02.handoff.template.json)。无需聊天上下文或另外两个新包。

## 交付目的与边界

已有路由/模块契约及合成 MATRIX 比较案例。本包解决更前端的买方问题：一家半导体成长公司究竟该选哪些模块，低谷公司会不会丢掉观察题，多业务集团是否被单个行业标签误导。交付完整适用性研究与能调用原路由/compose 入口的离线回归包；不做第二 router，不调用 LLM、不写正式模块、不生成真实 owner 正例。

基线问题目录由 catalog.json 权威列出；当前 common 3.0.0/24题、routing-policy schema1.3.0/router2.3.0 以锁中原字节为准，不假设旧 fixture 的 router2.0 已当前。所有被冻结 catalog 模块必须有一行覆盖记录；数量由实际文件计算，不能预设或漏掉 lens/overlay/diagnostic。优先读 questions/catalog.json、routing-policy.v2.json、scoring-contexts.json、schemas/quick_scan/route-decision.schema.json、scripts/question_sets.py/routing.py 及相关设计文档。

## 必须完成的内容

1. 建 `content/module-coverage.json`：每个 catalog 模块一行，RC02-ID、module_id、kind、source_file_sha256、适用/排斥条件、可观察证据、依赖/替代关系、与其他轴的相互作用、case_refs、真实产品支持/缺口。不要复制维护题目文字。
2. 建主 `content/route-cases.json`，protocol=iqs.route_coverage_candidate/1.0.0。至少24个独立情景，覆盖全部8类主体（operating/bank/insurer/capital_markets/property_owner/property_developer/holding/pre_revenue）、7阶段、行业多轴、稳定属性、周期、困境以及不确定性。每个模块可标专门 gap，但覆盖表不得缺行。数量只是最低覆盖，不要求笛卡尔积膨胀。
3. 每例 records 严格字段：case_id、fixture_class、owner_mapping_status、production_execution、as_of、input_profile、evidence_facts、previous_state、expected、question_refs、explanation。evidence_facts 每条 {id,claim,public_at,period,scope,source_class}；expected 为 {required_modules,excluded_modules,conditional_modules,retained_question_ids,unresolved_reasons}，conditional_modules 每项 {module_id,condition}。所有输入是明确合成事实，不能伪造生产 search receipt。expected 是分析预期，实际原产品结果另留报告，二者不可同一函数生成。
4. 必须有：半导体+scaling+cyclical；控股公司多个重要分部；无商业收入的验证项目；银行客户存款；保险承保与投资；地产持有/开发混合；成熟业务与第二曲线；低谷但优势尚存；现金不足且反转证据弱；永久需求被替代；业务份额14%/15%进入和9%/10%保留边界；连续两期退出/切换；概念标签和股价下跌不能触发；来源晚于cutoff；owner 未映射/行业不确定不能硬选。行业必含半导体、工业、电池/汽车、软件/互联网、医药、消费、金融/地产对应现有模块，不虚构新 module_id。
5. 用冻结原 `question_sets.py` 的实际 help 与现有测试样例确定入口。至少跑 `compose --profile <合成profile> --answer-format screening-1 --out-dir <新目录>` 的正常与不适用对照；routing-v2-request/resolve-route/compose-route 若需已有 release/receipt，用源测试的明确 synthetic fixture 在本包复现，不手签真实 receipt。不能调用 publish/activate 源指针。无法离线满足的路径记录 unsupported；不得用本包自造算法冒充生产路由已过。
6. 对照实际 manifest 的原题 ID/题义/hash/替代核心题/顺序/诊断作用层。输出 runtime-observations.json 和 known-product-gaps.json，每例有原命令/退出码/产物hash、预期与实际差异。将改进写 proposals.json：proposal_id、target_ref、expected_old_sha256、counterexample、candidate_change、compatibility_impact、affected_case_ids；提案不改冻结源码。

## 实施与测试

先 RED：多轴被简化单标签、重复题、unknown 强制选行业、低谷丢观察题、阈值边界及旧对象篡改。然后实现候选 schema、薄 CLI `iqs_route_coverage_lab` 与原入口回归驱动。主文件≤4MiB、case≤100、profile 文本有界；覆盖表只核引用与业务约束，不自行决定正式模块。

Unit 检实际模块/题义引用、未知/条件性、日期/份额边界数据；integration 调用本包冻结原入口并校 manifest，不把产物自签为真实；公开 CLI E2E 含坏输入/两次导出/路径与清理。一次稳定候选集中测试+买方适用性审查，原产品失败保留并报告，不为了全绿删 case。

## 完成交接与总控接入

交主case、完整模块覆盖、runtime-observations、proposals、known-product-gaps、schema/工具/测试及共同交接文件到 docs/handoff/ROUTE-COVER-02/。资料覆盖完成与原产品全部满足分开报告；有产品缺陷可完成资料包但不能写路由门已过。总控将这些案例接回 C01 的现有回归和模块发布决策，本包不占 B01 admission/runner 或生产路由源。
