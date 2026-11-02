# 共享引擎运行与恢复实操（2026-10-25）

本页描述当前公开接口。当前执行状态以根 `task_plan.md` 为准；10/18 实验文档是历史快照。研究导出、原工作检查点、封包完成、StockWiki 接收是四个不同结果，必须分别记录。

## 入口与分工

- IQS 的 `scripts/shared_company_engine.py` 编排原 Company Runner 和原 RuntimeBridgePort；不建立第二个模型客户端、预算库或调度循环。
- StockQA 的 `OwnerResearchServices` 使用原 owner、SDK、安全响应、请求/检索账本和标准答案存储。身份来自 StockWiki 公共主体/挂牌绑定，名称只用于显示。
- `execute_shared_engine(...)` / `resume_shared_engine(...)` 产生研究导出；显式调用 `finalize_shared_engine(task, services, export_dir)` 才尝试写原标准答案检查点。
- CLI `capabilities` 可独立使用；当前 CLI 不构造 owner。实际执行通过 Python API 消费原公开入口准备的服务，不从散装 JSON 或任意 callback 取得执行权。默认 CLI `report` 使用空的附加语义规则，只适用于原本未注入这类规则的产物；带 typed rules 的产物须用下述显式 Python 报告接口。

## 已付回答、只读操作与新发送分开处理

同一原任务的“检查并恢复”先读取原工作状态。已收到的响应可以单独保存、补封和导出；不需要重新配置今天的 API key、费用表或预算，也不因后续模型顺位、题包大小、思考参数和诊断开关变化重新提问。原账户访问与接收库校验仍保留。

普通与共享受绑定扫描现在复用StockQA原响应journal保存公开最终正文，写入与原response/费用记录同事务，早于题目解析。新扫描无需启用额外diagnostic才能恢复；旧记录先读journal，没有journal时兼容原已保留的diagnostic。旧记录若两者都没有正文，仅有hash无法恢复，不能新造正文或重发冒充恢复。

原 StockQA 公开入口的已付恢复使用 `--seal-deliveries --recover-checkpoints`，共享扫描再提供原 `--shared-company-config` 路径作为历史位置，其他原登记输入路径及 confirmation 继续使用原任务的值。不要为了保存旧答案重新 prepare/confirm 或创建新 work。缺少原始输入/响应时明确报告缺项，不用同名公司或最新一代结果代替。

一批题只答完一部分时，输出 `.scope.json` 的 `status=partial`，并分别列 `saved_question_ids`、`remaining_question_ids` 和原题数。退出成功表示本次保存操作成功，不表示剩余题已经问过或整个扫描完成。未知请求不能重发。逐项入库沿 StockWiki 原 ACK 记录接收与拒绝，单项拒绝不等于整批没有成果。

未登记指标名称按原文保留，并标记为未映射，不能猜改名称后用于标准指标横比。普通业务文字、无害扩展字段、JSON fence、同值冗余和正常长理由可以读取；错误主体、冲突分数、期间/单位冲突、实际私有思考或凭据仍不能当作合格标准答案。原正文、score、模型与原响应时间不因兼容读取而改写；工程保存成功也不是金融准确性背书。

同一HTTP包的缺题或坏题只影响该题；其他有效成员可保存，重复恢复沿原CP。事实列表条数和公开说明长度不作整答接受门。合法同比/期初期末等多期引用不能仅因输入年份不同被拒；有目标期来源也不证明计算正确。明确forward期间可以晚于截止日，但资料发布日期仍不能晚于截止日；把计划当current/trailing实际值的冲突仍需显示。原冻结schema与历史诊断不重写。

## 共享扫描的模型顺位

新扫描可以显式使用原 owner policy `1.6.0`，在原 `qa.quote_schema_version` 填 `1.6.0`，并增加 `ordered_route_targets`。下面只是并入原策略的字段片段；账户、route、模型、quota group 必须与 StockQA 生效模型策略逐项相同，首项还须与原 policy 的 `provider/model` 和 `qa.route_id/provider_config_ref` 相同。密钥继续只放环境变量，不改已经确认的原包。

