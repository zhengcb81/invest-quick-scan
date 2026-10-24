# RULE-SCOPE-DECISION-19｜三条模块的适用范围裁定与改动清单

- 日期：2026-10-24
- 裁定人：项目所有者（口头指令 + 本文件落盘）
- 影响：题库目录文本（主仓 `questions/`）、适用性谓词（applic lab）、组装默认值、快照重建、既有台账 R003 的效
- 性质：**裁定 + 改动清单**。文本改动落地需按 §4 分阶段执行（跨仓）

## 0. 所有者原话（2026-10-24）

> 1，杜邦分析和波特五力分析对所有公司都要做，不是选做题。
> 2，我以为 Industry 是广义制造业或工业，如果按照你的狭义定义那么否定是正确的，你要看看题库里的题目到底是针对狭义的行业还是广义的行业，然后由你决定。

## 1. 决定一：`industrial` 维持狭义（装备制造），但把文本写清楚

### 取证（题库原文，四题全部假设装备/项目型商业模式）

| 题号 | 维度 | 题目 | 隐含商业模式 |
|---|---|---|---|
| INDUSTRIAL_01 | moat | 设备可靠性、客户认证和服务网络能否保持竞争优势？ | 卖设备 + 认证 + 服务网络 |
| INDUSTRIAL_02 | business | 订单在取消、验收、质保和收款后具备多高利润确定性？ | 项目订单 + 验收 + 质保 |
| INDUSTRIAL_03 | execution | 产能与项目交付能否兼顾成本、质量和进度？ | 项目交付 |
| INDUSTRIAL_04 | growth | 安装基数、售后和升级需求能否形成持续增量？ | 安装基数 + 售后升级 |

四道题没有一道问「制造工艺/产能利用率/良率/成本曲线」这类流程制造问题；全部围绕**设备销售、项目验收、安装基数与售后**。电池电芯（CATL）的商业模式是连续生产 + 供应，不满足这四题的假设。

### 决定

- **口径不变**：`industrial` = 资本品与专用设备制造（EQUIPMENT）。CATL 判不适用 —— **正确**，与所有者本日裁定一致。
- **把名实写清**（避免「工业制造」被读成广义）：

  - `name`：`工业装备与专用设备`（原「工业制造、自动化与专业设备」）
  - `applies_when`：
    > 资本品、专用设备、自动化装备、航空航天与国防装备的制造与销售。判定要点：以设备/项目交付与安装基数为商业模式（订单验收、质保、售后升级）；不含流程制造（化工、材料、电池、钢铁等），后者按 operating 与对应行业/主题模块评定。

- **连带**：流程制造若需要专门题目，应另立模块（如 `process_manufacturing`），不在本次范围。

## 2. 决定二：`dupont` / `porter` 改为对所有公司必做

### 取证

两条规则原文都写成「…**时选用**」的条件触发：

- dupont：「ROE变动或质量无法由核心题解释时选用；仅在因子具经济含义时评分，不进入汇总。」
- porter：「竞争结构或价值链利润归属不清时选用；明确真实市场边界，不进入汇总。」

但两套题的 7 + 5 道题本身是**结构化的普遍分解**（杜邦三/五因素、五力五项），并不依赖「先验不清」这个前置判断。原措辞实际是**控量手段**（避免每题都问），不是适用性判断。

### 决定

- 语义改为**对所有公司适用**；「不进入汇总」保留。
- 新文本：

  - `dupont.applies_when`：
    > 对所有公司适用（所有者 2026-10-24 裁定：杜邦分析是所有公司的必做项，不是选做题）。仅在因子具经济含义时评分，不进入汇总。
  - `porter.applies_when`：
    > 对所有公司适用（所有者 2026-10-24 裁定：波特五力是所有公司的必做项，不是选做题）。明确真实市场边界，不进入汇总。

- 谓词：由 `owner_ruled_always_applicable`（现由 G2-1 支撑）改为**契约恒适用**（`contract_always`），与 `common` 同级，不再依赖单次裁定记录。
- 组装：`diagnostic_modules` 从「手工可选」改为**默认必选**（对齐 PIPELINE-AUDIT-17 Q3 选项 A）。

## 3. 对既有台账的影响（必须记录，不许静默覆盖）

复核台账 `review-pack-01.jsonl` 的 **R003（CATL/industrial，keep_composition，「电池制造业当然是制造业（工业）」）** 被本日裁定**推翻**：

- 新裁定：industrial 是狭义装备制造，CATL 不适用 → 组装应**移除** industrial；
- 台账 append-only，不修改 R003；在下一份 pack（pack-02）中该行不再出现（因两侧已一致），并在 `progress.md` / 报告注明「R003 由 D-2026-10-24 裁定取代」。

## 4. 改动清单（分阶段，跨三仓）

### 4.0 实施约束（主控实测，2026-10-24）

主仓 `questions/` 目录受**信任锚**管辖：`scripts/module_registry.py::_verified_legacy_ids` 要求
「没有 lifecycle 元数据的模块必须与 `schemas/quick_scan/module-legacy-baseline.json` 字节完全一致」，
该 baseline 又由 `LEGACY_BASELINE_SHA256` 常量锁定。

主控试改 3 个模块的文本后实测：**29 个路由/发布测试红**（`industrial: untrusted legacy module archive; lifecycle metadata is required`）。

因此阶段 A 不是纯文本替换，必须二选一，且都属**题库 lane**：

- **方案 A（推荐，符合设计意图）**：给这 3 个模块补 `activation` / `introduced_in` / `dependencies` / `conflicts`，使其脱离 legacy 集（不再受 baseline 字节约束）；同时确认 `module_contract.validate_registry` 与 routing/registry 的 29 项回归。
- **方案 B（轮换信任根）**：更新 baseline 文件 + `LEGACY_BASELINE_SHA256` + `LEGACY_BASELINE_RELEASE_ID`，等于宣布「原基线作废」，影响所有历史包可比性 —— **不推荐**。

