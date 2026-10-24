# OWNER-RULINGS-R3｜2026-10-24 追加裁定与交接说明（发布契约 / 路由默认诊断 / 基本题库扩张）

- 日期：2026-10-24（晚）
- 性质：**所有者裁定记录 + 交接说明**。本文件是后续 lane / 主线派发的设计输入，裁定内容以 §0 原话为准
- 关联：[RULE-SCOPE-DECISION-19.md](RULE-SCOPE-DECISION-19.md)、[RULE-SCOPE-DECISION-19-review.md](RULE-SCOPE-DECISION-19-review.md)、
  [APPLIC-LLM-JUDGE-20-R2.md](APPLIC-LLM-JUDGE-20-R2.md)、新卡 [BASIC-BANK-EXPANSION-21.md](BASIC-BANK-EXPANSION-21.md)

## 0. 所有者原话（逐字，2026-10-24）

1. **LLM 匹配简化（R2）**：
   > 「一个公司是否与某一个题库匹配的逻辑太复杂了，如果第一轮LLM里面有大多数说这个公司与某个题库是匹配的，
   > 就认为匹配就好了，不用再复核或调用其他复杂逻辑了。我不介意在每个题库的公司池里多增加几家公司，没有什么坏处的。」
2. **选项 1（发布契约阻断）**：[复核报告 §7](RULE-SCOPE-DECISION-19-review.md) 的三选一 → 所有者选择 **B** 并授权重构：
   > 「1，B，做，该重构就重构」
3. **选项 2（路由默认诊断）**：所有者选择 **做**：
   > 「1，B，2，做，该重构就重构」
4. **基本题库扩张（首次提出）**：
   > 「还有一个办法，把杜邦和波特的题目直接加到基本题库，不是就解决了吗？」
5. **24 核心题限制**：
   > 「必须恰好是 24 个核心题是很奇怪的限制，不应该有，基本题库要允许自身的升级和扩张。」
6. **架构原则**：
   > 「我从来没有在最初设计里提过这样的要求，项目架构和设计也不应该依赖于一个硬编码的数字。」
7. **收尾与分卡**：
   > 「这样吧，你把本项目先收尾，然后把这个重构另作一个卡，或者交接给主线，让它另外派发或自己做。」
8. **本文件要求**：
   > 「你要把我上面的选择和要求明确的写到交接文档里。」

## 1. 裁定与落地状态

| # | 裁定 | 状态 | 落地内容 |
|---|---|---|---|
| **R3-1** | 发布契约按 **方案 B**：`applies_when`（适用条件说明）允许**就地修订**，前提是**至少 minor 版本升版**；题面/anchors/题 ID 仍绝对不可变（同 ID 内容改动一律拒绝）。patch 升版或无升版仍须走后继题 ID | ✅ 已实现 | `scripts/module_contract.py::validate_upgrade` + 新测试（`test_module_contract.py`：3.0.1 变更被拒 / 3.1.0 允许且题面仍不可变）；`_at_least_minor` 辅助函数 |
| **R3-2** | 三模块按 minor 升 **3.1.0** 并重新发布，使新文本进入发布包 | ✅ 已发布 | industrial/dupont/porter = 3.1.0（`introduced_in` 同步）；**v1 包 `pkg_ca11c5c3…`（current，catalog 3.2.1，恢复 profile 驱动流程）**；**v2 包 `pkg_143d610a…`（router 2.4.0，供路由驱动流程）**；两包均含新文本 |
| **R3-3** | **路由驱动组装也默认包含** dupont/porter（不只是 profile 驱动） | ✅ 已实现并实测 | 新路由谓词 `default_diagnostic`（仅 diagnostic 轴可用）+ router **2.4.0**；`questions/routing-policy.v2.json` 两模块谓词更新；路由判定实测：`dupont/porter = selected / policy / default_mandatory`，`dispatch_plan.eligible` 含两者，路由驱动组装 12 道诊断题；`validate_route_decision` 策略基允许组合同步 |
| **R3-4** | 基本题库（`common`）**允许升级与扩张**，去掉"恰好 24 核心题"的硬编码；项目架构不得依赖硬编码数字 | ⏳ **另卡**（`BASIC-BANK-EXPANSION-21`） | 按所有者指示本轮**未**实施：该重构触及 `CORE_IDS` 常量、`summarize` 固定比较、`routing` 最小题数、`scoring_rubrics` 24 构念、以及银行 lab / UI 的镜像约束；需独立卡 + 跨仓验收（见新卡） |
| **R3-5** | 把上述选择与要求写进交接文档 | ✅ 本文件 | — |

> 说明：R3-4 未实施**不是**因为拒绝，而是所有者明确要求「另作一个卡，或者交接给主线」。本轮已把相关的半成品改动**回退**
> （`validate_module` 的 common 扩张、`validate_upgrade` 的非核心删题放宽），避免留下未验收的语义。

## 2. 对本批开放项的关闭情况

