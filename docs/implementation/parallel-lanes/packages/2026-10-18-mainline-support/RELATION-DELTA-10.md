# RELATION-DELTA-10：产业链关系的跨时点观察变化候选

唯一写根 **C:/Users/郑曾波/Projects/iqs-relation-delta-lab**；branch `codex/relation-delta-10`；module `iqs_relation_delta`。先读 [共同契约](integration-contract.md)、[输入清单](input-catalog.json) 的本包段。不写 StockWiki identity/query/关系表，不把关系变化推断成收入或分数变化。

## 目标与分工

用户需要用多次扫描构建产业链数据库。第二次没有搜到某个客户，可能只是搜索覆盖变化，不能被 UI 自动写成客户流失；同名供应商也不能靠名称合并。本包对两个冻结的事实回答生成保守变化候选和完整对照分母。它不核官网新来源、不重复 CHAIN-VERIFY，不建另一身份映射器，不做生产 query 历史比较或数据库迁移。

## 输入与公开边界

输入 `iqs.relation_delta_request/1.0.0` 闭合 required `protocol,before_ref,after_ref,as_of_date,matching_policy`。before/after 引用本包 snapshot。matching_policy 只可 `exact_explicit_identity_v1`，不提供模糊名称自动匹配。

snapshot `iqs.relation_observation_snapshot/1.0.0` 闭合 required `protocol,snapshot_id,data_kind,subject_ref,question_ref,information_as_of,observed_at_utc,model_provenance,answer_ref,item_refs,termination_assertions,coverage_statement,limitations`。data_kind=synthetic|unqualified_export；subject_ref 结构同 SUMMARY 卡但本包独立定义；question_ref 含 question_id/field_id/question_version/definition_sha256。answer_ref 必须指锁定原 answer schema 合法对象；item_refs 每条 `item_id,pointer,item_sha256,identity_scope`；pointer 指原 answer.items 数组元素，item_id 仅本快照局部定位。

item_refs 必须是原 `answer.items` 的**完整一对一覆盖**：N个原item恰好N条，pointer 的集合严格等于 `/items/0`…`/items/N-1`，允许引用行顺序改变，不允许漏项、同pointer不同ID重复、重复item_id或同ID指不同item。N=0时只允许空 item_refs。item_sha256 使用原 module_contract canonical_bytes 规则（UTF-8、sort_keys、紧凑分隔、allow_nan=false）对所指原item重算；仅此通用 JSON 规则在本包作为 wire 定义实现，不复制原模块/路由算法。answer.question_id 必须等于 question_ref.question_id；question_ref.field_id 必须能在锁定 facts.json 中找到该题且一致。原答案与 wrapper 信息日必须一致。任何上述不一致都作为非法输入 exit2 拒绝，不能删掉问题行再报剩余集合通过。before_total/after_total 必须从验证后的原 answer.items 长度得出，不能从过滤后的 item_refs 或配对结果反推。

identity_scope 闭合 `authority,entity_id,business_unit_ref,confidence`；authority=synthetic_fixture|caller_unqualified；entity_id nullable；business_unit_ref nullable；confidence=explicit|unresolved。canonical_entity_id 与 identity_scope.entity_id 不一致必须拒绝。只有 confidence=explicit 且 entity_id 非null才可进入 exact 配对；confidence=unresolved 即使携带同样的非空ID也必须归 unresolved、reason=identity_unresolved，不借“已有一个ID”升级可信度。business_unit_ref 非null时必须为调用方明确提供的稳定单位ID字符串，不能从名称/segment文字猜生成；只有confidence=explicit才表示该ID的范围同样明确。null只表示源没有声明独立business unit，键保留null，不代表所有分部相同；item.segment/subject scope差异仍不合并。非 null ID 只是精确候选配对键，不是本工具认证为 StockWiki 身份。名字/aliases 只展示，不能作为可自动匹配的唯一键。

