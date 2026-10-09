# 公开结果与外部搜索绑定：Phase111接续接口

2026-10-09。IQS消费者已接入新格式；StockQA生产源仍42a517c/schema8。本批生产者修改仅在runs/n111a/qa，完整Phase111、公开CLI、MCP、源发布仍未完成。旧checkpoint01–05及其接口/执行字节不修改。

## 版本与拥有者

- `QABatchResult.to_quick_scan_dict(..., work_store=actual_store)`：无外部使用意图时仍输出`stockqa.quick_scan_result/1.0.0`，原字段/行为保留；含实际外部使用时输出`stockqa.quick_scan_result/1.1.0`。混合批次可保留原生题的原字段，外部题必须有新binding。
- 外部结果序列化必须重新读实际QuickScanWorkStore：核work的entity/question、实际use proof、原最终HTTP记录和原始回执。没有owner、错公司/题目、外来或重哈希proof、原native receipt漂移均拒绝；不把元数据自述或self-consistent hash当权限。
- `scripts/stockqa_adapter.py`是无I/O消费者，接受1.0/1.1；1.0夹带external binding拒绝。它只核可信producer公开输出的一致性，不能独立认证搜索发生、费用或金融事实。答案始终`unverified_model_output`，没有审计晋级。
- 现有router2.3与RouteV2保持模块/评分政策；新增可选的`stockqa.search_binding/1.1.0`承载外部来源。旧无binding历史可读；新binding不可放入2.0–2.2的历史router。来源校验同时覆盖新执行和归档读取，包括unknown/无candidate的结果。

## 公开绑定结构

每个外部题的execution_receipt附带`search_binding`，只有六个字段：

```json
{
  "schema": "stockqa.search_binding/1.1.0",
  "entity_id": "<实际work的发行人ID>",
  "question_id": "<实际work题ID>",
  "identity_snapshot_sha256": "<实际身份快照SHA-256>",
  "external_context_use": "<actual_store派生的use/1.1.0对象，非字符串>",
  "native_receipt": "<actual_store保存的原始sanitized HTTP receipt对象，非字符串>"
}
```

上面是结构示意，不是可执行fixture/golden。use对象保留use/work/work_attempt/context/manifest/请求prompt/原LLM receipt hash、实际provider/model/使用时间、六字段检索引用及外部URLs。不会输出lease token、数据库路径、prompt、思考正文、网页或财报正文。

重要区别：`work_attempt_id`是耐久work attempt；公开/native `attempt_id`是原HTTP attempt。两者由实际owner关联，不要求文本相等。`request_prompt_sha256`包含system和用户prompt；原HTTP `prompt_sha256`是实际用户prompt hash，也不要求两者相等。禁止为适配而改写其中任何一个。

原native receipt digest沿用StockQA的ASCII JSON canonicalization（sort_keys、紧凑分隔、ensure_ascii=True）；use proof digest沿用原journal的UTF-8 canonicalization（ensure_ascii=False），不能混用。生产者同时验证原始sanitized receipt与实际保存字节相同。

通用search_receipt_id指向actual use ID，source_urls为原native来源在先、external来源在后的稳定去重集合；原native搜索状态/ID/URLs/模型/body digest仍在native_receipt，真实`web_search_calls`原样保留。external-only必须无native调用；hybrid必须有真正完成的原生调用及相符URL。路由schema允许既有native调用返回的`sources`短元数据（url/title/published_date），不制造工具事件。

## 消费者验证与边界

`external_search_urls`核精确binding/use字段、两个hash、公司/题ID、实际provider/requested/actual/HTTP attempt、原2xx completed响应、原body/model-resolution hash、使用/检索/回答时序和URL集合。检索operation不可重复，缺来源/未知模式/自授权字段拒绝。调用方提供独立identity_snapshot_sha256时必须匹配；routing不会丢弃该独立输入。

归档unknown分类不代表无需验证回执；其所有候选仍为空、score=null，原检索证据只说明搜索和回答绑定，不说明公司类别或投资价值已确认。module置信度阈值、周期/困境观察保留与旧政策不改变。

## 当前实际测试及恢复

证据在`docs/implementation/intake/QA-NET-01/2026-10-09-external-context/verification/public-*`。既有guard拒绝外网、密钥继承和自有根外Python写，所有数据库、HTTP替身和临时发布包隔离在runs/n111a。producer->JSON->IQS routing例实际运行client、SQLite、serializer和router；HTTP/model内容及身份/价格均synthetic，QAResult在既有答案边界构造，不冒充公开CLI、StockWiki owner golden、付费厂商或金融准确性E2E。

原RED和控制器错误保留，批次数不加总为总覆盖。`run_consumer_tests.py --producer`同时冻结两仓边界源码，`--affected`扩大各自相关回归；每次必须新label，不覆盖旧目录。最后一次通过的真实结果由progress和本批新checkpoint索引记录，不能照抄本接口的预期。

下一步仍是实际runner/cascade检索调度、异步provider投影、两阶段/跨lease恢复、逐HTTP MCP握手及公开CLI，再一次集中相关回归/静态/独审、StockQA正常源发布和严格自有根清理。当前环境仍有未完成实现，不删除runs/n111a。StockWiki四新路径、真实gold/G3/F05/TH-IN授权等原门独立不变。
