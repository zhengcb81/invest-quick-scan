# 在原账本保留旧暴露，明确批准独立新实验

日期：2026-10-18。此文是总控下一大节点的实现输入，不是已交付功能，不授权任何请求，也不是外包卡。只读原源码和原 S1 SQLite；零 API、零真实库写入。主 PWF 由总控维护。

## 1. 结论与实际可行的最小范围

新增一个原生 **repeat-exposure 能力**：当前真实 owner 在原 namespace 中，明确接受指定旧预算请求尚未对账、原研究范围无法证明的暴露，同时批准精确的一组独立新 cohort/SubjectRef/题目/模型/实验控制和最大新 HTTP 数。执行仍使用同一个原 SQLite、原预算表、原 SDK 和原每 POST owner 守卫。

这不是恢复或重发旧 intent，不是将未知费用改成零，也不是借新 task ID 宣称无重叠。由于旧 S1 无原生 work 关联，无法证明新旧公司或题目不同，批准必须明确写 `unknown_reference_scope`，不能写 `disjoint`。能力缺失、旧版本、普通批准、仅委托 agent、调用者传 `independent=true`，一律维持现有全局暂停。

初版只处理历史 **budget-only** 暴露，要求 `work_attempt_id IS NULL`，旧原 work/pack/intent 不可被目标 cohort引用。本次真实 S1 满足该分类。若存在原生 owner work 的未决同题，仍由原 `guard_unresolved` 拒绝；不为本次预算功能扩大原比较/重试权。已知结果的比较继续原 work decision/新 generation 路径。原生未知 work 的明确重复实验若未来必需，应单独扩展它自己的 owner work decision，不能复用这里的 budget-only 豁免。

## 2. 已核的真实基线

精确只读报告：本目录 `real-baseline-readonly.json`。原库为 `runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite`，SHA256 `79ae4b84e293a63c762025e326753d78d998e6a5a2d54b5d83245923f03ae85e`；检查前后相同。schema20，未见 WAL/SHM/journal，100 个 budget attempts，`work_item` 零行。

| 分类 | 数量 | 已知实际费用 µUSD | 未决预约 µUSD | request_counted | 原 in_flight |
|---|---:|---:|---:|---:|---:|
| settled | 98 | 655435 | 不再计为未决预约 | 98 | 0 |
| response_unpriced / HTTP200 | 1 | NULL | 100000 | 1 | 0 |
| outcome_uncertain / HTTP未知 | 1 | NULL | 100000 | 1 | 1 |

两个待明确接受的原请求：

- `DISPATCH_86004529874040469881f32f71aa5a55`：HTTP200、无已知实际费用，必须保留 response_unpriced。
- `DISPATCH_a11c198286874b70a7fa6de11af144ee`：HTTP未知、无已知实际费用，必须保留 outcome_uncertain 和原 in_flight=1。

原 policy `company-agent-s1-20261015` / `t2-reviewed-v2-20261016`：25 USD、350 requests、每次预约0.1 USD、全局并发2。当前记账暴露为0.655435+0.2=0.855435 USD，原请求累计100。**当前小实验并不需要改大原预算上限**；还有250个请求槽，但它们不是权限。不得把0.855435称为完整账单或实际费用上界。

## 3. 为什么现有 API 不能直接做

1. `src/utils/quick_scan_refresh_inspect.py::inspect_refresh` 在 quote 中硬编码 `unreconciled_attempts == 0`。因此仅改发送准入，正常公开 preview/确认也不会到达发送。
2. `src/utils/quick_scan_work_store.py::_reserve_budget_attempt_tx` 对 policy 内 unpriced/unknown 全局暂停。它明确拒绝 `independent_task` 与非空 `work_attempt_id` 同时使用。
3. `quick_scan_uncertain_seal.py::seal_uncertain` 的 SQL trigger 和 Python 检查只接受 budget-only、HTTP未知的 outcome_uncertain；HTTP200 不满足。其 review 本身不认证 owner。
4. `amend_research_budget` 明确拒有 owner work 或非 sealed-unknown 的未决账；不能借它清除当前 HTTP200 unpriced，也不能只换 policy version 越过 `_ensure_budget_policy_tx`。
5. `quick_scan_owner_refresh_journal.py::guard_unresolved` 横跨全部代次检查同 entity/question/scope，原 comparison 仅允许已认证 decision 指向的 result_ready 源；task/cohort/generation 改名不是豁免。
6. 原 generic intent 表 `(task_sha256,intent_sha256)` 是物理请求关联，不是独立性或授权证明；仅换 task 内容可改变 hash，不能拿 hash 自证可重发。
7. 外部 search continuation 仅允许原研究矩阵中未派发差集，且 production_owner_verified=false。不能冒用为本次 owner 模型工作权限。

