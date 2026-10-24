# RULE-SCOPE-DECISION-19 复核报告与交接记录（主控）

- 日期：2026-10-24
- 复核对象：[RULE-SCOPE-DECISION-19.md](RULE-SCOPE-DECISION-19.md)（设计输入/裁定）+ 其 [实施报告](RULE-SCOPE-DECISION-19-report.md)
- 复核方式：**不采信 lane 自报数字**；全部关键数字由主控对磁盘/git 对象独立重算（脚本与命令见各节），并另派
  **独立审查 agent（非作者、非主控）** 复核，其报告见
  [RULE-SCOPE-DECISION-19-independent-review.md](RULE-SCOPE-DECISION-19-independent-review.md)（结论已并入本报告 §7）
- 复核时点：四仓工作树均 clean（主仓仅剩 2 个**与本卡无关的预存脏态**，见 §6）
- 证据可复现：修正组装的 profile 以 [RULE-SCOPE-DECISION-19-catl-corrected-profile.json](RULE-SCOPE-DECISION-19-catl-corrected-profile.json) 入 git；
  生成命令：`python -c "import sys,json;sys.path.insert(0,'scripts');import question_sets as qs;q=json.load(open('docs/implementation/parallel-lanes/packages/2026-10-24/RULE-SCOPE-DECISION-19-catl-corrected-profile.json'));print(qs.compose(q,'quick','runs/rule-scope-19-catl-2026-10-24/composed',answer_format='screening-1'))"`
  （使用当前 release `pkg_24f07923…`；其 prompt 文本仍为冻结包 3.0.0 文本，原因见 §5-F1/R-03）

## 1. 门禁（卡 §5）

| 门 | 要求 | 状态 | 证据 |
|---|---|---|---|
| G1 | 卡即设计输入，主控核 | ✅ | 卡 §0–§4 与阻塞项全部落到实施报告 §1–§4 |
| G2 | 无新裁定项；实施中发现新语义问题须停问所有者 | **PARTIAL（按卡执行，但 2 项待所有者）** | 两条语义均来自所有者原话，未新增语义；实施中暴露的 F1（发布契约阻断）与 R-02（路由路径默认诊断）**需要所有者裁定才能关闭**，已登记未擅自改语义 |
| G3 | TDD | ✅ | 主仓新增 2 测试、翻转 4 处旧语义断言、夹具确定性重封；applic/UI/银行三仓各自红→绿留证（见各 handoff tests/logs） |
| G4 | 独立审查（快照 distribution 可解释、parity 428 格 basis 如实、组装默认值恒包含） | ✅ | 主控独立重算（§2/§3）+ 独立审查 agent 报告（另一文件） |
| G5 | 所有者签收 | ⏳ **待所有者** | 本报告与独立审查报告供签收 |
| G6 | 三仓交接 + 主控 CLI `--verify-references` exit 0 | ✅ | §4：四个 handoff 全部 exit 0 |

## 2. 验收用例（卡 §6）

