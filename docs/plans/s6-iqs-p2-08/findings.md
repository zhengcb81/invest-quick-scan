# 已发布入口和现行边界

| 正式路径 | 实际责任及原协议 |
| --- | --- |
| `scripts/open_dashboard.py` → `iqs_scan/workbench/open_dashboard.py`，Windows `start_workbench_background.ps1` | 启动只读服务、显示快照、状态 ready JSON。无刷新不访问模型或 owner。配置、启动、服务端原失败归 IQS。PowerShell 是正式无窗口宿主入口。 |
| `iqs_scan/workbench/dashboard_http.py` 的真实 listener | 静态 GET/HEAD、产品 GET/POST/PUT、CSRF/host/origin、body 和 JSON 协议；错误有既有 JSON schema，日志不能泄露请求或凭据。 |
| `scripts/workbench_snapshot_cli.py`、`view_quick_scan.py`、`run_answers_page.py` | 独立发布读取、渲染和离线计划。保留原读取权限和原输出。 |
| `scripts/one_click.py`、`thin_scan.py`、`question_sets.py` | 快扫计划、原题目和实际 provider，保持每题原 scope 及已公开字段。 |
| `scripts/dashboard_prepare.py`、`dashboard_owner.py`、`owner_job_cli.py`、`iqs_feedback_owner.py` | 原准备、协调、提交、执行、回读、恢复、原过程日志。公开 JSON 归对应 owner，保持已有 idempotency 和原费用判定。 |
| `scripts/identity_contract_cli.py`、`query_contract_cli.py`、`refresh_contract_cli.py`、`subject_dispatch_cli.py`、`parallel_handoff_cli.py` | 发布契约与跨层公开调用。保留原请求和已登记回执，避免在日志边界重新派发。 |
| `scripts/status_report.py`、`run_tests.py`、`ci_tests.py`，其他历史脚本 | 工程状态、当前正式验证、历史复现和离线出版。对照实际安装和引用记录；历史 pilot 及测试工具不能充当真实业务主入口。 |

已发布 C06 正例已覆盖原准备调度前与真实派发后强停、未知付费冷查/RF 风格重放、间断响应与逐题独立诊断。复用 `docs/plans/s6-p1-08-iqs-2026-11-28/c06-native-recovery.json` 与现有 owner tests。B04 按中央 anti-trick 的已实际证明范围标识。

当前代码线索为 `open_dashboard` 的普通 argparse、配置、绑定和原生访问日志，`workbench_snapshot_cli` 的普通 argparse 与出口失败，以及 `dashboard_http` 弃用捕获到的实际异常。`providers/provider_transport` 仍一次无界读取，须先核对调用者已有配置/预算契约再决定日志卡内的修复。`tools/status_report.py` 两条个人路径仍在执行源。Busy 准备已有明确的原失败冷读，原作业文件在别人持锁时继续保护。
