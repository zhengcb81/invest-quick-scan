# APPLIC-RESOLVE-14｜公司属性与题库适用性判定（数据化谓词 + 版本化快照）

- 包 ID：APPLIC-RESOLVE-14
- lane：iqs
- 类型：独立外包施工包（数据资产与纯函数引擎，唯一 writer）
- 写根：C:/Users/郑曾波/Projects/iqs-applic-lab（新建；本包唯一可写仓库）
- 读根：C:/Users/郑曾波/Projects/invest-quick-scan（只读数据与题库）
- 状态：ready_for_scoped_support_after_unique_writer_preflight（未派发；worker 由所有者选择）
- 依赖：QUESTION-BANK-UPGRADE-12（S04/S05 发布包与 routing 层拥有 applies_when 谓词）；消费方 UI-BANK-EXPLORER-13（矩阵四态与 basis 抽屉已就绪）
- 网络：network_scope=none（全程零外网）
- 输入：`inputs.lock.json`（8 文件，raw SHA-256 + bytes；加载前逐文件校验，不符即停）
- 交接：按本批次 `handoff-rules.md` 执行（写边界/红线/门禁/交接套件/CLI 校验）

## 0. 所有者裁定（原话，D-A14-01，2026-10-21）

> 「无法两个方法，1，是对每个特定题库设计一套动态筛选逻辑（一个lambda函数），对每家公司调用这个函数得到是否适用这个题库与否。2，保存静态的对照表格，根据表格来决定。事实上更合理的方法是1和2的结合，先用1来判定，然后保存下来，下次就直接读取保存的对照表而不用每次都运行lambda函数。」

落地解释（主控转写，供 G2 确认）：

1. "方法 1"落地为**数据化谓词规则**（结构化 JSON 规则，不是存储的代码闭包——代码闭包会制造第二真源，不可 hash/不可 review，违反 S01/S05 既有约束）；
2. "方法 2"落地为**版本化不可变快照**（判定结果缓存 + 审计工件）；
3. 真源永远是（公司属性表 × 谓词规则）；快照键含两侧版本号，输入版本未变直接读快照，任一侧 bump 自动失效重算；快照可全量重建，禁止手改。

## 1. 目标

把「公司 × 题库」适用性从现状（只有 common 恒适用，其余 47 个模块 10058 格全部 not_evaluated）升级为**有据可判的四态判定**：

- 建 214 家公司属性表（行业/阶段/类型/属性），每条带出处与置信分级；
- 为 47 个非 common 模块把定性 `applies_when` 映射为可机判谓词规则，逐条带映射决策记录；
- 纯函数引擎按三值逻辑判一次 → 产出版本化快照；
- 导出 UI-BANK-EXPLORER-13 ApplicabilityResolver 可直接读取的 JSON 形状，矩阵灰格变为蓝/阴影灰/琥珀三态增量，未映射模块保持诚实的 not_evaluated。

## 2. 必做资产（缺一不可）

### A1 公司属性表 data/attributes/companies.v1.json

- 每家公司：`entity_id`、`attributes: {industry, stage, type, extra[]}`、每属性 `{value, confidence: verified|assumed|unknown, source_ref, as_of}`；
- `verified` 必须带仓内出处（roster/运行工件/已发布文档路径+sha256）或所有者提供的分类表条目（原话引用 + 时间戳）；
- `assumed` 允许合理推断但必须写推断依据，UI 侧判为"待确认"琥珀态；
- 无出处 = `unknown`，属性缺失绝不由名称/代码猜测；
- 全表带 `attributes_version`（内容 sha256）。

### A2 谓词规则 data/predicates/modules.v1.json

- 每个非 common 模块一条规则：`module_id`、`all/any/not` 组合的结构化谓词（op ∈ in/not_in/eq/neq/exists/not_exists）、`provenance: {mapped_from: applies_when原文, decision_ref, mapped_by, approved_at}`；
- 语法复用 S06 ROUTE_02 已冻结的机器策略谓词语义，**不新建第二套规则语言**；
- 旧 prose `applies_when` 原文保留为文档字段，规则与原文并存、互相引用；
- 全表带 `predicate_version`（内容 sha256）；common 模块无规则 = 恒适用契约，不参与映射。

### A3 判定引擎 src/（纯函数）

- 输入（属性表快照 × 谓词规则）→ 输出逐格 `{entity_id, module_id, state, basis}`；
- 三值 Kleene 逻辑：属性缺失 → `unknown`（不是 not_applicable）；谓词可判假且有肯定性反证 → `not_applicable`；无规则 → `not_evaluated`（fail-closed）；
- `basis` 记录：命中的属性值+出处、命中的谓词分支、规则版本、属性版本、evaluated_at；
- 确定性：同输入两次运行输出逐字节一致；零网络、零副作用。

