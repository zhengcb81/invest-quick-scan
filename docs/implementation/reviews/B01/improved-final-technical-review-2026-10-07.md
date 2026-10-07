# B01 改进实验集中技术终审（2026-10-07）

本批已完成原匿名164行、扩展匿名57行的独立逐claim审查，再读取最终实现、测试、预注册与结果草稿。没有API/凭据/外仓写入。技术范围内没有剩余归档阻断；可以整理轻量归档并按已验证自有路径清理临时run。此结论不授予生产默认或G3评分准确性通过，候选g5/g10事实审查由另一独立agent另列。

## 独立执行的验证

`python -m unittest discover -s tests -p 'test_batching_benchmark*.py' -v`：此前完整27 tests，0失败，0.711秒；随后定向增量1 test通过，见末尾同批复核。先26 tests也通过；新增第27项是本终审发现的检索baseline串用反例，属于同批修复回归，没有新增小节点审查门。

以socket/DNS、subprocess与read_key拒绝守卫执行纯离线 `batching_benchmark_archive.replay_inputs` 和 `batching_benchmark_report.summarize`：410个实际model payload全部匹配system/prompt/body/question/evidence hash，无HTTP或凭据读取。账本独立重建为410模型、48搜索、保守USD4.869098、0未决；actual_model为81 MiniMax-M3、126 mimo-v2.6-flash、203 deepseek-flash，全部usage存在。报告总参考模型价格USD0.653576与重算一致；套餐资源消耗/实际控制台账单没有被伪称已确认。

最终budget记录410模型/200搜索/USD10，保存原350/200/USD25及budget_revision、extension-preregistration。主线提供的用户追加授权及报备是扩展授权依据；不是因剩余美元预算而自行忽略原HTTP上限。预注册、账本和结果分别保留阶段变化。

## 实质问题及本批修复

旧report只匹配stage/company/route，search-cross的Tavily g5被配到Brave g1，且Tavily g1还被作为另一个Brave基线的包装对照。本审指出后，改为同时匹配evidence_variant、evidence_sha256、完整题号序列和prompt_profile；同池主矩阵性能不变。固定反例先RED，后GREEN。真实Tavily g5现在配Tavily g1：9个共同有效题、speedup1.26、参考费用比0.321；Brave为1.30/0.400。异context hash不比较。不同搜索源的因果比较须另列2×2，不混入同输入打包效果。

## 账本、失败与接续

Ledger恢复顺序校验reserved/finished：重复reservation或结算、未知attempt结算、非有限/负值/超过预留的金额均拒绝；原子线程预留和fsync发生于send之前。未知/超时不降为零费用，未知预留保持，summary未决单列。实际原账本无未决。401/403/429和2056在下一reserve前按route冷却，已在途请求仍可能返回；这属于有界并发行为，不是无界重发。

冻结StockQA十个源码白名单经commit及文件hash锁定，namespace导入避免整个配置聚合器；实验复用其LLMClient和连接池，无新生产client。GET/POST transport retry与redirect禁用。credentials只在收费路径读取，key不进入semantic key、receipt或归档。missing route不换其他模型拼同一模型臂。

搜索query checkpoint阻止重复同provider/query发送；pending或unknown必须对账，不盲重发。已经完成的block按run/context/questions/profile锁跳过；未写完block但存在attempt时保守pending，不自动重问。这是停止重复扣费的安全接续，不是崩溃后所有状态都能自动补齐的生产恢复承诺。

应用cache key包含route/模型/endpoint、system、identity/rubric/cutoff及证据全文输入、生成参数、parser version。warm路径在构造client/读取key之前返回；实际三模型warm及六stage公开CLI零send证明已在run留档，本审读取其证明并在隔离测试验证warm与input drift。cold仅指不复用应用答案，provider KV cache可能已经温。不能把本实验宣称为严格全冷硬件测速。

## 严格输出与补问

parser拒重复JSON键、qid缺失/重复/额外/乱序、unknown带分、bool score、未知source引用、scored无claims。代码围栏去壳及完整末题投影为确定性规范化，不补题、不改分、不去重，成功有normalization记录。JSON无歧义时逐行验收只作用于新扩展臂，原state仍invalid_answer且answers仍空；supplemental_valid_rows不能加进原strict完整率。

补问仅原题序前至多5个未通过qid/公司，最多一轮，新增attempt独立计费，已valid及已逐行恢复的qid不重问。report检验交集不为空就拒绝重问，union只在最终恢复链计数。独立复算M3三司最终有效26/30、19/30、25/30；合计wall41.575/53.073/38.857秒，与草稿一致。没有把失败题变成unknown或用后续分数覆盖原行。

## 耗时、价格与质量分母

主表各组独立复算一致：DeepSeek g1/g5/g10/g30严格有效89/90、90/90、90/90、90/90；每司wall中位17.143/10.664/9.344/17.825秒；g5同公司配对中位speedup1.56、费用比0.655。新增g3为87/90严格有效、另2行恢复；不存在同stage g1时不伪造配对统计。M3 g5为20/90严格有效、另44行恢复；g30为0/90。MiMo各组主表与重算一致。相同公司/同输入、可评分交集的MAE或±1只是模型内部一致性；不能称正确率。

