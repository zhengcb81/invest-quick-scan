# 复用 StockQAbyLLM

本skill只编排题库与检查轻量结果，不复制API客户端、密钥管理、提供商、搜索、重试、缓存或请求调度。默认上游仓库为`C:/Users/郑曾波/Projects/StockQAbyLLM`；生产调用应使用StockQA自己的环境和公共CLI。

2026-10-07核查的原生搜索、外部证据context及缓存边界见[搜索策略](search-policy.md)。[外部搜索来源清单](../examples/search-provider-inventory.json)登记Brave、Tavily及用户新增的Z.ai MCP/REST；它不是执行器配置，不能据此启用搜索或改模型顺位。下方旧批次验收数字保留为历史记录，当前能力以搜索策略的日期和实际源码/回执为准。

用户设置的接口地址、模型标识、环境变量名和脱敏连通性证据见[提供商连接配置](../examples/provider-connectivity-profiles.json)，schema为`../schemas/provider-connectivity-profiles.schema.json`。密钥值必须留在运行环境，不能写进该文件或日志；模型优先级只由`examples/model-policy.template.json`管理。DeepSeek的Anthropic兼容Messages接口已直连验证服务端`web_search`，但一次`max_uses=1`探针返回了两次搜索事件，因此现阶段不能依赖该参数限制搜索费用；StockQA适配及单公司端到端验收仍未完成。

2026-10-07复测更新：DeepSeek Responses旧别名映射为`deepseek-flash`，完整回答仍无搜索事件；Anthropic兼容接口再次证实搜索，但`max_uses=1`出现3次调用，且本次强制工具响应无最终答案。完整记录见[搜索策略](search-policy.md)，不要把直连搜索阳性等同公开CLI公司问答通过。

## 当前协议

| 能力 | 当前边界 |
|---|---|
| 旧strict | `score/description`兼容路径继续保留；仅由旧normalize读取独立审核文件中的`accepted_ids`，不自动迁移。 |
| 新筛选题包 | `scripts/question_sets.py compose --answer-format screening-1`导出含`question_id`和`text`的StockQA JSON题目，并在manifest显式写入protocol版本。 |
| StockQA执行 | `main_with_llm.py --company ... --provider ... --config ... --output ... --require-search --entity-id ...`调用可验证搜索；Q01—Q03修复分数透传、native null、身份/问题绑定和搜索来源；Q12让公开回执带实际`Question.text`哈希及成功HTTP状态码。 |
| 快扫导入 | `question_sets.normalize()`按manifest的`answer_format`显式分流。screening-1要求版本化bundle和`stockqa.quick_scan_result/1.0.0`结果，不读或生成旧`accepted_ids`。 |
| 深研接受 | screening输出固定为`formal_research_status=not_accepted`。它不写StockWiki正式证据、不替代company-wiki资料流程，也不创建公司文档。 |

Q01—Q03与Q12的离线调用契约通过独立复核。Q12定向测试64项通过；StockQA全套中除25项与本任务无关的`tests/unit/test_http_client.py`用例外，461项通过、1项live测试跳过。未过滤全套在当前沙箱因无法读取Miniconda `certifi` CA文件而有13项HTTP client测试失败；这些失败发生在客户端TLS上下文初始化，与Q12无关。OpenAI真实联网测试仍因本机没有`OPENAI_API_KEY`/`STOCKQA_OPENAI_API_KEY`而跳过；不能据此宣称真实搜索或付费调用已经通过验收。

## Screening bundle

本地导入bundle结构固定为：

```json
{
  "schema_version": "invest-quick-scan.screening-import/1.0.0",
  "manifest_sha256": "按规范JSON序列化计算的SHA-256",
  "input_question_sha256": {"IQS_01": "对应manifest prompt的SHA-256"},
  "result": {
    "schema_version": "stockqa.quick_scan_result/1.0.0",
    "entity": {"entity_id": "稳定实体ID", "name": "公司全名"},
    "observed_at": "UTC时间",
    "provider": {"name": "openai", "requested_model": "请求模型"},
    "answers": {"IQS_01": {"question_id": "IQS_01", "status": "scored", "score": 8}},
    "execution_receipts": {"IQS_01": {"search_status": "executed", "search_receipt_id": "执行器回执"}}
  }
}
```

