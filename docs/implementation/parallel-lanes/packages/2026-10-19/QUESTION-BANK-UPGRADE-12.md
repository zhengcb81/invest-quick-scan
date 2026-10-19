# QUESTION-BANK-UPGRADE-12｜题库全面升级与版本化架构

- 包 ID：`QUESTION-BANK-UPGRADE-12`
- lane：iqs
- 类型：独立外包施工包（offline candidate，唯一 writer）
- 写根：`C:/Users/郑曾波/Projects/iqs-question-bank-lab`（新建，包内唯一可写仓库）
- 读根：`C:/Users/郑曾波/Projects/invest-quick-scan`（只读 vendor；禁止改主线）
- 状态：ready_for_scoped_support_after_unique_writer_preflight
- 语言/运行：Python 3.11+，仅标准库；零网络、零模型调用、零付费调用

## 1. 为什么做这个包

现有题库不是“没有特色题库”，而是“特色题库存在但主线只用了 common”。本包要把全部题库做成**可独立升级、可版本化、可历史读取、可组合**的一套统一题库，而不是继续在主线里打补丁。

基线事实（只读核对，实施时复算）：

- `questions/catalog.json`：version 3.2.0，48 个模块、222 道评分题。
- 构成：common 24；types 8 模块/46 题；industries 21/84；stages 7/28；overlays 8/24；diagnostics 3/16。
- 已发布锁 `questions/releases/locks/modrel_18c097b…json`：48 modules / 222 questions。
- 类型题通过 `replaces` 替换核心题（如 bank 替换 IQS_16/03/11/12/22），保留 construct；行业/阶段/属性题是新增题（construct 为空，context）。
- 设计文档要求：`common → types → industries → stages → overlays → diagnostics` 固定顺序；core 24 冻结；类型恰好一个、主阶段恰好一个、行业 0–2、属性正交。
- 组合可用：以宁德时代手工路由 `operating + auto + scaling + concentrated` 实测，quick 29 题、full 37 题（24 core + 13 context）。
- 实际扫描的缺口：native manifest 的 `route_decision.status=partial`、classification `not_run`，profile 的 company_type/industry/stage/overlay 全空，`eligible_module_ids=["common"]`、`max_questions=24`；薄扫描只读了扁平 24 题清单，未绑定 package/release/模块/题义哈希。

## 1.1 基线审计发现（2026-10-19，格式审计已回）

格式/一致性审计（独立 agent，只读）结论：question_sets.py validate 通过，48 模块/222 题、ID 唯一、锚点 1/5/10、replaces 合法、无重复题面；只有 1 个真实跨文件不一致与 3 个版本/标记问题：

| # | 严重度 | 位置 | 问题 | 本包要求 |
|---|---|---|---|---|
| F-1 | 中 | questions/catalog.json recovery.applies_when | 与 recovery.json 及已发布 artifact 文案不一致（catalog 是唯一漂移副本） | 必须修复并加 catalog 与 module 一致性校验 |
| F-2 | 低 | 48 个模块 version 全为 3.0.0 | catalog 已到 3.2.0，recovery 文案修改未升模块版本 | 建立“内容变更必须升模块版本或记录 catalog-only”的规则 |
| F-3 | 低 | 8 道题 rubric_version=2.0.0，其余 214 道 1.0.0 | 无模块级 rubric 版本记录，版本语义混杂 | 统一 rubric 版本或按模块记录并校验 |
| F-4 | 低 | 10 道 types 题显式 critical=true | 与替换 IQS_12/13/16 的自动继承重复；选择器会消费该字段 | 明确保留/删除并写入契约与测试 |

### 内容审计（独立 agent，只读，2026-10-19）

结论：222 个定义中只有 60 个 core（24 common + 36 types），162 个 context；每家公司实际 24 个计分槽。主要问题：

