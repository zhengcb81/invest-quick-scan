# F05-IQS-CONSUMER-01｜IQS facts 查询消费端合约

## 目标

在独立 IQS 工作副本中实现 F05 事实/关系查询 wire 的 IQS 原生合约入口，使已交付的 StockWiki F05 候选能够通过公开 IQS contract CLI 执行并校验其声明的 facts 合约操作。

本包交付后应能用离线合成输入证明：

1. IQS 可以验证 facts 请求、计算稳定查询哈希、构建和校验 facts 响应；
2. StockWiki F05 候选所调用的四种 native contract 操作都能通过 IQS CLI 路由；
3. facts 能力声明、schema 版本与实际 CLI 能力一致；
4. 原有 2.0.0–2.6.0 查询与 capability 行为保持兼容；
5. unknown、coverage gap、unsupported wire、owner rejection、strict/explore 等不同状态不会被压成“没有事实”。

## 不在本包目标内

- 不改 canonical IQS 或 StockWiki，不向任何源仓远端推送。
- 不把 F05 partial 改成 complete；不伪造真实 owner golden。
- 不连接生产 StockWiki 数据库、名单、8766 UI 或真实 owner store。
- 不运行真实公司查询，不调用 LLM、搜索、网络或收费 API。
- 不实现 facts 数据采集、owner 存储、身份解析、筛选策略或 UI。
- 不重写 F05 的 owner 查询服务，也不以本包的本地合成互操作代替真实 owner 端到端验收。

## 冻结输入和工作区

**IQS 输入提交：** aca0f4be5adcb96f0c7d8f58e0c4a205e6c17981

**F05 owner 输入提交：** 63a6ffcf23f8d16f47acf44bdbcf3e567a85458e

**工作目录：** C:\Users\郑曾波\Projects\iqs-f05-iqs-consumer-lab

**Owner schema：** C:\Users\郑曾波\Projects\iqs-stockwiki-f05-query-lab\config\quick_scan_facts_query.schema.json

**Owner schema SHA-256：** CD3E03417289A99F5194263603EAD6D954FD601B875CD3D5C08A74505BA8CBAD

在新 Lab 中基于上述 IQS commit 建立隔离克隆，并移除克隆的远端。若工作目录已存在或非空，不覆盖、不清理，先向总控报告。实现前确认当前提交与冻结输入完全一致，并确认 owner schema 的实际 SHA-256 与本卡一致；若文件缺失或哈希不同，暂停接口实现并报告，不从其他版本猜测。

不得把 canonical IQS 当前工作树的未提交文件带入 Lab。不得复制或读取 StockWiki 未跟踪运行数据。

## 协议基线

- Facts wire：schema 2.7.0。
- Query protocol：stockwiki.c06_facts_query/1.0.0。
- Owner operations：query_facts、export_facts。
- Query contract CLI protocol：iqs.query_validation/1.0.0。
- F05 owner candidate 通过 IqsQueryContract 请求下列 IQS CLI 操作：
  - facts-request：验证请求。
  - facts-query-hash：计算请求语义哈希。
  - facts-build：从已校验的基础 profile、facts 请求和 owner provenance 构建 wire 响应。
  - facts-response：验证 facts 构建响应及其与请求、owner 的绑定。
- 另提供消费端专用的 facts-export-response：验证 StockWiki presenter 返回的公开导出响应，并用原请求、快照和 owner profile 重建校验；它不是第五个 owner wrapper 调用。
- F05 schema 和冻结代码是协议事实来源；本包不得另造字段、枚举、方向表或状态含义。

## 允许改动范围

在独立 IQS Lab 中，新增或修改仅限于实现及直接测试这些职责所需的文件：

1. 新增 scripts/query_facts_contract.py：facts 合约纯函数。
2. 修改 scripts/query_contract_cli.py：新增四个 owner wrapper 使用的 facts-* operation，以及消费端专用 facts-export-response 校验入口；沿用现有 JSON 读取、重复键拒绝、canonical 校验、大小上限、标准输出和命名拒绝模式。
3. 新增 schemas/quick_scan/query-facts-v2.7.schema.json：从冻结 F05 owner schema 原样复制；内容必须与指定 SHA-256 一致。
4. 如 capability wire 的诚实声明需要，最小修改 scripts/query_capabilities_contract.py、scripts/query_capabilities_vendor_contract.py 及实际使用的 query-capabilities schema。只添加 2.7.0 / query_facts / export_facts 对应声明，保持旧版本响应内容与既有闭合校验不变。
5. 新增 tests/test_query_facts_contract.py、tests/test_query_capabilities_facts_wire.py 和 tests/test_f05_facts_cli_conformance.py；只有确有必要时，才在 tests/test_query_contract_v2.py 添加公开 CLI 回归。

如果必须新增其他文件，需证明它是这条合约的直接依赖，并在 handoff 中逐项解释；不得顺手改 UI、题库、路由、部署配置、依赖安装流程或不相关测试。

