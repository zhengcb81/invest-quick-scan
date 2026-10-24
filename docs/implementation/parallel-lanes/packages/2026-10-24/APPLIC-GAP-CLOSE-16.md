# APPLIC-GAP-CLOSE-16｜parity known_gaps 证据驱动化与关闭（APPLIC 侧小版本）

- 批次：`2026-10-24`
- 写范围（唯一）：`C:/Users/郑曾波/Projects/iqs-applic-lab`
- 消费输入（只读）：UI 仓 @ `0f3dc3e`（UI-APPLIC-BRIDGE-15 交付，其 U5 已实测两个 gap 的关闭条件）
- 起源：UI-APPLIC-BRIDGE-15 open_items（handoff.json）明确预留：

  > known gap ui_rewrites_basis：关闭条件已具备（parity basis_gaps 10272 格全部 X->X 同值映射，见 logs/known_gaps_assessment.log）；关闭动作待 applic 侧小版本在其 parity_check.py 执行
  > known gap not_evaluated_absent_from_route_decisions：关闭条件未完全具备（UI 显式 not_evaluated 分支已上线；待提供方 export_ui 显式写出 not_evaluated decision）

- 交接协议：`docs/implementation/parallel-lanes/handoff.schema.json#1.0.0` + [../2026-10-21/handoff-rules.md](../2026-10-21/handoff-rules.md)

## 1. 目标

parity_check 的 `known_gaps` 目前是**静态文字**（不随实测结果变化，见 `src/applic/parity_check.py:150-166`）。本卡把它改为**证据驱动**，并落地 UI-BRIDGE-15 已验证的两个事实：

1. **gap `ui_rewrites_basis` → 已关闭**：UI resolver（BRIDGE-15 建议 1）已优先采纳 decision 自带 basis。证据：UI 卡 parity 运行 2/3 `basis_gaps` 10272 格全部 `X -> X` 同值映射（17+214+8409+428+1204），改写对 `-> routing_gate_below_threshold` / `-> routing_rule_matched` 计数 0。
2. **gap `not_evaluated_absent_from_route_decisions` → 过渡声明**：UI 显式 `not_evaluated` 分支已上线（BRIDGE-15 建议 2，缺席兜底保留）。当前快照 `not_evaluated=0`，故 export_ui 是否显式写出**在本卡数据上不可观测**；本卡不切换导出约定，仅把 gap 描述更新为「UI 已支持显式四态；导出切换留待首个 not_evaluated>0 的快照」。

## 2. 必做交付（缺一不可）

| # | 交付物 | 位置 |
|---|---|---|
| G1 | `known_gaps` 证据驱动化：`compare()` 输出 `known_gaps` 为动态结构（每条含 `gap/closed_or_transitional/detail/evidence`），依据本轮 `basis_gaps` 实测：全部同值映射 ⇒ `ui_rewrites_basis` 判 `closed`；任一改写对计数>0 ⇒ 判 `open` 并列出改写对与计数 | `src/applic/parity_check.py` |
| G2 | gap 语义更新：`ui_rewrites_basis` 标 closed（引用 UI 卡评估日志为关闭依据）；`not_evaluated_absent_from_route_decisions` 改为 transitional 描述 | 同上 |
| G3 | 新增测试：同值映射 → closed；构造改写对 → open；not_evaluated gap 的 transitional 文案；旧断言（known_gaps 静态两条目）相应更新 | `tests/` |
| G4 | 复跑 8 步 CLI 链（verify_inputs → … → parity_check --ui-repo … --ui-commit `0f3dc3e`）全 exit 0，新日志入 `docs/handoff/APPLIC-GAP-CLOSE-16/logs/` | 交接套件 |
| G5 | 交接套件：handoff/artifacts/tests/cleanup/summary/report + logs；har Hash 磁盘实算 | `docs/handoff/APPLIC-GAP-CLOSE-16/` |

## 3. 红线

1. 只写 applic 仓；UI 仓 @ `0f3dc3e` 只读（parity_check 已有 dont_write_bytecode + dirty 检测，保持）。
2. **不改判定语义**：三值逻辑、快照、导出格式一概不动；export_ui 的 not_evaluated 写出约定**本卡不切换**（数据上不可观测，切了就是无证据变更）。
3. `ui_rewrites_basis` 判 closed 的**唯一合法依据**是本轮 parity 的 basis_gaps 全同值 + 改写对计数 0 —— 不许只改文案。
4. G4 的 parity 必须对准 `0f3dc3e`（UI 仓当前 HEAD；若验收时 HEAD 又前移，以交接时点 HEAD 为准并在 report 注明）。
5. 测试模板不填假通过；sha256 磁盘实算，禁占位符。
6. **元数据纪律**（三包教训固化）：result_commit = payload commit 真值；声明的每个数字/commit/路径与磁盘或 git 对象一一对应；生成器为交付文件的唯一写入方。

