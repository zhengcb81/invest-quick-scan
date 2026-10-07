# MiMo Pro 小实验：本批集中技术审查

日期：2026-10-07。审查者：独立只读 agent `identity_wire_review`。

**状态：初步代码审查，待修订及完整执行证据复核。** 接收任务时主 matrix 正在运行，JSON-off 仅 prepare；不能把本报告当实验完成、模型优劣结论或 G3/F05 签收。后续只在同一批补证据，不增加 helper 审查门。

## 审查范围

读取 `mimo_pro_pilot.py`、`mimo_json_mode_probe.py`、本轮 `batching_benchmark.py` diff、六项新增离线测试、预注册文档，以及共用报告/归档和题目选择路径。CodeGraph context 已用于定位账本/缓存；从明确冻结 commit 只读检查 StockQA `LLMClient.send_request()` 的 transport 语义。

没有执行测试或实验，没有联网/读取 key、修改外仓或 Phase92、操作运行根/清理、修改旧归档。唯一写入为本报告。以下反例为源码控制流推导，未另发请求或跑探针。

## 已确认的正确边界

- 主矩阵为 `3公司 × 3模型 × (10逐题 + 2五题包 + 1十题包)=117` 请求；十题包独立重复为 9；Pro thinking 两个五题包/公司为 6，合计 132。JSON-off 为两个模型 × 三公司 × 两包，共 12，须独立标注为观察初步失败后新增的 adaptive 诊断。
- 主臂同一个冻结十题集合、同证据和 SYSTEM v5；Pro thinking 去掉 temperature、增加 output cap、开启 thinking，因此单列。JSON-off 用 alias route 保持 endpoint/model/价格/其他生成参数，只省略 `response_format`，方向正确。
- JSON-off 的冷调用没有使用 warm cache；其参数变化产生不同 cache key，不会用 JSON-on 的结果填充。主 repeat 同样再次真实请求，不是用应用缓存伪造独立重复。
- 正常解析严格检查题号完整/唯一/顺序、unknown/N/A 的 null 分数、引用存在；未知不填 5。完整末项投影和整段 JSON fence 只是既有 parser v4 的可记录归一化，不增补答案；结构有效率须与原始严格格式率分列。
- StockQA 固定源码 commit 为 `6a9ff13864ebb160d5c4ab3cf2f42155d9f4aa99`，运行时仅精确白名单导出。题面/锚点取该 commit 的 `questions_rendered.json`，选定 QIDS 后保持原值，不走本轮生产模块路由或重新生成题库。
- 固定 `LLMClient.send_request()` 一次 session.post；runtime 关闭 pooled adapter 自动重试；observer 禁止重定向、每实际 HTTP 先 durable reserve。异常/未知保留预算上界，接续不盲发。
- 主 pilot freeze 核对问题/身份/证据/源码/参数；主块 marker 有 fingerprint，应用 warm 拒绝读 key 并核 ledger hash。根内 TEMP 和受控 Python guard 的定位合理；这不是通用 OS 沙箱。

## 实质发现

### MP-01 / P1：JSON-off 记录父锁但未执行配对校验

初审 `mimo_json_mode_probe.py:29–44` 复制父输入并记录 parent lock/source hashes；`run` 与 `warm` 路径并未将自己的 questions、companies、evidence、源码或执行参数与该记录核对。`target.exists()` 也直接跳过，不核 binding。

固定反例：prepare 后只改 JSON-off 的一个 snippet、锚点或 question 顺序；原 manifest 仍写“唯一变化省略 response_format”，run 仍能加载修改后的输入发请求。StockQA runtime hash 检查只能保护 transport 源码，不能保护这些对照输入。这会使协议诊断失去配对基础。

诊断首发前应冻结并核对自己精确输入/代码/生成参数，核对与父冻结内容的相关子集一致；父 budget 与 child budget 等有意不同项明确单列。漂移须 0 key/0 HTTP，warm 和已有 block 也校验 binding。不要通过修改已冻结主 context 来修诊断。

### MP-02 / P2：新增模型破坏旧归档重算的 route 集合兼容

