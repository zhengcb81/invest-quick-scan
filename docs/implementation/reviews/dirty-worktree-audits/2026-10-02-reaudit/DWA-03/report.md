# DWA-03R — QAbyLLM 未提交改动只读盘点（合规复审）

- **任务编号**：DWA-03R（复审重派，前次 DWA-03 因非只读+快照不一致继续归因被拒收）
- **目标仓库**：`C:\Users\郑曾波\Projects\QAbyLLM`
- **基线**：分支 `main`，HEAD `64ec7721af3b9a2e80b1a1c580a85a8d0610ca51`，porcelain 条目 66（` M`=7，`??`=59）
- **状态清单 SHA-256（期望）**：`58c44b820517b03457faa9415477ebe3abda1a3c62067d886178e715e4806e1c`
- **快照时间**：2026-10-02T06:40:01Z（snapshot.json `captured_at_utc`）
- **审计执行日期**：2026-10-02
- **审计性质**：全程只读；未在目标仓库创建/修改/删除/暂存/提交任何内容；本报告与全部工作草稿仅写入 `C:\Users\郑曾波\AppData\Local\Temp\dwa-reports\`

---

## 1. 快照核验结果（开始 / 结束）

### 1.1 开始核验（PASS）

| 检查项 | 方法 | 期望 | 实测 | 结果 |
|---|---|---|---|---|
| HEAD | `git -C <root> rev-parse HEAD` | `64ec7721af3b9a2e80b1a1c580a85a8d0610ca51` | 相同 | PASS |
| 分支 | `git -C <root> rev-parse --abbrev-ref HEAD` | `main` | `main` | PASS |
| 状态命令 | 按 snapshot.json `status_command` 原样重跑（`safe.directory` + `core.quotepath=false` + `--porcelain=v1 --untracked-files=all`） | 66 条 | 66 条 | PASS |
| 条目清单 | 与 `snapshot-status.txt` 有效条目逐行比对 | 完全一致 | 66/66 行逐字节相等 | PASS |
| 清单摘要 | 规范：条目 LF 连接 + 一个尾 LF 的 UTF-8 SHA-256 | `58c44b82…4806e1c` | `58c44b820517b03457faa9415477ebe3abda1a3c62067d886178e715e4806e1c` | PASS |
| 状态计数 | ` M`=7、`??`=59 | 7/59 | 7/59 | PASS |
| 文件重哈希 | `snapshot-files.jsonl` 中 66 条 `sha256` 全部重算并比对 `size_bytes` | 66 匹配 | ok=66, bad=0, missing=0 | PASS |

**开始结论：与冻结基线零漂移，允许基于 2026-10-02 快照开展归因。**

### 1.2 结束核验（PASS，仓库稳定）

| 检查项 | 期望 | 实测 | 结果 |
|---|---|---|---|
| HEAD | `64ec7721…610ca51` | 相同 | PASS |
| 分支 | `main` | `main` | PASS |
| 状态条目 | 66 条，与开始时一致 | 66 条；`start` 与 `end` 两次捕获**逐字节相同**（`start==end bytes: True`） | PASS |
| 清单摘要 | `58c44b82…4806e1c` | 开始、结束两次均为 `58c44b820517b03457faa9415477ebe3abda1a3c62067d886178e715e4806e1c` | PASS |
| 文件重哈希 | 66 条哈希+大小不变 | ok=66, bad=0, missing=0 | PASS |

**结束结论：审计期间目标仓库零变化，状态稳定；全部 66 条归因均基于已核对部分，无独立漂移项需列出。**

### 1.3 与 2026-10-01 基线的口径核对

- 本审计环境重跑结果为 **66 条**（不含 `?? .claude/settings.local.json`），与 2026-10-02 冻结基线**同口径**，无需按“67 条回退口径”处理。
- `git check-ignore -v .claude/settings.local.json` 显示命中规则来源为用户级全局忽略文件 `C:\Users\郑曾波\.config\git\ignore:3:**/.claude/settings.local.json`，与总控已核实的说明一致（仅取规则元数据，未读取该文件内容）。
- 该文件本体仍存在：`C:\Users\郑曾波\Projects\QAbyLLM\.claude\settings.local.json`，172 字节，mtime 2025-09-16T20:59Z（**仅元数据，内容未读取**）。属总控“已知基线说明”，本报告不重复归因。

---

## 2. 纪律合规声明

1. **零写入目标仓库**：本次仅执行 `git status / rev-parse / diff / ls-files / log / check-ignore / cat-file / stash list / branch` 与本地读文件、哈希计算；未编辑、删除、移动、暂存、提交、清理、安装，未在目标仓库创建任何临时文件、脚本、报告或测试产物。开始/结束两次状态捕获逐字节相同、66 个文件哈希全部不变，可作独立佐证。
2. **不运行写文件/测试/下载/网络请求**：未运行 pytest/ruff/构建脚本，未安装依赖，未发起任何网络或 API 调用（含 pip、LLM API）。全部分析为本地只读读取与哈希。
3. **凭据处理**：未读取、复制、打印任何疑似凭据内容。具体处置：
   - `.claude/settings.local.json`、`config.yaml`（真实本地配置，2261 字节，被 `.gitignore:4:config.yaml` 忽略）、`app.log`（84501 字节，`*.log` 忽略）——**只记路径与大小/mtime 元数据，未输出任何内容**。
   - 对 66 条状态文件做过一次**只输出命中数量/文件名**的疑似凭据模式扫描（不输出内容）；随后对 4 个命中文件做分类核验（见 §5.1 风险项），其中 `README.md`、`config_example.yaml`、`RAG_IMPLEMENTATION_SUMMARY.md` 的命中经核验均为 `your_…_here` 占位符。
   - **过程披露（轻微处置瑕疵）**：对 `simple_porter.py` 做占位符分类核验时，输出语句按长度截断打印了该疑似密钥的前 26 个字符到本会话终端；**完整值未被检索、未被保存、未被写入任何文件，本报告仅记录“存在疑似硬编码 `sk-` 形态密钥（46 字符字面量）”这一元数据事实**。
   - **过程披露（扫描口径）**：跨引用扫描（查找 import/提及关系）以二进制方式打开过工作区全部文件（含 `config.yaml`、`app.log`、`.claude/settings.local.json`）做正则匹配，**未打印、未保留、未转出这三个敏感路径的任何内容**，且三者均未出现在任何匹配结果中；`vector_db/`、`test_vector_db/` 二进制库文件未被读取。
4. **仓库文档/提示词视为待审数据**：README、指南、脚本内容仅作为证据引用，未作为对本 harness 的指令执行。
5. **报告去向**：仅写入任务发起者指定收件位置 `C:\Users\郑曾波\AppData\Local\Temp\dwa-reports\DWA-03R-report.md`，未写回目标仓库、未写回任务包目录。

---

## 3. 全量 66 条逐路径盘点

图例：
- **分类**（任务卡 8 类）：产品实现 / 测试文档 / 待审工作 / 生成物缓存 / 个人配置数据 / 临时文件 / 删除重构 / 证据不足
- **建议动作**（5 桶）：可提交 / 应保留本地 / 可忽略 / 疑似临时（待 owner 确认）/ 需 owner 决策
- **为何未提交**：无证据一律写“未知”
- **信心度**：高 / 中 / 低（对“用途+分类”综合判断）

### 3.1 已跟踪且被修改（` M`，7 条）

| # | 状态 | 路径 | 用途 | 证据 | 分类 | 为何未提交 | 建议动作 | 信心 |
|---|---|---|---|---|---|---|---|---|
| 1 | ` M` | `.gitignore` | 新增 RAG/模型缓存/文档临时/测试等忽略规则 | `git diff`：+41/-1；新增 RAG 块**整体重复出现两次**；新规则 `test_*`(行93)、`temp_*` 会隐藏磁盘上已存在的 `tests/unit/test_*.py`、`test_logging.py`、`test_rag.py`、`test_deps.py` 等（`git check-ignore -v` 实证命中）；`rag_analysis_*.json`(行79)、`vector_db/`(行77) 使 README/PROJECT_SUMMARY 新增的“海康威视RAG分析示例”“vector_db/”条目指向被忽略对象 | 待审工作 | 未知（与 RAG 功能改动同期，仅时间相关，无直接证据） | 需 owner 决策（先去重、收窄 `test_*` 为 `tests/test_*` 或移除、确认示例文件策略，再提交） | 高 |
| 2 | ` M` | `PROJECT_SUMMARY.md` | 项目总结改为“双模式运行”叙述，新增 RAG/多Provider/示例清单 | `git diff`：+128/-36；新增行含 `本地RAG系统 (rag_system.py)`、`交互式启动器 (run_analysis.py)`、`海康威视RAG分析示例` 等指向本工作区未提交文件的清单 | 产品实现 | 未知 | 可提交（须与 §6 提交边界 A/B 同批，避免文档先行失配） | 高 |
| 3 | ` M` | `README.md` | 项目说明新增双模式、本地RAG知识库、DeepSeek/Qwen、运行模式章节 | `git diff`：+123/-41；新增 `### 2. 本地RAG知识库 🆕`、`## 🔄 运行模式` 等；含 `your_api_key_here` 占位符（已核验为占位，非真实密钥） | 产品实现 | 未知 | 可提交（同 A/B 批） | 高 |
| 4 | ` M` | `config_example.yaml` | 示例配置新增 DeepSeek/Qwen、`mode`、`local_rag`（ChromaDB/分块/嵌入/检索）、`answer_verification` 大段配置 | `git diff`：+159/-2；全部 key 值为 `your_deepseek_api_key_here` 等占位符（核验：3 处命中均为 PLACEHOLDER）；**同时写入个人本机路径** `C:\Users\zheng\Dropbox\Stock\安防\海康威视` | 产品实现 | 未知 | 需 owner 决策（个人本机路径脱敏/改为占位符后提交） | 高 |
| 5 | ` M` | `enhanced_dashboard.html` | 交互式仪表板大幅改造（被已跟踪 `start_dashboard.py` 直接引用加载） | `git diff`：+1063/-517，130+ 个 hunk；工作区 45184 字节，HEAD 版 29638 字节（`git show HEAD:…` 重哈希比对）；`<title>企业竞争力分析仪表板 - 现代版</title>` | 产品实现 | 未知 | 可提交（需人工审查大 diff；与备份/中间稿的取舍见 §5.2） | 高 |
| 6 | ` M` | `qa_system.py` | 核心问答入口新增“在线/本地RAG”双模式分支 | `git diff`：+89/-17；新增 `from rag_system import RAGSystem`（try/except 降级）、`setup_rag_system()`、`analyze_company_with_rag()`、`mode` 配置读取、`rag_analysis_{公司}.json` 输出命名 | 产品实现 | 未知 | 可提交（**必须与 `rag_system.py` 等 A 批文件同批**，否则功能静默降级） | 高 |
| 7 | ` M` | `requirements.txt` | 新增 RAG 依赖 9 项 | `git diff`：+10/-1；新增 `chromadb>=0.4.0`、`sentence-transformers>=2.2.0`、`langchain>=0.1.0`、`langchain-community>=0.0.10`、`pypdf2>=3.0.0`、`python-docx>=0.8.11`、`openpyxl>=3.1.0`、`tiktoken>=0.5.0` 等；其 `pkg>=ver` 约束与 §5.3 的 18 个重定向误创建文件一一对应 | 产品实现 | 未知 | 可提交（A 批） | 高 |

