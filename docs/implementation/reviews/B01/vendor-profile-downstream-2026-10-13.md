# B01 下游兼容接续（2026-10-13，实施中）

本次继续 checkpoint46 的同一隔离候选 `runs/b01-engineering-2026-10-11-01`，未部署。PRIMARY 三包及 FIN 已验收交付不重做。不新增小节点审查门；以下发现合并到 B01 大节点回归。

## 独立只读审查

`b01_downstream_review` 审查现有候选，未写源仓、未联网或操作数据库：

- StockWiki 的 execution qualification、qualification、subject refresh、pool 四个内部消费者仍固定 query 2.0，遇到 Observation 1.2 会明确拒绝。内部选择新 2.6 方言；旧公共 2.0 仍按原 schema 拒绝新版，不静默丢行。
- StockQA execution inspection 将原件版本固定为 1.1；需支持具名 1.2，同时保留完整 SQL 重建、事前登记和物理请求/响应摘要验证。`durable-response-v1` 是正确来源标记，不需改名。
- IQS field assessment 的 `_bound` 直接使用旧 original validator。需显式新方言入口，复用 `_assess(... bound_original=...)`；不得另造资格判断引擎。pool 公共紧凑 wire 无需为内部原件版本升级。

## 实际整链测试

无密钥/禁网络/自有临时 SQLite 与固定 OS CLI，只有供应商 HTTP 回答被明确合成。不是 StockWiki 真实身份 golden，也不证明金融准确性。

- 四次准备运行分别暴露缺原 bundle producer、sandbox 原子硬链接权限、缺旧 CSV fixture、错误合成 citation 形状；原日志保留，均不计产品 RED。
- 原 fixture 精确补入同源 producer 与 `iso10383_sample.csv`（SHA256 `a4f5d6aa9941d91a7867e74cd98f9e83f47f7f12762c95bea3bcaf4dab4fadc4`）；atomic 发布未改，测试显式使用原生权限且仍受隔离 guard 约束。
- `vendor-full-chain-valid-mimo` PID23260，exit1，18.25秒：实际事前注册与回答 checkpoint 成功，封存明确失败 `invalid request_payload_sha256`。原因是同步/异步 client 仅在提供可选 thinking/token 参数时捕获请求 body 摘要。此次默认调用没有摘要，是有效产品 RED。
- 候选修复为所有搜索调用在 POST 前捕获最终 JSON body；不捏造旧回执，不改变历史 Observation 内容。上述三组下游修复仍在同一集中节点实施/验证。

当前软件测试与源仓部署分开。真实首轮 13 HTTP/26原生搜索/CNY1.268162、30题分母、4blocked、0评分/ACK0全部保持；金融、G3/F05/UI/一键及全池门不关闭。

## checkpoint48：候选集中验证结果

原测试准备和失败日志全部保留，未拼成一次全绿。实际结果：

| 批次 | 实际结果 | 范围/限度 |
|---|---|---|
| 新/旧公开整链首次集中 | PID73324：2P/2F | 两旧格式通过；两新格式负例的内部KeyError与测试预期ValueError不符，仍是拒绝，无坏数据入库 |
| 新版完整负例修正 | PID26600：2P | 实体/挂牌，缺PRE事务回滚、错work/hash、四个vendor sidecar字段伪造均拒绝 |
| 冻结profile选择接线 | PID54064：2P | 默认1.2工作捕获请求摘要，旧无绑定调用保持旧receipt外形；没有开启/关闭思考的隐式变更 |
| 客户端/原件封存/inspection | PID25492：244P/1deselected | 原受影响回归；Windows asyncio精确内部socketpair放行，其余网络仍禁。旧schema16不可变SQL仅复制件正常迁移 |
| 默认同步/异步＋真实junction | PID2676：5P | 四个新默认成功/失败回执单元例；junction用核定临时路径的原生mount-point API并清除，未开放任意shell |
| owner下游/qualification/pool | PID72664：72P/1F，PID16820：原失败选择器1P | 一个60k合成codec例缺既定IQS runtime环境，补环境续测；含新版固定CLI字段评估与原库保持控制 |
| pack与逻辑终态 | PID31104：69P/2F，PID65528：原两个fixture选择器2P | 实际部分成功原件/费用保持；旧schema16 fixture需移除新18 trigger，另原子进程显式env |
| v18 ledger/client扩大回归 | PID79188：372P/12F，PID29528：原12＋错误分类1，共13P | 旧schema3/4/6/7 fixture留18 trigger导致形状错；只在mutable legacy fixture移除，未放宽native schema验证 |
| 最终terminal/engine | PID25224：35P | 写锁等待期间过期会拒绝；真实lifecycle只结束明确解析失败，generic storage/lease问题仍恢复 |
| 实际partial最终状态 | PID35336：2P | 一物理请求：有效题result_ready，缺题failed，原费用/receipt不变，重新运行零发送；无authority的测试封存阻断/日志诊断不当完整成功 |
| CNY显式新方言 | PID58588 RED2F/4P；PID10428 GREEN49P | 原refresh-v1字节不变，只new1.1接受真实CNY及query2.6，拒未知币种/混旧wire |
| CNY公开preview→consent→admission/replay | PID61124：1P，100.46秒 | 合成consent，真实临时native库/OS CLI，API0，零attempt/预算预留，重复无新work；USD文件替换拒绝并恢复原字节 |
| 实际公开main→owner ACK→native执行核验→assessment | PID63468：1P/35deselected，177.41秒 | Observation1.2，原main恢复/引用无重封无新请求，撤owner许可拒绝；只execution_verified，screening/金融准确性false |

