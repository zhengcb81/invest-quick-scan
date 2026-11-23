# F4 · IQS 快扫检查回执闭环

## 执行和归属

本仓既有 F2 检查器会对照冻结题库，标明覆盖率。F4 补齐从公开检查入口产出观察、重新发布本仓检查回执、按同一作业复验和回告的链路。这个修复适用于任何已保存的快扫结果，只在原可用声明和冻结题库覆盖率矛盾时执行。合法部分结果依然返回完整现有答案的检查信息。公司登记与读面继续走各自已有公开接口。

真实偏差为 runs/thin-bank-catl-full-2026-10-22/final 的原 scan-result-check。旧 3dde7fa6 的原检查返回 0 并标 usable=true。实读原答案有 24 题、题库 38 题、已评分 15 题。修复后答题数保持 24，检查回执明确 14 题未覆盖，coverage=partial、ok=true、usable=false，命令退出 1。另两份旧干跑分别为 24/38 和 3/37，旧检查都已标不可用，本次都作为真实阴性对照。

原始输入文件由本仓从配置的运行根按相对 run ID 读取。观察引用即原 answers.json 字节 SHA。一次修复原子提交原请求及修正覆盖回执，随后可独立读回。复验重新读取指向的同一原件，核对实际发布值后才回告。SQLite 文件只登记反馈动作。历史搜索费用取原文件的 cost_micros 字段，完整供应商费用继续记 unknown。派生修复和复验的新增模型、搜索、费用均为零。

## 上线配置

工作目录是已发布 IQS 检出目录。配置 IQS_RELEASE_ROOT、IQS_RUNS_ROOT 和 IQS_FEEDBACK_DB，分别指向发布检出、原生结果目录和 IQS 专用的反馈 SQLite。现场 IQS_RUNS_ROOT 为项目下的 runs，动作库与观察目录独占。以下数组使用实际绝对路径，$变量表示部署时展开。

```text
owner    = invest-quick-scan
cwd      = IQS_RELEASE_ROOT
base     = ["C:/Miniconda/python.exe", "-B", "-X", "utf8",
            "IQS_RELEASE_ROOT/scripts/iqs_feedback_owner.py",
            "--db", "IQS_FEEDBACK_DB", "--runs-root", "IQS_RUNS_ROOT"]
argv     = base + ["triage" | "repair" | "replay" | "report" | "reconcile"]
lookup   = base + ["get-action"]
view     = base + ["get-coverage", REPAIR_ACTION_ID]
```

前四个 actions 逐一配置 argv 与 lookup_argv，宿主将原 action ID 追加到查询命令。reconcile 配置固定 argv，以 lookup 请求只读查询原作业。get-action 回传完整原提交与结果，get-coverage 读回已经落盘的 IQS 覆盖回执。RO 查询先于数据库存在时返回空结果。replay 的 acquisition 为 reuse_only。通用拒绝审视随分诊记录，按冻结题库收窄“完整可用”的判定。

生产者为 scripts/scan_result_check.py --run RUN。IQS_FEEDBACK_RUNS_ROOT 使用上述同一目录。总控 intake run 会设置独占 RESEARCH_FEEDBACK_OUT，并在退出后唤醒处理；其他受控调用可直接设置唯一的 JSONL 路径。run_id 取实际运行根的相对路径，重放原发现时沿用原 RESEARCH_FEEDBACK_ATTEMPT_ID。--previous-check ARCHIVED_JSON 仅用于比较同一冻结运行的旧检查报告；首次审计可以指定该报告。当前报告和历史报告分开投递，新的独立检查使用新的 attempt。

```text
python -B -m tools.feedback_loop.intake --settings SETTINGS --hosts HOSTS run --owner invest-quick-scan -- C:/Miniconda/python.exe -B -X utf8 IQS_RELEASE_ROOT/scripts/scan_result_check.py --run RUN
python -B -m tools.feedback_loop.intake --settings SETTINGS --hosts HOSTS drain --owner invest-quick-scan
```

## 测试和恢复证据

最终定向回归 **283 passed / 40.20 秒**。测试文件列表见机器收据的 regression.suites。独立工作树通过 IQS_STOCKQA_ROOT、IQS_COMPANY_AGENT_ROOT、IQS_AGENT_RUNTIME_ROOT、B03_STOCKWIKI_ROOT 指向本机对应 owner 检出，以公开入口复验已登记读面。兼容性沿既有公开端口，tools 通过公开的 Workbench 入口回放公司登记读，两个观察生产者共用 foundation 的可选 JSONL 出口。

真实跨仓验收在独占短临时目录运行，IQS 源码 9a33d65985737435c0b9b9aee4d4c7a46916017d，CWP 宿主 0d580d75ee5c6bce911b4e4cf04550847a3c47a9。使用同一原生真实运行与两份真实阴性对照，旧版脚本从 3dde7fa6 本地 Git 读取。模拟在修复和回告落盘后、宿主收到 stdout 前退出进程，随后真实 local_host recover 分别从 get-action 取回原修复和回告。重复投递后四种动作各执行一次，后续完整 intake run 无人干预收到回告并清空等待队列。探针捕获外部网络事件为零，核对三份运行的 9 个原文件 SHA 和修改时间一致。

[脱敏机器收据](evidence/f4-iqs-coverage/native-runtime.json)保存执行版本、真实发生、原修复与回告 ID、阴性对照与恢复计数。8 个独立测试目录已清理。发布与组合复验由 ROOT 接收候选后进行。

## 日常调用的收件与部署

普通拒绝、作业非零退出、按 runs 根冷读、已有人为绑定或自动分配的子进程运行编号以及 Windows 物理长路径，由 [本仓日常运行 F4 计划](f4-runtime-failures/task_plan.md) 统一维护。IQS 的收件根在已配置的 state_root/observations。StockQA 子进程使用所属代码根下的 logs/.feedback/observations；实际付款仍查 bundle 原有 admission_config.work_store。
