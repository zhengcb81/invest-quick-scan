# 公司身份解析与消歧架构建议

日期：2026-09-28
状态：身份设计已同步到本仓 C01 v2.2 契约与验收计划；StockWiki权威存储、来源注册表及W02/W03运行时接线仍待实现，正式当前receipt仍待重验。
范围：快扫对象识别、来源候选归并、证券挂牌映射、跨市场同一发行人判定。轻资产约束继续有效：不下载或保存财报/网页文档。

## 1. 核心结论

**名称和 ticker 都不是公司的主键。** 两者只用于检索候选或定位挂牌；名字会变、重复、翻译或简称化，ticker 会在不同交易所重复、改名、退市后复用。系统应生成不含名称、ticker、市场的不可变内部 ID，并把所有外部编号、名称、证券代码作为有来源、有时间、有核实状态的可变声明保存。

扫描身份的法律底座是“发行人（issuer）”，但公司经营问题的实际扫描范围必须是单独的 `AnalysisSubject`，以记录独立报告主体或经核实的并表范围；二者不能混为一个 ID。母公司、上市子公司和同集团公司保持独立 issuer；可另以带类型的关系连接，例如 `parent_of`、`controlled_by`、`associate_of`。一个 issuer 可发行不同证券类别；同一证券也可能在多个交易场所挂牌，因此数据模型必须将发行人、证券工具、交易挂牌三层分开。只有 `AnalysisSubject` 的权威并表范围回执确认后，A/H 股或普通股/ADR的经营画像才可共享；证券级价格、币种、挂牌状态和估值仍按具体证券/挂牌分别处理。暂定单挂牌主体只可组成一个精确Listing锚定的provisional subject。

## 2. 身份层级与稳定键

| 层 | 标识 | 语义 | 不能替代什么 |
|---|---|---|---|
| 来源候选 | `candidate_id` | 某来源某版本的一条原始证券/公司记录，待解析 | 不是公司，也不自动可扫描 |
| 发行人 | `entity_id` | 被覆盖的法律发行人/上市经营主体，系统生成的 opaque UUIDv4 | 不能由名称或代码计算 |
| 可交易证券 | `security_id` | 发行人发行的股份类别、债券或 ADR 等证券工具，系统生成的 opaque UUIDv4 | 不是公司主键；不含会变的 ticker |
| 交易挂牌 | `listing_id` | 某证券在某交易场所用某代码交易的记录，系统生成的 opaque UUIDv4 | 裸 ticker 不是唯一挂牌键 |
| 名称/标识声明 | claim/alias ID | 一个外部名称、法律编号、来源编号或代码映射及其证据 | 除登记为强唯一的核实法律标识外，不自动唯一 |

**三层是目标契约的必需语义，不延期到未来版本。** `Entity` 表示 issuer，`Security` 表示股份类别/证券工具，`Listing` 表示 venue 上的可交易代码。历史兼容输入可由 adapter 把旧的 `entity+exchange+ticker` 记录提升成单一 `Security+Listing`，但不得把两种身份压在新写入的 `Security` 字段中。A/H 股是同一 issuer 下不同 `Security`；若同一类别证券在两地挂牌，则可由两个 `Listing` 指向同一 `Security`；ADR 是独立 `Security` 并以显式关系指向基础证券。所有三类内部 ID 均不含名称、ticker 或市场且不因更名/改码而改变。

建议主表字段：

- `quick_scan_entity`: `entity_id`、`canonical_legal_name`（可空/待核）、`display_name`、`identity_status`、`identity_revision`、`incorporation_jurisdiction`（未知则 null）。内部 ID 由权威库随机生成并永不复用。
- `quick_scan_security`: `security_id`、issuer 归属、证券类别/工具类型、ISIN（如有，按 claim 规则核验）、ADR/underlying 等显式证券关系。
- `quick_scan_listing`: `listing_id`、`security_id`、市场、原始交易所、规范 MIC（未知可空）、原始及规范代码、挂牌/退市状态、报价币种和有效期。交易所/代码变更写历史事件，不据此重算内部 ID。
- `quick_scan_identifier_claim`: `(scheme, assigning_authority, jurisdiction, normalized_value)`、issuer/security 作用层、状态、有效时间、来源记录、证据 URL/引用、核验人或规则版本、核验时间。仅经证实且该 scheme 的唯一性规则允许时施加部分唯一约束。
- `quick_scan_name_alias`: 名称、语言/地区、类型（法定全名、曾用名、交易简称、品牌名、英文名、音译等）、有效时间、来源及核实状态。名称允许多对多，索引供召回，不设全局唯一约束。
- `quick_scan_source_binding` / `quick_scan_identity_event`: 保存来源行到挂牌/发行人的精确映射、身份修订、合并/拆分/纠错事件与影响对象。事件追加，历史不覆盖。
- C01 v2.1 为实体关系和身份事件增加严格契约：关系表达母子/控制/同集团等经济关系，禁止将 `same_issuer` 当成关系类型；事件显式绑定前后修订、有效/记录时间、影响证券/挂牌、来源和证据，每个身份事件恰好递增一个修订。StockWiki 权威存储负责追加唯一事件、冲突事务和禁止旧事件覆写。

