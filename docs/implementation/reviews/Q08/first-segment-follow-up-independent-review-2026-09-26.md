# Q08 第一段修复后的独立复审

**结论：上一轮三个发现均在本段范围内关闭；Q08 整体仍为 partial。** 没有在本次复审范围内发现新的 P0/P1/P2。三个修复不替代 Q06 的持久待办/成功题检查点、Q09 的费用预算账本、跨进程容量租约或 LLM-10 立即生效热更新验收。

## 修复核对

| 原发现 | 独立证据 | 结论 |
|---|---|---|
| P1：共享 HTTP Session 暗中重试付费 POST | [`src/utils/http_client.py:39`](C:/Users/郑曾波/Projects/StockQAbyLLM/src/utils/http_client.py:39) 的 Retry 不再允许 POST；实际 adapter `is_retry('POST',429,has_retry_after=True)=False`、`is_retry('POST',500)=False`，GET 500 仍可重试。新单元测试用真实 Requests Session、拦截 urllib3 `_make_request` 返回带 `Retry-After: 18000` 的 429，且让 `Retry.sleep` 一旦调用即失败；只调用一次底层 send 并立即保留 429。`LLMClient` 测试确认公开 attempt 仍有同一个 429 和 18,000 秒提示。 | **关闭**，限 HTTP 状态重试；连接建立前的安全重试不在本次接受/计费争议范围。 |
| P1：晚到短 429 公布过早 `next_probe_at` | [`quick_scan_provider_health.py:324`](C:/Users/郑曾波/Projects/StockQAbyLLM/src/utils/quick_scan_provider_health.py:324) 在 `BEGIN IMMEDIATE` 内读旧截止时间，写入并返回胜出的最终截止时间与对应来源。独立反例：先 `Retry-After=3600`，1 秒后无头 60 秒，返回值和新实例 `admit()` 均为原 3,600 秒终点，来源保持 `retry_after`。同截止时间的已知提示优先；后来更长的已知提示覆盖旧时间。 | **关闭**。 |
| P2：晚到未知 quota 抹去已知恢复点 | [`quick_scan_provider_health.py:271`](C:/Users/郑曾波/Projects/StockQAbyLLM/src/utils/quick_scan_provider_health.py:271) 同样在事务内选择胜出的组时间与来源。独立反例：先已知 3,600 秒、1 秒后无头 60 秒，`next_probe_at` 不退化，数据库 `reset_at` 仍保留原时刻、`reset_at_source=retry_after`；同截止时间已知提示优先。 | **关闭**。 |

## 验证边界

在 StockQA 冻结源码上以唯一 TEMP 目录运行 `tests/unit/test_http_client.py`、`test_quick_scan_provider_health.py`、`test_llm_client.py`、`test_llm_integration.py`、`tests/integration/test_quick_scan_cli.py`：**194 passed in 8.25s**。设置 `PYTHONDONTWRITEBYTECODE=1`、禁用自动第三方 pytest 插件、禁用 cacheprovider 与原配置 coverage addopts，移除本进程 API key/live 开关，全部只用模拟响应，无网络 API 请求。TEMP 目录内 240 项测试产物已清理。另以标准库新建临时 SQLite 数据库，重复旧反例并加同截止时间/逆序更长提示；四项断言全过且目录清理。上一轮跨进程单探针、崩溃前后租约、坏时间失败关闭与数据库无明文凭据的测试仍在这五个文件的执行范围。未独立重跑全仓 617 项；本复审只支持上述修复范围。

冻结的 SHA-256：`src/utils/http_client.py` `15BF417FBDABB9E883A54DB814BA1BDE6A1512A677BC4FF2BD8CC94868A77323`；`src/utils/quick_scan_provider_health.py` `7727FAE30C07D08ACCB3412A2245966E293B58F3F35F071F85F43FED2A95ECF9`；`tests/unit/test_http_client.py` `F2F22560691BE1DDAE72CB982177AC1C988863CA405B7AF014A334FF804291FB`；`tests/unit/test_quick_scan_provider_health.py` `F6BC1E036EF9E4945A731C33FEBFA3694AFCEC3DB453921A04CF4670B8605268`；`tests/unit/test_llm_client.py` `9EA4CA1EC77494DAC2FAB752CC2BE1A452C8DBBB94D3C06F77697D2EA5D141AC`；`tests/integration/test_quick_scan_cli.py` `790684938FE0E4036D924B3CB813D4DA977BEBDF35DE51C92FD2638B19B66444`。关联调用方 `src/providers/llm_client.py` 保持 `9977B097B1EB8870C0DA7FD8F61E6D7318A63C050FF6E506C1D8B9724DECBD3B`。

剩余 Q08 完成门应继续保持开放：全部组冷却时需持久 `waiting_for_provider`/`retry_wait` 与接续资格；重启和手动点击不得重开已耗尽的尝试轮；成功题不得重问；所有实际请求（含搜索、失败、fallback）需通过共同预算预留与结算；立即切换策略只能影响未派发任务。
