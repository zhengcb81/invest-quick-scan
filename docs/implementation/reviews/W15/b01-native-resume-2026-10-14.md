# 原 B01 原生恢复准备：首条真实预览已就绪

日期：2026-10-14。先前三包验收已由IQS a701725提交并推送；本记录是之后的原B01接续，不能将这里新增owner配置与三包验收的零生产写混为一轮。

## 已完成的真实准备

1. 当前StockQA205b749、StockWiki9d411c7，tracked均clean；没有修改两仓源码。先用CodeGraph查询，索引未覆盖新增owner模块后才读明确源码。原public QA inspector真正成功派生一条原IQS_01 length请求，并非复用旧合成exit0。
2. 对实际26 leased逐条调用当前public derive_work_decision：26 derived/0 rejected，其中15 output_length/null诊断、11 known_response_no_accepted_answer中性诊断。11份诊断基于原状态/无checkpoint/response_sha256实际落盘并核rawSHA；未将“无接纳答案”猜成parser错误。原4 result_ready/insufficient_evidence checkpoint单列保留。原IQS_01幂等键和request SHA与先前成功publicCLI完全相同。请求派生不代表批准或已经恢复。
3. 隔离副本上调用实际QuickScanWorkStore initializer做18→19：原34张表的每行、rowid、类型、原文本与schema对象不变，预算和4checkpoint/26leased保持；只增加空决议表、2不可变trigger及2隐式索引。13项检查通过，副本和临时logger文件已删除。不是对生产库迁移。
4. 已从StockWiki公开--principal读取当前Windows原生进程令牌principal，未复制隔离clone的SID。原owner namespace/store_id/SubjectRef/current anchor沿用；发现真实universe/member均0、刷新配置缺失后，按既有授权备份原6库，使用既有create_universe和add_member公开方法建立只包含原Alphabet试点entity的实验名单及版本1成员，并安装通过原IQS纯结构校验的1.1 policy。仅授权score.iqs_01、原MiMo Pro路线，不自动覆盖其余29题、新公司或模型。这不是用户2000家公司名单的选择或变更。
5. 已在原namespace通过原get_profiles公开CLI生成实际capture，store_id与原派发凭据一致，状态为**coverage_gap**，没有制造评分或参考资格。新captures.sqlite3是公开接口的持久快照库，有本地写，不能宣传整个过程零文件/owner数据库写。
6. 当前原生work-decision预览成功，status=ready、requires_user_confirmation=true、dispatch_started=false。预览由原StockWiki服务重新核当前主体/字段/成员/路由、原QA response/费用/派发原件；没有插入fake confirmer、fixture authority、假confirmation或手填决议。

原work仍为schema18、SHA236e5aa4c4252a37f76c092100c8012c9abff11ee60914edb839bf424b0864e2。原13HTTP/CNY1.268162及旧cap15未改；剩2请求不足后续至少4次的pack3→pack1配对，后续按用户已有预算授权调整实际policy版本/上限/报价，不能清零旧13次。原30work仍26leased+4result_ready，0正式评分、ACK0。

## 当前需要用户完成的动作

现有原生确认要求正确OS主体的stdin与stderr均为真实TTY，再输入当次CONFIRM短语。要求来自StockWiki现有confirm_work_decision_in_terminal，不是新增审查门，也不是重新索取泛授权。总控已经把真实配置与预览准备好，未自动填写挑战。

请在本机自己的PowerShell/Windows Terminal运行：

```powershell
& 'C:/Miniconda/python.exe' -B -X utf8 'C:/Users/郑曾波/Projects/invest-quick-scan/runs/b01-resume-2026-10-14-01/confirm_first_native_work.py'
```

本机专用helper会检查原work与policy、重新生成15分钟内有效的真实预览，再调用原公开--confirm-work-decision；stdin/stderr继承用户真实终端。请读原生界面，按提示输入短语，完成后回聊天回复“已确认”。helper不发送模型请求，不执行QA apply/迁移。它只覆盖首条Alphabet IQS_01已知length结案；并非全26项确认。`--check`已通过；非TTY调用在创建任何新预览前按预期exit2，真实TTY交互仍待用户执行。