本轮新增 `mimo_pro` 到全局 `b.ROUTES`；共用 `summarize_archive()` 仍以历史 `model-input-lock-v5.routes_sha256` 和**当前全部** ROUTES 比较。原三模型归档与现在四模型映射必定不同，即使原模型、价格、答案完全没有变，也会 `historical_pricing_route_drift`。

即便去掉该检查，`summarize()` 的 by_model 遍历当前所有 route，增加一个零请求模型后仍会与旧归档 analysis 的三键字典不同。JSON-off 进程还会注册两个 alias，使同一问题扩大。

应从历史冻结 route/价格集合重算并严格校验其原有定义，新增未使用 route 不应阻断旧归档可读；缺少可验证历史映射时明确兼容边界。不能改旧归档/hashes，也不能简单跳过原价漂移检查。主矩阵结束后集中修订共享报告源码，避免热改正在执行的冻结源。

### MP-03 / P2：pilot 新归档内容未纳入最终 hash 清单，锁提前释放

初审 `mimo_pro_pilot.py:237–245` 先释放 orchestrator.lock，再调用共用 archive；共用函数已经生成 retained_files/archive-manifest，wrapper 后来才追加 pilot-input-lock、pilot-registration 和 source/。追加文件没有入该最终清单，返回文件计数也仅为追加前计数。

同时，归档期间没有持有本轮运行锁，另一个合法 CLI 可取得锁继续写 results/ledger，使 snapshot 移动。只是检查锁不存在不能形成归档独占。

最后归档应在本次独占持有期间完成一致 snapshot，或具备明确的不可运行终态封锁；全部追加文件完成后生成最终递归 hash 索引并校验，保留原归档规则对旧格式的兼容。不要为了本次运行追补修改旧 archive。

### MP-04 / P2：检索 provenance 属性承诺与实际数据结构不一致

预注册承诺保留 document family 和自述属性；实际 generic `targeted_search()` 只创建 source_id/url/title/snippet/published_at/retrieved_at，只有旧 scoped 特例另加 `document_family`/`source_scope`，本 pilot 没调用它。retrieval 描述还固定为“six precise Chinese intents”，本轮实际为四个意图，含 Alphabet 英文。

URL 不同窗口已有独立 fragment ID，引用绑定正确；但不能因此把同报告多个窗口视为独立证据。可以在独立事实支持审查中记录 URL family/发行人自述/第三方属性作为**后附审查注释**，明确其发生在答案后，不回写冻结 context、伪称模型原来已收到这些标签。最终文档应如实注明当前模型输入的字段。

## 预算和证明范围待确认

主登记为 cap160模型/24搜索/USD5，诊断另账本 cap12/USD1。固定计划 132+12=144 仍在模型请求计划上限内；现金保守上界却没有两账本联动，可到 USD6。若 USD5 是整个小实验上限，诊断首发前应从父终态快照核剩余额度；若已明确追加授权，须登记扩展并报告两账本合计。不能只展示主 ledger 成本。

主 warm 当前直接证明 ledger 不变和 credential 读取被拒；JSON-off warm 仅打印 0HTTP/0key，没有持久化对照 proof 或 ledger/output hash 前后断言。实际调用的 cache-hit 分支是纯读取，但最终报告如要写“账本和输出 hash 不变”，需由本批 warm 证据支持，不能仅引用该打印句。

“不同模型”比较须对实际 receipt 的 actual_model、requested model、缺失 usage 和 finish_reason 分开检查；不能凭 route 标签宣称服务端模型已验证。费用只是定价快照参考，provider cache token 有缺失/不同历史，不能当套餐实扣或完全控制的冷缓存实验。

## 离线测试与后续集中证据

本轮六测试覆盖 Pro 价格计算、请求数、主 source/evidence lock、搜索接续、完成 block 接续、thinking/cache 参数分离。FakeClient 不经过实际 HTTP reserve/settlement；旧 B01 测试可提供通用账本补充，不能因此说六新测试已验证真实调用。新增 diag 配对漂移、旧三模型归档、完整归档索引/独占、合并预算与 warm proof 的少量定向反例，放在同一实施批和集中复核即可。

