# StockQA执行线：搜索、LLM、预算、工作状态与轻量回执

**Owner:** StockQAbyLLM项目owner。

**项目目录:** `C:/Users/郑曾波/Projects/StockQAbyLLM/`；一个写入harness独占全仓，禁止另一个agent同时写StockQA。

**授权:** 用户已授权StockQA全仓修改，但每个批次必须在写入前把精确文件清单和目的报备；此lane文档不扩大授权、不授权真实API或费用。

**第一候选:** Q04；当前Q03结果路径任务级验收通过，但准确StockQA树有55项既有未提交状态，故需先冻结包含Q03修复的准确基线。

## 独立上下文与职责

StockQA执行版本化问题，负责模型优先级/故障分类、搜索receipt、逐题任务、预算/并发、重试/检查点/outbox、配置与可控公开运行入口。它消费IQS question/recipe/release与StockWiki的权威身份/dispatch fence/ACK契约；不能复制StockWiki名单、身份映射或正式观察库。公司输入只在prompt/内存处理并产生允许保存的结构化答案和最小来源receipt，不下载或保存财报、网页正文或公司档案。

## 任务范围与包内顺序

负责`tasks.json`中owner=`stockqa`的26项：Q01–Q05、Q06–Q12、Q13/Q14/Q15、F02、L01/L03、B01、O02/O04、X01/X03、V06/V09/V14。任务依赖不可跨越；同一执行链内按`depends_on`顺序完成。

重要写入簇共用runner、parser、attempt/outbox、预算与transport，必须由同一线连续实现：

1. Q04/Q05/Q08/Q09/Q11/Q12/Q14/Q15：provider cascade、策略snapshot/revision、失败分类、预算并发、答案parser与dispatch fence。Q04第一阶段只处理LLM-10运行中revision和PAR-11路由槽位等待，并先查明公开CLI真实构造/调用链。
2. Q06/Q07/Q10/Q13/V09/V14：work store/逐题检查点、结果outbox、recipe与facts执行及回执。
3. X01/X03/O02/O04/V06：公开runner/配置/能力与公平调度；只能在依赖门通过后接入。
4. L01/L03/B01：运行试点/搜索分组benchmark是评测包，不与生产数据混跑；只用独立临时目录、用户提供的公司名单和已确认的预算。

## 依赖接口

输入：IQS版本化问题模块、ScanRecipe、provider capability/compatibility、budget policy；StockWiki identity snapshot与一次性permit/ACK等公开版本协议。

输出：标准答案/unknown状态、request/response ID、模型真实provider/model ID、policy/recipe hash、executed search receipt、来源最小元数据、预算账本、任务/dispatch/outbox回执。输出可重放但不可改写历史；route alias不冒充provider。

Slot满时同route要有界等待/恢复语义，不得因为本地容量等待自动转备用模型；policy热更新只应用到未派发工作且记录确切dispatch边界。失败请求如可能已发送必须保持outcome_unknown，不能无依据重复付费。

## TDD测试包

- Q04：先加公开调用路径RED反例；`tests/unit/test_llm_integration.py`覆盖运行中policy revision和next-run生效边界；`tests/integration/test_quick_scan_budget.py`用受控阻塞HTTP证明同route并发槽满时不fallback、槽释放后用原route发送、超时则零POST/明确延期。按预报文件清单后，可能需要新增/改runner、provider cascade或budget transport测试，路径须先检查并报备。
- Parser/receipt：相关`tests/unit`与`tests/integration/test_quick_scan_cli.py`验证unknown/null不可被外层分数覆盖，dispatch/search/source receipt在错误/中止分支仍保留。
- Work/budget：隔离SQLite/多进程fixture，覆盖幂等settle、额度不足、未知费用、进程崩溃和并发；无真实账户。
- E2E：公开QuickScan CLI对mock搜索provider走完整question→answer→receipt→outbox/ACK；测试SQLite/HTTP均在唯一临时根中，结束断言根目录移除、正式公司目录无新增文件。
- Real/live：只在明确批准的单独测试case执行；运行前检查API key是否存在但不输出其值，只有用户确认的model/provider/sample/budget允许发包；保留脱敏计价证据，不能让live测试默认进入普通suite。

README/pytest配置经预检确定实际命令；移除shell里的live opt-in和provider key，offline batch强制mock网络。高风险结算/并发/实际POST前围栏可额外review，普通Q卡并入G1/G3/G6一次大节点审查。

## 文件边界、基线与交接

worker开始前给IQS总控精确列出拟写路径和行为目的；先保存当前Git HEAD、status路径及文件SHA。当前观察到55项既有工作树状态，严禁reset/checkout清理、整树暂存或将其混入提交。必须用有标签的只读快照/独立工作树；若目标快照不含Q03修复，不得开始Q04。测试路径按原子任务allowlist申领，先查`AGENTS.md`和CodeGraph。

handoff应包含Q04的请求派发边界图、精确策略revision语义、RED/GREEN测试、并发时间线、每个route/provider状态、POST计数、完整测试统计与清理结果、base/head/所有源测试SHA、未解决P0–P2。若不能在保留他人脏更改的前提下隔离，状态写`blocked`并交回总控处理，不要主动commit共享脏树。
