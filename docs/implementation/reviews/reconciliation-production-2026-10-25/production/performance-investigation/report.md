# 原 owner / StockWiki 公开 CLI 性能调查（只读）

- 调查者：`/root/review_bank21`；日期：2026-10-25。
- 范围：当前源码、本轮运行日志/配置元数据、精确本任务进程元数据。只在本目录写薄报告；没有运行产品校验器、测试套件、数据库查询或付费/API请求，没有改源码/PWF/生产数据，也没有结束进程。
- 源码SHA与运行证据绑定：`metadata.json`，由只用标准库读取文件的 `collect_metadata.py` 生成。CodeGraph已优先查询；外仓新符号未索引，主仓查询又命中历史intake同名符号，因此随后直接读已知的当前源码，未把历史拷贝当现状。
- 留档维护：metadata已追加活动文件覆盖后的两次preflight观测；`collect_metadata.py`是最初单次采集脚本，后续不得直接重跑来覆盖这份多次观测记录。新增观测应追加或另存新文件。

## 结论

**慢点在权限读取链条中嵌套的重复纯校验与进程启动，不能归因于LLM。最小第一刀可以只减少同一不可变题库发布包的重复加载，不缓存权限。**

真实单题preflight有两次不同输入锁的观测，二者均 `model_http=0`、`search_http=0`：

| 观测 | 耗时 | source_pins_sha256 | 当前可复核证据 |
|---|---:|---|---|
| 首次读取的旧driver观测 | 116.1734865秒 | `a04461bd157c1922716cf266060eaa4c7190f6ee31f1084554556d8c63c76f94` | 本目录 `metadata.json` 的 `observed_preflight` 保留了当时读取的完整JSON内嵌快照；原路径已被覆盖，不能用现在该路径的文件证明116秒 |
| 后一次、该批次最终preflight | 80.9808152秒 | `39d92b881a890b99758ae8b7a4fcf7c8069fda1b5225911f461b6b6d26c5c80b` | `runs/r25-live/failed-pretransport-01/preflight.json` 归档文件；校正时主路径 `runs/r25-live/preflight.json` 也为同一80秒内容；确切文件SHA与快照见metadata新增记录 |

**期间没有实施本报告建议的性能代码，且两次pins不同；116→80秒不能称为性能优化成果或受控A/B。** 原主路径是活动运行文件，不能把它的当前80秒内容仍标成116秒实物。首次116秒的证据类型是本调查已保存的内嵌读取快照，不冒称保存了原始文件字节。

两次计时都从驱动main入口开始，包含import/输入pin校验/owner准备/任务构造/服务初始化/engine preflight，**不是prepare_execution单个函数的独占耗时**。现有证据没有逐函数计时，不能伪造哪一步占了百分之多少。

调查期间 `engine-fix/native-actual-finalization.xml` 被活动总控更新：最初读到旧的179.598秒/80秒install-delegation等待超时，随后最新字节已经变为软件E2E **1 testcase通过、0 failure/error，case645.111秒、suite648.869秒**。`metadata.json`绑定的是最新通过的XML SHA `b6ee1a7d728d5f92e912b25108b969a9400ce200f1ae4cf264a3ccfaca855514`，不能继续把旧超时当当前失败，也不能把脚本化软件E2E当真实模型准确性。

## 1. 可定位的串行进程链

```text
run_live.main
  prepare_execution
    RefreshAdmissionService.__init__ -> _ledger_ready
    read_registered -> _ledger_ready（同次准备重复一次）
      bridge.inspect(current_permissions)
        StockWiki refresh_owner_cli（子进程，80秒上限）
          delegated inspect / 当前权限、grant和revocation实时读取
          policy_reader -> IQS refresh_contract_cli（反复启动子进程）
          routes.get_for_execution
            IQS route_store_handoff execution（子进程，60秒上限）
    OwnerRefreshClient.prepare
      StockWiki route-current（子进程，120秒上限）
      StockWiki route-refresh（子进程，120秒上限）
        SubjectRefreshView -> get_for_execution
        plan_module_refresh -> get_for_execution（同一输入再次验证）
      StockWiki route-anchor（子进程，实时漂移读取）
  create_company_scan_task -> owner.check（进入和退出各一次）
  OwnerResearchServices.__init__ -> owner.check
  engine._scan_preflight -> owner.check
```