等待主线提供完整主/repeat/thinking/diagnostic结果及 warm/归档/清理后，本报告再核：计划与实际调用总数、所有失败/未知是否保留、实际模型/usage、相同问题/证据配对、无补问与重放、原始/归一化结构率、引用支持审查、总耗时和参考费用、所有文件 hash及精确根清理。现在没有这些终态证据，不作最终通过结论。

## 初审原字节快照

| 文件 | SHA256 |
|---|---|
| `scripts/mimo_pro_pilot.py` | `d3ce4cdf5f63659697eb9aed51df1d83e0ecea744500d24c77b053465f2fbc65` |
| `scripts/mimo_json_mode_probe.py` | `6dfa52a017c8e29bc6cb49dae3d398b1e3f902fbfc791cec37bb205c46e614bc` |
| `scripts/batching_benchmark.py` | `4162755fc16a4bad926e5c9719a2e4bd402ad054285005456dd259a6e023fc7b` |
| `tests/test_mimo_pro_pilot.py` | `fdb46e446c443706851698302831166656ca7a44169b060f19a05ed29647a2e5` |
| 预注册文档 | `ee071be96fd8cfdc92db08a5b3faabaea043878740eae755b1c91ee283d5bace` |

这是开始审查时的源码快照；修订和终态证据须另列 hash，不能覆盖或冒充最初执行版本。

---

## 同批执行结束后的追加复核（归档/清理仍待第二份证据）

主线扩展为四模型思考开关对照：新增 `mimo_pilot_extension.py`，JSON-off 原入口作为兼容 wrapper。已结束收费阶段为主 132、thinking extension 42、JSON-off 12，共 **186 模型 HTTP / 24 搜索 HTTP / 0 未知发送**。统一新登记 cap 为 200 模型 / 24 搜索 / USD8。没有为本审查重发请求。

本段只使用标准库读取 JSON、AST、计算 SHA 与算术，未调用实验模块/公开 CLI/测试/API，未读 key，未修改源、外仓或 Phase92。首次只读检查脚本有一次本地默认编码读取错误，改为显式 UTF-8 后继续；该错误没有修改工件、执行应用或发请求。

### 初审 MP-04 更正：撤销“模型输入缺 family/scope”结论

初审漏看实际一次性输入选择脚本 `docs/implementation/experiments/mimo-pro-input-selection-2026-10-07.py`，仅凭通用检索 helper 推断最终模型输入，结论有误。保留上文作为审查历史，在此明确更正。

`pilot-selection.json` 时间为 `19:19:23.774395Z`；最早 model reserve 为 `19:19:33.101980Z`。选择脚本拒绝任何已有模型请求/未知发送，注入 family/source_scope 后再 freeze。最终 CATL/CNCB/Alphabet 分别 23/15/15 条，全部 53 条都包含两属性，三池文件 hash 与 selection 记录及主锁一致；selection source SHA 为 `ba612f0dcdc7ee41f5ed9f6f2e5d856a8fc6703c1a2aceeb6af245f5ad28a57c`，与实际脚本一致。这是首模型前输入，不是答案后注释。

### 已落实的修订与兼容边界

- **MP-01**：新 extension 锁包括问题/身份/证据/transport runtime/预算/注册/代码和父原执行源；另核父 ledger 终态 SHA、父冻结 input fingerprint 和 child-copy 原 SHA，已有 block 核 fingerprint，执行前重复 verify。实物主锁 12/12、两个 child 锁各 29/29 一致；child-copy 各 6/6，thinking 父 ledger 1/1、JSON-off 父 ledger 2/2 一致。JSON-off 旧 adaptive prepare 记录以 `initial-adaptive-registration.json` 保留，不冒充最初预注册。
- **MP-02**：报告按历史 route snapshot 计算；无 snapshot 的旧版本仅接受明确 legacy route 集合及其匹配 SHA。真实旧三模型归档公开重算回归已 GREEN，测试核前后原件 hash 未变；不是放宽任意历史价格漂移。
- **MP-03**：共用 archive 现在接收 caller 当前 PID 且核已持锁，或自行 O_EXCL 获取；复制 source/parent-source 和注册后才生成 retained_files。定向回归核索引与实际文件集合一致、错误 owner 拒绝且 caller 锁保留。此为代码/离线日志支持；本轮真实新归档及清理尚未完成，等待主线第二份证据再核。
- 合并预算按不可变父账本扣余额：thinking 预算由 `8−1.889780=6.110220` 得到；JSON-off 由 `8−2.704924=5.295076` 得到，独立模型 cap42/12、搜索 cap0。父余额没有因未知/失败返还，本次未知为0；合并实际上界 **USD2.877381**。这解决了初审两个子上限互不扣减的问题；该值是保守账本上界，不能当控制台实际扣款。

