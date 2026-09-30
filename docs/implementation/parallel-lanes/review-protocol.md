# 并行施工包的大节点独立审查规范

此规范由总控发给只读reviewer，不能当作写入授权。目标是审查一个冻结交付包，而不是让reviewer维护第二份计划或对每个小任务重复review。

## 审查输入

总控提供lane handoff、base/head或SHA绑定快照、allowlist diff、相关`tasks.json`与acceptance case、接口契约版本、同一快照的测试日志、隔离环境/清理记录及前次已知问题。缺任一关键输入时报告`insufficient_evidence`，不要猜测实现状态。

## 必查项

- 变更路径是否只在该lane的owned scope和当前获批task allowlist内；共享脏文件是否被误stage。
- producer/consumer输入输出是否和确切契约release/hash一致；向后读取、版本过期、未知字段、迁移失败与历史快照是否失败关闭或按计划兼容。
- TDD反例是否真正命中新公开入口；异步/错误/部分成功/重试/并发/事务/退出路径不能只测helper。
- 本地unit、owner内integration及阶段E2E是否在同一快照运行；测试结果和临时根清理是否有可复现证据；静态test count不能代替实际结果。
- 轻资产、身份、授权、费用和数据隔离边界；不产生隐式下载/无授权网络访问/公司文档、财报或网页正文持久化；日志不含密钥。
- 输出结构是否可横向比较并保留时间、模型、问卷/recipe与字段版本；模块增加/路由变化不静默改写早期数据。

## 结果格式与门槛

每条finding列严重级别、file/line、可复现触发条件、影响、所需最小整改和测试建议，并说明审查的exact snapshot SHA。状态为`approved`、`changes_requested`或`insufficient_evidence`。

- **P0:** 数据破坏/密钥泄漏/错误权限或严重不可逆业务行为，阻断。
- **P1:** 错误分数/身份错并/重复付费派发/观察历史不可追溯/接口破坏，阻断。
- **P2:** 重要边界或测试缺口；大节点关闭前修复，或由总控显式记录已接受风险及范围。
- **P3:** 可延后的维护性建议，不为此重跑无关全套测试。

G0–G6做阶段级独立审查；用户要求的TDD与owner测试仍逐行为变化执行。纯文档或低风险改动不自动触发review；身份、数据库迁移、预算/并发与实际HTTP发送边界按风险加做聚焦review。

Reviewer仅返回审查结果与证据，不直接编辑owner代码。Owner完成修复后，按受影响测试范围重测；只对变更哈希相关的finding做一次follow-up，不重复无关整套review。
