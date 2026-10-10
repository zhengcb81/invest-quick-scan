# C06/W15 非空查询接续：2026-10-10

上一目标回合分类：progress。最新实际IQS HEAD为13d263ed85d1d7b0ba1caf0ce070d23a6d23605d；仅原opencode未跟踪，当前私有owner reader 13P且未发布。本文件是原完整节点的连续实施记录，不新增审查门。

- 当前reader把任何非空观察都显式拒绝，下一步必须接真实store的原payload/ACK与原模型时间，不能停在容易通过的空覆盖。
- 先完整读取旧无事前subject绑定的观察，放入独立legacy_unbound历史数组，不进入当前主体覆盖；历史不按当前subject或route猜填。实际owner保存的payload/hash/导入与ACK序列作为独立引用，projection字节不能重写。
- 有效snapshot应复用已捕获原结果及owner refs，不读当前DB、不用新数据替换；未知/过期/不同query snapshot拒绝。请求新时点不应使旧冻结read_at失效；response_at仍是本次回复时间，整体digest/原数据不改。
- 生产前的必要后续：实际事前sidecar生产与事务导入、当前资格/TTL、公开CLI及真实owner serializer golden。原金融/G3/F05/L03/TH-IN门不变，当前依然0收费API。
- 读取实际owner方法时给定的apply_item等候选名没有AST命中，不据此断言store缺导入能力；继续从已打开源码的实际类方法选正确入口。固定178原SW/64原IQS输入保持，测试仍在独占c15a。

## 历史读取反例预检

owner-history-red-01 实际PID7184已终止，13P/8F，controller2.777秒。其中六项先被新测试fixture的错误item_前缀阻断，实际C06地址须为itm_；这六项不作为实现缺陷证据。修正fixture后用新label运行，保留旧日志。其余已到达实现的两项分别是已知snapshot错误query未给出明确拒绝码、主体索引ID与原JSON不一致却被接受。全部测试为真实SQLite组件加合成数据，收费API0，原输入和guard字节未改。

修正地址后的owner-history-red-02 PID3660终态1，实际13P/8F/2.45秒，六项到达明确observation_projection_pending拒绝。实施后owner-history-green-01 PID23528终态0，21P/2.37秒。最终扩展反例owner-history-fault-01 PID22152终态0，33P/20.22秒，包括实际owner事务产出的5,001份重复delivery；查询只抓原ACK1、全局ACK水位5,002，不扫描/误用所有重复回执。contract-snapshot-01 PID5688终态0，65P/0.89秒，实际执行SHA匹配。33/65各自含原组，不相加成金融准确率。

## 当前已做到与下一动作

- 真实owner旧结构化答案保持DB原字节/ID/hash/模型/时间，严格对照索引和最初accepted ACK；损坏/重复键/外store回执等具名拒绝。只有include_history且符合原作用层、field、实际model和cutoff才返回独立legacy_unbound历史；其subject列不代替事前绑定。
- snapshot目前是同一reader进程内的有界捕获：上限32份/16MiB、单份响应8MiB、TTL一小时；原结果/独立owner refs深拷贝，显式snapshot复读不接触SQLite，query不符/未知/过期拒绝，重启不假称能恢复。这是原节点的一段进展，尚非公共耐久freeze。
- 下一步连续接原事前subject sidecar生产/事务导入与当前绑定投影，并连接原route/refresh计划、资格/TTL和公共query CLI/耐久snapshot。允许的源候选变更必须明确冻结，与未改原依赖区分；不能让当前178原输入不可修改检查妨碍计划内必要接线，也不能不记候选差异就绕过检查。保持原inputs/private源码档案不覆盖。
- 收尾仍只有同一完整C06大节点集中审查。真实owner serializer/golden、公开受控刷新、C06/W15/G3/F05/L03/TH-IN与金融准确性均未签收，收费API0。自有c15a继续保留，旧一次性归档/提交helper不复跑。
