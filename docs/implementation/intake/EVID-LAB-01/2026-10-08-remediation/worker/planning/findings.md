# EVID-LAB-01 findings

## 输入与授权
- 用户在分派会话中回答确认：授权在 `C:/Users/郑曾波/Projects/iqs-evidence-lab` 新建目录与
  仓库并作为唯一writer（施工卡要求“用户授权该目录后新建”）。
- IQS 开工观察：`master@6f7d7db5dbec75903319cabae8c69398f2272d0f`，脏树10项均为他人工作
  （findings/progress/task_plan/standard_answers + G3/opencode 未跟踪件），只读、不提交、不reset。
- 输入锁 `inputs.lock.json` 记录的 IQS base `c223cc92` 已前移；按卡只核对**文件级SHA**，
  不要求 HEAD 一致（README 亦声明“这些是观察，不是锁”）。

## 三归档结构（artifacts/mimo-pro-pilot-2026-10-07-*）
- main(01)：results 132 / blocks 39（pilot-matrix 27、pilot-repeat 9、pilot-thinking 3），
  answers 266（scored 160、insufficient_evidence 106）；ledger 156 reserved=132 model+24 search。
- thinking-all：results 42 / blocks 21（paired-off 12、paired-on 9），answers 115（scored 74）。
- jsonoff：results 12 / blocks 6（paired-jsonoff），answers 15（scored 10）。
- 合计 answers 396 = 326（两分区盲评）+ 70（独立重复）；模型HTTP 186、搜索 24、未知 0。
- normalization 仅 `full_json_fence`（thinking-all 3、jsonoff 2）；其余原始严格。
- Pro 思考臂复用 main 的 pilot-thinking 3 blocks（配对表 on 列跨归档）。

## 已发布口径（inputs-manifest 内 final-statistics.json，schema mimo_pilot_final/1）
- `median_company_seconds = round(median(block.wall_s for cell), 3)`（块中位数）。
- `aggregate_budget` = 三归档 budget 键求和：186 / 24 / 2.877381 / 0。
- `model_token_reference_usd` = 0.392538（三归档 by_model reference 求和，非实扣）。
- `failures` = 非valid块的 `parse_error|exception_type|state` 计数。
- by_model reference 由 ledger finished 事件 usage + route-snapshot 价目计算。

## review/join
- primary 196 + extension 130 = 326，互斥分区；join schema `mimo_pilot_source_support_join/1`。
- answer_sha256 = canonical fingerprint（sort_keys+紧凑分隔符的 SHA256）。
- 两分区是不同agent的分区盲评，**不是 inter-rater gold**；`not_human_or_world_gold=true`。
- claim_support: supported/partial/no_claims/unsupported；score_basis: supported/insufficient/not_scored。

## 关键约束记忆
- 48次实际 temperature=0.7（固定StockQA客户端默认注入），数据不改、不重发。
- 价格=公共参考（peak/undiscounted），套餐实扣未知；上限与token参考不可相加。
- 历史 snippet 已清理：事实支持只能 `not_verifiable` / `agent_review_only`。
- 原报告工具 `tempfile.TemporaryDirectory(dir=b.ROOT)` 写其模块ROOT → 不得直接 import 进 IQS 路径。
