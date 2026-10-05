# W11 定向补扫接线批次 — 独立审查报告（r1）

日期：2026-10-05。审查者：独立审查 agent（与实现者无关，全部门/断言独立复跑复算，未采信施工卡描述）。
审查对象：W11「接通有范围与预算的定向补扫」（tasks.json id=W11，case=QUERY-04/TIME-05/JOB-06/DB-07，invariants=I09/I13/I18）。
裁决：**needs_revision**（1×P1 阻断 + 7×P2，无 P0；门与 case 断言本身全绿，问题在"接通"半程未做且卡内有未兑现承诺与一处失实记录）。

---

## 1. 范围

### 1.1 被审改动（实际 git 状态，独立核对）

| 仓 | 命令 | 结果 |
|---|---|---|
| StockWiki | `git -C C:\Users\郑曾波\Projects\StockWiki status --porcelain` | 恰 2 处新增：`?? stockwiki/quick_scan_refresh.py`、`?? tests/test_quick_scan_refresh.py`；`git diff --stat` 为空（既有文件零改动） |
| IQS | `git status --porcelain` | 仅 `?? opencode.json`（既有杂物）；本批 4 文件已提交：`b495eee`（卡 8 行修订 + progress + task_plan + `tests/test_time05_scope_update.py`）、`2dc8221`（写前卡 47 行 + progress + task_plan Phase 79） |
| StockQA（I18 零改动核对） | `git -C C:\Users\郑曾波\Projects\StockQAbyLLM status --porcelain` | 仅既有 untracked 杂物（`.codegraph/`、`.workbuddy-ai/`、`nul`、`pilot_runs/*`、`progress_update.txt`）；**无任何已跟踪文件改动** ⇒ StockQA 源码改动=0 属实 |

注：任务描述中的 StockQA 路径 `Projects\StockQA` 不存在，实际仓为 `Projects\StockQAbyLLM`（已按此核对）。

### 1.2 只读参照（已读原文，非采信摘要）
- `tasks.json` L2228-2274（W11 steps/allowed_changes/case_ids/completion）
- `acceptance-cases.json`：QUERY-04 L1592、JOB-06 L1272、TIME-05 L924、DB-07 L1386
- `decision-register.md` L15=I09、L19=I13、L24=I18（原文核对无误）
- StockWiki `quick_scan_query.py`（`profiles_from_store` L68-112 只投影 entity_id/canonical_name/identity_state/securities；`coverage` L397-440 为聚合粒度）、`quick_scan_delivery.py`（W10）
- IQS `scripts/work_contract.py`（`field_freshness_preview` L73-97、`logical_work_key` L177-189，纯 stdlib 导入 L8-11）
- IQS `docs/implementation/contracts/exchange-and-query.md` L61（request_refresh 协议要求）、`schemas/quick_scan/query.schema.json`（RefreshPayload/RefreshPreviewResult）
- StockQAbyLLM `main_with_llm.py` L210-276（既有参数面）

### 1.3 声明范围 vs 实际
- StockWiki 两新文件、IQS 一新测试 + 卡/Phase 79/progress 记档 —— **与声明一致**（见 1.1）。
- 本报告为本次审查唯一写入文件；三仓其余内容只读。复算脚本以 stdin 传入 python（不落盘），JOB-06/全池复算用的一次性临时 store 建在 `%TEMP%` 并 `finally` 删除，**不落在三仓内**。

---

## 2. 门独立复跑（命令 + 数字）

### 2.1 StockWiki

| 门 | 命令 | 独立结果 | 卡/记录声称 | 一致 |
|---|---|---|---|---|
| 全量 | `bash scripts/check_all.sh`（本审查后台 pwsh-130，exit 0） | ruff clean；`coverage run -m pytest -q` → **926 passed, 15 skipped in 302.48s**；`coverage report --fail-under=73` → **TOTAL 81%** PASS；ui.py **75%**（≥40）PASS；validate-framework → **12 warnings / 0 errors** → **`=== ALL CHECKS PASSED ===`** | 923 既有 + 新测试、0 errors、12 既有 warnings、≥73% | ✔（923+3=926 自洽） |
| 定向 | `python -X utf8 -m pytest tests/test_quick_scan_refresh.py -q -p no:cacheprovider -o addopts=` | **3 passed in 0.47s** | 3 passed | ✔ |
| 格式 | `python -m black --check -l100 stockwiki/quick_scan_refresh.py tests/test_quick_scan_refresh.py` | exit 0，`2 files would be left unchanged`（stderr 有 Python3.13/目标3.15 解析警告，非失败） | black 净 | ✔ |
| Lint | `python -m ruff check stockwiki/quick_scan_refresh.py tests/test_quick_scan_refresh.py` | **All checks passed!**（exit 0） | ruff 0 | ✔ |

### 2.2 IQS

| 门 | 命令 | 独立结果 | 声称 | 一致 |
|---|---|---|---|---|
| TIME-05 定向 | `python -X utf8 -m pytest tests/test_time05_scope_update.py -q -p no:cacheprovider -o addopts=` | **2 passed in 0.13s** | 2 passed | ✔ |
| 计划门 | `python -X utf8 -m pytest tests/test_implementation_plan.py -q -p no:cacheprovider -o addopts=` | **80 passed, 53 subtests passed in 15.28s** | 80/53 | ✔ |
| Lint | `python -m ruff check tests/test_time05_scope_update.py` | **All checks passed!** | ruff 0 | ✔ |
| 空白 | `git diff --check` → exit 0；另 `git show --check HEAD` → exit 0 | 0 | 0 | ✔（改动已提交，故补 `show --check`） |
| 附加 | `python -m black --check -l100 tests/test_time05_scope_update.py` | 会重排 1 处（见 INFO-1） | 未声称 | 见 INFO-1 |

**门结论：无一失败，无 skip 充数（定向 3+2 全实际执行）。**

### 2.3 独立复算探针（非采信测试，直接对实现）

1. **顺序探针（毒 store：任何属性访问即抛）** —— 证明 SQL 形输入在任何 store 访问前被拒：
   - `entities=["ENT_A'; DROP TABLE entity;--"]` → `RefreshError input_rejected`
   - `fields=["industry';--"]` → `input_rejected`
   - `fields=["not_in_set"]` → `scope_field`
   - `entities=[]` → `bad_request`
   - 对照组（合法入参）→ `STORE ACCESSED`（证明该探针确有区分力，不是恒不访问 store）
2. **纯度探针**（先将 `socket.socket`、`sqlite3.connect` 替换为必抛函数，再调 `derive_scope_update`）：
   - `{"threshold": {...}}` → `model_calls=0`、`work_keys=[]`、`derived_updates=[{kind: threshold_derived,...}]`
   - `{"new_questions":[Q_1..Q_3]}` → `model_calls=0`、**3 个互异 5 元组 tuple**、无 I/O 异常抛出
