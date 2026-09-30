# S06 历史兼容与搜索来源绑定终审（2026-09-26）

结论：**本仓 S06 离线路由/组合/历史读取范围通过独立复审。** 前两轮审查的 P1 均已关闭；本结论不代表真实 provider 接入、持久待办、StockWiki/UI 或 live E2E 已完成。复审只读产品源码，仅写此报告；未联网或调用付费 API。

## 已关闭的反例

1. **模型伪来源。** `scripts/routing.py:234-251,295-306` 仅取受信任回执 `search_receipt_id` 对应的完成搜索事件 URL，并逐条绑定模型候选；不匹配/空集降为 `uncertain`，实际模块收窄为 common 加独立核实的必需风险题。`validate_route_snapshot` 对新路由重验，重签快照后删除可信 URL 仍拒绝。`tests/test_routing.py:152-192` 的 URL、空集、错误事件、失败事件和快照篡改反例通过。
2. **伪候选压掉可信困境。** `scripts/routing.py:310-316` 让 `verified_facts` 覆盖同 ID 未绑定候选，并清除对应的 `unbound_sources`；`tests/test_routing.py:194-208` 固定 `distressed` 与 `recovery` 的六道必需题仍被派发。
3. **旧 router 2.0 搜索快照。** `tests/fixtures/s06_router_20_search_route.json` 绑定真实第一段归档包 `pkg_5c7facbfd9b772130e3fb5150d2c4d390083e72570b28c82cc4ab67151fd881f`、旧 prompt SHA、旧式无 `web_search_calls` 的回执及 route 内容 hash。`schemas/quick_scan/route-decision.schema.json:1017-1036` 仅对非 2.0 版本要求该新字段；`validate_route_snapshot` 对旧包保留 package/hash/身份/prompt/时间校验，同时只对非 2.0 快照要求新增 URL 归属。独立运行的旧快照读取成功。原始字节改动、重签后 prompt/entity 错误、复制到唯一 TEMP 后篡改旧 package 均被拒绝。
4. **旧包只读。** `resolve_route_decision` 对旧 2.0 package 拒绝产生新决策，`validate_route_for_execution` 对旧 2.0 决策拒绝新执行，`compose_from_route` 在写目录前拒绝新导出。`validate_recorded_route_execution` 单独校验已存 manifest 中的原决策 ID、原校验时刻和 TTL；`question_sets._validate_published_manifest` 用此只读路径，因此旧 2.0 的 28 题历史 manifest 可验证，伪造 expected ID 被拒绝。`tests/test_routing.py:428-475` 两个固定测试通过。
5. **未来版本与新版本隔离。** 在唯一 TEMP 发布 router **2.2.0** 测试包：真实 `searched_llm` 候选可选 common/operating/scaling/semiconductors；删除 `web_search_calls` 报 `ValidationError`；替换半导体来源为未返回 URL 后仅 common 可派发。说明历史例外没有因版本泛化而放松后续版本。TEMP 清理成功。

## 独立验证记录

- `python -B -X utf8 docs/implementation/reviews/S06/run-first-segment-offline.py green`：**20 tests passed，0 failures/errors/skipped，TEMP_CLEANED True**。runner 禁 socket、限制写入唯一 TEMP。
- `python -B -X utf8 -m unittest discover -s tests -p test_routing.py -k ArchivedRouterCompatibilityTests -v`：2/2；伪 URL 固定例 1/1；可信困境覆盖固定例 1/1。另运行上述旧包篡改/2.2 临时包纯内存与 TEMP 反例。
- `second-segment-snapshot-2026-09-26.json` 所列 **56 个旧 release 文件**逐一重算 SHA-256：漂移 0；`questions/releases/current.json` 仍为 S05 `pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f`。
- 相关文件 `git diff --check` 无 whitespace 错误；Git 对 `question_sets.py` 提示未来可能进行 LF→CRLF 转换，不影响本轮运行结果。

源码 SHA-256：`scripts/routing.py` `44987334d38a8d731259663f94b5eecaa16bf4607a0600ad60e6c8a138344712`；`scripts/question_sets.py` `134e2e72e3d83d11f42daed64de2570972686f3a1ae7614aab1f86ca27c389ee`；`tests/test_routing.py` `bb98fb80b135cbb945c54c53c3e8dc1226e2983d1bfaabe8eaec3999c98083dc`；`tests/fixtures/s06_router_20_search_route.json` `956d4345b38c9aab35cee77584c3380b893d8bfdd847f49f5c6221b85575a77e`；`schemas/quick_scan/route-decision.schema.json` `1bca5d2b470b29007e06417acb9b8451e589506942755caab461afc593a4265d`。

执行回执及 `web_search_calls` 必须由上游受信任的 provider adapter 提供；本路由只校验记录间的归属，不联网验证 URL 所指页面的真实性。真实 provider 与跨仓闭环仍按后续任务验收。
