# SR02-4B 一次集中有限独立复审

日期：2026-10-08。审查者：既有 `sw_repair_acceptance_review` agent；本轮复用，不新增小节点审查。

范围是固定 StockWiki `cc587a8cf76f2c50a0cdfb4693d3767dfa5944fa` 的三个受影响文件，以及实际接收 `d253fea5f4f6e4242d2b91eaf8d89d3dac8b45ff` 的交接。只读静态审查，不写外仓、不自行运行测试或调用 API。下面记录收到的审查结论，动态测试结果由总控另外绑定。

审查结论：**有限静态复审通过，没有发现剩余软件阻断。**

- `quick_scan_backup.py` 三处边界（270、356、599）正确处理 `UnicodeError`：list 标 invalid、prune 跳过；owner registry、verify、restore 具名拒绝。保留严格 UTF-8 解码，没有忽略或替换损坏字节，也没有宽泛吞异常。
- `test_swr_backup.py` 641–741 的七个实例覆盖 `0xff`、截断多字节、合法备份保留、外来字节不变、verify/restore 具名拒绝及损坏 owner registry。
- R3 清理与旧 R2 的 `not_performed` 分开，不能用新 GREEN 证明旧环境恢复。实际删除取证仍以收到的原件和总控自己的本轮清理分别记录。
- 每项 `blob_ref` 可归因；`git_blob_sha256` 的 40 位值是 Git SHA1 OID。应按实际算法核验、记录命名错误，不将可验证的对象误报为软件漂移。

审查的放行条件是：同一固定代码提交上的原两反例、受影响 backup 回归、实际公开 CLI 通过。条件满足后仅关闭 **SR02-4B 有限软件范围**。真实 owner golden、QA 联合链、G3/F05、同库多变体查询选择及旧共享 TEMP 的取证不随本项关闭。

总控补充原件核对：R3 dry-run 的 538 个文件 `nlink` 都是 0，与回执文字 `nlink==1` 不相符，不能独立认证过去硬链审计。另有两份真实 R3 回执未列入 worker 的 75 项索引，已按收到的 HEAD 另行归档并双域核验。这些限制单列，不回写原件或重开无关软件审查。
