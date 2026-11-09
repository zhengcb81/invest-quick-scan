# owner job façade 语义契约（iqs-job/1）

OWNERPKG-INVEST-QUICK-SCAN-01 · G-m8-IQS-01…05 + G-m8-COMMON-01/02/03 的**权威语义文本**。
实现：`scripts/dashboard_job_facade.py`（投影/账本/幂等）、`scripts/owner_job_cli.py`（公共CLI）、
`scripts/dashboard_service.py`（同origin路由）。本文与代码不一致时，以测试+代码实际行为为准并修文。

版本：`MAPPING_VERSION = iqs.owner_job_actions/1.0.0`；wire协议：`iqs-job/1`。

## 0. 红线声明（不可放宽）

1. **预算闸门不可绕过**：`jobs/submit` 是既有授权链的**新入口**，不是替代。提交解析到已登记
   execution_bundle 后，实际启动完全由既有 `ExecutionGateway.start` 执行（原owner预检、
   registered permissions 核查、spend_authorization、preview 复核、原子启动记录）。本面不新增
   预算、不拼装bundle、不重发未知请求。`thin_scan.py`（草稿、无预算闸门）从本面**不可达**。
2. **不复制评分逻辑**：Dashboard只消费JobView投影；题库/量表/评分/admission全在owner仓内。
3. **formal/草稿不混**：只接受 `scan_kind=formal`；任何草稿scope被显式拒绝
   （`draft_scan_not_exposable`），不存在把草稿路径标记为formal的入口。
4. **诚实投影**：`work_completion_authoritative` 恒为 `false`（本地引用/摘要不是完成权威，
   原owner核查才是）；`paid_dispatch_started=None` ⇒ `cost_state=unknown`，任何调用方
   （含Dashboard）不得改写为 `known`。

## 1. 提交（G-m8-IQS-01 / COMMON-01）

`POST /api/product/jobs/submit`（CLI：`owner_job_cli.py --origin … --operation submit`，
请求体 stdin 或 `--request-file`）：

```json
{"command_request": <Dashboard CommandRequest（owner=invest-quick-scan, requested_action=run_scan）>,
 "return_to": "可选；逐字通过 iqs.dashboard.owner/1.0.0 白名单"}
```

命令以幂等键和命令 ID 锁定。其他命令和其他任务的操作可以独立进行。

1. CommandRequest 形状核验（未知字段拒绝）；company 必须 `resolution_status=resolved`；
   entity_id/listing_id/analysis_subject_id 逐字通过 owner 有界标识规则（`safe_entity_id`）。
2. `scan_kind != formal` → 409 `draft_scan_not_exposable`（红线3）。
3. `explicit_scope.bundle_id` 可选。它只选择 owner 已登记的包。省略时，公司须恰有一个登记包。
   显式挂牌、分析主体和资料截止日分别与冻结的身份快照、原分析主体配置和题目清单比对。
   无法核实的范围由 owner 返回具名错误。
   `universe_id` 非空时必须等于已部署 `config.universe_id`，否则 409 `universe_mismatch`；
   `questionnaire_version` 非空 → 400 `questionnaire_version_unverifiable`
   （owner当前没有已部署的题库版本键；不把声明当已验证。owner侧发布版本键后扩展）。
4. `return_to` 若提供：必须逐字通过 `safe_return_to` 白名单且公司scope与命令一致
   （跨公司return拒绝），否则 400 `return_to_invalid`；不静默回落。
5. `limits_ref`（G-m8-COMMON-03）注册表（精确映射到已部署owner配置键）：
   | limits_ref | owner已部署键 |
   |---|---|
   | `null` | execution bundle 的 `spend_authorization`（登记路径，链内既有权威） |
   | `iqs.bundle.spend_authorization` | 同上 |
   其他值 → 400 `limits_ref_unknown`（不猜测授权或金额）。
