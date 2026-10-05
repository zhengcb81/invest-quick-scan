# Q06 收尾批次独立审查报告（2026-10-05）

审查者：独立审查（与实现者无关）。本报告所有结论均来自本人复算/复跑与源码逐行审读，未采信施工卡或实现者的过程描述。

## 1. 范围

- **权威输入**：`docs/implementation/reviews/IQS-lane/Q06-closeout-card-draft-2026-10-05.md`（范围与门）、`docs/implementation/tasks.json` id=Q06（steps/case_ids=JOB-01/JOB-02/PAR-12/JOB-10/JOB-11、invariants=I02/I12/I54、completion）、`docs/implementation/acceptance-cases.json`（上述 5 case 的 given/when/then）、`docs/implementation/decision-register.md`（I02/I12/I54 定义）。
- **被审改动**：StockQA 仓 `C:\Users\郑曾波\Projects\StockQAbyLLM` 未提交改动。`git status --porcelain` + `git diff --stat` 实测：**恰 3 个 tracked 文件被修改**（`src/core/qa_engine.py` +57、`src/runners/llm_runner.py` +212、`main_with_llm.py` +7）**+ 1 个新增 untracked 测试**（`tests/unit/test_q06_work_binding.py`），共 4 文件；`src/utils/quick_scan_work_store.py` 与 transport **零改动**（`git diff --stat` 为空）；untracked 杂物（`.codegraph/`、`.workbuddy-ai/`、`nul`、`pilot_runs/*`、`progress_update.txt`）为既有物，不在范围。
- **参照语义**：`src/utils/quick_scan_work_store.py`（create_or_attach L1419 / claim L1538 / prepare_attempt L1562 / mark_send_intent L1667 / record_attempt_outcome L1730 / recover_expired L1867）、IQS `scripts/work_contract.py`、W04 golden `docs/implementation/contracts/goldens/stockwiki-g2b-72531b5-provisional.json`。
- **约束遵守**：未读取 StockQA 真实配置/密钥（`llm_apis.json` 未打开）；未联网、未调用 LLM API；StockWiki/IQS 只读；全部探针在系统临时目录建 SQLite；本报告是本次审查唯一写入的文件。

## 2. 门复跑结果（命令 + 数字，全量独立执行）

工作目录均为 `C:\Users\郑曾波\Projects\StockQAbyLLM`。

| # | 命令 | 实测结果 |
|---|---|---|
| G1 | `python -X utf8 -m pytest tests/ -q -p no:cacheprovider -p no:base_url -o addopts=` | **872 passed, 4 skipped, 0 errors**（85.29s，exit 0）。4 skipped = `tests/live/test_live_quick_scan.py` 的 4 个 `skipif`（离线门，既有） |
| G2 | `python -X utf8 -m pytest tests/unit/test_q06_work_binding.py -q -p no:cacheprovider -p no:base_url -o addopts=` | **6 passed**（1.81s，exit 0） |
| G3 | `black --check --line-length 100 src/core/qa_engine.py src/runners/llm_runner.py main_with_llm.py tests/unit/test_q06_work_binding.py` | exit 0，`4 files would be left unchanged` |
| G4 | `ruff check <同 4 文件>` | exit 0，`All checks passed!` |
| G5 | `python -X utf8 -m mypy src/core/qa_engine.py src/runners/llm_runner.py main_with_llm.py` | exit 0，`Success: no issues found in 3 source files` |
| G6 | 回归子集：`pytest tests/unit/test_qa_engine.py tests/unit/test_llm_runner.py tests/integration/test_quick_scan_cli.py tests/unit/test_q05_content_boundary.py`（分 4 次实跑） | **12 + 23 + 48 + 14 = 97 passed**，0 failed/0 skipped——与任务书"回归 97 项"口径吻合 |
| G7 | 反证旗标：`pytest tests/ -q -p no:cacheprovider -o addopts=`（**不带** `-p no:base_url`） | **854 passed, 4 skipped, 18 errors**（87.36s，exit 1），18 个 error 全部落在 `tests/unit/test_llm_client.py` / `test_llm_provider.py` 的参数化用例（第三方插件 ScopeMismatch），**不涉及本次 4 文件**——证实任务书"缺旗标 18 错非代码回归"的说法 |

