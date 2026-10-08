# EVID-LAB-01 第二次残余整改验收

2026-10-08，总控 `/root`。结论：`partial_verified / changes_requested`。**原六项残余修复均已验证；仍有同属 LR-02 历史来源链的一处 P1，不签整包。** 只有一轮集中独审，补充四项公开入口正反例用于证疑，不新增小节点审查门。

## 接收与范围

Lab 分支 `codex/evid-lab-01`，基线 `380cb496f30c72128c2cc8e3c88e36924f3c4f2c`，代码结果 `d4360fdbbd9a83d2830066546edf1827ab424834`，交接 HEAD `aeff0e68022f56b331a58503df7b53ed8d2b3882`，初始与收尾实际 clean、无 remote。结果后的28条路径是交接证据与 `tools/make_artifacts.py`，无运行源码/测试/fixture 后续修改。

122/122 工件工作树原字节 size/SHA 与 Git blob OID 匹配；102件工作树与 Git 字节仅 CRLF/LF差异。按接收 commit 导出123个跟踪文件，程序只在 IQS 新独占副本运行。复制的 worker handoff/logs 保留原字节，Git存储属性不清洗日志。[初始核验](../../../intake/EVID-LAB-01/2026-10-08-second-remediation/artifact-verification.json)和[收尾核验](../../../intake/EVID-LAB-01/2026-10-08-second-remediation/artifact-verification-after.json)分开保存。公开 handoff 用本波正确 catalog exit0，仅证明结构/范围校验有效。

版本确认：CLI0.2.1、diagnostic schema1.2.0、fixture schema1.1.0、semantic/structure rules3。Lab源码只读，QA/SW仍由原 harness 独占。没有执行动态外仓树、网络、API、下载或生产库访问。

## 集中复验

| 范围 | 总控实际结果 |
|---|---|
| 当前受影响回归 | 108 passed /14.67s，进程 wall15.871s |
| 原 Phase97 固定反例 | 9 passed；保留原断言，仅 IO 故障定位适配真实 staging，并增加无残留/同路径重试 |
| 原首批边界 | 5 passed；原文件逐字节复制，断言未改 |
| 原六项残余 | 6 passed；原文件逐字节复制，断言未改 |
| fixture catalog | 34fixture /42expectation /350record，0问题；28synthetic、5historical、1未收集真实片段槽 |
| 三历史归档 | 两个新输出根，5个核心 payload 逐字节一致 |
| 逐 fixture 公共 CLI | 34/34 exit0 |
| 整体批次 | 42命令均exit0，含108回归、原9/5/6、catalog、index双跑、34fixture、handoff |

9/5/6与108中的 worker 用例有重叠，**不相加宣称128个唯一方法**。结果和全部原 stdout/stderr 见[复验回执](../../../intake/EVID-LAB-01/2026-10-08-second-remediation/verification/result.json)。原128独立IQS输入与123导出源文件在全部追加案例后SHA不变；224是锁检查次数、127是绑定路径，不能混为唯一文件数。

确认原修复：custom起止不再丢失、只改fixture答案不能借省略hash绕过、`1e400`拒绝、冲突+未知窗口abstain、每条记录来源类别正确、提案实际cap10000费用覆盖。Decimal复算0.82296 USD，展示上界0.83；草案保持 `draft_not_signed / execution_enabled=false / live_not_run=true`，不因接收文件签实验。

## 剩余 P1：LR-02B

[独审](independent-review.md)发现历史 fixture 比对当前归档，却未校验其锁定SHA。总控复制全部128锁定输入到自有根，先逐字节一致、原 lock/index不变，仅修改一份副本 `results.jsonl` 对应答案，通过真实独立 CLI 进程得到：

| 正反例 | 实际 | 预期 |
|---|---|---|
| 完整原答案、省略可选hash | exit0并发布 | 通过 |
| 只改fixture、归档不改 | exit4、无发布 | 拒绝 |
| 同改副本归档与fixture、省略hash | **exit0并发布historical，verified_before_write=true** | **非零拒绝，不发布** |
| 同一漂移副本走index | exit2、无发布 | 拒绝 |

正式四项为3 GREEN/1 RED，不是四项全通过。原日志、输入、修改归档原字节、错误发布的summary/diagnostics保留于[证据目录](../../../intake/EVID-LAB-01/2026-10-08-second-remediation/verification/archive-binding-corrected)。[单项接续卡](remaining-repair.md)复用现有锁验证，只闭合这一条来源链，不扩成新评测平台或再做其他六项。

初次补证输出误放LAB外，四命令全被exit3正当拒绝；这是controller错误，不算产品RED。初版helper与原日志保留，改为LAB内全新根后重跑以上四项，没有覆盖初版证据。已知路径首次猜错 `historical_model_output/FX-032.json` 只读失败，改用实际 `historical/`；一次文档rg通配参数无效改读实际指南，均未写源仓。

## 环境与交接

子进程环境无API key，继承Python audit guard拒绝网络/任意外部child/私有根外写入；不声称完整OS读隔离。546临时文件/136目录，经单硬链、无重解析点、精确集合/size/SHA与严格CIM0，dry-run后Apply逐项清理；全部已知测试会话/同步child终止，私有根已不存在。[清理回执](../../../intake/EVID-LAB-01/2026-10-08-second-remediation/cleanup-receipt.json)与[lstat清单](../../../intake/EVID-LAB-01/2026-10-08-second-remediation/cleanup-baseline.json)留档。源Lab收尾HEAD/clean与122工件不变、源 `.temp-roots` 0项；旧Phase92、共享TEMP、外仓和opencode保留。

worker自述曾误在IQS生成并删除 `nul`，本轮实际未再见此路径；其历史归属/大小没有被总控独立证明。此会话事故单列，不被测试 `external_writes=false` 抹去。总控本轮没有外仓写入，不删除或读取既有opencode.json。

可确认的是先验冻结输入下的有限离线工具范围；公开历史fixture来源链尚未闭合。提案仅接收草案，事实/评分准确性、人类gold、模型实际revision与完整L02/G3/F05/TH/IN/L03均不关闭。PWF记录本轮有限结论；原Lab writer接续单项卡，QA/SW新交接另行回收后按既有联合说明打通。
