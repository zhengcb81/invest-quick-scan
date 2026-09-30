# S01 第三轮独立复审报告

- reviewer: `/root/g0_independent_review`
- review_date: `2026-09-23`
- decision: `needs_revision`
- local_scope_release: `blocked`

## 审查快照

| 文件 | SHA-256 |
|---|---|
| `scripts/question_sets.py` | `8C90D2FFDE395BC263367764CC941D39F5156A8A0D269E9B66130E6D462B55B9` |
| `tests/test_question_sets.py` | `EA16C33107E6CF336D7173F39C4A0A57300CE43C09D30762A269FE4AF569CD16` |
| `docs/implementation/contracts/receipt-S01.json` | `8041218F9821716BB09366BE10972C4830966D1F716C13915B06C8914E6D55BB` |
| 第二轮 S01 报告 | `81D4D2185F38B4BE24C13494562AAB9B3FEA3511C4D589225B61A9CE4BA49873` |

## 结论

第二轮剩余的 replacement map 阻断已关闭：bank compose 后把 `manifest.replacements.IQS_16` 从 `BANK_01` 改为 `IQS_01`，`normalize` 现在抛出 `ValueError: manifest replacement mapping drift`；把 `BANK_01.module_id` 改成 `common` 也会抛出 module drift。正常 3.1.0 题库 manifest 的 selected replacements 由 canonical question `replaces` 推导，metric mapping 继续决定 aggregation 与 critical；旧无 mapping manifest 保持兼容。

但扩展恶意检查发现 validator 仍没有闭合“被选择的问题集合”。它只验证 manifest 中出现的每一题来自 canonical catalog，没有验证 question ID 唯一、question ID 集合与 mapping ID 集合相等，也没有按 profile/mode 重算应选择的完整题集。因此：

1. full bank manifest 中可用第二份 `BANK_05` 替换 `MATURE_01`，保留全部原 mapping；normalize 接受重复 context 问题和未消费的 `MATURE_01` mapping。
2. 请求了 dupont 的 quick manifest 中，可同时删除 `DUPONT_01` question 与 mapping，并把 `question_count` 减一；normalize 接受，虽然 profile/modules 仍声明选择了 dupont。

这会造成 UI/完整率/诊断输出与路由声明不一致，也否定“question↔mapping 一一对应”和“选择结果由版本化题库推导”的契约。S01 仍不能在本地实现范围标记 verified。

REC-04 继续正确保持 `specified_not_executed`，本地测试没有被用来放行真实 StockWiki 查询入口。

## 独立执行结果

| 检查 | 原始结果 |
|---|---|
| `python -X utf8 -m pytest -q tests/test_question_sets.py tests/test_metrics_contract.py -p no:cacheprovider` | `39 passed, 76 subtests passed in 20.24s` |
| `python -X utf8 -m pytest -q -p no:cacheprovider` | `191 passed, 112 subtests passed in 90.20s` |
| bank replacement attack | `PASS_REJECTED ValueError manifest replacement mapping drift` |
| BANK_01 module attack | `PASS_REJECTED ValueError manifest question module drift: BANK_01` |
| 正常 bank manifest | 26 questions/mappings；`BANK_01` 为 `quality_core` 且 critical；top-level replacements 与 canonical questions 一致 |
| 旧 manifest | `legacy-all-questions` 成功读取 |
| 重复 context attack | `FAIL_ACCEPTED BANK_05 replaced MATURE_01` |
| 删除已选择 diagnostic attack | 删除 `DUPONT_01` question+mapping 并调整 count 后 `FAIL_ACCEPTED` |

## 指定复审项

### Replacement map — Closed

`validate_manifest_metric_contract` 现在从已验证 question 的 canonical `replaces` 构造 `expected_replacements`，拒绝重复目标，并要求顶层 `manifest.replacements` 完全相等。`recovery_watch` 虽仍读取顶层字典，但新版 manifest 在进入 normalize 时已证明它等于 canonical map。第二轮反例关闭。

### Module ID — Closed

canonical 索引现在保存 `(question, module_id)`，manifest question 的 `module_id` 必须与版本化题库一致。把类型题伪装成 common 会被入口拒绝。

### Metric mapping execution — Closed for accepted rows, set closure still open

