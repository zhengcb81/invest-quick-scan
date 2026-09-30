# TH-01｜主题价值链研究读取快扫候选

**可单独交给 Theme harness 的施工指令，当前仅可只读预研。** Owner 子树 `C:/Users/郑曾波/Projects/local-skills/analyze-theme-value-chain/`；任务 T01，验收 CONS-01、CONS-02、QUERY-04、CONS-05、CONS-06。G3、F05、W11 为硬前置；这三项及 StockWiki 公开 query endpoint/能力/golden 都通过之后，且用户授予 Theme 子树写入权限，才能进入代码施工。Theme 与 Industry 共用 `local-skills` Git 根：各用独立工作树/分支，绝不写对方子树，集成串行。当前总计划只授予本子树 read-only。

## 现在立即执行：只读预研（本卡可独立使用）

**只读范围**：本技能子树、IQS 契约/计划、StockWiki 公开接口和测试/文档；不改任何项目文件、不创建技能代码或测试文件、不访问 StockWiki 私有 SQLite、不发 LLM/API 请求、不下载公司资料。若检查命令产生临时文件，使用独立临时根并在结束时删除。预研不能因缺生产端点就伪造成功；可如实完成“查明缺口”的报告。T01 的实施验收仍等待 G3/F05/W11、StockWiki 真实 query/golden 和用户对 Theme 子树的写授权。

请依次完成以下调查，并在报告中给每条事实标注具体文件/公开方法与观察到的版本/hash：

1. 冻结 `local-skills`、StockWiki、IQS 三仓 HEAD、工作树摘要和所读关键文件 SHA-256；读当前 `AGENTS.md`（如有）。
2. 从 `SKILL.md` 第 5/6 步、`references/quality-gates.md`、`references/output-schema.md`、`references/company-model.md` 绘制“主题定义→价值链叶节点→公司发现→可比数据→报告”真实路径，指出**一个**最小快扫接入点与旧流程降级路径。
3. 核对 IQS [查询契约](../../contracts/exchange-and-query.md)、[字段/模块契约](../../contracts/question-modules.md)、`tasks.json` 的 T01，以及 StockWiki 当前**实际已实现**的 `capabilities/search/get_profiles/request_refresh` 公开入口、协议版本、owner response golden、错误码/coverage/watermark。合同文本不等于端点实现；找不到时写 `not_available`、查过的位置及对 G3/F05/W11 的依赖，不用私有表或自造 golden 补齐。
4. 列字段映射：`analysis_subject_id`/revision、issuer 与 listing、细分行业/上下游/设备/材料/客户、score/status、field/module release、`information_cutoff`/`observed_at`、真实 provider/model、source pointer、coverage/freshness 各从哪个**公开字段**到主题候选表哪一列。区分搜索线索与主题收入暴露的正式证据；缺字段指明 IQS 或 StockWiki owner。
5. 设计而不执行实施测试：完整/部分覆盖、空结果、身份歧义、同 issuer 多挂牌、过期/unknown、strict/explore 未证实关系、旧版 unsupported、分页快照、刷新预览零派发。列出未来本子树拟写的精确文件和目的，不在本次动手。

**交接接口**：最终消息同时给出一份完整 UTF-8 Markdown 报告和一份完整 JSON。Markdown 按[统一模板](../prestudy/template.md)的“冻结输入、当前路径、字段映射、公开接口缺口、测试设计、拟写文件/授权、实际只读检查与下一步”分节。JSON 必须符合[handoff schema](../handoff.schema.json)：`schema_version=1.0.0`、`lane_id=theme`、`package_id=TH-01`、`status=partial`（预研查清但 T01 未实施）或 `blocked`（连预研必要输入也无法读）；填写 `snapshot`、`scope`、`interfaces`、`verification`、`review`、`open_items`，其中 `authorization_scope_ref=not_authorized`、`changed_paths=[]`、`external_writes=false`、`network_calls=false`、`paid_calls=false`。嵌套字段严格按 schema，不只给 hash 或摘要；未运行的测试标 `not_run`，不能写成通过。

**留档接口**：harness 不写 IQS 中央仓。总控核对事实和 JSON 后，把 UTF-8/LF 报告按完整字节 SHA-256 前 12 位存为 `docs/implementation/parallel-lanes/prestudy/TH-01-<YYYY-MM-DD>-<sha12>.md`，完整 JSON 存同前缀 `.handoff.json`，将两份完整 hash、三仓输入 commit、观察/接收时间、依赖缺口加入[归档索引](../prestudy/archive-index.json)并按[索引 schema](../prestudy/archive-index.schema.json)校验，随后更新 `progress.md`/`findings.md`。预研报告是不可变快照；新结果新增文件。`prestudy_complete` 仅表示本次勘察完成，T01 实施仍是 `not_started`。更详细的共同规则见[只读预研规程](../prestudy/README.md)，但本卡已列出执行与交接所需字段。

