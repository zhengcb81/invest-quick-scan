# 轻量交换、结果查询与研究交接契约

**任务**：C06 · M0 · Owner `iqs`  
**契约版本**：1.0.0（本地协议定义，未实现跨仓端点）  
**机器契约**：[exchange.schema.json](../../../schemas/quick_scan/exchange.schema.json)、[query.schema.json](../../../schemas/quick_scan/query.schema.json)  
**样例**：[quick_scan fixtures](../../../examples/quick_scan/)  
**离线参考规则**：[exchange_contract.py](../../../scripts/exchange_contract.py)  
**验收**：DB-02、DB-03、DB-06、DB-07、QUERY-01、QUERY-02、QUERY-04、FACT-01、CONS-05

本契约冻结边界和报文形状，不代表 StockWiki 或 StockQAbyLLM 已实现事务、HTTP/CLI端点、持久化队列、认证或真实消费者。此目录只定义题库和交换格式；不创建第二个权威库、不保存公司文件或网页正文，也不实现LLM客户端、检索或模型分派。

## 1. 唯一写入者与轻量数据边界

| 数据/行为 | 唯一拥有者 | 本契约规定的边界 |
|---|---|---|
| 经核实的证券身份主档 | company-wiki（只读来源）/身份契约拥有者 | 可提供证券身份快照；快扫不要求先有公司文档目录 |
| 股票池成员、quick_scan观察、导入ACK与筛选快照 | StockWiki | 唯一可写轻量库；独立命名空间，不与研究文档库混写 |
| 联网LLM提问、搜索、路由、费用、任务和模型实际标记 | StockQAbyLLM | 唯一问答执行者；对外只导出轻量观察包/outbox |
| 问题/评分含义与报文契约 | invest-quick-scan | 本目录维护schema、样例、校验和离线参考规则 |
| 产业链/行业研究读取及刷新请求 | 研究消费者 | 通过版本化只读查询协议获取；刷新先预览并单独确认 |

两项目不得共享可写数据库、交换内部路径或互相修改私有表。包/查询响应是轻量数据传输，不是StockQA的第二个持久库或StockWiki的第二套可写状态。快扫观察保留已有标准Observation、答案和时间/模型字段；不带PDF、原始财报、网页正文、正式source manifest、evidence span或证据接受标记。URL、标题、日期及短依据只是回答元数据，不等于归档链接内容或正式证据通过。

下一版生产Observation与查询profile还必须区分法律发行人与快扫研究范围：新增`analysis_subject_id`、`analysis_subject_revision`、`primary_issuer_id`与范围类型/coverage；旧Observation保持原样，只作历史读取，不静默合成subject。经营答案按subject修订比较，证券/挂牌报价答案继续按`security_id`/`listing_id`比较。该字段进入C04/C06实施前，不得声称当前生产协议已经具备报告范围绑定。

## 2. 交换包、散列与版本

`ExchangePackage`由StockQA产生，每包1—100条完整Observation。`document_payloads_included`必须为`false`；`data_class`固定为`lightweight_screening`；生产者、消费者命名空间、必需能力和依赖契约版本都显式列出。当前schema拒绝未知顶层字段和未知schema版本；v1.0.0的`extensions`固定为空数组（`[]`），禁止借任意嵌套字段夹带正文或二进制。新增可选能力必须先定义具名、限长、版本化的轻量Schema，分配稳定`capability_id`、定义负例兼容行为并更新协议版本/能力清单；消费者不支持必需能力时整条对应记录拒绝，不能猜测降级。

散列规范为UTF-8 JSON、对象键按Unicode码点排序、无多余空格、保留Unicode、拒绝NaN/Infinity。构包参考函数会先深拷贝观察与版本字典，避免调用方后续修改输入使已计算散列失效。每条观察的`payload_sha256`绑定完整Observation；`item_id`绑定`observation_id + payload_sha256`；`package_sha256`绑定完整包体，但计算时排除`package_id`和`package_sha256`本身，`package_id`为`pkg_`加完整小写SHA-256。Schema校验结构；消费者仍须重算散列并核实各ID关系，不能把JSON Schema格式通过当作内容散列验证。

每条Observation独立返回ACK：

| 输入与权威库状态 | ACK | 语义 |
|---|---|---|
| 已验证且观察键不存在 | `accepted` | 插入一次不可变观察 |
| 相同`observation_id`且相同payload hash | `already_present` | 幂等重放，不复制或改写观察 |
| 相同`observation_id`但payload hash不同 | `conflict` / `immutable_key_hash_conflict` | 不做last-write-wins、不覆盖；进入人工/程序冲突处理 |
| schema/实体/题目/payload/来源链无效 | `rejected`及对应错误码 | 不得部分接受该观察 |

ACK需回显package、item、observation、payload hash和目标store身份。真正的StockWiki实现必须在一个本地事务中完成唯一键查重、内容hash比对、插入或冲突决策、ACK/sequence记录；跨库不能用分布式事务假设。丢ACK后可原样重投；若模型已回答而仅导入失败，只重放原包，不重新提问。一个包可以有部分ACK，调用方仅重试未确认item。

StockQA outbox按不可变C06 package/item持久化并重投相同规范化字节，稳定幂等键至少绑定`package_id + item_id + payload_sha256`。发送前先记录耐久send-intent。只有能证明请求未发送的失败才允许重新派发；发送后超时、连接中断或进程崩溃都属于结果不明，必须先从StockWiki取得精确ACK或通过其权威查询对账，不能猜测未导入或自动重新POST。重投同一包/项时，StockWiki按不可变键给出相同`already_present` ACK。`accepted`/`already_present`且所有ID/hash/store精确匹配后，StockQA才原子标记该项已交付；`conflict`/`rejected`记录后阻止自动重试，保留人工/更正路径。

