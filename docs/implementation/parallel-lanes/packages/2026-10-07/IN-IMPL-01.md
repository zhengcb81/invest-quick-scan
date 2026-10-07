# IN-IMPL-01｜行业研究消费快扫数据

完整的未来实施包，任务T02；**现在不开始消费者代码实现**。唯一源仓 `C:/Users/郑曾波/Projects/industry-research`，观察 `main@4a80f9988f9325fb0a348c8acd9e41d615005c5f`、clean。只写本仓已授权范围，不写Theme/StockQA/StockWiki/IQS/company-wiki、local-skills或安装镜像。先读[共同交接规范](handoff-rules.md)、[输入锁](inputs.lock.json)与本技能SKILL。

## 开工门与上下文

复用[已验收IN-02预研原件](../../prestudy/IN-02-2026-09-30-023f9a7960c8.md)，不要重做预研。原件中的local-skills owner和“query全部不存在”是历史观察；本轮明确以独立Industry源仓实施。只检查集成点/接口的增量变化。

硬前置为G3、F05、W11、总控已接收的StockWiki实际公共query能力/schema/golden和人类对本仓精确写授权。W11已有交付，G3/F05未齐、W09 facts=false；当前仅接收上游新交付/列缺项，handoff partial，不写消费者实现、不用synthetic补生产正例。不得因股票池名单已获准而认为全池扫描或消费端改动也获准。

## 目标、范围与接口

第6步行业公司评估增加“快扫候选/画像”可选来源，并让第7步报告保留出处和缺口。原行业框架1–10评分、行业证据、收入/估值不与IQS分数混合。快扫数据不依赖companies目录，也不要求读取/下载年报；原技能深研PDF路径属于既有功能，本包不把它变成快扫前置。

拟写范围：本仓 `SKILL.md`、`modules/company-evaluation.md`、必要`modules/report-generation.md`中出处/缺口显示、本仓脚本风格下只读适配器（预研拟`tools/quick_scan_client.py`，开工核实）、本包`tests/`、`docs/handoff/IN-IMPL-01/`。`config.yaml`、安装同步、原资料下载器、其他模块不在默认范围；必要扩展先由人类明确授权。不要顺便统一历史`company_list.json/companies.json`命名，除非本包反例证明接线必需且原格式兼容保留。

消费总控冻结的StockWiki C06公开query信封和F05关系/术语版本，不读SQLite、私有目录或`companies/`清单冒充权威池。能力/覆盖→条件search→分页快照→批量get_profiles，响应shape/operation/版本、字段/范围元数据都校验。只输出公司发现/评估表和缺口，绝不向StockWiki写观察、改身份或成员。

| 公开输入 | 行业报告映射 |
|---|---|
| analysis_subject_id/revision、primary_issuer_id | 经营分析范围/发行人主键；同scope多挂牌一行，范围变更不可假横比 |
| security/listing/market/ticker | 挂牌信息保留，证券报价按各挂牌而非混成公司指标 |
| industry/segment/field_id、关系方向/时期/证实状态 | 细分行业、上下游/设备/材料/客户线索；不按短词匹配直接断言受益 |
| score/status、question/module/rubric版本 | 快扫初筛分项及状态，独立于行业框架量表；unknown不是0 |
| information_as_of/observed_at、actual model/provider、来源pointer | 三维追溯：公司×时间×模型；标快扫线索而非正式accepted证据 |
| coverage/freshness/snapshot/watermark | 当前缺口、过期和查询范围；未覆盖不能写“没有该业务/供应商” |

strict/explore必须保持证实级别；行业关键词/短词/别名只按已版本化规则匹配，不在消费端另建词表。当前模型或题篮不同的分数不平均、不重新计算排名；只按已对齐的同口径分项展示。

## 实施与测试批次

1. 开工门齐后，按源仓真实第6/7步入口冻结接口/golden/hash和精确拟写清单。RED先覆盖已有流程与可选来源，不通过重写整个技能达成接线。
2. 做只读请求/响应适配、能力降级和有界超时/重试。刷新预览是有状态请求，丢响应先对账/幂等处理，不按普通GET盲重发。失败/不支持显式回到既有研究路径，不当无候选，也不自动用LLM联网补库。
3. 在第6步增加快扫来源，保留原来源选择与第7步模板，新增初筛/待核/缺口列。名称歧义不自动合并，单公司多挂牌与不同subject分开处理；来源文本/URL安全显示。
4. 只展示request_refresh preview，范围/费用/需要确认可见；无人类确认不approve，不扩股票池/派发/下载。
5. 单元→真实owner golden协议集成→公开技能入口隔离离线E2E→本仓现有静态/提交门一次。G4集中review，不逐个helper审查。

| 层级 | 案例 | 必须结果 |
|---|---|---|
| 单元 | 中微风格易混名、same issuer两挂牌、不同subject、短词误命中、模型/期间不同 | 稳定ID，范围/证实层级明确，无伪排名/合分 |
| 集成 | owner真golden、旧版本/unsupported、empty全覆盖vspartial空、unknown/stale、分页query变化 | coverage不丢、不把缺口当不存在；错快照停止续页 |
| 集成 | timeout/限流/错误JSON、预览重复/响应丢失、无确认、源服务离线 | 有界结束，保留原研究流程；搜索/LLM/自动批准0 |
| 离线E2E | 虚构行业少量公司、第6步来源选择→第7步报告，无companies目录 | 真公开入口和报告列可复现；不下载、不触生产数据；临时根已清理 |

case-map为T02 CONS-03/CONS-04/CONS-07，并引用QUERY-04（W11）、SC-11（C02）原owner语义，不自行关闭它们。现有仓无pytest基建时采用标准库unittest或现有风格，不为了本包引入大测试栈；`tools/pre_push_gate.py`/现有质量门的参数先用真实help/源码核实，不能猜命令或替门降阈值。

安装一致性若要求写仓外，交总控处理并如实报告partial；worker不运行`sync_installations.py --apply`。交付[IN-IMPL-01.handoff.template.json](IN-IMPL-01.handoff.template.json)和共同规范附件：实际入口/复现命令、报告样例hash、字段映射/query版本与golden、旧流程兼容、无调用/无下载和清理证据。前置未齐无实现commit；正式实施后按实际填commit/review。总控做G4联调与镜像同步，本包不宣布全系统上线。
