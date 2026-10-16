# OPERATING-CATL-05：CATL 的经营机制与反证资料候选

把本卡、integration-contract.md、interface-spec.md、handoff.template.json、总控发布 inputs.lock.json 和本包 consumers 输入一起交给 harness 即可；不需要另一新包或后续模型结果。唯一可写根 `C:/Users/郑曾波/Projects/iqs-operating-catl-lab`，编卡检查不存在，开工重新检查，不覆盖现有 writer。IQS/所有既有仓均只读。先核共用契约与锁，再在自己根建 Python 包 `iqs_operating_catl`，不创建其他 Lab。

## 对象与范围

用户已同意的 pilot：宁德时代新能源科技股份有限公司，company_key=`catl`，300750/XSHE，以冻结 StockWiki DTO 的 entity/security 为唯一身份 authority，原 identity_state=provisional 保留，不升级 formal，不自行添 H 股或改主证券。真实 DTO 与题包绑定不符就拒绝，不靠名称/ticker 猜。

研究资料截止 `2026-10-13`。冻结原 formal-routes 题包真实日期为 `2026-10-11`，保留原字节/题号/锚点/30题结构，不改题面。资料包分别记录 research_as_of/base_question_as_of、来源两种 eligibility；12–13日资料可单列研究候选，但不能喂进原11日题上下文。实际新13日题/生成模型准入由总控另登记。本包只按原题义映射经营资料，OPERATING_01 不可用 IQS_11 改名冒充。

输入别名：`identity/catl.json`、`questions/catl/{manifest.json,questions.json}`、`financial/parent/{reference-pack.json,calculation-ledger.json}`、`financial/catl/{reference-pack.json,calculation-ledger.json}`、`financial/parent/schemas/`、`rules/`。精确原路径/hash 见发出的锁；父包1.2.0及子包1.1.0均只读候选，保留 needs_revision/partial/全分数null，不能称金融 gold。父/子矛盾在 gaps 报告，不能临时合并重写。只引用既有 financial reference_id/fact_id，不重新计算毛利率、ROIC、现金流、资本开支或重新补全其标量。

## 要完成什么

交有界、逐命题、可核来源的经营机制参考资料及离线校验/覆盖工具。重点材料域（不是必须得到肯定答案）：

1. 动力电池与储能的真实客户价值：安全/循环/补能/全生命周期使用边界，技术发布参数与客户实际使用结果分开；不能把厂商实验条件当全场景 ROI。
2. 收入延续机制：车型/平台定点→验证→量产→采购/交付→收入，框架协议/产能预订/客户意向与有约束订单分层，车型生命周期/价格重谈/取消条件；定点不等于续约率或保证收入。
3. 工程与交付约束：制造良率/质量追溯、客户认证、供应材料/技术路线、海外建设/许可/产能爬坡、储能系统交付和并网边界；公告产能不等于已可用/已售产量。
4. 竞争与侵蚀：LFP/三元/钠离子/固态路线的已证阶段、客户自研/多供/替换、价格与原材料传导、专利和标准真实范围；不得用“技术领先”自述替代迁移成本证据。
5. 可核管理承诺/实际落地与反证：选不超过5条截止日前可查承诺，标 deadline、deliverable、已证阶段/未兑现；时间晚于截止的结果禁用。区分行业逆风、公司事件与尚无证据。

先读原题拆 dimension，给每维 existing_financial_refs/needed_observation，再做有界公开 HTML 核源。优先公司技术/产品/客户合作页、监管/交易所 HTML、官方客户行为与项目许可/投运页面。公司/客户合作稿同一原稿一个 origin_group，不伪装多独立来源。每项结论写 business_scope/period、事实vs公司自述vs推断、来源日期证明、限制、反证、falsifier及unknown；找不到复购、维护成本、客户经济回报或合同条款就诚实 gap。主观评分没有唯一1–10答案，LLM自述不是真值，不产生 score 或评分区间。

