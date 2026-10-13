# 三个可独立开工的后续施工包

状态：仅完成施工包编制与输入冻结，未创建worker仓、未派发、未调用模型。三个新根在编制时不存在，开工必须重查唯一writer。

|施工卡|工作目录|任务|依赖|
|---|---|---|---|
|[ROUTE-E2E-03](ROUTE-E2E-03.md)|C:/Users/郑曾波/Projects/iqs-route-e2e-lab|把47路由案例接原v2公开入口，保留真实失败与不可适配项|冻结IQS+已修ROUTE|
|[CHAIN-SOURCE-03](CHAIN-SOURCE-03.md)|C:/Users/郑曾波/Projects/iqs-chain-source-lab|核36槽位的官方来源，优先18partial及尚未独立核实具名关系|冻结IQS+已修CHAIN|
|[BLIND-REVIEW-03](BLIND-REVIEW-03.md)|C:/Users/郑曾波/Projects/iqs-blind-review-lab|匿名评审包、双人审查/裁决与准确性分母工具|冻结IQS+EVID+FIN+SCORE|

三个包之间没有运行时或交付前置；研究包与离线工具包分离。只写自己的新根，所有现有仓和共享快照只读。真实收费实验、原26/4恢复、生产入库、UI与正式发布由总控负责。

发给harness自身施工卡的绝对路径即可；卡链接[共同规则](common-rules.md)、[接口](integration-contract.md)、[manifest](manifest.json)、[多仓锁](inputs.lock.json)、各自目标和handoff模板。共享快照在 C:/Users/郑曾波/Projects/invest-quick-scan/runs/parallel-next-2026-10-13-01/inputs/；不以浮动最新源码替代。异机需要携带原字节快照及锁。

准备检查：python -B -X utf8 verify_preparation.py。validation.json只代表施工卡、目录边界、锁和模板检查，不是worker产品测试。完成一个稳定候选只做一次包级集中验收，后续仅复跑受影响范围。
