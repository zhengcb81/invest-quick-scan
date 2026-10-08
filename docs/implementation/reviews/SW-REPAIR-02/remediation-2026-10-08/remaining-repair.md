# SW-REPAIR-02 R2 单项接续：SR02-4B

状态 `partial_verified / changes_requested`。原12反例、96受影响回归与11真实浏览器已通过，保留现有交付；只补下述同SR02-4损坏输入链和交接文字，不重新实现其他组，不新增小节点review，不机械重复full-suite。

## Owner与基线

原StockWiki唯一writer，工作目录 `C:/Users/郑曾波/Projects/StockWiki`。代码结果 `c83c148af35407a5ae01072314ba9bd17e59b3d9`，总控接收/收尾 HEAD `1831a73b37a3ed1b67d3556f6425ed2b52594a24`，当时master/clean。开工重新核HEAD/status；此基线不授权reset/clean其他进程改动。总控不代写此仓，其他QA/Lab线仍独占其仓库。

沿用[原五组卡](../remediation-2026-10-08.md)的实际授权，最小改动预计 `stockwiki/quick_scan_backup.py`、`tests/test_swr_backup.py`，文档/证据限原获批文件和 `docs/handoff/SW-REPAIR-02/`。不要凭交接自述扩大授权，新文件/不兼容接口/生产数据改动另需owner明确授权。本项无需这些扩展，不访问凭据/生产库/名单，不写IQS、StockQA、Lab或共享TEMP，不调用API/下载。

## 软件唯一残余：损坏UTF-8也必须invalid/skip（P2）

公开list/prune读取外来manifest单字节0xff，会在 `quick_scan_backup.py:589` 抛UnicodeDecodeError。当前两方法整体中断，外来文件没有被删；这是稳健性缺口，不声称发生越界删除或数据丢失。

复用现有 `_read_manifest_object` 的明确损坏输入分类，在读取/解码边界处理UnicodeError等实际格式错误，返回invalid；不要 `errors=ignore/replace` 让损坏字节变有效，不吞掉全部异常冒充成功。公开list/prune应保留外来文件、报告invalid/skipped，并继续处理合法自有备份。若其他现有读取入口共用此链，保持明确错误类别和fail closed，不能让错误registry获得删除权；不用泛化成全仓解析器重构。

固定用例：[corrupt_manifest_cases.py](corrupt_manifest_cases.py)。它使用真实create创建backup_a/backup_z，再放外来 `foreign_corrupt_bytes/MANIFEST_NAME`，内容 `b"\xff"`；两条公开路径已RED，详见[原始stdout](../../../intake/SW-REPAIR-02/2026-10-08-remediation/verification/utf8.stdout.log)和[counterexamples](../../../intake/SW-REPAIR-02/2026-10-08-remediation/counterexamples)。不要改断言、标xfail或把controller错误当产品RED。当前helper绑定已清理单次根，仅解释旧证据，writer移入已有获批测试并使用新独占根。

正反例至少覆盖：UTF8合法manifest照常；UTF8坏JSON、非对象和坏files照常invalid；0xff和截断多字节为invalid；list不中断、prune仅删合法backup_a/保留backup_z/skip外来，外来字节不变；登记坏数据仍拒删除。现有registry/junction/variant/恢复目标冲突与原六组成果不回退。受影响单元/集成集中跑一批，只有UI/接口变化时才再跑浏览器；上轮全套与本轮96/12/11证据保留。

## 同批交接澄清，不重造历史证据

1. artifacts目前69/69原字节和Git blob全部匹配接收HEAD1831a73、36仅EOL；但note说全部git_blob来自c83c148，实际16路径当时不存在、11路径当时内容不同。应明确 **runtime结果c83c148；后续handoff证据来自各接收commit**，为每项标具体ref或声明证据快照ref；不重写旧日志/图片/历史索引。总控已保留两ref对照，不将此描述错误当软件失败。
2. 旧共享TEMP删除者不可重构，“pytest retention删除”标为可能解释，不当已取证事实，不要求通过删其他lane目录来补救。旧R2未做SHA/硬链/正式监听扫只保留真实not_performed，不能事后伪填。接续测试按独占root、所有TEMP/profile/basetemp同根、进程/监听终态、无链接/单硬链、精确文件set/size/SHA、dry-run→Apply清理并留原回执。原历史取证缺口仍open，不靠新GREEN冒充旧环境恢复。
3. 明确多变体库暂不支持查询期选择；单变体正例在另一个workspace，不夸大为同库按维度选择。保持ambiguous不入默认白名单。

返回实际base/result/HEAD/status、最小改动/版本、两条RED→GREEN及正例原日志、具体hash字节口径、严格本轮清理回执。功能收口后一次集中交回，总控只复验受影响路径并签有限范围；真实owner gold/QA跨仓flow/双owner恢复仍missing/not_run，不关闭G3/F05/TH/IN/L03，不推送其他仓库或自动派发任务。
