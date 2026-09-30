# W02/W03 可扫描临时身份：缺失字段时的保守路径

状态：只读设计审计，尚未实施；不构成 StockWiki 写入授权，也不把现有 W02 候选导入视为 2,000 家扫描就绪。

身份键、名称别名、ticker/挂牌冲突和 Dayu/StockInfoDLSimple 适配边界的补充设计见[公司身份解析与消歧架构建议](identity-resolution-architecture-2026-09-28.md)。该补充需先同步至 C01/W01/W02/W03 的契约、case 和实现范围，再继续身份存储实现。

## 决策与事实

建议把身份拆成同一 StockWiki `quick_scan` SQLite 中的三个阶段：`source_candidate`（仅可复核）、`provisional`（可执行有限快扫的单证券身份）、`verified`（经发行人核实的公司身份）。它们使用**同一个权威库、同一套不含股票代码或名称的 `ENT_...`/`SEC_...` 稳定内部 ID**。`source_candidate` 仍是 W02 来源行，尚无 Entity；`provisional` 是有明确准入证据的工作实体，不是第二套公司数据库。用户可一次选出约 2,000 个可扫对象，但报告必须分别列明“已核实独立发行人”和“暂按单挂牌计数的临时对象”，不能把两者相加后称为 2,000 家已去重公司。

真实 company-wiki 三地快照（2026-07-19，CN 6,137、HK 2,746、US 6,959 行）不提供注册国家、普适证券类别、交易币种或精确挂牌状态。`active` 布尔值不区分停牌、退市等状态；US 含 iPath ETN，`BATS`/`NYSE ARCA` 等交易所也超出 W01 枚举。来源 `security_id` 实质常是代码；US `source_record_id` 是可能对应多证券的 CIK。因此不能把挂牌市场当注册地，把活跃标志当 `listing_status=active`，把所有来源行当普通股，或以 CIK/名字/代码作跨证券 Entity 合并键。W02 当前提案把不完整行留在 candidate，安全但若不补本路径，W03/一键启动的可扫描覆盖会接近零。

## 准入状态和用户可见含义

| 状态 | 最低证据和动作 | 计数/派发 |
|---|---|---|
| `source_candidate` | 快照行经格式、来源记录 ID、来源 URL/哈希解析；仅建议审核 | 不进入可扫描池、不发 LLM；可用于覆盖/待核报告。 |
| `provisional` + `eligible_provisional` | 唯一证券来源键已绑定；市场、原始交易所、代码、显示名和来源版本明确；**另有正向上市经营主体资格依据**，例如官方明确的 A 股证券类别或用户对这个精确来源键的带时间人工筛选声明；无 ETF/ETN/债券/测试证券反证、无身份冲突 | 可入 W03 工作池，用 `candidate` 成员状态、显式 eligibility 和 reason；只派发以发行人经营为对象且问题要求的身份字段已具备的题。UI 标“临时身份/单证券”，分数只能进入临时观察名单，不自动进入已核实白名单。 |
| `verified` | 法律发行人核实依据、所需国家/类型/交易信息及证券归属完整；跨挂牌桥接有明确官方证据/人工复核 | 可使用 C01 完整 Entity 契约、按 Entity 去重问经营题；每一证券仍独立处理币种与估值。 |
| `blocked`/`superseded` | 正向资格不足、有冲突/反证、或被核实后的身份映射替代 | 不创建新待办；旧记录和观察保留为历史。 |

人工声明只授予**临时快扫许可**，不能把字段/发行人关系升级为“官方已核实”；主题研究的自动提名仍先入候选。若来源明示 ETF、ETN、基金、债券或测试证券，普通人工声明不能覆盖反证，应提供新的权威分类证据并留审计。亏损、低景气、缺行业标签不是身份反证。单一来源键/代码有多种可能时仍 blocked；不能靠模型答案自证身份后立即派发。可自动准入的市场范围必须由版本化规则逐条说明，CN `cninfo_category=A股` 可作为公司股权正向证据；HK/US 快照本身不足以对每行这样断言，应在补充官方分类或人工精确筛选后准入。

`provisional` 的 `incorporation_country`、`security_type`、`currency`、规范交易所、精确 `listing_status` 均可为 `null`；另保存不丢失的原始交易所和 `source_record_id`。`null` 意味着尚未核实，不能写 `CN/HK/US`、`ordinary`、`USD`、`OTHER`、`active` 或 `ZZ` 冒充已知。提问上下文携带市场、交易所原文、代码、来源名称和记录 ID 以消歧；缺字段所依赖的证券估值/ADR 折算任务返回 `unknown`/不适用，不填中性分 5。通用经营题和路由有足够公司证据时可先执行；行业/生命周期模块仍由证据路由，不从市场或名字猜。

