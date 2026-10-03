# DWA-04R-EXT — revenue-forecast ACL 解锁后 1985 条 `??` 分类审计（只读）

- 任务编号：`DWA-04R-EXT`；上游报告 `docs/implementation/reviews/dirty-worktree-audits/2026-10-02-reaudit/DWA-04/report.md`（本报告沿用其 §4「未知集合」与 §6「建议表」的格式约定）
- 审计方式：独立只读 harness。目标仓库全程零写入；本报告为唯一交付物，写入 `C:\Users\郑曾波\AppData\Local\Temp\dwa-reports\DWA-04R-extended-report.md`
- 目标仓库：`C:\Users\郑曾波\Projects\revenue-forecast` ｜ 分支 `fcap` ｜ HEAD `5319ee263c4af41ac255938c25bebd32cce56f66`
- 审计对象：DWA-04 §4 记载的 1985 条「可见性受限未知」`??`（1971 条 `.tmp-zr408-unit*` + 14 条 `.planning/…/reviews/revenue/scratch/*`），ACL 解锁后首次可读、可分类
- 报告日期：2026-10-03；未执行任何 commit / add / 删除 / 清理 / ignore 修改 / 测试运行 / 网络访问

## 1. 开始 / 结束核验（会话内 verdict: **PASS — 无漂移**；起始值 ≠ 2401，已精确记录并归因）

| 核验项 | 任务卡期望 | 开始时实测 | 结束时实测 | 判定 |
|---|---|---|---|---|
| `git status --porcelain=v1 -uall` 条目数 | 2401（±并发变化） | **1985**（≠2401，精确记录） | **1985** | 起止一致，0 漂移 |
| 状态前缀计数 | 12 ` M` + 2389 `??` | **0 ` M` / 1985 `??` / 0 其它** | 同左 | 起止一致 |
| 条目清单逐行 diff | — | 基线 `_status_start` 1985 行 | 与开始快照 **diff = 0 行** | 一致 |
| HEAD | — | `5319ee263c4af41ac255938c25bebd32cce56f66` | 同左 | 一致 |
| 分支 | — | `fcap` | 同左 | 一致 |
| status stderr | — | 无告警（4 组目录已可读） | 无告警 | 一致 |
| `.git/index` mtime（元数据） | — | `2026-10-02 22:20:20 +0100` | 同左 | 未被本会话改写 |

**与 2401 的差额归因（−416 = −12 ` M` − 404 `??`，完全可归因、非并发噪声）**：DWA-04R 报告 §6 建议的四个批次已由 owner 授权落库，发生于 2026-10-02 22:14–22:20 +0100（即 2401 期望值成文之后、本会话之前）：

| 批次 commit | 说明 | 消耗的可见条目 |
|---|---|---|
| `9152528d` | batch-A 规划证据（numstat 360 行 = 325 文本 + 35 二进制，与提交信息「360 paths」闭合） | 5 ` M` + 355 `??` |
| `23ac4357` | batch-B 产品 3 文件 | 3 ` M` |
| `a00211ee` | batch-C 运行时台账 4 文件 | 4 ` M` |
| `5319ee2` | batch-D `.gitignore` +5 行（`.tmp-r41-mutation/`、`.bak`、`weekly-run-*.log`、`h2.log*`）；h2 两个 0 字节 `??` 同批删除 | 46 `??` 转 ignore + 1 `??` 日志 + 2 `??` 删除 |

对账：`5+3+4 = 12 M` ✓；`355+46+1+2 = 404 ??` ✓；`416 − 416 = 0` 剩余，`1985 + 0 = 1985` ✓。批次 D 提交信息原文亦自我印证："Post state: 1985 untracked entries remain — exactly the audit's visibility-limited unknown set, untouched by design."

**观察（记录、非违规）**：`--ignored` 变体的 status 另报 3 行 `Permission denied`（`.planning/…/filing/tests/pytest_tmp/`、`.review-zr407-20260818/company-wiki/.pytest_cache/`、`.review-zr407-20260818/tmp-wiki-focused/`）——均**不属于本次 4 组范围**，仍为 ACL 受限，按 DWA-04 §4 惯例只记录不推断。

## 2. 分组清单（inventory）

