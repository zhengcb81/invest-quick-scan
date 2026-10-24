# RULE-SCOPE-DECISION-19 实施报告（主控）

- 日期：2026-10-24
- 设计输入：[RULE-SCOPE-DECISION-19.md](RULE-SCOPE-DECISION-19.md)（G1：本卡即设计输入；所有者原话见其 §0）
- 性质：跨四仓实施（主仓阶段 A/C + applic lab 阶段 B + UI lab 阶段 D + 银行 lab 阶段 E）
- 门禁：G2 无新增裁定项（两条语义均由所有者原话给定）；G3 TDD；G4 独立审查（主控逐仓核 + 独立审查 agent）；G6 主控 CLI 校验
- 复核：**2026-10-24 复核完成** —— 见 [RULE-SCOPE-DECISION-19-review.md](RULE-SCOPE-DECISION-19-review.md)（主控）与
  [RULE-SCOPE-DECISION-19-independent-review.md](RULE-SCOPE-DECISION-19-independent-review.md)（独立审查）；
  AC-02 复核后改判 **PARTIAL**（profile 驱动路径满足；v2 路由驱动路径为已登记边界），勘误见卡片 §7
- 网络：全程零外网、零模型 API、零付费调用；主仓与各仓写范围严格按卡 §4

## 0. 结论摘要

| 阶段 | 仓 | 状态 | 交付 commit | G6 主控 CLI |
|---|---|---|---|---|
| A 题库目录文本 | invest-quick-scan（主仓） | ✅ 落盘 | `644ae58`（主仓 A/C 内容提交） | n/a（主仓即主控） |
| C 组装默认必选 | invest-quick-scan（主仓） | ✅ 落盘 | `644ae58`（同上） | n/a |
| B 谓词/快照/parity | iqs-applic-lab | ✅ 见 §3 | 见 §3 | 见 §3 |
| D 枚举/文案/图例 | iqs-question-bank-ui-lab | ✅ 完成 | `40d7927`（内容）+ `41be324`（套件） | ✅ exit 0 |
| E 银行 lab 文本同步 | iqs-question-bank-lab | ✅ 完成 | `a1965fb`（内容）+ `c8468a9`/`436ef2c`/`7af4119`/`96bbb4f`（套件与 G6 修复） | ✅ exit 0（修复后） |

验收用例对照（卡 §6）：

| ID | 期望 | 实际 | 判定 |
|---|---|---|---|
| AC-01 | CATL 的 industrial 判定不再 applicable；组装不再含 industrial | applic 侧：industrial 谓词逻辑不变（in[industrial]），CATL 属性 industry=[auto] → 判假 → `unknown`（非 applicable）✅；文本收窄使「电池制造=工业装备」的误读在题库侧被显式排除 ✅。组装侧：新组装不再把 industrial 当默认项；CATL 历史实跑 profile（手工含 industrial）为冻结证据不改写，下一次实跑按新文本重判（见 §5-F5 边界说明） | ✅（判定层面） |
| AC-02 | dupont/porter 恒 applicable（contract_always）且组装默认包含 | 快照 428 格全部 applicable + `common_always_applicable`（§3）✅；**profile 驱动组装**默认恒入（§2）✅；**v2 路由驱动组装**不注入默认诊断（冻结 route 为准，路由策略仍 `user_diagnostic`）——复核判 **PARTIAL**，关闭需新路由策略 + router 升版（§5-F8） | ⚠️ PARTIAL |
| AC-03 | dupont/porter 的 428 格 basis 全部为契约恒适用；总数 10272 不变 | 新快照 10272 格；428 格 dupont/porter basis=`common_always_applicable`；分布与旧快照逐格 state 零变化（applicable 1846 / unknown 8426）（§3） | ✅ |
| AC-04 | 主仓 catalog、applic 谓词 mapped_from、bank lab 4.2.1 三处文本逐字一致 | 主仓 catalog（3.2.1）= 卡片 §1/§2 原文；applic `provenance.mapped_from` 由锁内 catalog 逐字重建（§3）；bank lab 4.2.1 由独立脚本对卡片原文交叉核对 8/8 True（§4） | ✅ |
| AC-05 | 回归全绿；parity state_consistent=true；UI basis 枚举无未知值 | 主仓：见 §6 数字；applic：见 §3；UI：122 项 OK（6 skip 为既有 env 门控）；UI `APPLICABILITY_BASES` 含全部出现值（common_always_applicable 与历史 owner_ruled_always_applicable 均在册） | ✅ |

