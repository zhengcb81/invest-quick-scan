# B01-b phase-1 独立只读复核

日期：2026-10-07
审查范围：只读复核 B01-b phase-1 报告与其归档矩阵/回执。**这不是 G3 全门审查，也不关闭 B01 或 G3。**
审查方式：独立审查者复核，IQS 总控另用只读 Python 汇总复算；未修改 StockQA、StockWiki 或其他外仓文件，未运行项目测试、联网搜索、模型请求或数据库写入。

## 结论

终版矩阵的 540 条结果、题目唯一性、各状态总数、18 个公司×方法单元格的分数和引用计数均可复算。**“样本不足以证明打包策略达标，因此暂时保留逐题策略”这一保守操作结论成立。** 这不代表逐题策略已经通过金标准或盲评。

审查原快照状态：**needs_revision**（报告的用量、重跑来源与若干证据表述需更正或收窄）。完成复核后，已在原报告 §9 追加更正和边界说明，避免继续沿用无法复算的口径；但历史重跑结果缺少独立快照/逐题响应绑定，真实账单也未完成对账，证据缺口无法靠文字修复。故 B01 phase-1 仍不是可用于胜出策略/成本结论的完整验收材料。

## 主要复算

- `method_results.json` 有 540 行，主键 `(company, method, question_id)` 540 个且唯一；每个 3×6 公司/方法组合都有 30 个唯一题目。
- 状态合计与报告一致：331 `scored`、88 `insufficient_evidence`、110 `missing_in_response`、8 `error`、3 `not_applicable`。逐格分数和引用数也与报告表格一致。
- `method_results_run3_base.json` 与终版均为 540 行、主键集合相同。重跑 ledger 的 30 个 chunk 覆盖 270 个唯一题键：`group_5` 90、`group_10` 90、`batch_30` 90。终版相较 base 有 234 行值变化（`batch_30` 90、`group_5` 90、`group_10` 54）；变化行均落在重跑覆盖键内，另有 36 个重跑键的值与 base 相同。
- 已保存主回执的 prompt token 合计为 **10,008,297**：run-1 无效轮 3,894,261 + run-2b 部分轮 1,058,876 + smoke 602,716 + 合并 run-3/重跑回执 4,452,444。最后一项已包含 run-3 base，不能再把 3,843,236 重复相加。这个合计尚不含报告提到的其他探针；报告写的约 6.5M 因此与已保存回执不符。
- 引用计数逐格相符，合计 420。按 540 个结果槽计算为 77.8%；按 430 个非 missing 结果计算为 97.7%。现有资料不能复算报告所写的合并“约 88%”，而且“有引用”不能替代对引用是否支持具体事实主张的审查。
- 从主 ledger 请求项读取的 provider `cached_tokens`：run-3 base 的 240 项中位数 12,928，其中 88 项不超过 128；大组重跑的 30 项中位数 128，其中 18 项不超过 128。这证明部分回执记录了 provider 的缓存 token 字段，不能单凭该字段证明搜索缓存、应用答案缓存或实际账单节省。

## 发现

| ID | 严重度 | 位置/触发条件 | 观察与影响 | 处理要求 |
|---|---|---|---|---|
| B01-P1-01 | 重要 | phase-1 报告 §1；汇总已保存的 run 回执 | 报告称全程约 6.5M prompt tokens；已保存的主回执合计 10,008,297，且未含其他探针。费用/额度结论不能据此核实。 | 对齐报告口径与回执；注明哪些轮次纳入、哪些探针遗漏，以及 MiniMax 控制台实际额度/费用对账状态。不得把配额消耗推算成未核实的现金价格。 |
| B01-P1-02 | 重要 | `method_results.json`、`method_results_run3_base.json`、`method_ledger.json`、`method_plan.json` | ledger 可覆盖 270 个重跑题键，但 36 个与 base 同值的结果无法分辨是沿用旧值还是新请求恰好同值；终版答案行没有 `response_id`/`attempt_id`，plan 未记录 `max_completion_tokens`，且无独立重跑结果快照。可复算矩阵，不能独立证明每个重跑结果都由所称的 131072 设置生成。 | 报告收窄来源/参数结论；记录历史证据无法补齐的部分。后续实验把生成参数、chunk ID、response ID 与逐题结果放入不可变 run sidecar，并保留独立 rerun snapshot。 |
| B01-P2-01 | 一般 | phase-1 报告 §3 | 各格引用计数可复算，但合并“约 88%”无明确分母；可复算的两个常见分母分别得到 77.8% 与 97.7%。 | 删去该合并百分比，或写明计算字段与分母；不要把引用存在率表述为事实支持率。 |
| B01-P2-02 | 一般 | phase-1 报告 §6 缓存发现 | 缓存字段分布并非稳定的“约 16K/请求”；也没有搜索缓存和应用答案缓存的正交命中/失效实验。provider 的 `cached_tokens` 不等于已证明的费用节省。 | 限定为“部分 provider 回执报告缓存 token”；将三类缓存效果与费用留到独立实验验证。 |
| B01-P2-03 | 一般 | phase-1 报告 §6 大包完整性发现 | HK `batch_30` 终版是 1/30，而诊断文件有一次 30/30 且 `finish_reason=stop`。两份材料说明保存的输出不同，但没有足够的逐请求输入 hash/完整参数绑定来把差异确定归因于服务端非确定性。 | 改称“观察到输出完整度不同，原因尚未确定”；保留缺题风险与逐题默认，不作根因断言。 |

