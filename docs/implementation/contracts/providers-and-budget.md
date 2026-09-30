# 有序模型、故障分类与费用边界契约

**任务**：C05 · M0 · Owner `iqs`  
**契约版本**：1.0.0  
**配置Schema**：[model-policy.schema.json](../../../schemas/model-policy.schema.json) v2.0.0  
**用户模板**：[model-policy.template.json](../../../examples/model-policy.template.json)  
**离线验证器**：[model_policy.py](../../../scripts/model_policy.py)  
**相关验收场景**：LLM-03—06、LLM-10、BUD-01—04、PAR-01—03、PAR-06—08

本契约冻结调用策略与费用账本语义。配置的导入、模型/搜索执行、配额状态、费用预留和持久化仍由StockQAbyLLM独占。本skill只保留无密钥的可填写模板、schema、离线配置检查和此契约；schema/模板通过不能证明提供商可用、搜索已发生或运行时严格遵循策略。

## 模型顺序和派发

`models`数组中启用的路由从上到下就是用户给出的优先级。StockQA每个logical work首先选择顺位最高、已启用、具备该问题所需能力且不在故障/额度冷却中的路由。题目要求联网搜索时先核对路由搜索能力；不支持的路由在发包前跳过并记原因。首选路由仅因并发槽满时必须等待；容量不足不是降级理由。不能为抢速度向多个模型同时发送同一primary问题。

primary work沿用C04的逻辑键，键中不含模型、attempt或run。遇到符合策略的失败后，按顺序尝试下一个有效路由。一个派发轮次的`max_attempts_per_dispatch_round`包含该轮内所有实际发送，不包含纯本地能力检查；到上限就持久化`retry_wait`及下次资格时点，重启不能重新开启轮次。每个题目最多只有一个重试预算拥有者，skill、StockWiki和StockQA不可叠加各自的重试循环。

成功收到符合输出契约的回答后立即停止primary fallback。有效低分照常保存，不能为找更高分调用备用模型；有效的`insufficient_evidence`等unknown也作为带缺口的回答接受，并按字段冷却规则安排以后复查，不应在当前轮次追问全部模型。备用模型成功不证明首选模型恢复；只有针对首选路由的健康探测或明确可验证的恢复事件才能解除首选冷却。

## 故障分类

| 故障/结果 | 路由动作 | 费用和恢复记录 |
|---|---|---|
| 明确的共享账户额度耗尽 | 冷却整个`quota_group`，按顺序跳过同组路由后尝试下一可用组 | 记录原始拒绝类别、组、观测时点、reset值与来源；只有提供商明确给出的reset才能当精确时间 |
| 普通429或短期限流 | 尊重`Retry-After`并做有界等待/重试，达到策略上限后再考虑下一路由 | 不把普通429推断为五小时额度耗尽，不编造剩余额度或reset时间 |
| 5xx/临时服务错误 | 按统一attempt上限做有界重试，之后再顺序fallback | 每个实际发送都计入请求数和费用预留 |
| 认证/权限错误 | 禁用出错路由，直到配置修复或独立恢复检查通过 | 不对相同凭据错误无限重试 |
| 全局坏请求/参数错误 | 停止当前派发，不遍历其他模型 | 这是请求/调用方问题，不得把错误广播给全部提供商；保留可诊断错误类别 |
| 缺少所需搜索/输出能力 | 发包前跳过此路由，再检查下一顺位 | 不记作已发送请求，不消耗请求预算；能力检查结果和版本需留记录 |
| 结构错误/无法解析的模型响应 | 有界重试，耗尽后再fallback或标为结构失败 | 每次实际发送计费；不得把无法解析的外层默认值改造成有效分数 |
| 超时、断连或发送后结果不明 | 按C04置为`uncertain`，先用相同attempt/request ID对账；未澄清前不能并行发送备用请求 | 保留费用预留；未确认成本不得记为零。提供商不支持幂等/查单时保留重复收费可能性 |
| 有效低分或正常unknown | 接受并停止本轮fallback | 记录原答案及其缺口；以后是否重问由字段刷新代次与cooldown决定 |

无已知恢复时间的额度组使用配置的有界冷却时间，并在冷却结束后用持久化组锁执行至多一个半开探针。两个worker不能各自探测；探针失败则延长冷却，成功才恢复该组普通派发。若所有路由均不可用，保存`waiting_for_provider`并退出本次有界运行，不能忙轮询。

## 并发与共享额度

适用的同时在途上限取全局、共享账户组、单路由三个上限的最小值。模板的全局4、每账户组2和单路由配置仅为保守示例，不代表厂商额度。共享同一账户的不同模型必须引用同一个`quota_group`；换模型名不得绕过同一账户熔断。跨进程槽位、冷却和派发租约必须由StockQA的持久化协调器原子管理。

不同logical work可以并行。相同primary work只能由一个有效租约发出；fallback不创建新logical work。若首选模型仅仅满槽，当前待办等候首选槽位释放。`speculative_racing`固定为false。显式对照实验遵循单独的比较配置和预算，不是primary racing的变体。