**门结论：四重门全绿，数字与施工卡声称一致（872/4/0、6/6、black 0、ruff 0、mypy 0）。门通过 ≠ 语义通过，见 §4—§6。**

## 3. R1 等价性 diff 结论（零注入逐分支审读）

`src/core/qa_engine.py` 的全部改动：

1. `__init__` 新增形参 `work_item_lifecycle: Optional[Any] = None`（L38）+ 单赋值 `self.work_item_lifecycle = work_item_lifecycle`（L54）+ docstring（L46-49）。无副作用。
2. `process_questions` 循环内新增块（L145-190）整体被 `if self.work_item_lifecycle is not None:` 包裹：
   - 钩子为 None 时：不构造 `hook_question`、不调用 `before_question`、不构造 `Answer/QAResult`、不 `add_result`、不走 `[SKIP]` 分支，直接落入原 `try:`。
   - 成功分支（L194-195）与失败分支（L205-206）的两处调用均为 `if self.work_item_lifecycle is not None and lifecycle_handle is not None:` 双守卫，None 时短路为无操作。
3. 唯一在 None 路径也会执行的新增语句是 `lifecycle_handle: Optional[dict] = None` 的局部变量赋值——无副作用、不改变控制流。

**结论：`work_item_lifecycle is None` 时执行路径与钩子引入前逐分支等价（除新增属性/docstring 文案外零行为差异）**；R1 的"现有测试必须原样通过"由 G1（872 passed）+ G6（97 passed）佐证；`git status` 显示**没有任何既有测试文件被修改**，期望未被放宽。

## 4. 逐 case 语义证据（含独立探针）

以下探针均为本人现场编写的 stdin 脚本（不落盘），全部离线。

### 4.1 Q06 steps 1-3（原子创建/领取、代次、状态转换）— **部分达成，第 3 步未达成**

- **原子创建/领取（steps 1）**：`create_or_attach` 在单事务内 SELECT→INSERT + `work_run_ref` INSERT OR IGNORE（store L1473-1536），九元 UNIQUE 键 `(entity_id, question_id, generation, scope, scope_id, identity_revision, source_binding_version, identity_state, source_binding_refs_json)`；`claim` 用 `WHERE status='pending' AND lease_epoch=?` 的 CAS，`rowcount!=1` 抛 `LeaseFencedError`（L1549-1556）。生命周期按 create_or_attach→claim→prepare_attempt 真实调用，探针 **C4 happy path：claimed=True，产出 WORK_/ATTEMPT_ id**。
- **多 run 同代次一个待办（JOB-01）**：store 层由九元键 + `run_id/scan_id` 多对一 attach 保证；`test_r5` 用 run_id=RUN_1/RUN_2 两次 create_or_attach 得到同一 `work_item_id` ✓（我复跑通过）。
- **状态转换记录（steps 3）— 未达成**：**`after_question` 与 `after_question_failed` 每次都抛错并被吞掉**，账目永远停在中间态。实测：

  ```
  STATUS after successful dispatch: ('leased',)
  ATTEMPT phase: ('prepared', None, None)
  EVENTS: ['created', 'attached_run', 'claimed', 'attempt_prepared']
  ERROR - record_attempt_outcome 失败（response requires successful HTTP status and receipt hash）
  ERROR - record_attempt_outcome(failed) 失败（confirmed refusal requires a recognized provider rejection）
  ```

  根因（store 源码 + 直调复算）：
  - `outcome="response_available"` 要求 2xx **且 `receipt_sha256` 非空**（L1806-1809），而 `after_question` 只传 `http_status_code=200`、无 receipt → `ValueError`；
  - 补上 receipt 再直调 → `WorkConflictError("attempt is not in send_intent")`（L1818/L1834），因为 attempt 停在 `prepare_attempt` 写入的 `'prepared'`（L1638），而 `phase='send_intent'` 只有 `mark_send_intent`（L1667/L1713）会写——**该生命周期从不调用 `mark_send_intent`**（`bind_quick_scan_work` 只在测试中被使用，全仓 grep 证实生产路径不设 work 上下文）；
  - `outcome="confirmed_failure"` 要求"可识别的 provider 拒绝"（401/403/404/429 + receipt + 错误码，L1804-1805），`failure_category="dispatch_error"` 不在其中 → `ValueError`。

