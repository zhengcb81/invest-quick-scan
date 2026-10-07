# EVID-LAB-01 下一轮小样本实验提案（预注册，未执行）

**状态：`execution_enabled=false`、`live_not_run=true`。** 本提案只是预注册设计，
未获用户预算授权与总控live放行前不产生任何请求。运行时复用 StockQA 执行/账本/搜索，
不另建客户端、调度器、缓存或outbox；不向生产执行器发新字段。

## 1. 沿用的冻结样本（不自行扩大）

- 三市场：宁德时代 300750、中信建投 06066、Alphabet GOOGL（真实历史身份样例，
  identity_revision 2/2/1，provisional/provisional/verified 原样）。
- 每司10题：IQS_01/02/04/05/08/09/10/12/13/16，题意与1/5/10锚点冻结
  （rubric_version 1.0.0），prompt 骨架沿用冻结 v5。
- **是否增加样本由用户决定**；本提案默认不扩大股票池、不加题。
- 需要重新检索：历史 source snippets 已清理，证据臂必须重新取片段
  （快扫只用搜索短片段，不下载财报/网页正文）。

## 2. 研究问题与四层报告（严格分开）

| 层 | 问题 | 指标 |
|---|---|---|
| L1 数据工程成功 | 请求/包是否按协议完成 | model/search 请求数、成功/失败/未知、整包成功率 |
| L2 结构恢复 | 一题坏是否拖垮整包、可恢复多少 | 逐项契约有效率、item_inspection 可恢复率（缺则 not_measurable） |
| L3 来源支持 | claim 是否被当次片段支持 | supported/partial/unsupported/no_claims（agent分区盲评，非gold） |
| L4 评分锚点依据 | 高分是否有方向/区间依据 | scored 分母内的 basis supported/insufficient（≠精确分验证） |

四层分母互不混用；历史 186/24/396/70/326/191/14 不并入本轮分母。

## 3. 实验因素与矩阵

- **A 打包**：`mixed-five`（现协议混合题包）vs `themed-five`（同证据主题分组五题包）。
- **B 证据**：`baseline`（检索片段原样）vs `annotated`（片段带显式真实主体/期间/
  单位/表头覆盖标注；无法确定期间/单位的片段剔除并记 unknown，不编造）。
- **C 思考**：DeepSeek `off/on` 为主对照；MiMo Pro 仅 `off/on` 小额对照
  （固定在 mixed×baseline，避免把 Pro 矩阵铺满）。

| 模型 | cells | 每cell请求数 | 小计 |
|---|---:|---:|---:|
| DeepSeek（A2×B2×C2） | 8 | 6（3公司×2个五题包） | 48 |
| MiMo Pro（A1×B1×C2） | 2 | 6 | 12 |
| **合计** | 10 | | **60 模型请求** |

搜索与矩阵共享：3公司 × 4检索意图 × (Brave basic + Tavily advanced) =
**24 搜索请求**（Tavily advanced ≈24 credits）。

生成参数：`explicit_only/2`（未声明即省略 temperature）、`stream=false`、
输出上限10000、官方 thinking 开关；披露 DeepSeek thinking 忽略 temperature、
MiMo 开启强制采样的服务端行为；`finish_reason=length` 记失败（沿用本轮口径）。

## 4. 预算、缓存与停止规则

- 上限：`model_http_cap=60`、`search_http_cap=24`、`cash_usd_cap=4.00`。
- token 公共价参考估算 ≤ USD 0.85（思考开/关按本轮实测方向放大取保守值）；
  **参考与现金上限不可相加**；MiniMax 套餐扣额保持 unknown（本轮不涉及M3）。
- 应用缓存冷启动（输入指纹与本轮不同）：不给缓存预算；缓存键绑定
  题意/锚点/身份/日期/上下文/模型/端点/生成参数/parser/transport policy；
  新 warm miss 直接拒绝发送；provider 前缀缓存单独报告。
- 随机顺序：`(cell, company)` 单元以 seed=`20261007` 洗牌，登记于预注册JSON。
- 停止/接续：reserve-before-send；已归档 run_id 禁止 prepare；崩溃续跑只对
  未完成 reservation 处理；**未知结果不重新收费、不重发**。
- 失败不补齐：每请求一次机会，无格式重试、无换模型拼臂；失败保留原错误。

## 5. 报告与判读规则

- 逐题分母 = 已回答条目（含 unknown）；整包分母 = 60 请求；
  评分依据分母 = scored 条目；claim 支持分母 = 含 claim 的回答。
- unknown 支持规则：unknown 计入逐题分母、排除出评分依据分母；unknown 带 claim
  仍出诊断记录。
- 思考假设只允许表述为“来源支持与语义维度 abstain 率是否改善”，
  **不得**表述为投资准确率提升；高分弱证据必须单独列出。
- 结构通过 ≠ 来源支持 ≠ 评分锚点依据；三层各自出表。
- 评审仍是两个互斥分区的 agent 盲评，`not_human_or_world_gold`；
  inter-rater 校准与人类 gold 校准保持 `not_run`。

## 6. 短片段缺表头的可执行改进（证据臂 B 落地）

1. 按题选择上下文：只注入与该题主题相关的片段，减少换行错位。
2. 保留必要单位/期间：切片时强制携带表头行与期间行；携带失败则该片段不入注释臂。
3. 来源不足明确 unknown：片段无期间/单位 → 结构化字段 `period/unit = unknown`，
   模型应给 insufficient_evidence，诊断器把缺信息判 abstain 而非矛盾。

## 7. 协议/工具生成参数：现状与缺口

- 当前版本：`mimo-pilot-generation-policies-2026-10-07.json`（声明
  thinking/response_format/上限/缓存键）；历史 observer 已改 `explicit_only/2`
  并离线验证，**未再收费重跑旧臂**。
- 缺口：固定 StockQA 客户端历史上会注入默认0.7（48次实际发生）；本轮必须由
  transport 显式省略并在 provenance 中记录；缓存键需包含 transport policy
  （已升级点）；`finish_reason=length`、reasoning token 缺失仍按未知处理。
- 不新增生产执行器字段、不移植新的网络调用器；执行仍由 StockQA 侧现有入口承担，
  放行与实施顺序按总控回收流程。

## 8. 执行门（全部未满足，故未执行）

1. 用户对该上限的明确预算授权；
2. 总控对 live 运行的当前明确放行（含样本、输入、价格、清理方案）；
3. 预注册JSON由总控核签后把 `execution_enabled` 改为 `true` 才可运行。

**本包不执行任何一项；新真实搜索、模型实验、人类gold校准、生产采用均 `not_run`。**