termination_assertions 每条 `assertion_id,item_ref,asserted_end_date,evidence_ids,source_pointer,status`；status 只可 `caller_asserted_unverified`。原 valid_to 若存在也只是源中声明的观察边界，不能据此给正式 terminated。coverage_statement 闭合 `status,limitations`，status=complete_claimed|partial|unknown；complete_claimed 是调用方说法，不是工具核定完整。

```python
def compare_relations(request: dict, *, input_root: Path, source_root: Path, lock: dict) -> dict: ...
```

CLI `python -B -X utf8 -m iqs_relation_delta compare --input request.json --input-root fixtures --source-root vendor/iqs --lock inputs.lock.json --output runs/delta-01`，另共同 validate/evaluate/version/help。不读取原 SQLite/动态身份 API，不执行搜索，读到不支持的协议明确拒绝。

结果 `iqs.relation_delta_report/1.0.0` 使用共同 result 顶层；payload 闭合 `before_snapshot_id,after_snapshot_id,comparison_scope,status,comparison_failures,matched,only_before,only_after,unresolved,counts,required_followup`。

- status=comparable_observation_candidates|scope_mismatch|method_changed|information_out_of_cutoff|cutoff_not_ordered。comparison_scope 闭合为 `before_subject_ref,after_subject_ref,before_question_ref,after_question_ref,requested_as_of_date`，保留两边原件。
- `as_of_date`/两 information_as_of 均为真实 Gregorian YYYY-MM-DD 日期。它是本次允许的最晚信息截止日，要求 before.information_as_of <= as_of_date 且 after.information_as_of <= as_of_date；任一超出则 information_out_of_cutoff。before.information_as_of >= after.information_as_of（相等或逆序）则 cutoff_not_ordered。observed_at_utc 是采集时间，可晚于 as_of_date（合法回溯采集），不能替换 information_as_of 或据此把历史信息判未来；它须是UTC有效时间戳，但不参与上述信息截止资格。
- scope_mismatch 当且仅当 subject_ref 的 entity_id/scope/security_id/segment_id 任一不同。method_changed 当且仅当 question_ref 的 question_id/field_id/question_version/definition_sha256 任一不同；这里采用保守的版本严格相同规则，不能仅因为题面相近就等同。不同模型不触发 method_changed，保留明细并标 required_followup=model_changed，不直接认定业务改变。
- 所有 schema/hash/一对一覆盖/字段绑定错误首先作为非法输入 exit2拒绝；在合法输入之上，comparison_failures 列出实际发生的所有比较失败原因，固定排序为 scope_mismatch、method_changed、information_out_of_cutoff、cutoff_not_ordered。非空时 status 取这个顺序第一项，空时才 comparable_observation_candidates。任何比较失败时 matched/only_before/only_after 都为空，两侧每个原item各在 unresolved恰一行、reason取主status，并在 comparison_failures 和 required_followup保留其余原因；禁止因只检查首个失败条件丢掉另外证据。
- 比较资格满足后才做 item 级规则，固定主reason优先级 identity_unresolved > missing_identity > unsupported_relation > ambiguous_key；两侧独立守恒，所有适用附加解释放limitations，不删item。exact match key=`subject_ref/entity+scope+segment,field_id,relation,role,identity_scope.authority,entity_id,business_unit_ref,item.segment`；entity_id null 一律 unresolved；前述confidence=unresolved规则优先于ID存在。商业阶段/描述/日期属于变化字段，不加入稳定配对键；同键多项形成 ambiguity，不挑第一项或合并。母公司与子公司不匹配，equity/customer/supplier 关系不同也不配对。
- matched 每项 `before_item_id,after_item_id,key,classification,changed_fields,limitations`；classification=unchanged_observed|attributes_changed_candidate|end_date_asserted_candidate|conflicting_observation。changed_fields 逐字段原值/后值/pointer。未来结束日期、商用阶段由 pilot→commercial、多个相反声称等分别列，并声明未认证。符合 interval 的比较只评源自述区间，不给 verified_active=true。
- only_before 每项 `item_id,classification,limitations`，classification 固定 not_reobserved；即使新 coverage complete_claimed、搜索返回零条或原 valid_to 已过，也不得输出 lost_customer/terminated。明确 termination_assertion 时额外展示 end_date_asserted_candidate，但保持 not_reobserved。
- only_after 每项 `item_id,classification,limitations`，classification 固定 newly_observed；不是 newly_started。unresolved 每项 `side,item_id,reason,limitations`，reason=identity_unresolved|missing_identity|ambiguous_key|scope_mismatch|method_changed|information_out_of_cutoff|cutoff_not_ordered|unsupported_relation。counts 闭合 `before_total,after_total,matched_pairs,before_only,after_only,before_unresolved,after_unresolved`，从原items得出的前后分母各自独立守恒，不把两侧 item 混成公司家数。

