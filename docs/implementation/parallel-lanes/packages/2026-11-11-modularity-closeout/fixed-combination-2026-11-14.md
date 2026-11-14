# 模块化固定来源联测

2026-11-14。范围为九个活跃代码仓的公开边界与 I1–I7。产品保留原 CLI，IQS 把 136 个脚本的实现迁入十个能力域。跨域引用显式导出或公开 wire，StockQA 持有请求、已付回答与逐题状态，StockWiki 持有身份、名单与观察 ACK。详见[架构与边界](../../../../architecture/module-boundaries.md)。

## 固定来源

| 组件 | 实现提交 | 本次使用的边界 |
| --- | --- | --- |
| IQS | `30c30c0631ae68cacff8b346e23f584bfb506b90` | 能力域 API、原 CLI、工作台 HTTP、snapshot 1.0、`iqs-job/1` |
| StockQA | `f6897ac5c437f6baa36bae336d2c47a7e1722ad1` | company-scan API 1.8、逐题原生保存和接续 |
| Company Agent | `ba54694ef8027689cfafe2bc31208d3bbf4530a9` | public API 2.3、任务 DTO 1.1 |
| Runtime | `369a44b44e324c1179ae67c6ae3ada67c6a7ef45` | public API 1.4、services 1.0 |
| StockWiki | `9a62022d055c879e8975693555e5228b6bdd9d95` | identity、prepare、名单、ACK 与 facts 2.7 |
| 原工作台 | `3ed63911e29a3398fdab927ae82194b2ce9b1f89` | `src/app` 静态资源、IQS snapshot 和 HTTP |
| Dashboard | `b03e14bb1966aea07a09b58487859421cf302b54` | QuickScanPort、JobPort、HTTP 与 CLI |
| Theme | `00e4fbde8529cf1c895e9c17c005b131de36e089` | 公共 facts query/export |
| Industry | `bb0c3b9255cca0944e5f127e42cd10a3797eae52` | 同一公共 facts query/export |

StockQA 与 Industry 的既有远端分支已核对为表中提交。Dashboard 已推 `b03e14b`，另一个进程随后发布 `e6a9efc`，其历史包含本次提交。StockWiki 本地 `master` 后续为 `21cf489`，包含 `9a62022`，该仓无远端。Company Agent、Runtime、原工作台和 Theme 为本地仓。

## 联测结果

| 场景 | 主要断言 | 结果 |
| --- | --- | --- |
| I1 公开边界与替换 | 域间依赖方向与导出、窄 API、错误版本、跨私域负例、三市场身份向量及冲突 | 196 项通过，71 个子测试通过 |
| I2 普通与共享执行 | 普通 31 题逐题保存、冷重启零新增请求、重复封包。共享原生 SDK 冷重启恢复两槽，HTTP 替身只收一次 | 普通与共享各 1 项通过 |
| I3 已付与未知 | 已付首题恢复、封包、入库与 ACK。次题原状态未知时暂停，另两题保持未发。第二次接续没有重发或重复入库 | 混合 1 项通过。另有未知请求冷重启负例 1 项通过 |
| I4 缓存 | 新鲜复用零新增请求、过期后刷新、只读历史不延长有效期，保留原日期与 ACK | 1 项通过 |
| I5 事实消费 | Theme 与 Industry 通过实际 StockWiki 2.7 公开 CLI 读取同一隔离快照，核对分页、导出与异常输入 | 1 项通过 |
| I6 原工作台 | 数据目录、另一检出、静态快照、真实 owner 名单、Chromium 的显式启动与重开。重开只查原任务 | 19 项通过，两个历史 VIEW 外部夹具未安装而跳过 |
| I7 Dashboard | 真实 IQS HTTP/CLI 与 Dashboard 浏览器。模拟提交响应丢失后按原命令 ID 查回，一次提交 | 2 项通过，有两个既有 websockets 弃用提示 |

I2–I5 初次全绿的 IQS 固定来源为 `2f9838190b3041b963c9579801412645bef45cb1`，其余仓固定提交与表一致。与 `30c30c0` 比较，产品源码只改了 `open_dashboard.py` 及 `verified_evidence_audit.py` 两个入口。I2–I5 的实现和实际测试文件一致，I1、I6、I7 已从 `30c30c0` 重跑。另从主线候选运行 `python -B scripts/run_tests.py fast --temp-root C:/Temp`，1127 项和 391 个子测试通过。