出处：StockQA `quick_scan_refresh_execution.py:143,292`、`quick_scan_refresh_admission.py:149,179,307`、`quick_scan_owner_refresh.py:147,245`；IQS `shared_company_task.py:263,450`、`shared_company_engine.py:606`；StockWiki `quick_scan_refresh_owner_cli.py:220`、`quick_scan_subject_refresh.py:23`、`quick_scan_module_refresh.py:235`。

单次 `prepare_execution` 本身至少有 **4次StockWiki子进程**：consent inspect、current、refresh、anchor。显式可见的4次额外owner.check又各走consent inspect+anchor；因此当前preflight正常路径可静态识别至少 **12次StockWiki进程边界**，尚未计算其内部的IQS子进程。此为源码推导下界，未做动态profiler观测。

delegated inspect重复policy校验也很具体：`DelegatedApprovalService.inspect_confirmation:547` 前后各 `_grant`；每个grant会由 `_native_principal` 和 `_binding` 各读policy。中间 `RefreshApprovalService._recheck_current_permissions`、`RefreshPreviewService._build` 与尾部inspect再次读policy。正常路径合计约 **9次policy_reader**，而CLI的policy_reader每次都调用公开 `IqsRefreshContract.validate_policy`，各另启一个Python进程。**policy字节实时重读有必要；重复启动进程验证同一schema结果没有必要。**

补充：Windows principal是 `quick_scan_refresh_principal.current_principal` 直接读取本进程token/SID（ctypes），不是whoami子进程。`QuickScanStore.__init__`不自动迁移。不能把耗时错误归咎于“每次身份读取都启动系统命令/迁移库”。

## 2. 最明确的放大器：一次路由执行校验至少9次整包读取

`scripts/route_store_handoff.py:55` 正常execution路径：

| 入口 | 间接validate_route_snapshot次数 |
|---|---:|
| validate_route_bundle显式校验route | 1 |
| question_manifest._validate_published_manifest -> published_selection | 1 |
| 同manifest -> validate_recorded_route_execution | 1 |
| 当前执行 -> validate_route_for_execution -> validate_recorded_route_execution | 1 |
| 合计 | **4** |

每次 `routing.validate_route_snapshot:778` 先 `registry.load_package`，又 `registry.load_routing_policy`；后者 `module_registry.py:317` **再次load_package**。manifest自己在 `question_manifest.py:131` 另load一次，因此 **4×2+1=9次**。

每次load_package都做：包hash与格式 -> 所有归档模块bytes/hash/schema -> 完整registry和依赖图 -> contexts -> routing policy校验。`module_contract.validate_release`和随后`validate_registry`都逐模块调用validate_module。即使本次只问IQS_05，当前manifest仅含common的24题，这条路径仍校验包内全部模块，而不是只看那24题。

若route带原搜索执行receipt，每次snapshot还通过 `build_route_request:273` 再load_package和load_routing_policy，静态下界会上升为 **17次**。**本次r25实际route.execution=None，适用9次，不把17说成已实测。**

## 3. 最小可测的优化顺序

### A. 先消除同一snapshot校验中的二次整包加载（建议第一刀）

`validate_route_snapshot` 已拿到经过load_package验证的 package/modules/release 后，使用该上下文加载并校验policy（现有 `_load_routing_policy(root,release,modules)` 已具备该实现），而不要再调用会重载整个包的 `load_routing_policy(package_id)`。可提供一个有明确“已验证上下文”类型的内部/公开辅助函数，避免到处跨层调用私有方法。

- 不加跨进程缓存，不减少当前权限/当前anchor/lease/预算读取。
- 一次execution路由校验的整包load下界可由 **9降到5**；这是调用次数目标，不是承诺墙钟下降44%。
- 反例必须仍拒绝：policy archive hash错误、policy版本与release不一致、未知依赖、被篡改归档、错误独立expected decision ID。

### B. 在一次公开validator调用内复用不可变校验上下文

将“发布包/route/manifest不可变内容正确”与“给定时刻和owner状态是否允许执行”拆开。一个内部 `VerifiedReleaseContext` 在首次验证后携带完整输入指纹，manifest选择、历史执行时间核验、当前执行时间核验复用相同已验证内容；当前时间/手动override到期/router当前兼容规则仍分别运行。