3. **4 实体临时池复算**（池 = A/B/C/ENT_D_POOL）：
   - 请求 3 家 → items 实体 = `['ENT_A','ENT_B','ENT_C']`，count=3（**无全池**，实现正确）
   - 全覆盖字段 + `cost_cap_micros=0` → items=0 / reused=1 / estimate=0（**有效字段复用且不计费**）
   - 重复入参（实体×2、字段×2）→ items=4 但 unique task_key=1、estimate=4,000,000（见 P2-5）
   - JOB-06 V1(2实体)→V2(3实体)：`carried_over_keys==v1_keys=True`、`v1k⊆v2k=True`、fingerprint/batch_id 均不同（版本与覆盖可追踪）
   - `incorporation_country`（store 里有值）→ items=1 / reused=0（恒缺口，见 P2-4）
   - `identity_state` → `RefreshError scope_field`（与卡记录矛盾，见 P2-1）
4. `REFRESHABLE_FIELDS` 实测 = `['canonical_name','incorporation_country','industry','segments']`（4 项）。

---

## 3. 逐 case 语义证据

### 3.1 QUERY-04（负例，owner=W11）— 原文 then：「仅允许范围内缺口，费用上限适用；禁止直接写库或扩成全池；有效字段复用。」

| 语义点 | 实现证据（行号按 `stockwiki/quick_scan_refresh.py`） | 测试断言 | 独立复算 |
|---|---|---|---|
| 范围外实体具名拒绝 | L155-164：`_ENTITY_ID` 形状先校验 → `profiles_from_store` 后 `missing` → `RefreshError("scope_entity", ...)` | `pytest.raises(RefreshError)` + `"scope" in str(...)` | 毒 store 探针 + 4 池复算 ✓ |
| 字段具名拒绝 | L150-154：形状 `input_rejected` / 词表 `scope_field` | 同上（仅 `pytest.raises`，未断 code） | 实测 code ✓ |
| SQL 形输入先于任何 store 访问 | L150-158 全部校验 **先于** L160 `profiles_from_store(store)`；模块无任何 SQL 文本 | 测试只断 `raises(RefreshError)`，**未验证顺序** | 毒 store 探针证明顺序 ✓（对照组会被访问） |
| 费用 cap 生效 | L179-181 `estimate=len(items)*REFRESH_COST_MICROS > cost_cap_micros` → `cost_cap` | `cost_cap_micros=1` → raises + `"cap" in str` ✓ | 全覆盖+cap=0 → estimate=0 通过 ✓ |
| 有效字段复用不提交 | L172-177 `_covered` → 入 `reused`，否则入 `items` | 断 ENT_A/canonical_name 不在 items；**未断 `reused` 非空** | items=0/reused=1 ✓ |
| 不扩全池 | L169 `for entity_id in entities`（仅迭代请求集），空 entities 直接 `bad_request` | `{entity_id} <= 所请求集` —— **夹具池=请求集，恒真、不具区分度** | 4 池复算：请求 3 → items 只含 3 ✓ |

3 家×2 字段部分有效：`fields=["canonical_name","industry"]`，夹具 3 家，canonical_name 恒覆盖 / industry 恒缺口 —— 与 case given 一致 ✓。
**结论：QUERY-04 语义在实现层面全部成立；证据链的薄弱点在测试断言（P2-2、P2-7），不在实现。**

### 3.2 JOB-06（metamorphic/integration，owner=W11）— then：「旧任务不重建，新增实体并入增量；版本和覆盖范围可追踪。」

- **task_key 与 roster 版本无关（关键前提）**：`_task_key` L62-66 只吃 `entity_id|field|generation`（generation 恒=1），**不含 roster_version** ✓（读实现 + 复算 `v1k⊆v2k=True`）。
- 旧任务不重建：V2 的 `items` 中旧实体键与 V1 完全相同（内容寻址），`carried_over_keys = prior ∩ current`（L183-201）——实测 `carried_over_keys == v1_keys=True`，消费方据此跳过。
- 增量只含新实体：测试 `increment = entities(v2 items) − entities(v1 items)` `<= {"ENT_C"}` ✓；我方 4 池复算一致。
- 可追踪：`roster_version=2`、`prior_roster_version=1`、`coverage_fingerprint` 与 `batch_id` 在 V1/V2 均不同 ✓（测试断了前两个 + fingerprint 非空，未断"指纹随版本变化"）。
- **注意**：`items` 并非严格"增量"——它重列所有未覆盖项（含旧实体），增量语义靠 `carried_over_keys` + 执行器幂等承载；测试未断 `carried_over_keys`（见 P2-7 / INFO）。

### 3.3 TIME-05 双侧（owner=C04，本批执行其契约测试）— then：「阈值修改模型调用0；新增题只产生3个逻辑待办键；旧观察的内容/来源/时间不变；持久化队列实现由Q06/W06验收。」

**IQS 侧（真对既有 `work_contract.py`，非替身）**
- `import work_contract`（`sys.path` 插 `scripts/`，与既有 `test_freshness_and_jobs_contract.py` 同款写法），调用真函数 `field_freshness_preview(field_metadata, now=...)`、`logical_work_key(entity, q, gen, scope, scope_id)` ✓。
- 派生 `dispatch_started=False` 零模型调用：fresh/stale 两个窗口均断 `dispatch_started is False`，stale 侧 `refresh_needed_fields==["industry"]` ✓（`field_freshness_preview` L96 硬编码 False，属"预览永不派发"的契约常量，与 prepstudy 期望 `dispatch_started=false` 一致）。
- 恰 3 个互异 5 元组逻辑键：`len(keys)==3` 且 `len(set(keys))==3` ✓；"阈值改动不铸新键"用同参重调 `same==same_again` ✓。
- **旧观察不可变：断言空转** —— `old` 从未传给被测函数（preview 吃 metadata、`logical_work_key` 吃 id），`old==frozen` 恒真（P2-3）。
- 阈值路径本身在 `work_contract` 中无独立"threshold"入参：测试用"同 now、不同 validity window"的两次 preview 作为阈值派生的替代语义（映射为解释性，P2-3 附注/INFO）。
- 纯度：`work_contract.py` 只导入 datetime/hashlib/json/re（L8-11），无 DB/worker/HTTP ✓。

