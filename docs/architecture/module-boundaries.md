# 快扫产品模块归属与公开边界

最后核对：2026-11-10。本文登记参与快扫正常运行的产品模块、状态归属、公开接口和允许依赖方向。它描述的是运行时边界，不把测试工具、历史证据目录或普通 helper 文件算作独立产品模块。

## 运行时关系

```mermaid
flowchart LR
  UI[Dashboard UI / application]
  IQS[IQS：题库、模块路由、评分编排]
  QA[StockQA：模型、搜索、预算、任务与恢复]
  CA[Company Agent：任务与回答执行]
  RT[Agent Runtime：运行时端口与回执投影]
  SW[StockWiki：身份、名单、观察与事实查询]
  TH[analyze-theme-value-chain：只读事实消费者]
  IR[industry-research：只读事实消费者]

  UI -->|Dashboard ports / HTTP adapters| IQS
  IQS -->|versioned company-scan API| QA
  QA -->|versioned public facades| CA
  QA -->|versioned runtime facade| RT
  IQS -->|registered CLI / JSON contracts| SW
  TH -->|public query_facts / export_facts CLI| SW
  IR -->|public query_facts / export_facts CLI| SW
```

跨仓调用经过 facade、CLI/HTTP port 或版本化 JSON contract。消费者不通过导入对方私有 Python 路径、读取对方文件目录或打开对方数据库来取得产品数据。模块内部仍可调用本 owner 的私有实现。

接口分两层管理：跨仓产品合同和被明确登记为稳定协作者的仓内 API 使用版本与导出白名单；同一 owner 内的辅助实现模块不逐文件建立版本协议，也不因此变成跨仓接口。仓内协作可以使用非私有符号，但禁止跨模块访问下划线私有符号、动态导入绕开登记边界或越权读取 owner 数据。该划分避免把每个 helper 都升级成独立产品模块，同时让真正需要兼容的接口具有可检查的合同。

## Owner 与合同

| Owner / 产品边界 | 唯一负责的数据与行为 | 对外公开入口及版本 | 允许依赖方向与主要消费者 |
|---|---|---|---|
| **invest-quick-scan (IQS)** | 公司扫描编排；题库模块、路由决策、标准答案投影和扫描 UI 合同 | 题库模块 schema `$id=urn:iqs:quick-scan:question-module:1`；每个模块有独立 `module_id`、语义版本及不可变 release/lock；当前 router `2.5.0`、routing policy schema `1.3.0`、route decision schema `2.0.0`。跨仓任务 port 为 `stockqa.company_scan_task_port/1.0.0`；共享执行器 capabilities 为 `iqs.shared-company-engine/1.0.0`；答案语义协作者为 `iqs.answer-validation-api/1.0.0`；owner API 下限见 `scripts/shared_company_ports.py`，当前按已观察候选固定为 StockQA 1.5、Company Agent 2.3、Runtime 1.4；更低版本的历史兼容尚无 canonical 矩阵证据 | IQS 编排到 StockQA company-scan facade，并经公开 owner 命令/JSON contract 到 StockWiki；不拥有 StockQA 工作库或 StockWiki 身份/观察库 |
| **StockQA** | LLM 与搜索 provider、请求/额度/预算、扫描执行、work ledger、checkpoint 与恢复 | 工作树候选 `src.utils.quick_scan_company_api.PUBLIC_API_PROTOCOL = stockqa.company-scan-public-api/1.5.0`；WorkStore 导出候选 `stockqa.quick-scan-work-store-module/1.5.0`。截至当前 canonical HEAD `4c24789`，公开 company facade 文件尚未跟踪，相关 owner 实现处于大范围未提交状态。候选配置不再检查 Company Agent `task.py`/Runtime `port.py`；证据、扫描及恢复操作统一经版本化 Company Agent facade，缺失导入有稳定错误映射。 | 目标依赖是 IQS 调用 company-scan facade，StockQA 通过 Company Agent 和 Agent Runtime 的公开 facade 组合执行；工作库由 StockQA 独占。不能将工作树候选视为已发布接口 |
| **Company Agent** | agent task contract、回答验证、执行/恢复及导出 | 工作树候选 `iqs_company_agent_lab.api.PUBLIC_API_PROTOCOL = iqs.company-agent-public-api/2.3.0`；canonical HEAD `d0280f5` 尚无 `api.py`，新 facade 与相关 task 改动尚未提交 | 目标由 StockQA 集成层调用；外部消费者经 `api` facade，不导入 runner、answers 等内部模块。当前仅是候选 |
| **Agent Runtime** | runtime service port、原生回答与工具调用回执投影 | 工作树候选 `iqs_agent_runtime_lab.api.PUBLIC_API_PROTOCOL = iqs.agent-runtime-public-api/1.4.0`、`RUNTIME_SERVICES_PROTOCOL = iqs.agent-runtime-services/1.0.0`；canonical HEAD `5839ef4` 尚无 `api.py`，并有相关改动未提交 | 目标由 StockQA/IQS 执行组合按 facade 调用；不越过 `api` 直接访问内部 port/receiptmap。当前仅是候选 |
| **StockWiki** | 公司/证券身份、股票池成员、观察、事实来源与 ACK/查询状态 | 事实查询入口 `python -m stockwiki.quick_scan_query_v2_cli`；能力 envelope `iqs.facts_contract_capabilities/1.0.0`，可协商 capability schema `1.2.0` 并兼容 `1.1.0`；facts wire `2.7.0`，`stockwiki.c06_facts_query/1.0.0`；export `stockwiki.c06_facts_export/1.0.0`；CLI result `stockwiki.c06_facts_cli_result/1.0.0`。原有 query wire 保留其公开版本 | IQS、Dashboard 与只读消费者通过 owner CLI/HTTP contract 使用；数据库和原始 owner 文件由 StockWiki 独占 |
| **investment-dashboard** | UI、HTTP/application 层、Dashboard 自身投影与展示状态 | `backend.dashboard.ports.QuickScanPort` 定义 `capabilities/list_observations/get_result/link`；IQS adapter 使用 owner 声明的协议与 generated DTO；生成合同 `CONTRACT_VERSION = 0.1.2-d`，QuickScan DTO 为 `QuickScanView` | UI → application/service → ports → owner adapters；Dashboard 不从 StockQA/StockWiki 实现层导入模块，也不重算 IQS 分数 |
| **analyze-theme-value-chain** | 主题研究自己的结果与本地 capture/output | `scripts/quick_scan_client.py` 以固定 StockWiki CLI 发起只读查询；接受 capability `1.1.0/1.2.0`，只消费 facts schema `2.7.0`、`stockwiki.c06_facts_query/1.0.0` 与 export `1.0.0` | 只读消费 StockWiki 公共 facts contract；结果留在 Theme 自己的输出根，不回写 owner 数据库 |
| **industry-research** | 行业研究自己的结果与本地 capture/output | `tools/quick_scan_client.py` 使用同一 StockWiki CLI/facts wire；当前常量与 Theme 对齐：facts schema `2.7.0`、query/export protocol `1.0.0`，capability `1.1.0/1.2.0` | 只读消费 StockWiki 公共 facts contract；结果留在 Industry 自己的输出根，不回写 owner 数据库 |