生成完整`Observation`所需的题义/模板版本、cohort、information cutoff及标准答案证据字段若未在已验证快照中提供，StockQA不得从简化answer checkpoint猜补。此时工作仍为`result_ready`，保留持久化的`exchange_package_incomplete`阻断原因；补齐适配器后才能建立C06 outbox。离线或mock outbox测试须使用完整有效的C06 fixture，不能把简化checkpoint包装后声称真实StockWiki导入已验收。

## 3. 查询信封、覆盖和固定快照

请求/响应均携带`schema_version`、稳定`request_id`、`operation`与UTC时间；消费者用operation对应的payload/result结构，不得接受类型漂移。`capabilities`先报支持操作、能力、协议版本、市场范围和当前coverage；缺少需要的能力时应显示不可用，不能把“无结果”解释成“市场没有公司”。

`search`最多每页100个实体，第一页建立`query_hash + snapshot_id`，后续cursor必须绑定同一个snapshot。结果包括稳定`analysis_subject_id + analysis_subject_revision`、`primary_issuer_id`、公司名/别名、范围类型与覆盖度、证券/挂牌列表、类型/行业/阶段、评分引用、恢复观察状态、事实可用性与最后观察时间。每条分数引用保留question/field、原分、状态、信息日期、回答时间、observation ID、实际模型和检查等级；查询层不得自行求平均、重评分或抹掉unknown。跨模型分数只有消费者显式要求并满足口径对齐时才可比较。

查询响应还执行跨对象语义校验：`ok`必须有结果且coverage完整，`empty`只能对应完整覆盖和零结果，`partial`只能对应部分覆盖；scored引用必须带非空分数、信息日期、观察时间、观察ID、实际模型和检查等级。新profile中的每条经营类Observation必须与外层profile的`analysis_subject_id`和修订一致，并核对`primary_issuer_id`；证券/挂牌观察还须匹配其报价范围，不能仅凭各自Schema通过。

`get_profiles`按最多100个analysis subject批量读取，可选字段、指定同一结果snapshot及包含历史；旧entity键只供历史兼容，不自动合成subject。每个观察仍通过既有Observation schema校验。响应报告缺失subject、所请求字段覆盖、能力和水位。`candidate_set`固化原查询snapshot、规则ID/版本、成员subject和观察ID列表；同一ID不可被后续新结果悄悄改变。读取响应提供`watermark`中的store、snapshot、成员/观察/ACK序号及read时间，方便消费者确认结果范围，不代表多个操作共享可写快照事务。

覆盖状态只有`complete`、`partial`、`not_covered`或`unknown`。0条匹配只有在请求市场/字段覆盖完整时才可返回`empty`；覆盖不完整返回`partial`或`coverage_gap`。显式覆盖错误比“空结果”优先。由此，下游技能不会因数据库尚未扫过某市场而报告该主题没有上市公司。

## 4. 刷新预览与明确授权

`request_refresh`只能提交明确snapshot、最多100个entity、最多200个field、调用方任务ID与原因。StockWiki以权威名单和当前权限检查范围，再返回不可变`preview_id`、规范`scope_sha256`、policy版本、复用/待问字段、估算最高费用、拒绝范围及`requires_user_confirmation`。已有效观察应复用；只将缺失、过期或被事件失效的精确字段列入缺口。消费者无权通过请求自填费用、预算、模型或名单外entity。

预览永不启动派发（`dispatch_started=false`）。确认必须经StockWiki的已认证用户界面/会话单独产生，调用`approve_refresh`时提交preview、确认凭据和稳定幂等键。StockWiki要重新检查权限、scope hash、策略版本及可用预算；变更时拒绝并要求新预览。`accepted`只表示StockWiki已登记/交给StockQA的刷新请求，响应仍声明当前调用没有直接派发；重复确认返回`already_submitted`，scope/预算变化或凭据无效返回明确拒绝。随后的实际发问、费用结算和任务接续归StockQA。浏览、筛选和查询绝不调用模型或消耗费用。

## 5. 提名、冲突、事实和深研交接

`nominate`只创建待核身份的候选，`auto_admitted`恒为false；不能把主题技能发现的名称直接加入成员名单。`report_conflict`只登记人工复核线索，`identity_changed`恒为false；不能由消费者合并/拆分实体。

Fact型Observation的score保持`null`；关系项记录角色、对象引用和观察证据ID，不伪装为数值评分。基础资料未覆盖时返回unknown/coverage gap，不能因空列表暗示没有供应商、客户或下游应用。

`ResearchLead`必须留存原任务ID、实体、所用Observation ID、上游Observation ID、URL指针和交接理由，并且`formal_evidence_accepted=false`。下游深研可沿上游链定位线索，但不能把同一Observation的转述再算作独立支持，也不能把快扫模型检查等级升成正式证据准入。独立支持判断必须遍历完整上游闭包；任一祖先缺失、出现环、或候选链最终包含目标Observation时均保守拒绝。正式来源采集、验证与接受由深研契约拥有者完成。

## 6. 本地验证边界

可复现验证：

```powershell
python -X utf8 -m unittest discover -s tests -p test_exchange_and_query_contract.py -v
python -X utf8 scripts/implementation_plan.py validate
```

这些fixture全部虚构且离线。`exchange_contract.py`只演示内容散列、导入决策、覆盖状态、精确范围预览和来源链防重复规则，不写文件、不连网、不执行事务或发模型请求。离线通过不等于StockQA outbox/StockWiki数据库端点、真实查询/UI、权限确认、消费者接入或一键启动已经交付；相应真实owner测试与独立审查仍须通过后才能verified或release。
