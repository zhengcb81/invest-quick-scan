# EVID-LAB-01 单项接续整改：LR-02B

状态：`changes_requested`。原六项反例已 GREEN，不重复实现其余五条或改写旧证据。本卡是 LR-02 历史来源绑定链的补全，收到新 commit/handoff 后只做一次受影响复验和集中签收，不增加小节点审查门。

## Owner 与冻结基线

唯一 writer 仍是原 Lab harness，工作目录 `C:/Users/郑曾波/Projects/iqs-evidence-lab`。总控只读此仓，不代改源码。代码结果 `d4360fdbbd9a83d2830066546edf1827ab424834`，本次接收 HEAD `aeff0e68022f56b331a58503df7b53ed8d2b3882`；截至收尾实际 clean、122 原字节工件匹配。开工前重新核实际 HEAD/status，后续有变化则注明差异；不得 reset/clean 其他改动。

仍遵守 [原施工包](../../../parallel-lanes/packages/2026-10-07-wave2/EVID-LAB-01.md) 的 owner/allowlist/隔离边界，只改 Lab 内相关源码、测试、版本/schema说明与交接。允许读 IQS 锁定输入；禁止写 IQS、StockQA、StockWiki、真实库、生产名单、共享 TEMP，不调用网络/API或收集新 gold。终端重定向使用 `os.devnull` 或 PowerShell `$null`，不要写 `nul` 文件；不得自行删除外仓路径来补救。

## LR-02B / P1 — 每个历史公开入口先验证它消费的真实归档锁

`fixtures._archive_rows()` 读取的是当前文件，`archive_provenance_verifier()` 新增的完整答案比较没有验证该文件的锁定 SHA。公共 `prepare_fixture_replay()` 因而接受“副本归档与 fixture 同步修改”；同一归档由 index 入口可以正确拒绝。不能把动态计算得到的新 hash 当历史可信绑定。

实现可复用现有严格 `verify_lock` 或收敛为所消费归档的最小可信锁校验；不用造第二套来源声明。校验必须在读取/派生/发布历史诊断之前完成，传入 IQS 根与实际读取根一致。缺锁、缺文件、锁或 index 漂移、归档漂移、重复键/非有限 JSON、错误 run/chunk/question 均应产生稳定非零退出和明确诊断；不得落下 final/staging 或给 summary 写已验证。错误类别与现有 CLI exit2/exit4 一致或显式文档化。纯 synthetic/未收集槽不应被无关历史锁缺失阻断。所有能够发布 historical 来源的公共入口共享该保证，catalog 也不可将漂移来源称已验证。

保留已通过行为：未修改完整历史答案省略可选 hash 可通过；只改 fixture 必须拒绝；原始三归档和34 fixture 可重放；重复键、非有限数值、窗口 abstain、来源标签、输出目标排他性、发布失败清理/同路径重试均不回退。行为/rule版本应按既有兼容规则更新，冻结 fixture 字节及原实验归档不得改写。

## 固定复现与测试包

总控 helper：[run_archive_binding.py](run_archive_binding.py)，原始结果：[archive-binding-result.json](../../../intake/EVID-LAB-01/2026-10-08-second-remediation/verification/archive-binding-corrected/archive-binding-result.json)。该 helper 有已经清除的单次根，不能直接原地重跑；按其中逻辑使用新的本仓独占根，路径只指向副本。

1. 复制锁绑定128输入文件，逐字节验证，再固定原 lock/index 不动。不要复制真实库、凭据、ignored配置，也不要指向真实 IQS 写入。
2. 正例：FX032完整答案省略可选 `answer_sha256`，真实 CLI exit0。
3. 负例：只改 fixture 的 score/rationale、归档不改，真实 CLI 非零不发布。
4. 核心负例：副本中只修改匹配 run/chunk/question 的归档答案，同步改 fixture、去掉可选 hash，保留原 lock/index。真实 CLI 必须非零且无 final/staging；本轮实际 exit0、发布 historical、`verified_before_write=true`。
5. 控制：同一漂移副本走 index，必须非零不发布；本轮实际 exit2。另覆盖 missing lock/archive、catalog 历史校验、synthetic 无历史根的正例，避免只靠总控外置先验保护。
6. 红绿测试、受影响单元/集成、三归档双重放/34fixture集中跑一批。原108结果不重复泛跑无关仓库或收费矩阵。保存原日志，不将残余案例改成 xfail/预期通过、不用重新签篡改锁凑绿。

初次总控 helper 将输出放 LAB 外，四命令均被 exit3 正当拒绝；这是 controller 错误，不是产品失败。原日志保留。正式反例是在 LAB 内新输出根重跑所得。

## 交接与收口

返回实际 base/result/HEAD、版本/rules、改动范围、双 hash 工件索引、原反例 RED→GREEN、相关公开 CLI 正反例、输入不变和严格临时清理证明。明确记录会话外写事故与测试运行边界；不以空 `out_of_scope_writes` 或测试 `external_writes=false` 宣称全会话从未越界。归档原字节与 Git EOL差异分别列示，不能清洗日志或历史 fixture。

proposal 继续 `draft_not_signed / execution_enabled=false / live_not_run=true`，本卡不签预算/实验、不重跑 Phase96，不关闭完整 L02、人类 gold、G3、F05、TH/IN 或 L03。收到交接由总控核验真实新快照，合并这一个缺口的收口结果。
