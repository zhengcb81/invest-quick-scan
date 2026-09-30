# 部署、生命周期与就绪级别契约

**任务**：C07 · M0 · Owner `iqs`  
**契约版本**：1.0.0（本地协议定义；未实现生产启动器）  
**机器契约**：[deployment.schema.json](../../../schemas/quick_scan/deployment.schema.json)  
**虚构样例**：[deployment-contract.examples.json](../../../examples/quick_scan/deployment-contract.examples.json)  
**离线参考规则**：[deployment_contract.py](../../../scripts/deployment_contract.py)  
**验收**：DEPLOY-02、DEPLOY-04、START-02、START-03、START-05、START-09、START-11、E2E-04、E2E-05

本契约定义各仓公开入口的行为和证据形状。`deployment_contract.py`只对传入的虚构状态做纯函数判断；不会查找安装路径、启动/停止进程、访问网络/数据库或模型接口。schema、参考规则与fixture通过，不代表StockWiki安装器/CLI、StockQA控制面或快捷方式已接好。

## 1. 单一入口、公开操作和职责归属

统一入口预期由StockWiki的公开CLI/UI协调；已有基线包含`python -m stockwiki.cli`，但下表中的快扫子命令/操作名仍是协议提案，不能在真实入口实现前写成“已存在”：

| 操作 | 允许行为 | 不得代替的拥有者 |
|---|---|---|
| `setup` | 收集配置引用、逐项调用配置拥有者并记录配套安装/profile版本 | 不得复制StockQA密钥/策略；StockWiki保存名单与profile，StockQA保存模型顺序/凭据/预算 |
| `doctor` | 本地只读检查路径、解释器、schema、实际加载hash、凭据“存在/缺失”状态与owner端点版本 | 不做付费请求，不打联网探针，不执行迁移/安装/修复 |
| `plan` | 返回当前snapshot下可复用、缺口、待办、冷却/预算状态与范围预览 | 不创建模型请求、不预留费用、不写入成员/Observation |
| `start` / `resume` | 对已配置profile的有限任务运行做预检，再经公开接口创建/附着/恢复逻辑run | 不复用正式研究scheduler/source worker，不重置StockQA账本 |
| `status` | 只读展示run、组件、导入、覆盖、费用与阻塞 | UI可打开不等于worker运行或结果已导入 |
| `stop` | 停止新的派发，等待/记录已发请求，保留outbox、费用预留和未完成work | 不能杀仅PID/端口相同的进程；不删除run/结果 |
| `verify_live` | 用户显式确认且StockQA预算有效时，运行真实联网/搜索探针并记入该账本 | `doctor`不暗中升级成此操作；启动协调层不记第二份费用 |

操作信封带`workspace_id + profile_id + request_id + idempotency_key + expected_release_set_id`。设置、名单、模型策略等只通过其owner公开接口读写。传给模型配置owner的仅为配置/profile引用与revision，不包含API key、cookie、环境变量值或秘密内容。无效/缺失配置直接返回`setup_required`并指向owner，不回退到示例配置或无限预算。

`doctor`响应中的`network_calls`、`paid_calls`、`mutating`必须为false。真实连接探针必须是分开的`verify_live`请求，引用用户确认记录及StockQA策略版本；是否允许调用由StockQA再按当前共享预算裁决。缺少StockQA不能因进程/页面存在而判为可扫描。

## 2. 配套release set与实际加载握手

`ReleaseSet`冻结一组共同支持的工件、接口能力和依赖版本。核心组件固定为`iqs`、`stockqa`、`stockwiki`、`theme`、`industry`；`company_wiki`可选，快扫不能依赖它在线或存在公司目录。清单每个组件记录唯一ID、版本、工件SHA-256、来源引用、公开entrypoint、独立Python/lock信息、契约版本和能力。每个清单列出G0—G6及两个消费者为完整发布所需条件。

任何release helper都必须先用完整deployment Schema校验整个对象，再执行hash、组件集合和能力等语义判断；缺字段或畸形组件不得因helper只读取少数字段而被接受。

`manifest_sha256`按与C06相同的canonical JSON规则计算整个ReleaseSet，计算时排除该hash字段本身。`contract_versions`复用C06 `identity_schema / observation_schema / model_policy_schema / exchange_schema / query_schema`等稳定键，另列`metric_schema / score_schema / rule_schema / work_schema / deployment_schema`；不得把同一接口版本分别写成`model_policy`和`model_policy_schema`等不同拼法。版本名相同不够：预期工件hash、实际安装/加载hash、entrypoint和依赖解释器必须对应。消费者技能需比对宿主真正加载的路径与内容hash；源文件新了但宿主仍加载旧副本时报告`version_mismatch`，阻止相应写入/联动。

运行组件握手至少记录workspace/profile、component、run与process instance、PID、启动时间、实际可执行文件hash、working directory、版本、能力、schema版本、source/load root与工件hash。路径要求可识别绝对路径，允许中文和空格；不同仓库可以使用独立venv。禁止把仓库`src`路径拼入另一项目`sys.path`或让UI直接导入对方私有实现。

