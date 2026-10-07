# QA-NET-01｜搜索与模块增量执行闭环

这是可单独交给 StockQA harness 的大包。唯一源仓为 `C:/Users/郑曾波/Projects/StockQAbyLLM`；当前沙箱外只读观察 `master@6a9ff13864ebb160d5c4ab3cf2f42155d9f4aa99`、7个既有未跟踪项（inputs.lock列明），原样保留，不检查/清理其内容。不写 StockWiki/IQS/研究技能/company-wiki。读[共同交接规范](handoff-rules.md)和[输入锁](inputs.lock.json)后开工；每批按既有 StockQA 全仓授权先报告确切文件/目的。本包默认离线，不发真实 provider 请求。

## 目标与已经完成的底座

覆盖任务 Q10 剩余 glue、Q13，以及 Q02 搜索能力的增量适配。本包不是重新实施 Q02/Q06/Q07/Q09/Q10 底座：用户模型順位、共享账户冷却、预算/并发、work/lease、逐题检查点、C06 adapter/outbox/ACK 原语已有实现和审查。直接复用。

还缺两件产品行为：检查点落定后 runner 调用 C06 adapter 并封存/记录阻断；消费冻结模块问卷，仅派新增/过期的具体题而不重问成功题。在此基础上接外部检索证据路径和经过验证的原生协议，采用[联网规范](../../../../../references/search-and-llm-playbook.md)，不能再写一层通用重试器绕过既有状态机。

当前连通证据：MiMo/MiniMax 指定原生搜索协议已有生产接线；Brave/Tavily 只在 B01 实验中使用；Z.ai REST/MCP 直连通过，未接生产；DeepSeek Responses 忽略 web_search，Anthropic 兼容有关联结果但 stop_reason=tool_use 无最终答案，且 max_uses1 实际3次搜索。这些只是精确 route 的能力证据，不默认启用新模型/顺位或保证计费。

## 写入范围

预期自有文件族（开工要列成确切清单）：

- `src/runners/llm_runner.py`、现有 QA engine/answer_generator、`main_with_llm.py`：冻结 manifest 输入、检查点→封存/阻断及公开参数。
- `src/utils/quick_scan_c06_adapter.py`、现有 work_store/outbox/transport/provider 边界：只补经反例证明的缺口；不得重构已验证状态机或修改 C06 公共 schema。
- `src/providers/` 下现有 llm_client/llm_provider 与新的搜索 adapter/证据规整模块；`src/config/` 下必要版本化配置/schema。新模块命名由现有仓布局决定，实施前逐项报备，不复制 IQS 的 LLM 客户端。
- 该仓已有 unit/integration/公开 CLI 测试、新 adapter 的离线测试、`docs/handoff/QA-NET-01/`。`.gitignore` 只有本包新公开配置/schema 被既有规则误忽略时精确例外，不整类取消忽略。

禁止改动：生产配置/名单/DB、凭据值、B01 冻结输入或历史结果、StockWiki 私有表、IQS 题库/schema/中央计划、安装目录。不能拿未知权威字段从答案自由文本猜补。

## 固定接口

| 接口 | 消费或产出 | 不可改变的语义 |
|---|---|---|
| S05/S06 冻结 manifest/release/route | 消费 IQS 已发布输出 | 问题 ID、模块/语义/prompt hash、作用范围均冻结；篡改在 HTTP 前拒绝 |
| C05 attempt/预算/model policy | 消费现有 StockQA 实现 | 用户模型与搜索顺位分离；outcome_unknown 不 fallback/重发；重启不清零 |
| evidence context | StockQA 内部版本化产出 | source_id/实体/截止日/题目映射、短证据/hash；不是新的 C06 公开顶层字段 |
| checkpoint→C06 package | 产出既有 C06 1.0.0 | 权威版本/身份/执行信息完整才封存；缺字段 durable block，模型请求0 |
| 导入 ACK | 消费 StockWiki W05/W10 公开响应 | package/item/observation/payload/store 全匹配；丢 ACK 不重问 |

C06 v1 当前 adapter 对 unknown 等状态有自己的拒收边界；不为“结果全入库”偷偷放宽 schema。先持久保存原检查点/缺口，需要协议扩展交总控。外部 context 的搜索证明必须标 external，不能伪造回答模型原生搜索回执；输出仍需满足现行可表达且已版本化的字段。若现行 receipt/schema 无法表达 external，提交最小加法提案并保持该路径未启用，不能塞 `extensions`。

配置应导入 StockQA 单一有效策略，参考 [搜索策略模板](../../../../../examples/search-and-llm-policy.template.json) 不可直接变成执行授权。厂商顺位由用户填；原生/external/显式混合冻结择一，不能默认同时双搜。按量、套餐、搜索 credits、MCP 发现/查单分别记账；缺明确计价/可控制成本上界时相应 paid route 拒发。Brave 的存储权需要账户 entitlement 确认；未确认可保存范围的 route 不能产出需要长期保存来源/片段的观察，不能根据“已买 API”猜有 storage rights。

