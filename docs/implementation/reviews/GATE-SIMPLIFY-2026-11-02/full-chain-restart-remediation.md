# 保存、补封、入库和回执恢复：混合状态及重启整改（2026-11-02）

本轮已完成，独立审查通过。本轮是原链路的相邻审查与直接修复，不扩大内容、模型、名单或数据库范围，不新增审批或回执体系。旧节点通过实例保留；不能把它们外推为本轮未检查场景已通过。

## 根因与最终行为

|位置|实际遗漏|本轮修复|
|---|---|---|
|StockQA公共补封|旧已匹配ready占满limit，blocked或同组compact待升级永远排不到；前项不可修复同样阻后项|原Store `list_result_seal_candidates()` 单SQL仅取ID，未封/blocked/ready顺序固定为本次有限快照；只实际sealed/superseded或typed之后确认新目标包进展计额度，no-op继续；诊断保留原字段并明确计数/截断|
|共享文件发布|固定.pending残片挡同回调再次保存；RunCrashed分支直接重写最终checkpoint，写一半会破坏上次有效记录|同目录唯一暂存+fsync+原replace，沿原checkpoint codec；history内容区分命名，原完整事件/CP hash仍校验；原已发布坏history仍拒|
|交付job|worker排队后用户已放弃/别worker已完成，迟到worker仍导入；全entry已交付但最终job标记中断还要查当前receiver|锁内尊重completed/abandoned；完整原entry摘要仅用于补本地结束标记，pending或坏摘要不能冒充完成；不重签ACK|
|回执接续|接收库已commit、StockQA尚未记ACK时，先重建UI导出，缺release/cache就无法承接原ACK|先读原native映射和当前接收库身份，以原package_id取公开stored完整ACK交原StockQA逐项验证；已确认保持，混合只导剩余|
|UI派生归档|直接写最终immutable文件，中断可留下半截，后续永久报冲突|完整暂存发布；原封存包与冻结release有完整内容地址时可重建旧半截，正确缓存不重写；通用不同完整材料仍不覆盖|

这不是把任意磁盘损坏忽略：原检查点引用的history、原主体/工作/接收库/ACK hash仍验证。仅未引用暂存和可从可信原字节精确重建的UI缓存不再变成恢复前置。没有新表、队列、模型客户端、预算或权限平台。

## 验证边界与证据

- 原始共享两项RED均真实成立：orphan staging阻同回调写；真实原Runner/RunCrashed+原codec组合的写故障截断已发布checkpoint。修后共享三模块36P/16.86秒；corrupt-history断言收窄原 `StrictJsonError` 后新4项4P/1.67秒。非作者新4+旧atomic1独立5P/1.61秒，并另用真正子进程os._exit验证旧字节保持、新进程成功发布。原正常resume创建新session，不能把同session回调缺陷夸称所有冷重启都会失败。
- QA五文件最终61P/25.77秒，非作者独立19P/12.54秒。覆盖limit1下ready挡blocked、同ready组升级、不可修复先项、typed成功后再诊断、有限快照不追新入项、真实TEMP Store重新开库与公共CLI两次接续。fixture首用不存在 `--mode llm` 参数已改成实际CLI参数，不当产品失败。
- IQS作者jobs30P/2.80秒；三个相关模块首轮84P/1F中唯一失败是新增fsync mock设置错误，修fixture后focused46P/16.55秒；历史cache尾更新focused48P/43 deselected/43.07秒，不冒称94全文件最终绿。非作者最终主链40P，最后新增archive尾10P/1.75秒；覆盖本轮全部变更，组间重叠不相加。首次AppContainer硬链接WinError5三项已在授权C:/Temp复跑通过，未放宽产品代码。
- 非作者 `/root/fullchain_peer` 亲读最终源码、独立跑上述QA19/root5/IQS40+尾10及os._exit实验，最终无开放阻断。不是作者自报测试代替独审。
- 原SDK五组件冷CLI最终1P/323.82秒（wrapper325.38秒），两个新进程无key/删除当日model和budget配置，恢复同原响应/CP、未问项保持缺口，0新API；owned_runtime_removed=true。其自有副本两个QA生产文件和IQS共享源码与最终提交字节相同；该例是原实际SDK/CLI组合、vendor wire脚本化，不是重新付费真实扫描。

原始短日志在总控自有 `runs/audit-effectiveness-2026-11-02/`：`publication-restart-red/final/strict.log`、`fullchain-qa-red-final/green-final.log`；冷CLI在 `runs/qa-public-seams-2026-11-02/fullchain-publication-cold.log`。无需为日常恢复创建这些文档或逐表hash。

测试仅用自有C:/Temp短目录、原SQLite/原SDK与脚本化vendor wire；远端storedACK读取在定向测试中是明确port，StockQA真实ACK验证器另用原SQLite执行，不冒称本轮重新跑真实StockWiki服务导入。去密钥、禁模型/搜索请求、无真实公司文档下载；AppContainer源仓跨进程权限问题改在授权隔离runner执行，不改产品规则。所有自有临时目录已确认清理；原先其他任务遗留或未知归属目录没有擅删。

定向测试选择器（由现有隔离runner提供短TEMP、去密钥、禁网和finally清理；不直接运行在真实工作区）：

```text
tests/test_shared_publication_restart.py tests/test_shared_company_engine.py tests/test_read_only_replay_boundaries.py
tests/test_dashboard_delivery_jobs.py tests/test_dashboard_delivery.py tests/test_dashboard_product_prepare_api.py
```

QA目标文件为 `tests/unit/test_seal_batch_progress.py` 与原 `test_quick_scan_c06_complete_seal.py` 等相关短组。冷CLI调用原 `tests/test_paid_partial_cold_native_e2e.py::test_paid_partial_cold_cli_without_current_sending_configuration`，本机隔离wrapper `runs/qa-public-seams-2026-11-02/run_paid_cold.py fullchain-publication-cold` 负责五组件源码副本、guard、去密钥、短TEMP和finally清理；测试不作为日常启动前置。上面IQS三文件是可单独运行入口，本轮采用作者focused+非作者定向覆盖，并未声称最终三文件94全跑。

## 提交与原服务

源码IQS `e24c359`（8文件）与StockQA `4cffabc`（4文件）均已推原origin/master；QA正常hooks全过，IQS按仓库现有正常commit完成。Company/Runtime/StockWiki/UIlab本轮未写，不碰活动writer。原README独立改动及未跟踪文件保留，未纳入本次提交。

原UI已核原PID/创建时间/argv、37个任务均exited/stopped、0在途且无任务子进程后精确重载；只读doctor ready/无blocked，新旧gen6/gen7观察均可读。配置hash `89010b116f7b055b436c7a82b214cfd7177e1980c1dff178466d188b133dbe70`，账本仍87 HTTP/2053896micros、0在途/未结，无新增调用。此只读冒烟不冒充重新扫描或金融核验。原配置、历史回答、模型、分数、响应时间和费用保持；软件通过不代表金融内容全对、200/2000家公司或完整项目完成。下一步仍回根计划既有小池内容/事实主线，不新发包或追加门禁。