离线日志支持本批新增/升级测试 **8 pilot + 7 extension = 15 GREEN**，以及旧受影响 B01 **28 GREEN**。独审只读取源码和已有日志，没有再跑一次。新增测试涵盖重签 child 仍须匹配父输入、父 ledger 漂移、源码/预算/输入漂移、真实旧归档、锁与最终索引、DeepSeek 单 token-limit、reasoning body 不持久化及混入正文拒绝。

### 实际执行/输出账本核对

| 执行根 | model/search | 有效 chunk / 无效 chunk | 有效回答 / 原始严格回答 | scored / insufficient | warm |
|---|---|---|---|---|---|
| 主实验 | 132/24 | 107/25 | 266/266 | 160/106 | 107，0HTTP/0key，ledger SHA 一致 |
| 四模型 thinking 扩展 | 42/0 | 23/19 | 115/100 | 74/41 | 23，0HTTP/0key，ledger 与 result hash 不变 |
| JSON-off | 12/0 | 3/9 | 15/5 | 10/5 | 3，0HTTP/0key，ledger 与 result hash 不变 |
| 合计 | 186/24 | 133/53 | 396/371 | 244/152 | 只对有效缓存项证明，未把失败项称缓存成功 |

每个 model attempt 都有唯一 result；block chunk 链接分别 132/42/12，全部存在且没有同一结果重复计入不同 block。53 个失败 chunk 均保留 `invalid_answer` 和错误，未用补问或别的模型拼齐。所有186次实际模型字段与 requested model一致；usage 输入/输出计数全部存在。主和 JSON-off finish_reason 全 stop；thinking 扩展为41 stop/1 length，该 length 并未有效化。25个非原始严格回答来自5个整段 JSON fence 归一化 chunk，不能合并到原始格式有效率。

四模型 on 的 usage 都返回 reasoning_tokens：MiMo Flash 8408、Pro 16105、DeepSeek 37997、MiniMax 2133；Pro on 复用原主6请求，未另算新增调用。off 有缺少 reasoning_tokens 字段的返回，不能说“缺失=已证明零思考”，只能记录接口声明 off 和字段缺失。业务只解析 `message.content`，receipt 仅保存 usage 数字；混合正文负例与 separate reasoning canary 的测试支持不持久化隐藏推理。

事实支持审查尚在其他分区进行，396 个结构有效回答和244个评分回答不是世界事实正确率。JSON-off 仅15/60题有效，独立重复仍有格式差异；不能据一次局部结果宣布全面最优。模型 token 费用参考合计为 USD0.392538（冻结峰值/未折扣参考，不含把套餐实扣反推为token价格）；真实外部搜索成本也不得与参考模型费用混称一张实际账单。

### MP-05 / P1：真实 wire 温度与省略声明不符，归档回放尚阻断

本次独立从冻结输入和账本参数重建186个 request body。仅138个按账本 `parameters` 重建时与 `request_body_sha256` 一致；失败恰为**原 Pro thinking6 + thinking 扩展42**，共48个。

根因：冻结 StockQA `send_request()` 初始 payload 总有 `temperature=TEMPERATURE`；固定 settings 的值为0.7。实验 `call_chunk()` 从 observer.params pop temperature，但 observer 从初始 payload 复制后只 `update(params)`，没有删除原 payload 的 temperature。因此这48次实际发送仍有 **temperature0.7**，账本的 intended parameters 没记录它，“不传temperature”声明不成立。

