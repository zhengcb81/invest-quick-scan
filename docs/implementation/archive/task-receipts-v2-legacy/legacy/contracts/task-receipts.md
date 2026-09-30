# 任务回执 v2 与只读校验设计

任务回执契约版本2；由本仓P01实施。当前实施计划版本以`docs/implementation/tasks.json`为准。本文件定义任务验收证据契约；设计文字本身不表示回执验证器、任何任务或阶段门已实现/通过。

## 目标与边界

回执是任务验收证据的索引，不是实现者自报状态。校验器只读取计划、case目录、源码快照、测试日志、依赖证据和独立审查报告，计算`eligible_to_close`及阻断原因；不执行回执内的命令、不改变任务状态、不修改/删除回执，也不写业务数据库。

新任务使用receipt v2。已知旧回执保持原始字节，可作为历史进度/范围说明：包括当前P00基线的无`schema_version`旧格式，以及明确标记`schema_version="1.0"`的v1 envelope。由于缺少逐断言和当前任务契约hash，统一返回`legacy_historical`，不得由迁移器补造当前通过证据。声明为v2或任何未知/未来版本的回执不得降级解释成旧格式。

## 依赖与旧回执的启动迁移规则

每条`depends_on`默认是当前关闭门：被依赖任务必须有匹配当前任务/case/global-boundary hash的receipt v2且推导为`eligible_to_close=true`。旧receipt v1即使历史上标成完成，也不能满足当前依赖。依赖闭包必须逐层检查，不能只检查最末任务的本地receipt。

唯一例外必须在任务卡`historical_context_dependencies`中逐边列出，且该字段必须是`depends_on`的子集。这类边只允许读取前置任务已经存在、不可变且哈希锁定的上下文文件；验证器要求receipt关联一份路径/hash清单和独立review确认。它不授予前置任务当前完成状态，不满足任何ready/verified/G0/G6门，也不能被传递成其他普通依赖的豁免。缺文件、路径越界或hash变化时停止并重做对应baseline任务。

当前计划中唯一bootstrap例外是P01→P00：P01实现receipt v2验证器前，可以将P00旧基线输出作为只读输入上下文并记录其文件清单；P00旧v1仍仅为`legacy_historical`。P01自身验证通过后，必须按当前BASE-01/02重新执行P00并生成新的v2回执，保存到`docs/implementation/contracts/receipt-P00.json`及对应校验/隔离证据；原`docs/implementation/baselines/receipt-P00.json`字节不动。随后逐一重新执行C01—C07当前完整case/assertion并生成v2回执，G0再审查这些当前回执后才能关闭。若旧P00输出缺失或不匹配，先重做P00 baseline，不能继续借用旧回执。该安排只拆除P01建立验证器时的引导循环，并不减免P00最终验收。

## 验收与审查节奏

回执是大节点的证据汇总，不是逐个小修复的停工手续。实施者可在接口/契约稳定后连续完成同一依赖链中的实现；只要某任务的owner case尚未在计划的里程碑批次中验收，其状态保持未关闭即可。进入依赖关闭或G0—G6放行节点时，再为该节点一次性整理当前任务回执、共享测试批次和合并独立审查结论。一次批次可支撑多个任务和assertion；回执仍保留owner、selector、实际结果、源码hash与依赖关系，不能把一项宽泛“全绿”推成全部通过。

独立审查的单位是里程碑候选/重大风险边界，不是普通任务卡。一个审查批次覆盖多个任务快照，并须列明每个任务的范围、结果与发现；各task receipt只记录其对应结论并指向这次审查批次。若现有路径校验要求任务专属报告路径，可将同一批次的任务结论保存到相应task目录，但不得因此重复审查或重复测试。这样不会要求审查者重复阅读同一变更或重复运行同一套测试。若个别任务确需提前关闭依赖门，可对该任务及其直接受影响范围做一次定向验收，不扩大为全仓回归。

## 必需绑定

