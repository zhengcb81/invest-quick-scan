# B01-b 前置导入批施工卡（写前报告 — owner 通授 2026-10-03 覆盖导入；样本=owner round-81 决定）

日期：2026-10-07。本批 = B01-b live 实验的实体前置：将 **宁德时代（CN-A:300750）** 与 **中信建投 H（HK:06066）** 以 **provisional** 状态经已验证的 G2b-A 导入路径（StockWiki `f701909`，Alphabet 首样本同路径）入库，随后 W04 `identity-export-g2b` 导出两份 identity_snapshot 供 B01-b 冻结清单使用。

## 授权与样本
- **样本**：owner round-81 两项结构化决定——A股=宁德时代 300750、港股=中信建投 H 06066（美股=Alphabet 现成）。
- **导入写授权**：owner 2026-10-03 通授「全部剩余卡/批次一次性授权」（含 G2b 导入类），条件=写前报告+独立审查（本卡即写前报告）。
- **provisional 诚实边界**：verified 需 IVR 回执+owner 批准 evidence（Alphabet 走 `owner-2026-10-03-alphabet-sec-10k`）——本批**不声称 verified**；BENCH-01 只需冻结「身份 revision」，provisional rev1 即满足，样本身份状态如实记 provisional。

## 实施步骤
1. 构建两 payload（Alphabet 四键形状 `{provenance, entity, source_bindings, issuer_receipt}`：
   - entity：`ENT_<uuid4>`、identity_state=provisional、rev1、canonical_name 全称（宁德时代新能源科技股份有限公司/中信建投证券股份有限公司）、incorporation_country=CN、scope_attestation_id=`ATT_<hex32>`、verified_issuer_receipt_id=None、单证券（宁德：300750/SZSE/**XSHE**/CN-A/CNY；中信建投 H：06066/**SEHK**/XHKG/HK/HKD，listing_status=active、security_type=ordinary、adr_ratio=None）；
   - issuer_receipt：kind=**provisional_scope**、receipt_id=ATT_、scope=listed_operating_company、negative_scope_flag=false、basis=**user_exact_security_attestation**+actor_id=`owner-2026-10-06-b01-sample-freeze`（诚实：非官方股权分类源，系 owner 样本决定的精确证券佐证）、recorded_at=UTC ISO、identity_revision/entity_id 匹配；
   - source_bindings：`BIND_<uuid4>`，source_namespace=`iqs:b2a_candidates/2026-10-03`（诚实溯源到 B2a 分类批次）、record_id=listing_key；
   - provenance：purpose/entity_source/owner_approval(`owner-2026-10-06-b01-sample-freeze`)/exchange_mic_source(iso10383_sample.csv)/build_at。
2. 导入：`python -m stockwiki.cli --root <StockWiki> entity-import --file <payload>` ×2 → exit 0 + 回执。
3. 库内只读复验（entity/security/binding/receipt 各行数与字段）+ **幂等重放**（同 payload 再跑→零新增）。
4. W04 `identity-export-g2b` ×2 → 两份 identity_snapshot（哈希记档）→ 交 B01-b 冻结材料。

## 允许改动
1. StockWiki **零代码改动**（复用已验证 CLI `f701909`）——本批仅**经授权 CLI 的数据写入**（两实体+证券+绑定+provisional 回执）+ `identity-export-g2b` 只读导出。
2. StockQA：`pilot_runs/b01_prereq_2026-10-06/`（两 payload + 导入回执 + 两份导出 snapshot + 证据文档）——沿 Alphabet 样本目录惯例。
3. IQS：本卡、Phase 84 进度。
4. **禁改**：一切生产代码、B2a 资产、叙事三提交、既有实体数据（幂等不覆盖）。

## 门与证据
- 导入 exit 码 + 回执 phase_status + 库内行数复验 + 幂等零新增 + 导出字节哈希。
- 独立审查两轮（数据批同样审：范围/溯源/provisional 诚实性/幂等）。
- **无 live 成本**（纯本地 CLI 与只读查询；不联网、不调 LLM）。

## 风险与边界
- 名称与证券属性取自 B2a 分类（source_namespace 如实标注）；不引入未经分类的字段。
- 单证券约束（provisional）两样本均满足；A/H 多挂牌语义不在本批（B 类另论）。

## r1 findings 处置记录（round-86/87）
- **P1-1/2/3 → CLI rev2 修复（证据档 v2 §1-§3）**：rev2 双导入 exit 0 + 幂等重放双 exit 0 + 回执/payload listing MATCH + trusted_context 仅 rev2 + cncb namespace 溯源更正（新 BIND，旧 BIND 孤儿残留披露）；**未再裸 SQL**。
- **P2-1**：允许面补 `market-registry-import`（iso10383 fixture，Alphabet 同源）。
- **P2-2**：JSON 证据档经 `git add -f` 入库（绕过 `*.json` ignore 的证据适用性）。
- **P2-3**：证据措辞更正（仅导入回执 0/0；导出无回执）。
- **P2-4**：拒绝事件字节证据引用审查报告复现（v1 e1/e2 零字节如实说明）。
- **P2-5**：IQS 公共契约 CLI 兼容项（BND_/status）单独开项，非本批引入。
- **LOW**：Phase84 侦察③勘误入 task_plan；时间戳/ CRLF 如实披露入证据档 §3/§4。
