# Q08 第一段独立复核：持久冷却和半开探针

**结论：partial；暂不能将 Q08 标为 verified。** 在冻结的源码快照上，持久 SQLite 组冷却、跨进程单探针、崩溃后的保守延后、备用组成功不清首选组和坏状态发送前失败关闭有离线证据。发现两个必须修复的运行缺陷；运行级 `waiting_for_provider`/`retry_wait` 待办、逐题成功检查点、预算账本、跨进程容量/派发租约与立即生效的策略热更新本来就不属于本段，仍是独立验收门。

## 审查发现

1. **[P1] HTTP 层隐式重试绕过快扫 attempt 与冷却拥有者。** [`src/utils/http_client.py:39`](C:/Users/郑曾波/Projects/StockQAbyLLM/src/utils/http_client.py:39) 给共享 Requests Session 配置 `total=3`、`POST` 和 429/5xx 重试；[`src/providers/llm_client.py:485`](C:/Users/郑曾波/Projects/StockQAbyLLM/src/providers/llm_client.py:485) 的搜索请求直接用该 Session。离线读取实际 adapter 得到 `POST` 对 429、500 都会重试，`Retry-After: 18000` 会被解释为 18,000 秒。因此在快扫层收到最终响应前，单次公开 attempt 可能已经发出多次 POST，或被提供商的五小时头阻塞，组冷却、fallback、总尝试和预算无法及时生效；若最终变成 `MaxRetryError`，外层还可能丢失原始 429 分类。最小修复范围：让 web-search POST 使用明确不重试的传输，并在 `tests/unit/test_llm_client.py`、公开 CLI integration 反例中断言一个外层 attempt 只触发一个实际 POST。此问题在实施者交接中已经诚实标为后续项，但严重程度仍为 P1。

2. **[P1] 晚到的普通 429 可公布早于真正放行时间的 `next_probe_at`。** [`src/utils/quick_scan_provider_health.py:340`](C:/Users/郑曾波/Projects/StockQAbyLLM/src/utils/quick_scan_provider_health.py:340) 把数据库 `cooldown_until` 保留为较晚的值，但第 345 行返回新事件的 `now + wait`，而且把 `reset_at_source` 无条件改成新事件来源。固定时钟反例：同一路由先有明确 `Retry-After=3600`，1 秒后另一个在途请求收到无头 429；`rate_limited()` 返回 `2027-01-15T08:01:01Z`，而 `admit()` 仍阻断到 `09:00:00Z`，原有的已知来源被改成 `unknown`。当前公开 `retry_eligible_at` 可使用错误的早时间；接入 Q06 接续后会触发无意义唤醒。应从事务中读回最终有效截止时间及其匹配的来源，再返回/公布；补并发晚到 429 的逆序事件测试。

3. **[P2] 晚到的无头额度拒绝会抹去较长且有来源的组恢复点。** [`src/utils/quick_scan_provider_health.py:300`](C:/Users/郑曾波/Projects/StockQAbyLLM/src/utils/quick_scan_provider_health.py:300) 保留较晚的 `next_probe_at`，但第 308–309 行无条件覆盖 `reset_at` 与 `reset_at_source`。固定时钟反例：组先收到明确 `Retry-After=3600`，1 秒后收到无头额度拒绝；实际放行时间仍为 `09:00:01Z`，但 `reset_at=NULL`、来源变为 `unknown`。这不会提前发包，却破坏 PAR-07 要求的已知恢复点与未知标记准确性。与上一项一起在 `quick_scan_provider_health.py` 及其单元测试内修复。

## 验收映射

