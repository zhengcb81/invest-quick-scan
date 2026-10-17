# LOCALE-ROBUSTNESS-09｜同一快扫在中英文表达下是否稳定

**目的**：用受控小样本测量语言变化是否让相同公司、相同事实和相同题义的评分发生实质改变。不是模型排行榜、翻译器开发、公司研究或prompt打包比较。

**唯一可写根**：`C:/Users/郑曾波/Projects/iqs-locale-robustness-lab/`。输入为总控dispatch lock冻结的三市场已验收参考案例（A股、港股、美股各一个），每家公司6道具有锁定题义/答案rubric和证据包的可评分题；如任何市场缺少已验收reference或双语证据，`blocked`并列缺项，不自行编造gold或换公司。不得读锁外的FIN Lab原件、生产DB、公司名单或密钥。

派发lock只冻结三公司18个题目/问卷的**源输入**、gold裁决与证据包、rubric、指定prompt builder和StockQA `ResearchChatSession`/原生usage账本适配；锁不虚称在派发前已有派生译文。实施者只能从这些锁定源材料准备双语版本，并在任何模型调用前生成绑定`dispatch_lock_sha256`的派生translation/input manifest。`run-manifest.json`须符合`locale-run-manifest.schema.json`：`locked_files`逐项记录源文件的lock引用、来源角色、安全相对路径、字节数和原始SHA；`derived_files`记录每份翻译与cell input bundle的文件ID、角色、相对路径、字节数和SHA；每个问题及cell都引用对应lock/file ID。语义预检必须证明locked-file三元组与dispatch lock完全相同、每道题的question/evidence/gold/rubric lock引用分别匹配相同角色、题目主体和hash，rubric文件内容声明的release与`rubric_release`相同，cell引用的三个derived-file ID与主体/题目/语言组合和hash一致，且所有引用唯一可解析。独立双语reviewer签收该manifest原始SHA后方可运行。gold与核证理由永不进入任何模型prompt。总控指定provider/model/revision、budget owner、quota group和UTC执行窗口必须由lock固定；若和其他任务共享一个配额组，需由wave-level检查保证窗口不重叠。未锁定的源文件、不同版本或无法验证的usage账本一律`blocked`。

## 预注册对照

使用单一锁定的provider/model/revision、thinking配置（优先按用户偏好打开）、温度/采样参数、输出schema、信息截止日期、原始证据ID、请求字段顺序与token上限；搜索和Fetch关闭。每个case仅翻译题目文本与证据表述，system/developer指令、评分定义、固定模板、字段顺序、工具定义与输出schema保持字节一致；所有结果仍用中文输出。总共18组“公司×题目”。每组进行2×2配对：中文题+中文证据、中文题+英文证据、英文题+中文证据、英文题+英文证据；翻译只改变语言，不得增加/删减/解释事实，证据ID和原始出处保持逐一对应。

双语材料由实施者在派发后制备。**第一次模型HTTP之前**，独立双语reviewer逐组检查全部18题四种语言组合，核对主体、断言、数字、单位、期间、否定词、限定语、出处定位均等价。实施者生成`run-manifest.json`，列出lock相对路径/字节数/SHA、译文和cell输入的相对路径/字节数/SHA、dispatch lock SHA及配对键；独立reviewer原始artifact必须明确批准该manifest原始SHA。未批准、SHA不符或有未解决差异，一律不发请求。最终payload仍须由实施者之外的独立reviewer审查；可由同一真实reviewer task在运行后继续整包复核，但必须保留调用前签收和最终审查两个可核验artifact。修订任何双语文本都要冻结新manifest并让reviewer重新检查全部18题，不能只批准diff。观察结果后不得回头改翻译、gold、样本或指标。

执行次序用固定种子打乱。计划72个主cell，再对固定种子预先抽出的6个cell各重复一次，计划共78个模型HTTP发送尝试。锁的硬上限最多90；剩余12次只供明确可重试的已知失败，或独立reviewer要求的定向复跑。所有HTTP尝试（包括超时/错误）都占用同一个上限；review请求不能另算。不得因结果不理想而重跑，不得重试发送状态不确定的调用，不得切换模型补位。搜索/Fetch HTTP硬上限为0。

## 输出指标和裁决