| 字段/证据 | 绑定规则 |
|---|---|
| `task_id`与`plan_version` | 指明回执对应的owner任务和产生时计划版本。版本名用于追溯，不单独决定是否过期。 |
| `plan_sha256`与`case_catalog_sha256` | 记录生成回执时完整计划包原始字节hash，作来源上下文；不因无关任务/用例变动而自动使其他owner的证据失效。 |
| `task_spec_sha256` | 规范序列化当前完整任务卡（含case_ids、依赖、owner、允许路径、完成/回退条件）的内容hash；不同则回执stale。 |
| `owned_case_bundle_sha256` | 对本任务拥有的所有case按ID排序后做规范序列化，包含`id/given/when/then/assertions/requires_tasks/owner_task/status`；任何owner case变化均需重验。 |
| `referenced_case_bundle_sha256` | 对`case_ids`中由上游任务拥有的回归引用case按ID排序后做同字段规范序列化；每个引用owner必须处于本任务传递依赖闭包。存在此类引用时必填，且定义变化必须使下游receipt stale。仅本任务自有case的旧v2回执可以缺省此字段。 |
| `global_boundaries_sha256` | 对`global_boundaries`有序规范序列化的hash。硬约束变化使全部受其约束的回执stale；新增无关owner/case不会。 |
| `case_results` | 必须与任务卡case_ids一一对应，无缺失、重复或额外case。每个case必须包含全部稳定assertion ID。显式case.assertions使用其ID；否则按`then`顺序派生`<case_id>.T01`、`T02`等。 |
| 每条assertion测试证据 | `status`、实际测试选择器、完整可复现命令、退出码、日志相对路径/SHA-256、skip数、必填测试阶段（`unit/contract/integration/e2e/review`）、网络/费用/临时环境清理证据。命令只记录，绝不执行。 |
| `implementation_snapshot` | 以仓库身份和规范相对路径列出源码、schema、配置、fixture及测试文件的SHA-256。路径必须在显式登记的仓库根/证据根内。 |
| `independent_review` | 封存前实现review的报告路径/hash、审查结论、对应的完整实现snapshot hash及未关闭问题级别。reviewer不得只审摘要，且报告不得引用尚未生成的receipt/sidecar hash。 |
| `dependency_evidence` | 每条普通依赖引用其当前v2 receipt及验证结果；历史上下文边引用限定路径/hash manifest，标记`context_only`且永不贡献依赖关闭状态。 |

完整计划和case目录hash保留以便追溯。任务spec、自有case bundle和全局硬约束hash始终参与有效性判定；当任务卡引用上游case作为回归检查时，还必须校验`referenced_case_bundle_sha256`，并拒绝owner不在传递依赖闭包内的引用。新增无关行业模块或另一owner的case不会要求重跑完全不受影响的任务；本任务定义、已引用验收内容或全局硬约束变化则必须重验。旧v2收据仅在没有上游case引用时可省略引用hash，以保持向后兼容；存在引用但未绑定内容的旧收据保持blocked，需重新生成证据。

## v2文件形状与哈希

回执文件是严格JSON对象：`schema_version="2.0"`、`core`、`core_sha256`。Core即封存边界；`core_sha256`为core canonical JSON字节的SHA-256。sidecar、封存后证据review和运行日志必须在core文件外，不能增加在core或顶层wrapper里。权威schema为`schemas/quick_scan/task-receipt.schema.json`，附加字段默认拒绝。

`canonical-json-sha256-v1`固定使用UTF-8、对象键按Unicode码点排序、紧凑分隔符、数组保留声明顺序、禁止NaN/Infinity；hash字段为64位小写hex。解析输入时拒绝任何JSON对象中的重复键，避免不同消费者对同一原始回执采用不同值。涉及金额/小数的字段以十进制字符串表达，不能依赖跨语言浮点序列化。后续C06若复用该算法须显式声明版本；不兼容改动走单独契约变更。

