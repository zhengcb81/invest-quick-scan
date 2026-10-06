# B01-a 独立审查报告 — BENCH-02 入口预检 fail-closed 门

日期：2026-10-06。审查者：独立审查（与实现者无关，复跑/复算不采信描述）。两仓只读（本报告为唯一写入文件）；全程离线、无 LLM 调用、无网络、未读真实配置；探针置于 `%TEMP%\q09_review\`，不落被审仓。
被审基线：StockQA 工作区 = 2 源文件修改 + 1 新增测试 + 1 个已披露的 harness 测试文件修改（Q10 已提交为 HEAD 03b34f4，Q09 为 05ff583）。

## 1. 范围

**StockQA（`C:\Users\郑曾波\Projects\StockQAbyLLM`）**
1. `main_with_llm.py`（+7）：argparse `--spend-authorization`（L275-280）+ 透传 `run(spend_authorization=...)`（L309）
2. `src/runners/llm_runner.py`（+53）：import re/uuid；`_spend_authorization_preflight`（L593-623）；`run()` 增参（L857）+ 入口预检块（L889-907）——**在 identity 加载（L908）、`_run_single_company`（L918）之前**，而 budget_store（L1014）/work_store（L1100）均在 `_run_single_company` 内 → 预检 return 2 位于一切 store/attempt/budget 创建之前（代码顺序核对）
3. `tests/unit/test_b01_preflight.py`（新增 92 行，3 测试）
4. **卡允许面外但已披露**：`tests/integration/test_quick_scan_cli.py`（+19）——仅 `_invoke` 增 `spend_authorization="default"` 参数（默认自动写有效快照并附 `--spend-authorization`；None/Path 供反例），无任何既有断言改动（diff 逐行核对 ✓）

`git status -- src/ main_with_llm.py tests/` = 上述 4 项；StockWiki 零改动 ✓；untracked 杂物（`.codegraph/`、`nul` 等）不在范围。卡「允许改动」节列 llm_runner/test_b01/IQS 文档（**未列 main_with_llm.py**——v2 的 `--spend-authorization` 隐含、Phase 83 提交清单已列，见 INFO-1）。

## 2. 门复跑（命令 + 实测数字）

| # | 命令 | 结果 |
|---|---|---|
| G1 | `python -X utf8 -m pytest tests/unit/test_b01_preflight.py -q -p no:cacheprovider -o addopts=` | **3 passed** in 1.80s |
| G2 | `python -X utf8 -m pytest tests/integration/test_quick_scan_cli.py -q -p no:cacheprovider -p no:base_url -o addopts=` | **48 passed** in 6.25s |
| G3 | `python -X utf8 -m pytest tests/ -q -p no:cacheprovider -p no:base_url -o addopts=` | **906 passed, 4 skipped** in 75.62s，**0 errors**（分解核对：Q09 审基线 897 + Q10 已提交 6 + 本批 3 = 906 ✓，与预期一致） |
| G4 | `mypy main_with_llm.py src/runners/llm_runner.py` | **Success: no issues found in 2 source files** |
| G5 | `black --check -l100`（main_with_llm/llm_runner/test_b01/test_quick_scan_cli） | **4 files would be left unchanged** |
| G6 | `ruff check`（同 4 文件） | **All checks passed!** |
| G7 | `git diff --check` | 干净；探针运行后 `git status` 复核 = 运行前（本审对被审仓零写入） |

独立探针（离线、真实公共入口、临时目录）：
```
A1 无 --spend-authorization：
{"blocked": true, "reason": "spend_authorization_missing", "run_id": "run-20261006T190331Z-13d72f",
 "schema": "stockqa.spend_preflight/1.0.0", "status": "needs_configuration"}   exit=2
