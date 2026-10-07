# B01改进实验结果（2026-10-07）

结论：DeepSeek五题包是当前效率与结构稳定性的候选，十题包更快；独立事实审查发现两者仍有证据和口径缺陷，不能宣布正确性最优。正式G3与生产默认没有变更，不得按分数高低判模型胜负。

## 范围与真实消耗

宁德时代300750、中信建投H06066、Alphabet GOOGL；相同30题、真实历史身份、rubric、截止日2026-10-07，模型MiniMax-M3/MiMo-v2.6-flash/DeepSeek-flash。主矩阵逐题基线并发4，其余包并发≤4；不预设低谷、不把券商套银行或制造业口径。

最终410模型HTTP、48搜索HTTP；0未知/0缺usage，保守预算结算上界US$4.869098。初始350请求上限后，用户追加继续授权并报备63请求扩展；新hard cap410/200/US$10。费用未超过原US$25上限。

公开价参考模型合计US$0.653576（包含失败、诊断、重复与补问）。这是估计，不是控制台账单；MiniMax套餐资源/是否额外收费无法从tokens反推。Tavily24请求=18basic+6advanced=30credits，PAYG参考US$0.24；Brave24请求，用户声明套餐月请求无限。搜索上界账本预留US$0.48，未将套餐额度虚构为现金支出。

| 模型 | HTTP | input tokens | output tokens | provider cached tokens | 公开价参考USD |
|---|---:|---:|---:|---:|---:|
| minimax | 81 | 517965 | 67863 | 150896 | 0.401220 |
| mimo | 126 | 928707 | 54874 | 760000 | 0.041112 |
| deepseek | 203 | 1237518 | 120611 | 1036544 | 0.211244 |

