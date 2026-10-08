# SW-REPAIR-02集中独审记录

2026-10-08，独立agent `/root/sw_repair_acceptance_review` 只读审查StockWiki代码、交接和总控实际执行日志。agent未写文件、未跑测试、未调用网络或收费API；以下动态结果由总控在准确提交9f9e0af的私有导出副本执行，不把它记成agent亲跑。

审查对象为master结果`9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f`，当前`6d1dddbc1289a17a2fb91d40a0d4f57494fa1bfd`卡内代码无变动。agent的Git提升曾因其只读任务约束被自动审批拒绝，随后使用总控已获准取得的只读Git基线和确切路径；没有绕过拒绝写仓，也没有因此暂停未受影响验收。

| 发现 | 源码位置（结果提交） | 已取得的验证 |
|---|---|---|
| P1 不可比维度丢失 | quick_scan_profiles.py约92–97的SQL未取segment_id；约225–267的字段投影漏分部/period_start/period_end/basis；quick_scan_rows.py约118–134的variant key缺这些 | 三个公开accepted输入2/9只剩9，>=8通过。subject/model/rubric已有隔离，不能笼统称所有模型混分 |
| P1 备份根/祖先junction | quick_scan_backup.py约97–101先resolve后建立安全根判断 | 两个真实Windows junction create成功，输出在逻辑workspace之外但仍在总控IQS私有根。仅动态证create，不宣称已动态证prune逃逸 |
| P2 owner registry不足 | quick_scan_backup.py约242–249只校schema/records；约315–319匹配digest/name/记录版本而缺owner/workspace绑定 | 未知registry版本及两种foreign记录均授予backup_a删除权 |
| P2 malformed合法JSON | quick_scan_backup.py约537–542对非dict/None调用get或len，异常捕获未覆盖形状 | []/null/0/files=null四项中断list/prune |
| 交接/隔离 | handoff glob、cleaned=false根、interface hash对象 | 公开CLI原exit2；范围展开诊断仍exit2，且worker105截图未在根库存完整列出 |

agent复核原81项/11浏览器GREEN与新增边界RED并存，认可裁决changes_requested及保留现交付；每组整改同批处理一次回归/集中复审即可，不增加小节点审查。

agent另指出初始period/basis用未来年末且current，可能干扰用例解释。总控已将最终输入改为截止2026-09-30的FY2025/2026H1，以及同2026H1 current/normalized，定向重验2 failed/1.13s；原记录保留，最终仍12个逻辑反例失败。修正没有修改StockWiki生产代码、旧case或历史结果。

证据：[实际日志/计数](../../intake/SW-REPAIR-02/2026-10-08/verification/result.json)、[五组整改](remediation-2026-10-08.md)、[最终反例源码](acceptance_cases.py)。无需再为本收尾触发第二轮独审。