### 仓内协作者与版本化范围

- 版本化范围以稳定协作者/API 白名单为准，不按每个 `.py` 文件机械分配版本。StockQA WorkStore 的 `MODULE_API_PROTOCOL`/`MODULE_API_EXPORTS` 是 StockQA owner 内的稳定协作者合同；外部消费者仍必须走 `quick_scan_company_api` facade。
- StockWiki 的 `tests/test_f05_module_api_boundaries.py` 对 8 个明确登记的稳定模块逐项核验版本和精确导出，并核验消费者只导入这些模块声明的名称；同时扫描全部 `quick_scan_*.py`，拒绝下划线私有导入/成员调用及常见动态导入绕行。其他未登记的 `quick_scan_*` 实现文件属于 StockWiki owner 内部协作，不是跨仓协议，不要求逐文件版本号。当前独立审查没有发现这些边界上的 P1/P2。
- IQS/StockQA/Company Agent/Runtime/Dashboard/Theme/Industry 的表内版本字段表示仓间或已登记模块合同；各 owner 的局部 helper 仍由其仓内测试和实现共同演进。若某 helper 开始被跨 owner 消费，必须先迁入已有 facade 或登记版本化入口并加合同正反例。
- IQS `shared_company_engine` 的 1.0 capabilities 保留旧 profile 元数据以兼容已有读取方，并报告本地声明的 owner API 最低版本；运行时 admission 另从 owner facade 读取并核对实际协议。CLI 能在 provider 仓库未安装时工作。旧的 12 题/截止日字段只是历史 profile 描述，generic task admission 从公开任务 DTO 读取问题集和有效 cutoff。答案语义模块协议由 engine 在调用时核对。

### IQS 题库的兼容边界

- 新增/升级题库通过 `kind` 模块（common、industry、stage、overlay、diagnostic 等）独立组合；模块内保留 `module_id` 与语义版本，release/lock 绑定精确工件 hash。改变题目含义应发布新版本并保留旧 release，不静默改写已发布内容。
- 路由策略与题库模块分开升级。router 负责证据门槛与模块选择；模块 schema 负责题目与适用条件；评分/答案 DTO 由已有 schema 版本管理。旧兼容格式只在生产者与消费者明确支持时继续接受。
- 题库、模型执行、事实查询和 Dashboard DTO 各自有 owner。需要组合时通过 versioned contract 传递数据，不将任一方的数据库表或目录当作共享接口。