## 实现要求

### A. Schema 与 API 边界

- IQS schema 文件逐字节复制冻结 owner schema；测试必须验证该文件的 SHA-256 与本卡固定值。
- 不依赖网络 schema resolver；所有 JSON Schema 引用在本地可解析。
- CLI operation 名称与 F05 IqsQueryContract 的四个调用完全一致；facts-export-response 只用于验证 presenter 生成的公开导出 envelope，不改变 owner wrapper 接口。
- 每个 CLI 输入必须检查精确允许字段；重复 JSON key、超限输入、错误 wire、额外 envelope 字段按既有 CLI 规则拒绝。
- Unsupported operation/version、owner 明确拒绝、无事实、coverage gap、unknown 必须保留不同语义；任何 unsupported 或 rejected 均不得回退成空结果。

### B. 请求哈希与重放语义

- 按冻结 F05 contract 实现 query hash 的规范化规则。
- page/cursor 和 snapshot 仅是呈现/重放参数时，不得错误地拆成不同逻辑查询；筛选条件、信息截止日、实体范围或 strict/explore 模式改变时查询身份应改变。query_facts 与 export_facts 代表同一逻辑查询及其不同呈现，必须共享查询哈希；以冻结 owner contract 为准。
- information_cutoff 的 materialize/default/replay 规则必须和冻结 wire 一致，保证同一快照重放可复现。
- 游标和 snapshot 必须绑定正确 query hash；跨查询、跨 snapshot 或非法 offset 的游标必须拒绝。

### C. 响应构建与验证

- facts-build 只消费 IQS 已验证的原始 profile 与 owner 引用；不访问数据库或网络，不引入第二事实库。
- 对 observation_id、payload hash、item index、subject/listing/segment scope 和 evidence id 的引用做一致性验证；不得构造不存在的来源。
- strict 与 explore 分离。strict 中不得出现未绑定、冲突、过期、方向未解析、商业阶段 unknown、证据缺失/未解析等候选；explore 可以保留候选，但必须保留实际 status_detail，不能升级其资格。
- 保留 empty、coverage_gap、unknown、unavailable 等状态的区别。一个有效空结果只能表示查询确实已执行且覆盖状态允许；缺能力、拒绝、源缺失不能表达成“没有事实”。
- 方向、期间、商业阶段、证据审核、断言冲突、质量条件、分页、快照与 export 的规则逐项遵循冻结 F05 contract。不要新增公司名、ticker、市场或小行业特判。
- 不得把事实候选升级为正式产业链结论、金融准确性证明或全市场覆盖声明；保留 no_cross_fact_join 和 market_wide_claim=false 等协议字段。
- export_facts 必须校验候选列表、查询哈希、dataset 哈希、协议/快照与原查询的一致性。

### D. 能力声明

- 只有四个 CLI 操作真实可执行后，才可在对应 capability wire 中声明 2.7.0、query_facts 和 export_facts。
- capabilities 1.1.0 与 1.2.0 的既有字段、旧 wire 数量/含义和严格响应重建必须正确适配；若 schema 需要增加 wire 数量，测试必须覆盖新旧版本边界。
- 冻结输入中 capabilities 1.1.0 当前为 6 个 supported_query_wires，1.2.0 当前为 7 个（含 2.6.0）；加入 2.7.0 后相应应为 7 和 8。若代码实现的分支与此不同，先按冻结源码查明，不得照抄数字猜改。
- 保持 facts_producer_ready=false、financial_accuracy_proven=false、full_C06_milestone_accepted=false，除非这些常量由独立后续任务按实际产品验收改变；本包不得改变它们。
- 2.0.0–2.6.0 的 operations、capabilities 和合法响应不可因新增 wire 而改变。

## 测试要求

全部测试使用临时目录、合成实体与冻结协议 fixture；测试中不读生产路径，不调用网络或 API，结束清理由测试创建的临时目录。不要运行全仓小时级测试。

### 单元测试

至少覆盖：

- schema 对合法 request/response/export 和错误版本、未知 operation、缺字段、额外字段、重复 JSON key 的接受/拒绝。
- facts-request、query-hash、facts-build、facts-response 四个 owner wrapper operation 的正反例；facts-export-response 另需覆盖公开导出响应验证正反例。
- query hash 对页大小/游标/快照呈现参数的稳定性，以及对真实筛选条件变化的敏感性。
- 信息截止日默认值和同一快照重放；跨查询 snapshot/cursor 误用拒绝。
- strict 与 explore 的状态边界；unknown、not_applicable、expired、conflict、coverage_gap、empty、unavailable 不混淆。
- subject、listing、segment、observation、evidence 引用和 hash 一致性；伪造/错绑/重复引用拒绝。
- 方向约定、期间边界、商业阶段、证据审核、断言冲突、质量条件、分页和 export 的边界案例。
- capabilities 中 2.7 声明与 CLI 可执行操作一致，同时旧 2.0–2.6 路径不退化。
- 不因低分或无匹配候选把 unknown 改成 0/empty，不静默接受 owner 明确拒绝。

