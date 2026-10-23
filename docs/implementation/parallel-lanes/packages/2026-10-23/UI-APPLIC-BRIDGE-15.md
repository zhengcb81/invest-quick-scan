# UI-APPLIC-BRIDGE-15｜UI 小版本：四态适用性矩阵的接口落地（三条建议）

- 批次：`2026-10-23`
- 提供方（只读输入）：APPLIC-RESOLVE-14 @ `C:/Users/郑曾波/Projects/iqs-applic-lab`（已验收，G5 signoff 在库）
- 消费方（本卡唯一写范围）：`C:/Users/郑曾波/Projects/iqs-question-bank-ui-lab` @ `9ab7a3398459dd92b181eb19929b753964a57bf9`
- 起源：APPLIC 侧 `docs/interface-proposals.md`（3 条建议，sha256 见 `inputs.lock.json`）。按其「变更流程声明」：主控转交 → UI 卡 owner 评审 → UI 仓按自身流程合入 → applic 侧 parity 复核。
- 交接协议：`docs/implementation/parallel-lanes/handoff.schema.json#1.0.0`（Draft202012，逐层 `additionalProperties:false`）+ [../../2026-10-21/handoff-rules.md](../../2026-10-21/handoff-rules.md)（含「禁止占位符 sha256」条款）。

## 1. 目标

让 UI 的适用性矩阵真正呈现 APPLIC 快照的四态与证据等级，修复三处已被定位的信息丢失：

1. **basis 采纳**：resolver 不再把 unknown 覆写成 `routing_gate_below_threshold`、不再把 `not_applicable` 显示成 `routing_rule_matched`；优先采纳 decision 自带的 `basis` 原值（`attribute_unresolved` / `negative_evidence_not_verified` / `no_rule_fail_closed` 等 9 种）。
2. **显式 `not_evaluated`**：decision 携带 `state: "not_evaluated"` 时按四态渲染，不再被归一成 unknown；保留「缺席 = not_evaluated」旧行为兜底。
3. **`decided_confidence` 琥珀徽标**：`ApplicabilityCell` 新增 `decided_confidence: Optional[str] = None`；`assumed` → 该格加琥珀「待确认」徽标（state 不变）；`to_dict()` 对 None 剔除字段，旧消费者 JSON 逐字节不变。

三条建议的原文、现状行号、建议代码与向后兼容分析**以 `interface-proposals.md` 为准**（本卡不复述实现细节，避免第二真源）。

## 2. 必做交付（缺一不可）

| # | 交付物 | 位置（UI 仓） |
|---|---|---|
| U1 | resolver 三处修改（basis 采纳 / 显式 not_evaluated / confidence 填充） | `adapters/applicability_resolver.py` |
| U2 | `ApplicabilityCell.decided_confidence` 字段 + `to_dict` 剔除约定 | `adapters/contracts.py` |
| U3 | 渲染：琥珀「待确认」徽标 + 图例释义（9 种 basis + 3 级 confidence） | UI 渲染层 |
| U4 | 测试：每条建议的正例+反例+向后兼容例（旧数据无 basis/无 confidence 不受影响） | UI 仓 tests |
| U5 | parity 复核：`applic.parity_check` 对新 UI HEAD 跑通，`ui_rewrites_basis` 与 `not_evaluated_absent_from_route_decisions` 两个 known gaps 的关闭或更新 | 只读跑 applic 仓命令，结果写本卡交接日志 |

## 3. 红线

1. **不改 applic 仓任何文件**（含 parity_check 的 known_gaps —— 关闭动作由 applic 侧后续小版本做）；不改主仓。
2. **不改 `state` 归一逻辑**：`applicable/not_applicable` 原样、其余归 unknown 的既有语义保持（仅新增显式 not_evaluated 分支）。
3. **旧消费者逐字节兼容**：新字段默认 None 且 `to_dict()` 剔除；未携带新字段的旧导出渲染结果不得变化（须有测试锁死）。
4. 渲染颜色语义沿用既有约定：绿 `#1f9d55` 已评分、琥珀 `#b8860b` 证据不足/待确认、灰 `#9aa0a6` 未评估、蓝 `#2563eb` 适用、阴影灰 not_applicable、紫 `#7c3aed` 合成、红 `#c0392b` 不匹配。徽标只加不改。
5. 测试模板不填假通过；失败/跳过如实报。
6. 所有 sha256 按磁盘字节实算，禁止占位符。

## 4. 过程与门禁（按顺序，不得自签）

