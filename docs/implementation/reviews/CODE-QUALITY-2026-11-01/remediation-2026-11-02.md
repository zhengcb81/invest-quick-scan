# 四组剩余问题整改结果

日期：2026-11-02。状态：本轮原5/8/9/10软件范围已完成，集中独立审查通过；不是全项目或金融准确性验收。未新增施工支线、模型客户端、执行/预算数据库或许可系统。

|原组|根因与最终处理|
|---|---|
|5 前端启动|可选答案草稿与必需bank/manifest分开加载；读取/JSON/结构/实际页面解引用的坏容器局部降级，保留可用记录与警告；原子发布快照，必需源失败保留旧状态；未知数据不显示为没有记录|
|8 模型能力|实际ResearchChatSession构造与公开能力复用原SDK纯声明；普通web_search不冒充final_json研究能力。新顺位对native/external单题也预先跳过确定不兼容的通道，不捕获宽泛错误重问|
|8 共享顺位|显式1.6原preview/confirmation/state冻结有序targets；binding5在原journal保留原primary及完整目标。StockQA原runner组合每route不可变task，只对已结算明确拒绝切换剩余题；原attempt保留实际route/账户/模型，未知和内容失败不降级|
|8 预算与恢复|在原预算事务内按DISTINCT物理budget attempt统计全原scope；换模型/重启/当前UI参数漂移不能重置首task cap。原lease/CAS只接受已结算明确拒绝并单调前进；旧确认不扩权。已保存CP排除提问/重放，原safe无CP先沿原task零发送恢复|
|9 公共边界|生产factory/engine通过QA公开context、answer transport、task/live validation薄接口，不复制原校验或跨仓读取私有成员。legacy研究task保留旧合同|
|10 旧工具链|one_click显式workspace/work、caller相对路径解析，provenance只读明确两库；不传work则标未检查。HTML真正落盘并转义；固定旧实验检查显示历史，不作为当前工作区检查或新门|

共享缓存另修一个真实根因：原StockWiki按successful_scan判新鲜、QA却再按资料日期拒绝。现在按原policy同一时钟引用，保留原信息日期/成功扫描时间/实际模型；未来、过期、无原搜索回执或未批准目标仍拒。

## 针对性测试与独立审查

以下有重叠，不合计成总通过数。没有跑小时级全仓套件。

|范围|实际结果|
|---|---|
|UI作者/非作者|37P/51子例；非作者原5个真实ESM反例和boot组7P/16子例。必需bank坏仍失败，坏可选源不崩溃、不假无记录|
|公开边界/旧CLI|非作者当时81P；root最终含新route投影/入口/原Store110P/4.86秒。真实caller cwd CLI、SQLite字节不变、原transport28组合一致|
|SW/IQS顺位合同|非作者105P/17.79秒，含原SQLite active/unknown优先、TTL/未来时间、真实fixed CLI/capture；旧无targets行为不变|
|准备入口|作者23P/248.26秒含原36题双scope/重放与恢复/比较兼容；非作者新1.6端口16P。不把mock端口视为真实准入|
|QA授权/缓存|相关12文件216P/125.48秒；新增25P，非作者含今日顺位变化与原state篡改等7反例合32P/5.14秒|
|原Store/pack|组合117例116P/1F；唯一历史v16夹具漏删24/还原25 CHECK已修，定点1P。真实预算并发争同一cap、pack计1次、过期epoch、未结拒绝均通过；没有新增迁移DDL|
|共享执行独审|79P/6.38秒；最后paid-route尾组非作者28P/6.53秒，覆盖旧确认不扩权、partial题排除、原cap继承、混合原route根和无safe拒绝|
|首次原owner/SDK E2E|1P/491.08秒：两题pack2，primary401→fallback成功，2CP/outbox ready；普通owner重建后题序变化仍0新HTTP|
|最终已付窗口E2E|1P/656.77秒：fallback响应已保存后强制发布中断，CP全空；删除今天模型配置，原paid-only owner/lifecycle按原fallback恢复2CP/outbox ready并hydrate；恢复配置后普通owner冷重建零新HTTP、CP相等|

独立执行审查由非对应作者完成：授权域new6_retest，执行域ui_boot_fix，UI/旧工具与SW合同由其他作者交叉复测。发现的mixed已付入口只准单route、今日顺位阻止旧答保存、首cap漂移、单题研究能力预选及完成primary错误重放等均已修并定向通过；没有未修阻断。

原owner/SDK E2E仅替换vendor HTTP，使用合成公司和回答；最后窗口复用先前构造的SDK client。它证明owner冷重建、无当前模型配置文件的零发送恢复，不证明全新进程经完整CLI无key构建SDK，也不证明真实供应商准确性、StockWiki ACK或新的UI三市场入库。之前真实三市场/原gen6 ACK的既有证据独立保留。

本机证据目录：`runs/qa-public-seams-2026-11-02/`与`runs/new6-retest-2026-11-01/`。关键最终日志为`ordered-paid-final.log`、`independent-paid-route-tail.log`、`authorization-v16-independent-r2.log`。旧的同名日志曾被早期复跑覆盖，按progress明确范围引用，不再用其证明旧80/81P。完整重复回答/上下文/数据库/密钥不随文档发布。

所有本轮自有隔离TEMP/五仓副本结束自动删除；去密钥、禁pytest缓存和pycache。两个原owner/SDK E2E加载原网络guard，其他短组不冒称额外socket拦截；没有下载公司文档，没有清理他人运行数据。正常hooks格式/行尾/isort曾自动修文件，真实Optional类型问题已修；最后完整耦合提交全部hooks通过，未绕检查。

## 提交与实际部署

|仓库|本轮提交与远端|
|---|---|
|IQS|d168425公开边界/旧工具；da0fbd5顺位合同；e20e1b5准备/实际route与E2E；均已推既有origin/master。文档提交见后续Git记录|
|StockQA|d1d22cc SDK能力/公开seam；58fb6ce完整顺位/预算/已付恢复；均已推既有origin/master|
|StockWiki|dc857a5组合原planner/cache/preview/CLI；本地提交，无remote|
|UI|77d372c可选草稿故障隔离与未知展示；本地提交，无remote|

原8766已按实际PID/argv核实无活动子任务后，沿原启动参数隐藏重载，使用--no-refresh，不建新数据根。重载后公开doctor ready、blocked_reasons空，实际main导入的store.js返回200且含新optional source逻辑。

普通policy1.1 successful_scan/24h、pack2/thinking/max32768/shared=null/refs=null保持；execution_bundles60。原账本仍87HTTP/2053896micros，inflight/未结0；gen6 delivered/CP1，gen7 leased epoch2/CP0，旧raw/safe/分数未改、未重发。新增顺位必须在原owner显式1.6新准备中使用，不自动升级旧确认；专用人工work-decision仍按既有版本，不冒充1.6比较/continuation。

## 下一步

四组软件整改闭合后回到PWF既有小池回答质量收尾；gen7内容/金融范围、200家可靠性、事实F05/两消费者与全池配套仍未完成。不得拿本轮工程测试消除这些范围，也不再重复实施本轮四组或重问原已付任务。配置见[共享引擎实操](../../shared-engine-operations.md#共享扫描的模型顺位)。
