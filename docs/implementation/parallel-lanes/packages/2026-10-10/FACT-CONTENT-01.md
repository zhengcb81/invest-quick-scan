# FACT-CONTENT-01｜事实内容、术语歧义与关系语义验收包

唯一工作目录：`C:/Users/郑曾波/Projects/iqs-fact-content-lab`。本轮核查时不存在。人类分派本卡后可新建独立Git仓，分支 `codex/fact-content-01`，首次真实起点commit记入handoff；不加remote、不安装全局技能、不创建服务/研究数据库。目录若已存在且非空，先核owner，不覆盖。

必读：[共同规范](handoff-rules.md)、[输入锁](inputs.lock.json)、冻结 `questions/facts.json`、`schemas/answer-content.schema.json`、`references/standard-output.md`、`docs/implementation/composable-evolution-plan.md`。这些实际输入全在IQS，只读。历史文档关于已实现运行器的陈旧措辞不改变本卡边界，以本批README和PWF顶部为准。无需重做TH-01/IN-02预研，也不依赖EVID-REF-02的新结果。

## 目标与正式实施的区别

原61题已有内容，但未来产业链检索还需要可检查的词义、关系方向、期间、分部、商业化及证据状态。使用设备不等于制造设备，客户不等于下游应用行业，研发合作不等于量产供货，未披露不等于不存在。短词和中文同义名尤其容易拉进错误标的。

本包把这些边界做成**版本化候选内容与语义验收资料**，并提供真实可执行离线校验/导出工具。它支持原F01/F03/F04/F05/F06/V03/V07，不是这些卡正式发布；不绕过G3/C06，不修改正式题库、本体schema或StockWiki。61題保留ID、field、题义、顺序和max_items；候选模块只引用原题，不复制并维护第二题库。

## 写范围与稳定性

本新仓内 `README.md`、`.gitignore`、`pyproject.toml`、`src/iqs_fact_content_lab/`、`schemas/`、`content/`、`tests/`、`fixtures/`、`tools/`、`docs/handoff/FACT-CONTENT-01/` 和自己的临时根。其他一切只读；禁止在其他仓脚本旁生成缓存、报告和__pycache__。用 `python -B`，隔离TEMP与PYTHONPATH。

不做LLM分类、搜索、抓取、关系库、matcher服务或正式F05 strict/explore查询引擎；不改active/release指针，不分配正式新题ID。新题建议可放proposals，用局部candidate_id，交总控判断。现有源题若发现歧义，不直接改文本；给原hash、反例、候选补充和是否改变题义的影响评估。

## 实施步骤

1. 建本包PWF与真实新仓起点，核输入SHA；先RED：漏题/重题/field不符、未定义术语、父子层混并、倒置关系、丢期间/分部、宣称真实来源却无出处、输出路径冲突等。
2. 逐题分析61题的对象类型、必需scope/时期、关系列表、依赖/条件适用、未知/N/A、最小可比较信息。生成61行映射，question原文只用引用/hash，任何不确定映射明确待决。候选分组按通用/公司类型/行业/生命周期/恢复观察，可多轴组合，不能每家公司私改题义。
3. 按问题实际需要整理最小中英文术语集，区分产品/设备/材料/工艺/应用/行业/商业模式/管理职责。每个term有语义类型、定义、父层/细分层、别名和反例；不要为凑数大量造术语。AI、存储、液冷、封装、渠道、平台等多义或短词须明确语境、token边界和不可自动合并项。
4. 整理关系角色规范：公司的产品、所用设备/材料、设备/材料供应方、客户/渠道、产品下游应用、研发伙伴、竞争者、管理者分别列方向/角色/target kind。只用原61题声明的relation code；新code标proposal，不塞进冻结答案schema。
5. 做至少36个独立语义验收case，覆盖不同类型、行业和生命周期；输入为短结构事实/明确synthetic文本，每个预期说明为什么。严格/探索资格是**待生产owner落实的oracle**，不能在Lab发明一套正式查询算法并当F05验证。漏证据/冲突保留unknown，不把所有候选都strict，也不把暂时低谷公司过滤掉。
6. 实现 `validate-pack` 与 `export-cases` 离线CLI；验证映射/引用/候选本体闭合、案例语义标签一致、schema/重复键/非有限值、候选ID与source hash。输出标准Lab case JSON，未来owner可消费相同case测试其实际代码；不伪装StockWiki真实query/golden。
7. 一次集中单元/集成/真正CLI E2E与内容审查；复用源schema对允许的示例答案做shape校验。shape通过与业务关系正确分开报告，生产owner尚无API的case标not_run。固定输入两次新输出根结果一致，篡改输入不会被悄悄接受。
8. 正常commit并交接，清自有测试环境。给总控“如何接到正式F06发布/术语owner/关系F05”的接口映射和变更影响清单；不替总控执行合入或签G3/F05。

## 输出接口：`iqs.fact_content_candidate/1.0.0`

最终 `content/content-pack.json`：`schema_version`、`package_id`、`pack_id`、`created_at`、`input_refs`、`question_map`、`candidate_modules`、`terms`、`relation_roles`、`case_refs`、`proposals`、`unresolved`。严格有界、未知字段/duplicate key/NaN拒绝；pack_id内容寻址，排除自身id，另保存raw SHA。不与正式ModuleRelease/TermRelease的ID或版本空间混用。