**StockWiki 侧（`derive_scope_update` 纯函数）**
- 实现 L77-121：函数体只做类型/形状校验与列表构造，**无 DB、无 worker、无 HTTP 调用**（模块级仅 `hashlib/json/re` + 从 W09 导入 `profiles_from_store`，但该函数在 `derive_scope_update` 内未被调用）✓。
- `threshold` → `model_calls=0`、`work_keys=[]`、有派生更新 ✓；`new_questions` → 3 个互异 5 元组 ✓（独立探针，非仅测试）；`old_observation` 作为入参被读取且断言未变（**非空转**）✓。
- I09 的"规则变更不触发模型"在两侧都有显式断言 ✓。

### 3.4 DB-07（owner=Q10）
卡 L29：「不在本批执行；其『消费者不写 SQLite』面向 I13 的部分由本批接口设计覆盖，durable block/outbox 语义留给 Q10」；`task_plan.md` L1175 记「DB-07 归 Q10」。全仓 grep `DB-07` 无任何"已执行/已通过"声称（findings.md/progress.md 均为历史他批语境）。**无越权声称 ✓。**

---

## 4. 不变量对照

### I09（L15：时效按字段和实际信息；规则变更不触发模型）
- 阈值/规则路径 `model_calls=0`：StockWiki `derive_scope_update` 返回恒 0（探针+测试双证）；IQS `field_freshness_preview` 恒 `dispatch_started=False` ✓。
- "按字段"：缺口/复用按字段逐项判定（L169-177），非按 last_run 一刀切 ✓。
- "按实际信息"：**部分** —— owner 接口侧的缺口只看"字段是否存在"，不看 information_as_of/过期/事件失效（`request_refresh` 不接触 `valid_until`/`information_as_of`）；时效判定留在执行器侧 `work_contract.freshness_status`。两条链路无集成测试衔接 → P2-4。
- 无"新 run 全问"：有效字段复用 ✓、增量按实体 ✓。

### I13（L19：消费技能只读查询，定向补扫/走拥有者接口；不得为 3 家补缺触发全池、直接改库）
- **无 SQL 面**：`request_refresh(store, *, entities, fields, cost_cap_micros, roster_version, prior_task)` —— 无 connection/sql/query 参数；入参严格字符类（实体 `[A-Za-z0-9_-]{1,160}`、字段 `[A-Za-z0-9_]{1,64}`），引号/空格/分号不可能穿透；SQL 形输入在 `profiles_from_store` 之前被拒（毒 store 探针证明）✓。
- **无全池路径**：`entities` 非空列表为硬前置（空→`bad_request`），items 只由请求集迭代产生；不存在"省略 entities 即全池"的分支（探针 + 4 池复算）✓。
- **消费者不直接改库**：模块零写库代码（唯一 I/O 是 W09 `profiles_from_store` 的 SELECT）；`store` 由 owner 侧持有，消费者拿不到写通道 ✓。
- 遗留：接口**没有任何对外入口**，"消费者经拥有者接口提交"目前不可发生（P1-1）。

### I18（L24：真实接口先核实，跨仓一个任务一个写入拥有者）
- 只调用 W09 公共函数 `profiles_from_store`（`quick_scan_query.py`）✓；`quick_scan_query.py`/`quick_scan_delivery.py` 零改动（git status）✓。
- StockQA 零改动（`StockQAbyLLM` 无已跟踪改动）✓；本批写入拥有者唯一（StockWiki 2 文件 + IQS 文档/测试）✓。
- 未重写既有模块、未把设计命令当现存 API（卡 L9 已 grep 实证 `request_refresh` 原不存在，本批新建）✓。

---

## 5. 范围与过度声称扫描

| 声称（出处） | 核验 |
|---|---|
| `check_all` ALL PASSED / framework 0 errors / 12 warnings（task_plan L1178、卡 L53） | 我方独立复跑 **全部相符**（926 passed、81%、12 warnings、exit 0）✔ |
| 定向 3 passed、IQS 2 passed、plan 80/53、ruff 0（同上） | 全部独立复跑相符 ✔ |
| 卡 L53 写"check_all 后台（pwsh-120）待收"而 task_plan/progress 已写 ALL PASSED | 时序上是"卡先记待收、记档后补结论"，结论本身经我复跑证实 ✔（轻微不一致，INFO） |
| docstring 预算披露（L9-12：离线估价仅用于 cap 检查，真预算与模型策略由执行器 Q09 统一落实） | **诚实**：`REFRESH_COST_MICROS=1_000_000` 确只用于 `estimate > cap`；模块无费率卡、无预算落盘 ✔ |
| `llm_calls=0` / `network_calls=0` | **属实**：模块无网络代码、无 LLM 调用；测试全离线（临时 SQLite）；`coverage()` 类 W09 函数亦恒 0 ✔ |
| 卡 L51 实施记录：`REFRESHABLE_FIELDS` 含 `identity_state` | **失实**：实际 4 字段无 identity_state，实测 `scope_field` 拒绝 → P2-1 |
| 卡 L21-22：输出工件"格式对齐 StockQA 现有入口可消费的题面/实体清单"、"题面清单由工件携带" | **未兑现**：工件只有 `{entity_id, field, task_key}`，无题面/问题 ID，也无 field→question 映射 → P1-1 |
| 卡 L23 设计第 3 条：状态回读经 W10 `project_runtime_status` | 本批零代码零测试引用（grep W10 函数在新增文件中无命中）→ 并入 P1-1 |
| 卡 L18 设计："缺口检测走 W09 `coverage`" | 实现走 `profiles_from_store` + 本地 `_covered`；实施记录 L52 已披露偏离（`coverage()` 是聚合粒度，无法逐实体逐字段，偏离必要）→ LOW-2 |
| 允许改动清单 | 卡"允许改动"第 3 条在 GREEN 提交 `b495eee` 中**事后修订**加入 `tests/test_time05_scope_update.py`（内嵌"实施期修订补入"标注）→ LOW-1 |
| DB-07 | 无越权声称 ✔ |

---

## 6. Findings

### P1（阻断）