## 费用上限、预留与结算

`budget.max_cost`和`budget.max_requests`是整个有效策略期间的硬上限，StockQA账本跨run、进程重启、模型fallback和共享账户保留；`reset_on_restart`必须为false。每次实际发送前，StockQA在同一原子事务里领取logical work、适用并发槽，并按`max_cost_per_attempt`或当前已验证费率卡预留费用。若总费用、请求数、comparison子预算任一不足，则不发请求，待办留存。

一个账本纳入输入/输出token、搜索工具费、失败请求、格式重试、fallback及模型comparison。预算不能只统计成功回答。`cost_policy`必须明确采用当前StockQA费率卡引用或用户填写的保守单次费用上限；此配置不复制厂商价格表，也不能把示例价格当实际价格。搜索收费必须包含在所用费率或保守上限内。

收到提供商费用回执后，按实际值结算预留并写清计价引用、币种、请求ID与策略版本。实际费用未知时保留预留并暂停后续派发/人工对账；不能释放预留、按零费用继续，也不能为了“精确”估计而写入未经验证的单价。结果不明时，费用可能重复的边界必须如实记录；没有提供商幂等或查单能力时不承诺零重复收费。

比较预算是全局上限内的独立子上限，primary和comparison各自还须通过共享总额原子预留。comparison开启时须至少设置正的费用与请求数上限，且不超过总预算。任何预算编辑都形成新策略版本，既有消费不被清零。

## Primary fallback与显式模型比较

默认模式只选择一个有效成功答案；fallback是故障恢复路径，绝不是多模型投票。显式comparison必须在运行前设定模型数、请求上限和费用子上限，并为同一实体/题目/题义版本/截止日/搜索条件及共同输入分别创建可恢复的模型请求。各指定模型独立记request/attempt/费用，遵守同一全局、组和路由限制；指定模型不可用时保留缺口，不能暗中用另一模型替代。

结果以模型实际回报身份为准。若实际型号未报告或不能核实，保存`unknown`及可用的请求身份，不把请求型号伪装为已确认的实际型号。comparison结果标记为对照，不自动覆盖primary观察、不取最高分或平均分，也不改变已完成primary问答。

## 配置变更、版本与升级

StockQA导入每份有效策略时生成不可变`policy_version`和hash；模板中的`policy_id`只是用户标签。默认在下一run生效。若用户明确要求立即生效，必须在logical work派发边界原子切换：已发送attempt继续沿用原版本，只有未派发待办使用新版本；新排序不使成功观察失效，不创建新代次。设置页、CLI和执行器只能读写StockQA的唯一有效配置，不维护第二份优先级。

本次schema从1.0.0升为2.0.0，因为费用策略、能力、对照预算和更细的失败分类成为必需字段。旧配置不得自动补成已授权策略；迁移时显式补齐`required_capabilities`、`cost_policy`、`max_cost_per_attempt`、新的错误动作和`comparison`，复核总预算后再由用户启用。示例仍是`configured=false`、所有模型禁用、预算为0，不得用于发送。

## 离线检查范围与待生产验收

运行`python -X utf8 -m unittest discover -s tests -p test_model_policy.py -v`及`python -X utf8 -m unittest discover -s tests -p test_providers_and_budget_contract.py -v`，可验证模板/schema/跨字段界限和契约常量。`python -X utf8 scripts/model_policy.py --input examples/model-policy.template.json`只做结构检查；不调用provider，不证明搜索执行、并行重叠、跨进程原子预算、失败后的fallback或热更新边界。

LLM-03—06、LLM-10、BUD-01—04及PAR-01—03/PAR-06—08在本卡冻结预期和离线配置边界；实际ProviderCascade生产接线、真实请求账本、重启、多worker与健康探测仍由StockQA后续任务实现并验收。C05通过不能标记这些生产场景已完成，也不能替代C04独立审查或M0的G0冻结审查。


## 1.9.3 备用路由必须由attempt终态驱动

模型顺位先后与attempt生命周期是两个维度：并发槽满时等待当前首选，不能fallback；只有冻结策略认可的provider故障才允许进入下一顺位。下一attempt仅能在上次请求被明确证明未发送，或provider已返回策略认可的retryable terminal结果且账本完成费用对账后创建。fallback使用新的单调attempt_id、重新预留共享预算，并通过W16获得新的permit/consume/dispatch_commit。HTTP结果不明、超时或consume后崩溃若可能已经发送，必须保留预留并进入`outcome_unknown`，只允许同attempt查单/对账，不能换模型抢答。成功答案即停止顺位；低分、unknown或搜索证据质量不足不构成fallback理由。

StockQA本地`send_intent_prepared`必须在传输前耐久记录，但只有StockWiki W16 consume事务的匹配`dispatch_commit`回执授权一次POST；这用于跨owner数据库无法原子提交的边界。permit发出后未consume不可重放；consume成功后最多执行一条POST。细节和组件资格CAS见[全项目可组合演进设计](../composable-evolution-plan.md)及I46/I49/I50。
