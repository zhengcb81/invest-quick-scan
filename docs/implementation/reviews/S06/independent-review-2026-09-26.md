# S06 独立审查：第二段路由集成（2026-09-26）

结论：**不放行。发现一个 P1 证据归属缺口。** 审查只读源码和归档；本文件是唯一仓内写入。未调用真实模型、网络或外仓写入。

## P1：一次搜索发生过，不等于候选引述的来源出自该次搜索

`scripts/routing.py:201-214` 的 `_fact` 只检查候选来源的结构、`entity_id` 和截止日。`scripts/routing.py:261-278` 检查执行回执的实体、prompt、时间后，把候选标记为 `searched_llm`。`schemas/quick_scan/route-decision.schema.json:612-696` 的执行回执有 `search_receipt_id` 和 `search_status=executed`，但没有实际完成搜索所返回的来源 URL 集，路由也没有逐条归属比较。因而模型候选中的任意格式正确的 URL 都能被当作搜索证据，选择行业/阶段模块并进入真实问卷。

隔离的最小反例：以 `tests/test_routing.py:62-112` 的临时发布包、半导体扩张公司及已执行回执为输入，将高置信半导体候选唯一来源 URL 改成 `https://not-in-search-receipt.invalid/hallucinated`。该 URL 不在回执里；回执实际上没有可证明它存在的来源列表。调用 `resolve_route_decision(..., candidate=..., execution_receipt=...)` 后，`semiconductors` 为 `selected` 且 `basis=searched_llm`；随后 `compose_from_route` 导出 28 题，包含该行业模块。过程输出：

```text
searched_llm_selected selected
fabricated_url https://not-in-search-receipt.invalid/hallucinated
receipt_has_source_urls False
composed_questions 28
TEMP_CLEANED True
```

修复的最小闭环是由受信任的搜索执行层提供或引用**该次已完成搜索事件实际返回的规范化 URL 集**，同时绑定现有 attempt/search 事件、prompt、实体和时间。对每条 `searched_llm` 候选来源验证 URL 属于这一集合；集合缺失或不匹配时，不得把对应行业、类型或阶段作为已证实分类派发，应保持 uncertain，并按现有规则只运行 common 与已独立核实的必需风险题。模型自身提供的 URL 列表不能充当执行层回执。此检查不要求路由模块联网访问 URL 内容；当前“URL 内容由上层验真”的职责边界可保留。

## 复现通过的范围

- 独立运行 `python -B -X utf8 docs/implementation/reviews/S06/run-first-segment-offline.py green`：16 tests，0 failures/errors/skipped，`TEMP_CLEANED True`。
- 独立运行同一 runner 的 `integration`：11 tests，0 failures/errors/skipped，`TEMP_CLEANED True`。覆盖低置信主轴仅派 common、困境加恢复六道题及预算 24/30、TTL 新导出与历史读取、旧 2.0 请求 hash、native CLI 请求→解析→决策→组合。runner 禁 socket、限制写入唯一 TEMP；未产生 API 调用。
- `second-segment-snapshot-2026-09-26.json` 列出的 **56 个旧 release 文件**逐一按现存字节重算 SHA-256，`drift=[]`；该 snapshot 还记录 `current_unchanged=true`。本审查没有切换当前发布包。
- 针对来源归属另做上面的真实 `resolve_route_decision` 与 `compose_from_route` 反例，使用唯一临时根，输出清理成功。此反例没有被现有 27 个聚焦测试覆盖。

审查所见源码 SHA-256：`scripts/routing.py` `9286b0bad8c931ea4b73a72aaaa3517422dbea5fc481257f38b85afb28305b7e`；`scripts/question_sets.py` `580b44d5c5408fb3bdabfd48c8306ccb5f520b93d7ba9bcb0404fceea994b3f5`；`tests/test_routing.py` `75592f97c38a48124823f0ef39b873a69315663311b9c689ef63c4586628c02b`；`tests/test_question_sets.py` `d85e67d633f8c9a98cb972c4ceb5c676fcb0be60295d64f56e96a74f2de0924a`；`schemas/quick_scan/route-decision.schema.json` `008185fe4550a204099eefc34a155d9f69c0375fa1a77f2632c6747dc12ec036`。

修复后需新增固定反例：执行事件发生但候选 URL 不在可信来源集、可信来源集为空、多个候选仅一条不匹配、URL 规范化差异、回执跨 attempt/prompt/entity 复用；证明这些情况不会选择该候选或发出额外模块题。原有历史包和旧 manifest 仍须可读，旧 release 字节须保持不变。
