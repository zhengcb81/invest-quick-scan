# 批次 2026-10-24：APPLIC-GAP-CLOSE-16

- 一张卡：[APPLIC-GAP-CLOSE-16.md](APPLIC-GAP-CLOSE-16.md) —— APPLIC 侧小版本：parity `known_gaps` 证据驱动化；关闭 `ui_rewrites_basis`（依据 UI-BRIDGE-15 实测 10272 格全同值）、更新 `not_evaluated_absent` 为过渡声明。
- [inputs.lock.json](inputs.lock.json)：UI `0f3dc3e` 双文件 + applic 侧五文件 + 关闭依据日志的字节级 hash。**派发前先核锁。**
- [manifest.json](manifest.json)：挂 A01（本会话补登的任务），support_only，UI 仓只读。
- 交接协议：`docs/implementation/parallel-lanes/handoff.schema.json#1.0.0` + [../2026-10-21/handoff-rules.md](../2026-10-21/handoff-rules.md)。
- 门禁：G0 核锁 → G1 设计确认 → **G2 无新裁定项（如冒出语义问题必须停下来问所有者）** → G3 TDD → G4 8 步 CLI 链 + parity 对准 `0f3dc3e` → G5 所有者签收 → G6 CLI `--verify-references` exit 0。
- 元数据纪律（三包教训）：result_commit=payload 真值；每个数字/commit/路径可对磁盘或 git 对象；生成器为交付文件唯一写入方。
