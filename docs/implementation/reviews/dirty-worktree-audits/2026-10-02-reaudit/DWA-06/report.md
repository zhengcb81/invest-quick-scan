# DWA-06R — StockQAbyLLM 未提交改动只读盘点（细化复审报告）

- 报告编号：`DWA-06R`（任务卡 `DWA-06/task-packet.md`，通用纪律 `2026-10-02-reaudit/README.md`）
- 报告人：独立只读审计 harness（opencode）
- 目标仓库：`C:\Users\郑曾波\Projects\StockQAbyLLM`（`master` @ `3c685dda28f67a00bd653ad257a121d3b8edebb8`）
- 基线快照：`snapshot.json`（`captured_at_utc=2026-10-02T06:40:01Z`，63 条，digest `d995195971295b7da6aff13dfe9a37a04605808219d27d2eccf64029dcacbebd`）
- 全程零写入目标仓库：未编辑/删除/移动/暂存/提交/清理，未在目标仓库创建任何临时文件/脚本/报告；草稿与本报告均在 `C:\Users\郑曾波\AppData\Local\Temp\dwa-reports\`。未运行任何测试、写文件脚本、下载或网络请求。未读取任何疑似凭据内容（`llm_apis.json` 仅核对其被 `.gitignore:89 *.json` 覆盖的元数据）。

---

## 1. 快照核验（开始 / 结束）

**开始核验（全部通过）：**

| 项 | 快照值 | 重跑值 | 结果 |
|---|---|---|---|
| 状态命令 | `snapshot.json.status_command` 原样重跑 | 同 | ✅ |
| 分支 | `master` | `master` | ✅ |
| HEAD | `3c685dda…ebb8` | `3c685dda…ebb8` | ✅ |
| porcelain 条目数 | 63 | 63 | ✅ |
| porcelain SHA-256 | `d9951959…acbebd` | `d9951959…acbebd` | ✅ |
| 与 `snapshot-status.txt` 条目逐行 diff | — | 完全一致（含顺序） | ✅ |
| `snapshot-files.jsonl` 逐行重哈希 | 62 hashed | 62/62 一致，0 失败 | ✅ |
| `omitted-sensitive-path` | 1（`nul`） | 1（`nul`，**未读取、未哈希**） | ✅ 跳过 |

**结束核验（全部通过，无漂移）：**

| 项 | 快照值 | 结束重跑值 | 结果 |
|---|---|---|---|
| 条目数 / digest | 63 / `d9951959…acbebd` | 63 / `d9951959…acbebd` | ✅ |
| HEAD / 分支 | `3c685dd…` / `master` | 同 | ✅ |
| 起止 porcelain 输出 diff | — | 字节级完全相同 | ✅ |
| 62 个 hashed 行重哈希 | — | 62/62 一致，0 失败 | ✅ |

**判定：开始/结束均与快照完全一致，无任何漂移 → 正常交付全量逐路径盘点（非漂移报告）。**

附带基线交叉验证（增强前次结论可复用性）：本快照 62 个 hashed 行的 `path+sha256` 与 2026-10-01 前次 DWA-06 快照**逐条完全相同**，62 条状态码（去掉 `?? nul`）也与前次逐行相同 → 前次报告已核对的文件内容级证据在当前仍然成立，可逐条复用（差异见 §7）。

---

## 2. 总体形态（当前证据）

- 暂存区（`--cached` vs HEAD）：**57 个文件，+21,109 / −206**，为 “quick-scan 可观测性/预算/持久化工作存储” 特性主体 + `experiments/scoring_comparison` 实验框架 + 配套测试梯度 + `.gitignore` 豁免。
- 工作区（vs index）**有内容差异**的：**27 个文件，+217 / −140**（black/isort 格式重排 + 少量实质小修）。
- **新增证据（前次未记录）**：16 条条目（14 个 `MM` + 2 个 `AM`）的工作区列 `M` 为**纯 stat 项**——index blob 与 worktree blob 字节完全相同（`git hash-object` vs `git ls-files -s` 逐一比对），`git diff` 输出为空。即这些行的第二列 `M` 是 stat 缓存/换行重写造成的陈旧标记，不携带内容差异。
- 未跟踪（`??`）5 条：工具生成物 1、个人记忆数据 2、保留名空文件 `nul` 1、历史阶段草稿 1。
- 最后一次提交仍是 2026-09-04 的 `3c685dd fix(ci): make tests self-contained and meet 87% coverage gate`；本批改动此后一直未提交。
- QA-04 线索：仓库根 `q04_handoff.json`（11,683 B，mtime 2026-09-30 22:44，被 `.gitignore:89 *.json` 覆盖故不在 63 条内，未跟踪）。其中 `package_id=QA-04`、`status=partial`、`scope.owned_paths` = 本卡 4 条 QA-04 路径 + `q04_handoff.json` 自身、`open_items[6]` 明示“既有 55 项脏工作树原样保留、**nothing committed**、协调者需决定 Q04 文件是否可从共享脏树中分离”、`next_action` 同向。**本报告只读引用该线索做归因，不替 QA-04 收口。**

---

## 3. 逐路径盘点表（63 条全覆盖，无分组/通配）

状态码图例：`MM`=暂存修改+工作区修改；`M␠`=仅工作区修改（首列为空格）；`A␠`=仅暂存新增（次列为空格）；`AM`=暂存新增+工作区修改；`??`=未跟踪。
“未暂存内容差”指 `git diff`（工作区 vs index）实测；“stat 项”指 worktree 与 index 字节一致、第二列 `M` 仅为 stat 标记。
信心度：高/中/低；“为何未提交”无据一律写“未知”。

| # | 状态 | 路径 | 用途 | 证据 | 分类 | 为何未提交 | 建议动作 | 信心度 |
|---|---|---|---|---|---|---|---|---|
| 1 | `MM` | `.gitignore` | 豁免 quick-scan schema/模板/测试集 JSON，并忽略 quick-scan sqlite 工作库 | 暂存 diff +6（4 条 `!src/config/…schema.json`、`!examples/…template.json`、`!experiments/…test_set.json` + `/quick_scan_health.sqlite*`、`/quick_scan_work.sqlite*`）；未暂存无内容差（stat 项）；哈希同前次冻结 | 产品实现 | 与 quick-scan 特性同批暂存，特性整体尚未提交 | 可提交（随特性提交边界） | 高 |
| 2 | `M␠` | `.pre-commit-config.yaml` | pre-commit pytest 钩子加 `-p no:base_url` 禁用插件 | 未暂存 diff 恰 1 行（`args: [..., '-p', 'no:base_url']`，+1/−1）；`q04_handoff.json` `open_items[4]` 记载“基线测试环境需要 `-p no:base_url`（本地 pytest-base_url ScopeMismatch）”与该改动同源；插件 `base_url` 定义未在仓库中搜到 | 待审工作 | 环境规避性改动（QA-04 handoff 线索）；**是否永久保留未知** | 需 owner 决策：保留本地调试遗存 or 随特性提交（不建议随特性自动带入） | 中（来源归属中、永久性低） |
| 3 | `A␠` | `docs/quick_scan_rate_cards.md` | quick-scan 费率卡设计文档 | 首行 `# Quick-scan rate cards`；暂存 diff +36；哈希同前次冻结 | 测试文档 | 属特性配套文档，已暂存未提交 | 可提交（随特性边界） | 高 |
| 4 | `A␠` | `examples/quick_scan_rate_cards.template.json` | 费率卡空模板（52 B，`rate_cards: []`） | 暂存 diff +4；为 `.gitignore` 豁免对象之一 | 测试文档 | 属特性配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 5 | `A␠` | `experiments/scoring_comparison/README.md` | Jev vs LLM 打分对比实验说明 | 首行 `# Jev vs LLM …对比实验`；暂存 +137；与 `.workbuddy-ai/memory/2026-09-20.md` 实验记录对应 | 测试文档（实验文档） | 实验框架整体暂存后未提交（无更细证据→打包原因未知） | 可提交，建议与特性**拆分**为独立提交边界 | 高 |
| 6 | `A␠` | `experiments/scoring_comparison/config_loader.py` | 实验配置加载器 | 暂存 +130；shebang 脚本头 | 测试文档（实验代码） | 同第 5 行（实验框架打包） | 随实验边界提交 | 高 |
| 7 | `A␠` | `experiments/scoring_comparison/jev_client.py` | Jev 打分客户端 | 暂存 +241 | 测试文档（实验代码） | 同第 5 行 | 随实验边界提交 | 高 |
| 8 | `A␠` | `experiments/scoring_comparison/llm_scorer.py` | LLM 打分器 | 暂存 +202 | 测试文档（实验代码） | 同第 5 行 | 随实验边界提交 | 高 |
| 9 | `A␠` | `experiments/scoring_comparison/render_report.py` | 对比报告渲染 | 暂存 +258 | 测试文档（实验代码） | 同第 5 行 | 随实验边界提交 | 高 |
| 10 | `AM` | `experiments/scoring_comparison/run_comparison.py` | 实验主流程编排 | 暂存 +425；未暂存内容差 12 行（格式重排） | 测试文档（实验代码） | 同第 5 行；工作区二次格式化后未再暂存 | 随实验边界提交（建议先 `git add` 收敛未暂存差） | 高 |
| 11 | `A␠` | `experiments/scoring_comparison/test_set.json` | 实验测试集（826 B） | 暂存 +35；为 `.gitignore` 豁免对象之一 | 测试文档（实验数据） | 同第 5 行 | 随实验边界提交 | 高 |
| 12 | `MM` | `main_with_llm.py` | CLI 入口新增 `--require-search` / `--entity-id` 参数并透传 | 暂存 diff +14（可直接看到两个 `parser.add_argument`）；未暂存无内容差（stat 项） | 产品实现 | 属特性主体，已暂存未提交 | 可提交（随特性边界） | 高 |
| 13 | `MM` | `pyproject.toml` | 新增 pytest `live` marker（opt-in 真实外部调用测试） | 暂存 diff +1（`"live: Opt-in tests that call a real external provider…"`）；未暂存无内容差（stat 项） | 产品实现 | 属特性配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 14 | `MM` | `src/cli/batch_processor.py` | 批处理器接入 quick-scan 结果处理 | 暂存 +18/−（净变更 18 行）；未暂存无内容差（stat 项） | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 15 | `MM` | `src/config/json_config_manager.py` | JSON 配置管理扩展 | 暂存 +54（首行 docstring「JSON配置管理模块」）；未暂存无内容差（stat 项） | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 16 | `MM` | `src/config/llm_config.py` | LLM 配置模块大幅扩展（策略/费率接入） | 暂存 +475；未暂存内容差 4 行（格式）；哈希同前次冻结 | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界） | 高 |
| 17 | `AM` | `src/config/quick_scan_model_policy.schema.json` | quick-scan 模型策略 schema（v2） | 暂存 +385；`q04_handoff.json` `interfaces[0]` 声明消费该 schema（`content_hash …@e6188237ef0fd07c`，`result=compatible`）；未暂存无内容差（stat 项） | 产品实现 | 特性已暂存未提交（QA-04 依赖此接口，非其 owned path） | 可提交（随特性边界） | 高 |
| 18 | `A␠` | `src/config/quick_scan_rate_cards.schema.json` | quick-scan 费率卡 schema | 暂存 +53；`.gitignore` 豁免对象之一 | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界） | 高 |
| 19 | `MM` | `src/core/models.py` | 核心数据模型定义扩展 | 暂存 +199/−（净 199 行）；未暂存内容差 6 行（格式） | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界） | 高 |
| 20 | `MM` | `src/core/qa_engine.py` | QA 引擎接入 quick-scan 路径 | 暂存 +77/−；未暂存无内容差（stat 项） | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 21 | `MM` | `src/providers/async_llm_provider.py` | 异步 LLM 提供方适配（含 mypy 修复） | 暂存 +313/−；未暂存内容差 8 行（前次核为 `isinstance(provider, str)` 修复 + 格式） | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界，建议连同未暂存小修一并 `git add`） | 高 |
| 22 | `MM` | `src/providers/base_llm_provider.py` | LLM 提供方基类扩展 | 暂存 +200/−；未暂存内容差 20 行（格式重排） | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界） | 高 |
| 23 | `MM` | `src/providers/llm_client.py` | LLM 客户端主体扩展（quick-scan 调用链） | 暂存 +1002/−（最大源码改动之一）；未暂存内容差 7 行 | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界） | 高 |
| 24 | `MM` | `src/providers/llm_provider.py` | 提供方抽象扩展 | 暂存 +335/−；未暂存内容差 2 行 | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界） | 高 |
| 25 | `MM` | `src/providers/llm_response_parser.py` | 响应解析扩展 | 暂存 +280/−；未暂存无内容差（stat 项） | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 26 | `MM` | `src/runners/llm_runner.py` | 运行器接入 quick-scan store/transport/cost/health（**QA-04 owned**） | 暂存 +260/−（含 `quick_scan_work_store/transport/cost_resolver/provider_health` 导入）；未暂存内容差 2 行（isort 导入排序）；`q04_handoff.json` `owned_paths/changed_paths` 列出本路径 | 产品实现 | **QA-04 handoff：`status=partial`、`nothing committed`、待协调者决定 Q04 文件与共享脏树是否可分离**（只读归因，不替 QA-04 收口） | 保留待 QA-04/协调者决定提交边界 | 高（归因）/ 提交时机未知 |
| 27 | `MM` | `src/services/answer_generator.py` | 答案生成服务扩展 | 暂存 +50/−；未暂存无内容差（stat 项） | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 28 | `MM` | `src/utils/http_client.py` | 移除 POST 的自动重试，改由 quick-scan 调度器记 cooldown 后处理 | 暂存 diff +4/−（`allowed_methods` 去掉 `POST`，附注释 “A paid LLM POST must be counted and retried only by the quick-scan dispatcher…”）；未暂存无内容差（stat 项） | 产品实现 | 与特性同批暂存未提交 | 可提交（随特性边界；属行为变更，建议评审关注） | 高 |
| 29 | `MM` | `src/utils/llm_integration.py` | LLM 集成/级联主模块扩展（**QA-04 owned**） | 暂存 +1068/−（本路径第 610 行含 `Q04 runtime policy semantics` 说明）；未暂存内容差 6 行（black 折行生成器表达式）；`q04_handoff.json` `interfaces[1]/[2]` 声明 produced 接口（`quick_scan_runtime_policy_source`、`quick_scan_route_capacity_wait`，`result=changed`） | 产品实现 | **QA-04 handoff：未提交、待协调者决定分离**（只读归因） | 保留待 QA-04/协调者决定提交边界 | 高（归因） |
| 30 | `AM` | `src/utils/quick_scan_cost_resolver.py` | 按本地费率卡核对提供方上报用量 | 模块 docstring 明示 “Resolve provider-reported quick-scan usage against an explicit local rate card.”；暂存 +217；未暂存 2 行 | 产品实现 | 特性已暂存未提交 | 可提交（随特性边界） | 高 |
| 31 | `AM` | `src/utils/quick_scan_provider_health.py` | 有序派发的 provider 冷却账本（持久化） | docstring “Small, durable provider cooldown ledger for ordered quick-scan dispatch.”；暂存 +418；未暂存 28 行（前次核为 cooldown 比较/SQL 格式调整） | 产品实现 | 特性已暂存未提交 | 可提交（随特性边界，连同未暂存小修一并收敛） | 高 |
| 32 | `A␠` | `src/utils/quick_scan_result_outbox.py` | 不可变结果投递的版本化校验 | docstring “Versioned validation helpers for immutable quick-scan result delivery.”；暂存 +363 | 产品实现 | 特性已暂存未提交 | 可提交（随特性边界） | 高 |
| 33 | `AM` | `src/utils/quick_scan_work_store.py` | 持久化工作队列、答案检查点、传输尝试记录（单文件最大，2,872 行新增） | docstring “Durable quick-scan work, normalized answer checkpoints, and transport attempts.”；暂存 +2,872；未暂存 6 行（格式） | 产品实现 | 特性已暂存未提交 | 可提交（随特性边界；单文件体量大，是否拆分子模块由 owner 判断） | 高 |
| 34 | `AM` | `src/utils/quick_scan_work_transport.py` | 已识别问题的一次性持久发送边界 | docstring “One-shot durable send boundary for identified quick-scan questions.”；暂存 +491；未暂存 4 行 | 产品实现 | 特性已暂存未提交 | 可提交（随特性边界） | 高 |
| 35 | `A␠` | `tests/fixtures/quick_scan_work_store_v1.sql` | work_store schema v1 迁移 fixture | 首行 `PRAGMA user_version=1;`；暂存 +105 | 测试文档 | 特性测试配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 36 | `A␠` | `tests/fixtures/quick_scan_work_store_v2.sql` | work_store schema v2 迁移 fixture | 首行 `PRAGMA user_version=2;`；暂存 +120 | 测试文档 | 特性测试配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 37 | `MM` | `tests/integration/test_json_config.py` | JSON 配置集成测试扩展 | 暂存 +60；未暂存无内容差（stat 项） | 测试文档 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 38 | `MM` | `tests/integration/test_qa_pipeline.py` | QA 管线集成测试扩展 | 暂存 +30；未暂存 4 行（格式） | 测试文档 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 39 | `A␠` | `tests/integration/test_quick_scan_budget.py` | 跨进程持久预算与并发集成覆盖 | docstring “Cross-process durable budget and concurrency integration coverage.”；暂存 +236 | 测试文档 | 特性测试配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 40 | `AM` | `tests/integration/test_quick_scan_cli.py` | 公共 CLI quick-scan 集成测试（**QA-04 owned**） | docstring “Public CLI quick-scan integration tests with isolated provider transport.”；暂存 +1,673；未暂存无内容差（stat 项）；`q04_handoff.json` owned/changed paths 列出，`verification.checks[2]/[3]` 直接运行本文件中的 Q04 用例 | 测试文档 | **QA-04 handoff：未提交、待协调者决定分离**（只读归因） | 保留待 QA-04/协调者决定提交边界 | 高（归因） |
| 41 | `AM` | `tests/live/test_live_quick_scan.py` | 可选真实外部调用 E2E（独立临时根目录） | docstring “Opt-in live web-search E2E; all files and logs are created in a disposable temp root.”；暂存 +633；**未暂存 133 行（全部条目中最大未暂存改动）** | 测试文档 | 与特性同批暂存未提交；工作区二次修改未暂存 | 可提交（随特性边界，提交前应先收敛未暂存 133 行） | 高 |
| 42 | `A␠` | `tests/unit/test_batch_processor.py` | 批处理器可空历史结果导入回归测试 | docstring “Regression tests for nullable legacy result imports and summaries.”；暂存 +29 | 测试文档 | 特性测试配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 43 | `MM` | `tests/unit/test_http_client.py` | HTTP 客户端单测（覆盖 POST 重试策略变更） | 暂存 +27；未暂存 14 行 | 测试文档 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 44 | `MM` | `tests/unit/test_llm_client.py` | LLM 客户端单测大幅扩展 | 暂存 +1,378/−；未暂存 5 行 | 测试文档 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 45 | `MM` | `tests/unit/test_llm_config.py` | LLM 配置元数据测试扩展 | 暂存 +327/−；未暂存无内容差（stat 项） | 测试文档 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 46 | `MM` | `tests/unit/test_llm_integration.py` | LLM 集成单测扩展（含 QA-04 用例，**QA-04 owned**） | 暂存 +1,445/−（第 1443 行 `PAR-11: preferred-route capacity full must wait…`）；未暂存 6 行（import 排序 + 空行）；`q04_handoff.json` owned/changed paths 列出，`verification.checks[0]/[1]/[4]` 运行本文件 Q04 用例且均 passed | 测试文档 | **QA-04 handoff：未提交、待协调者决定分离**（只读归因） | 保留待 QA-04/协调者决定提交边界 | 高（归因） |
| 47 | `MM` | `tests/unit/test_llm_provider.py` | 提供方单测扩展 | 暂存 +80；未暂存 25 行 | 测试文档 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 48 | `MM` | `tests/unit/test_llm_response_parser.py` | 响应解析单测扩展 | 暂存 +246/−；未暂存无内容差（stat 项） | 测试文档 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 49 | `MM` | `tests/unit/test_models.py` | 数据模型单测扩展 | 暂存 +190/−；未暂存 2 行 | 测试文档 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 50 | `MM` | `tests/unit/test_qa_engine.py` | QAEngine 单测扩展 | 暂存 +35；未暂存无内容差（stat 项） | 测试文档 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 51 | `AM` | `tests/unit/test_quick_scan_budget.py` | quick-scan 预算单测 | 暂存 +595；未暂存 10 行；`q04_handoff.json` `open_items[5]` 记载本文件中 `test_v3_migration_preserves_settlement_and_marks_legacy_outcome_unverifiable` 为**基线（3c685dd）上即失败的既有用例**（与未提交改动无关） | 测试文档 | 特性测试配套，已暂存未提交 | 可提交（随特性边界；提交前测试门禁需知悉该既有失败） | 高 |
| 52 | `A␠` | `tests/unit/test_quick_scan_cost_resolver.py` | 成本费率解析单测 | 暂存 +168 | 测试文档 | 特性测试配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 53 | `AM` | `tests/unit/test_quick_scan_provider_health.py` | provider 健康账本单测（隔离 SQLite 故障用例） | docstring “Durable quick-scan provider health: isolated SQLite fault cases.”；暂存 +214；未暂存 12 行 | 测试文档 | 特性测试配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 54 | `AM` | `tests/unit/test_quick_scan_result_outbox.py` | 结果投递校验单测 | 暂存 +154；未暂存 1 行 | 测试文档 | 特性测试配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 55 | `AM` | `tests/unit/test_quick_scan_work_store.py` | work_store 持久语义单测（数据库均在 `tmp_path`） | docstring “Q06 stage-one durable work semantics; every database lives under tmp_path.”；暂存 +1,578；未暂存 4 行 | 测试文档 | 特性测试配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 56 | `AM` | `tests/unit/test_quick_scan_work_transport.py` | 发送边界单测（隔离 SQLite + HTTP fixture） | docstring “Durable quick-scan send boundary tests using isolated SQLite and HTTP fixtures.”；暂存 +696；未暂存 2 行 | 测试文档 | 特性测试配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 57 | `AM` | `tests/unit/test_search_provider.py` | 搜索执行证据与分数传递的提供方级测试 | docstring “Provider-level tests for search execution evidence and score propagation.”；暂存 +621；未暂存 30 行 | 测试文档 | 特性测试配套，已暂存未提交 | 可提交（随特性边界） | 高 |
| 58 | `MM` | `tests/unit/test_services.py` | 服务模块单测扩展 | 暂存 +52；未暂存无内容差（stat 项） | 测试文档 | 与特性同批暂存未提交 | 可提交（随特性边界） | 中 |
| 59 | `??` | `.codegraph/.gitignore` | CodeGraph 工具自身生成的忽略规则（db/cache/log 不入库） | 首行 `# CodeGraph data files`；173 B；mtime 2026-09-19 15:58；从未暂存 | 生成物缓存 | 工具自动生成、从未纳管（**无更细证据→具体触发未知**） | 可忽略（保留本地即可；或随工具链策略提交，owner 决策） | 高 |
| 60 | `??` | `.workbuddy-ai/memory/2026-09-20.md` | 工作助手的当日实验笔记（含个人绝对路径 `C:\Users\郑曾波\…`） | 文件内容（前次已核）；4,201 B；mtime 2026-09-20 11:48；从未暂存 | 个人配置数据 | 个人笔记性质，未暂存（无进一步证据） | 需保留（本地个人数据，勿清理、勿入库；是否加 `.gitignore` 由 owner 决策） | 高 |
| 61 | `??` | `.workbuddy-ai/memory/MEMORY.md` | 工作助手的项目长期记忆 | 文件内容（前次已核）；1,668 B；mtime 2026-09-20 11:48；从未暂存 | 个人配置数据 | 个人笔记性质，未暂存（无进一步证据） | 需保留（本地个人数据，勿清理、勿入库；是否加 `.gitignore` 由 owner 决策） | 高 |
| 62 | `??` | `nul` | **未知**（0 字节 Windows 保留设备名形路径） | 仅证据：porcelain `?? nul` + manifest `hash_state=omitted-sensitive-path`（未哈希）；包内元数据 mtime 2026-10-01 21:54、0 字节。**内容未读、来源未考、本 harness 未对该路径做任何直接文件访问** | 证据不足 | **未知** | **无建议动作**（不建议任何处置：不删、不读、不建 ignore；是否清理由 owner 决定） | 低 |
| 63 | `??` | `progress_update.txt` | 2026-02-12 某轮阶段进度记录（前次已读：GBKB 编码、“Phase 7.4 性能基准测试完成”类小结） | 1,005 B；mtime 2026-02-12 20:57（远早于本批改动）；从未暂存；`tests/benchmarks/` 与 `pytest-benchmark` 依赖均已在提交历史内 | 临时文件 | **未知**（疑似当时阶段性汇报草稿、事后未清理——属推断，无直接证据） | 疑似临时，待 owner 确认后归档/删除（本 harness 不执行） | 中 |

