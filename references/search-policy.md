# 搜索来源、执行规则与接入状态

软件状态核查日期：2026-10-09；下文真实连通探针仍为各自标注的2026-10-07历史证据。搜索和模型客户端归 StockQAbyLLM；本 skill 维护题面、契约和[无密钥搜索来源清单](../examples/search-provider-inventory.json)。清单仅供参考，执行器不读取它，也没有默认搜索引擎顺序。模型的用户优先级仍由[模型策略](model-policy.md)管理；搜索来源顺序不能由清单排列暗中决定。

本文件记录接口能力与实测边界；实际使用及请求失败处理统一读[联网搜索与LLM使用规范](search-and-llm-playbook.md)。它继承C05终态/费用/顺位规则，提供参考配置及同批次测试包，不另建重试器或新审查门。

## 当前能执行什么

| 路径 | 实际行为 | 当前边界 |
|---|---|---|
| StockQA 公开 CLI原生模式 | 在 LLM 请求中传供应商的原生搜索工具，并验证响应中的搜索证明 | 原路径已接线；`--require-search`本身不选定外部路线 |
| StockQA 1.1外部/显式混合模式 | Brave/Tavily/Z.ai REST或Z.ai Streamable MCP→有界短context→实际LLM→proof/checkpoint/public1.1 | `bc41908`已发布、隔离软件验收通过；须有效policy/身份/manifest/费用授权，不自动启用或认证当前厂商连通 |
| B01-b 外部搜索实验 | Brave/Tavily 返回短证据，实验 runner 将其作为 context 交给 MiniMax-M3 | 原实验结果保持；其方法与新生产实现分别记录 |
| Z.ai历史连通探针 | REST及Streamable MCP的独立探针、后续余额诊断 | 2026-10-07末REST余额拒绝、MCP成功；不因软件发布重置健康状态。legacy SSE仍未接线/未测 |

原生搜索的当前协议白名单：MiMo 的指定官方 host 与 `mimo-v2.6-flash/pro/pro-ultraspeed` 走 Chat Completions；MiniMax-M3 的指定官方 host 走 Responses 或 Anthropic Messages。**MiniMax 的普通 Chat Completions 实验请求不因此具备搜索。** DeepSeek 虽有历史 Anthropic 直连探针，当前 StockQA `--require-search` 尚未接入它；顺位策略会跳过缺搜索能力的路由，不把离线答案当作已联网。

