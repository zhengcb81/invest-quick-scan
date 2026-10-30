# IMPORT-PERF-30｜原入库链的可重复剖析与守卫不变的加速候选

唯一工作目录：C:/Users/郑曾波/Projects/iqs-import-performance-lab
分支：codex/import-perf-30。本地Python包：iqs_import_perf。
只读总控入口：C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-30-mainline-next/README.md。
先读handoff-rules.md、interfaces.md、inputs.lock.json及manifest.json本包条目。

## 实际问题及边界

本轮原UI对C的33题交付约19分钟，原pipeline反复冷启动、逐包多个CLI/preview/status可能重复加载。该耗时是线索不是可直接比较的benchmark。现在未证明哪段占主导，请先测量再优化；不以删校验或缓存旧授权求快。

本包不再设计scheduler/LOAD案例，不做真实扫描/公司数据，不接8766、原DB/预算/名单。**只能在自己Lab冻结原源码副本和临时合成原生库里执行**。目标交可落到锁定原仓的局部candidate.patch及可靠基准，由总控以后整合。

## 应交实现

1. 以锁定dashboard_delivery/jobs、StockWiki原import/ACK、StockQA原outbox构成真实离线入库路径。合成fixture尽量复用原tests helpers/原封存逻辑，标synthetic_native；不能重新造一个“快的mock导入器”来冒充优化。
2. 记录每包/每批spawn、冷import/解析、release/schema读、原preview/权限检查、SQLite事务、逐ACK/回写/状态轮询的耗时/次数与原调用栈。profiling插桩不能改变返回或只给候选排除开销。
3. 合成1/3/33/36包，在同机同数据/隔离条件基线和候选各至少3次，区分冷进程/暖进程（不清OS缓存或改全局设置）。给median/离散、总时间与每阶段比例、原有效导入/ACK数量，失败亦保留；不能只展示最快一次。
4. 实现至少一个有根据的局部加速候选，例如受控批量原封包传输/复用冻结schema解析或减少无用重复status；优先选剖析表明的瓶颈。不另建owner/回执库/第二个导入器。若不能在守卫不变下取得正收益，诚实partial及根因，不牺牲语义换数字。
5. 原当前权限/撤权、身份/subject、cutoff/上下文、版本、预算/源store/package/item/obs/payload、原ACK序列与幂等、unknown HTTP和send_uncertain边界必须保持。只能缓存内容地址稳定且SHA核验的不可变release/schema；**不能缓存授权/预算/身份决定/ACK成功**，不能降低验证、改journal、扩大busy_timeout、取消strict parser或修改旧记录。
6. candidate.patch仅改本Lab对应原源码副本，目标文件逐一解释；最终建议不以新的后台队列/测试回执系统替代原链。文档给生产待测事项，不能写原19分钟已降到某值。

## 必要测试矩阵

单元：解析/包选择/内容地址缓存key、未知版本/重复键/超限/路径越界、缓存被篡改仍拒；对真实原边界做有效RED→GREEN。

集成：合成临时原生SQLite/封包→原preview/import→原ACK及原producer对账；对基线/候选逐项比对语义。至少正常、重复同包幂等、错store/obs/payload、换主体/版本、撤权或校验失败不因缓存绕过、部分成功后失败、ACK迟到/未知后按原允许接续、进程中断后再次执行。

E2E：从本Lab公共benchmark入口经实际子进程或受控in-process原路径，完成33包并复核实际ACK/清理；故障路径同样清理。可以本Lab loopback，但不得冒真实远程owner；端口冲突退出。不是只有monkeypatch函数返回成功。

比较原结果状态/序列/幂等行为；可能变化的计时/随机ID须有显式对齐依据，不能为了“同等”忽略拒绝项。semantic_equivalence与speedup分别给结果。旧full suite不需跑一小时，只跑受影响的原定向用例和你新矩阵。

## 交付与审查

按interfaces.md交bench/原始测量/语义对照/candidate.patch/performance-design。README必须能从干净Lab复现命令；无私有原库和密钥依赖。测试临时库/子进程/端口/缓存finally清理，raw-runs只留薄记录，合成fixture可保留。

独立agent全面核测量是否公平、是否真的跑原路径、是否偷缓存可变权限/漏ACK/去校验、故障行为是否一致，以及patch是否局部可合；所有发现修复并复审后交docs/handoff/IMPORT-PERF-30/handoff.json。无收益/缺依赖不能伪造通过。
