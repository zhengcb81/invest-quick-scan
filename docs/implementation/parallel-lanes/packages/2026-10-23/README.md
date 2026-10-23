# 批次 2026-10-23：UI-APPLIC-BRIDGE-15

- 一张卡：[UI-APPLIC-BRIDGE-15.md](UI-APPLIC-BRIDGE-15.md) —— UI 小版本，把 APPLIC-RESOLVE-14 的三条接口建议（basis 采纳 / 显式 not_evaluated / decided_confidence 琥珀徽标）落进 `iqs-question-bank-ui-lab`。
- [inputs.lock.json](inputs.lock.json)：消费方基线 commit、双方文件字节级 hash、交接协议 hash。**派发前先核锁。**
- [manifest.json](manifest.json)：包登记（task_ids U01–U04，support_only，提供方与主仓只读）。
- 交接协议：`docs/implementation/parallel-lanes/handoff.schema.json#1.0.0` + [../2026-10-21/handoff-rules.md](../2026-10-21/handoff-rules.md)。
- 派发流程：核锁 → G1 设计确认 → **G2 所有者裁定（徽标语义，不得自签）** → G3 TDD 实现 → G4 parity 复核（applic 仓只读命令）→ **G5 所有者签收** → G6 交接（CLI `--verify-references` exit 0）。
