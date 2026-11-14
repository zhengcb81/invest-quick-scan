# FACT-CONTENT-01-R2：同一次集中续验结果

2026-10-11。结论：**changes_requested**。原八项缺口和三项内容问题已关闭；剩一个未来断言误伤、一条无效测试覆盖及两个交接清单条目。保留现有交付，不重做原整改。

## 接收基线与实际运行

- 源仓 `C:/Users/郑曾波/Projects/iqs-fact-content-lab`；分支 `codex/fact-content-01-r2`；实际 HEAD `1ece6b2b49195dc5a4514c8b263192cb017eed55`，产品 `fb187d92a5b267f8ec7bcbef10bfc8b396f4bb8e` 是祖先。工作树前后干净；产品到 HEAD 只改本轮交接目录。
- 固定140个受控文件到 IQS 自有 `runs/fc2a/fact`，213个原输入锁文件全匹配。137个 artifacts 中135个匹配；`planning/progress.md`、`planning/task_plan.md` 的大小和 raw SHA 不匹配，与原监测已知问题相同。不能把收到通知当清单已修复。
- 主控实际原生整包回归：**135 passed / 0 failed / 0 error / 0 skipped**，controller 41.354秒，PID62808/exit0。交付者的135P与本次主控运行分开保留。
- 本次独立公开 CLI 正反例共25项：原控制器22项断言匹配；一个错误消息匹配条件写错，实际产品正确拒绝，独立更正后**23项符合预期、2项实质失败**。不把控制器 exit0 当产品全绿，不把两批135与25相加成pytest分母。
- 公开 handoff CLI exit0，只证明交接结构与自述范围。实际 validate、export两次、read-legacy均成功；两次导出的48个文件路径/raw SHA全部相同。

原件目录：[fact-remediation-02](../../../intake/parallel-packages/2026-10-10/fact-remediation-02/)。权威结果 `acceptance-result-01.json`；源固定 `source-freeze-01.json`；主控 JUnit `fact-r2-regression-02.xml`；原始 stdout/stderr/退出码在 `logs/`；原断言与消息匹配更正分别为 `counterexample-original-assessments-01.json`、`counterexample-marker-correction-01.json`。

## 已关闭，不重复实现

原八项通过正常控制及具体原因拒绝：未来来源不能证明当前成立、历史区间不相交、嵌套假秘密路径、真实Windows junction、伪造provenance根/锁、unsourced给true、来源主体错位、member_of引用不存在。原源SHA、缺题、explicitly_absent、日期、不可变导出快照和schema override输出边界保护也保留。

具名 `read-legacy` 实际读取1.0归档45例，保持只读/不导出/未认证。中性根下真实1.0输入的正常控制exit0；同根嵌套 `api_key.json` 实际exit6，说明产品的这个路径拒绝有效。原控制器错误要求消息出现文件名或 `forbidden`，实际脱敏消息是 `secret-like path component rejected`；该断言错误单独留档，没有重跑产品或改原日志。

同次独立只读内容审查确认：FC11设备引用闭合保留业务unknown；FC01仅hardware证据不证明internet；FC05集团与项目公司两个主体和方向已经对齐，源分片同步；46个case ID保留。`valid_to >= as_of` 的含端点口径文档/实现一致。

## 剩余补丁

| 项 | 实际证据 | 要求 |
| --- | --- | --- |
| FR2-01，P1：未来断言误伤 | `case_rules.py:366` 遍历全部assertions并拒绝任何未来valid_from。FC16保持当前主断言，另附未来计划，公开CLI exit4；FC17是合法 `candidate_relation/forward`，relation与strict为unknown、explore为true，亦exit4。两者只有目标 `[period]` 错误，schema和hash已通过 | 未来证据不能授予当前true；保留未知的未来候选、独立的非primary未来补充，不删未来资料或缩成单断言 |
| FR2-02，P2：旧版测试被上层路径掩盖 | `test_r2_counterexamples.py:342` 用prepare生成1.1输入且根名 `legacy-secret`；先由根名拒绝，未覆盖真实旧版嵌套读取。135P成立但这条覆盖无效 | 中性目录、真实1.0包、同根正常exit0后嵌套假秘密exit6，使用实际脱敏错误；不放松guard |
| FR2-03：清单不一致 | 两planning条目大小/raw SHA不符，其余135匹配 | 最终PWF写完后刷新这两个条目并正常提交；不修改历史R0/R1和输入锁 |

下一张补丁卡：[FACT-CONTENT-01-R3.md](FACT-CONTENT-01-R3.md)。这是同一个包级验收的接续，不新增逐helper审查门，不自动派发harness。

## 环境恢复与限制

全部登记进程已终态，成功只读CIM核验自有Python0。先保存真实收到的交接原件/日志/结果，再按lstat、单链接、精确集合、大小/raw SHA清理898个文件和220个目录；`runs/fc2a` 已不存在。真实junction先只删除链接本身，目标字节保持后再随自有集合清理。源仓140文件、213锁输入均无漂移；未动C06活根、共享TEMP、生产DB或名单。

控制器失败同样保留：第一次pytest在初始化被精确Windows NUL设备误挡，未进入测试，修正设备例外后运行；第一次独立控制器拼接重复future import，在解析阶段失败，修正后运行。两者不是产品失败，不用来充当RED。没有联网、API、密钥读取或公司文档下载。

46case仍 `synthetic / production_mapping=not_mapped / production_case_status=not_run`。本次不关闭F05、真实金融准确性、G3、正式题库/词表发布、C06/W15、L03/B01、TH/IN或全池门。
