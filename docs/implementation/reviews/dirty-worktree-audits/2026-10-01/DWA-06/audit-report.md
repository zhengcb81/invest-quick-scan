# DWA-06 — StockQAbyLLM 未提交改动只读盘点（审计报告）

- 报告人：审计 harness（opencode）
- 任务卡：`task-packet.md`（同目录）
- 快照：`snapshot.json`（2026-10-01T20:35:25Z，62 条）
- 目标仓库：`C:\Users\郑曾波\Projects\StockQAbyLLM`（master @ `3c685dda28f67a00bd653ad257a121d3b8edebb8`）

## 1. 快照冻结核验

**开始时（全项通过）：**

- HEAD `3c685dda…ebb8` ✅、分支 `master` ✅、状态条目 62 ✅
- porcelain-SHA256 重算 `ddf06a25…e33e6b` = 快照值 ✅
- `snapshot-files.jsonl` 中 62 个文件 SHA-256 全部重算一致，无一不可读 ✅

**结束时（存在 1 条漂移）：**

- 原有 62 条逐条核对、全部文件哈希不变
- **漂移：新增第 63 条 `?? nul`**（仓库根 0 字节文件，mtime 2026-10-01 21:54，即本次审计进行中产生）
- 结束状态 porcelain-SHA256 `d9951959…cacbebd` ≠ 快照 `ddf06a25…e33e6b`

按任务卡规则，这不是"快照失效"级别的漂移（旧 62 条已逐条全部哈希核对无误），因此对已核对部分交付全量盘点，`nul` 单列入漂移报告。

`nul` 说明：Windows 保留设备名，文件 0 字节，性质与某次 CLI 调用中误将输出重定向到 `nul` 字面路径可能有关；产生它的程序考证证据不足，**归因为"未知"**。审计窗口内该文件出现于本会话期间，极可能由某个并行进程或某轮测试创建。Owner 可安全删除（0 字节、Windows 保留名易与重定向互踩），且 `.gitignore` 无对应条目；是否清理由 owner 决定，审计方不代做。

## 2. 总体形态

- 快照期间是"quick-scan 可观测性/预算/工作存储"大型特性改造 + 后续格式化清理未提交的组合：暂存区**新增/修改 57 处文件共 +21,109/-206 行**（15 个 `A `、14 个 `AM`、28 个 `MM`），随后又在工作区进行一轮**全区 black 格式化**（涉及 36 个文件，+217/-140 行，大多数文件增删行 1～2 行、逐段格式重排）。
- 特性在 `experiments/scoring_comparison/`（Jev 与 LLM 打分对比实验）、`src/utils/quick_scan_*`（预算、健康度、成本、工作存储/传输/输出信箱）、`src/config/quick_scan_*`（模型策略与费率卡 schema）、`tests/`（单测/集成/live/fixture）等处落地。
- 关键"为什么没提交"证据：

  - 仓库最后一次提交为 2026-09-04 的 `3c685dd fix(ci): make tests self-contained and meet 87% coverage gate`；本批改动此后一直未提交。
  - `.pre-commit-config.yaml` 未暂存差异为 **`'-p', 'no:base_url'` 插件禁用**（`args: ['tests/unit/', '-v', '--tb=short', '-p', 'no:base_url']`）。插件名 `base_url` 无对应本地文件，也未 grep 到该插件定义，无法判断其来源；也未看到与之匹配的任何提交。**用途与是否保留 unknown**。
  - `.gitignore` 暂存 +6 行用于豁免 4 个 JSON schema/模板/新测试集文件不被 `*.json` 全局忽略。
  - 大量 `.py` 文件的未暂存差异为 black/isort 格式重排 + 少量实质修复（如 `src/providers/async_llm_provider.py` 的 `isinstance(provider, str)` mypy 修复、`src/utils/quick_scan_provider_health.py` 的 cooldown 比较/SQL 格式调整）。

## 3. 逐路径盘点表

（信心度：高/中/低；"为何未提交"无据均写"未知"）