| 原开放项 | 状态 | 证据 |
|---|---|---|
| F1 / R-01：真实 `publish()` 被 `validate_upgrade` 阻断 | **已关闭** | 方案 B 落地后：v2 包 `pkg_143d610a…`、v1 包 `pkg_ca11c5c3…` 均发布成功（`publish` 返回 modules=48/questions=222），模块版本 3.0.0+3.1.0 |
| R-02 / F8：v2 路由驱动组装不注入默认诊断 | **已关闭** | router 2.4.0 + `default_diagnostic`；实测 eligible 含 dupont/porter、组装 12 题 |
| R-03：修正组装用冻结 3.0.0 包 | **基本关闭** | 发布包已升级到 3.1.0；如需"新文本端到端"演示，用新包重跑修正 profile 即可（命令见复核报告头注，仅需把 `module_package_id` 指向新包或使用 current） |
| R-07：`current.json` 预存脏态 | **已解决** | 当前指针 = `pkg_ca11c5c3…`（v1，含 3.1.0 新文本），随本轮提交入库 |
| R-04：UI `src/generated/bank.json` 旧文本 | **仍开放**（UI 仓小卡） | 需在 UI 仓以主仓 3.2.1 为数据根重建并提交 |
| R-05：银行 `activation` 文案 / version-policy 例外 | **仍开放**（G5 签收时明示） | 银行 catalog dupont/porter `activation` 仍"按需激活"；version-policy 行文与文本级 4.2.1 的张力 |
| R-06：卡片勘误 | **已记录** | RULE-SCOPE-DECISION-19.md §7（428→856、contract_always 术语、AC-01/AC-02 边界） |
| R3-4：基本题库扩张 / 去硬编码 24 | **新卡** | [BASIC-BANK-EXPANSION-21.md](BASIC-BANK-EXPANSION-21.md) |

## 3. 交接状态（给主线 / 后续 lane）

- **写范围**：本轮只在主仓 `invest-quick-scan` 落地（代码 + 发布制品 + 文档）；applic / UI / 银行三仓**零写入**、工作树 clean。
- **发布制品（新增，append-only）**：
  - v2：`pkg_143d610a…`（release `modrel_4787a297…`，router 2.4.0，policy 新 sha）
  - v1：`pkg_ca11c5c3…`（release `modrel_ac0a18a0…`，current 指针指向它）
  - 三模块新归档 `3_1_0-*.json`、新锁、新策略 `router_2_4_0-*.json`
- **运行时口径**：`load_current` = v1 → plain `compose(profile, …)` 可用且含新文本；**路由驱动流程**必须显式使用 v2 包
  （`module_package_id`），否则会按 v1 走 legacy 路径。
- **applic 侧注意（fail-closed）**：`inputs.lock.rule-scope-19.json` 钉的仍是 **router 2.3.0** 的 policy sha；
  本轮 policy 已变 2.4.0 → 任何 **新的** applic 重建必须**新建输入锁**（旧锁校验会立即失败，这是预期行为）。
  已冻结的 predicate 表/快照/交接不受影响（历史构建）。
- **复跑证据**（可重放）：
  - 发布：`python -B -X utf8 -c "import sys;sys.path.insert(0,'scripts');import question_sets as qs,routing,module_registry as r;print(routing.publish_routing_package(renderer_version=qs.RENDERER_VERSION,renderer_rules_sha256=qs.renderer_rules_sha256(),activate=False))"`（v2；v1 用 `r.publish(router_version='1.0.0',…)`）
  - 路由默认诊断：见 §1 R3-3 实测（路由判定 + `select_questions_for_route` 12 题）
- **验证证据（实测，2026-10-24 晚）**：
  - `pytest tests/test_module_contract.py tests/test_routing.py tests/test_module_registry.py tests/test_route_store_handoff.py` → **59 passed / 23 subtests**
  - `pytest tests/test_question_sets.py` → **69 passed / 174 subtests**
  - `pytest tests/test_standard_answers.py tests/test_c06_authority.py tests/test_c06_release_publish.py`（同批运行）→ 通过
  - 发布实测：v2 `publish` → `{package_id: pkg_143d610a…, release_id: modrel_4787a297…, modules: 48, questions: 222}`；
    v1 `publish` 同形；`load_current` → schema 1.0.0 / catalog 3.2.1 / 模块版本 `{3.0.0, 3.1.0}` / diagnostics 语境 `{dupont, porter}`
  - 路由实测（真包 + 构造 verified facts）：`dupont/porter = selected/policy/default_mandatory`，
    `eligible=[auto, common, dupont, mature, operating, porter]`，`profile.diagnostic_modules=[dupont,porter]`，
    组装模块 `[common, operating, auto, mature, dupont, porter]`、诊断题 **12**；profile 路径 compose 40 题且 DUPONT_01 prompt 含新诊断语境
- **测试**：受影响测试文件见上；全量回归按主仓惯例（单轮 35–50 分钟，所有者已要求不再无谓重跑）。

## 4. 下一步（建议顺序）

1. **BASIC-BANK-EXPANSION-21**（R3-4，本轮新卡）：去硬编码 24、基本题库扩张/升级 + 跨仓镜像；
2. UI 仓重建 `src/generated/bank.json`（R-04）+ 补 LLM basis 图例（既有 open item）；
3. 银行 lab：`activation` 镜像文案（R-05）+ G5 签收时对 version-policy 例外留痕；
4. 若所有者要"新文本端到端"演示：用 v1 包重跑 CATL 修正 profile（去掉 `module_package_id` 覆盖即可）；
5. applic 侧如要重建：新建输入锁（policy 2.4.0）→ 8 步链 → 新快照 + parity → 更新 RULE-SCOPE-19-APPLIC handoff。
