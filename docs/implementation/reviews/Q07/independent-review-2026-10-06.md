# Q07 独立审查报告 — 逐题检查点、部分回复与取消恢复

日期：2026-10-06。审查者为独立复跑 reviewer（与实现者无关）。全部结论来自本机重新执行的命令、对 `git diff` 的逐行审读、对 store 契约原文的核对，以及 8 个离线独立探针（`%TEMP%` 临时目录 + 临时 SQLite，Fake provider/generator，不联网、不调 LLM、不读真实配置，两仓零写入，审查报告为唯一写入文件）。

被审对象：StockQA 仓 `C:\Users\郑曾波\Projects\StockQAbyLLM` 的未提交改动；施工卡 `docs/implementation/reviews/IQS-lane/Q07-checkpoint-card-2026-10-06.md`；任务卡 `tasks.json` id=Q07；case 定义 `acceptance-cases.json`；不变量原文 `decision-register.md`（I05 L11、I12 L18、I17 L23）；Q06 基线 `reviews/Q06/independent-review-2026-10-05.md`（r2 裁决 approved）。

---

## 1. 范围

任务卡 Q07（tasks.json L1966-2015）：case_ids = JOB-03/JOB-04/JOB-05/LLM-07/PAR-04/PAR-09；invariants = I05/I12/I17；depends_on = Q06/Q03；steps 要求逐题即存、只补漏题、停发/取消与在途分离、崩溃检查已存与未知、默认逐题、cap 仅上限。

`git diff` + `git status` 实测，**恰 4 个变更面**：

| 变更面 | numstat | 内容 |
|---|---|---|
| `src/core/models.py` | +78 / **-0** | 纯新增 `final_transport_provider`（L308-324）与 `execution_receipt_for_checkpoint`（L326-383）；既有代码零改动 |
| `src/core/qa_engine.py` | +33 / **-0** | 纯新增水合分支（L158-190），位于既有 Q06 钩子块内 |
| `src/runners/llm_runner.py` | +191 / -11 | `__init__` budget 对、`mark_send_intent` 传参、`hydrate_question`（L272）、`after_question` 四前置扩展（L308）、`recovery_report`（L407）、`cancel_pending_work`（L459）；-11 全部为被替换的注释行 |
| `tests/unit/test_q07_checkpoint.py` | 新增 497 行 / 6 用例 | 六 case 绑定 |

- `src/utils/quick_scan_work_store.py` **零改动**（卡允许"最小缺口"，实际无需动）；`main_with_llm.py` 未改；Q06 及所有既有测试文件未改（`git status -- tests/` 仅 `?? test_q07_checkpoint.py`）。
- untracked 杂物（`.codegraph/`、`.workbuddy-ai/`、`nul`、`pilot_runs/*`、`progress_update.txt`）为既有杂物，不在范围。
- 卡"禁改"面（transport 协议、Q09 预算语义、Q06 生命周期契约、既有输出 schema）：diff 未触及 `quick_scan_work_transport.py`、`quick_scan_result_outbox.py`、`to_quick_scan_dict` 既有行 ✓。
- 无网络/LLM/密钥：新测试仅用 FakeProvider/FakeGenerator + `tmp_path` SQLite，grep 无 requests/urllib/密钥引用（唯一命中是 policy 字段 `"max_requests": 100`）；policy 为测试内联 dict，未读真实配置 ✓。

---

## 2. 门复跑（命令 + 数字，全部本机独立执行）

| 门 | 命令（cwd=StockQA） | 实测结果 |
|---|---|---|
| 定向 pytest | `python -X utf8 -m pytest tests/unit/test_q07_checkpoint.py tests/unit/test_q06_work_binding.py tests/unit/test_qa_engine.py tests/unit/test_llm_runner.py tests/unit/test_basic_runner.py tests/unit/test_quick_scan_work_store.py -q -p no:cacheprovider -o addopts=` | **123 passed**（12.83s，exit 0）— 与预期一致 |
| 全量 pytest | `python -X utf8 -m pytest tests/ -q -p no:cacheprovider -p no:base_url -o addopts=` | **887 passed, 4 skipped**（72.46s，**0 errors**，exit 0）— 与预期一致；887 = 基线 881 + 新 6，与施工卡"基线 881 口径"吻合 |
| Q06 回归 | `pytest tests/unit/test_q06_work_binding.py -q` | **15 passed**；文件未改动（原样通过） |
| CLI 回归 | `pytest tests/integration/test_quick_scan_cli.py -p no:base_url -o addopts=` | **48 passed**（exit 0）— 即"48 项 CLI 测试"。注：不带 `-p no:base_url` 单独跑会 44 passed/4 errors（插件夹具问题，属跑法差异，非本批回归） |
| mypy | `mypy src/core/qa_engine.py src/runners/llm_runner.py src/core/models.py main_with_llm.py` | **Success: no issues found in 4 source files** |
| black | `black --check -l100` 四文件（含新测试） | **4 files would be left unchanged** |
| ruff | `ruff check` 四文件 | **All checks passed!** |
| 空白/冲突 | `git diff --check` | exit 0，无输出 |

---

## 3. Q06 契约不破坏证据（重点）

**结论：Q06 的 honest-unknown / uncertain 不重派契约未被破坏；Q06 15 项测试原样通过。**

