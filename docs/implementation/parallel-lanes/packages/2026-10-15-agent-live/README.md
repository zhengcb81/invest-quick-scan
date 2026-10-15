# 真实公司 agent 实验：三个独立施工包

准备日期：2026-10-15。**可由用户分别派发，尚未派发；总控没有创建三个新仓或启动 harness。** 把下面某张卡的完整路径交给一个 harness 即可；卡内包含共同规则、输入锁、接口及交接链接，不需要复制聊天上下文。

| 施工包 | 做什么 | 唯一可写工作目录 |
|---|---|---|
| [AGENT-RUN-02](AGENT-RUN-02.md) | 把已验收策略引擎与 StockQA 真实研究传输接起来；补真实任务和恢复边界 | `C:/Users/郑曾波/Projects/iqs-agent-runtime-lab` |
| [AGENT-REF-02](AGENT-REF-02.md) | 为三家公司原12题准备独立、逐条核源的参考事实和评分检查依据 | `C:/Users/郑曾波/Projects/iqs-agent-reference-lab` |
| [AGENT-EVAL-02](AGENT-EVAL-02.md) | 把 ResearchRun 1.1 接既有盲评，并产出保留失败分母的质量/费用/时间对照 | `C:/Users/郑曾波/Projects/iqs-agent-evaluation-lab` |

三个物理目录不重叠。RUN 只交执行桥候选；REF 只交参考资料；EVAL 只交适配与评测候选。各自可以用锁定输入与明确合成fixture开发，**不等待其他包的新交付，也不写其他包的目录**。所有新接口先由[共同接口](integration-contract.md)冻结；遇到冲突写 proposal，不擅改接口逼另一包跟进。

总控继续负责 StockWiki 实际主体/新 admission、真实收费实验、参考资格签收及最终跨仓集成；总控不同时修改这三个新根。三个包不调用收费模型/搜索，不消费旧 IQS01 批准，不写生产数据库/名单，不改生产 UI 或正式发布指针。REF 可以使用 harness 自带搜索/浏览核官方 HTML；不读取环境密钥、不另开付费 API。

现状：[S0报告](../../../experiments/company-agent-s0-results-2026-10-15.md)已真实完成12模型HTTP；两模型思考/工具回传/缓存已核验，SDK已提交并推送 StockQA `41763bf`。这不是公司准确性通过。不要重做 COMPANY-AGENT-01 或重新发 S0。原 B01 旧25项后置且账本保持。

固定输入：[inputs.lock.json](inputs.lock.json)，默认快照根 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/agent-wave-2026-10-15/inputs`。这是按目录选择的冻结源码/数据，不是完整 Git checkout。上游即使有新commit也继续用已锁字节；搬机器时把快照一并交接，显式传新根，不回源补文件。输入遗漏可以报告，不能默默追 latest。

准备校验：`python -B -X utf8 verify_preparation.py`。它只验证输入字节、36槽目标、目录边界及交接模板，不代表三个产品已经实现或金融验收通过。用户派发后，工人检查新根当前归属再初始化自己的仓/PWF；准备时不存在不等于永远不存在。

每包都有独立 targets 与 handoff template。统一交接流程和公开形状校验见[共同接口](integration-contract.md)。只在整包完成时集中审查一次；关键机制用TDD、最后整包验证，不增加逐helper审查/回执制度。
