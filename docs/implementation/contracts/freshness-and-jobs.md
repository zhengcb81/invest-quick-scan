# 字段时效、逻辑待办与状态转移契约

**任务**：C04 · M0 · Owner `iqs`  
**契约版本**：1.1.0（本地参考规则，不执行持久化任务）  
**关联约束**：I08、I09、I12  
**验收**：TIME-01—09、JOB-01、JOB-08  
**机器契约**：[work.schema.json](../../../schemas/quick_scan/work.schema.json)  
**参考实现**：[work_contract.py](../../../scripts/work_contract.py)

**W03 局部 v2 扩展**：身份绑定观察的独立结构契约见[observation-v2.schema.json](../../../schemas/observation-v2.schema.json)和[W03 第一段交接](../reviews/W03/work-observation-v2-first-segment-2026-09-26.md)。本页原 C04 v1 规则与测试继续作为历史读取参考；v2 尚未接入 StockWiki/StockQA 生产库。

本契约定义字段何时可复用、逻辑问题如何去重、状态如何接续。`work_contract.py`只实现无网络、无文件写入的纯判断，供将来的StockQA/StockWiki适配和测试使用；任务领取、SQLite事务、提供商调用、回执传送仍归各自项目拥有者。

## 时间字段各自回答不同问题

| 字段 | 含义 | 能否刷新旧观察 |
|---|---|---|
| `information_as_of` | 公司事实对应的实际日期/期间端点；不知道时为null | 否。缺失时不能称fresh |
| `published_at` | 所引用来源首次公开的UTC时间；只存来源元数据 | 否。严格历史查询要求它不晚于截止日；未知发布时间不能证明当时已知 |
| `answer_started_at` / `answered_at` | LLM请求实际开始与返回的UTC时间；无执行时为null | 否 |
| `valid_until` | 按字段时效策略算出的UTC有效边界；未知时为null | 否。只有`now < valid_until`才未过期 |
| `imported_at` | 这份不可变观察第一次写入结果库的UTC时间；重复导入只追加ACK/投递事件 | 否 |
| `checked_at` | 本观察对应的复核事件时间；后续复核追加新事件，不改旧观察 | 否。单纯复核不产生新信息 |
| `event_invalidated_at` | 已确认的重大事件使观察提前失效的UTC时间 | 会提前失效；不改原观察 |

时间字符串必须带`Z`或`+00:00`，日期精度字段可以是ISO日期；已有开始时间不能晚于回答时间，回答时间不能晚于首次导入时间。发布日截止按UTC当日结束解释。公司文档和网页正文不进入此契约；最多保留URL、标题、日期和短claim。期限策略以后由中央字段注册表提供，C04不在skill里臆造统一TTL天数。

`freshness_status(meta, now)`仅作当前时点判断：没有信息日期/有效期返回`missing_date`；失效事件已发生返回`event_invalidated`；`now`早于边界才是`fresh`，到边界即`stale`。复用还要求问题含义、路由、刷新代次和作用范围匹配，且检查等级达到本次要求。信息日期较旧并不由导入时间变新。

`field_freshness_preview(field_metadata, now)`按字段ID排序，分别调用上述规则，并返回每个字段的状态/刷新标记、`refresh_needed_fields`列表及固定的`dispatch_started: false`。相同输入和UTC时钟必须给出相同输出，且不得修改输入。它只是纯本地缺口预览，不建work、不写数据库、不调HTTP/LLM，也不替代W06拥有的实际刷新调度。

严格回溯查询另用`source_available_as_of(published_at, cutoff)`：公布时间缺失或晚于截止日，该来源不能支持当时已知的结论。今天的LLM回答不能被倒填为过去的认知。

## 字段级增量与刷新代次

每个既有字段独立判断有效性。健康字段仍有效、只有风险题过期时只补风险题；新增题/新增分部仅为新适用范围建待办。比较阈值、排序和页面筛选是本地操作，不能触发模型。全局题库版本号改变本身不让全部旧观察失效。

