# SW-REPAIR-02｜备份、可比查询与UI六项整改

**PWF pin**: 本任务计划目录固定为 `docs/handoff/SW-REPAIR-02/planning/`（PLAN_ID=`SW-REPAIR-02`）。
解析失败时不回落到仓库根 `task_plan.md` 或 `.planning/` 下任何其他计划。

- 施工卡: `invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-07-wave2/SW-REPAIR-02.md`
- 共同规范: 同目录 `handoff-rules.md` / `interfaces.md` / `inputs.lock.json`
- 原整改卡: `invest-quick-scan/docs/implementation/reviews/SW-READY-01/remediation-card-2026-10-07.md`
- 独立报告: 同目录 `intake-review-2026-10-07.md`
- 基线: StockWiki `master@04dfc5190589a8bbe224a47e94b045779c884b80`（开工时 clean）
- 写授权: 用户在本任务分派中批准 —— 唯一 writer；源码 `stockwiki/quick_scan_{backup,backup_manifest,profiles,query,rows}.py`、`stockwiki/ui_quick_scan.py`、`stockwiki/ui_static/{app.js,index.html,styles.css}`；
  测试 `tests/test_quick_scan_{backup,profiles,query}.py`、`tests/test_ui_quick_scan.py`、`tests/test_e2e_quick_scan_ui.py`、新增 `tests/test_swr_*.py`；
  文档 `docs/quick-scan-backup-restore.md`、`docs/ui.md`、`docs/handoff/SW-REPAIR-02/`。
  新源码文件 / store 迁移 **未预授权**，需要时先列精确路径/迁移/证明再向用户确认。

## Goal

六项 SWR-1..6 固定反例全部闭合、WAL 正例保留、真实浏览器多条件 AND/OR 通过、旧 `9f552a67` 真实 snapshot 与未知状态兼容、环境清理与集中审查完成，交完整 handoff。

## Phases

### Phase 1 — 只读复核与反例映射
**Status:** complete

1. 复核当前代码与原 freeze（原 6 RED / 1 WAL positive pass），保留原 RED 证据，不回写。
2. 把原 7 场景映射到本仓测试（新 `tests/test_swr_*.py`），旧 query snapshot 必须由旧 Git 真实 producer 函数生成（`git show 9f552a67:stockwiki/quick_scan_query.py`），不手算 hash。
3. 公开 import 产生 synthetic subject 观察走真实 `import_package`，不手造 profiles。
4. 报备本包精确写路径清单。

**Next Step:** 写 `tests/test_swr_cases.py`（7 场景 RED 映射）并跑出原 6 fail / 1 pass。

### Phase 2 — SWR-1/2/3 备份恢复、owner 与 partial
**Status:** complete

- SWR-1: absent 与 existing-empty 恢复成功；非空/并发填入/junction/越界拒绝；检查到空才不授予删目录权限；失败保留原目标、只清自己的 staging。
- SWR-2: prune 仅处理真实 create 流程登记的受管完成备份；版本/结构/hash/名称/路径安全 + **trusted owner 记录**均核验；foreign/unknown/partial/损坏/链接全部跳过；旧无 owner 备份只读 verify/restore，不自动 adopt。
- SWR-3: finalize rename 纳入错误处理；注入失败不留可被 list/prune 当完成的 partial；manifest 成功字段不早于真实最终提交；崩溃恢复明确 partial 状态。
- 同批 TDD: 空/非空/并发、foreign 自洽 manifest、损坏/链接、rename 异常、WAL 已提交、旧备份兼容。

**Next Step:** 先 RED 后最小 GREEN。

### Phase 3 — SWR-4 projection/variant + SWR-6 查询兼容
**Status:** complete

- SWR-4: 两个 accepted 导入的不同 subject/scope/模型/语义变体均可见；未唯一选择时 ambiguous 或全展示；不取最近/最高/最后一条静默合并；`>=8` 不靠错误高分入选；同 issuer 多挂牌一行、不同 issuer 不并名。
- SWR-6: 旧 `9f552a67` 实际 snapshot 继续读 page2，IDs/顺序不丢不重；错查询/错条件 snapshot 仍拒绝；不放宽匹配换绿。
- 覆盖: 倒序导入、旧高分/新 unknown、不同模型同题、同 issuer 多挂牌、同名不同 issuer。

