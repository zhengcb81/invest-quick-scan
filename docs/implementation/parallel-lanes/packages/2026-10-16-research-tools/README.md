# 真实研究实验：三条独立工具线

## 最新派发状态 — 2026-10-16

用户已确认三张施工卡全部发出：ANSWER-CODEC-03、RESEARCH-JUDGE-03、CACHE-PLAN-03。三个Lab由各自harness写入，总控只读等待正式交付，不重复开发、不向其目录写入。下文“未派发”和inputs.lock的workers_dispatched=false仅保留准备时历史，不代表当前状态；原输入锁不修改。总控继续标准JSON bounded3真实实验。

准备日期：2026-10-16。**三包可开工，尚未派发，目录在准备时均不存在。** 目录存在、模板通过和工程测试通过都不代表用户已派发或金融验收通过。

| 施工卡 | 交付目标 | 唯一可写项目目录 |
|---|---|---|
| [ANSWER-CODEC-03](ANSWER-CODEC-03.md) | 紧凑答案传输→现有标准答案，减少重复输出，不损失理由、口径及引用绑定 | `C:/Users/郑曾波/Projects/iqs-answer-codec-lab` |
| [RESEARCH-JUDGE-03](RESEARCH-JUDGE-03.md) | 显式接受隔离研究输出，制作盲评包、导入人工判定、保留失败分母并解盲比较 | `C:/Users/郑曾波/Projects/iqs-research-judge-lab` |
| [CACHE-PLAN-03](CACHE-PLAN-03.md) | 复算真实 token/价格/耗时，离线分析前缀和请求顺序，分清已观测收益与模拟收益 | `C:/Users/郑曾波/Projects/iqs-cache-planner-lab` |

三个物理根不交叠，无依赖箭头。工人只读共同冻结输入，写自己目录；不要修改 IQS、StockQA、StockWiki、company-wiki、既有 Lab 或另外两条线。总控继续真实六会话改进试验及生产 owner 接线，不同时开发这三项候选。**本轮主线暂不实现紧凑 codec，以免重复施工；标准答案的 bounded3/反馈实验仍由总控推进。**

工人只需本卡、[共同接口与交接规范](integration-contract.md)、[冻结清单](inputs.lock.json)、清单对应的输入快照及自己的 handoff 模板。不依赖聊天记录或其他工人的新交付。外部源码只是只读适配依据，不得按当前 HEAD 自动升级。

默认快照：`C:/Users/郑曾波/Projects/invest-quick-scan/runs/research-tools-wave-2026-10-16/inputs`。**这些运行快照不随 Git 自动发布。** 同机 harness 使用此路径；异机交付必须一并复制快照，执行 `python -B -X utf8 verify_preparation.py --inputs <新快照根>`，不能回活动源补文件。清单相对路径不随搬迁改变。

快速开工顺序：

1. 读自己的卡和共同规范，核冻结 SHA；输入缺失明确报阻塞，不猜接口。
2. 确认自己根的真实归属；若已存在未识别的源码或其他 writer，先停下报告，不能 reset/clean。可在自己的根初始化独立 Git 与 PWF；沿用已存在的自己的计划。CodeGraph 未初始化按项目要求询问，但可先读文档，不需要为此暂停所有准备。
3. 先为关键边界写会失败的测试，再做最小实现，最后集中跑整包测试和公开 CLI E2E。**一个包级审查节点，不增加逐函数验收。**
4. 在自己根提交、记录交接；不要自动 push、新建远端或调用付费服务。总控按真实产物验收后集成。

背景：首轮 Alphabet 三策略×两重复共 21 次真实模型 HTTP，4/72 个槽形成合法标准答案，0/6 会话完整。缓存输入占比约 92.23%，公开价格估算 USD 0.100300，现金账单未知，金融准确性尚未判定。这说明需要分别解决输出负担、质量评估和计量问题，**不能因为缓存高就宣布 agent 成功，也不能把结构失败算成事实错误**。

用户已明确选择先隔离研究、后生产 owner。新工具只交候选；不写生产评分、名单、预算、发送登记或授权。真实模型/搜索实验、原生预算、准入、源码接入、正式金融结论均归总控。各包不发真实模型/Brave/Tavily/ZAI 请求，不读环境密钥；不下载财报、PDF、完整 HTML。

共同准备校验：`C:/Miniconda/python.exe -B -X utf8 verify_preparation.py`。该命令只核卡片、目录边界、模板及输入字节，不代表产品测试完成。
