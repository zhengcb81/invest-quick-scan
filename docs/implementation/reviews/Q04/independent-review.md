# Q04 独立只读审查

日期：2026-09-24  
结论：**needs revision**。快扫 CLI 主链路和基础顺位fallback可运行，但当前实现尚未遵守仓库采用的完整 model-policy v2 合约，且对限流/额度状态的处理不足以支撑配置所表达的行为。

## 审查范围与方法

只审查 StockQAbyLLM 中本轮 Q04 指定的六个文件：`src/config/llm_config.py`、`src/runners/llm_runner.py`、`src/utils/llm_integration.py`、`tests/unit/test_llm_config.py`、`tests/unit/test_llm_integration.py`、`tests/integration/test_quick_scan_cli.py`。StockQA 工作树还包含其他已修改文件；本报告不把它们或 Q01—Q03 的实现、审查结论归因给 Q04。

按要求在唯一 `%TEMP%\q04-review-<uuid>` 工作区重跑三个定向测试文件，设置 `PYTHONDONTWRITEBYTECODE=1`，关闭 pytest cache 与 coverage，并在结束后删除整个临时目录。结果为 **116 passed in 6.66s**；StockQA 当前 Git 状态与运行前记录一致，没有新增测试生成物。独立原始日志：[independent-validation-2026-09-24.log](independent-validation-2026-09-24.log)，SHA-256 `4F6EF16A9ED14CF83A3D4DEA174762275AB805A480A1D822B27D36DC6A845D0E`。已有目标日志：[validation-Q04-stockqa-targeted-final-r2-2026-09-24.log](../../contracts/validation-Q04-stockqa-targeted-final-r2-2026-09-24.log)，SHA-256 `ADD8A1AD723286E4237BD94F0F07A45AB145F85E43EC8AA0BF27F4B3F78E5FE3`。

`black --check --no-cache` 对六个文件通过；`git diff --check` 通过。公开 CLI 集成测试调用真实 `main_with_llm.main()`，经过题目加载、StockQA配置、provider、解析器、runner和JSON输出，仅把 `http_client_manager` 指向测试 session 并 mock `Session.post` 这个网络边界。没有真实联网或LLM调用；返回结构和搜索回执由实际解析路径处理。

## 阻断问题

### Q04-B1：写入端接受不符合完整 v2 schema 的活动策略

位置：[src/config/llm_config.py:263](C:/Users/郑曾波/Projects/StockQAbyLLM/src/config/llm_config.py:263)–326。

`_validate_quick_scan_policy` 只检查少数路由字段和 `max_attempts_per_dispatch_round`。但本项目的 `schemas/model-policy.schema.json` 还要求预算、成本策略、并行/打包约束、quota group 完整字段、fallback 各故障类别的动作，以及 comparison、resume 等字段。当前校验不会验证这些内容，也不会验证 `on_rate_limit`、`on_server_error`、`on_auth_error` 等取值。

复现：运行 `tests/unit/test_llm_config.py::TestQuickScanModelPolicy::test_save_policy_is_atomic_and_preserves_provider_credentials`。其 `_quick_scan_policy()` 缺少完整 v2 schema 的多个必填部分，仍能通过 `save_quick_scan_model_policy()` 并被认定为 `configured=true`。由此，一个声称具有预算/额度/恢复语义、实际却未提供这些字段的策略可以被保存并执行。应在保存和加载时对完整 v2 策略做同一套 schema 校验，并加上“缺少预算或fallback动作必须拒绝”的测试。

### Q04-B2：fallback 未执行已声明的限流、额度与认证故障动作

位置：[src/utils/llm_integration.py:714](C:/Users/郑曾波/Projects/StockQAbyLLM/src/utils/llm_integration.py:714)–721、[src/utils/llm_integration.py:757](C:/Users/郑曾波/Projects/StockQAbyLLM/src/utils/llm_integration.py:757)–778，以及 [src/runners/llm_runner.py:335](C:/Users/郑曾波/Projects/StockQAbyLLM/src/runners/llm_runner.py:335)–342。

当前把所有 429 合并成 `rate_limited_or_quota_rejected` 后立即尝试下一个模型；没有读取 `Retry-After`，也无法区分短期限流和账户额度耗尽。活动策略下每个 provider 被固定为 `max_retries=1`，所以 5xx 直接换顺位，不执行合约要求的有界重试。401/403 虽然会换到备用模型，但没有在本轮剩余题目中禁用失效 route；每道题都会重新先调用这个相同的失败 route。仓库的 v2 schema 明确约定普通429尊重 `Retry-After`、额度耗尽先冷却共享额度组、服务器错误有界重试、认证错误禁用route后再切换。

复现/覆盖缺口：`test_public_cli_falls_back_after_quota_rejection_and_records_ordered_attempts` 证明429后能发送到备用模型，但未检查冷却、`Retry-After` 或额度组；`test_server_error_can_fallback_but_dispatch_limit_is_hard` 只验证503立即切换；没有401/403跨多道题禁用route的测试。相关 transport 回执目前也不带 `Retry-After`；传输实现位于本次 Q04 指定范围之外，因此这是本次集成尚未满足合约的边界，不将该文件中的其他改动归因于 Q04。

## 非阻断问题

### Q04-N1：顶层 provider 字段表示首选route，但没有标明这一含义

位置：[src/runners/llm_runner.py:407](C:/Users/郑曾波/Projects/StockQAbyLLM/src/runners/llm_runner.py:407)–412、[src/utils/llm_integration.py:638](C:/Users/郑曾波/Projects/StockQAbyLLM/src/utils/llm_integration.py:638)–640。

`OrderedSearchProviderCascade.get_provider_name()` 和 `.model` 固定返回首个可用 provider/model。即使整份扫描都由 backup 回答，输出顶层 `provider.name` / `requested_model` 仍显示 primary。逐题 `execution_receipts` 的 provider/model/attempts 是准确的，所以并未丢掉真实执行信息；但顶层无标记字段容易被误认为实际使用模型。建议将顶层字段命名为首选策略，或输出实际使用模型集合/按题汇总，并增加该断言。

## 通过项

- 顺位按用户策略数组保留；同一逻辑题只在遇到可分类HTTP失败时尝试下一route，每道新题从首选route开始。
- 低分、unknown、insufficient-evidence都会停止fallback；400、无HTTP状态的超时/连接不确定结果不会被当作可恢复错误重复派发。
- 缺少联网搜索能力的公开CLI route会在发送请求前跳过；E2E测试确认只调用backup。
- 成功与失败的已发送尝试会聚合route/provider/model与policy version；顺序修改会改变策略fingerprint。
- 公开 CLI 测试走到了真实产品入口和实际JSON解析/输出路径，且唯一模拟网络边界清晰，适合作为离线集成测试；116项定向测试、格式与diff检查全部通过。

## 建议补充的验收用例

1. 用完整策略schema的有效fixture执行保存/加载；分别删除预算、quota group恢复字段、fallback动作时断言拒绝，且文件字节不变。
2. 429带 `Retry-After` 的时间形式与秒数形式；同组额度耗尽需跳过该组；普通限流不可伪装为五小时耗尽。
3. 两道以上题的同一次扫描中，primary返回401/403后不再派发primary；503在总attempt上限内执行配置的有界重试。
4. 全部fallback到backup时，顶层策略字段和每题实际model字段各自语义明确。

真实LLM E2E仍未执行；本次审查只证明离线调用路径与隔离边界，没有证明账户权限、联网搜索质量、真实模型配额或生产持久化行为。
