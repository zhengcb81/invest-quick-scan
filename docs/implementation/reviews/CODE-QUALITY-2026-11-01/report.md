# 代码质量与模块边界审查

日期：2026-11-01。范围：IQS 现行题库、路由、UI/编排、契约与共享引擎，以及它实际依赖的 StockQA、StockWiki、Company/Runtime/UI Lab。此次是代码审查，不修改生产配置、不发模型请求、不新增准入门或施工支线。

起始基线：IQS `dfb831c`。根目录原有其他 writer 的 `docs/implementation/parallel-lanes/packages/2026-10-10/README.md` 改动保留。报告只将实际可达的运行路径视为产品行为；历史实验、测试样例和未跟踪辅助脚本单独说明。

## 随后实施的整改状态（2026-11-01）

本节是当前实施状态，下方审查发现保留为整改前基线；不把历史发现篡改成当时已修。本轮业务源码整改和集中独审已完成；原产品未完项明确保留。

|原发现|当前实施|
|---|---|
|1 已付恢复期限|原owner增加仅保全已付响应语义；发送委托/租约到期与新发送分离，原safe/已结算回执/token/epoch/当前actor/明确撤权仍检查。独审补出的初始化顺序、事件误记、手动分类TTL、混合scope及普通leased capture均已修；截止日沿原binding，外层省略日期沿原inner，不重写原响应|
|2 共享默认额度|生产资源不再读取冻结实验LIMIT_CAPS；按实际packs派生默认请求、输入/输出和时长，显式不足提前报告，旧CP继续原冻结task/证据/输出控件|
|3–5 UI|慢只读请求锁外执行并冻结部署视图，写操作保留原锁/CAS；超时统一；坏草稿仅附属warning，正式结果可读；分页防跨工作区|
|6 跨期间指标|IQS/SDK统一坐标规则；保留多期数据、拒同坐标重复和模糊重复；比较不再按单ID丢行；旧单行未知期间保持兼容|
|7 模块元数据|新未知诊断用中性diagnostic并保留framework；旧冻结schema读法保持；rubric可冻结critical、缺整行仍保留风险。旧profile兼容入口在帮助中明确，多业务用原route入口|
|8 模型能力|共享层消费原SDK能力，移除品牌分支并支持原SDK32k配置；Runtime新协议沿会话预算，旧1.0仍16k。共享跨模型自动fallback仍是原计划未完功能，本次不以循环client冒充接通|
|9 薄边界|StockQA公开脱离私有对象的任务输入投影及原子work-binding快照；IQS不管理其连接；delivery改显式参数；共享错误/纯路由契约抽离，解除两组延迟import环；纯构造/getter减少重复动态权限检查|
|10 实验假设|新部署不自动指旧实验；旧只读工具要求显式工作区，默认候选/输出中性化；旧subject生成器退役；身份归档审计导入纯化，取消公司名和000002的无证据豁免|

阶段验证已有共享入口17P、Company profile22P、Runtime6P、指标/原子快照QA117P、UI72P、题库87个不同测试（其中14项因Windows环境问题单独重跑通过）、共享/交付42P及旧工具25P等。结果重叠，不加总。原owner/SDK/共享引擎完整隔离E2E已1P/744.04秒，原HTTP请求载荷含短证据，保存/封包/复用通过，只有vendor wire脚本化、0收费、临时根已移除。随后paid-only尾修用实际会话/SQLite与原parser118P覆盖，最终独审QA32P/1S、UI3P；关键过期oracle另单跑1P确认非skip。最终完整UI执行模块154P/76.44秒；具体终态见根progress。所有已结束的本轮隔离测试临时根已清理。

保留边界：原登记材料、预算和提供商配置仍须存在并可绑定；删除原route或改写原预算文件时不重造历史许可/客户端。仅时间过期的保全与未知请求重发不同，后者仍拒。生产普通配置与原已交付观察不被这些隔离修复测试改写。

## 继续实测发现并关闭的同节点遗漏

