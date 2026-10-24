# APPLIC-LLM-JUDGE-20｜适用性判定的 LLM 通道（细则）

- 日期：2026-10-24
- 依据：所有者指令「应该引入 LLM」+ LLM-PROBE-18 实测（deepseek-flash 在 12 条人工裁定上 11/12，优于规则引擎 10/12）
- 性质：**设计细则 + 实施卡**。落地写 applic lab；主仓/UI/bank 侧为只读或无改动
- 前置依赖：RULE-SCOPE-DECISION-19 的文本修正先落地（否则 LLM 与规则会一起错）

## 1. 定位：LLM 判定什么，不判定什么

| 轴 / 模块类型 | 判定方 | 理由 |
|---|---|---|
| `type`（operating/bank/insurer…）、`stage`、`industry` 枚举匹配 | **确定性谓词** | 全部由属性表字段直接映射，可复现、零成本 |
| `common`、`dupont`、`porter` | **契约恒适用**（规则） | 所有者已裁定，无需逐公司判断 |
| `extra.*` 旗标（cross_border / acquisitive / listing_structure / concentrated / controlled / subsidized） | **确定性谓词**（属性为 true 时适用） | 同上，属性驱动 |
| **语义边界类**：`industrial`（装备 vs 流程制造）、主题模块（semiconductors、software、medtech…）与公司业务的贴合度 | **LLM** | 需要理解商业模式语义，谓词写不出 |
| **触发类**：`recovery`（此前是否真下滑过）、`turnaround`、`distressed` | **LLM**（或时序数据，暂缺） | 需要历史判断，属性表只有当前时点 |
| 属性缺失/assumed 导致 `unknown` 的格 | **LLM 仅作提示**，不改 state | 见 §6：LLM 不能把 unknown 变 applicable 除非 confidence≥medium 且经抽检 |

**红线**：LLM **不得**把任何格判为 `not_applicable`（反证仍须 verified，G2-3 不变）；LLM 的 "no" 只能产出 `unknown`。

## 2. 数据模型

新增第三个证据源，与谓词、override 并列：

```
data/llm_judgments/llmj_<hash>.json      # 一次判定批次的不可变存档
{
  "schema": "applic-llm-judgments/1.0.0",
  "llm_judge_version": "llmj_a1b2c3d4",   # sha256(template_sha + model_id + params + chunk) 前 8 位
  "template_sha256": "...",
  "model": "deepseek-flash",
  "params": {"temperature": 0, "max_tokens": 12000, "chunk": 24},
  "judged_at_utc": "...",
  "catalog_sha256": "...",
  "judgments": [
    {"entity_id": "...", "module_id": "industrial",
     "applies": "yes|no|unsure", "confidence": "high|medium|low",
     "reason": "≤60字", "evidence_hint": "≤80字",
     "prompt_sha256": "...", "answer_archive": "runs/.../answer-*.json"}
  ]
}
```

快照 `inputs` 增加 `llm_judge_version`；快照 cell 的 `basis.kind` 增加两种：
- `llm_judged_applicable`（LLM 判 yes 且合并规则采纳）
- `llm_unsure_or_no`（LLM 判 no/unsure → 归 unknown）

## 3. 提示词模板（版本化，逐字固定）

模板存 `prompts/llm_judge_v1.txt`，sha256 进 `template_sha256`。结构：

1. 角色：资深权益研究分类员；
2. 公司：名称 + 代码 + 市场 + （可选）业务描述 —— **只用属性表已有的事实，不引入网络检索**；
3. 模块清单：`id｜轴｜中文名｜适用条件(逐字来自 catalog)`；
4. 输出契约：严格 JSON `{"modules": {"<id>": {"applies": "...", "confidence": "...", "reason": "..."}}}`；
5. 约束：必须覆盖所有给定 id；`unsure` 用于确实无法判断；不得输出 not_applicable；理由 ≤60 字。

**分块**：固定 `chunk=24`（LLM-PROBE-18 实测 48 一锅与 24 分块在一条触发规则上会翻转；固定分块才能复现）。

## 4. 合并规则（所有者裁定 2026-10-24）

### 4.0 两条裁定（原话）

> 先用 LLM 吧，然后再用其他规则
> （置信门槛）都采纳
> （LLM 说 no 怎么办）LLM 说 no 则用其他方法再试