CNY公开链另实际复现了Q13 admission借用原store但缺schema17起的thread-local事务上下文（PID74768，exit1），候选只初始化该内存状态，不调用创建/迁移initializer。后续一次fixture路径超长错误（PID62012）保留；runner改成固定长度唯一短临时根，PID61124才作有效正例。

新逻辑终态用原failed状态和原work_event。schema18只为该事件表加禁止UPDATE/DELETE两个trigger，17先严格校验后迁移，不改旧数据；当前仅隔离副本。最新attempt/当前lease/原耐久response及model resolution核对，pack额外核membership/receipt/非uncertain和settled/completed费用。checkpoint/delivery、过期/旧epoch/发送不明或未结算均拒绝。没有把旧真实26条leased自动改成failed，也没有拿absence-of-answer判定崩溃请求无效。

一次大节点独立审查发现的无PRE旧兼容分支、明确member错误reason丢失、锁前now三项已分别直接修复并加入真实负例；不增加helper验收门。

部署仍未完成：同候选需最新源writer/HEAD/逐文件SHA核对、精确应用与源级接线验证。真实旧expired工作仍需原owner对账/重试决议，不自动恢复或换代。真实金融/G3/F05/生产门、原13HTTP/26搜索/CNY1.268162/0评分/ACK0保持。

## 2026-10-13 checkpoint49 — B01源码交付与正常本地提交

此前checkpoint47/48的“未源部署”是历史。本节点68个精确文件已部署：IQS20、StockQA32（含新schema的精确Git忽略例外）、StockWiki16。部署前逐文件及HEAD核对无目标并发漂移；原文件备份和实际交付SHA留在本机，当前68目标再次匹配。其他进程的2026-10-10 README不覆盖、不提交；生产数据库、名单、旧实验账本均未修改。

StockQA正常本地提交`21b2c5f9caa4db8adafb7bc74d69ce75aed4c9fe`；首次正常hook修正四个文件的混合换行而拒绝提交，保留日志后只重暂存同32文件，第二次black/isort/mypy/secret及其它正常hooks全通过。StockWiki正常本地提交`5b11f55909efdbd724fb07e1e7f298631c4200cb`，正常静态hook通过。独立源静态检查QA PID76912/exit0、SW PID34484/exit0；均未跳过检查。换行只改变raw bytes，原schema canonical SHA一致，候选镜像和交付摘要已同步，不把canonical相同声称为raw相同。

公开协议：Observation1.2/profile vendor-http-identity-v1；事前主体request1.2/binding1.1；query2.6/capabilities1.2；refresh显式1.1接受CNY、旧1.0继续USD；work store18。新旧整链、逻辑terminal、原件恢复与CNY admission的集中测试见[本节点报告](docs/implementation/reviews/B01/vendor-profile-downstream-2026-10-13.md)。同节点独审发现的缺PRE、typed reason、锁前clock已直接修复；最后源只读复核未发现这三处遗漏，不新增小审查门。

下一动作：只读核对原真实owner/work账本和当前公开恢复路径，保留13物理HTTP、26原生搜索、已settled CNY1.268162、30题分母、4旧blocked/26旧expired、0评分/ACK0。schema18升级需原账本备份及原生迁移；无答案的旧expired不能用新terminal强改，不补造事前记录或header ID。由原owner生成当前显式1.1 CNY quote/新的批准与admission后，才对固定IQS_01/02/04做pack3/32768→pack1真实小实验；旧approval不扩大、不重放one-shot控制器。

