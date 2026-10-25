# 公司快扫工作台：部署与接口

2026-10-25，产品API `1.0.0`，本机部署配置 `1.0.0`。此文为当前实现契约；不取代原StockWiki/StockQA校验。

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

## 当前未完成项

界面不是全名单扫描完成的证明。当前214实体、旧12运行/11公司，另有一条原CATL正式入库观察（旧24题manifest，仅IQS_05）。基础当前36题不反向改写旧观察。W09读原语义，不宣称C06 envelope已验收，不用前端均分替代原质量规则。

本版还需继续补“任意唯一实体→组合题库→原公开准入/预算→批量原执行→交付登记”的自动准备与连续全名单路径。当前automatic_pool_dispatch=false；空登记列表不是功能已完成，也不为已耗尽的r25原范围增加预算或重发cold。
