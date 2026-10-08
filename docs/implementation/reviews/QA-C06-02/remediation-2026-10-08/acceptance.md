# QA-C06-02 四组整改验收（2026-10-08）

结论：**部分签收，仍需补四处同链边界**（`partial_verified/changes_requested`）。原问题已修，247受影响回归、原9反例及真实CLI正常路径通过；本批新增6个失败case属于原四组边界，不增加小节点审查。原StockQA harness保留唯一写权，总控未修改源仓。

代码结果：`acb7dbfae0e6a45221924e2d1d5742a4999f4c9d`；接收HEAD：`361a721df382c468640b27bbafc484e31c8aa321`（master）。结果后仅交接及.gitignore为清理回执新增一条精确例外，运行时无变更。前后原七未跟踪一致，内容未读/未删/未提交。

## 实测结果

| 项目 | 总控实际结果 | 边界 |
|---|---|---|
| 固定源码/工件 | 135源码＋SQL；47索引工件size/SHA全匹配，5件差异仅EOL；收尾不变 | 结果Git与收到工作树字节双锚定，五冻结CRLF不改；.secrets.baseline仅opaque hash、不复制内容 |
| 集中受影响 | **247 passed /105.62s**，wall106.376s | 6个unit文件＋3个integration；含新增真实subprocess四例；不是重跑1083全套 |
| 原固定反例 | **9 passed /2.32s**，wall3.062s | 原字节执行；含真实v5迁移/rollback两例 |
| 异步预算 | 沙箱外guard下 **1 passed /1.21s**，wall1.873s | Mock HTTP；同例也在247中，不能相加报248唯一case |
| 真实CLI | cold→另一进程warm→第三进程seal；仅HTTP边界stub；cold31、后续0新增 | 进程/runner/budget/checkpoint/seal真实；合成公司与搜索回执，不是live搜索 |
| IQS公开校验 | 正常CLI生成 **31/31**观察通过真实validate API；观察run均在持久refs内 | 合成结构/发布兼容，不是StockWiki真实owner golden或跨仓签收 |
| 一次独审补证 | **1正常 passed /6反例 failed /11.74s**，wall12.719s | 六例收敛原四组，下表；无新门 |
| 公开handoff | exit2 `temporary_root_not_cleaned` | 正式原件未改；旧共享TEMP归属缺口保留，不当成新代码问题 |

worker的1083 passed全套与pre-commit日志接收归档，**没有由总控重跑**。worker收到日志曾按其标准hook清洗行尾/EOL；此处保留收到字节，与总控原pytest输出分开，不称它们为未改的原始执行字节。

## 剩余四组

| ID | 动态证明 | 影响 |
|---|---|---|
| QR1B P1 | IQS_22.security_id改SEC_FOREIGN且重签context，loader接受；真实CLI最终exit1，但已stub31、fixture key打开2、建库并保存结果（30 healthy ready） | 无法在key/HTTP/预算前拒绝具体挂牌混淆；exit1不足证明早拒 |
| QR2B P1 | 外来run/scan被公开seal阻断，随后公开prepare将同一完整包写ready；持久refs仍仅原RUN_COMPLETE/SCAN_COMPLETE | 完整write可绕过seal的run门；不是静态预测 |
| QR3B P2 | 标准正文metrics.value=1e400，parse返回inf、未抛ValueError | 入口未拒非有限；后续canonical会拒，本例没有证明错误head |
| QR4B P1 | 无完整context/answer侧表，从外部构造full包，改claim及started_at全层重签，prepare/supersede两入口均落ready；两侧表仍0 | 新完整write在缺持久输入时fail-open；正常历史读取不需改变 |

详情、预期和原harness接续规范见[唯一剩余卡](remaining-repair.md)。[集中独审](independent-review.md)先给静态候选，总控同批实际证实；没有给每个修改增加独审节点。

## 隔离、异常与清理

所有测试只用本轮IQS唯一根 `runs/qa-c06-remediation-2026-10-08-01`；去API密钥环境，关闭live开关，guard拒外网、外根写入和非Python子进程。Windows asyncio仅允许内部临时回环socketpair；Python audit不是完整OS读隔离。生产数据库访问/复制、收费、下载、源仓写入均0；stub key为fixture内容，未输出真实key。

三类controller问题如实保留：初冻结因后续.gitignore例外在mkdir前停止；初guard将只读整数文件描述符误当路径，首边界批一例setup失败；初受影响300s和单async45s在沙箱内timeout，subprocess.run终止/等待直接child并保存输出。修改controller后在沙箱外受严格guard运行Mock异步和247全部GREEN。初输出不删除，不把环境错误算产品RED。

本轮743文件/402目录完成逐文件集合/size/SHA、lstat单硬链/无reparse、严格CIM拥有者进程0核验；dry-run和Apply分别留回执，仅删除本轮独占根，旧Phase92、共享TEMP、opencode.json及外仓全部保留。实际Apply终态与根不存在以[清理回执](../../../intake/QA-C06-02/2026-10-08-remediation/cleanup-receipt.json)为准。

worker历史清理回执只有file_count/total_bytes/清单聚合SHA，未附逐文件清单；原pytest147/148归属不明，不代删或伪称完整环境恢复。新两独占根及149删除是worker声明，无法重构过去逐文件操作；本轮总控自己的完整清理证据另列，不能替代历史证明。

真实QA→StockWiki import/ACK/UI、双owner恢复、真实identity/facts golden仍not_run/missing；G3/F05、TH/IN、L03不放行。下一步原writer同批补四边界，收到新交付后只验受影响；SW的SR02-4B、Lab的LR-02B各自原writer接续，Lab不人为阻塞QA/SW联合。

归档入口：[接收快照](../../../intake/QA-C06-02/2026-10-08-remediation/source-baseline.json)、[终态核验](../../../intake/QA-C06-02/2026-10-08-remediation/verification/final-verification.json)、[247输出](../../../intake/QA-C06-02/2026-10-08-remediation/verification/affected-regression-corrected.stdout.log)、[原9输出](../../../intake/QA-C06-02/2026-10-08-remediation/verification/original-nine-boundaries.stdout.log)、[残余输出](../../../intake/QA-C06-02/2026-10-08-remediation/verification/remaining-boundaries-corrected.stdout.log)、[真实库状态](../../../intake/QA-C06-02/2026-10-08-remediation/verification/remaining-observed-state.json)。所有helper使用已清理旧根，接手者需新编号/固定新提交，不能盲跑覆盖原证据。