按真实 transport 的已知默认合并方式重建（初始 temperature0.7，再以账本参数覆盖），**186/186** request_body SHA 精确匹配；不是尝试任意值凑 hash。138次其他请求明确覆盖 temperature0，因此不受该温度偏差影响。原账本、参数、hash、包和收费记录不能回写成新语义。

这48次 thinking 开关的同模型等 cap 比较仍有相同的实际温度0.7，可以保留并如实限定；它们不能称“未传temperature”，也不能与主 temperature0 臂说只变化思考。服务端是否忽略思考态温度不由本次返回反推。缓存 key 也仅记录 intended params；未来修真正省略须升级 wire/cache 协议，避免旧 temperature0.7 值与新省略值共用 key。

已立即通知主线暂缓真实归档。当前 `replay_inputs()` 按 intended params 重建 body，会对48次报 `actual_payload_binding_mismatch`，不能靠跳过 hash、改 ledger 或收费重跑解决。需要有冻结 transport/settings 字节证据的历史 wire 回放、显式协议偏差记录和未来发送边界修复；随后在同一批核归档/清理。MP-05 解决前，本段不签技术终态通过。

### 此次追加证据的关键 SHA（MP-05 修订前快照）

| 文件 | SHA256 |
|---|---|
| 新 `mimo_pilot_extension.py` | `4536567e20674ddfbabd44831e23890eac26989b320efee61806a86aa41c0ffe` |
| JSON-off wrapper | `c2d0db865d061b02454ee8ab6a1cd09c32e36cec99a79e578fe73ab737321e66` |
| 共用 benchmark | `788823f6bc3a2102b4ac744f3e05268020cbb72cdcb13324f79961c41fc9f159` |
| 共用 report | `d907253b97de65194bdf35ceb63194aecd28ca65a144747101bae6212c2585fb` |
| 共用 archive | `ba67cfc1b58565961c228e6668053525e4d38798dd68c8ba007fca11d4e5333e` |
| 主 ledger | `1a4fa699de2b8d59d64b5467c9f6657a21e2e028cf6233edd72a54eae27f6b14` |
| thinking ledger | `4cecd6845ccc0d2bc7e9a63fc54c1e4a59652e0240d514c77f6de7ab293d22b8` |
| JSON-off ledger | `28337432a368b77018b4c88949085d17c938ea8dce25c2778d3f8f8f604fe004` |
| 7 extension 测试日志 | `6b08d629bcbec2da2ab44961d524215d071c50680f57ebb2d8ec1102e708bdc0` |
| 28 B01 回归日志 | `c2462f197abcbff09fafd856ae9e036fb0e4dddf4c6d6da84befaea647870410` |
| 8 pilot 测试日志 | `7071d40a2d9a9c3c69efb60e8575a7ed6947f38fcb90f8cc8430dd6a2341e9d6` |

初审原文/初审 SHA 保持，以上作为追加状态；后续 MP-05 修订、实际归档和清理必须另列最终 SHA。

---

## 同批终态签收：MP-05 修订、真实归档与清理

**结论：本轮实验的技术执行记录、最小归档和精确清理范围通过；未发现剩余归档阻断。** 初审和上次追加原文、原 hash 保留，本段替代其“尚待归档/清理”和 MP-05“尚阻断”的当前状态。此结论不签收 G3/F05、Phase92、跨仓产品接口或生产默认策略，不把实验结构通过率或两位 agent 的来源复核当人类事实/评分 gold。

本次只读源码、JSON、既有日志，以标准库核 hash、集合、事件、统计与文件存在性；没有导入应用执行路径，没有跑测试/公开 CLI/API，没有读 key、操作清理或写外仓。现有日志的测试/公开 CLI 成功来自主线执行，不冒充独审重跑。唯一写入仍为本报告，没有新增审查门。

### MP-05 已消除归档阻断，并保留真实偏差