## 1. 阶段 A — 主仓题库目录文本（含 §4.0 方案 A）

主控实测确认 §4.0 的信任锚约束后按**方案 A** 实施（不轮换信任根）：给 3 个模块补 lifecycle 元数据，使其脱离 legacy 基线字节约束。

| 文件 | 改动 |
|---|---|
| `questions/industries/industrial.json` | `version` 3.0.0→3.0.1；`name`→`工业装备与专用设备`；`applies_when`→卡 §1 全文；新增 `activation`（mode=automatic，required_evidence=[设备或项目交付收入, 安装基数与售后服务收入]，exclude_when=[流程制造（化工、材料、电池、钢铁等）, 无设备或项目交付商业模式]，minimum_confidence=medium）、`dependencies=[]`、`conflicts=[]`、`introduced_in=3.0.1` |
| `questions/diagnostics/dupont.json` | `version` 3.0.0→3.0.1；`applies_when`→卡 §2 全文；`activation` mode=**diagnostic**（对齐 routing.validate_policy 对 diagnostic 轴的 expected_mode）、required_evidence=[同口径财务报表]、exclude_when=[财务因子不具经济含义]；dependencies/conflicts 空；introduced_in=3.0.1 |
| `questions/diagnostics/porter.json` | 同上，required_evidence=[真实市场边界与竞争结构证据]、exclude_when=[市场边界无法界定] |
| `questions/catalog.json` | `version` 3.2.0→**3.2.1**；industrial 条目 name/applies_when 同步；dupont/porter 条目 applies_when 同步 |
| `questions/scoring-contexts.json` | `version` 1.0.0→1.1.0；**新增 `diagnostics` 映射**（dupont/porter 两条）——见 §5-F3（契约必需，非可选） |

- 题面、anchors、rubric_version、question_count 全部未动（48 模块 / 222 题不变）。
- `activation` 取值经交叉验证：`routing.validate_policy` 的「routing policy weakens declared module activation」规则要求 diagnostic 轴模块 mode=diagnostic、industry 轴 mode=automatic，且 activation.minimum_confidence=high 时 rule 必须 high —— 三模块均取 medium + 正确 mode，冻结路由策略（router 2.3.0）校验不受影响。
- 校验：`module_registry.validate_source_registry()` OK（48 模块，catalog 3.2.1）；`question_sets.validate_library()` OK（222 题）。

模块版本取 3.0.1（patch）而非 minor 的理由：本变更被所有者裁定为「文本级」（题面不动），与 catalog 3.2.0→3.2.1 的 patch 口径一致；同时保住 `test_mod_02`（工业模块改内容须先升版再改题）的既有语义。

## 2. 阶段 C — 组装管线默认必选（PIPELINE-AUDIT-17 Q3 选项 A 落地）

| 文件 | 改动 |
|---|---|
| `scripts/question_library.py` | 新增常量 `ALWAYS_APPLICABLE_DIAGNOSTICS = ("dupont", "porter")`（单一真源）；`validate_profile` 新增 `diagnostic_exclusions` / `diagnostic_exclusion_rationale` 校验：只能排除默认必选集成员、不得重复、不得与 `diagnostic_modules` 点名冲突、每个排除必须给理由 |
| `scripts/question_selection.py` | `select_questions`：`selected` 的诊断段 = 显式 `diagnostic_modules` ∪（默认必选集 − `diagnostic_exclusions`）——未显式排除即恒入 |
| `scripts/question_sets.py` | `compose` 的 profile 规范化排序字段加入 `diagnostic_exclusions` |
| `examples/profile.json` | 增加空的 `diagnostic_exclusions` / `diagnostic_exclusion_rationale` 字段（示例即文档） |
| `tests/test_question_sets.py` | 新增 2 个正/反例测试（默认恒入 + 四类非法排除）；翻转 4 个编码旧「诊断选做」语义的断言（见下） |

