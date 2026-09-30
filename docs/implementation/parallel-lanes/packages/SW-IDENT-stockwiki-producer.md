# SW-IDENT｜StockWiki 身份与名单剩余验收包

**可单独交给 StockWiki harness 的施工指令；交付前必须重读当前 HEAD。** Owner：`C:/Users/郑曾波/Projects/StockWiki/`；任务 W01→W02→W03。IQS 总控独占 G2b 跨仓最终验收。W01 依赖 G0/C01/C06，W02 依赖 W01，W03 依赖 W02；依赖与 case 的唯一来源是 [`tasks.json`](../../tasks.json)。与 QA-04 可跨仓并行；StockWiki 内只设一个写入者。

## 2026-09-30 基线：已交付与未证明

只读观察的 producer 基线为 `StockWiki master@72531b5`（合并 W04 `8bee364` 与 reader 拆分 `6f0c2c4`）；其后总控获精确授权修复 mapping 有效区间，提交 `2058931`。开工以实际 HEAD 为准；原有未跟踪 `.claude/` 保留，不删除、不暂存。先前 `c8cfb2e` 的 snapshot 只含 Entity/AnalysisSubject/source bindings，缺 owner receipt/market registry 的诊断是**历史状态**，不可再据此要求重造。

新 HEAD 已有 `stockwiki/identity_snapshot.py`、`identity_mapping.py`，并新增 `market_registry.py`、`identity_receipts.py`、`identity_g2b.py`、`services/identity_g2b.py`、`cli_parsers/identity_g2b.py`。公开 CLI `identity-export-g2b` 从 owner stores 导出 identity package **2.2.0** / Entity **2.1.0** 的 exact-key request envelope，`trusted_context` 含 owner 管理的 `market_registry`、`identity_receipts`、`source_bindings`。W04 [施工记录](../../../../../StockWiki/.planning/w04_g2b_owner_context/closure.md)记载一个 provisional、单证券/单挂牌 fixture 的 canonical JSON SHA-256：`0efc2c04daa7b6345078410a5df5ae0aa5bec9098b1523d7c25f9f60f53e5d2f`。命令：

```powershell
python -B -X utf8 -m stockwiki.cli --root <隔离根> identity-export-g2b --entity-id ENT_1b2a4d3e-0000-4a1b-8c2d-000000000001 --as-of 2026-09-29T00:00:00Z
```

IQS 总控从本仓运行 StockWiki 的四个定向测试文件（`test_market_registry.py`、`test_identity_receipts.py`、`test_identity_g2b_export.py`、`tests/e2e/test_g2b_iqs_cli.py`）：**64 passed / 11.54s**，独立 pytest 临时根已删除。测试包含 owner CLI 生成的正例和逐字段负例；这证明该提交的定向测试通过，**尚不等于** W01/W02/W03 全部验收、真实多挂牌 issuer 身份桥接或总控 G2b 签收。W04 自述的全套测试及一次官方 ISO CSV canary 是 owner 记录，不必重复联网下载。跨仓状态和门槛见 [G2b 交接](../../reviews/IQS-lane/G2b-handoff-2026-09-29.md)。

开工先读目标仓 `AGENTS.md`（若有）、当前 Git status/HEAD、W01–W03 case 定义、[身份契约](../../contracts/identity.md)、[股票池设计](../../../stock-pool-design.md)、已有 store/snapshot/mapping/receipt/registry/CLI/测试。记录当前代码 hash 和可公开调用的版本，不以旧计划文件名推断代码不存在。

## 授权边界

此前获批的 StockWiki 精确文件并集：`stockwiki/quick_scan_store.py`、`stockwiki/quick_scan_identity.py`、`stockwiki/quick_scan_universe.py`、`stockwiki/cli_parsers/quick_scan.py`、`stockwiki/cli_registry.py`、`tests/test_quick_scan_store.py`、`tests/test_quick_scan_identity.py`、`tests/test_quick_scan_universe.py`、`.gitignore`。不存在的旧路径不要求创建。2026-09-30 用户**另行仅授权**总控修复 `stockwiki/identity_mapping.py` 和 `tests/test_identity_mapping.py` 的 as-of/退役边界；这不是对 SW-IDENT harness 后续工作的普遍扩权。其余新合并的 snapshot/mapping/registry/receipt/G2b 模块、测试和 fixture **不在这份授权中**。本卡不扩权；若 RED 反例证明修复必须碰未获批路径或新增文件，先把精确路径、目的和最小差异报给用户并取得授权。未获授权时可做只读复核、报告缺口，不能绕过审批写入。

