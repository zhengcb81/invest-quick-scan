# QA-NET-01 集中接收审查（2026-10-07）

结论：当前只能接收为partial，不放行Q10/Q13生产闭环或外部context执行。parser/证据规整/配置准入等离线交付可以保留，外部context尚未实施本身是允许的partial；但必须拒绝该模式而不能付费走native。主要阻断是实际runner和计划回执脱节、备用模型结果无法落检查点、admitted external静默退到native，以及共享TEMP清理违规。以下是同一大节点集中审查，不要求逐helper新增审查。

## 审查快照与方法

代码主体 `610de6a4c66ca86f835775fee1e986c012b8c888`；只读Git复核当前HEAD `d160d80dc2340c6fb6cef0453b289b5210cf2cb6`，中间为 `a90adf9d662b98de7b213924d9fb38891bf6122b`。610de6a..d160d80仅变3件交接记录，未变代码。本审完整读施工卡、共同规范、handoff/summary/interfaces/case-map/isolation/artifacts及关键runner/manifest/seal/authority源码与对应测试；36件artifacts字节数/SHA全部吻合当前交付。

本审未在外仓运行测试、写文件、读取凭据、发HTTP、stash/commit或清理。Git检查为只读；报告只写IQS指定路径。CodeGraph在新符号上无结果/旧行号偏移，随后使用已经指定并打开的具体源码；以下行号以当前d160d80文件实际行号为准。

原四batch日志为4/7/10/5共26个通过结果；主线隔离导出实际收集27例，首轮26过/1失败因导出未含公开examples样例，属于验证环境缺件，并非产品失败或总测试计数错误。主线随后从同commit补出精确的不可执行公开样例，报告仅复跑该缺件项GREEN；原日志覆盖26例和实际收集27例需分别记录。原全量GREEN报告962/986通过可以作为历史提交证据，不能覆盖本次具体反例。

本审已读取主线最终六例及guard日志：5 failed / 1 passed / 4.81s，五条均为业务断言RED，没有环境错误。原有两次CLI fixture迭代出现过同路径题文件缓存/错误回答qid问题，最终版使用独立版本题文件并为新增IQS_03提供正确的HTTP边界答案；这些早期fixture失败不作为产品反例。此次是冻结owner源码的隔离调用，合成身份、合成答案及stub HTTP，并非真实API、真实StockWiki身份golden或付费调用。本审只读取日志，没有再次运行。

## 最终复现证据与边界

| 项目 | 冻结记录/结果 |
| --- | --- |
| 导出manifest | `runs/qa-net01-intake-2026-10-07/export-manifest.json`；SHA256 `bea11e7f1f9cec9a5ae1330d711cf844f2c29f4fc071847fc1c511040c077c32`；67件精确允许文件，36件交付artifacts全部匹配；无真实provider配置、env或生产DB |
| 反例源码 | `docs/implementation/reviews/QA-NET-01/acceptance_cases.py`；8181 bytes；SHA256 `dde1dfd7efe910d6814c01869c0505f3f230db0a0363759047339532c70263f8` |
| 最终反例日志 | `runs/qa-net01-intake-2026-10-07/guarded-test-output.log`；38004 bytes；SHA256 `698e0a4a358e22a989fe2855c70a6a583c2bbb0653e8a676a9144785d60c1acc` |
| F1 | admitted external走公开CLI，native HTTP stub调用2次，预期0；未实施external时仍发生错误派发 |
| F5 | 旧attempt已落unknown后更换prompt，真实planner计划1次模型调用，预期0/reconcile；未在本例实际发送新增HTTP |
| F3 | 首轮2题成功；合成manifest增加IQS_03后plan为reuse2/dispatch1，新增题成功，但旧题触发frozen routing冲突，CLI exit1；未运行IQS真实compose，证据是owner公开CLI消费增量manifest的失败 |
| F4 | 第1版成功、第2版gen2成功并封存；再次同第2版时plan为reuse/gen2，实际attach发生gen1冻结冲突、CLI exit1；未重复付费发送，但恢复失败 |
| F2 | lifecycle收到其余结构合格、actual_model为alternate的合成receipt后checkpoint为None；没有执行真实双路由HTTP，因此只证明lifecycle边界问题，尚需owner公开fallback E2E |
| N/A对照 | 真正写入status=not_applicable、score=null检查点后，planner为skip_not_applicable且0调用；此隔离对照GREEN |

guard最终计数为outside_write_blocked=1/network_blocked=1，均来自启动时的故意canary；guard源码明确测试根外文件写入和DNS会被拒，文件未创建。其余冻结运行没有真实HTTP/根外写；日志中的offline-fixture-key由测试自建，不是读取本机凭据。验证使用自有--basetemp、显式rootdir及自有pytest日志，不复现owner此前共享TEMP删除行为。

## 阻断发现

