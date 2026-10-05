# W06 审查跟进批次 F1/F2/F3 独立审查报告（2026-10-05）

审查者：独立审查（与实现者无关，全部结论基于本人复算/复跑，不采信施工卡与进度台账的描述）。

## 1. 范围

| 项 | 内容 |
|---|---|
| 施工卡（范围与门的权威） | `docs/implementation/reviews/IQS-lane/W06-followup-F1F2F3-card-2026-10-05.md` |
| 被审变更（StockWiki） | `stockwiki/quick_scan_freshness.py`（59 增/2 删）、`tests/test_quick_scan_freshness.py`（114 增/0 删），均为未提交工作树变更 |
| 被审变更（IQS） | `tests/test_freshness_and_jobs_contract.py`（+15/0，已随 commit `2feaf99` 入库） |
| 参考语义（只读） | IQS `scripts/work_contract.py` `reuse_decision` L148-175（C04 对照实现）；`Q06-closeout-card-draft-2026-10-05.md`（Q06 终局方案佐证） |
| 明确排除、未予评价 | StockWiki 同仓 A/H bridge 批次：`stockwiki/cli_parsers/quick_scan.py`、`stockwiki/quick_scan_schema.py`、`stockwiki/quick_scan_store.py`、`stockwiki/quick_scan_issuer_bridge.py`（新）、`tests/test_quick_scan_issuer_bridge.py`（新） |
| 纪律 | 两仓均未提交、未改任何产品文件；本报告为唯一写入产物（UTF-8 无 BOM）；全部测试离线（pytest 临时目录 + socket bomb），零网络、零 LLM API |

## 2. F1（代次对齐门）证据

**对照实现（C04 `work_contract.py:160-162`，本人读取原文）**

```python
requested_generation = expected.get("generation")
if requested_generation is not None and work_item.get("generation") != requested_generation:
    return "dispatch"
```

**StockWiki 实现**（`quick_scan_freshness.py:242-267`，diff 新增）：门位于 `_field_decision` 的 in-flight 分支内、`resume_existing_work` 赋值**之前**；条件与 C04 逐字同构（`requested_generation is not None and work_item.get("generation") != requested_generation`），命中则 `decision=dispatch_new_work`、`generation=expected.generation`、`reasons=["generation_mismatch"]`、带 `logical_todo_key`；`expected.generation` 为 None 时条件短路 → 保持 `resume_existing_work`。**三项行为全部满足施工卡与任务书的 F1 定义。**

**三个测试真绑定**（`tests/test_quick_scan_freshness.py:474-520`）：
- `test_f1_generation_mismatch_in_flight_dispatches_instead_of_resume`：pending/gen2 + expected gen1 → 断言 dispatch + generation==1 + `generation_mismatch` + todo key；
- `test_f1_matching_generation_still_resumes`：leased/gen2 + expected gen2 → resume；
- `test_f1_absent_expected_generation_keeps_resume`：expected generation=None + uncertain/gen3 → resume。

**复跑命令与结果（本人执行）**

```
cd C:\Users\郑曾波\Projects\StockWiki
python -X utf8 -m pytest tests/test_quick_scan_freshness.py -q -p no:cacheprovider
→ 16 passed in 4.46s          （预期 16 passed ✓）
```

**RED 声明独立复现**：以 `git show HEAD:stockwiki/quick_scan_freshness.py` 在内存中 exec 旧实现并对比新实现（无文件写入）：
- 旧实现：pending/gen2 + expected gen1 → `resume_existing_work`（F1 首测 RED ✓）；
- 旧实现：incompatible + 未来冷却 → `deferred_unknown`（F2 首测 RED ✓）；
- 恰好 2 处行为在实现前缺失，与 task_plan Phase 76 "RED 2 失败" 声明一致；F3 为"行为本正确、纯补测"亦一致。

## 3. F2（兼容门重排）证据

实现顺序（`quick_scan_freshness.py:242-301`）：**F1 代次门 → in-flight resume → observation is None → F2 `observation_compatible` 前置门 → unknown/冷却 → unusable status → freshness/reuse**。

本人以 OLD/NEW 双实现对照探针（exec HEAD 版 vs 工作树版，同输入）实测：

