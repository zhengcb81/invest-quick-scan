# G0 独立复审报告

- reviewer: `/root/g0_independent_review`
- review_date: `2026-09-23`
- reviewed_candidate_path: `docs/implementation/reviews/G0/candidate-snapshot.json`
- reviewed_candidate_sha256: `6F8ECB2BC9C0B65CD689EA56C57095A0266A48B6ABFC1467114CCF5A37B742CA`
- re_review_packet_sha256: `E7BF33DA7902CA23C6FE08C8750DE17DFF2AB79591F3BF0620BD27B62F779B63`
- decision: `needs_revision`
- G0_release: `blocked`

## 结论

整改关闭了 G0-02、G0-03、G0-04、G0-06、G0-08，并修复了 G0-01、G0-05、G0-07 的首轮最小反例。但后三项仍存在同类绕过，G0-09 的候选绑定也不完整，因此 G0 仍不可放行。

我没有采用 `remediation-receipt.json` 的自述作为结论。我逐一核对了候选哈希、schema、公共 helper、测试源码、验收案例状态、原始日志和 company-wiki 同哈希源码，并独立复跑测试和恶意输入。候选清单中列出的 41 个 hash 全部与当前字节一致；问题在于清单没有覆盖全部受审依赖。

## 测试与原始结果

| 验证 | 独立结果 |
|---|---|
| `python -X utf8 -m pytest -q -p no:cacheprovider` | `181 passed, 108 subtests passed in 127.01s`，退出码 0 |
| `python -X utf8 -m pytest tests/test_g0_regressions.py -vv -p no:cacheprovider` | `7 passed in 13.05s`，退出码 0 |
| `python -X utf8 scripts/implementation_plan.py validate` | `planning_valid=true`，73 tasks，171 cases，`product_tests_executed=false` |
| 候选逐文件 hash 重算 | 41 项全部匹配，0 mismatch |
| 整改原始日志核对 | 文件 hash 匹配候选；内容为 `181 passed, 108 subtests passed in 127.58s`、计划校验成功、11 个 schema self-check、34 个 JSON parse |
| 首轮最小反例重放 | score 两种非法状态、伪造未知 receipt、跨实体 entity/work/universe、extension 正文、畸形 release、低证据 self-attestation、查询覆盖矛盾、诊断进入核心、空规则、传递/缺失/成环 lineage 均按预期拒绝 |

全绿测试没有覆盖本报告下面的新反例；这些反例均直接调用冻结候选中的 schema/helper。

## 首轮 Finding 逐项裁决

| Finding | 复审状态 | 裁决 |
|---|---|---|
| `G0-01` | `not_closed` | score/status 条件已闭合，未知 receipt 会拒绝；但 helper 只检查 receipt ID 是否在一个无类型集合中，不校验它授权的公司、问题、观测或等级。已知的低等级/他公司 receipt 可重放为 `formal_research_accepted`。 |
| `G0-02` | `closed` | `validate_entity`、`validate_universe_manifest`、`validate_work_item` 与 query profile 校验已覆盖父子实体、scope owner、成员唯一性/计数和 profile observation 实体一致性；首轮反例全部拒绝。 |
| `G0-03` | `closed` | C01-C03 已调用 `scripts/contract_validation.py` 的公共实现；测试内仅余 fixture/data helper。C05-C07 新增 `*-CONTRACT-*` case，原 `PAR-01`、`BUD-01`、`DB-03`、`START-02` 均保持 `specified_not_executed`；计划校验明确 `product_tests_executed=false`。 |
| `G0-04` | `closed` | exchange v1.0.0 将 `extensions` 限制为 `maxItems=0`，公共 validator 也拒绝非空扩展；嵌套 `raw_document` 反例被拒绝。 |
| `G0-05` | `not_closed` | `validate_release_set` 已 schema-first，首轮畸形 manifest 被拒绝；低证据 full-ready 反例也被拒绝。但 response schema 允许七份重复的 `G0` gate、错误的 gate/release ID 与任意 manifest hash，仍可自报 `full_release_verified`。 |
| `G0-06` | `closed` | `validate_query_response` 闭合 search status/coverage、scored lineage 与 profile/observation 实体关系；首轮三个反例被拒绝。 |
| `G0-07` | `not_closed` | diagnostic role 与空规则已拒绝；但 CompositeRule 子节点 `$ref: "#"` 会允许裸 `FieldThresholdCondition` 或完整 `ScreeningPolicy`，而 `evaluate_rule` 只支持包装后的 `condition/all/any/not`，导致合法 schema 输入运行时 `KeyError`。 |
| `G0-08` | `closed` | `independent_support` 递归检查完整祖先闭包、缺失祖先与环；两跳依赖返回 false，完整独立链返回 true。 |
| `G0-09` | `not_closed` | company-wiki issuer-index 描述已按同哈希源码纠正，packet 自身也与 candidate 中记录的 hash 一致；但 candidate 漏绑多项直接受审/执行依赖，且自称 `not_frozen`，不能唯一固定本次候选。 |

