# 公司快扫工作台：部署与接口

2026-10-25，产品API `1.0.0`（新增准备、编排与交付job接口），本机部署配置 `1.0.0`。此文为当前实现契约；不取代原StockWiki/StockQA校验。

## 运行与边界

`python scripts/open_dashboard.py`复用同级`iqs-question-bank-ui-lab/scripts/serve.py`，启动时更新题库/旧草稿快照，默认不跑测试。`--dashboard-config PATH`选择连接配置；`--no-refresh`复用已有快照；服务仅监听127.0.0.1。Ctrl+C停止服务，不强杀已经开始的原模型HTTP；后续原状态未知时必须先核原owner，不能盲重发。

默认本机配置`config/dashboard.local.json`被精确忽略。可复制`examples/dashboard.config.template.json`后在“设置”编辑；密钥只放环境变量。runtime_dir须为原StockQA运行目录，其中已有原`llm_apis.json`；model_policy_path必须指向同一文件。设置直接调用原LLMConfig保存`quick_scan_model_policy`，保留其他provider配置，不返回密钥。按读取时整文件SHA检查并发更新，冲突须重读。运行中/原进程未知时禁止切换连接；正常已退出的进程不阻止切换。

StockWiki工作区与StockQA账本不能因“测试副本”随意换路径：接收store_id和PRE绑定原路径。这里不迁移生产数据、不移植收据；默认已有r25工作区标记isolated_research。新工作区应由原owner合法初始化，不由GET自动建库。

## 原包登记

execution_bundles以短bundle_id为键，每条指向原输入文件：questions、manifest、identity_snapshot、c06_authority、owner_config、admission_config、spend_authorization、inspection_request；以及原entity_id、company、provider、confirmation_id。可选search_policy、runtime_dir、inspection_schema_version（默认1.0.0，按原检查器版本选择）、pack_size（1–30）、thinking（默认true）、max_output_tokens（默认8192）、security_scope_id。准入配置里的原work_store/budget_policy_file必须已经存在。spend_authorization是原授权文件路径，不能临时填虚构JSON。

import_bundles指向原package、release文件，可登记package_sha256、release_sha256和entity_id显示标签。需要完整对账时，加work_store（原StockQA账本）和work_item_ids（observation_id到work_item_id的完整一一映射）。这些是服务部署引用，浏览器动作只能选bundle_id，不能提交任意命令、运行脚本或拼接shell。

执行预览调用原refresh inspect，绑定原输入字节和检查结果；启动前重新核验。重复点击附着已有记录。过程记录只存本机启动引用，不是第二套题目队列。process_started只证明CLI启动，paid_dispatch_started未知时保持null；进程退出不等于ready、入库或金融资格。暂停在公司边界排空，保留在途请求；未知/租约/费用不明继续由原owner拒绝恢复。服务重启不盲重发。

## 页面与API

| 页面 | 原数据/操作 |
|---|---|
| 工作台 | 名单/题库快照及原owner实际连接能力 |
| 生产结果 | 原StockWiki W09查询、原三态分数条件、缺项、逐题理由/证据 |
| 历史与模型 | 原不可变观察的时间、模型、版本，缺失保持未记录 |
| 信息与关系 | 原fact items；没有结构化关系能力时明确不支持，不从叙事补造 |
| 名单维护 | 原唯一entity_id、候选预览、加/移出/恢复/保留及版本 |
| 扫描任务 | 已登记原包预览/启动、逐任务原状态检查、公司边界暂停/恢复、导入ACK |
| 设置/环境 | 原连接、原模型顺序/并发/额度组策略；不自动发模型请求 |

所有API路径前缀`/api/product/`。统一成功`{ok:true,data:...}`，失败`{ok:false,error:{code,message,details}}`。