### 4.2 JOB-10 / I12 — **被违反（实测重复派发 + 虚假 unsent）**

同一题成功拿到答案后，人为让租约过期并调用 `recover_expired`（对账兜底路径）：

```
recover_expired -> pending
work status: pending | attempt phase: abandoned_unsent
re-run dispatched again: scored ans
attempts now: (2, 'abandoned_unsent,prepared')
```

即：**一次实际已发送、已成功应答的 LLM 请求，被账目记为 `abandoned_unsent`（"可证明未发送"）**，work item 回到 pending，下一次 run **重新派发同一题（重复调用/重复费用）**。这直接违反 JOB-10 then"不能仅凭 lease 过期认定外部请求未发送"与 I12"重导入重问、重复领取……均需修正；外部结果不明不得承诺零重复费用"，也否定施工卡 R2"响应后到达终态"。失败模式的根因是漏接 `mark_send_intent`，不是文案问题。

### 4.3 JOB-02 / PAR-12（并发一领一拒、晚到写拒绝）

- 晚到旧 token 写被拒：`test_r4` + 我的直调探针（stale lease → `prepare_attempt` 抛异常）✓；store 层既有 `test_two_processes_race_on_one_lease_and_stale_epoch_is_fenced`（真子进程竞争）覆盖 CAS 原子性。
- **但本批新增 `test_r3` 是顺序两次 `before_question`，没有施工卡 R3 要求的"子进程/线程级并发"**；PAR-12 then 要求的"同步屏障并发 claim"在本批新测试中没有绑定（依赖既有 store 测试）。

### 4.4 steps 5 / JOB-11（issuer 级去重 vs listing 分立）

- `test_r5` 我复跑通过：entity scope 同题两次 → 同一 work item；security scope `SEC_aaa`/`SEC_bbb` → 两条互异、且与 entity 行互异。**去重逻辑真实绑定在 store 的九元 UNIQUE 上，不是自证**（故意改 store 键会红——键查询在 L1475-1477）。
- **限制**：绑定路径（`QuickScanWorkLifecycle.before_question`，llm_runner L140-141）**硬编码 `scope="entity"`、`scope_id=entity_id`**，生产路径永远不产生 listing 级 work item；JOB-11 的"valuation work distinct per listing"只在 store 直调层被证明，未走本批新增的绑定路径。

### 4.5 `--identity-snapshot` 映射（`load_identity_snapshot` vs golden）

字段逐项核对（对真实 golden 实跑）：

| 检查项 | 结果 |
|---|---|
| `object_type == "entity"`、`schema_version == "2.2.0"` | 读取并校验 ✓（golden 顶层两字段齐备） |
| `payload.listings[].source_binding_ref` → `source_binding_ref(s)`，去重取首 | ✓ 得 `BND_fixture_acme_1` |
| `payload.identity_revision`（int ≥1）、`payload.identity_state` ∈ {provisional, verified} | ✓ 得 1 / provisional |
| `identity_snapshot_sha256` = **文件原始字节**的 sha256 | ✓ 独立复算 `0efc2c04…e5d2f` 与 loader 返回值一致 |
| 映射错误 fail-fast（raise 而非静默） | ✓ 6 例畸形（object_type/schema_version/payload 缺失/listings 空/identity_state 非法/identity_revision=0）全部 `ValueError`，无一静默 |
| **`payload.entity_id`** | ✗ **被完全忽略**，也不与 `--entity-id` 交叉校验（见 P1-2） |
| **`source_binding_version`** | ✗ golden 中**不存在**该字段，loader **硬编码 1**（见 P1-3） |

### 4.6 生产激活路径端到端 — **三处断裂（P0，见 §6）**

施工卡的核心承诺是"`--identity-snapshot` 作为生产激活路径"。我按代码原样复算该构造路径：