状态条目总数 `657×3 + 14 = 1985` ✓。三组 `.tmp-zr408-unit*` 结构完全同构（下表并列）；盘上文件数（1287/组）> 状态条目数（657/组）的换算：**1287 = 606 个 `.git` 内部文件（21 个内嵌仓，被折叠为 21 条目录级 `??`）+ 681 内容文件；681 = 40（藏于内嵌仓工作树内，随 21 条目折叠）+ 5（被 `.gitignore:16 artifacts/` 忽略）+ 636（逐文件列示）**，逐组闭合 636+21+40+5+606 = 1287 ✓。

| 组 | 状态条目 | 盘上文件 | 内容文件 | 内容字节 | 盘上总字节 |
|---|---:|---:|---:|---:|---:|
| `.tmp-zr408-unit/` | 657（636 文件 + 21 内嵌仓目录） | 1287 | 681 | 19,550,685 | 20,125,469 |
| `.tmp-zr408-unit-final/` | 657（同上） | 1287 | 681 | 19,550,721 | 20,125,503 |
| `.tmp-zr408-unit-retry/` | 657（同上） | 1287 | 681 | 19,550,718 | 20,125,499 |
| `scratch/{model-tests,publication-tests,pytest}/` | 14（1 + 8 + 5） | 14（另有 3 个已跟踪 sibling 不在本次 1985 内） | 14 | 272,920 | 272,920 |
| **合计（1985 条）** | **1985** | 3875 | 2057 | 58,925,044 | 60,649,391 |

### 2.1–2.3 `.tmp-zr408-unit{,-final,-retry}/`（每组）

- **形状**：450 个一级 case 目录，全部为 **pytest `--basetemp` 节点名**（`test_<函数名截断至≤31字符><实例数字>`；450/450 以数字结尾，238/450 恰为 31 字符截断）；每目录内为 fake-project 式测试树（`wiki/`、`companies/`、`proposals/`、`artifacts/`、`repo/`、`source/`、`scheduler.db` 等），相对组根深度 6–8 层（自仓库根计 7–9 段路径）。
- **内嵌 git 仓**：每组 21 个（7 个在 case 根、14 个在 `repo/`/`source/` 子目录），其 `.git` 内部共 606 文件/组（`HEAD/config/index/COMMIT_EDITMSG` 等 312 + git hooks `*.sample` 294）。
- **二级条目直方图（unit 组，final/retry 同构）**：`(case 内直接文件) 348`、`wiki/ 45`、`companies/ 27`、`test*.db 20`、`test_wiki.md 15`、`repo/ 13`（内嵌仓）、`proposals/ 11`、`sectors/ 9`、`themes/ 8`、`artifacts/ 7`、`source/ 6`（内嵌仓）、`scripts/ 6`、`state/ 4`、`project/ 4`、`gold/ 4`、`destination/ 4`、`control/ 3`、其余零星。
- **扩展名直方图（内容文件 681/组；`*_wal/_shm` 为 SQLite 运行时伴生）**：`.md 204`、`.db 154`、`.json 70`、`.sqlite3 57`、`.yaml 53`、`.txt 30`、`.sqlite3-wal 17`、`.sqlite3-shm 17`、`.db-wal 16`、`.db-shm 16`、`.pdf 13`、`.py 12`、`.jsonl 8`、`.env 4`、`.source_catalog 2`、`.example 2`、`.bin 2`、`.lock/.gitignore/.bak/.archived 各1`。（另 606 文件/组为 `.git` 内部，见上。）
- **时间戳**：内容 mtime 全部落在 **2026-08-18 23:17–23:19**（unit→retry→final 依次 23:18:02 / 23:18:44 / 23:19:18 的墙钟嵌名，目录 mtime 23:18:22 / 23:19:06 / 23:19:35），与 ZR-408 工作单元（lease 2026-08-18T22:13Z）同夜。例外：12 个内嵌仓 `.git/index` mtime = 2026-10-01 21:26（仅索引元数据被外部触碰，无树内容变化迹象）。
- **三组同构性证据**：450 个 case 目录名三组两两 **diff = 0**；内容路径清单仅 13 处差异，全部为嵌入墙钟的文件名（`prop-new_entity-20260818-231802/231844/231918.json` 等）；内容字节差合计 ±36 B。⇒ 三组 = 同一套 450 测试的三次连续重跑。
- **代表性路径（每组 ≤3，以 unit 为例）**：
  1. `.tmp-zr408-unit/test_analyze_gaps0/wiki/companies/中微公司/wiki/公司动态.md`（285 B）
  2. `.tmp-zr408-unit/test_build_manifest_is_complet0/repo/.git/`（内嵌仓）
  3. `.tmp-zr408-unit/test_read_artifact_bound_uses_0/artifacts/n.json`（被 `artifacts/` 规则忽略，5/组）

