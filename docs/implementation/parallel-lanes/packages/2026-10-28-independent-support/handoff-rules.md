# 两包共同规则：输入、隔离、独审和交接

本文件和具体施工卡、manifest、inputs.lock 构成完整任务上下文。只在自己新 Lab 实施；禁止修改另一 Lab、主 IQS、StockQA、StockWiki、现 UI、共享 PWF、数据库、名单、配置、授权文件、缓存账本或服务。不得自动派发其他施工包/给其他 harness 发消息。可以调用本任务独立审查 agent，用户已要求真实独审。

## 1. 开工及输入冻结（一个前置节点）

1. 卡中 Lab 编卡时不存在。开始重新检查：若已存在非本人文件、Git 变更或活动 writer，停止报告，不覆盖/清理/接管。只创建自己的 Lab 和本地 Git，分支使用卡中 codex/ 名；不 clone/push、不改全局 Git 配置、不初始化外仓 CodeGraph。
2. `inputs.lock.json` 中只使用本 package_id 的 files，先校验路径在声明只读 repo 内且不是外跳 symlink/junction。工作树 raw SHA256 必须 **64 位 hex**、字节数精确；commit/blob OID 是 **40 位 hex**，blob SHA256 仍是64位。Git EOL过滤可能使工作树与 blob 字节不同，分别核查，不能混称。
3. 上游参考从冻结 commit/OID 的 Git blob 原字节消费到本Lab vendor（LF等按blob原样）；工作树 raw SHA/字节另作当前漂移守卫，不把CRLF/LF差异叫内容脏改。HEAD 因无关提交变化时记录新 HEAD，并证明每个锁定文件/对应 blob 没变；不跟 latest。锁定文件或 blob 有任何变化，停止、报告路径与旧/新摘要，由总控决定新锁。**不自行更新锁、不静默采用新源。** 预检结束/交接前再核锁。
4. 可将锁内必要参考原样复制到本 Lab `vendor/` 并标 reference-only；不执行/import 这些源仓 Python/JS/CLI，不 `pip install -e` 外仓，不连接原 SQLite/Store/owner。只实现和测试自己的 ESM 组件、mock adapter 与新 schema。源仓脚本/测试不得运行，命令示例只是总控后续接口。
5. 不读取/打印/留存 Windows 凭据值（API_KEY/token/secret/password等）、真实答案/上下文/私有思考、真实公司池或运行目录；允许读取TEMP/TMP/SystemRoot等普通运行环境，隔离子进程用普通变量白名单，凭据变量不继承、不打印环境全集；不扫描 Projects、自动挑2000公司、上网查身份或补名单。全部测试数据 synthetic，明确不是 owner golden/金融事实；例中实际公司名/代码只是用户要求的边界标签。

## 2. 实现约束与 CLI

- 无框架强绑定的原生 ESM；生产 API 用依赖注入的原 client，禁止第二套 fetch鉴权、owner、身份解析器、评分/金融计算器或数据库。Python仅用于本 Lab工具/测试/服务，Node仅本 Lab ESM；不自动联网安装。依赖缺失如实 blocked/partial，不 skip关键验收后声称完成。
- DTO/schema `1.0.0`：每个自身DTO对象 required 字段完整，`additionalProperties:false`；唯有明确标为原owner opaque payload的字段原样保留源协议，不把它的未知字段说成本Lab校验认可。支持 nullable 与 unknown，拒 bool冒数字、重复 JSON键、NaN/Infinity、非法编码、超限/路径逃逸。schema只检查本接口，不冒原owner语义验证。保留源值；UI使用 textContent/安全 DOM，不用原数据拼 innerHTML；URL仅允许明确安全协议。
- 公共 CLI：`python -B -X utf8 -m <卡中工具模块> verify-inputs|demo|validate-delivery ...`，另 `--help/--version`。必须显式 `--lab-root --lock`；所有输出 `--out` 是本 Lab 内不存在的新目录。stdout一份JSON，诊断stderr；退出 **0=该操作完成；2=输入/版本/锁非法；3=路径越界/输出存在/端口占用；4=能力或环境不足；1=测试/内部失败**。成功仅指该命令，不是生产准入。
- 零远端网络、零真实owner/收费/模型/搜索API；允许自己合成 mock server 在卡的127.0.0.1端口。网络审计区分本地mock与外部调用，不把localhost也发生网络时谎填 network_calls=false。生产 request function 在本 Lab只能注入 mock。
- 小步 TDD，合并相邻用例为一次功能批次。先留至少一个“目标行为失败”的 RED，再实现 GREEN；导入/缺环境失败不是产品红。最终一个集中审查节点，不要求每个小节点都审查。

## 3. 隔离和清理

测试 cwd、TEMP/TMP、缓存、上传样本、日志、浏览器 profile 放 `Lab/.tmp/<随机ID>` 或本人唯一系统临时子根。原目录和文件只读；禁止产生SQLite生产库/真实下载。禁止启动原UI/8765/8766、终止陌生PID或复用用户浏览器会话。浏览器E2E用自己的隔离profile、自己的loopback合成服务。port冲突退出，不回收别人的端口。后台 Windows 进程隐藏窗口。

所有 success/failure/timeout 都 finally：只关闭本次创建且PID/命令/profile匹配的进程；递归删除前证明 resolved绝对路径在本人临时根；删除后核0残留/端口关闭，保留薄cleanup记录，不保留敏感屏幕/正文。真实已安装浏览器/运行时不可用，报缺项，关键E2E不跳过充数；可先交partial。