未来 observer 明确只继承 `model/messages`，按声明构造生成参数，拒绝 endpoint/model 漂移；账本和应用缓存共同使用 `explicit_only/2`。这样固定 StockQA 的默认 `temperature=0.7` 不会再进入“省略温度”的新 body。warm miss 在读取 key/初始化 client 前抛出 `warm_cache_miss_zero_send`，已归档 run_id 的 prepare 在导出源码/创建新执行内容前拒绝。定向测试含实际 observer 接收到默认0.7和另一 token-limit 的 canary，断言实际代理 payload 只保留 model/messages 与声明参数；不是只检查声明字典。

历史归档回放先尝试 intended parameters，只有旧策略、未声明 temperature 且 hash 不匹配时，才从本次冻结 transport/settings 源码重建默认；runtime commit、十文件白名单与每文件 hash 必须一致，AST 必须找到唯一数值 TEMPERATURE 及 `send_request()` 对它的实际使用。随后仍要求 body/prompt/evidence/questions hash 精确匹配，不接受任意数值试配，也不跳过冲突。原186次收费请求、账本事件、参数、答案和运行源未改或重发。三归档分别132/42/12次精确匹配，其中6/42/0次记录继承0.7；它们是可验证 canonical JSON body provenance，不能称原始网络包。

修订只经过离线验证，**没有 live 验证未来 `explicit_only/2` 的 provider 行为**。结果文档已披露48次实际0.7、与主温度0矩阵的比较限制、服务端思考采样可能覆盖/忽略参数，以及读取 timeout 不是严格 wall deadline。不能据内部 hash 一致推断服务端采样完全受控。

### 归档实物、历史事件与公共读取

| 最小归档 | retained 文件 / 连 manifest 总文件 | model provenance | 继承默认温度 | 索引核验 |
|---|---:|---:|---:|---|
| `mimo-pro-pilot-2026-10-07-01` | 15 / 16 | 132/132 | 6 | 原字节 SHA 与精确文件集合一致 |
| `mimo-pro-pilot-2026-10-07-thinking-all` | 18 / 19 | 42/42 | 42 | 原字节 SHA 与精确文件集合一致 |
| `mimo-pro-pilot-2026-10-07-jsonoff` | 18 / 19 | 12/12 | 0 | 原字节 SHA 与精确文件集合一致 |

合计 **51/51 retained 文件**核验，无未索引新增或缺失文件；另有3份 manifest。原主执行源码、child 执行源码和 parent-source、输入锁/注册/route snapshot/附加 metadata 均已入最终索引；归档源码 hash 与原执行登记一致。这里的最终当前源码 SHA 不冒充被冻结执行源的 SHA。

归档 `ledger.jsonl` 统一紧凑 JSON 序列化，与原运行账本**不是相同原字节文件**。独审按原运行写入的默认 JSON 空格及换行方式在内存中重新编码归档事件，三个结果均精确还原此前记录的原运行账本 SHA；因此本批能核对事件内容和顺序未变，而不是要求两文件直接同 hash。

| 账本 | 原运行字节 SHA256 | 最小归档字节 SHA256 |
|---|---|---|
| 主实验 | `1a4fa699de2b8d59d64b5467c9f6657a21e2e028cf6233edd72a54eae27f6b14` | `b071099b22236006be9119704002697d4bb8975de0113ff2a19caac2817fd85f` |
| thinking | `4cecd6845ccc0d2bc7e9a63fc54c1e4a59652e0240d514c77f6de7ab293d22b8` | `7e89fe222ea81ba1b2c333cc8f810c5d6efd09da1c028730a9dfdfe4b4fd13af` |
| JSON-off | `28337432a368b77018b4c88949085d17c938ea8dce25c2778d3f8f8f604fe004` | `6898d15cb47af52d87f71f62ec27c5749efacc38ec715fb281cdec3f2d584322` |

三个既有公共报告日志都含 `archive_statistics_verified=true`；主线记录其 exit0。公开预算重算分别132/24、42/0、12/0，未知均0，保守上界合计USD2.877381。最终日志为 **17新离线 + 28旧受影响B01 = 45独立用例 GREEN**，不把中途重复运行累加到45，也没有由独审重跑。旧三模型真实归档兼容测试仍核原件 hash 不变。本批异常/53个无效 chunk 仍保留，未被后来的诊断有效项覆盖。

### 来源 join 与清理闭环