## 边界回归与审查证据

边界规则用静态 AST 测试阻止产品代码越过已登记依赖：私有跨组件 import/member、常见直接及别名动态 import、直接访问 owner 数据文件/数据库。公开 facade/CLI 的合法调用和明确支持的旧合同由正例测试保留。测试守卫在以下位置：

| 代码 owner | 守卫测试 | 快速/默认测试入口 |
|---|---|---|
| IQS | `tests/test_shared_public_boundaries.py`、`tests/test_shared_company_task_api.py`、`tests/test_dashboard_module_boundaries.py` | suite manifest；`scripts/run_tests.py integration --plan` 可见任务 API 合同组 |
| StockQA | `tests/unit/test_quick_scan_module_boundaries.py` | `scripts/checks.py` daily target |
| StockWiki | `tests/test_f05_module_api_boundaries.py` | `scripts/checks.py` short target |
| Company Agent | `tests/test_public_api.py`、`tests/test_secret_boundary.py` | pytest 默认测试发现 |
| Agent Runtime | `tests/test_module_boundaries.py` | pytest 默认测试发现 |
| Dashboard | `tests/integration/test_module_boundaries.py` | pytest 默认 `tests/integration` |
| Theme | `tests/test_quick_scan_integration.py` 中 QuickScan client boundary 用例 | pytest 默认测试发现 |
| Industry | `tests/test_quick_scan_module_boundaries.py` | pytest 默认测试发现 |

## Canonical 集成状态核对（2026-11-10）

边界图与静态扫描器的历史 ACCEPT 不能替代共享引擎跨仓接线验收。当前各仓实际状态如下：

- IQS 本地 HEAD `bb20529` 已包含 `scripts/answer_validation.py`、`scripts/shared_company_ports.py` 和调用它们的回归；该提交可独立检出，但尚未推送到 `origin/master`，因为 owner 端还没有锁定版本。
- StockQA canonical HEAD 仍为 `4c24789`；当前 `master` 工作树已出现 `src/utils/quick_scan_company_api.py`（1.5.0）及配套变更，但未提交。
- Company Agent canonical HEAD 仍为 `d0280f5`；当前 `master` 工作树已出现 `src/iqs_company_agent_lab/api.py`（2.3.0）、`public_port.py` 及配套变更，但未提交。
- Agent Runtime canonical HEAD 仍为 `5839ef4`；候选在 `codex/agent-run-02` 工作树，已出现 `src/iqs_agent_runtime_lab/api.py`（1.4.0）及运行支持修改，但未提交，也尚未合入 canonical branch。
- 当前定向候选测试：IQS 19 文件组合 454 passed + 244 subtests（其中包含共享引擎/语义/边界177、task-factory合成合同2、模块/路由/题库214+236 subtests）；StockQA 61、Company Agent 11、Runtime 38 均通过。跨仓 smoke 以只读导入确认三份候选版本和公开操作可解析。上述 owner 侧结果读取未提交工作树，证明当前候选能组合，不证明固定提交的 canonical 组合或清洁部署可运行。

完成条件：三个 owner 分别把 facade 与必要依赖固化为可引用的 commit；IQS 按这些版本固定依赖并推送 `bb20529`；随后使用固定 commit 的隔离干净检出跑跨仓公开操作正例、拒绝不兼容版本反例和公开 capabilities 命令，并经新的独立审查。只收敛这些接口及其必要依赖，不带入其他并行改动。

2026-11-10 TDD 先加入失败的别名与嵌套 `getattr(importer, "import_module")(... )` / `getattr(builtins, "__import__")(... )` 反例，再修扫描器。七个边界套件最终通过：IQS 50、StockQA 24、StockWiki 9、Runtime 9、Dashboard 2、Theme 2、Industry 4 项测试及 12 个子测试；Company Agent public API 两项通过。独立 reviewer `final_modularity_audit` 对扫描器、动态导入探针和模块图给出 **ACCEPT**。后续审查发现共享引擎 facade 的 owner 实现仍有未提交候选，不能将该 ACCEPT 外推为干净检出或生产跨仓接线通过；该集成项仍开放。

这些测试是架构回归保护，不是 Python 运行时沙箱：下划线成员名本身不能阻止任意反射或 `exec`。公开 facade 只导出白名单名称，越界静态调用在测试中失败；不要把该约束表述成抵御恶意代码的安全边界。

## 范围边界

本结论关闭的是上表已登记的活跃生产模块边界和常见绕行回归。它不证明所有未来代码都不可能写出新形式的反射，也不等于真实 owner facts 全覆盖、TH/IN 技能入口实服务 E2E、金融内容准确、G3 的 200 家/G4/G5/G6 或 2000 家规模目标完成。后续新增运行时 owner/consumer 时，先在本表增补唯一 owner、公开入口、版本与允许方向，再在其现有快速测试组加一条正例和相邻越界反例。