### 3.2 未跟踪（`??`，59 条）

按 snapshot-status.txt 顺序：

| # | 状态 | 路径 | 用途 | 证据 | 分类 | 为何未提交 | 建议动作 | 信心 |
|---|---|---|---|---|---|---|---|---|
| 8 | `??` | `0.0.10` | pip 安装 `langchain-community` 的标准输出日志 | 首行 `Collecting langchain-community`；7217 B；mtime 2025-06-07T23:31:22Z；文件名 = `langchain-community>=0.0.10` 的版本号；全仓 0 处引用 | 临时文件 | 误创建的命令输出（有内容证据），非有意提交对象；原始命令拼写未知 | 可忽略（见 §5.3） | 高 |
| 9 | `??` | `0.1.0` | pip 安装 `langchain` 的输出日志 | 首行 `Collecting langchain`；4429 B；2025-06-07T23:30:17Z；对应 `langchain>=0.1.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 10 | `??` | `0.11.0` | pip 安装 `seaborn` 的输出日志 | 首行 `Requirement already satisfied: seaborn …`；2018 B；2025-06-07T23:33:05Z；对应 `seaborn>=0.11.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 11 | `??` | `0.19.0` | pip 安装 `python-dotenv` 的输出日志 | 首行 `Requirement already satisfied: python-dotenv …`；100 B；2025-06-07T23:32:27Z；对应 `python-dotenv>=0.19.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 12 | `??` | `0.4.0` | pip 安装 `chromadb` 的输出日志 | 首行 `Collecting chromadb`；13999 B；2025-06-07T23:28:45Z；对应 `chromadb>=0.4.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 13 | `??` | `0.5.0` | pip 安装 `tiktoken` 的输出日志 | 首行 `Requirement already satisfied: tiktoken …`；896 B；2025-06-07T23:31:59Z；对应 `tiktoken>=0.5.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 14 | `??` | `0.8.11` | pip 安装 `python-docx` 的输出日志 | 首行 `Requirement already satisfied: python-docx …`；346 B；2025-06-07T23:31:40Z；对应 `python-docx>=0.8.11`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 15 | `??` | `1.0.0` | pip 安装 `openai` 的输出日志 | 首行 `Requirement already satisfied: openai …`；1965 B；2025-06-07T23:33:14Z；对应 `openai>=1.0.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 16 | `??` | `1.21.0` | pip 安装 `numpy` 的输出日志 | 首行 `Requirement already satisfied: numpy …`；93 B；2025-06-07T23:32:55Z；对应 `numpy>=1.21.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 17 | `??` | `2.2.0` | pip 安装 `sentence-transformers` 的输出日志 | 首行 `Collecting sentence-transformers`；4767 B；2025-06-07T23:29:02Z；对应 `sentence-transformers>=2.2.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 18 | `??` | `2.25.0` | pip 安装 `requests` 的输出日志 | 首行 `Requirement already satisfied: requests …`；582 B；2025-06-07T23:32:08Z；对应 `requests>=2.25.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 19 | `??` | `21.0` | pip 安装 `pip` 的输出日志 | 首行 `Requirement already satisfied: pip …`；91 B；2025-06-07T23:26:01Z；对应 `install_dependencies.py` 中 `pip>=21.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 20 | `??` | `3.0.0` | pip 安装 `PyPDF2` 的输出日志 | 首行 `Requirement already satisfied: PyPDF2 …`；93 B；2025-06-07T23:31:29Z；对应 `pypdf2>=3.0.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 21 | `??` | `3.1.0` | pip 安装 `openpyxl` 的输出日志 | 首行 `Requirement already satisfied: openpyxl …`；208 B；2025-06-07T23:31:49Z；对应 `openpyxl>=3.1.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 22 | `??` | `3.5.0` | pip 安装 `matplotlib` 的输出日志 | 首行 `Requirement already satisfied: matplotlib …`；1320 B；2025-06-07T23:32:46Z；对应 `matplotlib>=3.5.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 23 | `??` | `4.10.0` | pip 安装 `beautifulsoup4` 的输出日志 | 首行 `Requirement already satisfied: beautifulsoup4 …`；222 B；2025-06-07T23:32:36Z；对应 `beautifulsoup4>=4.10.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 24 | `??` | `50.0` | pip 安装 `setuptools` 的输出日志 | 首行 `Requirement already satisfied: setuptools …` 后接 `Collecting setuptools`；508 B；2025-06-07T23:28:06Z；对应 `setuptools>=50.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 25 | `??` | `6.0` | pip 安装 `pyyaml` 的输出日志 | 首行 `Requirement already satisfied: pyyaml …`；93 B；2025-06-07T23:32:18Z；对应 `pyyaml>=6.0`；0 引用 | 临时文件 | 同上 | 可忽略 | 高 |
| 26 | `??` | `PYTHON_INSTALL_GUIDE.md` | Python 未安装/不在 PATH 的排障与安装指南 | 首行 `# Python安装指南`；引用 `python quick_test.py`(L56)、`setup_rag.bat`(L64)、`install_dependencies.py`；2091 B | 产品实现（文档） | 未知 | 可提交（D 批；与其引用的工具脚本同批） | 中 |
| 27 | `??` | `RAG_IMPLEMENTATION_SUMMARY.md` | 本地 RAG 模式实现总结（目标、模块清单） | 首行 `# QAbyLLM 本地RAG模式实现总结`；提及 `rag_system.py`、`run_analysis.py`、`USAGE_GUIDE.md`、`install_dependencies.py`；4148 B；1 处 `api_key` 命中为 `your_deepseek…` 占位 | 产品实现（文档） | 未知 | 可提交（B/D 批） | 高 |
| 28 | `??` | `USAGE_GUIDE.md` | 使用指南（安装、交互式配置、双模式运行） | 首行 `# QAbyLLM 使用指南`；引用 `install_dependencies.py`、`run_analysis.py`；6927 B | 产品实现（文档） | 未知 | 可提交（D 批） | 高 |
| 29 | `??` | `answer_verifier.py` | 答案验证系统：验证 LLM 生成答案的准确性与可信度 | 模块 docstring（54804 B，本批最大未跟踪源码）；被 `tests/conftest.py`、`test_logging.py`、`tests/unit/*`(4)、`tests/integration/*`(1) import；依赖 `config_manager`、`logging_config`；mtime 2025-09-16T19:50:47Z | 产品实现 | 未知 | 可提交（B 批，需与被隐藏的测试文件一并处理，见 §6） | 高 |
| 30 | `??` | `check_deps.py` | 依赖包状态检查脚本 | docstring `检查依赖包状态`；2980 B；全仓 0 处被引用 | 待审工作 | 未知 | 需 owner 决策（与 `install_dependencies.py`/`install_deps.bat` 功能重叠，去留/合并待定） | 中 |
| 31 | `??` | `check_python.bat` | Python 环境检测批处理 | 首行 `@echo off` + `🐍 Python环境检测工具`；被 `install_dependencies.py`、`python_check.py` 提及；调用 `python quick_test.py`；1133 B | 产品实现（工具） | 未知 | 可提交（D 批，与指南同批） | 中 |
| 32 | `??` | `config_manager.py` | 配置管理器（增强配置管理与校验） | docstring `配置管理器 / 增强的配置管理和验证系统`；被 `answer_verifier.py`、`logging_config.py`、`setup_logging.py` import；20452 B；mtime 2025-09-16T19:51:14Z | 产品实现 | 未知 | 可提交（B 批） | 高 |
| 33 | `??` | `conversation_manager.py` | 多轮对话上下文管理与记忆 | docstring `对话管理器 / 支持多轮对话的上下文管理和记忆`；14784 B；**未发现任何静态引用**（可能经 `plugin_manager` 动态加载或尚未接入） | 产品实现 | 未知 | 可提交（B 批，附接入度说明） | 中 |
| 34 | `??` | `diagnose_python_path.py` | Python PATH 诊断工具，可运行时**生成** `fix_python_path.bat` | docstring `Python路径诊断工具`；L114 `with open("fix_python_path.bat", "w", …)`；4947 B；0 处被引用 | 待审工作 | 未知 | 需 owner 决策（机器排障工具是否入库） | 中 |
| 35 | `??` | `document_processor.py` | 多格式文档扩展处理 | docstring `文档处理器 / 支持多种文档格式的扩展处理`；14305 B；**未发现静态引用** | 产品实现 | 未知 | 可提交（A 批，附接入度说明） | 中 |
| 36 | `??` | `enhanced_dashboard_backup.html` | 仪表板人工备份副本 | 43892 B，mtime 2025-06-08T19:46:54Z；`<title>` 与 `enhanced_dashboard.html` 相同；与 HEAD 版（29638 B）、工作区版（45184 B）、`modern_dashboard.html`（35620 B）哈希**均不同**；0 处被引用 | 临时文件 | 未知（人工复制动机无据；按 mtime 判断为 19:41→19:46→20:37 编辑序列中的中间副本，属推断） | 疑似临时（待 owner 确认；**git 中不存在同内容版本，删除即不可恢复**） | 中 |
| 37 | `??` | `env_check.py` | 空壳文件 | **内容恰好 1 字节（0x20 空格）**，与 `setup_environment.py` 同哈希 `36a9e7f1…`；mtime 2025-06-07T16:35:24Z；0 处被引用；`env_check` 关键字全仓无引用 | 证据不足 | 未知（仅 1 字节，无任何来源证据） | 疑似临时（待 owner 确认后清理） | 高（对“空文件”事实；来源未知） |
| 38 | `??` | `fix_python_path.bat` | Python 路径修复批处理 | 首行 `🐍 Python路径修复工具`；1170 B；可由 `diagnose_python_path.py` L114 以 `open(...,"w")` 重新生成；除生成脚本外 0 处引用 | 生成物缓存 | 未知（推断为诊断脚本运行产物，无直接执行记录） | 疑似临时（待 owner 确认：既可再生成，也可能被本地用户直接双击使用） | 中 |
| 39 | `??` | `fix_python_permanently.ps1` | Python PATH 永久修复（PowerShell） | 首行注释 `# Python永久修复脚本 / 解决"python命令找不到"的问题`；5660 B；0 处被引用 | 待审工作 | 未知 | 需 owner 决策（机器排障工具是否入库） | 中 |
| 40 | `??` | `fix_python_simple.bat` | Python 路径冲突修复（简化版） | 首行 `🐍 Python路径冲突修复工具`；1796 B；mtime 2025-06-07T21:35:05Z（与 #38 相差 49 秒）；0 处被引用 | 待审工作 | 未知 | 需 owner 决策（与 #38/#39 同族，存在重复） | 中 |
| 41 | `??` | `hybrid_retriever.py` | 本地检索 + 网络搜索混合检索策略 | docstring `混合检索器`；14604 B；引用 `network_search`；自身 0 处被引用 | 产品实现 | 未知 | 可提交（A 批） | 中 |
| 42 | `??` | `install_dependencies.py` | 全量依赖安装脚本（18 条 `pkg>=ver`） | docstring `依赖包安装脚本 / 自动安装QAbyLLM项目所需的所有依赖包`；被 `PYTHON_INSTALL_GUIDE.md`、`USAGE_GUIDE.md`、`RAG_IMPLEMENTATION_SUMMARY.md`、`quick_test.py` 引用；6213 B | 产品实现 | 未知 | 可提交（D 批） | 高 |
| 43 | `??` | `install_deps.bat` | RAG 依赖安装批处理 | 首行 `🎯 安装RAG依赖包`；861 B；0 处被引用；与 `install_rag_deps.py`/`install_rag_simple.bat` 功能重叠 | 待审工作 | 未知 | 需 owner 决策（三条安装路径去重） | 中 |
| 44 | `??` | `install_rag_deps.py` | RAG 依赖安装脚本 | docstring `RAG依赖包安装脚本`；2397 B；0 处被引用 | 待审工作 | 未知 | 需 owner 决策（去重） | 中 |
| 45 | `??` | `install_rag_simple.bat` | RAG 依赖安装批处理（简化） | 首行 `🎯 安装RAG依赖包`；841 B；0 处被引用 | 待审工作 | 未知 | 需 owner 决策（去重） | 中 |
| 46 | `??` | `llm_providers.py` | 统一 LLM 提供商接口（OpenAI/DeepSeek/Qwen 抽象） | docstring `统一LLM提供商接口`；13091 B；被 `plugin_manager.py` import；66 条文件密钥扫描**无命中** | 产品实现 | 未知 | 可提交（C 批） | 高 |
| 47 | `??` | `logging_config.py` | 结构化日志配置系统 | docstring `结构化日志配置系统`；6840 B；被 `answer_verifier.py`、`config_manager.py`、`setup_logging.py` import；并提及 `rag_system`/`setup_logging` | 产品实现 | 未知 | 可提交（B 批） | 高 |
| 48 | `??` | `modern_dashboard.html` | 仪表板“现代版”中间稿 | 35620 B，mtime 2025-06-08T19:41:59Z；`<title>` 与 enhanced 版相同；哈希与 HEAD/工作区/backup 版均不同；0 处被引用（`start_dashboard.py` 只加载 `enhanced_dashboard.html`） | 临时文件 | 未知（中间稿判断基于 mtime 序列与无引用，属推断） | 疑似临时（待 owner 确认；不可从 git 恢复） | 中 |
| 49 | `??` | `network_search.py` | 多搜索引擎网络搜索集成 | docstring `网络搜索集成模块`；17635 B；被 `hybrid_retriever.py` 引用 | 产品实现 | 未知 | 可提交（A 批） | 高 |
| 50 | `??` | `ocr_table_processor.py` | 图片 OCR 与表格提取 | docstring `OCR和表格处理器`；13715 B；**未发现静态引用** | 产品实现 | 未知 | 可提交（A 批，附接入度说明） | 中 |
| 51 | `??` | `plugin_manager.py` | 动态加载/管理 LLM 提供商插件 | docstring `插件管理器 / 支持动态加载和管理LLM提供商插件`（`importlib`/`inspect`）；8731 B；自身 0 处被引用（动态加载场景） | 产品实现 | 未知 | 可提交（C 批） | 中 |
| 52 | `??` | `porter_analysis.py` | 波特五力分析（复用现有向量库） | docstring `波特五力模型分析 - 直接使用现有向量数据库`；import `rag_system`；提及输出名 `porter_five_forces`；2325 B | 产品实现 | 未知 | 可提交（A 批） | 高 |
| 53 | `??` | `porter_five_forces_海康威视.json` | 波特五力分析生成结果（海康威视） | 内容头部 `company: 海康威视`、`analysis_time: 2025-09-16T22:26:40`、`analysis_type: porter_five_forces`；3658 B；由 `porter_analysis.py`/`simple_porter.py` 写出（两脚本内含该文件名） | 生成物缓存 | 未知（运行产物，非手写内容） | 可忽略（可由脚本重建，需 API/向量库；若作示例数据须 owner 明示，注意 PROJECT_SUMMARY 指向的是另一文件 `rag_analysis_海康威视.json`，该文件已被 `.gitignore:79` 忽略） | 高 |
| 54 | `??` | `python_check.py` | Python 环境检测脚本 | docstring `Python环境检测脚本`；1368 B；提及 `check_python`；0 处被引用 | 待审工作 | 未知 | 需 owner 决策（与 #31 同族去重） | 中 |
| 55 | `??` | `quick_test.py` | RAG 系统快速冒烟测试 | docstring `快速测试脚本 - 验证RAG系统基本功能`；import `rag_system`；被 `PYTHON_INSTALL_GUIDE.md`、`check_python.bat`、`setup_rag.bat` 引用；5127 B | 测试文档 | 未知 | 可提交（D 批） | 高 |
| 56 | `??` | `rag_system.py` | 本地 RAG 知识库系统（扫描/向量化/检索问答） | docstring `本地RAG知识库系统`；被**已修改的** `qa_system.py`、`porter_analysis.py`、`quick_test.py` 引用；25872 B；mtime 2025-06-08T14:48:26Z | 产品实现 | 未知 | 可提交（A 批核心，缺失则 #6 双模式静默降级） | 高 |
| 57 | `??` | `run_analysis.py` | 交互式启动器（在线/本地RAG 模式选择） | docstring `企业竞争力分析系统启动器`；被 `README.md`、`PROJECT_SUMMARY.md`、`qa_system.py`、`USAGE_GUIDE.md`、`RAG_IMPLEMENTATION_SUMMARY.md` 等引用；8240 B | 产品实现 | 未知 | 可提交（A 批） | 高 |
| 58 | `??` | `run_rag_analysis.bat` | 本地 RAG 分析批处理启动器 | 首行 `🎯 QAbyLLM 本地RAG分析启动器`；仅在 `setup_rag.bat` 的提示文本中出现；674 B；与 `run_analysis.py` 功能部分重叠 | 产品实现（工具） | 未知 | 可提交（D 批；与 #57 的去留一并由 owner 确认） | 中 |
| 59 | `??` | `setup_environment.py` | 空壳文件 | **内容恰好 1 字节（0x20 空格）**，与 `env_check.py` 同哈希；mtime 2025-06-07T16:03:44Z；`setup_environment` 全仓 0 引用 | 证据不足 | 未知（仅 1 字节，无任何来源证据） | 疑似临时（待 owner 确认后清理） | 高（对“空文件”事实；来源未知） |
| 60 | `??` | `setup_logging.py` | 日志系统初始化脚本（应用启动时调用） | docstring `日志系统初始化脚本`；被 `logging_config.py` 提及；被 `test_logging.py`(忽略区) import；2776 B | 产品实现 | 未知 | 可提交（B 批；`test_logging.py` 因 `test_*` 规则处于忽略区，需 §6 一并处理） | 高 |
| 61 | `??` | `setup_python_alias.bat` | Python 别名设置工具 | 首行 `🔧 Python别名设置工具`；796 B；0 处被引用 | 待审工作 | 未知 | 需 owner 决策（机器排障工具是否入库） | 中 |
| 62 | `??` | `setup_rag.bat` | RAG 环境一键设置（安装依赖→写配置→自检） | 首行 `🎯 QAbyLLM RAG环境设置`；被 `PYTHON_INSTALL_GUIDE.md` L64 引用（“双击运行”）；内部调用 `python quick_test.py` 并提示 `run_rag_analysis.bat`；2642 B | 产品实现（工具） | 未知 | 可提交（D 批，与指南/冒烟脚本同批） | 高 |
| 63 | `??` | `simple_porter.py` | 简单波特五力分析（直接调用 API） | docstring `简单波特五力分析 - 直接调用API`；3435 B；提及 `porter_five_forces` 输出名；**密钥扫描命中 1 处非占位：`api_key = "sk-…"` 形态 46 字符硬编码字面量（值未记录/未保存）** | 产品实现 | 未知 | **需 owner 决策：提交前必须脱敏并轮换该密钥，禁止原样提交** | 高（密钥存在性）/ 中（用途） |
| 64 | `??` | `simple_test.py` | RAG 依赖自检脚本 | 无 docstring，首行 `print("🔍 检查RAG依赖包...")`；逐包 try/except import；1987 B；0 处被引用（但文件名不匹配 `test_*` 故仍可见） | 测试文档 | 未知 | 可提交（D 批） | 中 |
| 65 | `??` | `tatus` | `git log --oneline` 单行输出片段 | 53 字节，ANSI 黄色码包裹：`aaaacd3 <中文提交标题>`；GB 解码为 `aaaacd3 添加交互式仪表板和启动器`，与 `git cat-file -t aaaacd3` = `commit`、`git log --oneline -3 aaaacd3` 首行完全一致；mtime 2025-06-08T19:52:20Z；0 处被引用 | 临时文件 | 误创建的命令输出（有内容证据）；原始命令拼写未知（`git log` 输出经 `>` 重定向落入该文件） | 可忽略（见 §5.3） | 高 |
| 66 | `??` | `tests/conftest.py` | 答案验证系统的 pytest 共享 fixture 与配置 | docstring `测试配置文件 / 为答案验证系统测试提供共享的fixture和配置`；2047 B；import `answer_verifier`；mtime 2025-09-16T19:26:01Z；**其配套测试 `tests/unit/test_*.py`（4 个）、`tests/integration/test_*.py`（1 个）、`test_logging.py` 等被新 `.gitignore` 行93 `test_*` 规则隐藏，不出现在 66 条中** | 测试文档 | 未知 | 需 owner 决策（须先修 `.gitignore` 的 `test_*` 规则，conftest 与测试文件同批提交，否则孤立 fixture 无意义） | 高 |

