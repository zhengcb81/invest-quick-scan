# Q10 请求模型与实际模型来源绑定

基线 StockQA `86b1e8ab1221e085f08718ed31d18e792e526d34`。总控拥有IQS文档/控制器/PWF；实现worker只写[scope](scope.json)中IQS独占副本的文件及其自有worker日志。真实StockQA发布由总控完成，任何其他外仓均不写。不读取用户API配置、生产库或公司资料，不发收费请求。

## 必须保持的链

POST payload.model与派发前route.requested相同；actual只来自HTTP响应的model。显式许可按canonical provider、协议、requested、resolved精确匹配，无通配/前缀/大小写猜测。默认仍exact；未知和未注册替换拒绝成功checkpoint，诚实保留响应/费用来源。任何native search协议、sync/async和legacy路径不得绕过同一许可。

使用独立`quick_scan_model_resolution`版本化配置，不改IQS已冻结的v2 route字段。严格验证未知键、重复映射、空/control字符串、协议及有限集合。非空许可的非秘密投影进入policy指纹和route snapshot；空缺配置保持旧无alias指纹兼容。当次许可在发送前冻结并参与durable attempt身份，恢复不能读当前配置追认。同步/异步provider构造同样接线；fallback使用实际选中route，format repair每一次单独来源。

schema8新增不可变旁表。成功响应和attempt outcome同事务保存完整sanitize receipt、其hash、actual/model身份和仅HTTP JSON canonical SHA-256摘要；不存原HTTP正文。摘要说明为canonical JSON（有限值/无歧义键），不得宣称原网络bytes。新成功checkpoint只接受当前work最终ordinal的耐久响应原件，读取／封包也保持此来源；不得在repair／fallback新attempt出现后退回中间成功receipt。旧checkpoint历史exact读取可保留，旧无checkpoint attempt不能从requested补actual，也不能被新alias策略补授权。v1–v7升级空新表，迁移失败rollback，JR2 schema7保护和旧ACK兼容保持。

已有Observation `execution.model_requested/model_resolved`、run/scope/question/lease和封包重建校验保留；不改公共ExchangePackage/ImportAck/schema，不让正文或merged repair metadata当模型权威。计费继续按actual rate card；未知价格保留unknown与费用预留，不取requested价或0。

## 单批测试与交付

先测试RED、后实施，原日志不可覆写。三个native协议与sync/async覆盖exact/注册alias/未注册及错provider-protocol；route与POST不等须在费用预留／send意图／HTTP之前拒绝，已有provider构造阶段凭证配置解析不冒称零读取；正文假模型、receipt/摘要/response ID篡改、别名配置派发后改变、late lease、迁移缺失、重启与伪造sealed包均拒绝无部分落库。公开CLI冷跑alias正例后，独立进程warm/seal不用HTTP仍相同requested/actual和同包；fallback/repair只最终attempt有权成为checkpoint。

仅受影响套件、原JR2/checkpoint/outbox回归及owner静态检查，一次集中独审。测试synthetic模型别名为软件证明，不填实际厂商未确认的alias，不冒充真实owner golden或G3/F05签收。worker交付日志/用例映射/准确文件清单，不修改PWF、正常提交或外仓。总控核源hash和writer状态后才能发布；清理只删本批自有根，共享TEMP和历史根不动。