- 行业题 84 道全部是 context，行业特定信息（软件收入质量、半导体出口管制、医疗集采/专利悬崖、公用事业监管回报）没有进入分数；部分行业题只是 IQS_03/05/11/17 的复述。
- pre_revenue 继承 IQS_02/10/21（收入耐久、ROIC、增量资本回报）对商业化前公司结构性不可答；PRE_REVENUE_03 把 burn 效率映射到 IQS_11。
- common 的 IQS_20/21 重复（增长净效果 vs 增量资本回报）；IQS_05/06 重复计分，且 IQS_06 要求“趋势”但 schema 无趋势字段。
- holding 的 HOLDING_03 替换 IQS_03 却问组合资本回报（IQS_10），造成 IQS_03 丢失、IQS_10 双计。
- 只有 IQS_05/18 明确要求反证；其余题缺 falsifier 与观察窗口。
- 10 道题的 10 分锚点依赖内部数据（组织授权、clawback、RWA、项目全成本），公开证据通常只够 5 分。
- overlays 24 道全部是核心题复述，无触发/优先级/权重；type 的 10 道 context 也多为复述。
- turnaround/recovery/declining 重叠；DUPONT_01 是其余因子之和；Porter 重复 IQS_04/05。
- 多分部类型题（银行零售/对公、保险财险/寿险、券商费/自营）强行给一个分。

本包要求：逐条给出 KEEP/REWRITE/NEW/RETIRE 决策；行业题至少各 1 道进入可计分构念或明确删除；pre_revenue 增加 N/A/替代；IQS_20/21、IQS_05/06 去重；overlays 改为有触发和优先级的修饰项或删除；多分部题拆分或明确分部口径。

### 架构审计（独立 agent，只读，2026-10-19）

结论：**打包/发布是解耦的；测量身份不是。** 旧包/旧锁/旧 artifact 不可变且可解析，但以下耦合必须修：

1. 薄扫描自建 prompt 却盖上 manifest 的 prompt/semantic/definition hash（本包必须禁止；主线已改为 manifest prompt 逐字发送并校验 hash，另记 dispatch hash）。
2. 聚合权重/阈值/关键门是代码常量，method_id 只哈希 core 题指纹；改权重不会改 method_id。
3. type 替换只校验 replaces/construct，不校验 dimension/scope/锚点/rubric 等价；跨类型分数可能不可比。
4. 路由策略嵌在模块 release 里，router 升级被迫连带模块 release。
5. renderer 是代码而非可归档 artifact；renderer 一改，所有历史 semantic hash 与旧 manifest 校验失效。
6. 模块分/覆盖率只有文档，没有 module-level score/method hash。
7. 生产实际 common-only（CATL 24 题），compose 不拒绝空行业覆盖；观察仍显示“已绑定题库”。
8. legacy manifest 的 replacement 校验依赖当前 catalog 版本，题库升级会让旧观察降级为 needs_verification。

本包要求：把聚合/评分尺、renderer、router 各自做成独立 release；type 替换发布等价类；模块分/覆盖率成为 manifest 字段；生产 manifest 必须记录覆盖缺口并拒绝静默 common-only；legacy 读取 pin 旧 catalog/package，不依赖当前版本。

## 2. 目标（必须全部完成）

1. **统一设计**：一份题库总规范（内容、格式、架构、版本、兼容、迁移），覆盖 common + 所有特色模块。
2. **全面升级所有题库**：对 48 个模块逐一给出“保留 / 改写 / 新题 / 退役”的决定和理由，不允许跳过；升级后题量不少于 222，且不得靠堆题稀释核心。
3. **每个模块充分解耦**：模块内容、路由适用性、组合关系、评分映射、发布锁、呈现规则分层；模块之间不互相 import；主程序只依赖 catalog/schema/release。
4. **版本管理**：模块版本、题目 ID、题义指纹、catalog 版本、release lock、release 生命周期、兼容矩阵、历史读取、迁移/退役，全部可机器校验。
5. **三个独立审计**：内容、格式、架构各由不同 agent 完成；作者修复后由原审计 agent 复核。
6. **可交接**：handoff 文件集完整，主控 CLI 预检通过，作者与审计者身份可追溯。

## 3. 非目标（明确不做）