- **C1**：`json.dumps(questions, …)`（llm_runner L683-687）在 `questions` 为 `List[Question]`（require_search 路径强制，L549-553 要求每题是 `Question` 且带 question_id）时 → **`TypeError: Object of type Question is not JSON serializable`** → `_run_single_company` 中止，**一个题都跑不到**。
- **C2**：即使绕过 C1，`routing_fingerprint = "rf-" + sha256hex` 违反 store `_sha256` 的 64-hex 校验（L686-689，`_HEX_SHA256`）→ 探针实跑 `before_question` 返回 `{'claimed': False, 'reason': 'store_error:ValueError'}`，日志 `invalid routing_fingerprint` → **每题拒绝、零派发**。
- **C3**：W04/IQS 的真实实体 id 形如 `ENT_1b2a4d3e-0000-4a1b-8c2d-000000000001`（golden `payload.entity_id`；IQS 侧 `ENT_97bf6a65-a9e6-43f0-8409-c5695e2f6e1e`、契约文档 `ENT_11111111-1111-…`）含连字符，被 store `_ENTITY_ID = ^ENT_[A-Za-z0-9_]+$`（L28）拒绝 → 探针 `{'claimed': False, 'reason': 'store_error:ValueError'}`，日志 `invalid entity_id` → **按 W04 格式传入的实体 id 100% 被拒**。
- **C4**：仅当 entity_id 用无连字符测试值、routing_fingerprint 用 64-hex 时才 claimed=True——即**只有测试里的注入载荷能跑通，生产接线跑不通**。
- **零覆盖**：全仓 grep 显示 `load_identity_snapshot` 与 `--identity-snapshot` **没有任何测试引用**（新测试 R6 只注入手写 dict payload，不经过 loader、不经过 CLI、不经过 runner 构造段）。

### 4.7 各 invariant

- **I02**（StockQA 唯一执行者）：本批无新增网络/LLM 客户端，测试全离线 fake ✓。
- **I12**（逐题持久化 + 幂等 + 旧租约不覆盖新结果）：**不达标**——成功结果不落终态、租约过期后同题重复派发（§4.2 实测）。
- **I54**（issuer id 不由名称/ticker 派生）：`--entity-id` 显式传入、不从公司名推断（既有校验 L480-481）✓；但 entity id 与身份快照不互校（P1-2）。

## 5. 失败面与诚实性审读

**拒绝面（符合要求）**：探针 C7（注入非法 routing_fingerprint 使 store 必拒）实测：

```
dispatched_calls = 0 | status = error | metadata = {'work_claim_refused': True, 'work_claim_reason': 'store_error:ValueError'} | processed_count = 1
```

即 claim 拒绝 → **error 结果 + `work_claim_reason` 元数据 + 零派发** ✓；`work_item_not_pending` 拒绝时还会附 `work_item_id`（qa_engine L180-184）✓。`before_question` 的 catch-all 确实降级为拒绝不抛出（llm_runner L151-153/L180-186，探针 C2/C3 无异常外泄）✓。

**对账兜底说明**：类 docstring 写明"失败静默记日志（store 对账兜底）"——**说明存在** ✓。但兜底的**语义是错的**：兜底路径（`recover_expired`）把已发送请求记成 `abandoned_unsent` 并放行重派发（§4.2），所以"兜底"不但没救场，还产出虚假账目与重复费用。文档诚实性达标、工程后果不达标（并入 P0-3）。

**过度声称扫描**：