required_followup 是固定 reason-code 数组（identity_owner_resolution/source_confirmation/model_changed/scope_changed/method_changed/information_out_of_cutoff/time_inconsistent/coverage_gap），按此枚举顺序去重输出；比较失败各自映射 scope_mismatch→scope_changed、method_changed→method_changed、information_out_of_cutoff→information_out_of_cutoff、cutoff_not_ordered→time_inconsistent。不输出可执行重试/写库命令，不授任务权限。公司名称原文保留，不能把括号/简称相似自动当同一法律实体。

## 内容与测试

1. 冻结输入，自建不少于 24 对 fixture，全部合成/虚构。事实关系值从锁定 facts.json 的字段允许集合中读；使用原 answer schema 校验 item，不另造不同生产关系类型。跨关系变更保留两端，不当同键覆盖。
2. 正常对照：相同实体同关系重观测；相同数据变 item 顺序；相同实体更名但 ID 和身份范围不变；阶段/分部明确变化；新记录更早开始时间但本次才观察；重复 source 不影响 item 分母。
3. 防误判：缺 identity；同名不同 ID；同一非空ID但confidence=unresolved不得配对及两侧explicit的正常对照；中微公司/中微半导体采用明确 synthetic 不同 ID；一家公司 A/H 两挂牌同实体仍同关系对象；parent/subsidiary/business-unit；相同 ID 两条冲突；名字缩写相近不能配；旧有新缺且 coverage partial/unknown/complete_claimed 三对；计划合作→实际供货需 source_confirmation；valid_to 过去/未来；asserted termination 无核证；information_as_of超过请求as_of；cutoff逆序/相等；采集时间晚于as_of但历史信息合法的正例；模型改动；题目定义/版本/关系类型改变；主体范围改变；scope+method+future+逆序同时发生时主status与完整comparison_failures排序固定。
4. 单元：所有配对/不配对/时间和分母守恒，期望根据明确规则手工锁定。集成：标准答案 schema→snapshot 指针/hash→compare，不从测试 expected 读分类；至少两个不同行业形态和多供应商/客户集合。
5. E2E：真实 compare→validate→evaluate，随机 cwd/中文空格/输入顺序打乱、坏引用/重复键/错日期/hash 不符、原子拒覆盖。必须通过公开CLI证明漏掉一个item_ref、两不同item_id指同一pointer、重复item_id、answer/question不一致均exit2且无正式结果；行顺序改变且一对一仍完整时正常通过。证明 `not_reobserved` 永不变 terminated、`newly_observed` 永不冒新签订单；所有外源 bytes 保持、请求0、清理自有临时根。

交带规则依据的 casebook、合成 snapshots/answer/items、测试预期分离、schemas/src、完整测试日志和共同交接。integration-map 列总控需要的 owner 输入字段/保守输出消费方式及正式身份/事件审核仍在 owner 的边界。独立 reviewer 必须全面审配对规则和每类案例，编写至少两个未见歧义/覆盖变化反例；修完有效发现后复审 passed 才交接。
