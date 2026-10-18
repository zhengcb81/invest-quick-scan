# COST-LEDGER-11 验收记录

- 验收时间：2026-10-18（本会话复核）
- 交付方：外部 Lab C:/Users/郑曾波/Projects/iqs-cost-ledger-lab，分支 codex/cost-ledger-11
- payload commit：6b2df76063869119c71414812b4b86c765034849
- review fixes commit：cc2ae03e44bc5108900e81ed8c9387b150d6fa1b
- metadata/HEAD：fb44349c505cf697594ec28614bcb2c3f15b5ac1
- handoff 状态：complete；review approved（round-01 发现已修复并由同一 reviewer 复核）

## 总控复核（本会话实际执行）

| 检查 | 命令/方式 | 结果 |
|---|---|---|
| handoff 形状/声明范围 | scripts/parallel_handoff_cli.py + manifest | valid，errors=[] |
| artifacts sha256/bytes | 按 repo 根逐项重算 | 155/155 匹配 |
| input lock | tools/input_lock_tool.py verify | 11/11 verified，exit 0 |
| 单元/集成/E2E | unittest discover -s tests -t . | 124 tests OK，exit 0 |
| casebook | iqs_cost_ledger evaluate（PYTHONPATH=src） | 34/34 matched，exit 0 |
| commit 可达性 | git merge-base --is-ancestor | 6b2df76、cc2ae03 均为 HEAD 祖先 |
| worktree | git status --porcelain | clean（0） |

注：handoff verification 记录 unit suite 为 116，实际套件为 124（summary 亦写 124）；以实测 124 为准，不影响验收。

## 接口与输出

- 输入：frozen ledger exports（4 个真实 ledger）+ 合成 fixtures；全部经 inputs.lock.json 锁定。
- 输出：projection / audit report / validate / bundle；零网络、零付费调用、零模型调用。
- `invoice_verified=false`、`all_invoice_amounts_unknown=true` 固定，不得当作已核实发票金额。

## 已知边界（接受）

1. controller-frozen `docs/handoff/COST-LEDGER-11-ledger-projection.json` 源提交中仍不存在；response_unpriced / outcome_uncertain / reserved_in_flight 只在合成 fixtures 与转换器输出中有证据，未伪造真实行。该占位出现后需在主线段复跑 evaluate。
2. 四个真实 ledger 未导出 policy_version，policy_refs 保持为空，不补造 policy_missing。
3. budget_revision 行完整字段集未逐字核验，行内容保留在各 projection 的 source_note。
4. 真实 ledger 偏粗：所有真实行 settled_cost_unknown，报告带 usage_unknown_not_zero；round_half_up 与供应商账单可能有差异，重算仅作参考估计。

## 决定

ACCEPTED — 离线成本/预算审计工具交付合格，非生产资格，不合并进 IQS 产品代码。

后续动作：
1. 控制器冻结 projection 后，主线段复跑 evaluate；
2. 接入前把 projection/audit 协议版本化并明确 consumer；
3. 保留 invoice_verified=false 与 usage_unknown 标注，禁止把参考估计当发票金额。

## 证据位置

- Lab handoff：C:/Users/郑曾波/Projects/iqs-cost-ledger-lab/docs/handoff/COST-LEDGER-11/
- 包卡：docs/implementation/parallel-lanes/packages/2026-10-18/COST-LEDGER-11.md
