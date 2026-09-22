# 公司、证券、分部与名单身份契约规范（Task C01）

**契约版本**：1.0.0  
**任务编号**：C01（Stage M0，Owner: `iqs`）  
**关联约束**：I03, I04, I16, I18  
**验收场景**：ID-01, ID-02, ID-03, ID-04, UNI-04  
**Schema 定义**：[`schemas/quick_scan/identity.schema.json`](file:///C:/Users/郑曾波/Projects/invest-quick-scan/schemas/quick_scan/identity.schema.json)  

---

## 一、 核心概念与分层原则（I04）

系统严格遵守**法律实体（Entity）、挂牌证券（Security）与经营分部（Segment）**三层分离：

```
[独立法人实体 Entity: ENT_XXX]
  ├── 经营业务/下游分部 (Segment)
  │     ├── Segment A (主营)
  │     └── Segment B
  ├── 交易证券 Security 1 (例如 A股: SEC_002594_SZ, CNY)
  ├── 交易证券 Security 2 (例如 H股: SEC_01211_HK, HKD)
  └── 交易证券 Security 3 (例如 ADR: SEC_BYDDY_US, USD, adr_ratio=null 或 官方核实比率)
```

1. **实体与证券解耦（ID-01）**：
   * **经营与质地题**：以 `Entity` 为单位汇聚，每题只提问并生成 1 个答案，不同挂牌地共享相同的商业模式、护城河与治理事实，避免重复调用 LLM 产生双倍费用。
   * **估值与行情题**：以 `Security` 为单位分别处理（如 A/H 股具有不同的本位币 CNY vs HKD、不同的市场折溢价与流动性）。
2. **严禁母子公司或同品牌同名合并（ID-02）**：
   * 母公司（`PARENT`）与旗下上市子公司（`LISTED_SUB`）即使共用集团品牌、名称高度相似或代码存在字面关联，只要其发行人法人资格独立、未核实为同一独立法人，**严禁合并为同一实体**，必须独立建档。
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

### 1. 正例：A+H 同实体多挂牌（ID-01）
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

### 2. 反例与边界：母子同品牌拒绝合并（ID-02）
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

### 3. 边界样例：ADR 折算比例缺失（ID-03）
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

### 4. 大股票池版本增补与逻辑操作（UNI-04）
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