**P1-1 「接通」只有接口层：无入口、无消费方、step1 后半与卡设计承诺未做，也未显式延期**
- 证据 1（无入口）：StockWiki 全仓 grep `request_refresh|derive_scope_update|quick_scan_refresh` **只命中新增 2 文件**；`stockwiki/cli.py` 无 refresh 命中，`cli_parsers/` 中含 refresh 的 6 个文件均与本接口无关；无 HTTP/UI 路由。
- 证据 2（无消费方）：IQS 全仓同 grep 只命中 docs 与 `tests/test_time05_scope_update.py`（且该测试不 import 本模块）；prestudy 设想的 `scripts/quick_scan_client.py` **不存在**（`Test-Path=False`）；StockQAbyLLM 零改动。
- 证据 3（工件不可直接驱动既有入口）：`main_with_llm` 参数面 = `--company/--provider/--config/--output/--batch/--entity-id/--identity-snapshot/--require-search/...`；refresh 工件只有 field 级条目，无题面/问题 ID，字段→题面的映射不存在 ⇒ 卡 L21「格式对齐…题面/实体清单」与 L22「题面清单由工件携带」无实现、无测试。
- 证据 4（依赖未动）：deps 含 W10，卡设计第 3 条要求状态回读走 `project_runtime_status` —— 本批零调用、零测试。
- 证据 5（case 级别与测试级别错位）：QUERY-04/JOB-06 在 acceptance-cases 中 `level=integration`，但测试只到 owner 函数本体，没有执行器/入口侧集成。
- 影响：tasks.json W11 标题「接通…」、step1「生成白名单任务，**复用同一个 StockQA 执行入口**」、deliverables「补扫提交/**状态**接口」的后半段无证据；卡在写前报告中承诺却未在实施记录中披露该缺口。
- 整改二选一：(a) 补最小接线 + 1 条离线端到端测试（入口消费工件 → 白名单增量 → 执行器复用既有 `main_with_llm` 参数面，仍可保持 StockQA 源码 0 改动）；(b) 由 owner 显式把 W11 收窄为"拥有者接口层"，改卡与 `tasks.json` step 文字，并把接线立为后续卡（**改 tasks.json 需 owner 批准，非实现者可自行决定**）。

### P2（阻断级缺陷，但不推翻 case 结论）

**P2-1 卡实施记录与代码不符（失实记录）**：卡 L52 称 `REFRESHABLE_FIELDS = canonical_name/identity_state/incorporation_country/industry/segments`，实际 frozenset 只有 4 项、**无 `identity_state`**（我方实测 `fields=["identity_state"]` → `scope_field`）。需更正记录，并说明 identity_state 是否应可刷新。

**P2-2 QUERY-04「禁止扩全池」断言不具区分度**：测试 `tests/test_quick_scan_refresh.py` L103 的 `{i["entity_id"]} <= {"ENT_A","ENT_B","ENT_C"}`，而夹具池恰好就是这 3 家 ⇒ 恒真，即使实现改成全池展开也照过。实现本身正确（我方 4 池复算：请求 3 → items 只含 3），但回归防线缺失。整改：夹具增加 1 家不在请求内的实体并断言其不出现。

**P2-3 IQS TIME-05「旧观察不可变」断言空转**：`old`/`frozen` 从未作为入参传给 `field_freshness_preview` 或 `logical_work_key`，`assert old == frozen` 必真，对"观测不可变"零证明力（StockWiki 侧 `derive_scope_update(old_observation, ...)` 是真读入参后断言未变，故语义仅有单侧证据）。整改：把由 `old` 派生的 metadata 传入被测函数（或对 `old` 深拷贝后作为入参）再断言。附注：TIME-05「只改筛选阈值」在 `work_contract` 中无对应 threshold 入参，测试以"同 now、不同 validity window"两次 preview 近似，属解释性映射，建议在测试 docstring 写明该映射依据。

**P2-4 缺口语义只覆盖「缺失」，不覆盖契约要求的「过期/事件失效」，且存在恒缺口字段**：
- `exchange-and-query.md` L61（QUERY-04 所属合同的验收条款）要求「只将**缺失、过期或被事件失效**的精确字段列入缺口」；实现只做存在性判定（L173 `_covered`），stale-but-present 字段会被判 `reused`。
- `incorporation_country` 在 store 中有值，但 `profiles_from_store` 只 SELECT `entity_id/canonical_name/identity_state`（query L85-87）⇒ 该字段**永不覆盖**（实测 items=1/reused=0），会每次都被提交，与"有效字段复用"相悖；夹具注释 `_store()` 中 "ENT_A: country covered" 也因此失实。
- "执行器侧 work_contract 时效判定兜底"这条链路在本批**无集成测试**（与 P1-1 同源）。
整改：要么把 `incorporation_country` 移出 `REFRESHABLE_FIELDS` 直到投影可用，要么在缺口检测中接入时效判定；并在记录中写明兜底位置。

**P2-5 重复输入不去重**：实测 `entities=["ENT_A","ENT_A"]`、`fields=["industry","industry"]` → items=4 / unique task_key=1 / estimate=4,000,000（虚增 4 倍）、`coverage_fingerprint` 也基于含重复的列表。重复 item 若被逐条派发即触 I12（重复领取/重问）。整改：入口对 entities/fields 去重（或显式拒绝重复），并对"执行器按 key 幂等"补一条测试。

**P2-6 同名不同形的协议混淆风险**：IQS `query.schema.json` 已把 `request_refresh` 定义为查询协议操作（`RefreshPayload`/`RefreshPreviewResult`：`preview_id`、`scope_sha256`、`policy_version`、`requires_user_confirmation`、`dispatch_started=false`、≤100 entity/≤200 field、**消费者不得自填费用/预算**；`exchange-and-query.md` L61 同）。本实现同名但形状不同：caller 自填 `cost_cap_micros`、无 100/200 上限、无 preview/确认两步、无上述响应字段。prestudy（TH-01/IN-02）已把该端点记为 `not_available` 待 G3/T01。整改：模块 docstring 与卡内声明"库内拥有者接口，非 query.schema 端点；协议端点归 T01/G3"，或按合同补齐上限与确认语义（需 owner 裁定 cost_cap 归属）。

**P2-7 测试断言质量（拦不住回归）**：
- L95 `assert task["roster_version"] == task["roster_version"]  # present` —— 同义反复，未验默认值=1。
- 三处负例均只 `pytest.raises(RefreshError)` 未断 `.code`（scope_entity/scope_field/input_rejected 靠消息子串部分覆盖）；我方独立复算 code 全对，但测试锁不住。
- `reused` 列表、`carried_over_keys`（实测 == v1_keys）均无断言；JOB-06 未断"指纹随 roster 变化"。

### LOW / INFO（不阻断）

- **LOW-1** 写前卡"允许改动"在 GREEN 提交 `b495eee` 中事后加入 IQS 测试文件（已内嵌"实施期修订补入"标注，披露充分）；属事后扩范围，建议下批预先列入。
- **LOW-2** 卡设计段"缺口检测走 W09 `coverage()`"与实现（`profiles_from_store` + 本地 `_covered`）不符；实施记录已披露，且 `coverage()` 为聚合粒度、无法逐实体逐字段，偏离是必要的——但设计段未回写，后续读卡者会被误导。
- **LOW-3** `derive_scope_update` 的 threshold 分支只回显变化的 key 名（`{"kind":"threshold_derived","changes":[...]}`），不含派生值（重算后的分类/池）；`new_questions` 不去重（重复 id 会产出重复键）、未知 request 键静默忽略。
- **LOW-4** StockWiki TIME-05 测试只断 `len==3` 与 5 元组，未断三键互异；IQS 侧已断互异 ✓，我方探针亦实测互异 ✓（双侧合起来证据够，单测仍可补）。
- **INFO-1** IQS 新测试 `black --check -l100` 会重排 1 处（把 `logical_work_key(...)` 折行并回单行）。既有 IQS 测试同样非 black-clean（`test_freshness_and_jobs_contract.py`、`test_implementation_plan.py` 均 would reformat），black 不是本批声明的 IQS 门（本批只要求 ruff + `git diff --check`，两者均过），故不计为回归。
- **INFO-2** DB-07 无越权声称 ✓；卡/记档口径一致。
- **INFO-3** 离线与预算披露属实：`llm_calls=0`/`network_calls=0` 经代码与全离线测试复核成立；docstring 对"离线估价只做 cap 检查、真预算由 Q09 执行器落实"披露诚实。
- **INFO-4** StockQA 零改动经 `StockQAbyLLM` 工作树复核成立（仅既有 untracked 杂物）。
- **INFO-5** 卡 L53 记 check_all"待收"而 task_plan/progress 已记 ALL PASSED —— 结论经我独立复跑证实，仅记录时序不一致。

---

## 7. 裁决

**needs_revision**

理由（按权重）：
1. **P1-1**：W11 标题/step1 的"接通…复用同一个 StockQA 执行入口"、deliverable"状态接口"、卡 L21-23 的工件格式/题面清单/状态回读三条承诺，在本批既无实现也无测试，且未在实施记录中显式延期——这是任务级而非 case 级的缺口（case 与不变量本身不依赖它即可通过）。
2. **P2-1**（记录失实）与 **P2-2/P2-3/P2-7**（关键负例断言不具区分力/空转）会让下一轮回归失去防线；P2-4/P2-5 是语义边界（过期缺口、重复入参），需明确处置。

不构成 P0 的依据：四道门独立复跑全绿（926 passed / 81% / framework 0 errors+12 warnings / ALL CHECKS PASSED；IQS 3+2+80/53）；I09/I13/I18 逐条对照均有实现级证据（含毒 store 顺序探针与纯度探针）；范围与声明完全一致、StockQA 零改动、离线与预算披露诚实、DB-07 无越权声称。

**放行条件**：P1-1 按 (a) 补接线+1 条离线 e2e 或 (b) owner 批准的收窄改卡二选一落实；P2-1~P2-7 逐条整改或由 owner 书面接受；整改后复跑 §2 全部命令并出 r2 报告。

---

# r2 聚焦复核（2026-10-05，round-61）

**裁决：needs_revision**（r2 新增 4×P2 + 6×LOW；**无 P0、无 P1**——r1 的 P1-1 已按 owner 选项 (a) 实质达成并经我独立验证；阻断项为 3 条"声称与实物不符"的记录/披露问题 + 1 条 P2-5 整改引入的新回归，全部为 10 行量级修正）。

## R2.1 范围与提交状态（独立核对）

| 仓 | 命令 | 结果 |
|---|---|---|
| StockWiki | `git status --porcelain` | **恰 3**：`M stockwiki/cli_parsers/quick_scan.py`、`?? stockwiki/quick_scan_refresh.py`、`?? tests/test_quick_scan_refresh.py` |
| StockWiki | `git diff --numstat` | `72 0 stockwiki/cli_parsers/quick_scan.py` → **纯加法：72 增 / 0 删**（逐行核对 diff：仅 +2 import、+2 `add_parser` 块、+2 handler；**无任何既有行改动**），`git diff --check`=0 |
| IQS | `git status` / `git log` | 工作树仅 `?? opencode.json`（既有杂物）；`1fee231` = 卡 +5、r1 报告 +224、progress +2、`tests/test_time05_scope_update.py` +5 —— 与声明一致 |
| StockQA | `git -C ...\StockQAbyLLM status --porcelain` | 与 r1 **逐字相同**（仅既有 untracked 杂物）→ 产品代码 0 改动 ✓ |

## R2.2 门独立复跑（命令 + 数字）

| 门 | 命令 | r2 独立结果 | r1 对照 |
|---|---|---|---|
| StockWiki 全量 | `bash scripts/check_all.sh`（本审查后台 pwsh-176，exit 0） | ruff clean；`coverage run -m pytest -q` → **929 passed, 15 skipped in 243.83s**；coverage **TOTAL 81%**（≥73 PASS）、ui.py **75%**；validate-framework **0 errors / 12 warnings** → **`=== ALL CHECKS PASSED ===`** | 926 → **+3**：+1 条新 e2e（`test_quick_scan_refresh` 3→4）+ 2 条新命令被 `tests/test_cli_smoke.py` 参数化 smoke 纳入（COMMANDS 恰 +2），算术自洽 |
| StockWiki 定向 | `python -X utf8 -m pytest tests/test_quick_scan_refresh.py -q -p no:cacheprovider -o addopts=` | **4 passed in 1.97s** | 3 → 4 |
| StockWiki 格式 | `python -m black --check -l100`（3 文件） | exit 0，`3 files would be left unchanged` | 2 → 3 文件 |
| StockWiki Lint | `python -m ruff check`（3 文件） | All checks passed!（exit 0） | 0 |
| IQS 定向 | `pytest tests/test_time05_scope_update.py -q -p no:cacheprovider -o addopts=` | **2 passed in 0.49s** | 2 |
| IQS 计划门 | `pytest tests/test_implementation_plan.py -q …` | **80 passed, 53 subtests passed in 12.13s** | 80/53 |
| IQS Lint/空白 | `ruff check tests/test_time05_scope_update.py`、`git diff --check` | 0 / 0 | 0/0 |

另：`pytest tests/test_cli_smoke.py -k refresh -v` → **3 passed**（新命令 `--help` 干净退出 + handler 已接线，由既有 smoke 安全网自动覆盖）。

## R2.3 核查点 (a)：P1-1 三件套 + e2e 是否真达 integration 级

| 件 | 实现证据 | 独立验证 |
|---|---|---|
| 公共入口 | `cli_parsers/quick_scan.py` 新增 `quick-scan-refresh-request`（`--entity/--field` 可重复、`--cost-cap-micros` 必填、`--roster-version`、`--prior-task`、`--questions`、`--out`）与 `quick-scan-refresh-status`，handler 复用既有 `_emit/_fail` | cli_smoke 参数化自动纳入（`-k refresh` 3 passed）；`--entity` `required=True` ⇒ 无"省略即全池"入口 |
| 工件消费格式 | `render_refresh_artifact`：每 gap 实体一个 invocation，`entities_file=entity_id+"\n"`、`questions_file={categories:[{category:"refresh",questions:[{question_id,text}]}]}` | **我用 StockQA 真加载器实测**（离线、不触密钥）：`JSONConfigManager(qfile).load_question_items()` → `[('IQS_RG01', '该公司的行业地位如何？')]`；`main_with_llm.load_stock_list(entities_file)` → `['ENT_A']`；再核 `llm_runner._run_single_company` L615-631：`--require-search` 恰要求 JSON 题面带显式 `question_id` —— 工件满足该硬性要求 ✓ |
| W10 回读 | `refresh_status(paths)` = `project_runtime_status(QuickScanObservationStore(paths))`（延迟导入） | `project_runtime_status` 走 `_ro_connect`：`PRAGMA query_only=ON`、库缺失即 `store_not_migrated` ⇒ **真只读、不自建库**（e2e "先 migrate 再查"注释属实）；实测 payload 含 W10 键集（`rules_version/import_items/observations/coverage/…`）且 `llm_calls=0/network_calls=0` |
| e2e（1 条） | `test_p1_1_cli_entry_emits_consumable_artifact_and_status`：真 `stockwiki.cli.main(["--root", tmp, …])` → exit 0 | 断言区分力核过：invocations **==** {A,B,C}（池含 ENT_D，全池展开即失败）、`entities_file == entity_id+"\n"`、题面逐字相等、stdout 含紧凑 JSON 标记、status exit 0。**integration 级成立**（owner 仓内真 CLI+真 store；跨仓消费由我用 StockQA 真加载器补证，StockQA 保持 0 改动） |

残余（→ P2-r2-4、LOW-1/2）：`entities_file` 的 `load_stock_list` 表述与真实入口互斥规则冲突（`--require-search` 拒绝 `--batch`，`llm_runner.py` L550-553）且工件缺 `--company` 标签；status 只断 exit 0。

## R2.4 核查点 (b)：r1 P2×5 修复逐条核

| r1 finding | 声称 | 核验结果 |
|---|---|---|
| P2-1 卡记录失实 | "已修" | **未修** → **P2-r2-1**：卡 L51 原句仍写 `REFRESHABLE_FIELDS …（canonical_name/identity_state/incorporation_country/industry/segments）`，全卡 58 行无更正；处置记录 L57 与 progress 只写"已修"未给更正内容 |
| P2-2 池扩容区分力 | 4 实体池 | ✓ `_store` 加 `ENT_D`（L73）；断言 `touched = items∪reused`、`touched <= {A,B,C}`、`"ENT_D" not in touched`、`reused` 非空（L106-109）→ 全池展开必失败，**有区分力**（遗留恒真句 L105 → LOW-3） |
| P2-3 真传参 | `observation_compatible(old, …)` | ✓ 已加 `assert isinstance(work_contract.observation_compatible(old, dict(old)), bool)` 后再比 `old == frozen` —— `old` 现真的进入被测契约函数（浅拷贝共享嵌套引用，变异会被 frozen 深比较捕获）。仅验 `isinstance(..., bool)` 未验值、test2 仍未传参 → LOW-4 |
| P2-5 去重 | `dict.fromkeys` | ✓ 去重生效（我复算：重复实体/字段 → items=1、`estimate=1_000_000`）；**但引入回归** → **P2-r2-2** |
| P2-7 断言质量 | `.code`、去同义反复、reused/carried | ✓ 全部落地：L96 `roster_version == 1`；L119/129/139/149 四处 `.code` 分别断 `scope_entity / scope_field / input_rejected / cost_cap`；L109 `reused` 非空；L197 `carried_over_keys == sorted(v1_keys)`；L198 `reused == []` |

**P2-r2-2 证据（新回归）**：`request_refresh` L154-155 的 `list(dict.fromkeys(fields/entities))` 位于形状校验（L156-164）之前 ⇒ 不可哈希元素抛裸异常。独立复算：`fields=[["industry"]]`、`fields=[{"a":1}]`、`entities=[["ENT_A"]]` → 全部 `RAW TypeError: unhashable type`（非 `RefreshError`），违反模块 docstring「Raises RefreshError … bad request shape」。**边界**：发生在 `profiles_from_store`（L166）之前 ⇒ 无 SQL 面暴露（I13 不受影响）；CLI 侧 `except Exception` → `_fail` exit 2 fail-closed（实测缺题路径：exit 2、stderr `{"error_code":"refresh_request_failed","detail":"questions_missing: industry"}`）。修法一行：先形状校验再去重，或捕 TypeError 转 `RefreshError("input_rejected", …)`。

## R2.5 核查点 (c)：P2-4 / P2-6 延后是否 owner 书面接受 + 披露面成立

- **owner 书面接受 ✓**：卡 L58「P2-4 / P2-6：owner 书面接受延后（round-60 结构化决定+「接受」确认）：过期/事件失效留 **Q07（观察时间接入）**；与 query.schema 同名不同形留**后续 schema 统一**」；progress round-60 条目同口径。
- **披露面 ✗（半数）**：卡内披露 ✓；**模块 docstring 无披露** —— 对 `quick_scan_refresh.py` 全文 grep `Q07|schema|stale|expir|过期|失效|endpoint` 仅命中 L266 工件 schema 字符串，docstring（L1-19）无一句涉及延后语义 ⇒ 卡 L58「两者的现况已在**模块 docstring**/本记录披露」该半句不成立 → **P2-r2-3**（代码读者正是最需要看到该边界的人）。