> 覆盖率核对：上表 66 行 = 快照 66 条；` M` 7 行（#1–7）+ `??` 59 行（#8–66），路径与 `snapshot-status.txt` 逐条一致（顺序一致）。

---

## 4. 分类与动作汇总

### 4.1 按分类计数（8 类，合计 66）

| 分类 | 数量 | 占比 | 涉及路径（摘要） |
|---|---:|---:|---|
| 产品实现 | 28 | 42.4% | 7 条中 6 条修改（#2–#7）+ 21 个未跟踪源码/文档/工具（#26–29,31–33,35,41–42,46–47,49–52,56–58,60,62–63） |
| 测试文档 | 3 | 4.5% | #55 `quick_test.py`、#64 `simple_test.py`、#66 `tests/conftest.py` |
| 待审工作 | 10 | 15.2% | #1 `.gitignore`、#30,34,39,40,43,44,45,54,61（排障/安装类工具，均无引用） |
| 生成物缓存 | 2 | 3.0% | #53 `porter_five_forces_海康威视.json`、#38 `fix_python_path.bat` |
| 个人配置数据 | 0 | 0% | 66 条内无此类（真实本地配置 `config.yaml`、`.claude/settings.local.json`、`app.log` 均为**忽略文件**，不在状态清单内，本报告只记元数据） |
| 临时文件 | 21 | 31.8% | 18 个版本号 pip 日志（#8–25）、`tatus`(65)、`enhanced_dashboard_backup.html`(36)、`modern_dashboard.html`(48) |
| 删除重构 | 0 | 0% | 无 ` D`/`D ` 条目，本批不存在待提交的删除或重命名 |
| 证据不足 | 2 | 3.0% | #37 `env_check.py`、#59 `setup_environment.py`（各 1 字节） |
| **合计** | **66** | **100%** | — |

