# W01 StockWiki quick-scan SQLite 独立审查

- 审查者：`/root/g0_independent_review`
- 日期：2026-09-26
- 被审仓库：`C:\Users\郑曾波\Projects\StockWiki`
- 审查方式：只读源码/工作树，测试仅写唯一系统 TEMP；未运行生产迁移、未修改 StockWiki。
- 结论：**needs_revision**。DB-01、ID-01、ID-02、ID-04、DB-06 的现有正例通过，但存在两个 P1 迁移完整性缺口；另有一个 P2 ADR 基础证券语义缺口。

## 审查快照

| 文件 | SHA-256 |
|---|---|
| `StockWiki/.gitignore` | `9E320C206A5259F0DC5C78B73B4455F20E28979FD349328DCAAE9695C691061F` |
| `StockWiki/stockwiki/quick_scan_store.py` | `7B49DB4C2CB74C3CD4AA3E9A152F4A79E694C26F71BEA5869E9B5F15C66C5807` |
| `StockWiki/tests/test_quick_scan_store.py` | `5D97B5D1C704A0D64BA98E59A92D1FB65C29763ABA4BDF743F067FD637A5DA3A` |
| `invest-quick-scan/schemas/quick_scan/identity.schema.json` | `B0F1931B4EB6CDCEF0FAB0E6F7AC5D6DB707686555F363301AEA0511C9AE0A82` |
| 只读真实样本 `StockWiki/data/companies/TSM.N/classification.yaml` | `EFC254F85C0FB0201B0E6C33EFD60142ED9019D5EA1FBE1DB59E9DD9B0E32AE0` |

`.gitignore` 仅增加 `/data/quick_scan/*.sqlite*` 与 `/data/quick_scan/backups/`。W01 产品实现只新增 `quick_scan_store.py`，测试只新增 `test_quick_scan_store.py`；本报告不把 StockWiki 工作树中其他进程的大量改动归入 W01。

## 独立验证

使用唯一系统 TEMP `C:\Users\郑曾波\AppData\Local\Temp\w01r8fc80b11`，设置 `PYTHONDONTWRITEBYTECODE=1`、`STOCKWIKI_REAL_CLASSIFICATION` 指向上述只读真实样本，并显式传入 `--basetemp`：

- `python -X utf8 -m pytest -q -p no:cacheprovider --basetemp=<unique-temp> tests/test_quick_scan_store.py`
  - 结果：`15 passed in 0.84s`。
  - 当前文件只收集到 15 项；无法复现交接消息所称的 21 项，但没有 skip。
- `python -m ruff check --no-cache stockwiki/quick_scan_store.py tests/test_quick_scan_store.py`
  - 结果：`All checks passed!`。
- 测试后安全删除经解析且确认位于系统 TEMP 下的唯一目录，结果 `CLEANED=True`。
- 真实 `classification.yaml` 的测试前后 SHA 保持为 `EFC254…32AE0`；测试只在 `tmp_path` 中迁移其副本。

现有测试确认了：独立 SQLite 路径、重复迁移、旧 YAML 副本不变、外键启用、跨实体 ADR FK 失败、同名/同 ticker 不合并、空 company-wiki/正式 profile、额外 formal evidence 参数拒绝、事务回滚、较新版本拒绝及连接在公开实现路径关闭。

## Findings

### W01-IR-01 — P1：`user_version=1` 可用“同列名、无约束”伪 schema 绕过验证