### A4 版本化快照 data/snapshots/

- 键：`(entity_id, module_id, predicate_version, attributes_version)`；
- 值：`{state, basis, evaluator, evaluated_at, snapshot_id}`；整表带 `snapshot_id = applicsnap_<sha256>`；
- 不可变：只追加新快照，禁止原地修改；可由（属性×谓词）全量重建，重建 hash 一致是硬验收；
- 任一侧版本 bump → 旧快照自动失配，消费者按当前版本重读/重算，不存在"悄悄用旧结论"。

### A5 人工覆盖通道 data/overrides/（一等公民，对齐 W15）

- owner 判定入表：`{entity_id, module_id, state, operator, reason_原话, decided_at, ttl}`；
- 覆盖优先于 auto 判定；TTL 过期自动回归 auto 结果并记录；
- append-only，与 D-01/D-02 决策记录同构。

### A6 UI 消费对接

- 导出器输出 UI-BANK-EXPLORER-13 `adapters/applicability_resolver.py` 可直接读取的形状（四态 + basis 字段同名）；
- UI 卡不改红线、不改渲染逻辑，只消费本包数据资产（UI 卡版本跟进属协调事项，见风险 4）。

## 3. 现状与红线（实测，2026-10-20/21）

- 模块构成：48 = common 1 + types 8 + industries 21 + stages 7 + overlays 8 + diagnostics 3；
- 矩阵实测：10272 格，其中 214 applicable（=214×common）、10058 not_evaluated（=214×47）；
- `applies_when` 现状是定性 prose（例：semiconductors「设计、制造、封测、设备、材料、电子元件；以实际环节解释指标。」），不可机判；
- roster 214 家无结构化行业/阶段/类型字段——**属性表是真正的瓶颈资产**；
- alias 先例（11 匹配 = 7 verified + 4 assumed + 1 unmatched）是本包属性分级的直接模板；
- 红线（全部有测试锁死）：无证据 ≠ 不适用；unknown ≠ not_applicable；null 永不渲染为 0；不猜、不编、fail-closed；快照是派生物，真源是属性×谓词。

## 4. 过程与门禁（必须按顺序）

### G0 派发
主控确认本卡、写根为空或干净、唯一 writer。未确认不得开工。

### G1 设计（独立 agent A）
产出 design/functional-tech.md：四资产 JSON Schema（冻结）、谓词语法与三值语义、失效/重建策略、UI 对接形状、边界（属性全 unknown 的公司、模块无规则、TTL 过期）。不写实现。

### G2 所有者确认（必须，不得自签）
把三件事提交所有者逐项确认，产出 design/owner-approval.json（decision / 原话 / timestamp / 涉及 commit）：

1. prose→谓词的**映射判读规则**（按 kind 分组的判读口径样例）；
2. 属性**分级口径**（verified/assumed/unknown 的证据门槛）与**属性来源清单**（仓内工件白名单 + 所有者补充分类表）；
3. override 协议（operator/reason/TTL）。

未拿到 approved 不得进入生产阶段。changes_requested 则回 G1 修订。

### G3 引擎实现（TDD，实现 agent B ≠ A）
- 红线先写反例测试（missing→unknown、not_applicable 需反证、重建幂等、失效自动失配、override 优先与 TTL 回归）；
- 实现 A3 纯函数引擎与 A6 导出器；
- 全测试离线可跑，日志入 docs/handoff/logs/。

### G4 属性与谓词生产
- 按 kind 分批映射（industries 21 → stages 7 → types 8 → overlays 8 → diagnostics 3），每批独立可审；
- 属性表逐家落 source_ref；无源条目如实 unknown；
- **独立审查子代理全量复核**（provenance 抽查 + 红线复跑），审查结论落 review/，不得自签。

### G5 快照生产与验收
- 全量 214×48 快照生成 + 重建一致性校验；
- 失效用例：bump 单条属性 → 对应格失配重算，其余不动；
- UI parity：UI-BANK-EXPLORER-13 resolver 读快照后矩阵状态分布改变，common 仍 214 适用、未映射模块仍 not_evaluated；
- 所有者验收：demo（状态分布对比页）+ signoff.json（decision/原话/approved commit）。

### G6 交接
docs/handoff/APPLIC-RESOLVE-14/ 全套件（handoff.json/artifacts.json/tests.json/cleanup.json/summary.md/report.md/logs/），按本批次 `handoff-rules.md` 第五节逐项填写；过主控 parallel_handoff_cli.py 强制 --catalog 校验（规则第六节命令），worktree clean。

## 5. 技术约束

