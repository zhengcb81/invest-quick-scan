# DWA-03 审计报告 — QAbyLLM 未提交改动只读盘点

- 审计时间：2026-10-01（快照对照基线 2026-10-01T20:35:25Z）
- 审计方式：只读（无暂存/提交/清理；未读取任何敏感文件内容；除一次已恢复的审计自有临时文件误写外零改动）
- 快照：`snapshot.json` / `snapshot-status.txt` / `snapshot-files.jsonl`；仓库 `C:\Users\郑曾波\Projects\QAbyLLM`；分支 `main`；HEAD `64ec7721af3b9a2e80b1a1c580a85a8d0610ca51`

## 1. 快照核验结果

| 项目 | 快照记录 | 开始重跑 | 结束复跑 | 结论 |
|---|---|---|---|---|
| HEAD | `64ec7721af3b…` | 相同 | 相同 | 一致 |
| 分支 | `main` | `main` | `main` | 一致 |
| 状态条目 | 67（` M`=7, `??`=60） | 66（` M`=7, `??`=59） | 67 | 见下 |
| Porcelain SHA-256 | `cc17c9a7…86b8` | `3ee6ccec…` | `cc17c9a7…86b8` | 见下 |
| 文件哈希 | 66 条 hashed | 全部复算 | 66/66 吻合，0 missing，0 mismatch | 一致 |

**开始的表面不一致及成因（已查明）**：

1. 重跑 `status_command` 时 `.claude/settings.local.json` 未出现。证据：`C:\Users\郑曾波\.config\git\ignore:3` 含规则 `**/.claude/settings.local.json`（全局 excludesFile，`git check-ignore -v` 命中）。快照 harness 当时显然未受该全局 ignore 影响——差异为环境口径，非工作树变化。文件本体仍存在（`.claude/` 目录 mtime 2025-11-08；文件按 manifest 172 字节，2025-09-16 20:59:06Z），未删除。若需严格可复现口径，建议 owner 在 `status_command` 中固定 `-c core.excludesFile=` 后重制快照。
2. 复核中曾出现 `?? .dwa03v2.py`：**这是审计校验脚本误写入仓库的临时文件，属审计方操作错误**，已立即删除恢复原状，并已在最终核验中确认工作树与快照逐字节一致。
3. 快照自洽性：由 `snapshot-status.txt` 原文条目行计算得 `cc17c9a7…86b8`，与 `snapshot.json` 记录一致。

**结论**：HEAD、分支、66 个文件 SHA-256、其余 66 条状态条目在开始与结束时均与快照完全吻合；结束时状态摘要恢复为 `cc17c9a7…86b8`。审计期间工作树稳定，**无内容漂移**；唯一状态口径差异是全局 ignore 隐藏了 `.claude/settings.local.json`。

## 2. 未提交状态逐条盘点（67 条）

背景证据：仓库共 4 个提交，HEAD `64ec7721`（2025-06-07，"项目完成：添加项目总结文档"）。全部未提交内容分两批生成：① 2025-06-07～06-08（RAG 系统扩展，manifest mtime 群组证据）；② 2025-09-15～09-16（配置/验证/波特五力模块群，mtime 群组证据 + `tests/conftest.py` 针对"答案验证系统"）。

### A 组：已跟踪文件的修改（7 条，` M`）— 产品实现，未提交

| 路径 | 用途证据 | 为何未提交 | 建议 | 信心度 |
|---|---|---|---|---|
| `.gitignore` (+42/-2) | diff 内容为新增 RAG 忽略段（`vector_db/`、`test_config.yaml`、模型缓存等），且同一段落重复抄写两遍、结尾无换行——多次草率修改的痕迹 | 伴随 RAG 扩展修改，从未提交（HEAD 之后所有改动均未提交） | 清理重复段后与配套代码一起提交 | 高 |
| `PROJECT_SUMMARY.md` / `README.md` (各 +164±) | ±160 行级改写；项目总结类文档同步新模块 | 同一未提交工作 | 随实现提交 | 中（未逐字比对，规模证据为主） |
| `config_example.yaml` (+161) | 新增 RAG 相关配置项 | 同上 | 随实现提交，先核对无真实密钥 | 中 |
| `enhanced_dashboard.html` (±1580) | 大幅改写的仪表板 | 同上 | 与 `enhanced_dashboard_backup.html`、`modern_dashboard.html` 一并做 owner 决策后提交 | 中 |
| `qa_system.py` (+106±) | 核心系统扩展 | 同上 | 随实现提交 | 中 |
| `requirements.txt` (+11/-1) | diff 实证：新增 chromadb、sentence-transformers、langchain 等 RAG 依赖；尾部无换行 | 同上 | 提交（依赖声明与代码边界应成一组） | 高 |

### B 组：RAG 系统新模块（9 条，`??`，2025-06-07/08 群）— 产品实现

`rag_system.py`（25.9KB，头注释"本地RAG知识库系统，支持文档扫描、向量化存储和基于知识库的问答"）、`document_processor.py`、`hybrid_retriever.py`、`network_search.py`、`ocr_table_processor.py`、`conversation_manager.py`、`plugin_manager.py`、`answer_verifier.py`（54.8KB）、`check_deps.py`。