软件接线完成不等于答案准确：本轮API/付费搜索0，金融gold0，Financial/G3/F05/生产UI/一键/全池仍开放。PRIMARY/FIN已交付不重做。源码与本批公文只正常本地提交，尚未推远端；此前自动审批导出范围pending保持，私有日志/数据/golden/密钥不随公文发布。

## 2026-10-13 checkpoint50 — 源码提交终态、真实旧账本备份迁移及owner恢复候选

checkpoint49源码交付已完成正常本地提交：IQS `29f49d3ff59974ecbe25ec9e7e7438a774cb1a63`、StockQA `21b2c5f9caa4db8adafb7bc74d69ce75aed4c9fe`、StockWiki `5b11f55909efdbd724fb07e1e7f298631c4200cb`。远端未推；不重做68文件部署或已签收PRIMARY/FIN。

真实实验原work.sqlite先只读核实，schema17、30个work/attempt、4 checkpoint、26 leased（已到期）、13 physical budget全settled/completed，原SHA60d4446d…。在自有实验目录做完整SQLite backup后，用已部署原生QuickScanWorkStore升级18，只添两个work_event不可变trigger；所有原表逐行摘要/计数完全保持，完整性及外键检查通过。原schema17备份SHA f3e6101f…，迁后236e5aa4…；没有改状态、答案、费用、旧context/PRE或补造header ID，也没有HTTP。备份与原件仅留本机，不上传数据库。

同节点只读审查未部署work-decision旧草稿，不能整树复用：草稿18与已交付18同号异构；旧native-currency profile不等于当前refresh1.1；当前PRE1.2不含回答后的payloadSHA；首次apply过期确认漏洞；comparison限制合法checkpoint导致旧26不可实验；retry时间/controls尚无planner/admission/runner消费。对无accepted answer只能作owner中性结案，不以诊断hash自证具体parser错误。全部纳入同一原B01实施，不新开小审查门。

仅自有runs/b01-engineering-2026-10-11-01候选复用原journal，显式schema19保留原18；未部署源、未迁真实账本19、未结束真实旧26。候选resolve取锁后clock，双读owner权限后以真实commit clock持久化，倒退拒绝；物理receipt/attempt/pack/预算保持，已有checkpoint拒绝resolve。独立comparison可接已授权failed-resolution，不伪造旧score/checkpoint或要求先伪造旧投递；只保存独立意图，尚未创造新work/HTTP。扩展projection显式include_owner_decisions=True，旧默认shape保持；新旧只读quote不偷偷迁18。

TDD与续测保留原分母：PID60796原目标RED1F（缺resolve方法）；移植脚本两次重复锚点断言零store写，先跑批次PID45108仍34F，不算已实现后的产品回归。真正当前移植后PID66732 31P/3F（漏显式投影）；直接修后PID62972 34P/5deselected。其余五项适配当前真实1.1/schema18→19及guard：PID56168 4P/1F，发现SQLite C层绕原open hook在runs创建空foreign.sqlite；已按实际创建时刻/绝对路径/0bytes确认仅该自有文件并删除，加sqlite3.connect有界审计后PID10648 1P。新commit-clock/旧默认shape/币种/迁移联合PID50592 9P/35deselected，含5项新控制和原4项，不相加冒充一次全绿或金融准确率。子进程无key、外部网络拒绝，原日志/PID/SHA保留。

下一步唯一动作：继续同一候选将真实owner预览/TTY确认/首次fresh-registration与既有精确决议重放接通当前refresh1.1/query2.6，随后将已授权retry/comparison引用、冷却时间、目标generation及固定controls贯通原planner→preview→admission→runner。需要扩展wire时用显式新版本，不暗改旧1.0/1.1。完成整个owner控制节点再一次集中原生CLI/SQLite/TDD与既有同节点独审、核源差异后交付；不要用FixtureAuthority处理真实26、重放旧one-shot、放宽旧批准或把4旧blocked补成新结果。之后才IQS_01/02/04 pack3/32768→pack1收费实验。

本轮金融gold0、已接受评分0/ACK0，原13HTTP/26搜索/CNY1.268162/30题分母保持；工程完成不授Financial/G3/F05/生产UI/一键/全池。私有候选、备份、日志和真实材料不随公文发布。

隔离清理已在实际CIM自有Python0后核绝对路径/reparse/硬链接闭合和逐文件SHA；删除自有temp 4176文件/3012目录，剩余0。保留候选/冻结输入/原日志/交付备份与真实实验；没有删除源仓或其他进程文件。旧长路径第一次清理在只读枚举阶段退出，改原生扩展路径后才执行。

