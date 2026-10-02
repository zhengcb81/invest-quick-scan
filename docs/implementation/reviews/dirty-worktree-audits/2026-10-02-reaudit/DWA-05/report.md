# DWA-05R — StockInfoDownloader 未提交改动只读盘点（合规复审）

- 任务编号：`DWA-05R`
- 目标仓库：`C:\Users\郑曾波\Projects\StockInfoDownloader`
- 基线：`docs\implementation\reviews\dirty-worktree-audits\2026-10-02-reaudit\DWA-05\`（`snapshot.json` / `snapshot-status.txt` / `snapshot-files.jsonl`，捕获时间 2026-10-02T06:40:01Z）
- 执行方式：全程只读；报告与临时脚本仅写入 `C:\Users\郑曾波\AppData\Local\Temp\dwa-reports\`；未运行任何测试、脚本、下载或网络请求。

---

## 1. 快照核验（开始 + 结束）

`snapshot.json.status_command` 原样重跑，并核对 HEAD / 分支 / 条目 / 摘要，重算 manifest 中 4 条有哈希条目。

| 核验项 | 基线值 | START 实测 | END 实测 | 结果 |
|---|---|---|---|---|
| HEAD | `dcf2c64c175e1bccb1771078219c78f7a9abe8fa` | 同 | 同 | PASS |
| 分支 | `改版新下载器` | 同 | 同 | PASS |
| porcelain 条目数 | 6 | 6 | 6 | PASS |
| 状态构成 | ` M`=5, `??`=1 | 同 | 同 | PASS |
| 状态摘要 SHA-256 | `c34f77a8d6672089634a7377824829451b8b1a69b4eff668c6018c42f30015be` | 同 | 同 | PASS |
| 条目逐行 | 见 snapshot-status.txt 6 行 | 完全一致 | 完全一致 | PASS |
| `e2e_official_report.json` size/mtime/sha256 | 142 / 2026-04-16T21:21:42Z / `4b18be36…03d4` | 同 | 同 | PASS |
| `org_id_validation_report.json` size/mtime/sha256 | 893 / 2026-04-15T21:11:20Z / `3f9007a4…9b62` | 同 | 同 | PASS |
| `src/data/stock_orgid_mapping.json` size/mtime/sha256 | 8188 / 2026-04-15T22:25:39Z / `abf4b9fd…f1e` | 同 | 同 | PASS |
| `logs/debug_page_300750.html` size/mtime/sha256 | 142085 / 2026-04-15T18:10:44Z / `39fa2f0a…247c` | 同 | 同 | PASS |
| 禁读路径 | 仅元数据 | 仅元数据 | 仅元数据 | 合规 |

**结论：开始与结束核验全部 PASS，零漂移。** 摘要与 2026-10-01 冻结 digest 完全一致（`c34f77a8…15be`），即本卡相对前次冻结为零漂移，按卡继续逐路径盘点。

---

## 2. 逐路径盘点（6 条）

### 2.1 禁读路径（仅元数据，内容未知）

| 状态码 | 路径 | 元数据（os.stat 层） | 用途 | 分类 | 未提交原因 | 建议 | 信心度 |
|---|---|---|---|---|---|---|---|
| ` M` | `config.json` | size=8062 B；mtime=2026-04-17T19:10:10Z（UTC） | **按元数据记录，内容未知。** 未读取、未 grep、未复制、未打印、未哈希；用途判断="未知，需 owner 本地核查" | 不能判断 | 未知（内容未读，不推断） | 由 owner 本地自行查看 diff 并决定提交/还原/保留；审计侧不做任何内容级建议 | 元数据高 / 内容与用途无（未读） |
| ` M` | `.claude/settings.local.json` | size=7249 B；mtime=2026-04-16T21:24:43Z（UTC） | **按元数据记录，内容未知。** 同上，用途判断="未知，需 owner 本地核查"；另注 `.gitignore:35` 忽略 `.claude/`，该文件仍为 ` M` 说明其已被跟踪（ignore 不影响已跟踪文件） | 不能判断 | 未知（内容未读，不推断） | 同上；如属本地开发配置，owner 可考虑 untrack（需另行授权，本卡不执行） | 元数据高 / 内容与用途无（未读） |

> 合规声明：以上两行的全部信息来自 `git status` 输出、`Get-Item`（size/mtime）与 manifest 登记；两文件内容在本卡全程零接触。

### 2.2 有证据路径（生成来源与可重建性）

| 状态码 | 路径 | 用途（证据） | 生成来源 / 证据链 | 可重建性 | 分类 | 未提交原因 | 建议 | 信心度 |
|---|---|---|---|---|---|---|---|---|
| ` M` | `e2e_official_report.json`（142 B） | 官方 E2E 测试运行报告（`overall_success`/`browser_strategy`/`main_py_success`） | 写入点：`tests/e2e/official_e2e_test.py:343-350`（`open("e2e_official_report.json","w")`）；文档：`docs/testing/official_e2e_test.md:140-151`。工作副本 `timestamp=2026-04-16T22:21:42`（机器本地 UTC+1）与 mtime `2026-04-16T21:21:42Z` 精确对应，即由当前代码的一次成功运行产生；HEAD 版本为 2026-04-13 旧格式（含逐股票 `results` 数组），当前代码只写 4 字段摘要 → 本次改动=旧报告被新一轮运行覆盖 + 报告格式随代码演进 | 可重建：按 `docs/testing/official_e2e_test.md` 运行 `python tests/e2e/official_e2e_test.py`（需浏览器/网络/下载，本卡未运行）。内容含时间戳，逐字节不可复现，属运行记录类 | 可归档（运行记录） | 上次运行后未提交 | 二选一（owner 定）：①作为运行记录提交；②若不跟踪运行记录则 `git checkout -- e2e_official_report.json` 还原到 HEAD。建议先确认该文件是否应被跟踪（仓库已跟踪它，倾向①） | 高（写入点+时间戳闭环） |
| ` M` | `org_id_validation_report.json`（893 B） | orgId 批量验证报告（统计+明细+`mapping_file`+`timestamp`） | 写入点：`src/tools/legacy/validate_all_cached.py:95-106`（CWD 相对路径硬编码 `report_file="org_id_validation_report.json"`）。工作副本 `mapping_file="…\Temp\tmpt_y7nxwj\regression_test.json"` 与 `tests/unit/test_org_id_validation.py:249` 的 `regression_test.json` 命名吻合、`timestamp=1776287480` 与 mtime `2026-04-15T21:11:20Z` 精确一致 → 该副本极可能是**单元测试 `test_regression_batch_validation`（网络已 mock）运行时对仓库根目录报告文件的副作用覆盖**，而非对真实映射文件的正式验证；与 HEAD 的差异仅 `mapping_file` 临时路径与 `timestamp` 两行 | 可重建（测试路径）：重跑 `tests/unit/test_org_id_validation.py` 可再次产生同形文件；正式重建需运行 `python src/tools/legacy/validate_all_cached.py`（真实网络验证，本卡未运行）。逐字节内容依赖运行时刻，不可精确复现 | 疑似临时（测试副作用产物） | 测试副作用产生后未提交 | 不建议按现状提交（内容指向临时测试文件，非有意义的验证记录）。建议：①还原到 HEAD；②（另行授权的代码改动）让测试把报告写入临时目录避免污染仓库根——属代码审查建议，本卡不执行 | 中高（路径+时间戳双证据；具体触发进程未直接观测） |
| ` M` | `src/data/stock_orgid_mapping.json`（8188 B） | 股票代码→orgId 映射数据，被 `MappingManager` 默认加载（`src/data/mapping.py:51`），全仓多处引用（`src/core/config_constants.py:62`、`src/tools/legacy/orgid_utils.py:17` 等）；`tools/protect_expected_results.py:72-74` 将其列为受保护数据路径 | 内容差异：+175 行新增条目，形态统一为 `source:"auto", confidence:0.7`；写入点：`src/data/mapping.py:202-208`（`add_mapping(..., source="auto", confidence=0.7)`，即运行时 orgId 自动爬取缓存，见 `mapping.py:184-216`）。新增条目 `timestamp` 区间 ≈ 1776287871–1776291939 → 2026-04-15T21:17:51Z–22:25:39Z，末条时间戳与文件 mtime `2026-04-15T22:25:39Z` 精确一致 → 由 2026-04-15 一次或多次下载/爬取运行追加 | 部分可重建：重跑下载器/E2E（缺映射代码自动爬取，`docs/testing/official_e2e_test.md:160`）或 `src/tools/legacy/orgid_crawler.py` 可再次产生同类条目；但逐字节内容依赖当次爬取结果（网络/时效），精确复现=未知。机制证据强，触发该次运行的具体命令=未知 | 需保留（有信息价值的缓存数据） | 运行期自动追加，未提交 | 建议提交（owner 授权后）：属可持续累积的数据资产；提交前逐条 review 新增 175 行（确认股票代码/名称/orgId 合理）。审查缺口：本卡未联网校验 orgId 正确性 | 生成机制高 / 精确触发命令中（未观测） |
| `??` | `logs/debug_page_300750.html`（142085 B，582 行） | 页面源码转储：首 6 行为 `<!DOCTYPE html> lang="zh-CN"`、`author=深圳证券信息有限公司`（ cninfo/深交所披露页样式），对应股票 300750（宁德时代，见 `tests/e2e/official_e2e_test.py:130`） | **生成来源=未知**：当前工作树与全部历史提交中均未定位到写 `logs/debug_page_{code}.html` 的代码。穷尽性证据：`git log -S "debug_page" --all` 仅命中 4 个提交，其中写文件者为 `unified_downloader.py:424`（写 `logs/debug_page_{code}_p{page}.png`，.html 变体不存在）、历史 `tools/debug/debug_links.py:59`（写根目录固定名 `debug_page_source.html`）、`debug_page_structure.py`（写 `.log`）；`src/` 下 `open(...html...)` 写操作 grep 为零命中。mtime=2026-04-15T18:10:44Z（早于同日映射爬取时段）。`.gitignore:29` 仅忽略 `logs/debug_page_*.png`，**无 `.html` 规则**，故以 `??` 暴露 | **未知**：无可定位的重建入口；可能来自一次性/未提交的调试代码或人工保存 | 疑似临时（调试转储） | 无人跟踪的一次性调试产物 | 不建议提交。owner 二选一：①删除（需授权，本卡不执行）；②补 `.gitignore` 规则 `logs/debug_page_*.html`（需授权）。若认为有排查价值，先人工确认内容再决定 | 分类高（位置+ignore 缺口+无写入者）/ 生成来源低（未知） |

---

## 3. 提交边界建议（仅建议，不执行任何提交/删除/ignore 修改）

1. **可考虑提交（需 owner 精确授权后另行执行）**
   - `src/data/stock_orgid_mapping.json` — 数据资产，+175 行 auto 条目，建议提交前逐条 review。
   - `e2e_official_report.json` — 若仓库惯例跟踪该运行记录则随附提交；否则还原。
2. **不建议按现状提交**
   - `org_id_validation_report.json` — 疑似单测副作用（指向 Temp 内 `regression_test.json`），建议还原到 HEAD，并在代码层面（另行授权）修复测试污染根目录报告的问题。
   - `logs/debug_page_300750.html` — 调试转储，删除或 ignore（二选一，需授权）。
3. **审计盲区，owner 本地处理**
   - `config.json`、`.claude/settings.local.json` — 内容未知，仅凭元数据无法给出任何提交/还原建议。
4. **测试/审查缺口**
   - E2E 与真实 orgId 验证均需浏览器/网络，本卡按纪律未运行，报告类文件的"当前内容正确性"未复验。
   - 未联网核验映射新增条目的 orgId 真实性。
   - `validate_all_cached` 硬编码 CWD 报告路径（`validate_all_cached.py:104`）是可复现的仓库污染源，建议列代码审查项。
   - `.gitignore` 对 `logs/debug_page_*.html` 存在规则缺口（仅 png 被忽略）。

## 4. 汇总计数与风险

| 分类 | 数量 | 路径 |
|---|---|---|
| 可归档（运行记录，可提交或还原） | 1 | `e2e_official_report.json` |
| 可忽略 | 0 | — |
| 需保留（数据资产，建议提交） | 1 | `src/data/stock_orgid_mapping.json` |
| 疑似临时（不建议提交） | 2 | `org_id_validation_report.json`、`logs/debug_page_300750.html` |
| 不能判断（禁读，内容未知） | 2 | `config.json`、`.claude/settings.local.json` |
| **合计** | **6** | 与基线条目数一致 |

风险：低。6 条中 0 条涉及本卡可见的机密泄露面（禁读两文件内容零接触）；主要残留风险是 ①测试副作用持续覆盖根目录报告、②调试 html 因 ignore 缺口长期以 `??` 暴露、③禁读两文件用途对审计完全不透明——均需 owner 本地动作，本卡不执行。

## 5. 合规声明

- 目标仓库零写入：未编辑/删除/移动/暂存/提交/清理，未在目标仓库创建任何文件；临时脚本与本报告仅位于 `C:\Users\郑曾波\AppData\Local\Temp\dwa-reports\`。
- 未运行任何测试、会写文件的脚本、下载或网络请求。
- **`config.json` 与 `.claude/settings.local.json` 内容全程未被读取、grep、引用、复制、打印或哈希**（仅 `git status` 行 + size/mtime 元数据 + manifest 登记）；grep 采用排除式匹配（限定扩展名，两禁读路径的扩展名 `.json`/`.local.json` 不在任何检索模式内）。
- 仓库内文档仅作为待审数据引用，未作为对 harness 的指令执行。
- 开始/结束双次核验全部 PASS，无漂移，故本报告基于冻结基线归因有效。