建议：与 A 组同类工作，属同一未提交实现批次。未提交原因同上（从无提交动作）。信心度：高（注释头 + requirements 条目相互印证）；"为何未提交"为证据不足项：HEAD 提交信息称"所有功能已实现"但未包含它们，准确意图未知。

### C 组：2025-09-15/16 新增模块（8 条，`??`）— 产品实现（第二批）

`config_manager.py`、`llm_providers.py`、`logging_config.py`、`setup_logging.py`、`porter_analysis.py`（头注释"波特五力模型分析 - 直接使用现有向量数据库"）、`simple_porter.py`、`run_analysis.py`、`porter_five_forces_海康威视.json`（分析产物）。

为同一批未提交的分析功能扩展；为何未提交：未知（无相关提交或文档痕迹）。建议合并入提交边界。

### D 组：测试/辅助脚本

`tests/conftest.py`（头注释"为答案验证系统测试提供共享的fixture"）— 值得提交，但对应测试用例文件缺失（`tests/` 下仅 conftest 出现在状态中），有测试缺口。

`quick_test.py`、`simple_test.py`、`install_dependencies.py`、`install_rag_deps.py`、`install_deps.bat`、`setup_rag.bat`、`run_rag_analysis.bat`、`install_rag_simple.bat`、`setup_python_alias.bat`、`fix_python_path.bat`、`fix_python_simple.bat`、`fix_python_permanently.ps1`、`check_python.bat`、`python_check.py`、`diagnose_python_path.py` — 装机/环境修复脚本，个人环境排障性质（如 fix_python* 系列）。建议本地保留、不提交（owner 可选择性提交通用安装器）。

### E 组：文档（3 条 `??`）— 文档

`PYTHON_INSTALL_GUIDE.md`、`RAG_IMPLEMENTATION_SUMMARY.md`、`USAGE_GUIDE.md` — 与实现配套的使用/总结文档，适合随实现提交（提交前先审阅是否有个人路径/凭据描述）。

### F 组：临时文件/生成物（24 条目级，`??`）— 疑似临时，可删除，但需 owner 确认

- 18 个数字命名文件 `0.0.10`～`6.0`（mtime 全部落在 2025-06-07 23:26–23:33 的 7 分钟窗口）：内容实证为 pip 安装命令输出的碎片（如 `0.19.0` 内文是 `Requirement already satisfied: python-dotenv … 1.0.0`；文件名 = requirements.txt 中出现的版本号），属安装排障时误重定向的产物。可重建，无本地依赖价值。**建议：删除，但留 owner 确认（本卡禁止清理）。**
- `tatus`（53 字节，2025-06-08 19:52）：内容为丢失 `g` 的重定向 `git status > tatus` 输出，仅含当时 HEAD `aaaacd3 … 添加交互式仪表板和启动器` 一行。误输产物，建议删除（owner 确认）。
- `env_check.py`、`setup_environment.py`：各仅 1 字节（一个空格，`od -c` 实证）。失败/中断的引导脚本残根，建议删除（owner 确认）。
- `enhanced_dashboard_backup.html`（43.9KB，2025-06-08 19:46）：已跟踪 `enhanced_dashboard.html` 的手工备份副本（命名与时间紧邻主文件改动）。被备份目标的旧版已在 git 历史中，备份可由 git 恢复，建议 owner 确认后忽略或删除。
- `.pytest_cache/`、`.ruff_cache/`：目录级缓存（不在 porcelain 清单内，被忽略规则覆盖），可重建，可忽略。

### G 组：个人配置/数据（1 条 `??`）— 需保留本地，不提交

`.claude/settings.local.json`：敏感路径（快照按策略仅记元数据，本审计未读取内容）。属于本地个人工具配置；本机全局 ignore 已覆盖它（证据见第 1 节）。建议保留本地、永不提交（若要跨机共享可另议），repo 内 `.gitignore` 可补一条显式规则以防其他环境泄漏。

## 3. 汇总结论

| 类别 | 数量（条目） | 建议 |
|---|---|---|
| 产品实现，可提交（A+B+C+E + tests/conftest.py） | 约 26 | 建议提交边界：① RAG 内核（A 组代码 + requirements + B 组）② 2025-09 批次（C 组 + conftest.py，缺口：answer_verifier 的测试仅有 conftest、无测试用例，未验证即提交需注明）③ 文档/仪表板随各自批次。提交前审阅 config_example.yaml 与文档中的个人路径 |
| 疑似临时/可删除（F 组） | 24 | 均有可复现来源（pip 输出重定向、误输重定向、1 字节残根、手工备份）；均可重建或由 git 历史替代，建议 owner 确认后删除，本审计未执行 |
| 个人配置，需保留本地不提交 | 1 | `.claude/settings.local.json` |
| 需 owner 决策/未知原因 | 全体"为何未提交"的准确性 | HEAD 提交自称"所有功能已实现"却与全部未提交内容脱节，真实未提交原因未知，未推测为事实 |
| 审计自身错误 | 1 起已恢复 | 曾误写 `.dwa03v2.py` 入仓库，已删除并经终检确认恢复；此外工作树零改动 |

风险提示：唯一持久风险是 67 条未提交内容（含约 1613 行式主实现）仅存于工作树，建议 owner 处理删除项后尽快按上述边界提交固化。审计全程只读（除已披露并恢复的临时文件），未读取任何敏感文件内容，未提交/暂存/清理任何仓库内容。
