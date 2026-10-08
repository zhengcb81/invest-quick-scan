# Phase108集中独立审查记录

审查agent：`/root/qa_c06_02_acceptance_review`。只读固定QA b6eaa08 / SW cc587a8副本及实际日志，未写任何文件/运行测试。以下由总控记录收到的结论与同批补充意见，测试数字来自实际原日志，不称reviewer独立动态复跑。

主审确认三阻断：JR1 enriched ACK1.0多余字段及未注册内部错误码；JR2首次store只检查字符串、事后从ACK学习；JR3深层重复键last-write-wins。源码定位：SW quick_scan_observations.py:360–379/312、quick_scan_import.py:167/505–527；QA quick_scan_result_outbox.py:341–353/390、quick_scan_work_store.py:3677–3684。IQS ImportAck冻结十根字段，不应放宽additionalProperties。

建议新原生公共DTO在owner导入事务durable保存，公共taxonomy和local审计分离；历史enriched ACK保持原件、严格注册legacy恢复或pending。QA须从公开owner信息事前绑定目标，在begin和ACK事务都校验；迁移后旧terminal只读、缺目标pending不自学。严格文本解码须覆盖深层重复键、数组对象及1e400等非有限，零写入，不退compact/默认分数。核心范围已写[整改卡](remediation.md)，不是授权凭证。

原批17实例6P/11F不都是产品failure：J07采集两种item形状，J05未migrate，J11依赖J03缺产物。原J03只改HTTP actual、请求还是A，不能称真正B模型；resolved与requested支持边界应单列。后续模型追溯应严格绑定durable原响应，不能删检查或把actual覆盖为requested。

同批补充审查已读corrections stdout/process、additional-results与c-j11-query原件。补批9实例7P/2F独立保留，不加总称整套通过。J03同模型B_DIRECT实际CLI0/31替身HTTP；J11公开>=8查询total0/rows[]，原2/9详情ambiguous、两变体；J07五个错键同一get_item完整前后快照均拒且不变，send_intent后的wrong store仍错delivered；J05空库拒且观察0但entity_not_found违反公共枚举；独立q8 warm/sealCLI0/HTTP0/attempt及包不变，不依赖J06。

J01仍缺ACK闭环；J02/J08只证运行子范围；J05真实owner身份缺；J09非模型结果unknown/预留全链；J10仅SW单侧恢复；J12能力为false不证F05。UI只调用builder，不是浏览器验收。真实身份/事实golden、G3/L03/F05/THIN仍开放。结论：**partial_verified / changes_requested**；原三包的有限软件成果不重开，只修当前三项跨仓边界并集中回验一次。