1. **getattr 守卫 = 缺 hydrate 的钩子零行为变化**（qa_engine L161-162）：`hydrate = getattr(self.work_item_lifecycle, "hydrate_question", None)`；钩子无此方法时 `checkpoint = None`，直接落到与 Q06 逐字相同的 `before_question` 调用（L191）。diff numstat +33/-0 = 纯新增，无既有行改动。
2. **零注入 None 路径逐字节等价仍成立**：`self.work_item_lifecycle is None` 的分支（L148）与 Q06 拒绝分支（L192-225）零改动；diff 中唯一 -11 行在 llm_runner 且全为注释替换（`after_question` 的 Q07 说明改写），代码体未动。
3. **after_question 四前置失败 → 严格回退 Q06 honest-unknown**：
   - 无回执：`execution_receipt_for_checkpoint` 返回 None → 整段跳过 → 落入原 Q06 `record_attempt_outcome(outcome="unknown")` 块（代码未改）。**探针 D 实证**：attempt=`uncertain`、work=`uncertain`、checkpoint=0、`claim_after=None`（不重派）。
   - 非 verified 身份：`self._identity.get("identity_state") == "verified"` 短路 → Q06 路径（代码审读；store 侧 `save_answer_checkpoint` L2225 亦独立拒绝非 verified）。
   - 形状不符：`shape_ok`（L330-338）拒 `"error"` 状态、非 1-10 分、非 scored 带分 → Q06 路径。
   - 模型不匹配（本批新增的第四前置，**无既有测试覆盖**）：**探针 E 独立实证** —— receipt.actual_model=`other-model` ≠ model_requested → attempt=`uncertain`、work=`uncertain`、checkpoint=0 ✓。
   - record 自身抛错（如租约已 fencing）：catch 后 return，不再落 unknown —— 但 Q06 下 `record(unknown)` 同样 `_assert_lease` 必抛并被 Q06 的 except 吞掉，终态同为"租约到期 → `recover_expired` → uncertain"（store L1870-1921），**收敛一致，无行为回退**。
4. **Q06 测试 15 项原样通过 = 实证**（上表）；且 `test_q06_work_binding.py` 零改动（I17：无既有反例被删/改）。
5. **水合不绕过 Q06 拒绝语义**：hydrate 无命中 → None → `before_question` → 对 uncertain/leased/cancelled 照旧 claim 拒绝 + error 结果（探针 C/D）。卡面歧义面决议"有 checkpoint→水合成功，无→保持 error 拒绝"实现属实（探针 B：result_ready+checkpoint 的 IQS_05/06 被水合、零新派发；IQS_09 正常走 claim）。
6. `hydrate_question` 的 `create_or_attach` 参数与 `before_question`（L182-198）逐字相同（question_id 派生公式、指纹、九元键一致），二次调用幂等（`INSERT OR IGNORE` + `attached_run` 事件仅首次），对 Q06 既有路径无状态干扰。

---

## 4. 六 case 语义证据（测试断言审读 + 自行复跑 + 独立探针）

### JOB-03（6 题 4 存 2 补）
- 测试 `test_job_03_hydrates_saved_and_only_refills_missing`：4 检查点种子 → 引擎 6 题：`provider.calls == 2`（恰 2 次搜索/派发）、`processed_count == 6`（pack 不整体丢弃）、hydrated==4 且分数 `sorted == [7,8,9,10]`（**分数来自存档**）、fresh==2。定向门复跑通过 ✓。
- 探针 B 独立复证：2 题水合时 provider 调用仅 +1（未水合题），水合数正确。
- **缺口**：fresh 2 题"不假全成"（未落 checkpoint、attempt 不记成功）测试未断言 —— 行为由探针 D 复证正确（无回执 → uncertain、checkpoint=0），属断言缺口（LOW-2）。

### JOB-04（四点崩溃分区）
- 桶判定实现（`recovery_report` L407-456）与文档逐条对照：**checkpoint 优先**（L424-428）→ persisted；`pending` → pre_dispatch；`cancelled` → cancelled；`uncertain` → unknown_in_flight；`leased` 按 attempt phase 分流（`phase ∉ {prepared, abandoned_unsent}` = 已发 → unknown_in_flight，否则 pre_dispatch，L437-444）= 卡面"派发前(pending/未发 intent 无费用)、发出后不明、已存不重问、未 ACK(Q10 域标注)" ✓ 一致；未知状态兜底进 unknown_in_flight（保守列出，无静默丢弃）。
- **只读核**：`recovery_report` 仅调 `list_run_items`（L2809，纯 SELECT）、`get_answer_checkpoint`（L2327，纯 SELECT）、`list_attempts`（L2877，纯 SELECT）—— **不写库** ✓（`cancel_pending_work` 写库属 JOB-05 设计内）。
- 测试 `test_job_04_recovery_partitions_all_states_no_silent_loss`：A（仅 create）→ `pre_dispatch` 断言 ✓；B（lease=10s + 时钟推进 11s + `recover_expired == "uncertain"`，**短租约真过期**）→ `unknown_in_flight` 断言 ✓；分区断言 = 五桶并集无重叠（`len == len(set)`）且总数 == `list_run_items` 数（无遗漏）✓；`q10_import_ack_note` 存在 ✓。
- **缺口（P2-1）**：C（checkpoint 种子）**只断言 `isinstance(report["persisted"], list)`，未断言 C 的 id 在 persisted 桶** —— 实现因 checkpoint-first 代码序正确落入 persisted（L424-428 审读确认），但若有人把状态判断提前，测试仍绿；D（导入 ACK 前）crash 点**从未实例化**（import_ack_pending 恒空表，桶逻辑零执行）；`cancelled` 桶在 JOB-04 中无实例；"派发前无费用"无预算断言（该测试根本没配置 budget）。

### JOB-05（取消 = 状态变更）
- 测试 `test_job_05_cancel_is_state_change_and_history_survives`：`cancel_pending` 二次调用均返回 `"cancelled"`（幂等）✓；`created` 与 `cancelled` 事件并存（历史不删）✓；`claim(...) is None` 且 `before_question` 返回 `claimed=False` + 具名 reason（不派发）✓；他项 `status == "pending"` 不动 ✓；leased 项 `cancel_pending` 抛 `WorkConflictError` ✓。复跑通过 ✓。
- store 契约核对（L2835-2861）：仅 pending 可取消、二次幂等、事件追加不删行 ✓。
- `cancel_pending_work`（L459-471）包装语义代码审读 + **探针 C 实测**：pending→`"cancelled"`、leased→`"refused:WorkConflictError"`、不存在 id→`"refused:KeyError"`，从不抛出、按名拒绝 —— 符合卡面"包装语义"。**但该函数零测试覆盖、生产无调用方**（全仓 grep 仅定义处）→ LOW-1。
- "在途结果仍可保存"：`save_answer_checkpoint` 只要求租约有效 + attempt response_available（L2224-2243），与"取消/pending 保持"正交，未被本批破坏（代码审读）。