### 4.2 按建议动作计数（5 桶，合计 66）

| 建议动作 | 数量 | 占比 | 风险/说明 |
|---|---:|---:|---|
| 可提交 | 28 | 42.4% | 必须按 §6 分 5 个边界提交；`qa_system.py` 不可脱离 `rag_system.py` 单独入库；`config_example.yaml`、`simple_porter.py` 被移入 owner 决策桶 |
| 应保留本地 | 0 | 0% | 66 条内无“必须只留本地”的确证项（个人配置均已被忽略规则挡住，不在清单内） |
| 可忽略 | 20 | 30.3% | 18 个 pip 重定向日志 + `tatus` + `porter_five_forces_海康威视.json`；均有内容级证据、可再生、零引用；**删除仍须 owner 精确授权** |
| 疑似临时（待 owner 确认） | 5 | 7.6% | `enhanced_dashboard_backup.html`、`modern_dashboard.html`、`env_check.py`、`setup_environment.py`、`fix_python_path.bat`；其中两个 HTML **不可从 git 恢复**，删除前须确认 |
| 需 owner 决策 | 13 | 19.7% | `.gitignore`（规则缺陷）、`config_example.yaml`（个人路径）、`simple_porter.py`（疑似真实密钥）、`tests/conftest.py`（配套测试被隐藏）+ 9 个无引用排障/安装工具 |
| **合计** | **66** | **100%** | — |