## 2026-10-13 checkpoint51 — owner控制公开CLI候选贯通，重试调度仍待接线

沿同一B01候选，不重做已交付68源码、原17→18迁移或PRIMARY/FIN。新work决议19仍只在自有候选，源QA仍18；真实旧26/4和13HTTP/26搜索/CNY1.268162/30题分母/0评分/ACK0不变。

复用九个旧草稿接口/测试后，移除未发布native-currency profile，用当前显式refresh1.0/1.1及query2.0/2.6 schema。owner控制仍独立于付费dispatch；公开原refresh CLI新增work-decision三个入口，保持旧入口。首次apply必须fresh-registration；只有实际19 SQL内完全相同的不可变request+grant可过期后读取current-permissions，用户JSON不能自报重放；两次读取变化拒绝。PRE1.2由真正owner contract核profile，不编造其不存在的payloadSHA；真实请求摘要仍由QA原pack/receipt核。

候选集中接口/owner/readonly/apply测试PID24296 exit0/61P/22.79秒。原PID16788 30P/1F是旧合成fixture漏当前protocol；补fixture后PID24944 30P/1F为sandbox原子硬链接权限，不放宽发布，续原权限完成61P。新增PID63700 4P/3.60秒验证精确SQL才能重放、首次过期不授予grant、当前撤权仍拒绝、1.2不造PRE字段；全部合成数据，不当真实issuer/金融gold。

完整native临时库＋真实公开CLI整链：PID14316先在fixture未知return键request失败；只改读取原持久refresh Request。PID58160实际owner1.2预览因入口漏configured release_root失败，这是产品集成RED。复用旧CLI并传原配置release_root后，PID64712 exit0/1P/135.68秒：真实before-send原件/冻结pack/已settled合成响应→公开owner预览→明确fixture-only同意→QA公开apply/精确重放，原physical/receipt/budget/PRE全部保持、一个逻辑work failed、决议仅一行、无checkpoint或HTTP。软件E2E不证明真实人确认或金融准确性，测试SQL过期仅作用于合成tmp。

真实数据边界实验：原真实ledger18副本的IQS_01，通过现有LLMConfig.get_quick_scan_model_policy规范化后，policy snapshot SHA与原账本完全匹配；公开inspect CLI实际exit0/API0/DBwrites0，识别原length/completed物理终态且原库/副本未变。原配置models不是规范化routes，直接送原配置第一次拒invalid policy_version；错误猜嵌套policy断言零写，使用原配置器解决，不手编policy_version或价格。相对路径as_uri准备错误原日志保留。

复制五个真实轻量owner SQLite及原release到自有根，原五库SHA保护、不复制公司文档。clone新增仅原试点公司一个隔离测试成员及新owner配置，不修改原名单。真实旧PRE在纯原validator通过，且复制owner行完全匹配；公开owner却明确拒绝新路径store_id，因为当前QuickScanObservationStore以数据库绝对路径派生namespace。该负例是正确隔离：同公司/同DB字节不能冒充原owner namespace，不能改旧receipt、替换store_id或伪造正例。真实控制正式执行应使用原已配置owner namespace；隔离clone只作负例与原件读取。

当前唯一下一步：候选中的retry/comparison意图还没有接进planner/preview/admission/runner。继续同一节点用显式新wire绑定真实决议引用、cooldown、目标generation、comparison cohort及pack/thinking/max_output_tokens；无可用旧答案也可独立比较，但不变成scored baseline、不需要伪造旧投递；旧1.0/1.1和原审批范围保持。整个节点集中验收/核最新源writer差异后才交付19并在原owner namespace合法处理真实旧任务、批准新实验；不自动重放旧控制器或以FixtureAuthority处理原26。

本阶段新接口/同意/价格/公司事实均未金融签收，F05/G3/生产UI/一键/全池继续开放。主线候选、真实副本和原日志只本机留档，公文只本地提交、远端未推。checkpoint50的清理统计是当时终态；本次又产生临时整链库，待此节点结束再精准清理，不假称当前temp仍空。

checkpoint51本轮终态补记：实际CIM自有Python0后，核绝对路径/reparse/硬链接闭合及SHA，精准清理新生成temp594文件/578目录（67,777,862 bytes），temp剩余0；保留候选、原日志、必要真实只读副本及备份作为接续输入。原五owner库、真实work18和他人2026-10-10 README当前SHA再次全部保持。无新HTTP/搜索或生产名单修改。本批6份PWF/报告正常本地提交，实际commit以Git为准；19仍未源交付，下一步仍是retry/comparison调度控制接线，不将源18与候选19混淆。
