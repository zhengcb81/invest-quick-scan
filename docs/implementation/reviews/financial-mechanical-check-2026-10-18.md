# 金融答案的机械检查器 — 2026-10-18

只读工具 `scripts/financial_mechanical_check.py`：对已入库 observation 的答案做**确定性机械检查**，不判断金融准确性、不给评分、不替代人工复核。用于在人工金融复核之前先挡住结构/口径/来源日期类错误。

## 检查项

- 题号一致：`answer.question_id == observation.question_id`
- 评分/状态：scored 必须是 1–10 整数；非 scored 必须 score=null
- 事实/评分契约：response_kind=fact 不得带 score/items
- 时间：information_as_of、period_end、各 metric period_end 不得晚于 information_cutoff；period_start ≤ period_end
- 证据：id 唯一、URL 必须 https、published_at 可解析且 ≤ cutoff、title 非空
- 指标：metric_id 唯一、basis 合法、value 数值、currency 与 unit 一致、period 合法、evidence_ids 非空且都指向本答案证据、definition 非空
- 输出：每条 observation 的 findings 与 `mechanical_pass`；汇总只报机械通过/失败

## 当前结果（真实 workspace，只读）

- observation 2 条（CATL IQS_12 / IQS_16），**2/2 机械通过、0 findings**
- 明确声明：不是金融复核；来源充分性、缺失披露、反证质量、评分仍由人工审查负责

## 负例验证（mutation）

对真实 observation 逐项注入错误，检查器均能报出对应 code：

| 注入 | 结果 |
|---|---|
| 非评分答案写 score=5 | FAIL `score_on_unscored` |
| 证据 URL 改成 http | FAIL `evidence_url_invalid` |
| 证据发布日期改到 2027 | FAIL `evidence_after_cutoff` |
| 指标引用不存在的证据 | FAIL `metric_evidence_unknown` |
| 指标期末超出 cutoff | FAIL `metric_period_after_cutoff` |
| 货币指标缺 currency | FAIL `metric_currency_missing` |

## 用法

```powershell
python -B -X utf8 scripts/financial_mechanical_check.py --json runs/existing-list-onboarding-2026-10-18/financial-mechanical-check.json
```

## 边界

- 机械通过 ≠ 金融正确；不改变原答案、不写库、不联网。
- 后续可接入 profile 生产链，作为人工复核前的第一道门。