随后真实单题比较暴露 `ResearchChatSession` 仍16k，与已修共享层/Runtime32k矛盾；首段在发送前失败且0新HTTP，却先claim。生产final_json现复用原SDK应用上限，旧工具会话16k保持；纯SDK构造/控件校验移到claim前，实际step仍在原owner/预算/send guard内。有效SDK RED2F→40P、Runtime RED2F→9P；非作者实际构造/撤权/原budget反例通过。

原Store以精确原Lease原子释放确实未发送的claim；已发送、未知、safe、CP与未结预算均拒，不重置epoch或计数。原gen7零attempt/CP的lease已安全释放。旧engine随后把这个原已释放未发送意图也误当unknown；现只从原只读事务和同epoch事件派生not_sent，原native intent/safe/unknown优先，replay_only或任何pending receipt仍禁止新发送。派发仍走原正常claim/CAS/当前owner与预算，不新增许可凭证。最终相关124P、独立not_sent63P/getter27P（有重叠）；真实原Runner单次cap0→1、旧CP不改。

共享部分保存亦已根修：后续题包明确拒绝时，先沿同一真实export的逐成员safe/receipt/语义检查保全成功题到原CP，原entry继续incomplete且不发布完整export。默认全量调用兼容；显式子集返回原分母/剩余题。原owner/SDK两pack32k隔离E2E1P/396.47秒，仅vendor wire脚本化，首CP/ready、次401无CP、再入0HTTP且原CP不变；这份先写E2E不冒签后写的not_sent分支。删除纯构造/私有内存观察的重复current读取，真正发送/写提交不缓存权限。

上述源码集中非作者审查通过；原UI同run第三段真实质量比较仍待终态，不以软件通过授金融准确性。详情与清理限制见根progress；未新发支线或扩大原预算。

## 方法与边界

- 先查 CodeGraph；文件清单可用，context 在当前混合历史副本的大索引上长时间未返回，停止等待后读取已知源码，并用只读 AST/字面搜索补足。
- 独立检查题库泛化、UI/编排、跨仓 owner/引擎，主控复核证据与优先级。
- 区分业务政策、兼容合同和硬编码特例；区分必要的主体/预算/幂等保护与重复的审批、状态和校验。
- 只做与发现直接相关的无网络静态检查或纯函数反例，不重复小时级全套测试。

## 整改前审查结论与核实范围

**已有合理的职责划分，但没有充分解耦；题库可扩展，但若干下游规则没有随之泛化；仍存在重复检查和实际误门。** 以下为当时核实的整改前发现；当前修复范围与边界以上方整改状态为准。

未发现本轮检查的现行题库、原UI和共享生产分支按宁德时代、腾讯、微软等公司名称或ticker选择分数、指标或执行行为。发现的是实验参数进入产品路径、旧工具带公司实验目录、跨仓私有对象耦合及重复规则漂移；不能据此保证每行代码均无公司特例。

|仓库|主控实际Git核对|检查范围|
|---|---|---|
|IQS|dfb831c|题库/路由/发布/回答/汇总、UI编排、共享引擎、契约、旧CLI|
|StockQA|a37d60c|runner、共享入口、owner adapter、恢复、回答保存及授权|
|StockWiki|1bde9e0|本链相关身份/观察/查询和委托接口，非整仓逐行审计|
|Company Lab|a37af8d|scan profile、runner、checkpoint及生产默认资源|
|Runtime Lab|f58fdb1|原SDK port与资源上限|
|UI Lab|8fc9072|原UI API、页面、比较/名单/结果组件边界|

外仓tracked状态干净。Git受限shell读取被拒后使用已授权外层只读命令核对。三个独立agent分别检查题库、UI、owner/引擎，主控核源汇总。IQS scripts下126个tracked Python文件均可AST解析；这不是功能测试通过。CodeGraph文件清单有滞后，未作为完整现状。

完成10组定向内存反例：委托仅过期、18包/8次额度、UI全局锁、超时冲突、坏历史草稿、跨年指标、新诊断映射、新关键题缺失、三行业旧profile、合法fact旧误检。部分执行源码抽取的纯函数，不是实际数据库/收费E2E。无生产写入、网络请求、临时下载或小时全套测试；没有新增审查回执或准入凭证。

