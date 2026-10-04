# G2b Alphabet 样本入库证据（美股 A 类 + 多挂牌 B 类）

日期：2026-10-04。执行者：IQS 总控。授权链：owner 2026-10-03「Alphabet A 全 4 只签」「美股 B 按 CIK 签收」+ 通授；实现批次经独立审查两轮 approved（`ses_efa090556ffepNraXlO3bq8RAy`，StockWiki `f701909`）。

## 1. 样本构成

| 项 | 值 |
|---|---|
| entity_id | `ENT_97bf6a65-a9e6-43f0-8409-c5695e2f6e1e` |
| canonical_name | Alphabet Inc. |
| identity_state | **verified**，identity_revision=1 |
| verified_issuer_receipt_id | `IVR_663efa0137144ccba0e6c88781da6752` |
| 证券（4，多挂牌样本） | GOOG=ordinary、GOOGL=ordinary、GOOGM=preferred（存托优先股）、GOOGN=preferred |
| 挂牌 | market=US，exchange_raw=NASDAQ，**exchange=XNAS**（`tests/fixtures/market_registry/iso10383_sample.csv` 权威 MIC），listing_status=active，currency=USD |
| binding（4） | source_namespace=`company-wiki:security_master/us.json`，record_id=`0001652044:<ticker>`，canonical_name=Alphabet Inc. |
| evidence_ref | `https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm`（SEC 10-K，owner 批准） |
| decision_ref | `owner-2026-10-03-alphabet-sec-10k`（回执内持久化 provenance） |
| same_legal_issuer | true；security_ids/listing_ids 覆盖 **4/4 全等** |
| verified_adr_ratios | `{}`（四只均非 ADR，诚实为空；GOOGM/GOOGN 是美国本土发行的存托优先股，adr_ratio=None） |

## 2. 执行与验证

1. **构建**：4 条记录取自 company-wiki `security_master/us.json`（CIK 0001652044）；证券类型按各自 SEC 描述（GOOG/GOOGL 普通股；GOOGM/GOOGN 存托优先股）；`share_class` 诚实置空（主档无此字段，快照投影亦恒 None）。payload：`StockQAbyLLM/pilot_runs/g2b_alphabet_2026-10-04/alphabet_payload.json`（含 provenance 块）。
2. **导入**：`python -m stockwiki.cli --root <StockWiki> entity-import --file <payload>` → **exit 0**，回执 `phase_status=entity_saved_receipt_recorded`（存于 `import-receipt.json`）。
3. **库内独立复验**（只读查询两库）：
   - `quick_scan_entity`：1 行，verified/rev1/回执 id 关联 ✓
   - `quick_scan_security`：4 行，类型与 MIC 如上 ✓
   - `quick_scan_source_binding`：4 行 ✓
   - `identity_receipt`：1 行 kind=verified_issuer，coverage 4/4，`same_legal_issuer=true`，evidence_ref/decision_ref 就位；`events=[]`（无生命周期事件=active，符合 `active_receipt_id` 语义）✓
4. **幂等重放**：同 payload 再跑 → 同 `receipt_id`、entity 仍 1、证券仍 4、回执仍 1 行 ✓（`identity_receipts.sqlite` 无重复、`scan.sqlite` 无重复证券）。
5. **回执经 store 全量校验**：`record_receipt` 的 `_validated_verified` 逐项比对（coverage 集合全等、security/listing_attributes 与 store 投影字节相等、incorporation/canonical 一致、HTTPS）——派生字段由导入器从 store 投影注入、owner 字段原样保留（审查 F1–F3 整改已核）。

## 3. 对 G2b 类别的效果

- **A 类（发行人核验样本）**：**本样本即为首个真实落库样例** —— verified 实体 + IVR 回执 + 权威 HTTPS evidence_ref + decision_ref provenance。类别 A 从"0 READY"→"有 1 个可签收样例"。
- **B 类（多挂牌）**：同一 entity 下 4 只证券/4 挂牌，**美股侧多挂牌样本就绪**（653 CIK 组的机制性证明）。A/H 仍挂起（owner 已决定先跳过，等映射表）。
- **C 类**：仍待 AnalysisSubject 存储实现（通授已给，下一施工项）。
- **D 类**：仍待过渡播种 + 官方登记表（owner 已决定两步走）。
- G2b 卡**保持 open**，直到四类齐；本样本已让 A（美股）+ B（美股）具备签收实物。

## 4. 边界与诚实注记

- `incorporation_country="US"` 取自发行主体注册国（10-K 封面为 Delaware，evidence_ref 即该10-K）；未逐字引用封面（不做原件下载，轻资产边界）。
- `share_class`/`ordinary_security_ref` 保持 null：主档未提供 share-class 映射，**不编造**（W02 步骤"share-class 映射缺失阻断复用"的下游影响：如后续需要 share-class 级判断，须 owner 提供映射）。
- 全程零网络、零 LLM；payload 构建只读 company-wiki 主档与 iso10383 fixture。
- 首次导入尝试因 `IVR_` id 含连字符被**写前校验拒绝**（exit2，零写入）——修正为契约允许的 `[A-Za-z0-9_]+` 后成功；该拒绝记录本身即为写前门有效的证据。
