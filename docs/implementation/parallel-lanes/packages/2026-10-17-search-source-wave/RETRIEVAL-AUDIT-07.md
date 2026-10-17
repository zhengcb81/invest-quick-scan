# RETRIEVAL-AUDIT-07：检索证据质量的人工盲审协议与离线对比工具

唯一可写根`C:/Users/郑曾波/Projects/iqs-search-annotation-lab`，包`iqs_retrieval_audit`。阅读共同施工/独审要求；根开工复核。全离线，0API/下载，不要求取得总控这轮搜索结果。三个新包互不依赖，不能写其他仓库。

## 与现有工作明确分工

本包只评**搜索返回的有限证据能否定位、覆盖、支撑预先规定的检索目标**，不评LLM答案、1–10分、投资结论或真实金融充分性。不复刻REVIEW-CAL-06合成金融答案校准、原JUDGE/scorer、匿名任务系统或新任务回执；工具是无状态显式输入/输出的research候选。冻结IQS允许背景文件即可，不读T4答案/费用/模型标签/private。最终真实供应商比较由总控在另冻材料上用本协议，不由本包造出结果。

## Rubric和内容

交`content/rubric.json`及人类可读指南，至少20个实质不同synthetic标注案例，至少8组成对变化（只变身份、时点、原始性、支持范围、重复来源或缺失等关键要素）。全例显式synthetic，`.invalid`地址不能伪装真实官方URL。预期只能是校准解释/允许争议，不当金融gold；不能用“所有标签皆可”刷100%。

每个检索task包含独立target_id、issuer_ref/status、as_of、claim_or_information_need、required_dimensions、bounded_source_items。source item沿已发布短证据字段`source_id/title/publisher/url/published_at/retrieved_at/short_snippet`，附可选provider_record_ref、source_kind、document_date_semantics、independence_group、supporting_locator；未知null。不得含LLM答案或模型/成本/速度/供应商排名。

标注单位为`target×source`，另有target级coverage，不拿source条数当覆盖。维度至少：entity_match、temporal_eligibility、primary_source_status、claim_support、dimensional_completeness、independence、snippet_sufficiency、conflict_handling、prompt_injection_present。每维有明确枚举和unknown/not_applicable原因，claim_support=`supported/partial/contradicted/not_assessable`；标注rationale与source_id/必要短引文绑定。只有片段看不出发布日期时不能凭抓取日猜；原始来源高质量不等于其自述已证明护城河。

## 匿名化的真实边界

assignment删除供应商/路由/模型/价格/耗时标签，原始请求ID/响应水印不公开；稳定随机anonymous IDs和private一一映射分离。**不能删改URL、发行人名称、事实、日期或引文来追求完美盲化**，因为这些是审查依据。URL/摘要可能暴露搜索风格或查询，必须在limitations记录“供应商标签盲化，不保证不可推断”，不得称双盲。模型不应看到private map/预期。原供应商排序与计数可按显式seed打乱，同时private保留原序；相同原始source出现跨组不自动当独立。

业务protocol：`iqs.retrieval-rubric/1.0.0`、`iqs.retrieval-public-assignment/1.0.0`、`iqs.retrieval-private-map/1.0.0`、`iqs.retrieval-annotations/1.0.0`、`iqs.retrieval-audit-report/1.0.0`。每种有schema及共同context/qualification。public、private及输入bundle逐项内容绑定，不能信自报hash。对外公开assignment不含expected、来源case名、pair_id或正负提示性ID。

## API与CLI

```python
def make_assignment(retrieval_bundle, rubric, *, seed, expected_context) -> dict: ...
# 返回 public_assignment/private_map；不调用任何agent或API。
def validate_annotations(public_assignment, annotations, rubric, *, expected_context) -> dict: ...
def compare_annotations(public_assignment, private_map, annotations_a,
                        annotations_b, rubric, *, expected_context) -> dict: ...
```

CLI `python -m iqs_retrieval_audit validate --inputs ... --lock ... --expected-lock-sha256 ... --bundle ... --rubric ...`；`assign`加`--seed --output <新根>`输出`public/assignment.json`和`private/map.json`；`compare`显式接`--assignment --private-map --annotations-a --annotations-b --rubric --output <新根>`及共同锁参数。独立评审者只收到public与rubric，不能先看private/expected。

report给计划/收到/重复/未知/缺失targets和逐维分母，分别列unknown/not_applicable/分歧/待裁决；两人一致不等于事实正确。可给一致性计数，第一版不编造加权综合准确率、供应商赢家或真实Kappa；不存在的实测成本/耗时全null。单人标注不冒充两人一致；缺少B标注可生成pending checkpoint，不伪造B完成compare。

## 集中测试与交接

先定义rubric/成对预期→schema/匿名化RED→实现薄工具→补足案例与完整测试→一次整包独审。至少验证：错主体/未来时点/日期unknown/同源重复/部分支持/注入文本；public泄露provider/expected/原case提示拒绝；URL等实质证据完整；错private map/重复或外来ID/改内容仍自报旧hash/重复JSON键/版本及路径边界拒绝；缺标注列真实缺口不判正确。

集成用自己明确synthetic且独立编写的A/B标注验证一致/分歧/缺失，不能称真实LLM评测。CLI E2E validate→assign→compare，搬迁/任意cwd成功，篡改/已有输出安全失败；网络/secret/外写隔离和清理按共同契约。实际独审者逐案例及rubric检查预期/匿名化边界，实跑公开链/反例；修复所有有效发现复审passed后交`docs/handoff/RETRIEVAL-AUDIT-07/`，绑定最终payload和input lock。该工具是否接入本轮实测由总控以后显式决定。
