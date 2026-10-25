# 原 lease 到期后恢复计划的独立复核

同意使用现有公开接口，条件是先用已锁定的 pretransport 证据经原 API 结算 confirmed_not_sent/0，再等真实 lease 到期。当前公开方法没有立即释放未过期 lease 的入口；不能改 clock、SQL、私有 handles 或另库重开。

原 recover_expired 对 native attempt=0 的到期工作返回 pending，然后由原 engine generation_scope 的 owner batch claim 领取。若出现原 native send intent、response 或 uncertain，必须停止，不能沿此路径强推。

仅改变记录在案的 query_id 会产生新的检索 cache/operation identity；原 shared budget version 只绑定模型预算和检索 route/dispatch/pricing/metering，所以 route 和预算输入不变时 composite 应完全相等。原 task factory 不读 external retrieval；group key 不含 lease，registered task SHA 应保持 a524cb5b…7657。重跑时仍需实际重建并断言 task SHA、generation、owner inputs 与 composite 全相等，不能只引用这份静态分析。

必须保留旧 unknown operation/receipt/dispatch、账本、session 与 pins，另留 retry session 与新 pins。首次失败 model=0，无响应可缓存恢复；新的真实 cold 成功后才有资格检验断网 recover 和再次封存。详细源码 SHA 与运行时必要断言见 unsent-retry-plan-review.json。本复核没有执行结算、恢复、claim、API 或修改生产源码。
