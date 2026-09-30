# 分类与组合

## S06 v2 请求、决策与导出（候选待审）

`scripts/routing.py` 负责离线请求组装、证据到模块的决策、冻结快照与执行前检查，不建模型客户端或公司数据库。`question_sets.py` 的 `compose_from_route` 与新CLI消费已验证的v2快照；直接 `compose` 也执行相同门禁。现有 `ROUTE_01`、严格 `validate_profile` 及S02答案消费回归保留。v2的部分分类或多业务输入不能伪装成旧profile绕过检查。

- `publish_routing_package(root=..., renderer_version=..., renderer_rules_sha256=..., activate=False)` 发布候选包。唯一编辑源为 `questions/routing-policy.v2.json`；48个既有模块全部列明谓词、证据标签、置信门槛与必需题。策略按字节 SHA-256 归档到 `questions/releases/routing/`，release v2 锁住路径和 hash，package 再锁住 release。更改策略必须升 router 版本；未激活候选不改 `current.json`。旧 S05 包仍可读取。
- `build_route_request(identity_context, package_id=..., root=...)` 返回`ROUTE_02`候选问题、package/release/policy身份和精确prompt hash；请求保持StockQA native外层字段形状。`parse_route_response`解析原生路由回答并保留独立分类置信度；`stockqa_adapter.py`消费公开`stockqa.quick_scan_result/1.0.0`结果，核对实体、问题、已完成搜索、实际/请求模型、来源归属及答案SHA-256回执，再交给本地路由/组合入口。分类score绝不进入企业评分；router 2.0—2.2历史形状按各自版本只读兼容。
- `resolve_route_decision(route_input, package_id=..., route_response=..., execution_receipt=..., user_policy=..., previous_decision=..., expected_previous_decision_id=..., now_utc=..., root=...)` 接受已由调用方确认的实体/证券/截止日、可信 `verified_facts`、完整原始模型回答，以及旧式原生回答需要单独提供的执行回执。resolver 自行解析回答，并由同一回答派生候选、分类置信度和答案SHA-256；不接受调用方拆开的候选/置信度/hash 字段。StockQA公开结果中的绑定回执与答案必须成对使用，单独重复传入的回执必须与其完全相同。每条客观候选保留 entity-bound 来源、理由、分类证据类型、原始重大性输入、周期位置及事件/连续期数。`searched_llm`候选的每个URL必须逐字存在于该回执`search_receipt_id`所选、`completed/search`调用的`web_search_calls[].source_urls`；空集、错误调用或未匹配来源仅记录待核缺口，实际派发收窄为common和必需风险题。固定时钟与候选语义相同的情况下，候选顺序不改变模块选择、eligible集合或派发语义；由于原始回答字节不同，答案哈希和封存决策身份仍会不同。`identity_ref`、已核实事实、回执与用户授权必须由上层受信任入口提供；本模块不通过访问 URL 验证其内容。
- `validate_route_snapshot` 验证封存内容、政策包、来源、模型请求、scope/profile、必需题和派发状态，保持历史可读。归档 router 2.0 的旧搜索回执没有 `web_search_calls`，按其原发布包和旧回执契约只读验证；router 2.1/2.2历史快照继续按原契约验证；所有新发布版本都必须把每条模型来源绑定到完成的搜索调用。`resolve_route_decision` 不再用 router 2.0 旧包创建新决策，`validate_route_for_execution` 和 `compose_from_route` 也拒绝把旧决策重新派发。`validate_route_for_execution(now_utc=..., expected_decision_id=...)` 另外检查执行时的手工覆盖 TTL；到期瞬间拒绝新执行。生产入口应提供独立存储的 `expected_decision_id`，仅自报 hash 不能证明来源可信。legacy v1 仍走 `module_contract.validate_route_decision`，不能伪装成 v2 策略运行。
- `enforce_route_budget(decision, maximum)` 对已验证快照检查24核心加必需题预算；`profile_from_route` 是数据投影，`diff_routes` 是相同实体/分部的新旧模块差集。它们不替代入口验证，也不写任务、答案或费用。

`question_sets.compose_from_route(decision, output_dir, now_utc=..., expected_route_decision_id=..., answer_format="screening-1", max_questions=...)` 派发快照允许的模块，强制必需风险题优先于可选题。manifest保存整个route、精确policy/package绑定、原执行时间和独立expected ID。历史manifest只用封存的原执行时间和ID做读取校验（`validate_recorded_route_execution`），不会因此重新授权派发；重新导出走`validate_route_for_execution`并拒绝任何非当前router版本，即使旧manifest仍可读取。

从项目根运行以下离线入口；身份、模型回答、搜索回执和用户授权由调用方提供，CLI自身不联网：