| 声称（施工卡"实施完成记录"/测试 docstring） | 实测 |
|---|---|
| "create_or_attach→claim→prepare_attempt→record_outcome **全生命周期**" | `record_attempt_outcome` **从未成功过一次**（P0-3） |
| R2"响应后到达终态"；`test_r2` docstring "terminal outcome" | 终态 = `leased`/`prepared`，永不 terminal；测试仍绿是因为断言恰好兼容"卡在 leased" |
| "生产激活路径（W04 导出消费）" | 构造即 TypeError；即便修复，参数格式仍 100% 被 store 拒绝（P0-1/P0-2） |
| "provisional/verified 单绑定均支持（多 listing refs 去重取首）" | 去重只对**相同** ref 有效；provisional 下多个**不同** ref 不在 loader 拒绝，而是推迟成逐题 `ValueError` 拒绝（P1-3） |
| "identity 快照文件 sha256 钉进 work_item" | ✓ 实测成立（A1/A2 + C4 落库） |
| "缺省 None 逐字节不变" | ✓（§3 diff 审读 + 97/872 回归） |
| "prompt_sha256 = 渲染前代理（docstring 明示）" | 已明示 ✓；但实际公式是 `sha(identity_snapshot_sha256 + "|" + text)`，docstring 只说"题面文本的 sha256"，与代码不完全一致（LOW-1） |
| run_id/scan_id/route 派生取舍 | **未在任何 docstring 明示**：`run_id="run-"+UTC墙钟`、`scan_id="scan-l02"` 硬编码、`route_id="cli"`、`provider="quick-scan-cli"`、`model_requested="quick-scan"` 均为占位常量（P2-1） |
| Q07 checkpoint | 未声称已做 ✓（`record_attempt_outcome` docstring 亦注明 checkpoint 属 Q07） |

**范围合规**：恰 4 文件 ✓；无网络/LLM 调用（测试用 FakeProvider/FakeGenerator + `tmp_path` SQLite）✓；未改 transport/Q09 预算/既有 CLI 参数语义（`--identity-snapshot` 为纯新增）✓。

## 6. Findings

### P0（阻断）

- **P0-1 `--identity-snapshot` 生产激活路径构造即崩溃，功能不可用。**
  `src/runners/llm_runner.py:683-687` 对 `List[Question]` 调 `json.dumps(...)` → `TypeError: Object of type Question is not JSON serializable`（C1 实测）。require_search 路径的 `questions` 必为 `Question`（L549-553 强制）。批次核心交付物（"生产激活"）在真实 CLI 下跑不出任何一题，且没有任何测试覆盖 loader/CLI/runner 构造段（§4.6）。

- **P0-2 即使修复 P0-1，接线参数格式与 store 校验不兼容 → 生产路径 100% 拒绝派发，且不 fail-fast。**
  (a) `routing_fingerprint="rf-"+sha256hex` 违反 64-hex 校验（C2）；(b) W04/golden/IQS 真实 `ENT_<uuid>`（含连字符）被 `_ENTITY_ID = ^ENT_[A-Za-z0-9_]+$` 拒绝（C3）。两者都只降级为逐题 `warning` + error 结果（进程可能仍退出 0），没有启动期校验。

- **P0-3 attempt 终态从不记录；恢复路径把"已发送且已成功"记为"未发送"并导致同题重复派发。**
  `after_question` 必然 `ValueError`（缺 receipt_sha256，store L1806-1809）；即便补 receipt 也必然 `WorkConflictError`（phase 停在 `prepared`，缺 `mark_send_intent`，L1818/L1834）；`after_question_failed` 必然 `ValueError`（`confirmed_failure` 需可识别 provider 拒绝，L1804-1805）。全部异常被 `except Exception` 吞成日志。后果（§4.2 实测）：work item 永停 `leased`、租约到期后 `recover_expired → pending` + attempt=`abandoned_unsent`、**下一 run 重新派发同一题**。违反 Q06 steps 1-3、JOB-10 then、I12；施工卡与测试 docstring 的"终态"表述属过度声称。

### P1（应修复后再判 verified）

- **P1-1 施工卡 TDD R3/R6 未按定义交付**：R3 卡面要求"子进程/线程级并发双 claim"，实为顺序调用（`test_r3` L140-152）；R6 卡面要求"公开 CLI 端到端 + 回执含 work item 关联"，实为"注入 payload 落库字段检查"（`test_r6` L242-263）。**这正是 P0 未被任何测试捕获的直接原因。**
- **P1-2 身份快照与 `--entity-id` 不互校**：loader 忽略 `payload.entity_id`，operator 可把 A 公司的身份包绑到 B 公司的 work item 上（`identity_snapshot_sha256` 照样"钉入"，账目看起来自洽）。至少应比较并 fail-fast。
- **P1-3 `source_binding_version` 硬编码 1 且未披露**：该字段按 `docs/implementation/contracts/freshness-and-jobs.md` 是 StockWiki 按 Entity 维护的**单调权威版本**，W03/Q06 首段审查明确"不能由调用方自报"；golden 无此字段时应显式记录取舍并在 docstring/卡中披露，而不是静默写 1（错版本会导致 v2 逻辑键错配、身份/绑定变更时命中旧待办）。同批：provisional 下多个**不同** binding refs 未在 loader fail-fast，推迟为逐题拒绝。
- **P1-4 JOB-11 的 listing 分立未走绑定路径**：`before_question` 硬编码 `scope="entity"`（L140-141），绑定路径永不产生 security-scope work item；`test_r5` 只在 store 直调层证明分立，case 的 listing 半边缺少"经本批接线"的证据。