6. **命令级幂等**（G-m8-IQS-04）：`idempotency_key` 已绑定命令 → 直接返回同一命令与同一
   `owner_job_id`（`attached=true`），**不再调用执行链**，零二次计费/二次执行。
7. 新命令先持久化意图和幂等索引，再通过原网关登记选择接口核对范围。
   选定的包 ID、实体和指纹写入命令，随后由原 `execution.start` 启动。
   进程在命令绑定前中断时，同键接续仍使用冻结登记，原网关按包附着已有启动。
8. 明确的无派发拒绝以 `submission_refused` 返回，记录拒绝码和原 HTTP 状态。
   不确定的启动保持 `needs_original_inspection`。同键重放或查询命令时，按冻结登记查找原启动引用。
   找到唯一匹配时附着原引用。查不到时继续返回 unknown，保留原命令和幂等键。

成功返回：`{ok:true, data:{attached, command, job_view, API_requests}}`；
`command.owner_job_id` 即原生 `run-<32hex>`，同时是JobView的`owner_job_id`。

## 2. JobView 投影（G-m8-IQS-02 / COMMON-01/03）

`GET /api/product/jobs/{owner_job_id}`（或按命令 `GET /api/product/jobs/commands/{command_id}`）。
四种原生job统一投影为Dashboard合同JobView（12字段，无扩展键）；owner原生细节放在并列的
`annotation`（owner_kind / command_bound / work_completion_authoritative / status_source /
owner_error_details / mapping_version）。

### 状态映射表（权威）

| 原生记录 | status | status_known | error | 备注 |
|---|---|---|---|---|
| run `starting`/`running`（活跃子进程） | running | true | — | 本地启动引用+活跃句柄 |
| run `needs_original_inspection`（含重启后running/starting、记录损坏） | unknown | false | status_unknown | 只许reconcile |
| run `process_exited`（未核查） | unknown | false | status_unknown | **进程退出≠完成** |
| run `process_exited` + 已缓存reconcile核查（全部result_ready/delivered） | succeeded | true | — | 注明cached_owner_inspection+observed_at |
| run `process_exited` + 已缓存核查（含pending/failed） | failed | true | run_incomplete_or_failed | resumed后回running |
| run `observed_stopped`+有效retirement证明（全部result_ready/delivered） | succeeded | true | — | 证明是持久owner证据 |
| run `observed_stopped`+证明含pending/failed | failed | true | run_incomplete_or_failed | |
| run `launch_failed` | failed | true | run_incomplete_or_failed | 未启动进程 |
| 命令 `submitting`（崩溃窗口） | queued | true | — | 重放同key提交可转正 |
| 命令 `refused` | failed | true | 原拒绝码 | owner_job_id=null, recovery=unavailable |
| prepjob `preparing`/`registration_in_progress` | running | true | — | |
| prepjob `registered` | succeeded | true | — | |
| prepjob `owner_prepared`/`registration_pending` | failed | true | registration错误 | 登记恢复属原工作台显式动作，不经本面 |
| prepjob `needs_original_inspection` | unknown | false | status_unknown | |
| prepjob `abandoned` | cancelled | true | — | |
| deliveryjob `running`（活跃） | running | true | — | |
| deliveryjob `needs_original_inspection`（重启后发现） | unknown | false | status_unknown | |
| deliveryjob `partial` | failed | true | delivery_partial | resume接续pending entries |
| deliveryjob `completed` | succeeded | true | — | 注意：完成=所选范围已对账，**不等于**金融审查通过 |
| deliveryjob `abandoned` | cancelled | true | — | |
| deliveryjob `historical_read_only`（原目标不可证） | unknown | false | status_unknown | 不隐藏历史，但不可据此恢复 |
| batch `running`/`draining` | running | true | — | draining仍是运行（排空中） |
| batch `paused` | queued | true | — | queued=已受理、暂停派发，resume继续 |
| batch `blocked`（阻断原因含未知类） | unknown | false | status_unknown | |
| batch `blocked`（确定性原因） | failed | true | batch_blocked | blocked_reasons入annotation |
| batch `needs_original_inspection`（实例变化） | unknown | false | status_unknown | |
| batch `owner_ready` | succeeded | true | — | owner已有答案；不代表已导入/金融通过 |
| batch `abandoned` | cancelled | true | — | |

