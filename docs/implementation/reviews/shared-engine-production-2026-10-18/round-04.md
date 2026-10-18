# 原生 core 最终精确范围独审

同一整节点中的原生 core 精确 **15 文件**已通过独审，签收记录为 `native-core-scoped-acceptance.json`，CAS SHA-256 为 `2797ad08433fe0f9ee952fad6e9950e5d5f0953aaf40ead67277bc9b2d6c44fe`。应用前的 StockQA 基线仍为 `e63a79f6698d60b398ed4c0c2e67979d051cd93e`。独审核对全部候选哈希、字节数及原工作树前像；未写入原仓。

独立实际重跑最终原生 50 项测试，**50 通过**（33.09 秒）；另运行不同 agent 自建的 11 项反例/正例，**11 通过**。二者的测试组和历史重复执行不相加冒充唯一覆盖数；更没有宣称历史 524 项全套最终一次全绿。

新的来源绑定负例覆盖：替换原 pack 成员再重算 join 自哈希；改变 task SHA 或 intent SHA 再重算 join 自哈希。最终 getter 从原 singleton attempt/原完整 pack 重推成员和请求 SHA，并核对原 immutable native receipt 中的 `research_intent_binding_sha256`，以上伪造均拒绝。原 native receipt 没有被测试改写。

未知结果测试让实际 SDK（scripted wire）遇到超时后，用相同 intent、不同 prompt 再调用原 send 通道。其总 wire 调用和原预算请求数仍为 1，没有产生安全重放输出，没有另开账本或清空预留来绕过。

向后兼容测试在隔离 SQLite 中构造严格的原 v22 schema：只读原预算结果、借用同一 read transaction，库版本仍为 22，主文件 SHA-256 完全不变。另加不属于原 v22 的表，原严格 schema 校验拒绝且主文件仍不变。没有调用 writer 做隐式迁移。

隐私、安全输出重哈希、跨新 OS 进程读取原安全输出、错模型 pack 已知用量保留/不重发等前轮独立反例，也在当前最终 native 候选重跑通过。证据在 `runs/shared-engine-production-2026-10-18/independent-review/native-full-final.xml`、`native-final-probes.xml`、`native_probes.py`、`intent_probes.py`。

**整个生产 owner 节点仍 in_progress**。该签收支持及时提交已完成的原生 core 源码；没有替代 owner adapter/factory、真实公开 12 题跨组件运行、真实模型缓存恢复或金融准确性验收。审查者 0 付费 API、0 密钥读取、0 生产数据库修改，未修改任何实现源码。

## 正常提交 hook 的换行等价附记

原仓正常 pre-commit 首次提交因 mixed-line-ending hook 将 5 个文件 CRLF 转为 LF 而按规则停止；未绕过 hook。独审逐一读取 15 个实际工作树文件、原已签收候选和总控的 `native-precommit-normalization.json`，确认 10 文件字节完全相同，另 5 文件只有 CRLF→LF，且 15 文件含 type comments 的 AST 均完全一致。附录为 `runs/shared-engine-production-2026-10-18/independent-review/native-post-hook-equivalence.json`，已追加绑定至同一签收 JSON；原 CAS 与旧哈希完整保留。

这是原签收的精确等价绑定，不新增测试门，也没有重跑未改变行为的测试。支持按正常 add/commit/hooks 继续提交；整个 owner 节点仍保持进行态。
