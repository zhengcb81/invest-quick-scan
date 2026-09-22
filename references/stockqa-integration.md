# 复用 StockQAbyLLM

检查基于 2026-09-19 的本地代码。默认仓库 `C:/Users/郑曾波/Projects/StockQAbyLLM`；可由用户另指定。保留配置、密钥、HTTP 客户端、提供商、重试和缓存于该仓库，本 skill 不实现这些功能。

## 已确认接口

| 接口 | 契约 |
|---|---|
| `src.config.json_config_manager.JSONConfigManager(path).load_questions()` | 接收 `[{category, questions: [字符串]}]`，不能直接传本 skill 的结构化题目对象 |
| `src.providers.llm_provider.LLMProvider(company_name=..., provider_name=..., config_file=...).search(question)` | 返回 SearchResult 列表；评分位于第一项的 score，描述位于 snippet；复用既有重试 |
| `src.providers.llm_client.LLMClient.send_request()` | 既有 HTTP 请求发送者，搜索能力修复应发生于这里或上游配置适配层 |
| `main_with_llm.py` | 接收 `--company --provider --config --config-format json --output`；当前显式传 provider，不能依赖默认值 |

## 目前需要先解决的上游缺口

1. `LLMClient` 与异步客户端的请求体只有 model/messages/temperature/max_tokens，未传搜索工具或厂商搜索开关；`SearchService` 是占位实现。服务端是否自行提供搜索尚未验证。提示词写“开启搜索”不能改变这个事实。
2. 单公司 CLI 经 `AnswerGenerator.generate_answer()` 将普通成功回复 score 设为 5，未使用 `SearchResult.score`。CLI 输出成功率也不足以证明每题有效。不要直接平均 raw score。
3. 解析失败、缺密钥和部分异常会产生默认 5；原始模型内容和 API 搜索元数据没有完整透传。来源必须放在 description 内；搜索执行证据需由上游运行层保存。

本阶段已完成问题库、导出和离线结果校验，**尚未声称实际联网问答已跑通**。以后修复客户端搜索参数、搜索执行记录和分数传递应在 StockQAbyLLM 完成，不能在本目录偷偷建立第二套 API 系统。

## 实际调用路径

先在上游验证所选 provider 的真实搜索执行（请求中正确的厂商开关或经验证的服务端搜索配置，以及搜索事件／返回来源）。一次小规模真实问答通过后，再执行整套问题；provider 不支持或无法确认搜索时返回 search_unavailable，不能退回模型记忆评分。

2026-09-22复核实际代码与离线调用链：提供商返回8，AnswerGenerator仍写5；客户端请求体仍未见搜索工具开关。Q01/Q02/Q03必须在StockQA修复，不能把本地schema验证当上游能力就绪。

生产接入在StockQA自己的解释器/工作目录执行，经版本化公共CLI/本地协议交给StockWiki；不在其他仓库用sys.path拼入StockQA内部模块。现有JSONConfigManager字符串问题格式可以继续使用，但标准评分/事实答案须原生透传JSON对象和独立执行回执，不能走旧默认分数包装。旧解析器只供明确的legacy兼容路径。

接收数据边界见[标准输出](standard-output.md)：StockQA拥有requested/resolved模型、UTC时间、搜索与费用回执；本skill只校验/编排。事实score=null，provider实际模型未知留null，错误不填默认5。公开运行/能力接口仍由Q/X系列卡实现，本页不假称已有可运行的生产命令。

分类也使用同一接口。分类题的内层 description 包含 routing 对象，由运行者核实后保存 profile。其 score 只评价路由可信度，不进入后续画像。运行完成后按 scoring.md 建立独立审核文件，再执行 normalize；审核文件不能由模型在自身答案里声明。

## 离线验收边界

离线测试验证真实JSONConfigManager能读取24题核心导出、真实解析器保留内层结构、题目路由和评分校验正确，并检查可选诊断不重复计分、关键问题不会被高均分掩盖。测试使用假响应和虚构公司，不使用密钥或产生LLM费用，不证明网络搜索能力、来源真实性或实际分析准确性。
