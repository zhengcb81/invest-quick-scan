# S01 独立审查报告

- reviewer: `/root/g0_independent_review`
- review_date: `2026-09-23`
- task: `S01 — metric与作用层编排`
- decision: `needs_revision`
- scope_note: G0 candidate 是历史门禁；本次 S01 文件变化不影响 G0 已冻结证据。

## 审查快照

| 文件 | SHA-256 |
|---|---|
| `scripts/question_sets.py` | `020D1A43C4CD4C14F34BD03AE014874915E0754352C1BFBD0A17BABFA44562D5` |
| `tests/test_question_sets.py` | `B54D37217398D7BF330584AD99BA972ED3065B674DDBD270896C03DC870CB941` |
| `questions/catalog.json` | `4C830DD60A27B019E3A86215241EBD9B886241E7C25AF791E406081E9AFF285C` |
| `references/scoring.md` | `C3A7AB99829E38DBE558AB89267D42C11025139FC3189BDA883D3CB0D68E43E7` |
| `schemas/quick_scan/metric.schema.json` | `251ED13329E3A361853ED7539D2EE4FEE43674317EA3A686127F9ECFA5741F23` |
| `docs/implementation/contracts/receipt-S01.json` | `31842015A230950E1804F2BA2021C7165891D54604CC12ADA45DB8D8772842AE` |

## 结论

S01 当前不能标记 verified。正常 `compose` 路径生成的 metric mapping、24 个核心构念、类型替代、security scope、诊断隔离和关键风险标记彼此一致，旧 manifest 也能继续读取；但 `normalize`/`summarize` 不消费也不校验 manifest 中声明为冻结契约的 `question_metric_mappings` 或每题 `metric_contract`。执行器仍直接信任问题行上的 `dimension`、`comparison_role`、`aggregation`、`critical`、`construct_id` 和 `scope`。

因此，schema-valid mapping 可以与实际汇总语义相反而不被拒绝。诊断题也可以在 mapping 声明不计分且不 critical 的同时，通过问题行字段触发关键风险。security scope 可独立漂移。这个断点直接违反 S01“metric 与作用层编排”和审查要求中“每个 schema-valid mapping 都与汇总执行语义一致”。

此外，`receipt-S01.json` 把 REC-04 登记为 passed，但 REC-04 仍是 `specified_not_executed`，现有 selector 没有执行该 case 要求的三个查询入口。MATRIX-07 与 SC-09 也只覆盖了部分预期。

## 独立测试结果

| 命令/检查 | 原始结果 |
|---|---|
| `python -X utf8 -m pytest -q tests/test_question_sets.py tests/test_metrics_contract.py -p no:cacheprovider` | `36 passed, 72 subtests passed in 16.03s` |
| `python -X utf8 -m pytest -q tests/test_scoring_and_rules_contract.py -p no:cacheprovider` | `8 passed in 2.94s` |
| `python -X utf8 -m pytest -q -p no:cacheprovider` | `188 passed, 108 subtests passed in 228.08s` |
| 正常 quick compose（杜邦+五力） | 43 题；top-level mapping 与 embedded mapping、`metric_mapping(q)` 全部一致；12 个 diagnostic，0 个 diagnostic critical |
| 正常 bank quick compose | 24 个 core construct 且唯一；`BANK_01→IQS_16` critical/entity，`BANK_03→IQS_11` entity，`BANK_06→IQS_22` security/valuation 均正确 |
| 旧 manifest | 无新版 mapping 字段仍可 normalize；使用 `legacy-all-questions`，全 5 分得到 quality 5.0 |
| 恶意/边界检查 | 3 个不一致 manifest 被接受，详见 findings |

测试全绿仅证明当前库生成的正常路径。现有测试没有覆盖 mapping 与执行字段发生矛盾时的拒绝行为。

## Acceptance case 裁决

| Case | 结论 | 独立依据 |
|---|---|---|
| `SC-08` | `needs_revision` | 正常生成的杜邦/五力诊断不进入维度和质量分，现有 metamorphic test 通过；但 mapping 与问题行未闭合。诊断 mapping 仍可配上 `critical=true` 的问题行并把 quality 置空，故“诊断只独立展示”的契约未在入口强制。 |
| `SC-09` | `needs_revision` | 正常关键题低分/未知会把 quality 置空，独立规则单测也证明 critical gate 可压过 OR；但 S01 receipt 所列 selector 没有验证 OR 集成，且 mapping 的 `critical_risk` 不是执行来源。关键风险与实际 gate 仍可漂移。 |
| `SC-10` | `verified` | 8 类公司×6 生命周期的参数化选择、24 核心覆盖、替代关键标记、ID 唯一、生命周期与周期独立、诊断按理由启用均有公共实现回归；正常生成路径独立抽查通过。 |
| `SC-11` | `needs_revision` | 正常 bank 替代的 construct/scope/metric 正确，metric comparability 测试也通过；但新版 manifest 没有把 construct、comparison role、scope 与 metric mapping 形成单一受校验作用层，schema-valid mapping 与执行字段可冲突。 |
| `REC-04` | `not_executed` | 验收 case 要求在“所有相关/质量/恢复”三个查询入口验证 `quality_score=null` 的恢复对象仍可见、未审核 reported score 不得成为优势。现有 `tests/test_question_sets.py` 只测试本地 recovery-watch/normalize，没有执行这些查询入口；case 文件本身仍为 `specified_not_executed`。receipt 的 `passed` 不成立。 |
| `MATRIX-07` | `needs_revision` | 现有 selector 证明直接传给 `summarize` 的 context 10 分不改变 24 个 core 5 分；独立旧 manifest 检查也通过。但 selector 没有同时覆盖 quick/full、关键风险与恢复观察保留、旧汇总快照保存；更关键的是 manifest mapping 与实际 comparison role 可不一致。 |