**Next Step:** RED → GREEN → 定向测试。

### Phase 4 — SWR-5 真实 UI 多条件
**Status:** complete

- 可增删至少两条分项条件；AND/OR 由 W07 服务器规则执行，JS 不重评分、不调 LLM/下载。
- query/snapshot key 绑定完整 leaf + combine；改任一 leaf 使旧 snapshot 失效；unknown 不补 5。
- 页面只展示存储数据；恶意短文本安全呈现。

**Next Step:** 改 `index.html`/`app.js` 控件与 state，接 W07 同一服务器规则。

### Phase 5 — 一批受影响测试 + 真实浏览器离线 E2E
**Status:** complete

- 受影响 unit/integration 一批，再一次真实浏览器离线 E2E（真实 StockWiki 服务 + 自有 SQLite，HTTP 模型边界 stub）。
- 断言 DOM/实际请求/业务，不用截图或 HTTP200 代替。
- 断言外部浏览网络/模型发送 0，仅本包 loopback HTTP 并留本地请求证据。

**Next Step:** 跑 `tests/test_swr_*` + `test_quick_scan_{backup,profiles,query}` + `test_ui_quick_scan` + `test_e2e_quick_scan_ui`。

### Phase 6 — 门禁、清理与交接
**Status:** complete

- 交付相关全量/静态门一次（`python -B scripts/checks.py --static-only` 提交前；`python -B scripts/checks.py --full` 一次集中）。
- 关闭本包服务/进程/浏览器，核端口与逐路径清理。
- `docs/handoff/SW-REPAIR-02/` 交模板全套 + 六项闭合表 + 原/新版本 + 旧实际 snapshot + owner/旧备份兼容说明 + 浏览器日志/截图 + 公开 query schema/capabilities/golden 实际现状与生成命令。
- TTL/replacement、W15、真实 QA 导入/双库恢复、F05/golden 明确 not_run。

**Next Step:** 集中独审后签本地 complete。

## Decisions Made

| # | 决策 | 理由 |
|---|---|---|
| D1 | 写路径先问用户再开工 | 手卡与共同规范都要求 authorized_paths 来自分派消息，不能复制卡自称获批 |
| D2 | 旧 snapshot 兼容走「无条件时保留旧 hash 口径」 | 手卡 SWR-6 明确允许「无条件筛选保留旧 hash 口径」，且不放宽跨 query 匹配 |
| D3 | trusted owner 记录复用现有 backup 管理结构，不建第二数据库 | 手卡禁止在投资库外创建第二研究数据库 |
| D4 | owner 记录落在 `backups/quick_scan/owner_registry.json`（用户已单独授权该新持久化文件） | “真实create流程登记”需要 name↔digest 绑定，纯 manifest 字符串不算 owner |
| D5 | 备份 manifest 读取策略冻结为 `SUPPORTED_MANIFEST_SCHEMAS` + 严格 MAJOR.MINOR.PATCH | 原 `1.garbage` 因只比主段被当 v1 |
| D6 | 恢复目标只做（复检后的）`rmdir`，永不 `rmtree` | “检查到空不授予删目录权限” + 失败保留原目标 |
| D7 | 变体可比键 = subject/revision + scope/security/listing + 题义版本 + 模型；组内按信息时点取最新 | 满足“倒序导入”与“不静默合并” |
| D8 | 变体逻辑放入已授权的 `quick_scan_rows.py` 而非新建源码文件 | `quick_scan_profiles.py` 超 600 行诊断告警；新源码文件未获授权 |
| D9 | legacy 观察的 `subject` 增加 `analysis_subject_id: None` 显式空值 | 让 payload 形状统一；`recorded=False` 仍禁止当作已绑定，原冻结用例的无条件取键不再 KeyError |
| D10 | 总控 `guarded_tests.py` 硬编码 IQS `runs/` 根，无法在 StockWiki 根复用且不得改总控脚本 | 自建 `run_frozen_acceptance.py` 复刻同一 audit-hook 语义，根在 StockWiki `runs/` |
| D11 | 交接 commit 分两次：先代码后 handoff | 共同规范要求“提交代码后固定 commit，再生成交接证据指向该 commit” |

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| （尚未发生） | | |

## Next Step

无。六项反例全闭合，本地 complete 已签；等总控派发集中审查与 QA/SW 联合离线 E2E。