| # | 状态 | 路径 | 用途（证据） | 证据 | 分类 | 为何未提交 | 建议动作 | 信心度 |
|---|------|------|--------------|------|------|-----------|----------|--------|
| 1 | MM | `.gitignore` | 豁免 4 个 schema/模板/新测试 JSON 不被 `*.json` 全局忽略 | diff vs `3c685dd`：+6 行 | 产品实现 | 与 quick-scan 特性一起打包大提交，尚无提交 | 可提交（随特性提交） | 高 |
| 2 | ` M` | `.pre-commit-config.yaml` | pytest pre-commit 中 `-p no:base_url` 插件禁用 | 工作区 diff（1 行） | 待审中的工作 | **未知**；本地未搜到对应插件定义 | **Owner 决策**：本地调试遗存 or 永久需提交 | 低 |
| 3 | `A ` | `docs/quick_scan_rate_cards.md` | quick-scan 费率卡设计说明 | 文件内明确描述 schema 与 Decimal 定价规则 | 测试/文档 | 属 quick-scan 特性，暂存后未提交 | 可提交 | 高 |
| 4 | `A ` | `examples/quick_scan_rate_cards.template.json` | quick-scan 费率卡空模板（`rate_cards: []`） | 文件本身 4 行 | 测试/文档 | 属特性打包 | 可提交 | 高 |
| 5–11 | `A `/`AM` | `experiments/scoring_comparison/*`（README / config_loader / jev_client / llm_scorer / render_report / run_comparison / test_set） | Jev vs LLM 打分对比实验框架 | `.workbuddy-ai/memory/2026-09-20.md` 列表完整对应；`README.md`、`test_set.json` 内容对齐 | 测试/文档（实验代码） | 本日 20:09 左右重新格式化后一并暂存，未提交 | 可提交（建议与 quick-scan 特性拆分为独立提交边界） | 高 |
| 12–35 | `MM`/`AM`/`A ` | `main_with_llm.py`、`pyproject.toml`、`src/cli/batch_processor.py`、`src/config/json_config_manager.py`、`src/config/llm_config.py`、`src/config/quick_scan_model_policy.schema.json`、`src/config/quick_scan_rate_cards.schema.json`、`src/core/models.py`、`src/core/qa_engine.py`、`src/providers/{async_llm_provider,base_llm_provider,llm_client,llm_provider,llm_response_parser}.py`、`src/runners/llm_runner.py`、`src/services/answer_generator.py`、`src/utils/{http_client,llm_integration,quick_scan_cost_resolver,quick_scan_provider_health,quick_scan_result_outbox,quick_scan_work_store,quick_scan_work_transport}.py` | quick-scan 特性主体：持久化工作队列/预算/健康度 ledger、成本费率解析、result outbox、transport hook，接入 LLM 客户端路径 | 暂存 diff 为整体新增/大改（如 `quick_scan_work_store.py` +2872 行）；未暂存仅是后续 black 格式化 + 少量 mypy 修复 | 产品实现 | 本日大改造 + 格式化收尾暂未提交；暂存侧大体完整 | 可提交（建议"特性主体 + 格式化 + 测试配套"合并提交边界；2872 行单文件是否折叠为子模块需 owner 判断） | 中 |
| 36–58 | `MM`/`AM`/`A ` | `tests/*`（fixture SQL、integration、live、unit 全梯度） | 与 quick-scan 特性配套的完整测试梯度（1500+ 行 work_store 单测、两版本 SQL fixture、CLI/budget 集成、live 双端测试、provider 测试） | tests 内 16 处 import 指向新模块；`tests/fixtures/quick_scan_work_store_v{1,2}.sql` 与 store 内 `SCHEMA_VERSION=5` 对齐 | 测试/文档 | 与特性绑定的暂存 + formatter 二次修改未提交 | 可提交（随特性一个提交边界） | 中 |
| 59 | `??` | `.codegraph/.gitignore` | CodeGraph 工具自身生成的忽略规则（db/cache/log 不入库） | 文件内容直观说明 | 生成物/缓存 | 工具自动生成，未提交 | 可忽略（或随工具链策略提交） | 高 |
| 60–61 | `??` | `.workbuddy-ai/memory/MEMORY.md`、`.workbuddy-ai/memory/2026-09-20.md` | 工作助手的个人/本地长期记忆与当日实验记录 | 内容为个人笔记 + 当日实验结论，含个人绝对路径（`C:\Users\郑曾波\…`） | 个人配置/数据 | 个人笔记不适合入公共仓库；也未纳入 .gitignore | 保留本地；建议把 `.workbuddy-ai/` 加入 `.gitignore`（owner 决策） | 高 |
| 62 | `??` | `progress_update.txt` | 2026-02-12 某轮"Phase 7.4 性能基准测试完成"的一次性进度记录（GBK 乱码） | 文件内容；`tests/benchmarks/` 产物已在提交历史内 | 临时文件 | 像是当时本地阶段性汇报草稿，事后未清理 | **疑似临时待 owner 确认**；不影响功能 | 中 |
| — | 漂移 | `nul` | 0 字节 Windows 保留名文件 | 结束期新增（见 §1） | 临时文件/未知 | 未知（产生进程不明） | 待 owner 确认后可删除 | 低 |

