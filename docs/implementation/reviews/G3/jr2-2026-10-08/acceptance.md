# JR2事前消费者绑定：单侧软件验收

状态：`verified_for_jr2_producer_scope; source_committed_and_pushed; owned_cleanup_complete`。本批接续Phase108唯一JR1–JR3集中整改卡；仅签StockQA的JR2，未签StockWiki原ACK、JSON接收或全局门。

## 交付范围与接口

用户此前授权StockQA全仓修改并要求报备。本批先报备两个源码/三测试，再因真实调用点追加两个测试；真实外仓发布总计七文件。外仓基线master `a39d7eafceacfa1114f5e5cb094eadb32030652c`，软件基线`b6eaa082e6e1df1306fa144bd623aa6de68213a1`，原七未跟踪保留。初始136文件由固定Git字节与已签收raw SHA还原，未复制配置、密钥、真实库、财报或公司名单。

工作库schema升级6→7，新增独立目标表与四个SQL保护trigger。公开API：

```python
store.bind_result_delivery_consumer(work_item_id, {
    "component": "StockWiki", "namespace": "quick_scan", "store_id": configured_store_id
}, source_ref=trusted_config_source)
store.begin_result_delivery(work_item_id)
store.apply_result_delivery_ack(work_item_id, original_ack)
```

目标必须由受信操作员配置或接收方公开owner信息在发送前提供；`source_ref`只是来源指针，不自证调用者授权。目标按delivery/revision/package/item/observation及hash持久绑定，同绑定重试保留原时间和hash；新head需重新绑定。发送或ACK落定在同一事务内核目标，缺绑定/错目标先拒且全库不变。目标表不可改删，插入锁定当前head。工作/查询读侧核绑定hash和head。

旧v6终态原ACK可精确重放，旧pending/send_uncertain无目标不能学习ACK；升级只加空目标表，失败整个迁移rollback。公共ExchangePackage/ImportAck1.0字段、ID与hash不改，ACK仍十根字段。封包CLI目前停ready，不新增隐式派发；StockWiki公开owner getter/真实owner golden尚未交付，本批使用明确的operator-configured synthetic target，不冒充真实公司或接收方黄金样本。

## 实际测试与集中审查

从IQS根运行以下runner，argv、raw stdout/stderr、JUnit和process都按独立label保存：

```powershell
python -B -X utf8 docs/implementation/reviews/G3/jr2-2026-10-08/run_tests.py --label <new-label> tests/unit/test_quick_scan_result_outbox.py tests/unit/test_q10_delivery.py tests/unit/test_quick_scan_work_store.py tests/unit/test_quick_scan_c06_complete_seal.py tests/integration/test_qa_c06_02_e2e.py
```

此helper仅用于本批精确私有根；清理后不得盲跑，复验须按固定manifest新建独占副本并使用新label。

| 批次 | 真实结果 | 含义 |
|---|---|---|
| jr2-red-01，原三文件`-k jr2` | 22 failed/88 deselected，5.39s，pytest1，wall6.084s | 实施前缺目标仍可发送/接受ACK及新增接口缺失；原件保留 |
| jr2-green-01，五文件 | 135 passed/1 failed，22.52s，pytest1，wall23.008s | 新trigger抢先报错，破坏旧terminal ACK不可变错误语义；没有改原assert |
| jr2-green-02，五文件 | 136 passed，21.89s，pytest0，wall22.362s | 限定首次非terminal转换后通过，七源码执行前后hash相同 |
| owner静态批次 | isort+七次单文件Black+mypy九命令全部0，40.367s；56源文件无类型问题 | 仅七文件格式化，私有cache；源码主体AST和import binding/scope等价留档 |
| jr2-green-03，最终格式化字节 | 136 passed，24.91s，pytest0，wall25.61s | 最终七文件hash执行前后相同，无超时 |

不能把各次重叠测试相加为独立总数。新增用例覆盖缺绑定/ready及send意图错store全库不变、四种合法ACK状态、精确重放、时钟推进幂等、禁止retarget、supersede新head/旧ACK、真实v6 pending及三terminal迁移、DDL失败rollback、直接SQL伪造head/revision/package与不可改删。父两依赖fixture先绑正确目标再验证旧head/错package，保留原断言区分力。集中独审见[报告](independent-review.md)，未另跑无变化full/UI或live。

最终固定清单：[source.json](../../../intake/G3/2026-10-08-jr2/snapshots/jr2-green-03/source.json)，SHA256 `c299f1c1440691a6538801b83d638945ddb7cf121ba72671230ad33728461483`。七raw源码与实际执行hash匹配，129未改副本/136原外仓字节与原HEAD/status发布前均相符。格式来源：[format-provenance](../../../intake/G3/2026-10-08-jr2/format-provenance.json)；AST/import-scope证明有明确范围，不当通用语义等价定理。

## 控制器记录与隔离边界

初collect在七文件已保存后因“key文件读0”假设错误退出1；初脚本、初源快照和相对名ledger保留。E2E明确在自有tmp生成`offline-fixture-key`配置，v1六次相对名read只能凭固定fixture来源解释，不能证明OS级读取隔离。v2记录12次绝对自有tmp配置read，拒自有根外该配置读取，所有真实key环境变量移除；没有复制/输出真实key。guard是Python audit控制，不称完整OS读沙箱。网络尝试/收费/真实搜索/下载/生产库/名单写0。

第一次black多文件check在沙箱无输出；CIM确认本轮PID46492/parent84416仍活且无直接子进程后，明确停止该检查并poll原session54363终态。随后isort check实际失败；不报初black成功，不因观察超时启动第二份并行检查。改自有guard/单文件Black完成。曾在静态批次尚未结束时读取未生成08日志，真实只读报错，等同一session终态再读，未重启。各原错误与修正写入PWF。

本轮只清理`runs/jr2-2026-10-08-01`，待精确SHA/lstat/单硬链/无reparse、严格CIM进程0和独立dry-run→Apply后记录实际回执；共享TEMP、Phase92、外仓七项、opencode不动。清理、外仓提交及IQS提交当前均未预填成功。

StockQA实际发布七文件后，正常提交钩子/diff/push都0；结果commit `86b1e8ab1221e085f08718ed31d18e792e526d34`已正常推送既有origin/master并与HEAD相同，七raw字节在钩子之后仍匹配最终GREEN，原七未跟踪不变。[源仓Git回执](../../../intake/G3/2026-10-08-jr2/source-git-receipt.json)与逐命令raw另存。未提交其他路径、不跳钩子、不强推。上一段“未预填”保留真实时序；IQS提交/自有清理仍等实际回执。

自有清理现已完成：136源对照7授权raw/129未改相符，2419文件/487目录的SHA/set/lstat单硬链、无reparse、严格CIM0全部核验，独立dry-run→Apply都0，Apply session24049已退出0且唯一根不存在。[清理回执](../../../intake/G3/2026-10-08-jr2/cleanup-receipt.json)保存实际时序；原共享TEMP/Phase92/外仓原项不动。IQS提交只待后续Git实际回执。

## 保留的全局门

JR1公共原ACK及错误taxonomy、JR3严格JSON仍待StockWiki新增四文件许可；QA单侧绑定不能证明跨仓ACK闭环。G3还需L03+W11（W11已交付），L03/事实gold/F05/TH-IN和双owner恢复不自动关闭；requested/resolved模型能力另列，未夹带实现。