完整plan和case catalog字段保留生成时原始文件字节SHA作为出处；task spec hash对完整任务卡规范JSON求hash；owner bundle及非owner引用bundle各自按case ID排序，再对上述字段规范JSON求hash；global boundaries保留声明顺序后规范JSON求hash。自有case hash始终是新鲜度关闭门；存在上游case引用时，引用bundle hash也必须存在且相符。Receipt v2 wrapper自身的`core_sha256`必须与core匹配。

相对路径使用正斜线。校验器路径引用需要显式`root_id`，调用者登记本地仓库与证据根；回执不得扩大登记根。拒绝绝对路径、盘符、`..`、反斜线、敏感目录/文件名、敏感目录本身作为登记根、跨根符号链接、解析后指向敏感子目录的根内符号链接、硬链接、目录及非普通文件。每次读取还必须先通过用途策略：receipt/plan/catalog仅接受操作员显式传入的控制文件路径；源码快照必须匹配当前任务卡的`allowed_changes`及快照类型；测试日志必须位于`docs/implementation/contracts/validation-<task_id>-*.log`；独立审查报告必须位于`docs/implementation/reviews/<task_id>/`；历史manifest路径必须与计划登记边完全一致，其条目只允许manifest对应的固定路径；普通依赖只能引用`receipt-<dependency_task_id>.json`。用途、任务范围或敏感文件检查先对回执给出的路径执行，解析符号链接后还必须对最终根内目标重跑相同策略；任一检查失败时必须在读取字节前阻断。公司目录、secret、财报raw、完整web正文不属于允许的验收材料。校验器只输出稳定阻断码、状态和hash，不输出命令、日志正文、公司材料或密钥。

## 状态推导

回执不接收调用者自报的最终`verified`作为事实。校验器逐assertion重算：

- `passed`必须有真实测试选择器、非空复现命令、命令退出码0、日志存在且非空、日志hash相符、skip=0、隔离运行ID及清理验证、网络/费用证据；不得只用空selector或整套未细分测试命令替代具体atomic assertion。
- `failed`、`not_run`、未解释skip、缺输入或证据环境不具备时保留失败/partial/blocked原因，不得折叠成通过。
- 当前receipt v2 schema与只读校验器不提供可获批的`not_applicable`通过路径；任何断言状态不是`passed`都会阻断关闭。不得用`not_applicable`绕开owner case或固定负例。未来若需按case条件豁免，必须先版本化扩展schema、case契约、理由/审批证据及校验器，并增加正反例测试；在该扩展发布前，所有任务一律不得以`not_applicable`满足关闭门。本版P01全部case/assertion均为必需。
- 只有所有owner case及其每条必需assertion passed、普通依赖可验证、独立review与当前implementation snapshot完全匹配且无未关闭P0/P1/P2时，输出`eligible_to_close=true`。
- 任何实现文件在review之后发生变化时，review立即变为`review_stale`；旧报告保留，但不满足当前闭环。
- 完整计划/catalog provenance hash仅用于追溯；任务卡、owner case bundle、global boundary变化则使回执失效。允许向无关owner追加任务/case而不使本任务失效。
- 普通依赖没有当前v2 `eligible_to_close=true` receipt时，本任务不能关闭。历史上下文清单只证明读取对象的完整性，不把其旧receipt升级为当前证据。

对每项复杂验收，`assertions`应以稳定顺序细分不同公开入口、正反分支、失败注入和边界。一个参数化测试函数可以服务多个assertion，但receipt必须列出各自的selector参数/子测试ID和实际结果，不能只给一个整体pytest命令。

## 跨版本兼容证据的职责边界

通用receipt v2只证明任务断言的测试选择器、执行结果、日志和源码快照，不表达跨版本兼容矩阵，也不验证release ID/hash、action或兼容窗口。凡涉及跨版本兼容，必须由对应的兼容性契约/专用评估器保存并验证完整声明；receipt中的测试日志只能证明评估器测试曾运行，不能替代该语义校验。EVO-83定义的窗口规则属于专用兼容性评估：被测producer/consumer release ID/hash、action和UTC测试时刻必须绑定；支持窗口为`valid_from_utc <= now < valid_until_utc`。只有字段存在且`expiry_policy="non_expiring"`时，`valid_until_utc=null`才表示无到期；缺字段、时区不明、区间倒置/重叠或当前时钟不可信均失败关闭。历史读取、新写、付费派发、迁移、回退必须分别检查对应声明。