## 4. 与当前委托确认的交接

独立作者正在实现的原委托能力保持不变：`rc2` → `stockwiki.refresh_confirmation_record/2.0.0`，method=`native_owner_delegated_agent`、delegation=`stockwiki.refresh_delegation/1.0.0` → 原固定 CLI `stockwiki.refresh_approval_inspection/1.2.0`。它返回原 `ApprovedRefreshSession`，其 `owner.check()` 仍经原 bridge.inspect(current_permissions)，POST 前重核 namespace/撤销/期限/OS owner 和精确 action。

新的最终实验发送批准复用这一个原批准对象和原 record，不复制 grant、不相信消费者 JSON。权威读取必须沿 `ApprovedRefreshSession` → 原 inspect 验证 → `proof['confirmation']['delegation']['binding']` 及原 action/preview/owner policy 的完整绑定；确认来源可为原 TTY 或已经正式交付的明确委托。**委托单独只允许谁执行，不表示接受旧 unknown、不表示放宽同题 retry。**

**必须增加 quote 之前的原生 exposure control，打破循环。** 当前委托grant要求真实ready preview，旧preview却被unknown阻断，不能让同一个尚不存在的grant自举。采用两阶段原owner控制：先由原namespace固定owner配置中的精确 exposure acceptance 条目，经原公开固定CLI独立安装原生 exposure decision；它不依赖refresh quote、不发送请求。再由新quote读取这个真实已安装decision重算，最后原TTY/委托grant确认新quote和完整refresh action。两阶段是不同的能力用途，不是复制委托grant。

第一阶段不能只在配置中放enable=true。原owner受控配置条目本身必须给出旧refs逐行预期、新future-request核心/精确cohort/cells、原ledger/policy、有效期、最大新增请求、unknown范围/费用明确接受及来源操作记录。安装器通过原namespace/OS owner principal/固定配置位置和权限边界校验条目，调用者只能选原配置中的ID，不能传自由JSON作为权威。当前用户已给后续全部权限，后续实施可据此具体建立原受控配置并安装，不必再次询问；但这一步未实施前不能假称已有能力。与原委托设计一样，同OS账户过程不具密码学独立身份，必须如实标 `native_owner_config_acceptance`，不能伪造人类TTY。

第一阶段的原记录建议 `stockwiki.budget_exposure_decision/1.0.0`，原StockWiki namespace append-only保存；固定CLI新增 `install-budget-exposure`/`inspect-budget-exposure`（命名拟定，挂在原owner CLI），使用原policy/principal reader，其inspect无需ready refresh preview。StockQA只从固定原bridge读取并验证该原记录与当前owner配置，原ledger原子登记对应projection。它只解锁指定future action的预算quote评估，不直接授权POST；真正POST还必须取得后阶段原 `ApprovedRefreshSession`。

future request绑定需避免decision自引用：原生规范定义 `future_request_core` 为原完整1.4 request仅移除 `continuation_decision_ref` 这一个已知字段，纳入全部其他scope/题目/模块/模型/cohort/控制/ledger/policy字段。第一阶段绑定其canonical完整内容与digest，安装后把生成ref放回构成完整request。最终确认绑定完整request和真实新quote；不能任意排除字段或只看hash。

新决策须由原 namespace 的 owner 能力策略允许；不是发现 delegation 字段就默认开启。当前作者尚未完成验收，因此本设计不声称其能力已交付，不写入其独占目录。

