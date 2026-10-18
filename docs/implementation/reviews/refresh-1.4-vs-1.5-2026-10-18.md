# refresh 1.4 vs 1.5：24 题能不能一次 admission — 2026-10-18

只读核对 schemas/quick_scan/refresh-v1.4.schema.json 与 refresh-v1.5.schema.json 的 $defs。

| 约束 | 1.4.0 | 1.5.0 |
|---|---|---|
| BudgetExposureControl.protocol | stockqa.owner_budget_continuation/1.0.0 | 1.1.0 |
| purpose | const independent_comparison | const independent_comparison |
| mode | const explicit_repeat_exposure | 同 |
| cells | minItems 1 / maxItems 1 | minItems 1 / maxItems 1 |
| ComparisonCell.question_ids | maxItems 30 | maxItems 12 |
| max_new_http_requests | integer 1..350 | const 1 |
| Request.question_ids | maxItems 30 | （cell 侧限制 12） |

结论：
- 1.4 允许一个 cell 里放 24 题，一次 admission、一次 HTTP（max_new_http_requests 可设 1）；1.5 只能 12 题 + 1 次 HTTP，24 题必须 2 次 admission/2 次 policy revision。
- 两个协议都要求 purpose=independent_comparison，语义仍是“独立对比曝光”，不是“研究型画像”。如果坚持研究型语义，需要另找 work/research 合同（目前未定位到第三种 refresh 协议；1.4 是更宽的工作预算协议）。
- 因此 24 题画像的可行路径：
  - A. 1.4 单次 admission：1 个 cell 24 题、1 次 HTTP、1 次 policy revision；语义标 independent_comparison。
  - B. 1.5 两次 admission：2 个 cell 各 12 题、2 次 HTTP、2 次 policy revision；语义同上。
  - C. 先不跑画像：先做 S1–S5 搜索接线。

建议：先用 1.4 单次 admission 在副本演练（24 题 1 cell、1 HTTP），验证 admission 能通过；若成功，再只做一次真实 policy revision，成本约一次 24 题请求。若语义上必须“研究型”，则 1.4/1.5 都不满足，需要另立合同。
