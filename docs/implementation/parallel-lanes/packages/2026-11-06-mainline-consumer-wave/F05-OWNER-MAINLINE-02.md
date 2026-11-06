# F05-OWNER-MAINLINE-02｜将事实查询 producer 适配到当前 StockWiki

**lane：** `stockwiki`
**唯一 Lab：** `C:\Users\郑曾波\Projects\iqs-stockwiki-f05-mainline-lab`
**只读 source：** `C:\Users\郑曾波\Projects\StockWiki`，`master@6d1e40bcdcde5e99488e22c38d57bd8e1b33c27e`
**行为参考：** `C:\Users\郑曾波\Projects\iqs-stockwiki-f05-query-lab`，接受 payload `63a6ffcf23f8d16f47acf44bdbcf3e567a85458e`，交接 Lab HEAD `5bdb54fe828856a9d69c4857caca737ca775321a`
**消费者合同：** IQS `master@acb03e3c084f61ca2b49181180195118077d43e3`；facts schema 2.7.0，SHA-256 `cd3e03417289a99f5194263603ead6d954fd601b875cd3d5c08a74505ba8cbad`。

## 目标

把已接受的 F05 owner 候选按行为移植/适配到**当前** StockWiki 代码基线，而非把旧分支盲目 cherry-pick。交付可通过 StockWiki 公共 query CLI 暴露的 `query_facts` / `export_facts` 2.7.0 producer，能力声明与可执行路径一致，旧 query/capability wire 保持兼容。

F05-FACT-QUERY-01 已交付的候选是行为参考，不重做整份研究。当前 owner 候选状态 `partial`；本包只负责 StockWiki owner 代码。IQS 消费端已在 `acb03e3` 主线，不在本包中修改。

## 隔离基线和写入范围

在用户确认的本机 Projects 目录创建全新 Lab，只从 `StockWiki` 的锁定 tracked commit 克隆；不复制 source 工作树内容，不创建 shared worktree，不改 source branch/index/remote。Source 当前有四个既存未跟踪路径：`data/companies/688012.SH/research_source_links.sqlite`、`data/dashboard_onboarding/`、`data/dashboard_research_binding/`、`runs/c16b/`。这些路径内容禁止读取、复制、修改或清理。输入状态见 [inputs.lock.json](inputs.lock.json)。

只在 Lab 中允许变更：

- `config/quick_scan_facts_query.schema.json`、依赖声明 `pyproject.toml`；
- `stockwiki/quick_scan_facts_contract.py`、`stockwiki/quick_scan_facts_query.py`；
- 与 owner 实际接线直接相关的现有文件：`stockwiki/quick_scan_query_capture.py`、`stockwiki/quick_scan_query_contract.py`、`stockwiki/quick_scan_query_v2_cli.py`、`stockwiki/quick_scan_subject_authority.py`；
- 对应 F05 测试：`tests/test_c06_facts_query.py`、`tests/test_quick_scan_facts_scope.py`、`tests/test_quick_scan_facts_wire.py`；
- `docs/handoff/F05-OWNER-MAINLINE-02/`。

若当前 base 的结构使必须改其它文件，只改 Lab；在 handoff 说明实际原因与精确路径。不得改数据库 schema、现存事实/观察、名单、生产配置、其他 StockWiki 模块或 IQS 代码。

## 公开接口

保持接受候选的 CLI 入口形态：

```powershell
python -B -X utf8 -m stockwiki.quick_scan_query_v2_cli `
  --root <owner-workspace> --iqs-code-root <IQS-root> --request <request.json>
```

从 `<owner-workspace>` 作为工作目录运行；`request.json` 放在 Lab/TEMP。query 会按既有协议写入 snapshot/capture，故 E2E 的 `--root` 必须是本包自建的临时 owner workspace，不能指向 source repo、真实用户 root 或其生产路径。

Capabilities 使用同一 CLI 的只读入口 `--capabilities --capabilities-version 1.1.0|1.2.0`，有请求时使用 `--capabilities-request <request.json>`。`2.7.0` operation 只有 `query_facts` 与 `export_facts`；consumer wire/schema 以 IQS 锁定输入为准。不得因实现方便改操作名、把 `facts_available=false` 固定成 true，或把无覆盖/未知状态说成“没有事实”。

输入原始 observation 必须沿用当前 owner serializer、主体/查询绑定、来源引用和 snapshot capture；不能另建 facts 库或拼接跨主体、跨分部、跨时间事实。Strict 只给满足契约的关系；explore 可保留候选但状态必须明示。方向、期间、commercial stage、review status、分页游标、snapshot 与导出查询哈希都按冻结协议校验。

## 实施和测试

1. 在 Lab 建 RED，验证旧 CLI/能力回归与本包 owner 事实查询缺口；逐项比较候选与 `6d1e40b` 的变化，只移植所需事实 producer 行为。
2. 单元测试覆盖 schema/envelope、facts 与原始 observation/subject 的绑定、方向/期间/分部、strict/explore、unknown 与 complete-empty/partial-empty、重复冲突事实、来源/证据状态、稳定分页和 snapshot replay、`export_facts` 与原 query 同 hash。
3. 集成测试走当前 owner query serializer、`QueryReader`、capture/replay、公共 `quick_scan_query_v2_cli`；能力声明必须和可运行操作一致。至少一个合成 facts/关系进入 strict，一个反向/过期/未确认关系只在 explore 中出现或被明确排除。
4. 隔离 E2E 使用本包临时 StockWiki root，走 public CLI 的 capabilities→query→分页/回放→export。source repo 与其 untracked data 不参与测试。
5. 跑触及文件的测试、`python -B scripts/checks.py --static-only`；按 StockWiki `AGENTS.md` 在本包大节点是否满足时最多跑一次 full gate。费用/API/搜索/下载均为0。

如果只靠临时 synthetic owner store，包可交付代码实现，但不能声称真实 owner golden。只有源仓已公开文档明确的只读入口，且输出/TEMP 可完整限制在本 Lab 时，才可通过该公开入口获取最小真实 golden；严禁直接打开/复制 source 的 untracked SQLite。无安全只读入口时，标 `partial`，写清所缺入口；由总控在 owner 主线接好后采集真实 golden。

## 交付完成标准

- 允许路径内有本地 commit；定向与日常静态检查结果真实、可重跑；旧 wire 回归通过。
- 一名非作者独立 reviewer 对最终 commit 审查并复审修复；最终 review `approved`、没有未修 finding。
- `docs/handoff/F05-OWNER-MAINLINE-02/report.md` 与 `handoff.json` 完整记录基线、改动、schema/hash、真实测试计数、临时清理和未解决项。不推送 canonical StockWiki remote。
- “代码包完成”不等于 F05 整体关闭。F05 仍需总控在受支持的当前 owner runtime 上生成/复核真实 golden，并与 IQS consumer public CLI 做真实正反互操作。