- 不接生产、不写 owner/StockQA/StockWiki、不做预算/凭证/派发。
- 不跑 2000 家公司、不做真实搜索/模型调用。
- 不重写 facts 题库（事实题单独体系，本包只做评分题库；可在附录给接口建议）。
- 不把行业/阶段/属性题静默计入核心 24 均分。
- 不覆盖旧观察、旧 manifest 或旧回执。

## 4. 交付物

### 4.1 题库仓库结构

```text
iqs-question-bank-lab/
  README.md
  pyproject.toml
  catalog.json                  # v4：模块清单、版本、路径、状态、能力
  modules/
    common/                     # 24 核心题（冻结构念）
    types/                      # 8 类公司模板（替换式）
    industries/                 # 21 个行业模块（新增式）
    stages/                     # 7 个阶段模块
    overlays/                   # 8 个属性模块
    diagnostics/                # 3 个诊断模块（不计核心分）
  schemas/
    module.schema.json
    catalog.schema.json
    release.schema.json
    compatibility.schema.json
  releases/
    locks/
    packages/
    routing/
  tools/
    validate_bank.py            # schema/ID/锚点/重复/替换/冲突/覆盖矩阵
    compose.py                  # 确定性组合（quick/full，含 replacements）
    diff_bank.py                # 两版本语义 diff 与兼容分类
    simulate_upgrade.py         # 升级/退役/历史读取反例
    audit_bundle.py             # 生成三份审计材料
  tests/
  docs/
    bank-design.md              # 统一设计
    version-policy.md           # 版本与兼容政策
    migration.md                # 迁移/退役/历史读取
    audit-criteria.md           # 三审计的验收标准
  review/
    content/                    # 独立内容审计
    format/                     # 独立格式审计
    architecture/               # 独立架构审计
  docs/handoff/QUESTION-BANK-UPGRADE-12/
```

### 4.2 内容交付

- `catalog.json`：48+ 模块，逐模块记录 `id/kind/version/name/applies_when/axis/activation/scope/dependencies/conflicts/status/path/question_count/content_sha256`。
- 每个模块一份 JSON：题目 `id/dimension/priority/question/evidence/anchors/counter_evidence/replaces/construct_id/comparison_role/rubric_version/scope`。
- 逐模块决策表：`KEEP / REWRITE / NEW / RETIRE` + 理由 + 影响的旧题 ID。
- 覆盖矩阵：8 类型 × 21 行业 × 7 阶段 × 8 属性 × 3 诊断，每格至少有一个模块负责；`other` 明确标覆盖缺口。
- 内容标准：
  1. 决策相关：答“是/否/多少”能改变投资判断；
  2. 可观察：公开披露/搜索能取得证据，不要求内部数据；
  3. 可证伪：每题有反证条件/失效信号；
  4. 不重复计分：同一经济机制只能有一个核心题；扩展题必须说明增量信息；
  5. 锚点可校准：1/5/10 三档边界互斥，8 分以上要求多期或可比证据；
  6. 类型会计正确：银行/保险/REIT/开发商/控股/商业化前必须替换会计冲突题；
  7. 反证必填：高风险/核心题要求 `counter_evidence` 字段。

### 4.3 格式交付

- 不可变题目 ID：核心 `IQS_01..24`；模块命名空间 `BANK_*`、`AUTO_*`、`SCALING_*` 等；全局唯一。
- 题义变更禁止同 ID 改写：必须新 ID + `supersedes` + 旧 ID 进入 `retired_question_ids` 墓碑；旧题永久可读。
- `anchors` 恰为 `{"1","5","10"}`，整数且严格递增；`evidence` 3–7 条；`replaces` 只允许 types 模块引用核心 `IQS_*` 构念。
- 模块 `version`：semver；patch=元数据/文案不影响题义；minor=新增题；major=适用范围/锚点/题义变化并退役旧题。
- catalog/release 规范序列化：键排序、UTF-8、无 NaN、字节稳定、内容 hash。
- 提供 `validate_bank.py` 的正反例，拒绝：重复 ID、缺字段、锚点缺档、非法 replaces、跨模块重复题、冲突未声明、覆盖矩阵空洞、同 ID 改义。