### 4.3 汇总风险（任务卡第 38 行要求）

- **最高风险**：`simple_porter.py` 硬编码疑似真实 API 密钥（§5.1 R1）——一旦随手 `git add .` 即泄密入库。
- **高风险**：`.gitignore` 的 `test_*`/`temp_*` 规则（#1）把磁盘上已存在的整套测试（`tests/unit/*` 4 个、`tests/integration/*` 1 个、`test_logging.py`、`test_rag.py`、`test_rag_fix.py`、`test_deps.py`、`test_python_access.bat`）**永久隐藏**，且与“可提交”的 `tests/conftest.py` 形成断裂（R2）。
- **中风险**：文档（`PROJECT_SUMMARY.md` 新增行）指向已被 `.gitignore:79` 忽略的 `rag_analysis_海康威视.json` 与被 `:77` 忽略的 `vector_db/`，文档-忽略规则自相矛盾（R3）。
- **中风险**：`config_example.yaml` 含个人本机路径；README/示例配置若与代码不同批提交会造成文档失配（R4）。
- **低-中风险**：21 个临时文件长期滞留（多为零引用、可再生），增加误提交面；2 个 1 字节空壳来源不可考（R5）。
- **不能判断**：`env_check.py`、`setup_environment.py` 的创建意图（归入“证据不足”，未作任何用途推断）。