- GET status、setup、settings、tasks、doctor、coverage、universe、delivery。
- GET results：query、limit（1–100）、offset、filters、conditions、condition_combine、view、snapshot_token。filters仅原市场/行业/证券类型；conditions为原`[{field,op,value}]`非空列表或省略，combine为all/any；view为原all_relevant/quality/recovery/pending。字段来自原coverage.by_field。
- 首次分页保留原owner snapshot于服务内存并返回短snapshot_token；后页带同条件及token。15分钟、128个快照上限；过期/重启/更改条件409要求从第一页刷新，不能静默重排漏公司。
- GET entity/history/facts：精确id（或entity_id）。静态draft_runs另列，不合并为正式观察。缺少数据库不返回假0。
- POST universe/preview、universe/apply；动作add/remove/restore/pin/unpin，含原entity_id/universe_id/reason。apply必须带原preview_token；名称只用于候选检索，不自动建立或激活身份。
- POST tasks/preview、tasks/start：仅已登记bundle_id（可核entity_id），start带preview_id。POST tasks/{run_id}/inspect、pause、resume，逐任务allowed_actions不代替服务端守卫。
- POST import/preview、import/apply：bundle_id，apply带preview_token。原public PRE预检不写库、不产生ACK。实际导入事务重新核验；接收目标来自独立owner.status，在导入前调用原bind_result_delivery_consumer冻结，不能从ACK反向学习。原receipt逐项传回原apply_result_delivery_ack；pending保留已成功入库与原回执，重试幂等。没有登记原账本映射时明确not_configured，不能宣称原执行器delivered。
- PUT setup：`{config,revision_sha256}`；PUT settings：`{policy,revision_sha256}`。未知字段拒绝；不接收密钥。

Host只允许当前端口127.0.0.1/localhost；Origin如存在须为本机同源；写请求需status提供的X-IQS-CSRF。拒绝跨站、重复JSON字段、NaN、超过1MiB或64层JSON。没有开放CORS、外网监听、任意shell或自动收费操作。

## 自动准备与批量操作

在本机连接JSON中设置`prepare`，路径均指向已由原owner部署好的文件；浏览器不上传任意脚本、身份收据、授权或预算。空`prepare`仍能预览题库，实际登记会列出缺项。示意值必须替换为真实部署引用：

```json
{
  "prepare": {
    "state_root": "runs/dashboard-preparation",
    "admission_config": "runs/my-owner/deployment.json",
    "runtime_dir": "../StockQAbyLLM",
    "spend_authorization": "runs/my-owner/spend-authorization.json",
    "producer": {"component_version": "实际版本", "build_id": "实际构建标识"},
    "authorization_reference": "实际用户授权引用",
    "agent": {
      "profile_id": "已登记profile",
      "profile_sha256": "真实profile的64位SHA256",
      "harness_ref": "实际harness引用"
    },
    "pack_size": 1,
    "thinking": true,
    "max_output_tokens": 8192,
    "work_lease_seconds": 3600,
    "delegation_ttl_seconds": 43200,
    "worker_timeout_seconds": 900,
    "native_timeout_seconds": 300,
    "routing_profiles": {}
  },
  "batch": {"max_concurrency": 1}
}
```

`admission_config`继续指向原StockQA work_store/budget_policy_file和原StockWiki工作区；它们必须已存在。准备器只派生每次准备独有的不可变输入目录，不创建第二预算或覆盖旧manifest。新原范围必须由原部署提供；不能给已耗尽的r25六次请求补额度。**自动准备当前支持原owner policy 1.0/1.1**；1.2及以上在预览中明确返回`native_prepare_owner_dialect_not_supported`，不先写原路由、不降级策略。已登记的高级原包仍走执行器对应的原1.2–1.5检查与控制，此能力不等于自动准备已支持它们。

`prepare.work_lease_seconds`是新工作每次claim的有限处理时长，允许1–86400整秒；省略时保留原StockQA默认600秒。显式值随新执行包冻结，并由`--work-lease-seconds`传给原CLI，不修改旧包、旧代次或已有租约。联网搜索可能持续发送心跳，因此HTTP的`timeout`不是总耗时上限；本轮真实MiMo请求曾耗时633秒。长搜索可明确选3600秒，并为新准备单独设置足够的`delegation_ttl_seconds`（例43200秒），二者都不是自动续期，也不增加费用预算。设置须等原工作安全退出；旧grant或lease过期后仍走原核验/恢复，未知HTTP不重发。`worker_timeout_seconds`和`native_timeout_seconds`仅限制准备流程，不能当作模型请求总超时。

默认模块包采用已发布router2.5：所有公司基础36题，可信`routing_profiles`按实体登记`verified_facts`/`user_policy`后追加行业、阶段、属性模块。profile标签改名不使输入失效；真实事实或策略变化使旧预览失效。分类未知保留基础，不猜行业；本自动准备路径当前为评分题，61道信息题面和已存信息记录可查，但不能宣称信息题已自动采集。