### 4.4 架构交付

- 分层：`content`（题文/证据/锚点）→ `routing`（applies_when/activation）→ `composition`（deps/conflicts/replacements）→ `scoring`（construct/role）→ `release`（locks/hashes）→ `presentation`（renderer/contexts）。
- 模块只依赖 schema，不 import 其他模块；组合器只读 catalog/release。
- 依赖图闭合：缺依赖、依赖未决、环、冲突、同核心题双替换 → fail closed，不产出半成品。
- 评分分离：核心 24 分母与模块 context 分分开；types 替换保留 construct，但跨类型比较必须标 `same_construct_different_instrument`。
- 发布：release lock 记录每个模块版本/内容 hash/题义指纹；package 绑定 lock + renderer + scoring contexts；active 指针独立。
- 历史读取：旧 manifest/旧观察按旧版本解释；新派发只用当前 active；不能拿当前 catalog 重算旧题。
- 兼容分类：`comparable / new_question / replaced / incomparable / blocked`，由 `diff_bank.py` 输出并带原因。
- 升级模拟：`simulate_upgrade.py` 必须覆盖新增模块、minor、major、退役、冲突、旧 manifest 读取、旧观察可读、不可比标记。

### 4.5 版本管理政策（必须成文并机器校验）

- `catalog_version`：整库 semver；新增模块 minor，退役/改适用 major。
- `module_version`：模块 semver；题目 ID/题义/锚点/适用变化必须 major + 退役旧 ID。
- `question.rubric_version`：单题口径版本；题义变化必须新 ID。
- `release_id`：内容寻址；lock 记录逐模块 hash；package 记录 lock + renderer + contexts hash。
- 生命周期：`draft → candidate → active → deprecated → retired`；只追加，不改历史。
- 回退：仅当目标 release 全部组件仍有新派发资格且兼容矩阵成立；否则只读。
- 迁移：旧 ID → 新 ID 的 `supersedes` 表；未覆盖的旧题进入墓碑；比较工具必须输出 `incomparable` 原因。
- 版本反例：同 ID 改题义、删除未退役 ID、复用退役 ID、无 lock 的 release、跨版本重算旧分，全部拒绝。

## 5. 三个独立审计（本包硬门槛）

作者不得自审。三个审计必须是**不同 agent**，各自只拿到冻结候选包 + 审计标准；作者修复后由原审计者复核。

### A. 内容审计（content）

审：决策相关性、可观察性、可证伪/反证、重复计分、锚点校准、证据关注是否足够、类型会计正确性、行业/阶段/属性题的增量信息。

产出：`review/content/round-01.json`（逐条 finding：id、severity、问题、证据、建议）、`content/final.json`（verdict=passed|changes_requested、open_findings、复核记录）。

### B. 格式审计（format）

审：schema 闭合、ID 唯一/命名空间、锚点 1/5/10、evidence 数量、replaces 合法、construct/role、版本字段、模块元数据 vs catalog、重复题面、确定性序列化、validate 正反例覆盖。

产出：`review/format/round-01.json`、`format/final.json`；必须附 `validate_bank.py` 的正例/负例日志。

### C. 架构审计（architecture）

审：分层是否真的解耦、模块是否独立、catalog/release/lock/hash 是否闭合、组合是否 fail closed、版本/退役/历史读取是否可执行、核心与 context 分是否分开、升级模拟是否覆盖、旧观察/旧 manifest 是否可读。

产出：`review/architecture/round-01.json`、`architecture/final.json`；必须附一次“新增模块 + 一次 major 改版 + 一次退役”的模拟日志与旧包读取日志。

每个 final 必须是：`verdict`、`open_findings`、`reviewed_commit`、`invocation_evidence`、`limitations`。任何 P0/P1 未关闭 → 不得判 passed。

## 6. 验收用例