### 2.4 `scratch/{model-tests,publication-tests,pytest}/`（14 条 `??`）

- **形状**：`model-tests/publication-registry0/`（1 文件）；`publication-tests/`（5 子目录 8 文件：`publication-registry0/`、`test_c1_atomic_write_complete0/`、`test_c1_atomic_write_replaces_0/`、`test_c2_registry_failure_exits0/`、`test_c3_same_input_twice_ident0/`）；`pytest/`（5 子目录，各含 `pub/publications.jsonl`）。case 名同样为 pytest 节点名截断惯例。
- **字节**：14 文件共 **272,920 B**（model-tests 6,178 + publication-tests 261,648 + pytest 5,094）。同级另有 3 个**已跟踪** sibling（`publication-failure-probe/{input.json,registrations.jsonl}`、`publication-probe-registry.jsonl`，33,437 B，commit `3a674f645`）——**不在 1985 内**，仅作对照。
- **扩展名**：`.jsonl 7`、`.json 7`。
- **时间戳**：mtime 2026-09-19 07:10–07:47（jsonl 内 `registered_at` 亦为 2026-09-19T07:10Z），与 `.planning/2026-09-19-three-project-history-audit` 审计会话同日。
- **代表性路径（≤3）**：
  1. `.planning/2026-09-19-three-project-history-audit/reviews/revenue/scratch/publication-tests/test_c3_same_input_twice_ident0/out1.json`（94,614 B）
  2. `.planning/2026-09-19-three-project-history-audit/reviews/revenue/scratch/model-tests/publication-registry0/publications.jsonl`（6,178 B）
  3. `.planning/2026-09-19-three-project-history-audit/reviews/revenue/scratch/pytest/test_c1_zijin_canary_journey_f0/pub/publications.jsonl`（1,482 B）

## 3. 分类与证据（含每组 5 文件抽样，静态推理，不跑测试）

分类结论：

| 组 | 条目 | 分类 | 关键证据 |
|---|---:|---|---|
| `.tmp-zr408-unit/` | 657 | **可重建临时**（pytest basetemp 测试夹具/运行产物） | 见下方抽样 + §4 交叉核对 + 溯源（§3.4） |
| `.tmp-zr408-unit-final/` | 657 | **可重建临时**（同上，第二次重跑） | case 名 0 diff、路径仅 13 处墙钟差异 |
| `.tmp-zr408-unit-retry/` | 657 | **可重建临时**（同上，第三次重跑） | 同上 |
| `scratch/*` 14 条 | 14 | **可重建临时**（测试输出，强 schema 证据）；但与 3 个已跟踪 sibling 同目录，去留带审计语境 → 建议保持待裁定 | 5 文件抽样（§3.2）+ §4 |
| 每组 5 个 `artifacts/n.json`（合计 15，已在状态外） | 15 | **可忽略**（已被 `.gitignore:16 artifacts/` 规则忽略，无需动作） | `git check-ignore -v` 命中规则行 |
| 需保留 | **0** | 抽样未发现独有证据：全部内容可由测试代码 + 仓内 fixture 推导 | 见 3.1/3.2 |
| 不能判断 | **0** | 4 组全部可读并完成抽样；（二进制内容的字节级复现性见 3.3 局限） | — |

### 3.1 临时组抽样（每组 5 文件，静态可推导性判定）

抽样内容（unit 组）及 final/retry 对照：

