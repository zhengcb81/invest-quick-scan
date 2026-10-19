# UI-BANK-EXPLORER-13｜题库浏览、公司矩阵、逐题答案与选股器

- 包 ID：UI-BANK-EXPLORER-13
- lane：iqs
- 类型：独立外包施工包（UI 设计与实现，唯一 writer）
- 写根：C:/Users/郑曾波/Projects/iqs-question-bank-ui-lab（新建；本包唯一可写仓库）
- 读根：C:/Users/郑曾波/Projects/invest-quick-scan（只读数据与题库）
- 状态：ready_for_scoped_support_after_unique_writer_preflight
- 运行：本地离线 Web 应用；零外部网络；可用本地静态资源与真实 JSON 数据
- 目标用户：项目所有者（你）与后续研究/投资流程使用者

## 1. 目标

做一个可本地运行的 UI，把现有题库、公司适用性、逐题答案和选股筛选连成一条可用的浏览与筛选链路：

1. 看到每一组题库的内容，并按版本切换查看；能比较不同版本。
2. 看到“公司 × 题库”矩阵：基础题库对所有公司适用；特色题库按类型/行业/阶段/属性显示适用、不适用或待确认。
3. 对每家公司，看到其适用题库下每一道题的回答，包括分数、理由、证据和缺失状态。
4. 做选股器：按题库内题目分数筛选目标公司列表，并明确显示覆盖率和缺失数据。

## 2. 必做功能（缺一不可）

### F1 题库内容与版本

- 列出全部模块：common、types、industries、stages、overlays、diagnostics。
- 每个模块展示：名称、kind、版本、applies_when、题目数、状态、来源文件。
- 点开模块看每道题：题号、题面、维度、优先级、证据关注、1/5/10 锚点、replaces/construct、rubric 版本。
- 版本选择器：按 catalog/release/module 版本查看；至少支持：
  - 当前版本；
  - 历史 release（从 questions/releases/locks 读取）；
  - 两个版本并排比较，标出新增、删除、改题义、改锚点。
- 对“同一模块不同版本”必须能看出差异，不能只显示一个静态列表。

### F2 公司 × 题库矩阵

- 行：公司；列：题库模块（可按 kind 筛选）。
- 基础题库 common 对所有公司显示“适用”。
- 特色题库显示四态：applicable / not_applicable / unknown / not_evaluated。
- 每个格子可点开，显示判断依据：公司类型、行业、阶段、属性、route decision id、来源；没有依据时明确写“未评估”，不能默认“不适用”。
- 支持按公司、kind、适用状态筛选。
- 数据不足时（当前只有 12 家公司有答案）矩阵仍要能展示全部公司，并标“无答案/未扫描”。

### F3 公司逐题答案

- 选择公司后，按“适用题库”分组展示题目。
- 每题展示：分数（1–10 或“证据不足”）、理由、证据 URL、题目版本、模块、是否核心题、运行/模型信息。
- 支持切换题库版本；切换后明确标出该答案对应的版本是否与当前版本一致。
- 缺失答案显示“未回答/无数据”，不能补 5 分或空白假装 0 分。
- 对当前扁平 24 题扫描（未绑定题库版本）必须显示“未绑定版本”徽标，不能冒充正式版本化答案。

### F4 选股器

- 选择题库/版本、题目、分数条件（例如某题 >= 7，或多题 AND/OR）。
- 输出公司列表：命中公司、命中题数、缺失题数、覆盖率。
- 支持按“必须全部有答案”或“允许缺失”切换；默认必须显示缺失，不能静默排除。
- 支持导出 CSV/JSON；保存筛选条件。
- 结果页明确写“这是按草稿答案筛选，不是投资建议”。

## 3. 当前真实数据与约束

