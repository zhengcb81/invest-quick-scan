# BASIC-BANK-EXPANSION-21｜基本题库扩张与去硬编码「24 核心题」重构

- 日期：2026-10-24（晚）
- 来源：所有者裁定（原话见 [OWNER-RULINGS-R3.md](OWNER-RULINGS-R3.md) §0.4–0.7）
- 性质：**设计输入卡**。所有者明确要求「先收尾本项目，把该重构另作一卡，或交接给主线另行派发/自行实施」
- 写范围（建议）：主仓 `invest-quick-scan`（scripts/tests/docs/schemas/questions 数据）+ 银行 lab 镜像；applic/UI 视需要
- 前置：无（与本批 R3-1/R3-2/R3-3 的发布契约修订兼容；新卡实施后按需再发布一次）

## 0. 所有者原话

> 「还有一个办法，把杜邦和波特的题目直接加到基本题库，不是就解决了吗？」
>
> 「必须恰好是 24 个核心题是很奇怪的限制，不应该有，基本题库要允许自身的升级和扩张。」
>
> 「我从来没有在最初设计里提过这样的要求，项目架构和设计也不应该依赖于一个硬编码的数字。」
>
> 「这样吧，你把本项目先收尾，然后把这个重构另作一个卡，或者交接给主线，让它另外派发或自己做。」

## 1. 问题（现状取证）

主仓当前把「24 个核心题 = IQS_01..IQS_24」**硬编码**在架构里（不是所有者最初设计要求）：

| 位置 | 内容 | 影响 |
|---|---|---|
| `scripts/module_contract.py` | `CORE_IDS = frozenset(IQS_01..IQS_24)`；`validate_module` 要求 common **恰好**这 24 个 ID；types 的 core 替换靶子必须是 CORE_IDS 成员 | 基本题库无法增加/删减任何题（连诊断题都不行），也无法把新题并入 common |
| `scripts/question_sets.py` `validate_library` | `len(common_ids) == 24` 断言 | 数据一改就红 |
| `scripts/question_sets.py` `summarize`（`core-constructs-v1`） | `len(constructs) != 24 or set != {IQS_01..24}` | 固定比较依赖数字与固定 ID 列表，而非发布包的核心构念集合 |
| `scripts/routing.py` | 派发计划 `minimum_questions == 24 + len(mandatory)` | 核心题数写死 |
| `scripts/scoring_rubrics.py` | `CORE_DIMENSIONS`（IQS_01..24 → 维度）；basket 校验要求恰好这 24 项、维度按硬编码映射 | rubric 发布被 24 锁死 |
| 银行 lab `tools/validate_bank.py` | common 必须恰好 24 题 / 核心 ID 列表 | 跨仓镜像同一限制 |
| UI（生成数据/展示） | 构念数、矩阵列等按 24 呈现 | 银行扩张后 UI 需自适应 |

## 2. 设计（核心原则：**从数据派生，不写死数字**）

1. **核心构念集合 = 发布包 `common` 模块中 `comparison_role == "core"` 的题**（在 registry/release 级派生一次，
   传给校验函数；任何代码不得再出现 `24`、`range(1,25)`、`IQS_24` 之类的固定列表）。
2. **common 内容契约**：
   - 必须包含 ≥1 个核心构念；核心题必须 `construct_id == id`、`comparison_role == "core"`、无 `replaces`；
   - **允许追加扩展题**：必须 `aggregation == "diagnostic"`、`comparison_role == "diagnostic"`、
     `construct_id == null`、无 `replaces`（即"只做诊断、不进核心固定比较、不进质量汇总"）；
   - 扩展题可以来自任何框架（dupont/porter/自定义），不改变核心分母。
3. **版本/升级规则**（在现有 `validate_upgrade` 上扩展，保留既有不可变量）：
   - 追加扩展题：minor 即可；
   - 删除扩展题：minor 即可，但必须有 `retired_question_ids` 墓碑（ID 永不复用）；
   - 增删/替换**核心构念**：仍需 major + 后继 ID 映射（与今天一致，保证历史可比）；
   - 同 ID 题面/anchors 永不可变（不变）。
4. **固定比较**：`summarize('core-constructs-v1')` 改为「每个发布版核心构念恰好一行；集合与发布包一致」——
   由调用方（manifest/release）把核心集合传入；无发布包时退化为「核心行唯一且非空」。