```json
{
  "ordered_route_targets": [
    {"provider": "mimo", "model": "mimo-v2.6-pro", "route_id": "YOUR_PRO_ROUTE", "provider_config_ref": "YOUR_ACCOUNT", "quota_group": "YOUR_QUOTA_GROUP"},
    {"provider": "mimo", "model": "mimo-v2.6-flash", "route_id": "YOUR_FLASH_ROUTE", "provider_config_ref": "YOUR_ACCOUNT", "quota_group": "YOUR_QUOTA_GROUP"}
  ]
}
```

修改原策略后，沿原 UI 重新准备新扫描，预览会冻结这一顺序，没有额外许可系统。旧 `1.0–1.5` 确认、比较和已付任务保持原模型。普通本机配置不会因为代码升级自动切到 `1.6` 或扩大预算。1.6 的范围是普通自动顺位、缓存与原回答恢复；既有专用人工 work-decision 协议仍按其支持版本使用，不把 1.6 冒充 comparison/continuation。

StockQA 原 runner 先跳过没有本地客户端或原 SDK 未实现当前 `final_json` 研究通道的目标，这一步不发送请求。普通 `web_search` 可用不代表该研究通道可用。实际尝试只在原账本确认并已结算的 401/403、404、已识别 429 拒绝后向下一目标继续。未知结果、超时、5xx、收到但内容不合格、低分，都不会自动换模型重问。

每个目标保存自己的不可变 task、实际 route/账户/模型和原响应。前面完成的题目写原 CP 并排除于后续提问，只有剩余原题继续。原公司 scope 的顺序与首个 task 请求上限固定，换模型、改 UI 设置或重启均不重新获得额度；物理 pack 在原预算事务内只计一次。原共享费用、总请求与并发限制继续原子生效，不把各目标余额相加。

最近成功扫描与资料日期分别保留。多模型缓存按批准顺序选择第一个原策略允许的新鲜观察，原模型、来源、日期不改；未决原工作优先按原 owner 处理。已付恢复只重放尚缺 CP 的实际收到回答的原 route/task，已保存的部分结果不重复恢复，更不重复付费；缺原 safe 则停止。

## 首次运行顺序

1. 使用原公共工具取得真实身份、题目 manifest、authority、owner-config 和题目输入。冻结实体/主体版本、挂牌、题义、信息截止日和模型路由。分别保留 manifest 原文件 SHA 与规范内容 SHA；不能混用。
2. 如使用外部搜索，先以原 `build_shared_external_budget_policy(base_model_policy, search_policy)` 合成预算，再交给原 admission/confirmation。owner 与 lifecycle 使用同一合成策略；`external_retrieval.model_policy` 保留 base。已经确认的输入不得在背后改字节。
3. 由原 `prepare_execution` 读取实际确认记录和原生当前权限。当前work-decision 1.2/1.3方言在创建task前还须通过公开`assert_execution_controls(...)`核对本次cohort/retry/comparison参数；`prepare_execution`成功不代表这一步可省略，其他方言按其原契约核验。不得直接改私有control状态。搜索绑定的 manifest 文件 SHA 来自原验证后的 observation context，与 search plan 独立比对；不能从 search plan 自己取一个值来验证自己。
4. 创建原 lifecycle、task、OwnerResearchServices 和 runtime config；运行公开 `preflight`。预检没有模型/搜索 HTTP，也不是回答成功。真实发送仍执行原当前权限、lease 和预算检查。
5. 用新的、彼此分离的 session/export 目录调用 `execute_shared_engine`。在模型调用前保存原 intent 和 pending checkpoint；实际 SDK 响应保存安全可见输出，不保存私有思考。
6. 核对原检索 journal 与 `external_context_use`：实际取得 sources、传入实际模型消息、并绑定题目/主体/截止日/请求。搜索成功不自动等于答案有证据。当前这条正式检索封存正例只覆盖 singleton；question pack 仍受原 external context 契约限制。
7. 调用显式封存 API。它核原导出日志与 sidecars，完整答案必须按原引用ID规范化规则逐字段匹配原 native safe response，并属于原 work 的成功 attempt。原单题裸对象与pack载体分别按原SDK契约识别，不通过删字段“匹配”。最终写入复用原 `commit_standard_answers`；不能改分数、补造来源或手写检查点。

