# JR1/JR3：备份兼容的单路径扩展

用户已授权 StockWiki 四文件且指定总控唯一 writer；源仓仍未改动。此文只申请一个额外路径，不扩大其他外仓权限。

新增持久审计表使 `scan_observations.sqlite` 的 `PRAGMA user_version` 从 1 升到 2。原 ACK JSON、ID、SHA 和历史行不改写，内部细节单独存储。现有备份恢复工具的 schema 上界为 1，真实隔离 `create_backup()` 已返回 `schema_newer_than_supported: scan_observations.sqlite: 2 > 1`。该失败保存在 `docs/implementation/intake/G3/2026-10-09-jr13/affected-backup-red-01/`，不得覆写。

候选修复只修改 `StockWiki/stockwiki/quick_scan_backup_manifest.py` 的一个值：

```diff
 SUPPORTED_USER_VERSIONS = {
     "scan.sqlite": 5,
-    "scan_observations.sqlite": 1,
+    "scan_observations.sqlite": 2,
```

其余 schema 上界、备份格式、权限和 owner 记录保持。版本 1 的备份仍可读；版本 2 的新审计表及原 ACK 由现有实际备份/校验/恢复流程保存。不执行真实库迁移或操作生产名单。

该一行候选仅写在 IQS 自有 `runs/r13a/sw` 副本。`affected-backup-green-01` 实际通过 61 项（观察、交付与备份三个测试文件），含新增审计与历史 ACK 保留、真实备份恢复、schema 1→2 失败回滚。仅为软件隔离验证，尚未完成联合链与集中审查。

源仓第五路径须人类授权后才可发布；四个已获批路径不重新请求权限。发布前重核最新源 HEAD/状态/原文件 SHA，不覆盖其他进程变动。

最新软件候选还通过受影响113项、完整联合18项和同次集中独审的实证接续；原61项是较早执行，不相加。可审阅完整候选补丁位于 `docs/implementation/intake/G3/2026-10-09-jr13/source-candidate.diff`；第五路径相对 c40de21 的实际 Git 内容仍只有上述一个值变化。这些证据不代替该路径的人类授权，也不关闭真实金融准确性和全局生产门。
