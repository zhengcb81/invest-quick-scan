# TH-01｜主题价值链研究读取快扫候选

**可单独交给 Theme harness 的施工指令，当前仅可只读预研。** Owner 子树 `C:/Users/郑曾波/Projects/local-skills/analyze-theme-value-chain/`；任务 T01，验收 CONS-01、CONS-02、QUERY-04、CONS-05、CONS-06。G3、F05、W11 为硬前置；这三项及 StockWiki 公开 query endpoint/能力/golden 都通过之后，且用户授予 Theme 子树写入权限，才能进入代码施工。Theme 与 Industry 共用 `local-skills` Git 根：各用独立工作树/分支，绝不写对方子树，集成串行。当前总计划只授予本子树 read-only。

当前只读部分使用[统一预研与记录规则](../prestudy/README.md)及其报告模板；由本 harness 在最终消息交回结果，总控核验后记入 IQS，不要求本 harness 写中央计划仓。

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

前置未齐时，harness 可以交出：现有第 5/6 步调用图、候选字段映射表、StockWiki 当前 capability 缺口、拟写文件清单、RED fixture 设计和开放问题；状态写 `blocked` 或 `partial`，**不能提交消费端实现或宣称 T01 完成**。前置齐全且获写授权后，完成需有五个 case 的运行证据、版本/水位/覆盖端到端验证、旧版降级、临时目录清理及 owner review。

按 [handoff schema](../handoff.schema.json) 返回 `package_id=TH-01`、base/result commit、只改本子树的路径与 hash、实际 query/golden 版本/hash、测试命令及数量、网络/费用标志、review 和 open items。总控只在接口与 G4 大节点验收后串行合并共享 `local-skills` Git 根。
