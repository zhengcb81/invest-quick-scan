# SW-READY-01：集中整改卡

这是本包一次验收后的整改，不新增小节点审查。当前未授权总控写StockWiki；原harness继续或用户指定新唯一writer后开工。总控已查收完整交付，但暂不签收实现：48/48工件匹配，基线`master@04dfc5190589a8bbe224a47e94b045779c884b80`，主体`0d76dc39e8d9d53d451b1ce84c7147b0dd1bd2c5`。用户若选择总控接管，本卡精确文件清单即拟写范围；开工先重核当前HEAD与状态，不能回退到旧基线覆盖后续工作。

先读[独立报告](intake-review-2026-10-07.md)、[原施工包](../../parallel-lanes/packages/2026-10-07/SW-READY-01.md)、[共同规范](../../parallel-lanes/packages/2026-10-07/handoff-rules.md)。本次实跑[7项反例/正例](acceptance_cases.py)：**6 fail / 1 pass / 3.83s**；其中UI单条件为静态断言，其余为真实Python路径。WAL已提交数据备份正例通过。初轮有缺inert导入配置的fixture错误，已单独存档，最终没有setup错误；不能拿初轮当6个产品反例。

## 六处问题及允许的最小方案

| ID | 已复现行为 | 整改边界与验收 |
|---|---|---|
| SWR-1 | restore已允许空目标，最后又因target.exists拒绝 | absent和existing-empty均能恢复；非空、并发填入、junction/越界均拒绝；不覆盖历史，不凭旧空检查盲删目录。失败保持原目标并清理自己的staging |
| SWR-2 | 仅format/files/digest的外来manifest被prune删除 | 校验版本化schema/必填结构、受管目录和manifest name、路径唯一、安全性和文件信息；**哈希自洽不是owner证明**。prune仅处理create流程留下可核验归属的完成备份；外来/未知/损坏/partial/链接目录一律跳过。旧备份仍按明示兼容规则可只读校验/恢复；缺归属不自动授予删除权，不做自动adopt/批量清理 |
| SWR-3 | 最后rename异常在try之外，留带成功manifest的partial | finalize也在受管错误处理内；注入失败不残留可被list/prune当完成的partial。list/prune显式区分完成与partial，不能用移除异常或忽略失败报绿 |
| SWR-4 | 两个真实公开导入accepted的synthetic subject观察，同field只剩后导入的高分 | 保留subject/revision、scope/security/listing、题义/口径版本、模型与时点的可比边界；未选择唯一合法variant时明确ambiguous/unknown或展示全部，不能静默拼成一个分数/恢复判断。两个subject可见；无明确选择时>=8不能靠后导入高分入选。保持同issuer多挂牌一行与不同发行人不并名；不越范围宣称W14完整比较/TTL已完成 |
| SWR-5 | UI仅硬编码一条条件，AND/OR恒等 | 可增删至少两条分项条件，AND/OR传统一W07服务器规则，不在浏览器重算分数。query/snapshot key包含完整条件及combine，改变任一leaf使快照失效。实际浏览器验证“一项过、一项不过”：AND无命中，OR有命中；unknown仍不变5 |
| SWR-6 | 旧9f552a67真实search返回snapshot交新同版本search，page2拒绝 | 无新条件请求保持旧query hash/读取协议，或显式兼容读取旧snapshot；不能静默放宽不同查询snapshot匹配。旧实际producer分页IDs/顺序不丢不重；新多条件快照错查询仍拒绝。协议变更必须明确版本，旧对象含义不改 |

SWR-4的反例使用producer `_workspace/_observation/_package`，经真实`import_package`得到两个accepted ACK后再投影；不是手造profiles或StockWiki真实身份golden。SWR-6使用旧Git源码真正产生snapshot，不只手算hash。UI当前反例为静态证据，整改后须真实浏览器行为，不能把静态改字当UI通过。

