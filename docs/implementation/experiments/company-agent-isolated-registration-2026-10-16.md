# Alphabet 隔离真实研究对照：S1R

2026-10-16。用户要求接收RUN后推进真实公司准确性、费用、耗时对照，已有后续实施及真实调用预算授权。总控提出先隔离研究或先生产owner的偏好选择；尚无答复，给出充分答复时间后，按推荐的隔离研究路径推进。若用户随后选择先完成生产接线，停止尚未发出的后续实验。

这是新增实验分支，不修改/冒称原生产S1的准入：原 integration-contract §4“协议探针的budget-only路径不能变成公司研究路径”继续约束原 `create_runtime_port` / ResearchRun1.1 / owner_runtime 路径。本试验用独立、显式的 `iqs.isolated-company-research/1.0.0`，不调用该生产桥、不自填owner_runtime、不生成生产评分观察或确认。它复用StockQA ResearchChatSession和原已建立S1原生预算库/路由/发送登记；没有自建模型HTTP、检索或费用账本。其结果不关闭G3/F05/生产准入。

## 请求前锁定

- 公司仅 Alphabet。以原真实主体的只读核查和2026-10-13题库manifest profile作为身份出处；多地证券不拆公司，不建立新股票池。定义与实际题号按已验证routed12，包含OPERATING_01，完整原题定义/锚点不改。完整渲染prompt和哈希保留为输入原件；模型前缀只发送原始题义定义，共享一次schema/指标注册表，去掉每题重复的渲染包装，避免161987字节题对象中130733字节重复prompt。
- 三策略fixed3、free_agent、evidence_agent，各2次；repeat1正序、repeat2逆序。使用Company Lab已修复的实际调度工厂。fixed3顺序三题；evidence_agent事实依赖三题；free_agent开放剩余题，允许模型分批交卷。free/evidence在预算内多一轮全局自查；这是S1R策略修订，不与原冻结策略协议混称同版本。
- 全部deepseek-flash，https://api.deepseek.com/chat/completions，开启思考。隐藏思考仅SDK私有内存，不能写原始provider响应/请求体；保存脱敏原生回执、公开合法答案及修订、无思考工具结果和输入hash。
- 六会话使用同一冻结公开REF证据，按fact_id/source_id逐一核对后去重，保持十个事实、六个来源及原限制，不带私有rubric/gap/gold。S1R搜索请求=0，用来分离打包/共享会话的影响；并不评价Brave/Tavily/ZAI效果。
- 每会话最多8个SDK step、每次max16384输出token含思考、会话输入240000/输出48000/900秒。step调用数与真实HTTP分别记录；HTTP数取原生budget/receipt，不把preflight或被拒SDK调用算收费请求。首家公司最多48真实HTTP，计入既有144HTTP/USD14.40共享预算，不重置S0或S1。
- 单会话不跨模型自动切换，不盲重试。任何不明发送/未计价状态停止后续会话，保留原预算预留。进程崩溃不自动重开同run；输出目录存在则拒绝，防重复消费。生产跨进程恢复仍未接通。
- 价格复用已验证CohortPriceResolver，当前官方DeepSeek档与2026-10-15一致；跨峰谷窗口拒绝自动结算。单独报告公开价估算、保留预留和现金账单未知。缓存仅用真实usage，未知不填0，不宣称“冷缓存”。

## 质量评估及局限

客观参考在读模型答案前锁定为[10个已独立核验主标量](alphabet-objective-reference-2026-10-16.json)。仅资格范围内核历史标量，不把复合父记录或1–10评分全部授予资格。按主体/指标/期间/单位/币种/口径匹配，跨题去重；分别报告正确性、引用支持、覆盖、合理拒答。所有非数值判断和评分理由需实际盲评。结构验证使用IQS原standard_answers.validate_content，引用id/URL/日期绑定当前公开来源，原Company leak scanner；它们不是金融事实审核。

原实验PWF和生产协议不被本次隔离工程替代。真实输出只能说明这家公司、这套证据、这一个模型和明确token上限下的观察，不宣布普遍赢家。之后根据结果决定多模型、真实检索S2和重复提问扩展。

## 启动与隔离

`python -B -X utf8 scripts/company_agent_research_pilot.py --config <冻结配置>`默认仅预检。真实调用须显式`--live`，由本轮launcher仅注入DEEPSEEK_API_KEY（不落配置）、DNS/443仅api.deepseek.com，写入只允许本轮实验目录及既有S1原生budget SQLite精确路径；SQLite connect也校验。无财报/全文/HTML下载、无生产owner/名单写入。输入raw SHA、真实进程时间/PID、每次发送准备/原生回执、预算前后和临时文件清理留档。
