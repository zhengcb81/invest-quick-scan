# 2026-10-29 UI 两包返修入口

这不是新功能波次，而是原来两个交付的**各一份合并返修卡**。总控实际验收均为 changes_requested，现阶段不能合入原工作台。原业务源码/测试未被总控修改，保留原交付；仅按已有授权为两Lab初始化CodeGraph，留下各两份本地未跟踪索引配置。

| 可以交给谁 | 返修卡 | 唯一工作目录 | 实际基线 HEAD |
|---|---|---|---|
| 原比较包 harness | [UI-COMPARE-28-R1](UI-COMPARE-28-R1.md) | `C:/Users/郑曾波/Projects/iqs-comparison-view-lab` | `dd99431d3abda7920cb0a6b0377dae01bc7b53ef` |
| 原名单包 harness | [UI-UNIVERSE-28-R1](UI-UNIVERSE-28-R1.md) | `C:/Users/郑曾波/Projects/iqs-universe-import-ui-lab` | `154afd936c7d1ae84f974eb6c0a689225fa883dd` |

两个源目录互不重叠，可并行修。不得修改原UI、StockWiki、StockQA、主IQS、共享PWF、真实名单或数据。总控保留最终生产接线责任，真实108题主线继续暂停。不要自行派发任务；用户把对应卡交回各自harness即可。

## 开始只需读

本卡 → [共同规则](handoff-rules.md) → [输入/基线锁](inputs.lock.json) → 对应 [COMPARE总控报告](evidence/compare-final-report.md) / [UNIVERSE总控报告](evidence/universe-final-report.md)。原设计、接口和边界仍以 [10-28总入口](../2026-10-28-independent-support/README.md) 为基础；原21输入锁不改，本轮明确补充真实公共serializer参考和交付基线。锁外原仓只读参考需要总控提供精确补充，禁止自行扫描私有数据。

## 已经亲自跑到什么程度

- COMPARE：原unit88、可安全执行的integration58、perf1通过，另正确dispose/remount控制1通过；4个确定产品反例+1个全拦截安全清理反例失败。原CLI21/browser2因清理代码危险未执行，不能说它们通过。外部直接重赋config不是已声明更新API，该诊断已从阻断中排除。
- UNIVERSE：原unit145通过，5个强化后的业务反例失败。Python首次52通过、1项因验收副本没有独立Git index失败，修验收环境后该1项通过；浏览器初轮DNS误屏蔽自己loopback，不记源产品失败，修验收环境后单个真实浏览器E2E通过31.26秒，另5个DOM集成未复跑。没有宣称整套204重现。
- 两包原公开handoff CLI均形状/引用检查valid；这不验证最终独审真实性。实际最终invocation/commit绑定不闭合，COMPARE部分hash为文字或null。
- `evidence/*-product.test.mjs` 是可移植合成反例；总控对本轮发布版本再执行：比较4F、清理stub1F、名单5F，正确连接生命周期控制1P。见 [执行记录](evidence/portable-regressions-execution.json)。这些红是当前缺陷的证据，**不是项目验收通过**。

只进行输入/复现、合并修复与回归、最终独立审查/交接三个大节点；不为每项小修新增审批。交接前必须真实不同agent全面检查，所有发现修复后最终 passed/open_findings=[]。旧审查原件保留，不把旧invocation改写成一次新调用。

总控未来只对新R1交接执行原公开CLI；新manifest的两个package_id分别为UI-COMPARE-28-R1/UI-UNIVERSE-28-R1。各卡写明交回路径。CLI valid不授予生产或金融资格。