### 4.1 判定顺序

```
1. 所有者 override                      （最高，不变）
2. LLM 判定（conf ∈ {high, medium}）      （LLM 优先）
   - yes  → applicable（basis=llm_judged_applicable, confidence=assumed）
   - no   → 进入 4.2 升级路径（不直接下结论）
   - unsure/出错/缺答案 → 回落谓词（见 4.4）
3. 谓词判定（作为升级路径的仲裁证据 + LLM 失效时的兜底）
4. 其余 → unknown
```

### 4.2 LLM 说 no 时的升级路径（本次裁定新增）

「用其他方法再试」落成三条互证，任一为 yes 即视为**有争议**，不得判不适用：

| 步骤 | 方法 | 结果处理 |
|---|---|---|
| ① 换模型复判 | 同模板同模块，另两个模型各判一次（mimo_pro、minimax） | 任一 says yes ⇒ **争议** → unknown + 记 `llm_no_conflict`，进人工复核队列 |
| ② 谓词仲裁 | 读确定性谓词结果 | 谓词 applicable ⇒ **争议**（LLM 与规则冲突）→ unknown + 进复核队列；谓词 unknown ⇒ 进入 ③ |
| ③ 三方一致为 no | 三个模型都说 no 且谓词非 applicable | **not_applicable**，basis=`llm_corroborated_not_applicable`，confidence=assumed，**进复核队列**（可被 override 推翻） |

要点：
- 只有「三个模型的 no + 谓词不反对」才允许产出 `not_applicable`；任一异构结论 ⇒ unknown。这取代 G2-3「必须 verified 反证」在 **LLM 通道**上的约束（G2-3 仍约束属性驱动的判定，见 §4.5）。
- 所有产出 not_applicable 的格**强制进复核队列**（不静默生效），复核页沿用 `pipeline_review_pack` 的形式。
- 升级只对 no 触发：本轮 shadow（24 家 × 4 模块 = 96 格）实测 **no 75 / yes 20 / unsure 1**（no 占 78%，`runs/applic-llm-probe-2026-10-24/shadow-4mod/report.json` 为权威值）；需 2 个额外模型 × 75 ≈ 150 次调用/24 家，214 家全量一次性约 $15–25（增量缓存后日常更低）。
  > 更正（2026-10-24）：本卡初稿写「no 占 52 格（54%）」为加总错误，由 applic worker 核对存档后指出；此处以存档 75/96 为准。

### 4.3 置信门槛（本次裁定）

`high` 与 `medium` **都采纳**；`low` 丢弃并回落谓词。本轮 shadow 96 格中 high 59 / medium 37 / low 0，故实际等于全采纳。

| 置信 | 处理 |
|---|---|
| high | 采纳 LLM 结论（yes 直接 applicable；no 进升级路径） |
| medium | 同上，但采纳后在 basis 里保留 `confidence=assumed`（与 high 相同）；差别只在统计与复核抽样权重 |
| low | 不采纳，回落谓词 |

### 4.4 LLM 失效时的兜底

`unsure` / 调用失败 / 缺该模块答案 ⇒ 回落谓词结果（不空转、不放行）：
- 谓词 applicable ⇒ applicable（basis=`predicate_true`）
- 谓词 unknown ⇒ unknown
- 谓词 not_applicable ⇒ not_applicable（不变）

### 4.5 与 G2-3 的关系（显式记录）

原 G2-3：「`not_applicable` 必须有已核实反证（verified），否则 unknown」。本次裁定为 LLM 通道开了一条**旁路**：三方一致的语义否定可产出 `llm_corroborated_not_applicable`。因此：

- 属性/谓词驱动的否定：仍受 G2-3 约束（assumed 属性判假 ⇒ unknown）；
- LLM 通道的否定：受 §4.2 三方一致约束，且强制复核。

两者并存，`basis.kind` 可区分来源，快照与 UI 不受影响（UI 侧只认 not_applicable 状态）。

## 5. 可复现性与质量门