### LLM-07 / I05（不猜分、不合成成功）
- 测试 `test_llm_07_unfixable_results_never_become_checkpoints` 逐条断言：search_status≠executed 拒、http 500 拒、score `"8"`/`11`/`True`/scored-null/unknown-带分 全拒（ValueError）、**`get_answer_checkpoint is None`**、无伪造成功。复跑通过 ✓。
- 对照 I05 原文（L11）：bool/0/11/字符串猜分/默认 5 拒绝 —— store `save_answer_checkpoint` L2161-2165 用 `type(score) is int and 1<=score<=10`（bool 天然拒）、非 scored 必须 null ✓；`0` 与 `11` 同一代码路径（11 有测试，0 同式覆盖）。
- 引擎侧四前置与 store 契约同构（`shape_ok` 与 L2154-2165 语义逐条一致；`actual_model == model_requested` 对应 store L2241 `attempt.model_requested != actual_model`）。
- **缺口**：LLM-07 测试直打 store，未走 `after_question` 引擎路径；"修复预算硬顶"不在本文件（format_repair 断言在 `tests/integration/test_quick_scan_cli.py` L954-996 等，属 Q03 依赖面）→ LOW-3。

### PAR-04（恢复只补 2、原 4 不变）
- 测试 `test_par_04_resume_keeps_original_checkpoints_and_provenance` 断言全覆盖并复跑通过：`provider.calls == 2`（只补 q5/q6）；`before_items <= after_items` 且 `len(after_items) == 6`（**工作项宇宙恰 6，原 4 不被重铸/新包不铸新题**）；原 4 个 attempt 的 `(work_item_id, prompt_sha256)` 逐一相等（**attempt id + prompt hash 不变**）；`answer_checkpoint` 恰 4 行、provenance `actual_model == "model-a"`、`response_completed_at == 原时间`（**原时间/模型保留**）；水合结果 metadata 内 provenance 可见 ✓。
- 混合模型逐字段来源：checkpoint payload 的 provenance 由 store 哈希钉死（`payload_sha256` + `_checkpoint_record` L2084-2114 逐字段绑定 attempt），水合时原样透传（qa_engine L177）✓。
- 相关缺口见 P1-2（输出信封侧丢失回执 + created_at 伪造，checkpoint 侧本身正确）。

### PAR-09（预算不双预留/结算、迟到回执幂等、不可重 POST）
- 测试 `test_par_09_late_receipt_settles_once_and_no_repeat_post`：`configure_quick_scan_budget` 注册后 `before_question`（携 budget 对）→ `quick_scan_budget_attempt` 行数 **== 1**（mark 单次预留）✓；时钟 +11s → `recover_expired == "uncertain"`；**`claim(...) is None`（不可重 POST）** ✓；`note_late_receipt` 二次调用（try/except 包裹）后 reserves 仍 == 1、settlement 事件 ≥1 ✓。复跑通过。
- **探针 G 独立复算**（同 policy 真临时库）：
  ```
  after mark:            status=in_flight, in_flight=1        （恰 1 预留）
  after 1st late receipt: status=response_unpriced, http=200, completed_at=1011.0
  2nd call: no exception
  after 2nd late receipt: status=response_unpriced, completed_at=1011.0  （未变 → 未双结算）
  reserves: 1 | settlement events: ['late_receipt']           （恰 1）
  ```
- 双结算护栏在 store（只读参照核对）：`_record_budget_outcome_tx` L1240-1266 对非 in_flight 行做逐字段匹配，一致则 no-op、不一致抛 `WorkConflictError`；`note_late_receipt` 的 late 事件仅在 `previous is None` 时记（L1975-1990）；现有 store 测试（`test_quick_scan_work_store.py` L1150-1153）钉死重复调用幂等 + 冲突 sha 拒绝。
- **LOW-4**：`settle_events >= 1` 是弱断言（若真双结算出 2 条事件也会过）；建议改 `== 1` 并断言 budget 行 `completed_at` 不变。

---

## 5. 诚实性与过度声称审读

### 5.1 四前置是否"真前置"——**部分成立；"record 成功后 save 不会再抛"不成立（P1-1）**
四个前置（verified 身份 / 回执完整 / I05 形状 / actual_model==model_requested）确实**全部位于 record 之前**（L311-351），这点属实。但 `save_answer_checkpoint` 的校验面**大于**这四个前置，record 与 save 之间存在劈叉窗口，且 save 失败后代码只 warning + return（L373），不回退、不补偿：

| save 侧校验（store） | after_question 是否预检 | 实测 |
|---|---|---|
| `description` ≤5000 且无控制字符（L2153，`_safe_text`） | **否** | **探针 A：6001 字 → record 成功、save 抛 `invalid answer description`**；探针 A2：`\x0c` 控制字符同果 |
| `source_urls` ≥1 合法 URL（L2203 → `_canonical_source_urls` L606） | **否**（builder 只过滤非 str，接受空表） | **探针 F：`search_status=executed` + `source_urls=[]` → record 成功、save 抛 `verified search receipt requires source URLs`** |
| `completed_at` 为带时区 ISO（L2202 `_timestamp`） | 否（builder 只查非空 str） | 代码审读（触发面较低但存在） |
| id 字段长度 160/300、request_id strip 后相等（L2188-2206/L2240） | 否 | 代码审读 |
| 租约在 record→save 之间过期（L2224） | 否 | 微秒级竞态，理论存在 |

