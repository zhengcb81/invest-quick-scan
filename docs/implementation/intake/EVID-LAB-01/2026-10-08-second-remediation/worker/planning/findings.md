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

## 2026-10-08 残余整改发现（LR-01..LR-06）
- custom 期间被 normalize_period 丢掉 start/end → 同年不同日期判 pass；修复后缺边界一律abstain。
- 历史答案校验由“有没有 answer_sha256”开关决定 → 删hash即可改答案；修复后 hash 只是额外校验。
- strict_loads 只拦 parse_constant → 1e400 变成 inf 仍被当正数方向 pass；修复后统一入口拒非有限数。
- check_sources 排除未知窗口后按“已知全冲突”发布 fail → 未知来源被默示为冲突；修复后abstain。
- structure.duplicate_json 硬编码 historical_model_output → synthetic 题包记录错标；
  修复后全document按 source_category 统一映射并校验（FX-034 未收集 → none）。
- 草案 generation.output_limit=10000 而费用公式按5000 → 声明上界 0.48276/0.49 低估；
  复算 0.82296，上界改为 0.83（价格与输入上限未变，未取新价）。
- 文档曾标 semantic-rules/2 而输出带 semantic-rules/1：本轮起规则版本单一来源（__init__）。
- 费用上界取“覆盖实际生成上限”而非降生成上限：历史 completion_tokens 最大值即 10000，
  且 finish_reason_length_is_failure=true，降上限会改变实验能力。
