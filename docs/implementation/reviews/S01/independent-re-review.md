# S01 整改独立复审报告

- reviewer: `/root/g0_independent_review`
- review_date: `2026-09-23`
- decision: `needs_revision`
- local_scope_release: `blocked`

## 审查快照

| 文件 | SHA-256 |
|---|---|
| `scripts/question_sets.py` | `FB9F9EECC81C534939E57F9487A446CD4F6C53BD0D6619A7E9D2256955B1A6E1` |
| `tests/test_question_sets.py` | `6B2827DF987C04F84BA2B64164907578649B76ED23752262503CBE6AA402610D` |
| `docs/implementation/contracts/receipt-S01.json` | `77F6794706446D8C4EDECE11AE96F1BEFDDD87AE7DCD671DD2A37A10E4413204` |
| 首轮 S01 审查报告 | `4B43AE0439E8B93B57F0FCEC6F8C81343A93B626E1DE334C77131F58847F901D` |

## 结论

首轮提出的四个指定篡改已被关闭：top-level mapping 漂移、诊断 critical 漂移、security scope 漂移、embedded metric contract 漂移均在 `normalize` 入口被拒绝。3.1.0 题库生成的 metric-enriched manifest 会先绑定当前 catalog 的 canonical metadata；通过校验后，mapping 成为 aggregation 与 critical 的执行来源。旧的无 mapping manifest 仍能按 2.1/`legacy-all-questions` 读取。

但 S01 仍不能按本地实现范围标记 verified。顶层 `manifest.replacements` 是实际恢复判断使用的作用层数据，却未进入 `validate_manifest_metric_contract` 的一致性检查。银行 manifest 中把正常的 `IQS_16 → BANK_01` 篡改为 `IQS_16 → IQS_01` 后，`normalize` 仍接受；`recovery_watch` 随后使用错误的有效生存问题。问题行的 `replaces` 和 construct 虽已绑定 canonical source，真正被执行的顶层 replacement map 仍可漂移。

`receipt-S01.json` 已正确把 REC-04 改为 `specified_not_executed`，没有再用本地 recovery-watch 单测冒充 StockWiki 三个真实查询入口。这一点整改成立。

## 独立测试结果

| 检查 | 原始结果 |
|---|---|
| `python -X utf8 -m pytest -q tests/test_question_sets.py tests/test_metrics_contract.py -p no:cacheprovider` | `38 passed, 76 subtests passed in 15.76s` |
| `python -X utf8 -m pytest -q -p no:cacheprovider` | `190 passed, 112 subtests passed in 85.66s` |
| 正常 metric-enriched manifest | template `3.1.0`、manifest schema `3.0`、metric contract `1.0.0`；38 题与 38 个 mapping 一一对应 |
| IQS_01 top mapping 改为 fact/diagnostic | `ValueError: manifest metric mapping drift: IQS_01` |
| 只把 DUPONT_01 `critical` 改为 true | `ValueError: manifest question metadata drift: DUPONT_01.critical` |
| 只把 IQS_22 scope 改为 entity | `ValueError: manifest question metadata drift: IQS_22.scope` |
| 只改 IQS_01 embedded `metric_contract` | `ValueError: manifest metric mapping drift: IQS_01` |
| 旧无 mapping manifest | 成功读取；输出 schema `2.1`、policy `legacy-all-questions` |
| 篡改 bank 顶层 replacements | `IQS_16→BANK_01` 改为 `IQS_16→IQS_01` 后被接受；恢复逻辑使用被篡改映射 |
| MATRIX-07 quick/full 边界 | quick：30题、24 core、2 context、quality `5.0`；full：33题、24 core、5 context、quality `5.0`；两者均保留 recovery watch |

## 首轮 Blocking 复审

### 首轮 S01-01 — Closed

`validate_manifest_metric_contract` 现在要求：

- metric contract version 受支持；
- template version 与当前 catalog 一致；
- mappings 和 questions 数量一致且 mapping ID 唯一；
- 每题 bound metadata 与 canonical question 一致；
- top-level mapping、embedded mapping 与由 canonical question 重算的 mapping 完全相等。