主控未直改（已回滚，主仓保持绿）。本卡交付文本与决定，实施归题库 lane。

### 4.1 阶段 A — 主仓（题库目录文本）

| 文件 | 改动 |
|---|---|
| `questions/industries/industrial.json` | `name` + `applies_when` 按 §1 |
| `questions/diagnostics/dupont.json` | `applies_when` 按 §2 |
| `questions/diagnostics/porter.json` | `applies_when` 按 §2 |
| `questions/catalog.json` | 版本号 bump（3.2.0 → 3.2.1，文本级）；`applies_when` 同步 |

主仓侧无题目内容变更（题库题面、anchors 不动），仅元数据文本 + 版本。

### 阶段 B — applic lab（谓词与快照）

1. 重建谓词：`industrial` 谓词逻辑不变（枚举行业匹配），`provenance.mapped_from` 更新为新文本；`dupont`/`porter` 改为 `contract_always`（3 条 → 5 条契约恒适用）；
2. bump `predicate_version`；重建快照（新 `snapshot_id`）；`distribution` 预期变化：applicable 增加 428 → 428 + 214×2 = 856（dupont/porter 从 owner_ruled 改为 common 类恒适用，仍 applicable）；industrial 状态不变（仍 unknown/not_applicable）；
3. 复跑 parity（UI 侧 basis 名 `owner_ruled_always_applicable` → `contract_always` 会让 10272 格中 428 格的 basis 值变化 → UI 侧枚举需同步，见阶段 D）；
4. 8 步 CLI 链 + 交接套件。

### 阶段 C — 组装管线（主仓）

`diagnostic_modules` 默认必选：组装时若 profile 未显式排除，`dupont`/`porter` 恒入；这是 PIPELINE-AUDIT-17 Q3 的落地。

### 阶段 D — UI lab（枚举与文案）

`adapters/contracts.py` 的 `APPLICABILITY_BASES` 增加 `common_always_applicable` 已有；`owner_ruled_always_applicable` 保留（历史快照仍可能带），图例补一条说明；basis 文案表更新。

### 阶段 E — 银行 lab（4.2.0 候选）

`iqs-question-bank-lab` 的 `modules/industries/industrial.json`、`modules/diagnostics/{dupont,porter}.json` 同步文本，bump catalog 版本（4.2.0 → 4.2.1），重跑 `validate_bank.py` 与一致性测试。

## 5. 门禁

- **G1**：本文件即设计输入，主控核；
- **G2**：无新裁定项（两条语义均由所有者原话给定）；若实施中发现新语义问题 → 停问所有者；
- **G3**：TDD（文本改动不影响题目，但谓词/快照/组装各有测试）；
- **G4**：独立审查（重点核：快照 distribution 变化是否可解释、parity 428 格的 basis 变化是否如实、组装默认值是否真的恒包含）；
- **G5**：所有者签收；
- **G6**：三仓交接 + 主控 CLI `--verify-references` exit 0。

## 6. 验收用例

| ID | 用例 | 期望 |
|---|---|---|
| AC-01 | CATL 的 industrial 判定 | not_applicable 或 unknown（不再是 applicable）；组装若仍含 industrial 则视为未完成 |
| AC-02 | CATL / Alphabet 的 dupont、porter | 恒 applicable（`contract_always`），且组装默认包含 |
| AC-03 | 快照 distribution | dupont/porter 的 428 格 basis 全部为 `contract_always`；总数 10272 不变 |
| AC-04 | 文本一致性 | 主仓 catalog、applic 谓词 `mapped_from`、bank lab 4.2.1 三处文本逐字一致（可 diff） |
| AC-05 | 回归 | 187+测试全绿；parity `state_consistent=true`；UI basis 枚举无未知值 |

## 7. 复核勘误（2026-10-24，主控与独立审查共同确认；不改变本卡任何裁定语义）

复核报告见 [RULE-SCOPE-DECISION-19-review.md](RULE-SCOPE-DECISION-19-review.md)、独立审查见
[RULE-SCOPE-DECISION-19-independent-review.md](RULE-SCOPE-DECISION-19-independent-review.md)。文字层面的勘误：

1. **§4.B.2 的分布数字有误**：原文「applicable 增加 428 → 856」与实际不符。复核实测：现行 applicable=1846
   （dupont/porter 本就 applicable）；本裁定的实际效果是 **428 格 basis 换类、逐格 state 零变化**，总数 10272
   不变——与 AC-03 一致，按 AC-03 执行。
2. **AC-03 的「basis 全部为 `contract_always`」用词不精确**：`contract_always` 是谓词表的 *decision*
   （dupont/porter 在本卡前就已是 contract_always）；落到快照的是 `basis.kind = common_always_applicable`。
   §2 的「谓词改为 contract_always」同理应读作「basis 映射与 `provenance.mapped_from` 变更」。
3. **AC-02 的执行边界**：「组装默认包含」已在 **profile 驱动组装** 落地并测试；**v2 路由驱动组装**
   （`select_questions_for_route`，以冻结 route 的 eligible 模块为准）仍按路由策略（dupont/porter 为
   `user_diagnostic`）；如需同为默认包含，须新路由策略 + router 升版（另卡）。
4. **AC-01 的组装口径**：「组装应移除 industrial」以**新组装**为准（主控交付修正 profile 与复现命令，
   见复核报告头注）；`runs/thin-bank-catl-full-2026-10-22` 属历史实跑证据，不改写。