## 5. 最小版本与配置

不要修改旧协议解释。建议下一节点在现有1.3 dialect之后新增明确1.4 dialect：

| 合约 | 新增内容 | 旧版本行为 |
|---|---|---|
| `stockwiki.refresh_owner_policy/1.4.0` | owner配置允许 `budget_continuation=explicit_legacy_exposure`，限定原ledger、policy、目的、精确目标和新请求上限 | 1.0–1.3不允许 |
| `iqs.refresh_request/1.4.0` | 请求原生 `continuation_decision_ref`/精确cohort，不携带authorized布尔值 | 原字段/语义不变 |
| `stockqa.refresh_inspection/1.4.0` | 保留全局raw状态，仅对真实已安装exposure decision新增 eligibility 和完整保留暴露投影 | 旧quote仍因unreconciled暂停 |
| `stockwiki.budget_exposure_decision/1.0.0` | quote之前原固定owner配置接受的精确暴露/未来action记录 | 不由普通request/委托grant自举 |
| `stockqa.owner_budget_continuation/1.0.0` | 原批准生成的append-only决定，绑定旧请求、目标、保留暴露与权限来源 | 不由旧reader猜读 |
| `stockqa.owner_refresh_binding/5.0.0` | 同原work绑定一个已原生登记的continuation decision ref；保留原subject/work控制 | 旧1–4不获得豁免 |

这些是**拟定版本**，须以实施时实际已交付注册表检查无冲突后固定；不要机械提升所有无关合约。委托 record2.0 / inspection1.2无需重做，新增请求/quote应由同原确认绑定器完整覆盖；若它显式仅接受旧dialect，应增精确已知新dialect，不扩大通配兼容。

原 `quick_scan_model_policy` 和费用 policy 首版不需要改值。owner策略的能力开关应在同原配置/原schema中明示，缺省全局暂停；配置开关只是 owner可批准的能力，不等于任何请求已获批。

## 6. 原生决定必须包含的内容

决定由上述第一阶段原owner控制链安装，最终实验批准再绑定它；不接受任意 dict 直接注册。建议至少：

- 原账本 deployment/store身份与规范绝对路径、policy ID和精确当前snapshot；path hash本身不认证身份，需原配置与固定registry共同核对。
- 第一阶段原owner配置记录/namespace decision ref、future_request_core、owner-policy ref及原有效来源、权限版本、有效期、撤销key；之后原注册关联第二阶段完整确认record/preview/request，未有关联前不得POST；每次重核原当前权限。
- exposure mode=`explicit_repeat_exposure`，reference_scope=`unknown_reference_scope`，purpose=`independent_comparison`。
- 两个或更多精确旧 budget_attempt refs；逐行冻结原 status/HTTP/request_counted/in_flight/reservation/actual=NULL及原可用receipt hash。不能只保存一串IDs或总账hash。
- 明确 `no_retry_original_intents=true`、`unknown_cash_remains_unknown=true`、`retained_original_requests=true`；这些是原决定中的承诺，不能单独作为调用参数生效。
- 旧本地 sender 已停止/不会自动恢复的原运行登记与停机审查证据；原未知远端是否完成仍未知，不将“本地停机”当作服务端未执行。没有可信停机证据时，不放开相应历史 in_flight 并发占位。
- 精确新 target cohort及每个comparison cell：原SubjectRef/身份修订、题目ID与实际完整body hash、module/version、信息日期、模型resolution/provider config/route、搜索策略版本、thinking开关、pack/agent方式、输出上限、replicate ordinal；目标不能靠调用者临时拼接。
- 最大新增物理 HTTP 和每次预约规则、当前有效累计上限；owner显式接受的额外风险预约若有，必须单列来源/金额/原因，不能改旧 reserved 值。
- 目标新原work binding/allowed generation、到期时间、exact action digest；digest用来防漂移，不作为授权来源。

审查过程中其他新请求/费用改变状态，不能直接重用旧quote。允许原生CAS检测后由同原确认流程重新投影；不是把source全库SHA永久当锁（新合法请求必然改变库）。