## Findings

### S01-01 — Blocking — 冻结 metric mapping 不是汇总执行的权威输入

- trigger: 在正常 compose manifest 中，将 `IQS_01` 的 top-level 和 embedded mapping 改为 schema-valid：`dimension=fact`、`aggregation_role=diagnostic_only`、`critical_risk=false`。该 mapping 通过 `metric.schema.json`。问题行仍保留 `comparison_role=core`、`aggregation=scored`。
- expected: 新版 manifest 应因作用层冲突被拒绝；或者执行器应按冻结 mapping 把 IQS_01 排除于核心汇总。
- actual: `normalize` 接受 manifest。其余核心题 5 分、IQS_01 10 分时，business score 变为 `6.67`，quality score 从基线 `5.0` 变为 `5.33`。
- location: `scripts/question_sets.py:26-57` 生成 mapping；`:295-309` 同时保存两套字段；`:397-429` 汇总只读 record 字段；`:503-544` normalize 不校验或使用 mapping。
- impact: 对外冻结的 metric contract 与本地/下游实际比较结果可以相反，导致横向筛选、白名单和 UI 对同一 manifest 得到不同分数。
- required_fix: 对 schema 3.0 manifest 增加公共 `validate_manifest_semantics`，要求 top-level mapping 与题目一一对应、ID 唯一、与 embedded mapping 完全相等，并与实际 construct/action layer 一致。汇总应从验证后的单一 canonical mapping 投影 record，不再独立信任重复字段。
- verification: 上述 schema-valid 冲突必须在 normalize 前被拒绝；遍历所有允许 mapping/action-layer 组合，确保所有被接受 manifest 的执行角色与 mapping 完全一致。

### S01-02 — Blocking — diagnostic/critical 与 security scope 可绕开 mapping 独立漂移

- trigger A: 正常杜邦+五力 manifest 的 `DUPONT_01` mapping 保持 `diagnostic_only`、`critical_risk=false`，只把问题行 `critical` 改为 true，并给该诊断题 2 分、其余题 5 分。
- actual A: normalize 接受，quality 从 `5.0` 变为 `null`，`critical_issues` 出现 `DUPONT_01 material_concern`。
- trigger B: 正常 manifest 中 `IQS_22` 的问题行 scope 从 `security` 改为 `entity`，mapping 和其他字段不变。
- actual B: normalize 接受并输出 `record_scope=entity`。
- location: `scripts/question_sets.py:47` 只在 mapping 中强制 diagnostic 非 critical；`:423-429` 实际关键风险读取 `record.critical`；`:520-524` record 的 scope/critical 来自问题行；metric schema 不含 scope、construct 或 comparison role。
- impact: 诊断可错误阻断公司质量，证券估值可挂到实体层并污染多地上市比较；消费者不能依据 metric contract 判断作用层。
- required_fix: 将 `construct_id`、`comparison_role`、`aggregation`、`scope` 纳入版本化 action-layer contract，或为 manifest 增加同等严格的配套 schema；对 diagnostic 强制执行 `critical=false`；security/entity scope 必须由受信任题库快照/manifest hash 验证，不能接受未校验的行内覆盖。
- verification: diagnostic+critical、security→entity、core→context、construct replacement 漂移均必须拒绝；合法 entity/security 和诊断 manifest 保持通过。

### S01-03 — Important — S01 receipt 将未执行或部分执行 case 记为 passed

- trigger: 对照 `receipt-S01.json` selector 与 acceptance case 原始 then 条件。
- location: `docs/implementation/contracts/receipt-S01.json:13-19`；`docs/implementation/acceptance-cases.json` 的 SC-09、REC-04、MATRIX-07。
- impact: 审查/后续 gate 会误以为真实查询可见性、OR 筛选、quick/full 与旧快照行为已被验证，掩盖 owner 项目尚未实现的集成工作。
- required_fix: REC-04 保持 `not_executed/pending_owner`，不得在 S01 receipt 写 passed；SC-09、MATRIX-07 要么补齐其完整本仓可执行部分并明确剩余 owner case，要么把 receipt 结果标为 partial/contract-only。
- verification: case-selector 矩阵逐条覆盖每个 then；无法由本仓执行的集成条件必须明确未执行，且计划校验禁止 receipt 把它登记为 passed。

## 已确认正确的行为

- 正常 compose 会在 manifest 顶层和每题嵌入 C02 mapping；当前题库两份 mapping 完全一致。
- 当前题库的 diagnostic mapping 全部为 `diagnostic_only` 且 `critical_risk=false`。
- `core-constructs-v1` 正常路径只汇总 24 个唯一核心构念，context 高分不会改变核心分。
- 类型替代在当前题库中保留原 construct；替代 IQS_22 的 `BANK_06` 保持 security scope 和 valuation role；替代关键题 IQS_16 的 `BANK_01` 继承 critical。
- 关键题低分、未知、缺失或 N/A 均不能被其他高分平均掉；恢复观察不会上调 quality。
- 未包含新版字段的旧 manifest 仍走 `legacy-all-questions`，兼容读取成功。

## 放行条件

1. 关闭 S01-01、S01-02：为 schema 3.0 manifest 建立单一、入口强制的 metric/action-layer 语义，并让汇总消费该 canonical 结果。
2. 增加 schema-valid 恶意 manifest 回归，至少覆盖 metric role、diagnostic critical、construct/comparison role、entity/security scope 和 top-level/embedded mapping 不一致。
3. 更正 receipt 的 case 状态；REC-04 不得在真实三个查询入口执行前标 passed，SC-09/MATRIX-07 必须准确区分单元契约与尚未执行的集成预期。
4. 修复后独立复审当前源码和原始日志，才能将 S01 标为 verified。

