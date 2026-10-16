# OPERATING-CSC-05：中信建投的经营机制、周期与反证资料候选

把本卡、integration-contract.md、interface-spec.md、handoff.template.json、总控发布 inputs.lock.json 与本包完整 consumers 子集交给 harness 即可独立施工；不依赖 CATL 或桌面包。唯一可写根 `C:/Users/郑曾波/Projects/iqs-operating-csc-lab`，编卡检查不存在，开工再次核无未知源码/writer；其余仓与总控 PWF 全只读。

## 对象、时间与有限参考

用户已同意 pilot **中信建投证券股份有限公司**，company_key=`cncb_h`，06066/XHKG，冻结真实 StockWiki entity=`ENT_1af6804e-40c1-4c35-b190-ea691dba2c85`，security 以锁内 DTO 为准。原 identity_state=provisional 不升级。A股601066与H股06066描述同一发行人；业务资料可属于同公司，但不把它们当两家公司、两份独立公司证据或两套集团营收。严禁与**中信证券**/CITIC Securities/600030/06030混淆。A/H价格、币种、每股口径不能互换，不新增/改身份库证券映射。业务名称含“中信”不是身份支持；拿不到 issuer 归属的材料列 identity_unresolved。

研究固定 cutoff=`2026-10-13`；真实原30题 formal-routes/as_of=`2026-10-11` 保持。两种 cutoff 单独登记，12–13日资料不能进入原11日题上下文，14日以后不能进入本研究合格范围。不改题面/题号/锚点，不把OPERATING_01改名接旧IQS_11。

输入别名：`identity/cncb_h.json`、`questions/cncb_h/{manifest.json,questions.json}`、`financial/parent/{reference-pack.json,calculation-ledger.json}`、`financial/cncb_h/{reference-pack.json,calculation-ledger.json,parent-scope-quarantine.json}`、`financial/parent/schemas/`、`rules/`。锁内父pack1.2.0与子pack1.1.0是已工程接收的 partial 资料候选，保留needs_revision/全分数null；父包恢复的母公司事实仍不等于集团值，不靠读入schema变成金融gold。子包quarantine是边界诊断，不将其直接并入新事实。已有财务标量/账本只引用 reference_id/fact_id，不重算净资本、ROE、FCF、分红或母/集团桥，不另建财务标准答案。

## 实施范围

交按原题义拆维度的经营机制/可核行为/反证/未知，优先覆盖：

1. 投行获客与履约：发行/保荐/承销角色、在审/注册/发行/收费确认阶段、撤回/终止/监管审查边界。项目储备和排名不能证明保证收入，单项目不能推全公司稳定份额。
2. 经纪/财富：交易佣金与市场活跃的依赖、投顾/代销/客户资产服务边界，客户行为证据和营销自述分开；AUM/客户数/成交量增长不能冒充留存或不加获客成本的收入延续。
3. 资管/机构服务：受托规模、产品期限/赎回/费率、托管/做市/研究等角色与同公司子公司/母公司/集团scope；不能将产品规模、资产负债表投资资产和营业收入互代。
4. 资本与风险机制：融资融券/自营/信用敞口、流动性约束/净资本监管如何影响业务边界，仅引用既有数值；不按工业公司通用“OCF减capex=可分配现金”解释券商，不将有息负债一律视经营恶化。
5. 竞争与执行：客户关系/牌照/承销能力可替代与周期侵蚀机制、可查业务承诺与实现阶段、监管处罚/纠正措施真实对象/最终性/日期；立案/监管问询/处罚/生效裁决分层，不能把指控当已证实罪责。优先包含相反信息，找不到则写反证待核。

每维列 required_proposition、原参考边界、新 claim、出处、source date依据、support范围、limits/falsifier/unknown和未补缺口。机制写出交易/客户行为→限制条件→收费/风险影响，不靠行业常识或模型自述当真值。原题评分主观，无唯一1–10金标准，本包不产score/区间/模型预期答案。公司新闻/董事长讲话保留 company_statement；券商行业总量不自动支持本公司，市场份额仅某明确期间口径可用。

