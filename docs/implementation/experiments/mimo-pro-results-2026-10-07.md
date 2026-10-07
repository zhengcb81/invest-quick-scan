# 三市场小样本：打包问答与四模型思考对照结果

日期：2026-10-07。范围：宁德时代300750、中信建投06066、Alphabet GOOGL，每司同样10个问题。结论只适用于本次冻结片段、题目和协议，未改变生产默认策略，也没有关闭G3/F05。

本轮已完成全部收费调用、来源支持复核、离线归档校验和自有临时目录清理。DeepSeek五题包仍是速度与结构稳定性的候选；开启思考改善其本轮结构完整性，但明显增加耗时和输出token。MiMo Pro没有在本次严格结构协议下稳定胜出。**不能据此宣布模型的投资判断准确率，也不能把思考全部打开当作默认最优方案。**

## 1. 旧实验与本轮设计

旧实验三司30题，DeepSeek五题包90/90结构有效，对并发4逐题的配对速度约1.56倍、费用参考约低35%；高分、期间和财务依据仍有缺口。旧410模型/48搜索的上界USD4.869098及原件不改，见[旧结果](b01-improved-results-2026-10-07.md)。

本轮不是重新执行旧30题矩阵。固定10题为IQS_01/02/04/05/08/09/10/12/13/16，原题意与1/5/10锚点不改，使用真实历史身份样例和固定StockQA commit `6a9ff13864ebb160d5c4ab3cf2f42155d9f4aa99` 的10个源码文件。源仓只读，不使用其当前未提交修改。

主矩阵：Flash/Pro/DeepSeek × 每司1/5/10题包，逐题并发4、五题包并发2、十题包1请求；另有每模型十题包独立重复和Pro思考臂。然后按用户追加要求，登记四模型等输出上限10000的五题包开/关对照，Pro原开启6次复用；再做MiMo移除JSON mode的有界诊断。每包一次，不补问、不格式重试、不换模型拼齐失败臂。不同打包方法同时改变并发，因此比较的是执行方案，不是只改变包大小的单变量实验。

三司各4检索意图 × Brave basic/Tavily advanced，共24搜索请求（各12；Tavily advanced约24 credits）。候选片段在首模型前固定剔除21条错发行人、空导航、访问拒绝或陈旧无关来源，最终CATL/CNCB/Alphabet分别23/15/15片；上下文14113/10349/12026字符。片段均带source_id、URL、family、主体范围，未知发布时间保留未知。输入fingerprint `7deca8a41e1778a8fe5d388fd6975c1d317098ce532d1c7082879bc519aba866`。

**Brave/Tavily的短片段作为有编号的context交给LLM，模型必须用claim引用这些编号。**没有下载财报/网页正文，也没有在此次同输入对照中调用LLM原生搜索。首发前选择证据不代表每题证据充分；模型应在不足时返回insufficient_evidence。

## 2. 四模型开启/关闭思考，等上限五题包

每个模式请求三家公司各10题，分母30。下表“有效”包括合法未知态；有一项题号、状态或claim引用不合格时整包拒绝，不能把所有失败都解释为漏答。耗时是三家公司各自完整block耗时的中位数，单位秒；费用为该模式三家公司总模型token公共价格参考，不是每家公司费用，也不是控制台实扣。

| 模型 | 关闭：有效/30 | 开启：有效/30 | 关闭/开启耗时 | 关闭/开启USD参考 | 开启时报告的思考token |
|---|---:|---:|---:|---:|---:|
| MiMo v2.6 Flash | 20 | 5 | 17.873 / 69.695 | 0.00163748 / 0.00556280 | 8408 |
| MiMo v2.6 Pro | 5 | 15 | 22.655 / 138.799 | 0.00264464 / 0.02003681 | 16105 |
| DeepSeek Flash | 25 | 30 | 5.643 / 35.338 | 0.00811806 / 0.06406846 | 37997 |
| MiniMax M3 | 15 | 15 | 18.286 / 35.261 | 0.03575148 / 0.05272596 | 2133 |

DeepSeek开启约6.26倍耗时、7.89倍公共价格参考费用；provider缓存命中不同，费用比不是纯思考token的因果效应。M3开启有效的15行均经过完整JSON fence归一化，原始严格结构为0/30；关闭为15/30原始严格有效。归一化只去掉完整外层包装，不从思考/分析混合正文里抽取JSON。

