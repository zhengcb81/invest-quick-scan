# IQS P1-08 调查与 owner 依赖

以原发布版本在无密钥、无邻仓的原生 Windows 环境执行 `pytest tests --collect-only`，发现 2,367 项以及 8 个收集错误。旧 CI 清单无法暴露这些异常。涉及早期研究工具实验、Company Agent 与 Runtime 本地组件、StockQA 私有测试夹具。GitHub 配置没有这些草稿仓的可签出处。

| 来源 | 需要它的测试 | 复验输入 |
| --- | --- | --- |
| Company Agent 与 Runtime | Company 工程约束、回放、语义、原始保存链及 native C06 | 两份固定 Git SHA，仅导出源码及必要合成 fixture |
| StockQA | 原 owner 绑定和 runner 交付、native C06 | 固定仓版本与原可公开 DTO 对照。历史组合仍读取 StockQA 确定性测试辅助模块，留给后续端口整改 |
| StockWiki | 原身份/发行人登记、准备和交付、共用分析 | 固定版 owner 公共 CLI 及临时 SQLite |
| UI 与 Dashboard | 原产品构建、浏览器和 Viewer | 对应已授权仓或私有组件的固定版本、Node/Chromium 与独立目录 |
| 历史研究工具 | Owner Company Agent Contrast | 三个本地 lab 的固定版本，加明确指定的冻结试验输入 |
| 旧路由基准 | 旧 48/222 版本发布对照 | 固定老版本的题库、schemas |
| Research Consumers | 到 StockWiki、theme、industry 的复用 | 完整冻结 C06 与三方已公布入口 |

需要外部资料的混合模块使用 `owner_assets` 逐节点标记。自足节点留在 `tests/`；整个模块因真实 owner import 不能在自足环境收集时，才迁往 `owner_tests/`。旧分组完整性测试仍跟踪两棵树，防止文件消失。复验混合节点可在配置资产后用 `pytest -m owner_assets tests` 收集；从运行器调用时显式启用 `owner_assets` 隔离环境。旧的 `native` profile 按模块分别启动，以免测试清理全局模块后相互污染；需要 `IQS_C06_RUN_INTEGRATION=1` 及 `IQS_C06_OWN`、`IQS_C06_COMPOSITION_CODE_ROOT`、`IQS_C06_COMPANY_ROOT`、`IQS_C06_BRIDGE_ROOT`。

自主 CI 仅为原生 OS 独立矩阵。依赖 Win32 console/sharing 的节点显式标记 Windows。任何自主套件 skip 都不能提供执行覆盖。在测试环境内启动的 Python 使用回环地址安全护栏。替换环境的子进程及非 Python 程序由相应用例隔离，不能从通用护栏推断所有子程序已阻断出网。
