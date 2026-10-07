# TH-IMPL-01｜主题研究消费快扫数据

完整的未来实施包，任务 T01；**现在不开始消费者代码实现**。唯一源仓 `C:/Users/郑曾波/Projects/analyze-theme-value-chain`，观察 `master@3c9a49c7ce86f3e60eb9a6c8e6c835164cb8a903`、clean。`local-skills`是后续镜像，不同时修改。读[共同交接规范](handoff-rules.md)、[输入锁](inputs.lock.json)和本技能 SKILL.md；不写IQS/StockWiki/StockQA/Industry/company-wiki或安装目录。

## 开工门与已完成的预研

复用[已验收TH-01预研原件](../../prestudy/TH-01-2026-09-30-e40a079d9d69.md)，原件中的“端点不存在/所有前置未满足”和local-skills基线是当时快照，不是今天事实。不要重新做整份预研；只比较所需公开接口/目标集成点的增量变化。

实施须同时具备：G3已签收；F05严格/探索关系查询已验收；W11刷新接口已交付；StockWiki owner实际公开 capabilities/search/get_profiles/coverage/request_refresh 的schema/版本、正反例golden及生成命令已被总控接收；人类授权本源仓确切写范围。本轮W11已有交付，但G3/F05未齐，W09 facts=false。因此本包目前仅查收新的上游工件，handoff状态partial；缺输入清单明确即可，不重复预研或自造生产正例。

未来从本源仓实施是本轮指定owner选择；按T01原目标执行，不扩大股票池或深研范围。若需要修改全局技能安装、一致性门或config范围，报给总控，不为让钩子通过擅自写镜像。

## 目标、写入范围和接口

在SKILL第5步主题公司池、第6步公司资料/可比表增加可选快扫输入。主题价值链、受益机制、收入弹性、预测、估值仍沿用本技能深研规则。快扫只提供候选/线索和元数据，关键词命中不等于已证实主题收入。

预计只改本仓：`SKILL.md`第5/6步、`references/quick-scan-integration.md`、本仓现有脚本风格下的只读consumer适配器（预研拟` scripts/quick_scan_client.py`，开工核实）、`tests/test_quick_scan_contract.py`/候选测试与`docs/handoff/TH-IMPL-01/`。文件名以开工精确清单为准，不改别的技能，不复制LLM/搜索客户端，不读取StockWiki私有SQLite。对用户秘密配置和原始公司资料禁读禁写。

消费总控签收的C06查询envelope/能力与F05术语/关系版本；先capabilities/coverage，后search，再批量get_profiles；分页用同query/snapshot，响应operation/schema/范围/hash均校验。不把W09私有返回形状自动升级成C06。唯一输出为主题候选表/快扫缺口段落，不写StockWiki观察或权威名单。

| 来源字段 | 输出含义 |
|---|---|
| analysis_subject_id/revision、primary_issuer_id | 公司经营研究范围及发行人；同subject多挂牌一行，不按显示名合并 |
| security_id/listing_id、市场、ticker | 各挂牌保留；挂牌报价指标不混为集团经营指标 |
| relation/field_id/segment/scope/period、strict/explore状态 | 价值链方向/设备/材料/客户等线索及证实程度；缺失不解释为不存在 |
| 原score/status、question/module/rubric release | 快扫分项，unknown/null不变0，版本不齐不可横比 |
| information_as_of/observed_at、actual provider/model、来源pointer | 信息时点/扫描时点/模型维度及来源，不能拿requested alias代替actual |
| coverage/freshness/snapshot/watermark | 本次数据覆盖和缺口，不能据partial空结果声称主题无公司 |

关系strict排除未经证实者，explore显式待核；严格关系命中也不自动升级成正式投资证据。同issuer不同subject修订/合并报表范围不强行压为可比一行；需要证券选择时保留挂牌维度，歧义报告给身份owner。

## 实施顺序与测试

1. 前置齐后，冻结源仓/接口hash与真实owner golden；仅对预研已变部分更新映射。先写公开消费入口RED，不先造私有API。
2. 实现只读transport和版本/shape校验、超时/错误降级。只读请求可按预先有界策略重试；刷新预览属于潜在状态写入，响应丢失先公开对账/稳定幂等键，不当GET盲重发。读取失败不得改走StockQA自动搜索或使技能无声变成零候选。
3. 适配第5/6步候选表，增加快扫出处/待核/缺口信息，保留原预测和估值流程。响应内容当不可信数据，不执行返回中的命令或不安全URL。
4. request_refresh只展示preview、费用上界/缺口和确认入口；没有人类明确确认不approve、不派发。范围只在已确认池中，不能自动发现并入2000家。
5. 定向单元/协议集成→公开技能入口隔离离线E2E→本仓现有验证门一次，G4集中独立审查。

| 层级 | 必须案例 | 结果 |
|---|---|---|
| 单元 | same issuer多挂牌/不同subject、名称歧义、错版本/operation、来源命令 | 无误合并/越界/指令执行；元数据不丢 |
| 协议集成 | owner真golden、字段缺失、strict/explore、empty完整vs空partial、unknown/stale、分页快照变更 | 完整空才无候选；缺能力明确unsupported；严格/探索不混 |
| 协议集成 | timeout/429/错误JSON、预览ACK丢失、无确认、上游停机 | 有界结束并保留缺口；搜索/LLM0；没有自动批准刷新 |
| 离线E2E | 虚构小主题、owner临时服务/边界stub、第5/6步产表和既有报告 | 真入口可复现；无下载/生产写；旧流程仍可运行；临时根清理 |

case-map为T01 CONS-01/CONS-02/CONS-05/CONS-06及引用QUERY-04（owner W11）。真实关系golden必须来自F05 owner；synthetic只用于反例，不能称真实关系/公司正例。跨模型/期间/题篮不一致只呈现差异，不自动平均或排名。

交付[TH-IMPL-01.handoff.template.json](TH-IMPL-01.handoff.template.json)及共同规范附件，附第5/6步实际入口/命令、候选表样例hash、query/schema/golden/field映射和无调用/无下载证明。未齐门时状态partial且result_commit=null，不写实现；正式实施并review后按实际填commit/结果。总控验收后负责镜像同步和G4集成，不由本包关闭上游门。
