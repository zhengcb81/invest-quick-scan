# 公开契约、能力域与 TDD

本文是九条线的共同设计输入。已有协议按实际实现复用；标为“拟新增”的内容尚未发布，提供者负责实现，消费者可以用这里定义的fake并行开发。不得由各包自行发明另一套状态库、预算、协议或版本。

## 1. 能力域和允许方向

|owner|域与允许方向|持久化/副作用边界|
|---|---|---|
|IQS|HTTP/CLI组合根 → 工作台应用/共享编排 → 题库路由与答案语义；应用 → 本地owner adapters → 外仓公开入口|只有IQS自有配置、作业投影、导出；题库资源由IQS读，不替QA写工作库或替SW写身份/观察|
|StockQA|组合根/runner → lifecycle/服务ports；provider/SDK和work store分别实现ports；业务领域不反向import runner/具体SDK|唯一真实请求、搜索、共享额度、已付响应、逐题checkpoint、outbox所有者；不新增第二恢复器|
|Company Agent|公开api/装配 → task/策略/runner/恢复领域 → 值规则；执行效果通过runtime port|持有agent会话事件/checkpoint语义；不是模型收费账本；状态对消费者隐藏|
|Runtime|api/组合 → runtime/tool/receipt适配 → services协议；services实现由QA提供|薄适配，不自行保留另一个预算/重试/成功结果库；测试double不得被生产装配默认加载|
|StockWiki|CLI/组合 → 身份名单、观察入库/ACK、刷新准备、查询投影、交付对账五域；查询读公开只读仓储，准备调用身份/只读观察port，交付调用入库服务|身份/名单/研究观察/ACK唯一owner；事务与SQLite只在其基础设施层；纯publication规则不接万能control|
|原工作台|静态视图/组件 → API client或公开展示快照|UI只持有草稿/选择/展示状态；不裁决身份、不重算评分、不解析owner私有目录|
|Dashboard|transport/组合 → application → domain/ports；adapters实现ports；前端→generated DTO/API|仅Dashboard自己命令/视图状态；SavedViewStore可注入；m6/m8不穿越owner实现|
|Theme / Industry|技能入口/研究编排 → 只读客户端 → 公共CLI/JSON；响应→本域研究输出|capture/output只写消费者根；服务不可用显式缺口，不自动付费补扫|

方向规则以**域**为单位。域内文件可协作，普通helper不独立版本化。逻辑循环应拆纯值与装配，不为“文件无环”搬来搬去。只在组合根允许选择实现和设置包加载路径。

## 2. 已有跨仓契约

### C1 StockQA ↔ IQS / CA / Runtime

- facade：`src.utils.quick_scan_company_api`。正式磁盘1.5与候选1.8须由MC-QA归拢；IQS当前最低要求1.7。**目标采用已实现候选1.8，消费者所需下限由实际所用操作决定**，不要仅因发布了1.8便无条件提高所有调用者下限。
- 继续使用已有`create_native_task`、`create_company_scan_task`、`create_company_research_runtime`等公开操作；准确签名以候选facade及合同测试为准，兼容封装不改既有调用形状。
- 不返回provider module、原SDK session、数据库store或生命周期实现；返回已有opaque runtime/session及脱离owner的投影。需要查状态应增加明确只读操作，不能返回原对象让调用者自行查。
- 新发送检查身份/原题包/真实预算/lease/幂等。已付回答的读取、保存、补封不重新要求“今天可发送”或模型key。格式/研究质量问题作为逐题诊断保存，不能伪造HTTP失败诱导重发。

### C2 Company Agent