5. **路由最小题数**：`minimum_questions = 派生核心数 + len(mandatory)`。
6. **rubric**：`validate_rubric` 接受可选 `core_constructs`（来自题库的 构念→维度 映射）；未提供时只做内部一致性
   （唯一、维度合法、权重 100），`expected_core` 由 basket 长度派生。
7. **跨仓镜像**：银行 lab 同一套规则（其 `validate_bank` + 一致性测试）；UI 从生成数据读取构念数（不写死）。

## 3. 改动清单（供派发）

| # | 文件 | 改动 |
|---|---|---|
| M1 | `scripts/module_contract.py` | 删除 `CORE_IDS`；新增 `core_construct_ids(common_module)`；`validate_module(module, *, core_ids=None)`；`validate_registry` 派生并传入；`validate_upgrade` 增删扩展题规则（minor + tombstone）；types 替换靶子按派生集合校验 |
| M2 | `scripts/question_sets.py` | `validate_library`：去掉 `==24`；核心题 priority/唯一性按派生集合断言。`summarize`：去掉 24/固定 ID；支持 `core_ids` 参数（normalize 传入发布包核心集） |
| M3 | `scripts/routing.py` | `minimum_questions` 派生；测试同步 |
| M4 | `scripts/scoring_rubrics.py` | `CORE_DIMENSIONS` 改为可选参数/派生；`expected_core` 由 basket 派生 |
| M5 | 主仓 tests | 更新所有 `range(1,25)`/24 断言为派生；新增扩张/删减/升级正反例 |
| M6 | 银行 lab（`iqs-question-bank-lab`） | `tools/validate_bank.py` 同规则；`banklib`/测试；`build_bank` 生成；catalog/release 重建 |
| M7 | UI lab（`iqs-question-bank-ui-lab`） | 构念数/矩阵列从生成数据派生；图例说明"核心 + 诊断扩展" |
| M8 | docs | 设计契约文档（`docs/modular-question-bank-design.md` 等）+ 本卡 report |

## 4. 验收用例

| ID | 用例 | 期望 |
|---|---|---|
| AC-01 | 现状数据（24 核心、无扩展） | 所有既有测试绿；快照/组装/manifest 与改动前**逐字节相同**（无银行扩张时零行为变化） |
| AC-02 | 在 common 追加 1 道诊断扩展题（minor） | `validate_registry`/`publish` 通过；组装包含该题；`summarize` 核心分母仍为 24（核心集合不变）；`method_id` 不变 |
| AC-03 | 删除该扩展题（minor + tombstone） | 通过；无 tombstone → 拒绝；替换/删除**核心**题（minor）→ 拒绝（须 major + 后继） |
| AC-04 | 硬编码清除 | 全仓 grep：除**测试数据/历史快照**外，`scripts/` 不再出现 24/`range(1,25)`/`IQS_24` 等固定列表 |
| AC-05 | 路由/评分派生 | `minimum_questions`、`expected_core` 随银行规模变化 |
| AC-06 | 跨仓 | 银行 lab `validate_bank` + 测试绿；UI 生成数据含新构念数且显示无硬编码 |
| AC-07 | 回归 | 主仓全量、applic 链（如需新锁）、UI/银行测试全绿；发布一个含扩展题的包（可选演示） |

## 5. 门禁

- **G1**：本卡即设计输入（所有者原话见 §0）；
- **G2**：**无新增语义裁定**——若实施中发现"扩张后固定比较如何对齐历史答案"等新语义问题，停问所有者；
- **G3**：TDD（先写 AC-02/AC-03 反例测试）；
- **G4**：独立审查（重点：无静默行为变化、历史可比性、跨仓一致性）；
- **G5**：所有者签收；
- **G6**：交接套件 + 主控 CLI `--verify-references` exit 0。

## 6. 风险 / 非目标

- **R1 历史可比性**：核心构念不变时历史答案可比；核心变更仍须 major+后继（本卡不改变这一点）。
- **R2 method_id/评分**：`method_id` 只哈希 core 行，扩张不改变；质量汇总只统计非 diagnostic 行，扩张题不进汇总。
- **R3 跨仓漂移**：银行 lab 与 UI 必须同批改，否则同一扩张在主仓/银行/UI 表现不一致。
- **非目标**：不改变 24 个核心构念的**内容**（题面/锚点/anchor 语义）；不迁移历史答案；不重做评分模型；
  不把现有 dupont/porter 模块的题 ID 迁入 common（题 ID→模块归属对历史不可变；本卡只开放"新增"）。