**必须披露的实际参数偏差：**注册原本声明不传temperature；固定StockQA客户端却默认注入0.7。原Pro开启6次和追加42次共48次实际发送了0.7。按固定原源码重建，186/186 canonical request-body hash精确匹配；原参数记录、账本和答案不回写。上述等上限开/关双方实际都发送0.7，内部配对仍成立，但不能称温度省略，也不能与主温度0矩阵声称只改变思考。MiMo开启会按官方规则强制推荐采样、DeepSeek开启忽略temperature，服务端有效采样未完全控制。[MiMo协议](https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/text-generation/deep-thinking)、[DeepSeek协议](https://api-docs.deepseek.com/guides/thinking_mode/)。

后续observer已改为`explicit_only/2`，只从客户端继承model/messages，生成参数按完整声明构造；缓存协议也升级，避免旧0.7与新省略共用key。实质反例RED→GREEN，此修订只离线验证，**没有再收费重跑旧臂**。provenance重建的是原canonical JSON payload，未声称保存了原始网络数据包。

## 3. 主矩阵与稳定性

主矩阵关闭思考、明确temperature0，输出上限随包大小变化；各模型同臂输入一致。格式有效数不等于已验证评分数。

| 模型 | 包大小 | 有效/30 | 每司耗时中位数(s) | 三司模型USD参考 |
|---|---:|---:|---:|---:|
| MiMo Flash | 1 | 28 | 20.619 | 0.00539450 |
| MiMo Flash | 5 | 20 | 18.042 | 0.00565725 |
| MiMo Flash | 10 | 0 | 11.870 | 0.00185930 |
| MiMo Pro | 1 | 27 | 114.628 | 0.09724091 |
| MiMo Pro | 5 | 10 | 38.442 | 0.02282053 |
| MiMo Pro | 10 | 10 | 23.324 | 0.00947409 |
| DeepSeek Flash | 1 | 26 | 6.502 | 0.01329550 |
| DeepSeek Flash | 5 | 30 | 6.037 | 0.01448248 |
| DeepSeek Flash | 10 | 30 | 9.030 | 0.01016974 |

独立十题包重复：Flash从0→10/30，Pro从10→30/30，DeepSeek30→30/30。一次Pro重复通过不能覆盖第一次失败，也不能证明已解决结构问题。JSON-off诊断Flash5/30、Pro10/30有效（Pro原始严格0），没有稳定解决MiMo缺题/根结构，且新增JSON语法错误。M3思考开/关多项失败来自claim引用契约，不是请求被拒或一定没有回答。

本轮同输入下，DeepSeek五题包比逐题并发4略快但token参考略贵，与旧实验费用方向不完全相同。逐题臂反复使用同一前缀，provider缓存较多；provider缓存不是可控冷启动，不能只按输入token总量推断花费。五题包仍比十题包更快，十题包本轮参考费用较低；尚无事实gold可判综合最优。

## 4. 来源与评分支持复核

396个契约有效回答中，独立重复70行只用于结构稳定性；剩余326行由两位独立agent分区盲评，核对每个回答hash、题号、实际短片段、claim与评分依据。196主分区与130扩展分区不重叠，合并校验326/326；不是人类gold，未测两评审者一致性。Pro开/关跨分区，不能直接拿两agent的差异断言准确率提高。

| 维度 | 结果 | 正确解读 |
|---|---|---|
| claim支持 | 支持162、部分支持150、不支持2、无claim12 | 只检验本次实际提供的来源片段，不代表公司事实总体准确率 |
| scored回答 | 191 | unknown等合法非评分135，不能逼模型填分 |
| 评分方向/区间依据 | 有限支持14、不充分177 | 支持不代表1–10精确分已经验证；不得称“准确率14/191” |

高分缺充分支撑在多个模型/模式都出现。典型问题：发行人自己发债不等于承销客户留存；集团活动亏损不等于研发费用；现金流金额不等于ROIC−WACC；半年的数字错当全年、片段换行/缺表头导致单位错误；治理流程不能直接推出小股东公平。本次缺完整表头和期间口径的500字符片段，是许多依据不足的共同原因。unknown回答也可能带错claim，不能免审。

因此目前建议：保留DeepSeek五题包作为下一轮性能候选；开启思考作为复杂财务/口径判断的待验证策略。下一轮应先改善证据覆盖、期间/单位/主体语义校验和评分锚点所需证据，再检验思考能否提高来源支持度。不能靠自动补写模型缺项、降低引用契约或增加无依据评分提升通过率。此次没有启动200家公司试点，也没有将候选变成生产默认。

## 5. 隐藏思考、缓存和失败行为

MiMo/DeepSeek使用官方`thinking.enabled`，M3用`thinking.adaptive`和`reasoning_split:true`。只解析`choices[0].message.content`；独立`reasoning_content`在响应内存阶段丢弃，归档仅保留最终结构答案与usage计数。合成canary验证分开思考正文不进入账本/receipt；混入content的think/analysis前缀被拒绝，不用正则截取末尾JSON。[MiniMax协议](https://platform.minimax.io/docs/api-reference/text-openai-api)。开启字段与返回的思考token支持本轮确有思考输出；关闭臂某些接口缺reasoning计数，不能把缺失字段当独立证明0token。

本轮是一次external context问答；未来多轮native工具若协议要求回传思考，应只在易失会话保留必需状态，隐藏UI不能破坏协议。输出上限可能包括思考，记录finish_reason；本轮扩展1次length保留为失败。180秒是网络读取等超时设置，未宣称全请求严格wall deadline（Pro曾208.895秒）。Python guard只限制已知域名/端口、自有写根和子进程，不是操作系统级沙箱。

应用缓存：有效块main107、thinking23、JSON-off3，各自warm实测0HTTP/0key，账本和相应输出hash不变；不把53个失败块称缓存成功。缓存绑定题义/锚点、身份/日期、上下文、模型/端点、生成参数、parser及新transport policy。新warm miss直接拒绝发送；已归档run_id禁止prepare。provider前缀缓存与应用缓存分开报告，缺usage字段保持未知。实验中没有故障切换来掩盖臂失败；未知结果不重新收费，本轮未知发送为0。

## 6. 费用、归档、验证与交接

全部186模型HTTP + 24搜索HTTP，0未知，预算保守上界**USD2.877381**，未超新增统一200/24/USD8上限。主132/24上界1.889780；thinking新增42/0上界0.815144；JSON-off12/0上界0.172457。模型token公共冻结价格参考合计**USD0.392538**（不含搜索，不是套餐实扣）；不能把上界与token参考相加。MiniMax实际套餐扣额未知。DeepSeek离峰和MiniMax当前折扣价格可另以历史参考的一半展示，原冻结分析不改。[价格快照](mimo-pilot-pricing-2026-10-07.json)同时记录官方[MiMo](https://mimo.mi.com/docs/pricing)、[DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/?tab=case-studies)、[MiniMax](https://platform.minimax.io/docs/pricing/overview)。

三份不可变最小归档位于：

- [主实验](artifacts/mimo-pro-pilot-2026-10-07-01/archive-manifest.json)：132结果，实际payload回放132匹配，6个继承温度。
- [四模型扩展](artifacts/mimo-pro-pilot-2026-10-07-thinking-all/archive-manifest.json)：42结果，42匹配/42继承温度。
- [JSON-off](artifacts/mimo-pro-pilot-2026-10-07-jsonoff/archive-manifest.json)：12结果，12匹配/0继承温度。

保留原答案、错误、最小receipt/usage、ledger事件、题目/身份、来源URL+片段hash、输入锁、原执行源码和附加实际参数provenance。归档ledger.jsonl统一JSON序列化，因此归档文件hash与原运行账本字节hash不同；事件内容不改，两种hash分开记录，不能宣称归档ledger逐字节等于原文件。删除运行副本、cache/log、短来源context与盲评packet；未保存API key、原始API body或独立思考正文。来源短片段删除后仍可核hash/引用链与复核结论，但不能仅靠URL重构当时片段；这是轻资产留存边界。公共报告能从最小归档重算结构/费用统计。

离线验证最终17新测试+28受影响B01回归，共45独立用例GREEN，含真实旧三模型归档兼容、锁/输入/父账本漂移、参数/缓存协议、reasoning分离和归档完整索引。中间RED/环境错误日志保留，不把重复测试数累加。三个公开报告命令均exit0、archive_statistics_verified=true；来源join核326/326完成。一批集中技术审查见[报告](../reviews/B01/mimo-pro-technical-review-2026-10-07.md)，两来源报告和[join](../reviews/B01/mimo-pilot-source-support-join-2026-10-07.json)作为本批事实支持证据。

精确清理脚本先核来源审查完成、归档所有hash、0未决、strict CIM同名Python进程0、根路径及非link，再核每文件hash。三个自有根**537文件已删除**，回执[在此](../reviews/B01/mimo-pro-cleanup-receipt-2026-10-07.json)。初次Windows PowerShell默认编码读取失败、沙箱CIM不可访问均在删除前停止；显式UTF-8与沙箱外严格预检后再执行。未删除共享TEMP/别仓；Phase92 `runs/c06-context-2026-10-07-01`仍在。

在IQS根目录可离线校验（不调用付费API）：

```powershell
python -B -X utf8 scripts/batching_benchmark_report.py --archive docs/implementation/experiments/artifacts/mimo-pro-pilot-2026-10-07-01
python -B -X utf8 scripts/batching_benchmark_report.py --archive docs/implementation/experiments/artifacts/mimo-pro-pilot-2026-10-07-thinking-all
python -B -X utf8 scripts/batching_benchmark_report.py --archive docs/implementation/experiments/artifacts/mimo-pro-pilot-2026-10-07-jsonoff
python -B -X utf8 scripts/mimo_pilot_review_summary.py --check
```

`mimo_pilot_results.py`是运行根尚在时使用的历史统计收集脚本；清理后不要调用它重建原run。历史执行版与未来`explicit_only/2`源码不同，禁止关闭source lock继续旧run。后续主线接续Phase92：先修`embedded_answer`真实RED，再接Q10生产authority/store；本实验未提交该批未完产品代码，StockWiki六整改项和TH/IN开工前置仍独立待办。