计价来源：[MiMo官方](https://mimo.mi.com/docs/pricing)、[DeepSeek官方](https://api-docs.deepseek.com/quick_start/pricing/?tab=case-studies)、[MiniMax官方](https://platform.minimax.io/subscribe/token-plan?tab=api-enterprise)、[Tavily credits](https://docs.tavily.com/documentation/api-credits)。DeepSeek采用peak参考，offpeak约半价；M3参考采用未优惠标准价，比公开50%优惠价更保守。cache usage已扣除，没用套餐价格伪装按量账单。

## 打包方式：效率与完整性

以下每家公司30题，三公司中位数；费用只含此方法的模型请求，不含共享检索/预检。有效行含合法unknown/N/A；不是可评分率或准确率。

| 模型 | 包大小 | 规范化后严格有效行/90 | 逐行额外恢复 | 每司wall中位秒 | 每司模型价参考中位USD |
|---|---:|---:|---:|---:|---:|
| deepseek | 1 | 89/90 | 0 | 17.143 | 0.014343 |
| deepseek | 3 | 87/90 | 2 | 11.643 | 0.009389 |
| deepseek | 5 | 90/90 | 0 | 10.664 | 0.008577 |
| deepseek | 10 | 90/90 | 0 | 9.344 | 0.007579 |
| deepseek | 30 | 90/90 | 0 | 17.825 | 0.005947 |
| mimo | 1 | 86/90 | 0 | 59.240 | 0.007118 |
| mimo | 5 | 50/90 | 0 | 23.528 | 0.001625 |
| mimo | 10 | 40/90 | 0 | 36.780 | 0.001870 |
| mimo | 30 | 30/90 | 0 | 41.389 | 0.001232 |
| minimax | 5 | 20/90 | 44 | 31.456 | 0.033454 |
| minimax | 30 | 0/90 | 0 | 70.886 | 0.015991 |

DeepSeek五题包：相对同公司并发4逐题基线，中位配对speedup=1.56，中位费用比=0.655（约降35%）。每司实测10.174–11.946秒。三题包没有进一步提高完整性；十题包更快，但状态/评分会变；三十题包总体没有快过逐题并发，CATL五个评分变为全unknown。

MiMo整包结构不稳定：首次HK30题全失败，同输入重复又30完整；本轮许多失败finish_reason=stop，不能都归因token截断。M3三司30题均失败、不同公司五题包也失败多；十二题Alphabet和目标HK有完整结果，不能跨公司把成功归因检索。温度0不保证服务确定性。

完整输出的代码围栏与明确完整末题投影仅作确定性规范化，成功记录normalization；没有补题/改分/去重。原strict chunk失败依然失败，新增逐行恢复另列，不改旧失败工件。全表与原始chunk/receipt见最小归档。

## 只补失败题的结果

| 公司 | 首次整包严格有效 | 逐行校验后有效 | 再问题数 | 补问通过 | 最终有效/30 | 合计wall秒 |
|---|---:|---:|---:|---:|---:|---:|
| alphabet | 10 | 25 | 5 | 1 | 26/30 | 41.575 |
| catl | 0 | 18 | 5 | 1 | 19/30 | 53.073 |
| cncb_h | 10 | 21 | 5 | 4 | 25/30 | 38.857 |

最多一轮、每司最多5失败题，15次只成功6题；不重问已通过题、不覆盖第一次分数。逐行严格校验能保住有效行，反复补问不能保证高质量；此轮M3路线不是批量默认候选。

## 搜索怎么给模型

本轮只用显式外部context：先Brave/Tavily搜索，保存有界标题/URL/短片段/时间/source_id，按公司与主体过滤，作为untrusted_evidence JSON喂入LLM。两方轮流合并避免第一方填满；不会把检索来源当成可信指令。没有下载PDF/财报/网页正文，模型native搜索不在这组同输入对照内；所以结论不能推断原生搜索谁更好。

宽意图basic：36请求、三司；HK单一Brave/Tavily×逐题/五题的交叉都0scored。输入盲审36槽仅2有限充分/34不足、82来源published_at未知。它能测试结构和性能，不能支持大部分深度评分。

目标检索：另12请求，中文题意/主域限定、Tavily advanced、同URL不同主题窗口保留独立fragment ID，21片/13URL/8476字符。比宽摘要具体，但仍只有12题中2有限充分/10不足；两片主体是中信股份00267，需来源主体级过滤。少数无关PDF片段仍通过域名过滤，说明主域白名单不等于正确发行人。

最后v6组合：只取已盲审7个明确业务/财务片段，去除其他主体，标报告family，并提醒客户资产/永续权益/CFO/资本成本口径。DeepSeek五关键题逐题/包/重复全有效且全unknown；M3五题首次失败、重复五题全scored。这不是可证实的准确率提升：证据不足仍应是未知；未来需要题目级检索覆盖与来源支持检验。

## 事实与评分审查

三份匿名审查共281行，row ID无重叠；逐行核对原答案hash、状态、分数、claim索引与实际引用。它检查给定片段支持、主体、期间、单位、口径与给分充分性，是agent-assisted审查，不是人类双gold、世界事实准确率或精确正确分。样本偏向关键题与异常，不能把三份比例合并当作总体准确率。

| 独立样本 | 行数 / claims | 支持 / 部分支持 / 冲突 / 无支持 | 已评分行：有限可辩护 / 不足 / 冲突 | 未评分行中有claim问题 |
|---|---:|---:|---:|---:|
| 原匿名样本 | 164 / 283 | 214 / 53 / 11 / 5 | 11 / 46 / 9（66行） | 21 |
| 扩展三题包、五题恢复、补问 | 57 / 109 | 67 / 37 / 4 / 1 | 5 / 23 / 3（31行） | 14 |
| DeepSeek五题、十题候选补审 | 60 / 118 | 89 / 29 / 0 / 0 | 8 / 19 / 0（27行） | 22 |

候选补审在性能统计之后选取：五题、十题两方法、三公司所有scored行，加固定六个财务/治理题；没有挑选表现好的行。五题方法14个评分中仅4个有限可辩护、10个不足；十题13个评分中4个有限可辩护、9个不足。样本不同且不是精确gold，不能据此判两者谁更准确。仍有期间补全、收入替代利润、引用窗口越界和同业主体省略；1个未知项的缺证据表述与已给类股权利事实冲突。unknown能保护分数，也可能包含错误事实。

原样本与扩展样本还出现金额十倍错、错年、C股投票权错、承诺当已发生、截断现金当两年缓冲等。rationale/counterevidence/sensitivity的问题另记whole_answer_note；没有claim问题不等于整行正确。完整标签及边界分别见[原审查](../reviews/B01/improved-answer-blind-review-2026-10-07.md)、[扩展审查](../reviews/B01/improved-extension-answer-blind-review-2026-10-07.md)、[候选补审](../reviews/B01/improved-candidate-answer-blind-review-2026-10-07.md)。格式齐不能通白名单。

## 缓存、接续与复现

三模型实际答案warm命中，6个完成stage的公开CLI接续均在DNS/socket/凭据读取禁止guard下通过；账本原字节未变，模型/搜索新增0。应用答案cache、检索片段cache、provider KV cache分开计；所谓cold只是不复用应用答案，provider cache已可能温，使用actual usage记录。

全部410 actual request payload的system/prompt/question/evidence与body hash可回放匹配；runtime复用StockQA固定commit6a9ff13十个明确源码白名单、不复制配置密钥。早期probe profile后来显式重构，匹配实际hash；初始orchestrator只记录hash未存source，因此不声称所有历史代码都可逐版复原。所有正式主臂v5以及v6输入独立锁。

最小归档只保留结构答案、最小receipt/ledger、统计、题库/身份metadata、source URL/fragment hash、输入锁/审查标签。审后清理自有runtime/log/cache/snippet；清理后可复算统计与hash记录，但重新搜索不能得到原相同短片段，这个限制明确留档。28离线单元/集成/归档测试通过，真实收费探针均单独计账。独立[技术审查](../reviews/B01/improved-final-technical-review-2026-10-07.md)无归档阻断；同批修复检索对照串用基线问题，严格配对context variant/hash、题集与profile，未增加HTTP。

## 后续采取的方案

已实测的性能候选为“共享说明一次+按原题序每包5题+包并发≤4+显式片段context”。三公司合计11个与逐题基线都能评分的配对题，分差均在±1内；这只是输出一致性，不证明分数正确。“按相关主题组包”是待验证的后续改进，本轮没有测试该变量。先检查题目证据覆盖与身份/期间/单位，再评分；逐行验收、失败题有界补问、确定性应用cache接续可分阶段接入。g3/g5/g10不能只按价格选择，弱证据下任何包都不应强填分。

生产仍保留逐题基线，等G3事实/评分gold及正式工作链验收；本轮不启动L03、200家公司或2000家名单，不改正在由别的harness施工的外仓。QA-NET/StockWiki接收时可消费本实验建议，接口实现与覆盖另在原大节点集中验收。

运行、版本与预算调整见[预注册和迭代记录](b01-improved-2026-10-07.md)。[统计归档](artifacts/b01-improved-2026-10-07/analysis.json)保留所有成功和失败；下面命令仅离线验证归档hash并复算统计，不重发模型或搜索：

```powershell
python -X utf8 scripts/batching_benchmark_report.py --archive docs/implementation/experiments/artifacts/b01-improved-2026-10-07
```

公开入口是实验工具，不是新的生产LLM client；收费发送仍复用冻结StockQA LLMClient。禁止接手模型为复现统计重新执行prepare/core等收费stage。输入短片段在审查后删除，原实时上下文不可从hash恢复；来源URL只供后续重新检索与追溯。

封存清理已执行：先验证全部410请求payload、归档8个数据文件hash和904个自有run文件清单，确认无运行锁/重解析点；仅删除绝对路径`C:\Users\郑曾波\Projects\invest-quick-scan\runs\b01-improved-2026-10-07`。9文件归档保留（含manifest）。删除后再运行上述公开CLI，DNS/socket/凭据/子进程全部禁止，仍exit0、archive_statistics_verified=true、模型410/搜索48且新增0；临时目录自动恢复。实录`validation-B01-archive-cleanup-2026-10-07.log`。未下载财报，未触碰其他harness仓库、公司库或既有opencode.json。
