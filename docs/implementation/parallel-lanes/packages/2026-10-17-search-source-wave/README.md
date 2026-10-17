## 2026-10-17总控修复检查点

五包修复/源码正常提交已完成，最终整包独审因平台usage limit中断，不能读下方旧接收/编卡文字当最终passed。最新commit、测试时序及剩余具体动作见总控`docs/implementation/reviews/remaining-packages-2026-10-17/controller-status.json`及`docs/implementation/experiments/remaining-packages-acceptance-2026-10-17.md`。原CONTEXT已签不重复实现；本轮0收费API/0生产写，不给金融gold。

## 2026-10-17交付接收状态

用户已确认全部外包完成，三个约定Lab正式handoff目录均已见。当前由总控冻结并隔离验收，尚不等于签收；不再将本页编卡时“不存在”误作当前目录状态。QUERY验收已启动；实际payload/独审/测试/hash以各包冻结回执为准，不追活动latest。所有源仓仍只读，未自动导入生产。下方为原施工规格。

# 搜索准确性独立施工波次：三个可以并行的大包

编卡日2026-10-17。这里只交施工说明，不创建Lab、不派发、不调用API。编卡时以下三个工作根均不存在；收到卡片的harness必须开工再核，遇陌生文件/活动writer停止，不接管或清理。三个包可以同时开工，不依赖本轮DeepSeek/Brave/Tavily/ZAI真实对比结果，也不依赖另两个包。

| 卡片 | 唯一可写工作根 | 总控只读接收接口 |
|---|---|---|
| [SOURCE-TIME-07](SOURCE-TIME-07.md) | `C:/Users/郑曾波/Projects/iqs-search-source-lab` | `source_cases.json`、`coverage.json`、`validate` CLI及完整正式交接 |
| [QUERY-ENTITY-07](QUERY-ENTITY-07.md) | `C:/Users/郑曾波/Projects/iqs-query-identity-lab` | `query_catalog.json`、`query-plan.json`、`plan/validate` CLI及完整正式交接 |
| [RETRIEVAL-AUDIT-07](RETRIEVAL-AUDIT-07.md) | `C:/Users/郑曾波/Projects/iqs-search-annotation-lab` | 检索标注rubric、匿名assignment、独立标注报告及`assign/compare` CLI |

三根互不相交，不写StockQA、StockWiki、IQS及任何旧Lab。**StockQA接入实现和本轮真实收费实验由总控负责**；本波次只是离线资料与可组合薄工具，不复制搜索客户端、故障路由、账本、金融scorer或生产身份库。REVIEW-CAL-06仍由其原writer负责；本波次第三包只评价“检索证据本身”的质量，不评价LLM答案、1–10分合理性或金融整体充分性。

每个harness独立阅读本卡、[共同施工与交接契约](integration-contract.md)、[独立整包审查要求](independent-review.md)。本目录没有预先冻结的输入authority，不得借用06的输入锁冒充本波次。各自在自己的Lab只读冻结明列的已有输入、建立自己的raw-byte锁，版本从1.0.0开始。输入缺失/变动不拼接追latest；留gap或在实际必需依赖缺失时blocked。

## 总控导入规则

1. 收到正式交接后，总控冻结payload、输入锁和审查证据，在自己的隔离目录验证raw hash和公开CLI；不会把`ready_for_acceptance`当正式签收。
2. 总控以显式adapter读取各自versioned JSON：SOURCE提供证据陷阱与支持范围；QUERY提供候选检索意图；AUDIT提供独立检索评审字段。任何一包都不能写另两包结果或要求它们先交付。
3. 实际证据跨包复用须总控另立明确输入锁；不同company/as_of/reference scope不能仅按名称合并。QUERY候选不能自动改用户模型/搜索顺位；SOURCE案例预期不能当新实时事实；AUDIT人工判断不能自动变生产分数。
4. 不导入private匿名映射/答案期望到模型检索context；总控只在盲审结束后连接。旧协议固定测试保留；新增major由显式adapter启用，不覆盖旧实验。

## 施工完成的统一标准

三包都只设一个整包独审节点：实际调用不同agent全面审查，修复所有有效问题并复审`passed/open_findings=[]`后才正式交接。无独审能力、上游必要前置缺失或有效发现未关，均不能报完成。每卡自己的单元、集成和公开CLI E2E、干净隔离与清理证据是整包输入，不增加helper审查门。编卡发布审查不代替实施后独审。
