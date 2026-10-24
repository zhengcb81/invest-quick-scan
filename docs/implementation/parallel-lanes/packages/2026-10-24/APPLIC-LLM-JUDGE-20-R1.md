# APPLIC-LLM-JUDGE-20 整改要求（R1）— 2 项阻塞 + 1 项证据缺陷

- 包 ID：APPLIC-LLM-JUDGE-20
- 交付：payload `fbceeb1`，元数据 `01125bf`（协调方代为提交并修正 schema 违规后 CLI valid）
- 独立审查（进行中）已给出 2 阻塞 + 1 证据缺陷；以下逐条要求修复。**通道在修复前不得启用**。

## B1（阻塞）三方互证可被「同一个模型两次」满足；且复核队列未端到端强制

### 事实

1. `src/applic/llm_merge.py:470-481` `prepare_channel` 只拒 `model_id == primary_model`，**未按模型去重**；
   `llm_merge.py:310-328` `_escalate_no` 仅数 `len(no_votes) == 2`。
2. `src/applic/judge_modules.py:660-679` 同一漏洞；`--corroborate` 可重复传同一文件。
3. 实测：主模型 deepseek 判 no + **同一份 mimo_pro 文档传两次** ⇒ 状态 `not_applicable`，
   `corroborating_models=('mimo_pro','mimo_pro')`。
4. `src/applic/run_eval.py:259-279` **从不调用** `review_queue_rows`；只有 `judge_modules.py:693` 调用。
   因此经 `run_eval --llm-judgments … --llm-corroborate same.json --llm-corroborate same.json`，
   `llm_corroborated_not_applicable` 直接进快照，**无任何复核队列**。

### 要求

1. **按模型去重**：三方互证要求 **2 个互不相同、且都不等于主模型** 的 corroborator；
   同一 `model_id` 出现多次只算一票；同一文件路径重复传入直接**拒绝**（fail-closed，报错退出）。
2. 判定结果里记录 `corroborating_models`（去重后的元组），并在存档与快照 basis 里保留。
3. **`run_eval` 必须产出复核队列**：凡 `llm_corroborated_not_applicable` 或 §4.2 ② 冲突格，
   在快照同批产物中强制写复核队列行（不是可选、不是只在 judge_modules 里）。
   复核队列产不出 ⇒ **构建失败**，不得静默进快照。
4. 测试（必须能失败）：同一模型重复 ⇒ 拒绝；两个同模型不同文件 ⇒ 拒绝；
   两模型不同且均 ≠ 主模型 ⇒ 允许；`run_eval` 路径下 not_applicable ⇒ 队列非空。

## B2（阻塞）金标门未按裁定实现

### 事实

1. `judge_modules.py:336-380` `_golden_check` 是**单次命中计数**；`--mode golden` 只调一次
   `_judge`（`judge_modules.py:499-523`、`591-622`）。**没有 `--runs`、没有多数投票、没有不稳定格清单**。
2. `data/llm_judgments/golden-llmj_b7ad6ef9.json` 是 `cross-model/deepseek` 旧答案的**回放**
   （全部 `confidence=medium`，理由与 fixture `archived_deepseek_flash` 逐字一致），**不是实调门禁**。
3. 唯一真实的 3 次日志（`logs/golden_noise.log`：12, 11, 11）按 **逐格 2/3 多数**计算结果是 **11/12**
   （`software` = no,no）⇒ **金标门实际不通过**。
4. 测试是同义反复：`test_llm_golden.py:77-82` 把期望值喂进去；
   `test_llm_channel_cli.py:218-250` 直接按期望值写答案。

### 要求

1. 实现 `--runs N`（默认 3），逐格 **多数投票**；**投票结果 12/12 才算通过**，否则 exit≠0。
2. 实现**不稳定格清单**：`acquisitive`、`software`（Alphabet）—— 这两格不参与单模型投票裁决，
   必须走三方互证；清单写进代码常量并在 report 列出；新发现的不稳定格追加。
