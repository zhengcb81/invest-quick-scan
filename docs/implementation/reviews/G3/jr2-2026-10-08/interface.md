# JR2实施接口与边界

本批仅接续[JR2](../joint-2026-10-08/remediation.md)，StockQA用户全仓旧授权有效，已报备两个源码及对应测试。StockWiki仍未获本次四文件新增授权，不写。此次先固定a39d7ea/b6eaa08的136文件隔离副本；父目录/rootAGENTS不存在，使用会话提供的CodeGraph规则，已先查询结构，不修改索引。

公开API约定：`QuickScanWorkStore.bind_result_delivery_consumer(work_item_id, consumer, *, source_ref)`。consumer严格三个字段component=StockWiki、namespace=quick_scan、store_id（现有受限字符串）；source_ref为受信操作员配置或接收方公开owner DTO的来源指针，不来自LLM答案或incoming ACK。返回持久目标记录及其hash，绑定delivery/head/package/revision；相同绑定重试幂等，不重新打时间戳。`begin_result_delivery`缺绑定先拒，`apply_result_delivery_ack`在事务内与绑定核对。历史terminal原ACK重放保留；旧pending无目标不得从ACK自动学习。

独立目标存储不得混用过去ACK写入的consumer_store_id冒充事前证据。通过事务迁移/独立记录实现，旧head记录保留，新的ready head需明确重新绑定；发送中或terminal不能改目标。旧schema迁移不补造目标，失败rollback保持原库。不得改变ExchangePackage1.0字段/ID/hash以加入目标。

正向TDD允许明确标注operator-configured synthetic target，不是StockWiki真实身份/事实golden。未来跨仓正向必须在发送前取接收方公开owner信息并保存，不拿第一次ACK给自己背书。StockWiki没有公开owner信息时如实unsupported；本次不伪造已交付getter/CLI。JR1尚阻断原SW ACK，JR2单侧完成不解G3/F05。

已授权予定发布源：src/utils/quick_scan_result_outbox.py、src/utils/quick_scan_work_store.py。受影响回归在现有test_quick_scan_result_outbox.py、test_q10_delivery.py、test_quick_scan_work_store.py；需要修改其他现有夹具先说明依赖，不无声扩大任务/删除旧断言。完整seal/subprocess无关行为保持；legacy unsafe first ACK可升级为新明确绑定夹具，terminal读取断言不能删。

父调用点检查后另报备两测试依赖：tests/unit/test_quick_scan_c06_complete_seal.py与tests/integration/test_qa_c06_02_e2e.py。父独占这两副本，原断言保留，只在begin/ACK之前使用独立固定的operator-configured synthetic consumer；旧head/错package负例须先绑正确当前目标，避免被缺绑定提前拒而削弱原断言。总发布清单为两个源码加五测试；worker仍只写原五路径，外仓实际发布仍待集中测试/审查与源hash核对。

隔离worker只写runs/jr2-2026-10-08-01/qa下这两个源码和三测试，由总控独占docs/implementation/reviews/G3/jr2-2026-10-08与intake/PWF。测试在自有tmp下、guard禁止外网且移除所有key，仅离线合成。保存首次真实RED和最终GREEN，不为每helper新增审查；本大节点集中独审/必要回归后，源仓当前hash未漂移才按获授权路径发布，并严格清理自有根。源仓提交与IQS归档提交分开，按实际回执登记。