兼容期限届满不会自动删除归档或观察。旧内容若没有仍可核验的archive reader，返回`needs_review`，不可回退当前schema解释、更改旧答或生成新派发。

## P01两阶段审查与封存方向

1. 冻结P01源码/schema/测试的完整implementation snapshot；独立实现review报告绑定其snapshot hash，记录reviewer身份/角色、独立性/分离依据、结论及问题级别。报告不引用receipt或sidecar hash。
2. 将封存前实现review的路径/hash写入receipt core；计算canonical core hash并封存回执。此后不改core与pre-seal review。
3. 执行只读CLI。验证输出到stdout，可由调用方重定向到独立sidecar文件；sidecar绑定core hash、validator hash、eligible结果和UTC时间。校验器本身不写文件。
4. 由不同的封存后证据review核对core与sidecar，并在receipt core之外绑定二者hash。该报告与sidecar都不得反向写入core或封存前review；否则形成hash cycle。

P01关闭包由receipt core、detached sidecar与封存后证据review组成。缺少任何一环、hash不匹配或review仍有未关闭P0/P1/P2时不能关闭。

## 只读命令与detached sidecar

命令路径由root ID与正斜线相对路径构成；操作员显式登记本机仓库/证据根，回执不能自行扩大root：

```powershell
python -X utf8 scripts/task_receipts.py verify `
  --root iqs=C:\Projects\invest-quick-scan `
  --receipt iqs:docs/implementation/contracts/receipt-P01.json `
  --plan iqs:docs/implementation/tasks.json `
  --cases iqs:docs/implementation/acceptance-cases.json
```

验证结果只写stdout，调用方如需保存detached sidecar须在命令外显式重定向到任务允许路径。JSON sidecar包含`schema_version`、`status`、`eligible_to_close`、`blockers`、规范`core_sha256`、原回执文件`receipt_sha256`、正在运行的validator文件`validator_sha256`、UTC时间及逐case/assertion的`case_results`审计投影。case与assertion都保留输入的`reported_status`，而`status`/`validation_status`只在其所有子断言、日志单次读取后的SHA校验及相关字段校验均通过时显示passed。每条assertion投影列出稳定ID、有效selector、测试阶段、退出码/skip数，日志的安全相对路径、期望/实际SHA-256与hash校验结果，以及阶段、selector、日志、隔离清理、网络证据等布尔检查项；不回显命令、日志内容或network evidence原文。含控制字符、过长或疑似密钥的selector及测试日志路径会被拒绝且不回显。不可安全展示的路径会留空并附稳定错误码。退出码0仅表示eligible；部分/阻断/旧v1返回非零。`legacy_historical`不尝试读取计划依赖或升级旧receipt。

## P01上下文manifest与验收范围

P01 manifest仅枚举现有P00 baseline report和P00 v1 receipt的规范相对路径与原始文件SHA；manifest本身是receipt中历史依赖证据的hash目标。计划需显式allowlist P01→P00边与manifest路径。必须证明清单内P00 receipt仍为非v2历史回执；任何内容变化、缺文件或路径越界都阻断P01上下文复用。该状态只为`context_only`，绝不满足P00当前依赖、ready或G0/G6关闭门。

P01仅在临时证据根内测试receipt schema与真实只读校验器：合法完整回执、无关计划增量、漏/多/重复case或assertion、task/case/global-boundary hash变化、日志缺失/篡改/空白、非零退出、skip、审查过期、路径逃逸、v1历史receipt、bootstrap历史上下文依赖和敏感字段均有独立固定oracle。校验器必须证明不会执行回执命令或改变任何输入文件。P01自身receipt core由新校验器在源码/测试冻结、封存前独立实现review完成后封存；之后生成detached sidecar，再生成封存后证据review。封存后的两份工件不反写receipt或前置review，保持方向单向且无自引用。
