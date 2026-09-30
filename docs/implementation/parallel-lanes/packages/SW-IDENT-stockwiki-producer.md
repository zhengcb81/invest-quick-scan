# SW-IDENT｜StockWiki 身份主档、名单剩余闭环与真实 golden

**可单独交给 StockWiki harness 的施工指令。** Owner：`C:/Users/郑曾波/Projects/StockWiki/`；对应 W01→W02→W03 与 IQS G2b producer 交接。W01 依赖 G0/C01/C06；W02 依赖 W01；W03 依赖 W02。StockWiki 当前写授权仅限既有 W01 三文件及 W02/W03 精确八文件；此卡不扩权。与 QA-04 可跨仓并行，StockWiki 内只有本 harness 一个写入者。

## 当前事实与开工核验

2026-09-30 只读观察 StockWiki `master@c8cfb2e`，存在未跟踪 `.claude/`。该 HEAD **已合并** `stockwiki/identity_snapshot.py`、`stockwiki/identity_mapping.py` 与相应测试；`build_identity_snapshot` 从真实 `QuickScanStore` 序列化，identity package 2.2.0 / Entity 2.1.0 / AnalysisSubject 1.0.0，mapping DTO 1.0.0；`.planning/w02_golden_receipt.json` 仅含摘要 hash/count，并非可直接交给 IQS CLI 的完整请求 golden。旧进度说 W02/W03 首段 partial；合并提交后必须重新跑真实 owner 测试、检查该结论是否仍成立。旧计划中的 `quick_scan_identity.py` / `quick_scan_universe.py` 当前不存在，不能机械按文件名重造。

先读目标仓当前 `AGENTS.md`（如有）、[`tasks.json`](../../tasks.json) W01/W02/W03、[身份契约](../../contracts/identity.md)、[股票池设计](../../../stock-pool-design.md)、[G2b 交接](../../reviews/IQS-lane/G2b-handoff-2026-09-29.md)、现有 `identity_snapshot.py`/`identity_mapping.py`/测试、`quick_scan_store.py` 与 CLI 注册路径。记录 HEAD、全量 status 路径/哈希、现有 serializer 的公开调用方式、receipt hash 可否复算。 `.claude/` 不删除、不 stage。核对 W01 旧 P2 问题是否已被后续合并解决；不能只因有合并提交就把 W01 标为通过。

## 允许范围和前置门

先前精确授权文件并集：`stockwiki/quick_scan_store.py`、`stockwiki/quick_scan_identity.py`、`stockwiki/quick_scan_universe.py`、`stockwiki/cli_parsers/quick_scan.py`、`stockwiki/cli_registry.py`、`tests/test_quick_scan_store.py`、`tests/test_quick_scan_identity.py`、`tests/test_quick_scan_universe.py`、`.gitignore`。其中未存在的文件**不要求创建**。当前新合并的 `identity_snapshot.py`、`identity_mapping.py`、其测试、fixture/golden 文件不在先前授权里；如果实质修复必须改这些文件或新建公开 CLI/测试路径，先给用户报备精确文件与目的，取得该范围写授权后再动。若没有授权，继续完成只读验证与可直接由现有 serializer 生成的交接，剩余写入标 `blocked`，不绕审批。

## 工作分解与 TDD

1. **W01 重新判定**：在临时 SQLite 库运行真实 migration/store 测试，核对唯一键、source binding、身份版本和历史保留。针对仍存在的 P2 只在获批文件里写 RED，然后最小修复、GREEN；不可用旧工作日志替代新 HEAD 结果。W01 不通过时不宣布 W02/W03 完成。
2. **W02 身份选择剩余项**：检查已合并 snapshot/mapping 与现有证券导入 preview 是否已实现权威 Listing→Security→Entity 绑定、精确 venue/ticker/effective-time 键、issuer receipt、source binding 和明确的 `unresolved`/`ambiguous`/`mapped`/未尝试四态。名称相近（如中微公司/中微半导体）、同 ticker 跨市场、ADR/双重上市没有权威桥接时必须保持分离或待核，不能为了扫描资格自动合并。LLM 建议只做候选，不写 verified 身份。缺口通过公开 StockWiki API/CLI 的反例证明；仅在授权路径实施。
3. **W03 名单与扫描资格**：核对 add/remove/restore/pin/list/diff 和版本历史在当前 HEAD 真实可用。验证 `unresolved` 不进 paid work、`provisional` 只绑定精确挂牌、verified issuer 的研究对象范围另有独立 AnalysisSubject 修订。名称变更/ticker 复用不改写旧 ID/旧观察；退市/低分不删除历史。此前已完成的成员 CRUD 不重写，只补公开权威 identity projection 到扫描待办的真实缺口。
4. **G2b producer 交接**：用独立临时库经现有真实 serializer/public read path 生成完整 Entity snapshot、mapping DTO 与对应 `trusted_context`。固定 canonical JSON golden、SHA-256、调用入口、来源/库 revision、as-of 策略；若公共入口缺失，明确指出差距，不用测试 helper 或手写 JSON 假装生产接口。`w02_golden_receipt.json` 可核对摘要，不能代替完整 golden。新增 golden/CLI 文件若超授权则先申请扩展。不得导出生产真实库或保存公司文档。
5. **owner 测试和交叉接口**：RED/GREEN 之外跑当前 `test_quick_scan_store.py`、`test_identity_snapshot.py`、`test_identity_mapping.py` 及受影响 CLI 测试；临时根和 SQLite 清理后不存在。producer 侧先证明序列化字节稳定、receipt/ref/join 可溯源，再交总控用 IQS 公开 `python -B -X utf8 scripts/identity_contract_cli.py --input <request.json> --schema-version 2.2.0` 做正反例。StockWiki harness 不改 IQS，也不独自宣称 G2b 闭合。

## 验收矩阵与 handoff

真实 serializer 正例：同一库/修订重复导出字节/hash 相同；Entity 2.1.0 的每个 Listing 指向同 snapshot 的 Security/Entity、有效 source binding 和同 revision receipt；可选 AnalysisSubject 单独验证，不从母公司控制关系推断并表。反例：一处 ID/MIC/ticker/source/receipt 错位、缺 trusted owner record、歧义同名、未知/不支持版本均失败关闭；snapshot 正例必须经真实公开读路径获得。完整跨仓正反例由 IQS 总控按 [G2b 交接](../../reviews/IQS-lane/G2b-handoff-2026-09-29.md)执行。

返回 [handoff schema](../handoff.schema.json) JSON：`package_id=SW-IDENT`，HEAD/源文件 hash、确切 write scope 和授权依据、W01/W02/W03 每个 case 的当前通过/未通过证据、serializer/DTO 版本与 public invocation、golden 原文路径或安全交付方式及 SHA、迁移版本、测试计数、临时库删除证明、未完项。身份与迁移在本批次末做一次聚焦只读审查；其他小函数无需各自审查。没有完整真实 golden 时 G2b 仍 pending；没有扫描工作生产接线时 W03 仍 partial。
