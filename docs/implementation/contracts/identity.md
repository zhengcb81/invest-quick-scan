# 公司、证券、分部与名单身份契约规范（Task C01）

**契约包版本**：2.2.0（发行人 Entity 写入格式仍为 2.1.0；新增独立 `AnalysisSubject` 1.0.0；v1/v2.0.0 仍为历史只读格式；跨仓运行时尚未接入）
**任务编号**：C01（Stage M0，Owner: `iqs`）  
**关联约束**：I03, I04, I16, I18  
**验收场景**：ID-01, ID-02, ID-03, ID-04, UNI-04  
**Schema 定义**：[`schemas/quick_scan/identity.schema.json`](file:///C:/Users/郑曾波/Projects/invest-quick-scan/schemas/quick_scan/identity.schema.json)  

---

## 一、 核心概念与分层原则（I04）

### v2.1 发行人身份准入边界与稳定键（2026-09-28）

现有 company-wiki 证券主档快照缺少法人注册国、普适证券类别、交易币种和精确挂牌状态，不能以挂牌市场推断注册国，也不能把 `active=true` 直接当成正式 `listing_status=active`。美股来源含 ETN，部分原始交易所不在旧枚举内。Entity 格式 v2.1 定义两个**新写入**的发行人状态分支：

| 身份状态 | 必需字段 | 容许未知 | 快扫边界 |
|---|---|---|---|
| `provisional` | `identity_schema_version=2.1.0`、`identity_revision>=1`、一个 issuer、一个 Security、一个 Listing、权威库内 `scope_attestation_id` 和精确 source binding | 注册国、规范交易所 MIC、币种、证券类别、股份类别、挂牌状态可显式为 `null`；原始交易所和原始 ticker 必须保留 | 正向资格回执必须绑定同一 Entity 修订、Security、Listing、来源命名空间/记录 ID、完整挂牌字段和已知属性。不能以模型自述、名字或裸代码准入；暂定实体不得证明跨挂牌同一发行人。 |
| `verified` | 上述身份版本/修订、已知注册国、至少一个 Security 和 Listing、权威库内 `verified_issuer_receipt_id` | ADR 比率及存托证券基础证券关系可为 `null` | 发行人回执必须精确覆盖全部 Security IDs 和 Listing IDs，以及各自属性和来源绑定，才允许共享 issuer 级经营画像。证券报价、流动性、币种与估值仍按 Security/Listing 分开。 |

**主键规则**：`entity_id` 是系统生成、不可变、不含名称/ticker/市场含义的法律发行人 ID；`security_id` 是证券工具或股份类别 ID；`listing_id` 是 venue 上的具体挂牌 ID。v2.1 新 ID 使用带类型前缀的 UUIDv4，不编码公司属性；名称、ticker、市场代码、域名、品牌名都不是全局主键。市场代码符合 ISO 3166-1 alpha-2 形式，实际辖区代码由权威市场导入层维护，Schema 不把市场范围封闭为中港美；交易场所由 MIC 与保真保存的原始交易所名描述。挂牌有效区间使用半开区间 `[valid_from, valid_to)`，未知边界保留为 null；同一市场+ticker 的时间重叠项若任一项缺 MIC，则本地校验器失败关闭，不从原始交易所名猜测是否同一场所；两个已知且不同的 MIC 才能证明是不同场所。公司名与外部编号以带 scheme/authority/jurisdiction、来源、状态和有效期的声明保存；名称 alias 明确允许多对多。已核实 claim 必须有非空证据且有效区间有序；但 claim 的 `verified` 状态本身不等同于编号方案具有 issuer 级唯一性，自动桥接仍需可信方案注册表和权威库事务。Source-local `orgId` 等永远留在各自 namespace。

来源快照中的一行 `source_candidate` 不是 Entity，不可仅凭股票代码创建可扫描对象。名称相似只用于生成候选；**精确 venue+代码+有效期定位 Listing，再经 `Listing → Security → Entity` 定位证券和 issuer**。跨市场归并须有可信 issuer 级 claim 或权威桥接。LLM/搜索只可给候选与来源证据，不得签发 `verified` 或写身份桥接。母子公司是独立 Entity，以 `parent_of`/`controlled_by` 等关系表达集团联系，不将集团关系当成同一 issuer。

身份状态与扫描资格分开保存：`unresolved` 不生成正式 Entity/Work；`provisional` 仅对精确、已准入挂牌做受限快扫，不进 verified 白名单；`conflicted` 暂停新派发但保留旧观察；`verified` 才做完整扫描；`superseded` 只读保留。人工处理必须指向精确 source/listing key 并追加审计事件，不能把一个名称或模糊搜索结果全局合并。亏损、行业未知或暂时停牌不是法人身份的自动反证。

`identity_state` 在 Entity 快照里表示证据保证等级（`provisional`/`verified`）；解析工作流的 `unresolved`、`conflicted` 和 `superseded` 属于 StockWiki 的候选/生命周期状态，不能伪装成一个可扫描 Entity。`EntityRelationshipV21` 只表达 `parent_of`、`controlled_by`、`associate_of`、`same_corporate_group`、继任/合并等关系；schema 明确不提供 `same_issuer` 关系，因为同一发行人必须由一个 Entity 表示。关系双方相同、无证据的关系升级和重叠有效区间由语义校验/权威库阻断。

### v2.2 分开法律发行人与快扫研究对象

`entity_id` 只代表法律发行人，**不再兼任快扫问题的分析对象或并表范围**。契约包 v2.2 新增独立、可演进的 `AnalysisSubjectV10`，由 `analysis_subject_id`（不透明 UUIDv4）和 `analysis_subject_revision` 标识一个有时间边界的研究范围。它记录 `primary_issuer_id`、范围类型、范围基准日、覆盖完整度，以及带有效期和来源证据的发行人成员关系。成员角色必须明确是主发行人、并表主体、权益法投资或未并表关联方；集团控制关系本身不推导并表关系。

范围类型分三种：`provisional_listing_scope` 只能锚定一个精确挂牌及其暂定 issuer，不能扩展成集团经营画像；`standalone_issuer` 只包含已核实的主发行人；`consolidated_reporting_group` 以已核实主发行人的合并报告范围为准，成员清单允许标明仅锚点、部分列示或按特定披露完整列示。快扫不声称成员清单完整，除非来源明确支持 `complete_as_disclosed`。验证必须从 StockWiki 当前权威库取得 issuer 状态和暂定挂牌归属；不能由候选 JSON、LLM 答案或单纯的母子公司关系自证。

任何 `consolidated_reporting_group` 都必须另有 owner-controlled、状态为 `verified` 的并表范围回执，键为精确 `analysis_subject_id@analysis_subject_revision`。回执必须绑定主 issuer、范围基准日、覆盖状态、每个成员的 issuer/角色/有效区间/证据引用，并保存规范化 perimeter 摘要的 SHA-256 和可追溯 HTTPS 披露来源。`trusted_issuer_states` 只证明 issuer 已存在/已核实，不证明它属于该报告范围；成员上的 `evidence_ref` 字符串也不是信任根。新建或修订主体时，传入快照摘要必须与可信回执逐字节语义相符，否则拒绝新 Work。`complete_as_disclosed` 不能由模型推断或手工填字获得。

摘要采用 UTF-8、紧凑 JSON、递归键排序、成员按 `entity_id` 排序后计算 SHA-256；摘要覆盖 subject ID/revision、primary issuer、scope kind、`scope_as_of`、coverage 与完整 membership 对象，不覆盖可单独修改的 `display_name`。运行时 `trusted_reporting_perimeter_receipts` 参数必须只由 owner 事务读取已审阅的权威回执，不接受UI/LLM直接组装；通用校验器仅核对精确键、verified 状态、回执引用、主体锚点及摘要，不能自行访问URL并把网页存在等同于关系已核实。

这使 A/H 股或 ADR 可以共用一个研究对象的经营问答，同时保持不同 Security/Listing 的价格、币种和估值边界；上市子公司仍保留独立 issuer 和可独立快扫的 subject，也可以作为母公司合并范围中的一个有证据成员。若收购、出售、分拆或会计合并范围改变，追加 `AnalysisSubjectEventV10`，版本只前进一步；旧 subject、Work 和 Observation 不回写。现有 v2.1 Entity 保持原 issuer 语义且仍可历史读取，但**不能仅凭 Entity 自动合成一个已验证研究对象**。新 Work/Observation 必须在 C04/C06/W05 接口完成前置兼容改造后绑定 `analysis_subject_id + analysis_subject_revision`；证券专属任务仍另绑 `security_id/listing_id`。旧未绑定 subject 的任务只能走历史查询，不得静默补造范围。

`IdentityEventV21` 是身份内容变更的追加式事件契约，记录事件类型、`entity_id`、`from_revision`/`to_revision`、生效和记录时间、影响到的 security/listing、来源记录、证据和理由。每个事件必须且只能将修订递增 1；改名/改 ticker 必须说明实际变化，issuer 合并/拆分不得把自己列作继任对象。具有 before/after Entity 快照的转换验证器还要证明事件只解释精确差异；issuer rename 的 affected 集合精确覆盖其原有 Security/Listing；ticker/listing 事件的 `security_id` 必须等于被影响 Listing 在两个快照中的 Security，affected listing/security 集合不得多报或漏报。

`AnalysisSubjectEventV10` 同样必须绑定同一 `analysis_subject_id` 和连续的前后 revision。`display_name_changed` 只能改变名称；`primary_issuer_changed` 的旧/新值必须对应两个快照并精准标记两个 issuer；`perimeter_changed` 旧/新值使用规范化 perimeter SHA-256；`scope_kind_changed` 旧/新值必须对应实际范围类型转换。应用器比较两个完整快照，只接受事件声明允许的字段变化，affected issuer 集合必须精确覆盖成员差异（纯覆盖状态变化时标记 primary issuer）。事件 ID 唯一约束、revision compare-and-swap 和追加写入由 owner 数据库事务实施；本地语义验证器不冒充数据库并发控制。

写入验证器还必须取得 StockWiki **当前权威库**投影出的 `trusted_source_bindings` 和 owner-controlled `trusted_market_registry`。后者是按版本加载的 ISO 3166-1 alpha-2 辖区及 MIC 所属市场映射；schema 的两位大写格式只做词法校验，不代表市场代码真实存在。市场不在注册表、MIC 未登记或 MIC 与市场不匹配、注册表缺失时，新身份写入失败关闭。不能用模型给出的交易所描述临时扩充信任映射。`SourceBindingV21` 至少有来源绑定 ID、命名空间、来源记录 ID、来源显示名、内部 Entity/Security/Listing ID、市场、原始交易所、MIC、原始及规范 ticker、有效区间和 active/retired 状态。每一挂牌先与这条独立于传入对象和资格回执的来源行逐项相符，再将资格回执里的来源命名空间/记录 ID/挂牌信息与之对照。仅凭传入 Entity 与回执彼此自洽，仍不能证明它们属于真实来源证券。`verified` 回执属性覆盖 Security 的工具/股份类别字段和 Listing 的原始及规范 venue/ticker、有效区间、报价属性和来源绑定。非 ADR/GDR/CDR（包括普通股、优先股和未知类别）的 `adr_ratio` 必须为 `null`；存托证券比例非空时仍须核实。

参考验证器的 `trusted_market_registry` 形状为 `market_code -> registered MIC set`，但“可信”来自受控注册表装载/版本验证而非Python参数类型。注册表更新必须另走owner发布与审查，不允许扫描请求携带市场列表替代。完整可用的全球 ISO/MIC 数据源及刷新周期由W02/W03的owner注册表实现冻结；本地schema/validator不内嵌不完整的临时白名单。

本地单对象验证只能检查同一 Entity 内部的重复与归属，**不能证明两个 Entity 没有抢占同一来源键或证券 ID**。StockWiki W02/W03 写入者须在一个 SQLite 事务中施加全库唯一约束与冲突检测；该项尚未实现。`trusted_identity_receipts` 与 `trusted_source_bindings` 必须来自数据库/认证接口，不得由候选 JSON、LLM 回答或 UI 字段原样传入。

原 v1 `Entity`/`Security` 与 v2.0.0 身份只可走历史读取路径；`validate_identity_v20_read` 不授权新写入或扫描资格。`validate_entity` 唯一新写入口仍只接受 v2.1.0 issuer Entity；AnalysisSubject 独立接受 `analysis_subject_schema_version=1.0.0`，不改变 v2.1 的字段含义。旧字段即使填有注册国或类型，也不会据此自动成为 `verified` 或生成 subject。任何 W02/W03 新入库调用必须使用 v2.1 写入验证器并由权威库事务验证 subject 映射。现阶段本仓参考验证器不代表 StockWiki 已实现全库唯一约束、回执/来源绑定存取或 SQLite subject 迁移，也不代表 StockQA Work/Observation、C04/C06 已携带 scope 修订。**C01 仍为局部修订，不能标为跨仓完成。**

系统严格遵守**发行人（Entity）、证券工具/股份类别（Security）、交易挂牌（Listing）与经营分部（Segment）**分层：

除逐对象JSON Schema外，导入与调度入口必须执行跨对象语义校验：Entity内每个Security和Listing的`entity_id`必须等于父Entity；每个Listing必须引用该Entity下存在的Security；内部 IDs、source binding 和 venue-qualified listing key 不得重复；ADR 基础证券只能指向同一 Entity 下已核实的 ordinary Security。Universe成员引用的Entity/Security/Listing必须存在、相互归属一致且去重后的成员数必须等于清单声明值。不能用各对象分别通过Schema代替这些关系约束。

```
[发行人 Entity: ENT_opaque]
  ├── Security: A 股 ordinary class ── Listing: XSHG / ticker / CNY
  ├── Security: H 股 ordinary class ── Listing: XHKG / ticker / HKD
  ├── Security: ADR ────────────────── Listing: XNYS / ticker / USD
  │                                      └── 显式关联基础 ordinary Security（若有证据）
  └── 经营分部 Segment: 业务画像 / 下游应用

[不同的上市子公司 Entity: ENT_other] ── controlled_by ──> [集团 Entity]
```

1. **发行人、证券和挂牌解耦（ID-01）**：
   * **经营与质地题**：以 `Entity` 为单位汇聚，每题只提问并生成 1 个答案，不同挂牌地共享相同的商业模式、护城河与治理事实，避免重复调用 LLM 产生双倍费用。
   * 同一股份类别在多个场所挂牌时，多个 `Listing` 指向同一个 `Security`；A/H 不同股份类别各自一项 `Security`；ADR 作为独立存托 `Security`，有证据时显式关联基础股。
   * **估值与行情题**：证券条款按 `Security`，交易所报价、ticker、币种、状态和流动性按 `Listing` 分开处理。
2. **严禁母子公司或同品牌同名合并（ID-02）**：
   * 母公司（`PARENT`）与旗下上市子公司（`LISTED_SUB`）即使共用集团品牌、名称高度相似或代码存在字面关联，只要其发行人法人资格独立、未核实为同一独立法人，**严禁合并为同一实体**，必须独立建档。中微公司/中微半导体这类近似名字只应进入候选消歧，不能按字符串自动合并。
3. **ADR 折算比例边界与严格防猜（ID-03）**：
   * 若官方/监管文件未核实存托凭证与普通股的具体折算比例（如 1 ADR = N 股），`adr_ratio` 必须显式为 `null`，证券层对应估值记为 `unknown`，**严禁猜测折算比例**；但其经核实的实体经营画像仍可安全复用。
4. **轻资产快速准入（ID-04）**：
   * 快扫实体只需具备经核实的证券主档映射，**不以在 `company-wiki` 预先创建公司原件目录、启动下载 worker 或完成 `StockWiki` 正式研究建档为前置条件**。未关联时字段显式保留为 `company_wiki_ref: null`，`formal_stockwiki_profile: null`。

---

## 二、 大股票池成员管理与版本演进（I16, UNI-04）

1. **软目标容量与非强制淘汰**：
   * 设定约 2,000 家独立公司的软目标（A/H/美股各 600~800 家）。
   * 扩容机制：新增 3 家公司后总数增至 2,003 家，**绝不因为超过 2,000 家而自动淘汰/挤出老公司**。
2. **人工锁定保护（`manual_pin`）**：
   * 用户显式设为 `manual_pin: true` 的企业，无论最新打分多低，自动化批次均不得将其自动清退。
3. **逻辑移除与审计溯源**：
   * 移出大池仅变更为 `membership_status = "logically_removed"`，必须记录 `removed_at` 与 `removal_reason`；
   * 恢复入池变更为 `membership_status = "active"`，必须记录 `restored_at` 与 `restoration_reason`，版本号递增。

---

## 三、 单一写入归属（I03, I18）

* **权威拥有者**：`StockWiki` 是股票池成员名单与状态的**唯一写入拥有者**（存储于其内部独立的 `quick_scan` 命名空间下 SQLite 数据库）。
* **只读协议**：`invest-quick-scan`（本仓库）仅作为契约定义者、离线校验器与编排器，不维护第二套生产数据库。
* **上游解耦**：`company-wiki` 仅提供只读的证券主档快照，不承担名单维护职责。

---

## 四、 标准数据契约样例

### 1. v2.1 当前新写示例：身份信息不全的精确挂牌（provisional）
```json
{
  "identity_schema_version": "2.1.0",
  "identity_state": "provisional",
  "identity_revision": 1,
  "entity_id": "ENT_11111111-1111-4111-8111-111111111111",
  "canonical_name": "来源记录所载名称",
  "incorporation_country": null,
  "company_wiki_ref": null,
  "formal_stockwiki_profile": null,
  "scope_attestation_id": "ATT_exact_01",
  "securities": [
    {
      "security_id": "SEC_22222222-2222-4222-8222-222222222222",
      "entity_id": "ENT_11111111-1111-4111-8111-111111111111",
      "security_type": null,
      "share_class": null,
      "adr_ratio": null,
      "ordinary_security_ref": null
    }
  ],
  "listings": [
    {
      "listing_id": "LST_33333333-3333-4333-8333-333333333333",
      "entity_id": "ENT_11111111-1111-4111-8111-111111111111",
      "security_id": "SEC_22222222-2222-4222-8222-222222222222",
      "market": "US",
      "exchange_raw": "NYSE ARCA",
      "exchange_mic": null,
      "ticker_raw": "EXAMPLE",
      "ticker": "EXAMPLE",
      "currency": null,
      "listing_status": null,
      "source_binding_ref": "BND_source_01",
      "valid_from": null,
      "valid_to": null
    }
  ],
  "segments": []
}
```

该示例只表示来源记录中有一条可定位挂牌的 provisional issuer；有效写入还必须从权威库解析与之逐字段一致的 source binding 和正向资格回执。它不证明名称唯一，也不能与另一个市场的同名记录自动合并。

### 2. v1 历史只读示例：A+H 同实体多证券（ID-01）
```json
{
  "entity_id": "ENT_BYD_COMPANY",
  "canonical_name": "比亚迪股份有限公司",
  "incorporation_country": "CN",
  "company_wiki_ref": null,
  "formal_stockwiki_profile": null,
  "securities": [
    {
      "security_id": "SEC_002594_SZ",
      "entity_id": "ENT_BYD_COMPANY",
      "market": "CN",
      "exchange": "SZSE",
      "ticker": "002594",
      "currency": "CNY",
      "security_type": "ordinary",
      "adr_ratio": null,
      "ordinary_security_ref": null,
      "listing_status": "active"
    },
    {
      "security_id": "SEC_01211_HK",
      "entity_id": "ENT_BYD_COMPANY",
      "market": "HK",
      "exchange": "HKEX",
      "ticker": "01211",
      "currency": "HKD",
      "security_type": "ordinary",
      "adr_ratio": null,
      "ordinary_security_ref": null,
      "listing_status": "active"
    }
  ],
  "segments": [
    {
      "segment_id": "SEG_AUTO",
      "segment_name": "汽车及电池业务",
      "revenue_share_pct": 80.0
    }
  ]
}
```

### 3. 历史反例：母子同品牌拒绝合并（ID-02）
```json
{
  "bridge_id": "BRG_REJECTED_SAMPLE",
  "entity_id": "ENT_PARENT_HOLDING",
  "security_ids": ["SEC_PARENT_01", "SEC_SUB_02"],
  "verified_same_issuer": false,
  "verification_source": "unverified_brand_match",
  "verified_at": "2026-09-22T21:00:00Z",
  "notes": "母公司与子公司虽然品牌同名，但经查属于两个独立法人实体，严禁合并为同一Entity。"
}
```

### 4. v2.0 历史只读样例：ADR 折算比例缺失（ID-03）
```json
{
  "security_id": "SEC_BYDDY_US",
  "entity_id": "ENT_BYD_COMPANY",
  "market": "US",
  "exchange": "OTHER",
  "ticker": "BYDDY",
  "currency": "USD",
  "security_type": "adr",
  "adr_ratio": null,
  "ordinary_security_ref": "SEC_01211_HK",
  "listing_status": "active"
}
```

### 5. 大股票池版本增补与逻辑操作（UNI-04）
```json
{
  "manifest_version": "1.0.1",
  "updated_at": "2026-09-22T21:50:00Z",
  "soft_target_capacity": 2000,
  "total_entities": 2003,
  "active_entities": 2002,
  "manual_pinned_count": 150,
  "members": [
    {
      "entity_id": "ENT_NEW_01",
      "membership_status": "active",
      "manual_pin": false,
      "added_at": "2026-09-22T21:50:00Z",
      "version": 1
    },
    {
      "entity_id": "ENT_SAMPLE_REMOVED",
      "membership_status": "logically_removed",
      "manual_pin": false,
      "added_at": "2026-01-01T00:00:00Z",
      "removed_at": "2026-09-22T21:50:00Z",
      "removal_reason": "主营业务全面变更为停运重组，已由人工确认移出监控池",
      "restored_at": null,
      "restoration_reason": null,
      "version": 2
    }
  ]
}
```
