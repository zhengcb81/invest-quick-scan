# Q08 第一段：持久提供商冷却与单探针（实施者交接）

状态：**partial / 待独立审查**。本段只实现已配置有序快扫路由的持久配额组冷却、普通429逐路由冷却和跨进程单个半开探针。`Q06`逻辑待办/租约尚未实现，所以运行级持久`retry_wait`、逐题成功检查点、预算账本和跨轮尝试次数仍未闭环；公开`dispatch_outcome`仍如实标`retry_wait_recommended`、`scheduled=false`，但增加可见的`retry_eligible_at`。

## 实现与安全边界

- StockQA配置文件旁独立`quick_scan_health.sqlite`，仅已配置策略创建；默认旧单提供商CLI不新建状态库。`.gitignore`只忽略根目录该库及SQLite伴生文件。
- `BEGIN IMMEDIATE`使多个worker对同一组到期探针互斥；重启保留冷却，超时/崩溃探针不立即重发，而再延后保守探针期；迟到旧令牌不能清新冷却。
- 确认额度拒绝按组冷却，同组其他模型跳过；备用组成功不清首选组。组已知`Retry-After`记录来源，未知时只记录本地下一探测点，不伪造五小时重置时刻。普通429按单路由；无头429本地60秒冷却不标作厂商`Retry-After`。
- SQLite只保存哈希化的组/路由键、故障时刻与有限探针状态，不存密钥、URL、公司信息、请求体；完整schema/版本、坏时间值与未知表均在发送前失败关闭。
- 成功回答仍按原级联停止；模型A的半开成功才清A冷却，模型B回答不恢复A。

## 精确源码快照（SHA-256）

| StockQA路径 | SHA-256 |
|---|---|
| `.gitignore` | `7E14F2B57B54BEF0C7C69E67B043D1D0F8EAF1DB741FE12A4B6958B715EE4D82` |
| `src/config/llm_config.py` | `A6CF872A115BE1A418CCAA6457DDAE45ABC1FBFEA17A8E1E6AA7E08778D4F4A3` |
| `src/utils/llm_integration.py` | `3E7BAC54444ADF59B7CF4043AB5C150E1AF2BDFC3730B289C42751A2F88C01B9` |
| `src/utils/quick_scan_provider_health.py` | `236DEA178C0F8F1A8D65B8D91EB691CE35125C63EBEB6CE5D2AFEA90E338C59A` |
| `src/runners/llm_runner.py` | `1601273FFC0EB88447DB228471D8CA2CA856D265678F0814F9BB3E3DA9C3E8AD` |
| `tests/unit/test_llm_integration.py` | `1E15243F1CDDA27B90E0D11EAD172C60A731759E74A0BE5332DFB3FF8C81993B` |
| `tests/unit/test_quick_scan_provider_health.py` | `3897DDAA8F9C7E85EF78A54AC5F9B02B792A618E7E2DF26424744B6053705539` |
| `tests/integration/test_quick_scan_cli.py` | `790684938FE0E4036D924B3CB813D4DA977BEBDF35DE51C92FD2638B19B66444` |

## 验证与后续

全量离线unit+integration **612 passed**，唯一TEMP已清理；日志见[`validation-Q08-first-segment-2026-09-26.log`](../../contracts/validation-Q08-first-segment-2026-09-26.log)。新增反例覆盖跨进程争抢一探针、半开崩溃、过期旧令牌、错误恢复时间/伪v1/额外表、分组隔离、无头429本地冷却与公开CLI重启。Ruff通过；两份新Python文件Black检查通过。既有共享文件此前就有Black格式差异，未格式化整仓。

独立审查应重点核查：`src/utils/http_client.py`目前Requests适配器仍可隐式重试POST 429/5xx，当前`LLMClient.send_search_request`取全局Session；这层网络重试没有进入公开attempt预算，**单一重试拥有者尚未完成**，需后续获报备扩展文件并修复。`Q06`任务/租约、`Q09`预算预留和费用不明对账、运行级`retry_wait`调度/成功题不重问均待后续卡实施。此回执不能标Q08整体verified，也不替代真实模型搜索验收。