## R2.6 核查点 (d)：范围 / 纯加法 / 离线

- 范围 = 恰 3 文件（R2.1）✓；`cli_parsers/quick_scan.py` 纯加法 `72/0`、无既有行改动 ✓。
- 离线无密钥：e2e 只跑 StockWiki CLI（临时 root），不读 `llm_apis.json`、不起 HTTP；我方 StockQA 加载器实测只读临时 JSON，未加载配置/密钥 ✓；模块 `llm_calls=0/network_calls=0` 仍属实 ✓。
- 不变量复核无回归：**I13** 去重/校验仍在任何 store 访问之前、CLI 无 SQL 参数面、`--entity` 必填、状态走 W10 `query_only` 只读；**I18** 仍只调 W09 `profiles_from_store` + W10 `project_runtime_status`，`quick_scan_query.py`/`quick_scan_delivery.py` 零改动、StockQA 零改动；**I09** `derive_scope_update` 未被本次改动触碰（`model_calls=0` 断言原样）。

## R2.7 r2 findings

### P2（阻断）
1. **P2-r2-1**：r1 P2-1 声称"卡记录失实更正…已修"，实际卡 L51 失实句原封未动（仍列 identity_state），处置记录与 progress 只写"已修"未给更正内容 —— **修复声称不实**。修法：改写 L51 为实际 4 项（canonical_name/incorporation_country/industry/segments）或加更正注。
2. **P2-r2-2**：P2-5 去重前移引入回归 —— 不可哈希输入抛裸 `TypeError` 而非 `RefreshError` 命名拒绝，违反 docstring 契约（store 访问前发生、CLI fail-closed ⇒ 非安全问题，是契约/健壮性回归）。修法一行 + 补 1 条断言。
3. **P2-r2-3**：P2-4/P2-6"模块 docstring 已披露"声称不成立（docstring 零命中）；owner 书面接受本身有效。修法：docstring 补 2-3 行（过期/事件失效缺口留 Q07；本接口非 `query.schema` 端点、同名不同形待 schema 统一）。
4. **P2-r2-4**：工件消费表述与真实入口规则冲突 —— docstring「one-entity-per-line file for `load_stock_list`」会被读成 `--batch` 用法，而 `--require-search` 与 `--batch` 互斥（`llm_runner.py` L550-553），单公司路径又必须 `--company` 而工件未携带；真实配方是逐 invocation `--require-search --entity-id <entity_id> --config <materialized questions_file> --company <label>`，`entities_file` 仅白名单记录。**可消费性结论仍成立**（R2.3 真加载器实测）⇒ 表述/字段完备性缺陷：docstring+help 需限定，建议工件补 `company/canonical_name`。附：CLI help「never touches SQL」措辞不准（owner 接口有 `profiles_from_store` 只读 SELECT）。