主分区196和扩展130的 review_id 各自唯一、集合精确匹配盲评映射；326个原答案 canonical hash 与映射及 judgment 全部一致，两个分区的原答案键不重叠。主分区 JSON 未声明 `summary.complete`，扩展分区为 true；本次完成依据是实际196/130覆盖及报告终态，未回写主分区加标记。join 为326/326：claim支持162、部分150、不支持2、无claim12；score_basis 有限支持14、不充分177、非评分135。**14/191不是精确分数准确率，也不是 gold**；跨分区开关比较有评审者差异限制。

新增 `mimo_pilot_review_summary.py --check` 只重算并比较既存 join（仅将 created_at 对齐到原值），不写归档；默认创建行为保留。末尾交接命令已改为 `--check`，既有 check-console 与 retained join 的统计一致，主线记录 exit0。清理后短来源 context 不再存在，留存 URL/片段 hash 和复核结论可核引用链，但不能仅凭 URL 重构当时上下文或再独立核世界事实。

清理回执记录三个精确自有根、strict CIM 同名 Python runner0与已知 session 终态、非link/逐文件 hash 检查；537件路径唯一、对应根内、size/hash合法，均标记删除。独审只读确认三个运行根现已不存在，`runs/c06-context-2026-10-07-01`仍在。未独立重跑 CIM/删除；对删除前进程及非link预检的证据为既有回执，不宣称事后重建了环境。共享TEMP、外仓和Phase92不在删除范围。

### 最终关键原字节 SHA256

| 文件 | SHA256 |
|---|---|
| 当前 `mimo_pro_pilot.py` | `6a323908171b27a3997cf4ad3eb77e137d168742a3a08283bce5f63033dd71b4` |
| 当前 `mimo_pilot_extension.py` | `875e6149113a559bd530363343be39c20f1270157498b496753cdc5453280d39` |
| 当前 JSON-off wrapper | `c2d0db865d061b02454ee8ab6a1cd09c32e36cec99a79e578fe73ab737321e66` |
| 当前 `batching_benchmark.py` | `0e191cd5cdd5613427dd07d37fa79293cc2eeec1775f900226d5a38e61f72db3` |
| 当前 `batching_benchmark_archive.py` | `a3d75bfbaae17b63f49f66b8b76e725d08238b12bf46f4042c0ae9d19aa68878` |
| 当前 `batching_benchmark_report.py` | `d907253b97de65194bdf35ceb63194aecd28ca65a144747101bae6212c2585fb` |
| 当前来源 join/check 脚本 | `2df57cad56cdb83acd9d4595aff05e4342728b8792eefdd1d67a1de5a040ce25` |
| 主归档 manifest | `cd21cfa052699b716423c6ca96b7bb945260082c0715b9da385a4c358d82324a` |
| thinking 归档 manifest | `049c755b3710b02ed5bc31e27f3758b3abf4e035afd9e5fd05b2aadb7ea30057` |
| JSON-off 归档 manifest | `1404ff0f9e7656b022d69fb259ae57f9c6bc87f3f020d5248cb049175fe92f18` |
| 最终17测试日志 | `335bbef5cac490552b767bf4c9f631376e6dbafa1b4b2966f2141d94907f1852` |
| 最终28回归日志 | `acaad4849a306a57354e6002b8c9a95d4827b83b660e34a764b4b9ba201997e7` |
| 来源 join | `25b60b43df9111b58ec8c858ffdbf86ff84e18aa8389a7e0ec0c5f9ffdee9787` |
| 来源只读 check 日志 | `08d0efa64813480d1e9186f202a826157e1517d57c1c43b04c7a15b0324f746e` |
| 清理回执 | `3c4673b46e213541955b44efdee7f29b12c98311254a304732b47b24743ceac2` |
| 最终实验结果文档 | `3844f9c6d84d6643776957084a80a78092320d8d603a1027d238967cd2d77072` |

本终态仅接受本次有证据的执行/归档/清理事实；未来协议未 live 验证、缺评分 gold、采样/输出上限/并发与 provider 缓存的比较限制均保持。可以提交本实验交付，不据本签收改变其他未完主线的状态。