### P2

- **P2-1 attempt 审计字段失真/未披露取舍**：`provider="quick-scan-cli"`、`model_requested="quick-scan"`、`route_id="cli"`、`scan_id="scan-l02"`、`run_id` 墙钟派生——与真实调用的 provider/model 无关；`after_question` 还意图写入未经观测的 `http_status_code=200`（当前因缺 receipt 必然失败，但代码意图在案）。run_id/scan_id 派生取舍未在 docstring 明示（任务书"诚实性"项不达标）。
- **P2-2 拒绝结果不可与成功区分于批次摘要**：拒绝结果计入 `processed_count`，`finish_batch` 文案 `成功: 1/1`；只在单题 metadata 里可见。建议拒绝单独计数或在摘要暴露。

### LOW / INFO

- **LOW-1** `prompt_sha256` docstring 描述（"题面文本的 sha256"）与实际公式（含 identity sha 前缀）不一致。
- **LOW-2** QAEngine 在 `try` 之外调用 `before_question`；钩子若抛异常会中断整批（当前实现 catch-all 兜住，但契约 docstring 未声明"钩子不得抛出"）。
- **LOW-3** 拒绝归因粗糙：`Question(text=…)` 构造失败时 reason 为 `lifecycle_refused`，与 store 拒绝同形（该题本也会 ValidationError，影响有限）。
- **INFO-1** 四重门独立复跑全绿（872/4/0、6/6、black 0、ruff 0、mypy 0），回归 97 项原样通过，既有测试零改动。
- **INFO-2** golden 映射字段核对与 sha256 复算通过、6 例畸形 fail-fast 通过、拒绝不派发（error+metadata+零搜索调用）通过、文件范围恰 4 个、无网络/LLM/密钥触碰。

## 7. 裁决

**needs_revision**

门（G1-G7）全部通过、R1 零注入等价成立、issuer 去重在 store 层真实绑定、身份映射与 fail-fast 合格、拒绝面行为符合要求——但本批次的核心承诺"公共题路径绑定真实 work item + `--identity-snapshot` 生产激活"存在三个 P0：生产接线跑不起来（P0-1）、跑起来也会 100% 拒绝（P0-2）、即便全部修好，attempt 终态永远不落账并在租约到期后把已成功的请求记成未发送、诱发同题重复派发与重复费用（P0-3，直接违反 JOB-10/I12）。在 P0-1—P0-3 修复并补充 loader/CLI/runner 构造段与终态断言测试（P1-1）之前，Q06 不得由 partial 转 verified，W11 不解锁。

修复建议要点（供实现者参考，非本审查范围）：
1. `routing_fingerprint` 改用 64-hex（如对题目集合求 sha256），`json.dumps` 改为序列化题面/题 id 列表而非 Question 对象；
2. 明确 entity id 来源与格式：放宽 store `_ENTITY_ID` 需 owner 签认（属改 store 最小缺口），或在 loader 交叉校验 `payload.entity_id` 与 `--entity-id` 并 fail-fast；
3. 生命周期补 `mark_send_intent` 后再 `record_attempt_outcome`，或改用与阶段机一致的收口 API，并为 `response_available` 提供真实 receipt_sha256（否则如实记 `unknown`，绝不写臆造 200）；
4. 补三条红测：CLI/runner 构造段端到端（发现 P0-1/P0-2）、成功后 work item 达到终态且 `recover_expired` 不重派发（发现 P0-3）、loader 对真实 golden 的字段级断言。