观察只有在问题语义指纹、路由指纹、`scope`与`scope_id`一致，且`check_level`达标时才兼容。复用还要求其关联WorkItem的字段刷新代次与当前期望一致。题义/锚点/适用范围改变时，为受影响字段增加刷新代次；用户强制刷新也显式增加该字段代次。普通run、scan、模型fallback、重启或改白名单阈值不会加代次。代次属于WorkItem与观察引用关系，不改写原观察内容。

WorkItem还必须与身份对象交叉核对：`analysis_subject` scope的`scope_id`只能等于权威`analysis_subject_id`，且必须绑定其`analysis_subject_revision`；`entity` scope的`scope_id`只能等于自身法律发行人`entity_id`；`security` scope必须引用该发行人实际拥有的Security；`segment` scope必须引用其分部。经营画像题默认以明确的AnalysisSubject为范围，证券报价题则明确使用Security/Listing。集团关系不自动构成AnalysisSubject成员。仅通过work schema而未核对身份图和报告范围的待办不得派发。

v2 新派发必须从 StockWiki 权威库取得独立的当前身份投影：准入状态、Entity ID、身份修订、来源绑定版本、当前绑定集、证券到绑定的映射和分部归属。传入的 WorkItem/LLM 答案不能充当该投影。`provisional` 只允许 `eligible_provisional` 的单来源证券；`verified` 只允许 `eligible_verified`。来源绑定/资格被撤销后不能创建新 work。`validate_work_item` 与 `transition_work_item` 明确拒绝 v2，防止旧状态机在没有权威投影时派发。

## 两种键，不要混成一个

**逻辑待办键**为：

```text
(entity_id, analysis_subject_id, analysis_subject_revision, question_id, generation, scope, scope_id)
```

W03 的 v2 逻辑键在上述各项之后明确追加 `identity_revision`、`source_binding_version`、`identity_state`、排序且唯一的 `source_binding_refs`。身份、并表范围修订或来源绑定变更时，即使题目与原 `generation` 不变，也不能命中旧待办或旧请求缓存；owner 同时应提高受影响字段的 `generation`。`source_binding_version` 是 StockWiki 按 Entity 维护的绑定集单调版本，不是来源证券代码或模型推测字段。升级后新写入协议必须锁定 subject revision；旧五元键/旧v2键只用于历史兼容，不能推导或补造缺失的分析范围。

v2 观察到达时，可先用 `validate_observation_identity_v2` 核对已持久化 work 与 attempt 的身份/执行外壳；这个检查不能替代冻结题包、答案语义、真实联网回执和 StockWiki 接受回执。`observation_identity_is_current` 对缺任一独立权威凭据均返回 false，包括尚未实现的 v2 内容校验凭据。`insufficient_evidence` 等未知态即使错误夹带数字，也绝不参与当前分筛选；旧身份结果只保留在历史时间线。

`generation`是该逻辑字段/作用范围的刷新代次，不是股票池批次序号。实体级题用实体ID，估值等证券级题用证券ID，分部题用分部ID。A/H双挂牌的公司经营题共用一条实体待办；不同币种/证券的估值题不会撞键。同一逻辑题出现在多个`run_id`/`scan_id`时关联既有work并记下调用来源，不能重复创建/收费。新代次仅发生在该字段失效或用户明确刷新时。

**请求缓存键**标识某一次具体请求，至少包括逻辑待办键、规范prompt/输入hash、题义和路由指纹、截止日、搜索能力、实际目标provider/model。fallback的具体尝试可以改变缓存键与attempt记录，但不会改变primary逻辑待办键。`run_id`、`scan_id`、attempt及provider/model不作为逻辑去重键。

## 状态与安全接续

