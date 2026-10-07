# 三条线的固定接口与汇合边界

主权：IQS定义题义/版本/schema；StockQA生成问答/执行记录/耐久投递；StockWiki写身份、观察、ACK、查询与UI；Lab只做离线诊断和实验提案。公司名/ticker不是唯一键，多挂牌不得复制发行人；没有verified身份来源不能编造StockWiki正例。

## QA-C06-02输入/输出

消费[Phase92输入映射快照](inputs/iqs-phase92/c06-authority-v2-input-map-2026-10-07.md)、IQS真实发布manifest、身份文件原字节、私有authority2.0.0/context1.0.0。context每题只有metadata和冻结/实际prompt hashes，不能夹answer/execution。公开ExchangePackage仍1.0.0、Observation1.1.0、Answer1.0.0，不改公共schema或旧authority1.0。原始文件SHA与canonical内容SHA分开。

正式语义见[交换契约](../../../contracts/exchange-and-query.md)、[Observation](../../../../../schemas/observation.schema.json)、[Answer](../../../../../schemas/answer-content.schema.json)、[Exchange](../../../../../schemas/quick_scan/exchange.schema.json)及输入锁的准确路径。若这里版本与原件不同，报告差异，不能猜另一份schema。

产出：真实StockQA公开CLI从冻结authority/manifest/identity与完整标准答案封存单观察包；包/item/payload/observation/content地址完整，provider/model/timestamps来自原attempt，不来自封包日期。version/revision/head/supersedes只在新增耐久侧表保存，旧checkpoint/包/ACK不原地改hash。导出稳定字节+公开生成命令+输入fixture来源；synthetic身份明确标synthetic。

消费StockWiki ACK：package/item/observation/payload/hash/namespace/store全部匹配才accepted/already_present落定。send_uncertain先对账，无充分结果不能重发/换head/解锁LLM重问。接收不可用保持result_ready和具体durable block。

## SW-REPAIR-02输入/输出

消费现有StockWiki import/query/backup/UI公开入口，原六反例、旧`9f552a67`的真实producer query snapshot与明确synthetic完整Observation。**本卡六问题测试不依赖新的QA完整接线。**输出修后query/backup/UI能力和准确CLI/HTTP签名；协议变化显式版本，旧snapshot兼容不可通过放宽跨query匹配完成。

查询不得混合不同subject/revision/scope/口径/模型的分数；没有唯一选择时输出ambiguous/可见变体，不能靠后来的高分入选。多条件AND/OR由同一服务器规则处理。没有facts/历史时标缺口，不临时生成。恢复/prune只操作受管、可核验owner的备份，不使用manifest自述作删除授权。

SW产出需要总控接收的公共query schema/capabilities/真实owner golden与**生成命令**。可以明确哪些已存在、哪些仍missing；本卡不要求伪造真实身份/事实golden填空。six-fix complete不自动等于F05或TH/IN前置齐全。

## EVID-LAB-01输入/输出

只读IQS已提交`5edf5eb497a0a8d5b3e1057f77fe9af76b14ec9a`的三归档、326来源review/join、生成/价格配置，准确SHA在[输入锁](inputs.lock.json)。新独立root可使用`lane_id=iqs`的原handoff，scope.repository/owned_paths始终指Lab。任务L02只委托离线支撑产物；不是重新宣称60家公司校准完成。

输入历史答案不变。历史source snippets已删，source-index只有URL/hash；缺正文不能重建当时证据，相关内容支持输出not_verifiable。review标签可以用于软件校验和已报告分母，不能充当人类gold。schema/claim引用有效和事实正确是分开的结果。

输出为Lab自己的非生产诊断schema/fixture/CLI与版本化实验proposal；绝不修改IQS问卷、生产阈值或公司的分数/状态。诊断结果含input hash、rule/metric版本、错误码/定位、abstain原因；不能把数值score当质检通过率。新实验proposal标execution_enabled=false/live_not_run；运行仍复用StockQA执行/账本/搜索，不另建客户端/调度器。

## 总控的唯一联合测试

QA/SW交回后，由总控在独占临时根从两个实际commit导出真实组件：回答/checkpoint→完整C06→真实StockWiki observation-import→ACK→StockQA落定→真实查询/UI。HTTP模型边界stub，owner存储/CLI不stub。正例、缺字段/错身份、丢ACK/重复、旧head ACK、未知发送、重启、恢复水位和不可比variant同批验证。只读现有真实身份例的资格边界，不能合成verified身份或扩大样本池。

如果模型已回答但资料不足，原insufficient_evidence与低分保留；困境反转/周期低谷不能被后续质检或UI默默剔除。恢复关注由原版本化标记展示，不替用户新增筛选门槛。