三类探针的**共同落态**：attempt=`response_available`（已记成功 + 若有预算已结算）、work 仍 `leased`、**checkpoint=0**、事件止于 `response_available`；随后 `recover_expired → uncertain`、`claim → None` —— 该题**永久不可补不可水合**（恢复时 hydrate 未命中 → claim 拒 → error 结果），恢复报告将其列进 unknown_in_flight（尚不算静默，但一个**已成功的回答被降级成永久 unknown**，"逐题返回即持久化"与 JOB-03"成功题留存"对该题失效）。无伪造分数、无双预留、无重复 POST（I05/I12 未破），但 llm_runner L366-369 的注释 "**so a failed save can never strand the attempt after a successful record**" 与 models L331-333 的 "every field `save_answer_checkpoint` requires" 均为**可证伪的过度声称**。无任何测试覆盖此路径。

### 5.2 回执字段同源 + `final_transport_provider` 抽取对输出零影响——**成立，但"共享"声称不成立（P2-2）**
- 同源核对：`execution_receipt_for_checkpoint` 读 `result.answer.metadata`（llm_runner L322-324），`to_quick_scan_dict` 亦读 `result.answer.metadata`（models L466）；provider 判定算法（候选序 `[execution, metadata, *reversed(attempts)]` + 同一谓词）逐字等价（models L498-511 vs L314-324）；actual_model/request_id/response_id/search_status/completed_at/attempt_id/prompt_sha256/search_receipt_id/source_urls 全部同源同式 ✓。
- 对输出回执行为**零改变**：models.py diff 为 **+78/-0 纯新增**，`to_quick_scan_dict` 无一行改动；全量 887 passed、CLI 48 passed 佐证 ✓。
- **但** `final_transport_provider` docstring 称 "Shared by the output envelope … can never disagree" —— **输出信封并未调用它**（仍是内联副本 L498-511，全仓 grep 仅 execution_receipt_for_checkpoint 一处调用）。当前两份实现语义等价（已逐条比对），但"单一事实源"未达成，属潜在漂移风险 + 文档过度声称。

### 5.3 水合是否伪造 created_at/时间——**是，已实测（P1-2）**
施工卡风险条明确："水合路径**不得伪造 `answer.created_at`/执行时间**……只用 checkpoint provenance"。实现（qa_engine L166-183）构造 `Answer(...)` 时**未传 `created_at`**，走 `default_factory=datetime.now`：

- **探针 B**：种子 `response_completed_at = 2020-05-05T05:05:05Z`，水合结果 `answer.created_at = 2026-10-06T03:49:24`（恢复墙钟），`equal: False`。
- 更实质的是**输出信封侧**：`to_quick_scan_dict` 只读 `answer.metadata`（空），水合题的 `execution_receipts` 实测为
  ```
  IQS_05(水合): {"provider": null, "search_status": "not_attempted",
                 "completed_at": null, "actual_model": null,
                 "answered_at": "2026-10-06T03:49:24Z"}
  ```
  即：**已 verified 搜索 + 已存回执的成功题，在跨仓交换包里被序列化成"未联网执行"、无模型、无完成时间，且 answered_at 是恢复时刻的伪造时间**；provenance（含原模型/原时间/回执字段）虽随 `QAResult.metadata` 可见（测试只测到这里），但信封层完全丢弃它。卡面设计 2 的"答案+**回执直出**"在输出层不成立；checkpoint 层（PAR-04 case 断言面）本身正确保留原时间/模型。
- 顺带：`hydrate_question` docstring 自称 "read-only"，实际会 `create_or_attach`（写 work_run_ref/建行）——幂等且与 claim 路径副作用等价（docstring 已自认），措辞不严谨（INFO-1）。

### 5.4 其他
- 四前置的失败方向全部是**回落诚实 unknown**，无任何"降级假成功"分支 ✓（探针 D/E）。
- `recovery_report` 兜底 unknown 状态保守入 unknown_in_flight，无静默丢任务 ✓；但若 checkpoint 行损坏，`list_run_items` 会先抛（fail-loud，报告整体失败）——可接受（INFO-2）。

---

## 6. 范围扫描

- 恰 4 变更面 ✓（§1 表）；store 零改动 ✓。
- `models.py` 改动**仅限**卡允许的"回执组装抽共享函数"：两个新增函数均为回执组装，无其他行改动 ✓（+78/-0）；"抽共享"目的部分达成见 P2-2。
- 新增 `__init__(budget_policy=, budget_route=)` 为**可选参数**，生产构造（llm_runner L933）未传 → `mark_send_intent` 收到 None/None，与 Q06 行为逐字相同（L1681-1685 既有 both-or-neither 守卫）→ **Q09 预算语义未被本批改变** ✓；reserve 逻辑全部是 store 既有 `mark_send_intent` 能力（L1690-1714，本批未改）。
- 无网络/LLM/密钥/真实配置读取 ✓（§1）。
- I17：既有测试零改动、无 skip 新增、分母未动（887 = 881 + 6 纯增量）✓。

---

## 7. Findings

严重度阶梯：**P0** = 不变量破坏/伪造类立即阻断；**P1** = 应修复后再判 verified（卡契约或诚实性实质偏差）；**P2** = 本批应补的测试/声称缺口；**LOW** = 建议；**INFO** = 备忘。**本批无 P0。**

### P1（阻断）

- **P1-1 `after_question` 存在 record 成功 / save 失败的状态劈叉路径，且代码注释对此的否认为过度声称。**
  四前置未覆盖 `save_answer_checkpoint` 的全部校验面（description ≤5000/无控制字符 L2153、source_urls ≥1 合法 URL L2203→L606、completed_at ISO L2202、id 长度、租约竞态）。三类独立探针实证（`%TEMP%\q07_independent_probe*.py`）：
  - A：description 6001 字 → `record_attempt_outcome(response_available)` 成功 → save 抛 `invalid answer description`；
  - A2：文本含 `\x0c` → 同果；
  - F：`source_urls=[]` 且 `search_status=executed`（builder 接受、store 拒绝）→ 同果 —— **此触发面最现实**（零结果搜索/无 URL 的搜索回执）。
  落态：attempt=`response_available`（预算若已绑则已结算）、work 持续 `leased` → 租约到期 `uncertain` → 永久 `claim=None`，checkpoint 恒 0；该成功题在后续 run **既不水合也不补问**（JOB-03"成功题留存"失效），只能以 error/unknown 面孔出现。无伪造/无双花（I05/I12 未破），但 llm_runner L366-369 注释 "a failed save can never strand the attempt" 与 models L331-333 "every field save requires" 均被实测证伪；**无任何测试覆盖**。
  修复方向：record 之前预检 save 的全部确定性校验（description 长度/字符、completed_at ISO、source_urls ≥1 合法、id 长度），或对 save 失败做补偿收口（如实落 unknown/保留结果证据），并补劈叉回归测试。

