# EVID-REF-02 R1 集中续验，2026-10-11

结论：`changes_requested`。本次已经完成接收、同一次包级独立只读审查、隔离回归、公开 CLI 反例和严格清理；不是缺交接，也不重复实施旧成果。FACT 当前仍由外部 `codex/fact-content-01-r2` writer 修改，本轮没有验收其半成品。

## 接收版本与证据

- EVID 工作目录：`C:/Users/郑曾波/Projects/iqs-evidence-lab`。
- 接收分支/HEAD：`codex/evid-ref-02-r1@70498e40918ea28476b8d0185a0294be7bbb6e0e`；产品 commit `44aa20402125b23de151e2c7c0f4abff7082a7cb`。
- `44aa204` 到接收 HEAD 只有本包交接/PWF/日志变更，产品源码、schema、fixture、tests 不变。接收与结束时工作树均只有 CodeGraph 基础设施未跟踪项。
- 258 个版本管理文件前后原始字节相同；91 项 artifacts 的大小/SHA 全匹配；213 项原输入锁无漂移。原始 1.0 报告另按已交付摘要声明的原始 SHA 验证，不重新生成历史结果。
- `parallel_handoff_cli.py` 返回 exit0 / `handoff_shape_and_declared_scope_only`。这只说明交接结构通过，不代表产品或金融准确性通过。
- 原样隔离副本的修正回归为 **150 passed / 64 failed / 0 errors / 0 skipped**（214 项），没有绿色验收。首次控制器误传 `--basetemp` 与包内 conftest 独占根冲突，112 errors / 1 failure 的原日志保留；第二次移除控制器覆盖，保留真实失败，不改测试或锁来凑通过。
- 同一次独立反例组包含 16 个案例，4 个正常控制均通过；真实 Windows junction 单项接续另 1 案。合并后有 12 个复现案例，归并为下表 **9 个根因**，不能按反例个数宣称 12 个独立根因。

私有接收证据位于 `docs/implementation/intake/parallel-packages/2026-10-10/evid-remediation-01/`：`source-freeze.json`、两个 JUnit、`logs/*.result.json`、`counterexample-fixtures/results.json`、`counterexample-fixtures/junction-result-02.json`、`relocated-input-fixture.json`、`acceptance-result.json`、`cleanup.json`。不在此前授权向 origin 导出的七份 Markdown 之列。

## 不同层次的结果

原样搬到隔离目录时，`pack.py` 以运行路径匹配原锁内绝对 `repository.root`，因此正常 pack 在进入其他语义约束前就被 `required input is not covered by the batch lock` 拒绝。不能把随后所有反例的 exit2 当目标约束通过，也不能更改真实输入锁或改回在源仓执行测试。

为区分余下缺陷，主控复制已逐字节验证的 213 项输入，生成**明确标为合成的重定位锁**：只改 `repositories[].root` 和 `files[].source_root` 路径，所有文件大小/SHA 及其他锁元数据不变；相应 pack 只更新该锁引用大小/SHA 和 pack_id。原锁、原 pack、原源仓均未修改，也没有 monkeypatch 产品 guard。该重定位正常 pack 经公开 CLI 返回 exit0；下面采用它的公开 CLI 反例均属于隔离合成输入，不证明原交付的可搬迁性，不成为真实 owner golden 或金融 gold。