## 精确拟写范围（仅获准的唯一writer）

StockWiki源码：`stockwiki/quick_scan_backup.py`、`stockwiki/quick_scan_backup_manifest.py`、`stockwiki/quick_scan_profiles.py`、`stockwiki/quick_scan_query.py`、`stockwiki/quick_scan_rows.py`、`stockwiki/ui_quick_scan.py`、`stockwiki/ui_static/app.js`、`stockwiki/ui_static/index.html`、`stockwiki/ui_static/styles.css`。

StockWiki测试：`tests/test_quick_scan_backup.py`、`tests/test_quick_scan_profiles.py`、`tests/test_quick_scan_query.py`、`tests/test_ui_quick_scan.py`、`tests/test_e2e_quick_scan_ui.py`。

StockWiki文档：`docs/quick-scan-backup-restore.md`、`docs/ui.md`，以及已有`docs/handoff/SW-READY-01/`文档/日志/索引。如确需上述之外文件，先说明具体缺口和路径再由用户授权；不改IQS/PWF、生产库/名单/配置、安装镜像、其他harness文件或中央C06/C07 schema。

## 同批实施与测试

1. 复用已交付实现与本次六反例，先RED，逐缺陷做最小修复与定向GREEN。保留原失败和原990日志，不能回写成全覆盖。
2. 一组集中单元/集成覆盖：空/非空/并发目标、外来/partial/坏manifest不删、finalize失败；多subject/模型/语义/作用域/倒序时点的可比边界；旧真实snapshot+新多条件兼容。保留WAL正例。
3. 一次真实浏览器离线E2E覆盖多条件AND/OR、条件变动快照失效、unknown/N/A不补分、entity去重与变体明确显示。不给弱模型另造UI规则引擎。
4. 完成后在独占临时workspace运行仓现有大节点全量门一次，再统一更新handoff/artifact hashes、源码commit、RED/GREEN原始日志、独立审查结论。后续只做必要增量，不为每个小修改重跑完整门。

测试必须独占manifest根；所有真实存储/旧交付只读，备份/恢复/prune反例只操作自有fixture。退出所有服务/浏览器/子进程；逐路径核绝对范围、归属和无junction，再保存证据清理。禁止按mtime或pytest编号清共享TEMP，不下载公司文档/调用API。全量日志成功不抵消本次固定反例或旧隔离事故。

## 交接与状态

保持W12/U01/U02整包partial：TTL与replacement upstream、真实QA C06→W05 ACK→UI、执行侧快照/费用恢复仍待原依赖，不能伪造完成。交回本仓完整handoff，scope为源仓相对路径，明确本次6项闭合和仍未运行的边界；总控只更新自己的PWF与集中联调状态。

总控冻结导出manifest和原日志位于`docs/implementation/intake/SW-READY-01/2026-10-07/`。先用公开导出脚本重建（只读Git，不复制本地配置或真实库），然后运行7测试：

```powershell
# 在IQS根目录；新root必须尚不存在，不覆盖别的测试目录。
python -B -X utf8 docs/implementation/reviews/SW-READY-01/export_runtime.py --repo 'C:/Users/郑曾波/Projects/StockWiki' --manifest docs/implementation/intake/SW-READY-01/2026-10-07/export-manifest.json --work-root '<IQS>/runs/sw-ready01-intake-<unique>'
$env:IQS_SW_READY_WORK_ROOT = '<IQS>/runs/sw-ready01-intake-<unique>'
python -B -X utf8 docs/implementation/reviews/SW-READY-01/guarded_tests.py
```

导出器逐件复核producer字节hash及旧query版本，仅生成固定`providers: []`导入fixture，不是可运行模型配置。原7测试针对冻结未修版本预期6 RED/1 GREEN；修后新producer先独立登记新manifest，不把原hash/旧RED覆盖。退出后按共同清理规范处理专属root，清理后不能假定原runtime仍存在。
