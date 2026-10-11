# 编制依据与接收边界（2026-10-11）

这是总控编制施工包的记录，不是三个Lab已经建成、已派发或测试通过的记录。

## 基线与选择

编制基线为IQS `master@cf1d05558827d70df23b2268d21a79afb89cd39c`。编制前已核根PWF、任务/验收场景清单、现有交接CLI、契约和版本归档；同一只读规划agent提出候选，总控选定三个非重叠新根。三根在 `inputs.lock.json` 的实际观察时均不存在，未创建、初始化索引或派发。开工须重查，不能把这个历史观察当独占锁。

IQS、StockQA、StockWiki由总控继续C06/W15发布收尾；EVID/FACT仍有原owner整改。新包不占这些根，不接管未完成整改。配置工作台没有另立一包，因为当前模型/搜索策略模板已有实现，再做会重复。Theme/Industry不另造第二份预研，也不提前解锁G3/F05/W11前置。

| 包 | 支撑任务 | 资料/工具的产出 | 后续由谁接入 |
| --- | --- | --- | --- |
| MATRIX-CASE-01 | W14/V02/V17/V18/U03/U04 | 可复验的比较/版本演进案例、离线资料validate/export | 总控接权威比较器、演进计划和UI入口 |
| LOAD-CASE-01 | O02/L03/X09 | 合成负载、手工trace和离线分析 | 总控接真实公开执行入口；200家公司真实试点仍独立 |
| IDENT-EDGE-01 | W02/W03/W13/O01 | 官方短事实与身份边界候选、离线validate/export | StockWiki身份owner核实；总控公开CLI接收真实DTO/golden |

这些task_id表示支撑关系，不移交任务所有权，也不证明全任务完成。另两包未交付不阻塞任何一包在其限定范围内施工。

## 输入与接口

输入锁共41个不同文件；MATRIX消费27、LOAD消费15、IDENT消费15，共享项只读。保存原始工作树bytes/SHA，不改用Git blob SHA。当前锁只发布路径与元数据，没有把历史golden、源仓、实验私有intake或生产DB复制进本批目录。

本批Markdown/JSON固定LF；verification原日志禁Git文本转换，保持过程记录的raw SHA。此目录的精确gitattributes不修改输入源或全局Git配置。

首次正常提交预检将原生Windows stdout的CRLF视为尾随空白，因此未执行commit。原日志不改字节；仅将本目录原日志作为binary证据归档，保持process记录的大小/raw SHA，产品文档与JSON仍接受普通文本检查。随后正常重跑该提交预检，不跳hooks。

每包开工把获准锁内输入冻结到自身根，可脱离动态主线开发；漂移处理见共同规则。标准handoff沿用现有1.0.0，新的案例/trace具名schema由各Lab建立1.0.0，不能伪装成Observation或IdentityMappingDTO。manifest、三个模板和共同规则是配套入口；模板只有结构预检意义，所有执行结果字段必须在实际交付时重填。

身份历史manifest引用的三份真实owner golden原bytes/SHA已与清单匹配；生成命令是历史记录，本轮没有重跑。评分尺只有未校准候选，query只有锁内历史公开边界。这些输入不能支持新的真实金融/事实覆盖通过结论。

## 本批验证

只做一次本批文档集中核验：锁内原字节、任务ID、三个写根互不包含且不占现有仓、模板通过现有公开handoff CLI、相对链接存在、历史golden对应原清单。实际结果在 [validation.json](validation.json)，模板原命令/stdout/stderr/退出码在本目录的 `verification/`。

没有运行三个未建成Lab的产品测试，没有网络/模型/搜索/收费请求，没有生产名单、数据库或外仓写入。包实施时各自一次稳定候选相关全回归、真实本包CLI E2E和一次集中review；收到后总控一次包级接收和受影响续验，不增设helper审查。

编制中曾读取错误猜测的schema路径，随后从已知公开CLI定位正确的 `docs/implementation/parallel-lanes/handoff.schema.json`；首次元数据生成把历史manifest的 `path` 错写为 `file`，在任何输出落盘前失败，按原manifest修正后生成。它们是编制控制器错误，不是产品反例，也没有运行三个Lab。
