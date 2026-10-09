# JR1/JR3 发布接续：只剩备份上界单路径许可

这是同一大节点的接续说明，不新增小节点审查，不是写入授权。StockWiki 源仓尚未改动；用户已授权四文件并指定总控独占 writer，第五文件的一行修改仍待答复。

## 不再重做的交付

读取本目录 `README.md`、`acceptance.md`、`compatibility-recheck.md`，以及 `docs/implementation/intake/G3/2026-10-09-jr13/acceptance.json` 与 `final-snapshot/execution-lock.json`。候选、源锁、实际生成的两轮各31个包及原回执/子进程日志均为合成软件验收证据。不能把它们改称真实金融数据、真实身份 DTO/golden 或供应商计价验证。

原失败、原独审与 first recheck 保留；修复包括新公共 ACK 事务落库、独立内部审计、严格 raw/direct JSON 入口、锁内版本检查、accepted 原引用、历史原 ACK 只读对账、混合/竞争槽整批回滚。旧 ACK 不投影、不改 SHA/ID/时间；历史非公共格式只在 receipt 侧标 `legacy_wire_pending`，QA 仍严格拒绝。当前独立正常新 ACK 闭环另由联合测试证明。

受影响最终批次113P，联合最终批次18P，静态通过；各是独立原执行，不能加总成单批测试数。复用精确执行字节与同一次集中审查，不为未变化的小文件重复跑全仓/UI/收费测试。

## 源文件与许可

| StockWiki 路径 | 写权限 | 最终原件位置 |
|---|---|---|
| `stockwiki/quick_scan_import.py` | 用户已授权 | `final-snapshot/candidate/stockwiki/quick_scan_import.py` |
| `stockwiki/quick_scan_observations.py` | 用户已授权 | `final-snapshot/candidate/stockwiki/quick_scan_observations.py` |
| `tests/test_quick_scan_observations.py` | 用户已授权 | `final-snapshot/candidate/tests/test_quick_scan_observations.py` |
| `tests/test_quick_scan_delivery.py` | 用户已授权 | `final-snapshot/candidate/tests/test_quick_scan_delivery.py` |
| `stockwiki/quick_scan_backup_manifest.py` | **单行额外许可待答复** | `final-snapshot/candidate/stockwiki/quick_scan_backup_manifest.py` |

唯一条件补丁：`SUPPORTED_USER_VERSIONS["scan_observations.sqlite"]` 1→2；相对基线 Git 内容仅此值变化。其他版本上界/备份协议不改。没有这行许可不要发布四文件半批，否则新审计库 schema2 会被现有真实备份工具拒绝。具体依据及原RED见 [backup-scope-extension.md](backup-scope-extension.md)，可审补丁与 SHA 见 intake 中 `source-candidate.diff/json`。

## 获许可后的动作

源发布工作目录：`C:/Users/郑曾波/Projects/StockWiki`。总控/PWF/材料目录：`C:/Users/郑曾波/Projects/invest-quick-scan`。本接续不写 StockQAbyLLM；不要把私有快照误当源仓执行目录。

1. 先重读四份根PWF的最新块，确认第五路径许可和 writer 独占仍成立。不要代其他 harness 写仓库。
2. 只读核最新 StockWiki HEAD、完整状态、五路径工作树/Git原 SHA；基线是 `c40de21403720306ba21edbf71b9634a40ee58f8`，QA源为 `bc41908e4cdc44c13fefda97f3118e5434aed5f8`。当前源文件清单见 intake `source-candidate-diff.json` 和 source-preflight原件；如果 HEAD/源码/配置发生变化，先查实际差异、重新定界，不覆盖或强制重置别人的改动。
3. 核验 `execution-lock.json` 对应五件候选和正式独审文件 SHA，只把上述五个候选原字节复制到已获权路径。记录写前/写后完整状态、精确五文件 byte/Git SHA。源若完全匹配已验证基线、候选与依赖锁，复用本批测试/审查证据；源码有新变化时按影响范围补大节点回归，不盲称通过。
4. 按用户要求在沙箱外正常 Git hooks/commit/push；不绕过 hooks、不全仓 `add -A`、不暂存其他进程/未知文件。只暂存上述五个路径，检查 staged Git blob 与受审执行字节一致。hook若修改未授权路径或另一 writer出现，暂停发布并报具体冲突，不替别人清树。确认远端分支实际 commit，保留原命令/退出/终态回执。
5. 更新 IQS 的 `task_plan.md`、`progress.md`、`findings.md`、`docs/implementation/handoff-for-new-agent.md`，追加实际 StockWiki commit/remote/schema2发布回执，正常提交推送；此前 `source_written=false` 的接收/测试原件不能回改成已发布。

不操作真实公司名单/生产库，不主动迁移真实 schema1，不下载文档，不调用收费 API。G3/F05/L03、真实 identity/facts/query owner golden、真实准确性/计价和 TH/IN 源写授权仍按各原门独立签收；本修复发布不自动解锁全池一键启动。

## 测试环境恢复与复现

本批仅使用 IQS 自有短根 `runs/r13a`。严格清理终态以 intake `cleanup-receipt.json` 为准；原 `.gitignore`、真实库、共享TEMP、外仓、原未知 `opencode.json` 均不属于清理范围。原进程已终态才可清理，不停止别人的进程。

旧 `prepare.py`/joint helper 是一次性固定根实验脚本，标签不可复用。根清理后不要盲跑旧命令或重建老目录来伪造原结果。要复现时创建**新独占短根**，按 `execution-lock.json` 导出固定非秘密源、精确执行 guard/fixture/adapters和六模块锁，明确保持 manifest 的 Git LF 与独立旧 authority CRLF 执行 SHA 区别。配置仅为已登记 inert/synthetic 替身，env去真实keys、TEMP/插件/字节码/网络边界同原 guard。先固定输入再执行，测试运行期间不得改候选；记录新名字的实际结果，保留原证据。Python audit guard 不是整个 Windows/原生工具的安全认证。
