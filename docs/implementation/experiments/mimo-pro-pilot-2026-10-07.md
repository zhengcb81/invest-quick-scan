# MiMo Pro 小规模对照：预注册

用户2026-10-07明确授权加入mimo-v2.6-pro并组织小规模实验；沿用普通MIMO_API_KEY，不切换Token Plan。复用StockQA固定源码的LLMClient、连接池、既有B01账本/答案解析/缓存/归档工具，不改StockQA源仓或生产设置。Phase92当前交付保留，暂插本实验；G3/F05与下游包状态不变。

三家公司为原真实历史身份样例：宁德时代300750、中信建投06066、Alphabet GOOGL。固定10题IQS_01/02/04/05/08/09/10/12/13/16，题意/原锚点不改；同模型/题目/证据比较逐题并发4、五题包并发2、十题包单请求，三模型MiMo Flash、MiMo Pro、DeepSeek Flash。每家公司三模型十题包独立重复一次。主臂117HTTP、重复9；Pro另两次五题包开启思考共6HTTP，总132HTTP（此前口头129是漏计thinking第二个包，更正以此为准）。上限160模型、24搜索、USD5；无自动格式修复或补问，不为填满额度多发。429/401/403暂停该模型，不换模型拼齐臂；未知发送保留，接续不重发。

四个定向检索意图/公司×Brave basic和Tavily advanced=24HTTP，主域/交易所限定；只保留每片≤500字符、各公司unique snippet≤30K字符、合并context≤16K字符。同URL不同窗口是不同source_id，保留published_at未知、报告family和自述属性；不下载网页/PDF/财报，不把主域等同发行人正确。所有模型主臂同一证据、同SYSTEM v5、thinking disabled、JSON object、相同输出上限1024+600*n。Pro thinking臂max_completion_tokens=10000，不传temperature；参数变化单列，不混入主模型比较。模型原生搜索不纳入本同输入对照。

主要统计为完整结构有效率（unknown/N/A也有效）、实际总耗时、每成功题费用参考、实际provider缓存tokens、配对状态/分数一致性。全部新结果均保留失败项；高分、未知和财务断言按实际引用片段做全样本支持审查，不把结构完整率、模型分数或agent审查等同世界事实正确率。证据本来不足的题保持unknown才合适；不存在确定正确分的全量human gold。本轮只判是否值得扩大Pro对照，不宣布全局最优。