| 状态 | 含义 | 允许的去向 |
|---|---|---|
| `pending` | 等待领取，尚未开始外部请求 | `leased`、`cancelled` |
| `leased` | 单一worker持有租约；记录每次实际尝试 | `result_ready`、`uncertain`、`failed`；只有已证实未发出请求才能退回`pending` |
| `uncertain` | 请求可能已发出/计费，当前未取得可靠结果；绑定唯一attempt和request缓存键 | 同一attempt对账后转`result_ready`/`failed`；只有证明未发送或未执行才可退回`pending` |
| `result_ready` | 有效结构化回答和不可变observation已持久化，等待投递ACK | 仅匹配work ID、观察hash且`accepted`的ACK可到`delivered`；失败只重投，不重新询问 |
| `delivered` | StockWiki已确认接收该ID/hash；另记录独立的`response_status` | 该work为终态；不同hash必须报冲突，不能覆盖 |
| `failed` | 已确认的终止错误，记录类别/尝试，不抹掉已发生费用 | 重试有资格后回`pending`，或人工取消 |
| `cancelled` | 未派发待办已撤销 | 终态；不删除已有观察 |

```text
pending -> leased -> result_ready -> delivered
                   |       ^
                   |       | 同一attempt迟到响应/对账成功
                   +-> uncertain
                   |       +-> failed / pending（仅凭明确对账证据）
                   +-> failed
已投递的资料不足答案 -> 查询返回`deferred_unknown`（不派发） -> 到期后建立新generation
```

租约过期不能证明没有收费。无法区分请求是否已经发送时必须进入`uncertain`并先对账，不能换模型竞速重问。worker取消只阻止尚未派发的工作；已发请求仍接受回执并记账。`result_ready`的网络导入失败不回退到模型派发。未知答案需要记录`response_status`与`next_retry_at`；回答/投递状态仍走`result_ready`→`delivered`。ACK的item/hash/status任一不匹配均保持`result_ready`。

`uncertain`是请求的执行结果不明；`insufficient_evidence`是已收到且可投递的答案；`deferred_unknown`是读取历史答案/冷却记录后，由调度查询返回的“不派发”决定。它不是可变WorkItem状态。冷却内不创建任务；冷却到期按该字段递增generation后再创建新逻辑待办。已投递观察永不被改写。状态转换参考实现要求同一attempt的恢复证据、有效的冷却截止或匹配ACK；不能只凭调用方传一个目标状态跳转。

## 本地行为验证

```powershell
python -X utf8 -m unittest discover -s tests -p test_freshness_and_jobs_contract.py -v
python -X utf8 scripts/implementation_plan.py validate
```

契约测试调用`work_contract.py`的纯规则并按格式校验真实schema；不把测试内自造的状态机当作生产队列，不访问其他项目。运行器/数据库/并发/断电故障的生产验收仍分别属于StockQA或StockWiki卡。C04通过不能替代C05/C06/C07和G0冻结审查。


## Q15 两阶段授权与attempt恢复（实施边界）

WorkItem租约和provider attempt分开记录。StockQA为每个work维护单调attempt ID、route/policy hash、permit ID、费用预留状态、`send_intent_prepared`、W16 `dispatch_commit` receipt、transport结果、ACK及对账状态。一个work最多允许一个有效或outcome_unknown attempt；同run重复点击、worker抢占或fallback都不能生成新的逻辑work键。

StockQA先本地耐久写入`send_intent_prepared`，再调用StockWiki W16 `consume_dispatch_permit`；W16在一个owner事务中重新核对active ReleaseSet和每个组件的资格revision、消费一次性permit并返回耐久`dispatch_commit`。此回执是跨仓派发授权线性化点。consume前过期或资格变化直接拒绝；consume后最多允许原attempt一次POST，即使随后退役也只结算该承诺。permit未消费时重启后不可重放；consume后无法证实请求未发出则标`uncertain/outcome_unknown`、保留预算，不自动新建attempt。

只有明确未发送，或provider给出冻结策略认可的terminal retryable拒绝并完成费用/搜索账本对账，才允许创建下一attempt；其ID递增、预算重新原子预留、资格重新核验、发包再走新permit。结果成功、unknown、费用未知或ACK失败都不允许借“切换模型”重复发送；ACK重试只投递同一observation/hash，不产生模型调用。
