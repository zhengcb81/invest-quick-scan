# 原 delegation 到期与在途 CP 边界（只读源码诊断）

本轮只读源码、原 grant 元数据和配置中的 grant 时长；未执行任何真实 CLI、服务调用、模型请求或数据库写入，未改源码。没有查询本轮运行数据库或阅读答案正文。PID 4972 / attempt 3 的即时进度沿用 root 提供的状态，不宣称独立重新检查过运行状态。

## 结论

1. **原 grant 到期后，新 claim / subject dispatch / 实际 POST 会被当前原权限检查阻断。** `current_permissions` 可越过“旧 preview 的 15 分钟有效期”，但不能越过 delegation 自己的 expiry。
2. **已在 grant 有效时发出的 HTTP，不会只因 grant 在等待期间到期而丢 CP 或费用。** 原 response/pack 落账及 `after_question` 的 transport checkpoint 路径不再检查 delegation 当前时间；原 lease 仍有效、答案/回执合规时，可在 grant 到期后正常落地 CP、标准答案、费用和封存。
3. **work lease 是独立、较短的硬边界。** 若真正到回复/CP 时 lease 已过期，原代码保留 late receipt 与费用并进入不确定/恢复路径；不能凭“POST 时 grant 有效”越过 lease。此时可能无 accepted CP，但根因不能说成 grant 到期。当前 runner 构造默认 lease 600 秒，原 dashboard 启动命令不覆盖它，也未发现此原路径的自动 heartbeat/续租。
4. **没有现成的运行中 grant 续期/替换机制。** 原 grant/confirmation 都绑定不可变 preview 和时长；同 grant ID 的更长 expiry 会安装冲突。已有安全路径是本次原进程安全停定后，为剩余原工作重新走 fresh prepare/owner consent/admission，再用原启动/恢复接口。不能给正在运行的会话热换 confirmation。
5. **下一次新 prepare 可合法使用 12 小时（43200 秒）grant，服务无需重启；但必须先满足原服务的 inactive 守卫。** 当前活跃扫描期间修改 `prepare.delegation_ttl_seconds` 属于非追加部署变化，原 setup 和热加载都会拒绝，不能宣称可以边跑边改。12h 只作用之后新建 grant，不延长当前 `dg1_450…`。

## 原 grant 与配置实证

原文件：`runs/r25-live/owner-workspace/runs/state/quick_scan_refresh/delegations/dg1_450af2fa40412610ddbf907d1ad9bc2433d5368bb2ec1f63d33b55aee5499260.json`。

- created_at：`2026-10-28T11:31:55.624910Z`。
- expires_at：`2026-10-28T15:31:37.344873Z`。
- preview：`rv1_4ea1f0ddc807ef8e5b90df9c26835d5a1329e57746f07f882cbffe78ad3df60d`。
- 当前 dashboard 本地配置 `prepare.delegation_ttl_seconds`：14400。

## 发送前权限硬边界

以下路径均为当前原实现：

- StockWiki `stockwiki/quick_scan_refresh_delegation.py:355–372`，`_grant` 每次加载原 grant、查 revocation、核原 binding，要求 `created_at <= clock() < expires_at`；到时即 `delegation_expired_or_future`。
- 同文件 `:547–555`，`inspect_confirmation(..., admission_mode='current_permissions')` 在父类当前权限核查前后都调用 `_grant`。因此当前权限模式并不豁免 grant 时效。
- StockQA `src/utils/quick_scan_refresh_consent.py:272–295`：旧 preview expiry 只在 `fresh_registration` 模式限制当前时点；delegated 模式仍调用 `validate_delegated_native`。`quick_scan_delegated_consent.py:163–166` 再独立要求当前 `now < grant.expires_at`，且总 grant 时长不能超过24小时。
- StockQA `src/utils/quick_scan_refresh_execution.py:275–309`，`ApprovedRefreshSession.check()` 调原 bridge `current_permissions`，并核当前 confirmation/preview/owner_policy、原 registration、冻结输入及 native owner 状态。
- 同文件 `:494–553`，`claim_registered_question_batch` 先 `self.check()` 才调用原原子 claim；`:674–684` 注册 subject dispatch 也先 check。
- StockQA `src/runners/llm_runner.py:283–289`，单题 attach/hydrate/claim 前通过 `_owner_work→session.check()`；`:742–758`、`:797–831`，pack 准备及 dispatch context 也保留原 check。
- StockQA `src/utils/quick_scan_work_transport.py:118–145`，`consume_for_post()` 在真正进入 HTTP 前再次 `_check_owner_refresh_guard()`；`:1268–1286` 在容量等待循环的每次尝试前也重检。不能用早先已通过的 claim 绕过到期后的 POST 检查。

