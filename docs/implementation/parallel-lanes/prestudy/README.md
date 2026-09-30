# TH-01 / IN-02 只读预研与记录规则

预研是**接口勘察和施工准备**，不是 T01/T02 实施或验收。两个 harness 可以同时做，因为只读自己的技能子目录、IQS 契约和 StockWiki 的公开接口；任何写入仍须等 G3/F05/W11、真实 query 能力/golden 与用户对相应 `local-skills` 子目录的授权。预研不发真实 LLM/API 请求、不抓取或下载公司资料、不跑会改仓库或生产数据的测试。

## 分工和预计用时

| harness | 先读的实际路径 | 要回答的核心问题 |
|---|---|---|
| TH-01 | `analyze-theme-value-chain/SKILL.md` 第 5/6 步、`references/quality-gates.md`、`references/output-schema.md`、`references/company-model.md` | 候选公司如何进入主题价值链表？哪些快扫字段只是线索，哪些主题暴露必须另行证明？何处显示覆盖/过期/身份歧义？ |
| IN-02 | `industry-research/SKILL.md` 第 6/7 步、`modules/company-evaluation.md`、`modules/report-generation.md`、`config.yaml` | 当前公司名单从研报/wiki/companies 目录怎样汇集？如何把快扫作为可选候选来源，且不破坏既有深研/PDF流程？ |

两者共同只读核对 IQS [`exchange-and-query.md`](../../contracts/exchange-and-query.md)、[`freshness-and-jobs.md`](../../contracts/freshness-and-jobs.md)、[`tasks.json`](../../tasks.json) 中自己的 T01/T02，以及 StockWiki **当前实际** `capabilities/search/get_profiles/request_refresh` 公开 API/CLI、版本、owner golden。合同文字与样例只代表协议，不代表端点已实现；找不到公开端点时精确记录“未找到/尚无验收证据”，不得调用私有 SQLite 填空。不要自选股票池，不要把快扫评分或关系事实升级为正式投资结论。

## 每个 harness 的操作顺序

1. 记录 `local-skills`、StockWiki、IQS 的 HEAD 和工作树摘要，当前 skill 文件/合同的 SHA-256；查目标子树当前 `AGENTS.md` 与公开入口。只读命令不能生成缓存到外仓。记录观察时间和查询路径，避免报告被后续新提交误用。
2. 画出本技能“当前发现公司→收集数据→产出报告”的真实调用路径。列出可插入快扫的**单一边界**，标明输入、输出、失败降级和旧流程保留方式；区分经营主体 `analysis_subject_id`、法律发行人、证券/挂牌。
3. 做字段对照表：业务细分、上下游/设备/材料/客户、评分、模型、`information_cutoff`/`observed_at`、字段/模块版本、coverage、freshness、来源指针分别来自哪个公开字段，如何进入本技能的候选/报告列。缺的字段和所需 owner 契约变更要明确列出，不能凭中文显示名或私有表名猜字段。
4. 给出 TDD 清单与真实入口的最小离线 fixture 方案：完整覆盖/空结果、partial/not_covered、身份歧义、同 issuer 多挂牌、旧协议/unsupported、过期/unknown、分页快照、未证实关系及刷新预览零派发。没有 owner golden 时仅设计 fixture，**不得称其为生产正例**。
5. 列出后续实施的精确拟写路径、前置版本与授权需求、估计依赖风险。到此停止；不写技能代码、不为测试触发 API，也不提交外仓。预研报告以 [模板](template.md) 返回给总控。

## 结果怎样保存

两个 harness **不写 IQS 总控仓**。它们在最终交接消息中提交完整 Markdown 报告和符合 [`handoff.schema.json`](../handoff.schema.json) 的 JSON（`status=partial` 或 `blocked`、`authorization_scope_ref=not_authorized`、`changed_paths=[]`、`external_writes=false`、`network_calls=false`、`paid_calls=false`）。如果其运行环境允许临时输出，可附临时文件 SHA；临时目录随后清理。总控核对报告里的版本、路径与事实后，在本目录新增不可变快照：`TH-01-<YYYY-MM-DD>-<shortsha>.md` 或 `IN-02-<YYYY-MM-DD>-<shortsha>.md`，并把报告链接、输入 commit/hash、状态与下一依赖记入 `progress.md` / `findings.md`。新预研覆盖旧认知时新增报告，不改写历史报告；施工包索引指向**最新已核验报告**。现在尚无两份预研结果，不创建空白“已完成”报告。