| ID | 卡要求 | 复核结果（主控实测） | 判定 |
|---|---|---|---|
| **AC-01** | CATL 的 industrial 判定 not_applicable 或 unknown（不再是 applicable）；组装若仍含 industrial 视为未完成 | 快照：CATL `industrial = unknown`（basis `negative_evidence_not_verified`，非 applicable）✅；**修正组装**已生成并可由 git 内 profile 复现（`RULE-SCOPE-DECISION-19-catl-corrected-profile.json` → `runs/rule-scope-19-catl-2026-10-24/`），modules = `[common, operating, auto, mature, dupont, porter]`，**不含 industrial** ✅。历史实跑 `runs/thin-bank-catl-full-2026-10-22` 是冻结证据、未改写（见 §5-F2）；修正组装的 prompt 仍来自冻结 3.0.0 包（见 §5-F1/R-03）。独立审查：**PASS（带 caveat）** | ✅（caveat 已登记） |
| **AC-02** | dupont/porter 恒 applicable（contract_always）且组装默认包含 | 快照：dupont/porter **428 格全部 `applicable` + `common_always_applicable`**（214+214，含 CATL/Alphabet，source=contract）✅；**profile 驱动组装**：任何 profile 默认含两模块（`ALWAYS_APPLICABLE_DIAGNOSTICS`，quick 固定 +12 题），排除须 `diagnostic_exclusions` + 逐条理由（4 类非法输入有测试）✅。**但 v2 路由驱动组装**（`select_questions_for_route`，冻结 route 的 `eligible_module_ids` 为准）不注入默认诊断——路由策略中两模块仍为 `user_diagnostic`；独立审查据此判 **PARTIAL**。关闭需新路由策略制品 + router 升版（另卡，见 §5-F8/R-02） | ⚠️ **PARTIAL**（profile 路径已满足；路由路径为已登记边界） |
| **AC-03** | dupont/porter 的 428 格 basis 全为契约恒适用；总数 10272 不变 | 快照 `applicsnap_26f494e5…`：cells **10272**、分布 **{applicable:1846, not_applicable:0, not_evaluated:0, unknown:8426}** 与旧快照逐项一致；**逐格 state 变化 0**；basis 变化恰 **428 格**（`dupont: owner_ruled_always_applicable→common_always_applicable ×214`；`porter: 同 ×214`）；428 格全 applicable ✅。注：卡 §4.B.2「428→856」是算术笔误；AC-03 的 `contract_always` 指的是谓词 decision，落到快照的 `basis.kind` 是 `common_always_applicable`（见 §5-F3/R-06）。独立审查：**PASS** | ✅ |
| **AC-04** | 主仓 catalog、applic 谓词 mapped_from、bank 4.2.1 三处文本逐字一致（可 diff） | industrial/dupont/porter 三模块：`主仓 catalog 3.2.1 == 主仓模块文件 == bank catalog/module 4.2.1 == applic predicates.provenance.mapped_from` **逐字一致**，industrial `name` 亦逐字一致 ✅；三文本 sha256 各源相同（独立审查 9/9）；bank 侧另有独立脚本对裁定卡原文交叉核对 8/8 True | ✅ |
| **AC-05** | 187+ 测试全绿；parity `state_consistent=true`；UI basis 枚举无未知值 | applic lab **323 tests OK**（独立审查与主控均复跑；handoff 时点为 298，见 §5-R-08）；UI lab **122 OK / 6 skip（与基线同集）**；银行 lab **52 passed / 0 failed**、`validate_bank --releases` OK；主仓定向测试 129 passed/185 subtests（独立审查）；parity（对 UI `41be324`）`state_consistent=true`、mismatch 0、`ui_repo_writes=0`、4 组 basis 全同值（含 `common_always_applicable→…` 642 格）、`known_gaps[0]=closed`；导出 basis 4 种 ⊆ UI `APPLICABILITY_BASES`（13 值）✅。主仓**全量**回归见 §3 定论轮 | ✅ |

## 3. 主仓回归（AC-05）

| 轮次 | 命令 | 结果 |
|---|---|---|
| 改动前基线 | `python -B -X utf8 -m pytest tests -q` | 1036 passed / 3 skipped / 755 subtests（34:14） |
| 定论轮（交付 commit `644ae58` 树，无并行写入） | 同上 | **1038 passed / 3 skipped / 759 subtests**（exit 0，48:32） |
| 文档/清单收尾（`2f1e8e6`、`21d8e67` 后） | g0 清单 + 交接/计划类 | g0 **13/13**；`test_parallel_handoff_cli`+`test_parallel_lane_plan` **23 passed** |
| 最终复核轮 | 全量（pytest tests） | **未重跑**：代码与定论轮 `644ae58` 逐文件相同（其后提交仅 docs/manifest/progress）；按所有者要求不再花 35–50 分钟重跑全量。最终文档/清单树以 `test_g0_manifest` 复验（13/13），代码侧证据＝定论轮 1038 passed + 独立审查定向 129 passed/185 subtests | ✅（证据充分） |

> 说明：中间轮出现的 `test_g0_manifest` 失败经定位为**主控在跑测期间写文档**造成的清单哈希竞态（g0 对
> `docs/implementation/**` 逐字节哈希），非代码缺陷；g0 单独重跑 13/13 证实。故定论轮在"无并行写入"窗口执行。

## 4. 交接（G6 三仓 + 通道包）

| 包 | 仓 | 内容提交 | handoff | 主控 CLI `--verify-references` |
|---|---|---|---|---|
| RULE-SCOPE-19-APPLIC | iqs-applic-lab | `e8fbfbf`（+套件 `2382aea`） | `docs/handoff/RULE-SCOPE-19-APPLIC/` | ✅ exit 0 |
| RULE-SCOPE-19-UI | iqs-question-bank-ui-lab | `40d7927`（+套件 `41be324`） | `docs/handoff/RULE-SCOPE-19-UI/` | ✅ exit 0 |
| RULE-SCOPE-19-BANK | iqs-question-bank-lab | `a1965fb`（+套件 `c8468a9`/`436ef2c`/`7af4119`/`96bbb4f`） | `docs/handoff/RULE-SCOPE-19-BANK/` | ✅ exit 0（首跑曾报 `temporary_root_not_cleaned`，lane 清理后修复） |
| APPLIC-LLM-JUDGE-20（关联包，非本卡） | iqs-applic-lab | `4c6cbca`（+元数据提交） | `docs/handoff/APPLIC-LLM-JUDGE-20/` | ✅ exit 0 |

