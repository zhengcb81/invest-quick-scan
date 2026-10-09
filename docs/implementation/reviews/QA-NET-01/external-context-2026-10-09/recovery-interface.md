# Phase111 两阶段与跨租约恢复：已验证切片

本说明接续已冻结的runtime-dispatch-interface.md。StockQA生产源仍42a517c/schema8，私有实现schema12未发布；公开main的独立进程恢复和整Phase111验收仍待执行。

## 实际恢复边界

外部搜索已持久完成并结算、回答HTTP尚未发送时，工作租约过期后可由真实recover_expired→claim接续。新租约只读取同一generation/身份/manifest/查询计划/策略及TTL内的原检索结果，保留原operation、原retrieved_at、原context SHA和原费用。warm读取先于密钥、health和新预留；不需要重新提供搜索凭据或再次搜索。

回答的实际HTTP在新租约下创建独立attempt并计费，context-use proof关联原检索；checkpoint2保存后再次打开工作库，只读取原答案和费用，不再claim或发HTTP。external-only与hybrid都按此行为验证，原native事件解释保持。

搜索HTTP结果未知时，原外部操作与Q09预留保留。即使工作租约过期且工作行重新可claim，检索journal仍阻止发送或进入回答；工作pending不是搜索允许重试。旧租约及其旧context在HTTP前被fence，不能由context副本获取新发送权。

模型HTTP在租约过期后才返回时，真实response/model及已知费用可以留账，但context-use不能成为有效proof，不能生成checkpoint或发布回答；work保持uncertain、无法claim重复发送。晚到收到的响应不等于免费失败，也不恢复旧工作者的提交权。

## 实际证据及限制

cross-lease-first-01实际5 passed、195 deselected、0失败/错误/跳过，pytest2.53s/controller3.079s；HTTP边界替身，使用真实client/store/journal/Q09。测试source与16文件776P执行源相比仅tests/unit/test_quick_scan_external_context.py新增五项，其余生产源码与测试字节不变；不为纯测试新增重复跑776项。

这里不是OS进程被杀、公开CLI重启、MCP会话恢复或金融事实准确性实验。未发送但旧租约已过期的外部检索意图仍按现有保守规则等待明确处理，不声称所有断点都可自动恢复。继续逐HTTP计费MCP与真正子进程CLI；整批一次集中静态/回归/独审后才正常源发布，最终严格清理独占根。
