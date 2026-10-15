# 真实公司 agent 实验：三个独立施工包

准备日期：2026-10-15。**最新：REF已正式交付，总控核源并直接修复，payload a179149/交接cc51a26，真实源55P；仍为部分参考，未授金融资格。RUN/EVAL尚未见正式handoff，继续保留活动writer边界。** 各包原输入锁保持，不自动派发；REF实证见[验收报告](../../../experiments/agent-reference-acceptance-2026-10-15.md)。

manifest的workers_dispatched=false/root_existed=false保留为准备时快照，不是实时台账。当前施工状态以本段用户确认及总控PWF为准。总控已生成截止13日的新路由候选，但未安装/授权；见[总控接续](../../../experiments/company-agent-route13-candidate-2026-10-15.md)。新候选不修改worker的原输入锁，不要求追latest。

| 施工包 | 做什么 | 唯一可写工作目录 |
|---|---|---|
| [AGENT-RUN-02](AGENT-RUN-02.md) | 把已验收策略引擎与 StockQA 真实研究传输接起来；补真实任务和恢复边界 | `C:/Users/郑曾波/Projects/iqs-agent-runtime-lab` |
| [AGENT-REF-02](AGENT-REF-02.md) | 为三家公司原12题准备独立、逐条核源的参考事实和评分检查依据 | `C:/Users/郑曾波/Projects/iqs-agent-reference-lab` |
| [AGENT-EVAL-02](AGENT-EVAL-02.md) | 把 ResearchRun 1.1 接既有盲评，并产出保留失败分母的质量/费用/时间对照 | `C:/Users/郑曾波/Projects/iqs-agent-evaluation-lab` |

三个物理目录不重叠。RUN 只交执行桥候选；REF 只交参考资料；EVAL 只交适配与评测候选。各自可以用锁定输入与明确合成fixture开发，**不等待其他包的新交付，也不写其他包的目录**。所有新接口先由[共同接口](integration-contract.md)冻结；遇到冲突写 proposal，不擅改接口逼另一包跟进。

总控继续负责 StockWiki 实际主体/新 admission、真实收费实验、参考资格签收及最终跨仓集成；总控不同时修改这三个新根。三个包不调用收费模型/搜索，不消费旧 IQS01 批准，不写生产数据库/名单，不改生产 UI 或正式发布指针。REF 可以使用 harness 自带搜索/浏览核官方 HTML；不读取环境密钥、不另开付费 API。

现状：[S0报告](../../../experiments/company-agent-s0-results-2026-10-15.md)已真实完成12模型HTTP；两模型思考/工具回传/缓存已核验，SDK已提交并推送 StockQA `41763bf`。这不是公司准确性通过。不要重做 COMPANY-AGENT-01 或重新发 S0。原 B01 旧25项后置且账本保持。

固定输入：[inputs.lock.json](inputs.lock.json)，默认快照根 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/agent-wave-2026-10-15/inputs`。这是按目录选择的冻结源码/数据，不是完整 Git checkout。上游即使有新commit也继续用已锁字节；搬机器时把快照一并交接，显式传新根，不回源补文件。输入遗漏可以报告，不能默默追 latest。

**开工还须读[owner对齐补充](owner-alignment-addendum.md)。** 真实预检发现IQS_11按类型替换为OPERATING_01，原逻辑槽与实际题须外置显式投影，原targets/输入锁保持。额外只读诊断输入锁与当前cutoff不符边界均在该补充内，不是新执行授权。

准备校验：`python -B -X utf8 verify_preparation.py`。它只验证输入字节、36槽目标、目录边界及交接模板，不代表三个产品已经实现或金融验收通过。工人检查自己工作根归属，沿自己已初始化的仓/PWF继续；准备时不存在不等于永远不存在。

每包都有独立 targets 与 handoff template。统一交接流程和公开形状校验见[共同接口](integration-contract.md)。只在整包完成时集中审查一次；关键机制用TDD、最后整包验证，不增加逐helper审查/回执制度。
