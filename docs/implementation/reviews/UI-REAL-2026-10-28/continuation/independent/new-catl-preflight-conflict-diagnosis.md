# 新 CATL 续扫预检冲突（只读诊断）

已确认 run-02474de15f11463ca9d95bae9e475bad 原回执为 process_exited、exit_code=1。33 个当前实体问题中 14 已回答、19 error，未声明全范围或全公司完成。

实际直接错误是 IQS_15 与 IQS_16，不是 IQS_16/17。IQS_17 起只因前包停止而未派发。IQS_15 的进度提示也不代表成功；原结果为 error/null。

两题在旧 epoch1 有 prepared 后 recover_expired 生成的 abandoned_unsent。旧共享 PACK_00682555046048a99f29bff94c0bd7ba 没有 send 行、outcome 或关联物理预算。新进程成功 claim epoch2，但没有创建任何 epoch2 attempt；两题保留 leased，17 仍 pending、没有 attempt。本诊断不处理这些租约。

根因是旧工作已有不可变的 observation context。旧 hash fedcc040… 的 run 为 dashboard-d9e50…；当前 bundle dashboard-bc311… 的 context d143b817… 可由本 bundle 已成功的 IQS_04 generation6 原记录核实。逐字段比较显示，IQS_15/16 原 contract、subject 和全部稳定输入都一致，仅 metadata.run_id、scan_id、inputset_id 三处不同。

原 runner `dispatch_question_pack_context` 在约 846 行无条件调用 freeze_observation_context_before_send(current self context)；原 store `_store_side_tables` 4550 行严格拒绝不同的 immutable work-context binding。该路径发生在实际 search_pack 前，所以没有新 attempt/HTTP。原公开日志仅保留 WorkConflictError 类型，未保留精确消息；“task already bound to a different observation context”来自精确原绑定不等与实际源码路径推导，不伪称捕获了原 traceback。

最小根修是每个原工作在当前 owner 正本准入通过且稳定合同完全相同的前提下，继续使用其原冻结上下文。不能覆盖原 context、移除原不可变校验或强行忽略任意 metadata 差异。还须覆盖 `_standard_transport` 1237 和 `_save_transport_checkpoint` 1308 的当前 self context，否则只修预检会在封存时再次失败。混合旧工作与从未冻结的新工作时，每题应独立选对应上下文。

建议 TDD：原 SDK 临时 SQLite 冻结 context2 → 原 pack prepared 未 send → 合成时钟过期恢复 abandoned_unsent → 新 runIDs 原授权 claim → stub HTTP 一次 → 原 strict checkpoint 使用旧 context 成功。另测 cutoff/主体/提示/semantic/schema/registry 改变全部 0 HTTP 拒绝；混合旧/新 work 保留各自 context；send_intent/uncertain/late 不能借此自动重发。该诊断未执行测试或真实重放。

仅使用 URI mode=ro、query_only 短事务；不构造写 schema 的 Store；没有真实库/源码/PWF 修改、请求、私有思考或 key 读取、正文或上下文归档、UI/进程控制。M/T 在途任务完全未干预。