## 业务边界与现有入口

现有 `SKILL.md` 第 5 步建立主题公司池，第 6 步收集可比公司数据。快扫可提供候选、细分产业链/上下游字段、版本化评分及观察时间/模型，但不能把一个关键词命中或模型自述提升为“主题收入受益”证据。主题技能仍负责价值链原子拆分、受益机制、收入弹性、场景预测和估值，原有深研证据规则继续有效。快扫项目轻资产：不下载/持久化公司财报、网页正文，也不创建第二个 2000 家股票池。

先读本技能 `SKILL.md` 的第 5/6 步和 `references/quality-gates.md`，再读 IQS [查询契约](../../contracts/exchange-and-query.md)、[题目/字段契约](../../contracts/question-modules.md)、[Theme lane](../lane-theme.md)、`tasks.json` T01。接线前从 StockWiki owner 取得**已实现**的公开 `capabilities` / `search` / `get_profiles` / `request_refresh` 方法、协议版本、真实响应 golden、覆盖/水位与错误码；当前 IQS 查询契约是本地定义，不等于生产端点已经存在。不得直连 StockWiki SQLite 或解析其私有目录。接口缺字段时提交契约变更建议给 IQS 总控，不在技能里造私有参数。

## 输入、输出与精确集成点

输入是主题定义、地理/市场/时间范围、价值链细分方向及已发布 field/module ID。第一步查询 capability/coverage，随后用严格关系/细分条件取候选，再批量取有版本的 profiles。每条候选必须带稳定 `analysis_subject_id` 和 revision、`primary_issuer_id`、匹配原因、字段/模块 release、观察/信息截止时间、真实 provider/model、source pointer、覆盖状态与查询 snapshot/watermark。`security_id`/`listing_id` 仅用于挂牌信息；跨市场同 issuer 不能重复当两家公司。查询 `empty` 只在完整覆盖时代表无候选；partial/not_covered/unknown 必须在报告里明确显示，不可当作零。

输出是候选清单/研究线索及缺口提示，不改写 StockWiki 观察。主题纯度、收入增量和估值仍要按主题技能自己的来源与模型做独立论证。事实型字段（设备/材料/客户/下游）只作产业链索引线索，strict 模式排除未证实关系；explore 模式明确标出待核。刷新只生成预览与用户确认入口；没有显式确认不派发模型/产生费用。旧版 StockWiki 没有 capability 时可明确 `unsupported` 降级到技能既有流程，不能将其视作零候选。

## TDD 工作包（依赖满足后）

1. 冻结 IQS 合同 hash、StockWiki 公开响应 golden/版本、目标技能 HEAD/status；列出本子树拟写的精确文件和目的，请用户授权。预期修改集中在本技能 `SKILL.md` 的第 5/6 步、对应 `references/` 和本技能测试/工具；具体路径以预检结果为准。不得碰 `industry-research/`、StockWiki/IQS/StockQA 代码。
2. 对公开技能入口写 RED：正常候选、同 issuer 多挂牌去重、严格关系与探索模式区分、空且覆盖完整、空但部分覆盖、身份歧义、旧协议/unsupported、过期评分、分页 cursor/snapshot 改变、来源/模型/时间元数据透传。mock 只替代 StockWiki 的公开边界；必须用一个真实 owner golden 的 consumer-contract 测试证明请求/响应形状，而非私造生产正例。
3. 最小适配器接入第 5/6 步。保持研究报告原有表格/计算，新增“快扫初筛/待核”出处与缺口列；不把快扫分数直接转为主题投资推荐。刷新预览无 side effect；重复运行只读查询不会写库或发送模型请求。
4. 用虚构小主题、临时输出根做离线 E2E，从技能公开入口走到候选表；断言无 live provider/网络、无 PDF/网页下载、无写出根外文件，结束后删除临时根。再跑该技能现有质量校验脚本/受影响测试。G4 阶段进行一次独立只读审查；无需逐个 helper 审查。

## 当前可交付的只读准备与完成标准

前置未齐时，harness 交出上述预研报告；若已完整勘察，即使结论是“生产端点尚无”，报告也可标 `prestudy_complete`，handoff 的 T01 状态仍为 `partial`。只有必要源码/接口无法读取时才标预研 `blocked`。**不能提交消费端实现或宣称 T01 完成**。前置齐全且获写授权后，完成需有五个 case 的运行证据、版本/水位/覆盖端到端验证、旧版降级、临时目录清理及 owner review。

按 [handoff schema](../handoff.schema.json) 返回 `package_id=TH-01`、base/result commit、只改本子树的路径与 hash、实际 query/golden 版本/hash、测试命令及数量、网络/费用标志、review 和 open items。总控只在接口与 G4 大节点验收后串行合并共享 `local-skills` Git 根。