1. **金标集**：`tests/fixtures/llm_golden.json` = 所有者已裁定的行（当前 12 条，含 RULE-SCOPE-DECISION-19 后的期望值）。启用前必须 **12/12 命中**（当前 deepseek-flash 为 11/12，剩 1 条正是规则文本问题 —— 文本修好后应达 12/12）。
2. **模板冻结**：模板、模型 id、参数、分块任一变化 → `llm_judge_version` 变 → 必须全量重判并重过金标集。
3. **重跑抽检**：每季度或每 50 家公司，抽 10% 重判，与存档比对不一致率 >5% 则停用通道并复审（模型侧漂移）。
4. **失败即降级**：HTTP 错误/非法 JSON/超时 → `unknown` + `basis.kind=llm_error`，**绝不**按 yes 处理；重试仅限同模板同分块，最多 2 次。
5. **成本**：实测 48 模块 ≈ 1.8k prompt + 9k completion tokens；deepseek-flash 约 $0.012/公司；214 家全量一次性约 $2.6。增量缓存键 `(entity_id, module_id, catalog_sha, llm_judge_version)`，只重判变化的格。

## 6. 与快照/组装/UI 的关系

- **快照**：LLM 结果作为第三种输入；`snapshot_id` 键含 `llm_judge_version`，与 attribute/predicate 版本同级；任一 bump → 旧快照失配。
- **组装**：消费快照的 applicable 集合（不变）；LLM 补充的格与谓词判定的格在组装里**无差别**（组装不关心来源），但导出/UI 里 basis 区分。
- **UI**：`llm_judged_applicable` 与 `assumed` 同级显示琥珀「待确认」；抽屉展示 `reason`（原文逐字）。

## 7. 实施顺序（shadow → 启用）

1. **阶段 1（shadow）**：`scripts/judge_modules.py` 只产出 `data/llm_judgments/llmj_*.json`，**不接入快照**；对 214 家跑一遍，与当前快照逐格 diff，产出「LLM 与谓词分歧清单」（正是 PIPELINE-AUDIT-17 的复核页格式，可直接用 `pipeline_review_pack` 生成 pack）。
2. **阶段 2（人工抽样）**：从分歧清单抽 20 行交所有者裁定（复核页），统计 LLM vs 所有者一致率；≥85% 才进入阶段 3。
3. **阶段 3（启用）**：按 §4 合并规则接入快照；金标集 12/12；重建快照；parity 复跑；上线 UI 徽标。
4. **阶段 4（固化）**：季度抽检 + 版本纪律写进 bank-run-playbook。

## 8. 门禁

- **G1**：本细则 + 模板草案，主控核；
- **G2**：**所有者必须确认 §4 合并规则**（尤其「LLM 只能正向补充、不得产生 not_applicable」「置信度阈值 high/medium 才采纳」）；
- **G3**：TDD（合并规则、失败降级、缓存键、金标集各有用例）；模型调用用注入，测试离线；
- **G4**：独立审查（重点：合并是否真的单调、失败是否真的降级、金标集是否可复现）；
- **G5**：所有者签收（演示 shadow 分歧清单 + 金标集结果）；
- **G6**：交接套件 + CLI exit 0。

## 9. 验收用例

| ID | 用例 | 期望 |
|---|---|---|
| AC-01 | 金标集（12 行） | 全部命中；命中率打印可复核 |
| AC-02 | LLM 判 no 的 applicable 格 | 状态保持 applicable（单调性） |
| AC-03 | LLM 报错 | 该格 unknown + `llm_error`；不重试超过 2 次；无静默升级 |
| AC-04 | `llm_judge_version` bump | 旧快照失配；重建后新 id；金标集重跑 |
| AC-05 | 214 家 shadow 全量 | 产出分歧清单 + 成本实测；不写快照 |
| AC-06 | 缓存键 | 仅 changed cells 重判；命中率可观测 |

## 10. 开放问题（所有者 2026-10-24 答复）

1. **判定范围**：确认「先 4 个模块」——`industrial` + `recovery`/`turnaround`/`distressed`；13 个主题模块后置。
2. **置信门槛**：确认「先跑一版看分布再定」——本轮 shadow（24 家）产出 high/medium/low 分布后由所有者定阈值。
3. **业务描述**：沿用建议，先不进提示词（只用名称+代码+市场）。
4. **LLM 的 no 能否产出 not_applicable**：所有者裁定「LLM 说 no 则用其他方法再试」——实现为 §4.2 三方一致升级路径；仅三方一致时才产出 `llm_corroborated_not_applicable` 且强制复核。
