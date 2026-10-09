# 实际 LLM 上下文使用接口：私有实施状态

2026-10-09；Phase111 在 IQS 独占 `runs/n111a/qa` 中实施，StockQA 源仍为 `42a517c`、生产 schema8。本批私有 schema10，不是生产发布或全项目验收。

`bind_external_question_context` 从实际、已计价的搜索记录构建并冻结短上下文。真正的同步/异步 `send_search_request` 在 HTTP 前重新核对工作项、租约、独立题面 manifest、TTL 和实际提示词；使用既有 Q09 预算与回答 attempt。external-only 请求没有模型原生搜索工具，explicit hybrid 保留原生工具并分别证明两条来源。来源内容按不可信数据输入，最终回答只读取正文，不返回 reasoning/thinking 区块；本测试不认证真实厂商的 thinking 配置或回答准确性。

不可变 `quick_scan_external_use_intent` 在回答发送前记录上下文哈希、实际完整提示词哈希、检索 operation/receipt 引用和租约。它不保存提示词正文或再次复制搜索摘要。`get_external_context_use` 只从既有实际回答响应生成 `stockqa.external_context_use/1.0.0` proof；实际模型不获许可、响应未保存或原生/外部模式冲突时没有可用 proof。原模型回执的 native `search_status`、原生搜索事件、URL、actual model 和 SHA 均保留，不伪造外部服务为回答模型。

实际检索引用严格核对 operation、query、route、kind、receipt SHA 和原检索时间，缺项/多项或重新哈希后的漂移仍拒绝。混合模式有原生搜索而缺外部 proof，不算全部搜索完成。回答落库失败保留未知预留，不第二次发送；使用意图落库失败发生在预算预留/HTTP 前。schema9→10 仅追加空使用表，既有已收费搜索记录和费用不变，不补造使用历史。

本批七个实际测试标签见 checkpoint04：首 RED9F；首 GREEN9F 原因为 fixture provider 与预算 route 不一致；修 fixture 后9P。新增边界 RED7F/14P中六项为真实私有实现缺口、一项为 fixture 猜错稳定错误文字。第一次边界 GREEN9F/12P 是读取实际 transport 的嵌套 attempt 路径错误；改为原 `work_transport.work_attempt_id` 后21P。最终八个受影响测试文件455P/0失败错误跳过，pytest36.24s、controller37.077s，执行源码 SHA 不变。HTTP 都是替身，真实 SQLite 和客户端实际运行；收费/真实 key/外仓写均0。

## 下一段实施，不另建 helper 审查门

1. 由真实 store/attempt 校验 proof，给通用结果和 C06 投影提供确实输入给 LLM 的来源 URL；不能把模型正文生成的 URL 当已检索来源，也不能修改原 native receipt 来绕过检查点。
2. 原 checkpoint schema1 的 SQLite CHECK 明确只允许1，读取、恢复、标准答案和 C06 adapter 也都显式校验1。新搜索 provenance 必须设计显式版本及原子迁移、保留旧 payload/hash/终态原样，不能暗塞进旧历史解释。此段尚未实现。
3. 接通原 runner/cascade、两阶段与跨租约恢复、逐 HTTP 计费的 MCP 握手和真实公开 CLI。所有路径仍复用原预算/health/attempt，而不创建第二执行器。
4. 完整 Phase111 批次完成后再做一次集中审查、正常 StockQA 发布及严格自有根清理。当前自有根保留；G3/F05/L03、真实身份/事实 golden、TH/IN授权和 StockWiki JR1/JR3许可仍独立未齐。
