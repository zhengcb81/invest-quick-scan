# W15 同次集中独立审查最终附记

结论：对冻结候选02的限定软件基础签收，`outcome=limited_foundation_signed_off`、`software_open_findings=0`。初次集中审查的唯一已证实产品阻断F1已关闭；本附记继续同一次审查，不新增门。签收范围为IQS producer handoff、StockWiki原路由/Observation存储及刷新、QA原work/费用/发送事务接合，不代表全W15或全部软件栈关闭。

## 冻结字节与已发布基线

`candidate-index-02.json`实际SHA256：`f28a33b27de7de7b30016fc35acecd1f56015f1725946b691137fb34c39bea5a`。独立逐项读取全部36文件：StockWiki15、StockQAbyLLM16、IQS5。当前文件与`candidate-source-02`均逐字节相同，SHA和长度均等于索引；包括QA`.gitignore`及两个JSON contracts。具体逐项结果保存于`frozen-candidate-02-verification.json`。

已读主控`source-publication/before-publication-01.json`，其实际SHA256为`0f04f0c17c87c497f0d7cf2ff331d5c7744e88c144e1586b939473c27706188e`，内含相同候选索引SHA；报告的已发布HEAD为SW `6c46f03b486d215d696d32bee618793bc7fcb410`、QA `bc41908e4cdc44c13fefda97f3118e5434aed5f8`。这是对已存preflight材料的核对，没有冒称另行重跑整个外仓受保护文件审计。

## F1独立原反例复核

当前`quick_scan_work_transport.py:651`以具名异常保留owner拒绝；`:665`入口、`:770`work循环及`:797`budget-only循环每次准入前均调用同一owner guard。最终transport执行SHA256为`69ec8dce71337a9c359a49302e2739cb217e60371b964907ae1843a6d70b1fc4`，owner bridge为`a4548f56d62b60e4f0f22baab391f8d5f16eb37b39743af5c300f3cb7ccab490`。

保留初次`capacity-anchor-01`的真实RED原件；沿用原双SQLite反例，仅换独立自有basetemp/label为`capacity-anchor-02`。实际PID37400，returncode0，terminal_confirmed=true，pytest **1 passed in 1.28s**，controller1.829s，19个产品/公开schema执行SHA前后不变，HTTP_calls=0。

真实owner SQLite初始current A，真实QA容量账本已有占位。第一次收费准入被容量拒绝，等待调度点通过真实`set_current`切A→B，并通过真实`record_budget_outcome`释放占位。固定后累计3次锚点读取、1次容量等待，实际current B与绑定A不一致时得到`owner_refresh_guard_rejected`，`permit_returned=false`。独立只读账本核验：attempt只有`prepared`、send_intent_at为null；费用表只有原`DISPATCH_busy`已settled/in_flight=0，未新建该work的收费reservation。初次RED的错误发送许可已不可复现。

反例使用真实SW/QA SQLite与原费用事务；仅IQS UnitValidator及typed CLI传输为已明确的storage-boundary替代，不能称为真实owner查询golden。源码、PWF、外仓和真实库均未由审查agent写入。证据为`capacity-anchor-02.stdout.log`、`.stderr.log`、`.process.json`，反例原件与新runner均在本review目录留存。

## 终态材料与执行SHA的限定核对

| 记录 | 实际终态 | 与最终候选字节的关系 |
|---|---|---|
| storage-final-09 / PID10952 | 91P / 59.41s，exit0 | SW产品与最终一致；之后仅两个profiles fixture变化 |
| storage-profiles-final-11 / PID10748 | 90P / 16.73s，exit0 | 全SW15候选与最终一致 |
| executor-final-affected-04 / PID67172 | 307P/1F / 72.30s，exit1 | QA产品均为最终SHA；唯一失败为Q07 fixture，之后仅该fixture维护 |
| executor-checkpoint-final-05 / PID36492 | 8P / 3.44s，exit0 | 所有记录的QA Python/schema候选与最终一致；`.gitignore`不在该测试hash清单，另由36文件核对确认 |
| handoff-final-01 / PID75248 | 18P / 103.01s，exit0 | IQS5候选与最终一致 |
| capacity-anchor-02 / PID37400 | 1P / 1.28s，exit0 | 独立复核原F1；19个产品/schema前后不变 |

这些记录不相加，不改写307P/1F为308P。该1F为`test_par_04_resume_keeps_original_checkpoints_and_provenance`：维护fixture时response写model-a而requested model仍默认，原产品正确拒绝与frozen request不匹配的durable response。最终fixture显式对齐requested model，后续8P通过；产品没有为测试降低绑定校验。

已直接解析307P/1F的JUnit：work/budget-only × owner-change/stable四个`test_capacity_retry_rechecks_owner_before_reservation`组合全部passed。此前full发现的owner bridge fixture暴露已显式恢复；短独立根下实际IQS producer/SW OS CLI/QA接合已执行。issuer首次迁移和完整v4/staged分支均达到，最终测试保留完整原candidate row tuple相等及新route表核验。两个profiles断言只改为实际规范Observation ID，原得分、日期、来源、freshness语义检查保留且后续90P达到；没有让产品接受非法短ID。

`static-qa-05`的Black/isort/mypy/Bandit四项均真实终态0，mypy63文件；产品Python SHA与最终一致，后来仅Q07 fixture SHA不同，故不把该旧static记录说成最终Q07 fixture的static证据。`static-sw-01`真实终态0，8个SW产品SHA与最终一致；其后变化的测试fixture不借用该旧SHA记录。发布时的正常源hook由主控另行执行，本附记不预报成功，也不重复大套或调整阈值。

## 隔离支持与full非绿继续保留

本次原反例实际使用guard v3，SHA256 `28c141822093777bbc503603e8ba16aec20b3f1f664db57ac926c1979c994b58`。只允许stdlib `_fallback_socketpair`原code frame内、其局部csock连其本次正在listen的lsock，仍拒普通loopback和远端；foreign SQLite仍拒。307P/1F的原JUnit中四个隔离案例均passed：普通127.0.0.1拒绝、192.0.2.1拒绝、stdlib socketpair允许并关闭、foreign SQLite不打开。guard为私有隔离支持，不属于36个产品候选，不发布；不声明全OS隔离。v2原件保留。

`full-sw-support-fixed`的原终态仍为PID5808、exit1，1063P/64F/18skip/21error、225.22s，coverage80%仍只作diagnostic。没有重复full，没有用guard局部修复把旧UI/HTTP断言追认为通过。其具体基线fixture、私有导出支持、TEMP/长路径、Windows链接权限、配置剥离与未达到的真实内容/UI分支分类，沿用`full-sw-classification-01.md`。该附记中需要补测的W15 owner bridge、issuer完整v4、两个profiles和F1，现由上述具名受影响终态及独立复核补齐；其余原full非绿记录继续保留。

## 原门仍未完成

公开wire继续明确`c06_envelope_validated=false`。真实C06/query serializer/envelope、actual owner query golden、事实与金融准确性尚未完成；26真实结构化元数据及四个native backup只是已锁真实owner输入，不能代替真实query或财报验证。router2.1/2.2保真仍只是unit/storage边界，不冒称完整producer golden。

本签收不关闭G3/L03、F05、B01、TH-IN或全W15，也不提高上述原门状态。软件限定范围内未剩已证实产品阻断；审查agent仅写review材料及review-owned独立运行目录，产品/PWF/源仓写入0、full重跑0、模型/API/HTTP调用0。