| 区块 | 必需字段与兼容约束 |
|---|---|
| question_map | 完整61行、原顺序、question_id/field_id/module_id/source_question_sha256/source文件hash；每行candidate_module_refs、object_kinds、scope_requirements、period_requirements、unknown_rules、case_refs |
| candidate_modules | candidate_id、轴/条件描述、question_refs、依赖/排斥提案、为什么该组共用scope；不包含复制的question body或活发布指针 |
| terms | candidate_term_id、kind、中文/英文label、definition、parent_refs、aliases、ambiguous_aliases、disambiguation、not_equivalent_refs、例子/反例、synthetic或review来源 |
| relation_roles | 原relation code、source_kind/target_kind、方向/角色、scope/时期/商业化/证据必要条件、proposed_only标记；不能偷偷等同上下游位置与已成交关系 |
| proposals | 局部candidate_id、原题/术语hash、问题与反例、建议、题义/路由/历史可比性影响；不得分配正式题号或宣布兼容 |

`source_question_sha256`仅绑定原facts.json的单个question对象：UTF-8、JSON键排序、ensure_ascii=false、separators=(',', ':')、allow_nan=false的SHA256；数组顺序保留。它不是生产question_semantic_hash，不伪称已有事实发布包。`pack_id`使用同样规范域并排除自身id，prefix为`factcand_`。

单个case格式 `iqs.fact_semantic_case/1.0.0`：case_id、fixture_class、question_refs/input_sha、source_facts（有界结构数据）、scope/period、terms/relations候选引用、expected_labels、reason、negative_variant、production_case_status。

`fixture_class`区分synthetic/historical_structured_answer/real_source_excerpt；本包零网络，默认synthetic，不给虚构公司冠真实owner资格。真实资料只能引用输入锁中的已有原件，缺正文不可重建。expected_labels至少分别给 `relation_supported`、`strict_eligible`、`explore_eligible` 的 `true/false/unknown` 与原因；strict未知不能被自动改false=不存在，explore也须显示待核和分部/期间。

案例不是输入生产adapter的完整Observation，不能造exec_key/actual_model/send receipt/AnalysisSubject。导出用本包具名case envelope并保留原input hash，owner正式接口未到则明确未映射。

## 必须覆盖的内容验收case组

| Case组 | 至少要区分的语义 |
|---|---|
| FC-01 | 61题全覆盖且原ID/field/题义不变；候选多轴组合不重复同题、银行/保险/REIT/未商业化适用条件保留 |
| FC-02 | 使用设备/生产设备/设备供应方；购买材料/制造材料/材料供应方，各有正负例 |
| FC-03 | 直接客户/经销商/终端用户/产品应用/下游细分行业，不能从行业背景推公司供货 |
| FC-04 | 在研/验证/试产/量产/商业收入；拟合作/签约/实际销售，potential不等于已获益 |
| FC-05 | 集团/子公司/分部/地区；A/H多挂牌不是多家公司；近名不能由文本自动合并身份 |
| FC-06 | 当前/历史/失效关系，期间未知与没有关系不同；第二曲线不要吞掉第一曲线经济来源 |
| FC-07 | AI短词/token边界、英文缩写、同音/同名、多义词；父行业命中不得冒充细分业务命中 |
| FC-08 | 未披露/明确否定/证据冲突/缺来源，三值闭合；strict与explore分开，不靠score补证据 |
| FC-09 | 临时周期低谷/自身经营修复与结构衰退；保留恢复观察所需竞争优势/触发条件，不自动刷高分 |
| FC-10 | 管理层职位/控制人/激励/承诺与实绩，描述不等于治理结论；供应商/客户清单保留角色与时期 |
| FC-11 | 未定义term/不合法relation/环形父层/冲突alias/错direction/丢scope/date/重复键/未知版本等输入错误拒绝 |
| FC-12 | 实际CLI重复新根输出稳定；现有输出/越界/篡改拒绝；源SHA不变，0网络/费用、临时与进程清干净 |

每组至少包含独立正例与有鉴别力负例或unknown例，总量至少36。case reason是内容设计依据；还须集中审查其语义，不能测试“oracle与它自己相同”就说关系正确。生产owner未来运行这些case的结果另列not_run，不混进本包软件通过数。

## 目标CLI、退出码和留档

```powershell
$env:PYTHONPATH = 'src'
python -B -X utf8 -m iqs_fact_content_lab validate-pack --input content/content-pack.json --inputs-lock <本包只读输入锁>
python -B -X utf8 -m iqs_fact_content_lab export-cases --input content/content-pack.json --output <本包内不存在的新目录>
python -B -X utf8 -m pytest tests/ -q
```

这些是待实现目标，不是已跑测试。0=验证/导出成功；2=输入schema/重复key/版本/hash漂移；3=输出已存在/越界；4=内容引用/61题映射/语义内部约束不闭合；5=用法；6=网络或秘密访问尝试；系统意外1。所有输入写前校验，输出exclusive，案例数据有界，路径不跟随外来reparse。

交[共同规范](handoff-rules.md)要求的全部文件，并加 `content-pack.json`、`question-map.json`、`semantic-cases.json`、`ambiguities.md`、`coverage-matrix.md`、`production-adoption.md`。交接必须说明candidate pack需要总控怎样映射到正式模块/本体/owner算法，哪些是题义变更，哪些仅别名/例子，不伪称已接入。软件/内容工程完整可complete；F01/F03/F04/F05/F06、G4、TH/IN正式消费者仍保持原门。