## 3. 唯一性与匹配证据等级

1. **精确挂牌键**：`交易场所标识（优先 MIC） + 规范本地代码 + 有效时间` 唯一定位一项挂牌；必要时以工具/报价板块作 venue 内部限定。只有市场、不含交易所的代码不够；如上游没有 MIC，保留交易所原文并将标准 venue 映射标为 unknown/待核。代码复用必须由有效期和挂牌历史区分。挂牌再经 `listing -> security -> issuer` 关系定位证券与发行人。
2. **强发行人标识**：按命名空间保存司法辖区/分配机构，例如 LEI、SEC CIK、中国统一社会信用代码、香港公司注册编号、交易所/监管机构发行人编号。每种编号单独规定作用范围和唯一性；匹配前核实该编号指向的是法律发行人而非集团、申报主体或来源集合。冲突时进人工复核，不以“数字相同”自动合并。
3. **来源内编号**：CNINFO `orgId`、company-wiki 行 ID、供应商自己的 company code 等只能在各自 `namespace` 中定位记录。它们可提供可信 crosswalk，但不能跨来源当作全球 company ID。
4. **名称与别名**：规范化大小写、全半角、空格和常见公司后缀只用于召回。中文简称、翻译名、拼音、品牌、网站域名和模糊相似度均只生成候选；不能自动建立发行人等价关系。
5. **上市代码**：`ticker_to_company_id` 一类由 ticker 生成的 key 只适合作为某数据产品的局部键。裸 ticker、`市场+ticker` 或同一集团代码前缀均不能成为本系统永久公司 ID。
6. **跨挂牌桥接**：需要官方/监管发行人资料、明确法律登记映射或人工复核的可追溯证据。LLM 可搜索、摘录、解释并建议候选，但不能签发 `verified`、不能自行建立桥接，也不能用自己的回答证明身份。

每个编号 scheme 应在版本化登记表中说明：签发者、作用层、作用辖区、规范化算法、理论唯一性、允许一对多的例外、过期/重用规则以及可接受的证据类型。未经登记的未知编号只能作为 source-local claim 保存。

## 4. 确定性解析流程与状态机

导入只建立来源候选和解析结果，不直接由 LLM 或 UI 拼装正式 Entity。对每条输入按以下顺序处理：

1. **保真解析**：保存原始文本、来源 namespace/record ID/版本、原名称、原市场/交易所/代码；不先去掉可能具有含义的前缀/后缀。
2. **定位证券**：若存在精确交易所限定代码，先查找或建立挂牌候选；ticker 命中的是证券，不是公司。缺交易所、代码形态多解或来源记录指向多个证券时不得猜。
3. **定位发行人**：先查已核实 issuer identifier / 官方 source crosswalk；再查已核实 alias 与挂牌桥接。只有唯一、无冲突且证据仍有效的映射能自动附着到既有 issuer。
4. **生成名称候选**：名称相似度只返回 top-k 候选及原因（市场、辖区、曾用名、官方编号差异、母子/集团关系等）。候选结果不得触发归并或付费扫描。
5. **落到一个明确状态**：