### 精确提交和归档接口

| 阶段 | 唯一负责方 | 必需交付 / 动作 | 校验与拒收条件 |
|---|---|---|---|
| 提交 | TH-01 或 IN-02 harness | 最终消息中提供一份完整 UTF-8 Markdown（按[模板](template.md)）和一份完整 JSON，JSON 需满足 [handoff schema](../handoff.schema.json)；`package_id` 分别为 `TH-01`/`IN-02`，`lane_id` 分别为 `theme`/`industry` | 无完整正文、缺 base commit/关键文件 hash、改动外仓、把合同当生产端点、把拟测当已测，均退回补证；不会由总控猜补 |
| 接收 | IQS 总控 | 校验 JSON schema、Markdown 所列文件/版本与当前仓库快照、`changed_paths=[]` 与无网络/费用事实；记录 `accepted` 或 `rejected` 及原因 | 只接收可重现的精确快照；接口/golden 未实现可如实记录为缺口，不因此拒绝预研 |
| 留档 | IQS 总控 | 将 Markdown 规范为 UTF-8/LF，计算 SHA-256；文件名的 `<shortsha>` 是**该 Markdown 完整字节 SHA-256 前 12 位**。配套 JSON 保存为同前缀 `.handoff.json`，文件原文与 hash 都保留 | 若同名已存在且 hash 不同则拒绝覆盖；不得修改旧快照来伪造新状态 |
| 索引 | IQS 总控 | 原子更新本目录 [`archive-index.json`](archive-index.json)，按[索引 JSON Schema](archive-index.schema.json)校验：package、报告/JSON 相对路径和 SHA-256、观察时间、local-skills/StockWiki/IQS 三仓输入 commit、接收时间、预研状态、实施状态、前置缺口 | 索引只指向已验收文件；`implementation_status` 在 T01/T02 真实验收前固定 `not_started`，旧索引项不删除 |
| 计划同步 | IQS 总控 | 在 `progress.md` 写入报告链接/验证结论；`findings.md` 记接口差距；`task_plan.md` 的 T01/T02 仍未完成，并在施工包索引写“最新已核验报告”链接 | 仅预研通过不能解除 G3/F05/W11、写授权或正式 owner query/golden 门 |

`archive-index.json` 当前 `entries=[]` 是“尚未收到报告”的真实状态。每个索引项字段固定如下；`report_status=prestudy_complete` 表示勘察已完成，**不等于** `implementation_status=complete`；与 handoff JSON 的 `status=partial` 并不矛盾。

```json
{
  "package_id": "TH-01",
  "report_path": "TH-01-YYYY-MM-DD-<sha12>.md",
  "report_sha256": "<64 lowercase hex>",
  "handoff_path": "TH-01-YYYY-MM-DD-<sha12>.handoff.json",
  "handoff_sha256": "<64 lowercase hex>",
  "observed_at_utc": "<ISO-8601 UTC>",
  "accepted_at_utc": "<ISO-8601 UTC>",
  "input_commits": {"local_skills": "<commit>", "stockwiki": "<commit>", "iqs": "<commit>"},
  "report_status": "prestudy_complete",
  "implementation_status": "not_started",
  "dependency_gaps": ["<具体缺口>"]
}
```

上面的 JSON 是**格式示意，不是已发生的预研记录**；真实条目必须填真实值并通过档案校验。`archive-index.json` 中同一包最后一个已验收且输入快照最新的条目是当前预研入口；若仓库已变化，总控先核实是否需要增量预研，不自动沿用旧结论。

预研完成只意味着“实施入口、接口缺口和测试方案已查清”；T01/T02 仍处于依赖门等待。待 G3/F05/W11 和 owner query/golden 达标后，总控重新核对报告快照，过期则要求增量预研，再由用户授权具体子树写入并开工。