| 用例 | 本段证据及结论 |
|---|---|
| LLM-03/04 | 顺位 fallback、低分和 unknown 停止已有选定离线测试；本段未改这些逻辑，保留原有限验证。隐式 POST 重试仍破坏真实发送次数边界。 |
| LLM-05 | SQLite 冷却跨重新实例保留，B 成功不清 A；到点仅 A 自己的探针成功才清冷却。尚无持久成功题检查点，因此“旧 B 答案不重跑”未闭环。 |
| LLM-06 | `dispatch_outcome` 准确自称 `retry_wait_recommended`、`scheduled=false`，并给出恢复资格提示；运行级 `retry_wait` 持久任务与接续尚缺。全永久配置错误的路径沿用 Q04 范围。 |
| LLM-10 | [`llm_runner.py:314`](C:/Users/郑曾波/Projects/StockQAbyLLM/src/runners/llm_runner.py:314) 仍在 run 开始取一次策略快照；“下轮生效”符合当前实现；“立即生效只切未派发题”未实现。 |
| BUD-02 | 没有生产账本/发送前预算预留；HTTP 隐式重试还会绕过外层计数，不能验收。 |
| PAR-02 | 多 worker 的组冷却/单探针已可离线验证；晚到拒绝的已知/未知来源不准确，且 HTTP 内部重试抢在组冷却之前。 |
| PAR-07 | 两进程单探针、过期租约延后已验证；无持久待办、预算、尝试轮次和成功题检查点，恢复时间回执还存在上面两处错标。 |

## 可复现检查

冻结交接八文件的 SHA-256 与实施者报告完全一致：`.gitignore` `7E14F2B57B54BEF0C7C69E67B043D1D0F8EAF1DB741FE12A4B6958B715EE4D82`；`src/config/llm_config.py` `A6CF872A115BE1A418CCAA6457DDAE45ABC1FBFEA17A8E1E6AA7E08778D4F4A3`；`src/utils/llm_integration.py` `3E7BAC54444ADF59B7CF4043AB5C150E1AF2BDFC3730B289C42751A2F88C01B9`；`src/utils/quick_scan_provider_health.py` `236DEA178C0F8F1A8D65B8D91EB691CE35125C63EBEB6CE5D2AFEA90E338C59A`；`src/runners/llm_runner.py` `1601273FFC0EB88447DB228471D8CA2CA856D265678F0814F9BB3E3DA9C3E8AD`；`tests/unit/test_llm_integration.py` `1E15243F1CDDA27B90E0D11EAD172C60A731759E74A0BE5332DFB3FF8C81993B`；`tests/unit/test_quick_scan_provider_health.py` `3897DDAA8F9C7E85EF78A54AC5F9B02B792A618E7E2DF26424744B6053705539`；`tests/integration/test_quick_scan_cli.py` `790684938FE0E4036D924B3CB813D4DA977BEBDF35DE51C92FD2638B19B66444`。关联未改源码：`src/utils/http_client.py` `CC441D5626B090D788917450EB08BA6D6141C16732D66A6209246D3072E48F27`，`src/providers/llm_client.py` `9977B097B1EB8870C0DA7FD8F61E6D7318A63C050FF6E506C1D8B9724DECBD3B`。

在唯一系统 TEMP 根设置 `PYTHONDONTWRITEBYTECODE=1`、禁用第三方 pytest 自动加载、清除 API key/live 开关、覆盖 pytest 的 coverage addopts 后，运行三个相关测试文件：`116 passed in 4.49s`。默认沙箱首次因安装包读取权限而未启动；加权只读运行完成。测试没有调用真实 API，未生成仓库 coverage 产物；TEMP 目录内 236 项在运行后全部清理。Python 标准库独立故障注入还验证：模拟 lease 提交前进程崩溃可重新取得唯一探针；提交后第二 worker 被拒；租约过期先延后且旧 token 不能解除；向数据库注入非时间文本在发送前抛错；含 `api_key` 字样的配置组 ID 仅以哈希落库；相关临时数据库均已删除。独立双事件反例与 adapter 读取输出分别如上列出的具体时间与布尔结果。健康库本身无日志输出；本次未对整套应用日志做凭据扫描。

后续复审应在修复后重新冻结哈希，补充晚到事件原始/最终截止时间与来源一致性、一个逻辑 attempt 一个 HTTP POST、长 Retry-After 不在 HTTP 层睡眠的测试，再对 Q06/Q09 与热更新分别单独验收。
