# SESSION-PACK-04：共享公司资料，分段使用短会话

唯一可写根 `C:/Users/郑曾波/Projects/iqs-session-packing-lab`。先读本卡、integration-contract.md、inputs.lock.json；其他所有仓/Lab只读，三包无新依赖。不发真实模型、搜索，不碰预算/owner。允许注入并调用已冻结SDK的**离线假HTTP**进行契约测试，不写新网络客户端。

## 要验证的方案

“每公司一个agent”不必等于一个不断膨胀的模型对话。保留公司统一公开证据与调度状态，各问题包用新的SDK短会话；静态prefix可共享provider缓存，但不把另一组隐藏思考、长草稿和格式错误历史全带入下一组。先做fixed3，其他策略通过显式controller选择pack接入，不擅改原策略实现。

本包交可复用分段适配器、可回放的公开分段记录及离线证明；不声称真实缓存更高、费用更低或准确性通过。原长会话路径继续存在。

## 已锁公开接口

包名 `iqs_session_packing`：

```python
def create_segmented_session(session_factory, *, system_prefix: str,
                             tools: list, limits: dict, context_ref: dict,
                             checkpoint: dict | None = None,
                             checkpoint_canonical_sha256: str | None = None): ...
# 返回对象：
# select_pack(pack_id, question_ids, *, committed_answer_hashes, prior_tool_results)
# step(*, user_context=None, tool_results=None, continuation_context=None)
# public_state() -> dict
# close()
```

session_factory由总控注入，接收原ResearchChatSession的system_prefix/tools及resource kwargs，返回原SDK兼容对象；不读取key或自己构造LLMClient。limits严格含max_sdk_steps、max_output_tokens、session_input_tokens、session_output_tokens、wall_seconds，正整数，max_output_tokens≤16384。**max_output_tokens是单次HTTP输出上限，不是全公司总量，不逐次扣减该上限值**；其他四项是整个公司任务累计限制。wrapper负责SDK调用总数和累计实际usage/墙钟，新段的SDK只收到剩余input/output/wall额度（max_sdk_steps由wrapper管，不传给SDK）；新段可将单次max_output设为min(原单次上限,剩余output)，剩余0则停止，不能段段重置累计预算。未知usage/不明发送立即阻塞适配器，不自动新建段或重发。

step遵守SDK真实tool_call_id；同段pending结果严格完整匹配。select_pack首次创建段；切段前，上一pack全部题须有controller提交hash，并且prior_tool_results精确覆盖实际pending ID。结束旧SDK，记录这些结果“本地确认、会话关闭、未再发provider”，不能伪造provider已收工具结果；新SDK下一步用user_context，不把旧call_id塞入新会话。需要LLM消费某个工具结果时必须留在旧段完成，不能自动丢弃pending。controller输入是受信任务调度数据，不能把模型自称完成当提交证明。

context_ref绑定同公司/cutoff/题集/证据hash，所有段prefix/tools字节相同；另一家公司、变题、变证据应开新任务，不默续旧会话。public_state新protocol `iqs.segmented-research-state/1.0.0`，保留段号/pack/调用ID/真实native receipt引用、公开输入与结果hash、累计已知usage/未知状态/关闭原因；不序列化SDK对象、key、provider messages或隐藏思考。

checkpoint状态必须显式含原limits、sdk_steps_used、input_tokens_used、output_tokens_used、usage_complete、原公司started_at/deadline UTC、当前累计elapsed及未知/pending标记，SDK step与实际HTTP另计。重启仍受原deadline，停机时间不赠送新墙钟；当前时间早于原started_at等异常则拒绝恢复。恢复核context/limits/prefix/tools hash，不能提高额度或清零计数。公开结构化工具结果可留原件引用与rawSHA，不能只存hash却宣称已复原工具正文；controller负责引用加载与校验。

崩溃恢复只允许用公开checkpoint开启**新的**剩余已知任务段；传checkpoint时必须有调用方可信的checkpoint_canonical_sha256并匹配，不能自己从已篡改内容重算expected值。累计调用/token/墙钟预算和context原绑定继续，controller校验原native引用真实归属，适配器不代owner认证。任何未确定实际发送的pack保持inspection_required，不能从本地缺答案推断没发送。不要宣称可恢复旧SDK私有对话。可明确拒绝有pending/unknown的恢复，而不虚构完美恢复。

CLI `python -m iqs_session_packing plan|replay --inputs ROOT --scenario FILE --out NEWDIR` 只做离线合成传输；无live开关/密钥参数。schema、样例、controller最小接入示例齐备，示例不修改真实driver文件。

## 实施与验收

1. 关键RED先覆盖跨段额度重置、旧call_id串段、未知失败后偷偷换段继续，再最小实现状态/版本。
2. 单元：重复/冲突pack、未提交即切段、pending少/多ID、同段真实结果续传、跨主体/cutoff拒绝、边界额度和墙钟、未知usage不当0、重复close、禁止序列化私有对象、旧checkpoint版本拒绝。
3. 集成：两个明确synthetic公司×四个3题pack；调用原冻结SDK+假HTTP，核确实建立独立私有会话、同公司prefix相同、不同公司证据不串、上段历史不进入下段、所有native发送/usage只累计一次。预算仅临时测试库，不接真实S1。SDK logger按CWD建logs，必须在自己临时CWD中首次导入SDK，临时日志/SQLite由本包创建与清理，不能写输入快照/主线或其他源仓。
4. 使用T1真实问题/结果只做只读数据流回放，不能把缺失57槽补出成功；原标准答案逐字节/语义保持，不擅改分数。
5. 公开CLI E2E：正常分段回放、段内崩溃、未确定发送、已有输出、路径逃逸；网络/外根写保护与finally清理。输出分段与长上下文的bytes/消息数差异；无真实usage不得称缓存命中或token节省。
6. 一次包级整套验证，交 `docs/handoff/SESSION-PACK-04/`，用同目录handoff模板。给主线接入diff建议而不改IQS/StockQA；与上一轮codec/judge/cache候选无依赖。