上面省略的字段仍由公开StockQA结果完整提供；示例不能当可导入样本。负责启动CLI的本地协调层把其实际使用的manifest hash和题目prompt hash与原样CLI结果封装在bundle中；StockQA逐题执行回执由Q12实现为对实际`Question.text`计算的SHA-256及真实HTTP状态码。导入器会和manifest逐题精确比较哈希，要求顶层与最终attempt HTTP状态均为整数200并完全一致。回执还需带实际厂商/模型、响应/attempt ID、UTC回答时间、搜索回执、已完成搜索调用及来源URL；普通请求保留非空HTTP请求ID。MiniMax没有返回HTTP请求ID时允许逐题与最终attempt的`request_id=null`，前提是最终attempt也确认实际厂商为MiniMax，且响应、搜索与来源绑定均已验证，不能补造请求ID。多厂商批次的顶层`provider.name=null`，逐题实际厂商和请求模型须由最终attempt的厂商、模型及路由ID互证；`provider_config_ref`只是配置别名，不能当真实厂商。StockQA直连单厂商尝试可仅有`provider_config_ref`别名、`dispatch_outcome=null`，其旧回执按原条件导入。只要任一attempt含`route_id`、`route_ordinal`或`route_trace`，或顶层厂商为null，即按多路由回执校验：最终attempt须有真实厂商、请求模型及完整路由身份，逐题`dispatch_outcome`须为`completed`；若最终attempt公开`route_trace`，其末项须为匹配该路由的`accepted_answer`。导入器逐题校验search receipt ID与唯一已完成搜索调用的绑定，并要求每条证据URL属于该回执所指的搜索调用，答案内层信息日期与manifest截止日一致、历史期间不越过截止日。

截至2026-09-24，Q12已让`quick_scan_result/1.0.0`公开回执输出原始输入题目哈希和成功attempt HTTP状态。本地screening导入器在StockQA原样CLI输出上通过隔离跨仓测试并得到8分筛选观察；任一绑定不匹配时仍失败关闭，保留reported值但不采用screening score。该验证在HTTP发送边界使用固定Responses API回包，不发起真实联网或模型调用。

导入结果同时保留`reported_score/reported_status`和正式筛选字段。全部检查通过后可设`screening_checked`并颁发绑定实体、题目和结果摘要的`screening_audited`检查回执；不通过则保留reported值、正式分数置空。任何模型自报`accepted_ids`、`search_verified`或check level不能提升资格。低置信度不进入均分，未经核实的N/A不能从覆盖率分母扣除。正式深研级别仍由独立拥有者授予。

## 离线命令与端到端边界

先生成题包：

```powershell
python -X utf8 scripts/question_sets.py compose --profile examples/profile.json --mode quick --answer-format screening-1 --out-dir runs/score-screening
```

随后由StockQA公开CLI运行该目录的`questions.json`。归档原样结果和输入绑定后，以`question_sets.normalize(manifest, screening_bundle)`或现有`normalize --manifest ... --answers ... --output ...`导入；新模式不传`--review`。这条路径目前还不是最终一键运行器，批量接续、模型顺位/额度调度、统一数据库和结果UI仍按实施计划后续跨仓接线。

本地S02回归在唯一临时工作目录导入真实StockQA类并调用真实公共CLI；只在HTTP `Session.post`边界使用固定虚构Responses API响应，真实搜索响应解析器、provider、runner、CLI和序列化器均实际运行，不发网络请求、不产生LLM费用。API配置、日志、题包、输出均在唯一临时目录，字节码写入被禁止；成功和强制异常路径都验证文件句柄、模块缓存、cwd、参数、环境和临时目录恢复，并核对StockQA源码树的pyc文件零漂移。成功路径检查CLI自行生成的原始问题哈希和每次attempt的HTTP 200，筛选导入得8分，formal research仍为`not_accepted`；负例验证最终attempt回执篡改会失败关闭。真实网络与来源内容准确性另由启用密钥的live验收覆盖；没有密钥时该live验收保持未执行，不能用离线fixture替代。