初次实际预览ID为wdp1_8d2095d2f0e61c68dbce064ea76a21002699f61e27022dfa829fd75dbffcdca2，2026-10-14T21:43:54.251087Z创建，2026-10-14T21:58:54.251087Z过期。不要让接手者重复使用过期ID；helper每次重新取当前原生预览。ID/hash本身不构成授权。

## 收到真实确认后的精确接续

先读取owner-execution/operator-handoff/<当次UTC>/confirm.stdout.json和实际原namespace不可变confirmation记录，核原生principal/主体/字段/当前policy/原始request。不能据用户一句话手填confirmation ID，也不能伪造或修改原生record。

确认有效后，使用StockQA现有`src.utils.quick_scan_work_decision_apply_cli`，必填参数如下。此处只给绑定来源，**现在未执行**：

|参数|实际来源|
|---|---|
|--ledger|runs/c16b/native-live-pro-01/quick_scan_work.sqlite原绝对路径|
|--policy|runs/b01-engineering-2026-10-11-01/real-recovery-read/policy.normalized.json原绝对路径|
|--owner-code-root|C:/Users/郑曾波/Projects/StockWiki|
|--owner-workspace|runs/c16b/native-owner-alphabet-01/owner-workspace原绝对路径|
|--iqs-code-root|C:/Users/郑曾波/Projects/invest-quick-scan|
|--iqs-release-root|runs/c16b/iqs-release原绝对路径|
|--consumer-id|invest-quick-scan|
|--confirmation-id|上述真实记录产出的rc1 ID，不是示例常量|
|--refresh-schema-version|1.1.0，与已安装当前owner policy对应|

该CLI先由原生owner authority验证confirmation，然后才构造可变Store、迁移19并记不可变决议。届时须切换为明确允许原work写的隔离范围、保留本轮6库backup和逐表摘要；不得沿用本轮只读guard来凑成功，也不能去掉authority。首条执行后应只新增真实决议、迁移结构并中性结案对应work，原其他29项/预算/4checkpoint保持。后续其他字段需要明确scope，普通retry/同模型comparison走1.2，跨模型走1.3及owner目标确认，最后另行Q13准入和原调度器，不SQL补状态、不覆盖旧答案、不重置费用。

## 本轮证据、清理与环境问题

全部本机证据根：C:/Users/郑曾波/Projects/invest-quick-scan/runs/b01-resume-2026-10-14-01/。

- request-preparation/：26组真实intent/request/inspection、11诊断、6库前后SHA、PID19396/exit0、summary/verification/report。
- migration-rehearsal/：实际原生initializer、34表逐行摘要、13检查、父4012/子20992 exit0、cleanup与18件证据清单。
- owner-execution/configure.before.json、backup/、configure.result.json：原6库字节备份和数据摘要，实际只改scan.sqlite的quick_scan_universe/member/member_history三表；新增配置和capture库另记。原另外5库（含work）rawSHA保持。备份是正式回滚资料，不删作临时测试物。
- query-2和preview-4的actual stdout/stderr/process：公开原生成功；之前失败保留。closeout.json核旧表/原件/当前capture/真实预览，临时根空，实际PID+创建UTC闭包0，3个已复用PID只记录不操作。

初次guard阻止QA在源码cwd写默认日志，改为专用cwd；原生子进程仍固定cwd源码的日志被单独重定向到自有目录，未改业务源码。后续明确允许原生capture专用SQLite，并修正guard对Windows扩展路径的比较视图；不改实际原件路径或验证。原子发布原生记录使用同目录硬链接，沙箱WinError5拒绝；同一公开入口按用户既有授权在沙箱外成功，未把环境拒绝冒成产品坏数据。一次空hunk补丁和一次候选重名均在任何目标写前拒绝，后者改root-*独占前缀，未覆盖agent文件。

收费API/下载公司文档/源仓源码写/原work迁移/原work状态变更/确认创建均0；owner配置/成员/capture/preview是本轮明确授权的真实本地写。Financial/G3/F05、生产UI/一键/全池仍未关闭。COMPANY-AGENT-01仍由外包施工，未进入其目录；收到后显式接ResearchRun/BLIND，搜索与费用metadata未知不填0，独立参考资格仍0。