只用 harness 已有浏览/搜索核公开HTML；官方公司/交易所/证监与行业监管/项目发行人官方客户资料优先，第三方转载仅候选/gap。最多20主动检索/25新来源/40次打开，不下载PDF/财报/全文HTML、不调用filing-fetch/LLM/收费搜索key、不写搜索客户端。source未知/日期不明/公司不明/访问失败不能编造片段；有界paraphrase、同原稿origin_group和工具费用unknown按共同契约。找不到留存/合同费率/维护成本等属于交付gap。

## 公开接口

Python模块 `iqs_operating_csc`，package1.0.0，实现本包自己的 schema，不导入另一经营新包：`iqs.operating-reference/1.0.0` 与 `iqs.operating-coverage/1.0.0`，字段完整遵循 interface-spec。

```python
def validate_reference(document: dict, *, identity_dto: dict, questions: list,
                       question_manifest: dict, financial_pack: dict,
                       calculation_ledger: dict, expected_context: dict) -> dict: ...
def coverage(*, reference: dict, questions: list, financial_pack: dict,
             expected_context: dict) -> dict: ...
def export_bundle(*, reference: dict, coverage_report: dict, output_root: str) -> dict: ...
```

调用方从已验锁本公司binding取expected，不从误传输入重算expected自证；校验器不宣称判断网页语义真伪或授予身份资格。validate/coverage/export 默认离线，原财务引用和原件不改。

```powershell
python -B -X utf8 -m iqs_operating_csc --version
python -B -X utf8 -m iqs_operating_csc validate --inputs $snapshot --lock $lock --reference data/operating-reference.json
python -B -X utf8 -m iqs_operating_csc coverage --inputs $snapshot --lock $lock --reference data/operating-reference.json --output .test-work/run-01/coverage
python -B -X utf8 -m iqs_operating_csc export --inputs $snapshot --lock $lock --reference data/operating-reference.json --output .test-work/run-01/export
```

stdout单一JSON，输入不合格exit2、输出存在/路径冲突exit3、不支持版本exit4；全新输出原子发布。输出有原引用/raw hash/canonical hash、完整before/after维度、双cutoff/gaps，无分数、accuracy或winner。

## 必须执行的验收

- 单元：中信证券错主体、同名子公司冒集团、A/H两公司重复计数、HKD价格当CNY价格、母公司资产当集团值、集团事实错挂上市证券、营销自述当独立证明、在审当发行收费、AUM当收入/留存、行业排名当保证收入、监管提案当生效处分、券商OCF套工业FCF、未来/日期未知/跨11与13日、同稿多源、partial充分、悬空引用/重复键/NaN/篡改/路径越界，均有实质反例。
- 集成：实际冻结CSC身份+30题+财务父子包及quarantine跑完整链，保持全部原bytes；原题所有维度在报告，纯财务未补维度按边界留gap。真实来源能否支持一条机制如实展示，若无则完整失败记录与gap；不以合成来源充真实。before/after不能因同公司A/H重复而增独立源数，母公司有限材料不升级集团。
- CLI E2E：validate→coverage→export及搬迁复算，缺输入/改hash/跨公司/已存在输出/未来材料拒绝；测试禁网、无key、外根写0，人工核源单独记录费用unknown。清自己测试根/进程/端口，原件保持实测。
- 一个整包审查节点：接口/schema/实际来源与日期/财务边界/缺口/反证/测试及清理集中核对；普通问题直接修并跑受影响检查，不逐helper门。

最终 `docs/handoff/OPERATING-CSC-05/` 按统一模板，report有准确来源/claim/gap/查询次数、A/H与中信证券负例、全部未关闭边界、实际单元/集成/E2E日志。正常payload+handoff提交，无push/remote。资格固定false；不修改生产名单、StockWiki、预算、主线题包或PWF。