- **P1-2 水合路径伪造 `answer.created_at`，且回执在输出信封侧丢失，违反施工卡风险条与设计 2。**
  卡面："不得伪造 answer.created_at/执行时间……只用 checkpoint provenance"、"答案+回执直出"。实测（探针 B）：水合 `created_at` = 恢复墙钟（≠ provenance 原时间）；`to_quick_scan_dict`（只读 `answer.metadata`）对水合题输出 `provider=null / search_status="not_attempted" / completed_at=null / actual_model=null / answered_at=恢复时刻` —— 已 verified 的成功题在交换包里变成"未联网 + 伪时间"。checkpoint 层（PAR-04 断言面）正确，但输出层与卡面直接冲突，且触及 I27"复用旧回答不改时间"的注册表语义（I27 非本批 invariant，仅作影响面说明）。无测试覆盖。
  修复方向：水合时 `Answer(created_at=<provenance.response_completed_at 解析>)`，并把 provenance/回执并入 `answer.metadata`（或让信封识别 `answer_checkpoint`），补"水合题信封回执 = 原模型/原时间"断言。

### P2（本批应补）

- **P2-1 JOB-04 测试对桶归属的断言不完整**：C（checkpoint 点）只断言 `isinstance(..., list)` 而非 `C.id in report["persisted"]`（实现正确但桶序回归抓不住）；D（导入 ACK 前）crash 点从未实例化（`import_ack_pending` 恒空、该桶逻辑零执行）；`cancelled` 桶在报告场景无实例；"派发前无费用"无预算断言（JOB-04 测试未配置 budget）。
- **P2-2 `final_transport_provider` 的"与输出信封共享"声称不成立**：信封仍是内联副本（models L498-511 未改为调用该函数）。当前语义等价、输出零变化（diff 纯新增 + 887/48 通过），但 docstring（L309-313）承诺的"can never disagree"是假的，存在日后漂移风险。应接线信封或改写 docstring。

### LOW

- **LOW-1 `cancel_pending_work` 零测试、生产零调用**：JOB-05 测试直打 `store.cancel_pending`；包装函数（L459）语义由本审查探针 C 实测正确（cancelled / refused:WorkConflictError / refused:KeyError、幂等、具名拒绝），建议补一条包装层测试。
- **LOW-2 JOB-03 未断言 fresh 2 题"不假全成"**（未落 checkpoint、attempt 不记成功）；行为经探针 D 复证正确但未被测试钉住。
- **LOW-3 LLM-07 引擎路径未测**：测试直打 store；`after_question` 对 no-search/非 2xx 的回落靠代码审读（receipt builder 返回 None → Q06 路径），建议补一条引擎级用例；"修复预算硬顶"在 Q03/CLI 面（`test_quick_scan_cli.py` format_repair 断言），本文件未触。
- **LOW-4 PAR-09 `settle_events >= 1` 弱断言**：改成 `== 1` 并断言 budget 行 `completed_at` 不变（探针 G 显示现行为恰为单次结算）。

### INFO

- **INFO-1** `hydrate_question` docstring "read-only" 措辞不严谨：它会 `create_or_attach`（建行/挂 run），但幂等且与 claim 路径副作用完全等价（L182-198 同参），无完整性影响。
- **INFO-2** `recovery_report` 对每题二次查询 checkpoint（`list_run_items` 的 `entry["checkpoint"]` 已含），冗余只读开销；checkpoint 行损坏时 `list_run_items` 先抛 → 报告 fail-loud（可接受）。
- **INFO-3** budget 对接缝当前仅测试侧传入；生产构造不传（Q06 语义保持）。Q09 接线时注意与 transport 的 `begin_quick_scan_send`（quick_scan_work_transport L457-463，自带 budget 对 reserve）勿对同一 attempt 双路径预留——非本批范围，留给 Q09。
- **INFO-4** `recovery_report` 对未知状态兜底入 `unknown_in_flight`（保守列出、不重 POST），无静默丢任务 ✓。

---

## 8. 裁决

**needs_revision**

理由：门全绿（定向 123 / 全量 887+4sk / Q06 15 / CLI 48 / mypy / black / ruff / diff --check）、六 case 测试语义基本落地、Q06 契约与 I05/I12/I17 均未见破坏、范围恰好 4 变更面——但审查清单第 4 项的两个诚实性问题**均被独立探针证伪**：

1. **P1-1**：`record 成功 → save 失败` 劈叉路径真实存在（≥3 类可复现触发，含现实的 `source_urls=[]`），把成功题永久降级为 uncertain 且代码注释否认其存在；无测试。
2. **P1-2**：水合伪造 `answer.created_at`、输出信封把已验证成功题序列化为 `search_status="not_attempted"` + 恢复时刻伪时间——直接违反施工卡风险条与"回执直出"设计；无测试。

两处均为小改动 + 各补一条回归测试即可收敛（store/Q06 面无需动）。修复后复审（重点复跑：探针 A/A2/F 落态、探针 B 信封字段、两仓门八项）可改判 approved。

---

### 附：独立探针清单（`%TEMP%\q07_independent_probe.py` / `_f.py` / `_g.py`，离线）

