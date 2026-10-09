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


## Phase111 实际LLM上下文使用接续：2026-10-09
实际客户端接线和新schema10 intent已完成私有TDD，八文件455P；见answer-use-interface.md。下一段必须以实际store核proof/来源URL，并明确checkpoint版本/迁移，原schema1 SQL CHECK及消费者假设不可静默放宽。runner/两阶段/跨租约/MCP/公开CLI、整批静态/一次review/源发布/严格清理仍待。只存hash/引用，没有prompt/reasoning正文；源schema8未发布，其他仓0写。

## Phase111 检查点与执行器接续：2026-10-09
私有schema11/checkpoint2/use-proof1.1保留原native响应与旧checkpoint1字节；实际runner/同步provider metadata、完整standard body/C06/outbox通过672项相关回归。读checkpoint-interface.md；这不是源发布或完整验收。
下一段先补明确公开result版本和IQS ROUTE_02消费者的external来源规则，再接真实runner/cascade调度、异步provider、两阶段/跨lease/MCP/公开CLI。现有public1.0仅native来源，不能暗改历史解释或造web_search_calls。整个Phase111齐备后一次集中审查/正常源Git/严格清理；当前自有根保持，不另建工程回执或小节点门。

## Phase111 公开结果接续：2026-10-09

公开producer1.1与IQS消费者兼容已经接线：actual store/原HTTP/use proof验证后才输出external binding，native-only仍1.0；actual client/SQLite→JSON→IQS route的external/hybrid通过，原模型/receipt hash/真实native事件保留。读public-result-interface.md。StockQA十四相关文件682P/71.45s；IQS完整相关110P/1F及过期native CLI fixture修正后的原失败1P，原timeout/失败均留档，不声称同一调用111P，也不新增小节点独审。

下一实际动作：原runner/cascade检索协调和async provider投影；随后跨阶段/跨lease恢复、逐HTTP MCP init/discovery/search、公开CLI冷/暖/恢复/失败，最后完整批次一次集中相关回归/静态/审查/正常源发布及严格自有根清理。source仍42a517c/schema8，当前新public1.1仅私有producer；其他外仓、新授权和全局门不自动关闭。

## Phase111 正式调度接续：2026-10-09

runner/cascade检索协调与async投影已私有实现。独立identity/manifest/query覆盖在DB和HTTP前验证；retrieve完成后仅由owner绑定原context，再由真实发送边界记每次模型使用。同步/异步以及external-only/hybrid区分保持。失败关闭工作/路由/context绑定，unknown搜索保留费用与原操作，不让模型抢先回答。

实际public main()集成（不是OS子进程）10项通过：冷暖原回执一致、原上下文及全部失败/成功模型attempt恢复、401/明确429切换、独立manifest具名早拒、unknown搜索停机和损坏SQLite use证据不覆写原答案。真实根UTC/answered_at采用已保存HTTP时点；新版1.1的attempts采用owner持久HTTP，不复用仅在内存的route装饰。旧1.0未变，frozen public-result-interface.md不回写。本批synthetic身份/模型/价格及HTTP替身不能作为真实gold或准确率。

下一动作无原生搜索模型的实际external-only文本协议，随后跨阶段/跨lease恢复、MCP逐HTTP收费、真正公开子进程CLI，整个Phase111一次集中回归/静态/独审/正常源发布及严格自有根清理。33路径源范围已先报备，均只在IQS独占副本；其他原门不动。

## 最新接续：DeepSeek文本与schema12历史保护

本段优先于上方历史下一步/时点方案。36路径已先报备且仍仅私有副本；DeepSeek官方Responses external-only、显式model-resolution1.1及同步/异步/级联/公开main接通。answered_at采用实际durable response.recorded_at，原HTTP完成时点单独保持；native短事件通过schema12独立保存，不改变旧HTTP receipt哈希。

原42项GREEN之后，新增迁移保护18项首轮17P/1F定位真实历史补写缺口；现在事件首次插入只随新响应同事务，旧缺失不补写。16文件最终776P/0失败错误跳过/86.57s（controller87.324s），覆盖旧库真实DDL/回滚、事件不可变与坏恢复/上限及既有runtime路径。原失败仅增量归档，不跨批相加；这不是金融事实准确性、真实厂商计价或完整Phase111验收。

下一步两阶段/跨lease恢复→MCP每HTTP独立费用→真正OS子进程CLI，再在完整Phase111同一大节点最终回归/静态/集中一次独审/正常源发布/严格自有根清理。读runtime-dispatch-interface.md；checkpoint07仅IQS进度留档，实际Git看progress。StockWiki许可/联合ACK/真实gold及G3/F05/TH-IN/L03原门保持。

## 两阶段/跨租约追加：下一步转MCP

checkpoint07已正常提交推送4884e7b。追加五项真实client/store恢复路径5P/195 deselected/2.53s，无产品变更，原776执行源只新增一测试文件，不重复全套。已结算搜索跨lease保留context和费用，unknown检索不重发、旧lease在HTTP前fence、晚到模型只留响应与账务；读recovery-interface.md。不是公开OS进程杀停/恢复，过期未发送外部意图仍保守hold。

下一动作逐HTTP计费MCP，必须把initialize、initialized通知（若协议要求）、tools/list和tools/call各自记为真实发送及费用操作，不把工具会话协商隐藏在一次检索中；unknown任一步都停、已有结果恢复不重复计费。随后真正子进程CLI/恢复，最终完整Phase111集中一次审查/源发布/严格清理。当前只是私有进度，不关闭任何跨仓或准确性门。
