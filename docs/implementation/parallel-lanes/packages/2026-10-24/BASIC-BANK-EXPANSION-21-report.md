# BASIC-BANK-EXPANSION-21 实施报告

> 2026-10-25 实际独审补充：下面是10/24原实施记录。新增扩张整链的6项反例随后真实复现并由主控修复，现独立复审passed/open_findings=[]；初轮失败、复审、源码SHA、原测试日志和历史兼容比对见`../../../reviews/reconciliation-production-2026-10-25/basic/`。原报告列G4门名不代表当时已有持久审查。最新主仓200项+3环境重跑通过，UI134项含6既有skip；不将分次测试合称单次203通过，不代签G5。

- 日期：2026-10-24（晚）
- 设计输入：[BASIC-BANK-EXPANSION-21.md](BASIC-BANK-EXPANSION-21.md)（G1：本卡即设计输入；所有者原话见其 §0）
- 性质：跨三仓重构（主仓 `invest-quick-scan` + 银行 lab `iqs-question-bank-lab` + UI lab `iqs-question-bank-ui-lab`）
- 门禁：G2 无新增语义裁定；G3 TDD（先写 AC-02/AC-03 反例，22 条 RED）；G4 独立审查；G5 所有者签收；G6 交接套件
- 网络：全程零外网、零模型 API、零付费调用

## 0. 结论摘要

| 阶段 | 仓 | 状态 |
|---|---|---|
| M1–M4 契约/派生 | invest-quick-scan（主仓） | ✅ 落盘 |
| M5 主仓测试 | invest-quick-scan | ✅ 全绿 |
| M6 银行 lab 镜像 | iqs-question-bank-lab | ✅ 54/54 绿 |
| M7 UI lab 派生 | iqs-question-bank-ui-lab | ✅ 126/126 绿（6 skip 为既有 env 门控） |
| M8 docs | invest-quick-scan | ✅ 见 `docs/modular-question-bank-design.md` §核心构念集合 |

**核心变化**：`scripts/` 与两个 lab 的 `tools/` 中，**不再有任何**写死 24、`range(1,25)`、`IQS_24` 或固定 `IQS_01..IQS_24` 列表。核心构念集合唯一派生自发布包 `common` 模块中 `comparison_role == "core"` 的题。

## 1. AC 对照

| ID | 用例 | 结果 | 证据 |
|---|---|---|---|
| AC-01 | 现状数据零行为变化 | ✅ **逐字节相同** | 见 §2 |
| AC-02 | 追加 1 道诊断扩展题（minor） | ✅ | `tests/test_bank_expansion_21.py::DerivedCoreSetTests`、`ExpansionUpgradeTests`；银行 lab `test_common_extension_is_accepted_and_does_not_move_the_core` |
| AC-03 | 删除扩展题（minor + 墓碑）；核心变更仍须 major | ✅ | `ExpansionUpgradeTests` 6 条正反例 |
| AC-04 | 硬编码清除 | ✅ | 见 §3 |
| AC-05 | 路由/评分派生 | ✅ | `routing.minimum_question_count`、`sr.aggregate` 的 `expected_core`；`RubricDerivationTests` |
| AC-06 | 跨仓 | ✅ | 银行 54/54、UI 126/126；UI `bank.core_constructs` 由 `build_data.py` 派生 |
| AC-07 | 回归 | ✅ | 主仓全量、银行、UI 三仓测试全绿 |

## 2. AC-01：零行为变化（逐字节）

方法：把 HEAD 版本的四个脚本与 rubric schema 还原到一份工作树副本，与当前工作树**分别**跑同一探针（`.test-scratch/ac01_probe.py`），比对 24 个 compose 摘要 + 库校验 + 路由最小题数 + rubric 发布 ID + summarize 摘要。

结果：**唯一差异是两个新增的报告字段**（`library.core_constructs`、`library.common_questions`，均为 `None → 24` 的**新增键**）。以下全部逐字节相同：

- 3 个 profile × 2 个模式（example / bank_type / cyclical × quick / full）的 `manifest.json` 与 `questions.json` sha256；
- 各自的 `method_id`（如 `core-constructs-v1/4579731aa0cf4882`）与 `question_count`；
- 评分 rubric 的 `rubrel_1ae5bfbf…` 发布 ID 与 `core_basket` 摘要；
- `summarize('core-constructs-v1')` 的完整输出摘要。