- **G0 派发**：主控锁定 `inputs.lock.json`（本卡同目录），确认提供方/消费方 commit 与 hash 与磁盘一致。
- **G1 设计确认**：UI 侧实现 agent 给出修改方案（resolver 分支、dataclass 字段、渲染位置、测试清单），主控核对与 interface-proposals.md 三条建议的一致性；有出入先记录差异再动手。
- **G2 所有者确认（必须）**：琥珀「待确认」徽标的**语义与文案**（含图例位置）需所有者裁定落盘（原话+时间戳），agent 不得自签。参考 G2-2 先例：assumed=琥珀「待确认」。
- **G3 实现（TDD）**：先红后绿；UI 仓自身测试全绿；worktree clean。
- **G4 parity 复核**：只读运行 `python -B -X utf8 -m applic.parity_check --ui-repo <UI仓> --ui-commit <新HEAD>`（在 applic 仓目录执行），要求 `state_consistent=true`、`state_mismatch_count=0`、`ui_repo_writes=0`（该值现为实测）；把输出原样存入交接日志。若 parity 暴露新差异，先修 UI 侧再复跑。
- **G5 签收（必须所有者）**：演示 + 已知局限披露后由所有者原话签收，worker 记录但不自签。
- **G6 交接**：UI 仓按 `handoff.schema.json#1.0.0` 出 `docs/handoff/UI-APPLIC-BRIDGE-15/` 套件，主控跑 `parallel_handoff_cli.py --verify-references` 且 exit 0 后才算交齐。

## 5. 验收用例（对照 §2）

| ID | 用例 | 期望 |
|---|---|---|
| AC-01 | unknown 格（basis=`attribute_unresolved`） | cell.basis 原值呈现；不再出现 `routing_gate_below_threshold` |
| AC-02 | not_applicable 格（basis=`predicate_false_with_counter_evidence`） | basis 原值；reason 不被固定文案覆盖 |
| AC-03 | 显式 `state:"not_evaluated"` decision | 四态渲染（灰），basis=`no_rule_fail_closed` 原值 |
| AC-04 | 缺席 decision（旧导出） | 行为与今天完全一致（回归锁死） |
| AC-05 | decision 带 `confidence:"assumed"` | 琥珀「待确认」徽标出现，state 不变 |
| AC-06 | decision 无 confidence / null | 无徽标；`to_dict()` 输出 JSON 与旧版逐字节一致 |
| AC-07 | 全量 ui-export.json 灌入（10272 格） | parity 复核通过；applicable 1846 / unknown 8426 / not_applicable 0 / not_evaluated 0 与导出 distribution_after 一致 |
| AC-08 | 9 种 basis 释义 | 图例/抽屉全部给出释义，无 `routing_gate_below_threshold` 的错误归因残留 |

## 6. 输入锁（详见 inputs.lock.json）

- UI 仓基线 commit `9ab7a3398459dd92b181eb19929b753964a57bf9`（含 `adapters/contracts.py` sha `d15d0a81…278b20`、`adapters/applicability_resolver.py` sha `373c5571…66d8e9c`）
- 提供方导出 `demo/ui-export.json`（8431811 B，sha `83f1a5e3…ba3f63`，来自 snapshot `applicsnap_d296902c…`）
- 提供方建议书 `docs/interface-proposals.md`（9908 B，sha `045822bb…a42ea57`）
- 交接协议 `handoff.schema.json`（sha `ed38a65a…15c0e`）与 `2026-10-21/handoff-rules.md`（sha `fe9a2bb4…35eae`）

任一输入 hash 与磁盘不符 = 停止派发，先向提供方核实。

## 7. 非目标

- 不改 applic 仓（含快照、引擎、parity_check 代码与 known_gaps）
- 不做评分/路由/题库改动；不做 UI 视觉重设计
- 不引入框架依赖（UI 仓零框架约定不变）
- 不关闭 S01/S04/S05/S06/U01–U04 的包级门；`production_ready=false` 不变

## 8. 风险与开放问题

1. **R1** parity_check 的 `ui_rewrites_basis` gap 只能在 UI 合入后由 applic 侧关闭 —— 本卡只负责让关闭条件成立，交接时如实写「gap 关闭条件已具备/未具备」。
2. **R2** `not_evaluated` 显式化后 route_decisions 条数会开始包含四态格；消费端若有条数断言需同步（AC-07 用 distribution_after 交叉核对）。
3. **Q1** 琥珀徽标文案（如「待确认」vs「推断」）与图例位置由 G2 所有者裁定，不在本卡预设。
4. **Q2** 若 UI 卡评审认为三条建议某条应拒（如渲染性能），按 interface-proposals「变更流程声明」把拒绝理由落盘即可，不强制全收。

## 9. 参考

- 提供方建议书：`iqs-applic-lab/docs/interface-proposals.md`（术语对照表、9 种 basis、3 级 confidence 语义）
- 提供方 G2 裁定：`iqs-applic-lab/design/owner-approval.json`（G2-2 assumed=琥珀「待确认」、G2-3 反证门槛）
- 消费方现状：`adapters/applicability_resolver.py@9ab7a33`（第 44–61 行为三条建议的定位行）
- 先例：UI-BANK-EXPLORER-13（同 UI 仓、同交接协议、同红线风格）
