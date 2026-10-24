# APPLIC-LLM-JUDGE-20-R2｜匹配逻辑简化裁定（所有者 2026-10-24）

- 批次：`2026-10-24`
- 性质：**所有者裁定（R2）+ 落地方案**。取代 [APPLIC-LLM-JUDGE-20-R1.md](APPLIC-LLM-JUDGE-20-R1.md) 的 B3 冲突表与「三方一致 / 复核队列」口径
- 实施仓：`iqs-applic-lab`（唯一写根；主仓只记录裁定与验收）
- 交接：`iqs-applic-lab/docs/handoff/APPLIC-LLM-JUDGE-20/`（R1+R2 合并交付，主控 CLI `--verify-references` exit 0）

## 0. 所有者原话（2026-10-24，R2）

> 请你改一个地方，一个公司是否与某一个题库匹配的逻辑太复杂了，如果第一轮LLM里面有大多数说这个公司与某个题库是匹配的，就认为匹配就好了，不用再复核或调用其他复杂逻辑了。我不介意在每个题库的公司池里多增加几家公司，没有什么坏处的。

## 1. 裁定

| # | 规则 | 说明 |
|---|---|---|
| R2-1 | **第一轮 LLM 多数判适用 ⇒ 匹配** | 票 = 主判定 + 附加第一轮判定；有效票 = answered + yes/no + 置信度 ∈ {high, medium}；yes 票**严格过半**（`1/1`、`2/3` 成立；`2/4` 平票不成立）⇒ `applicable`（basis `llm_judged_applicable`） |
| R2-2 | **其余一律回落谓词，不改写谓词结论** | 多数 no / 平票 / unsure / 低置信 / 报错 / 无票 ⇒ 谓词 applicable 仍 applicable、not_applicable 仍 not_applicable、unknown 仍 unknown（basis 记 `llm_unsure_or_no` / `llm_error` 供审计） |
| R2-3 | **取消第二轮复核** | 不再互证、不再冲突升级、不再产出复核队列行；`review_queue_rows` 恒为空（复核队列文件仍产出，0 行） |
| R2-4 | **LLM 永不产出 `not_applicable`** | 原「三方一致 ⇒ not_applicable」路径取消；历史值 `llm_corroborated_not_applicable` / `llm_no_conflict` / `llm_conflict_single_no` 仅保留读取兼容 |
| R2-5 | 取舍依据 | 宁可多放进几家公司，也不为「谁能进池」做二轮裁决——误放进池的公司由后续研究自然过滤，代价远低于漏掉一家 |

**不动的部分**：override 最高优先；无规则格 `no_rule_fail_closed` 不得被 LLM 救活；置信度门槛 high/medium；
金标门（`judge_modules --golden`，判题质量的一次性门槛，R1 B2 口径：稳定格 10/10 多数 + 不稳定格单列）
不受影响；快照 schema 仅新增 `llm_ref.votes`（yes/no/total）记账字段。

## 2. 落地（applic lab）

- 代码：`src/applic/llm_merge.py`（`MERGE_SEMANTICS = r2_owner_2026-10-24_first_round_majority_yes`）——
  `merge_cell` 改为「多数 yes ⇒ applicable；其余回落谓词」；删除 `_escalate_no`；`review_queue_rows → []`；
  `_llm_ref` 增记 `votes`。`judge_modules` / `run_eval` 仅更新说明文案与提示；复核队列照常写空文件（兼容）。
- 测试：`tests/test_llm_merge.py` 重写为多数裁定 + 队列停用（含反例：平票不算多数、多数 no 不改写谓词、
  no 永不产出 not_applicable、低置信不计票、unsure 不进分母、历史 basis 可读）；
  `tests/test_llm_channel_cli.py` / `tests/test_llm_snapshot_channel.py` 的 R1 冲突/队列断言按 R2 改写。
  **全量：323 tests OK**（pytest 同为 323 passed + 234 subtests）。
- 实调复跑（856 格 = 214 家 × 4 模块，回放存档）：applicable 1846 → **1924**（+78 = 多数 yes 升级）；
  `llm_judged_applicable` 138、`llm_unsure_or_no` 679、`llm_error` 0；**复核队列 0 行**；
  快照无任何 `llm_corroborated_not_applicable` / `llm_no_conflict` / `llm_conflict_single_no`。
- 文档：`design/llm-judge-channel.md` §2 置顶 R2 段（原 §2.0/§2.1/§2.2 标注历史），§7/§10 文案同步；
  `docs/handoff/APPLIC-LLM-JUDGE-20/report.md` §9 记录 R2 与重生成产物。

## 3. 验收

| ID | 用例 | 结果 |
|---|---|---|
| R2-AC-01 | 第一轮多数 yes（含 1/1、2/3）⇒ applicable，且不产复核行 | ✅ `TestMajorityRuling` |
| R2-AC-02 | 平票 / 2-4 / 多数 no ⇒ 回落谓词，谓词结论不变 | ✅ `test_tie_is_not_majority`、`test_two_of_four_is_not_majority`、`test_majority_no_never_rewrites_predicate` |
| R2-AC-03 | LLM 永不产出 not_applicable | ✅ `test_no_never_yields_not_applicable` + 实调快照审查 |
| R2-AC-04 | 复核队列恒空（run_eval / judge_modules / shadow 三路径） | ✅ `TestReviewQueueDisabled`、`test_majority_no_falls_back_without_review_queue`、实调 0 行 |
| R2-AC-05 | 金标门口径不变、实调 10/10 仍有效 | ✅ report §8 / 金标日志 |
| R2-AC-06 | 主控 CLI `--verify-references` exit 0 | ✅ 本包 handoff（package `APPLIC-LLM-JUDGE-20`） |

## 4. 已知边界 / 后续

1. **UI 侧**：快照可能首次出现 basis `llm_judged_applicable` / `llm_unsure_or_no` / `llm_error`，
   UI 的 basis 图例释义尚未补（原 open item 不变；不阻塞本裁定）。
2. **金标门**仍是判题质量门；若所有者希望连门禁也简化，另裁。
3. 历史 R1 台账（`data/llm_judgments/review-queue-*.json` 旧行、复核页）原样保留，不改写。
