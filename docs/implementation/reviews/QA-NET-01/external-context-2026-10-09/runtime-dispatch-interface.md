# Phase111 调度、文本回答与原生事件：私有实施接口

本说明接续已冻结的public-result-interface.md；不回写旧工件。StockQA生产基线仍42a517c/schema8，本批实现仅在IQS独占runs/n111a/qa中。schema12、checkpoint2、public result1.1及下列行为都未完成整Phase111集中验收或源仓发布。

## 派发与恢复边界

- QuickScanWorkLifecycle.dispatch_context先验证独立identity snapshot、question manifest和查询覆盖，再由原检索协调入口取得短context。检索是Q09 budget-only operation，不是回答attempt。
- 同一个context可供已批准的顺位备用模型复用。每次模型HTTP仍有各自的实际attempt、请求/返回模型、响应摘要及费用；401/已确认且可计价429的失败记录不丢弃、不记免费。unknown发送停机并保留预留，不自动重复请求。
- synchronous/async provider与QAEngine checkpoint2恢复均使用真实store/use owner投影。main()的进程内集成已覆盖冷暖输出；这不是独立进程端到端实验。
- public1.1的answered_at采用原durable response.recorded_at（UTC）。原HTTP.completed_at和use.used_at单独保留，顺序为HTTP完成≤context-use保存≤回答记录。恢复不得把当前时间当原回答时间。

## 无原生搜索模型的文本协议

DeepSeek Responses仅在真实external_context_only绑定下准入；默认native能力仍为false。允许官方HTTPS api.deepseek.com的/responses或/v1/responses，不接受相似域名、明文、显式端口、userinfo、query或fragment。不把provider伪装成OpenAI。

实际文本请求携带冻结证据context与reasoning.effort=high，不带native tools/tool_choice/include。仅完整assistant最终文本进入答案；reasoning/thinking片段和原始响应正文不入结果或SQLite。external use独立证明上下文使用，不把native search_status从unverified改成executed，也不造web_search_call。

原model_resolution/1.0保持既有四provider协议组合；新增独立1.1 schema允许deepseek/responses。默认仍要求actual=requested，别名必须事先显式批准并匹配provider/protocol/requested/actual，不凭正文或请求名回填实际模型。

官方协议依据（本批只做离线HTTP边界验证，未调用收费API）：

- [Responses兼容说明](https://api-docs.deepseek.com/guides/responses_api/)
- [Responses参数](https://api-docs.deepseek.com/api/create-response/)
- [思考模式](https://api-docs.deepseek.com/guides/thinking_mode/)

## schema12 原生事件独立保存

新增quick_scan_native_search_events，主键是实际work attempt，外键指向quick_scan_attempt_response。保存原receipt SHA、HTTP response SHA、规范化短事件JSON及其SHA。插入必须匹配真实响应，UPDATE/DELETE被不可变触发器拒绝；回读重新核JSON及三个摘要绑定。

只保存有限工具元数据：最多20事件，每事件最多20短来源，总JSON≤60000字符。允许事件ID、状态、动作类型、来源URL/标题/日期和evidence_basis；不保存query、prompt、思考过程、网页正文或原始响应。

历史HTTP receipt allowlist、receipt_json及哈希配方保持。升级真实v11时只创建空事件表，不补造历史事件、不修改答案或费用。重放既存且没有事件的响应不能补入事件；新响应与事件同一事务持久化，已有事件只能精确重放。迁移中途失败应回滚到原schema、行和user_version。

## 测试与后续

tests/integration/test_external_context_cli_e2e.py使用合成身份/计价及HTTP替身，真实执行main/runner/client/SQLite。tests/unit/test_quick_scan_external_context.py覆盖事件持久绑定、不可变、损坏恢复、真实旧DDL迁移/回滚、禁止历史补写及保存上限。最新原始结果按checkpoint07索引及各process/JUnit读取，不跨批累加。

仍待两阶段/跨租约恢复、MCP每次init/discovery/search的独立Q09收费、真正OS子进程CLI、最终受影响回归/静态/一次集中独审、正常源发布及严格自有根清理。金融事实准确性、真实厂商计价、StockWiki import/ACK/query和真实owner golden另有门；本说明不关闭G3/F05/L03/TH-IN或启动200家live。