`normalize` 在处理答案前调用该 validator，并用返回的 authoritative mapping 决定 diagnostic/scored aggregation 和 critical。指定的 schema-valid IQS_01 mapping 攻击被拒绝，首轮 S01-01 的原反例关闭。

### 首轮 S01-02 — Partially closed, replacement action layer remains open

诊断 critical、IQS_22 scope 和 embedded mapping 三个指定攻击均被拒绝。当前 validator 绑定了 `dimension`、`metric_id`、`construct_id`、`comparison_role`、`rubric_version`、`scope`、`critical`、`aggregation`、`replaces` 等问题行字段。

然而，`recovery_watch` 实际读取 `manifest.get('replacements', {})`，validator 没有校验该顶层字典是否等于 questions 中 `replaces` 推导出的 canonical map。因此作用层仍有第二来源，首轮要求的 construct/replacement 语义尚未完全闭合。

## 新发现

### S01-RR-01 — Blocking — 执行中的顶层 replacement map 未绑定 canonical action layer

- trigger: 生成 bank quick + recovery manifest；确认正常 `replacements['IQS_16']='BANK_01'`，然后只把顶层值改为 `IQS_01`，问题行、construct、mapping 和 embedded contract 均不变。
- expected: metric-enriched manifest 应在 normalize 前因 replacement action-layer 漂移被拒绝。
- actual: normalize 接受；`recovery_watch.effective('IQS_16')` 使用 `IQS_01`，输出基于错误的生存问题。
- location: `scripts/question_sets.py:60-89` 未校验顶层 replacements；`:476-480`（`recovery_watch` 的 replacement/effective 路径，具体行号随整改偏移）直接信任该字典。
- impact: 类型替代的 construct 在汇总中可以正确，但恢复/生存判断仍可指向另一题；同一 manifest 对核心汇总与恢复观察表达两套“有效问题”。这影响 SC-11，也可能错误降低或抬高困境反转观察状态。
- required_fix: 从已验证 questions 的 canonical `replaces` 生成 expected replacement map，要求它与 manifest 顶层 `replacements` 集合和值完全相等；拒绝缺失、额外、重复目标和错误目标。执行阶段应使用 validator 返回的 canonical replacement map，而不是重新信任 manifest 原值。
- verification: 增加错误目标、缺失替代、额外替代、两个问题争抢同一 construct 的负例；合法 bank/insurer/property 等类型替代和旧无 mapping manifest 保持通过。

## Acceptance case 最终状态

| Case | 状态 | 依据 |
|---|---|---|
| `SC-08` | `verified` | diagnostic mapping 与 canonical aggregation/critical 已绑定；正常诊断不改变维度、质量、成长和估值，指定 critical 漂移被拒绝。 |
| `SC-09` | `verified` | canonical critical 通过 mapping 成为执行输入；低分、未知、N/A 均阻断 quality，规则契约的 critical gate 仍压过 OR。此结论限本地契约/执行语义。 |
| `SC-10` | `verified` | 24 核心覆盖、类型/阶段参数化、周期独立、关键标记及诊断理由保持通过。 |
| `SC-11` | `needs_revision` | question construct/scope 与 metric mapping 已闭合，但实际被 recovery 消费的顶层 replacement map 可漂移，类型替代尚未成为单一执行语义。 |
| `MATRIX-07` | `verified` | quick/full 均维持 24 core；core=5、context=10 时 quality 均为5.0，并保留 recovery watch；旧 manifest 仍可读。 |
| `REC-04` | `not_executed` | receipt 已正确标记 `specified_not_executed`；StockWiki 所有相关/质量/恢复三个真实查询入口尚未执行，本地测试不放行该 case。 |

## 放行条件

1. 将顶层 replacements 纳入 metric-enriched manifest 的 canonical action-layer 校验，并让 recovery 执行使用 validator 返回的可信映射。
2. 加入 replacement map 的缺失、额外、错目标和冲突负例；重跑定向与全量测试。
3. 独立复审该反例关闭后，S01 才可在“REC-04 明确保留 not_executed”的本地实现范围内标记 verified。