边界是原检查时点与实际 transport 进入之间的正常微小执行窗口，并非对任意未来 POST 的缓存授权；原路径没有“grant 临近到期剩余响应时长预算”的额外 margin 算法。

## 回复、费用、CP 与 after_failed 的顺序

- StockQA `quick_scan_work_transport.py:254–345` 的 `_record_response` 根据原 consumed permit、2xx、receipt identity、实际价格/费用记录原 pack/work/budget outcome，**没有调用当前 owner grant guard**。原 pack 分支先 `record_question_pack_outcome`，它会把真实费用落入原预算表。
- `quick_scan_question_pack_journal.py:505–631` 的 `record` 核原 physical receipt、subject response binding 与 work lease，并将预算 outcome 写入原同一操作。这里也没有 delegation 当前时间检查。
- `quick_scan_subject_journal.py:222–259` 的 `guard_response` 比较原发送 receipt 的 provider/model/prompt/request identity，要求完成时间不早于原 send，不要求完成时间早于 grant expiry。
- StockQA `qa_engine.py:657–689` 中有效成员生成 answer 后直接调用 `lifecycle.after_question`；这段不重新核 grant。
- `llm_runner.py:1240–1305` 的 `_save_transport_checkpoint→save_answer_checkpoint→_seal_delivery` 核实际原 transport/完整标准答案，然后存原 CP；没有 `_owner_refresh.check()`。`:608–621` 封存失败也不抛丢 CP，保留 `result_ready` 供原 `--seal-deliveries` 补封。
- `quick_scan_work_store.py:1996–2004` 的 `_assert_lease` 要求当前 lease token/epoch/status 和 `now < lease_expires_at`；`:4365–4386` 存新 CP 前仍调用它。**因此 grant 到期本身不阻断已发请求的 CP；lease 到期或原内容/receipt 校验失败仍可能阻断。**
- pack reply 遇 lease 过期：`quick_scan_question_pack_journal.py:574–628` 把整 pack 标为 late/uncertain，对到期成员调用 `recover_expired/note_late_receipt`，仍调用 `record_budget_outcome` 保留费用；`quick_scan_work_transport.py:285–286` 抛原 uncertain，不能自动 replay。
- `llm_runner.py:1446–1475` 的 `after_question_failed` 对 transport-managed 路径，只对 `missing_question`、`invalid_question`、`answer_generator_rejected_member` 尝试原 `fail_received_without_answer`；普通 ProcessingError/DB/timeout 不凭2xx宣布无效、不重发，原状态交恢复。lease 不合法时原 fail 也被围栏拒绝。

这不是“到期后保证 CP”：grant、lease、答案契约、receipt 一致性、DB 成功是不同条件。这里能确认的是 **grant expiry 不在 post-response CP/fee 路径上重新判断**。

## 已有时间边界与续授权接口，及其限制