对于 validator 实际遍历并接受的每一题，top-level mapping、embedded mapping、canonical mapping 和 bound metadata 一致，normalize 使用 authoritative mapping 决定 aggregation 与 critical。此前 fact/diagnostic、critical、scope 和 embedded mapping 攻击继续被拒绝。

尚未关闭的是集合层：可能存在重复 question row 和没有对应 question 的多余 mapping，也可能整体删掉已路由的 diagnostic/context question。故不能声称整个 manifest 的 mapping 都是唯一、被消费的执行输入。

### Legacy compatibility — Closed

不含 `metric_contract_version` 的旧 manifest 不进入 3.1 校验，仍成功按 `legacy-all-questions` 处理。

## 新 Blocking Finding

### S01-FR-01 — Blocking — selected question/mapping 集合未与 canonical 路由结果闭合

- trigger A: 对正常 full bank manifest，选择两个无 replacement 的 context 问题 `BANK_05`、`MATURE_01`；用 `BANK_05` 的完整 question row 覆盖 `MATURE_01` row，保留原 mapping 列表。
- actual A: normalize 接受。questions 中出现两个 `BANK_05`，`MATURE_01` mapping 仍存在但没有 question 消费。
- trigger B: 对 profile 明确请求 dupont 的 quick manifest，同时删除 `DUPONT_01` question 与它的 mapping，并将 `question_count` 减一。
- actual B: normalize 接受；profile/modules 仍声明 dupont，但诊断题被静默删减。
- location: `scripts/question_sets.py:69-100`。`by_id` 只证明 mapping 自身 ID 唯一且数量等于 questions；循环没有证明 question ID 唯一或两者 ID 集合相等，也没有调用 `select_questions(profile, mode, modules)` 对比预期选择结果。`question_count`、`modules` 也未校验。
- impact: 可重复 context、隐藏阶段/行业/诊断问题、留下未消费 mapping；所有问题覆盖率、诊断完整率、UI 行和后续消费者会与路由 manifest 不一致。当前核心 24 的 summarize 检查能阻止核心 construct 缺失，却不能保护 context/diagnostic 集合。
- required_fix:
  - 明确拒绝重复 question ID；
  - 要求 question ID 集合与 mapping ID 集合完全相等；
  - 校验 `question_count == len(questions)`；
  - 对 metric-enriched manifest 用 profile/mode 和版本化 library 重跑 `select_questions`，要求 questions 的 ID/module 顺序、modules 和 replacements 与 canonical selected result 完全一致；
  - 或存储并验证等价的不可变 selected-set hash。
- verification: 增加重复 core/context/diagnostic、遗漏 context/diagnostic、额外合法但未路由题、未消费 mapping、错误 question_count/modules/order 的负例；正常 quick/full、全部类型/阶段和旧 manifest 保持通过。

## Case 最终状态

| Case | 状态 | 依据 |
|---|---|---|
| `SC-08` | `needs_revision` | 已出现的 diagnostic 能正确隔离且不可变 critical，但已选择的 diagnostic 可从 manifest 与 mapping 同时删除而不被发现，独立展示与完整率不受保证。 |
| `SC-09` | `verified` | critical mapping、问题 metadata 与规则 gate 已闭合；低分/未知/N/A 不能被均分或 OR 绕过。限本地契约范围。 |
| `SC-10` | `needs_revision` | 核心 24 在正常路径覆盖并由 summarize fail-closed；但 case 同时要求无重复 ID，当前重复 context ID 的 manifest 会被接受。 |
| `SC-11` | `verified` | construct、scope、module 与 top-level replacement map 均绑定 canonical 类型题；指定替代攻击已拒绝。 |
| `MATRIX-07` | `verified` | quick/full 的核心 24 与 context 分离、旧 manifest 兼容均保持；本轮集合问题不改变核心分，但需由 S01-FR-01 防止展示/完整率漂移。 |
| `REC-04` | `not_executed` | receipt 仍为 `specified_not_executed`；真实三查询入口未执行。 |

## 放行条件

关闭 S01-FR-01 并加入集合层恶意回归后，再独立重放本报告两类反例。届时若 REC-04 继续明确保持未执行，S01 可仅在本地实现范围内标记 verified。