- `iqs_company_agent_lab.api`，`iqs.company-agent-public-api/2.3.0`。
- task DTO：`iqs.company-agent-task-contract/1.1.0`；`task_snapshot`/恢复构造是唯一任务投影入口。runner/journal通过已有公开创建、执行、恢复、checkpoint/export操作使用，调用者不读具体字段或journal文件布局。
- DTO嵌套数据深复制；修改副本不改变owner。未知破坏性major明确不兼容；新增optional显示字段依协议处理。现有封闭字段协议不能单边放宽，需提供者明确兼容规则并给消费者同一组向量。
- 动态生产问题集与冻结12题实验分开；保留原legacy回放，不给生产默认套实验日期/公司/题数。

### C3 Runtime

- `iqs_agent_runtime_lab.api`，`iqs.agent-runtime-public-api/1.4.0`。
- `iqs.agent-runtime-services/1.0.0`当前必选操作：`describe`、`route`、`create_session`、`step_session`、`close_session`、`generation_scope`、`search`、`inspect_attempt`、`request_resume`、`observe_native_step`、`observe_native_failure`。
- `observe_model_receipt`仅在声明相应能力时必需。缺本次需要的操作在claim/HTTP前报告；浏览或旧结果读取不因不相关新能力缺失而关闭。
- 公共runtime句柄仅提供既有`model_step/search/inspect_attempt/request_resume`；Company API桥只交所需公开操作，不返整个module。
- DTO规范由CA拥有、services由RT拥有、收费和持久化由QA拥有，不能三仓各写一套不同的任务资格判定。
- fake替换的是**消费者所需的公开协作者**。QA内部构造真实收费服务时仍可核本owner真实服务类型、注册任务/store绑定；该路径用隔离真实store/注册服务测试，不为让fake获准而删除这些绑定。外部消费者不依赖该具体类型。

### C4 StockWiki 与查询消费者

- 保留`stockwiki.identity_g2b_cli`、`stockwiki.quick_scan_dashboard_cli`、`stockwiki.quick_scan_prepare_cli`、`stockwiki.quick_scan_query_v2_cli`及现有公司评估公开入口。
- prepare request/reply：`stockwiki.quick_scan_prepare_request/1.0.0`、`stockwiki.quick_scan_prepare_reply/1.0.0`。具体字段沿既有schema。
- facts当前发布wire **2.7.0**；query/export协议`stockwiki.c06_facts_query/1.0.0`、`stockwiki.c06_facts_export/1.0.0`，CLI envelope `stockwiki.c06_facts_cli_result/1.0.0`。capability schema兼容1.1/1.2；IQS的2.8消费者代码不等于SW已支持2.8。
- **query wire/schema由StockWiki负责，问题/答案业务schema由IQS负责**。查询消费者本地保存有版本的公开schema资源或已有校验器；不在运行时进入IQS/SW源码树找文件。复制公开schema不是复制实现；不用新建SDK仓。
- 同一语义schema的空白、键顺序、CRLF变化可接受；不把文件hash当普通运行许可。测试用必要字段、类型、身份/作用域、快照绑定判断兼容。
- query和export分别绑定自己的operation/query/snapshot；`capture-root`属于消费者。optional扩展字段按对应wire声明处理；不能统一“忽略所有未知字段”，也不能无依据全字段相等。
- 本轮2.7资源来源明确为`StockWiki@12c441e`的`config/quick_scan_facts_query.schema.json`，后续兼容修改由MC-SW交付。MC-SW在本仓`tests/fixtures/public_contracts/facts-2.7/`给出少量可直接解析的JSON正反例及README（对应request/query/export、预期合法或错误及绑定上下文）；不新增签发/hash账本。TH/IN可先用各自已有fixture施工，最后对该目录同一组公共向量复测。
- 当前2.7主要对象为closed schema；已声明optional例如`Request.label`、`Counterparty.text/entity_ids`可以存在或省略。**任意未知字段不因为本计划的“可演进”而获准**；未来扩展要owner发布支持规则，本轮不强推2.8。公开CLI所需的`owner_root/iqs_code_root`仍保留；禁止的是消费者进入内部源码找schema/实现，不是删除合法CLI配置参数。

