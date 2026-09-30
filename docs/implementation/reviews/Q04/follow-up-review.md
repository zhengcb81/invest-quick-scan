# Q04 修订版独立复审（r3）

日期：2026-09-24  
审查快照：StockQAbyLLM `HEAD 3c685dda28f67a00bd653ad257a121d3b8edebb8`，下列工作树文件SHA均与委托复审时提供的r3哈希一致。  
结论：**needs revision，当前不能将Q04标为verified**。B2列出的同一运行内fallback行为已得到代码和公开CLI测试支持；B1虽已补齐大部分必填字段的关闭式校验，但仍与完整v2 schema存在可复现的接受差异。此外，新schema文件被StockQA `.gitignore` 忽略，未进入Git状态/可交付变更。

## 范围与隔离验证

本轮只读StockQA，没有编辑其中任何文件。复核Q04路由配置、schema、runner、LLM transport receipt及对应测试；其他Q01—Q03代码仅作为公开CLI的现有依赖读取，不把其实现归因于Q04。

在唯一短TEMP根 `q04f-<uuid>` 下运行三个定向文件；该根同时作为CWD、`TEMP`、`TMP`、`TMPDIR`，pytest `--basetemp` 位于该根内。命令关闭pyc、pytest cache和coverage：`PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -q --no-cov -p no:cacheprovider --rootdir <StockQAbyLLM> --basetemp <unique-temp>\p tests/unit/test_llm_config.py tests/unit/test_llm_integration.py tests/integration/test_quick_scan_cli.py`。结果 **131 passed in 3.86s**。测试生成的日志、benchmark和pytest临时文件都位于该根；清理后该根不存在，StockQA Git状态没有新增测试生成物。日志：[follow-up-validation-2026-09-24.log](follow-up-validation-2026-09-24.log)，SHA-256 `2D57F8DC5ED65A1A68CDE074F2C97E0BADA8B4DD6C37C4763158D5F53E78CD30`。

Black `--check --no-cache` 对8个相关Python文件通过；定向 `git diff --check` 通过。公开CLI集成测试执行实际 `main_with_llm.main()`、配置读取、provider/response parser、runner和结果序列化；HTTP边界由mock session隔离，没有真实联网或真实模型调用。

## B1：关闭式校验已有进展，完整schema一致性仍未通过

StockQA新增schema与本仓的公开v2 schema在JSON语义上相等（独立比较结果 `schema_semantically_equal_to_workspace_contract=True`）。缺少顶层预算、dispatch字段、quota字段、fallback动作、comparison/resume字段及未知字段现在会被拒绝；新增测试还验证读取不完整策略失败关闭，以及保存失败时原配置字节不变。这部分修订有效。

但手写校验器 [llm_config.py:265](C:/Users/郑曾波/Projects/StockQAbyLLM/src/config/llm_config.py:265) 仍未覆盖schema所有约束，B1因此没有关闭：

- [llm_config.py:397](C:/Users/郑曾波/Projects/StockQAbyLLM/src/config/llm_config.py:397) 只检查 `pricing_ref` 是字符串或null；未执行schema要求的条件约束：`pricing_basis=verified_rate_card` 时必须是非空字符串（schema [quick_scan_model_policy.schema.json:126](C:/Users/郑曾波/Projects/StockQAbyLLM/src/config/quick_scan_model_policy.schema.json:126)–138）。当前测试工厂 `_quick_scan_policy()` 本身设置为 `verified_rate_card` 加 `pricing_ref: null`，因此测试所用“完整”策略实际不符合v2 schema。
- [llm_config.py:326](C:/Users/郑曾波/Projects/StockQAbyLLM/src/config/llm_config.py:326)、452–459只检查字符串非空；没有验证 `policy_id`、quota group ID、route ID、provider引用、model及quota group引用的`maxLength: 200`（schema [quick_scan_model_policy.schema.json:8](C:/Users/郑曾波/Projects/StockQAbyLLM/src/config/quick_scan_model_policy.schema.json:8)–11、149–152、188–209）。
- [llm_config.py:518](C:/Users/郑曾波/Projects/StockQAbyLLM/src/config/llm_config.py:518)–521没有执行comparison条件约束；当`comparison.enabled=true`时，schema要求`max_cost > 0`、`max_requests >= 1`（schema [quick_scan_model_policy.schema.json:304](C:/Users/郑曾波/Projects/StockQAbyLLM/src/config/quick_scan_model_policy.schema.json:304)–315）。

独立schema探针在同一fixture上确认上述反例：手写校验器三者均接受，而StockQA新schema分别报1、1、2项错误。详情及SHA：[follow-up-schema-audit-2026-09-24.log](follow-up-schema-audit-2026-09-24.log)，SHA-256 `11E2D706748F7FAAF56F61D8EDFCD83D6F0131E2FBA97D2095946EA2C02B25A8`。修订可通过schema驱动校验，或补齐手写约束并加上“手写validator与schema一致”的差异测试；还应把测试fixture改成schema有效策略。

### 交付状态：新增schema目前被忽略