| # | 抽样文件 | 性质 | 可从测试代码推导？ |
|---|---|---|---|
| 1 | `test_analyze_gaps0/wiki/companies/中微公司/wiki/公司动态.md`（285 B，frontmatter + 空时间线） | 夹具生成的合成 wiki 页 | **是** — 由 `tests/unit/test_source_discoverer.py:128` 的 `test_wiki_with_gaps` fixture 流向 `SourceDiscoverer` 写出；`中微公司` 同样出现在 company-wiki `tests/acceptance/test_cw1_source_contract_receipt.py`；final/retry 同路径 **285 B 字节相同** |
| 2 | `test_append_log0/wiki/log.md`（82 B，`[2026-08-18 23:18/23:19] INFO query \| 测试日志消息`） | 运行时日志追加 | **是（内容级）** — 消息串为测试字面量；时间戳随重跑变化（unit 23:18 / retry 23:18 / final 23:19），字节级不复现 |
| 3 | `test_approve0/proposals/prop-new_entity-20260818-231802.json`（`title:"测试"`, `approved_by:"审核人"`） | 审批流输出 JSON | **是（内容级）** — 字段集为固定 schema，`proposal_id`/`approved_at` 内嵌墙钟（三组分别为 231802/231844/231918）；`prop-new_entity` 前缀由测试输入决定 |
| 4 | `test_build_extract_success0/companies/测试公司/raw/test.pdf`（8 B；同组 dry/scan/short.pdf 均 4 B） | 桩字节文件 | **是** — 4–8 字节非真实 PDF，即测试写入的哨兵字节 |
| 5 | `test_acquire_and_release_lease0/scheduler.db`（36,864 B，SQLite 3） | 租约调度器运行时库 | **是（结构级）** — 表结构由被测代码建表语句唯一决定，行内容为测试动作序列（case 名即 `test_acquire_and_release_lease`）；字节级含 SQLite 计数器/WAL，不保证逐字节复现 |

final/retry 两组各另抽 5 项（`wiki/…公司动态.md` 285 B 同尺寸、`log.md` 时间戳变体、`scheduler.db` 36,864 B 同尺寸、`test.pdf` 8 B、`sectors/半导体设备.md` frontmatter `sources_count: 5` 同构）：与 unit 组结论一致。

**文件名是否嵌 test case 名**：是——450/450 case 目录名 = pytest 节点名（截断 + 实例号），且 §4 交叉核对 5/5 命中真实测试定义。

### 3.2 scratch 组抽样（5 文件）

| # | 抽样文件 | 性质 | 可从测试代码推导？ |
|---|---|---|---|
| 1 | `model-tests/publication-registry0/publications.jsonl`（2 行样例，`schema_version:"3.7"`, `engine_version:"4.1.0"`, `registered_at:2026-09-19T07:10Z`） | 发布注册表追加日志 | **是（内容级）** — 键集为固定 schema；`input_sha256`/`line_sha256` 链由输入决定；时间戳不复现 |
| 2 | `publication-tests/test_c1_atomic_write_complete0/out.json` = `{"ok": true}`（13 B） | 测试断言输出 | **是** — 字面量 |
| 3 | `publication-tests/test_c2_registry_failure_exits0/input.json`（31,242 B，`"company_name": "Test Co"`, `"base_year": 2025`…） | 合成输入 fixture | **是** — 与 `test_c3_same_input_twice_ident0/input.json` **同尺寸同构**（"same_input_twice" 用例自证同一输入），纯 `"Test Co"` 合成数据 |
| 4 | `publication-tests/test_c3_same_input_twice_ident0/out1.json`（94,614 B，`historical_revenue` 链） | 流水线输出 | **是（内容级）** — 由 #3 输入经 `scripts/revenue_publication.py` 管线确定性生成（用例本身断言 out1≡out2 的 ident 性质） |
| 5 | `pytest/test_c1_zijin_canary_journey_f0/pub/publications.jsonl`（1,482 B） | 旅程测试的注册表输出 | **是（内容级）** — 同 #1 schema；由 `tests/test_ca302_three_journeys.py` 用例生成 |

### 3.3 可重建性结论（静态推理，不重跑测试）