## 3. 原工作台最小公开边界（本轮拟新增/调整）

### C5a 启动：复用 IQS 现有用户入口

保持`python scripts/open_dashboard.py --ui-root <UI仓根> --port <port> --dashboard-config <local.json>`。`--ui-root`明确仍是UI仓根/同形发布资源包根，静态资源根为其公开的`src/`，原`/#/dashboard`首页实际加载`src/app/index.html`（保留原资源相对URL行为）；只读取声明的静态资源，不能执行该根scripts。由IQS拥有监听器、DashboardService及product_handler装配。

普通启动由IQS内部调用自己的export实现，原子生成到配置`state_root/workbench/snapshot.json`（未配置时沿IQS现有默认state_root），不写UI仓、不导入或执行UI build_data。IQS同时提供下述generated HTTP读接口；浏览不会再触发build或模型。`--no-refresh`只读已有快照；不存在/损坏时公开状态标不可用，正式任务/结果/设置仍可用。`--plan`仅显示计划、无生成/写入/启动。

UI旧`serve.py`只是调用此公开CLI的兼容shim，把旧`--no-build`映射为`--no-refresh`，保留port/config参数和子进程退出码；IQS绝不再调回该shim。旧`--no-test`可兼容忽略，因为正常启动本就不跑测试。不新增代理/第二HTTP框架/启动审批。

### C5b 展示快照：单一公开export，代替目录知识

拟新增IQS `scripts/workbench_snapshot_cli.py --output <snapshot.json> [--dashboard-config <local.json>]`，只读，默认0模型/搜索。仅供题库/版本/名册/历史草稿展示，正式任务/结果仍走已有`/api/product/*`。

最小顶层JSON：

```json
{
  "protocol": "iqs.workbench-snapshot/1.0.0",
  "generated_at": "2026-11-11T00:00:00Z",
  "bank": {}, "versions": {}, "roster": {}, "answers": {}, "manifest": {},
  "availability": {"bank": "available", "versions": "available", "roster": "unavailable", "answers": "unavailable", "manifest": "available"},
  "warnings": []
}
```

上例是**字段形状示意，不是有效业务样本/golden**。五个payload对象保留当前UI `build_data.build()`的主要字段；MC-IQS负责真实内容和有效fixture。五段都有availability，值为available/partial/unavailable；warnings为`{section, code, message}`列表，不含密钥。unavailable段为null；partial保留确有内容及对应warnings；未知计数为null，不伪装为0。manifest只核已提供部分的派生计数，不要求缺失段满足旧全量expected计数。bank有效时题数由数据派生，不能空对象伪装成功。

- 生产新UI只取`GET /generated/snapshot.json`：一次返回完整snapshot，store从同一响应分出五段并处理availability/warnings，不新增多请求快照一致性校验或status凭证。为旧展示客户端保留`GET /generated/{bank,versions,roster,answers,manifest}.json`只读投影；新UI不再取这五个地址、不回退UI仓旧generated文件。缺快照也返回明确的五段unavailable展示状态，不影响/api/product。
- UI的build_data可保留为显式离线snapshot导入/静态演示工具，仅写UI自己输出；普通产品启动不调用它，也不读IQS questions/runs/docs。旧verify改测当前真实可用段，不为保住内部helper名字保留反向装载。
- `generated_at`只是展示快照生成时间，不能更新原扫描时间/信息日/缓存TTL。
- roster身份必须来自公开owner投影；历史不能唯一绑定时保留unbound/provisional，不按同名或ticker最后覆盖而标verified。
- synthetic版本示例由UI自有fixture显式开关加载；旧`versions.synthetic_locks/synthetic_diff`由UI本地兼容投影，不要求IQS读取UI fixture。
- 历史导入reader留在IQS内部兼容层，输入显式选择；不硬绑2026-10-18目录，不扫描整个历史runs。
- 此JSON无新的签发/核查凭证。输出原子写入且仅写用户指定的export位置。