进程控制需同时匹配`workspace_id + profile_id + component_id + process_instance_id + pid + process_started_at + executable_sha256 + working_directory`。PID复用、旧PID文件、只见端口占用、别的profile或解释器均不足以证明归属；不匹配时不附着、不终止，报告具体冲突。后台进程默认隐藏窗口；界面关闭只关闭视图，不能隐式stop。

## 3. Readiness按证据逐级升降

`readiness`和当前`status`分开记录。只允许下列等级，不能由模型自述、HTTP 200、文件存在、端口占用或一张截图升级：

| readiness | 最低证据 |
|---|---|
| `installed` | 已安装记录引用一个release_set；owner组件与工件路径可定位，但profile可能未配置或本地doctor不通过 |
| `offline_ready` | 所有必需工件的实际版本/hash与清单匹配；必要profile由各owner确认；schema、写路径、能力和本地端点doctor通过；没有付费/联网保证 |
| `live_verified` | 在同一匹配release/profile下有真实搜索执行回执与StockQA费用/usage回执，且没有把stub当真实响应 |
| `full_release_verified` | 满足live_verified；G0—G6回执均对应同一release/hash；G4事实/两个消费者、G5评分及浏览器结果UI、同入口启动/恢复等完整跨组件证据通过；两个消费技能实载hash匹配 |

任一必需组件缺失、迁移待办、契约不兼容或hash不匹配均降级/阻止写入。仅缺可选company-wiki不降低快扫就绪；但无身份主档时只能挂起该对象，不能自动启动来源下载。`full_release_verified`不是设置表单可以勾选的状态，必须由G6审查证据推导。

响应自报的`readiness`必须等于由同一响应中的`readiness_evidence`计算出的等级。`offline_ready`起要求组件hash、setup和doctor证据；`live_verified`另要求同一release/profile的联网与付费回执；`full_release_verified`再要求G0—G6各一次、两个不同消费者，以及每条gate与顶层均绑定同一`release_set_id + manifest_sha256`。所有响应导入必须调用公共语义校验器，将响应与预期ReleaseSet交叉核对；JSON Schema负责静态唯一集合/形状，不能单独承担动态等值。缺项、重复、跨release或错hash均拒绝越级。

## 4. 生命周期、幂等与费用连续

- 并发或重复`start`若匹配同一workspace/profile且存在active run，只返回同一`run_id`并附着；禁止再建逻辑队列、worker或费用账本。确无缺口时返回`no_work`，模型调用为0。
- `resume`恢复原profile与run的检查点、逐题work键、uncertain对账、outbox和StockQA已消费/预留费用；没有可恢复run时返回`no_resumable_run`，不以创建新run冒充恢复。
- `budget_exhausted`在关闭页面、重启组件、点击start/resume或切换备用模型后继续成立。只有用户经StockQA配置owner明确调整预算/期间额度，才可获得新可用额度；入口不能自行归零。
- 达到本次上限时先停止新派发；对已发请求完成排空或进入`uncertain`并保留预留，不把租约过期当作未收费。已回答未ACK时仅重投原outbox，不能重问。
- `stop`不删除未完成项或观察；无关/归属不明进程永不终止。后台worker是否退出按StockQA/StockWiki明确返回的所有权与状态执行。
- 启动路径只调用quick_scan控制接口；`generic_research_scheduler_started=false`、`source_pipeline_started=false`。常规扫描不因company-wiki关闭而触发来源下载。

## 5. C07本地契约验证边界

建议复现：

```powershell
python -X utf8 -m unittest discover -s tests -p test_deployment_contract.py -v
python -X utf8 scripts/implementation_plan.py validate
```

fixture包含虚构组件、hash、中文/空格安装路径和doctor/verify_live请求。策略检查覆盖同版不同hash、必需组件缺失、安装/离线/联网/完整就绪分级、doctor零付费、连接探针明确授权、重复启动附着、预算耗尽后不重置、关闭/停止边界及PID复用反例。

离线检查只冻结协议语义，不能称为真实进程/SQLite/费用/UI/联网结果。DEPLOY/START/E2E相关公共CLI、worker、共享预算和浏览器的实际行为仍由StockWiki、StockQA及X系列owner在各自允许目录中验收；外部仓的写入未获授权时保持只读，不得用本目录测试代替。


## 生产资格修订与dispatch commit

active ReleaseSet指针之外，W16还锁定组合内每个component release的生命周期/dispatch_eligibility revision。release在active pointer不变时被deprecated/retired，会使旧plan/apply/permit consume的CAS失效。只有StockWiki owner事务消费permit并返回与work、StockQA attempt、recipe、active pointer及精确组件资格revision绑定的`dispatch_commit`后，StockQA才允许一个provider POST。permit发行或UI显示ready不够授权网络调用。X09和G6需在隔离fixture中覆盖指针不变资格变化、consume前拒绝、consume后单次提交、崩溃结果不明与fallback新attempt；旧已commit的请求仍按原recipe结算。
