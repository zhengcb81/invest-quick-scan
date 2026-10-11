# EVID-REF-02 R3：原锁可移动验证与语义资格集中续做卡

这是原EVID-REF-02同一次包级整改的续卡。R2有有效修复，应保留现有交付；这里只解决 [R2实际验收](EVID-REF-02-R2-acceptance.md) 的剩余缺口，不重新实现旧包，不新增小节点gate。收到用户开工指令后核实唯一writer；总控编制此卡不等于已经派发。

## 1. 工作目录、基线与写边界

唯一实现仓为 `C:/Users/郑曾波/Projects/iqs-evidence-lab`。IQS、FACT Lab、StockQA、StockWiki、company-wiki、其他实验仓全部只读。不得写总控PWF、真实数据库、公司名单、共享TEMP、CodeGraph或任何API配置。

接收基线：

- 分支 `codex/evid-ref-02-r2`。
- 产品 `ffb1e7046423e9e97dec6aefba6e66a366fb119f`。
- 最终交接HEAD `b2c7c73812fca4a5ae3a4e2bc8b4ecf8f793099c`。
- 重建基线 `b59d5b976478887e386b12cfc0bc7d5eb9a633e7`；旧70498e4/44aa204对象当前不可读。不要修复、重造或假称已找回原Git历史。
- 验收时有5份旧清理回执未跟踪。开工读取最新实际状态，保留其他进程成果，不reset/clean/stash，不提交或删除无关文件。推荐正常新建 `codex/evid-ref-02-r3`，不要回退HEAD。相关source或固定输入字节若已经变化，先给总控具体新基线，不按旧状态覆盖。

本卡白名单：

- `src/iqs_evidence_lab/reference/`，允许新增本包resolver/check/request模块。
- 本包 `schemas/reference*.json`、`fixtures/reference/` 的**新增版本/新增合成输入**，以及 `tests/reference/`。
- `tools/reference_entry.py`，只加本包公开参数/入口兼容，不另造executor。
- 新增 `docs/handoff/EVID-REF-02/remediation-03/`，包括自有planning、日志、隔离记录和结果。

只读保留旧1.0/1.1 schema、原pack/报告、R1/R2交接、历史回答/请求、原IQS题库/anchors/manifest/inputs.lock。不得写共享 `guards.py`、`hashing.py`、`inputs.py`、`cli.py` 或旧Lab诊断；既有receipt环境override足够，不改旧测试bootstrap。若确需白名单之外的修改，把目标反例与最小文件路径报总控，不能自行扩范围。

自己的PWF只放 `docs/handoff/EVID-REF-02/remediation-03/planning/`。无联网采集、真实API、财报/网页正文下载、人工审批伪造或金融gold创造。

## 2. 必读和固定输入

- [原施工包](../../../parallel-lanes/packages/2026-10-10/EVID-REF-02.md)、[原交接规范](../../../parallel-lanes/packages/2026-10-10/handoff-rules.md)、[原inputs.lock](../../../parallel-lanes/packages/2026-10-10/inputs.lock.json)。
- [R2续做卡](../2026-10-10/EVID-REF-02-R2.md)、[R1实际验收](../2026-10-10/EVID-REF-02-R1-acceptance.md)、[R2实际验收](EVID-REF-02-R2-acceptance.md)。
- EVID仓的 `docs/handoff/EVID-REF-02/remediation-02/` 和当前实际 `reference` 源码。
- 上述公开验收报告链接的私有完整报告、21例controller记录、原公共CLI日志。可读用于定位，不能复制私有短文/金融输入到公开交接；首次controller错公司假阳性已经撤回，以第二版为准。

原锁raw SHA-256为 `106c9ead11b29df9319746e4fcc7e38e8c1a922c63d5ac8b5e1f8004e38ce7ee`，大小 **92334 bytes**，相对路径 `docs/implementation/parallel-lanes/packages/2026-10-10/inputs.lock.json`。锁的文件项声明source_root/path/bytes/sha256/hash_domain/consumers，并**没有单独role字段**；role属于原pack的input_refs。实现应核原pack角色与已冻结路径/用途的映射，不能假造锁内role字段、不能要求一个不存在的字段导致全拒，也不能只因字节相同就允许替换角色。

R2 pack/原锁/问题ID/wording/anchors保持原字节。为新增检查记录或字段升级可增加版本化候选，不能覆盖旧fixture。正常新版候选与保留旧字节必须分别核验。

## 3. 正式可移动source-root-map契约

先完成这一环节，再把公共语义结果作为验收证据。当前按照运行时绝对root匹配原锁，复制IQS或Lab就丢失必需角色覆盖；指回真实IQS也不能解决复制Lab的preregistration。不得改原锁中的路径、改pack锁SHA、派生新锁绕过 `_verify_against_batch_lock`，也不得monkeypatch全局LAB_ROOT/TEMP_ROOT/resolve_root。

