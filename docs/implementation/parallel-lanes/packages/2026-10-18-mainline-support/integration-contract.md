# 三包共同契约：独立、离线、可追溯、可演进

## 1. 目录与输入冻结

只有各卡指定的新 Lab 是可写根。不得写 IQS/PWF、StockQA、StockWiki、company-wiki、旧 Lab 或另两包；不要在共享安装镜像中更新文件。测试子进程环境去掉 provider 凭据，只允许必要的系统/Python路径，不读用户配置、.env、凭据或 secret-bearing JSON。

本波唯一外部输入是 [input-catalog.json](input-catalog.json) 中本 package 的文件，全部来自 IQS commit `d788a10e665440d68ad323f77711db83ea683e07`。目录列 repository、commit、路径、Git blob OID、原字节数和 raw SHA-256。使用 `git cat-file blob <commit>:<path>` 的二进制 stdout 读内容，逐项核对后复制到 Lab `vendor/iqs/`，保持相对目录。不要从工作树 latest 复制、转换换行、执行源仓脚本或 checkout 源仓。只允许在本 Lab 的 vendor 中调用锁定纯 validator。

在 `inputs.lock.json` 写闭合协议 `iqs.support_input_lock/1.0.0`，required：`protocol,package_id,source_repository,source_commit,files,created_at_utc`。files 的每条闭合为 `path,blob_oid,bytes,sha256`；只列本卡所分配的完整清单，不列自身。保存 input-catalog 原件及其 raw SHA。source commit 不在本机时可报告 missing_git_object，不切换源分支或猜测替代。目录、schema及合成数据由本包创建，标 synthetic；不伪装成源仓正例或金融参考答案。

输入锁可由实施者依目录直接生成，这是离线来源锁，绝不充当发送许可、owner authority、参考答案审核或预算批准。三包完全不调用模型/搜索/Fetch，不需要 dispatch lock。预检锁、路径、依赖后可直接实施。

本包新增 fixture/casebook/policy 属于自己的功能 payload，不加入外部 inputs.lock。另建 `fixtures/catalog.json`，逐文件记录安全相对路径、bytes/raw SHA、synthetic 标记和手工预期依据；catalog 不含自身或 expected。测试预期使用独立 `fixtures/expected-catalog.json`，业务 audit/compare 命令不得读取它；仅 evaluate 在被测工具输出后读取预期。输入锁证明来源未漂移，fixture catalog 证明测试输入未漂移，两者不混称 owner 信任。

若现有纯 validator 有确定缺陷，先保留最小反例，正常输出 upstream_validation_failed，不复制修一份同名 validator 来通过，也不去源仓修复；该异常不阻止交付独立工具的其他已证明范围，但必须列为 limitation 且不得把受影响规则标 passed。

## 2. 所有公开 JSON 与 CLI 的共同约束

包需提供 Draft 2020-12 本地 schema：每个对象 additionalProperties=false，required 全列，枚举/范围/长度明确；重复 JSON 键、NaN/Infinity、bool 冒数值、非法日期、未知 protocol 版本必须拒绝。schema 不能靠联网解析 $ref。已知旧版只读保持，新增语义升级版本；不原地重写旧 golden，稳定 ID 不复用新含义。

共同来源引用 `ArtifactRef={path,bytes,sha256}`，safe 相对 POSIX 路径，禁止绝对、盘符、反斜线、空组件、`.`/`..`。文件只从调用方显式指定的输入根解析，原字节哈希校验，不访问任意 URL。重解析点/junction/symlink/硬链接越界用实际 filesystem case 验证，无法稳定测试的平台情形明确 unsupported，不能伪造 passed。输出新目录通过原子发布，已存在或越界则拒绝、不覆盖旧数据。

所有 result 顶层闭合公共字段为 `protocol,package_id,input_lock_sha256,data_kind,production_qualified,source_refs,limitations,payload`。data_kind 固定 `offline_candidate`，production_qualified 固定 false。payload 的精确字段在各卡定义；状态、计数由实际观察得出，不从 expected 标签抄回。所有引用闭合、唯一 ID 检查必须在 schema 后额外做。

共用 CLI 行为：`--version`/`--help`，stdout 成功 JSON、诊断 stderr；exit 0=输入有效且报告生成，exit 2=输入/版本/路径非法，exit 3=输入可读但依赖/分析无法执行。**发现兼容问题/摘要丢失/关系冲突是成功诊断结果，可 exit 0，不等于业务通过。** `evaluate` 可用 exit 1 表示与冻结测试预期不符。所有命令禁网、无 DB、无 subprocess shell、无动态执行输入，出错不留下正式成功结果。

每包实现 `validate --input <file> --input-root <root> --source-root <vendor/iqs> --lock <file>`、卡中业务命令，以及 `evaluate --cases <file> --input-root <root> --source-root <vendor/iqs> --lock <file> --output <new-dir>`。source-root 只解析原 source lock 的安全相对路径并加载其纯 validator/schema，input-root 只解析本次 request 的 ArtifactRefs 及其 fixture catalog；两根独立校验，不用 cwd 猜测。RELEASE 对锁定真实 release 的 request 可显式将 input-root 和 source-root 都指向 vendor/iqs，此时只认来源锁而无需 fixture catalog。新合成 release/request 放 fixtures 并认 fixture catalog；源 validator artifact loader 按显式 request 选择本次根与锁，不跨两根猜同名文件。解析器通过显式参数取文件，不隐式扫描其他仓。交 Python API，使用独立 module 名；依赖声明精确版本/范围和离线安装说明，不复制共享引擎运行时。