| 用例 | 旧实现 | 新实现 | 卡片要求 |
|---|---|---|---|
| incompatible + 未来冷却（next_retry_at 未来） | `deferred_unknown` | `dispatch_new_work`（reasons=`semantic_change`） | 必须 dispatch ✓（新 F2 测试钉住） |
| incompatible + 无 retry_at | `manual_refresh_required` | `dispatch_new_work` | C04 L150-151 语义 ✓ |
| compatible + 未来冷却 | `deferred_unknown` | `deferred_unknown` | 保留 ✓（新 F2 测试钉住） |
| in-flight（gen 匹配）+ incompatible observation | `resume_existing_work` | `resume_existing_work`（reasons=`existing_work_in_flight`） | resume 保持在兼容门之前 ✓（新 F2 测试钉住） |

**docstring 取舍记录真实存在**（`quick_scan_freshness.py:209-225`，本人逐行读取）：`_field_decision` 新增 docstring，明确三条排序契约——(1) in-flight resume 只在 F1 代次门之后；(2) "Resume deliberately precedes the F2 compatibility gate … would double-send once work-item storage lands … **executor-side logical-key dedup from the Q06 chain is the eventual fix**, which lets the gate move ahead of resume exactly like C04 … reviewer-accepted anti-duplicate-dispatch tradeoff; lease expiry bounds how long a resume can starve a changed request"；(3) 所有 observation 派生决策（冷却/unusable/reuse/stale）都在 `observation_compatible` 之后。

**Q06 链终局方案**（与 `Q06-closeout-card-draft-2026-10-05.md` §只读勘察/设计取向互证，属实）：Q06 收尾卡要在题循环注入逐题 `claim/lease` 生命周期钩子，靠 `logical_work_key(...)` 存储唯一约束 + claim 原子实现 **executor（执行器）侧 logical-key 去重**。终局含义：等该去重落地后，即使兼容门提到 resume 之前，在途工作之上重复 dispatch 也会被存储层按 logical key 去重吸收，届时可像 C04 一样把兼容门放到 resume 之前；在此之前保留 resume-first，由租约过期（lease expiry）限制 resume 对已变更请求的饿死时长。docstring 对该取舍的记录与 Q06 卡实际设计一致。

## 4. F3（IQS test_time_03）证据

`tests/test_freshness_and_jobs_contract.py:89-103`（commit `2feaf99` 内 +15/0，本人 `git diff eb462d4..2feaf99` 读取）：
- 真实变更输入：`renewed = observation(valid_until=..., information_as_of=..., imported_at="2026-09-22T21:59:00Z", checked_at="2026-09-22T21:59:30Z")`——相对基座（`imported_at="2026-09-22T10:02:00Z"`、`checked_at=None`）两字段均实际改变，且 `assertNotEqual(renewed["imported_at"], value["imported_at"])` 钉住"输入确实变了"；
- 断言不失效续期：`freshness_status(renewed, "2026-09-22T22:00:00Z") == "stale"`（晚 30 秒的 checked_at、晚 12 小时的 imported_at 均未续期）；`reuse_decision(renewed, expected(), ..., {"status":"delivered","generation":1}) == "dispatch"`。若任一字段能续期，两断言均会红——绑定有效；
- `scripts/work_contract.py:52-70` `freshness_status` 确认只看 `information_as_of/event_invalidated_at/valid_until`，不看 checked_at/imported_at → 该测试正是"输入变化但结论不变"的真验证。

**复跑命令与结果（本人执行）**

```
cd C:\Users\郑曾波\Projects\invest-quick-scan
python -X utf8 -m pytest tests/test_freshness_and_jobs_contract.py -q -p no:cacheprovider -o addopts=
→ 17 passed, 9 subtests passed in 0.20s   （预期 17 passed / 9 subtests ✓）
```

## 5. 范围合规 diff 清单

**StockWiki**（`git status --porcelain` + `git diff --numstat`）：

