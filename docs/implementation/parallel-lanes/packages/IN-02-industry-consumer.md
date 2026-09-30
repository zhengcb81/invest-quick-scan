# IN-02｜行业研究第 6 步读取快扫公司画像

**可单独交给 Industry harness 的施工指令，当前仅可只读预研。** Owner 子树 `C:/Users/郑曾波/Projects/local-skills/industry-research/`；任务 T02，验收 CONS-03、CONS-04、QUERY-04、SC-11、CONS-07。G3、F05、W11 和 StockWiki 公开 query endpoint/golden 为硬前置；用户当前未授权本子树写入。`local-skills` Git 根也包含 Theme，两个 harness 必须在独立工作树/分支写各自子树，最终由总控串行整合。

## 现在立即执行：只读预研（本卡可独立使用）

**只读范围**：本技能子树、IQS 契约/计划、StockWiki 公开接口和测试/文档；不改任何项目文件、不创建技能代码或测试文件、不访问 StockWiki 私有 SQLite、不发 LLM/API 请求、不下载公司资料。检查产生临时文件时使用独立临时根并清理。T02 实施验收仍等待 G3/F05/W11、真实 query/golden 和用户对 Industry 子树的写授权；找不到端点可以完成缺口勘察，但不能宣称接线通过。

请依次调查，并在报告中给每条事实标注具体文件/公开方法与观察到的版本/hash：

1. 冻结 `local-skills`、StockWiki、IQS 三仓 HEAD、工作树摘要和所读关键文件 SHA-256；读当前 `AGENTS.md`（如有）。
2. 从 `SKILL.md` 第 6/7 步、`modules/company-evaluation.md`、`modules/report-generation.md`、`config.yaml` 画出“研报/wiki/companies 发现→公司评估→报告”真实路径，找一个最小快扫候选入口，并说明原深研/PDF路径怎样保留。不能把 `companies/` 目录是否存在当股票池权威准入。
3. 核对 IQS [查询契约](../../contracts/exchange-and-query.md)、[字段/时效契约](../../contracts/freshness-and-jobs.md)、`tasks.json` 的 T02，以及 StockWiki 当前**实际已实现**的 `capabilities/search/get_profiles/request_refresh` 公开入口、协议版本、owner response golden、错误码/coverage/watermark。合同文本不等于生产接口；缺失时写 `not_available` 和查过的位置，不用私有 SQLite 或合成响应冒充 owner golden。
4. 列公开字段到公司评估表的映射：`analysis_subject_id`/revision、primary issuer、security/listing、行业/细分、设备/材料/客户/下游、score/status、field/module release、`information_cutoff`/`observed_at`、真实 provider/model、source pointer、coverage/freshness。明确哪些只作快扫线索，哪些需原行业研究证据独立验证；缺字段指明 IQS 或 StockWiki owner。
5. 设计而不执行实施测试：完整/部分覆盖与空结果、歧义名称、同 issuer 多挂牌、短词误命中、未证实关系、过期/unknown、旧版 unsupported、分页快照、刷新预览零派发及原第 6/7 步不回退。列未来本子树拟写精确文件/目的，本次不实施。

**交接接口**：最终消息同时给出一份完整 UTF-8 Markdown 报告和一份完整 JSON。Markdown 按[统一模板](../prestudy/template.md)的“冻结输入、当前路径、字段映射、公开接口缺口、测试设计、拟写文件/授权、实际只读检查与下一步”分节。JSON 严格符合[handoff schema](../handoff.schema.json)：`schema_version=1.0.0`、`lane_id=industry`、`package_id=IN-02`、`status=partial`（预研查清但 T02 未实施）或 `blocked`（连必要输入也无法读取）；填写 `snapshot`、`scope`、`interfaces`、`verification`、`review`、`open_items`，其中 `authorization_scope_ref=not_authorized`、`changed_paths=[]`、`external_writes=false`、`network_calls=false`、`paid_calls=false`。嵌套字段按 schema；不只给 hash/摘要，未执行的测试写 `not_run`。

**留档接口**：harness 不写 IQS 中央仓。总控核对事实和 JSON 后，把 UTF-8/LF 报告按完整字节 SHA-256 前 12 位存为 `docs/implementation/parallel-lanes/prestudy/IN-02-<YYYY-MM-DD>-<sha12>.md`，完整 JSON 存同前缀 `.handoff.json`，将两份完整 hash、三仓输入 commit、观察/接收时间和依赖缺口加入[归档索引](../prestudy/archive-index.json)并按[索引 schema](../prestudy/archive-index.schema.json)校验，随后更新 `progress.md`/`findings.md`。预研报告不可变；新结果新增文件。`prestudy_complete` 只表示勘察完成，T02 实施仍是 `not_started`。共同规则见[只读预研规程](../prestudy/README.md)，本卡自身已经列明执行与交接字段。