创建服务前应核实原观察库capabilities。当前原owner singleton登记要求schema3或4；fresh隔离库经原公开迁移工具初始化，旧schema2须先用原工具备份并验证，再显式2→3→4迁移。不能复制另一个workspace的观察ACK来冒充当前库的主体绑定。原身份库只读复用，记录复制前后SHA。

共享生产Runner的语义门使用原`standard_answers.validate_content`及冻结题目、schema、metric registry；评分题的`items`必须为空，事实题、未知态等依原规则判断。生产v2还绑定当前native attempt与实际EvidenceBoard，经原StockQA标准答案来源/日期/context-use校验后才能完成slot。冷执行、恢复与封存走同一规则。schema通过不是评分语义通过，更不是金融结论正确。补充类型提示必须独立于历史原题面并有版本/hash，不能悄悄改题义。

## 中断后恢复

- 原UI已收回答但未完成保存时，选择该原运行的“检查并补封”。有冻结共享配置的包沿原`--seal-deliveries --recover-checkpoints`进入共享检查点的仅重放路径；缺原已收响应就停止，禁止新增模型或搜索请求，不要求重新提供密钥或新费用授权。普通恢复路径保持。恢复后继续原入库/ACK，不把“已受理”当作签收。
- 若一次重放被内容校验拒绝，其诊断继续保留；后续软件修复可以在仅重放模式读取最近尚存的原pending检查点。存在但损坏、目录或断链的检查点不能被静默跳过；不修改原答、原来源板、原时间或费用。
- 先检查同一原 intent/attempt，禁止先发一遍模型请求“试试看”。有原安全输出才恢复；存在原请求但缺安全输出时保持待核实，不清库、换任务或另开预算重发。
- 新进程仍使用同一冻结输入和原记录，以 `resume_shared_engine` 恢复。原 lease 必须按原规则有效；本接口不自动续租或接管过期 work，也不恢复私有思考。
- 恢复后显式封存；若之前已经保存同一完整答案和 receipt，重复封存复用同一检查点并补原封包，不再调用模型。多题部分成功时保留已保存进度。
- 沿原intent/attempt、预算和检查点确认接续的是同一次请求；已收答案不重问，ACK失败只重投原结果。日常恢复不要求逐表全行hash审计或新核查凭证。相关故障测试验证原记录保持及新增请求数；模型token cache命中与本地答案复用分别记录。

新显式company-scan允许发布日期未知的短来源进入上下文，前提是检索时点已知且不晚于截止日、主体绑定正确并保留限制说明；发布日期保持null，不从URL或财年推断。旧任务按原快照/事件中的接受语义恢复，不追认当时被过滤的来源。模型引用仍须与当前原请求的实际搜索或已发送provided来源对应，真实HTTP来源与HTTPS同样处理；已失效的板内记录不能改名成外部引用复活。

原安全响应已知但语义不合法时，保留原回答、receipt、费用与失败导出。先走原known-response resolution，再由原`retry_unusable_answer`明确开启新generation，重新准入与冻结输入；不得增加旧task请求限额、手改失败行或重置预算。当前singleton恢复证明与pack分支分开核验，singleton不能伪造pack intent/member。生产单次任务暂限一次模型请求，本轮不宣称已支持自动多轮修答。

源码或驱动因真实反例修复后，原cold锁和执行字节必须保留。尚未付费的失败preflight可以显式修复谱系后重冻结；已取得safe的版本不能在背后换锁冒称同版本恢复。摘要器也须从原loader重算task内容哈希，不能只相信文件内自报的`task_sha`。

### 带附加语义规则的恢复与报告

