# QA-NET-01 外部证据生产链接续

这是原施工包步骤3–6的剩余实施批次，不重做已签收parser、准入、原生搜索、Q10来源追溯或StockWiki整改。总控拥有IQS/PWF与本批StockQA唯一写线；StockQA按既有全仓授权逐批报备精确范围，其他仓只读。

当前StockQA输入为42a517c4bd6bc8219f926957c6c332944da3278a，IQS基线8363b49；已建立runs/n111a私有副本，基础边界24项和单次检索传输相关60项通过，尚无外仓发布。现行生产策略即使准入external仍固定dispatch=false，runner返回external_context_not_implemented。原整改只验失败关闭，不证明生产外部链完成。CodeGraph对新模块未命中、旧store上下文行号与当前文件不符，按已定位文件读取，不能据旧结构片段重造客户端。

连续实施一个完整批次：

1. 明确现有C05 work/attempt/预算/health接口与C06 external来源表达；若现行契约无法表达，先记录最小版本化提案，禁止伪造native回执或塞extensions。
2. 冻结精确源/测试范围与非秘密输入，在新的独占IQS临时根复制允许的Git源码；不复制真实配置、凭据、数据库、名单或原七未知项。测试环境剥离密钥、限制网络和写入，仅HTTP边界stub。
3. 先跑公开行为RED，再接入Brave/Tavily/Z.ai已定义adapter、冻结查询计划、证据筛选/短context与既有回答客户端。模型顺位和搜索顺位独立，复用既有预算/attempt与故障分类，不能另造通用重试器。默认策略/真实paid route不自动启用。
4. 覆盖冷跑、warm零请求、两阶段恢复、429/拒绝切换、发送后unknown保留预留不重放、费用/存储权不明早拒、坏JSON/不可信snippet/过期或错误实体、答案来源越界。按实际HTTP及stage分别记账，原生工具receipt不能冒充external。
5. 一次受影响单元/集成/公开CLI GREEN与集中独审，正常源仓钩子/提交推送；受审字节变化时如实补测，保留原RED和控制器错误。逐文件SHA与私有根严格清理后更新PWF和交接。

完成仅证明本批真实生产入口的离线实现，不关闭G3/L03/F05、StockWiki联合ACK、真实owner identity/facts golden或TH/IN写授权；不声称事实评分准确性或真实厂商计费认证。DeepSeek Responses忽略搜索，Anthropic续写成本上界仍未获验证，不能靠本批默认开通。

控制器已观察错误：StockQA根AGENTS.md不存在；不创建它。首PWF补丁只匹配行前缀而未匹配整行，工具原子拒绝、未写入；改用完整段落更新。上个只读heartbeat的外仓Git沙箱Permission denied已通过原授权下只读提升核实，三源仓HEAD不变且clean，不据null输出称clean。

检索耐久段采用独立external_journal模块，但事务、预留、槽位、结算均调用现有QuickScanWorkStore/Q09；不建第二账本。schema9仅追加不可变检索操作/结果，旧版本空表迁移不补造搜索历史。检索使用budget-only operation，不能成为成功答案attempt。检索意图与预留同事务，响应与预算结算同事务；unknown/无计价保留预留，晚到响应可保留账务但不推进失效租约下的答案。缓存必须核身份/题目/计划/策略/版本/TTL和已结算状态；不以query中的公司名认证归属。先补失败用例，再实施，最后与整批公开CLI和回答proof一起集中验收。

配置接续：独立1.1 schema及执行计划，原1.0 schema不改；域名认证与共享网站的发行人路径认证区分，不将www.sec.gov根站等认证给单一公司。1.1冻结投影篡改早拒。共享budget投影保留原模型顺位和现金额度，仅供Q09会计；回答cascade仍只用原模型policy。外部计价区分全部HTTP、已确认成功搜索、实际provider usage；无明确拒绝计价记录不补0，未知保持预留。execution-policy-red-01为15F/10P/39deselected，10负例目前仅整体版本拒绝，GREEN后需检查单独新约束，不虚称原RED全部对应现存漏洞。

本轮配置/数据段最终shared-owner-green-01为247P/20.94s，所有原失败保留。跨公司预算版本仅绑定模型预算及检索route/dispatch/计价，不含各公司执行计划；否则真实Q09在途版本保护会阻断并行。检索缓存同轮多题共享、明确新轮新操作，原历史费用不重置，未知发送继续停。上下文必需独立manifest hash，逐源校日期/host/path/检索时间/费用；context数据/metadata同受company cap，query_coverage明确缺项，claim_verification=not_automatic。此段尚无实际LLM或公开CLI，下一步仍原步骤3–6接线，不提前关闭大节点。

## Phase111 检索调度接续：2026-10-09
协调入口现已私有实现：lookup→必要时Q08 admission→Q09原预留/intent→单次adapter→原journal计价settle→重建短context；真实保存故障、并发和跨query中断都覆盖。最新276相关测试通过，原失败保留；没有集中review、LLM/公开CLI/MCP或源发布。

下一实际接线点是现有LLMClient/AsyncLLMClient.send_search_request、_search_request_payload、_parse_protocol_search_response及begin_quick_scan_send。不得改走不记账send_request：原生prompt/receipt SHA和Q10实际模型都保留原HTTP来源。external-only真实payload不提供native工具；hybrid按显式计划，同时分别证明外部context和原生工具；BaseLLMProvider不得继续无条件要求模型native搜索。先以实际HTTP payload与SQLite反例RED，再建立版本化私有context-use intent/result（绑定实际work/lease/attempt、context SHA、最终prompt SHA、原retrieval receipt SHA、实际response receipt SHA），调用点前后原子、不可由回答正文回填。不向native receipt插外部搜索事件/搜索route actual_model；公开C06 generic搜索状态只能在独立use-proof通过后投影。格式修复/备用模型是新的实际HTTP收费attempt，但复用原冻结上下文，warm/返回结果未知不得重复请求。MCP每个init/discovery/search单独Q09 operation，尚未完成，不把before-reservation拒绝作为最终交付。