## 7. SQLite最小增量与预算算法

schema23之后新增下一原生版本（实际号码由实施时注册表固定），保留旧表/旧行；不复制费用或另造scheduler。最多三个append-only表即可：

1. `quick_scan_owner_budget_continuation`：第一阶段原批准决定及目标集合、旧暴露快照、原namespace record ref、policy binding。更新/删除拒绝；决定的过期/撤销仍从原权限源读取，不靠本表单独生效。第二阶段的原refresh action确认通过原work/action关联绑定，不回写第一阶段记录。
2. `quick_scan_owner_continuation_work`：决定→实际由原admission创建的新work→comparison cell；native FK/唯一约束防同一cell再换task重复分配。此表登记前必须核原work所属cohort/代次/题目/subject，不能只核外来hash。
3. `quick_scan_owner_continuation_send`：决定/cell/原physical budgetattempt关联与消耗；单一POST仅一个，pack按一个physical记录且锁定全部成员，不按题目重复计费。若已有原intent/pack表能提供同等唯一关联，则复用并减少此表，不为此重构账本。

旧 exposure refs可存于canonical JSON并用登记/准入时逐行核验，未必需要独立第四表。任何schema增量都在原SQLite迁移事务内完成；默认新表零行，旧reader遇新版本拒写。

**同一BEGIN IMMEDIATE/FULL原发送事务**：原当前owner已重核 → 原subject/lease/work守卫 → native决定/ref逐行核 → new-cell唯一与未消耗 → 原预算累计/并发限制 → 插入原预算attempt/新关联 → 原intent/physical关联 → 返回原SendPermit。不能出现先发HTTP再补配额表；不能从普通caller参数选择排除SQL。

仅当决定有效时，对其精确旧refs在**本次cohort的阻断计数**中豁免；不改旧status/reconciled_at/actual_cost/in_flight/request_counted。所有未获接受的新unknown仍立即全局阻断；不得给未来未知请求blanket豁免。

记账暴露守恒：`settled_actual + sum(all_unsettled_original_reservations) + explicit_additional_risk_holds + all_new_reservations <= current_same_policy_cost_cap`；`sum(all_request_counted) + new_physical <= same_policy_max_requests`。保留旧两笔0.2 USD，原100次计数持续增加；失败/超时也依原流程记账。

**该公式限制记账暴露，不证明真实完整现金有界。** 旧缺usage时不知实际费用，原预约不自动成为已知费用上界；报告继续cash_actual_complete=false。若业务要求“绝不超过真实现金上限”的严格保证，缺官方账单或可验证最大收费界就必须继续暂停，owner风险接受也不能把数学未知变已知。当前研究要求是明确接受未决暴露后继续有限新实验，须如实标此差别。

并发报告分开raw_in_flight与effective_in_flight_for_this_grant。仅对已审查本地停止、精确接受的旧unknown预算请求，从本次有效并发计数扣除；旧raw仍1。group/route全套以同一集合处理，不能只改global。新请求仍占原并发槽。原HTTP200 unpriced本来in_flight0，只消除其本次reconciliation阻断，不能伪造seal。

本次不需要预算扩容。以后若实际达到25USD/350上限，当前“用户授权继续”应具体落成原owner批准的同policy cap amendment，保留旧预约/请求，有限新上限，只增允许cap/追加明确route，不改currency/旧路由/旧价格证据；不能拿旧research-only amendment绕过owner。此为后续原生能力，不是本次首版必要实现。

## 8. 公开preview与每次发送的闭环