行为：任何 profile（含完全不写诊断字段的）组装时 dupont+porter 恒入（quick +12 题）；`diagnostic_exclusions:["dupont","porter"]` + 逐条理由可显式排除；点名 `diagnostic_modules` 仍要求 `diagnostic_rationale`（显式请求的举证责任不变）。诊断题 `aggregation=diagnostic`，不进维度均分/质量汇总（`summarize` 既有语义），核心构念恒 24。

**边界（如实声明）**：默认恒入只作用于 profile 驱动的组装（`select_questions`）。v2 路由驱动的组装仍以冻结 route 的 `eligible_module_ids` 为准（`select_questions_for_route`）——冻结路由策略中 dupont/porter 仍是 `user_diagnostic`；把路由谓词改为恒选需要新路由策略制品 + router 升版，不在本卡范围，登记为后续卡候选（§5-F8）。

旧语义断言的翻转（均因所有者裁定直接推翻其前提，TDD 更新）：

1. `test_quick_covers_core_judgments_without_automatic_dupont_or_porter` → 更名 `..._with_default_mandatory_diagnostics`：有 framework 的题恰为 dupont/porter 12 道，核心覆盖/关键风险断言保留；
2. `test_s03_does_not_add_unapproved_bridge_questions_or_auto_diagnostics` → 更名 `..._or_nondefault_diagnostics`：默认诊断恒入，recovery 等非默认诊断与未批准桥接题仍不得自动出现；
3. `test_sc10_...`：48 个类型×阶段组合中 dupont/porter 题数断言 False→恰 12；
4. `test_full_mode_also_requires_a_specific_reason_for_optional_tools`：全量模式 framework 题集合断言 → 恰为 {dupont, porter}。

## 3. 阶段 B — applic lab（谓词 basis 收口 + 重建链）

lane 交付：内容提交 `e8fbfbf3537031486d30d050c6c1f4c6984de0e7`（7 文件）+ 交接套件 `2382aea`（31 文件）；base `4530118`。

- **代码**：`run_eval.py` 的 `contract_always` 分支统一发 `common_always_applicable`；`_contract_reason` 对非 common 模块改为契约文案 `"{module_id} 模块对所有公司恒适用（题库契约规定；所有者 2026-10-24 裁定纳入必做契约，不再依赖单次裁定记录)"`（`rules.owner_quote` 依赖移除）；`rules.py` docstring 记录契约化沿革，`OWNER_DECISIONS` 历史数据未动。
- **选择性 staging（共存纪律）**：`run_eval.py` 同树存在 APPLIC-LLM-JUDGE-20 lane 的未提交 WIP，lane 用 partial patch 仅暂存本包 3 个 hunk（+12/−12，blob 断言 0 处 llm_* 痕迹），并用索引态抽树重建快照证明「提交版代码重建结果 == 提交快照」逐字节相同；另一 lane 的 10 个 hunk 与其全部文件未被 revert/commit。
- **TDD**：`test_redlines.py` 先红（2 failures：owner_ruled ≠ common_always）后绿；历史快照夹具（手工 owner_ruled 格）原样保留且全绿 = 历史兼容证明。
- **重建链**（真实退出码，日志入 `docs/handoff/RULE-SCOPE-19-APPLIC/logs/`）：`verify_inputs` 8/8 ok（新锁 catalog `3e145130…`/15139B 吻合）→ `build_predicates` exit 0：**predicate_version `pred_6ffa4a71…` → `pred_6b258097d0b8…`**（48 规则 = 45 mapped + 3 contract_always；industrial `mapped_from` = 新文本 verbatim）→ `build_attributes` exit 0（attributes_version 不变 `attr_897fecae…`）→ `run_eval` **exit 1（预期：首写 unknown>0）** → 新快照 **`applicsnap_26f494e5e4faf19828c78e7ef10bcdbd563ff303f4f78b8006af8e97b94ee488`**（index 2→3 条；旧快照 `applicsnap_d296…` 前后字节不变）→ `validate` 复跑 exit 0 → `export_ui`（10272 格）→ `parity_check` vs UI `41be324…` exit 0 → `unittest` **298 OK**（交接时点数；基线 297，净 +1；与另一 lane 未提交测试同跑全绿。后续 LLM-JUDGE-20 提交后当前 HEAD 为 323 OK，见复核报告 AC-05/R-08）。
- **AC-03（lane 实测 + 主控独立复核，双方结论一致）**：10272 格；分布新旧完全一致 `{applicable:1846, unknown:8426}`；**逐格 state 变化 = 0**；basis.kind 变化恰 **428 格**（dupont 214 + porter 214，`owner_ruled_always_applicable → common_always_applicable`，reason 无旧原话）；428 格全部 applicable + source=contract。诚实披露：`basis.rule_ref` 因 predicate 内容哈希变化对全部 10272 格换新 `pred_6b258097d0b8` 前缀（重建设计使然）；industrial 谓词仍 `mapped`+`in[industrial]`，CATL 判定仍 `unknown`（非 applicable）✓。
- **parity（主控独立复跑确认）**：`state_consistent=true`、mismatch 0、`ui_repo_writes=0`；basis_gaps 四组全同值映射：`common_always_applicable→common_always_applicable` **642**（214 common + 428 dupont/porter）、`negative_evidence_not_verified` 8409、`predicate_true` 1204、`attribute_unresolved` 17；`known_gaps[0]` = **closed**、`identity_verified=true`。
- 共存披露：另一 lane 执行期间仍在活动（脏项 26→33），最终残余 32 项全部属其 lane；本包 0 项残余。