在既有 `tools/reference_entry.py` 的validate/evaluate子命令新增可选 `--source-root-map <file>`。不传参数时保留原位置只读行为；传参数时显式创建**一次不可变的本包resolver**，由现有pack加载/锁验证/answers读取调用链传递使用，不修改共享inputs/环境全局，不新增第二执行器。summarize若只消费已经生成的evaluation，不需要强行加此参数；其输入/输出路径保护保持。

新增严格版本schema `iqs.reference_source_root_map/1.0.0`。建议并按下列名称固定公开结构；具体磁盘地址由隔离harness填写，不在模板内预置个人路径：

```json
{
  "schema_version": "iqs.reference_source_root_map/1.0.0",
  "package_id": "EVID-REF-02",
  "input_lock": {
    "source_root": "iqs",
    "path": "docs/implementation/parallel-lanes/packages/2026-10-10/inputs.lock.json",
    "sha256": "106c9ead11b29df9319746e4fcc7e38e8c1a922c63d5ac8b5e1f8004e38ce7ee",
    "bytes": 92334
  },
  "roots": [
    {"symbol": "iqs", "original_root": "<原锁repositories中的IQS root>", "relocated_root": "<隔离IQS副本绝对目录>"},
    {"symbol": "lab", "original_root": "<原锁repositories中的Lab root>", "relocated_root": "<当前运行代码的隔离Lab绝对目录>"}
  ]
}
```

严格JSON禁止重复键、未知字段和未知版本；roots必须是iqs/lab各一次，不允许覆盖、别名、模糊匹配或自动推测来源。map文件本身在读取前执行既有secret/reparse/越界检查，放隔离Lab内明确自有输入目录。模板中的占位符不是可执行样例；交接必须给出真实生成命令和实跑map。

验证必须同时完成：

1. 对实际读取的原锁原字节核固定SHA/bytes。这个预期来自本包冻结契约，**不能仅由调用者map/被改pack自报**；换锁再同步改map/pack仍拒绝。若未来要换合法冻结锁，需要单独发布新输入基线，本卡不实现自动放行新锁。
2. `original_root`逐项精确绑定原锁repositories及files的来源，构造“原锁来源→符号”索引；`relocated_root`只决定此次读取位置，不能改变来源身份、相对path、角色或授权。lab映射必须等于当前代码副本的Lab根。拒绝未知origin、重复symbol、同一读取根冒充两个来源、UNC/协议或设备路径、dot逃逸与link/junction/reparse；先检查原始祖先再resolve，不能resolve后隐藏链接。只搬Lab时，Lab副本可能在IQS自有运行目录下；这种明确的只读根包含关系本身不能导致正常控制全拒。读取仍按每个ref固定symbol查找并核原来源/角色/字节，绝不能按“最接近的根”猜来源；写范围仅是当前复制Lab的原允许根。
3. 按原相对path打开实际副本；逐项核原锁/原pack声明的大小与rawSHA，核本包consumer、必需角色与被冻结文件用途的映射。角色不是新增自由授权；不得用其他同内容路径、同SHA的另一个角色、另一仓同名文件替代。
4. `_verify_against_batch_lock`仍做原必需覆盖/字节核验，只把索引的来源身份与实际读取位置分开；新resolver是正式公开机制，不是控制器patch或guard绕过。
5. 输出守卫继续只允许**当前Lab的原本包输出根**；map不能扩大写范围，不能把发布根映射到原源仓、真实数据库或其他项目。staging真实祖先保护保持。
6. receipt记录map版本/rawSHA、原锁rawSHA、每个符号的原来源身份与运行时副本身份及逐输入核验；公开报告可以脱敏具体副本目录。map不可被解释为金融证据或人工审批。

正常控制是**原pack、原锁、输入字节都未改变**，通过公共CLI在全副本和仅Lab副本两种位置validate。随后公共evaluate必须成功并产出完整结果，即使准确性诚实降为not_verifiable也算正常。再测伪origin、错字节/大小、换锁、换角色/路径、重复map、输入reparse、secret、输出越界，明确拒绝原因，不能用不相关错误冒充目标检查。

## 4. 剩余机制的具体实施顺序

这是一个工作批次，可以逐项开发，但只做一次集中交接/包级review。

### A. 保存已绿并建立可达反例

先在全新独占根按原字节冻结所有需要的src/schema/fixtures/tests/入口及锁定输入，核真实source SHA。保留R2 unknown残值、冻结资本题义、旧摘要accuracy分离和真实staging保护。新增反例先看见目标缺陷；公开原输入正控修好之前，纯函数观察只能标为局部定位，不能宣称公共E2E已经通过。