A2 cwd 存在有效默认 spend_authorization.json、无 flag → 仍 blocked exit=2（卡 v2「或默认路径」未实现）
A3 hard_cap=0（PowerShell BOM 文件）→ reason=spend_authorization_invalid  exit=2
A4 重复 A1 → run_id=run-20261006T190335Z-cd9eab（与 A1 不同 ✓ 每次新）
c5 hard_cap=0（Python 无 BOM）→ spend_authorization_invalid_hard_cap（精确码 ✓）
c6 path=None → spend_authorization_missing；c7 文件不存在 → spend_authorization_missing
探针全程配置文件（不存在的 config）从未被读、quick_scan_work.sqlite 从未创建（then-1 时点的直接证据）
C1 有效快照 + 无模型策略（quota 不可建立形态）→ exit=0, posts=1, store=false   ← 见边界评估
```

## 3. BENCH-02 四条 then 逐条证据

**then-1「explicit blocked/needs_configuration result before creating a dispatchable attempt」**
- 载荷（探针 A1/A4 逐字）：canonical JSON（`sort_keys=True`）、`status=needs_configuration`、`blocked=true`、`reason` 为 6 元闭集码（missing/invalid/invalid_currency/invalid_hard_cap/missing_pricing_snapshot/invalid_authorized_at——探针与代码双重核实，有界 ✓）、`run_id="run-"+UTC时间戳+"-"+uuid4[:6]`。
- 时点：预检块位于 run() L889-907，先于 identity 加载（L908）、单公司流程（L918）与其中一切 store 构造（budget L1014 / work L1100）——**任何 dispatchable attempt 之前**（代码序 + 探针：不存在的 config 不报错 = 配置 IO 未发生）✓。
- 测试钉法：`exit_code != 0` + `session.post.call_count == 0` + 无 store 文件（3 测试）。**载荷/status/exit==2/run_id 无自动化断言**（注释称 "verified via -s"）→ LOW-1。

**then-2「outbound exactly zero; no reservation or chargeable work」（授权触发）**
- 测试：三处 `session.post.call_count == 0`（L59/L73/L90）+ `not store_path.exists()`（L60/L92）✓。
- 实现面：return 2 在网络栈、cost_resolver、policy 加载之前——探针 A1 用不存在的 config 仍干净退出=零 IO；探针后 `git status` 零漂移 ✓。
- **quota 触发不成立**：C1（有效快照+无模型策略）→ **posts=1、exit 0、无预算跟踪** → 见 §4 → P2-1。

**then-3「prior completed work, production profile, pool, databases unchanged」**
- 预检 return 2 前无任何文件/DB 写入（探针实证：A1-A4 后仓库与临时目录零新增、`quick_scan_work.sqlite` 不存在）✓；测试3（`production_state_untouched`）断 tmp store 缺失 + 零 POST。
- 卡设计3 承诺的「运行前后 workspace 快照比对」**未实现为测试**（测试仅断 tmp 路径）——代码时点保证下风险低 → LOW-4。

**then-4「bounded reason; retry only after valid snapshot; new run id」**
- 有界 reason ✓（闭集码，无 str(exc) 注入）；重试：测试2 bad(hard_cap=0)→`!=0` 零 POST，good.json→**exit==0、posts==1** ✓；
- 新 run_id：代码每次新生成（timestamp+uuid），探针 A1/A4 两次 blocked run_id 不同 ✓——**但测试未断言 run_id**（`_invoke` 只回传 exit/output/session，stdout 未取）→ LOW-1；Phase 83 GREEN 记录把「新 run_id」列为第三测内容 → LOW-3。
- 「valid **price/quota** snapshot」：入口仅验 `pricing_snapshot_ref` 非空，**不解析/不交叉校验**该引用对应的真实计价来源（探针：任意非空串即过）→ LOW-5；quota 无字段、无校验 → P2-1。

## 4. 边界评估

### 4.1 probe 语义收紧与既有面零破坏
- 收紧点：所有 `--require-search` 运行现在必须携带有效花费授权快照，缺失/无效 → 入口 blocked（探针 C3/A1 exit=2）。**无 policy 但有有效快照的运行仍可派发**（C1）——即收紧的是授权维度，policy-less probe 派发本身保留。
- 自动快照零破坏实证：48 CLI + 906 全量绿；抽查断言实质（非 exit-only）：
  - `test_public_cli_exports_eight_score_entity_timestamp_model_and_search_receipt`（L480，**不带 model_policy**）：断 score==8、`search_status=="executed"`、request/response id、http 200、prompt/answer sha256、题面哈希——**真实派发语义完整保留**；
  - L466 容量耗尽反例：exit==1、posts==0、无输出、health 库字节级不变——既有 fail-closed 反例未被快照稀释；
  - Q06/Q09 identity e2e（unit 15 + Q09 glue）不走 `_invoke` 快照路径，直接生命周期断言，906 内全绿 ✓。
- **关键事实**：仓库内 **18 个** CLI 测试以 `_invoke` 无 `model_policy` 运行 require-search 并断言成功回执/评分——**policy-less 派发是被大量钉住的既有已验证契约**（Q06-Q10 面，卡禁改）。这正是卡设计1（policy 未配置→入口 blocked）无法直接落地的原因，也是必须显式披露划界的理由（P2-1）。

### 4.2 预检覆盖面 vs BENCH-02 when 三触发（如实评估）
| when 触发 | 入口预检 | 运行时层 | 结论 |
|---|---|---|---|
| hard spend cap = 0 | ✅ `hard_cap<=0`（bool 亦拒）→ blocked，探针 c5 | — | **入口全覆盖** |
| price snapshot missing | ⚠️ 仅验 `pricing_snapshot_ref` **非空**；引用不可解析/不存在的费率 → 入口放行 | policy 配置运行：Q09 准入/结算期暂停（既有 `test_budget_denial_happens_before_sync_http_post`、rate-card 测试=零 POST ✓）；policy-less 运行：**无账本直接派发**（C1） | 结构性覆盖；真实性解析留待 B01-b manifest 绑定（LOW-5），policy-less 面见下 |
| search/model quota cannot be established | ❌ **无字段、无检查**（卡设计1 的 policy/max_cost/cost_policy 入口检被 v2 静默替换，未标废止） | policy 配置运行：route/group 容量与 `budget_route_limit_missing` 等准入拒（Q09，零 POST ✓）；capability 缺失 → 换路由（L820 测试 posts=1 走 backup）；**policy-less 运行：quota 组不存在仍派发（C1 posts=1）** | **入口零覆盖**；运行时仅对 policy 配置运行 fail-closed |

即：**「quota cannot be established」的入口级预检未覆盖，运行时准入只对 policy 配置运行成立；policy-less 形态（有效快照）实证出站 1 POST**——与 BENCH-02 文本（when 触发(c) → then-2「exactly zero」）在宽读法下直接冲突，且该冲突被 18 个既有钉子测试固化为保留契约。**卡与测试文件对此的表述失实**（见 P2-1、LOW-6）。

## 5. 范围与诚实性

- 范围：实现面恰 3（+1 已披露 harness 文件，diff 仅增参无断言改动 ✓）；StockWiki 零改动 ✓；无网络/LLM/密钥（mock session、fixture key、探针全离线）✓；`git diff --check` 净 ✓。
- **披露充分性**：harness `_invoke` 增参在 **Phase 83 勘验节**明示「卡允许面外（integration 测试文件），随提交披露」+ 零破坏证据（48/906 实测）——**披露本身充分**，但位置在 plan 而非卡「允许改动」节（INFO-1）；卡 v2 L35 已在设计层声明「harness `_invoke` 默认代供有效快照」。
- **过度声称扫描**：
  1. 新测试模块 docstring（L3-5）："…**or an un-establishable quota must BLOCK the public entry**…" ——quota 既无实现也无测试 → **可证伪**（P2-1 证据）；
  2. 卡 v2「BENCH-02 的 then 全覆盖」——仅在"授权缺失/无效触发"的作用域内成立（本审探针证实该作用域全绿）；宽读法（三触发）不成立 → 需显式限定作用域（P2-1 整改项）；
  3. 卡设计1 与 v2 内部不一致且未标废止（P2-1 整改项）；
  4. 卡 v2「或默认路径 spend_authorization.json」未实现（探针 A2）→ LOW-2；
  5. Phase 83 GREEN 记录「生产不动+**新 run_id**」与测试实况（无 run_id 断言）不符 → LOW-3。
- 未发现虚构费用/live 声称（B01-b 未启动、卡明示未放行不执行 ✓）。

## 6. Findings

**P0 / P1：无。**

**P2（阻断）**
- **P2-1 BENCH-02「quota 不可建立」触发未覆盖且被失实声称**：(i) `_spend_authorization_preflight` 无 quota/policy 检查，卡设计1（policy 未配置/max_cost≤0/缺 cost_policy → 入口 blocked）被 v2 **静默替换、未标废止**；(ii) 实证（C1）有效快照+无模型策略 → **exit 0、出站 POST=1、零预算/配额跟踪**，与 then-2「exactly zero」在该触发下冲突；(iii) 测试模块 docstring「un-establishable quota must BLOCK」与卡 v2「全覆盖」（宽读法）为可证伪声称；(iv) 直接补入口 policy 检会**打破 18 个已验证 policy-less CLI 钉子测试**（卡禁改面）——正因如此该冲突必须显式披露/签认，不能沉默略过。**整改二选一**：(a) 卡 v2/测试 docstring/Phase 83 修正——明确三触发的作用域划分（入口=授权快照结构；quota/price 真实性=运行时准入，仅对 policy 配置运行 fail-closed；policy-less probe 派发=保留的已验证契约并给出处置签认）并撤回失实句；或 (b) 补入口 policy/quota 预检并同步重新协商 18 个钉子测试（owner 决策）。整改以文档/披露为主，可不含生产代码变更。

**LOW（非阻断）**
- **LOW-1** blocked 载荷（status/reason/run_id/exit==2）无自动化断言——测试仅 `exit_code != 0`（预检若改走异常路径 exit 1 仍可通过）；注释称 "verified via -s"。本审探针已逐字实证载荷正确，但建议补直调 `LLMRunner.run(...)`+capsys 或回传 stdout 的断言。
- **LOW-2** 卡 v2「或默认路径 `spend_authorization.json`」未实现（探针 A2：cwd 有有效默认文件、无 flag → 仍 blocked）。fail-closed 方向，无安全问题——卡文与实现二选一修正。
- **LOW-3** Phase 83 GREEN 记录把「新 run_id」列为第三测的测试内容，实际测试无 run_id 断言（仅代码生成+本审探针证实）——记录措辞与实况不符。
- **LOW-4** 卡设计3「运行前后 workspace 快照比对」未实现为测试（实测仅 tmp store 缺失+零 POST）；预检时点保证下风险低，卡文与测试二选一修正。
- **LOW-5** `pricing_snapshot_ref` 仅验非空、不解析不交叉校验（任意非空串即过）——then-4 的「valid price snapshot」仅结构性满足；真实性绑定应明示留待 B01-b manifest（卡 L15 已提 B01-b 占位，建议在 v2 补一句边界）。
- **LOW-6** B01 测试 docstring 首句的三触发枚举与实现覆盖面不符（quota 半句不成立；见 P2-1(iii)）——整改时与 P2-1 同批修正。

**INFO（披露，无需改动）**
- **INFO-1** 卡「允许改动」未列 `main_with_llm.py`（v2 的 flag 隐含、Phase 83 提交清单已列）与 harness integration 文件（Phase 83 勘验节已披露）——建议提交前把允许面清单与实况对齐一次。
- **INFO-2** 退出码 2 与 argparse usage 错误码撞车（语义可区分场景，仅披露）；reason 为闭集有界码、无异常文本注入 ✓。
- **INFO-3** PowerShell 保存（带 BOM）的授权快照 → `spend_authorization_invalid`（fail-closed，不会误放行）——操作提示：UTF-8 无 BOM。
- **INFO-4** 906 分解 = Q09 审基线 897 + Q10（已提交，6 测试）+ 本批 3，与预期 906 精确一致；StockQA 根 untracked 杂物（`nul` 等）照旧不在范围。

## 7. 裁决

**needs_revision**（无 P0/P1；唯一阻断 P2-1 = BENCH-02 quota 触发的覆盖缺口与失实声称——整改为卡/docstring/记录的**披露与作用域修正**（或 owner 决策补入口 policy 预检），不含必须的生产代码变更；LOW×6 / INFO×4 非阻断）。
授权维度的入口 fail-closed 门本身实现扎实：门全绿（3/48/906/Success/黑盒净）、载荷/退出码/时点/零状态经独立探针逐字证实、harness 增参披露充分、既有面零破坏经断言实质抽查证实。P2 整改完成后建议复审一轮（文档+断言收紧即可闭环）。

---

## 8. r2 复审段（2026-10-06 — 整改后字节复核；**本段为最终裁决依据**，取代 §7 裁决）

整改输入：IQS 处置提交 `9246102`（卡设计1 废止 + v2【r1 作用域限定 P2-1】+ Phase 83【r1 更正 LOW-3】）+ StockQA 工作区改动（LOW-2 默认路径、exit==2、测试 docstring 收窄）。

### 8.1 门独立复跑（当前字节）

| 命令 | 结果 |
|---|---|
| `pytest tests/unit/test_b01_preflight.py -q -p no:cacheprovider -o addopts=` | **3 passed** in 2.08s |
| `pytest tests/integration/test_quick_scan_cli.py -q -p no:cacheprovider -p no:base_url -o addopts=` | **48 passed** in 6.88s |
| `pytest tests/ -q -p no:cacheprovider -p no:base_url -o addopts=` | **906 passed, 4 skipped** in 82.15s，**0 errors** |
| `mypy main_with_llm.py src/runners/llm_runner.py` | **Success: no issues found in 2 source files** |
| `black --check -l100`（4 触及文件）/ `ruff check` / `git diff --check` | 4 files unchanged / All checks passed / 净 |
| 仓根 `Test-Path spend_authorization.json` | **False**（默认路径回落未污染测试隔离） |

### 8.2 (a) P2-1 作用域限定与设计1 废止 —— ✅ 消解（字节核证）
- 卡 L11：删除线 + **【v2 废止此条】** + 理由（18 个 policy-less CLI 钉子测试=禁改面，直接落地将破坏）+ **policy/配额维度入口化留待 owner 决策**（B01-b manifest 快照+policy 并备）✓。
- 卡 L33：**【r1 作用域限定 P2-1】**覆盖面=授权快照缺失/无效两类；quota 触发**入口零覆盖**（policy 配置运行由运行时准入 fail-closed 兜底、policy-less 派发=保留契约待 owner）；price 真实性解析留 B01-b、入口仅验非空；**「then 全覆盖」的宽读法不成立，以本段限定为准**——可证伪声称已显式撤回并设治理句 ✓。
- 测试模块 docstring（L3-9）收窄：covered trigger = SPEND-AUTHORIZATION snapshot；并明示 "The BENCH-02 'quota cannot be established' trigger is **NOT covered at the entry** (policy-less dispatch remains the pinned contract)" ✓。
- 残余（cosmetic）：L33 行尾旧括注仍含「BENCH-02 的 then 全覆盖…」字样，位于治理句之后并受其约束——建议下批删改括注 → **INFO-5**。

### 8.3 (b) LOW-2 默认路径 —— ✅ 实现 + 4 探针复跑
实现（llm_runner 净 +1 行，改动面=默认路径约 5 行）：`resolved = Path(path) if path else Path("spend_authorization.json")`（cwd 相对），附 r1 LOW-2 注释；卡文「或默认路径」与实现现一致 ✓。
- **A1** cwd 无默认文件、无 flag → blocked，`reason=spend_authorization_missing`，**exit=2**（fail-closed 不变）；
- **A2** cwd 有**有效**默认文件、无 flag → **放行**（exit=1=config 期失败、blocked 载荷 absent——预检已过）；
- **A3** cwd 默认文件 hard_cap=0 → blocked，`reason=spend_authorization_invalid_hard_cap`，exit=2（**默认文件被校验而非盲信**）；
- **A4** harness `spend_authorization=None` + cwd 有效默认 → **exit=0、posts=1、产出结果文件**（端到端授权放行）；
- A5 精确码不变（invalid_hard_cap / missing_pricing_snapshot / missing）；A6 两次 blocked run_id 互异、exit [2,2]。

### 8.4 (c) exit==2 断言核证 —— ⚠️ **声称与字节不符：实为 1/3，非 3/3**
- 字节实况：test3 L90 `assert exit_code == 2` ✓；**test1 L60 与 test2 L74 仍为 `exit_code != 0`**（其注释文本亦仍写 "exit != 0"）。
- LOW-1 其余（载荷/status/run_id 无自动化断言）已**如实留档**：测试注释（L63-65/L76「verified via -s；capsys 与嵌套 stdio 冲突」）+ Phase 83 更正句 ✓——未假装已断言 ✓。
- 残余风险：test1/2 对「预检改走异常→exit 1」仍假阳性通过；两处收紧在技术上无障碍（探针 A1/A3 实证两路径恒 exit=2）→ **LOW-1 记部分闭合**，两行收紧建议随提交顺手完成。

### 8.5 (d) Phase 83 更正 —— ✅ 与实况一致
`【r1 更正 LOW-3】第三测断言实况=exit==2/零出站/零 store，run_id 审计性未自动化断言（stdout 经 -s 人工核验；capsys 与嵌套 stdio 冲突）——非「run_id 已断言」`——与字节逐项相符（第三测确为 ==2）✓；GREEN 描述已去「新 run_id」✓；harness 面外勘误保留 ✓。IQS `9246102` 仅改卡（L11/L33）+ plan（L1224）各一处，无夹带 ✓。

### 8.6 (e) 范围与离线 —— ✅ 恰 3 面
`main_with_llm.py` +7（与 r1 同）、`src/runners/llm_runner.py` 53→**54**（差额=LOW-2 默认路径块，无其他改动）、`tests/unit/test_b01_preflight.py`（docstring 收窄 + exit==2×1）；harness 文件 +19 与 r1 逐字节同（无新改动）；StockWiki 零改动；untracked 杂物不在范围；探针/门全程离线、无网络无密钥 ✓。

### 8.7 整改声称核对（r2 反馈 vs 字节）

| r2 反馈声称 | 字节实况 | 判定 |
|---|---|---|
| P2-1 走路线 (a)（卡废止+作用域限定+docstring 收窄） | 均在（L11/L33/docstring L3-9） | ✅ |
| LOW-2 默认路径实现（A2 应放行） | 实现 + A1-A4 探针全证实 | ✅ |
| Phase 83 LOW-3 更正 | 与实况一致 | ✅ |
| 「**三处** `!= 0` 收紧为 `== 2`」 | **仅 test3 一处；test1/2 仍 `!= 0`** | ❌ 不实 |
| 「LOW-4 卡处置记录明示（workspace 快照比对未实现为测试）」 | **卡 L13 原文未动，卡/plan 均无该处置记录** | ❌ 不实（LOW-4 仍开放） |
| 「INFO-1 卡允许面清单补正（main_with_llm+harness）」 | **卡「允许改动」节未动**（两文件仍未列入；Phase 83 的 3 面+勘误系 r1 既有） | ❌ 不实（INFO-1 仍开放） |

持久记录本身诚实（Phase 83 更正句准确、卡的限定段真实落地）；失实集中在本轮反馈汇总——提交前请以本表更正（提交信息勿沿用「exit==2 pinned ×3」口径）。

### 8.8 r2 findings
**P0 / P1 / P2：无（r1 唯一阻断 P2-1 已实质闭环）**。
开放残留（均非阻断）：
- **LOW-1（部分闭合）** test1/2 仍 `exit_code != 0`，宜与 test3 对齐为 `== 2`（两行）；
- **LOW-4（未落）** 卡 L13「workspace 快照比对」承诺与测试实况的处置记录未入卡——补一句「以 tmp 断言+预检时点保证代替，快照比对不实施」或改卡文；
- **INFO-1（未落）** 卡「允许改动」清单补列 `main_with_llm.py` 与 harness integration 测试文件；
- **INFO-5（新增）** 卡 L33 行尾旧括注「then 全覆盖…」建议删改，避免与治理句并列造成略读者误读；
- **记录更正**：r2 反馈三处失实（8.7 表）需在提交信息/处置台账中更正。

### 8.9 终裁
**approved**。r1 唯一阻断 **P2-1 已以文档路线实质闭环**（设计1 废止+作用域限定+docstring 收窄，字节逐条核证，可证伪声称撤回并设治理句）；门独立复跑全绿（**3 / 48 / 906 passed·4sk·0 errors / mypy Success(2) / black·ruff·diff-check 净**）；**LOW-2 默认路径实现并经 4 探针证实**（无效→blocked exit2、有效→放行、端到端 posts=1、默认文件被校验）；Phase 83 更正与实况一致；范围恰 3 面、离线无密钥。残留 LOW-1（部分）/LOW-4/INFO-1/INFO-5 及三处反馈失实为非阻断记档——建议随 StockQA 隔离提交前顺手完成（两行 exit==2 + 两句卡文）并在提交信息中按 8.7 更正口径；B01-b live 段另批（成本声明+owner 放行硬门不变）。
