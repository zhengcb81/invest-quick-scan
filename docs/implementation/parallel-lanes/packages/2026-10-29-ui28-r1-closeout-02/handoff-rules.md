# R1补交02共同约定

## 范围和版本

1. 只写自己原Lab，原分支继续。其他Lab、原UI/IQS/StockWiki/StockQA、共享PWF、实际名单/库/预算禁写；不恢复收费扫描/生产接线。不要派发其他任务或给其他harness发消息。
2. 正式package_id仍原R1、remediation-01现行路径仍不变，使用现有 `verify-inputs/demo/validate-delivery` 与已实现 `--lock/--remediation-lock/--handoff/--package-id` 参数，不另造协议、工具或-R2要求。新元数据可以在同一现行路径发布，但**先用原Git对象及必要submission-history快照保留本次原件**。旧round/invocation原字节保留，新增真实复核记录和引用，不能把旧调用改写成新调用。
3. 新inputs.lock仍为 `iqs.ui28_remediation_inputs/1.0.0`。deliveries是本轮mutable目标开工基线（61982/be7），修后按最终新C校验，不能要求旧worktree hash不变，也不能修改旧基线求绿。原21只读锁仍为680c4d7d…；additional只读源保持。最终review/invocation的input_lock_sha256应绑定**本轮新锁raw SHA256**，report另列原21锁与上一轮R1锁042326供历史追溯。实际分支/HEAD若又变，先核writer和差异，禁止reset/stash/覆盖；仅本地索引配置不是业务修改。
4. 所有源码/schema/测试/工具按最终新payload C冻结；测试在本人隔离Git副本（可从自己Lab本地无网络、无hardlink克隆）执行，不能借祖先IQS index。生成log/报告/最终manifest和handoff的metadata M不能再改C功能文件。manifest如在M层生成，要明确按C逐文件核hash，不用未来C造成自指。Git commit/blob为40hex、SHA256为64hex，blob/工作树字节口径明确。

## 复现、修复和审查：仅三个大节点

- 开工核锁/当前writer → 运行卡内有效反例观察原行为红；不缺src、不伪造调用或固定预期输出。
- 在原模块边界最小修复，并将反例移入自己Lab永久回归；合并相邻测试，不重做已修的四/五个原业务设计，不重跑跨仓小时全套。
- 受影响功能和本包正常浏览器mock回归齐备后，冻结C，真正调用**非作者的独立agent**对最终C做一次集中完整审查；所有发现修尽后passed/open_findings=[]再交。若review后代码/validator改变，要按最终delta真实复核，不能仅改版本号或写一句“byte-identical”。不对每个函数加微审查门。

根已重跑本轮发布的portable counter：COMPARE启动失败1F、UNIVERSE async2F，均是实际断言红，0真实browser/owner/model，临时probe根已清。`IQS_R1_COMPONENT_ROOT`指向自己Lab/隔离副本即可运行 `node --test evidence/<...>.test.mjs`；复制到自己Lab后改import，保留核心不变量。startup反例只stub start边界为reject，close为真实调用的计数spy，未启动失败Chrome；其finally只删自己刚创建且已核resolved-parent的probe根。async反例仅gate真实crypto.digest/外部传输，再继续真实hash和状态逻辑。

CLI拒绝反例在本人临时副本改元数据/复制合法handoff到本人checkout-sibling模拟；finally恢复并清理。不要用真实库/owner/用户文件或删除别人文件证明路径边界。额外caller env只用普通非凭据变量并恢复，不继承/打印key、token、secret。

## 必须真正闭合的交接

- `handoff.json`符合既有handoff1.0.0闭schema，含全部scope字段（包括out_of_scope_writes），最终public CLI的shape/reference预检应通过，但不以它代替真实审查。
- final必须给有效 `invocation_ref/round_refs/fixes_ref/test_refs`（原卡已有要求），校验器真正跟随这些引用并查存在/必要字段/实际hash；不能只猜约定文件名，不能tests/fixes丢失还valid。
- handoff C/review.snapshot_commit/final C/实际最终invocation C/它引用的**有效最终round C**一致，reviewer与author不同，final/invocation/最终round reviewer一致。历史round可保留旧C；最终引用旧round加一个final_payload_commit别名不能替代真正最终复核。
- 原reviewer可以在独立会话中真正复核新C/delta，但须有对应实际调用或followup/round、精确文件hash与测试证据。初始化时间早于C本身不是自动判错；不能用未实证的“validator没变”豁免实际变过的validator。
- reviewed_file_hashes是具体文件的64hex实际SHA，evidence_path/evidence_sha真实匹配。不同metadata字节层的例外明确写出；不能接受文字/null/错误64hex/缺引用。validate-delivery应对本卡列出的错误样例明确拒绝，而不是自报valid等于真实owner/金融资格。
- 新report映射每个本轮ID→文件→有效红/绿→最终证据。tests.json记录实际argv/cwd/UTC/exit/pass/fail/skip/logSHA，不能照抄182/254或把多次补跑重复计数。原CLI环境PATH漏PowerShell/旧DNS误挡127的历史记录保留为环境问题，不当业务缺陷。

## 安全和最终交回

临时cwd/env/cache/profile/所有输出只在本人owned根。外网拒绝而本人loopback可用，COMPARE默认18771/后续动态，UNIVERSE默认18772；不碰8765/8766或用户浏览器、其他PID/端口。成功/启动失败/超时/取消均finally，删除前严格验证resolved路径和本次拥有记录，只用一套原生文件API，不跨shell拼删除命令。保留必要薄证据，清理本人进程/端口/temp/profile。

最终现行handoff仍各自remediation-01，package_id仍原R1。本轮不新增交接文件集合：report/tests/artifacts/cleanup/review/invocation/round/fixes/final齐备；新独审记录可以新文件名，当前final明确引用，旧历史不改。主业务未接生产，production_ready/financial_qualification_granted仍false。总控按本轮manifest及实际新C重新验收，用户尚未派发前不要自启动。
