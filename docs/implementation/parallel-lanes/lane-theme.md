# Theme研究消费者线

**Owner:** `analyze-theme-value-chain`。

**项目子目录:** `local-skills/analyze-theme-value-chain/`；Git根与Industry lane共用`local-skills/`，但本线只能写自己的技能子树。需用独立分支/工作树。

**授权:** 目前只读；用户单独授权写入前，不改SKILL.md、references或测试。

## 独立上下文与唯一任务

负责`tasks.json`中的T01：接入主题研究第5/6步的快扫公司查询。主题研究仍负责价值链拆解、主题关联、收入弹性和估值；Quick Scan提供初筛/字段和有时间戳的结构化证据，不替代深度研究、revenue-forecast或公司估值。

执行前依赖G3、F05、W11。前置未过时可以只完成read-only接口调查/测试设计，不改UI或猜测字段。StockWiki能力标记为未提供/版本不匹配时显式降级，不直连私有数据库。

## 接口与禁止项

只使用StockWiki公开版本化search/get_profiles/coverage等查询能力和IQS已发布的ScanRecipe/fact ontology；查询输入输出保留subject/security范围、as-of时间、field IDs、release/version及freshness。结果作为证据入口和候选公司，不把关键词命中当作主题因果或投资结论。

不实现另一个LLM client/搜索client，不写StockWiki存储，不写本地完整公司数据副本，不保存财报或搜索正文，不修改Industry技能文件。接口缺字段时向总控提IQS/StockWiki契约变更，不私自加参数。

## TDD测试与大节点审查

先为查询成功、空候选、unsupported capability、过期数据、身份歧义、分页与部分结果写RED；consumer contract fixture应明确版本与时间。mock StockWiki公开接口并留一个跨接口fixture测试验证请求shape、分页/错误语义及返回不被当成结论。技能端到端测试使用小型合成主题和临时输出，不触发live模型或联网搜索。

受影响pytest/unittest命令必须从本技能仓实际配置发现；报告范围只含自己的技能目录。T01作为G4大节点一部分做一次独立read-only审查，不逐个小函数审查。

## handoff

提交前置版本、读接口版本、写入路径、测试fixture hash与命令/结果、降级行为、未解决契约差异。任何写入必须先取得用户对该技能目录的精确授权；完成包由总控串行合并到共享`local-skills`根。