### 费用投影（G-m8-COMMON-03）

- `cost` 恒为 `null`：owner当前没有原生"单job金额"投影（预算账本在原StockQA store内部，
  产品面只暴露 `paid_dispatch_started=None`）。
- `cost_state`：run/batch → **unknown**（会派发付费工作，是否已付费未知；不得由任何旁路改为
  known）；prepjob/deliveryjob → **not_applicable**（0模型调用、不申请新spend、不复问）。
  `known` 的产生条件（owner未来暴露原生费用源）已写入投影形状，但当前**没有来源**，如实登记为
  本迭代不交出项。

### recovery_capability（COMMON-02）

| kind | 值 | 依据 |
|---|---|---|
| run-*/prepjob_*/deliveryjob_*/batch-* | `durable_owner_job` | 均为可按ID复查的durable owner引用 |
| refused命令（无owner job） | `unavailable` | 无job可恢复；新执行=新命令走完整链 |
| （本迭代无任何 `short_request_only` 投影来源） | — | 如实登记：枚举保留，当前不出现 |

## 3. allowed_actions 权威映射（G-m8-IQS-03 / COMMON-02）

Dashboard动作空间 `{cancel, resume, retry, reconcile}` 对 owner 原生动作的**权威对应**：

| Dashboard | owner原生 | 权威判定 |
|---|---|---|
| `cancel` | **无对应**（run: `pause`/`retire`；batch: `pause`/`abandon`；prep/delivery: `abandon`） | **pause ≠ cancel**：pause只是公司/scope边界排空，保留在途HTTP并安全完成，不取消任何工作；retire只是登记"原启动已停止"的事实引用；abandon只结束编排/等待且保留原工作与费用。cancel一律拒绝（`cancel_unsupported`），任何状态下不出现。 |
| `resume` | run `resume`；deliveryjob `resume`；batch `resume` | 仅在投影显示可恢复状态（run: failed且launcher paused/draining；deliveryjob: partial；batch: paused/blocked确定性）时出现在allowed_actions。实际动作仍由原生守卫复核（bundle指纹、进程停止证据、原owner预检），投影不代替守卫。prepjob**无**resume（原准备没有恢复动作）。 |
| `retry` | **被明确禁止** | owner规则 `inspect_original_owner_no_automatic_resend`：未知/失败不自动重发。retry一律拒绝（`retry_forbidden`），任何状态下不出现。新执行=以**新命令**重新提交完整授权链，由原owner重新准入并可拒绝。 |
| `reconcile` | run: `inspect`（只读原owner核查）；其余：durable重读 | **inspect ≡ reconcile**（语义等价：核原状态）。reconcile**只核原owner状态**：不重发、不完成prepjob登记（原生reconcile的登记写动作保留在工作台，不经本面）、不改预算、不产生费用。`status_known=false` 时 allowed_actions **恰好** `['reconcile']`（COMMON-02硬规则）。 |

各状态下的完整 allowed_actions 输出由 §2 状态映射表按上表规则派生（测试断言固化）。
动作幂等（JobActionRequest.idempotency_key）：同 `(owner_job_id, action, idempotency_key)`
重放返回**已记录的同一结果**（`replayed=true`），不重复执行原生动作。

## 4. 有界job目录（G-m8-IQS-04）

`GET /api/product/jobs?cursor=<opaque>&limit=<1..100>`（首页省略cursor）：

- 目录=命令账本（全部）+ 四类原生目录的有界窗口（runs 分页至 2000×5；prepjob/deliveryjob
  各50；batch 100——沿用各模块自身上限）。
- 返回 `{items:[JobView…], annotations:[…], page:{next_cursor, snapshot_id, total, total_status},
  work_completion_authoritative_default:false}`。
