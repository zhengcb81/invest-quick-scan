# SW-REPAIR-02 R2 集中独审

2026-10-08，`/root/sw_repair_acceptance_review`；只读源码与交接，未运行测试、浏览器、API、未写源仓、未派发其他agent。代码 `c83c148af35407a5ae01072314ba9bd17e59b3d9`，接收 HEAD `1831a73b37a3ed1b67d3556f6425ed2b52594a24`。CodeGraph未覆盖quick_scan新文件，按施工卡具体路径阅读。本轮只有一次集中独审，动态补证由总控完成。

原12固定反例的四组软件根因已修复：profiles/rows完整传递segment/期间/basis及缺失值，projection升1.1.0，默认歧义分数null并保留variants；create/verify/restore/list/prune均拒绝受管根及backups祖先junction；registry版本/schema和record的owner_module/workspace/manifest/digest绑定；合法JSON非对象/坏files形状报告invalid。UI新增维度进行安全转义。具体授权路径替代literal glob，多文件接口hash口径已明确。

## 唯一代码残余 / P2 / SR02-4B

`stockwiki/quick_scan_backup.py:589–595` 的 `read_text(encoding="utf-8")` 只捕获OSError，loads只捕获JSONDecodeError。单字节 `b"\xff"` 会抛UnicodeDecodeError，中断公开list（563）与prune（625），而非报告invalid/skip。文档已经将plain corrupt bytes列为可跳过的损坏manifest，属于原SR02-4边界。

建议两份真实create备份加外来目录/0xff manifest，测试list报告invalid、prune正常保留backup_z/删除backup_a，外来字节不变。本独审只提供静态证疑，未实跑；总控随后在固定副本两条路径均实际失败，见[原日志](../../../intake/SW-REPAIR-02/2026-10-08-remediation/verification/utf8.stdout.log)及[执行用例](corrupt_manifest_cases.py)。owner_registry坏字节目前fail closed，未另扩为新删除缺陷。

## 必须保留的证据边界

`test_swr_profiles.py:455–477` 单变体“选择”正例是另建workspace只导入所选一条，不能宣传已存在多变体库具备查询期选择。卡允许没有安全选择能力时保持ambiguous，文档已披露该缺口，不是新阻断。

worker R2清理回执明确未做逐文件SHA、硬链审计、正式监听扫，已删目录不能补取过去证据。共享TEMP105/109/110/111消失、删除者无法重构，不等于此writer已恢复成功。handoff一处将pytest后续retention作为确定原因，实际只能作为推断。真实identity/facts golden、QA联合流、双owner恢复、G3/F05仍未关闭。