```powershell
python scripts/question_sets.py publish-routing
python scripts/question_sets.py routing-v2-request --identity identity.json --module-package-id "<包ID>" --out-dir route-request
python scripts/question_sets.py resolve-route --input identity.json --module-package-id "<包ID>" --candidate native-answer.json --execution-receipt receipt.json --now-utc "<可信UTC时间>" --output route-decision.json
python scripts/question_sets.py compose-route --route-decision route-decision.json --now-utc "<可信UTC时间>" --expected-route-decision-id "<独立保存的决策ID>" --out-dir scan-questions --max-questions 30
```

`--candidate`是为兼容既有CLI保留的参数名，文件内容必须是完整的ROUTE_02原生回答，或完整的`stockqa.quick_scan_result/1.0.0`公开结果信封；不得只传拆出的`candidate`对象。公开StockQA结果自带其执行回执，通常不再传`--execution-receipt`；旧式原生回答才需要与原始答案哈希匹配的独立回执。`publish-routing`默认只归档，不切换current；没有成功搜索结果时省略candidate/receipt，可从`--input`中的可信verified_facts生成通用或已知风险问卷；不把失败模型自由文本转为已核实事实。已有输出不覆盖，改变日期或路由使用新目录。

执行入口必须提供从调用方可信状态独立读取的`expected_route_decision_id`。路由的内容哈希可发现快照内容变化，但因为任何人都能重算，它本身不证明来源标签或模型出处真实；不能从待执行快照自身取expected ID。

v2 默认重大行业进入条件为收入、毛利或投入资本一项占集团至少15%；已承诺资本开支或有约束力订单至少20%，存续关键性或有证据的重大事件也可触发。原模块在10%—15%区间保留；三个可比基础分母均低于10%、连续两次年度披露且无战略/存续触发，才退出。缺分母标 uncertain。商业化前公司可用已核实的主要开发项目，禁止捏造收入占比。类型/主阶段切换需两期确认或明确重大事件；`cyclical` 永远是正交周期轴。所有门槛和例外随策略版本封存。

三项及以上重大行业在quick返回`requires_full_or_segments`，保留全部候选；full只有明确`compatible_business_scope=true`才允许同实体展开，不兼容边界进入`requires_segments`。任一必需主轴缺证据、低置信或冲突时，router 2.3返回`ready_common_and_risk`，`eligible_module_ids`只含common及必需风险模块；其他有来源的分类仍保存在module_decisions供复核，不借用另一轴的确定性扩大派发。若已选模块依赖未选、被拒绝或仍不确定，或选中集合存在无向冲突，则返回`needs_review`、空`eligible_module_ids`，公共compose入口在生成问题文件前拒绝；缺失模块和依赖环由锁定release校验阻断。重复业务标签同样收窄并保留业务待办，不创建segment ID。缺搜索且无可信已知业务证据时仅common确定，不补operating/mature/other；已有可信困境证据仍保留风险题。

困境可以叠加 scaling，低谷可以叠加 mature。distressed 触发两道困境题及四道恢复题，预算至少30；周期低谷等单独恢复触发要求四道恢复题，至少28。仍有客观触发时，手工否决恢复或已证实困境会明确拒绝，不静默覆盖授权也不删除必需风险题。新增投资视角只允许显式用户授权及 TTL，模型不能自动启用。

## 分类只是选题输入

router 2.3将ROUTE_02外层`status/score`作为独立分类置信度封存到route决策和execution回执；当前策略schema 1.3.0、request protocol 3，最低分仍为7。分数低于7时，仅对`searched_llm`推断的适用候选标记`uncertain/overall_confidence_below_threshold`并排除出模块派发，独立传入的`verified_facts`不受影响；未运行模型时明确记录`not_run/null`，未知/证据不足必须是`null`且空候选。达到阈值仅允许继续评估，不绕过每个模块自己的证据类型、置信度、重大性、连续期和冲突门。StockQA公开结果必须将ROUTE_02答案SHA-256与execution receipt逐题绑定；执行同时核验调用方独立保存的decision_id。快照验证器重算分数资格、回执一致性、覆盖缺口及可派发模块；router 2.0—2.2快照仍可只读，但不能创建或执行新任务。

通过 `question_sets.py routing` 生成一个上游兼容的“分类结论证据充分度”评分问题，使用同一个已验证联网的 StockQAbyLLM 提供商回答。其评分是路由置信度，绝不纳入企业质量分。

路由必须有截止日内的证据支撑：公司官网／交易所实体信息，以及业务构成或主要利润与资产来源。输出最小 profile，格式见 `examples/profile.json`。无法辨认实体时先停止；行业或阶段不确定时给出候选与缺口，先运行 common 通用模板，不能伪造精确分类。

`company_type`、`industry_modules`、`stage` 等 ID 来自 `questions/catalog.json`。只保存路由所需事实，不提前生成完整行业描述、供应商表或客户表。

## 选择顺序

