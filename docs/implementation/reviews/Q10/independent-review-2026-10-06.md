# Q10 独立审查报告 — 结果 outbox 与投递回执消费批次

- 审查者：独立审查（与实现者无关，双仓只读，唯一写入=本报告）
- 日期：2026-10-06
- 被审对象：StockQAbyLLM 两个新增文件 `src/utils/quick_scan_c06_adapter.py`（201 行）+ `tests/unit/test_q10_delivery.py`（427 行，5 测试）
- 语义输入：任务卡 tasks.json id=Q10（steps 1-5、case_ids=JOB-07/JOB-08/DB-07/LLM-08/PAR-10、invariants I01/I12）、acceptance-cases.json 对应 case、decision-register.md I01/I12、施工卡 `reviews/IQS-lane/Q10-outbox-card-2026-10-06.md`
- 裁决：**approved**（无 P0/P1/P2；2 LOW + 5 INFO，见 §7；LOW-2 为 verified 翻转前的记录修正项）

---

## 1. 范围

本批 = C06 适配器（`build_c06_package` + `MissingC06Fields`）+ 5 条 Q10 测试。runner（llm_runner）接线**未实施**（见 §5）。禁改面（outbox 校验面、work_store delivery 状态机、Q06/Q07/Q09 已验证面）经 diff 核证零改动。LLM-08（owner=Q05）仅登记边界，未执行本体（见 §6）。

## 2. 门独立复跑（全部独立执行，命令+数字）

| 门 | 命令 | 实测 | 预期 |
|---|---|---|---|
| Q10 定向 | `python -X utf8 -m pytest tests/unit/test_q10_delivery.py -q -p no:cacheprovider -o addopts=` | **5 passed** in 2.29s | 5 passed ✓ |
| 电池（8 文件） | 同 flags，`test_q10_delivery.py test_q06_work_binding.py test_q07_checkpoint.py test_q09_budget_concurrency.py test_qa_engine.py test_llm_runner.py test_basic_runner.py test_quick_scan_work_store.py` | **138 passed** in 17.50s | 138 ✓ |
| 全量 | `python -X utf8 -m pytest tests/ -q -p no:cacheprovider -p no:base_url -o addopts=` | **902 passed, 4 skipped** in 76.94s，0 errors | 902/4sk/0 ✓（897 基线+5 新测） |
| mypy | `mypy src/utils/quick_scan_c06_adapter.py src/core/qa_engine.py src/runners/llm_runner.py src/core/models.py main_with_llm.py` | **Success: no issues found in 5 source files** | Success ✓ |
| black | `black --check -l100` 两新文件 | **2 files would be left unchanged**，exit 0 | ✓ |
| ruff | `ruff check` 两新文件 | **All checks passed!**，exit 0 | ✓ |
| `git diff --check` | — | exit 0，无 whitespace 错误 | ✓ |

## 3. 适配器正确性（含独立探针）

### 3.1 探针方法（独立于实现者测试）

审查者自写探针（Temp：`q10-independent-review-probe.py`，92 项检查**全部通过**，exit 0）：经真实 store 生命周期（create_or_attach→claim→prepare_attempt→send_intent→record_attempt_outcome→`save_answer_checkpoint`）构造 Q07 形 checkpoint record，**全部取值与实现者测试不同**（entity UUID、题号 IQS_PROBE_A..D、provider=minimax、model=probe-model-v9、authority 五键取 9.8.7/3.2.1 等异值）；三级内容寻址用**审查者自己的 canonical JSON**（`json.dumps(sort_keys, ensure_ascii=False, separators=(",",":"), allow_nan=False)` + sha256）重算，不复用被审模块函数。

### 3.2 正向：build → 双校验全过 + 逐字段溯源

- `validate_exchange_package(adapter 输出)` 全过；`validate_checkpoint_binding(adapter 输出, 真 checkpoint record)` 全过（探针 A1/A2）。
- 三级哈希逐项重算一致：`observation_id = obs_sha({entity_id,question_id,scope})`、`payload_sha256 = sha(observation)`、`item_id = itm_sha({observation_id,payload_sha256})`、`package_sha256 = sha(body 去双 id)`、`package_id = pkg_+package_sha256`（A3-A7）；同输入重建 canonical 字节逐位相同（A8，确定性）。
- **逐字段溯源（29 项对照 outbox L221-305 绑定契约，探针 T 系列）**：observation identity（entity_id/question_id/scope/security_id/segment_id）← payload.work+answer；answer{question_id/response_kind/score/summary/status} ← saved answer（status 仅 scored/insufficient_evidence/not_applicable 三值映射）；evidence[].url 集合 == provenance.source_urls 集合；execution 九字段（provider←actual_provider、model_requested、model_resolved←actual_model、request_id、attempt_id←provider_attempt_id、search_status、search_receipt_id、prompt_sha256←provider_prompt_sha256、answered_at←response_completed_at）逐一相等；envelope 权威字段（producer component_version/build_id、required_capabilities、contract_versions）== authority 输入；producer.component/consumer/data_class/document_payloads_included/extensions 为 C06 契约常量且被 `validate_exchange_package` 精确键集强制；无 `_FORBIDDEN_KEYS` 键；恰 1 item。**无任何推造字段。**

