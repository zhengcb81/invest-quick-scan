# F2-IQS-0001 部分完成被快扫检查报成完整可用

- issue_key: `iqs-scan-result-partial-reported-complete`
- 状态: verified
- 期望/实际: `partial-marked` / `complete-claimed`
  （影响：一份只答了 24/38 题的运行，检查器给出 `ok=true`、`usable=true`、
  退出码 0，读者据此把它当成一次完整可用的扫描结果）
- 责任层: 本仓 `scripts/iqs_scan/tools/scan_result_check.py`
- 修复版本: `invest-quick-scan/company_assessment-1.1.0-obs1`
- 复验: verified @ `invest-quick-scan/company_assessment-1.1.0-obs1`

## 发生引用

| # | run_id | attempt_id | step_id | check_id | evidence_ref |
|---|---|---|---|---|---|
| 1 | `thin-bank-catl-full-2026-10-22/final` | `scan-result-check` | `scan-result/<run>` | `coverage-claim` | `iqs:scan/runs/thin-bank-catl-full-2026-10-22/final` |

本仓 runs/ 留存此处原生答案。可移植复现使用 tests/fixtures/company_coverage/answers-partial-24of38.json 的脱敏样本。

F4 调取旧 checker 验证两份曾列作关联发生的真实样本。
thin-bank-catl-full-2026-10-22/dryrun（24/38）和 thin-bank-catl-dry（3/37）
原检查均为 usable=false、退出 1，两份作为新闭环的阴性对照，观察为 expected。
[F4 再核验与恢复证据](../parallel-lanes/packages/2026-11-11-modularity-closeout/F4-IQS-native-runtime.md)

## 最小复现

```bash
python -B -X utf8 scripts/scan_result_check.py --run runs/thin-bank-catl-full-2026-10-22/final
```

修复前输出（真实）：`question_count=24`、`scored=15`、`ok=true`、`usable=true`、
退出码 0，而同一份 `answers.json` 的 `bank.question_count` 是 38。

## 根因（已证）

`check()` 把 `question_count` 取成「已存在的答案条数」，再只用
`scored > 0` 判 `usable`；`bank.question_count`（冻结题库题量）从未被读取。
于是「答了一部分」与「答满」在报告里不可区分。证据：同一份文档里
`bank.question_count=38` 与 `len(answers)=24` 并存。

## RED / GREEN

- RED：`tests/test_scan_result_check.py` 新增 5 例，5 failed（`KeyError:
  'coverage'`），见交接 §测试。
- GREEN：同一批 5 例通过，另补 1 例「有缺项无题库总数判 partial」；原 9 例保持通过，`usable` 语义对无题库计数的
  旧运行不变（`coverage=unknown` 时仍按原规则判定）。

## 同类场景与反例

- 同类：任何 `answers.json` 带 `bank.question_count` 但答案条数不足的运行，
  以及带顶层 `missing_question_ids` 的 standard-1 产物。
- 反例（必须不报错）：答满题库的运行仍 `usable=true`；没有 `question_count`
  的旧扁平运行仍按原规则判定，只是额外标 `coverage=unknown` 并给一条警告。