- **每项都标 `work_completion_authoritative`（annotation内，恒false）**：本地启动引用、交付摘要、
  编排投影都不是工作完成的权威；只有原owner核查是，且核查结果以observed_at注明。
- 已绑定命令的job只经命令投影一次（不重复列出）；未绑定job的JobView `command_id=""`，
  annotation `command_bound=false`（诚实标注"无命令绑定"，不伪造command_id）。
- 某一原生目录不可读时：该窗口缺失不冒充为空，`total_status` 降为 `estimate`；单行不可投影时
  以unknown+reference_error呈现，不隐藏。
- cursor是窗口内位置token（`v1:<offset>`），不承诺跨写稳定；Dashboard按页重读。

## 5. 深链返回与命令绑定（G-m8-IQS-05）

- 命令记录是 **durable绑定**：`command_id ↔ owner_job_id` 在提交时落盘，完成/失败/unknown
  各态均保留（记录只追加状态，不删除）。`GET jobs/commands/{command_id}` 随时可查
  （返回command+JobView+return_to）。
- `return_to` 沿用 `iqs.dashboard.owner/1.0.0` 白名单（`dashboard_iqs_link.safe_return_to`）：
  8条逻辑路由、B03 `#/company/<ENT>[/<tab>]` 与绝对loopback公司路由、逐路由query白名单
  （`/results` 允许 `query/view/offset/limit/conditions/condition_combine/filters/snapshot_token`
  ——这就是"恢复原名单/筛选/行选择/报告run上下文"的owner权威声明：**只接受、逐字保存、
  逐字返回这些键**，owner不解释不改写）。非法值提交期显式拒绝（不静默回落）。
- 跨公司return（`#/company/<其它ENT>`）在提交期拒绝（与 `_iqs_link` 的cross-scope规则一致）。
- Dashboard在命令完成后凭command记录取回return_to与绑定；owner不做页面跳转，只提供绑定与
  白名单校验结果。

## 6. 路由与传输（与控制面共存）

同origin、同 `/api/product/` 前缀、同一套Host/Origin/CSRF/JSON防护（`dashboard_http.py` 未改）：

| route | 方法 | 语义 |
|---|---|---|
| `jobs/submit` | POST | 提交run_scan命令（写，需CSRF） |
| `jobs/{owner_job_id}` | GET | JobView+annotation |
| `jobs/commands/{command_id}` | GET | 命令绑定查询 |
| `jobs/{owner_job_id}/{cancel\|resume\|retry\|reconcile}` | POST | 动作（写，需CSRF；体={idempotency_key}） |
| `jobs?cursor&limit` | GET | 有界JobPage |

`GET status` 响应新增 `owner_job_facade` 发现块（wire_protocol/mapping_version/routes/
limits_ref_registry/job_id_kinds）。

CLI（`scripts/owner_job_cli.py`，协议 `iqs-job/1`）：固定argv，`--origin` 必须loopback；
`submit`/`act` 自动经 `GET status` 取CSRF；envelope `{protocol, ok, data, error}`；
exit 0=成功、2=请求/契约错误（4xx）、1=传输/服务故障（5xx、连接失败、非JSON envelope）。

## 7. 诚实登记（本迭代不交出项）

- `cost_state=known` + 非空cost：**无来源**（owner无单job费用投影）；投影形状已备，来源未部署。
- prepjob `owner_prepared`/`registration_pending` 的登记恢复：保留在原工作台（原生reconcile有
  登记写动作），Dashboard reconcile不代做——COMMON-02"只核原状态"的严格执行结果。
- `questionnaire_version` 非空核验：owner未部署题库版本键，当前拒绝而非假装核验。
- 真实formal扫描演练（§5.2预算闸门证据）：真实启动会产生付费派发，按红线须操作者确认预算边界
  后执行；本包交付软件级全链证据+真实验证留待演练（见handoff NOT_RUN登记）。