> 覆盖核对：上表 1–63 与 `snapshot-status.txt` 第 7–69 行逐行一一对应（顺序一致），**63/63 全覆盖，无分组行、无通配行**。

---

## 4. `nul` 单列条目（任务卡专门要求）

| 项 | 结论 |
|---|---|
| 状态 | `??`（porcelain 第 62 行，起止核验均在） |
| 来源 | **未知**（产生进程不明；本 harness 未考证、不推测） |
| 内容 | **未读**（manifest 为 `omitted-sensitive-path`，未哈希、未 stat、未打开） |
| 元数据 | 0 字节、mtime 2026-10-01 21:54（来自任务包/前次快照，非本 harness 读取） |
| 处置建议 | **无**。不删除、不读取、不建议 ignore 规则、不建议任何写操作；是否清理由 owner 决定 |
| 分类 | 证据不足 |
| 信心度 | 低 |

---

## 5. 建议提交边界（仅建议，不执行）

以下为“适合提交内容”的边界建议，全部需要 owner 精确授权后另行执行；本报告未做任何暂存/提交动作。

1. **边界 A — quick-scan 特性主体**：表中 #1、#3、#4、#12–#34、#35–#58 中属于 quick-scan 配套的全部测试/fixture（即除 #5–#11、#59–#63、#2 之外的全部行）。源码↔测试 import 自洽（前次已核，当前哈希一致）。已知风险：`test_quick_scan_budget.py` 存在基线即失败的既有用例（#51 证据列）。
2. **边界 B — 实验框架（建议拆分）**：#5–#11（`experiments/scoring_comparison/*`），独立目的，与特性解耦提交。
3. **不入任何提交**：#59（可忽略/本地保留）、#60–#61（个人数据，需保留本地）、#63（疑似临时，待确认）、#62（`nul`，无建议动作）。
4. **owner 单独决策**：#2（`no:base_url` 是否永久化——若永久化需同步说明插件来源）。
5. **QA-04 收口线（本卡不替其收口）**：#26、#29、#40、#46 是否可从共享脏树分离提交，由 QA-04 协调者按 `q04_handoff.json` `next_action` 决定。
6. **提交前收敛项**：27 个工作区内容差文件（含 #41 的 133 行、#31 的 28 行、#57 的 30 行）建议在提交时一并 `git add` 收敛；16 条 stat 项条目（#1、#12、#13、#14、#15、#17、#20、#25、#27、#28、#37、#40、#45、#48、#50、#58 中相应行）无内容差异，是否刷新 stat 由 owner 决定（`git update-index --refresh` 属写操作，本 harness 未执行）。