### 3.3 反例矩阵（全部 `MissingC06Fields`，共 24 子例）

authority={}；contract_versions 逐一缺 5 键之一；键值空白；capabilities/producer_component_version/producer_build_id 缺失；capabilities 含未知 token；capabilities 缺 standard_observation_v1；answer.status=unknown；status 越表词；work/answer question_id 不一致；provenance 缺 provider_prompt_sha256；8 个执行字段置空白逐例。另有：scored + source_urls 空 → MissingC06Fields；checkpoint_schema 非法 → MissingC06Fields。对照组：insufficient_evidence + 无 URL **可**打包且过双校验（evidence 仅 scored 强制，探针 B14）——与绑定契约一致。

## 4. 四 case 语义（测试断言 + 独立复跑双重证据）

- **DB-07**（测试 `test_db_07_...` + 探针 C1-C7）：authority 缺 → build 抛 `MissingC06Fields` → `mark_result_delivery_blocked` 后 work_item 保持 `result_ready`、delivery row `blocked`+block_code、无 package_json；同题再 `before_question` → `claimed=False`（**不重问**，探针 C4 实证）；authority 可用后 build 成功 → `prepare_result_delivery` blocked→ready、block_code 清空、封存过双校验（C5/C6）。
- **JOB-07**（测试 `test_job_07_...` + 探针 C8-C15）：封存→`begin_result_delivery` → state=send_uncertain、`request_bytes==package_bytes`、`idempotency_key==delivery_key(=outbox.delivery_key(package_id,item_id,payload_sha256))`；`confirm_result_delivery_not_sent`→ready→再 begin **同字节同 key**；精确 ACK（package/item/observation/payload 四元精确匹配 + namespace/store）→ delivery=delivered 且 **work_item=delivered**；重复同一 ACK 幂等（同 ack_json）；事件链 `package_prepared→send_intent→confirmed_not_sent→send_intent→accepted`（C15，且证不重发模型——全程 0 次模型调用，结构上无 provider）。
- **JOB-08**（测试 `test_job_08_...` + 探针 C16-C19）：异包 ACK（B 之四元组施于 A）→ `ValueError: ... does not match outbox`，原行保持 `send_uncertain`+`ack_json=None`（不伪造 delivered）；无 prepared delivery 的 ACK → 拒（`... not prepared`）；错 namespace consumer ACK → 拒（探针 C19）。
- **PAR-10**（测试 `test_par_10_...` + 探针 C20-C24）：**格式正确但 payload_sha256 错**的假 ACK → 拒；错 item_id、错 package_id 的假 ACK 各自 → 拒；state 保持 `send_uncertain`、`ack_json=None`；封存 `package_json` 内 observation summary 与 package_sha256 **原文未覆盖**；仅精确 ACK 解除不确定（C24）。`confirm_result_delivery_not_sent` 白名单外 reason（"maybe_lost_somewhere"）→ 拒（C11，只有证明未发出才可重臂）。
- **LLM-08**：owner=Q05，本批仅登记边界（`_FORBIDDEN_KEYS` 白名单已在 outbox 模块 L28-41 并在 L196-197 强制；探针实证 adapter 输出无禁键）；无越权执行、无声称。

## 5. runner 接线状态评估