| 文件 | 变更 | 与施工卡比对 |
|---|---|---|
| `stockwiki/quick_scan_freshness.py` | 59+/2- | ✅ 卡内（F1 门 + F2 门 + docstring + reuse 分支去冗余 compat 判断） |
| `tests/test_quick_scan_freshness.py` | 114+/0 | ✅ 卡内（+6 个 F1/F2 测试，纯追加） |
| `cli_parsers/quick_scan.py`、`quick_scan_schema.py`、`quick_scan_store.py`、`quick_scan_issuer_bridge.py`*、`tests/test_quick_scan_issuer_bridge.py`* | 改 4 / 新 2 | ⚪ 范围外（A/H bridge 批次，任务书明示不评；与任务书列举完全一致，除此之外 StockWiki 无其他改动） |

**IQS**：F3 唯一代码变更 = `tests/test_freshness_and_jobs_contract.py` +15/0；commit `2feaf99` 其余为 docs/progress/findings/task_plan（施工卡 §门 授权"测试结果记入 progress.md"）。工作树无未提交修改，`git diff --check` 与 `git diff --cached` 均干净。

**不变量逐项核对**：
- 决策词汇表：新增分支只产出既有 decision 名（`dispatch_new_work`/`resume_existing_work`），与旧实现全集比对无新增名；新词仅出现在 **reason**（`generation_mismatch`），卡约束的是 decision 名 ✅
- `plan_sha256` 口径：`build_gap_plan` L425-449（含 plan_sha256 计算）在 diff 中零改动 ✅
- `freshness_status`/`observation_compatible`/`request_identity_key` 函数本体零改动 ✅（diff 首个 hunk 从 L206 起，全部落在 `_field_decision` 内）
- 零网络：模块仅 import hashlib/json/re/datetime（本人列目录核验 `['socket','urllib','http','requests','aiohttp'] ∩ dir(module) = []`）；16 个测试全部调用 `_no_network` socket bomb；本人单独验证 bomb 有效性（monkeypatch 后 `socket.socket()` 抛 AssertionError）✅
- 旧测试断言未放宽：两仓均为**纯追加**（114+/0、15+/0，numstat 零删除行）✅

## 6. 门证据（全部本人复跑，不采信描述）

```
1) cd StockWiki; ruff check stockwiki/quick_scan_freshness.py tests/test_quick_scan_freshness.py
   → All checks passed!（exit 0）
2) cd StockWiki; black --check --line-length 100 两文件
   → "2 files would be left unchanged"（exit 0；附带 py3.13 vs py3.15 target 解析警告，见 INFO-5）
3) cd StockWiki; bash scripts/check_all.sh（后台全量复跑）
   → ruff clean PASS
   → 913 passed, 15 skipped in 209.14s；coverage TOTAL ≥73% PASS；ui.py coverage 75% PASS
   → validate-framework 0 errors（12 warnings 全为既存基线：news_by_topic OKF ×11、quick_scan_store 969 行基线）
   → === ALL CHECKS PASSED ===（exit 0）
   注：913 = 卡片基线 907 + 本批新增 6，数字自洽。
4) cd IQS; git diff --check → exit 0 无输出；git diff --cached --stat → 空
5) 定向测试：StockWiki 16 passed；IQS 17 passed + 9 subtests（见 §2/§4）
```

施工卡声称的 ruff/black 净、check_all ALL CHECKS PASSED **复跑全部属实**。

## 7. 反向检查（F2 重排的新缺口，任务必查 #6）

用例 C（**incompatible + unusable status**，本人 OLD/NEW 对照探针）：

```
OLD: decision=dispatch_new_work reasons=['status_error']      freshness=unusable_status
NEW: decision=dispatch_new_work reasons=['semantic_change']   freshness=fresh
```

- **是否被既有测试钉住**：否。全仓 grep `status_` / `unusable_status` 在 `tests/` 下零断言（仅 `quick_scan_rules.py` 另有同名 reason，属别的模块、未改）；`test_time_06` 等只断言 compat 系 reason `in` 列表。→ 该漂移不破坏任何既有测试，且本批 16 测试全绿佐证。
- **语义是否可接受**：可接受（附建议）。decision 不变、dispatch 不变；对不兼容观察，compat 系原因是更根本的归因（C04 对 incompatible 干脆只回 `dispatch` 连 reason 都不给，本实现更丰富）。代价是该组合下 `status_x` 归因与 `freshness_status="unusable_status"` 字段值丢失，`reason_counts` 连续性受影响（见 LOW-1）。
- 其余组合逐一对照：incompatible+unknown（E/F 用例）由 defer/manual_refresh 改为 dispatch = F2 的既定修复目标本身；incompatible+usable 路径新旧完全一致；compatible 路径行为零变化（C2 用例新旧逐字段一致）。
- 另发现一处重排副作用（NEW 相对 OLD 的新增异常面）：incompatible + (unknown|unusable) + `information_as_of` 为未来时间 → 新实现在 F2 门内调用 `freshness_status` 抛 `information_date_in_future` 中止整个计划，旧实现是 defer/dispatch（见 LOW-2）。