| 编号 | 问题及实际反例 | 结果与应有行为 | 根因位置（EVID 仓） |
|---|---|---|---|
| ER2-01 | CATL F01 保留真实结构化数值/单位/期间；rationale 仅 `2024。billion。`，或把营收改说利润 | 两案 text accuracy 仍 supported；应缺证或矛盾，年份/单位共现不足以支持营收语义 | `reference/compare.py:353`、`:502`、`:209` |
| ER2-02 | `status=unknown` 保留 166.77；`insufficient_evidence` 保留 score8 | numeric/score accuracy 仍 supported。公开 evaluate 同时记 unknown_total 和该条 numeric supported；应明确拒绝矛盾，或不得计正确 | `reference/compare.py:83`、`:230`、`:716`；`reference/evaluate.py:272` |
| ER2-03 | IQS_10 保留冻结题目/hash、缺 ROIC/WACC，补合法 4..9 区间；仅改 definition 为 Operating performance | validate exit0，score accuracy supported；应依据冻结题义判定资本回报缺口，不能靠改名字绕过 | `reference/model.py:295`、`reference/pack.py:470`、`reference/compare.py:754` |
| ER2-04 | IQS_05 仅把两端来源改成不存在的 SRC-9999 | validate exit0、score accuracy supported；应在目标来源闭包约束失败，正常真实来源控制继续可用 | `reference/pack.py:458`、`reference/compare.py:698`；schema 端点定义 |
| ER2-05 | `.temp-roots` 是指向本轮另一自有目录的真实 Windows junction，目标 generated 目录合法 | summarize exit0、输出成功；应在任何 staging 写入前 exit3。链接仅自身移除，目标哨兵未变。首次沙箱拒绝建链接的记录保留，单项接续在授权沙箱外真实复现 | `reference/entry.py:67`、`:147`、`:185`；共享 `cli.py:315` |
| ER2-06 | 真六题请求删 F02 答案，再删除 question_ids；原请求指纹仍保留 | evaluate exit0，requested_total=5 / missing_total=0；有显式六题的控制为6/1。应从冻结请求重建或拒绝缺依据，不能把答案数当请求数 | `reference/evaluate.py:147`、`:166` |
| ER2-07 | 公开 summarize 读取真实旧1.0报告的字节副本 | 新1.1摘要 accuracy_run_counts.numeric.supported=102，等同旧 consistency。应保留一致性，准确性不可因此升级；notice 文字不足以约束结构化消费者 | `reference/summarize.py:67`、`:104`、`:178` |
| ER2-08 | 正常 CATL F01 的 source_checked 仍 passed，但 actor/recorded_at/ref 全 null | validate exit0，numeric accuracy supported；应缺资格或约束拒绝，不能仅靠 passed 字符串 | qualifier schema、`reference/pack.py:452`、`reference/compare.py:146` |
| ER2-09 | 已核验全部字节的正常原样隔离 copy | 正常原 pack validate exit2，64 项回归失败。需明确且受校验的重定位机制，仍绑定原 source role/path/hash；不能放宽锁或到源仓跑测试以隐藏问题 | `reference/pack.py:190`–`:219` |

上述 `reference/` 位置指 `src/iqs_evidence_lab/reference/`。代码行来自这次接收产品，后续整改应以新 HEAD 的符号定位为准。

同一次内容审查另发现两项，**未冒称已用联网或金融 gold 证实**：citation 只核 `exact_passage` / URL / supports_claim_ids 声明和短事实自有哈希，不独立证明当前 claim 的语义；Alphabet IQS_05 的4..9端点仍由收入/盈利/capex等泛化事实支撑，缺可复制成本、机制和转换成本证据。应保留候选判断/缺口，不能把区间内分数自动当作金融准确。

## 保留成果与交接

R1 已改善非 passed 来源、登记冲突降资格、无值合规弃答、有 question_ids 时保留缺答、冻结公司/挂牌绑定、顶层/嵌套 secret guard、合法目标白名单及旧 schema 字节保留。不要退回旧版或重复实现这些内容。

后续使用同一次集中续验，修复说明见 `EVID-REF-02-R2.md`。完成九类根因和两项内容口径后，回归一次、公开 CLI 正反例一组、包级独审一次；不为 helper 或单项补丁追加门。G3/F05/B01 等整体门仍开放，human_signoff 仍 false。

本轮全部已记录子进程实际结束，成功只读 CIM 查询匹配0。按精确集合、lstat、单链接、大小/SHA 删除520文件/183目录，`runs/p114er1a` 不存在；原 C06 `runs/c15a`/真实 owner 副本、外仓、CodeGraph、共享 TEMP 和未知文件均保留。socket/收费API/公司文档下载0。FACT 只确认已有索引和活动 R2 分支，不重复初始化或介入写入。