### B. 检查记录、主体与时间绑定

当前source_checked仅核字符串非空，不能授资格。增加本包严格版本化的检查记录和引用解析；新增字段应发布新schema版本，建议候选pack/evaluation/summary **1.2.0**，保留1.0/1.1只读解析与历史字节，不在旧schema里塞未知字段或静默补审批。

每条可授某个维度资格的检查至少绑定：唯一check_id、record_id、question_id及冻结question hash、source_id、source snippet rawSHA、主体/上市scope与会计scope、metric/definition/currency/unit/reporting_basis、period/information_cutoff/disclosure时间、具体检查维度、method、actor、checked_at、结论与短理由。ref必须可解析到这条实际记录并核字段；不存在ref、通用URL、另一个record/source/hash、合成测试记录都不能授真实金融准确性。不要仅验证这些字段均非空就算完成；解析和逐字段对照是核心。

source和record均要核主体/口径，禁止同名混淆、跨公司source、scope层级或会计口径偷换。允许当前检索/核验时间晚于旧信息截止日，但来源披露及被用信息必须满足原冻结cutoff；晚于cutoff的披露、无法确定可用时间、混合比较期间要拒绝或not_verifiable，不能用新的检索时间替代历史可知时间。未来checked_at也不得凭自报通过。不得把actor写成人类或补human_approved。

先让旧pack在结构上正常读/评估；其旧source_checked若缺这套检查依据，资格降为未证实，**不要为了保留旧准确计数伪造检查记录**。synthetic正控只证明解析/绑定机制，不代表真实来源事实经过人工确认。

### C. 评分端点与冻结题义

端点source ID除了存在，还必须绑定本公司、本record、已引用的证据、冻结题目和对应端点锚点；核来源内容/可支持的论断，不能用另一个公司的营收或本公司的capex来支持护城河评分。IQS_05的4..9若两端机制/锚点/反证没有依据，保持候选区间或null/not_verifiable，区间内成员关系只能是机械一致性。保留IQS_10冻结资本题guard和原ROIC/WACC缺口，不因为新ref或definition变更放行。

负例必须包含：不存在SRC、真实存在但属于CATL且只支持其事实的SRC被用作Alphabet IQS_05端点、同公司却与record/锚点无关的来源。正常控制是正确闭合且用途绑定的合成例，加原pack缺证仍能正常evaluate但不授准确；不能为了“正控”把真实缺证评分硬标正确。

### D. 独立冻结请求与完整分母

历史请求集合必须来自原锁下实际question-set/preregistration/request manifest，独立于答案文件的可编辑question_ids。使用实际存量arm/company/route/request信息建立明确绑定；不要从剩余answer rows、set名称猜题集，也不要固定把所有run扩成48槽位。

规定并实现唯一的请求fingerprint规范：冻结题目ID有序序列及冻结题目hash/版本/公司scope组合，使用现有canonical hash能力；历史 `questions_sha256` 的真实口径需要读取实际冻结输入确认。若旧字段不是这个新口径，写明legacy映射、保留原字段，不把新hash冒充旧hash，不重写历史输出。新请求manifest与身份/hash绑定应在独立版本schema里发布，receipt保留映射来源。

显式question_ids必须等于独立冻结集合/顺序；删除/变更显式ID、requested_question_ids或fingerprint不能缩母。实际历史输入无法唯一重建时明确拒绝或not_evaluable，不推断一组“看起来合理”的题。全0/错误指纹必须被核验拒绝，不能忽略。六题缺F02仍6请求/5回答/1missing；真实单题仍1请求；未知保留分母但不计正确，重复/额外ID拒绝，重复模型run不增加独立金融样本。

synthetic输入必须显式声明自己的独立请求manifest；不允许把历史文件换一个source_category=synthetic来规避原冻结绑定。测试可以新增完全自有的合成请求/答案，但要保留合成标记，不能授生产资格。

### E. 不把token匹配升级成金融真值

当前text oracle是年份、单位、指标和数值词匹配；它可以发现明确矛盾或记录一致性，不能证明句义、更不能直接生成accuracy=supported。否定句、混合指标/期间/主体、比较句均需有鉴别力；“没找到冲突”和“双模型同意”不是支持证据。

本卡不要求另调LLM或做自然语言真值引擎。无法从可追溯、主体/期间/口径一致的实际检查依据得到语义支持时，text accuracy应not_verifiable。数值完全一致仍可记consistency；若要授某维度source support，必须由该维度实际绑定的检查记录给出依据并明确资格范围，不能跨维度借用。不要追求旧supported数量或承诺人工金融oracle准确率。

旧1.0摘要修复保留。旧1.1历史报告若没有新资格依据，可以读取和单列其原计数，但不能自动将旧accuracy字段当新版已验证金融准确性；interface说明版本迁移与计数含义，原报告字节不改。