### LOW / INFO
- **LOW-1** `--out` 文件与 stdout **非同一 canonical 字节**（文件 `json.dumps` 默认分隔符带空格，stdout `_emit` 用 `(",",":")`）：实测 `stdout == file` → False、`json.loads` 等价 → True。"stdout 为同一 canonical JSON"仅对 stdout 成立；e2e 也未断言二者相等。
- **LOW-2** e2e 对 `quick-scan-refresh-status` 只断 exit 0，未断 payload（我实测 payload 正常）；建议补 1 条键集/`llm_calls==0` 断言。
- **LOW-3** r1 P2-2 整改遗留恒真断言 L105 `assert {"ENT_A","ENT_B","ENT_C"}.isdisjoint({"ENT_D"})`（字面量恒真，应删）；真正区分力在 L106-109。
- **LOW-4** P2-3 断言只验 `isinstance(..., bool)` 未验返回值，且仅 test1 把 `old` 传入契约函数（test2 仍未传参）。
- **LOW-5** IQS 新测试 `black --check -l100` 仍会重排 1 处（r1 INFO-1 未处理；black 非本批声明的 IQS 门）。另记录避免误读：IQS 仓 `ruff check tests/` = **117 处既有**风格错误（E702/E402/E701…），**新文件 0**，均非本批声明门。
- **LOW-6** 未迁移观测库的工作区调 `quick-scan-refresh-status` → `store_not_migrated` exit 2（W10 `_ro_connect` 既有语义；e2e 注释已按"真实工作区在观测导入后"处理）。
- **INFO** DB-07 仍无越权声称；coverage 81%、framework 0 errors/12 warnings 不变；StockQA 0 改动复核成立。