| 探针 | 结论 |
|---|---|
| A / A2 | description 超长 / 控制字符 → record 成功 + save 抛 → attempt=response_available、work=leased→uncertain、checkpoint=0、claim=None、报告列 unknown_in_flight（**P1-1 实证**） |
| F | `source_urls=[]` → 同上劈叉（**P1-1 最现实触发**） |
| B | 水合 2 题零重派发；`created_at`=恢复墙钟 ≠ provenance 原时间；信封 `provider=null/search_status=not_attempted/answered_at=伪时间`（**P1-2 实证**） |
| C | `cancel_pending_work`：cancelled / refused:WorkConflictError / refused:KeyError、幂等、created 事件保留 |
| D | 无回执 → Q06 honest-unknown（attempt/work=uncertain、claim 拒、checkpoint=0） |
| E | actual_model ≠ model_requested → Q06 honest-unknown（第四前置实证） |
| G | PAR-09：mark 恰 1 预留、迟到回执单次结算（completed_at 不变）、二次调用 no-op、reserves=1、late_receipt 事件恰 1 |

---
---

# r2 聚焦复核（2026-10-06 round-63 后，对 r1 处置的独立复验）

复核方式：全部门由本审查独立复跑；r1 的三类劈叉探针（A/A2/F）与水合探针（B）对整改后代码原样复跑；`_preflight_checkpoint` 与 `save_answer_checkpoint` 逐条对照；处置消息的每条声称对照实况代码。门数字以本节自跑为准。

## r2-1 门复跑（自跑）

| 门 | 命令 | 结果 |
|---|---|---|
| Q07 定向 | `pytest tests/unit/test_q07_checkpoint.py -q -p no:cacheprovider -o addopts=` | **8 passed**（2.07s，含 `test_p1_1_precheck_falls_back_without_strand`、`test_p1_2_hydration_keeps_original_time_and_envelope_receipt`） |
| 六文件回归电池 | Q07+Q06+qa_engine+llm_runner+basic_runner+work_store | **125 passed**（11.37s）= r1 123 + 新 2 |
| 全量 | `pytest tests/ -q -p no:cacheprovider -p no:base_url -o addopts=` | **889 passed, 4 skipped, 0 errors**（65.82s）= r1 887 + 新 2 |
| Q06 回归 | `pytest tests/unit/test_q06_work_binding.py` | **15 passed**（文件未动） |
| CLI 集成 | `pytest tests/integration/test_quick_scan_cli.py -p no:base_url` | **48 passed** |
| mypy | 4 源文件 | **Success: no issues found** |
| black(100) / ruff / `git diff --check` | 四文件 | 4 files unchanged / All checks passed / exit 0 |

## r2-2 (a) P1-1：预检是否真覆盖 save 确定性面 —— **行为面通过；一处 r1 点名的过时注释未改（见 r2-5）**

**逐条对照 `save_answer_checkpoint`（store L2137-2228）↔ `_preflight_checkpoint`（llm_runner L423-486）**，全部使用 store 自己的校验器（函数内 lazy import `_ENTITY_ID/_safe/_safe_text/_sanitized_receipt/_timestamp/_canonical_source_urls/quick_scan_receipt_sha256`），且传给 record/save 的是**同一个未变形对象**（无中途转换 → 无漂移缝隙）：

| save 校验（行号） | preflight（行号） | 判定 |
|---|---|---|
| 答案恰五键（L2139-2146） | L439-446 | 同式 ✓ |
| `_ENTITY_ID.fullmatch(_safe(entity_id))`（L2149） | L447 | 同 ✓ |
| question_id `_safe`（L2148） | L449 | 同 ✓ |
| status∈四值集（L2154-2160） | L450-456 | 同 ✓（非 str/不可哈希在更早的 `shape_ok` 就被 Exception 兜住） |
| I05 分数规则（L2161-2165，`type is int`/1-10/非 scored 必 null） | L457-462 | 同式 ✓ |
| description `_safe_text ≤5000` 无控制字符（L2153） | L463 | 同 ✓（r1 探针 A/A2 触发面） |
| receipt dict + `_sanitized_receipt` 非空（L2174-2178） | L464-468 | 同 ✓ |
| search_status=executed（L2179）/ provider∈三值（L2181-2187） | L469-472 | 同 ✓ |
| actual_model/response_id/attempt_id/search_receipt_id `_safe_text` 160/300/300/300（L2188-2195） | L473-476 | 同 ✓ |
| response_status=completed（L2196）/ http int 2xx（L2198-2201） | L477-481 | 同 ✓ |
| `_timestamp(completed_at)` ISO+tz（L2202） | L482 | 同 ✓（r1 列的 completed_at 触发面） |
| `_canonical_source_urls` 非空规范（L2203→L606） | L483 | 同 ✓（r1 探针 F 触发面） |
| request_id `_safe_text ≤300`（L2204-2206） | L484-485 | 同 ✓ |
| `quick_scan_receipt_sha256`（L2207） | L486 | 同 ✓ |
| 事务内状态断言（`_assert_lease` L2224、attempt 相位/租约/sha/http/request/model 匹配 L2229-2243、状态 CAS L2301-2308、已存检查点幂等/冲突 L2214-2223） | 不可预检（依赖 record 时刻状态） | 由 `recorded` 标志分流：record 失败→诚实 unknown（L390）；record 成功后 save 异常→不双记录、交恢复（L385-389）✓ |

**独立探针复跑（我 r1 的原探针脚本，未改一行）**——三类劈叉态全部消除：

- 探针 A（描述 6001 字）→ `检查点预检拒绝（invalid answer description）——零状态降级为诚实 unknown`；attempt=**uncertain**（events 止于 `unknown`，**无 `response_available`**）、work=uncertain、checkpoint=0、claim=None、recovery_report 列 unknown_in_flight ✓
- 探针 A2（`\x0c` 控制字符）→ 同上 ✓
- 探针 F（`source_urls=[]` 且 executed）→ `预检拒绝（verified search receipt requires source URLs）` → 同上 ✓
- 即 r1 P1-1 的"成功回执落库一半"状态（response_available + 无 checkpoint + 预算按成功结算）不再可达；三例现在是 Q06 语义下的诚实 unknown（listed、不重 POST、I12 合规）。

