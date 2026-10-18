# 2026-10-18：主线配套的三个独立离线施工包

状态：**发布前整包独立审查已通过（cards_review18，passed/open_findings=[]），可交给三个独立 harness 实施**。审查记录见 docs/implementation/reviews/mainline-support-cards-2026-10-18/；此处只表示施工卡就绪，不表示已派发、实施完成或生产准入。

主线由 IQS 总控负责共享引擎生产接线、真实公司摘要、原生缓存和恢复验收。本波提供这些大节点可直接消费的离线测试及诊断候选，不再并行改引擎。三包互不等待，也不读其他包的新交付。

| 施工卡 | 唯一新工作根 | 具体交付 | 总控消费点 |
| --- | --- | --- | --- |
| [RELEASE-DIFF-10](RELEASE-DIFF-10.md) | C:/Users/郑曾波/Projects/iqs-release-diff-lab | 不可变题库版本差异、受影响题目和兼容性回归候选工具 | 模块组合升级与旧观察可重放 |
| [SUMMARY-LOSS-10](SUMMARY-LOSS-10.md) | C:/Users/郑曾波/Projects/iqs-summary-loss-lab | 摘要内容丢失/重标检测工具和带预期的保真测试集 | 真实摘要逐字段追溯与重要限定保留 |
| [RELATION-DELTA-10](RELATION-DELTA-10.md) | C:/Users/郑曾波/Projects/iqs-relation-delta-lab | 供应链关系跨时点观察差异候选工具与案例 | 事实时间轴不把未找到当终止 |

必读：[共同接口与交接规范](integration-contract.md)、本卡、[具体输入目录](input-catalog.json)。每张卡都定义完整实施范围、公开 JSON/CLI、验收场景；不需要聊天历史。输入已经绑定现有 IQS Git commit，实施者可以直接冻结，不需要等缺失的 dispatch lock、真实公司参考答案或新模型调用。

准备时（2026-10-18）三个 Lab 均不存在。实施者只创建自己工作根；若开工发现目标已有内容，先只读核对它是否就是本卡的本次接续。无法确认时记录 writer_conflict 并停止写入该根，不覆盖未知内容。可继续自身文档设计，不要求重复申请已有授权。

全部离线、零网络、零收费请求，不读环境变量密钥，不下载财报/公告/网页，不接真实数据库或股票池。无需重做 StockQA SDK/调度/预算/缓存，StockWiki 身份/关系存储，既有 scorer/Claim Guard/Viewer，也不修任何外仓源码。交付均为 candidate_only；总控后续独立决定消费和生产准入。

只在两个大节点审查：本波施工卡发布前一次；各包最终完整 payload 一次并按有效 findings 复审。不要为每个 helper、样例或 schema 设额外批准门。最终必须由真实独立 agent 全面审查、全部有效问题修复并通过后才交接，具体证据规范见共同契约。

输入根仅是 C:/Users/郑曾波/Projects/invest-quick-scan 的明确 Git 对象，不读取其活动工作树。总控主线和旧 Lab 继续施工，不因本波受阻。三个 Lab 不配置远端、不代总控推送；本地正常提交，交接精确 commit 和工件哈希。