## 现有流程与目标

行业技能 `SKILL.md` 第 6 步“评估行业公司”，`modules/company-evaluation.md` 目前从研报、行业 wiki、`companies/` 目录找公司，并有本地公司文档/年报读取路径。T02 只给这一步增加**可选的快扫候选/画像来源**，不删除或篡改既有深度行业研究路径；快扫自身不依赖下载文件，读取 StockWiki 的轻量结构化数据。不能为快扫去批量下载财报，不能把本地目录是否存在当成某上市公司是否在股票池的权威判据，也不能自选 2000 家名单。

先读本技能 `SKILL.md`、`modules/company-evaluation.md`、其现有测试/脚本入口，IQS [查询契约](../../contracts/exchange-and-query.md)、[事实字段/时效契约](../../contracts/freshness-and-jobs.md)、[Industry lane](../lane-industry.md) 和 `tasks.json` T02。真正接线还需 StockWiki owner 的公开 capabilities/search/get_profiles 文档、实际 response golden、版本/覆盖/水位语义。IQS 本地协议定义不代表生产端点已经上线。消费者不读 StockWiki 私有 SQLite，不修改其表，不复制 StockQA 客户端。

## 输入与标准输出

输入包括行业/细分行业、市场与 as-of、稳定 field IDs、必要的 Score/Fact 模块 release。先能力协商，再按行业/关系条件查询候选，批量取得 profile 与历史引用。公司主键使用 `analysis_subject_id + revision`，保留法律 issuer 与多个 listing 的区分；同 issuer 多挂牌在公司比较表仅一行，证券/市场指标仍带 listing 口径。每行明确标记数据来源为 quick scan、信息截止日/观察时间、模型/provider、题库/字段版本、证据级别、coverage/freshness 和未知状态。未知分数/null 不是 0；无供应商/客户条目且覆盖未完成，不得解释为“没有供应商/客户”。

输出是行业公司发现表、需补证的细分链条/设备/材料/客户线索，以及快扫评分时间轴入口。快扫不替代行业框架问题评分、正式证据采集、营收预测或估值。旧版能力不支持关系或事实版本时显式 `unsupported/partial`，保留原有行业研究流程，不静默把缺口当成筛选失败。刷新必须先预览并经用户确认；读取报告时绝不自动派发 LLM。

## TDD 工作包（依赖满足后）

1. 记录技能仓 HEAD/status 和现有第 6 步真实公开入口，冻结 IQS/StockWiki 版本与 golden。给用户报备拟写本子树的精确路径和目的，取得写授权。预期仅 `SKILL.md`、`modules/company-evaluation.md`、本技能专属测试/适配器；路径须预检，绝不改 Theme、StockWiki、IQS 或 StockQA。
2. 先写 RED：正常行业多公司、同 issuer 多市场去重、短词误命中、行业归类/关系未证实、`empty`+完整覆盖、partial/not_covered、身份歧义、过期/未知评分、字段 release 不兼容、分页快照一致性、分析范围变更、来源/模型元数据保留。用公开边界 mock 做单元测试，再用 owner golden 做协议集成反例；不自制所谓真实生产返回。
3. 最小适配第 6 步：按 stable ID 而非中文显示名或私有 SQL 取字段；把结果标成“快扫初筛”，保留第 7 步报告既有证据等级和定量逻辑。对 `request_refresh` 只展示 preview/缺口；没有明确授权不得触发派发。
4. 离线 E2E 从行业技能公开入口用虚构行业/少量虚构公司运行，确认原研究流程仍能使用、快扫可用时引入候选、不可用时明确降级；所有临时缓存/输出在唯一根下，结束 assert 清理。网络/API/PDF 下载默认关闭。跑本技能现有定向测试和输出校验；G4/G6 做一次阶段审查。

## 当前可交付的只读准备与完成标准

前置未齐时交付上述只读预研报告；完整勘察即使发现生产端点尚无，也可把报告标为 `prestudy_complete`，handoff 的 T02 状态仍为 `partial`。只有必要输入无法读取才标预研 `blocked`。**不提交实现，不声称 T02 验收**。正式完成需五个 case 的 owner 实测、真实契约 fixture/版本、unknown 与 coverage 正确呈现、可重跑离线 E2E 和清理记录。

按 [handoff schema](../handoff.schema.json) 返回 `package_id=IN-02`、base/result commit、子树内变更路径/hash、消费的版本/golden hash、测试命令与结果、未触发的网络/费用、review/open items。总控核对后串行整合到共享 `local-skills` Git 根。