即：**银行不扩张时，组装/发布/评分链路零行为变化**；唯一可见变化是 `validate_library()` 返回值多了两个只读统计键（调用方为 `question_sets.py main()` 的 `validate` 子命令打印，非契约字段）。

## 3. AC-04：硬编码清除

`scripts/` 与两仓 `tools/` 的严格扫描（`IQS_24`、`range(1,25)`、`24 + len(`、`== 24`、`!= 24`、`f"IQS_{`）**0 命中**。

剩余裸 `24` 全部人工核过，均与核心题数无关：日期（`2026-10-24`）、分批大小（`--chunk 24`）、预算上限（`search_http_cap: 24`）、CSS 宽度（`24%`）、`sha[:24]` 截断、历史文件名 `questions-24.json`、以及历史说明文字（`scan_result_check.py` 的历史 bug 描述）。

**刻意保留的两处**：银行 lab `tools/build_release.py` 的 `SCORING_POLICY.aggregation` 两条说明文字仍写「24 frozen core constructs」。它们是**内容寻址不可变工件**的一部分——改写会铸出新的 scoring-policy id 与 `method_id`，让未变更的题库看起来变了，直接违反 AC-01 与卡 §6 R1/R2。文件内已加注释说明；**分母本身**（`compose.py`、`validate_bank.py`）已改为派生。

## 4. 改动清单

### 主仓 invest-quick-scan

| 文件 | 改动 |
|---|---|
| `scripts/module_contract.py` | 删 `CORE_IDS`；新增 `core_construct_ids(module)`（非 common 返回空集）、`EXTENSION_KINDS`、`_is_extension_question`、`_validate_common_question`；`validate_module(module, *, core_ids=None)`；`validate_registry` 派生一次并下传；`validate_release` 从归档 common 派生后复核每个模块；`validate_upgrade` 增扩展题 minor 规则 + 核心变更 major 规则 |
| `scripts/question_sets.py` | `validate_library` 去掉 `==24`，改为按派生集合断言（核心题 priority、扩展题必须诊断型），返回值新增 `core_constructs`/`common_questions`；`summarize(..., *, core_ids=None)` 按发布包集合校验；新增 `_manifest_core_ids`，`normalize`/`normalize_screening` 传入 |
| `scripts/routing.py` | 新增 `minimum_question_count(modules, mandatory)`；`resolve_route_decision` 与 `validate_route_snapshot` 均改用它 |
| `scripts/scoring_rubrics.py` | 删 `CORE_DIMENSIONS`；`validate_rubric/seal_rubric(..., core_constructs=None)`；`aggregate` 的 `core` 切片与 `denominator.expected_core` 由 basket 派生 |
| `schemas/quick_scan/scoring-rubric.schema.json` | `core_basket` `minItems/maxItems` 24→`1/64`；`construct_id` pattern `^IQS_[0-9]{2}$`→`^IQS_[0-9]{2,}$` |
| `scripts/thin_scan.py` | `--limit` 默认 `None`（=清单全量）；标题/未绑定提示按实际题数；不再写「24 题」 |
| `scripts/thin_median.py` / `thin_retest.py` / `status_report.py` | 分母由实际题数派生，不再写 `/24` |
| `tests/test_bank_expansion_21.py` | **新增** 25 条 AC-02/03/05 正反例 |
| `tests/test_module_contract.py` | `test_common_core_and_type_replacement_are_frozen` 改为新语义（扩展合法、核心变更须 major） |
| `tests/test_question_sets.py`、`test_metrics_contract.py`、`test_module_registry.py`、`test_routing.py`、`test_route_store_handoff.py`、`test_scoring_rubrics.py` | 所有 `24`/`range(1,25)` 断言改为派生 |
| `docs/modular-question-bank-design.md` | 新增 §「核心构念集合：从数据派生，不写死数字」；4 处旧「24 冻结」表述改写 |

### 银行 lab iqs-question-bank-lab