1. 在任何新refresh preview前，原固定owner CLI由受控配置中精确acceptance条目安装 `stockwiki.budget_exposure_decision/1.0.0`，原budget-only旧两行/future_request_core/namespace/主体验证不依赖quote。StockQA经原固定bridge核原当前owner，原ledger原子登记同一decision。安装回执明确 `dispatch_authorized=false/API_requests=0`。缺此原记录的新preview仍blocked。
2. 新1.4 readonly inspector只读取已安装/当前有效的原decision，输出raw未决状态与真实continued quote，`API_requests=0/reservation_created=false`。原StockWiki preview展示两旧请求HTTP状态、未知范围/费用、保留预约、原累计计数、精确新实验cells和总上限，将完整decision投影纳入action/quote；“可供确认”仍不等于可发送。
3. 现在才有真正ready preview，原TTY或已交付delegated原确认批准这个具体action；原 `RefreshAdmissionService.admit` 验完整record、原current owner、第一阶段decision仍有效、所有原输入不变。
4. 原注册事务生成新work/cell binding并链接原决策与第二阶段原action确认，原action receipt可幂等回读；不能给旧legacy work补绑新权威。第一阶段仅安装decision而未走完第二阶段时，native reserve必须拒绝。
5. 每POST沿真实 `ApprovedRefreshSession.check`/原owner.current路径重核，native send事务再核决定/refs/目标/配额。撤销/到期/目标漂移在POST前拒绝。
6. 中断后原intent有安全输出则原只读恢复；已send但输出未知则保留未决并暂停，不重发、不换task。原决定剩余cell不自动覆盖这个新unknown；要新的原明确review。

## 9. 同公司/同题边界

| 情况 | 是否可发新实验 |
|---|---|
| 同原intent或旧work请求已发送但结果未知 | 不可重发；原native getter读取，未知则暂停 |
| 换run/task/cohort/generation但无原新增批准 | 拒绝 |
| S1旧budget-only无scope映射，仅声称新公司/不同题 | 拒绝；不能证明disjoint |
| S1两精确旧refs获当前owner repeat-exposure批准，新cell精确列入且原新work未发送 | 可有限新请求；即使语义可能重叠也明确称独立重复实验，不称差集或恢复 |
| 同题已有原native pending/leased/uncertain work | 首版仍拒；repeat-exposure budget-only能力不覆盖work守卫 |
| 同题原result_ready、完整原owner comparison decision+精确目标+下一generation/cohort、原预算续行也获准 | 可走现有已知结果比较路径；不能只取其result JSON |
| 同一cell重复执行、重命名task/run或传不同format但控制不变 | 原cell唯一、原work/intent关联拒绝重复POST；仅回读已保存结果 |
| 显式新增replicate或不同模型/控制 | 只有原确认列出新cell及物理次数上限才可发 |
| legacy原scope不可辨且有真实owner work未决 | 不猜scope；拒绝直到原独立work决策能力解决，不能按S1无work特例处理 |

## 10. 精确改动边界建议

StockQA原路径（下一节点先写失败反例再改，最终以实际函数调用面缩减）：

- 新 `src/utils/quick_scan_owner_budget_continuation.py`：canonical决定/原验证读入口/DDL与原事务投影，不实现HTTP/新费用表。
- `src/utils/quick_scan_work_store.py`：原schema注册、readonly状态、reserve/single/pack原预算路径，增加由原native binding推导的决定，不放任意排除list。
- `src/utils/quick_scan_refresh_inspect.py`：1.4 readonly eligibility/quote；旧版本不变。
- `src/utils/quick_scan_refresh_admission.py` 和原 `RefreshConsentClient` 所在bridge校验器：原完整确认绑定、第一阶段固定CLI exposure控制读取、原注册事务附加决定。
- `src/utils/quick_scan_owner_refresh_journal.py`：5.0绑定识别，仍完整保留原guard_unresolved；旧未知work不放行。
- `src/utils/quick_scan_work_transport.py` 和 `quick_scan_question_pack_journal.py`：仅必要的原context→single/pack send关联，原SDK/ledger保持唯一。
- 原相应refresh request/quote/owner binding schema中增加精确已知dialect；`src/utils/quick_scan_uncertain_seal.py` 不放宽HTTP200条件，不改其旧research语义。

StockWiki原路径：`stockwiki/quick_scan_refresh_contract.py`、`quick_scan_refresh_preview.py`、`quick_scan_refresh_approval.py`/`quick_scan_refresh_records.py`、`quick_scan_refresh_owner_cli.py` 及它们实际使用的原schema/原policy配置。增加一个薄的 `quick_scan_budget_exposure.py` 原control模块即可承载第一阶段安装/inspect与namespace记录，复用原policy/principal读取，不能因ready-preview依赖把安装误接到原refresh confirmation后。第二阶段复用正在交付的delegation验证；不复制其grant表/身份系统，不加入新收费执行器。

