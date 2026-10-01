# DWA-05 审计报告 — StockInfoDownloader 未提交改动只读盘点（只读，未改动仓库）

- 审计时间：2026-10-01（对话内执行）
- 仓库：`C:\Users\郑曾波\Projects\StockInfoDownloader`
- 分支：`改版新下载器`；HEAD：`dcf2c64c175e1bccb1771078219c78f7a9abe8fa`
- 审计方式：仅读取、哈希、git diff/log 查询；无任何写入、暂存、提交或脚本执行。

## 1. 快照核验结果

| 项目 | 快照值 | 实测值 | 结果 |
|---|---|---|---|
| HEAD | dcf2c64c…aabe8fa | dcf2c64c…aabe8fa | ✅ 一致 |
| 分支 | 改版新下载器 | 改版新下载器 | ✅ 一致 |
| 状态条目 | 6（` M`=5, `??`=1） | 6 | ✅ 一致 |
| porcelain SHA-256 | c34f77a8…15be | c34f77a8…15be | ✅ 一致 |
| 4 个哈希文件 | snapshot-files.jsonl | 全部重算 | ✅ 全部一致 |

**开始与结束时均复验一致，审计期间工作树稳定，无漂移。** 以下归因基于快照基线（快照时间 2026-10-01T20:35:25Z；HEAD 提交于 2026-04-16，文件 mtime 均为 2026-04-15/16，晚于最后提交的改动）。

## 2. 逐条盘点表

| # | 状态 | 路径 | 用途/来源 | 证据 | 分类 | 为何未提交 | 建议动作 | 信心度 |
|---|---|---|---|---|---|---|---|---|
| 1 | ` M` | `.claude/settings.local.json` | Claude Code 本地个人配置；**敏感路径，按卡不复读内容**（哈希省略，mtime 2026-04-16） | 卡规定 + `.gitignore` 含 `.claude/` | 个人配置 | 无提交痕迹表明有提交意图；最近提交 9c46305 (2026-03-28) | 不提交，保留本地 | 高 |
| 2 | ` M` | `config.json` | 主运行配置；**疑似含密钥/令牌，按卡不读 diff 内容**（mtime 2026-04-17，晚于 HEAD 提交）。含 `"stock_code": "300750"` 段（仅 grep 定位，未读取其余内容） | 卡规定；`git log` 末次提交 9c46305 (2026-03-28) | 配置/不属于本次评审范围 | 超出 HEAD 提交后的本地运行调整，**未知** | owner 本地检查改动；不提交 | 高 |
| 3 | ` M` | `e2e_official_report.json` | E2E 回归运行生成的机器报告（2026-04-16T22:21，`overall_success: true`, `browser_strategy: "playwright"`）；diff 显示由 4 条详细结果裁剪为 3 行摘要 | diff 全文；末次提交 b581c0a (2026-04-13) | 生成物/测试 | 测试 .py 重构（e4ea9e2 起）后运行 e2e 时被改写且未回提交 | 可提交；或改为不追踪 | 高 |
| 4 | ` M` | `org_id_validation_report.json` | orgId 校验报表运行输出（2026-04-15），diff 仅映射文件临时路径（`%TEMP%\tmpt_y7nxwj\...`）+ 时间戳变化 | diff 全文；末次提交 b581c0a | 生成物/测试 | 正常校验流程重写，未回提交 | 可提交；或改为不追踪 | 高 |
| 5 | ` M` | `src/data/stock_orgid_mapping.json` | **追踪数据文件被运行时自动写入**：+25 条新条目（约 +175 行），均为 `source: "auto"`、`confidence: 0.7`，timestamp 1776287871–1776291939 ≈ 2026-04-15/16 | diff 全文；末次提交 e4ea9e2 (2026-04-15) | 运行时数据（新数据） | 爬虫 auto 补录后未做收尾（运行时直接写入追踪文件） | owner 决策：作为数据提交或转为不追踪 | 高 |
| 6 | `??` | `logs/debug_page_300750.html` | 142 KB cninfo 披露页对 `stock_code 300750` (宁德时代) 的 HTML 快照（**临时调试产物**），疑为调试时手动保存或调试时用 `.html` 变体 | 全目录 grep：仅 1 处代码命中 `logs/debug_page_*.png`（unified_downloader.py:424），**无代码生成 `.html` 变体** | 疑似临时产物 | 生成来源：**未知** | **不删**；owner 确认后处理 | 高 |

## 3. 缺口与提交边界建议（不执行）

- **建议提交**：`e2e_official_report.json`、`org_id_validation_report.json`（均为运行产物覆盖更新，适合提交以清 dirty 状态）——但审慎起见，先由 owner 决定是否将两者转为不追踪（见第 4 节）。
- **应保留本地 / 不提交**：`.claude/settings.local.json`、`config.json`。
- `stock_orgid_mapping.json` 的 25 条新增是**可判断的新增业务数据**（2026-04-15/16 自动爬取），可作为独立数据提交；提交边界：仅该文件（生成物报告文件单独提交，不混入）。

## 4. 补充说明

- 这两类生成物报告（3、4 号）与 `stock_orgid_mapping.json`（5 号）**共同反映了"运行时自动/本地输出未回提交"**；若保持追踪，建议按"覆盖新报告快照"单次提交或改为不追踪（`git rm --cached`）加 `.gitignore`，但须 owner 决策，尤其 5 号 mapping 含新业务条目。
- `config.json` 与 `.claude/settings.local.json` 应**严格假定部分内容含个人/敏感片段**；如需提交 config.json 的建议改动，请 owner 先手工 diff 审阅。

## 5. 汇总结论

| 类别 | 数量 | 条目 |
|---|---|---|
| 可归档（清 dirty 状态） | 2 | #3 e2e_official_report.json、#4 org_id_validation_report.json |
| 需保留本地、不提交 | 2 | #1 .claude/settings.local.json、#2 config.json |
| 新增数据，需 owner 决策 | 1 | #5 src/data/stock_orgid_mapping.json |
| 疑似临时，owner 确认 | 1 | #6 logs/debug_page_300750.html |

**主要风险**：`config.json`、`.claude/settings.local.json` 为疑似敏感路径，只记录元数据，未读内容，其具体改动内容属"**未知**"，不能据此推断；`stock_orgid_mapping.json` 的临时路径字符串亦可视为潜在机器本地信息泄露，若提交建议先清洗。

审计执行期间对仓库仅做读取、哈希与 diff/log 查询，无任何写入、暂存、提交或脚本执行。