## R2.8 r2 裁决

**needs_revision** —— 4×P2（无 P0/P1）：
- 阻断理由集中在**记录可信度**（P2-r2-1 修复声称不实、P2-r2-3 披露声称不成立）与**契约一致性**（P2-r2-2 回归、P2-r2-4 消费表述），均与 r1 同类问题同源、10 行量级；
- **不阻断的部分**：P1-1 选项 (a) 已实质达成（入口/工件/W10/e2e 四件齐全，工件可消费性由我用 StockQA 真加载器独立证实）、r1 P2-2/3/5/7 修复全部到位、门全绿（929 passed / 81% / 0 errors+12 warnings / ALL CHECKS PASSED；IQS 2 passed + plan 80/53）、范围恰 3 文件且 `cli_parsers` 纯加法 72/0、StockQA 0 改动、离线无密钥、I09/I13/I18 无回归。

**放行条件（r3 可极简）**：① 卡 L51 更正（或更正注）；② 去重回归一行修 + 补 1 条不可哈希输入断言；③ 模块 docstring 补 P2-4/P2-6 两句披露；④ `entities_file` 消费表述限定（建议同时补 `company` 字段）。LOW-1~6 可选。整改后复跑 R2.2 全部命令出 r3 即可 approved。

---

# r3 终审（2026-10-05，round-62）

**终裁：approved**（r3 四条放行条件逐条实证闭环；无新增 P0/P1/P2；1 条非阻断 ADV + r2 遗留 LOW×6 按"可选"备案）。

## R3.1 放行条件逐条核（核查点 a）

| 条件 | 独立核验证据 | 结论 |
|---|---|---|
| ① 卡 L51 就地更正 | 卡 L51 现为「**【r2 更正 P2-r2-1】**`REFRESHABLE_FIELDS` 实为 **4 项**：canonical_name / incorporation_country / industry / segments（**不含 identity_state**——此前实施记录误写，本句为更正；未知字段具名拒绝 `scope_field`，实测 `identity_state` 会被拒）」；卡新增「## r2 findings 处置记录」（L60-65）逐条对应四条件，并写明「本卡 L58 旧句以本段为准」 | ✅ 失实句已就地消灭，更正内容与代码实测一致（r1 实测 `identity_state`→`scope_field`） |
| ② 去重回归 | 实现顺序：L158-167 形状校验（fields/entities 两循环）→ L170-171 `list(dict.fromkeys(...))` → L172-174 `scope_field` → L176 才 `profiles_from_store`；测试 L151-160 `pytest.raises(RefreshError)` + `exc.value.code == "input_rejected"`（抛 TypeError 该 raises 必失败）。**我独立探针**：`fields=[["industry"]]`、`fields=[{"a":1}]`、`entities=[["ENT_A"]]` → 三种全部 `RefreshError input_rejected`，**无裸 TypeError** | ✅ 闭环 |
| ③ docstring 披露 | 模块 docstring L14-18 新增「Known limits, disclosed (r2 P2-r2-3; owner accepted deferral round-60): … MISSING fields only — **stale / event-invalidated** … once **Q07** wires observation times in; and this … vocabulary is **same-name-different-shape with query.schema's** refresh preview form, pending a later schema unification」；grep `Q07\|query\.schema\|stale\|event-invalidated\|schema unification` → **4 处命中**（r2 为 0） | ✅ 两句披露真实入码 |
| ④ 消费表述 | (a) invocation 增 `"company": entity_id`（L276；我实测 3 个 invocation 的 company = ENT_A/ENT_B/ENT_C，keys = company/entities_file/entity_id/fields/questions_file）；(b) render docstring L237-241 逐 invocation 配方 `main_with_llm --require-search --entity-id <id> --company <label> --config <materialized questions_file>` + 明示「``--require-search`` REJECTS ``--batch`` … so the entities file is whitelist bookkeeping input, not a ``--batch`` roster」；(c) CLI help 改为「no SQL write surface — read-only SELECTs via W09 — and never expands to the full pool」 | ✅ 三件齐备（label 取值见 ADV-1） |