## 影响实际使用的发现

### 1. P1：已付回答零API恢复仍被新派发期限拦住

调用链：`UI补封 → StockQA read_registered → bridge.inspect(current_permissions) → StockWiki inspect_confirmation → _grant`。

- IQS `scripts/dashboard_execution.py:524–526`必须先通过权限检查；`:246–247`实际调用原read_registered。
- StockQA `src/utils/quick_scan_refresh_admission.py:312–328`读取已登记动作仍检查current_permissions。
- StockWiki `stockwiki/quick_scan_refresh_delegation.py:568–576`该模式仍两次调用_grant；`:377–392`独立确认未撤销、主体和binding相同后，又要求now早于原expires_at。
- StockQA `src/utils/quick_scan_owner_research.py:741–742、931、983`读取已付响应、恢复保存句柄、提交原答案还走owner.check，不能只绕过UI一层。

反例保持原主体、workspace、binding及未撤销状态，仅时钟超过expires_at，原函数报`delegation_expired_or_future`。隔夜可能无法封存已收到回答；这证明恢复被阻，不证明原响应丢失。上轮真实恢复在有效期内成功，不覆盖此边界，也不需要重问已交付答案。

最小整改：原owner内部区分新增收费发送与保全同一已付响应。后者仍核当前操作者、明确撤权、原work/attempt/response、主体、完整性和原子提交；不再要求新发送期限有效。不建第二许可证，不删未知请求防重。

### 2. P2：共享默认额度无法完成默认题包规模，却允许开始

Company Lab `src/iqs_company_agent_lab/scan_profile.py:69–90`从实验LIMIT_CAPS复制默认资源；`frozenregistration.py:31–43`默认仅8次模型请求。`scan_profile.py:183–201`生成packs却不核最低请求需求。`runner.py:603–615`达上限后停止；`checkpoint.py:248`恢复原累计counters，`runner.py:55–64`新segment不重置；IQS `shared_company_engine.py:531–532`合理地禁止resume暗改task/limits。

纯函数反例：36个泛化题、同模块、pack2、未传limits，接受并生成18包/cap8；第8次后原_budget_check返回false、budget_exhausted，模拟剩余20题。普通resume不会另获8次。显式足额配置可避免；这是可选共享路径问题，非普通扫描36题无法完成。

最小整改：生产默认与冻结实验参数分开；发送前由实际packs推导最低请求数，与原owner预算判断可完成性。不足提前说明，或在已有授权额度内取足额默认；不取消预算、不清计数续跑。

### 3. P2：全局UI锁覆盖慢I/O，阻塞无关请求

`scripts/dashboard_service.py:427–434`在同一RLock内执行完整_dispatch，包括同步owner子进程及准备/核查。双线程内存反例：coverage等Event，另一GET setup在250ms内不能返回；释放前者才返回。慢查询可延迟其他页面、刷新和暂停操作，不能把请求等待理解为后台模型已停止。

最小整改：锁内取稳定配置/gateway引用，锁外做慢I/O；写入继续用既有CAS、局部锁和owner原子约束。不新增队列或流程框架。

### 4. P2：设置接受的超时值，owner随后拒绝

`scripts/dashboard_service.py:117–118`允许1–600秒；`scripts/dashboard_owner.py:104–106`仅1–180。纯函数300秒配置验证成功，交owner报deployment_invalid，可能保存成功后名单/结果查询失效。

最小整改：统一一处字段规则；若不同操作确需不同超时，明确分字段，不能同名两种规则。保留真实超时和结果未知处理。

### 5. P2：可选历史草稿损坏，使正式结果也返回500

`scripts/dashboard_service.py:403–408`直接读UI仓src/generated/answers.json，`:552–567`在正式owner成功后仍调用它。内存反例：正式owner健康，只令可选草稿为坏JSON，整体HTTP500/internal_error。

最小整改：正式结果保持可读，附属草稿单独unavailable/warning；隔离读取、解析与结构异常。附属展示数据不能成为主结果前置。