| 解析状态 | 条件 | 快扫行为 |
|---|---|---|
| `unresolved` | 只有名称、缺必要交易场所，或多个可能对象 | 作为待处理候选保留；无 `entity_id`、不入扫描队列、不出正式分数 |
| `provisional` | 一个精确来源挂牌已识别；满足现有正向上市主体准入回执；尚无足够证据作跨市场/法人级核实 | 建单证券临时 issuer；只扫准入的发行人级题；显示临时/可能重复标记，不进入 verified 白名单 |
| `verified` | issuer 法律身份和每个关联挂牌均有足够权威映射，无未解决冲突 | 经营题按 issuer 共享；证券题按 security/listing 分开 |
| `conflicted` | 强编号互相冲突、一个挂牌被多 issuer 声称、来源映射变更未核实 | 暂停新派发；保留成员和旧观察供人工裁决 |
| `superseded` | 已通过审计事件合并、拆分或纠正为更新身份 | 旧 ID 只读；新任务按新身份修订生成，不继承旧分数 |

`identity_status` 与 `scan_eligibility` 分字段保存。存在 Entity 不等于可扫描；名字命中也不等于有 Entity。用户可对**精确 source key/listing key**作有记录的临时纳入/排除，但手工纳入只授予既定的 provisional 范围，不能覆盖 ETF/ETN/债券等反证，不能证明公司法律身份。

## 5. 典型边界处理

- **“中微公司”与“中微半导体”**：把每个名称各自查成候选 alias；在它们没有相同的已核实发行人标识或权威桥接前保持两个候选/对象，不因共享“中微”字符串而合并。若官方资料确认其中一个是另一个曾用名，则同一 issuer 下加带有效期的 alias；若是母子公司或不同法人，则保留两个 `entity_id`，另记录 `parent_of` 等关系。本设计不预判这两个具体名称的现实法律关系。
- **A/H 两地上市**：两个交易所限定挂牌各有独立 security/listing ID。只有经权威证据确认同一法律发行人后，共享 issuer 经营问卷；A/H 证券的价格、币种和折溢价仍分开。
- **ADR**：ADR 是不同交易证券工具，单独建 security/listing，按证据连到发行人和 underlying 普通证券；比率未知保留 null。ADR ticker 不成为第二个公司 ID。
- **母子同品牌**：issuer 不合并，组织关系另存。集团品牌、共同控制人、地址、域名、业务描述均不是同一法律发行人的充分证据。
- **更名/改代码/退市后代码复用**：内部 ID 不变；以 identity revision 与有效时间追加名称/代码变化。若代码被新发行人复用，建立新 listing ID 和 issuer，不覆盖旧记录。
- **名称-only 行**：不造虚构代码、不自动归到最相似公司；留在候选池待用户补充市场/交易所/ticker/法律编号，或由用户确认一个具体候选。

## 6. 对 Dayu 与 StockInfoDLSimple 的只读核查

- Dayu 的 `dayu/fins/ticker_normalization.py` 将多种代码格式规范为 ticker、market、exchange；这是有用的证券输入规范化。其 `ticker_to_company_id()` 当前返回 `ticker + exchange/market`，源码注释明确将跨市场折叠、CIK、统一社会信用代码留给后续更精细的主体映射。因此不能把该结果作为全球发行人主键。
- StockInfoDLSimple 的 `standardize_stock_code()` 只把代码规整为六位数字；`MappingManager` 用代码查 `orgId`，并以 CNINFO/浏览器查找补映射。它适用于 A 股资料获取和来源内 crosswalk，不覆盖 HK/US，也没有跨市场发行人消歧语义。
- 因此只复用它们的**市场代码规范化与来源内查找适配器**；把返回值写入各自 namespace claim，再由本系统 issuer resolution 决策。两者的现成 `company_id`、`orgId` 均不直接复制成快扫 `entity_id`。

## 7. 轻资产数据与审计要求

只保存必要的结构化身份声明和审计指针：原始输入、规范化值、来源/记录 ID、官方 URL 或 filing identifier、查询/核验时间、最短必要理由、核验人/解析器版本、前后状态和身份 revision。不得保存完整财报、网页、搜索结果正文、模型隐藏推理或 API key。若证据链接失效或来源变更，状态可降为 `needs_review/conflicted`，不可通过刷新当前名称静默改写过去映射。

所有 `WorkItem` 和 `Observation` 固定记录派发时 `entity_id`、`identity_revision`、来源绑定/挂牌键、identity/eligibility 状态和模型/时间元数据。后续桥接不能修改旧观察的身份或时间；新 issuer 可沿身份谱系查看旧对象，但当前排序不继承其分数。

