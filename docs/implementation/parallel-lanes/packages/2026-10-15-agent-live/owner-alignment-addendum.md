# Owner对齐补充：原逻辑槽与实际类型题

2026-10-15，真实owner只读预检后增加。**原合同、inputs.lock及三个targets不重写。** 本补充描述新 `routed12-v1` 实验变体的显式投影，必须在公司真实S1请求前登记；不能事后更换题目或将历史raw12与新变体混为同一组。

请求前变体登记：[routed12 amendment](../../../experiments/company-agent-routed12-amendment-2026-10-15.json)。原预算/重复数/截止日不变；实际新manifest与有效题仍须在首次公司请求前锁定，目前尚未finalized，live_enabled=false。

实际发现：Alphabet的原10月11日native manifest有30道有效题，登记12个通用题中11个原对象完全匹配；IQS_11被OPERATING_01替换，实际metric为score.operating_01、construct仍为IQS_11。原生路由层执行校验通过，只允许证明这一历史快照与主体绑定，**不批准新模型、12题费用或10月13日新路由**。

## 新的旁路载体（不修改ResearchRun1.1或原题）

`iqs.agent-question-projection/1.0.0`，通过task2.0/评测matrix的显式file_ref声明。每个原逻辑slot至少记录：

|字段|含义|
|---|---|
| company_key | 原三公司键 |
| benchmark_question_id / benchmark_question_object_sha256 | 原登记槽与原完整对象hash |
| effective_question_id / effective_field_id | 原生manifest中真正有效的题和metric，不能人工改名 |
| construct_id | 与原逻辑槽相同的投资构念，不表示题义/分数完全相同 |
| effective_definition_sha256 / effective_semantic_sha256 | 实际题的原生绑定 |
| mapping_kind | direct 或 type_replacement；缺失/冲突另列gap，不猜 |

整个载体含原manifest file_ref、登记/manifest cutoff、scope、execution_ready与qualification_granted。当前提供的真实诊断全部execution_ready=false、qualification_granted=false；主体/路由真实不等于收费授权。

解析规则：先找原id；若不在有效题中，只接受唯一一项同时满足 `construct_id==原id` 且 `replaces` 含原id的有效题。仅名字相似或hash相同不能认替代；多项/无项为gap。不能直接将原通用题重新塞回被类型模块替换的有效集合。

## 三包各自处理

- RUN：task2.0显式接投影及当前native manifest。模型真正收到effective题/原锚点，输出ResearchRun1.1使用**实际question_id**。原逻辑槽映射通过旁路file_ref保留，不修改旧Run schema、原task1.0或回答题号。真实cutoff/权限/题hash不符在POST前拒绝。原始raw12作为兼容/合成回放保留，不能伪装正式owner可执行。
- REF：仍保留原36个逻辑construct槽；标明支持的是通用构念还是具体类型变体，目标相关的短事实可复用。不得把操作题锚点当成原通用题同义；其他两公司尚无本补充提供的真实投影，保持未决，不按Alphabet模式类推证券公司。原expected_score不补。
- EVAL：matrix显式声明raw12历史或routed12-v1及projection_ref。研究Run槽按实际qid读，分析分母按已登记的12逻辑槽映射；原题与实际题分列，不能改答案题号。相同公司/变体内三策略配对；不同effective语义/metric跨公司不默认可比。多映射、重名、错construct、投影漂移、截止冲突或未授权投影全部有反例。

如果原载体严格schema无法直接放旁路ref，在本包配置封套加显式字段/新版本，不向历史封闭schema私加字段。原合同carrier1.0不被本补充重签；具体新配置格式在interfaces-used交接，公共Run1.1边界不变。

## 输入与开工边界

额外真实诊断快照与hash见 [owner-alignment.inputs.lock.json](owner-alignment.inputs.lock.json)，与原3703文件输入锁分开。默认冻结根为 `runs/agent-wave-2026-10-15/owner-alignment-inputs`，不能用其原始来源路径回源读取或写生产库。它是read-only native owner诊断，不是金融oracle或confirmation golden。

继续只写各自新根；不修改StockQA/StockWiki/原Lab或别包。无需等另一新包交付：可用明确synthetic的effective题/投影验证完整正反链，真实新cutoff/native授权由总控补齐。每包只在整包节点集中检验，本补充不增加helper审批门。