## 4. 必须真实不同 agent 集中独审

最终功能/单元/集成/mock E2E完成后冻结 payload commit **C**，由**非实现作者、实际不同agent**检查整个范围：需求完整度、实现/diff、所有边界、接口适配、测试真实性、临时清理、安全、用户可用性。审查者不得顺手改实现；发现问题由作者修并更新C，再在最终C重审/重跑必要小集，直到 passed 且 open_findings=[]。不能把自己换个称谓、两个提示、伪JSON或同一个agent二次回答算独立审查。

`docs/handoff/<ID>/review/` 至少：

- `invocation-evidence.json` required：`protocol="iqs.support_independent_invocation/1.0.0", author_agent_id, reviewer_agent_id, tool_name, invocation_id, invoked_at_utc, input_lock_sha256, payload_commit, payload_manifest_sha256, evidence_path, evidence_sha256`。两agent ID不同，平台实际调用/返回证据可追溯；不能手造调用记录。原始平台返回只留必要元数据，不含私有思考。
- `round-01.json`（必要round-02等）：required `protocol, round_id, reviewer_agent_id, payload_commit, input_lock_sha256, reviewed_file_hashes, findings, test_refs`；每finding有 `id,severity,path,reason,status`。无新问题用真实空数组。
- `fixes.json` required `protocol, findings:[{finding_id,from_payload_commit,to_payload_commit,changed_paths,test_refs,resolution}]`，没有发现也明确空列表，不伪造修复。
- `final.json` required `protocol="iqs.support_independent_final/1.0.0",status="passed",author_agent_id,reviewer_agent_id,payload_commit,input_lock_sha256,payload_manifest_sha256,reviewed_file_hashes,invocation_ref,round_refs,fixes_ref,test_refs,open_findings=[]`。摘要字段不能替代实际引用文件/hash。

缺真实审查工具时诚实 partial，向总控报告需其安排独审，不伪造完成。review字段只能真实记录；审查通过不授金融/生产资格。

## 5. 原 handoff 1.0.0 兼容及提交自指

本批采用锁定 `docs/implementation/parallel-lanes/handoff.schema.json`，**不扩其顶层字段**。各 Lab 唯一交接目录 `docs/handoff/<ID>/`：

1. `handoff.json` 原required字段：schema_version="1.0.0"、lane_id="iqs"、package_id=<ID>、status=complete/partial/blocked；snapshot={repository,base_ref,base_commit,result_ref,result_commit,worktree_before,worktree_after}，worktree对象={state,dirty_path_count,manifest_sha256}；scope={task_ids:[],authorization_scope_ref,owned_paths,authorized_paths,changed_paths,out_of_scope_writes:[]}；interfaces数组每项={name,version,content_hash,direction,result}；verification={checks:[{name,command,scope,result,passed,failed,skipped}],external_writes:false,network_calls:<真实bool>,paid_calls:false,temporary_roots:[{path_or_id,created,cleaned}]}；review={status:"approved",snapshot_commit:C,findings:[]}；open_items=[]；可选next_action。只有完整且独审通过才complete。所有Git commit本批加强为真实40hex，不照抄旧schema仅minLength7的宽松校验。
2. `artifacts.json` 形状 `{artifacts:[{path,bytes,sha256,role}]}`；sha256全部64hex，按真实文件原字节计算。相对路径只在自己Lab，原输入锁/源代码/schema/fixture/演示/测试及独审证据都能定位。禁止placeholder、自身hash循环、phantom paths。
3. `tests.json`：实际argv、cwd、环境边界、开始/结束UTC、exit_code、passed/failed/skipped、日志/JSON/JUnit引用与rawSHA；RED与最终GREEN分开，0测试不能算通过。
4. `cleanup.json`：临时根、前存在性、本次PID/profile/port、before/after、删除/残留、失败清理和外部写/外网/收费调用计数。
5. `report.md`：产品界面/流程、未接线能力、源接口映射、版本差异、测试证据、独审完整路径和hash。显式 `production_ready=false,financial_qualification_granted=false,real_owner_golden_produced=false`。`integration/host-patch-proposal.md` 只建议总控在原UI需要改的路径/函数/入口，不改源仓。

提交分层防自指：先本地空骨架base commit B；功能、schema、fixture及 `docs/payload-manifest.json` 形成最终payload commit C。payload-manifest索引payload路径/hash，不索引自己或未来交接元数据。真实独审绑定C及该manifest的rawSHA。修实现须新C并更新独审。最后单独 metadata commit M 加handoff/report/review/artifacts/tests/cleanup；**handoff.snapshot.result_commit=C、review.snapshot_commit=C**，result_ref可用C的完整40hex；M写在最终聊天交接，不把包含handoff自身的M写入handoff造成递归。M不能改C的功能文件；改则形成新C并重新审。artifacts不hash自己/handoff，不形成环；独审报告作为独立可定位artifact。新UI模块/JSON schema的interfaces.content_hash应指实际C文件hash，非仓库HEAD简称。

worker只在本Lab做schema形状/文件引用检查，不运行上游CLI。总控按README原parallel_handoff_cli --verify-references预检，再核真实独审和集成。旧1.0 shape valid != 独审有效/owner gate通过。该方案使用原允许字段和独立证据文件，不宣称另有隐含“新版1.0”。