- 题库：questions/catalog.json（48 模块 / 222 题），questions/releases/{locks,packages,artifacts}；版本以 lock 与每题 definition/semantic/prompt hash 为准。
- 公司：runs/existing-list-onboarding-2026-10-18/dashboard/roster-status.json（214 家）或等价导出。
- 答案：
  - docs/implementation/reviews/thin-scan-2026-10-18/*/answers.json（12 家、24 题、大多未绑定版本）；
  - 少量 bank 模式答案含 bank identity（package/release/module/逐题 hash）。
- 适用性：
  - 当前没有完整的逐公司 route decision 导出；UI 必须支持从 profile/route 文件读取，也支持“未评估”四态。
  - 不得把“没有答案”推断成“不适用”；两者分开。
- 演示数据：允许用 fixtures 补足 UI 状态，但必须标 synthetic=true，且不能覆盖真实数据字段。

## 4. 过程与门禁（必须按顺序）

### G0 派发

主控确认本卡、写根为空或干净、唯一 writer。未确认不得开工。

### G1 功能与技术设计（独立 agent A）

产出 design/functional-tech.md，必须包含：

- 信息架构与页面清单；
- 每个页面的用户流程、组件、交互状态；
- 数据契约：题库/版本、公司、适用性、答案、筛选条件的字段与来源；
- 技术路线选择：至少比较
  1. Vite + React/TypeScript 静态 SPA；
  2. Python 服务端渲染（FastAPI + Jinja/HTMX）；
  3. 其他（如纯静态 HTML + 预生成 JSON）；
  给出评分矩阵（离线能力、构建复杂度、数据适配、截图测试、可维护性）和推荐；
- 目录结构、运行命令、测试与截图方案；
- 边界：缺失数据、未绑定版本、版本不一致、空结果；
- 风险与未决问题。

限制：此阶段不写实现代码，不选美术细节。

### G2 美术设计（独立 agent B）

产出 design/visual.md + design/mockups/（HTML/SVG/PNG 均可），必须包含：

- 两个视觉方向（A/B）或一个方向 + 明确备选理由；
- 设计 tokens：字体、字号、间距、颜色、圆角、阴影；
- 页面布局与响应式断点；
- 组件状态：默认/悬停/选中/禁用/空/错误/加载；
- 题库列表、版本对比、矩阵、逐题答案、选股器五类核心界面；
- 中文排版与可读性；数据密度高的表格/矩阵的可读方案；
- 不使用无意义占位文案；mockup 用真实字段名与示例数据。

限制：此阶段不写业务实现。

### G3 POC（假数据，必须先给用户审阅）

在用户确认最终设计之前，实现 agent C 先做一个**假数据 POC**，用于验证信息架构、交互和视觉方向，不是最终实现。

POC 要求：

- 只使用 fixtures 假数据，必须在界面顶部和每页标注 POC / 假数据 / 非最终设计；
- 至少 6 家假公司、6 个题库模块（common + 2 个类型/行业 + 2 个阶段/属性 + 1 个诊断）、每个模块至少 2 个版本；
- 必须覆盖 F1-F4：题库浏览+版本切换、公司×题库矩阵、逐题答案（分数/理由/证据/缺失）、选股器；
- 可本地一键打开（静态 HTML 或一条启动命令），零网络；
- 产出 poc/index.html（或等价入口）、poc/README.md、poc/screenshots/（至少 4 张）；
- 不能读取或修改真实 IQS 数据；所有假数据字段名必须与真实数据契约一致。

POC 的用途是让用户在看到真实实现前先审阅方向；POC 代码不承诺可维护性，但界面结构、字段和交互应接近最终形态。

**POC 是 G4 的强制前置条件，不是可选项。** 没有可运行 POC、没有四功能截图、没有 POC 标志，不得进入 G4。

### G4 用户确认（必须）

主控把 G1+G2+G3 POC 一起提交给用户（项目所有者）确认。必须产出 design/user-approval.json：

- decision: approved / changes_requested
- approved_design_commit: Git commit
- approved_poc_commit: POC 的 Git commit（必须与 G3 提交一致）
- user_feedback: 原文摘要
- requested_changes: 列表
- timestamp / channel

未拿到 approved，不得进入 G5。若 changes_requested，回到 G1/G2/G3 修订并重新提交；POC 必须随设计变更更新。

### G5 实施（实现 agent C）

- agent C 不得是 G1/G2 的设计作者（避免自审）；
- 实现 G4 批准的设计；
- 数据只读，不写 IQS/StockWiki/StockQA；
- 提供一条命令启动本地应用；
- 单元测试覆盖数据适配与筛选逻辑；
- 浏览器截图测试覆盖五个核心界面；
- 记录所有 fixture 的 synthetic 标记。

### G6 成果演示

产出 demo/screenshots/ 至少 5 张：

1. 题库列表 + 版本选择；
2. 两个版本对比；
3. 公司 × 题库矩阵；
4. 某公司逐题答案（含分数/理由/证据）；
5. 选股器结果（含覆盖率/缺失）。

同时产出 demo/demo.md：启动命令、演示步骤、数据来源、已知缺口。
主控把截图与 demo 提交用户；产出 demo/feedback.json（用户意见原文 + 分类）。

### G7 迭代

每轮修改产出 demo/iteration-N.md（改了什么、为什么、影响页面、截图前后对比）。
重复 G5-G6，直到用户明确 signoff：

- demo/signoff.json：decision=accepted，user_feedback，timestamp，approved_commit。

未 signoff 不算完成。

## 5. 独立角色要求

- G1 功能/技术设计：独立 agent A（只读数据，不写实现）。
- G2 美术设计：独立 agent B（不得与 A 同一 agent）。
- G3 POC：agent C（假数据原型；不得与 A/B 同一 agent）。
- G5 实现：agent C（不得与 A/B 同一 agent；若无法完全分离，必须由主控记录并说明）。
- G4/G6/G7 用户确认：由主控转交项目所有者，不得由 agent 自签。

## 6. 页面信息架构（最低要求，设计可细化）

- 顶部导航：题库 / 公司矩阵 / 公司答题 / 选股器 / 数据说明。
- 题库页：kind 分组、模块卡片、版本选择、题目展开、版本对比。
- 矩阵页：公司搜索/筛选、kind 筛选、四态图例、单元格详情抽屉。
- 公司答题页：公司搜索、适用题库 tab、逐题卡片、版本一致性徽标、缺失状态。
- 选股器：条件构建器、覆盖率设置、结果表、导出、保存条件。
- 数据说明页：数据来源、版本、synthetic 标记、未评估/未扫描说明、非投资建议声明。

## 7. 技术约束

- 离线优先：运行时不访问外网；字体/图标本地化或系统字体。
- 只读：不得写 questions/、runs/、StockWiki/StockQA；UI 本仓库可写缓存/导出。
- 可复现：固定输入 fixtures + 确定性排序；截图可重复。
- 数据适配层必须与 UI 解耦：
  - BankRepository（catalog/versions/modules/questions）
  - ApplicabilityResolver（common 恒适用 + 条件规则 + unknown）
  - AnswerRepository（版本化答案 + 未绑定答案）
  - Screener（纯函数筛选）
- 不重新计算官方分数；只展示已有分数/理由/证据，或按明确规则筛选。
- 不把 missing 当 0，不把 unversioned 当 current。

## 8. 验收用例

| ID | 必须证明 |
|---|---|
| AC-01 | 列出 48 个模块；可展开任意模块看题目、证据、锚点、版本 |
| AC-02 | 可切换至少两个历史版本；差异页标出新增/删除/改题义/改锚点 |
| AC-03 | 矩阵覆盖全部公司；common 全适用；特色题库四态；格子有依据或“未评估” |
| AC-04 | 任选一家公司，能看到适用题库和逐题答案；分数、理由、证据、版本一致/不一致、缺失均可见 |
| AC-05 | 选股器支持多题条件、AND/OR、覆盖率开关；结果含命中/缺失/覆盖率；可导出 |
| AC-06 | 未绑定版本的 24 题答案有明确徽标，不被当作版本化答案 |
| AC-07 | 零网络运行；fixtures synthetic 标记可见；无数据不编造 |
| AC-08 | 五张演示截图与实际运行一致；demo.md 可复现 |
| AC-09 | design/user-approval.json 与 demo/signoff.json 存在且为用户确认 |
| AC-10 | handoff 形状通过主控 parallel_handoff_cli.py；worktree clean |
| AC-11 | G4 之前存在假数据 POC：可本地打开、四功能可点、POC 标识明显、至少 4 张截图，且 user-approval 引用 POC commit |

## 9. 交付物

text
iqs-question-bank-ui-lab/
  README.md
  package.json / pyproject.toml（按选定技术路线）
  app/ 或 src/
  adapters/
  fixtures/            # synthetic 标记
  tests/
  scripts/run.sh 或 run.ps1
  poc/                  # G3：假数据 POC，不是最终实现
    index.html
    README.md
    screenshots/
  design/
    functional-tech.md
    visual.md
    mockups/
    user-approval.json  # 必须引用 design + POC 的 commit
  demo/
    demo.md
    screenshots/
    feedback.json
    signoff.json
    iteration-N.md
  docs/handoff/UI-BANK-EXPLORER-13/
    handoff.json
    artifacts.json
    tests.json
    cleanup.json
    summary.md
    report.md
    logs/

## 10. 非目标

- 不做交易、下单、组合管理、实时行情。
- 不写正式观察库、不做 owner 准入、不做预算/凭证。
- 不做 2000 家公司扩容。
- 不重新训练/路由模型；只消费现有数据与题库。
- 不把草稿分数包装成正式评分或投资建议。

## 11. 风险与开放问题

1. 当前只有 12 家公司有答案，矩阵/选股器会大量显示“无答案”；UI 必须诚实展示覆盖率。
2. 适用性数据不完整；没有 route decision 的公司只能显示“未评估”，不能猜。
3. 版本化答案很少；多数扫描是扁平 24 题，需清楚标记。
4. 版本对比依赖 releases 工件；如果历史版本缺少完整 lock，需显示“不可比”。
5. 用户确认可能多轮；每轮必须落盘，不能口头带过。

## 12. 参考

- questions/catalog.json；questions/releases/；questions/*/*.json
- runs/existing-list-onboarding-2026-10-18/dashboard/roster-status.json
- docs/implementation/reviews/thin-scan-2026-10-18/
- docs/implementation/plan-v2-2026-10-18.md
- docs/implementation/parallel-lanes/handoff.schema.json
- docs/implementation/parallel-lanes/review-protocol.md
