# Cold 首次失败的独立复核（已补齐原始字节）

结论：现有证据支持这次 DeepSeek 搜索在本地进入原生 HTTP transport 前失败；不是服务商拒绝。旧 driver `f6607fb2…` 把共享 HTTP manager 改成只有 `post()` 的包装器，原搜索调用 `request()` 的属性查找即触发 `AttributeError`。归档 driver、pin-list、preflight、cold-started 和日志的 7 项 SHA 全部独立吻合，解决了首轮读取到正在修复的当前 driver 的歧义。首轮 `needs_investigation` 草稿保留于 `failed-cold-pretransport-draft.json`，追加结论见 `failed-cold-pretransport-resolved-review.json`。

只读核库：模型 attempt / response / checkpoint 都为 0；原搜索 dispatch/result 各 1，failure_type=AttributeError、HTTP status 为空，dispatch 到记录约 0.0099 秒。原适配器在调用 request 前已经消费 permit 并预记 request_count=1；这不证明原生 HTTP 已发送。原 `unknown` receipt、计数和 200000 micros 预留均原样保留，复核未改账本、未读密钥、未发 API。

这些因果证据可作为原公开 `QuickScanWorkStore.reconcile_budget_attempt` 的 `confirmed_not_sent`、实际成本 0 的证据引用；必须保留旧 operation / unknown receipt / 历史，不能直接改 SQL、删账本或重置另库。这里的 0 transport 是对已锁定调用路径的有限因果推断，没有抓包或供应商账单，复核本身不执行 reconciliation，不授予新 lease 或自动重发。

包装器修复已独立读码：只重绑 SDK 模块自身的 manager 为 facade，不修改共享搜索 manager。4 项离线回归 XML 为 4 passed / 0 errors / 0 failures（0.746 秒）；复核读取了测试源码、XML 与清理记录，没有再跑测试。最初沙箱 temp setup 错误另档保留。新 driver 与失败旧字节分开绑定，不能把新回归说成旧冷启动路径已经通过。