### C6 Dashboard

复用`QuickScanPort`、`JobPort`和generated DTO，不另起协议。IQS HTTP`/api/product/*`、`iqs-job/1` CLI保持原行为。application只要求ports；存储通过最小本地协议注入，在composition选择SavedViewStore。现有合同0.1.2-d不得由实现包手改生成物；确需变化交D00/D01统一处理。回包身份、scope、命令键、安全链接校验保留。

## 4. TDD统一矩阵

每个域按相关行执行，不是每个函数重复整张表。先复现实际缺陷的RED，再做最小根修到GREEN。已有正确实现只补缺失证明并记录既有GREEN，不能故意破坏业务伪造RED。

|编号|测试方法|证明什么/预期结果|
|---|---|---|
|T1 最小公开替身|fake只含协议操作，无store/client/runner/control私有字段|正常路径成功；业务不要求具体实现类或目录|
|T2 封装|普通访问未声明字段失败；嵌套DTO修改后再读owner|AttributeError/明确接口错误；owner状态不变|
|T3 依赖方向|在临时源码fixture加一条跨域私有/反向import或外库直读|已有架构测试失败；合法ports/域内helper通过。不要改真实源树做mutation|
|T4 独立装配|消费者环境没有provider实现；提供fake命令/HTTP或公开对象|公开替身能运行；换真实adapter不改业务代码|
|T5 协议演进|旧支持版本、允许的optional扩展、未知major、缺必需操作|正反均覆盖；不因无关capability或schema格式误拒|
|T6 所有权|只读查询/导出/浏览前后核受影响隔离库与API计数|不写owner、不发模型；不是全仓全文件hash审计|
|T7 保存恢复|混合answered/pending/delivered；保存中断、ACK前后重启、重复接续|已有付费响应/待保存/待封包/待ACK/已交付不重发；never_sent可按原授权首次发，unknown先查不能盲发；重复接续已完成分支API增量0，不能为整体0跳过未完成题|
|T8 缓存|注入时钟：有效期内/刚过期；查询和导出不续期|fresh/已付重放不要求新key；真正expired刷新仍需有效凭证/原预算，缺凭证保留旧结果并局部报无法新发，不能伪装已刷新；历史文档不阻断|
|T9 通用性|多个主体/挂牌、相同ticker不同市场、1/36/扩展题集、opaque模型名|不串公司、不写死公司/日期/题数/厂商；已声明不支持的能力局部报错|
|T10 错误隔离|schema错/owner不可用/部分源失败/提交超时未知|明确真实错误；不伪装空结果/成功、不自动重新收费、不让无关页失败|
|T11 当前组合|干净提交源码、新进程、无legacy conftest注入|不是仅导入smoke；执行到owner保存/ACK/查询及UI|

静态测试只看列明生产域和常见直接导入/访问，不能为了恶意`exec/__globals__`写解释器。**普通私有访问在句柄上报错；跨实现import由架构测试/CI报错**。若真需要不可信代码安全隔离应另用进程边界，此专项不造全局import hook、call-stack授权或运行许可证。

## 5. 必留与必删的校验

保留：主体/挂牌/题义真实绑定，原答/不可变题包完整性，原ACK/幂等键，真实金额额度与发送租约，未知请求防重复发送，路径穿越/凭据泄漏/本地CSRF保护。

删除或移出产品默认入口：手写测试计数、历史review/freeze pin一致性、同义schema原字节hash、未声明的实现文件布局检查、无关owner版本/新发送资格对只读和旧答保存的阻挡、域内每个helper版本审批。

判别原则：删除后若可构造错公司/重复收费/丢原答的反例，这是必要约束，简化实现而非删掉；若只影响文档、排版、无关目录或已不消费的凭证，就是冗余。不得以“安全”为名恢复旧门，也不能为求绿取消有业务意义的验证。