- **实况**：`grep` 全量核证 `src/runners/llm_runner.py` 无任何 `c06_adapter/build_c06_package/delivery/MissingC06Fields` 引用——**接线未实施**。
- **记录一致性**：GREEN 记录（progress.md L1805、task_plan.md L1214）只声称 adapter+测试+门数字，**未声称接线**——如实 ✓。但 task_plan.md L1215（未完成项）括注「（2 新文件：adapter/test_q10；**runner 接线按卡最小**）」易被误读为提交将含接线，LOW-2 建议修正后再翻 verified。
- **是否属于本批应交付**：判定**可延迟**。依据：(i) 四个 Q10 case 全部在 store 层可完整验收且已被测试+本审查双重覆盖；(ii) 卡允许改动清单将 llm_runner 列为「允许（最小）」而非必须；(iii) Q10 首段验证契约（`contracts/validation-Q10-result-outbox-2026-09-27.md`）已明确「public runner not yet wired → Q10 remains partial，只验收 producer-side」，本批不改变该边界；(iv) 剩余接线=检查点落定后 `list_result_ready_without_delivery` → build/`MissingC06Fields`→`mark_result_delivery_blocked` / 成功→`prepare_result_delivery` 的薄封装，store 侧通路已全测。**条件**：Q10 翻 verified 前记录须显式注明 runner 未接线（不得以沉默带过），且不得声称端到端投递闭环。

## 6. 范围/诚实性

- `git status --porcelain`：src/tests 下**恰 2 个 untracked 新文件**；`git diff`/`git diff --cached` 对 tracked 文件均为空 → outbox 校验面/work_store/Q06/Q07/Q09 **零改动** ✓（其余 `.codegraph/`、`nul`、`pilot_runs/*` 等为既有 untracked 杂物，不在范围）。
- 无网络/无 LLM 调用/无密钥：adapter 仅 import typing+outbox 助手；测试/探针全部用假 receipt+临时 sqlite（tmp_path/tempfile）。
- 门数字声称与实测一致（5/138/902+4sk/mypy/black/ruff）；RED→GREEN 声称（2 失败/3 过）与测试文件结构吻合（2 个 import adapter 的测试在 RED 期收集失败）。
- 测试内联 `_build_package` 与 adapter 同映射——使 adapter 漂移会被 store 真校验器夹住，属合理测试设计而非重复实现造假。

## 7. Findings

**P0/P1/P2（阻断）：无。**

- **LOW-1**：store 侧跨字节封存替换分支（`quick_scan_work_store.py` L2540-2543 `package is immutable`）与 blocked 覆写拒绝分支（L2490）**无任何测试钉住**（全 tests/ grep 无匹配；DB 级 immutable 触发器已钉于 test_quick_scan_work_store L1525-1559，故仅是纵深防御缺口）。本审查探针 C25（同 checkpoint、异 producer_build_id → 异 package_sha256 → prepare 拒 "immutable"）已实证该分支行为正确。建议随隔离提交补 1 条单测。
- **LOW-2**：task_plan.md Phase 82 待办行 L1215 括注「runner 接线按卡最小」与实况（未接线）不符（前瞻措辞、非完成声称）；翻 verified 前改为显式「runner 接线本批未做，留待下一小卡/批」。

- **INFO-1**：test_q10_delivery.py 模块 docstring L10-11 残留 RED 期句子「RED phase: the C06 adapter does not exist yet.」（GREEN 期已不成立）。
- **INFO-2**：卡勘察行称 created_at 属「不可从 checkpoint 推造」的 authority 输入，实现取 `created_at = provenance.response_completed_at`。该选择确定性、可溯源，且是同字节幂等重封存（blocked→ready 重建不换字节）的必要条件（wall-clock 会让重建字节漂移、破坏封存不可变契约）——实现优于卡的表述，建议卡面加一行勘误即可。
- **INFO-3**：adapter 对空白/非法 source_url 条目是**静默过滤**（L131-136）而非抛错。真实通路不可达（Q07 落盘时 `_canonical_source_urls`→`_safe_text` 拒空白；封存时 `validate_checkpoint_binding` L278 亦拒），且只丢弃不发明；建议改抛 `MissingC06Fields` 以与绑定契约严格一致。
- **INFO-4**：JOB-08「无 prepared delivery」用例经**不存在的 work_item_id** 钉住（测试 L360-363）；本审查探针 C18 以更严格变体（已 checkpoint、未 prepare 的真实 work item）实证同样拒绝（`... not prepared`）。测试可加严，语义已成立。
- **INFO-5**：LLM-08 边界登记正确：`_FORBIDDEN_KEYS`（outbox L28-41）+ 观察体禁键校验（L196-197）即登记面；adapter 输出经探针实证无禁键；无 Q05 本体执行与越权声称。

## 8. 裁决

**approved** — 可进入 StockQA 隔离提交（恰 2 新文件）。条件建议：随提交或记录更新落实 LOW-1（补跨字节拒单测，可直接采用探针 C25 场景）与 LOW-2（L1215 措辞修正 + 显式记录 runner 未接线）；Q10 整体仍为 partial（producer-side，W05 真实接收端未接，与首段验证契约口径一致）。

— 独立审查，2026-10-06
