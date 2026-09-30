# S01 第四轮独立闭环审查

- reviewer: `/root/g0_independent_review`
- review_date: `2026-09-24`
- implementation_behavior: `verified`
- evidence_package: `needs_revision`
- final_decision: `needs_revision`

## 审查快照

| 文件 | 当前 SHA-256 |
|---|---|
| `scripts/question_sets.py` | `A49BDB7BF23F99B0724BA7EC01BCAA6023A8DE37E6EF65BCED5D1A51EBF760EC` |
| `tests/test_question_sets.py` | `8BD50F4C647470D4B97A67C66B970FD4351DBBB6BB2991C9D97F4FD303100EDE` |
| `docs/implementation/contracts/receipt-S01.json` | `E933B9FD9AE7E0967A324D49DF709DA4A65F9E73970846DB7953402E81A90646` |
| 第三轮 S01 报告 | `9BE4FDB040F77D3E934DD1ACC87844DFCB6C15A2AEC5E55EEFCCFA70B5607E40` |

## 结论

S01 的产品行为阻断已关闭。当前 `validate_manifest_metric_contract` 会按 profile/mode 对版本化题库重新执行 deterministic routing，要求 question ID 唯一、question 与 mapping ID 集合相等、`question_count` 正确，并要求 questions 顺序、modules 和 replacements 与 canonical selected result 完全一致。请求的所有恶意输入均被拒绝，旧 manifest 保持兼容，REC-04 仍明确未执行。

但本轮不能把 S01 证据包标记为 verified：`receipt-S01.json` 的 implementation snapshot 仍指向上一版 `question_sets.py` 和 `test_question_sets.py`，其测试摘要也仍是上一轮的 `39/191`，而本次独立执行为 `40/192`。回执无法绑定本报告实际审查的闭环实现字节。该问题不要求修改产品代码，只需更新回执快照与当前原始测试证据；在此之前最终 decision 为 `needs_revision`。

## 独立测试结果

| 检查 | 原始结果 |
|---|---|
| `python -X utf8 -m pytest -q tests/test_question_sets.py tests/test_metrics_contract.py -p no:cacheprovider` | `40 passed, 76 subtests passed in 14.47s` |
| `python -X utf8 -m pytest -q -p no:cacheprovider` | `192 passed, 112 subtests passed in 72.58s` |
| 恶意/边界重放 | 9 个攻击全部拒绝；合法当前 manifest 与 legacy manifest 通过 |

## 指定反例重放

| 反例 | 独立结果 |
|---|---|
| 用重复 question ID 覆盖另一已选择 question | `ValueError: question metric mappings must be one-to-one` |
| 删除已选择 question 及 mapping，并递减 `question_count` | `ValueError: manifest selected question set differs from deterministic routing` |
| 追加重复 mapping | `ValueError: question metric mappings must be one-to-one` |
| 用未选择但 catalog 合法的 mapping 替换现有 mapping | `ValueError: question metric mappings must be one-to-one` |
| 修改 profile/company route | `ValueError: manifest selected question set differs from deterministic routing` |
| 修改 `BANK_01.module_id` | `ValueError: manifest question module drift: BANK_01` |
| 修改 `IQS_16→BANK_01` replacement | `ValueError: manifest selected question set differs from deterministic routing` |
| 调换 question 顺序 | `ValueError: manifest selected question set differs from deterministic routing` |
| 调换 module 顺序 | `ValueError: manifest selected question set differs from deterministic routing` |

合法当前 bank/full/dupont manifest 通过，共 36 个 question 与 36 个 authoritative mapping。旧无 `metric_contract_version` manifest 成功读取，输出 schema `2.1`、aggregation policy `legacy-all-questions`。

## 语义闭环核验

### Canonical selected set — Verified

validator 现在执行以下集合约束：

- question row 必须全为对象且 ID 唯一；
- mapping ID 必须唯一；
- question ID 与 mapping ID 集合完全相等；
- `question_count == len(questions)`；
- 以 manifest profile/mode 对当前 3.1.0 题库调用 `select_questions`；
- question ID 顺序、modules 顺序和 replacements 必须与 deterministic routing 结果相同；
- 每题 module、construct、comparison role、scope、critical、aggregation、replaces 与 canonical source 一致。

第三轮发现的重复 context 和删除 selected diagnostic 两个反例均已由上述约束覆盖。

### Metric mapping execution — Verified

对于 metric-enriched manifest，top-level mapping、embedded mapping 和 canonical `metric_mapping(source)` 必须完全相等。`normalize` 使用 validator 返回的 authoritative mapping 决定 aggregation 与 critical；dimension/construct/comparison role/scope 等执行字段也被 canonical metadata 校验保护。此前 fact/diagnostic、diagnostic critical、security scope、embedded mapping、module 和 replacement 攻击均持续 fail closed。

### Legacy compatibility — Verified

不含 metric contract 的旧 manifest 不进入新版 selected-set 校验，仍使用原 `legacy-all-questions` 路径。独立重放成功。

### REC-04 — Not executed

`receipt-S01.json` 中 REC-04 仍为 `specified_not_executed`，selector 明确说明需要 StockWiki 的 all/quality/recovery 查询入口。本仓仅有 supporting unit evidence，没有把本地 normalize/recovery-watch 测试登记为真实查询通过。该状态正确，且不妨碍仅对 S01 本地实现行为作 verified 判断。

## Case 最终状态

| Case | 状态 | 依据 |
|---|---|---|
| `SC-08` | `verified` | selected diagnostics 不能被静默删除或重复；diagnostic mapping 不计分且不 critical。 |
| `SC-09` | `verified` | canonical critical 进入执行语义，低分/未知/N/A 不能被均分或 OR 绕过。 |
| `SC-10` | `verified` | deterministic routing 固定完整 selected set、顺序、modules、24 核心覆盖与 ID 唯一性。 |
| `SC-11` | `verified` | construct、cohort/metric、scope、module 和 replacement 与 canonical 类型题闭合。 |
| `MATRIX-07` | `verified` | context 与核心汇总隔离；quick/full 和旧 manifest 行为保持。 |
| `REC-04` | `not_executed` | StockWiki 三个真实查询入口不在本仓实现，回执保持未执行。 |

## 唯一未关闭 Finding

### S01-CR-01 — Important evidence blocker — receipt 未绑定当前闭环实现

- trigger: 重算 receipt `implementation_snapshot` 中声明的文件 hash。
- actual:
  - receipt 记录 `scripts/question_sets.py = 8C90D2…`，当前为 `A49BDB…`；
  - receipt 记录 `tests/test_question_sets.py = EA16C3…`，当前为 `8BD50F…`；
  - receipt 摘要为 targeted 39 / full 191，当前独立结果为 targeted 40 / full 192。
- impact: 回执描述的是第三轮前版本，不能作为当前闭环补丁的不可变实现证据。后续 gate 无法从 receipt 确认所复核字节。
- required_fix: 只更新 S01 receipt 的 implementation hashes、当前测试摘要和对应原始日志 hash/path；保持 REC-04 为 `specified_not_executed`，不要改变产品代码或冒充产品测试。
- verification: 独立重算 receipt 中所有路径 hash 为 0 mismatch，原始日志与摘要一致，且 REC-04 状态仍未执行。

## 放行意见

产品实现无需继续整改本轮审查的功能行为。修正 S01 receipt 使其绑定当前字节和 `40/192` 测试证据后，若工作树未再变化，可将 S01 在本地实现范围内标记 `verified`；REC-04 继续留待 StockWiki 真实入口阶段。

