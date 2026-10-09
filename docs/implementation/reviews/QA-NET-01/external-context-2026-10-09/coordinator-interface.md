# 私有检索调度接线：Phase111

这是已实作接口及接续说明，不是生产 release、真实厂商认证或新增审查门。固定源输入 StockQA `42a517c4bd6bc8219f926957c6c332944da3278a`，私有 owner `IQS/runs/n111a/qa`；不写其他仓。范围仍是同目录 `scope.json` 的28路径，当前新变化在 external_context/external_journal/work_store/external_search_provider 及其原单元测试。

## 已实作入口

`src.utils.quick_scan_external_context.retrieve_external_question_context(store, work_item_id, lease, policy, model_policy, *, question_manifest_sha256, health_store, unknown_reset_cooldown_seconds, rate_limit_cooldown_seconds, probe_lease_seconds=180)` 返回独立短数据 context。store 是实际 QuickScanWorkStore，policy 是实际加载且不可篡改的1.1 SearchPolicy；manifest hash来自独立 producer authority，不能从 policy 自称的hash推定。health_store 是既有 QuickScanProviderHealth；冷却参数由调用者明确给定，仅表示下一次探测机会，没有实际 Retry-After 不声称厂商重置时间。

`model_policy` 始终是原回答模型顺位政策。函数仅给Q09添加搜索 route 的计费投影，不将这些 route 放入 OrderedSearchProviderCascade，不创建另一账本、scheduler或通用重试器。新搜索每个HTTP经原Q09成本、请求和槽位预留，实际价按收到HTTP/已确认成功/observed provider credits分别结算。原生模型使用原费率resolver；外部搜索用已冻结 ExternalSearchCostResolver，不能混用pricing_ref。

每个冻结query按用户搜索顺位尝试，单route最多发送一次：

1. `store.lookup_external_search` 只读实际 durable 意图/结果，核绑定和原ledger；已有结果先于key/health/预留处理，warm不需要新key或新HTTP。
2. 确认失败且费用已知、空/坏JSON或无目标发行人可用证据，可以到下一route；这些已付费历史不重发。超时、plain429/500等unknown、无usage/无拒绝计价、持久化失败均停止，不自动fallback。
3. 新发送先验证credential/protocol和既有Q08冷却，再原子begin/consume。未发送意图只有原同一有效lease、无dispatch/result才可原operation/原预留继续；dispatch存在或lease变化不能猜测未发。
4. received Retry-After仅保存已验证delta秒，非法/日期header目前按unknown处理。超verified usage仍真实计费；同计价预算版本不允许换generation绕过价格上界。改变计价是明确新配置动作，不重置旧费用。
5. 全部query有实际可用结果后，由实际journal重建 context。原时间不改；同URL单列，`query_ids` 与 `retrieval_provenance` 保留各query自己的短摘要、日期、operation、retrieved_at。标题/摘要是未可信数据；全部正文及metadata仍受30,000字符上限，单摘要不超过500。`claim_verification=not_automatic`。

安全的具名停止由 `ExternalRetrievalBlocked.reason` 给出；原SQLite/持久化错误直接停止。仅返回context尚没有回答attempt、实际模型、native web_search event或新used_at；调用者不得称它是“已被LLM使用”的证明。

## 当前实际证据

`intake/QA-NET-01/2026-10-09-external-context/verification/` 下各label保存实际执行源/guard/runner、stdout/stderr、JUnit、process.json。初20RED是入口缺失，不是20个旧漏洞；green-01/02的夹具错误与真实URL跨query丢来源分别记录。green-03为26P；受影响273P；Retry-After和价格界三RED后最终六文件**276P/20.36s**、controller21.007s，0失败/错误/跳过。各批有重叠，不相加。最新handle27720/35856已终态，没有活动等待。仅HTTP边界替身，真实SQLite/Q08/Q09；密钥/外网/生产库/下载/费用均0。

尚无全公开CLI、真实LLM context-use或厂商live E2E。MCP在预留前以 `mcp_handshake_required` 停机，仍须按完整计划实现分阶段计费init/discovery/search，不以REST通过替代。跨lease未发送接续/整体两阶段恢复也未认证。原有scope与同批一次集中审查要求不变。

## 下一步的真实入口

从既有 `LLMClient.send_search_request` / async counterpart、`_search_request_payload` / `_parse_protocol_search_response` 与 `begin_quick_scan_send` 接线。先用真实payload/原store RED验证：external-only真正把短context发给LLM且不提供native tools；hybrid两种来源独立；错误work/manifest/lease/context SHA、prompt遗漏context、伪造use-proof均在HTTP前拒绝。不能走旧不记账 `send_request` 规避现有传输边界。

随后建立同一store的私有不可变use-intent/result，实际绑定work/lease/attempt、context hash、实际发送prompt hash、原搜索receipt hashes与实际LLM receipt hash；HTTP前后事务边界分别验证。保持原HTTP receipt、actual model、usage与prompt SHA，不向native receipt补事件。BaseLLMProvider要求与模式一致；C06通用搜索状态只在完整独立use-proof校验后投影。格式修复/备用模型各自真实收费，同冻结context复用；结果未知不可盲重发。最终公开CLI cold/warm/中断/恢复/封包、MCP分段及受影响静态一次通过后集中review、源发布、严格自有根清理。

此前checkpoint01/02及raw字节不变；checkpoint03只留本轮私有实施。不要盲跑历史prepare/publish/cleanup helper；不据格式或软件GREEN关闭G3/F05/THIN、修改生产数据库或扩大已确认股票池。