## 4. 阶段 E — 银行 lab 4.2.1

- 内容提交 `a1965fb`（19 文件）+ 套件 `c8468a9`/`436ef2c` + G6 修复 `7af4119`/`96bbb4f`；base `fd75433`；最终工作树 clean；未 push。
- 三模块文本与主仓 3.2.1 **逐字一致**（lane 侧独立脚本对卡片原文交叉核对 8/8 True；主控 AC-04 复核见 §6）。
- catalog 4.2.0→**4.2.1**；文本经 `build_bank.py` 新增的 authoring override 通道生成（可复现，非手改漂移）；F-1（catalog 条目 vs 模块文件字段 + content_sha256）通过。
- releases/ 红线：**零改写**——按 lab 惯例以 `build_release.py --activate` 追加 3 个内容寻址 artifact、1 新锁、1 新包，`active.json` 可移动指针推进，`lifecycle-log.jsonl` 纯追加 1 行（git diff 证实 12→13）。
- 测试：`unittest` 52 passed / 0 failed / 0 skipped；`pytest` 52 passed（真实日志入 handoff logs/）。
- 登记张力（lane 如实上报，主控认可）：`docs/version-policy.md` 行文写 applies_when 变化应升 major + 退役题目；本卡所有者裁定明确按文本级处理，机器检查不强制该行文 —— 属裁定覆盖政策行文，不弱化任何机器门。残留项：bank catalog 的 `activation` 描述文案仍为「按需激活」（本卡未授权改；属阶段 C/B/D 语义的镜像文案，登记后续小卡）。

## 5. 实施中发现（G4 证据）