## 8. Findings

**P0：无。P1：无。**

### P2（阻断级）

- **P2-1｜F1 只关闭了"恢复"，未关闭"复用"——原 finding 字面范围半开，且取舍未记录。**
  - 证据：C04 L160-162 的门位于 status/resume 判断（L163）**和 reuse（L174）之前**，对任何 work_item（含非在途状态、乃至空字典）生效；task_plan Phase 61 原 finding 措辞为"**复用/恢复前**缺 generation 对齐门"。StockWiki 的门只放在 in-flight 分支内。
  - 本人对照探针实测残余缺口：① work_item=`{"status":"delivered","generation":2}` + expected generation=1 + fresh compatible observation → 新旧均 `reuse`（C04 会 dispatch）；② 无 work_item + expected generation=2 + fresh observation → 新旧均 `reuse`（C04 会 dispatch）。
  - 缓解事实（如实记录）：施工卡与本任务书都把 F1 定义为"resume 前"，实现对卡完全合规；用例 ② 若按 C04 字面修会打破冻结的 W06 TIME-01（fresh+兼容+无 work_item → reuse、0 API），故属 W06 观察缓存模型与 C04 work 身份模型的结构性分歧；当前 `build_gap_plan` 无生产调用方，尚无实害。
  - 但用例 ①（work_item 存在且非在途、代次不一致）存在**不破坏任何既有断言的中间修法**（本人核验：TIME-01/LLM-09/TIME-10/F2 诸测试的 work_item 要么缺席、要么代次匹配，加门后仍全绿），且该分歧未像 F2 那样在 docstring/台账留下任何记录。
  - 要求：二选一——(a) 把门扩到"work_item 存在且 generation≠expected"的 reuse 路径（含固定反例测试）；或 (b) 与 F2 同模式，在 `_field_decision` docstring 记录"reuse 豁免代次门"的取舍与理由（TIME-01 冻结冲突 + 观察缓存不随代次失效），使 finding 不带未记录缺口关闭。**在 work-item 存储批次动工前必须落定**（finding 原始 deadline 即该时点）。

### LOW

- **LOW-1**：incompatible+unusable-status 的 reasons 由 `status_x` 变为 compat 系、`freshness_status` 由 `unusable_status` 变为实算值（探针 C）。无测试钉住、decision 不变、语义可接受；建议在 compat 系 reasons 后**追加**而非替换 `status_x`，保住 `reason_counts` 归因连续性。
- **LOW-2**：F2 门对 incompatible 观察提前实算 `freshness_status`，使 "incompatible + future `information_as_of`" 从旧的 defer/dispatch 变成抛 `FreshnessPlanError` 中止**整份**计划，且与 "compatible + unknown + future" 仍 defer 不一致（探针 D）。与模块既有 fail-closed 风格一致、方向不算错，但单字段坏日期放大为整计划中止；建议该分支内防御求值（或导入侧校验未来日期）。
- **LOW-3**：施工卡 §门 要求"本批测试结果与 **SHA** 记入 progress.md"——progress.md L1746 记了结果（RED 2→GREEN 16/16、17+9、check_all）但未见本批日志/产物 SHA-256。
- **LOW-4**：F2 门内 `freshness_status(observation, now)` 被计算两次（L287 与 L295）。纯函数幂等，仅风格/性能问题。

### INFO

