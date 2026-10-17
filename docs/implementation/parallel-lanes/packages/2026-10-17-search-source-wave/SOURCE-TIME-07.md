# SOURCE-TIME-07：三市场官方来源、发布日期和证据支持范围案例库

唯一可写根`C:/Users/郑曾波/Projects/iqs-search-source-lab`，Python包`iqs_search_source`。先读同目录[integration-contract.md](integration-contract.md)与[independent-review.md](independent-review.md)。根在编卡时不存在，开工复查。全部离线，0收费请求/网页或公司文档下载，不依赖其他新包。

## 目标与不做的事

为总控DeepSeek/Brave/Tavily/ZAI对比提供**检索证据是否足以证明某命题**的离线挑战集与可核来源锚点，不选搜索赢家、不评LLM答案/公司评分、不另建金融数值scorer。不需要先取得真实搜索输出，不能碰REVIEW-CAL-06的代码/案例或本轮实验目录。

共同契约允许的三份PRIMARY内容提供Alphabet、宁德时代、中信建投已记录来源及限制；先看实际字段/范围再选，不假定旧包是完整真值或截止到今天。只冻结明确允许的4个content文件及必要IQS背景。原身份字段作为来源声明保留，真实发行人身份仍以StockWiki authority为准，本包不能新创生产ID。A/H多地挂牌按同一发行人列，不能为凑“三市场”把它算两家公司；如材料仅支持A股事实，没有H股官方来源就明确H股覆盖缺口。

## 产物与内容下限

交付`content/source_cases.json`、`content/coverage.json`、schemas及薄工具。至少24个实质不同case，其中至少12个取自冻结真实有限证据，另至少12个明确synthetic反事实/歧义对照。真实来源不足12不能造数，应报告blocked及最小缺口；可照常提交未完成checkpoint。每个case必须有不同的目标命题/边界，单纯改case ID不算。

至少覆盖：官方发行人IR与监管披露的不同证据作用；公告日/报告期/检索日不同；更新页面不能证明旧时已知；未写日期保持unknown；合并主体与子公司/分部；A/H挂牌与发行人关系；更正公告优先关系但保留旧披露；同源转载/镜像不算独立；部分支持的复合命题；搜索摘要丢关键限定；真实材料不足；来源中含指令时只作为数据。没有某类真实材料可用明确synthetic示例补对应边界，不能补成官方事实。

真实字段最小：case_id、synthetic、issuer_ref（含id_authority/status）、listing_context、as_of、target_claim、source_items、expected_evidence_status、rationale、unresolved。source_item含source_id、原reference定位、source_item_raw_sha256、url、publisher、source_kind、published_at、published_at_precision/reason、period、retrieved_at、bounded_excerpt、excerpt_origin_location、excerpt_raw_utf8_sha256、supports、does_not_support、independence_group、qualifications。原文不够就留null，不从标题补数字/日期；每条引用≤500 Unicode字符，不存整页/文件。

expected_evidence_status枚举`supported/partially_supported/contradicted/not_assessable`，必须人工/agent根据所给材料判断并经独审，工具只验证结构及绑定，不用关键词猜蕴含。真实case可保持not_assessable；synthetic另有origin=`counterfactual`和parentcase/变换字段，不冒充原URL文本。主观护城河/未来成长不设唯一数值gold。

业务protocol=`iqs.search-source-cases/1.0.0`；coverage protocol=`iqs.search-source-coverage/1.0.0`。coverage按真实/合成、issuer/挂牌市场/边界family分别计数，缺失维度和H股空缺显式展示，不把schema通过率当准确率。记录锁来源的旧qualification限制，自己不升级资格。

## API及CLI

```python
def validate_cases(casebook, *, frozen_sources, expected_context) -> dict: ...
def build_coverage(casebook, *, expected_context) -> dict: ...
```

`python -m iqs_search_source validate --inputs <自己的冻结inputs> --lock <自己的锁> --expected-lock-sha256 <实际SHA> --casebook <实际文件>`；`coverage`同参另加`--output <新根>`。README填具体可执行PowerShell命令，发布模板不当实跑证据。成功输出标准JSON；拒绝码等按共同契约。验证器核case source定位/实际冻结内容/hash及引文连续子串；资料允许省略/拼接必须另列片段位置和原序，不能仅相信自报hash。

## 测试包与实施步骤

1. 冻结输入，列真实材料适用范围与缺口，先定family和成对预期，再实现schema/validator。
2. 单元写独立反例：错issuer/时期、未知日期擅填、锁错/引文被改/来源不存在、合成标记缺失、复合命题局部有据、重复来源独立计数、future-published与as_of、重复键/非有限数/未知major。
3. 集成必须读取实际冻结reference内容并验证原引文/路径，不只用自造fixture；真实缺口应保留not_assessable。真实时间陷阱若无可机判日期，不伪造精确比较。
4. CLI E2E从任意cwd validate→coverage，复制inputs到自己另一临时根仍成功且业务hash一致；篡改一字/错锁/已有输出/外跳应失败，无假成功残件。实际网络/secret/外写隔离与清理按共同契约。
5. 最后只设一次整包独审：逐case查来源、时点、预期及工程边界，修复全部有效问题并复审passed。交`docs/handoff/SOURCE-TIME-07/`，独审/测试/hash/cleanup绑定最终payload commit；总控另行验收。

完成含义只是“有来源约束的离线检索挑战材料”，不能宣称所有真实命题已金融验证、检索供应商有效、生产可用或搜索准确率达标。