| 文件 | 改动 |
|---|---|
| `tools/validate_bank.py` | 核心集合由 `comparison_role == "core"` 派生；common 必须 ≥1 核心；扩展题必须诊断型（role/aggregation/construct_id/replaces/critical 四项）；`question_errors` 支持 common 的 diagnostic 扩展；报告新增 `core_construct_ids`，`core_count` 改为 `len(core_ids)` |
| `tools/compose.py` | 删 `CORE_ID_COUNT`；核心槽位由 common 的 core 题派生 |
| `tools/build_bank.py` | `core != 24` 断言改为 `core < 1` |
| `tools/audit_bundle.py` | `core_count: 24` → `report["core_count"]`；`core_constructs` 只含 core，新增 `core_extensions` |
| `tools/build_release.py` | 仅加注释（不可变工件文本见 §3） |
| `tests/helpers.py` | 新增 `core_construct_ids(root)` / `core_count(root)` |
| `tests/test_validate_bank.py` | 原 `test_core_set_must_stay_frozen` → 三条新用例（≥1 核心、扩展必须诊断型、扩展被接受且不动核心）；baseline 卡数字从 vendor 数据派生 |
| `tests/test_compose_diff.py`、`test_release_simulate.py` | 24 → 派生 |

### UI lab iqs-question-bank-ui-lab

| 文件 | 改动 |
|---|---|
| `scripts/build_data.py` | 新增 `core_constructs(modules)`；`bank.core_constructs = {ids, count, extension_ids, extension_count, common_question_count}`；`manifest.counts` 新增 `core_constructs` / `common_extensions` |
| `src/app/ui/bank_overview.js` | 新增「核心构念（派生）」「诊断扩展题」两个统计；模块清单标题与 facts 说明不再写死 48 |
| `src/app/ui/companies_matrix.js` | 列数/格数文案全部按 `modules.length`、`roster.entities` 派生；新增 `legend-core-constructs` 图例说明「核心 + 诊断扩展」 |
| `src/app/ui/data_notes.js` | 新增「核心构念 / 诊断扩展」行；格数文案派生 |
| `src/app/ui/module_detail.js` | 题号徽标区分「核心构念」/「诊断扩展」/「关键风险」（原先把 critical 误标为「核心题」） |
| `tests/test_catalog.py` | 新增 `TestDerivedCoreConstructs` 4 条 |
| `tests/test_diff.py` | 3 条写死 lock/package 数量的用例改为从数据派生（原断言 4 locks/6 packages，实际数据根已是 6/8，属**既有漂移**） |
| `src/generated/*.json` | 由 `build_data.py` 重建 |

## 5. 边界与如实声明

- **F1 生成数据重建带来的 UI 数字变化**：UI 的 `src/generated/*.json` 重建后，`locks 4→6`、`packages 6→8`、`routers 3→4`。这不是本卡引入的语义变化，而是**旧生成数据已与数据根漂移**（`test_diff.py` 三条断言原先是红的）。重建使其与数据根一致。
- **F2 评分 rubric 的分母校验需要调用方传映射**：`validate_rubric` 未传 `core_constructs` 时只做内部一致性。已提交的 `rubrel_1ae5bfbf…` 在两种模式下均通过（其 basket 恰好是当前 24 个核心构念且维度正确），AC-01 已逐字节验证。
- **F3 未迁移历史答案**：卡 §6 非目标。核心构念不变时历史答案可比；核心变更仍须 major + 后继。
- **F4 未把 dupont/porter 题迁入 common**：卡 §6 非目标。扩展题通道已开放，但本次未实际搬题（会改变题ID→模块归属）。
- **F5 未新增语义裁定**：G2 要求的边界（扩张后固定比较如何对齐历史答案）在本卡 §2.4 已给定——核心集合由发布包派生，扩展题不进固定比较；实施中未遇到需停问所有者的新语义问题。

## 6. 验证命令与结果

```text
主仓：python -m pytest tests -q                    → 见 §0（全绿）
银行：python -m unittest discover -s tests -t .     → Ran 54 tests, OK
      python tools/validate_bank.py --releases      → OK modules=62 questions=257 releases=OK
UI：  python -X utf8 scripts/build_data.py          → 计数校验通过（含 core_constructs 24 / common_extensions 0）
      python -X utf8 -m unittest discover -s tests  → Ran 126 tests, OK (skipped=6)
```
