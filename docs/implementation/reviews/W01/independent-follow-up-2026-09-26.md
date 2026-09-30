# W01 StockWiki quick-scan SQLite 整改复审

- 审查者：`/root/g0_independent_review`
- 日期：2026-09-26
- 被审仓库：`C:\Users\郑曾波\Projects\StockWiki`
- 范围：复核 W01-IR-01、W01-IR-02、W01-IR-03；StockWiki 全程只读，未执行生产迁移。
- 结论：**verified（W01 本地 SQLite 身份/迁移范围）**。三项 finding 均已关闭，无剩余 P1/P2。

## 冻结快照

| 文件 | SHA-256 |
|---|---|
| `StockWiki/.gitignore` | `9E320C206A5259F0DC5C78B73B4455F20E28979FD349328DCAAE9695C691061F` |
| `StockWiki/stockwiki/quick_scan_store.py` | `F0D3F4241B8F251A6996970A6AF7EADD49463991EBD3AA88163950CDC8866C0E` |
| `StockWiki/tests/test_quick_scan_store.py` | `274C709126626C6C0CFA9ADE43C0F71B6913A94B90D168203779131C4BC393B5` |
| `invest-quick-scan/schemas/quick_scan/identity.schema.json` | `B0F1931B4EB6CDCEF0FAB0E6F7AC5D6DB707686555F363301AEA0511C9AE0A82` |
| 只读真实样本 `StockWiki/data/companies/TSM.N/classification.yaml` | `EFC254F85C0FB0201B0E6C33EFD60142ED9019D5EA1FBE1DB59E9DD9B0E32AE0` |

## Finding 关闭情况

### W01-IR-01 — P1：关闭

当前 `_verify_schema()` 除表集合、列集合和 `foreign_key_check` 外，还将所有 `quick_scan_%` table/index/trigger 的规范化 SQLite DDL 与由当前 `_create_schema()` 在内存库生成的完整签名做集合等值比较。

我重新构造了原反例：五张表的名称和列名全部相同，但没有 PK、FK、NOT NULL、CHECK、索引或触发器，并设置 `user_version=1`。`migrate()` 现拒绝，错误为 `quick-scan database schema constraints or indexes differ`。

新增参数化测试还分别移除了实体 PK、实体 NOT NULL、证券实体 FK、基础证券复合 FK、市场 CHECK 和 ticker index，六种同列名伪 schema 均被拒绝。完整签名也覆盖本轮新增的三个基础证券触发器。

### W01-IR-02 — P1：关闭

schema 创建、`PRAGMA user_version=1` 和 `_verify_schema()` 现在均位于同一 `BEGIN IMMEDIATE` 的 try 块中；只有验证成功后才 commit。

我重新注入 post-create verifier 异常。迁移抛错后由新连接读取到：`user_version=0`、`quick_scan_%` 对象数量为 0。原先“调用失败但 version 1/五表已持久化”的反例已消失。

### W01-IR-03 — P2：关闭

`quick_scan_security` 新增表级 CHECK，只有 ADR/GDR/CDR 可持有 `ordinary_security_ref`，且禁止自引用。INSERT/UPDATE trigger 要求引用目标是同一实体的 `ordinary` security；另一个 trigger 禁止仍被存托凭证引用的普通股被原始 SQL 改为其他类型。

独立重放结果：

- ADR→ADR：拒绝，`ordinary base security required`。
- ADR 自引用：拒绝，`ordinary base security required`。
- 原始 SQL 将 ADR 的 ref 改指 ADR：拒绝。
- 原始 SQL 将已被引用的基础普通股改为 ADR：拒绝，`referenced ordinary security cannot change type`。
- 原有跨实体基础证券引用仍由复合 FK 拒绝。

## 独立测试

使用唯一系统 TEMP `C:\Users\郑曾波\AppData\Local\Temp\w01f21ba7bcd`，设置 `PYTHONDONTWRITEBYTECODE=1`、将 `STOCKWIKI_REAL_CLASSIFICATION` 指向只读 TSM.N 样本，并显式传入 `--basetemp`：

- `python -X utf8 -m pytest -q -p no:cacheprovider --basetemp=<unique-temp> tests/test_quick_scan_store.py tests/test_schema.py`
  - 结果：`29 passed in 1.86s`。
- `python -m ruff check --no-cache stockwiki/quick_scan_store.py tests/test_quick_scan_store.py`
  - 结果：`All checks passed!`。
- 运行结束后安全删除已解析且确认位于系统 TEMP 下的目录：`CLEANED=True`。
- TSM.N 源 YAML 只读，SHA-256 保持不变；迁移只作用于 pytest 临时副本。

## 判定与限制

DB-01 的迁移幂等、完整 schema 失败关闭、提交前验证回滚和旧 YAML 保护已闭合；ID-01/02/04、DB-06 及 ADR 同实体/普通股基础关系均有通过的正负例。W01 可以在其本地存储范围标记 verified。

本结论不认证 W02 主档导入、W03 名单业务命令、W05 观察导入，也不认证生产数据迁移、跨仓事务或真实运行库备份恢复。StockWiki 工作树中其他进程的大量改动未纳入本次结论。