## 验收场景状态

- **BENCH-01.A03：数据结构部分通过。** 六种方法与每格 30 个唯一 ID、missing/error 状态可复算；这不证明完整公开入口、费用与导入链通过。
- **BENCH-01.A05：未执行。** 没有冻结 gold、双人盲评、MAE、claim 抽样支持率或裁决记录；因此只能报告 `inconclusive`。
- **BENCH-01.A01、A02、A04、A06、A07、A08、A09：本次未完整验收。** 冻结/gold/预算、实际送模片段绑定、缓存正交实验、公司级耗时、真实价格和配额对账、隔离导入/清理、搜索源×打包策略交叉等均不能由这份 phase-1 报告单独关闭。
- **BENCH-02：未运行。** 本次没有做零预算/未知额度的公开入口零外发测试。
- **G3：未关闭。** `tasks.json` 规定 G3 依赖 L03 与 W11；W11 已 verified，L03 尚待 owner 明确启动，且 G3 还需真实中断/租约/费用预留/备份恢复证据。本复核只覆盖 B01 phase-1 资料，不替代这些验收。

## 复现记录与快照

复算读取 JSON 后按 `(company, method, question_id)` 建唯一键，比较 base/final 行值；把 ledger 的每个 chunk 的 `question_ids` 展开为同一主键集合；从 run receipt 的 `usage_total.prompt_tokens` 求和。所有输入均只读。

IQS：`master@8143cd9bb7e0cc4224c684cd9fba948723bf1e6e`；审查时仅有既有未跟踪 `opencode.json`。StockQA：`master@6a9ff13864ebb160d5c4ab3cf2f42155d9f4aa99`；已有工作树状态保留未动。审查没有修改这两个仓库的状态。

SHA-256：

| 文件 | SHA-256 |
|---|---|
| IQS `reviews/B01/phase1-report-2026-10-07.md`（审查时原快照；随后 §9 增加复核补充） | `66c5acd551219ff206866b894aa3945f4af82373084273df359b1a15e92ce2ac` |
| IQS `reviews/B01/phase1-report-2026-10-07.md`（当前含 §9 补充） | `5e13b00d7cd3276e01aa64bb81132c95ecbc6695e30010a1d5e2271452f73169` |
| IQS `reviews/IQS-lane/B01b-freeze-manifest-2026-10-07.md` | `935a47a1c629a1181241b28a23a64d8c7794e276e43b66e4473ef4ef7a3cb963` |
| StockQA `pilot_runs/b01b_method_2026-10-07/method_results.json` | `02db7d5f37b5d6747c29362df59f82e33e5fd9b62ec4a291dcf8ccdc9496a2ad` |
| StockQA `pilot_runs/b01b_method_2026-10-07/method_results_run3_base.json` | `610f3219a14268724b92299a33568c8aef3400d0971cc953d7cfae5cb274566d` |
| StockQA `pilot_runs/b01b_method_2026-10-07/method_ledger.json` | `117975ffe26dcd3045435425924dcede69d8bb799f068c57e4094541f704cbe8` |
| StockQA `pilot_runs/b01b_method_2026-10-07/method_ledger_run3_base.json` | `6c865a9dd0cbe62d267c671eb05320f69ea6cbfc1cf22317734ce8af6cb35125` |
| StockQA `pilot_runs/b01b_method_2026-10-07/method_run_receipt.json` | `dc77daffb4c04c714ad5c1b5d487cf2ffbd5b8c42a71df72f381ee27d16fb500` |
| StockQA `pilot_runs/b01b_method_2026-10-07/method_run_receipt_run1_invalid.json` | `6e1921e4c1b7b098b6f8688ad6b0ee80fbe56bbf61f89603eaa484eceaff7eab` |
| StockQA `pilot_runs/b01b_method_2026-10-07/method_run_receipt_run2b_partial.json` | `68f64d7209c48352782dc491316f07962ea0b1e4f58518b3b08aa55e27df9593` |
| StockQA `pilot_runs/b01b_method_2026-10-07/method_run_receipt_smoke.json` | `60bf7a3b2bb98c52d18406a61aeed6c91b85acfec99296d65c101e577484fb96` |
| StockQA `pilot_runs/b01b_method_2026-10-07/method_plan.json` | `e0f2665ad8c389b2673e65d08bdd41d76f9b04a29e1d11a86b12283e1d6f4f13` |
| StockQA `pilot_runs/b01b_method_2026-10-07/diag_batch30_hk.json` | `fa58c9f758d33d59185aa30d1b08309b81fb7bb4dd3ad35d29ccba44daa73c9e` |

未运行测试：本批是只读数据/报告审查，没有源码变更。下一步是修订或限定 B01 phase-1 报告中的上述说法，并在 owner 明确启动 L03 后再做完整 G3 大节点审查；不重跑相同 live 矩阵来弥补历史回执缺失。