- **F1（重要，需所有者/后续卡裁定）主仓未来 publish 被 `validate_upgrade` 阻断**：`module_contract.validate_upgrade` 规定「applies_when 变化且新旧题 ID 相交 → 必须全部换后继 ID」。本卡裁定文本就地变更、题目不动，因此对**真实发布库**执行 `publish_library()` 会报 `module applicability scope change requires successor IDs for all questions`（主控用冻结 3.0.0 归档 × 新源文件实测复现，industrial/dupont 均复现）。测试不受影响（夹具发布在临时根内新建历史，不与真实发布库比对），组合也不受影响（读冻结包）；受影响的只是「下一次真实发布」。三条出路（换后继题 ID / 契约修订 / 接受发布冻结）均超出本卡授权，**未擅自改动 `module_contract.py`**，登记为待所有者裁定项。
- **F2（卡内勘误）**：卡 §4.B.2 的「applicable 增加 428 → 856」与实际快照不符（现行快照 applicable=1846，dupont/porter 本就 applicable）；本裁定的实际效果是 **428 格 basis 换类、逐格 state 零变化**，与 AC-03「428 格 basis 全变、总数 10272 不变」一致。按 AC-03 实施。
- **F3（契约必需改动）**：模块脱离 legacy 集后，`validate_registry` 要求其 kind 在 `scoring-contexts.json` 有非空评分语境；`diagnostics` 映射原本不存在，故新增 dupont/porter 两条（顺带使 `question_prompts.applied_contexts` 已有的 diagnostics 通道生效：新发布的包中诊断题 prompt 会带该语境；冻结包不受影响）。
- **F4（预存脏态，非本轮产生）**：主仓 `questions/releases/current.json` 在本轮开始前即为未提交修改（worktree `pkg_24f07923…` vs git HEAD `pkg_b5a41d8c…`），系前序会话遗留；本轮未触碰、不提交该文件。
- **F5（AC-01 组装边界）**：CATL 历史实跑 manifest（`runs/thin-bank-catl-full-2026-10-22/`）是冻结证据，不改写；industrial 的移除发生在**下一次**按新文本的路由/组装。判定层（applic 快照）已按新文本重建（§3）。
- **F6/F7（lane 登记 + 复核修正）**：银行 lab version-policy 行文张力（见 §4）与 `activation` 镜像文案仍「按需激活」，需所有者 G5 明示例外；UI lab **并非不内嵌 catalog 文本**——其构建产物 `src/generated/bank.json` 仍内嵌 catalog 3.2.0 旧文本且运行时读取，`build_data.py --check` 检测不到此漂移；登记开放项：以主仓 3.2.1 为数据根重建 `src/generated/bank.json` 并提交（另卡）。
- **F8（后续卡候选）**：路由策略中 dupont/porter 仍为 `user_diagnostic`；若要 v2 路由驱动的组装也恒含两模块，需新路由策略制品 + router 升版（另立卡）。

## 6. 验证与数字（主控实测）

### 6.1 主仓全量回归（`python -B -X utf8 -m pytest tests -q`）

| 轮次 | 结果 | 说明 |
|---|---|---|
| 基线（改动前） | **1036 passed / 3 skipped / 755 subtests**（34:14） | 绿 |
| 阶段 A+C 后第 1 轮 | 53 failed / 1033 passed / 711 subtests | 失败全部集中在 2 个编码旧「诊断选做」语义的测试（48 个类型×阶段 subtest + `test_s03_..._auto_diagnostics`）——前提被所有者裁定直接推翻，按 §2 TDD 更新 |
| 第 2 轮 | 3 failed / 1035 passed / 759 subtests | 3 个失败均为本卡合法连带：① `test_applic_llm_probe` 钉了旧 industrial 文本；② `test_module_contract` 的 v1 路由冻结夹具钉了 catalog 3.2.0 时代 release_id；③ `test_mod_17_rehashed_current_catalog_edit_is_rejected` 以 industrial 为 legacy 信任锚靶子（industrial 已按方案 A 脱离 legacy 集）。逐一对齐新事实：probe 断言换新文本；夹具按同一构造函数确定性重封（新 `modrel_856e47d2…`，与该轮测试实算值逐字相同，重封后 `validate_route_decision` 自检 OK）；信任锚反例靶子换成仍留在 legacy 集内的 `software`（信任锚本身零改动） |
| 修复验证 | 3 个文件 **60 passed / 11 subtests** 全绿 | — |
| 定论轮（无并行写入） | **1038 passed / 3 skipped / 759 subtests**（48:32，exit 0） | ✅ 全绿 = 基线 1036 + 本卡净新增 2 个测试；subtests 755 → 759（+4 排除通道反例）。第 3 轮曾出现的 2 个 `test_g0_manifest` 失败系主控在跑测期间写入本报告文件导致的**写竞态**（g0 清单对 `docs/implementation/**` 做逐字节哈希）；g0 单独重跑 **13/13 passed** 证实，非代码缺陷 |

### 6.2 三仓 G6 主控 CLI（`parallel_handoff_cli.py --catalog … --verify-references`）