## 未关闭问题

### RR-01 — Blocking — check-level receipt 没有绑定授权对象与等级（G0-01）

- trigger: 构造 `question_id=IQS_99`、`check_level=formal_research_accepted`、`check_level_receipt_id=RCP_EXECUTION_OTHER_COMPANY`，并把该 ID 放入 `trusted_check_level_receipts`。`validate_parsed_answer` 返回成功，即使该 receipt 名义上来自另一公司/问题且只授权 execution 等级。
- actual: `accepted=True`。
- location: `scripts/contract_validation.py:52-63`；`schemas/quick_scan/score.schema.json:63-66,89-91`。
- impact: 一张真实存在但不相关或低等级的 receipt 可被模型输出重放，获得正式研究验收等级；“对应运行层或审核层签发并可查验”的闭包没有由契约执行。
- required_fix: 参数应是可信 receipt records/mapping，而非无类型 ID 集合。至少校验 receipt 的 `entity_id`、`question_id`/`observation_id`、授权 `check_level`、签发者、状态和不可变 hash；请求等级不得高于 receipt 等级。
- verification: 新增跨公司、跨题、跨 observation、低等级升高等级、撤销/不存在 receipt 的负例；合法同对象同等级 receipt 通过。

### RR-02 — Blocking — full release 的 gate/release 证据仍可伪造闭包（G0-05）

- trigger: 从冻结 example response 构造 `full_release_verified`，把三项布尔证据设 true、提供两个非空 usage receipt 和两个 consumer；`gate_evidence` 放入七份完全相同的 `G0/passed` 记录，每份使用 `release_set_id=REL_WRONG`，同时 evidence 顶层也使用错误 release ID 和任意 manifest hash。
- actual: `Draft202012Validator(deployment.schema).validate(response)` 成功，`error_count=0`。
- location: `schemas/quick_scan/deployment.schema.json:1173-1220,1248-1264,1441-1446`。
- impact: 不经过 `assess_readiness` 的 producer 仍能生成 schema-valid 的虚假完整发布结果；消费者无法依靠交换契约验证 G0-G6 各一次、同一 release、同一 manifest 的证据闭包。
- required_fix: 为 gate evidence 强制 gate ID 唯一且恰为 G0-G6，并在可信语义 validator 中校验每条 gate、evidence 顶层与响应/manifest 的 release ID 和 hash 相等。所有 response 输出/导入入口必须调用该 validator，不能只依赖 schema。
- verification: 七份重复 gate、缺任一 gate、错误 release ID、错误 manifest hash、重复 consumer 均拒绝；同一 release 的完整 G0-G6 才可得到 full verified。

### RR-03 — Blocking — CompositeRule schema 与公共执行器语言不一致（G0-07）

