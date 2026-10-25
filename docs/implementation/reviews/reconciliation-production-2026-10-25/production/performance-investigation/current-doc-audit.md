# 当前文档一致性审查（2026-10-25）

审查者：`/root/review_bank21`，与总控及产品修复者分离。取样时间：`2026-10-25T10:33:05.7725848Z`。本次只读审查根 PWF、接手入口、状态板、新实操手册、BASIC 持久审查证据和本轮薄运行记录；未运行产品、测试、付费 API 或数据库查询，未修改 PWF、源码、账本、租约或其他 writer 的文件。本文不是整轮验收、金融签收或生产完成证明。

结论：需要修正三组当前表述。BASIC 的独审闭合与提交绑定没有发现新的文档矛盾；真实 cold/缓存恢复仍未通过。已通过的软件正例和 0-HTTP 预检不得替代真实运行结果。

## 1. [P1] 当前 Next Step 仍停在第一次 cold 启动前后的旧状态

- `task_plan.md:9` 仍写“cold正在执行”；`:15` 仍让接手者检查安全响应、强退后禁网恢复。
- `docs/implementation/handoff-for-new-agent.md:9–11` 仅给正常 cold→安全输出→恢复的理想顺序，没有说明本次已在本地检索包装失败。
- 相比之下，`docs/implementation/parallel-lanes/packages/STATUS-BOARD.md:5` 已正确写明首试因 observer 缺 `request` 停下、原账本保留 unknown、模型未发送。
- 原薄记录 `runs/r25-live/failed-pretransport-01/live-cold-exit.json` 为 `exit_code=1`、`phase=cold`，结束于 `2026-10-25T10:18:13.3791767+00:00`。stderr 外层只报告 `external_search_unresolved`，本日志自身不足以单独证明底层是否发出 HTTP。

风险：弱模型可能把第一次 cold 当成仍在运行，等待不存在的模型安全输出，或直接执行当前“强退后恢复”，而不是处理原账本明确的本地未发送路径。

最小修法：只更新当前 R3/Next Step 和 handoff 顶部，明确第一次 cold 已失败、真实成功尚未发生，并引用 `engine-fix/pretransport-retry-plan.md`。该计划在本次取样时仍明确是计划，不是已执行事实：先保留本地 0-transport 离线证明和源码 pin；再经原公开 `reconcile_budget_attempt` 结算 `confirmed_not_sent`；保留原 unknown operation/receipt；等待原真实 lease 到 `2026-10-25T10:48:06.134260Z` 后经原 `recover_expired`；同账本、同 work/预算/题目输入，以新 query ID 和新 session 重试。只有实际取得新安全输出后才进入原来的禁网恢复与幂等封存验收。不要把重试称为缓存命中，也不要提前标 R3/R4 complete。

## 2. [P2] 当前 findings/progress 夹杂已解决的开工调查状态

- `findings.md:7` 称 handoff 顶部仍为 10/18；当前 handoff `:1–3` 已有 10/25 优先入口并明确覆盖旧暂停方向。
- `findings.md:8` 称 10/24 manifest 仍未实施/未派发；实际 `docs/implementation/parallel-lanes/packages/2026-10-24/manifest.json:85–96` 已是 `engineering_accepted`、`workers_dispatched=true`，包含六项修复与独审证据引用。
- `progress.md:19` 仍称“已启动” BASIC 独审，与同文件 `:3–8` 已闭合的最终结果混在同一当前节。

风险：接手者重复修正已完成的文档或重启 BASIC 审查，而不是继续当前生产实验。

最小修法：把上述条目明确标为“开工时发现，现已修复”，保留初始事实和最终证据链接。无需删除历史记录或重写旧审查的失败结果；也无需增加小节点审查。

## 3. [P2] 实操手册需要区分“真实不确定”与“证实未进入传输”

`docs/implementation/shared-engine-operations.md:24–27` 的不重发、保留原账本、原安全输出恢复规则正确，但没有链接本次本地 pre-transport 例外的公开处置路径。`:3` 又把当前状态指向尚未更新的根 Next Step，形成断开的接手链。