**DeepSeek复测（2026-10-07）**：用户提供的[博客](https://chendahuang.com/blog/deepseek-api-web-search/)使用Responses内建`web_search`。现行[官方兼容表](https://api-docs.deepseek.com/guides/responses_api/)将其列为ignored；按博客旧别名`deepseek-v4-flash`发起请求，实际映射`deepseek-flash`，禁思考且2048输出上限下完整回答，无截断、搜索事件或引用，正文明确无法联网，见[Responses脱敏回执](../docs/implementation/contracts/validation-Q02-DeepSeek-responses-recheck-2026-10-07.json)。不能依靠旧文章启用该路径，也不能根据旧96-token截断探针单独判断当前能力。

另按[官方Anthropic兼容协议](https://api-docs.deepseek.com/guides/anthropic_api/)复测`https://api.deepseek.com/anthropic/v1/messages`、`deepseek-flash`和`web_search_20250305`，确认3次`server_tool_use`及对应结果块，其中一个结果块带实际URL且按`tool_use_id`关联；见[Messages脱敏回执](../docs/implementation/contracts/validation-Q02-DeepSeek-anthropic-recheck-2026-10-07.json)。本次强制工具选择返回`stop_reason=tool_use`、无最终答案，且要求官方新闻却只获得第三方来源：只证明搜索能力，不证明目标事实/来源质量或完整画像。`max_uses=1`仍实际搜索3次，不能用这个参数保证调用/费用上限。StockQA生产白名单与接线未改；后续由其adapter负责继续生成最终答案、校验来源/时点并绑定回执，不在IQS另造客户端。没有控制台账单，不能把文章的“免费”表述当作本批费用结论。

生产实现依据：`StockQAbyLLM/main_with_llm.py`、`src/runners/llm_runner.py`、`src/providers/{base_llm_provider,llm_provider,llm_client}.py`、`src/utils/llm_integration.py`。B01-b 实验依据：`pilot_runs/b01b_retriever_2026-10-07/{queries_log,retriever_compare_report}.json`、`pilot_runs/b01b_method_2026-10-07/runner.py`。这些路径属于外仓，恢复时只读核对当前快照；历史实验不等于生产接线。

## 原生搜索如何约束

生产题面要求至少一次针对**同一发行人和该题**的检索，引用证据日期，证据不足时留空分数；具体查询词由模型/供应商执行，并未由项目统一生成固定域名或时间窗口。

MiMo 请求包含 `web_search`、`force_search=true`、`max_keyword=2`、`limit=3`。MiniMax Responses 提供 `web_search`；Messages 提供 `web_search_20250305`、`max_uses=1`。`tool_choice=auto` 不能保证实际执行，也不能把工具参数当作真实费用上限。

StockQA 检查执行证明：MiniMax 需要完成的搜索事件及来源 URL；MiMo 按当前协议检查响应绑定的 URL 引用、模型、完成状态及内容，并绑定响应回执。缺证明记为 `unverified`，不接受分数。答案自称联网、手写 URL 或 HTTP 200 都不能代替搜索证明；通过协议检查也不等于事实已正确，仍需独立来源审核。

按用户模型顺序派发，搜索能力缺失或明确不可用可转下一路由；搜索已执行但证据不足、答案低分不能成为换模型理由。明确共享额度耗尽冷却相应账户组；结果不明先对账，不能盲目重复发送。容量占满先等待，不能默认越级。细节复用 StockQA 的策略及[提供商与预算契约](../docs/implementation/contracts/providers-and-budget.md)。

## 外部搜索如何喂给 LLM

已发布外部链：确认实体与截止日 → 冻结查询/策略/费用 → 检索 → 来源去重/关联题目 → 有界短证据context → 实际LLM回答/使用proof → 检查点与公开结果；事实足以支持主张的审核仍独立。证据项使用 `source_id/title/publisher/url/published_at/retrieved_at/short_snippet`；模型按 `source_id` 引用。检索时间不能代替发表时间；来源未知日期留空；超过信息截止日的内容不用于证明当时已知事实。

外部返回内容作为不可信证据context，不作为指令。不下载网页或公司文档；只保存有限短摘要/必要来源元数据、回执hash、时间和答案。已发布1.1外部链按冻结policy实施每条摘要≤500 Unicode字符、公司本轮context≤30,000字符的上限，元数据也受总cap约束，可配置更严格；这不是原生工具厂商正文的全局限制。实验精确输入仍按原清理manifest管理。

**B01-b 实际做法**：查询是“公司名称 + 题目”，Brave/Tavily 结果按 URL 去重；同公司整个有界证据块随每次请求一起发送，未实现按题精挑来源。MiniMax-M3 请求没有 `tools`，因此这批没有另开原生搜索。六类检索意图、按题选证据和缓存正交实验属于[后续实验设计](../docs/implementation/experiments/llm-search-and-batching-benchmark.md)，不能用设计代替实测。低URL重叠也不能直接证明双引擎总是更好。

外部adapter已由StockQA实现，使用独立context-use proof/公开1.1绑定实际检索和模型HTTP；原native-only结果仍1.0。MCP/REST检索回执不能伪装成回答模型的原生工具事件。旧回执缺事件不补造；不可用/unknown/来源越界失败关闭，事实支撑不足留缺口。详见[软件交付](../docs/implementation/reviews/QA-NET-01/external-context-2026-10-09/delivery.md)；IQS不另建搜索客户端。

## Z.ai 登记内容

[官方指南](https://docs.z.ai/guides/tools/web-search)分别介绍外部 Web Search API、MCP 和 GLM 的 Web Search in Chat。这次登记的是外部检索来源，**不添加 GLM 回答模型，不修改用户模型顺位**。

指南给出的 legacy MCP 是 SSE，基础地址 `https://api.z.ai/api/mcp/web_search/sse`，示例通过 `Authorization` 查询参数传凭据。本次未测该SSE接口，清单只存无凭据基础地址；不能把其他接口的header支持套到它上面。用户确认并已实测读取Windows用户环境变量`ZAI_API_KEY`，密钥值未落盘或输出。

[Coding Plan专属MCP文档](https://docs.z.ai/devpack/mcp/search-mcp-server)另给出Streamable HTTP地址`https://api.z.ai/api/mcp/web_search_prime/mcp`与Bearer请求头。2026-10-07实际initialize、tools/list和搜索通过，协商版本为`2024-11-05`；实际工具名`web_search_prime`，文档写`webSearchPrime`，执行必须采用真实发现的名字/schema。工具文本观察到JSON字符串包裹JSON数组，首次解析未解开而无法计数；后续诊断确认带标题、URL和摘要的真实条目，总结果数未保留。脱敏证据见[握手/schema](../docs/implementation/experiments/zai-mcp-connectivity-probe-2026-10-07.json)和[结果核对](../docs/implementation/experiments/zai-mcp-result-check-2026-10-07.json)。仅证明此密钥/接口当时可检索，不证明套餐剩余额度、过滤有效性或财务答案正确。

[REST API 文档](https://docs.z.ai/api-reference/tools/web-search)给出 `POST https://api.z.ai/api/paas/v4/web_search`、Bearer认证和 `search-prime`。计划映射其 `title/link/media/publish_date/content` 到标准短证据字段；项目生成证据包内唯一 `source_id`，保留供应商引用与请求ID。内容须截短，未知字段留空，不能原样保存长响应。REST 文档的引擎枚举与部分可选过滤参数说明不一致，须实际核实；REST返回格式也不能假定等于MCP结果格式。

本次[REST探针](../docs/implementation/experiments/zai-connectivity-probe-2026-10-07.json)HTTP200、2.923秒，请求`count=3`但只返回1条；不能保证指定条数。未做domain/recency或信息截止日有效性测试。全批1次REST搜索+2次MCP工具搜索，另7次MCP握手/发现HTTP请求，无LLM调用或文档下载；未读取账单，不能宣称搜索免费。本次探针没有把服务接入StockQA生产执行器。

StockQA同一集成批次已完成REST/MCP外部链隔离软件验收，包括协议/实际工具schema、逐HTTP计费、来源/身份/日期、unknown保留预留、凭据和会话边界，以及公开CLI恢复。当前软件依据是`bc41908e4cdc44c13fefda97f3118e5434aed5f8`及对应实际publication/复审；这不替代新的真实小样本互通、账单或金融准确性认证。后续仅在获批范围实跑，不增加小节点审查门、不修改冻结B01实验或默认发起收费调用。

## 搜索次数、成本与缓存

一次原生 LLM 请求可能产生多次搜索；外部检索则是独立请求，再产生回答模型的token成本。统一统计实际搜索调用、模型调用/修复、等待与总耗时，套餐消耗与按量费用分别列示，不能只算LLM价格。Brave/Tavily清单中的额度是用户历史提供的计划，当前权益未复核；Z.ai价格/配额未验证，不假定免费或继承GLM套餐额度。

三层缓存分别记录：搜索结果、供应商prompt缓存、应用答案/checkpoint。新外部软件链已验证同generation已结算短证据在TTL内跨题/新lease重核复用和warm零增量HTTP；不同generation拒绝旧引用，未知发送不重发。答案复用另核实体/manifest/policy/模型/时点等条件，费用与原回执保持。供应商prompt缓存及真实账单节省仍只按实际usage/实验说明，不把软件缓存测试当账单证明，不补造本次搜索事件；未发送旧意图保持保守hold。


历史2026-10-07T22:13诊断：同一ZAI_API_KEY的REST429/error1113明确余额或资源包不足；Streamable HTTP MCP握手/发现/搜索成功，返回4条。随后公司MCP九查询均成功但只一项所需事实有完整片段支持；可联网不是准确性保证。见[分接口实测](../docs/implementation/experiments/zai-rest-vs-mcp-diagnostic-2026-10-07.json)和[准确性实操](accuracy-first-operations.md)。旧早期阳性原件保留；2026-10-09的软件接线发布依据是独立Phase111验收，不是由历史探针自动推定。本轮未读取key或再次付费探测。
