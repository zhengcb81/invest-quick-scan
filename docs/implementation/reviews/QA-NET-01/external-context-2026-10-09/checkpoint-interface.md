# 检查点与执行器接口：私有实施接续

2026-10-09。StockQA源仍`42a517c`/schema8；IQS私有`runs/n111a/qa`是schema11。当前31路径已先报备，不写其他仓；这不是正式发布或Phase111完成。

## 已接通的真实调用链

实际检索journal → 发送前不可变use intent → 原回答HTTP/响应记录 → owner派生use1.1来源URL → `project_quick_scan_search`重新读实际store/final receipt → transport-managed runner → checkpoint2 → 完整standard body/C06 → outbox。

`project_quick_scan_search(metadata, work_store=..., work_item_id=...)`也可在当前work ContextVar下运行。external key存在但为空、无实际owner、外来work/attempt、最终receipt漂移或自签proof都拒绝；native调用保留原行为。同步LLMProvider只投影通用metadata，不改`execution`原native回执。`execution_receipt_for_checkpoint`对外部仍返回原HTTP回执，由store独立验证proof；不可把generic状态写进原native receipt。

`save_answer_checkpoint(..., external_context_use=actual_proof)`显式生成版本2，保留原response/model/receipt SHA及native状态/receipt ID/URLs；generic source集合来自实际eligible检索与原native来源。旧无external意图仍版本1，历史payload/hash不变；实际external intent不得降级成版本1。旧use1.0可读但不补来源，不足以新封包。

schema10→11在同一事务重建CHECK约束为1/2，旧行与不可变trigger保留；故障回滚原schema、所有行与PRAGMA。fixture需真实旧DDL，不能只降低PRAGMA。当前所有迁移仅临时SQLite，不迁移生产库。

完整答案引用的每个URL必须在实际来源集合内；缺authority保留blocked，具备独立合成owner输入后可由原seal函数封包。测试fixture不是StockWiki identity/facts golden、准确性gold或真实厂商计费凭证。

## 已执行证据

原失败及中间fixture/控制器错误逐标签保留，checkpoint05索引列出全部15批。最终`runtime-checkpoint-affected-green-01`十四文件672 passed、0 failed/error/skipped，pytest58.19秒/controller58.868秒，执行源SHA不变。不得与491或455重叠批次相加。HTTP均替身，真实SQLite/客户端/runner/封包函数实际执行；key/paid/network/download/外仓写0。没有小节点独立审查，仍等整批集中一次审查。

## 单一接续入口和剩余事项

1. 先接公开结果输出。`QABatchResult.to_quick_scan_dict`及IQS `scripts/stockqa_adapter.py`当前public1.0/ROUTE_02仍从native calls认证source集合；目前内部provider metadata成功不证明公共输出可用。设计显式新public版本、分列实际native receipt和external use/retrieval引用，旧1.0行为与历史读取保持；不得制造native `web_search_calls`，不得靠模型自述认证来源。
2. 接实际runner/cascade的检索协调和异步provider投影；当前tests显式绑定检索context，生产CLI dispatch仍未打开。仍使用原模型顺位/Q08/Q09/attempt，不建第二执行器。没有native能力的模型如何使用external需明确端点/协议准入测试，不把当前三种协议测试当全模型覆盖。
3. 两阶段与跨租约恢复、逐HTTP计费MCP init/discovery/search、公开CLI cold/warm/resume/failure。发送后unknown、缺usage与持久化失败不能自动补发或释放预留。
4. 完整相关回归/静态/一次集中review，然后正常StockQA源发布和严格自有根清理。当前不能删runs/n111a；旧checkpoint helpers硬编码已不适用，旧index01–04/接口/原工件不可覆写。

G3/L03/F05、StockWiki JR1/JR3四新路径许可、真实identity/facts/query golden和TH/IN写授权仍未齐；不自动关闭门、刷新退役工程回执或开200家live。