## 5. 一批测试与一次review

开发阶段只跑受影响测试。最终同一隔离批次跑：

1. 本包reference相关测试（包括受影响的旧1.0/1.1兼容/输入/输出保护），新反例与正常控制；不重跑旧214项整个EVID-LAB，不复做其他Lab、UI或生产实验。
2. 实际公共 `tools/reference_entry.py`：原字节pack+原锁+正式map validate成功；原输入evaluate成功；实际产物summarize成功；旧1.0摘要仍可读且accuracy不升级。合成反例/候选新版另列，不能顶替原输入正控。
3. 同一批覆盖：否定/混合text，unknown残值与正常弃答，已绿资本guard，端点三种错绑定与正常例，检查ref缺失/通用/错record/hash/time及正常例，未来披露，六题缺答/改ID/错指纹/真实单题，map正反例，真实自有staging junction、普通输出和重复输出。

正式输出可降低准确性计数，这是诚实修复，不是测试失败。反例要记录目标拒绝原因；无关schema/hash/路径错误不能代替机制通过。保留真实RED/失败/最终结果，不修改旧日志，不把skip说成绿色。整批后一次包级review，整改接续同一个EVID-REF-02，不再拆成九个小验收门。

## 6. 隔离与清理

副本、数据库、subprocess、缓存、TEMP/TMP都在新自有短根，x/exclusive创建，先确认不存在。环境只传必要系统字段与自有路径，不读取API key值或让子进程继承凭据；原网络/SQLite guard保持，普通文件写入也须fence。只读源仓不能因为`conftest`默认receipt目录而写旧交接，使用已有receipt环境override指向本轮自有路径。

真实junction指向另一个本轮自有目录，观察target文件与sentinelSHA，产品必须在任何staging mkdir/open前exit3。Windows删除始终在同一shell或明确单一API内；核精确绝对路径、ownership、ReparsePoint后非递归删除链接自身，不跟随目标、不字符串拼cmd删目录。Windows PowerShell5的Remove-Item可能抛NullReference；可在已验证链接上用 `.NET Directory.Delete(link,false)`，不能据此禁用保护或清全仓。

终态对自有副本/临时文件建rawSHA/bytes清单，逐项验证路径和无reparse，严格清理，只保留必要结构化产物与原始日志。保留源仓、共享TEMP、CodeGraph、其他进程文件；记录PIDs/退出/实际残留、source与锁定输入前后SHA。运行失败也清理已获所有权的文件，不能把链接目标删掉或删除未获所有权的路径。

## 7. 交接、artifact与commit角色

交付目录唯一为 `docs/handoff/EVID-REF-02/remediation-03/`：

- `handoff.json`沿用原交接schema1.0.0、lane=`iqs`、package_id=`EVID-REF-02`；如总控schema要求字段，以原schema为准，不私造替代。引用本卡授权路径和实际范围。
- `summary.md`、`interfaces.md`、`case-map.md`、`isolation.md`、`artifacts.json`及自有三份PWF；原始stdout/stderr/JUnit/commands/exit/time/PID与清理记录。
- map schema/模板/真实生成命令与一份**实跑正式map**，原锁SHA/bytes和各source/role/path核验记录；`inputs_lock`必须指回原相对路径并保留原SHA/bytes，不以隔离派生锁替代。
- 新版本候选pack/evaluation/summary、来源检查记录与完整请求manifest（如新增），分清real sourcefacts、synthetic测试和legacy迁移；缺口/未测项诚实列出。

artifacts对每个交付文件列相对path、用途/role、原始文件SHA-256、bytes和hash_domain=`working_tree_raw_bytes`。目录hash不能冒充文件hash，Git CRLF差异需区分工作树rawSHA与Git blob，不循环hash自身。原输入前后SHA必须分别记录，不仅抄原manifest；公开文档只保留轻量元数据、状态、计数和短理由，不复制私有来源短文/金融原始输入、网页或财报正文、真实DB或密钥。

提交角色要清晰：实际基线commit、产品commit、最后交接文档commit、观察最终HEAD分别记录完整真实SHA。可以先提交产品，再在handoff写产品SHA并提交交接；不要让handoff内result_commit误称尚不存在的最终HEAD，不因文档commit后进而假称产品漂移。旧Git对象缺失限制继续披露；无授权不增remote，不改Git历史，精确提交本包允许文件，不夹带旧清理回执/基础设施/其他writer成果。

完成后交总控一次验收。不写总控PWF、不派发他人任务、不关闭G3/F05/B01/L03、真实金融gold/模型金融准确率、200家或全池、生产发布。若语义依据仍不足，交付可明确缺证并让准确性not_verifiable；这比人为把参考答案改成正确更符合本包目标。