| ID | 必须证明 |
|---|---|
| AC-01 | catalog+全部模块通过 `validate_bank.py`；≥48 模块、≥222 题；每个模块有 KEEP/REWRITE/NEW/RETIRE 决策 |
| AC-02 | 所有题目 ID 全局唯一；锚点恰为 1/5/10；evidence 3–7；核心题有反证要求 |
| AC-03 | 8 类型全覆盖；types 的 replaces 只指向核心 IQS 构念；无同一核心题被两个类型模块同时替换 |
| AC-04 | 组合 quick/full 确定性；type 恰好 1、stage 恰好 1、industry 0–2；冲突/依赖/环 fail closed |
| AC-05 | 新增模块只产生新题；minor 不改旧题；major 退役旧 ID 并给唯一后继；旧 manifest 仍可读 |
| AC-06 | 旧观察/旧 manifest 按旧版本可读；新派发只用 active；不可比项输出原因，不覆盖旧分 |
| AC-07 | `diff_bank.py` 对两版本输出 comparable/new/replaced/incomparable/blocked 分类 |
| AC-08 | 三个审计 final 均为 passed，或 changes_requested 已修复并复核；无未关闭 P0/P1 |
| AC-09 | 零网络、零模型、零付费：代码无 HTTP/模型客户端，测试日志证明；临时根清理 |
| AC-10 | handoff 形状通过主控 CLI；worktree clean；作者/审计者身份与 commit 可追溯 |

## 7. 交接文件集

```text
docs/handoff/QUESTION-BANK-UPGRADE-12/
  handoff.json            # schema: docs/implementation/parallel-lanes/handoff.schema.json#1.0.0
  artifacts.json          # 逐文件 bytes + sha256（repo 根相对路径）
  tests.json              # 命令、通过/失败/跳过、日志路径
  cleanup.json            # 临时根创建/清理
  summary.md
  report.md
  review/content/{round-01.json,final.json}
  review/format/{round-01.json,final.json}
  review/architecture/{round-01.json,final.json}
  logs/                   # validate/compose/diff/simulate/audit 的命令输出
```

handoff 必须声明：package_id、result_commit、worktree_before/after、verification checks、review verdicts、open_items、next_action（主控验收）。

## 8. 约束与禁止捷径

- 只能写自己的 lab 仓库；不得改 `invest-quick-scan` 主线、不得写 owner/StockWiki/StockQA。
- 零网络、零模型、零付费；不得抓页面、不得伪造来源。
- 不得复制旧题面后声称已升级；每个模块必须有审阅记录与变更理由。
- 不得用“新增题”稀释核心 24；核心构念冻结，类型替换保留 construct。
- 不得把 context 题计入核心均分；不得静默改分母。
- 不得自审；三个审计必须不同 agent，且作者不能参与审计报告撰写。
- 不得跳过 hooks、不得 `--no-verify`；提交信息要能追溯到本卡。

## 9. 风险与开放问题

1. **内容质量主观**：用“可观察/可证伪/反证/不重复”四条件降低主观性；审计必须给逐题证据。
2. **题量膨胀**：升级后题量允许增加，但必须证明增量信息；quick 模式仍需可截断并保留待办。
3. **类型会计**：银行/保险/REIT 的替换题必须与当地会计口径一致；审计需给依据。
4. **版本迁移**：旧 ID → 新 ID 映射必须完整；无法映射的旧题进入墓碑并标不可比。
5. **行业覆盖**：21 行业之外的公司用 `other`，必须明确是覆盖缺口，不能伪装精确分类。
6. **与主线的接口**：主控只接受 release lock 导入；不接受 lab 直接改主线 catalog。

## 10. 参考

- `docs/modular-question-bank-design.md`
- `docs/implementation/composable-evolution-plan.md`
- `docs/contracts/question-modules.md`
- `questions/catalog.json`、`questions/releases/locks/modrel_18c097b…json`
- `questions/routing-policy.v2.json`
- 基线组合实测：CATL `operating+auto+scaling+concentrated` quick 29 / full 37（2026-10-19，本会话）