官方2026-10-07核实：Pro每百万token海外输入未缓存USD0.435、缓存USD0.0036、输出USD0.87；国内分别CNY3/0.025/6。套餐/控制台实扣不从token反推。来源：[定价](https://mimo.mi.com/docs/pricing)、[Pro模型页](https://mimo.mi.com/models/zh-CN/mimo-v2.6-pro)、[JSON模式](https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/text-generation/structured-output)、[思考模式](https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/text-generation/deep-thinking)。JSON模式只保证语法，不保证题目/字段完整。

隔离根runs/mimo-pro-pilot-2026-10-07-01，TEMP/TMP/TMPDIR及日志均指向该根；源码白名单精确导出，运行前冻结完整脚本原字节与输入hash。API key只在授权请求内从环境读，不打印/落盘；仅允许MiMo/DeepSeek/Brave/Tavily端点。应用warm必须0HTTP/0key读取，输出/账本hash不变；搜索接续0新增HTTP。批末集中审查一次、最小答案/receipt/来源指针归档后按owner/路径/hash/进程核对清理，不能删共享TEMP。旧实验归档不修改。

入口：python -B -X utf8 scripts/mimo_pro_pilot.py prepare|search|freeze|matrix|repeat|thinking|warm|archive --run runs/mimo-pro-pilot-2026-10-07-01。

## 首轮主臂后的有界JSON模式诊断
主矩阵13个block后观察到MiMo两型号HTTP200/stop仍缺题/把末题平铺到根。追加12HTTP：三司×Flash/Pro×五题包（每司2包），仅移除response_format，其余identity/题意/证据/SYSTEM/输出上限/temperature0不变。总预计144模型/24搜索，仍低于160/USD5；独立run、独立arm、原失败不覆盖。诊断尚未调用，不把事后适应性臂说成主预注册胜者；与主JSON五题臂配对但运行时点/provider cache可能不同。不能把JSON object语法合法称shape约束，看看强制JSON模式是否反而诱发此模型的array问题。

## 用户追加四模型思考模式对照（首发前登记）

主132请求与warm完成后，用户要求其他模型也开启思考。追加42次真实模型请求：三公司×四模型×开/关×两个五题包=48，复用已经实际执行的Pro开启6次，不重发。所有新开/关臂输出上限10000且不传temperature；Pro已有开启臂参数完全一致。MiMo/DeepSeek开启用enabled，MiniMax M3用adaptive并reasoning_split=true；DeepSeek只发max_tokens=10000，不能同时携带冲突的旧长度上限。题意/锚点/身份/搜索片段/SYSTEM仍与主臂完全相同。main原关闭4024与开启10000的初步比较有长度混杂，此扩展用于控制它；不能把默认采样差异说成完全控制的思考开关实验。

共预计186模型HTTP（132+42+12），24搜索，统一保守上界USD8，硬模型cap200。用户已授权超原预算继续并报备；本次是在追加首发前登记的有界扩展，原main预算与原预注册字节保持不变。孩子ledger上限从父终态ledger冻结SHA及已占上界扣出；JSON-off再扣main+thinking，不允许独立USD预算相加无约束。继续只有每包一次真实请求，无失败臂补问，不调用原生搜索或重抓材料。真实套餐扣费无法由公共token计价推断。

新入口：python -B -X utf8 scripts/mimo_pilot_extension.py prepare|run|warm|summary|archive --kind thinking|jsonoff。它复用同一B01/StockQA客户端；共用报告兼容原三模型定价快照，旧归档不改。准备、首次派发、每个block、warm与archive均校验自己源码/输入/budget锁和父字节绑定，父input与已发送ledger漂移时0key/0HTTP拒绝。代码修订在原132请求及warm全部终态后进行，原实际执行4个脚本仍保留原字节，不冒充新版本执行了旧臂。

思考正文仅在单次服务端响应的内存中由协议携带，应用只取message.content；不得保存或显示reasoning_content，不从混合正文中正则抽JSON。MiniMax显式split字段是输出分离，不关闭其内部思考。usage里的reasoning_tokens如有返回仅作计数，无返回则未知，不当作0。官方协议：[MiMo](https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/text-generation/deep-thinking)、[DeepSeek](https://api-docs.deepseek.com/guides/thinking_mode/)、[MiniMax M3](https://platform.minimax.io/docs/api-reference/text-openai-api)。本实验不做多轮native工具调用；未来此类多轮若官方要求临时回传完整thinking，应仅在易失session中保留，不能为了隐藏UI而破坏工具协议。

## 终态审查发现的协议偏差（原计划不覆盖）

全部186请求/warm完成后，独立回放发现StockQA固定客户端初始payload自带temperature=0.7，observer仅pop自己的parameters，没有删除payload默认温度。原Pro thinking6+新扩展42共48请求**实际发送temperature=0.7**，原main关闭/JSON-off138请求实发temperature=0；只有按此真实合并规则重构才能186/186匹配保存的canonical request_body_sha256。原ledger、请求hash、输入、预算、执行源、warm与失败均保持原字节；新增provenance记录实际参数及由固定runtime源码验证的继承默认值，不冒充当时已捕获完整原始HTTP字节。

等上限四模型开/关的实际显式温度均为0.7，因此内部配对仍同输入/cap/温度；不得继续称“不传温度”，也不得说与main温度0的矩阵只改变思考。MiMo开启会强制推荐采样、DeepSeek开启忽略温度，原生开关本来带来有效采样差异，三公司结果不能归因于纯单变量思考。

后续发送改为explicit_only/2：只继承model/messages，生成参数按声明完整构造；明确拒错model。新增真实方向的单测RED（实发0.7）→GREEN，不收费重跑旧实验。缓存key新增transport_parameter_policy，旧key不能被新发送语义静默复用；warm miss立即0key/0HTTP拒绝。已归档run_id禁止prepare重新收费。归档使用纯离线公开archive CLI核原实际payload与持锁快照；新runner的执行源锁应拒绝旧run与当前修订源不同，这是正常保护，不能关闭它继续发送。