## 实施顺序（一个 harness 连续推进）

1. 复查 Q10 卡与源码，先写 runner 公共入口 RED：有效检查点自动封存；缺 authority 持久 block；重启补齐只构包、LLM0。最小接线，不重写 adapter/outbox 原语。
2. 做 Q13 manifest 消费与增量：新模块只新增题；已成功/未 ACK/结果不明分别复用、重投、对账；未适用题不派。两个 worker 的同题租约、取消/崩溃恢复沿用 work_store。
3. 建统一搜索能力适配边界，给原生工具回执、外部检索、证据包、最终答案不同阶段。先实现离线 parser/transport 测试与不可执行配置导入校验，再接现有 runner。Brave、Tavily、Z.ai REST 和 Z.ai Streamable HTTP MCP 都通过同一所有权/预算边界，不引入第二全局 dispatcher；legacy SSE 没有本包准入证据，不优先开发。
4. 外部检索按冻结 query plan 规整去重、实体/时点筛选、按题选 context。只留允许的短条目；每条最多500 Unicode字符、每公司本轮最多30,000，发送 token 另计。网页命令当数据；证据不足留 unknown，不让模型刷分。
5. DeepSeek Anthropic 续写必须验证确切协议：有工具结果不等于最终答案，保留 tool_use_id 关联；每次真实续写重新准入/计费，避免重复强制搜索。Responses 继续拒作 native-search route。协议/费用上界尚未确认时保持该 route 未启用，交 partial，不编造最终答案或搜索数。
6. 每种失败只映射到既有可表达状态：普通429按 Retry-After；共享额度耗尽冷却整组；401/403按真实作用域；可能发送后的超时/断线记 outcome_unknown，保留预留、同 attempt 对账。仅已证明未发送或终态结算后才新 attempt。有效低分/缺证据不触发模型 fallback。
7. 公开 CLI 离线 E2E 经真实 runner→checkpoint→C06 package；使用真实 StockWiki owner 接口/golden做 consumer-contract 测试，跨仓完整运行由总控收回后集中做。不把 mock ACK 当真实接收端验收。

## 本包测试包与完成标准

| 批次 | 关键反例/正例 | 精确结果 |
|---|---|---|
| 单元 | HTTP200但无搜索；嵌套JSON≤3层/超层/业务错；重复题ID/截断；错实体/时点/片段指令 | 不计分、不执行片段、不伪造来源；错结构分类明确 |
| 单元 | 检索器顺位与模型顺位；TTL/filter/locale/model版本/证据hash改变；存储权/费用未知 | 缓存准确失效，未准入请求发送0，未知费用不记0 |
| 集成 | 429/额度组/未知reset、首选满槽、5xx终态、Retry-After越deadline | 等待/冷却作用域正确，单半开探针，新发送有界 |
| 集成 | POST断线+迟到成功、consume后崩溃、双worker重启、ACK错hash或丢失 | 无盲重发/重复结算；原 attempt/outbox恢复，不重复模型请求 |
| 集成 | 增加模块/部分题成功/authority缺失后补齐 | 只问缺题，成功题不漂移；缺字段block后模型0仍能封存 |
| CLI E2E | 原生与external各走完整答案路径、tool_use续写、冷/warm、故障恢复 | 真公开入口；warm搜索/LLM0；stub仅在HTTP边界；临时根清理 |

case-map 覆盖 Q13 MOD-06/MOD-09/JOB-03、Q10 JOB-07/JOB-08/DB-07/PAR-10 与 Q02 LLM-02/LLM-11 增量路径；LLM-08等非本包 owner 仅引用原证据。新搜索故障断言编为本包场景，不擅改中央366 case或 reopen 已验收的 Q02 历史快照。

定向命令按新增真实选择器填写：`python -B -X utf8 -m pytest -p no:base_url <本包测试路径> -q`。提交前跑仓现有全量/静态门一次；base_url 禁用旗沿用已知插件隔离约定，不改全局插件。必须有 RED/GREEN 原始日志和精确源码/测试hash；未通过新 route 保持不启用，不用别的模型补成成功。

交付 [QA-NET-01.handoff.template.json](QA-NET-01.handoff.template.json) 及共同规范全部附件。interfaces.md 给可运行冻结 manifest CLI命令、有效配置/schema ID/hash、每个 route 的支持/未启用原因、最终答案/证据proof映射和 C06 golden生成命令。总控接收本包离线批次后才安排获准的有限 live；不自动运行 L03，不宣称200家公司或一键启动已经完成。