3. 金标门必须**实调**（或明确标注为 replay 并单独命名，不得用 replay 冒充门禁）。
4. 测试必须能失败：stub 模型故意返回错误 ⇒ 门禁失败；stub 返回正确 ⇒ 通过；
   投票平票/不足 ⇒ 失败。
5. **诚实结论**：按现状 11/12 ⇒ 金标门**未通过** ⇒ 通道保持禁用。
   report/summary 的 G4、AC-01 行必须如实写「未通过」，不得写 ✅。

## B3（证据缺陷）日志与提交产物不一致

### 事实

1. `logs/live_shadow_214.log` 记 `divergence=111 / review_queue=33`；
   但提交的 `data/llm_judgments/divergence-llmj_b7ad6ef9.json` 只有 **13 行**、
   `review-queue-llmj_b7ad6ef9.json` 是 `rows: []`。
2. 根因：`judge_modules.py:537-540` merge 模式按 **`archives[-1]` 字典序**选存档，
   选中了 96 格回放档 `llmj_959982…` 而非实调档 `llmj_550d…`，把 111/33 覆盖掉了。
3. 111/33 只存活在 `data/review/batches/rb_e7777790f8bde189.json`（源档 = `llmj_550d`）。

### 要求

1. **禁止按字典序选存档**：merge 模式必须显式 `--archive <path>`，
   或在多档并存时按 `created_at` 明确排序并在输出里记录所选档；不得静默取末位。
2. 从实调档 `llmj_550d…` **重新生成** divergence 与 review-queue，提交后二者必须与
   `live_shadow_214.log` 的 111/33 一致；若无法重现，如实在 report 说明差异。
3. 增加测试：两个存档并存时，未显式指定 archive ⇒ 拒绝或按记录规则选，并有断言。

## B4（一致性）AC-02 与 §4.2 ② 的裁决必须落到测试与文档

审查实测：`applicable` + LLM no ⇒ `unknown`（`llm_merge.py:296-308`）。
按所有者 2026-10-24 裁定「LLM 说 no 则用其他方法再试」与卡 §4.2 ②，**这是有意的**，
但必须满足两个前提：

1. **文档明确**：AC-02 的「状态保持 applicable」被 §4.2 ② **显式取代**（不是「已消解」），
   report 的 AC 表要写清「AC-02 按单调性不变量验收：LLM 的 no 永不产出 not_applicable；
   applicable 可降为 unknown，但必须进复核队列」。
2. **测试锁定**：`applicable + LLM no ⇒ unknown + 复核队列非空`（当前测试只断言 unknown，
   没有断言队列，见 B1 第 4 点）。

## B5（潜在）无规则 fail-closed 格可被 LLM yes 救活

`llm_merge.py:190-201` + `run_eval.build_cells`：`basis.kind == no_rule_fail_closed` 的格
（规则表缺该模块，属数据完整性缺口）当前可被 LLM yes 升级为 applicable。
守卫测试 `test_llm_merge.py:283-290` 把 `in_scope=False` 设掉，所以测不出来。

**要求**：LLM **不得**救活 `no_rule_fail_closed` 格（必须保持 not_evaluated / 规则补齐后才可判），
并补一条能失败的测试。

## 复验清单

1. `pytest tests -q` 全绿且新测试**能失败**（逐条给出反例测试名）；
2. 金标门实跑结果如实报告（当前预期 **11/12 不通过**）；
3. divergence / review-queue 与 live 日志一致（111 / 33）；
4. 复核队列在 `run_eval` 路径下非空（not_applicable 必有队列行）；
5. 主控 CLI `--verify-references` exit 0；
6. report/summary 中所有 ✅ 与数字逐条对应提交产物。

## 边界

- 通道保持**禁用**直到 B1/B2 修复且金标门通过（或所有者明确豁免金标门）。
- 不重开所有者裁定（自动映射、无强制审核）；复核队列是**留证与可选审计**，不是审批关卡。
- 不改主仓、UI 仓。