IQS shared engine/Runtime首版原则上不需要改算法：消费原有效原生批准对象和Task3，在原owner服务把精确cell/目标绑定到原work；如需把comparison cohort带入task，明确已知schema字段并保持旧协议不变，不能用Runner生成新grant。

## 11. 一次大节点TDD与独审，不设小门

先把下列关键反例写成可运行测试并RED，再实现原生能力；单元/集成通过后跑一次公开原owner+SDK+Runner链路和一次独立全节点review。发现问题直接修，重跑受影响范围，不每helper复审。

单元必须覆盖：

1. 旧policy/request/grant及未开启配置遇同两旧行仍reconciliation_required。
2. HTTP200不能seal；NULL实际费用不变、100旧请求不变、预约0.2保留；cannot set zero。
3. 伪造caller bool/hash/IDs/confirmation、错误ledger/namespace/provider/subject/qid/module、过期撤销均无SendPermit；enable开关无精确第一阶段原记录仍不能产生ready quote。
4. 精确两旧行+真实有效决定仅允许精确新cell；未被接受第三条unknown立即阻断。
5. 修改原旧row状态/预约/receipt、原budget policy或目标cell后CAS拒绝；不能跨policy排除。
6. same cell换task/run/cohort/新work UUID不能二次发送；新增replicate必须在原批准集合。
7. 保留所有原费用/预约，cost/request/global/group/route上限都仍生效；并发双worker争同最后一个HTTP槽仅一成功。
8. budget-only旧unknown的raw_in_flight仍1，授权本次effective减少；无停机审查时不扣并发；已知HTTP200不造unknown seal。
9. native work同题uncertain仍拒；result_ready只有原comparison decision可下一generation。
10. 单题/pack都仅一个physical原预算attempt、原intent唯一关联；失败/输出未知不自动重发。
11. 循环消除正反例：原quote blocked→第一阶段由固定配置安装（无需ready preview）→新quote真实ready→原委托确认→新admission可发；仅第一阶段无第二阶段必须0POST，伪造ready字段/自注册原记录拒绝。future_request_core移除字段精确性/内容漂移/decision撤销也覆盖。

公开集成：原 namespace/config→preview完整风险投影→真实原确认对象→admit→实际原SDK脚本wire→唯一原Runner→原SQLite读回，测试真实原软件而合成数据；新branch1POST，预算总请求100→101，旧两行逐字节不变，费用未知仍未知。POST前撤销必须0POST；发送后崩溃则原原子输出恢复0新POST，否则未知暂停。完整有效预算quote与真正admission正例不能只靠伪port。

真实旧账迁移验收：显式mode=ro打开原S1；before SHA/sidecars/stat→SQLite backup到自有临时目录（不直接copy活WAL文件）→只在副本跑原migration→每张旧表所有行canonical摘要/计数/约束/NULL/100请求/两ref/0work保持→新表零行→原integrity/FK和rollback/reopen→副本生成完整暴露投影，默认仍暂停→不调用API，不把真实identity/consent塞进迁移副本→after原SHA相同。原源严格只读，副本正常清理，自动策略拒绝则记录并隔离，绝不绕过/误报清完。

最后真实小实验只有在能力代码整节点独审通过、原namespace生成真实当前repeat-exposure确认且exact cells登记后才执行。先一个有限cell，核0.1预约/原总101/原两行不变/实际usage与费用来源；再冷暖与崩溃恢复；最后恢复真实公司准确性、经济性和速度对照。若任一条件未满足，按原拒绝，不再用合成批准当生产批准。

后续性能顺序：先完成本能力和有限真实安全运行，再针对435秒软件验收中原逐题claim/跨进程current检查做原batch claim事务；热复用不可变题库/模块与源码，权限/撤销/预算仍冷读取并在POST前重核。不要缓存当前权限、默认扩lease或借本能力重构运行引擎。