- trigger: `{"all":[{"field":"score","op":">=","value":8}]}`。子节点通过 `$ref: "#"` 被识别为顶层 `FieldThresholdCondition`，所以 `validate_rule` 接受；`evaluate_rule(..., {"score":9})` 随后按 composite wrapper 取 `any` 键并崩溃。
- actual: schema `accepted=True`；执行结果为 `KeyError`。
- location: `schemas/quick_scan/rule.schema.json:31-58`，特别是 `all/any/not` 的 `$ref: "#"`；`scripts/contract_validation.py:147-163`。
- impact: 策略可通过预检却在扫描/筛选时崩溃。完整 ScreeningPolicy 也可作为嵌套子节点通过同一根引用，形成更大的语言歧义。
- required_fix: CompositeRule 的递归引用只指向 CompositeRule；叶子统一为 `{"condition": FieldThresholdCondition}`，或让 schema 与 evaluator 都正式支持裸叶子。禁止 ScreeningPolicy 嵌套在规则树内。
- verification: 裸叶子和嵌套 policy 要么 schema 拒绝，要么执行器有明确定义；增加多层 all/any/not 正反例，并证明所有 schema-valid CompositeRule 都不会因节点形状崩溃。

### RR-04 — Blocking — candidate manifest 未绑定全部受审依赖（G0-09）

- trigger: `candidate-snapshot.json` 的 artifact/historical/remediation 三类路径全集不包含下列实际参与九项复审或全套测试的文件：
  - `schemas/quick_scan/work.schema.json`
  - `scripts/work_contract.py`
  - `scripts/model_policy.py`
  - `tests/test_freshness_and_jobs_contract.py`
  - `tests/test_model_policy.py`
  - `tests/test_providers_and_budget_contract.py`
  - `examples/quick_scan/exchange-package.example.json`
  - `examples/quick_scan/query-contract.examples.json`
  - `examples/quick_scan/deployment-contract.examples.json`
- actual: 九项均为 `UNBOUND`；它们可在 candidate hash 不变时被修改。manifest 自身的 `manifest_type` 与 `notice` 也明确写为 `not_frozen`。
- location: `docs/implementation/reviews/G0/candidate-snapshot.json`。
- impact: `6F8ECB…` 不能唯一标识实际执行的完整 G0 候选。特别是 G0-02 的 work schema、G0-03/C05 的 model-policy 实现测试以及多个回归测试 fixture 未被固定，违反 REV-02 的不可变审查要求。
- required_fix: 重新生成覆盖全部 G0 schema、公共 helper、测试、fixture、contracts、receipts 和 raw logs 的排序逐文件 manifest；把 candidate 状态改为 frozen-for-review，并在复审期间冻结这些路径。
- verification: 从声明的范围枚举文件，与 manifest 做集合相等检查，而非只验证 manifest 已列路径的 hash；随后逐项重算 0 mismatch。

## 已关闭问题的核验细节

- G0-02：跨实体 Entity、entity-scope WorkItem 和重复/错误计数 UniverseManifest 均由公共 validator 抛出 `ValueError`；profile 中异实体 observation 同样拒绝。security/segment scope 必须提供权威 owner lookup。
- G0-03：AST 检查显示 C01-C03 的决策调用来自 `contract_validation`；原自证函数已移除。`record` 仅为测试数据构造。生产 integration/fault case 没有被本仓 receipt 冒充为 passed。
- G0-04：schema 和公共 exchange validator 双重拒绝非空 extensions。当前版本没有注册扩展，所以不存在任意 payload 逃逸口。
- G0-06：`ok + empty/not_covered`、scored 但 lineage/model/time 为空、profile/observation 跨实体均拒绝。
- G0-08：独立复跑结果依次为 transitive target `False`、missing ancestor `False`、complete independent `True`、cycle `False`。
- G0-09 外部事实部分：只读重算 company-wiki `resolver.py` 为 `783460A9F21679B439073FC6B82F4D5A43F583423D59E9EE627B0C9F149BE21A`；源码确有 `_AMBIGUOUS_ISSUER`（1249）、`_load_issuer_index`（1253）和 `_issuer_index`（1699）。修订后的 external snapshot 已准确区分“存在 issuer-index 辅助逻辑”与“resolver 不自行建立 quick-scan 跨上市归并主数据”。

## 放行要求

1. 关闭 RR-01 至 RR-03，并把上述最小反例加入调用公共实现的回归测试。
2. 生成覆盖范围完整且声明 frozen-for-review 的新 candidate manifest，执行集合完整性和逐文件 hash 校验。
3. 基于新 candidate 独立重跑全套测试、九项 finding 和本轮四项反例；全部通过后才可将 G0 标为 `verified`。