- 三仓工作树：applic / UI / 银行 **clean**；主仓仅剩 2 个预存脏态（不纳入本卡交付）。
- 交接协议：`handoff.schema.json#1.0.0`；四份 handoff 均通过 shape+scope+reference 校验。
- 批量登记：`docs/implementation/parallel-lanes/packages/2026-10-24/manifest.json` 已登记
  RULE-SCOPE-19-APPLIC / -UI / -BANK 三个包（lane=iqs，task_ids=`["RULE-SCOPE-DECISION-19"]`）。

## 5. 复核中发现（承接实施报告）

- **F1（开放项，需所有者裁定）主仓真实发布库的下一次 `publish()` 会被 `validate_upgrade` 阻断**：
  「applies_when 变化且新旧题 ID 相交 ⇒ 必须换后继题 ID」。本卡按所有者要求就地改文本、题面不动，与该校验
  冲突。已用冻结 3.0.0 归档 × 新源文件实测复现（industrial/dupont 均报
  `module applicability scope change requires successor IDs for all questions`）。测试与组装不受影响
  （夹具在临时根新建历史；运行时读冻结包），但**发布路径被冻结**。未擅改 `module_contract.py`；
  三条出路（换后继 ID／契约修订／接受发布冻结）待所有者择路。独立审查 agent 亦被要求独立复现此项。
- **F2（口径）**：AC-01 的"组装不再含 industrial"落在**新组装**（`runs/rule-scope-19-catl-2026-10-24/`）；
  `runs/thin-bank-catl-full-2026-10-22/` 是历史实跑证据，按"不改写历史"原则保留，其旧 profile
  （含 industrial、无诊断默认）不再代表当前口径。
- **F3（卡内勘误）**：卡 §4.B.2「applicable 增加 428 → 856」与实际不符（现行 applicable=1846 且 dupont/porter
  本就 applicable）；实际效果为 428 格 basis 换类、state 零变化，与 AC-03 一致。按 AC-03 实施并在报告注明。
- **F4（附录）**：`questions/scoring-contexts.json` 新增 diagnostics 映射是**契约必需**（模块脱离 legacy 集后
  `validate_registry` 要求该 kind 有非空语境），非卡 §4.1 表格所列，但属必要实现细节。
- **F5（预存脏态）**：`questions/releases/current.json`、`packages/2026-10-10/README.md` 为本卡开始前即存在的
  工作树修改（git HEAD 与磁盘不同），未纳入本卡提交、未改写。
- **F6（后续卡候选）**：v2 路由驱动的组装仍按冻结 route 的 `eligible_module_ids` 选择（路由策略中
  dupont/porter 仍为 `user_diagnostic`）；如需路由路径也恒含，需新路由策略 + router 升版（另卡）。
- **F7（修正口径 + 开放项）**：UI lab 并不直接读主仓 catalog，但其**构建产物** `src/generated/bank.json`
  仍内嵌 catalog 3.2.0 的旧文本（旧 industrial 名/口径、旧 dupont/porter 口径），而 UI 运行时读取该文件。
  `scripts/build_data.py --check` 只比对格数与版本哨兵，**检测不到这次文本漂移**。本卡阶段 D 范围是
  basis 枚举/文案/图例，未授权重建生成数据；登记为开放项：在 UI 仓运行
  `python scripts/build_data.py`（以主仓 3.2.1 为数据根）重建并提交，随后刷新 UI handoff。
- **R-04（独立审查）**：同上 F7，措辞以本条为准（此前报告"UI lab 不内嵌 catalog 文本"表述不准确）。
- **R-05（开放项，银行 lab 语义/政策张力）**：银行 `catalog.json` 的 dupont/porter `activation` 文案仍为
  「按需激活」，与新 `applies_when`「对所有公司适用」矛盾；`docs/version-policy.md` §3 写 applies_when 变更
  应升 **major** 并退役旧题 ID，银行实际按文本级 4.2.1 处理（机器检查不强制该行文）。属"裁定覆盖政策行文"，
  需所有者 G5 签收时明示；建议随后修 `activation` 镜像文案。
- **R-06（卡内勘误补充）**：除 §4.B.2 的 428→856 外，AC-03 的「basis 全部为 `contract_always`」措辞混淆了
  谓词 decision 与快照 `basis.kind`（实际为 `common_always_applicable`）；卡 §2「谓词由 owner_ruled 改为
  contract_always」亦不精确（谓词 decision 前后都是 contract_always，变的是 `run_eval` 的 basis 映射与
  `provenance.mapped_from`）。实现与 AC 意图一致，建议更正卡片文字以免下一个复核者重复裁定。