逐cell记录固定`subject_id, market, question_id, question/rubric release, evidence/input manifest hash, prompt_locale, evidence_locale, provider, model, thinking, run timestamp, as_of, selected HTTP attempt id, model HTTP count, cache input/uncached input, output tokens, latency, reported usage, cash charge, subscription usage, status, score, evidence refs, counterevidence refs, concise rationale`。结果schema以`selected_attempt_id`绑定用于该cell裁决的请求，并显式保留`counterevidence_refs`。不保存reasoning trace。每个claim引用锁定证据，不拿翻译文本当新来源。独立盲评按冻结gold逐cell判：schema/问题覆盖；结论和关键事实的来源支持；题分MAE与±1一致；状态变化；实体/数值/单位/期间/风险critical error。至少报告：四种语言组合的分数差分布和状态翻转数；纯prompt语言效应、纯证据语言效应及交互效应；6个重复cell的自身波动；gold支持率与critical错误；每个cell端到端时延、真实现金、套餐额度、缓存usage。样本只有18组，因此只给配对原始值/区间，不做总体显著性或全市场外推。

独立盲评按冻结gold逐cell判：schema/问题覆盖；结论和关键事实的来源支持；题分MAE与±1一致；状态变化；实体/数值/单位/期间/风险critical error。至少报告：四种语言组合的分数差分布和状态翻转数；纯prompt语言效应、纯证据语言效应及交互效应；6个重复cell的自身波动；gold支持率与critical错误；每个cell端到端时延、真实现金、套餐额度、缓存usage。样本只有18组，因此只给配对原始值/区间，不做总体显著性或全市场外推。

“稳定”预注册为：无任何语言组合触发实体/关键数字/期间/风险critical错误；每组在可比的scored状态下四cell最高与最低分差不超过1，状态翻转为unknown/conflicted时单独列出；overall支持率不得因英语/中文cell下降超过10个百分点。任一条失败即报告“不稳健”，不得用均值掩盖单个critical fail。结果程序必须从逐cell与逐attempt原始记录重算所有可得metrics，并验证`stability_verdict`与上述门槛一致；complete状态下result cell ID集合须与manifest 78个planned cell ID集合完全相等且各出现一次，不得重复、漏项或增加，attempt及selected attempt引用也须逐项绑定计划cell。正确性优先，只有稳定门通过才讨论耗时/费用/缓存差异；缓存不是质量补偿。

## 测试与交接

单元测试验证配对键、lock及输入manifest哈希、调用前reviewer签收/阻断、四cell覆盖/重复检测、randomization可重放、72+6+12账本、费用/usage分开、`unknown`保留、超出HTTP上限拒绝。语义校验须确认样本恰为CN/HK/US各一家公司、每家公司六题；四种`prompt_locale × evidence_locale`对每题恰好各一格；计划cell ID唯一且execution order恰为计划ID的一种排列；六个repeat各自指向同一question/语言的primary cell。complete结果cell ID集合必须与manifest 78个planned cell ID集合完全相等且各出现一次，不得重复、漏项或增加；每次attempt属于计划cell，每个selected attempt真实存在、属于同一cell，且可见response哈希与该attempt相符。每道题的`rubric_lock_ref`必须唯一解析到dispatch lock里的`role=rubric`文件，文件声明的release须等于question行的`rubric_release`；其他三个lock ref亦须分别匹配对应角色、主体/题目与hash。结果程序须重算所有有数据支持的metrics并检查与原始行一致，按预注册门槛判定stability verdict。若完整矩阵被preflight阻断，结果标`blocked`、review approval为false或不可用、attempts/outcomes为空且verdict为`not_assessed`；只有preflight批准后开始但未完整收尾才标`incomplete`。派发后产生的冻结manifest须符合[`locale-run-manifest.schema.json`](schemas/locale-run-manifest.schema.json)，最终逐HTTP账本/逐cell盲评结果须符合[`locale-results.schema.json`](schemas/locale-results.schema.json)。集成测试必须从完整矩阵中选一个已计划cell复用真实SDK/账本断言，不额外发送HTTP；完整E2E的78个计划发送尝试覆盖剩余集成验收。集成和E2E共享相同原生调用记录，所有复跑/错误继续计入90总上限。输出及raw request/response按授权保管，密钥绝不进入文件/日志。端到端测试从冻结dispatch lock到盲评结果/报告完整跑通，验证无搜索/下载、未发送槽不计发送、未知发送不重发、失败退出可续行且不改原记录。真实调用前必须校验lock预算和translation manifest签收；不满足即`blocked`，不能临时换免费模型。

handoff至少含冻结的18组配对索引与证据/翻译SHA、符合schema的`run-manifest.json`和`results.json`、调用前review签收、盲评标签、逐组cell结果、差异表、实际账本/套餐与cache计算、统计脚本、受控原始可见输出、测试/清理、最终独立审查artifact。未获可用的三市场gold或双语review时不得换成虚构例子冒称完成。