`git check-ignore -v src/config/quick_scan_model_policy.schema.json` 返回 `.gitignore:89:*.json`；该schema虽在磁盘上并有下列SHA，但不出现在 `git status`，也不会随普通Git差异交付。它与本仓contract相同，却不是当前StockQA版本控制中的契约文件。需要把精确路径纳入跟踪后重新生成最终状态/收据；本次审查没有修改`.gitignore`或StockQA任何文件。

## B2：同一运行内的有限fallback验收通过

- 429按白名单provider error code区分`quota_exhausted`与普通`rate_limited`；额度耗尽会让同quota group的后续route在本次run跳过。普通限流的秒数和HTTP-date `Retry-After`会解析成秒并在切换前等待。raw header不进入receipt；只写规范化的`retry_after_seconds`。[llm_client.py:97](C:/Users/郑曾波/Projects/StockQAbyLLM/src/providers/llm_client.py:97)–141、[llm_integration.py:739](C:/Users/郑曾波/Projects/StockQAbyLLM/src/utils/llm_integration.py:739)–752。
- 401/403禁用route，404也禁用该route；cascade实例由整次单公司runner复用，因此后续问题会跳过失败route。公开CLI用跨两题401案例验证了该行为。没有针对403的独立CLI案例，但路由分类对401和403使用同一分支。
- 5xx在总attempt预算允许时最多重试；重试前计算后续合格route数量并保留fallback名额。公开CLI案例在上限3时实际记录primary两次、backup一次。400和timeout等歧义不触发fallback。
- transport receipt只保存白名单错误类别码、状态码、规范化Retry-After秒数和必要的attempt元数据，不保存错误正文或原始Retry-After。测试覆盖错误正文、HTTP-date原文不泄露。
- 顶层`provider`对象作为configured preference，逐题`execution_receipts[question_id].provider/requested_model`表示实际回答route；fallback公开CLI案例断言顶层primary而逐题receipt为backup。因此两者按JSON路径可区分，runner注释也标明了此语义。字段名仍较泛，但此处不构成阻断。

一个运行时边界仍应登记在LLM-06：当前对普通429直接`time.sleep(retry_after_seconds)`，没有等待上限或超时/恢复队列。HTTP-date测试用2099年的header并mock sleep，因此证明了解析与回执行为，不证明生产中这个长等待可安全恢复；实际runner可能长时间阻塞。v2要求的全路由不可用后持久化`retry_wait`/有界恢复仍未实现，不能以本轮fallback测试声称完成。

## 仍开放的系统边界

- **PAR-03**：未实施首选route容量槽满时等待；`max_in_flight`、全局容量字段目前只校验/保存，没有跨worker原子槽或capacity-wait调度。
- **PAR-08**：本轮没有StockWiki设置UI、配置导入API或UI/CLI/runner读取同一生效版本的跨仓闭环；StockQA Python保存方法不代表该设置入口已交付。
- **LLM-06**：能力缺失预检、坏请求停止和受限模型fallback已覆盖；全路由不可用后的持久化`retry_wait`、恢复事件/半开探针仍未实现。普通Retry-After的任意长等待也没有时间上限。
- **LLM-10**：当前只证明run开始时取快照、改动下轮生效；立即更新只作用于边界之后尚未派发题目、保留在途旧policy并避免成功题重跑，均未实现/验证。
- 当前quota cooldown与auth禁用集合只存在于cascade内存，未跨进程、跨run或重启持久化；没有真实provider、实时额度或正式数据验证。

因此，B2限定的顺位失败路由可标为本轮已验证；B1完整schema一致性及schema版本控制未关闭，Q04整体暂不能标为verified。PAR-03、PAR-08、LLM-06剩余部分和LLM-10应继续保持各自开放状态。

## 审查快照文件SHA-256

| 文件 | SHA-256 |
|---|---|
| `src/config/llm_config.py` | `058299379164D483907D3DB9C881B17646D4791DCCFD61537323E77AC313F4A7` |
| `src/runners/llm_runner.py` | `579CDE5A1FB21604E0A2BDCA5667C880E45E78864602E2BD664F23A2DBEDD2A4` |
| `src/utils/llm_integration.py` | `144212285E8E7BDDFAEE30907CE2D493471677DADF43591246C6701E31C2DC7C` |
| `src/providers/llm_client.py` | `207AE40383DA230AD544116DFB13CABC1963FADA117EE9C0670F601DFEAF099F` |
| `src/config/quick_scan_model_policy.schema.json` (ignored, not tracked) | `E6188237EF0FD07C4EE63C1EAB25AB250426BA7C12E6D0BC71A9D4AB1D7D0455` |
| `tests/unit/test_llm_config.py` | `9CD933701CE0D11538F366419DAA8F0C6EF10E872ED4CCC7000E8CFF28532932` |
| `tests/unit/test_llm_integration.py` | `D03B9DADB0A52F7F1D434F201F19AE43DE9B4DEF35AA61483DF81D5E25290860` |
| `tests/integration/test_quick_scan_cli.py` | `2548F0D07F0333C429008E88F4F3D4DB6DC1F7350FAA09F5250D3290BF0C5117` |
| 独立定向测试日志 | `2D57F8DC5ED65A1A68CDE074F2C97E0BADA8B4DD6C37C4763158D5F53E78CD30` |
| schema parity探针日志 | `11E2D706748F7FAAF56F61D8EDFCD83D6F0131E2FBA97D2095946EA2C02B25A8` |
