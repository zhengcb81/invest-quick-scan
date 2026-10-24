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

## 4. 合并规则（三值合并，确定性优先）

```
if owner_override_active:            -> override 值（最高优先，不变）
elif 判定来自契约恒适用模块:          -> applicable（不变）
elif 谓词 == applicable:              -> applicable（确定性优先）
elif 谓词 == not_applicable:         -> not_applicable（不变；LLM 不得推翻）
elif 谓词 == unknown/not_evaluated:
    LLM == yes 且 confidence in {high, medium}
                                      -> applicable, basis=llm_judged_applicable,
                                         confidence=assumed（UI 琥珀「待确认」）
    LLM == yes 且 confidence == low   -> unknown, basis=llm_unsure_or_no
    LLM == no / unsure / 缺失/报错     -> unknown, basis=llm_unsure_or_no（或 llm_error）
```

**关键约束**：LLM 只能把 `unknown → applicable`（正向补充），**永远不能**把 `applicable → unknown/not_applicable`，也不能把 `unknown → not_applicable`。这样 LLM 通道是**单调增强**，不会引入反证风险。

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

## 10. 开放问题（实施前须答复）

1. 业务描述是否进提示词？（LLM-PROBE-18 此条件未跑；进则一致性更高但引入人工文本依赖）建议：**先不进**，只用名称+代码+市场，与 G2-2 的事实口径一致。
2. 主题模块（13 个 themes）是否也走 LLM？建议：先只做 `industrial` + 3 个触发模块（recovery/turnaround/distressed），主题模块留待阶段 2 抽样后再定。
3. LLM 判定的 confidence 由谁给？建议：模型自评 + 金标集校准（后续可加投票：同模型两次或两模型取一致）。