- 位置：`StockWiki/stockwiki/quick_scan_store.py:188-198`。
- 触发：建立五张表，表名和列名与 `_COLUMNS` 完全一致，但不设置 PRIMARY KEY、FOREIGN KEY、NOT NULL、CHECK 或索引；设置 `PRAGMA user_version=1` 后调用 `migrate()`。
- 实测：`migrate()` 返回 `False`，即接受该数据库；随后同一 `entity_id='ENT_A'` 可插入两行，查询得到 `duplicate entity count 2`。
- 原因：`_verify_schema()` 只比较表集合、列名和当前数据的 `foreign_key_check`。没有外键的库自然不会产生 foreign-key violation；列名相同也不能证明主键、唯一键、检查约束、外键或索引存在。
- 影响：损坏、错误生成或被降级的 v1 库会被当作权威身份库，直接破坏实体唯一性、证券归属和 ADR 同实体约束。`test_newer_or_corrupt_database_fails_closed` 仅覆盖错误列名，未覆盖约束被移除。
- 修复要求：版本为 1 时验证完整 schema 语义，至少核对 `table_info` 的类型/notnull/PK、`foreign_key_list`、必需 unique/index，以及关键 CHECK/DDL 签名；缺少任一身份约束必须失败关闭。
- 验证要求：为每类关键约束各构造“列名完全相同但移除一个约束”的 v1 数据库，确保打开和读写入口都拒绝。

### W01-IR-02 — P1：schema verification 在提交之后执行，验证失败仍留下 version=1 数据库

- 位置：`StockWiki/stockwiki/quick_scan_store.py:176-185`。
- 触发：让 `_create_schema()` 正常完成，但故障注入使 `_verify_schema()` 抛出异常。
- 实测：`migrate()` 抛出 `injected post-create verify failure`，但重新打开数据库后 `PRAGMA user_version=1` 且五张 quick-scan 表都已持久化。
- 原因：代码在第 180 行先 `commit()`，第 184 行才验证；异常不再进入 rollback 范围。
- 影响：迁移调用方观察到失败，但磁盘状态已标为当前版本。下次启动可能进入版本相等分支；结合 W01-IR-01 的弱验证，会接受不完整约束。该行为不满足预审包的“迁移在事务中进行、迁移失败不留下半套 schema”。
- 修复要求：在同一 `BEGIN IMMEDIATE` 内创建 schema、设置版本、完成所有可执行的 schema/foreign-key 校验，验证通过后才 commit；任一验证失败必须 rollback 至 version 0、零张新表。
- 验证要求：新增 post-create/pre-commit 验证故障注入，异常后从新连接断言 user_version=0 且无 quick-scan 表。

### W01-IR-03 — P2：`ordinary_security_ref` 可指向 ADR 或自身

- 位置：`StockWiki/stockwiki/quick_scan_store.py:260-295`；数据库复合 FK 只保证目标 security ID 属于同一 entity。
- 触发：先写入 `SEC_ADR1(security_type='adr')`，再写入 `SEC_ADR2(... ordinary_security_ref='SEC_ADR1')`；另写入自引用 `SEC_SELF(... ordinary_security_ref='SEC_SELF')`。
- 实测：两种输入均成功并可读回。跨实体引用确实被现有复合 FK 拒绝。
- 影响：C01 将该字段定义为“ADR 对应的基础普通股 security_id”；同实体但非 ordinary 的目标和自引用会产生错误换算 lineage。后续估值或证券价格归一化可能沿无效关系计算。
- 修复要求：当 `ordinary_security_ref` 非空时，在同一写事务内要求目标已存在、同 entity、`security_type='ordinary'` 且不等于自身；可进一步限制只有存托凭证类型允许设置该字段和 ratio。
- 验证要求：保留现有跨实体负例，并新增 ADR→ADR、自引用、普通股携带 ordinary ref 的负例及 ADR→同实体 ordinary 正例。

## Case 判定

| Case | 结论 |
|---|---|
| DB-01 | **needs_revision**：正常迁移与 YAML 保护通过；P1 的伪 v1 schema 与 post-commit 验证失败破坏 fail-closed/原子性。 |
| ID-01 | 现有 A/H 一实体两证券正例通过；底层实体唯一性仍会被 W01-IR-01 绕过。 |
| ID-02 | 同名/同 ticker 不自动合并、重复 security ID 改挂另一实体均通过。 |
| ID-04 | 空 company-wiki/formal profile 可用且不建正式目录，通过。 |
| DB-06 | 未声明的 formal accepted/source manifest 参数被拒绝且未落正式工件，通过。 |

在修复两个 P1 并新增相应反例前，W01 不应标记 verified。W01-IR-03 建议同时修复；若延后，必须在 ADR 被任何估值或价格归一化消费者使用前关闭。
