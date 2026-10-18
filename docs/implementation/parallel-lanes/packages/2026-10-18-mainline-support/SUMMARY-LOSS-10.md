# SUMMARY-LOSS-10：企业快扫摘要的保真与遗漏测试工具

唯一写根 **C:/Users/郑曾波/Projects/iqs-summary-loss-lab**；branch `codex/summary-loss-10`；module `iqs_summary_loss`。先读 [共同契约](integration-contract.md)、[输入清单](input-catalog.json) 的本包段。不写摘要生产引擎、scorer、owner、Viewer 或其输入历史。

## 目标与边界

真实摘要要便于横向/时间/模型对照，但缩短信息容易抹掉 unknown、过期、周期低谷、恢复触发条件和来源模型。本包提供**确定性字段保真/覆盖核查**和完整测试集；总控将它用于真实摘要验收。工具不生成摘要、不调用模型、不评自由文本含义、不授金融准确率，不重复 CLAIM-GUARD 的指标口径/证据蕴含判断。

设计公开 sidecar，让生成器在摘要每个可核 claim/block 标原输入 JSON pointer。只核指向的字段存在、值和状态是否保留、关键字段是否得到覆盖；自然语言是否准确表达、引用是否真正支持仍 manual_review_required。工具不能因引用存在或关键词出现宣称整句正确。未提供追溯信息的普通文本也是合法输入，结果 unassessable，不故意设计成只有自家摘要才能通过。

## 输入、API 与协议

`iqs.summary_loss_request/1.0.0` 闭合 required：`protocol,source_ref,summary,coverage_policy_ref`。source_ref 指包内冻结的标准答案或 wrapper，必须经锁定 answer schema 及本包 envelope 验证；生产 owner 报文不在本卡范围。source envelope 闭合为 `protocol`=`iqs.summary_source/1.0.0`、`data_kind`=synthetic|unqualified_export、`subject_ref,information_as_of,observed_at_utc,model_provenance,answers,limitations`。subject_ref=`entity_id,scope,security_id,segment_id`，不把这些 caller 值认证为 owner 身份。answers 每项原始 answer 对象/hash/题目和字段 ID，保留源 answer schema，不私改。

summary 闭合：`text,blocks,traceability`；text <=12000 Unicode 字符；blocks 数组每项 `block_id,text,claims`；每 claim `claim_id,kind,source_pointer,rendered_value,rendered_status`。kind=verbatim_scalar|status|qualifier|free_text；pointer nullable；rendered_value 是 JSON 原子值/nullable；rendered_status nullable。traceability=provided|absent；absent 时 blocks 可为空。禁止让渲染字段自报 supported/financially_correct。

coverage policy 闭合 `protocol`=`iqs.summary_coverage_policy/1.0.0`、`policy_id,version,required_pointers,optional_pointers,limitations`；每 required 项 `pointer,reason_code,allow_omission`，reason_code 固定 identity|cutoff|model|status|score|counterevidence|recovery_trigger|missing_information|coverage_limit|scope；allow_omission 只可 false。optional_pointers 是唯一 pointer 字符串数组，不能与 required 重复。策略引用具体源字段，不根据答案分数高低改“重要”定义；源值为 null/[] 仍明确记 empty_not_required 并保留分母。非空数组/对象必须展开为明确叶子 pointer；不接受用整段父对象引用声称所有子项已覆盖。以 watch_triggers 为例，非空时逐条引用数组元素，而不是只引用整个数组。

```python
def audit_summary(request: dict, *, input_root: Path, source_root: Path, lock: dict) -> dict: ...
```

CLI：`python -B -X utf8 -m iqs_summary_loss audit --input request.json --input-root fixtures --source-root vendor/iqs --lock inputs.lock.json --output runs/audit-01`，另共同 validate/evaluate/version/help。

结果 `iqs.summary_loss_report/1.0.0` 使用共同 result 顶层；payload 闭合为 `source_sha256,summary_sha256,policy_sha256,assessment,checks,extra_claim_checks,coverage,manual_review_required`。assessment=deterministic_conflicts_found|no_deterministic_conflict|unassessable；**无 findings 不叫 accurate**。