## R3.2 门独立复跑（核查点 b，命令 + 数字，当前字节）

| 门 | 命令 | r3 结果 | r2 对照 |
|---|---|---|---|
| StockWiki 全量 | `bash scripts/check_all.sh`（我自启 pwsh-191，exit 0） | ruff clean；`coverage run -m pytest -q` → **929 passed, 15 skipped in 254.78s**；coverage **TOTAL 81%**（≥73）、ui.py **75%**；validate-framework **0 errors / 12 warnings** → **`=== ALL CHECKS PASSED ===`** | 929 一致 |
| StockWiki 定向 | `pytest tests/test_quick_scan_refresh.py -q -p no:cacheprovider -o addopts=` | **4 passed in 1.48s** | 4 |
| StockWiki 格式/Lint | `black --check -l100`（3 文件）、`ruff check`（3 文件） | exit 0「3 files would be left unchanged」/ All checks passed | 0/0 |
| StockWiki 空白 | `git diff --check` | exit 0 | 0 |
| IQS 定向 | `pytest tests/test_time05_scope_update.py -q …` | **2 passed in 0.44s** | 2 |
| IQS 计划门 | `pytest tests/test_implementation_plan.py -q …` | **80 passed, 53 subtests passed in 13.99s** | 80/53 |
| IQS Lint/空白 | `ruff check tests/test_time05_scope_update.py`、`git diff --check` | 0 / 0 | 0/0 |

## R3.3 范围与纯加法性质（核查点 c）

- StockWiki `git status --porcelain` → **恰 3**（`M stockwiki/cli_parsers/quick_scan.py` + 两新文件）；`git diff --numstat` → **`73 0`**（r2 为 `72 0`，+1 行是 help 文案改写；**删除行仍为 0 ⇒ 纯加法性质未变**）。
- IQS 工作树 → 本卡（r2 处置记录，未提交）+ 本报告（r2/r3 段）+ 既有 `?? opencode.json`，无其他改动。
- StockQA（`StockQAbyLLM`）→ 与 r1/r2 **逐字相同**（仅既有 untracked 杂物），产品代码 0 改动。
- 离线：全部门与探针均在本机离线执行，未读 `llm_apis.json`、未起 HTTP、未触密钥。

## R3.4 回归复核（既有语义与不变量未被 r3 改动破坏）

- 毒 store 顺序探针（r1 同款）：SQL 形实体 → `input_rejected`（store 未触）、未知字段 → `scope_field`（store 未触）、**对照组合法入参 → `STORE ACCESSED`**（探针仍有区分力，"先拒后访问"顺序保持）。
- 真 store 复算：去重 `items=1 / estimate=1_000_000` ✓；4 池无全池（`touched=[ENT_A,ENT_B,ENT_C]`、`reused=3`、ENT_D 不出现）✓；`render_refresh_artifact(questions_by_field={})` → `questions_missing` 具名拒绝 ✓。
- I09：`derive_scope_update` 本轮零改动（`model_calls=0` 断言原样）；I13：校验/去重仍在任何 store 访问之前、CLI 无 SQL 面、`--entity` 必填、状态走 W10 `_ro_connect`（`query_only`）；I18：仍只调 W09 `profiles_from_store` + W10 `project_runtime_status`，`quick_scan_query.py`/`quick_scan_delivery.py` 零改动、StockQA 零改动。

## R3.5 r3 findings

### ADV-1（本轮唯一新发现，**非阻断**）：`company` 标签取值 = entity_id
- 事实链：StockQA 既有约定是 `--company` = **人类可读公司名**（`tests/integration/test_quick_scan_cli.py` L376-389：`--company "Fixture Corp"` 与 `--entity-id issuer:fixture` 并用）；该值被注入题面 `base_llm_provider.py` L137 `Target company name: …`、L152-154 JSON `"company_name"` 字段、L196 修复指令 `Return company_name exactly as …`，并由 `llm_response_parser.py` L333-335 **逐字校验**；强制 `web_search` 由模型按题面所述公司构造查询。
- 影响评估：取值**自洽**（题面要求模型原样返回 `ENT_A` ⇒ 校验通过，不构成运行失败），故无运行级缺陷；但把稳定 ID 当"公司名"送进检索题面，**真实补扫的检索质量可能退化**。本批纯离线、不执行 live，且 r2 条件 ④ 只要求"补 company 字段"，故不阻断。
- **建议（live 前置项）**：任何 live 补扫执行前把该值换成 `canonical_name`（W09 投影已带该字段，CLI 一行可得）；e2e 顺手补 1 行 `company` 断言。
- **LOW×6（r2 遗留，按"可选"未动）**：`--out` 与 stdout 非同一 canonical 字节、status 只断 exit 0、测试 L105 恒真断言、P2-3 只验 `isinstance(bool)`、IQS 新测试 `black -l100` 重排 1 处、未迁移观测库时 status 返回 `store_not_migrated`（证据见 R2.7）。
- INFO：DB-07 仍无越权声称；离线估价与 `llm_calls=0`/`network_calls=0` 披露仍属实。

## R3.6 终裁

**approved**
1. r3 四条放行条件**逐条实证闭环**（R3.1：卡就地更正、去重顺序+三种不可哈希探针、docstring 4 处命中、company/配方/help 三件）。
2. 当前字节四道门全绿（**929 passed / 15 skipped、coverage 81%、framework 0 errors + 12 warnings、ALL CHECKS PASSED**；IQS 2 passed + plan 80/53 + ruff/diff-check 0），且与 r2 数字一致 ⇒ r3 改动未引入回归。
3. 范围恰 3 文件、`cli_parsers/quick_scan.py` 纯加法性质未变（73/0）、StockQA 0 改动、全程离线无密钥。
4. 不变量 I09/I13/I18 复核无回归；r1 P1-1、r1 P2×5、r2 P2-r2-1~4 全部可验证地解决。
5. 余留仅 ADV-1（live 前置建议）与 LOW×6（可选），不构成关闭 W11 的阻断项。

**交接**：可执行 StockWiki 隔离提交（3 文件）+ IQS 记档提交（卡 r2 处置 + 本报告），随后关闭 W11；ADV-1 请随 live/执行批次（Q09 执行入口）一并记档。
