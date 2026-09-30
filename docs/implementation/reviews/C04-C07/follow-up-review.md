# C04/C06/C07 整改后独立复审

- 审查者：`/root/g0_independent_review`
- 日期：2026-09-24
- 范围：仅复核 `independent-review.md` 中 C04-IR-01/02、C06-IR-01/02、C07-IR-01/02 及更新后的本地契约证据；未执行真实 provider、数据库或跨仓 E2E。
- 最终结论：**C04、C06、C07 均可在本地离线契约范围从 `implementation_complete` 晋级 `verified`。** 初审六项 finding 已关闭。生产 worker、StockWiki 持久化、真实进程和 paid search 仍不在本结论范围。

## 绑定快照

| 对象 | SHA-256 |
|---|---|
| `receipt-C04.json` | `02564D1FF46288D79BA07119CF0D57E53E867F555B6635E2F9E629670AD94B69` |
| `receipt-C06.json` | `56D60426E79CFE82D03F0B63F2833F9D4061E1B497AE69B9CEFB326B6052064B` |
| `receipt-C07.json` | `816218738681E8738FE2DB614F41259113D6CA97106790AF5155C80CB68F9078` |
| `docs/implementation/tasks.json` | `55DBB8D63A27A8D8A8ACD37C46322CD0FBDCE2D5113CEEC3E416E16AA401AC0F` |
| `docs/implementation/acceptance-cases.json` | `38642BFDBEA9C3BEBB7272D13EED6D3C4C85BEBC99D5A9C7B372CC7400E557FA` |
| `scripts/contract_validation.py` | `C7F22E27926A8404558E63B6ABB541448C4B957639E22FD99C06071F8C8EF8AE` |
| targeted 原始日志 | `138C34445D2098C5E4561F199F43E3372FE1CB2B007D87503E4AECEDBC591361` |
| full 原始日志 | `CA1C95B5F75BE5422459B4C236071F3D321DDF33502511616CCE7F27EA514833` |
| red 原始日志 | `724C73544E44EE32F47A60946709E427F8272B797D5A58536B8B703AD9B0A5A0` |

三份更新回执中列出的每个文件均存在，逐文件 SHA-256 全部匹配。三份回执的 `plan_sha256` 与当前 `tasks.json` 一致，`case_catalog_sha256` 与当前 `acceptance-cases.json` 一致。targeted 日志记录 51 passed，full 日志记录 222 passed，日志字节 hash 均与回执一致。

## 初审 finding 复核

### C04-IR-01：关闭

- `contract_validation.validate_work_item()` 现在拒绝重复 `attempt_id`，并要求 uncertain 状态的 `uncertain_attempt_id` 在持久化 attempts 中恰好出现一次。
- `work_contract.transition_work_item()` 先验证整个 WorkItem，再从其中提取 attempt 集与 uncertain ID；调用方提供冲突 ID 时返回 false。
- 独立反例结果：不存在的 ID 被拒绝；重复 ID 被拒绝；伪造 transition ID 返回 false；绑定同一真实 attempt 的 `response_available` 转换返回 true。
- 当前相关 hash：`scripts/work_contract.py` `1B59F282029D351911C99FED5E956DA4E91C359666074CCAE9AA940348AE06A4`；`tests/test_freshness_and_jobs_contract.py` `C00A03D29D041C071183EA65E77D1CB71357AE6B6D751EB025F6E7E0E2064A1F`。

### C04-IR-02：关闭

更新回执已绑定当前文档、schema、helper、公共 semantic validator、新测试以及整改 targeted/full/red 日志。当前快照闭包不再依赖未列入回执的 validator。

### C06-IR-01：关闭

- `contract_validation.validate_exchange_package()` 在 schema/extension 检查后调用 `exchange_contract.validate_package_integrity()`。
- validator 逐项核对 embedded observation ID、重算 payload hash 和 item ID，并从移除 package ID/hash 后的包体重算 package hash 与 package ID。
- 独立反例结果：分别篡改 observation、payload hash、item ID、package body、package ID 均被拒绝；原始包通过。
- 当前相关 hash：`scripts/exchange_contract.py` `BE08F84055DBB72AD5205EA31BD9AC17106B523F4CC5AE17A315171A570592F7`；`tests/test_exchange_and_query_contract.py` `EAC9D564A07940CED31DD608B4AA2BA9BAD3A62AD343E1D9FDF59A2A23278E2F`。

### C06-IR-02：关闭

更新回执已重新绑定当前 exchange/query schema、helper、公共 validator、测试、文档及整改日志；旧回执漂移已消除。

### C07-IR-01：关闭

- full readiness 响应验证现将 `result.components`、setup/doctor 状态、live/paid receipt ID 和 gate evidence 交给 `assess_readiness()` 重新推导，并要求推导结果仍为 `full_release_verified`。
- 独立反例结果：原始完整证据通过；篡改 required component `actual_loaded_sha256` 被拒绝；重复组件被拒绝；缺少组件在 schema 阶段被拒绝。
- 当前相关 hash：`scripts/deployment_contract.py` `5EFE2F140025212BAB5FF484FFF7ABB747EA78B0C0F4DB385FC845FE0C664897`；`tests/test_g0_regressions.py` `69291A1EFEC99D14A3381AA20D5E454F10EF8E310F1063505F06C2B2721A3B64`。

### C07-IR-02：关闭

更新回执已绑定当前 deployment schema、helper、测试、G0 regression、文档及整改日志。历史日志仍保留为历史证据，当前候选由新增日志与当前 hashes 绑定。

## 独立测试

测试均设置 `PYTHONDONTWRITEBYTECODE=1`、禁用 pytest cache，并将 `TEMP`/`TMP` 指向 reviewer 创建的唯一目录。

- 定向命令：`python -X utf8 -m pytest -q -p no:cacheprovider tests/test_freshness_and_jobs_contract.py tests/test_exchange_and_query_contract.py tests/test_deployment_contract.py tests/test_g0_regressions.py`
  - 结果：`51 passed, 16 subtests passed`。
- 全量命令：`python -X utf8 -m pytest -q -p no:cacheprovider tests`
  - 短唯一 TEMP `C:\Users\郑曾波\AppData\Local\Temp\ir65cf8e` 下结果：`222 passed, 139 subtests passed`；结束后目录内条目数为 0。

首次全量复跑使用了额外加长的唯一 TEMP 名，Windows 深层测试路径触发 4 个 `os.replace` 的 `FileNotFoundError`，其余 218 项通过。该目录比正常系统 TEMP 多出较长前缀；改用短唯一 TEMP 后相同全量套件全部通过且清理为空，因此记录为测试环境路径长度干扰，不作为本轮实现 finding。

## 分任务判定

| 任务 | 绑定 case | 判定 |
|---|---|---|
| C04 | TIME-01..08、JOB-01、JOB-08；重点重放 uncertain attempt 持久化与转换 | **verified（本地离线契约）** |
| C06 | C06-CONTRACT-01..03；重点重放全部内容寻址层级 | **verified（本地离线契约）** |
| C07 | C07-CONTRACT-01..03；重点重放 full readiness 组件证据闭包 | **verified（本地离线契约）** |

本报告不把离线 reference helper 等同于生产实现，也不改变真实 StockQA/StockWiki、运行调度、数据库事务、进程控制和 live E2E 的未执行状态。