- 理想静态目标：一次route_store_handoff内相同release的完整schema/语义验证只做一次，而非9次。
- 不接受调用方JSON自报verified，不把内容hash当身份/收费授权，不把history验证结果当execution授权。
- 缓存键至少涵盖 resolved release root、package与lock确切bytes hash、全部被读取archive和policy hash、schema集合hash、validator/renderer实现指纹；同ID但不同路径/文件字节不能共用。
- 不能只用package_id、mtime或TTL当key。命中仍验证文件路径约束和实际bytes hash，避免同名归档就地篡改被缓存掩盖；返回只读结构或deepcopy，避免调用者修改缓存。
- 先用**单次调用内**生命周期，不急于新增持久缓存、常驻daemon或跨仓Python直接import，保留现有公开CLI信任边界。

### C. 缓存纯policy/schema校验，仍实时重读policy与撤销记录

在StockWiki一次CLI进程内，policy_reader每次继续安全读取policy字节，比较前后变化；对同一确切policy bytes hash+schema/validator code fingerprint，只复用纯格式校验结果。新字节重新走原公开IQS validator。类似可复用已按schemahash编译的jsonschema validators/Registry。

- 正常delegated inspect的9次相同policy schema子进程可降为首次1次，前后principal、membership、grant/revocation、policy字节和当前anchor仍实时读取。
- 不缓存 `_grant` 的授权结论，不缓存current_permissions DTO、QA预算quote或ledger水位，不把“同policy文本”当成“权限未撤销”。

### D. 最后才考虑减少外层进程边界

可在StockWiki原公开CLI增加受限的“准备执行所需只读组合”操作，在一个进程里读取current、生成原refresh plan、末尾重新比对anchor/identity/policy。继续由原owner软件执行，拒绝drift，不产生新的executor/批准系统。它比A–C接口面更大，应后做；不要为了提速直接从StockQA跨仓import StockWiki内部模块，也不要先搞共享守护进程。

## 4. 超时与进程生命周期

当前上限是分层且不传总deadline：StockQA consent外层80秒，OwnerRefreshClient120秒，IQS subject/route CLI通常60秒，StockWiki QA inspection子调用40秒。外层80秒内可能串行执行多个60秒子操作；单个子操作均未超时也可能使外层超时。旧测试install-delegation超时与此结构一致，**没有逐阶段profile，所以不能声称已证明唯一耗时来源**。

单纯把80全改240只能减少拒绝，不能消除重复计算。后续可在原调用链传播单调时钟deadline和阶段名称：每次子调用用min(本层上限,剩余总时间)，并记录明确阶段。若发生timeout，应确认原subprocess实现能回收**自己创建**的进程树；Python对直接child的超时处理不能自动等同“全部grandchild均已结束”。本次精确scope进程快照未见活动匹配进程，不据此虚构孤儿进程事实，也未结束任何进程。

当前代码/输入已冻结用于真实验收，本调查不建议在cold/recovery之间悄悄打性能补丁。优化应另成明确提交、更新source pin后，用相同离线/真实小样本比较。

## 5. 建议验证包（后续实施时运行，本调查未运行）

只在两个大节点验证：纯校验优化完成后一次；原owner软件/实际preflight闭环后一次，不给每个小函数增审批。

1. 对同一只读fixture记录 `load_package`/`validate_module`/公开CLI spawn计数，以及phase elapsed；A要求9→5，B要求同一完整内容上下文只验证一次。相同输入输出DTO逐字节/规范化hash一致。记录冷/热两档耗时，不用一份总elapsed臆测逐阶段百分比。
2. 缓存预热后，分别改archive一个字节（可保持mtime）、改schema/renderer、切换不同root中同package_id、注入重复JSON键、修改返回对象；全部必须拒绝或重新验证，不能误命中。
3. 缓存预热后，模拟撤销grant、禁用universe member、身份revision/anchor变更、policy被改、预算耗尽、lease到期；原owner与SDK检查仍实时拒绝，调用次数和耗时记录不能靠跳过这些检查好看。
4. 对已有单题原软件E2E重跑必要case（脚本化wire、临时数据库），为优化前后另行冻结可比的代码/输入条件并记录零HTTP preflight。现有116.17秒与80.98秒是不同pins的历史观测，只作背景，不作为性能补丁A/B。确认原checkpoint/封包/恢复行为和原拒绝理由没有变化。测试Temp用短路径且自动清理，避免把Windows路径问题混作性能优化失败。

以上优化不降低金融准确性验证标准，不新增owner审批，也不复用过去权限结果延长任何lease或预算有效期。