---

## 5. 专项判断

### 5.1 凭据与敏感路径（元数据级）

| 路径 | 是否在 66 条内 | 元数据 | 处置 |
|---|---|---|---|
| `simple_porter.py` | 是（#63） | 3435 B；含 1 处 `api_key = "sk-…"` 形态 46 字符硬编码字面量 | **只记录存在性**；值未完整检索/未保存/未写入报告；建议 owner 轮换密钥并改为从 `config.yaml`/环境变量读取后再提交 |
| `config.yaml` | 否（被 `.gitignore:4` 忽略） | 2261 B，mtime 2025-09-16T21:14Z | **未读取内容**（跨引用扫描曾二进制打开做正则匹配，无内容输出/留存） |
| `.claude/settings.local.json` | 否（被用户全局 ignore 忽略） | 172 B，mtime 2025-09-16T20:59Z；文件仍在磁盘 | **未读取内容**；仅 `check-ignore` 取规则来源 |
| `app.log` | 否（被 `*.log` 忽略） | 84501 B | **未读取内容**（同扫描口径披露） |
| `README.md` / `config_example.yaml` / `RAG_IMPLEMENTATION_SUMMARY.md` | 是（#3,4,27） | 密钥模式命中共 6 处 | 逐一核验均为 `your_…_here` 占位符，非凭据 |
| `vector_db/`、`test_vector_db/` | 否（被忽略） | ChromaDB 二进制库，合计约 81 MB | 未读取 |