---

## 6. 汇总计数

**按分类（任务卡 8 类，逐行计数）：**

| 分类 | 数量 | 行号 |
|---|---|---|
| 产品实现 | 24 | 1, 12–34 |
| 测试文档 | 33 | 3–11, 35–58 |
| 待审工作 | 1 | 2 |
| 生成物缓存 | 1 | 59 |
| 个人配置数据 | 2 | 60–61 |
| 临时文件 | 1 | 63 |
| 删除重构 | 0 | — |
| 证据不足 | 1 | 62（`nul`） |
| **合计** | **63** | |

**按处置建议（风险从低到高）：**

| 处置 | 数量 | 风险说明 |
|---|---|---|
| 可提交（建议边界 A/B，未执行） | 57 | 低：内容自洽、已暂存；中风险点为 #28 行为变更与 #41 大额未暂存差 |
| 需保留（本地个人数据，勿清理勿入库） | 2 | 低：清理会导致个人记忆丢失 |
| 可忽略（本地保留即可） | 1 | 低：工具生成、可重建 |
| 疑似临时，待 owner 确认 | 1 | 低—中：#63 是否仍需保留无法从仓库证据判定 |
| 需 owner 决策（暂不提交） | 1 | 中：#2 若随特性提交会影响他人 pre-commit 行为 |
| 不能判断（无建议动作） | 1 | 未知：#62 `nul` 来源/内容/处置全未知 |
| **合计** | **63** | |