| 已有接口/原实现 | 能做的事 | 限制 |
|---|---|---|
| 每次原 `current_permissions` / pre-POST guard | grant 到期后停新发送，既有真实响应按原路径落账 | 不预留“回复必须在grant前到达”的时间，也无需靠此续grant |
| `QuickScanWorkLifecycle(deadline=...)`；`llm_runner.py:350–389` | 单题/pack claim 前停止新工作，已 claim 按正常 after 路径结算 | 原 `dashboard_execution.py:641–654` 启动命令不传 deadline；原 runner 构造 `:2702–2756` 也不传。不能把内部参数描述成现有UI可热设置的grant截止功能 |
| `POST /api/product/tasks/{run_id}/pause`；`dashboard_execution.py:840–845` | 原 launcher 标记 draining/paused，保留当前HTTP | `pause_scope='company_boundary'`，不能承诺打断当前33题内部派发或立即在下一pack停 |
| `POST /api/product/batches/{batch_id}/pause` | 原批次停止未来公司编排，安全等待当前公司 | 不延长当前grant，不杀在途HTTP，不替换当前会话授权 |
| 原 `stockwiki.quick_scan_refresh_owner_cli --request / --install-delegation / --confirm-delegated`、原 admission CLI；产品 `prepare/preview`、`prepare/apply` | 安全静止后为当前原剩余范围建立新preview/grant/confirmation/registration，再原启动 | 不是运行中续期。不得重复不明确的install，不改旧文件，不把新confirmation塞进旧进程 |
| 原 `main_with_llm.py --seal-deliveries`、产品 `tasks/export-delivery` / delivery jobs | 对已存在的 accepted CP做零模型封存/交付恢复 | 不修复无CP答案，不授新发送权；原批准会话的恢复报告仍检查当前权限 |

StockWiki 原 owner CLI 有 install/revoke，没有 renew selector；`quick_scan_refresh_delegation.py:433–447` 安装同一确定性 grant ID 时，除 created_at/record_sha256 外任何差异（包括 expires_at）都会 `delegation_single_action_install_conflict`。现进程保存着旧 `self.proof`/confirmation，并在 check 比较它；新授权必须经原新会话，不是热续。

## 12h 新grant与不重启服务的准确条件

- IQS `scripts/dashboard_prepare.py:169–175` 接受整数900–86400秒；43200合法，注释明确“NEW exact-scope native grant; never renew an old one”。`:1020–1023` 在新scope install spec构造时读此值并生成新 expiry。
- StockWiki `quick_scan_refresh_delegation.py:186–190` 和 StockQA `quick_scan_delegated_consent.py:163–166` 都允许至多24h；12h在原边界内。保持原 policy1.1/v6、quote1.1与ttl_hours24即可，不需切policy。`ttl_hours` 是原新鲜度语义，不等于 delegation_ttl_seconds。
- 产品原 `GET /api/product/setup` 返回当前 config/revision；原 `PUT /api/product/setup` 要求完整 config 与该 revision（`dashboard_service.py:372–389`、`:514–515`）。在这个 config 内把 **下一次** `prepare.delegation_ttl_seconds` 设43200即可，但本诊断未执行。
- `DashboardService._load`（`:165–191`）每次请求核配置字节 revision；改变 prepare TTL不属于`:193–197`的纯执行包追加，会先调用 `_assert_inactive`。`:208–223` 拒原 running/starting/needs_original_inspection execution、running/draining/needs_original_inspection batch及未处理prepare/delivery。
- `_setup` 自己也先查原 execution active并 `_assert_inactive`（`:382–387`）；合法更新后 `_save_config→_load` 使下一次 `_preparer` 重建。**所以服务进程可不重启，但本次活跃扫描期间不能合法热改该部署字段；应待原活动安全结束且各原未决引用按原接口处理后再更新。** 直接先改磁盘会在下一请求触发同样inactive拒绝，不是绕过路径。

本报告只说明已有行为和接口。当前在途请求不应因为grant临近到期而被杀；也不能通过改grant、假时钟、改lease或直接补CP来规避独立边界。