**测试**：`test_p1_1`（L528-620）正是三探针面 + 漂移探测对（同一输入直调真 save 必抛 ValueError、且其 attempt 永不停在 response_available）✓ 复跑通过。

**残余（如实记录）**：record→save 之间的非确定性窗口（租约在两相邻调用间过期、磁盘/DB 错误、进程崩溃）仍可产生"已收执、未存档"，由 L385-389 如实处理（不双记录、日志、恢复报告列为 unknown_in_flight，无静默丢任务）——在 store `save/get` 本批禁改的约束下可接受，属 Q06 既有的对账域语义。

## r2-3 (b) P1-2：水合原时与信封回执 —— **通过**

- **探针 B 复跑**（原脚本未改）：水合 `answer.created_at = 2020-05-05T05:05:05+00:00`，与 `provenance.response_completed_at` **equal: True**（非墙钟）✓；`envelope[IQS_05] = {provider: "mimo", search_status: "executed", completed_at: "2020-05-05T05:05:05Z", actual_model: "model-a", answered_at: "2020-05-05T05:05:05Z"}` ✓ 原回执完整；`answers` score=8、source_urls 自 provenance 恢复 ✓；未执行的假答案 IQS_09 仍如实 `not_attempted` ✓；provider 调用仅 1（水合零派发）✓。
- `_utc_isoformat` 路径：`_checkpoint_created_at` 产出 tz-aware datetime（`fromisoformat(raw.replace("Z","+00:00"))`），信封 `answered_at` 实测回 `…Z`，与 `test_p1_2` 断言（`created_at == fromisoformat("2026-10-06T01:00:00+00:00")`、`answered_at == "2026-10-06T01:00:00Z"`、`provider.calls == 0`、http 200、score 8）一致 ✓。
- 解析失败回退默认墙钟的分支：对真实 checkpoint 不可达（store save L2111 已 `_timestamp` 钉死 ISO+tz），仅防御性 ✓。
- `_provenance_metadata` 只从 store 哈希钉死的 provenance 拷贝，无凭空字段（execution/attempts/search_status/source_urls 全部有源）✓。

## r2-4 (c) P2-1 / P2-2 —— **均通过**

- **P2-1**：JOB-04 现为五项精确成员断言——A∈pre_dispatch、B∈unknown_in_flight（短租约真过期）、`wid_c ∈ persisted`、D 实例化（raw attach + SQL 置 `result_ready`、无 checkpoint → `import_ack_pending`，注释如实"modeled by state, never by fabricating a checkpoint"）、E 经 `cancel_pending_work` → `cancelled` 桶（顺带给包装函数补了测试）；`quick_scan_budget_attempt COUNT == 0`（派发前无费用）；分区断言跨 5 项、无重叠、总数==`list_run_items` ✓（读 L251-319 + 复跑）。
- **P2-2**：diff 实证 `to_quick_scan_dict` 内联 `next(...)` 已**替换**为 `final_transport_provider(*provider_candidates)`（models L498-503）。谓词等价复核：候选序 `[execution, metadata, *reversed(attempts)]` 同、provider 集合同、`response_id or type(http) is int` 谓词同、`isinstance(provider,str)` 冗余但不改值 → 输出行为不变，由 **CLI 48 passed + 全量 889 passed** 复跑佐证 ✓；`final_transport_provider` 的 "Shared by the output envelope" 现为真 ✓（r1 P2-2 消除）。

## r2-5 (d)/(e) 与诚实性复核 —— **Q06 不破坏、范围合规；发现 1 处处置声称与实况不符（唯一阻断项）**

- Q06：15 项原样 + 电池 125 ✓；探针 D（无回执）/E（模型不匹配）复跑仍为 honest-unknown + claim 拒 ✓；qa_engine diff **+89/-0 纯新增**（拒绝分支、`work_item_lifecycle is None`、getattr 守卫零改动）✓；hydrate docstring 已按处置改为「idempotent ATTACH plus a read-only lookup」✓（INFO-1 消除）。
- 范围：恰 4 变更面（models +82/-13、qa_engine +89/-0、llm_runner +273/-11、test_q07 656 行 8 用例）；store 零改动；新测试仅 sqlite3/hashlib，无网络/密钥/真实配置 ✓；preflight 为函数内 lazy import store 私有校验器——新增的唯一跨模块私有耦合，有 `test_p1_1` 钉住（INFO）。
- 卡 §r1 处置记录（卡 L47-53）逐条核对：P1-1 预检/recorded 分流、P1-2 原时+信封、P2-1 五项、P2-2 接线、LOW 四项、INFO-Q09 入卡 —— **卡内记录与实况相符** ✓。
- **P2-r2-1（阻断）：处置消息声称"原注释 `failed save can never strand` 已删换成与实现一致的分层说明"——不实。** 该注释**原样保留**在 `llm_runner` L309-315（"so a failed save can never strand the attempt after a successful record … (no fabricated success, no stranded state)"，grep 全仓仅此一处），与同函数 L385-389 自己刚加的 `recorded` 分支注释（"phase already committed to response_available … lease recovery owns the rest"）**直接矛盾**——record→save 的非确定性窗口（崩溃/租约竞态/DB 错）恰恰说明"never strand"绝对化仍不可成立。该句正是 r1 P1-1 点名的两处"可证伪过度声称"之一；另一处 `models.execution_receipt_for_checkpoint` docstring（"every field `save_answer_checkpoint` requires / the question stays refillable"，r1 同点名）同样**未改**——预检落地后其系统级后果（假成功/劈叉）已消除，但字面仍可证伪（`source_urls=[]` 可过 builder 后被预检拒）。
  处置要求（纯注释，零行为改动）：① 删除或改写 llm_runner L309-315 的绝对化表述，使其与 L350-353/L385-388 的分层说明一致（例："every deterministic input precondition is pre-checked before any state is recorded; non-preflightable failures after record are never double-recorded and are handed to lease recovery"）；② 收窄 models docstring 的 "every field" 措辞（或改为"其余 save 面由 `_preflight_checkpoint` 在落态前补齐"）；③ 更正处置消息中"已删"的表述。

