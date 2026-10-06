# B01-b 前置导入批证据（宁德时代 + 中信建投 H，provisional）

日期：2026-10-07。执行者：IQS 总控。授权链：owner round-81 样本决定（A股=宁德时代 300750 / 港股=中信建投 H 06066 独立选）+ 2026-10-03 通授（含 G2b 导入类）；写前报告=`B01b-import-card-2026-10-07.md`。路径=Alphabet 同款已验证 CLI（StockWiki `f701909` entity-import）。

## 1. 样本构成

| 项 | 宁德时代 | 中信建投 H |
|---|---|---|
| entity_id | `ENT_99ebb735-f072-41e4-8545-823bc012614f` | `ENT_1af6804e-40c1-4c35-b190-ea691dba2c85` |
| canonical_name | 宁德时代新能源科技股份有限公司 | 中信建投证券股份有限公司 |
| identity_state | **provisional**，rev1 | **provisional**，rev1 |
| 证券 | 300750 / CN / XSHE（深交所）/ CNY / ordinary | 06066 / HK / XHKG（港交）/ HKD / ordinary |
| 回执 | `ATT_bd730f17219941a0a422b1e322dbae70`（provisional_scope） | `ATT_a6be5f730d3247889affb583a09fee86`（provisional_scope） |
| basis | user_exact_security_attestation + actor `owner-2026-10-06-b01-sample-freeze` | 同 |
| binding | `BIND_<uuid4>`，source_namespace=`iqs:b2a_candidates/2026-10-03`，record_id=`CN-A:300750` | 同，record_id=`HK:06066` |

provisional 诚实边界：**不声称 verified**（verified 需 IVR+owner 批 evidence，本批不做）；BENCH-01 冻结「身份 revision」=rev1 即满足。

## 2. 执行与验证

1. **导入**：`python -m stockwiki.cli --root <StockWiki> entity-import --file <payload>` ×2 → 均 exit 0、`phase_status=entity_saved_receipt_recorded`、`receipt_recorded=true`、`llm_calls=0/network_calls=0`。
2. **库内只读复验**：quick_scan_entity 3 行（Alphabet verified + 两样本 provisional）；quick_scan_security 6 行（06066 HK/XHKG、300750 CN/XSHE、Alphabet 4 US）；identity_receipt 3 行（2×provisional_scope + 1×verified_issuer）。
3. **幂等重放**：同 payload 各再跑一次 → 同 receipt_id、entity/security/receipt 行数零新增 ✓。
4. **W04 导出**：`identity-export-g2b --entity-id <eid> --as-of 2026-10-07T00:00:00Z` ×2（经 `market-registry-import` 导入 iso10383_sample.csv 后）→ 两份 UTF-8 字节级 snapshot。

| 文件 | 字节 | sha256（前16） | 内容 |
|---|---|---|---|
| `catl_snapshot.json` | 2979 | `4ce7ba5a80868429` | provisional rev1、300750 CN XSHE ordinary |
| `cncb_h_snapshot.json` | 2938 | `2853cc982a91c958` | provisional rev1、06066 HK XHKG ordinary |

产物目录：`StockQAbyLLM/pilot_runs/b01_prereq_2026-10-07/`（两 payload、导出、回执日志、快照）。

## 3. 批内纠正记录（如实披露，待审查裁定）

1. **market 标签纠正（CN-A→CN）**：初始 payload 的 300750 `market` 误用候选层段标签 `CN-A`（源自 candidates 的 listing_key 习惯）；W04 导出按市场注册表校验（ISO 码集 CN/GB/HK/US）拒绝 `market_not_registered: CN-A`。导入器为 fail-closed 幂等（重导同绑定异数据 → `source binding conflict` 拒绝），且**无修正类 CLI**——故以**操作者文档化纠正**将本批自产的两行（quick_scan_security / quick_scan_source_binding 的 300750 market）改为 `CN`，随后导出通过。纠正范围恰两行 market 字段，其余零改动；**层标签语义区分**（security.market=ISO 国家码；candidates listing_key=段标签 CN-A）记为口径决定。
2. **UTF-16 重定向陷阱**：PowerShell `>` 把 CLI stdout 重编码为 UTF-16（BOM 0xff）——两份快照改以 python 子进程按原始字节捕获落盘（UTF-8 验证通过）。操作提示：快照类产物禁用 PS `>`。

## 4. 边界

- 全程零网络、零 LLM（导入与导出回执均 `llm_calls=0/network_calls=0`）；market-registry 导入用既有 iso10383 fixture（Alphabet 验收同源，7 条记录）。
- 单证券约束（provisional）两样本满足；本批不动既有实体（Alphabet 零触碰）、不动 B2a 资产、不触叙事三提交。