- 离线：零外网；属性来源仅限仓内工件 + 所有者提供的分类表，不得网络采集行业标签；
- 只读：不写 questions/、runs/、StockWiki/StockQA、invest 数据根；
- 确定性排序（entity_id 升序）、内容寻址版本、UTC 时间戳；
- 三值语义与现有 screener（unknown 策略）保持同一套词汇；
- 不重算任何官方分数；不裁决模块依赖/闭包（属 S06）；只做单模块适用性判定。

## 6. 验收用例

| ID | 必须证明 |
|---|---|
| AC-01 | 属性表 214 家全覆盖；verified 条条有仓内出处或所有者引用；无出处=unknown，assumed 不冒充 verified |
| AC-02 | 47 个非 common 模块每条谓词可追溯到 applies_when 原文 + 映射决策记录；未映射模块保持 not_evaluated（fail-closed 测试） |
| AC-03 | 三值逻辑：属性缺失 → unknown；not_applicable 必须有肯定性反证（反例测试锁死） |
| AC-04 | 快照键含双侧版本；任一侧 bump → 旧格自动失配（测试） |
| AC-05 | 快照不可变 + 可重建：同输入重建两次 sha256 一致；脚本拒绝手改 |
| AC-06 | owner 覆盖一等公民：operator/reason/decided_at/ttl 落盘、优先于 auto、TTL 过期回归（测试） |
| AC-07 | UI parity：UI-BANK-EXPLORER-13 resolver 读快照后四态分布改变且 common 仍 214 适用、未映射仍 not_evaluated；UI 卡红线零改动 |
| AC-08 | 零网络运行有 grep/日志证据；属性来源全部在白名单内 |
| AC-09 | 独立审查结论 + 所有者 signoff 落盘，无自签 |
| AC-10 | handoff.json 过 CLI 强制 --catalog 校验；worktree clean；.tmp 无残留 |

## 7. 交付物

```text
iqs-applic-lab/
  README.md
  pyproject.toml / .gitignore
  schemas/                     # 四资产 JSON Schema（冻结）
  data/
    attributes/companies.v1.json
    predicates/modules.v1.json
    overrides/                 # append-only owner 判定
    snapshots/applicsnap_*.json  # 不可变，可重建
  src/                         # 纯函数引擎 + 导出器
  tests/                       # TDD 红线反例
  scripts/run_eval.py, validate.py, export_ui.py
  design/
    functional-tech.md
    owner-approval.json        # G2 所有者确认（必须）
  review/                      # G4 独立审查结论
  demo/                        # G5 状态分布对比 + signoff.json
  docs/handoff/APPLIC-RESOLVE-14/
    handoff.json, artifacts.json, tests.json, cleanup.json,
    summary.md, report.md, logs/
```

## 8. 非目标

- 不做 2000 家公司扩容（214 家基线）；
- 不重算分数、不碰答案与选股逻辑（UI 卡职责）；
- 不写 StockWiki/StockQA/主仓数据根；
- 不新建第二套规则语言；不替代 S06 ROUTE_02 生产链路（本包是离线候选资产）；
- 不做网络采集行业分类；
- 不把 unknown 包装成结论；不做投资建议。

## 9. 风险与开放问题

1. prose→谓词映射有判读主观性：必须 G2 所有者逐 kind 确认口径后才批量生产；
2. 属性来源受限（零网络）可能使相当比例公司停留在 unknown：这是合法产出，诚实呈现，不降级红线；
3. 模块依赖/冲突闭包属 S06，本包只判单模块适用性——组合层结论以 S06 为准；
4. UI 消费形状若需 UI-BANK-EXPLORER-13 小版本跟进，属跨包协调事项，须主控走该卡的变更流程，不得本包越权改 UI 仓；
5. 快照体积（214×48 格含 basis）需在 G1 给出预算与裁剪策略（basis 只存引用不复制正文）。

## 10. 参考

- **本批次**：`handoff-rules.md`（交接规则，与本卡一并外发）；`inputs.lock.json`（输入唯一字节清单，加载前逐文件校验）；`manifest.json`（批次注册）
- docs/implementation/tasks.json：S06（证据化路由决策）、W15（持久化路由快照与人工覆盖）、U04（依据显示，消费方）
- docs/implementation/parallel-lanes/packages/2026-10-19/QUESTION-BANK-UPGRADE-12.md（routing 层归属）
- docs/implementation/parallel-lanes/packages/2026-10-19/UI-BANK-EXPLORER-13.md §3/§11.2（消费方契约与已知缺口）
- questions/catalog.json（48 模块 applies_when 原文）；runs/existing-list-onboarding-2026-10-18/dashboard/roster-status.json（214 家）
- docs/implementation/parallel-lanes/handoff.schema.json#1.0.0；review-protocol.md
