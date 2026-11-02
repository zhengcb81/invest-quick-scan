# 保存、补封与入库接续复查（2026-11-02）

本轮按用户要求独立检查[上轮整改](adjacent-remediation.md)的接续边界，实际复现后修复；不扩日期、模型或行业研究支线，不增许可或审查回执。源码、123项整合测试、集中独审及原SDK冷进程接线均通过，已完成本节点。

## 已确认并修复的共同根因

- **已付保存不依赖无关诊断路径。** 默认DBjournal可恢复时，不因旧diagnostic目录变文件或无效路径提前拒绝；只有缺journal、确需legacy capture时才验证原fallback路径。原新capture写入安全不放宽，坏fallback也不伪造正文。
- **原公共批量补封也须逐工作隔离。** 工作局部冲突不阻后续项，成功后诊断不覆盖实际成功。旧ready不自动等于当前原authority要求的目标封包完成：抽公共只读`get_matching_sealed_delivery`复用原native构建及匹配，普通batch/recovery与共享finalizer共用；不读新配置、不改包、不签新许可。legacy沿原native规则，V2/3按本次原冻结authority的期望包判断。真实存储损坏、全局权限错误仍传播。
- **交付恢复入口不重复审整个job。** resume原来先核所有条目，已交付或失效邻居会阻正常pending包。现沿原worker逐pending核原scope，单项失败保留，其他独立包继续；原接收库身份检查不变。
- **已满足的缓存引用不是待导出新包。** 原登记journal的references明确投影为referenced，不根据自由文本reason猜测。混合范围只导入新work包，纯引用范围无需import、包数0、不造ACK；真正缺工作仍partial。原观察、时间和模型不变，不称新扫描。
- **ACK按原观察逐项承接。** 真实坏hash/foreign consumer原来使helper抛出，后合法ACK未尝试。现在原Store独立验证每条，坏项拒收且不改原row，好项继续；合法非空子集可先应用，缺项为ack_missing，完整receipt后续幂等补齐。foreign/duplicate observation IDs仍在原scope层拒绝，SQLite/权限等整体错误不吞。不改变StockWiki协议或冒称缺ACK已签收。

## 反例、验证及独审

实现IQS `d7ec166`（10源码/测试文件）、StockQA `e5a2781`（5文件，正常hooks后推原origin）；Company、StockWiki及UIlab本轮未写。

- QA实际RED 4F/3P；最终作者15P /31.48秒，独立12P /34.92秒，含坏可选capture不阻journal、真正legacy仍保护、原batchtyped冲突、成功后诊断及旧compactready不能冒充V2目标。
- IQS交付恢复三例RED，jobs完整27P；缓存引用native两例RED/一个对照通过，修后native3+service4共7P /18.70秒，jobs+prepare完整43P /4.47秒。delivery原模块30P，两个新增测试辅助遗漏API_requests信封已修，受影响两例32.78秒通过；未放宽产品检查。
- 总控原SQLite ACK四例实际RED（39.23秒），逐项修复后含共享42例组46P /75.48秒；补合法ACK子集两例后，最终相关五模块整合123P /308.20秒，TEMP清理。
- 非作者`peer_persistence_chain`独立IQS22P /180.90秒（ACK6、共享目标匹配1、缓存/service7、resume3、receiver4及缺ledger1），QA12P /34.92秒，核最终代码无开放阻断。组间重叠不加总。

整合测试和独审使用合成短问答、原SQLite与公开接口，fixture中的权限/producer reader seam不冒充真实owner资格。根共享unit只替身公共匹配函数，QA真正SQLite/native期望包匹配另测。没有新模型或搜索请求、公司文档下载或真实库写入。未证实的任意getter typed故障候选经核源码撤回，没有新增无依据防御。

测试环境去密钥；核心helper/独审子进程禁网，根整合父进程加网络audit且原辅助脚本禁网，不将未装guard的fixture初始化夸称统一系统级网络沙箱。自有TEMP均已清理；QApeer首包装器日志句柄清理延迟，在子进程退出后核实绝对路径精确清除。AppContainer长路径导致的五例环境失败改短TEMP后通过，不是产品RED；未改产品路径规则。日志在`runs/audit-effectiveness-2026-11-02/`的`save-seal-qa-*`、`persistence-chain-*`及各交付测试日志，原SDK冷测试日志另在`runs/qa-public-seams-2026-11-02/persistence-chain-native-final.log`。

## 接续状态的含义

保存完整只表示原CP范围完整；补封完成须符合原本次authority目标；入库成功以原StockWiki ACK为准。本地ACK容器`owner_rejected`表示尚未全确认，单项`ack_rejected`和`ack_missing`分别区分无效与缺失回执，不把它们当成远端真实rejected ACK。重试复用原CP、封包和已应用ACK，不重新生成回答。

原SDK冷进程验收1P /419.97秒（runner421.35秒），五组件自有隔离副本、两个全新进程在删除当日模型/预算文件且无密钥时恢复同原响应/CP，未问题保持缺口，新增API为0，副本已删除。只替vendor wire，不能代签本轮多包真实金融或全池运行。原服务精确重载后doctor ready，新旧观察可读，原配置hash相同，账本仍87HTTP/2053896micros、0在途/未结；PWF/实操随本节点提交。不得由测试数量宣称金融准确性、全池或完整产品完成。
