# 批次 2026-10-21（iqs 泳道 · 1 包）

| 文件 | 用途 |
|------|------|
| `APPLIC-RESOLVE-14.md` | 施工卡：公司属性与题库适用性判定（数据化谓词 + 版本化快照）。**外发给 worker 的主文档** |
| `handoff-rules.md` | 交接规则：写边界、输入锁、红线、门禁、交接套件、CLI 校验、提交与消费对接。**与卡一并外发** |
| `inputs.lock.json` | 输入唯一字节清单（8 文件，raw SHA-256 + bytes）；worker 加载前逐文件校验 |
| `manifest.json` | 批次注册：task_ids=[S06,W15]、write_scope、authorized_paths、network_scope=none；`workers_dispatched` 由所有者派发后更新 |

- 背景：UI-BANK-EXPLORER-13 矩阵实测 10272 格中 10058 格 not_evaluated（仅 common 1 模块恒适用）；根因是 214 家公司缺结构化行业/阶段/类型属性、47 个非 common 模块的 `applies_when` 为不可机判 prose。本卡按所有者混合方案（先判定后缓存，D-A14-01）补齐判定资产。
- 依赖：QUESTION-BANK-UPGRADE-12（S04/S05 routing 层）；消费方：UI-BANK-EXPLORER-13。
- 全局协议：`docs/implementation/parallel-lanes/handoff.schema.json#1.0.0`、`review-protocol.md`。