## 泛化与演进的缺口

### 6. P2：同一财务指标不能自然保留多期间记录

IQS `scripts/standard_answers.py:92–94`只按metric_id判重；StockQA `src/utils/quick_scan_observation_context.py:567–593`同样限制，`src/providers/base_llm_provider.py:41–44`要求分部改custom ID。共享生产链在IQS `shared_company_engine.py:152`实际调用该校验。

反例：financial.fcf/2024单条通过，追加同主体同币种financial.fcf/2025即duplicate metric id。与此同时`question_prompts.py:134–137`要求逐年列原始输入。模型只能改custom ID、放摘要或删结构化记录，削弱横纵比较；不是完全无法用文字回答。

最小整改：指标观察唯一键含指标、期间、basis、币种及经济范围等实际坐标；保留真正重复行拒绝。统一IQS/StockQA语义，保持旧答案/冻结包可读，不仅删判重或改写历史。

### 7. P2：新增模块的语义仍由固定名单决定

- `scripts/question_manifest.py:38–40`将未知diagnostic framework默认归recovery_watch。schema允许新framework；实际ai_disruption诊断却被映射成困境恢复。应明确通用诊断类别并保留framework，或由模块声明映射；未知不能静默变恢复。
- `scripts/scoring_rubrics.py:25、229–231`仍固定关键构念IQS_12/13/16，rubric题目声明不保存critical。新增关键IQS_25的内存反例：存在但未知→quality=null/critical unresolved；整行缺失→quality8/critical_issues=[]。**这是V02公共聚合器扩展缺陷，未发现当前8766调用，不报成当前UI已误算。** 关键性应随冻结题库声明，旧版保留原含义。

另有P3入口差异：`question_library.py:68–76`固定profile行业≤2、可选诊断≤3；新`routing.py:712–718、895–897`支持full+compatible_business_scope的多行业。三行业直传profile被拒，但原UI新路由有可用通道。明确旧兼容入口或转译到新路由即可，不改签旧profile。

### 8. P2：共享模型能力由品牌名和实验上限决定

- StockQA `src/utils/quick_scan_shared_company.py:143–151`强制输出≤16384，原生搜索只许mimo。
- IQS `shared_company_task.py:412–413`、`shared_company_engine.py:733–734`非MiMo只能单题；Runtime `src/iqs_agent_runtime_lab/port.py:74–89`也固定16k。
- StockQA `src/runners/llm_runner.py:2997–3029`共享入口选单client，未接普通qa_engine.process_questions的顺位fallback。

普通32768配置不能直接切共享；新增同能力端点也得跨仓改源码。不属于公司特例，但不符合可替换模型目标。旧研究12题/固定日期guard已被新company-scan协议绕开，**不误报生产仍限12题**。

最小整改：端点能力、资源上限和顺位路由统一归原StockQA，IQS/引擎只消费能力和原操作接口。不能删除品牌检查就宣称端点接通；沿原预算/attempt防重完成能力验证。

## 解耦与可减负点

### 9. P2：跨仓接线穿透私有对象，并反复核同一原状态

边界穿透：

- IQS `dashboard_prepare.py:196–214`的Python字符串调用StockQA ReadOnlyWorkView._connect，手动BEGIN并赋值_inspection_connection。虽未另造SQL算法，UI已接管owner私有连接生命周期。
- StockQA `quick_scan_shared_company.py:54–73`动态加载IQS/Lab；IQS `shared_company_task.py:245–334、414–424`反向import具体class，读lifecycle的_owner_refresh/_store/_transport_managed/_observation_context/_route_id等。`shared_company_engine.py:698–728`与StockQA `quick_scan_owner_research.py:108–143`又重建同类投影。
- `dashboard_delivery.py:55`拿整个ExecutionGateway并用_select/_call；execution反向延迟import delivery。AST还确认module_registry与routing双向延迟import。环不是目前导入崩溃的证据，但职责交叉需要收敛。