## r2-6 裁决

**needs_revision**（唯一阻断项 = P2-r2-1 注释/处置一致性；**行为面 r1 全部 findings 已验证修复**）

- 已独立复验达标：P1-1 行为（三探针复现面全部消除、漂移探测对存在）、P1-2（原时 + 信封原回执）、P2-1（五桶精确成员 + 预算零）、P2-2（接线等价 + 输出不变）、全部 LOW（包装测试/fresh 断言/settle==1/hydrate docstring）、门全绿（8/125/889+4sk/Q06 15/CLI 48/mypy/black/ruff/diff）、Q06 契约不破坏、范围恰 4 面、离线无密钥。
- 阻断理由：r1 点名的过度声称注释未按处置声称"删除"，且保留的绝对句与新代码分支自相矛盾——属诚实性维度未闭环，不接受带假声称收批。
- 复审预期：纯注释 + docstring 措辞改动 → 门八项原样复绿即可判 **approved**（无需重跑探针，行为不变；我将 grep 确认 "never strand" 消失与处置表述更正）。

---
---

# r3 终审（2026-10-06 round-65，P2-r2-1 三件注释事项复验）

门全部本审查自跑；探针按 r2 预期未重跑（行为零改动，已用代码与门佐证）。

## r3-1 门复跑（自跑）

| 门 | 结果 |
|---|---|
| 全量 `pytest tests/ -p no:base_url -o addopts=` | **889 passed, 4 skipped, 0 errors**（69.14s，exit 0）——与 r2 同口径 |
| 六文件电池（Q07 8 + Q06 15 + qa_engine/llm_runner/basic_runner/work_store） | **125 passed** |
| CLI 集成 | **48 passed** |
| mypy（4 源文件）/ black(100) / ruff / `git diff --check` | Success / 4 files unchanged / All checks passed / exit 0 |

行为零改动佐证：`recorded` 分支（llm_runner L363-393）与 r2 逐字一致（读文件核）；numstat 增量仅 models +2、llm_runner +3、qa_engine +0（注释/docstring 行数增长）；测试计数不变（8/125/889）。

## r3-2 核查点 (a)–(f)

- **(a) 禁句 grep**：`git grep -E "never strand|no stranded state"`（tracked）= **0 命中**（exit 1）；`src/` = 0。`tests/` 有 1 处命中——`test_q07_checkpoint.py` L532 测试 docstring "…never **stranded** at response_available with no checkpoint"：这是对**已修复不变量的正向描述**（预检拒绝的输入绝不停在 response_available——探针 A/A2/F 实证为真），非 r2 禁止的"save 失败永不分叉"绝对化声称，**判为可接受**（区别记录于此）。
- **(b) 新头注释自洽**：llm_runner L309-318 改为分层表述——"EVERY deterministic input precondition is pre-checked before any state is recorded … non-preflightable window after a committed record (crash / lease race / DB error) is never double-recorded and is handed to lease recovery. Anything less stays on the Q06 honest-unknown path (no fabricated success)"。与同函数 L388-392 `recorded` 分支（"never double-record; lease recovery owns the rest"）**逐义一致**，无绝对化句；原 "can never strand" 与 "no stranded state" 已消失 ✓。
- **(c) models docstring 收窄**：`execution_receipt_for_checkpoint`（L326-336）现为 "…the **identity-bearing fields the checkpoint needs** (actual_model / response_id / attempt_id / search_receipt_id). The **remaining save-side input rules are enforced by `_preflight_checkpoint` in llm_runner BEFORE any state is recorded**; … NO checkpoint is persisted — never a fabricated success"；"every field save requires" 与 "stays refillable" 均已删除。字面与实现相符（builder 自查面如实枚举、其余明确指派预检）✓。
- **(d) 处置更正留痕**：IQS `git log` 实核 —— `76efd65 docs: Q07 r2 P2-r2-1 correction — false '已删' claim retracted, comment/docstring rewrite recorded`；卡 L55-57「r2 findings 处置记录」写明"前一轮处置消息中『原注释已删』为**不实陈述**（实际未删）——此处更正"并记录本轮真正改写内容与 grep 复核 ✓。假声称已在持久化工件与本轮消息双重更正，诚实性闭环 ✓。
- **(e) 门**：见 r3-1，八项全绿，全量 889 口径与 r2 相同 ✓；范围仍恰 4 变更面（models +84/-13、qa_engine +89/-0、llm_runner +276/-11、test_q07 新增 8 用例），store 零改动 ✓。
- **(f) 终裁依据**：r1 全部 findings（2×P1 + 2×P2 + 4×LOW）与 r2 唯一阻断项（P2-r2-1 三件事项）均已独立复验关闭；Q06 契约、I05/I12/I17、六 case、离线/无密钥全部达标。

## r3-3 遗留（全部非阻断）

- **LOW-3 残余**：`test_p1_1` 已提供 after_question 引擎级用例（预检拒绝面），但 receipt-builder 返回 None 的引擎级用例（无搜索/非 2xx 经 `after_question`）仍仅由审查探针 D 覆盖——保留为后续建议，不阻断。
- **INFO-2/3/4**（recovery 双查、Q09 双预留接缝已入卡随 Q09 处理、未知状态兜底列出）保持备忘。
- StockQA 改动仍未提交（3 M + 1 新测试）；隔离提交应严格限于此 4 变更面（已核 `git status -- src/ tests/`）。

## r3-4 终裁

**approved**

门全绿（全量 889+4sk / 电池 125 / Q06 15 / CLI 48 / mypy / black / ruff / diff --check）、三轮 findings 全部闭环并经独立复跑/探针/逐行对照复验、处置声称与实况一致（含假声称的正式更正）、范围恰 4 变更面、Q06 契约与 I05/I12/I17 无破坏。可进行 StockQA 隔离提交并关闭 Q07。
