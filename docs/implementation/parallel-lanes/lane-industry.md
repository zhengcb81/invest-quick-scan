# Industry Research消费者线

**Owner:** `industry-research`。

**项目子目录:** `local-skills/industry-research/`；与Theme共用`local-skills/` Git根但拥有互不相交的技能子树。使用独立分支/工作树，仅改本技能子树。

**授权:** 目前只读；用户单独授权写入前，不改SKILL.md、modules、tests或其他文件。

## 独立上下文与唯一任务

负责`tasks.json`中的T02：将行业研究第6步接入统一公司查询。Industry技能继续负责行业框架、行业内比较与研究报告；Quick Scan仅供候选/信息字段/评分时间轴检索，不能冒充行业事实验证、深度公司研究或投资建议。

执行依赖G3、F05、W11。起步时先读本技能现有`SKILL.md`与`modules/company-evaluation.md`，以及IQS query/ScanRecipe和StockWiki能力契约；当前能力或facts版本不足时明确unsupported/partial。

## 接口与禁止项

仅使用StockWiki公开read-only query/coverage/capability接口；字段选择使用stable `field_id`、`module_id`与release/version，不按中文显示标签拼接SQL或关键词猜列名。Industry可以在自己的研究artifact中引用公司profile的source/observed_at/model metadata，不拥有其写入权。

不读/写StockWiki私有SQLite，不复用或复制StockQA LLM/Search执行器，不保存公司文档正文，不改Theme技能，也不自行创建2000家公司池。接口缺失时向总控提交协议变更建议并停止接线。

## TDD测试与大节点审查

RED/GREEN覆盖有效profile、query无结果、身份歧义、能力版本不匹配、field freshness未知/过期、分页、来源元数据透传与旧StockWiki能力降级；离线集成测试使用明确版本的协议fixture，不请求网络/API。E2E从`industry-research`公开入口开始，验证查询工具选择与一小组虚构公司结果被标注为初筛资料，不触发公司深度研究。

使用技能仓自身测试入口，不假设与Theme共用依赖/pytest配置。T02参加G4/G6大节点审查；review者冻结本技能差异并read-only检查，无逐小任务独立review。

## handoff

返回实际读取的contract version/hash、具体接入步骤、changed path、测试fixture和命令结果、过期/unsupported表现、T02剩余消费者契约。用户明确授权前保持只读；交付由总控串行整合到共享`local-skills` Git根。