- **INFO-1**：全量门 913 passed/15 skipped = 卡片基线 907 + 新增 6，自洽；validate-framework 12 warnings 均为既存基线（含 A/H 批次的 quick_scan_store 969 行）。
- **INFO-2**：范围外 A/H bridge 文件清单与任务书列举逐项一致；除本批 2 文件外 StockWiki 无其他改动；IQS 批次 commit 内除 F3 外全为文档/台账。
- **INFO-3**：IQS 工作树存在幽灵未跟踪条目 `nul`，导致在仓库根跑 rg 直接报 `os error 1`（本人实测）；与本批文件无关，建议顺手清理，否则会持续干扰全仓 grep 审查。
- **INFO-4**：在途 work_item **缺 generation 键**时新门判 mismatch → dispatch（与 C04 字面一致；`WorkItem` schema 要求该字段，风险低）。
- **INFO-5**：black 在 Python 3.13 下提示 py3.15 target 解析警告，但 `--check` 通过（exit 0、2 files unchanged），不影响门结论。
- **INFO-6**：RED 声明（恰好 2 处行为缺失）经旧/新实现内存对照独立复现属实；`progress.md`/`task_plan` 关于本批的全部事实性声称（16 passed、17+9、ruff/black 净、ALL CHECKS PASSED、docstring 取舍、Q06 终局）逐项复核属实。

## 9. 裁决（r1）

# needs_revision（r1，已被 §11 r2 最终裁决取代）

理由：批次对施工卡 100% 合规、三处门（ruff/black/check_all/定向测试/IQS `git diff --check`）全绿、所有事实性声称复核属实、范围零越界、旧断言零放宽——但 F1 作为"复用/恢复前代次对齐门"仅落地了"恢复"半边（P2-1），残余缺口既未修也未记录。整改面窄：**(a)** 补 work_item-存在且代次不一致时的 reuse 门 + 反例测试，或 **(b)** 按 F2 先例在 docstring 记录 reuse 豁免取舍并由审查者/owner 签认；二者择一即可复审收口。LOW-1/LOW-2/LOW-3 建议随整改顺手处理，不单独阻断。

---

## 10. r2 复核（2026-10-05，聚焦整改面；r1 复跑结果仍为基准）

**整改面读取**：`git diff` 重读 `quick_scan_freshness.py`（104+/2-）与 `tests/test_quick_scan_freshness.py`（202+/0，**纯追加**）；施工卡新增"审查轮修订"节（+5）；`progress.md` 新增 4 行（r1→整改记录 + 三文件 SHA-256 + nul 清理）。

### r2 核查点逐项

**(a) reuse 门与 r1 探针 ① 期望一致 —— PASS**
- 实现：fresh→reuse 分支前，`work_item 非空 且 expected.generation 非 None 且 work_item.generation ≠ expected.generation` → `dispatch_new_work` / `reasons=["generation_mismatch"]` / expected 代次 / todo key（与在途分支同条件）。
- 本人探针复跑（同 r1 用例）：`terminal work_item gen2 + expected gen1 + fresh 兼容观察` → **`dispatch_new_work` reasons=`['generation_mismatch']`**（r1 时为 `reuse`，已按期望翻转）✓；反向不误伤：`terminal gen2 + expected gen2 + fresh` → 仍 `reuse` ✓；在途 mismatch → 仍 `dispatch` ✓。
- 反例测试 `test_f1_terminal_work_item_generation_mismatch_blocks_reuse` 真绑定（decision+generation+reasons 三断言）；RED 声明与我 r1 探针基线（旧行为=reuse）一致，可复现 ✓。

**(b) case ② 豁免的 docstring 留档 —— PASS（满足 (b) 选项"取舍留档待签认"）**
- `_field_decision` docstring **第 4 点**真实存在（本人逐行读取）：明确"generation gate covers BOTH halves of the original finding（复用/恢复前）"、"ABSENT work item stays exempt: no work history is not a generation conflict"、"C04's literal gate would also dispatch … that divergence is deliberate（TIME-01-style reuse flows 依赖）"、"recorded here for owner sign-off alongside F2's resume-first tradeoff"——C04 字面分歧、有意为之、与 F2 并列留 owner 签认三要素齐全 ✓。
- pin 测试 `test_f1_absent_work_item_keeps_reuse` 钉住豁免行为（expected gen2 + 无 work_item → `reuse`）✓；探针复跑 `absent workitem gen2` → `reuse` ✓。
- 施工卡"审查轮修订"节如实声明 F1 从 resume-only 扩展到复用/恢复双半边 ✓。

