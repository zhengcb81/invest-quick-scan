# S06 来源绑定独立复审（2026-09-26）

结论：**暂不放行。** 初审的“模型候选引用未出现在已完成搜索中的 URL 仍可派发”已修复；复审发现并复现了可信事实优先级和旧 v2 归档兼容/执行边界问题。复审仅写本报告，不修改产品源码、其他仓库或正式发布包；没有联网或付费 API 调用。

## 已关闭的原 P1：模型来源须归属同一次完成的搜索

`scripts/routing.py:234-251` 从受信任执行回执中只选 `search_receipt_id` 对应且 `status=completed/action_type=search` 的调用；`scripts/routing.py:295-306` 对候选逐条比较来源 URL，不匹配或空集不会进入 `searched_llm` 事实；`scripts/routing.py:530-533` 在旧快照重签后再次比较。回执 schema 现要求 `web_search_calls`。新增 `tests/test_routing.py:152-192` 覆盖伪 URL、空来源、错误事件、失败事件中有同 URL、缺回执字段、快照篡改。该层修复通过复审；执行回执本身仍须由上游受信任的 provider adapter 产生。

## P1 已由实施者补丁修复并加固定反例：伪候选不能压掉独立核实的困境事实

复审开始时，`resolve_route_decision` 先把 URL 未绑定的模型候选 module ID 加入 `unbound_sources`，随后虽以可信 `verified_facts` 覆盖 `facts`，决策循环仍先处理 `unbound_sources`。内存反例中，可信 `covenant_breach` 的 `distressed` 原为 `selected`，必需题是 `DISTRESSED_01/02` 加 `RECOVERY_01-04`；加入同 ID、伪 URL 的模型候选后，困境变为 `uncertain/unavailable`，六道题全部消失，只派 common。这是伪模型输出取消已核实风险覆盖的漏洞。

实施者随后在 `scripts/routing.py:316` 让可信事实覆盖时清除同 ID 的 unbound 标记，增加 `tests/test_routing.py:194-208` 固定反例。独立运行隔离 `green` 套件在修复后的测试计数为 **17 tests，0 failures/errors/skipped，TEMP_CLEANED True**；该反例已通过。此项本地修复可接受，但 S06 仍因下列旧版边界不放行。

## P1：新回执字段使合法旧 router 2.0 `searched_llm` 快照失去历史读取能力

`schemas/quick_scan/route-decision.schema.json:700-706` 无条件把 `web_search_calls` 设为所有 RouteV2 回执的必需字段。第一段真实归档 `pkg_5c7facbfd9b772130e3fb5150d2c4d390083e72570b28c82cc4ab67151fd881f` 的 router 为 2.0.0、policy schema 为 1.0.0；当时合法的搜索回执没有此字段，旧请求 prompt SHA 是 `6b35db51280523a71a860d82152054f95ce565cc534da0ca85cd1f05ba056740`。`module_contract.validate_route_decision` 使用当前全局 schema，故旧快照先遭 `ValidationError`。即使只在内存把 `web_search_calls` 从 schema required 移除，`routing.validate_route_snapshot` 仍在 `scripts/routing.py:530-533` 对旧 2.0 回执执行新的 URL 归属检查，拒绝 `ValueError: searched classification source is not in completed search receipt`。

复现方法：从上述真实旧 package 用 `resolve_route_decision` 生成同实体、同 cutoff 的可信事实快照；把三条客观 selected 决策的 basis 改成 `searched_llm`，加入第一段格式的旧执行回执（准确旧 prompt SHA、实体、截止日、已执行事件 ID/时间，**无** `web_search_calls`），按 `mc.digest` 重新计算 route ID。这是旧实现可生成的结构；当前 `mc.validate_route_decision(old, old_release, package=old_package)` 报 `ValidationError`。仅在内存暂时放松 required 后，`routing.validate_route_snapshot(old)` 报上述 URL 归属错误。探针没有存文件或修改全局 schema 源码。

应按**归档 release/router policy**而非当前可变默认规则分支：旧 2.0 快照只供历史读取与解释，保留旧回执契约；新 2.1 快照与新执行继续要求 completed-call URL 逐条归属。新增回归须证明旧完整 manifest/快照可读，旧包缺失或被改仍拒绝。

## P1：旧 router 2.0 包当前仍可生成新的执行问卷

以同一真实旧 package 和可信事实生成 v2 决策，调用 `question_sets.compose_from_route(route, unique_temp/new-scan, now_utc=..., expected_route_decision_id=...)`，当前源码实际返回 **28**，写出 `questions.json`，`TEMP_CLEANED True`。这与“旧 2.0 仅历史读取，不可重新派发”的验收边界相反。修复应让 `validate_route_for_execution` 或 `compose` 的新导出路径拒绝旧 2.0 路由，不能让历史读取入口因此失效。固定测试需分别断言 `validate_route_snapshot(old)` 成功和 `compose_from_route(old, ...)` 写入前拒绝。

## 其他复核记录

- 隔离 runner 的 `integration`：11 tests，0 failures/errors/skipped，`TEMP_CLEANED True`。它覆盖原生 CLI 请求→解析→组合、低置信收窄、困境必需题预算、到期后新导出与历史读取、旧 prompt 重现。
- `second-segment-snapshot-2026-09-26.json` 中 56 个发布前 release 文件逐一重算 SHA，漂移数 0；`questions/releases/current.json` 仍指向 S05 `pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f`。
- 本报告对应的源码 SHA-256：`scripts/routing.py` `62a660579704a793d55b0c10c92e45fc5bfac8324092ecadc13287484ed5a3f4`；`tests/test_routing.py` `928b41be3e0800ca8db7500272df1a1e8b0f935c34ec055fdf53abc0e3306cf9`；`schemas/quick_scan/route-decision.schema.json` `cd8e0ff29bee70b77b5bf050b7808d88486a57cfab64d6f77861b8c585f1ccd6`；`scripts/question_sets.py` `580b44d5c5408fb3bdabfd48c8306ccb5f520b93d7ba9bcb0404fceea994b3f5`。