1. **类型恰好一个。** 金融资产负债驱动选择 bank；保险责任驱动选 insurer；资管、券商或市场基础设施选 capital_markets。持有物业选 property_owner，开发销售选 property_developer。多种重大业务或投资控股选 holding。未规模商业化选 pre_revenue，其他已有实质经营收入选 operating。
2. **行业零至两个。** 金融类型、纯物业和控股平台可以不加行业，因为其类型题已承载行业机制；其他类型至少匹配一个。经营混合公司按核心经济驱动选一主一辅；收入并非唯一权重，利润、资本占用和存续风险同样重要。两个行业需要在 `routing_rationale` 解释。找不到匹配则用 other 并披露覆盖不足，不能为了覆盖所有行业而宣称无差别适用。
3. **成长阶段恰好一个。** validation、commercialization、scaling、mature、turnaround、declining。公司年轻不代表高分；成熟不代表衰退。阶段应由商业验证、单位经济、扩张方式与现金特征决定。
4. **周期性独立判断。** `cycle_sensitive=true` 另加 cyclical 模块。公司可以同时是成熟公司和周期企业，不能把“周期”与“成长阶段”混为一谈。`cycle_position` 写明上行／高位／下行／低位／不明及证据，标签本身不计分。
5. **重要属性按需叠加。** cross_border、controlled、listing_structure、concentrated、acquisitive、subsidized、distressed、recent_listing。纯海外挂牌不自动触发跨境经营风险；国资、家族或双重股权身份不自动扣分。quick 最多两个属性；更多均重要时用 full，不静默删掉困境等重要问题。
6. **工具按问题选择。** 默认 `diagnostic_modules=[]`。需要解释回报来源时可选dupont，需要厘清竞争结构时可选porter；每个模块都要在 `diagnostic_rationale` 对象中写出具体待解决问题，例如 `{"dupont":"ROE提高是否主要来自回购后权益缩减"}`。它们不是由行业标签自动触发的必答题。
7. **困难与恢复单独辨识。** 周期下行/低谷/初步修复、暂时经营困难或衰退性质不明时，给`recovery_review=true`及`recovery_rationale`，追加4道recovery诊断；不要求先证明反转成功。turnaround、declining及distressed属性自动触发。成熟周期企业不必改成turnaround，股价下跌也不等于经营低谷。手动选recovery须有诊断理由，与自动触发去重。具体评分与观察状态见[恢复观察](recovery-watch.md)。

多业务集团的分部画像应另建 profile 并标注分部边界。对各部分单独评分，母公司侧重资本配置和资金安全。无可靠分部证据时降低覆盖率，不算机械的集团综合平均数。

## 拼装与去重

- 先读全部24道 `IQS_` 通用核心题，类型题的 `replaces` 替换单位经济、现金、资产真实性、偿付或估值等特定口径，杜邦和五力另行选择。
- quick选所有priority=1和关键核查题；若它们替换一道通用题，就删除原题。priority=2的类型替换题若其对应通用题已入选，也自动入选。关键核查属性会传给替代题，不能通过切换行业避开资金生存或真实性核查。
- 先对已选模块递归补齐完整`dependencies`闭包，再进行题目拼装；依赖必须属于锁定release且图无环。依赖缺失、未决或其闭包引入冲突时返回`needs_review/blocked`并在发包前停止。
- `conflicts`只约束本次已选模块组合：release目录可包含互斥备选；已选集合中任一方向声明的冲突都按无向冲突处理。不能仅因互斥备选共存于目录而拒绝整个release，也不能因冲突只单向声明而漏掉拒绝。
- 行业、阶段和属性题是补充而不是额外的整套质量权重。同一事实可以作多题证据，但不同题需解释不同机制；不要将“客户续约”“客户粘性”“转换成本”改写后当成三份独立优势。
- manifest 记录已选模块、题号、替换映射、实际题数和源文件哈希。相同版本与 profile 可复现相同问题；采用新的截止日创建新输出目录，不混用旧缓存。
- 2.0.0版本核心题改为IQS_编号，与旧COMMON_题不逐项映射历史分数。旧运行保留原manifest，不能重新命名后拼到新画像。
- 2.1.0新增恢复诊断与观察状态；4道恢复题不进入质量均分。生成当前profile应明确recovery_review；旧profile未给时仍可运行，仅按stage/overlays自动触发，不能从自由文本周期位置猜出确定低谷。

## 地区与口径

覆盖按交易所和经营实质识别，不限 A/H/美股，也支持欧洲、日本及其他地区的普通上市企业。搜索当地语言／英文的实体别名，优先所在监管体系和公司自身的公开口径。记录会计准则、报告币种与财年末；不将不同财政年度、币种、ADR比例、股权范围直接混用。

监管指标按当地适用定义引用，不能把某一地区的资本充足标准、REIT分配要求、审计制度或税率硬编码为全球阈值。小公司和披露有限市场使用同样证据门槛，缺资料体现为覆盖率与置信度下降，不直接判经营质量差。