新增来源上限25、主动查询20、打开40（共用契约为硬上限）。不下载财报/PDF/全文HTML，不调用 filing-fetch/付费 API/LLM，不建新搜索客户端。人工核源记录与离线测试分开；访问失败、不确定日期、未来/动态内容都保留不合格状态。不得为满足“至少一条机制”编造。资料为空但完整 gap/失败审计仍可交候选。

## 必须交的接口与 CLI

公开签名（纯函数不联网）：

```python
def validate_reference(document: dict, *, identity_dto: dict, questions: list,
                       question_manifest: dict, financial_pack: dict,
                       calculation_ledger: dict, expected_context: dict) -> dict: ...
def coverage(*, reference: dict, questions: list, financial_pack: dict,
             expected_context: dict) -> dict: ...
def export_bundle(*, reference: dict, coverage_report: dict, output_root: str) -> dict: ...
```

落实 interface-spec 的 `iqs.operating-reference/1.0.0`、`iqs.operating-coverage/1.0.0` 两份闭合 schema；package1.0.0。校验只证明身份/时点/引用/结构和人工映射一致，不宣称程序自动验证网页真实性。expected_context 必须来自 CLI 从锁中选择的可信本公司绑定，不能接受误传 board 自证。

在本 Lab 运行，`$snapshot` 由调用者传入完整输入根，不依赖 cwd 猜：

```powershell
python -B -X utf8 -m iqs_operating_catl --version
python -B -X utf8 -m iqs_operating_catl validate --inputs $snapshot --lock $lock --reference data/operating-reference.json
python -B -X utf8 -m iqs_operating_catl coverage --inputs $snapshot --lock $lock --reference data/operating-reference.json --output .test-work/run-01/coverage
python -B -X utf8 -m iqs_operating_catl export --inputs $snapshot --lock $lock --reference data/operating-reference.json --output .test-work/run-01/export
```

`validate` stdout 是有错误/警告分层的机器 JSON，非法文档仍非零；成功不授予资格。coverage/export 输出原件引用、before/after完整维度、剩余gap、来源独立性限制、双 cutoff 与 hash，不改原财务 pack 或创建标准模型答案。既有输出拒绝覆盖。

## 必须执行的验收

- 单元：换 CSC 身份/同名公司/错 security、provisional被升formal、12日材料进11日题、14日材料、未知日期伪成访问日期、镜像同稿双独立、公司参数→客户ROI、框架合作→锁定收入、产能→销量、partial→充分、无来源 claim、悬空反证、非有限数/重复键/hash错误/外跳/未知版本等均有失败或明确不合格反例。
- 集成：冻结真实 CATL 题/身份/财务父子包跑全链，原 hash 全部保持；所有原题维度保留，即使纯财务维度本包不补也列 out_of_scope/原参考限制。至少展示一条实际来源命题的可追溯链，若无法取得则实证 gap；不能用合成源满足真实核源要求。对照 before/after，新增技术新闻不能自动覆盖留存/ROIC维度。
- CLI E2E：全新根 validate→coverage→export，搬迁同输入内容摘要一致；缺文件/篡改/错误公司/已存在输出/未来日期均非零且不产生合格bundle。禁网测试测出网络请求0、外根写0；人工核源单独如实报告未知费用。
- 整包审查：源码/schema/实际材料/限制及反证/源日期/原件保持/清理/CLI一致性集中一次。留关键 RED 和最终单元+集成+E2E 真实日志，不逐 helper 立门。只在自己根修复普通缺陷。

最终按共同 handoff 模板交 `docs/handoff/OPERATING-CATL-05/` 并正常提交：报告有来源/claims/gaps计数、每题剩余边界、查询/访问记录、未知费用、API调用0、测试与清理。`production_ready=false`、`financial_qualification_granted=false`、`rating_gold=false`。不写主线 PWF、不改 StockWiki/名单/生产 owner，不派发他包。