- **内容级可重建：4/4 组成立**。证据链：文件名嵌 pytest 节点名 → 节点名命中真实测试定义（§4，10/10）→ 内容为 fixture 流向（`Test Co`、`中微公司`、`测试` 字面量）+ 固定 schema（publication jsonl、proposal JSON、wiki frontmatter）+ 被测代码建表（SQLite）。
- **字节级不可保证**：所有含墙钟的文件（log/时间戳文件名/注册表 `registered_at`/SQLite 内部计数）重跑会产生**新字节**；三组间 13 个墙钟文件名 + ±36 B 差异即为实证。因此「删除后如需考古 2026-08-18/09-19 那次运行的逐字节现场」不可恢复——但该等运行的**结论**已固化在已跟踪的 ZR-408 receipts 与审计文档中（§3.4）。
- **未抽样余量（诚实边界）**：681×3 内容文件中抽 15/2043；SQLite 全库行、40×3 个内嵌仓工作树文件未逐字节核验。内嵌仓对象内容源自夹具文件，但其 commit 对象含墙钟 → 同样是「内容级可重建」。

### 3.4 溯源（origin 已知，不再是 DWA-04 §4 的「未知」）

- `assurance/unified_completion/receipts/ZR-408/11_implementer_receipt.json:10`：`pytest tests/unit -q --basetemp <revenue>/.tmp-zr408-unit-verify (company-wiki)` —— **company-wiki 的 pytest 以 revenue-forecast 为 basetemp 根**，解释了为何 revenue-forecast `tests/` 中搜不到这些 case 名。
- `progress.md:9-10`（repo 根）：「显式 basetemp 均在 revenue-forecast。停止 PID 20528、25964…**故不删除 `.tmp-zr408-unit*`，避免影响非本会话可控的进程**」；停止点载明后续动作：「确认 PID 20528 已退出并**仅删除精确的 `.tmp-zr408-*` 目录**」。
- `.planning/2026-09-19-…/reviews/cross_history/source_blocks.json:30447`：前轮审计已判定「可读 `.tmp-zr408-unit`、`-retry`、`-final` **是测试 fixture**」。
- `assurance/runs/2026-09-11_r4-phase-b/reviews/B.DR-rev4.json:153`：ACL 受限期即已登记该三目录「内容不在 git 可见范围内」——本报告即当时要求的「在能读该 ACL 的环境由 owner 只读核查」的补全。

## 4. 交叉核对（case token ↔ 测试套件，grep 只读）

任务卡示例 token `written_manifest_round` 命中（另 4/4）。**tmp-zr408 的 5/5 命中在 company-wiki 仓的 `tests/unit/`**（basetemp 归属方，grep 仅读取）；**scratch 的 5/5 命中在 revenue-forecast 自己的 `tests/`**：

| case 目录 token | 命中（file:line） |
|---|---|
| `test_written_manifest_round_tr0` | `company-wiki/tests/unit/test_deletion_manifest.py:100` `def test_written_manifest_round_trips(tmp_path)` |
| `test_analyze_gaps0` | `company-wiki/tests/unit/test_source_discoverer.py:128` `def test_analyze_gaps(self, test_wiki_with_gaps)` |
| `test_adds_assessment0` | `company-wiki/tests/unit/test_batch_assessment.py:187` `def test_adds_assessment(self, tmp_path)` |
| `test_build_extract_success0` | `company-wiki/tests/unit/test_pipeline.py:49` `def test_build_extract_success(` |
| `test_read_artifact_bound_uses0` | `company-wiki/tests/unit/test_zr304_read_model.py:196` `def test_read_artifact_bound_uses_binding(tmp_path)` |
| `scratch/publication-tests/test_c1_atomic_write_complete0` | `revenue-forecast/tests/test_zr710_publication_txn.py` |
| `…/test_c2_registry_failure_exits0` | `revenue-forecast/tests/test_zr710_publication_txn.py` |
| `…/test_c3_same_input_twice_ident0` | `revenue-forecast/tests/test_zr710_publication_txn.py` |
| `scratch/pytest/test_c1_zijin_canary_journey_f0`、`test_c3_non_mining_journey0`、`test_c4_formal_receipt_chain_c0`、`test_c5_three_journeys_zero_si0`、`test_c6_same_engine_path_three0` | `revenue-forecast/tests/test_ca302_three_journeys.py`（5/5） |
| `scratch/model-tests/publication-registry0` | `revenue-forecast/tests/test_publication_registry.py`（+ `tests/conftest.py` 出现 `publication_registry`） |