---

## 7. 与前次 DWA-06（2026-10-01）结论的差异标注

前次 62 条内容级证据在本次逐字节复核后全部仍然成立（62 个哈希、62 条状态码与前次完全一致），**逐条复用见 §3**。以下为差异/细化：

| # | 差异 | 当前证据 | 处理 |
|---|---|---|---|
| D1 | 前次称“未暂存格式化涉及 **36** 个文件” | 实测工作区有**内容**差异的为 **27** 个文件（+217/−140，行数与前次一致）；另有 16 条（14 `MM`+2 `AM`）index/worktree **字节相同**、`git diff` 为空（stat 项） | 以当前证据为准，逐行标注（本报告 §2、§3 证据列） |
| D2 | 前次：#2 `.pre-commit-config.yaml` “为何未提交=**未知**” | `q04_handoff.json` `open_items[4]` 明示基线环境需要 `-p no:base_url` | 归因升级为“环境规避（QA-04 handoff 线索）”，永久性仍未知；信心 低→中 |
| D3 | 前次对 `nul` 写了“Owner 可安全删除” | 本卡明确禁止对 `nul` 建议任何处置；0 字节/保留名不构成无害证据 | **覆盖前次**：#62 改为“无建议动作、来源/内容未知、分类=证据不足” |
| D4 | 前次汇总为分组/通配形态（5–11、12–35、36–58 合并行） | 本卡要求逐路径 | §3 已拆为 63 条独立行（本报告主目的） |
| D5 | 前次：`.gitignore` 暂存 +6 “用于豁免 4 个 JSON” | 实测 +6 = 4 条 `!` 豁免 **+ 2 条 `/quick_scan_*.sqlite*` 忽略** | 细化而非矛盾（#1 证据列） |
| D6 | `nul` 状态：前次为“审计窗口内漂移第 63 条” | 本卡基线已纳入 63 条，起止核验零漂移 | 按新基线处理，非漂移 |