供实现者固定的 v2 正例轮廓（示意字段不表示现有 v1 schema 已支持）：`ENT_K7P2` 的 `identity_state="provisional"`、`identity_revision=1`、`incorporation_country=null`；唯一 `SEC_A9D4` 指向它，`market="US"`、`exchange_raw="NYSE ARCA"`、`exchange=null`、`ticker="EXAMPLE"`、`currency=null`、`security_type=null`、`listing_status=null`。只有一份绑定精确来源键、经过人工/官方资格门的 `scope_attestation_id` 才使其 `scan_eligibility="eligible_provisional"`；若该证券是 ETN，即使用户误填声明也应 blocked。实码应由库生成不含 ticker 的 opaque ID，此例代码/名称纯属虚构。

## 精确契约修改（先于 W02 大量 apply 和 W05）

1. `schemas/quick_scan/identity.schema.json`、`docs/implementation/contracts/identity.md`、`tests/test_identity_contract.py`：发布明确的 **v2 身份契约**。保留 v1 的严格 `VerifiedEntity`/`VerifiedSecurity` 语义，新增带 `identity_state=provisional`、`identity_revision>=1` 的分支；其上述未知属性必须为显式 `null`，已知值仍用原校验。临时 Entity 默认恰一证券，只有显式已核实的 issuer bridge 才允许多挂牌；`VerifiedEntity` 必须有已核实属性和跨对象归属语义校验。来源候选不伪装成 Entity。`contract_validation.py` 增加状态与字段、证券归属、唯一来源绑定、发行人桥接和资格证据的跨对象检查。旧无状态记录按兼容入口读取，但不能从有值字段推断已核实。
2. `schemas/quick_scan/work.schema.json`、`docs/implementation/contracts/freshness-and-jobs.md`：WorkItem 绑定 `identity_revision`（或等价身份图指纹）及派发时的来源证券键。身份归属改变时，对受影响的所有字段提高 `generation`；旧租约/晚到回答仍按原身份处理，绝不按新 Entity 悄悄复用。题义、路由及身份修订都参与兼容判定；模型 fallback 不改变身份修订。
3. `schemas/observation.schema.json`、`schemas/quick_scan/exchange.schema.json`：新协议的每条 Observation 不可变地记录派发时 `identity_revision`、`identity_state_at_answer`、来源证券键/绑定版本；交换包声明新身份契约和必需能力。W05 入库校验来源绑定确曾属于该身份及修订；若核实已让身份过时，仍可按原身份接收为**历史不可用于当前筛选**，ACK 保持可重放、费用不重问。缺必需身份字段的新包拒绝；旧包仅走明确 legacy 只读兼容路径。
4. `schemas/quick_scan/query.schema.json`、`docs/implementation/contracts/exchange-and-query.md`：搜索/简表必须返回 `identity_state`、`scan_eligibility`、`identity_revision`、`eligibility_reason_codes`、`superseded_by_entity_id`（可空）和“当前分数是否可用”；每条 ScoreRef 也绑定产生它的 `identity_revision`，避免跨身份版本排序。市场覆盖分别统计候选、临时可扫、核实发行人和疑似跨挂牌重叠。默认评分白名单只纳入 `verified`；若用户显式选“含临时”，结果带清晰标记，不能把覆盖不足说成零结果。主题/行业消费者也须保留这个资格标签。
5. `docs/implementation/tasks.json` 和 `acceptance-cases.json`（由主计划 owner 修改）：把此修订设为 W02 的前置契约修订，给 W03/W04/W05/Q06/C06 增加身份修订与临时资格验收；现有 C01/C04/C06 receipt 应标 superseded 或补兼容回执，不能静默声称旧版本仍覆盖新语义。既有 `ID-01/02/03/05/06`、`UNI-01/02/06` 固定反例继续有效。

## StockWiki SQLite v1→v2 与 W02 关系

W02 尚未实施，宜把这项修订折进它计划中的**一次** v1→v2 迁移，而不是先按严格 v1 添加来源表，等 W03 再做一次破坏性改表。仍只写 W01 所有的 `data/quick_scan/scan.sqlite`；不写 company-wiki，不建正式 StockWiki 研究档。