## 8. 必须加入的测试矩阵

1. 别名与相似名：全名/简称/中英文名指向同 issuer 只有官方 alias claim 时才归一；“中微公司/中微半导体”、同品牌母子、同名异国测试必须保持独立或 `unresolved`。
2. 证券键碰撞：同裸 ticker 不同 MIC、同 ticker 不同股份类别、ticker 改名、退市后复用、缺 exchange 的港股/美股输入；只能精确找到 listing 或停在待审。
3. 外部 ID 规则：完全相同且已核验的法律编号可链接；source-local `orgId` 跨 namespace、同 CIK 但不明申报主体、冲突法律编号均不得自动合并；唯一约束和多对一冲突事务回滚。
4. 跨市场/ADR：未桥接 A/H 和普通股/ADR 保持 provisional 独立；权威桥接后经营题去重、证券估值仍独立；ADR 比率未知不猜。
5. 状态/队列：名称-only 不生成 Entity/Work/Observation；`conflicted` 零派发；LLM 候选建议不能直接改变状态；人工 exact-key override 有审计但不能消除反证。
6. 历史：更名、ticker 变更、issuer merge/split 均产生 revision/event；旧 observation 的 JSON、身份、模型、时间、分数哈希不变；新白名单必须用新扫描。
7. 真实副本 E2E：用只读的真实 source snapshot 子集加隔离临时 SQLite，覆盖 A/H、HK/US、相似简称及 source-local ID；验证原始文件 hash 不变、测试 DB/临时文件清理、没有真实模型/网络请求。单独的真实搜索验收只验证证据采集，不授予自动 merge。

## 9. 后续任务顺序与实现门

### 契约演进

当前本地 C01 v2.0.0 把市场、交易所、ticker、币种和挂牌状态放在 `Security` 里。新写入应发布 **identity schema 2.1.0**：`EntityV21` (issuer) 下挂 `SecurityV21` (工具/股份类别) 与 `ListingV21` (venue+ticker+报价属性)。v2.0.0 只作为历史读取分支；兼容 reader 可将每条旧 Security 投影为一项 legacy 单挂牌，但不得把投影结果升级成已核实 issuer，也不能覆盖来源缺失的 claim。身份 revision、source binding、scope/issuer receipt 必须明确绑定 listing IDs 和其属性。不能让组件仅凭相同 semver 接收不兼容的 schema/hash。

需要同步更新 C01 的 Schema、验证器、文档和用例，并将 C01 既有完成回执标为受新语义影响/待重验；不得伪造新版本的旧验收证据。StockWiki 当前独立 quick_scan 库仍无真实用户数据，W01 可按一次事务直接建目标 DDL，不需要为已部署公司行做不必要的破坏式回填；如果发现非空旧库，则先只读盘点、备份和演练，不自动迁移真实库。

### 依赖顺序

1. 在本地 C01 合同与任务图中冻结 opaque issuer ID、namespaced identifier claim、非唯一 alias claim、candidate 状态、Security/Listing 两层及旧版读取语义；更新 case owner、测试闭包和所有 `security_id`/`listing_id` 作用范围。
2. 在 StockWiki 唯一权威库中完成 `candidate -> listing -> security -> issuer claim` 事务与全库冲突检查；`save_entity()` 只能持久化权威实体，不能进行名称匹配。用隔离测试覆盖候选、精确挂牌、强 ID、冲突、修订重放与临时根清理。
3. 将 Dayu/StockInfoDLSimple/company-wiki 只接成只读来源适配器；每个源标明 namespace、source-record ID、resolver version。复用 Dayu 的 ticker 归一化和 StockInfo 的 CNINFO 映射时保留各自来源命名空间。若后续需改这些仓库，另行明确审批。
4. W02/W03 只让唯一精确挂牌或有效 issuer claim 进入 provisional/verified；名字-only 和 conflicted 保留候选、不建 Work。W04/Q06 派发前重新检查身份状态和 eligibility。query/UI 暴露状态、匹配原因、强冲突、候选列表和人工处置入口。
5. W05/W08 将 `entity_id + identity_revision + security_id + listing_id + source_binding_ref` 固定进 exchange、Observation、历史及比较逻辑。最终 isolated E2E 验证不同模型、跨市场、身份更新和轻资产边界。