重复动态检查：共享构造在IQS `shared_company_task.py:263、450`、StockQA `quick_scan_owner_research.py:210、337、448`、IQS `shared_company_engine.py:740`多次owner.check；请求时client_for:636和generation_scope:509再进入同链。StockQA `quick_scan_refresh_execution.py:279–309`每次重读配置/全部bundles及inspect权限；`quick_scan_owner_refresh.py:200、238–243、446–451`还起StockWiki子进程。**这是静态调用链，不是性能基准，不报耗时倍率。**

最小整改：原owner提供公开原子work-binding读取和共享任务上下文投影；不变输入入口校验冻结一次，动态状态只在真实发送、登记/写提交边界即时核查。delivery接明确bundle和transport，纯路由校验移小模块。不要另建注入平台、第二状态机或校验凭证；不要跨真实发送边界缓存权限。

### 10. P2：部署默认与旧CLI混有实验假设

- 当前`dashboard_service.py:65–76`回退到runs/c16b/native-owner-alphabet-01，release固定runs/c16b/iqs-release，配置模板也带实验路径。不是Alphabet评分特例，但新安装依赖旧实验。改显式配置或中性新工作区；保留已部署配置，不自动搬库。
- 已跟踪`owner_admission_subject.py:14–22、41–77`固定本机路径、10/18时间、FY2025、巨潮来源，仅ticker取首行并生成verified perimeter payload，且仍有--apply。同ticker跨市场可能选错，其他市场来源不成立。**当前8766没有调用它**，但保留的旧写工具有误用风险。退出产品入口并明确历史用途；通用能力沿原identity/subject接口按实体/证券解析，不用首行和构造来源代替证据。
- `financial_mechanical_check.py:17–18、50`默认Alphabet旧工作区、只认HTTPS，fact有items即判错；正式`standard_answers.py:74–75`要求成功fact有items。合法客户列表反例正式PASS、旧工具fact_contract FAIL。旧one_click.py:33调用它，非当前UI门。退役重复实现或转调正式校验，不改签历史报告。

旧工具与产品模块布局不清。只把非现行入口归入legacy/experiments并保留必要重放，不删除真实结果、不整仓格式化。

## 应保留的设计与未误报项

|模块/机制|结论|
|---|---|
|基础题选择|24核心+7杜邦+5五力，题数/核心分母来自数据；未发现当前UI截24/36。必保杜邦五力是用户需求|
|行业与周期|金融/商业化前替代指标、周期与恢复观察是合理差异，应留模块数据；不强套同一财务公式|
|纯域边界|selection/prompts/module contract/stockqa_adapter多数无模型网络和生产DB依赖，方向正确|
|身份来源|实体/证券/挂牌、有效区间、歧义、原主体和来源绑定应保留，不按名字合并|
|资金恢复|预算原子预留、租约、attempt/send-intent、防未知重发、响应完整性、ACK幂等应保留|
|UI安全|同源/CSRF、禁止任意命令路径、实际路径安全和配置CAS应保留|
|历史门禁|deployment_contract已明确离线兼容，当前dashboard/owner不调用；旧G0–G6/任务回执不再是当前运行前置，不重复报活跃门|
|前端组件|比较/名单导入/结果说明已有API注入边界，保留，不重写UI框架|

## 归入原主线的整改顺序

1. 优先已付恢复时限、共享计划可完成性、跨期间指标语义；沿原恢复/题包/回答测试补直接反例。
2. 同一小池节点修UI锁、可选草稿隔离、超时冲突；用轻量并发/故障注入测试，不重复三市场收费扫描。
3. 原共享fallback接线时收敛能力配置、owner投影和重复检查；新增模块时修诊断/critical元数据；新部署前清理实验默认和旧写入口。不另建平台、不再发一批支线施工包。

产品节点完成后一次集中独审与相关跨仓验证；不要求逐发现凭证。原200家可靠性、事实/消费者与部署目标仍保留，但不作为这些修复的开工门。上述运行缺陷及可局部收敛的边界已按顶部实施；原共享跨模型fallback仍未完。不作废历史已验收行为，不授新资格。