- 现有 `quick_scan_entity`、`quick_scan_security` 的 NOT NULL/CHECK 不能容纳未知属性。v2 需要在同一权威表增加 `identity_state`/`identity_revision`、允许未知属性为 NULL，必要时重建受外键约束的五张 v1 表；无状态的 v1 行原值逐项复制，标 `legacy_unreviewed` 且新扫描 eligibility 暂停，**不因旧字段非空而假定证据已核实**。`quick_scan_member` 的 `manual_pin`/版本/加入时间逐行不变。只有经证据核实后才从临时升格。
- W02 提议的 snapshot/candidate/source_binding/issuer_bridge 四类表继续保留；补 `quick_scan_scope_attestation`（来源键、资格类型、官方来源或人工操作者、时间、规则版本、撤销事件）及 `quick_scan_identity_event`（revision、旧/新 ID、bridge/证据、影响对象、时间）。证据可只存 URL/记录 ID/短说明，不保存原文文档。`source_binding` 唯一且稳定，不随更名/代码变化重算证券 ID。
- 迁移先核验冻结的 v1 DDL 签名和外键，制作可恢复 SQLite 副本；停写/取得独占锁后，在**单一事务**中重建必要表、复制并比较所有旧行、加 v2 表/约束、验证完整 v2 DDL 签名与 `foreign_key_check`、更新 `user_version=2`，再提交。若为重建需临时关闭 FK，必须仅在迁移专用连接且进入事务前操作，提交前做 `foreign_key_check`，重开连接开启 FK 后复核；任何失败回滚，绝不先提交后验证。生产迁移需单独备份/恢复演练，测试不得操作真实库。
- 扫描准入是 StockWiki 事务性判断而非前端/LLM 自报布尔值。`quick_scan_member.membership_status=candidate` 可以代表临时工作池成员，但 Q06 调度仅纳入具有有效 `eligible_provisional` attestation 的对象；v2 新写入的 `active` 只给已核实身份。迁移保留的旧 `active` 原值仅作历史，不经资格核实不得被调度或计入“已核实公司”。成员状态/资格与人工 pin 相互独立。撤销证据或发现反证后停止新派发，不删旧观察。

## 未来核实与历史观察

单证券更名、换代码若有连续性证据，保留内部 `SEC_...`/`ENT_...` 和旧观察 ID，增来源 binding 的有效期/别名。A/H 或 ADR 是否同一法律发行人必须由明确桥接核实；同名、同品牌、同 CIK 或同 ticker 仅产生 proposed/冲突队列。桥接前两条临时挂牌可能各被扫一次，UI 必须标潜在重复及额外费用；可优先复核疑似 A/H 对以省费用，但不能因相似而共享答案。

若两个已有临时 Entity 最终证实同一发行人，建议创建新的 canonical `ENT_...`（若一方原本已经是 verified，则沿用其 ID），事务内迁入两条稳定 `SEC_...`，将旧 Entity 置为只读 superseded tombstone 并记录 `old→new` 映射、bridge 和受影响名单/工作项。两个旧成员逻辑关闭/转入新成员时，版本审计和任一 `manual_pin` 均保留；有观察、候选集或运行中的任务时尤不可直接删除或覆写。核实后新 Entity 的所有经营字段都进入新 generation；旧 Observation 的实体 ID、答案时间、模型和分数**永不重写**，仅在旧身份的历史时间线展示，并可由新 Entity 的“身份沿革”查看；当前榜单/白名单不自动继承旧分数。晚到的旧 run 回执按旧身份历史入库且不刷新新 Entity；已发请求费用不重复。若桥接关系后被推翻，追加纠错事件和新身份修订，不改历史事件。

## 最小固定反例与真实副本验收

1. 三地快照真实结构的只读副本：CN A 股有正向类别可 provisional；HK/US 缺属性停候选，或由精确人工筛选声明准入；US iPath ETN、ETF/测试证券不得因 `active=true` 或 CIK 存在而入池。原快照哈希/mtime 不变，唯一临时 SQLite 位于 `tmp_path` 且测试结束清理。
2. 少国家、类别、币种、精确挂牌状态及 `BATS`/`NYSE ARCA` 原文：NULL/原值保留，不产生 `US`/`ordinary`/`USD`/`active`/`OTHER` 猜值；通用经营题可计划，依赖缺失属性的证券估值题不得计划或返回 unknown。
3. 同名母子与相同 ticker：两个临时 Entity；同 CIK 两种证券也不自动合并；A/H 两证券在正式桥接前各算 provisional，官方核实后按 Entity 去重，但旧观察仍归旧 ID/identity_revision。ADR 比率未知保持 NULL。
4. 两个旧身份均有模型结果、pin、不同币种、待投递 outbox 和 leased work：桥接迁移后旧 observation hash/ID 完全不变，新当前榜单无旧分数，旧回执只入历史，新 generation 唯一；pin 与成员版本可追溯。名字/ticker 更改但法律身份不变时 ID-05 稳定。
5. fake v1 schema、损坏外键、迁移中断和并发写：v2 不半成；旧五表及成员逐行/哈希不变或整库回滚；未被激活的临时资格不能被直接 SQL/外来包冒充。派发前撤销资格后零付费。

若无法先实现身份修订传递、W05 历史隔离和受控 SQLite 迁移，宁可保持 W02 candidate-only：它能安全导入 15,842 条证券来源，但 **不代表 2,000 家可扫描公司**。一键启动应清楚返回 `identity_review_required`、分市场缺口和补充人工筛选/官方分类的操作，不得用虚构字段凑满数量或暗中启动付费快扫。