**(c) LOW-1 追加语义不破坏 r1 反向检查结论 —— PASS**
- 探针：incompatible+unusable → reasons=`['semantic_change', 'status_error']`（**追加并存**，非替换；含去重 guard）；compatible+unusable 路径逐字段不变（`['status_error']`/`unusable_status`）✓；r1 反向检查结论（decision 不变、无测试钉住）依然成立且归因连续性缺口已按建议消除。
- 新测试 `test_f2_incompatible_unusable_status_keeps_status_attribution`（cancelled + 语义变更双断言）真绑定 ✓。

**(d) 门复跑（本人决定：全量 check_all 重跑，不采信描述）**
```
定向: pytest tests/test_quick_scan_freshness.py -q -p no:cacheprovider → 20 passed（16+4 ✓）
ruff 两文件 → All checks passed（exit 0）；black --check -l 100 两文件 → 2 files unchanged（exit 0）
check_all.sh 全量 → ruff PASS；917 passed, 15 skipped in 214.64s（= 913 + 新增 4，自洽）；
                     coverage ≥73 PASS；ui.py 75% PASS；framework 0 errors（12 warnings 仍为既存基线）
                     → === ALL CHECKS PASSED ===（exit 0）
IQS: pytest tests/test_freshness_and_jobs_contract.py → 17 passed, 9 subtests（F3 未动、hash 未变）
IQS: git diff --check → exit 0；rg 复常（r1 在仓根报 os error 1 的 grep 本次成功）
LOW-2 探针: incompatible + future information_as_of → dispatch（freshness=None，不再中止整计划）✓
LOW-4: 不兼容分支 freshness_status 单次求值（diff 读取确认）✓
LOW-3: progress.md 三 SHA-256 与本人 Get-FileHash 实测逐一完全一致
       （freshness 4CFF8633…、tests 6E13FB5B…、IQS test C51C69CB…）✓
INFO-3: 幽灵 `nul` 已删（git status `?? nul` 消失、仓根 rg 复常）✓
```

**(e) 范围合规 —— PASS**
- StockWiki：本批仍只触 `quick_scan_freshness.py` + `tests/test_quick_scan_freshness.py` 两文件；A/H bridge 4 文件 numstat 与 r1 完全一致（r2 未触碰）；测试文件纯追加零删除（202+/0），旧断言仍零放宽；decision 名零新增（新分支仅 `dispatch_new_work`）；`plan_sha256`/`freshness_status`/`observation_compatible`/`request_identity_key` 仍零改动（全部 hunk 落在 `_field_decision` 内）；socket bomb 16+4 全数在位、模块仍无网络 import。
- IQS：F3 测试文件未动（SHA 与记录一致）；本仓仅 card（审查轮修订节）+ progress.md（卡门授权的台账）两处文档变更，`git diff --check` 净。

### r2 新增观察（不阻断）
- INFO-7：reuse 门命中时行内 `freshness_status` 保留 `"fresh"` 而 decision 为 dispatch——如实反映"观察确实新鲜但代次冲突"，reasons 已解释，语义可接受。

## 11. 最终裁决（r2）

# approved

理由：r1 唯一阻断 P2-1 已按 (a) 路线闭环（reuse 门 + 反例测试，探针证实 case ① 由 reuse 翻转为 dispatch），case ② 按既定 (b) 先例入 docstring 第 4 点留 owner 签认并有 pin 测试钉住；LOW-1/2/4 同批修复、LOW-3 SHA 记录经我实测逐一相符、INFO-3 nul 清理复验；门全部独立复跑（20/20、ruff/black 净、check_all **917 passed ALL CHECKS PASSED**、IQS 17+9 与 `git diff --check` 净）；范围仍严格限于同 2 文件 + IQS 台账文档，旧断言零放宽、决策词汇表/plan_sha256/零网络不变。遗留待办仅一项非阻断：case ② 豁免与 F2 resume-first 取舍的 **owner 签认**（docstring/施工卡已留档，建议随 work-item 存储批次卡一并签认）。