### F1 [P1] 已准入external会付费走native，回执却声称可执行external

触发：提供 `mode=external_context` 或 `explicit_hybrid`，某Brave/Tavily/Z.ai route的credentials/cost/rights均通过准入。`src/runners/llm_runner.py:1156-1161`只拒 requires_external且未admitted；通过后搜索策略对象不进入后续answer provider/HTTP链。`src/config/quick_scan_search_policy.py:337`把bool(admitted)直接称external_dispatch_enabled。现有CLI测试 `tests/integration/test_qa_net01_cli_e2e.py:407-420`明确期望admitted external时exit0、native回答POST2次，证明测试固定了错误行为。

影响：用户选择冻结external模式，实际使用模型native搜索且可能付费，回执/预算/证据来源类型与选择不一致。不能用“没有真实external route所以目前没发生”证明安全；用户按模板补齐后即可触发。

反例：所有准入字段齐全的外部策略 + 真实runner/HTTP边界stub；外部context未实现时预期明确unsupported、exit1、搜索/模型0、external_dispatch_enabled=false，同时可保留admitted_routes表示配置检查通过。也需覆盖explicit_hybrid。可修为失败关闭，不要求本节点补完整外部发送链。

### F2 [P1] 备用模型成功后仍无法checkpoint/C06

`src/runners/llm_runner.py:1337-1370`固定首eligible模型到整个lifecycle；`421`仍要求receipt.actual_model == self._model_requested。若首路由A被拒后备用B回答有效，actual_model=B，按此条件检查点分支不走，落入 `478-490` honest-unknown，work变uncertain；回答无法封存，重启不能hydrate。最终隔离反例证实lifecycle对其余结构合格的alternate-model合成receipt丢检查点；本批没有真实执行A拒绝→B成功的公开双路由HTTP，完整路由闭环尚需owner验证。首路由修复只解决单模型，不足以证明用户模型順位链完成。

反例：两个不同model route，首路由终态可fallback拒绝、备用原生搜索最终回答成功；应以实际成功attempt/model的真实receipt保存checkpoint/C06并使warm0请求，不能把attempt.model_requested伪改为备用模型掩盖路由历史。shape严格校验仍保留，未知发送不能fallback。

### F3 [P1] 增加模块改变整组routing hash，旧题回执reuse但hydrate实际冲突

`src/runners/llm_runner.py:44-54,1367`用本次所有题面构成routing_fingerprint；`src/utils/quick_scan_work_store.py:1551-1558`将其与question/identity指纹一并冻结。新模块增加题后，全组hash改变，原同qid/generation/身份/scope旧题attach时WorkConflictError；hydrate吞错返回None，before_question也拒绝。与此同时 `quick_scan_question_manifest.py:249-279`仅按单题prompt判断reuse，不考虑该冻结字段。旧checkpoint还在库中，但正常输出不能hydrate、不能按计划reuse。

反例：先公开CLI答完2题，再由真实compose增加一个模块/题，旧两题prompt/identity不变。预期只派新题，旧checkpoint与C06 bytes不变并在输出可用；不仅检查model_calls_planned或HTTP0。不放宽store不可变约束，应让逐题动作使用已有冻结work或兼容的逐题路由绑定。

### F4 [P1] 过期题gen2下次续扫回落gen1

`quick_scan_question_manifest.py:330-331`只把expired_dispatch写入generation_by_question，匹配已有work的reuse/dispatch/reconcile等虽带generation却不传override。runner `1327,1373`只消费该字典，lifecycle `_dispatch_binding:196`默认为1。题目从旧prompt生成gen2并成功后，再跑同manifest，plan写reuse/gen2，但hydrate实际attach gen1；与旧prompt冲突或拿错代次，无法恢复gen2。gen2 pending同样会被错误回落。

反例：公开CLI三次运行：A→B产生gen2→再次B。第二次只有更新题请求，第三次hydrate gen2且0请求；再覆盖中断留下gen2 pending、uncertain和scope变体。不修改原gen1答案。

### F5 [P1] 改prompt绕过未确定attempt，直接派新generation

`quick_scan_question_manifest.py:249-257`先按指纹判expired_dispatch，再在258以后检查状态。旧同qid/scope/identity work为uncertain或leased，改prompt的新manifest可直接分配gen+1而非对账/等待。中央Q13第二步要求未确定attempt先对账，不能重复收费；本包测试 `test_mod_06_uncertain_and_not_applicable_are_never_redispatched:268-303`只测相同prompt，未覆盖更换manifest时的未确定态。

反例：实际HTTP发送后outcome_unknown/在途租约，随后升级同qid prompt。应reconcile/in_flight、0新请求，原预算持有；权威终态处理完成后才按规则派新版。须同时保证已成功旧题的合法版本升级仍可执行。

## 必须准确保留的partial和测试边界