- **R-08（口径）**：applic handoff 的 "298 tests" 是交接时点数字；当前 HEAD（含后续 LLM-JUDGE-20 提交）为
  **323 tests OK**（独立审查与主控均复跑）。AC-03 不受影响（快照与 `e8fbfbf` 均为祖先且已冻结）。
- **R-09（口径）**：`parallel_handoff_cli.py` 的 `validation_scope` 明确是
  `handoff_shape_and_declared_scope_only`——不做声索认证；声明的 artifact 哈希由独立审查逐文件复算
  （UI 13/13、BANK 38/38、APPLIC 34/34 全匹配）作为补充证据。

## 6. 独立审查结论（G4，非作者/非主控 agent；全文见独立报告）

| 项 | 独立审查判定 | 与主控结论的关系 |
|---|---|---|
| G1 设计输入 | PASS | 一致 |
| G2 无新裁定 | **PARTIAL**（F1/R-01、R-02 两项待所有者） | 主控同判（本报告 §1 已改 PARTIAL） |
| G3 TDD | PASS（证据法：红相未由审查者重跑） | 一致 |
| G4 独立审查 | PASS（即该报告） | — |
| G5 所有者签收 | **OPEN** | 一致（待所有者） |
| G6 三仓交接 + CLI | PASS（UI/BANK/APPLIC 均 exit 0；artifact 13/38/34 全匹配） | 一致 |
| AC-01 | **PASS（带 caveat）** | 一致（caveat＝R-03 冻结包 prompt） |
| AC-02 | **PARTIAL**（profile 路径满足；v2 路由路径不注入默认诊断） | 主控据此把 AC-02 改判 **PARTIAL**（边界=§5-F8/R-02） |
| AC-03 | **PASS**（10272、0 state 变化、428 basis 变化、rule_ref 全量换前缀已披露） | 一致 |
| AC-04 | **PASS**（9/9 逐字，三源 sha256 相同） | 一致 |
| AC-05 | **PASS（scope noted）**；主仓全量未由审查者重跑（本报告 §3 定论轮补位） | 一致 |

独立审查另提出 9 条 finding（R-01..R-09），主控逐条处置：

| 编号 | 性质 | 处置 |
|---|---|---|
| R-01 | 真实 `publish()` 仍被 `validate_upgrade` 阻断（独立复现） | **开放项（F1）**，待所有者择路（换后继 ID／契约修订／接受发布冻结） |
| R-02 | 默认诊断不覆盖 v2 路由路径 | **AC-02 判 PARTIAL**；新路由策略 + router 升版另卡（F8） |
| R-03 | 修正组装用的是冻结 3.0.0 包（prompt 未换新文本）、且原在 gitignore 的 runs/ | **已补**：profile 入 git 并给出复现命令（本报告头注）；"冻结包 prompt"是 R-01 的必然结果，登记 |
| R-04 | UI `src/generated/bank.json` 旧文本（构建产物未重建） | **开放项**（F7 重写）；重建命令见 §5-F7，属 UI 仓后续小卡 |
| R-05 | 银行 `activation` 文案与 version-policy 行文张力 | **开放项**；G5 签收时明示，建议随后修镜像文案 |
| R-06 | 卡内勘误（428→856、contract_always 术语混淆） | **已登记**（§5-F3/R-06）；建议更正卡片文字 |
| R-07 | 主仓 `questions/releases/current.json` 非 HEAD 且脏 | **预存脏态**（§5-F5），本卡未提交；建议发布前清理 |
| R-08 | "298 tests" 为交接时点数 | **已注明**（AC-05 行）；当前 323 |
| R-09 | CLI 只校验 shape/declared scope | **已注明**；artifact 哈希由独立审查复算补充 |

## 7. 结论

- 卡 §4 阶段 A/B/C/D/E 全部落地；**AC-01/AC-03/AC-04/AC-05 PASS；AC-02 PARTIAL**（profile 驱动路径满足，
  v2 路由驱动路径为已登记边界，需另卡/另裁）。
- **G1、G3、G4、G6 完成；G2 PARTIAL（两项待所有者裁定）；G5 所有者签收待办。**
- 需所有者决策的开放项：**F1/R-01 发布路径冻结**、**R-02/F8 v2 路由默认诊断**、**R-04/F7 UI 生成数据重建**、
  **R-05 银行 activation/版本政策**、**R-06 卡片勘误**、**R-07 指针清理**。其余为已注明的口径/后续项。