对照结论：10/10 抽样 token 命中真实测试定义；case 名截断规则（≤31 字符 + 实例号）与 pytest 惯例逐字吻合。revenue-forecast `tests/` 对 tmp-zr408 token **0 命中**——与「测试跑在 company-wiki、basetemp 指向 revenue」的溯源一致，不构成反证。

## 5. 风险矩阵

| 组 | 删除会失去什么 | 保留的噪声成本 |
|---|---|---|
| `.tmp-zr408-unit*` ×3（60.4 MB，1971 `??`） | 2026-08-18 ZR-408 验证夜的**逐字节运行现场**（含 13 个墙钟文件名与当次 SQLite 状态）；**不失去**任何测试代码、夹具、或 ZR-408 结论（receipts/state 均已跟踪）；三次重跑中另两组为冗余副本，删两留一亦不损失信息 | ① 1971 条 `??` 使 `git status` 永远 1985 行，任何「工作树干净」断言必须特判（DWA-04 已因此多做一节 §4）；② 21×3 内嵌仓可能干扰递归 git 操作与清点工具；③ 60 MB 常驻；④ `progress.md` 停止点长期挂账 |
| `scratch/*` 14 条（273 KB） | 2026-09-19 审计会话的测试输出现场；同级 3 个 sibling 已入库，若未来审计要求「该 scratch 全量可追溯」则缺 14 个（但 sibling 已覆盖 probe 证据主线） | 14 条 `??` + `.planning` 下永久非干净；体量可忽略 |
| 15 个 `artifacts/n.json` | 无（已被 ignore，不在 1985 内） | 无 |
| 误判风险（本报告自身） | 若把「需保留」证据误判为临时：抽样未发现此类内容，但 2043 内容文件仅抽 15 —— **残余误判风险不可归零**，故任何删除仍须 owner 授权 | — |

## 6. 建议表（**只建议，不执行；任何删除 / ignore 修改均需显式 owner 授权**）

| 组 | 条数 | 建议 | 前置条件 |
|---|---:|---|---|
| `.tmp-zr408-unit/` | 657 | **keep-as-is（短期）→ 二选一由 owner 裁定**：(a) 删除；(b) 追加 `.gitignore` 规则 `.tmp-zr408-unit*/` | **requires explicit owner action**（owner 此前对未知来源文件拒绝删除；现来源已证明为 2026-08-18 ZR-408 pytest basetemp，但删除仍属显式动作）。删除前置：`progress.md:10` 停止点条件——确认 PID 20528/25964 已退出；**regenerable 证明为内容级而非字节级**（§3.3），若需保 08-18 现场则先归档再删 |
| `.tmp-zr408-unit-final/` | 657 | **可删除候选（三组中冗余度最高：与 unit 组仅 13 处墙钟差异）** | **requires explicit owner action**；同上 PID 前置；建议三组同批裁定，避免留一组删两组的不一致状态 |
| `.tmp-zr408-unit-retry/` | 657 | **可删除候选（同上冗余）** | 同上 |
| `scratch/{model-tests,publication-tests,pytest}/` | 14 | **keep-as-is，owner 二选一**：(a) 随 3 个已跟踪 sibling 一并 commit（对齐审计证据惯例）；(b) 删除（可由重跑同名测试节点 + 同 basetemp 内容级再生） | **requires explicit owner action**；若选 (a) 需 commit 授权（本 harness 未执行）；若选 (b) 建议先确认 09-19 审计会话已闭环无引用 |
| 15 × `artifacts/n.json` | 15（状态外） | **无动作**（已被 `.gitignore:16` 覆盖） | 无 |
| 任何 `git add/commit/clean/rm` | — | **不做** | — |

对账：`657×3 + 14 = 1985`；建议覆盖 1985/1985 = 100%。

## 7. 纪律声明

