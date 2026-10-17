# 本波次共同施工、输入与交接契约

## 输入冻结与唯一写根

总控先提交本波次文档，再为每卡生成 `dispatch-locks/<PACKAGE-ID>.json`，符合随附 `schemas/dispatch-lock.schema.json` 的 `iqs.parallel-package-dispatch-lock/1.1.0` 协议。`input_files` 是以总控仓库根目录相对路径为key的对象（故不能重复路径），每项锁字节数/SHA-256；路径不得绝对、带盘符、含反斜杠或 `..` 组件。`source_snapshots` 以唯一source ID为key，`path` 是对应精确源仓/归档根下的安全相对路径；没有锁定路径不得读取。schema固定三个package对应的准确work_root。锁还绑定包文档commit、允许读入的外部公开来源、provider/model/revision、thinking/temperature、搜索/Fetch上限、现金和/或套餐额度、预算owner、quota group、UTC执行窗口和签发时间；锁不能包含自身。两个实时实验的源快照必须锁到实际使用的prompt builder、StockQA公开ResearchChatSession/原生账本适配和参考题目/证据输入；没有可锁定的真实路径/hash即 `blocked`。实施者逐字节复核锁定输入；缺锁、错路径、SHA/大小不符、Lab已有内容、锁外输入或writer冲突，一律 `blocked`，不自行补锁或覆盖。

JSON Schema通过后，总控还要做wave级语义检查并保存检查结果：UTC时间戳均以`Z`结尾且每个执行窗口`start_utc < end_utc`；三个package ID/work_root各不重复；实时包budget owner互异；同一quota group下的执行窗口按半开区间不得重叠；source snapshot的`repository+commit+relative path`三元组不能重复；TAXONOMY lock必须恰有四个互异官方来源URL（CSRC、C&SD、SEC、Census），另两包external_sources必须为空；实现实际读取的每个源文件都必须唯一解析到source snapshot且匹配字节数/SHA；live请求上限须覆盖本卡预注册主运行与reserved预算。单文件schema校验不能代替该wave级检查。

实施期间只写唯一工作根。IQS和StockQA源码仅按锁列出的精确快照只读；不复制/打印任何密钥和私有回答，不访问生产SQLite或真实股票池。下载财报、证券公告PDF、整页网页和其他公司文档均禁止。TAXONOMY可查询/记录公开官方分类网页或可公开复用的代码表，遵守来源条款并记录版本/访问时间/URL，不批量抓取被限制的站点；两个模型包不调用搜索/Fetch，测试证据完全使用锁定的短小输入或合成上下文。`.env`、账户配置、环境变量值和secret-bearing `config.json` 一律不读、不hash、不复制。

任何目录边界冲突、未授权输入、费用不可界定或公共接口不能从锁定输入恢复，都要报告具体路径/哈希/响应和 `blocked` 原因；不得以新版本、缓存、默认设置、同名公司或其他包输出替代。

## 测试、可靠性和结果保真

每包至少有：

1. 单元测试：封闭 schema、确定性核心规则、非法值拒绝和失败路径。
2. 集成测试：真实公开 CLI/API 边界、输入锁/发布版本绑定、覆盖/错误返回。
3. 端到端测试：从冻结输入到最终 handoff/result 的完整公开路径，使用本 Lab 临时根并在成功、失败、异常中断后核对清理。

变更先写能失败的 RED，再实现最小行为。集中运行本包完整门；不把 schema 通过叫作语义正确，不把合成测试叫作金融事实准确。实时试验必须逐 HTTP 记开始/结束、状态、响应类别、model/provider版本、usage、缓存字段、费用/套餐额度与原生回执；`unknown`/不确定发送保留预约且不重发。观察到的实际费用、官网参考价、套餐额度分别记账；无法确认的值保持 `unknown`，不算0。提示中的思考文本、内部 reasoning 或隐藏 chain of thought 不写进交付；仅保留可审阅的答案理由和证据定位。

## 每包最终整包独立审查

实施者冻结最终 payload commit 后，调用一个真正不同的 reviewer agent/task，只读审查完整最终实现、公开接口、测试、输入/费用边界、结果和清理。reviewer 必须直接检查核心源码/工件并实际复跑主要合法路径与拒绝路径，交付逐 finding 记录。总控接收者必须能从调度器/UI直接打开 review task 和原始 review artifact，并重算 artifact SHA；仅实施者填写“不同 agent”或自写review JSON无效。

每个 `docs/handoff/<PACKAGE-ID>/` 至少包含 `report.md`、最终 JSON/数据工件及对应封闭 schema、冻结输入清单、单元/集成/E2E命令与原始结果、coverage/清理证据、费用和请求摘要（若有）、`review/invocation-evidence.json`、全部轮次、finding修复清单及最终review artifact。最终记录须绑定 payload commit 与 dispatch lock SHA，具有实施/审查 task ID、平台 artifact 原始引用和 hash、全部 findings 状态；必须 `passed` 且 `open_findings=[]`。

有效 finding 逐一修复后，用同一独立 reviewer 复审新的 payload commit；无法关闭、reviewer不可验证或测试/清理不完整时，不交付 `complete`。仅新增不改变语义的交接元数据可以单独提交并说明。实施方不得向远端push，不得替总控做生产接线；总控仍单独验收。

## 共同测试清理

测试的临时文件、下载、数据库、缓存、日志和本地服务器都留在包内新建的临时根。开始时列路径并保存hash/进程基线；完成或失败时只清本包确实创建且结束的资源，并重算清理清单。不得递归删除任何 Lab 根外路径、全局浏览器/模型缓存、共享 SQLite、密钥文件或其他 writer 的内容。若不能证明某一临时下载/进程由本次run创建，保留并报告，不删。
