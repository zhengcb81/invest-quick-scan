# 首家公司真实主体与准入准备

日期：2026-10-15。状态：**真实主体读核通过，新实验尚未获原生准入，不发公司请求。**

先选原登记开发集中的 Alphabet，原因是它已有实际 StockWiki owner 数据，不需要另造实体或改大股票池。源 StockWiki 为9d411c7、StockQA41763bf，tracked业务均clean；未写源仓或三个新worker目录。

## 实际完成

- 在原 owner 工作区调用真正 `QuickScanRouteStore.identity_binding`、`get_for_execution` 和原 IQS route CLI，而非复制fixture DTO。发行人实际为 Alphabet Inc.，identity_revision=1，Windows当前原生principal与原策略匹配。主体/周界来自原owner表与receipt。
- 原路由经过当前时刻的真实执行校验，anchor_version=1、路由层new_execution_authorized=true。这**不是收费授权、12题许可或金融资格**。现有生效policy仍只允许score.iqs_01/MiMo Pro。
- 新S1独立预算库已通过原 `QuickScanWorkStore` initializer与`configure_quick_scan_budget`建立，schema19；总阶段144次模型HTTP上限、USD14.4保守预算、每次USD0.1预留、初步并发2。首家公司计划6 sessions/最多48次，计入S1原144总上限，不是额外扩容。
- 新预算实测requests/spent/reserved/in_flight/unreconciled全部0。配置不等于owner admission；没有创建confirmation、work/attempt或发模型/搜索请求。

原B01 work及旧费用不动；新库路径为 `runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite`。不能重跑configure脚本或删除重建这个库。S0两模型已用完的6次限额也没有改。

## 预检揭示的两个实际对齐点

1. 原路由信息截止2026-10-11，新实验原登记截止2026-10-13。不能把历史manifest的日期手改成13日、重签旧anchor或假装它就是新路由。
2. 原登记12个通用问题中有11个原对象在实际manifest中完全相同。IQS_11由公司类型模块替换为OPERATING_01：两者construct_id都为IQS_11，但原题、锚点、metric和语义hash不同。实际field为score.operating_01，不能冒充score.iqs_11或将实际回答改名为IQS_11。

这是模块化按类型选题的正常行为，不是丢题。原12个逻辑construct槽保持，研究执行必须显式携带“登记题→实际题/field/版本”的投影；同公司三策略用相同实际题，跨公司不同变体不自动混分数。原登记/targets/旧schema保持；在第一次真实公司请求前登记routed12变体与新manifest，不能事后换题。

三包已补[owner对齐说明](../parallel-lanes/packages/2026-10-15-agent-live/owner-alignment-addendum.md)。当前真实投影是历史manifest的诊断材料，execution_ready=false，不作为10月13日新执行批准。

## 下一动作

通过既有公开路由/compose流程生成并保存截止13日的新快照，保留旧route/anchor历史；不能只修改JSON日期或照搬旧LLM回执。随后按实际有效题的field、DeepSeek路线和本次预算准备原生owner scope、预览/确认及QA admission。真实 RuntimePort/独立参考/盲评接线仍分别由新施工包交候选，总控集成。当前没有要求用户泛泛再授权；如原生终端确需确认，应在具体批次准备完整后再给出命令。

StockWiki当前每workspace只有一份生效刷新policy；直接覆盖会影响旧25项恢复权限，故目前未安装/改动旧policy。安装策略切换或增加显式并存机制时须记录原件/回滚边界，不声称原policy未变。不得用budget-only的技术探针路径绕过公司授权。

## 证据与环境限制

本机证据：`runs/company-agent-owner-2026-10-15-01/`。最终native-read-3为PID1692/exit0，先前两次失败日志保留：首次在sqlite connect audit回调中设置query_only过早；第二次是导出器误把原生bytes直接当JSON，曾将TypeError误归为route拒绝。修正后用真实连接query_only和原字节file_ref导出，最终不得引用旧TypeError当产品阻断。

预算配置PID23164/exit0。父/子均keyless、禁网，写入限本轮根，所有原owner SQLite只读；原policy及6库rawSHA、旧B01 work与其他进程README最终闭包见本机closure。临时目录清理与源/进程状态在最终记录核实，不用合成owner正例代替真实读核。