## 3. 整包 TDD、集成与端到端测试

实施先写有投资/工程含义的失败案例和预期依据，记录至少一个 RED→修复→GREEN；不要求每个函数单独审查。预期标签保存 `fixtures/expected/`，工具不得读取 expected；evaluate 在工具完成后单独比较。独立 reviewer 至少新增两个未事先给作者的反例，并验证一个正常限定案例不被误杀。

单元验证算法/闭合/版本；集成实际调用锁定源 validator 或在两个独立 fixture 的契约边界调用本包 API；E2E 必须从公开 CLI 读文件到新 result，再由公开 validate 读回，含随机 cwd、中文空格路径、无网和最小环境、损坏 hash、重复 JSON 键、已存在输出、一次真正失败路径。不可只测试内部函数或预写 JSON。

每次 run 使用本 Lab 新建 `.tmp/<run-id>`，测试下载数必须 0。记录开始时自有资源、实际创建文件/PID/端口、结束与失败 finally 清理，清理后确认自有临时根不残留。输入与源仓 hash 复核保持。只清可证明本 run 创建且已结束的资源；不清全局缓存、未知目录或他人进程。必须保留需要的精简测试/审查证据到 artifacts 后再清临时工作文件，清理失败如实保留和说明。

## 4. 交接目录与 commit 的准确含义

`docs/handoff/<PACKAGE-ID>/` 必有：`handoff.json,report.md,input-catalog.json,inputs.lock.json,tests.json,cleanup.json,integration-map.md,inventory.json,review/invocation-evidence.json,review/round-XX.json,review/round-XX.md,review/fixes.json,review/final.json`。代码/数据/schema/测试与必要 CLI 输出也须包含在最终 payload 清单中。

先提交真实最终功能 payload（code/schema/data/tests/已冻结输入）；独立 reviewer 对这个 payload commit 审查。之后仅可新增/修正交接元数据提交，分别叫 payload_commit 和 handoff_metadata_commit。handoff_metadata_commit **不得在自己的同一文件里猜写自身 commit**：文件写已存在的 payload_commit、reviewed_commit、可选已存在的上一个 metadata commit，最终 handoff HEAD 由总控验收报告外部绑定。若代码/数据/规则/测试在 review 后改变，必须产生新 payload commit 并由 reviewer 复审；只修描述/清单/hash 元数据时做一次 metadata-only 独立核对即可，不重跑整套不变测试。

inventory.json 只列功能 payload 与固定输入/证据文件（文件角色、bytes/raw SHA），**明确排除自身、最终 review/handoff 元数据和会随登记变化的报告**，防止哈希循环；这些排除项由外部接受报告绑定。完整 Git tree 仍是交接依据，排除不能用来隐藏业务文件。报告列清已审 payload、当前 metadata HEAD 需总控外部绑定的规则，历史轮次不能覆盖或混称当前。

handoff.json required 闭合字段：`protocol`=`iqs.support_handoff/1.0.0`、`package_id,work_root,branch,payload_commit,reviewed_commit,input_lock_sha256,inventory_ref,test_summary,review_final_ref,cleanup_ref,artifacts,status,limitations`；status 只可 `ready_for_controller_acceptance` 或 `incomplete`。artifacts 是 ArtifactRef 数组。review_final_ref 是 final.json 的实际 hash，不反向要求 final.json hash handoff。未独审通过不得 ready。

## 5. 必须真正调用独立 agent 后才能交接

作者在最终大节点调用真正不同的独立 reviewer agent，要求全面检查需求覆盖、核心代码/数据、公开 schema/CLI、反例、依赖复用、离线安全、输入与清理、全部工件一致性，并独立复跑关键 E2E。不得由作者扮演 reviewer、自写一段“独审通过”或只运行 schema 冒充人工独立 review。

invocation-evidence.json 记录平台、作者 task/session ID、reviewer task/agent ID、UTC 实际调用时间、原始调用/返回或平台可打开 artifact 引用、审查输入 commit/锁、原 artifact bytes/hash；平台拿不到某项就填 null 并说明，不伪造。作者和 reviewer ID 必须不同且有可核验调用证据。review/round-XX 保留原始 findings、严重性/复现/路径/依据；fixes 逐项关联修复 commit 和复验结果。

final.json required 闭合：`protocol`=`iqs.support_review/1.0.0`、`package_id,author_task_id,reviewer_task_id,reviewed_commit,input_lock_sha256,verdict,open_findings,round_refs,test_evidence_refs,limitations,reviewed_at_utc`；verdict=passed|changes_requested|blocked。所有有效发现均修复并让同一独立 reviewer 复审到 passed、open_findings=[]，才可交接。独审平台不可用时 status=incomplete 并列具体阻塞，不冒充 passed，也不请求重复权限。

不设置新生产门。总控收到候选后在主线大节点整合；本包结果不能批准重新发送、释放未知费用、修改正式关系/分数或启动 2000 家扫描。
