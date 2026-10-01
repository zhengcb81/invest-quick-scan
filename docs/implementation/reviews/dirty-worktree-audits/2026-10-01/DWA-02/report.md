# DWA-02 — MeetingConverter 未提交改动只读盘点（审计报告）

审计时间：2026-10-01（本会话）
仓库：`C:\Users\郑曾波\Projects\MeetingConverter`
分支：`master`；HEAD：`3c0b0531637589b3c4b14b83da8e1b3c3e1adf9b`

## 1. 快照核验与稳定性

| 检查项 | 快照值 | 实测值 | 结果 |
|---|---|---|---|
| HEAD | `3c0b05316…` | `3c0b05316…` | 一致 |
| 分支 | `master` | `master` | 一致 |
| 状态条目 | 1（` M`=1） | 1（` M` `.coverage`） | 一致 |
| 状态摘要 SHA-256 | `8d555fe53d67e73bb230719f396574c9f169b3398187847862d06985771cce84` | 同左 | 一致 |
| `.coverage` SHA-256 | `6670792e382d6b97dbb38bf06fdd719141692cfbe29f87bf703f1aa7cb3c5d9c` | 同左 | 一致 |

- 按任务卡用 `snapshot.json.status_command` 原样重跑状态命令，并按 `status_digest_canonicalization`（UTF-8 porcelain 条目以 LF 连接 + 尾随一个 LF）重算摘要，哈希全部匹配。
- 结束时复查 HEAD、分支、porcelain 状态，均与开始一致，**审计期间工作树稳定，无漂移**。
- 全程只读（git 的 status/rev-parse/log/show/diff/grep、sqlite 只读查询），未编辑、暂存、提交或运行任何会写仓库的命令。未读取任何疑似凭据文件。

## 2. 逐项清单（全量 1 条未提交状态）

| 状态码 | 路径 | 用途 | 证据 | 分类 | 为何未提交 | 建议动作 | 信心度 |
|---|---|---|---|---|---|---|---|
| ` M` | `.coverage` | coverage.py v7.12.0 测试覆盖率 SQLite 数据库 | `pytest.ini:2`、`pyproject.toml:22/32-37`；DB `meta`/`file` 表；`git log` 入库历史 | 生成物/缓存（可再生成，但被误提交入库） | 任一次本地 `pytest` 运行都会重写该文件；`.gitignore` 未忽略它，故每次测试后自动回到 ` M`。快照 mtime（2026-07-09T20:59:58Z）晚于最后一次触碰它的提交 ad73843（2026-07-09T21:37:37+01:00）约同日时段，符合“跑测试后自动再生成”模式。无人类编辑痕迹 | 分辨（需 owner 决策）：① 推荐 `git rm --cached .coverage` 并在 `.gitignore` 追加 `.coverage`；② 维持现状接受永久脏状态。**不建议提交当前二进制 diff** | 高（分类与成因）；建议动作本身为 owner 决策点 |

覆盖 DB 内容（只读元数据）：8 个被计文件，均为本仓库源码（`engines/__init__.py`、`engines/base.py`、`engines/whisper.py`、`engines/factory.py`、`engines/mimo.py`、`engines/fallback.py`、`translator.py`、`company.py`），无凭据类路径。

## 3. 生成物判断说明（对照任务卡要求）

- **可复现来源**：`pytest.ini` 的 `addopts = -v --cov=engines --cov=translator --cov=company --cov-report=term-missing`、`pyproject.toml` 的 `addopts = -v --cov=. --cov-report=term-missing`；运行 `pytest` 即在根目录生成/覆写 `.coverage`。
- **可重建**：是。删除后任意一次 pytest 运行立即重建，`coverage report` 亦可由重跑生成。
- **是否被依赖**：覆盖率二进制无长期价值，无下游依赖证据；历史快照即使需要也可重新跑测试取得。

顺带发现（不在本卡范围，仅提示）：`pytest.ini` 与 `pyproject.toml` 的 `--cov` 范围不一致（前者仅 engines/translator/company，后者为全仓库 `.`），属配置漂移隐患，建议 owner 归一化。

## 4. 提交适宜性与边界

- **问题根源在提交历史**：`.coverage` 于 8826aed（feat: MeetingConverter v2，2026-07-09 19:25+01:00）首次入库，ad73843（fix: P0 快速修复，2026-07-09 21:37+01:00）又提交了二进制更新。此后成为**永久脏文件**：任何测试运行都使其回到 ` M`，污染 `git status`，且无法通过提交当前版本解决（下一次 pytest 又会使其变脏）。
- **当前未提交 diff 不建议提交**：非有意改动，仅为下次测试运行的副产物。
- **建议提交边界（供 owner，本次未执行）**：单个小提交，如 `chore: stop tracking .coverage artifact`，内容为 `git rm --cached .coverage` + `.gitignore` 追加 `.coverage`（或标准 coverage 段写法）。无测试配套要求。
- **测试/审查缺口**：无需新测试；注意若远端跟踪分支也含该二进制文件，后续 pull/merge 易出现二进制冲突，是 untrack 的主要动机。

## 5. 汇总结论

| 类别 | 数量 |
|---|---|
| 可归档/应提交 | 0 |
| 可忽略（应加 ignore + untrack） | 1（`.coverage`） |
| 需保留本地 | 0 |
| 疑似临时/待 owner 确认 | 1（同上条，untrack 与否为 owner 决策） |
| 不能判断 | 0 |

**风险**：低。唯一未提交项为可再生的测试副产品，无凭据、无不可逆风险；主要危害为 `git status` 噪音与远端二进制合并冲突隐患。

**给发起者的交回件**：本报告（DWA-02）。无漂移需上报，可沿用本快照基线。