### 计划验收补充

把以下反例分配给 C01 contract、W01 store、W02 resolver、W03 identity maintenance、W04 eligibility、W05 exchange/observation 的唯一 case owner；后续消费者仅通过依赖闭包做回归，不重复拥有同一 oracle：

- 相似中文简称/全名（包括“中微公司 / 中微半导体”测试夹具）、同品牌母子和同名异辖区不会因字符串相似而合并；LLM 命中的网页结果只生成有来源的候选。
- 同 ticker 不同 MIC/辖区/有效区间能分开定位；缺交易所的裸 ticker 有多个候选时停在 unresolved；改名、ticker 更改和代码复用不改变/复用 issuer ID。
- 同一 source-local `orgId` 跨 namespace 不合并；同一已核实且适用该编号方案的法律 issuer claim 能链接多个证券；强 claim 冲突时事务失败并阻断新派发。
- 名称-only 无 Entity/Work/Observation；Provisional 仍只按精确单挂牌资格受限快扫；经核实 A/H issuer 共享经营题但不同 security/listing 分开估值；ADR 是独立 security，并且基础证券/比例缺证据时保持 unknown。
- 同一证券两个 venue 有两个 Listing；A/H 不同 share class 有两个 Security；母子不同 Entity 通过 group relation 表达，不把 group relation 当 issuer equivalence。
- Merge/split/更名事件递增身份修订并保留 old-to-new 线索；历史答案 JSON/hash/原 issuer/listing/model/time/score 不变；新身份从新 generation 开始且不继承旧评分。
- 真实源快照只用只读 fixture 子集、SQLite 仅用隔离临时根；核对源 hash 未变、网络/LLM调用次数为零、所有临时库和下载目录结束后清理。

在以上设计同步到任务清单、schema 和验收场景之前，不应继续把目前只有 `entity/security/source_binding/member` 四类对象的 StockWiki W01 表视作身份解析完成。W01 当前几个数据完整性缺陷仍需先修；这些身份扩展也不可用“名字相似就复用 ID”绕过。

## 10. C01 v2.2合同补充与下一步信任边界（2026-09-28）

本文件前述“扫描对象为issuer”的表述仅适用于法律身份解析层。**快速扫描对象是 `AnalysisSubject`**：它可以是一个发行人独立报表范围，或经证据确认的并表成员范围。主体拥有不透明 `analysis_subject_id` 和单调递增的 `analysis_subject_revision`；每次快扫/Observation都要绑定确切的主体修订。证券交易问题继续额外绑定 `security_id` / `listing_id`。历史Observation不得在主体改版后静默补绑或重新解释。

并表不得由集团关系、控制关系、verified issuer标志、网页链接本身或LLM回答推导。StockWiki owner事务必须保存owner-controlled perimeter receipt，键合确切subject ID/revision、主发行人、完整成员与角色/有效期、来源及规范化snapshot digest；本地C01验证器只校验调用方提供的已信任receipt与snapshot一致，不负责认证receipt签发人或证明资料库完整。primary issuer变更事件仅可让旧主/新主的primary角色互换；其他成员变更必须由独立范围事件表达。所有事件按前后快照检查准确变化和受影响issuer IDs。

市场辖区和MIC采用owner维护、版本化的受控注册表。ISO字母格式只是一项词法检查；两字母代码有效不等于它是实际市场。校验器需要显式注入`market -> MIC set`注册表，缺省、未知代码、未知MIC或辖区不匹配都拒绝新写。W02/W03后续必须完成权威资料来源、版本/更新/撤销策略、来源绑定唯一约束和SQLite事务CAS；向validator传入某个Python mapping本身并不能证明官方真实性或全球完整性。

当前本仓实现仅闭合schema、语义校验器、文档和离线契约回归。独立复审的最后负例（事件快照引用外部issuer拥有的Security）已加为永久测试；身份/依赖批次为170 passed / 160 subtests，focused identity 36 passed / 50 subtests。C01正式receipt与P01依赖链仍因历史计划/任务/场景/边界hash、证据闭包和审查快照陈旧而未通过公开验证。跨仓resolver、权威信任根和consumer的实现不能从这些局部测试推定为已完成；后续实施应以当前`docs/implementation/contracts/identity.md`、I55及Phase 40为准，旧第9节只保留为架构演化记录。