`answer_semantic_rules` 是实际模型请求中已参与稳定前缀哈希的规则，不是恢复时可以另写的一段提示。生产入口从原已验证 task 中逐题读取完整题目，并由锁定版本的 `question_prompts.typed_semantic_rules` 生成规则；题目顺序、提示源码、schema 和 metric registry 都必须保持原冻结绑定。规则不从事件自报文本、模型回答或待恢复目录中的任意配置取值，也不授予 owner、来源或金融资格。

原 Company `build_runtime_request(..., answer_semantic_rules=())` 现在统一供冷执行和重放使用；`ReplayEngine`、`resume_from_files`、`generate_report` 均接受同名 keyword-only 参数。main 的 `resume_shared_engine` 和 `finalize_shared_engine` 已从同一生产语义入口把规则传入历史验证。原 protocol、稳定前缀和动态上下文的三项哈希比较继续严格执行；缺少规则、顺序变化或内容变化都应拒绝，不能捕获错误后改用空规则或信任事件里的哈希。

以下片段用于原部署环境已完成加载、`task` / `services` / `session_config` 已按本页首次运行步骤准备的场合。`checkpoint_path` 指原 pending checkpoint；三个输出目录是新的、自有、无链接目录。它不会代替原准入、lease 或原生安全响应检查。

```python
from scripts.shared_company_engine import resume_shared_engine, finalize_shared_engine
from scripts.question_prompts import typed_semantic_rules
from iqs_company_agent_lab.reporter import generate_report

recovered = resume_shared_engine(
    task, services, session_config, checkpoint_path, export_dir,
    session_dir=session_dir,
)
sealed = finalize_shared_engine(task, services, export_dir)
repeated = finalize_shared_engine(task, services, export_dir)

# task 和提示源码均须先与原输入锁核对；规则顺序与生产入口相同。
rules = tuple(typed_semantic_rules(row["question"]) for row in task.questions)
report = generate_report(export_dir, report_dir, answer_semantic_rules=rules)
```

Company 和 main 的普通 `report` CLI 当前没有传入这些可信规则的选项。默认空 tuple 保留旧研究产物兼容；它不能正确重放带附加规则的产物，拒绝是预期行为。不要由此改 checkpoint、删规则或绕过历史验证；这类报告使用上面的显式 API。该边界不表示所有公开 CLI 已完成 typed 产物接线。

### 已有 safe 的显式源码修复兼容

generation3 的真实 cold 已保存合法 native safe；当时暖恢复因重放漏传同一 typed rules，被原稳定前缀哈希检查拒绝。修复统一请求构造和规则传递，不能改 safe、问题、引用、receipt、原任务或账本来消除差异。原冷执行锁仍为原锁，修后暖恢复只能记为“不同源码的显式修复兼容”，不能称为同版本 cold/warm 验收。

以下仅记录2026-10-25 generation3一次历史修复，不是新扫描或日常恢复前置：当时使用 `typed-generation3/replay-repair/source-transition.json`、`repair-source-pins.json`、72项旧锁及六处源码前后摘要解释不同版本的恢复结果。历史证据原样保留，`same_source_cold_and_warm_claim=false`保持；当前恢复直接沿原intent/attempt、预算、检查点和公开入口，不创建或刷新这套transition凭证。

修复暖恢复在新进程执行：移除模型/搜索 key、通过audit阻断socket连接、解析与sendto；执行路径不调用子进程传输，只允许复用原 native safe。恢复前后比较原全部八张预算/请求/外部检索/context-use 相关表、原安全响应及 `owner_decisions` 的完整行投影哈希；同时核原 checkpoint、标准答案、delivery 和导出/报告之间的绑定。新增本地检查点与封包应单独记录，不把它们混入“账本完全不变”的比较。物理模型和搜索请求必须均无新增，不能只比较计费总数、金额或行数。双封存应复用同一原检查点；`ready` 仍只是本地待交付封包，不是 StockWiki ACK，也不是金融准确性通过。

本轮实际修复暖恢复已于2026-10-25 14:15:41Z通过，耗时128.479秒，新增HTTP0；两次封存同schema2检查点，delivery=ready，原完整账本行hash全等。只读摘要实际运行通过且工作库SHA前后相同，独立实际审passed/open_findings=[]。证据见本轮generation3/replay-repair薄归档；same_source_cold_and_warm_claim=false。