- security/segment scope缺权威ID时deferred、0请求是正确；segment当前没有绑定入口，始终deferred，不能宣称三种scope全部实际可派。`manifest_scope_bindings:203,218-223`只提供security_scope_id。security单元测试306-336只验证plan；须用真实runner到work/C06验证两个scope的输出和分别接续。
- 原`test_mod_06_uncertain_and_not_applicable_are_never_redispatched`的IQS_02实际调用默认scored的_settle，没有创建N/A，不能靠名字算覆盖。最终集中反例已额外创建真正not_applicable checkpoint并验证skip_not_applicable/0派发GREEN；该结果支持N/A这一路的planner行为，不扩大到其他未测scope或live答案。
- manifest loader只要求schema_version非空字符串（86-87），module_locks只有必填名未校验内容，semantic/definition SHA只核64hex，实际plan/work只用prompt指纹。未知schema版本如9.9.9或module/semantic/scope元数据改动而prompt不变没有owner lock核验。冻结manifest并非已完整验证的producer契约；应使用正式owner发布锁/已验证hash及支持版本，或明确缩小消费者保证，不能声称所有语义/模块hash篡改均已拒绝。
- C06缺authority落durable block、补齐后显式--seal-deliveries模型0的原测试为真实owner实现的隔离fixture；不是StockWiki真实身份golden/真实接收端。外部导入/ACK未跑的partial准确，不能升级跨仓verified。

## authority不可变与错误处理

`quick_scan_delivery_seal.py:44-60`对已有package返回already_sealed，不重建，保持旧字节；没有通过新authority覆盖sealed package。缺authority和adapter MissingC06Fields分别写blocked（66-88），checkpoint保留。自动封存异常在runner374-375只记日志并保留result_ready，由显式恢复入口补封；不应描述为所有异常均已有durable block。

已封存后换authority时helper直接返回already_sealed，不会抛immutable错误；interfaces134“换权威重建→immutable拒绝”需区分底层prepare拒绝与当前公开seal幂等行为。加载器对capabilities=[{}]会先set导致TypeError（authority.py80），而非AuthorityUnavailable；生产入口仍失败关闭，但有界错误分类需一致。此处并无来源证明可以重建旧包，修复不要放宽adapter/schema或根据自由文本补authority。

## 隔离记录：已发生的违规，不能靠后测抹除

共同规范要求唯一自有TEMP根、cleanup manifest/owner/hash/绝对路径及无越界，共享状态变化停止。`isolation.md:23-26,49-51`明确仅凭pytest-NNN名称和mtime<180min删除25个共享根；没有目录owner/hash/manifest。921含非本包publication-registry文件已证明共享状态，936曾锁后重试，收尾15/16/17仍仅按mtime删除。违反共同清理规则。

shutil.rmtree可能删除若干子项后才在锁定文件抛异常；PermissionError不是整棵目录原样保留的保证，pytest后续轮转也不能证明无损。已删除内容及影响未知，不能伪写“全部自有/无越界/无损”。不得重现删除、搜他进程临时资料或试图靠再次清理修复证据。需要把这次行为作为异常事件保留准确路径/已知影响与未知边界，后续验证使用明确自有--basetemp、隔离log/cov/cache/output，并按真实owner manifest清理。

此外isolation8-9仍声称未提交6a9ff13及27 dirty条，与handoff已提交610de6a/当前d160d80不一致；测试重写共享coverage/log并非环境完全复原。scope.out_of_scope_writes=[]只能按仓源码授权语义解释，不能拿它证明共享TEMP清理合规。

## 交接准确性修正

36件artifacts index当前全部匹配；但interfaces68及handoff中seal_deliveries content_hash为 `1ecee70715e654d4c62aec2949ed48475ac9b9db30f4ffb71333dc7260c619ca`，当前source/artifacts实际为 `d81f73e114a669882f91f2bac1653be0017f1f0b2dc464eb1373260ca66c4e99`，这是接口记录过期。handoff.changed_paths36以后是绝对路径，共同规范要求源仓相对路径。日志旧计数、隔离表、未启用external的真实失败关闭边界应一并在该owner最终交接更新；中央总控不代改外仓。

## 集中整改/验收建议

F1-F5已在同一隔离批次形成上述边界明确的RED证据，真正N/A对照GREEN。代码整改由唯一StockQA owner进行；沿用这批反例，不每小函数新增review门。在最终集中复验中再补公开双路由fallback E2E、security多scope、gen2 pending/uncertain与prompt升级在途租约，不把lifecycle或planner反例冒称完整派发闭环。断言检查实际发送、checkpoint/attempt状态、原budget持有、被hydrate的代次与scope、C06 package不变，不能只看plan统计或mock掉内部lifecycle。保留现有成功底座、历史失败与partial，当前不执行live或跨仓真实StockWiki验收。