现有主体由原serializer读取；无主体时可明确选择原`standalone_issuer`初始化。此范围只表示法律发行主体，不能冒称无子公司、完整合并范围或提高原身份状态。原verified/active身份收据、真实证据、OS SID/uid及原权限仍必须通过。预览将服务器当前完整UTC时刻冻结为原身份/主体快照时间，apply复用同值；信息截止日独立约束答案，不把今天新验证的收据回溯到午夜，也不据此声明过去的公司边界。缺少冻结时刻的旧未执行候选须重新预览，已完成结果仍幂等回读。多挂牌显选security_id，原题目scope不混用；当前基础按实际manifest产生33 entity＋3 security两个原包，此数字不写死，全部scope原ready后才算公司完成。

新增API：

- GET `prepare/status`、`prepare/jobs`、`prepare/jobs/{job_id}`；POST `prepare/preview`接受`entity_id/as_of/mode`及可选`scope_selector/subject_key/security_id/profile_id`，返回实际题面、数目、主体/挂牌候选和阻断。预览只写IQS自己的不可变候选。
- POST `prepare/apply`接受精确`preview_id/preview_token`，快速返回异步job；后台依次走原route snapshot、CAS activate、C06 capture、原delegation确认和StockQA admit。GET保留实际阶段与错误；POST `prepare/jobs/{id}/reconcile|abandon`只按allowed_actions恢复登记或停止等待，不重复确认/准入。unknown与partial不是成功。
- GET `batches`；POST `batches/preview`只冻结本地输入字节和完整公司scope集合，`owner_inspected=false`，**不是费用或真实派发准入**。POST `batches/start`登记薄编排引用，后台在每scope派发前调用原检查器；已ready复用，未知HTTP不重发。这样2000公司预览/登记不串行启动4000个原检查进程。
- POST `batches/{id}/pause|resume`；暂停在scope/公司边界排空。重启不自动续跑；已完成范围只核冻结字节，尚未启动的范围延迟到派发时原预检，已有在途/未知引用仍按原恢复规则核实。`company_counts`与`scope_counts`分开，`company_groups.complete`才是整公司所有scope完成。
- GET `tasks`只读本机过程引用并分页；每个run先点“核原状态”，即POST `tasks/{run_id}/inspect`，再按原allowed_actions恢复。不能用进程退出或缓存投影当派发许可。
- POST `tasks/deliver`选择bundle_id，或POST `batches/{batch_id}/deliver`选择该批当前原ready范围，均返回异步交付job；GET `delivery/jobs`查看，POST `delivery/jobs/{id}/resume|abandon`明确接续。长时间原CLI在后台，不占全站服务锁。父job只保scope摘要/计数；逐题ACK仍归原StockWiki和StockQA outbox，避免2000×36条明细复制成不可恢复的大文件。
- 原公开只读交付检查、精确outbox字节导出、冻结release投影、独立接收目标绑定、原导入及exact ACK仍逐步执行。不申请新spend grant、不重新封存或重问已完成答案。历史24题保留24，不能按当前36题改写旧观察。`tasks/export-delivery`可只导出原已封存包引用；不永久把全池每个包登记进另一个配置账本。

批引用读写统一16MiB上限，最大5000scope工程记录实测约6.26MB，可重启读取；交付引用同上限且不存回答或ACK全文。超限写入先拒绝，保留旧文件。配置和job控制使用OS释放的非阻塞锁：并发冲突明确409；崩溃不因遗留PID文件永久锁死。更换目标前检查完整任务、批、准备和交付引用，追加同源包不丢在途进程。

本机Windows建议状态/测试目录使用短路径。题库预览与准备均0模型调用；原完整36题准入工程用例实测bank preview约11秒、已有主体apply约543秒，首次法律发行人主体路径apply约232秒。它们不是同条件性能对照，不能将差异解释为提速。900/300是有界等待，不是成功保证；超时保原阶段、unknown与错误，禁止盲重做。

## 实际数据与尚存边界

界面不是全名单扫描完成的证明。当前214实体、旧12运行/11公司，另有一条原CATL正式入库观察（旧24题manifest，仅IQS_05）。基础当前36题不反向改写旧观察。W09读原语义，不宣称C06 envelope已验收，不用前端均分替代原质量规则。

本机已将用户认可的214个既有entity_id接入`UNI_IQS_APPROVED_214_20261025`，通过原名单API维护；实体身份完整摘要前后相同，没有新增/合并/升级身份，原实验名单保留。当前真实部署的自动准备参数和新预算仍需正确配置；空配置的阻断是实际部署状态，不伪称已开始全池扫描。原完整36题准入和工程假数据批协调通过，不等于214家公司已被实际问答，更不授金融准确性。