- **零仓内写入**：对 `revenue-forecast`、`company-wiki`、`invest-quick-scan` 均未执行任何 edit/delete/stage/commit/checkout/stash/clean/reset/ignore 修改；git 仅只读子集（`status`、`rev-parse`、`log`、`show --numstat`、`stash list`、`ls-files`、`check-ignore`、`diff` 空转）。
- **未运行任何测试**：全部可重建性论证基于静态推理（文件名惯例、fixture 流向、schema 比对、三组差分），无 pytest/python 项目代码执行。
- **无网络**：未发起任何网络访问。
- **唯一交付物**：`C:\Users\郑曾波\AppData\Local\Temp\dwa-reports\DWA-04R-extended-report.md`。审计期间曾在同一 Temp 目录生成的状态快照（`_status_start*.txt`）与 git-bash `/tmp` 中间文件已随收尾删除，仓内无任何本会话产物。
- **只读副作用记录**：`git status` 可能刷新 `.git/index` mtime（本会话起止均为 `2026-10-02 22:20:20`，未变）；一次 `--ignored` 探测输出 3 行他组 `Permission denied` 告警，已按惯例记录不处置。

## 8. 复现命令（全部只读）

```bash
# ① 起止核验（条数 / 前缀 / HEAD / 分支）
git -C "C:/Users/郑曾波/Projects/revenue-forecast" status --porcelain=v1 -uall | tee /tmp/st.txt | wc -l   # 1985
awk '{print substr($0,1,2)}' /tmp/st.txt | sort | uniq -c                                                   # 1985 ??
git -C "C:/Users/郑曾波/Projects/revenue-forecast" rev-parse HEAD; git -C "..." rev-parse --abbrev-ref HEAD  # 5319ee2… / fcap

# ② 分组条数（注意：git 会对含中文的路径加引号，须去引号后再取顶级目录）
awk '{p=substr($0,4); gsub(/^"|"$/,"",p); split(p,a,"/"); print a[1]}' /tmp/st.txt | sort | uniq -c
# .tmp-zr408-unit 657 / -final 657 / -retry 657 / .planning 14

# ③ 盘上文件 / 字节 / 形状
cd "C:/Users/郑曾波/Projects/revenue-forecast"
for g in .tmp-zr408-unit .tmp-zr408-unit-final .tmp-zr408-unit-retry; do
  find "$g" -type f | wc -l; find "$g" -type f -not -path '*/.git/*' | wc -l; du -sb "$g"
  find "$g" -mindepth 1 -maxdepth 1 -type d | wc -l; find "$g" -name .git | wc -l
done   # 1287 / 681 / ≈20.1MB / 450 / 21
find .planning/2026-09-19-three-project-history-audit/reviews/revenue/scratch -type f -printf '%s\t%p\n'

# ④ 三组同构性（case 名 0 diff；路径仅墙钟差异）
ls .tmp-zr408-unit | diff - <(ls .tmp-zr408-unit-final); ls .tmp-zr408-unit | diff - <(ls .tmp-zr408-unit-retry)   # 无输出
for g in .tmp-zr408-unit .tmp-zr408-unit-final .tmp-zr408-unit-retry; do
  find "$g" -type f -not -path '*/.git/*' -printf '%P\n' | sort | sha256sum
done   # 路径清单 hash 互异但 diff 仅 13 对墙钟文件名

# ⑤ 忽略规则命中
git check-ignore -v ".tmp-zr408-unit/test_read_artifact_bound_uses_0/artifacts/n.json"   # .gitignore:16 artifacts/

# ⑥ 交叉核对（token → file:line）
grep -rn "def test_written_manifest_round" "C:/Users/郑曾波/Projects/company-wiki/tests/"   # test_deletion_manifest.py:100
grep -rn "def test_analyze_gaps" "C:/Users/郑曾波/Projects/company-wiki/tests/"              # test_source_discoverer.py:128
grep -rln "c1_zijin_canary_journey" tests/                                                   # tests/test_ca302_three_journeys.py

# ⑦ 漂移归因（批次 A–D）
git -C "C:/Users/郑曾波/Projects/revenue-forecast" log -5 --format='%h %cI %s'
git -C "..." show --numstat --format='' 9152528d | wc -l    # 360（325 文本 + 35 二进制）
git -C "..." show 5319ee2 -- .gitignore
```