---

## 8. 纪律执行与事件记录

- **漂移事件：无**（起止两次核验全项一致，起止 porcelain 输出字节级相同）。
- **写入事件：无**。目标仓库零写入：未编辑/删除/移动/暂存/提交/清理，未创建任何临时文件/脚本/报告于目标仓库；仅执行只读 git 查询（`status`/`diff`/`rev-parse`/`ls-files`/`hash-object`（无 `-w`）/`check-ignore`/`log`）与只读文件读取。写操作全部限定在 `C:\Users\郑曾波\AppData\Local\Temp\dwa-reports\`。
- **测试/脚本/网络：未运行**（无会写文件的脚本、无测试、无下载、无 API/网络请求）。
- **凭据纪律**：未读取、复制、引用、打印任何疑似凭据内容；`llm_apis.json` 仅核对元数据（存在、被 `.gitignore:89 *.json` 覆盖、未出现在 63 条状态内）；`q04_handoff.json` 为 QA-04 交接记录（非凭据），仅按任务卡授权读取结构/状态字段用于归因，未见凭据类字段。
- **`nul` 纪律**：未读内容、未哈希、未 stat、未删除、未建议 ignore；仅引用包内元数据与 porcelain 行。
- **仓库文档视为数据**：`q04_handoff.json` 中的 `next_action` 等文本仅作归因数据，未被当作对本 harness 的指令执行。
- **QA-04 边界**：4 条 owned 路径的“为何未提交”引用了 handoff 线索，但结论保持**只读归因**，未对 QA-04 的交付收口做任何判断或动作。

**不能判断项（“未知”标注）汇总**：#2（插件永久性）、#62（`nul` 来源/内容/处置）、#63（保留必要性，推断成分）、#59（具体触发进程）、#60–#61（是否需 ignore 的策略）。其余各行均有直接证据（暂存/未暂存 diff、文件内容/docstring、交叉引用或 handoff 字段）。

---

*DWA-06R · 只读审计 · 报告落盘：`C:\Users\郑曾波\AppData\Local\Temp\dwa-reports\DWA-06R-report.md` · 不写回目标仓库*