最小修法：保留现有不确定请求守卫；另加一段明确分流：未知网络结果或缺少原安全响应时不得猜测未发送；仅当有实际零 native transport 证明时，按上述原公开 reconcile→真实 lease 到期→recover_expired 计划续行。链接完整计划，不复制一套新 owner、SQL/时钟旁路或新预算重发方案。原 `resume_shared_engine` 仍不得接受没有安全输出的假恢复；本地未发送重试与有安全输出的缓存恢复是两个实验阶段。

## 核实为一致、无需增门的内容

- 当前 PWF/交接/状态板都承认已有用户授权继续有效；`owner_authority_verified=false` 明确是观察器能力边界，没有发现需要再次向用户索权的当前依据。handoff 从第 22 行起已整体标成历史，不应把下方旧审批/暂停文字重新当作当前门。
- 当前入口明确保留其他 writer 的 10/10 README 与未跟踪归档，不整仓 add、不清理不明归属文件；本轮没有发现当前指令要求覆盖他人 writer。
- BASIC `final.json` 为 `passed/open_findings=[]`，仍保留初轮失败，不代签 G5、不授予金融或生产资格；`commit-binding.json` 的五份源码 blob SHA 与该 final 的候选源码 SHA 一一一致。final 的“提交后由总控绑定”是当时审查说明，独立绑定文件已承接，不应篡改原审查历史。
- 新手册正确区分研究导出、原检查点、封包 ready/delivered 和 StockWiki 接收；也未把软件 E2E 或预检宣称成真实金融准确性通过。
- 性能报告现已区分两次不同 pins 的预检：第一次 116.1735 秒仅在 metadata 中保有内嵌快照；第二次 80.9808 秒有归档原文件。没有实施性能代码，因此不是优化效果或受控 A/B 结论。

## 取样文件 SHA256

文档可能由总控继续更新。以下仅绑定本审查取样，不要求后续文件永久不变；修正文案后应据实更新当前入口，不回写旧证据。

| 文件 | SHA256 |
|---|---|
| `task_plan.md` | `046498a2155d190b9d1cbca246355b3523a27927f91b72ea202551edc6906b01` |
| `progress.md` | `6bbab82af5cee2beddbd97f20dc94ebbee31325c5ad010cf8d660aec80dc58da` |
| `findings.md` | `86925b62b6feada5a1a67160e180bdbad7ba3c05b4934209c992ecdd20611888` |
| `docs/implementation/handoff-for-new-agent.md` | `ace0e8285ed916423b56d3a9ab355baa492db0d95353bc2e014f2f344c3eda4a` |
| `docs/implementation/parallel-lanes/packages/STATUS-BOARD.md` | `2f0e76a3419aeb81d0e3041700413e54b5aa7bc7bb12b2d6e3f46c6f6c31eebe` |
| `docs/implementation/shared-engine-operations.md` | `4bee6a24a953a0f0d9376391e2957965bf579d702418b9f9dd5bf87309040ce8` |
| `docs/implementation/parallel-lanes/packages/2026-10-24/manifest.json` | `6d82c88479bdfe6a06b965821804ed70bc51cdd904758966df8e2662362550ab` |
| `docs/implementation/reviews/reconciliation-production-2026-10-25/basic/final.json` | `9d812be5269377354e9557dd4f47c7cd67af789a2fe702a0f8a6877dbb1a1c20` |
| `docs/implementation/reviews/reconciliation-production-2026-10-25/basic/commit-binding.json` | `4115bcd739002b2a276d2f4756a8e87bff66fd82459d373b9cd207cb6e0c75fa` |
| `runs/reconcile-production-2026-10-25/engine-fix/pretransport-retry-plan.md` | `37d22618fad966bbcbf93f8efea2685461cfe28727eee6f6953d94027fe44910` |
| `runs/r25-live/failed-pretransport-01/live-cold-exit.json` | `15dac3efbb2673f75a7490af0a7143b8db5acc4681a0e3dadb238beff38d779f` |
| `runs/r25-live/failed-pretransport-01/preflight.json` | `2fc8e4f10191aab024629d64f26b911b7edc513bf03b474e8a6a0c55a846673a` |

没有新增临时副本或待清理文件。本文仅请求上述三组文档修正；不构成整轮最终签收，也不证明 retry 计划已经执行。