### 公开 CLI 集成测试

用临时 JSON 文件分别通过公开 scripts/query_contract_cli.py 调用四种 owner wrapper operation 和 facts-export-response；断言退出码、protocol、operation、status、错误码及 canonical JSON 结果。公开导出正例须来自合成的 owner presenter 形状，负例至少要在重算自校验哈希后仍因候选集/查询/快照绑定不符而拒绝。另用合成能力响应覆盖 capabilities 1.1.0 / 1.2.0 的新旧 wire。

还必须用冻结 F05 候选的 IqsQueryContract 实例实际调用四个 wrapper，构造参数与返回验证均使用合成 fixture，并断言 native_supported=True。F05 候选代码只读，不传 owner root、不访问其运行数据。再用冻结 F05 的 FactsContractAdapter 包装上述 IqsQueryContract 实例，通过无效 facts request 触发 IQS native rejection；用 spy/monkeypatch 证明 StockWiki 本地 fallback 确实未执行，且 rejection 原样传播。若需要从提交中恢复 F05 调用代码，只能在 IQS Lab 自有临时目录恢复冻结提交 63a6ffcf23f8d16f47acf44bdbcf3e567a85458e 的 tracked 代码，结束后清理；不得改动候选仓。

推荐运行范围：

- pytest tests/test_query_facts_contract.py tests/test_query_capabilities_facts_wire.py tests/test_f05_facts_cli_conformance.py -q
- pytest tests/test_query_contract_v2.py -q

若某组测试必须依赖显式环境变量或外部服务，拆分成清晰的离线命令；本包离线测试不应因缺少真实 owner store 而 skip。handoff 要列出真实执行命令和原始 passed/failed/skipped 数，不得把 collect-only 当成测试通过。

## 独立审查与修复

最终交接前，由**与实现作者不同的真实独立 agent**审查冻结 payload commit，重点检查：

- F05 contract/schema 兼容是否逐项一致；
- strict/explore、unknown/empty、owner rejection 的语义是否被错误折叠；
- capability 声明是否与公开 CLI 的真实执行路径一致；
- 冻结 F05 IqsQueryContract 的四个 wrapper 是否实际打到 IQS Lab 的 native facts 操作，native rejection 是否不会错误触发 local fallback；
- 2.0.0–2.6.0 兼容是否保留；
- 测试是否有真实正反例、是否调用公开 CLI、是否存在只断言实现自说自话的 tautology；
- 是否越界访问生产数据、引入网络/收费调用、硬编码公司或复制了不必要的 owner 数据逻辑。

作者修复全部发现，对受影响测试重跑；同一独立审查者必须针对修复后的最终 commit 复查。只做这个集中审查节点，不在每个实现小步骤另加审批/凭证。交接必须附真实 agent 身份、调用/审查证据、审查绑定的最终 commit、每轮发现与修复、最终结论；不得自制 JSON 冒充真实审查。

## 交接内容

在工作 Lab 的 docs/handoff/F05-IQS-CONSUMER-01/ 提交：

- handoff.json：遵守源 IQS 的 docs/implementation/parallel-lanes/handoff.schema.json 1.0.0；lane_id=iqs、package_id=F05-IQS-CONSUMER-01。
- report.md：冻结输入与 payload commit、精确变更路径、协议版本与 schema SHA-256、运行命令和 passed/failed/skipped 数、隔离/清理、网络/付费调用、独立审查证据、未解决项。
- synthetic-fixtures/ 或明确的 fixture 路径：注明全部为合成协议样例，不是真实 owner golden。

handoff status=complete 仅代表本施工包代码完成。必须在 open_items 或 next_action 中写清：

- F05 仍未关闭；
- 尚缺受支持的真实 owner 只读入口及真实 owner golden；
- 总控仍需在正式产品接线后，通过 StockWiki 公共 query v2 CLI 运行真实 owner 端到端 strict/explore 正反例并核验 hash、分页/快照和来源；
- F05 历史离线全套计数差异仍待单独澄清。

不得推送到源仓 remote、改 canonical IQS/StockWiki、导入或读取真实数据库，或把 package complete 描述为 F05 complete。

## 完工定义

本施工包只有在：四种 IQS native facts 操作可由公开 CLI 和冻结 F05 调用 wrapper 实际调用、native rejection 不会触发 fallback、2.7 capabilities 声明与实际路由一致、旧版本定向兼容测试通过、上述集中独立审查对最终 commit 给出通过、交接文件齐全且无未修复发现时，才可交付为 package complete。真实 owner 互操作与 F05 关闭由总控按 PWF 后续节点完成。
