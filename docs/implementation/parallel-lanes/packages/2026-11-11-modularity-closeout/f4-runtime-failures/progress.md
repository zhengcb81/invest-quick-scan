# IQS 日常失败接入进度

## A 事故与红测

主线基线是 `296ab842`。2026-11-21 原始中微重评留下两项持久化错误，具体异常链缺失。由原工作区保留的八个离线 RED 在基线全部失败。总控的七例进程外基线覆盖缺文件、坏 JSON、全题失败、投影拒绝、HTTP 500、存储拒写、强杀，原有五个原生 F4 回归正常。独立续测还发现各题失败原因不同时整批可误报正常，及诊断目录失效导致独立投递目标漏报。

## B 已实现

- 提前捕获 CLI 入参、结果读取、完整题目内的执行失败。题库覆盖、业务可用性、费用分别保留原义，合法的证据不足仍是正常资料。
- HTTP、准备与交付作业和原 owner 子进程保留稳定作业标识、步骤、安全异常链、源码函数及行号。原生只读取允许的异常类型、errno 和代码坐标。HTTP 保留既有公开状态码。未知子进程状态从原作业冷读，保持未知。
- 可选日志的打开、写入、刷新和关闭独立于 stdout 的持续排空与原进程 wait。子进程原退出码、原生登记和账务由对应 owner 保留。
- 原生诊断位于 `<state_root>/diagnostics/<uuid>.jsonl`。对于没有启动器的普通调用，在原状态根 `observations` 内先原子写完 `feedback-<uuid>.jsonl`，最后写同名 `.ready`。已有单次 `RESEARCH_FEEDBACK_OUT` 优先，其次是可选 `RESEARCH_FEEDBACK_DIR`。默认发布 checkout 下相对目录为 `runs/dashboard-runtime/observations`；已配置的 Dashboard 使用其 `state_root/observations`，scan 检查指定 `IQS_FEEDBACK_RUNS_ROOT` 时使用该根的 `observations`。ROOT 据实际宿主配置登记目录。
- F4 JSONL 按 `feedback-observation/1` 仅投递身份、阶段、判定、证据和详情引用。HTTP／日志流不输出密钥、原 stderr 或异常局部变量。原证据存在且投递失败时，公开命令 `python scripts/iqs_feedback_owner.py republish-diagnostic iqs:diagnostic/<uuid> --state-root <state-root>` 可恢复同一身份，成功后重复调用不补发。用 `get-diagnostic` 代替 `republish-diagnostic` 可独立冷读；均不调用 provider 或原任务。
- 定向回归还发现旧 HTTP 测试打桩位置滞后、准备线程可提前与提交方争用进程锁，以及 Windows 读写同一原生引用时的原子替换短暂共享冲突。修正了测试的所属模块、线程登记时序和原子提交。没有提高测试超时或扩大业务限额。

## C 独立验收

原八条 RED 与七条新增故障／恢复测试曾在同批通过。已加入标准库启动、不同原因全失败、诊断 IO 故障降级的回归。先运行 `python -m pytest -q tests/test_runtime_failure_diagnostics.py tests/test_runtime_feedback_boundaries.py tests/test_scan_result_check.py`，再检查现有准备／交付、HTTP 与五个原生 F4 样例。总控可将其 PWF 内的公开 `probes/iqs.py` 指到候选 revision 做七例进程外复验。候选尚待交叉审查和主线发布。

### 2026-11-21 公开入口复验

已提交实现 2da0c95。69 项聚焦回归通过，包括原八个红测、独立冷读、真实子进程日志、HTTP、三条曾失败的旧测试。对同一 Git 快照从进程外运行总控七例，7/7 原生失败都有观察，分别为六条 deviation 和一条强杀后的 unknown。另有一条独立的题库覆盖 expected。原有五项修复、复验和回告正控均通过。总控 JSON 解析错误 0，合成私密标记出现在公开回执的次数 0，强制终止后的原 apply 计数为 1。历史中微两题的具体原因仍未知。本次是离线故障验收；实际工作目录的原生 outbox 还需由总控登记。其他并行专用分支继续保留其原进度。

### 长子进程日志的独审修复

外仓独审用正常子进程在第 1,070,000 字节后写错误原因，退出 29。旧 1 MiB 首段截断导致原作业、日志和 F4 全部缺失尾因。现在由原作业保存一份完整 UTF-8 脱敏文件，顺序读取、刷新、退出和付款判定相互独立。UTF-8、带 BOM 的 Windows UTF-16/32 及可识别的无 BOM 字节序先解码再脱敏。F4 的 evidence_ref 是 iqs:process-log/<id>。可用下列本仓命令查回，不需要源进程或调用模型。

    python scripts/iqs_feedback_owner.py get-process-log iqs:process-log/<id> --state-root <原状态根> --tail-bytes 4096
    python scripts/iqs_feedback_owner.py get-process-log iqs:process-log/<id> --state-root <原状态根> --offset 0 --limit 65536

下一页使用上页 next_offset，游标保证 UTF-8 字符完整。三种编码的真实子进程保留同一独立尾因、退出 29 和脱敏。独审反例、旧八条日志故障、分页及活跃进程共 24 项通过。更早已被截断的原日志无法补回。

同一独审另用未出现在本机环境变量的 password 和 Authorization 凭证验证了新尾读接口。日志现统一在写入前按常用凭证键、Basic/Bearer、URL userinfo、PEM 私钥及实际环境值脱敏；回归包括大记录后三种编码的明文反例。