checks 每项闭合 `check_id,rule_id,source_pointer,block_id,claim_id,status,source_value,rendered_value,reason`；status=preserved|omitted|mismatched|unassessable|empty_not_required。源不存在的 required pointer 是 policy_invalid，输入拒绝而非算 omitted；错误 pointer 不尝试名字相似自动匹配。coverage 闭合为 `required_count,empty_not_required_count,preserved_count,omitted_count,mismatched_count,unassessable_count`，各项互斥且和等于 required_count；另有不在 required 分母中的 extra_claim_checks，不混加。一个 block 多次引用同字段不能重复提高覆盖率；free_text 永远 unassessable。manual_review_required 固定 true。

checks 对每个 required pointer 恰有一行；多个 claim 指同 pointer 时按 mismatched 优先于 preserved、再优先于 unassessable 的保守顺序聚合，关联所有原 claim ID 另在 extra_claim_checks 逐条保留（同结构，但不进入 required 分母）。block_id/claim_id 仅在恰有一个关联时写该 ID，否则 null。traceability=provided 且未引用则 omitted；traceability=absent 时非空源字段全部 unassessable，不声称文本必然遗漏。源是 null/[] 且没有虚构非空 claim 则 empty_not_required。对空值编出具体值必须 mismatched，不能借 empty_not_required 放过。源空值未展示不影响风险，但保留原分母和空值计数。assessment 在任一 required/extra claim 为 mismatched 或存在 required omitted 时为 deterministic_conflicts_found；否则存在 unassessable 则 unassessable；仅其余情况为 no_deterministic_conflict。

所有 JSON pointer 按 RFC 6901 正确处理 ~0/~1、数组索引，不支持 `$ref` 执行/JSONPath eval。相同数值但单位/期间/scope/model 不同不得靠值相同算保真；政策必须将这些伴随字段独立列 required。score/status 的 exact scalar 提取是诊断，不计算新总分。不同模型回答不能合成一个“公司模型”。

## 内容与测试

1. 用锁定虚构 standard-output 派生源 envelope，保留 example_only 说明和原 bytes/hash；所有新增事实都是 synthetic，不冒真实答案。不依赖生产摘要新接口。
2. 至少 24 个成对案例，覆盖：unknown→5分/0分；N/A→差评；8分但过期；cycle 低谷+持久优势同时保留；恢复条件被漏/改已兑现；反证遗漏；partial 列表写成完整；三日期混淆；回溯 as_of 与今天采集区别；模型 fallback 混入统一默认模型；母/子/分部混用；单位/CNY/USD/期间漏标；同分不同题义；原输入本来为空；少量展示省略非 required；无sidecar合法 unassessable；恶意伪造 pointer/hash；重复来源不增覆盖。
3. 单元：pointer/闭合/拒假值与精确覆盖分母；正常限定摘要不误杀。至少一个 source 本身不足但摘要诚实保留缺口的正例，不要求编造信息填满。
4. 集成：真实从冻结 answer schema 校验虚构原例，再由本包 wrapper/policy→audit；至少两个不同题集长度和事实/评分混合。原 schema 未支持字段不静默丢弃。
5. E2E：公开 audit→validate→evaluate；至少六个关键错误确实在结构合法摘要中检测到；普通无sidecar文字给 unassessable 而非程序失败；未实现语义判断明确在 limitations，不能用手写词典冒 LLM 语义审查。网络0、模型0、源hash保持、临时根成功/失败后清理。

交 `content/policies/`、`content/casebook.json`、输入/摘要/expected 分离的 fixtures、闭合 schemas、工具、完整测试与共同交接。integration-map 精确说明主线摘要应怎样附带 pointer sidecar，以及哪些金融语义需独立人工/模型 review。独立 reviewer 全量核案例预期，并用自己的两个新遗漏/正常限定对照复测；修有效问题后 passed 才交接。