### 5.2 临时文件 / 缓存专项（可复现来源、可重建性、本地依赖）

| 文件组 | 可复现来源（证据） | 可重建性 | 是否被本地用户依赖 | 建议 |
|---|---|---|---|---|
| 18 个版本号文件（`0.0.10`…`6.0`，#8–25） | 内容 = pip 标准输出；文件名 = 同一命令中 `pkg>=ver` 的 `ver`；18/18 与 `requirements.txt`+`install_dependencies.py` 的版本约束一一对应（`chromadb>=0.4.0`→`0.4.0` 等）；mtime 全部落在 2025-06-07T23:26–23:43Z 同一安装会话；推断为 cmd.exe 将未加引号的 `pip install pkg>=ver` 中 `>` 解释为输出重定向（**具体命令拼写未知**，机制为推断，信心中） | **完全可再生**：重新执行对应 pip 命令即可得到同类输出；文件本身是输出而非输入 | **无**：全仓 0 处引用，无脚本读取 | 可忽略；owner 授权后删除（或补 ignore 规则）。不建议提交 |
| `tatus`（#65） | 单行 ANSI 着色 `git log --oneline` 输出，指向真实提交 `aaaacd3`（`git log --oneline -3 aaaacd3` 首行一致，标题逐字吻合）；53 B；mtime 2025-06-08T19:52:20Z；推断为 `git log … > tatus` 类重定向误创建（`git status` 被截断成 `tatus` 的可能性无法证实，**原始命令未知**） | **可再生**：重跑同参数 `git log --oneline` 即得等价内容 | **无**：0 处引用 | 可忽略；owner 授权后删除 |
| `enhanced_dashboard_backup.html`(#36)、`modern_dashboard.html`(#48) | 人工复制/中间稿（同 `<title>`、不同哈希；mtime 19:41 → 19:46 → 20:37 编辑序列） | **不可从 git 重建**：HEAD 版 29638 B 与二者（43892/35620 B）均不同；只存在于工作区 | **未知**：0 处引用，但可能被用户手工打开对照 | 疑似临时，**须 owner 确认**后方可删除；不建议提交 |
| `env_check.py`(#37)、`setup_environment.py`(#59) | 各 1 字节（0x20），同哈希；来源无证据 | 无意义内容，不需重建 | **无**：0 处引用 | 证据不足 → 疑似临时，须 owner 确认后清理 |
| `fix_python_path.bat`(#38) | `diagnose_python_path.py` L114 以 `open("fix_python_path.bat","w")` 运行时写出 | **可再生**：运行诊断脚本即重新生成 | **未知**：可能被用户双击使用 | 生成物 → 疑似临时，须 owner 确认 |
| `porter_five_forces_海康威视.json`(#53) | `porter_analysis.py`/`simple_porter.py` 运行输出（`analysis_time=2025-09-16T22:26:40`） | 可重建，但需 API/向量库与凭据 | **无静态读取方**（两脚本仅写它） | 可忽略；若作为示例数据入库须 owner 明示 |
| `.pytest_cache/`、`.ruff_cache/`、`__pycache__/`、`tests/**/__pycache__/`、`vector_db/`、`test_vector_db/`、`rag_analysis_海康威视.json`、`app.log`、`config.yaml`、`test_*.py` 等 51 个文件 | 不在 66 条状态内（已被对应规则忽略），仅作上下文登记 | — | 未知 | 不在本卡盘点范围；其中 `.ruff_cache` mtime 为 2026-10-01T20:50–20:52Z（**仅记录事实，不作归因**，超出本卡范围） |

### 5.3 上下文：仓库形态（解释“为什么 59 条未跟踪”）

- HEAD 树仅 9 个文件（`git ls-files`）：`.gitignore`、`PROJECT_SUMMARY.md`、`README.md`、`config_example.yaml`、`enhanced_dashboard.html`、`multi_company_analysis.json`、`qa_system.py`、`requirements.txt`、`start_dashboard.py`。
- 最后一次提交：`64ec7721`，2025-06-07 12:49:59 +0100，`项目完成：添加项目总结文档，所有功能已实现`；此后（2025-06-07 ~ 2025-09-16）约 3 个月的新功能、工具、文档、仪表板改动**全部停留在工作区**（`git stash list` 为空、仅 `main` 单分支，无分支/暂存痕迹）。
- 工作区实有文件 119 个（不含 `.git`）：66 条状态 + 2 个干净已跟踪文件（`start_dashboard.py`、`multi_company_analysis.json`）+ 51 个被忽略文件。

---

## 6. 可提交内容与提交边界建议（不执行任何提交）

> 以下为**建议**，须 owner 精确授权后另行执行。分批原则：文档与代码同批、核心依赖不拆分、问题文件先整改。

| 边界 | 内容 | 覆盖 66 条中的 | 前置条件 / 审查缺口 |
|---|---|---|---|
| **A. RAG 双模式核心** | `qa_system.py`(M)、`requirements.txt`(M)、`rag_system.py`、`run_analysis.py`、`document_processor.py`、`hybrid_retriever.py`、`network_search.py`、`ocr_table_processor.py`、`porter_analysis.py` | #6,7,35,41,49,50,52,56,57 | 无自动化测试覆盖（现有 pytest 均被 `test_*` 隐藏，且测试针对验证系统而非 RAG）；`document_processor`/`ocr_table_processor` 无静态引用，需确认是否实际接入 |
| **B. 答案验证 + 配置/日志** | `answer_verifier.py`、`config_manager.py`、`logging_config.py`、`setup_logging.py` | #29,32,47,60 | **测试缺口**：配套 `tests/unit/*`、`tests/integration/*`、`test_logging.py` 在磁盘上存在但被 `.gitignore:93` 忽略——必须先整改 `.gitignore` 再把测试与 `tests/conftest.py`(#66) 同批提交 |
| **C. 多 Provider / 插件 / 对话** | `llm_providers.py`、`plugin_manager.py`、`conversation_manager.py` | #33,46,51 | 三者接入度需说明（`conversation_manager` 无引用）；`config_example.yaml`(#4) 的 DeepSeek/Qwen 段与本批强相关 |
| **D. 文档 + 工具链** | `README.md`(M)、`PROJECT_SUMMARY.md`(M)、`USAGE_GUIDE.md`、`RAG_IMPLEMENTATION_SUMMARY.md`、`PYTHON_INSTALL_GUIDE.md`、`install_dependencies.py`、`setup_rag.bat`、`run_rag_analysis.bat`、`check_python.bat`、`quick_test.py`、`simple_test.py` | #2,3,26,27,28,31,42,55,58,62,64 | 文档引用的 `rag_analysis_海康威视.json`/`vector_db/` 当前被 `.gitignore` 忽略，须先解决 R3 矛盾 |
| **E. 仪表板** | `enhanced_dashboard.html`(M) | #5 | 1063 行增量 diff，需人工审查；与 #36/#48 两个备份稿的取舍须先做 §5.2 决策 |
| **F. 整改后单独提交** | `.gitignore`（去重 + 收窄 `test_*`/`temp_*` + 确认示例忽略策略）；`config_example.yaml`（个人路径脱敏）；`simple_porter.py`（密钥脱敏+轮换） | #1,4,63 | **提交前置**：R1 密钥、R2 测试隐藏、R3 文档-忽略矛盾 |
| **不建议提交** | 20 个可忽略项（#8–25,53,65）+ 5 个疑似临时项（#36,37,38,48,59）+ 9 个无引用工具（#30,34,39,40,43,44,45,54,61，去留由 owner 决定） | 34 条 | 删除动作一律需 owner 显式授权 |

**完整性与测试/审查缺口**：
1. `tests/conftest.py` 单独入库无意义——须连同被 `test_*` 隐藏的 6 个测试文件一起处理（这些文件不在 66 条内，属忽略区上下文）。
2. RAG 主链（A 批）无任何自动化测试；仅 `quick_test.py`/`simple_test.py` 冒烟脚本。
3. `enhanced_dashboard.html` 大 diff 未见任何审查痕迹。
4. 未提交状态下，README/PROJECT_SUMMARY 描述的文件（`rag_system.py`、`run_analysis.py`、`config.yaml` 示例、`vector_db/`）在干净克隆中不存在——文档与实现当前不可分离提交。

---

## 7. 验证记录（复现方法）

```
# 开始/结束各一次（同一命令，原样取自 snapshot.json status_command）
git -c safe.directory="C:\Users\郑曾波\Projects\QAbyLLM" -c core.quotepath=false \
    -C "C:\Users\郑曾波\Projects\QAbyLLM" status --porcelain=v1 --untracked-files=all

# 摘要规范化：porcelain 条目以 LF 连接 + 一个尾 LF → UTF-8 字节 SHA-256
# 开始: 66 条 58c44b820517b03457faa9415477ebe3abda1a3c62067d886178e715e4806e1c  PASS
# 结束: 66 条 58c44b820517b03457faa9415477ebe3abda1a3c62067d886178e715e4806e1c  PASS
# start/end 两次捕获逐字节相同: True

git -C <root> rev-parse HEAD            → 64ec7721af3b9a2e80b1a1c580a85a8d0610ca51  PASS（始/末）
git -C <root> rev-parse --abbrev-ref HEAD → main                                    PASS（始/末）
snapshot-files.jsonl 66 条重哈希       → ok=66 bad=0 missing=0（始/末各一次）      PASS
```

辅助只读证据：`git diff`（numstat/逐文件）、`git ls-files`（9 项）、`git log`/`git cat-file`、`git check-ignore -v`、`git stash list`、`git branch -a`、本地文件读取与 SHA-256 计算。**全部输出仅写入 `C:\Users\郑曾波\AppData\Local\Temp\dwa-reports\`（dwa03r-start-status.txt、dwa03r-end-status.txt、dwa03r-tracked.txt、本报告），目标仓库无任何新增/改动。**

---

## 8. 结论

1. **快照核验：开始 PASS、结束 PASS，仓库全程稳定，零漂移**；与 66 条基线及总控的全局忽略口径一致，`67→66` 差异已按“已知基线说明”确认，不重复归因。
2. **66 条全部完成逐路径归因**（覆盖率 100%）：产品实现 28、临时文件 21、待审工作 10、测试文档 3、生成物缓存 2、证据不足 2、个人配置数据 0、删除重构 0。
3. **动作建议**：可提交 28（须分 6 个边界并先整改 3 项前置问题）、可忽略 20、需 owner 决策 13、疑似临时待确认 5、应保留本地 0。
4. **三项提交前置**（见 §4.3）：R1 `simple_porter.py` 疑似真实密钥（脱敏+轮换）；R2 `.gitignore` `test_*` 规则隐藏整套测试；R3 文档引用与忽略规则自相矛盾。
5. **纪律**：全程只读、零目标仓写入、无测试/脚本/网络执行、凭据只记元数据；两项轻微处置披露见 §2 第 3 条（终端截断打印过疑似密钥前 26 字符；跨引用扫描二进制打开过敏感路径但无内容输出/留存）。
