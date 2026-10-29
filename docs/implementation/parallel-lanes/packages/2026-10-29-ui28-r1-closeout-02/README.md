# 两个R1补交02：本轮重验后的有限收口

本轮独立重验已确认：COMPARE原4项业务反例全部转绿、交付182项覆盖通过；UNIVERSE原5项反例全部转绿、完整交付254项通过。两包仍有下列收口项，暂不签收/接入生产。原业务源码未被总控修改，旧记录保留。

| 交给原harness | 补交卡 | 唯一工作目录 | 本轮实核基线HEAD |
|---|---|---|---|
| 比较包 | [COMPARE-R1补交02](COMPARE-R1-CLOSEOUT-02.md) | `C:/Users/郑曾波/Projects/iqs-comparison-view-lab` | `61982a72f35fd3250bc1710bc1a9cc3bf2455424` |
| 名单包 | [UNIVERSE-R1补交02](UNIVERSE-R1-CLOSEOUT-02.md) | `C:/Users/郑曾波/Projects/iqs-universe-import-ui-lab` | `be7e1ee07b6366d31e1b7eae60942b8d00f58be8` |

各自原目录可并行收口。正式package_id继续为 `UI-COMPARE-28-R1` / `UI-UNIVERSE-28-R1`，交回路径仍各自 `docs/handoff/<原包ID>/remediation-01/handoff.json`；CLI保持现有R1模式和参数。**“补交02”是本次提交轮次，不新增-R2协议/命令或新的Lab。**

先读本卡 → [共同约定](handoff-rules.md) → [本轮基线锁](inputs.lock.json) → 对应 [COMPARE报告](evidence/compare-final-report.md) / [UNIVERSE报告](evidence/universe-final-report.md)。[上一张R1总规则](../2026-10-29-ui28-remediation/handoff-rules.md)继续适用，本轮仅更新可变目标基线、将其遗留项明确成下面的断言。

- COMPARE剩余：启动失败清理；新handoff/最终审查/测试和fixes引用校验。
- UNIVERSE剩余：哈希await后与迟到resolve的状态归属；错误reviewer/兄弟前缀路径拒绝；最终真实review覆盖实际validator。
- 上轮已过业务无需重做设计；本轮所有新反例修成绿，受影响回归及最终不同agent集中审查通过再交。

本次新增反例均用合成数据，未读取真实公司答案/数据库，未调用真实owner/收费模型/搜索。源的正确功能组和曾出现的验收环境错误分开记，不能用环境失败充业务红，也不能把normal E2E通过说成启动失败路径覆盖。两包主线真实108/SDK仍暂停，最终接原UI由总控负责。