## 4. 临时文件/生成物的重建性说明

- `.codegraph/.gitignore`：由 codegraph 工具自身生成，可重建；建议保留（它保证 `*.db` 等不入库）。
- `.workbuddy-ai/memory/*`：不可随仓库重建，属用户个人记忆数据，**本地依赖明确**，不要清理。
- `progress_update.txt`：内容为 GBK 编码的阶段小结；从提交历史看 `tests/benchmarks/` 已存在、`pyproject.toml` 的 `pytest-benchmark` 依赖已含，该文件已无有效作用，**疑似可归档/删除**（审计方不做删除）。
- `nul` 漂移文件：0 字节；是否有任何脚本依赖未知，由 owner 确认。

## 5. "可提交"内容的完整性与提交边界建议

- **quick-scan 特性主体**：暂存侧包含 schema、store/transport、outbox、cost resolver、provider health、llm_client/llm_provider 等适配层 + `pyproject.toml` + `.gitignore` 豁免 + tests 全梯度，源码↔测试 import 自洽（见 `tests/unit/test_quick_scan_work_store.py:14-31` 等）。**缺口**：`experiments/scoring_comparison` 属另一独立目的，建议**拆分提交**；`progress_update.txt`/`.workbuddy-ai`/`.codegraph`/`nul` 均不应进入该提交。
- **black/isort 格式化收尾**：工作区相对暂存区为单轮统一格式化 + 1 处 mypy 修复，建议与特性主体合并提交，或 `git add -u` 后一并提交（审计方不代做）。
- **审阅缺口**：`quick_scan_work_store.py` 单文件 2872 行、含 schema v5 与多版本 fixture；是否按"单 PR 单模块"拆分由 owner 定。`pre-commit` `no:base_url` 插件禁用缺证据链，**需要 owner 决策**保留/删除。

## 6. 汇总结论

| 分类 | 数量 | 项目 |
|------|------|------|
| 产品实现（可提交/需配套测试） | 9 | 特性主体 + tests 全梯度 + `.gitignore`（合并组） |
| 实验代码/文档（可与特性解耦提交） | 7 | `experiments/scoring_comparison/*` |
| 个人配置/数据（保留本地） | 2 | `.workbuddy-ai` memory ×2 |
| 生成物/缓存（可忽略） | 1 | `.codegraph/.gitignore` |
| 疑似临时待 owner 确认 | 2 | `progress_update.txt`、`nul`（漂移新增） |
| 待审中的工作（需 owner 决策） | 1 | `.pre-commit-config.yaml`（`no:base_url`） |
| 删除/重构 | 0 | — |

**风险提示：**

1. 本地开发目录含有 `llm_apis.json`（已被 `.gitignore` 第 6 行正确覆盖，未出现在任何状态条目中）✅ 无泄漏迹象；审计全程未读取其内容。
2. 未暂存的 `.pre-commit-config.yaml` 保留与否证据不足（插件 `base_url` 不存在于常见插件集），不要随特性一起提交。
3. 漂移 `nul` 是审计窗口内新出现的第 63 状态条目，快照契约再冻结需由 owner 确认新基线；除此之外结束时状态未变动。

**不能判断项（"未知"标注）：** `.pre-commit-config.yaml`（插件来源）、`nul`（产生进程）。其余各项均给到直接证据（diff、文件内容、相关提交或交叉文档），未做事实性推测。
