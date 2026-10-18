# CATL 两题原生接线与恢复实验

2026-10-18；当前状态：同一真实安全响应已恢复，Company研究输出完成2/2；原正式搜索checkpoint与金融充分性仍未授予。

本轮验证真实身份、原权限、原预算、共享引擎和安全响应恢复是否能连起来。它不是不同模型/题包策略的随机对照，也不产生投资评级。公司为宁德时代；采用真实 StockWiki analysis subject，FY2025 合并口径，子公司范围仍未枚举。只选冻结 common 3.0.0 的 IQS_12、IQS_16，MiMo mimo-v2.6-pro 开启思考，输出上限16384，一包一次物理请求。

| 观察 | 实际结果 |
|---|---|
| 真实冷跑 | 305.8697秒；安全保存后按计划退出86 |
| 模型请求 | 1次HTTP200；实际模型mimo-v2.6-pro |
| usage | 输入11001、输出11208（包含思考7816）；provider cache命中0 |
| 价格 | 按已锁公开费率估算US$0.014537；不是现金账单确认 |
| 新增搜索 | 模型cell内0；准备阶段另有4次搜索和2次官方HTML打开 |
| 已有未知费用 | 原3笔保留，不结清、不另建预算绕过 |
| 独立金融参考 | 4个唯一数字受支持；派生比率不重复计入分母 |
| 评分/完整构念gold | 均0/2；不能声称整体准确率100% |

两答均选择证据不足、部分覆盖、分数null，有理由保持关注，不制造中间分。独立评审发现 IQS_16 对历史资金总量使用较强流动性措辞，缺少可用现金及义务规模验证；保留该限制和原始答案，不为通过验收重写回答。

第一次全新无密钥、核心进程禁网络恢复耗时68.55秒，因模型可见正文与工具调用同时存在、不符合旧执行回执的单通道要求而停止。修复后同一安全响应可零POST读回，第二次耗时76.66秒，但原批量计划不允许工具执行，正确拒绝SDK返回的 submit_answers，槽数仍0/2。这两个失败/partial现场保留，耗时不能从实验中删去。

当前根修将显式批量模式的未来wire设为纯JSON、无tools/tool_choice。对历史安全响应，先核原任务、原intent、原成员和完整工具外壳，仅把唯一合法的 submit_answers 作为历史运输载体转换为原批量parser格式；答案、题目声明、原始响应hash和原Runner白名单不变。无重新发送、补声明、延长租约或改旧checkpoint。修复经过不同agent整包审查，普通hooks与实际源码31项通过，已只恢复同一份响应到新目录。最终75.0352秒、退出0、2/2槽完成、新模型HTTP0、原native响应重放1次，报告与runtime summary一致。原101条budget、12条work、12条attempt逐行保持；总budget仍102条（99 settled、2 response_unpriced、1 outcome_uncertain）。原三笔未决没有变成已结清，原safe/config/checkpoint字节不变。

本地持久化响应恢复和供应商token缓存是两回事。本轮provider cache命中为0，没有高缓存率或成本优势结论。正确性优先的决定保持：证据缺口先补证据，逐题默认不变；两题工程样本不能批准大包或公司agent生产默认。

原始响应、数据库、实际准入材料和答案正文只留本机私有runs。公开留档仅工程过程、薄指标和独立评审结论。

最终恢复是已接收原回答的工程成功；两答的证据不足和score null保持。runtime summary中的现金费用仍null、owner_authority_verified仍false，它只报告观察值，不承载授权认证；实际原准入链及source pins由独立工程记录核验，不能改写这些保守标记。最终工程与金融薄审记录见同节点review及PWF。

环境：本轮未下载文件。精确测试临时目录清理被自动审批在执行前拒绝，已记录pending_policy并隔离保留；未换方式重试，不能称测试环境全部恢复干净。原库、实际响应、备份及历史失败现场按实验留档保留。

独立工程[最终验收](../reviews/native-continuation-v15-2026-10-18/actual-recovery-final.json)已通过、open_findings为空；金融薄记录c6c0828e...确认导出原答一致。原StockQA两条work仍uncertain且没有lease，不能称正式work完成。后续以显式新鲜publisher及research-only版本接原C06/outbox/StockWiki review_pending，保留旧verified-search规则，不对历史响应补搜索。