## 复现

使用表中 Git 提交导出短路径。各命令在独立进程运行，工作库、账本、浏览器和日志使用临时目录。原生子进程测试使用真实目录 `OWN/{qa,sw,iqs,company,bridge}`。将 `IQS_C06_OWN` 指向 `OWN`，设置 `IQS_C06_COMPOSITION_CODE_ROOT`、`IQS_C06_COMPANY_ROOT`、`IQS_C06_BRIDGE_ROOT` 到对应固定根。固定 UI、Dashboard、Theme 与 Industry 源码分别由 `IQS_UI_ROOT`、`IQS_DASHBOARD_ROOT`、`IQS_THEME_ROOT` 和 `IQS_INDUSTRY_ROOT` 选择。I7 的 web build 来自 Dashboard 锁文件的 `npm ci`，由 `IQS_DASHBOARD_TEST_WEB_ROOT` 选定。清理模型和搜索凭证。Python 网络守卫仅允许字面回环，模型和搜索由确定性传输替身提供。

用 `python -B -m pytest -q -p no:cacheprovider` 运行以下节点。StockQA 的原生集成设置 `IQS_C06_RUN_INTEGRATION=1`，禁用自动加载插件时显式加载 `pytest_asyncio.plugin`。

| 场景 | 测试入口 |
| --- | --- |
| I1 | IQS 的 `test_shared_public_boundaries.py`、`test_dashboard_module_boundaries.py`、`test_shared_company_task_api.py`、`test_question_manifest.py`、`test_question_fingerprint.py`、`test_identity_wire_profile.py`、`test_identity_contract.py`、`test_company_scan_guards.py` |
| I2 | StockQA `test_qa_c06_02_subprocess_cli.py::test_real_subprocess_cold_warm_and_seal_with_the_stub_only_at_http`，IQS `test_company_scan_native_e2e.py::test_original_dynamic_scan_owner_sdk_process_resume_no_duplicate_http` |
| I3 | StockQA `test_qa_c06_02_subprocess_cli.py::test_real_subprocess_shared_recovery_restores_saved_receipt_then_pauses_unknown`，IQS `test_unknown_intent_cold_native_e2e.py` |
| I4 | IQS `test_dashboard_prepare.py::test_i4_fresh_reuse_expiry_refresh_and_readonly_history_do_not_extend_cache` |
| I5 | IQS `test_research_consumers_owner_integration.py` |
| I6 | IQS `test_view_launcher.py`、`test_workbench_ui_public_integration.py`、`test_workbench_snapshot.py` |
| I7 | IQS `test_dashboard_iqs_public_integration.py` |

本机测试证据放在忽略目录 `runs/_modularity_20261114/evidence`，保留运行命令、测试统计和简短日志。没有收费模型或搜索请求，没有写入正式数据库或名单。旧准确率报告校验得到 `accuracy-report/2: matched`，旧真实对照实验用其冻结 runner 验证 12 个计划案例和 144 个槽，HTTP 增量为零。

## 根因修复和审查

- StockWiki 原读路径只认可身份 schema 5/6，名单日志升级到 7 后导致预览和事实查询误拒。存储 owner 现在集中声明 5/6/7 兼容，未知 schema 仍清楚报出不可用。
- Dashboard 原先以 `run-` 前缀推断 ID 类型，命令 ID 与任务 ID 重叠时会丢失提交状态。改为经公开命令查询确认，保留一个提交的事实。独立架构审查复现了原错误。
- 独立审查发现动态导入、别名、相对导入和容器能绕过迁移后的静态测试。新增反例先失败，随后合并解析和别名绑定，普通真实代码继续通过。历史施工文档和原始证据保留，快速测试停止用活跃源码字节和新计划去重验旧施工快照。产品运行没有新增门禁。
- 独立审查者 `final_boundary_review` 对 `30c30c0` 的导入边界、公开 API 与工作台兼容给出 ACCEPT。其直接执行了源码域扫描、私有访问负例和公开 DTO 正例。建议追加的事实能力负例单独回归。旧 Python 导入保留兼容，仓内新跨域依赖由 TDD 约束，外仓消费走公开协议。

下一步沿根计划使用真实事实和实际研究入口收尾 F05/W11/G4。此轮结果为软件边界与集成验收，既有真实业务证据继续独立保留。