| lane | handoff | 结果 |
|---|---|---|
| RULE-SCOPE-19-UI | `iqs-question-bank-ui-lab/docs/handoff/RULE-SCOPE-19-UI/handoff.json` | ✅ `{"status":"valid"}` exit **0** |
| RULE-SCOPE-19-BANK | `iqs-question-bank-lab/docs/handoff/RULE-SCOPE-19-BANK/handoff.json` | 首跑 exit 2（`temporary_root_not_cleaned`：`.tmp/tests/` 如实申报 created 未 cleaned）→ lane 实际清理并更新 cleanup/handoff + 刷新 artifacts 哈希（`7af4119`/`96bbb4f`）→ 重跑 ✅ exit **0** |
| RULE-SCOPE-19-APPLIC | `iqs-applic-lab/docs/handoff/RULE-SCOPE-19-APPLIC/handoff.json` | ✅ exit **0** |

### 6.3 主控独立复核（不采信 lane 报告，直接对磁盘重算）

- **AC-04 三方逐字**：主仓 catalog（3.2.1）== 银行 lab catalog（4.2.1）== applic 谓词 `provenance.mapped_from` —— industrial/dupont/porter 的 `applies_when` 与 industrial `name` 全部 `True`（9/9）。
- **AC-03 独立重算**（对 `applicsnap_26f494e5…` 与旧 `applicsnap_d296…` 全量逐格）：cells=10272；分布一致 `{1846,0,0,8426}`；state 变化 0；basis 变化 `Counter({(dupont, owner_ruled→common_always): 214, (porter, owner_ruled→common_always): 214})`；dupont/porter 428 格全部 applicable+common_always。
- **parity 独立复跑**：`state_consistent=true`、mismatch 0、`ui_repo_writes=0`、4 组 basis 全同值（642/8409/1204/17）、known_gaps closed。
- **提交内容审计**：applic `e8fbfbf` 的 `run_eval.py` blob 中 `llm` 痕迹 0 处；`owner_ruled` 仅存 docstring 历史说明 1 处。

### 6.4 各仓测试数字（lane 实测，日志入各自 handoff logs/）

- UI lab：unittest **122 OK**（116 passed/0 failed/6 skip，skip 集与基线完全相同）；`build_data.py --check` exit 0。
- 银行 lab：unittest **52 passed/0 failed/0 skipped**；pytest 52 passed；`validate_bank --releases` 三跑 exit 0；compose 冒烟 36 题 exit 0。
- applic lab：unittest **298 OK**（交接时点数；基线 297，与另一 lane 未提交测试同跑）；提交内容独立树 192 OK；当前 HEAD（含后续 LLM-JUDGE-20 提交）**323 OK**。

## 7. 台账影响（卡 §3）

- `docs/implementation/pipeline-review/review-pack-01.jsonl` **未修改**（append-only）；R003（CATL/industrial，keep_composition，「电池制造业当然是制造业（工业）」）保留原行。
- 注记：**R003 由 D-2026-10-24 裁定取代** —— industrial 收窄为装备制造，CATL（电池电芯）不适用；下一份 pack（pack-02）在两侧一致后不再出现该行。pack-02 需在新快照 + 修正后 CATL/Alphabet 组装之上由 `applic_pipeline_check.py` 重新生成，属后续动作（本轮不伪造 pack 数据）。

## 8. R3 后续变更（2026-10-24 晚，所有者追加裁定）

本报告 §1–§7 是白天交付时点的记录。当晚所有者裁定并落地（详见 [OWNER-RULINGS-R3.md](OWNER-RULINGS-R3.md)）：

1. **发布契约（方案 B）**：`applies_when` 允许就地修订（≥minor 升版），题面/anchors/题 ID 不变 →
   三模块升 **3.1.0**，发布 **v1 包 `pkg_ca11c5c3…`（current）** 与 **v2 包 `pkg_143d610a…`（router 2.4.0）**。
   §5-F1 的「发布阻断」已关闭。
2. **路由默认诊断**：新增谓词 `default_diagnostic`、router **2.4.0**；路由驱动组装与 profile 驱动一样恒含
   dupont/porter（实测 12 题）。§0 AC-02 的 PARTIAL 边界（路由路径）已关闭。
3. **基本题库扩张 / 去硬编码 24**：所有者要求另卡 → [BASIC-BANK-EXPANSION-21.md](BASIC-BANK-EXPANSION-21.md)
   （已登记 `ready_for_dispatch`）；本轮未实施，相关半成品改动已回退。
