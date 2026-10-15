# AGENT-RUN-02：真实研究端口与策略引擎执行桥

状态：准备完成，待用户派发。唯一可写根：`C:/Users/郑曾波/Projects/iqs-agent-runtime-lab`。准备时不存在；开工重新核归属。**所有其他仓库、新包、快照、生产库和总控PWF只读。** 不能直接修改 StockQA 或原 Company Lab。

## 先读与范围

读[共同接口](integration-contract.md)、[输入锁](inputs.lock.json)、[固定目标](AGENT-RUN-02.targets.json)、[handoff模板](AGENT-RUN-02.handoff.template.json)、[目录manifest](manifest.json)。这五项和本卡就是独立上下文；上游位置/HEAD/入口在共同接口内，不以旧卡的“尚未交付”描述覆盖最新事实。

StockQA ResearchChatSession 已实现并真实跑过S0；Company Lab三策略/execution_revision2已通过工程验收。本包做它们之间的可执行桥，**不重做SDK、策略算法、搜索客户端、预算库、队列或身份系统**。默认离线，不能读环境key、发真实模型/搜索请求，也不再跑S0。

在自己根内复制锁定输入到只读fixtures；自己的候选可以包含 `upstream-candidate/company/` 和必要的StockQA最小patch，但不能把它们写回原仓。每项上游候选列base原文件SHA与未来目标路径。依赖只从显式input-root解析；快照不是完整Git checkout，禁止回源补包或运行外仓测试来写缓存。

## 交付结果

1. 可导入的 `iqs_agent_runtime_lab`，提供共同接口规定的 `create_runtime_port(services, *, task, session_config)` 四方法端口，完整接 model/search request1.0。
2. 候选 Company 引擎真正通过该端口运行三策略，得到原ResearchRun1.1。真实 `owner_public` 不能再被纯synthetic validator一概拒绝，也不能通过改标签绕过；增加显式 `iqs.company-agent-task/2.0.0` 任务载体/解析路径，绑定原题/证据与实际主体/authority refs。旧research-task1.0仍原样synthetic验证、旧schema/fixture不改。
3. `content/runtime-bridge.json`，protocol=`iqs.agent_runtime_bridge/1.0.0`，完整列出支持/不支持的版本、真正native依赖、候选文件与限制，qualification_granted=false。
4. 可搬迁的最小离线replay-pack，既含完整主链，也含缺owner、未知attempt、崩溃、新segment等反例。真实owner正例与真实付费实验标not_run，由总控执行。

## 分步施工

1. 初始化自己的仓/PWF，锁字节复制，记录inputs-used。先列现有公开接口真实签名与差距；不要把共同接口的新注入服务当成StockQA已有API。先写核心失败用例。
2. 实现模型映射：稳定前缀包含完整原题/锚点/schema/工具；动态context携公司、截止、短证据、已答和工具结果。真正调用冻结ResearchChatSession，不只拼短directive。严禁将参考私有目录装进context。
3. 实现 provider真实工具调用↔Lab action/result 往返。一个响应多个tool不能丢后面的；顺序、call_id、失败工具、submit/patch/finish均可追溯，不伪造assistant消息。内部schema需扩展时新增显式版本，不能修改旧封闭schema，公共ResearchRun1.1保持。
4. 通过services接原generation_scope、client、search和attempt检查。缺实际owner配置、主体冲突、过期permission、原生绑定不完整在HTTP前拒绝。识别原 `assert_controlled_generation_payload` 对DeepSeek chat研究协议尚可能不支持的缺口，必要时在自己QA候选做最小新协议校验与反例，不绕过整个guard。
5. 私有会话按company/strategy/segment隔离；pending provider调用保存在内存，durable记录只留安全call引用和receipt。inspect/resume不盲重发。重启丢失reasoning时显式新segment，旧成功答案不重复提问，未知/未定价原attempt先核，不消耗旧批准。
6. S1必须禁search；S2委托原外搜端口，短结果实质进入下一模型上下文。记录原first-party物理ref、usage、状态和全部费用；同ref不双计，缺usage保持unknown。超时/取消/预算/并发由现有runtime负责，无法满足的native接口列具体gap，不能在本包另造相似账本。
7. 最后一次集中单元+集成+CLI E2E，搬迁复跑与清理，交候选patch和真正可执行入口。不能只交Protocol或全stub测试。

## 必测矩阵

|组|关键用例与预期|
|---|---|
|上下文|模型实际接收短证据与原完整12题；相同prefix跨公司稳定、动态公司不串；引用/单位/截止错不能被改标签修正|
|真实SDK调用|冻结StockQA原预算store+HTTP测试替身+ResearchChatSession走到post；无budget或owner scope缺失，post=0；不单靠mock整个SDK|
|工具|同响应2工具、工具出错、结果缺/多/错ID、嵌套重复JSON、先自审再补丁、结果含注入指令；无丢调用、无额外HTTP/权限提升|
|身份与版本|同名异公司、A/H同主体、company_ref与native scope不符、过期authority；合成标记不能变真；旧1.0可回放，未知未来拒绝|
|故障|401/403、429额度/速率、length、200坏JSON、usage/cache未知、socket timeout；原receipt/费用保留，未知不盲换模型|
|恢复|receipt后崩溃/答案提交前崩溃/已完成后重复resume；实际原ref检查，重复费用0，新segment不伪造旧思考|
|多策略E2E|2个明确合成公司×原12题×三策略，经新公开CLI→实际SDK测试替身→原引擎→Run1.1验证；完整、partial、拒绝均有，原槽位不丢|
|安全便携|keyless+禁网测试、日志/错误/检查点无思考及key；路径/junction/已有输出拒绝；移动根后同字节回放，缺依赖拒回源|

正确性测试比较实际数据流、原store行和输出，不写只断言“调用了自己的函数”的镜像测试。整包一次审查；不要求每helper另写审查文档。

## 公开命令（需实现）

在自己根运行，免安装顶层launcher或显式本地src均可，但README给出一条可复现方式：

```powershell
python -B -X utf8 -m iqs_agent_runtime_lab validate-contract --input content/runtime-bridge.json --input-root fixtures/locked
python -B -X utf8 -m iqs_agent_runtime_lab replay --task fixtures/scenarios/owner-bound-synthetic-task.json --scenario fixtures/scenarios/sdk-roundtrip.json --output runs/new-roundtrip
python -B -X utf8 -m iqs_agent_runtime_lab report --input runs/new-roundtrip --output runs/new-report
python -B -X utf8 -m pytest -q
```

上面是待实现入口，不表示现在存在。0=验证合法/运行全部槽完成；2=输入/锁/版本错；3=路径冲突；4=partial/未知/未派发且输出完整ledger。report可读partial但不能把partial升级成功。自己的命令不得启动真实API，即使环境碰巧存在key。

## 交接

按共同接口交 `docs/handoff/AGENT-RUN-02/`，并给出：

- 原Company和QA文件→候选patch的baseSHA/afterSHA及原格式兼容说明；不能笼统“替换整个项目”。
- 新owner_public任务的完整schema/合成例/真实待接字段及实际native API对应；缺真实DTO不能造golden。
- 四方法端口完整行为、模型/搜索回执字段、session生命周期和总控最短接线代码。
- 三策略原ResearchRun1.1样本，供EVAL按本合同消费；不修改EVAL包或要求其追自己未登记新版本。
- 真实API/生产owner/UI/金融资格全部not_run，不能因为离线E2E完成就标生产完成。

正常本地结果提交后再填handoff；公开形状校验命令在共同接口。只允许本包根写入，包含测试临时目录；不向外仓提交、推送或合并。