## 4. 门禁（按序，不得自签）

- **G0**：主控核 inputs.lock.json（UI `0f3dc3e` 的 contracts.py=4852544f…、resolver.py=469ef282…、applic 侧五文件 hash）。
- **G1**：设计确认 —— known_gaps 新结构 schema 草案（字段、判定条件、evidence 引用方式）经主控核对。
- **G2**：**本卡无所有者新裁定项**（closed/transitional 的语义已在 UI 卡 G2 与 interface-proposals 中定过；如实现中冒出新的语义问题，须停下来问所有者，不得自定）。
- **G3**：TDD 实现（先红后绿；158+新增全绿）。
- **G4**：8 步 CLI 链 + parity 对准 `0f3dc3e`；`state_consistent=true`、`state_mismatch_count=0`、`ui_repo_writes=0`、basis_gaps 全同值、`ui_rewrites_basis=closed` 有据。
- **G5**：所有者签收（演示 + 局限披露后原话落盘）。
- **G6**：交接套件 + 主控 CLI `--verify-references` exit 0。

## 5. 验收用例

| ID | 用例 | 期望 |
|---|---|---|
| AC-01 | 真实快照 parity（10272 格） | `known_gaps[ui_rewrites_basis].closed=true`，evidence 引用本轮 basis_gaps（5 组同值映射合计 10272，改写对 0） |
| AC-02 | 构造改写场景（stub resolver 改写 basis） | `closed=false` + 列出改写对与计数（fail-closed：证据不足不许报 closed） |
| AC-03 | not_evaluated gap | transitional 文案含「UI 已支持显式四态；导出切换待首个 not_evaluated>0 快照」 |
| AC-04 | 旧消费者兼容 | parity_check JSON 输出的既有字段（state_consistent 等）不变；known_gaps 由 list[str] 升级为 list[dict] 时，同步更新本包消费方与文档 |
| AC-05 | UI 仓零写入 | parity 后 UI `git status` clean、无新 __pycache__、`ui_repo_writes=0` |
| AC-06 | 全量回归 | applic 仓 158+新增测试全绿 |

## 6. 输入锁（详见 inputs.lock.json）

- UI 仓 `0f3dc3e`：`adapters/contracts.py` 8120 B sha `4852544f…`；`adapters/applicability_resolver.py` 5460 B sha `469ef282…`
- applic 侧：`parity_check.py` 9655 B sha `31a0a0b4…`；`export_ui.py` 475 B sha `6d55da77…`；`interface-proposals.md` 9908 B sha `045822bb…`；`ui-export.json` 8431811 B sha `83f1a5e3…`；`design/functional-tech.md` 24559 B sha `c58cf61b…`
- 关闭依据：UI 卡 `docs/handoff/UI-APPLIC-BRIDGE-15/logs/known_gaps_assessment.log` 2563 B sha `72908ea2…`

任一 hash 与磁盘不符 = 停，先核实。

## 7. 非目标

- 不改 UI 仓（含其 R1 元数据修正 —— 那是 UI 卡的活）
- 不切换 export_ui 的 not_evaluated 写出约定
- 不改快照/谓词/属性数据；不做真实数据矩阵接入（另卡）
- 包级门 S01/S04/S05/S06/U01–U04 不由本包关闭；`production_ready=false` 不变

## 8. 风险

1. **R1** UI 仓 HEAD 前移（如 R1 修正落地）：parity 以交接时点 HEAD 为准并留证；若 R1 修正改变了 resolver/contracts（不应 —— R1 是元数据-only），须先重核关闭条件。
2. **R2** known_gaps 结构升级（list[str]→list[dict]）可能破坏本包内其它消费方 —— G3 前先 grep 全部消费点并同步。
3. **R3** `--ui-commit` 校验失败（HEAD 前移后 exit 2）：这是设计行为（fail-closed），换新 HEAD 重跑并在 report 注明即可，不得删该校验。

## 9. 参考

- `src/applic/parity_check.py:91-167`（compare/known_gaps 现状）
- UI 卡评估日志（关闭条件的实测证据）
- `docs/interface-proposals.md` 建议 1/2（两条 gap 的起源与关闭路径）