## 剩余工作：先验收，后最小修复

1. **W01 存储和迁移**：从隔离空库/旧库做迁移、幂等、冲突回滚与历史保留；核对命名空间唯一性、非唯一别名、immutable Entity/Security/Listing ID、source candidate/binding。对照 DB-01、ID-01/02/07、DB-08/09 逐项记真实结果。旧 P2 是否已解决以当前公开 store 行为为准。
2. **W02 解析与身份选择**：经公开 API/CLI 验证 exact venue+ticker+effective-time/source key、权威 issuer ID、冲突 preview 和 `unresolved`/`ambiguous`/`mapped`/未尝试四态；单凭名称、LLM 建议或 group control 不合并 issuer。固定“中微公司/中微半导体”近名反例、跨市场同 ticker、ADR/双重上市缺桥接反例；缺真实权威 bridge 时保持分离或待核。核对 provisional 仅绑定精确输入 Listing、verified issuer 与独立 AnalysisSubject 的边界；对照 W02 的 ID-01/02/03/12/13/14、UNI-02/06。现有 `identity_mapping.py` 测试可作证据，但单挂牌 G2b golden 不能替代这些反例。
   2026-09-30 G2b 独立审查补充：重复**完全相同** Listing key 的两条合成记录保持 ambiguous，不能证明近名导入/解析不误并。owner `identity_snapshot.py` 当前把 Listing 与 binding 的 `valid_from/valid_to` 均投影为 null，store 尚无有效区间历史；即使 `identity_mapping.py` 对非空区间作失败关闭，W02 的真实 ticker 复用/到期时点验收仍需独立生产数据与公开入口证据。不得把合成名称标签或内存区间反例当作这项完成。
3. **W03 名单和扫描资格**：公开路径验 `add/add_security/remove/restore/pin/unpin/list/diff/explain`、成员版本/审计、退市/低分保留历史。确认 `unresolved` 不进付费扫描，名称变更/ticker 复用不改旧 ID/观察；reporting-scope membership 与法定控制关系独立修订。对照 UNI-03/04/08、ID-05/06/15。已有成员 CRUD 不重写；明确哪些仍缺生产接线。
4. **G2b producer 交接（只读复现）**：从独立临时库经 owner 公共 store/CLI 生成 request，按上面命令比对 canonical JSON SHA-256；列出 fixture provenance、as-of、receipt/registry release 和 exact key。交给总控原始输出或可复现的公开命令、hash、版本、所需 seed 步骤；不得用手拼 JSON 冒充正例。当前正例仅 provisional 单挂牌；不凭空造 verified、多挂牌或 AnalysisSubject golden。总控执行 IQS 公开 CLI 的跨仓正反例并决定 G2b 门是否关闭。

采用 TDD：每个真实缺口先有公开入口 RED，再在**获批路径**最小修复和 GREEN；只在本批身份/迁移大节点做一次聚焦审查。相关 unit/integration/隔离 E2E 需记录命令、通过/跳过数、失败反例和基线差异；临时 SQLite、下载样本和 pytest 根在 `finally` 清理并断言不存在。测试无需真实 API 或生产库；不保存公司文档。

## 交接与完成判据

返回符合 [handoff schema](../handoff.schema.json) 的 JSON：`package_id=SW-IDENT`、当前/起始 HEAD、工作树基线、授权与实际变更路径、各 W01/W02/W03 case 的公开入口证据、接口与 schema 版本、owner golden 命令/原文或安全交付位置/SHA、测试及清理结果、未完成项。可单独提交本 owner 授权文件，不能混入 `.claude/` 或其他进程改动。若某任务已被当前实现满足，提交“已验证”证据即可，不要为了凑变更重复实现。

验收状态要分开：**W04/G2b producer 已有实现和定向测试证据**；W01–W03 仍需逐 case 判定；**G2b 最终签收由 IQS 总控**在 owner 公开路径与 IQS CLI 做跨仓正反例后决定。若真实 issuer bridge、AnalysisSubject 或名单扫描生产接线没有对应正例，记为相应 partial，不把 provisional fixture 外推为生产覆盖。