如果本地适配代码在调用原native transport之前失败，须先保留确切源码、锁、异常及独立归因证据；仅“很快失败”“没有答案”或timeout不能证明未发送。确认未发送后可用原公开`reconcile_budget_attempt(... resolved_outcome="confirmed_not_sent", actual_cost=0, cost_source_ref=真实证据引用)`审计结算。旧unknown操作、dispatch、回执保留；不直接改SQL或清账。租约仍有效就等待真实到期，原`recover_expired`后由原engine领取；使用同账本/预算、显式新query_id和fresh session，不把重试冒充缓存命中。本轮精确案例见`runs/reconcile-production-2026-10-25/engine-fix/pretransport-retry-plan.md`及对应独审。真正无法确定是否发送的请求仍不得按此分支重试。

## 如何判读结果

| 输出 | 含义 |
|---|---|
| slot `completed` | 当前共享生产引擎已有通过原语义与当前attempt来源门的答案；历史版本可能仅作结构校验。均不代表金融结论正确 |
| finalization `completed` | 所选题原检查点存在，delivery 为 `ready` 或 `delivered` |
| `checkpointed_delivery_pending` | 检查点已保存，封包/交付仍有未完成项；按回执逐题处理，不能重问模型 |
| delivery `ready` | 原本地封包完成；尚未声称 StockWiki 导入成功 |
| `owner_authority_verified=false` | 当前 Company 摘要器的能力声明；不是“人类没有授权”的判定，不能因此重复索权 |
| cash cost `null` | 原摘要观察器未提供账单现金成本；公开价估算必须另列，不得写成零 |

真实摘要至少并列公司实体/主体、题目与版本、信息截止日、运行时间、请求与实际模型、新 HTTP/历史复用、usage 完整性、原检索/context proof、原检查点/封包状态、计价日期与估算/账单边界。报告中的 runtime summary 应与原导出 sidecar 逐字段一致，不由报告另算一套数字。

## 本轮验收与剩余边界

工程源码：最初封存/预算scope为IQS `23a05c8`、StockQA `8af0c86`；后续原观察库能力为StockQA`f88b53e`（59项），评分语义及来源门为IQS`1730023`/`854ed55`、Company`73d342b`（54项），严格singleton恢复为StockQA`24fc22f`（92项，格式后23项是其子集）。Company无remote，仅本地提交。早期软件scored正例1 passed及29/36项回归不替代真实样本；测试重叠不相加。精确源码、独审与原始XML在`docs/implementation/reviews/reconciliation-production-2026-10-25/`。

真实隔离实验使用原冻结24题中的 CATL `IQS_05`，截止日2026-10-18，DeepSeek Search + 开启思考的 `mimo-v2.6-pro`。本轮真实safe→中断→禁网恢复→同CP双封存→只读摘要已通过工程验收，源修IQS733186c/Company803ff51。新调用1search+1model，本代公开价估算5894micros，累计25023micros；现金账单unknown。最终实际证据见本轮薄归档与根PWF。不得据此宣称新版全题库、全股票池、agent 自主搜索或金融准确性已全部验收。

generation2的真实负例确认：传给SDK的context和原hash保留完整查询参数，模型输出删了两条URL的query，原来源门拒绝正确。提示应要求来源URL逐字复制（含query/encoding/fragment），不能“清洗”或猜测canonical URL。特别不能统一删`lang/type`等参数来制造匹配。旧评分结构合法并不使这份引用错误的答案自动有资格封存。该代次无检查点，原safe和费用保留；后续修答必须按原known-response协议等待真实lease到期，不能用无resolution记录的提前fail来破坏retry_unusable_answer接续。

临时测试库和源码副本结束后清理，并保留独审、哈希、请求/费用薄证据。真实隔离运行若仍需恢复，应保留其完整工作状态供本地审查；不将数据库、回答正文、context 全文、密钥或思考正文推送远端。