只有三个发行人和温度0请求，不报告总体p90、显著性或全局最优。先固定题序划包，尚未实测“相互相关问题分组”的额外改善；后续建议相关问题包装应标明为待验证的设计，不能当本轮已验证技术。

显式短片段context的证据覆盖很弱，published_at都未知，主域/公司名过滤只是candidate筛选。同行、客户、承销对象、人物旧任职和CITIC Ltd00267能出现在同一个公司文档/交易所域名下；来源主体标签不替代逐句核主体。targeted同时改变query、domain/depth/窗口，v6同时改变来源选择和口径提示，不能把其差异单因归检索或打包。M3旧宽池是Alphabet、新targeted为HK，不是配对检索效果。

原164行审283 claims：支持214、部分53、冲突11、无支持5；66个scored为46支持不足、11有限可辩护、9冲突。扩展57行审109 claims：支持67、部分37、冲突4、无支持1；31个scored为23不足、5有限、3冲突。两包row_id无重叠，仍分母独立。unknown也有事实错误：原21个、扩展14个非评分行至少一个claim有问题。这些为agent-assisted给定片段支持标签，绝不是人类gold、世界事实准确率、精确分值准确率。显式claims以外的rationale/counterevidence/sensitivity错误另见每行whole_answer_note，不能将其余行叫整体正确。

## 轻量归档与复现限制

archive在写目录前验证owned run/destination、无active lock、目的目录不存在、未决attempt为零、所有实际payload hash可回放。只归档结构答案/receipt/ledger、blocks、题库身份metadata、source URL/title/fragment hash、prompt与输入锁；parse_excerpt剔除，不保留搜索snippet正文、runtime/log/cache或API raw response。隔离canary验证来源正文和parse_excerpt不会写入归档，漂移与越界在写目录前被拒。

初始orchestrator源代码只有hash未保存，旧probe system明确重构后匹配实际请求hash；不能称历史每一版源码均可完全恢复。审后删除原短片段意味着以后只能复算统计、核hash留档，无法从hash恢复同一上下文；重新搜索不是相同输入。草稿诚实表述该限制，符合轻资产目标。

归档不执行删除；主线执行最终清理前需再次核绝对自有run路径及owner，并先确认独立候选审查结束。当前archive检查active lock但不在整个归档过程独占同一锁；本轮全部live已停，按单owner封存可接受。以后生产并发归档应设计互斥，不能把这里的离线实验函数视通用生产数据库归档器。

## 可接受的收尾及剩余限制

1. 归档并清理本批自有临时资料，保留失败、normalization、扩展和输入盲审的全部最小交付。
2. 结果草稿中的在途审查和25/26测试旧计数需更新为已完成标签与最终28项（主线全套通过，本审独立27+定向1）；候选g5/g10审查须独立分母留档。
3. “g5为性能候选”可保留；升级正式生产默认/白名单仍受来源事实、评分充分性和原G3大节点约束，不因完整率100%提前放行。
4. 不新增小节点gate；本批实质复核已收口，前述候选审查和最终归档属于现有大批交付。

## 同批归档复算增量复核

新增 `batching_benchmark_report.summarize_archive/--archive` 已定向审查，不重复其余完整审计。它先检查归档manifest的文件SHA及必要文件，再核历史v5 route/pricing hash；在IQS自有TemporaryDirectory以受限唯一chunk_id、数字block文件名和原ledger恢复最小工作输入，自动清理后重算budget/by_model/blocks/repair_chains，逐项比较已归档analysis。无source context、runtime/client导入、凭据或HTTP；未来价格/route漂移明确拒绝，不能无提示用新价格改历史统计。

独立执行新增 `test_public_archive_report_recomputes_without_network_or_sources`，并额外加socket/DNS/subprocess拒绝守卫：1 test GREEN，0.340秒。测试正例从真实Ledger实现生成的最小隔离fixture（不是真实API或身份golden）→archive→离线重算通过，改动results.jsonl的hash反例拒绝；temp文件自动清理。主线报告全套28 tests GREEN，本审本批独立验证为此前27全套及这次1项增量，不伪称再次全跑28。

archive metadata仅追加candidate匿名映射及answer-audit-summary；未增加snippet正文/密钥/raw response字段。正式归档和清理尚未执行，须等候选agent签收。这个新增公开复算入口完善“清理后统计可复算”交接；不能恢复原检索片段或历史初版源代码的边界仍成立。

## 审过的最终源码hash

- `scripts/batching_benchmark.py`：`5cb928fcfe63ff1f4aa27bc887b61ced56fec35f6cf457ccb1a2535acd93bfec`
- `scripts/batching_benchmark_report.py`：`519e9443a53a9da846f6890034b1601e8cd853e1916f657ef8a735ecf315d38c`
- `scripts/batching_benchmark_archive.py`：`69dad3fc3991f5658c29ec09602c5fb9f0f14a9fcec4bd7184b7569cff1ead9b`
- `tests/test_batching_benchmark.py`：`9e0e2916e9618a0512a0e4e22c2ac6f727858a46454f871198344d83e371aeda`
- `tests/test_batching_benchmark_report.py`：`905815c4dff33288055d481f3200d77272382b7ff8d04e2c941f5ccda8959557`
- `tests/test_batching_benchmark_archive.py`：`762ef4b51eebae2ca81db0689c16c59ac4f09c8e36db34d898396125ae2e6636`
