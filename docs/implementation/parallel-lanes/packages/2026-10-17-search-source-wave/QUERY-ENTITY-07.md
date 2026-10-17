# QUERY-ENTITY-07：检索意图、同义词和发行人防混淆候选规划器

唯一可写根`C:/Users/郑曾波/Projects/iqs-query-identity-lab`，包`iqs_query_entity`。先读共同契约/独审规范，编卡时新根不存在，开工再核。全离线，不依赖SOURCE/AUDIT或本轮真实实验；不写StockWiki/StockQA/IQS/旧Lab。

## 边界

产物是**候选查询计划**，由总控未来显式adapter采用；不是新身份解析器、生产证券主表或搜索派发器。不通过ticker字符串/公司相似名称自动合并，不调用搜索/LLM，不读API key，不改用户搜索顺位/预算/模型优先级，不给查询质量承诺。REVIEW-CAL-06与本包无共享写区。

背景输入仅共同契约中IQS明确文件；有需要可冻结三个PRIMARY Lab的reference-pack.json获取已记录名称/来源锚点，但不执行其代码，不把其声明当StockWiki真实identity DTO。没有生产身份DTO就使用自己明标synthetic的可测试输入契约；不能伪造StockWiki正例。示例中微公司/中微半导体的名称只说明存在混淆风险，真实代码、法人或别名关系没有冻结依据必须unknown。

## 内容和选择规则

至少36个实质不同query intent模板，覆盖收入/现金流口径、经营指标、竞争优势的可证行为、经营低谷与修复线索、客户/供应商/设备/材料、产业变革机会/替代风险；至少12个身份边界输入，涵盖A/H同发行人多挂牌、同名不同公司、中文简称近似、英文别名、ADR与普通股但映射未证实、历史更名/退市/挂牌有效期、分部与子公司、字母ticker跨交易所复用、用户只给模糊名称。模板是检索表达，不增删IQS题目、题号或评分规则。

identity输入protocol=`iqs.query-identity-input/1.0.0`：issuer_ref/id_authority/status、canonical_names、aliases（language/source_ref/valid_from/valid_to/status）、listings（market/exchange/ticker/security_type/issuer_relation/valid_from/valid_to）、as_of、questions（原question_id/text）、search_intents、explicit_query_order。身份status仅`verified/ambiguous/unresolved/synthetic`，verified须有明确authority来源声明；工具只能验证所给依据和时点，不能认证真实世界。status不确定应输出needs_resolution，不生成假精确目标查询。A/H数据只在显式issuer_relation已证实时共享发行人事实，证券价格/挂牌事项保留listing scope。

query_catalog protocol=`iqs.query-intent-catalog/1.0.0`：稳定intent_id/version、适用题型、查询槽位、language、必要实体约束、可选域名建议、时间语义、别名风险、检索目的/不能推出的结论。query-plan protocol=`iqs.query-plan/1.0.0`：原输入绑定hash、status、ordered_queries（query_id/intent_id/question_ids/query_text/issuer_ref/listing_scope/as_of/why/limits）、unresolved、dedup_groups、qualifications。

显式计划按用户给定query order，否则按intent输入顺序，不据词频排序“最优”；去重保留原题关联和合并原因。没有截止日期过滤能力不宣称限制有效，query_text出现年份也不是网页时点证据。币种/规模单位同义词表不可将OCF=FCF、净利润=经营利润。原问题文本不可被工具改写回正式题库。域名只是查询建议，不硬编码“IR全可信”；未知字段不猜。

## API和CLI

```python
def validate_catalog(catalog, *, expected_context) -> dict: ...
def plan_queries(identity, questions, catalog, *, explicit_order=None,
                 expected_context) -> dict: ...
```

CLI `python -m iqs_query_entity validate --inputs ... --lock ... --expected-lock-sha256 ... --catalog ...`；`plan`增加`--identity ... --questions ... --catalog ... --output <新根>`。遇合法但ambiguous identity应exit0输出needs_resolution、queries=[]及原因，不与非法输入exit2混淆；未知major exit4。给最小合成fixture和已冻结真实名称资料（如实际存在）的保守fixture，二者分开，不宣称已对接StockWiki serializer。

## 测试与步骤

先锁输入→写身份/查询不变量及RED→实现薄纯函数与版本schema→完成目录与边界内容→一次整包独审。测试至少包括：

- verified issuer多挂牌保留安全scope；同ticker不同exchange不合并；模糊名称/ADR映射未知时needs_resolution；公司名内特殊符号不造成路径/命令注入。
- 更名/挂牌半开区间`[valid_from, valid_to)`，跨时点别名不强行启用；日期unknown明确风险；ticker不是issuer主键；多个authority冲突不静默覆盖。
- OCF/FCF、分部/合并体、归母/整体不同intent不错误去重；重复question_id、别名冲突、未知模板/版本、上下文hash错、非有限数/重复键拒绝。
- 单元预期独立编写；集成目录→planner→validator；公开CLI E2E validate→plan→再次validate plan（实现`--plan`分支），任意cwd/输入搬迁稳定、无secret/网络/外写、已有输出与外跳拒绝、清理仅自己临时根。

交接`docs/handoff/QUERY-ENTITY-07/`，真实不同agent独审逐模板/身份案例/代码/schema测试，全部有效发现修复复审passed并绑定最终payload/input lock。只能交候选，不发布生产身份gold或真实搜索覆盖率；正式启用由总控以后在StockQA另行接线。
