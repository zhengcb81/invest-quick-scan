# F2-IQS-FEEDBACK 交接 · IQS 逐题回执与混尺度投影反馈

2026-11-19。回应 [F2-IQS-FEEDBACK 施工卡](C:/Users/郑曾波/Projects/company-wiki/docs/plans/feedback-loop-2026-11-17/owner-cards/F2-IQS-FEEDBACK.md)，
在 MANIFEST-DELIVERY-01 的原 harness 工作线与分支上接续，未新建工作树。

## 1. 结论

1. **「部分完成被误报为完整」在本仓有两处可复现入口**，都先红后绿修掉：
   - `scripts/scan_result_check.py`：一份 24/38 题的真实运行被判 `ok=true`、
     `usable=true`、退出码 0；
   - 公司 result/history 读投影：只转发 owner 快照，不发布逐题覆盖，
     35 条引用配 `observed_count=36` 的声明与真正完整的响应完全一样。
2. **混尺度结构本来就在 producer 侧**（`create_company_assessment_v2` 按
   `(rubric_version, aggregation_role)` 分区），缺的是读侧把它发布出去。
   现在 `coverage.groups` 逐组保留原 rubric 与聚合角色，空组显式标出。
3. **35/36 一律 `partial` 且保留缺项**；已确认的合法空结果
   （`company_result_not_registered` 等）保留原因、不产生任何 coverage；
   **如实声明缺项的空组是合法部分结果**，只披露、不归责。
4. **观察可选、隔离**：只有设置 `RESEARCH_FEEDBACK_OUT` 才写 JSONL，
   写失败只上 stderr，业务响应、退出码、计量不变。真实入口一次读 = 1 次
   StockWiki 公开子进程、0 次模型调用、0 次注册/发布/导入。
5. 本卡不触碰 manifest 登记与正式发布；`register` 仍按原工作线被
   `observation_answer_unusable` 拒绝（STATUS.md §11），本轮未改该结论。

## 2. 接续信息

| 项 | 值 |
|---|---|
| 工作目录 | `C:/Users/郑曾波/Projects/invest-quick-scan`（即 `codex/iqs-manifest-delivery-01` 的所属工作树，未新建） |
| base | `3dde7fa6a695644e646e48007916af4bda7f10af`（= 施工卡核对的 `codex/iqs-manifest-delivery-01@3dde7fa`） |
| 实现提交 | `11d2bd9eb9dcfcf12042a1fb7bb510b783684a2a` |
| 独审修复提交 | `4685608e80d066f22eef39872d841e028de94c0e` |
| 首轮独审版本 | `11d2bd9eb9dcfcf12042a1fb7bb510b783684a2a`（ACCEPT_WITH_FIXES） |
| 修复版确认 | `4685608e80d066f22eef39872d841e028de94c0e`（ACCEPT；其后仅测试与文档） |
| 测试解释器 | `C:/Miniconda/python.exe`（3.13.9；本机唯一带 `yaml` 的解释器，StockWiki 夹具需要它） |
| 问卷 / 释放 | `pkg_0151a1e3b23fe462476b1d7329211d8887a79c161eb765a1e64c7dcda1b60d9a` / `modrel_997312ab027300898b17a8943efaf95f3531c764f2ed5d3877c4954507b010df`，catalog `3.2.1`，36 题 |
| 实体 | `ENT_99deceb6-f58a-48b1-bd6b-437621015d76`（中微） |
| 公开结果版本 | 真实 workspace 无已登记结果：`company_result_not_registered`（`delivery/read-after.json`） |
| 投影版本 | `iqs.dashboard.company_assessment/1` / `company_assessment/1.1.0`（新增 `coverage` 块） |

### 2.1 原生作业与结果引用

| 用途 | 原生标识 |
|---|---|
| 快扫检查的真实运行 | `runs/thin-bank-catl-full-2026-10-22/final`（宁德时代，as_of `2026-10-18`，`meta.when` `2026-10-22T21:36:25Z`），`pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f` / `modrel_18c097b26b82746d3b48d9f2da4858a15ce216bce39c2572d10c2dcef23d32b9`，method `core-constructs-v1/e4bfeeb96eb34888`，`bank.question_count=38`、答案 24 条 |
| 公司读的 owner workspace | `runs/r25-live/owner-workspace`（store `qsobs_c2ce64820343a7b1` / registry `qsca_9db1fe38dd82c631`） |
| 公司读的原生作业（只引用，未重跑） | 批次 `batch-f00023ec230b46c2bd2dd59e2fbfdaff`（abandoned）、`batch-13f80bdcf0bc4a5fbc4a9c1f2651cbb6`；运行 `run-49122d17c4bb4e6687dfefe88e543396`（entity scope 33 题，security 3 题另一请求） |
| 公开结果 | 无——真实读返回 `company_result_not_registered`；`register` 仍被 `observation_answer_unusable` 拒绝 |
| 注入样本的公开 result ID | `cas_83694b860296b314daed`（遗漏题）、`cas_0fd4e809aa4a51991b5d`（整尺度缺失）、`cas_f249ba4efffde1ab8dda`（如实声明空组）、`cas_79dfd1e49dbc8ff6dd2e`（建模四态）、`cas_d7549e797cad86d0484f`（完整对照） |
| 本卡的 attempt | 真实读 `read-absent-2`（前一次 `read-absent-1` 因相对 workspace 路径被 owner 拒绝，无观察产出）；注入回放各用同名 attempt |

## 3. 复现与修复

### 3.0 上游事实核对（只读，未改结论）

按施工卡先核对了 MANIFEST-DELIVERY-01 的 `STATUS.md`：最终 **36/36 全部
`result_ready`**（entity 33 题 + security 3 题），其中 **8 题 scored、28 题
insufficient_evidence**；`register` 仍被 `observation_answer_unusable` 拒绝，
读面停在 `company_result_not_registered`。最后一题 IQS_22 的处置是
security 作用层重建 permission 请求后一次通过（`rc1_7adae578`），不是数据缺陷。
本卡不改这些结论，只在其上做逐题覆盖与反馈。

### 3.1 快扫检查：24/38 被报成完整可用

真实输入：`runs/thin-bank-catl-full-2026-10-22/final/answers.json`
（本工作树留存，`runs/` 未纳入版本管理；固定输入见
`tests/fixtures/company_coverage/answers-partial-24of38.json`，只保留检查器读取的
字段，正文已丢弃）。`bank.question_count=38`、`len(answers)=24`。

修复前：

```json
{"question_count": 24, "scored": 15, "ok": true, "usable": true}   # 退出码 0
```

修复后：

```json
{"question_count": 24, "manifest_question_count": 38, "coverage": "partial",
 "missing_question_count": 14, "ok": true, "usable": false,
 "warnings": ["run covers 24 of 38 frozen questions"]}              # 退出码 1
```

`partial` 不是 `problem`（问题集仍为空），但它不再算 `usable`；没有题库计数的
旧扁平运行保持原判定，只多一条 `coverage=unknown` 警告。文档只声明"没有缺项"
而没有题库计数时也判 `unknown`——自己说自己完整不构成证据。

### 3.2 公司读投影：不发布逐题覆盖，部分与尺度缺组不可辨

真实输入：MANIFEST-DELIVERY-01 交付的 36 题 V2 请求
（`delivery/register-request-v2.json`）。六个尺度组（`lineage_group_id` 由
`source_release_sha256 + rubric_version + aggregation_role + sorted(question_ids)`
派生，夹具里逐字节一致）：

| rubric | aggregation_role | 题数 | lineage_group_id | 题号范围 |
|---|---|---|---|---|
| 1.0.0 | diagnostic_only | 12 | `lg_16340f79735b2cfa4aa3` | DUPONT_01…PORTER_05 |
| 1.0.0 | growth_core | 1 | `lg_b1cf4655124efdacea41` | IQS_19 |
| 1.0.0 | quality_core | 15 | `lg_3ea3342289d0eec675fb` | IQS_01…IQS_17 |
| 1.0.0 | valuation_core | 3 | `lg_9c86dc2d3c5da6700034` | IQS_22…IQS_24 |
| 2.0.0 | growth_core | 2 | `lg_d330c4c79002442cfdc3` | IQS_20…IQS_21 |
| 2.0.0 | quality_core | 3 | `lg_357ef0ff66021b9271c8` | IQS_05…IQS_18 |

真实 workspace 没有已登记结果，所以按施工卡用**临时公开响应**注入偏差：

| 注入 | 结果 |
|---|---|
| 去掉 `PORTER_05` 的引用，仍声明 36/36 | `coverage-claim: complete-claimed`（deviation，`owner=stockwiki`） |
| 整个 `2.0.0` 尺度（5 题、2 组）连同引用消失，`scale_versions` 仍列 2.0.0 | `scale-lineage: scale-without-group`（deviation，`owner=stockwiki`），派生 `verdict=partial` |
| 整组 `2.0.0/quality_core`（3 题）无观察，但如实声明缺项 | 五项全 `expected`——合法部分结果 |
| 36/36 混尺度完整（合法对照） | 五项全 `expected` |

修复前 `GET company/result` 只校验 `result_id`/`entity_id`/`aggregate_score`，
`completeness` 与 `observation_refs` 从不互校；`GET company/history` 只有
`manifest_question_count`/`observed_count` 两个数字。

### 3.3 逐题四态

`coverage.questions[]` 逐题给 `status`，并保留 `answer_state`：

| status | 含义 | 证据来源 |
|---|---|---|
| `completed` | 已绑定不可变观察 | `observation_refs` |
| `settled_unsaved` | 已结算但没保存 | 回执摘要（`completed` 无观察也归此） |
| `provider_filtered` | 供应商内容过滤 | 回执摘要（`content_filter`） |
| `provider_truncated` | 输出被截断 | 回执摘要（`length`） |
| `not_run` | 未派发 | 回执摘要 |
| `unknown` | 现有证据判不了 | 默认 |

真实读入口拿不到 StockQA 的回执，因此未观察题一律 `unknown`，不猜；
回执只由离线回放（`--receipts`）或测试提供，对不上题号/词表一律
`ValueError` 而不是静默丢弃。回执与观察冲突时两个方向都记
`receipt_conflicts`。

## 4. 写入范围与接口

| 文件 | 变更 |
|---|---|
| `scripts/iqs_scan/workbench/company_result_coverage.py` | 新增：逐题覆盖与分组尺度派生（纯函数，无 I/O） |
| `scripts/iqs_scan/workbench/dashboard_company_feedback.py` | 新增：`feedback-observation/1` 投影与可选 JSONL 写出 |
| `scripts/iqs_scan/workbench/dashboard_company_projection.py` | result/history 响应新增 `coverage`；公开读出口接线观察；版本 1.1.0 |
| `scripts/iqs_scan/tools/scan_result_check.py` | 覆盖判定（`coverage`/`manifest_question_count`/`missing_question_count`），`usable` 收紧 |
| `scripts/iqs_scan/tools/company_result_feedback.py` | 新增：一次公开读或临时公开响应的回放 CLI |
| `scripts/{company_result_coverage,dashboard_company_feedback,company_result_feedback}.py` | 新增：本仓兼容入口（`scripts/dashboard_company_projection.py` 原入口保留未动） |
| `tests/test_company_result_coverage.py` | 新增 37 例 |
| `tests/test_scan_result_check.py` | +6 例 |
| `tests/test_dashboard_company_result.py` | 夹具自洽化：3 条声明对应 3 条引用（原先 3 声明配 1 引用，本身就是被本卡判定为矛盾的那种形状） |
| `tests/test_dashboard_entity_iqs_link.py` | 固定信封跟随投影版本 1.1.0 |
| `tests/fixtures/company_coverage/**` | 固定输入 + 生成脚本（含一份显式命名的建模夹具） |
| `tests/suites.json` | 登记新文件，并补登记此前遗漏的 `test_company_assessment_v2_projection.py`（`test_test_suites.py` 在 base 上即因此红） |
| `.gitattributes` | 夹具 JSON `-text`，防止行尾改写生成字节（保留文本差异可读） |
| `skills/repair-iqs-issue/SKILL.md` | 新增：本仓问题处置技能 |
| `docs/implementation/issues/F2-IQS-000{1,2}*.md` | 两张 `verified` 问题卡 |

公开响应形状：`company_result` 逐字节仍是 owner 的声明（未改写、未补算、
`aggregate_score` 仍为 `null`）；新增的 `coverage` 是兄弟键。版本升到
`company_assessment/1.1.0` 表示新增块；owner 侧读取的字段集合与语义未变，
Dashboard 适配器按字段防御式读取，不校验键集。

## 5. 测试

```powershell
C:/Miniconda/python.exe -B -m pytest -q tests/test_company_assessment_v2_projection.py tests/test_dashboard_company_result.py tests/test_scan_result_check.py tests/test_company_result_coverage.py
```

| 命令 | 结果 |
|---|---|
| 上列四文件（含施工卡指定的三份） | **126 passed / 0 failed / 0 skipped**，83.48s |
| 其中施工卡指定三份 | **89 passed / 0 failed / 0 skipped**，67.60s（base 83 passed / 67.08s） |
| `tests/test_dashboard_module_boundaries.py tests/test_dashboard_entity_iqs_link.py tests/test_test_suites.py` | 45 passed |
| `tests/test_dashboard_http.py` | 33 passed |
| `tests/test_dashboard_owner.py` | 39 passed / **2 failed（base 即有）**：`membership_request_required: use apply_membership_request for schema 7+`，SW-2 名单守卫的既有红，与本卡无关 |
| `tests/test_dashboard_iqs_public_integration.py` | 2 passed / **1 failed（base 即有）**：浏览器用例在 `npm run build`（esbuild）阶段失败，环境问题，与本卡无关 |

RED 记录：新增投影用例在实现前于收集期失败
（`ModuleNotFoundError: No module named 'company_result_coverage'`）；
同一批 `tests/test_scan_result_check.py` 5 failed（`KeyError: 'coverage'`）。

## 6. 观察

六份脱敏 JSONL 在
[`evidence/f2-iqs-feedback/`](evidence/f2-iqs-feedback/README.md)：

| 文件 | 行数 | SHA-256 |
|---|---|---|
| `real-read-absent.jsonl`（真实入口） | 6 | `97a72e1925dd94e75ff621e9ff5fc9e15a3d2236dca26d0209bcba34ba8e7b1c` |
| `injected-partial-claiming-complete.jsonl` | 6 | `e63af27fb663de206cd77118f543a1df6a35a073f489e796c8aefd0cf87abd4e` |
| `injected-scale-dropped.jsonl` | 6 | `6130a9e58d158b71f0ed33b00aff62527044947aa812e81a6a74886c47ae0a9e` |
| `injected-group-declared-empty.jsonl` | 6 | `8c9246cc97d2cd619d0f25284916a99a56ff265e63ec258eedc7bd641f51c28f` |
| `injected-modelled-run-states.jsonl` | 6 | `77bbdac2af2b4e7676e8917d9b8891a966049d6d3845f1a8f9e710645eae51b1` |
| `injected-complete-mixed.jsonl`（合法对照） | 6 | `990e8c6469567737a65b309ffdd8f0bbf62b4364aad153df59669e5783a288fd` |

每行必填 `schema_version, owner, run_id, attempt_id, step_id, check_id,
expected, actual`；`step_id` 为 `company-{result|history}/<entity>`，
`evidence_ref` 为 `iqs:company/<entity>/<result_id|reason|page>`，
`version` 取投影版本，`disposition ∈ {expected, deviation, unknown}`。

结果读的六项检查：`coverage-claim`（owner 声明 vs 引用）、
`scale-lineage`（声明的尺度是否有组承载、引用是否落在组内）、
`question-status`（逐题状态是否发布）、`missing-questions`（声明的缺项是否保留）、
`release-binding`（引用是否都指向冻结释放内题号）、`owner-absence`（无结果是否带名原因）。
历史页一项：`history-coverage`（每项是否带判定）。

真实调用计数：真实读 **2 次**（第 1 次因相对 workspace 路径被 owner 拒绝、无观察；
第 2 次成功并归档）——每次 1 个 StockWiki 公开命令子进程、模型调用 0、
注册/发布/导入 0、写入 owner workspace 0 字节；注入回放 **5 次**（归档的 5 份
样本，不读不写 owner，0 子进程）。同一 result 重复读取只追加观察，不新增
供应商发送或费用，见 `test_reading_the_same_result_twice_only_adds_observations`。

## 7. 独审与关闭记录

未参与实现的独立 agent 对照施工卡做了一次大节点审查（任务覆盖、真实入口、
在途边界、正常与反例、观测可选性、恢复副作用、隔离清理）。**首轮结论
ACCEPT_WITH_FIXES（受审 `11d2bd9`）**：三个 P1、五个 P2、五个 P3 全部复现并
修复，修复提交 `4685608`。**修复版复核结论 ACCEPT（受审 `4685608`）**，两次
独立测试运行均为 **124 passed / 0 failed / 0 skipped**（当时的用例数；复核后只新增测试，现为 126），并离树复核
`build_fixtures.py` 能逐字节重建全部夹具。

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| 1 | P1 | 回执写 `completed` 但该题没有观察时被发布成 `completed` | 归 `settled_unsaved` 并记 `receipt_conflicts`；新增用例 |
| 2 | P1 | 公开响应在投影时不带回执，离线回放既发布 `unknown` 又误报 `statuses-missing` | `project_result` 接收 `question_receipts`，读入口把同一份回执传给发布路径；新增 2 例 |
| 3 | P1 | 整组从 `lineage_groups` 消失而 `scale_versions` 仍列该尺度时无任何信号 | 派生 `missing_scale_versions` 并强制 `verdict=partial`，`scale-lineage` 报 `scale-without-group`；新增 2 例 |
| 4 | P2 | 历史页读会产出 `owner-absence=reason-missing` 假偏差 | 历史页只发 `history-coverage`；新增 2 例 |
| 5 | P2 | 释放外题号的引用被计入覆盖且不报告 | `unexpected_question_ids` 单列、不计入 `observed_count`，`release-binding` 报偏差；新增 2 例 |
| 6 | P2 | 如实声明缺项的空组被当成 IQS 偏差 | 空组只披露不归责；用例改为断言全 `expected` |
| 7 | P2 | 回执夹具无法产生过滤/截断状态 | 新增显式命名的建模夹具对，`provider_terminal` 改名 `provider_terminal_history` |
| 8 | P2 | `scan_result_check` 可凭"自我声明无缺项"判完整 | 无题库计数时判 `unknown`，有缺项无总数判 `partial` |
| 9 | P3 | `scale_versions` 未与组对账 | 并入 `missing_scale_versions`/`undeclared_scale_versions` |
| 10 | P3 | `PROJECTION_VERSION` 未随新增块变化；空结果 `coverage=null` 无说明 | 升 `1.1.0`，固定信封跟随，空结果语义写入文档 |
| 11 | P3 | 观察写失败信息带输出路径 | 只报 `strerror` |
| 12 | P3 | `.gitattributes` 把生成脚本标成二进制 | 收窄到 `*.json` |

审查同时确认的边界：`company_result` 与 owner 返回逐字节一致；未设
`RESEARCH_FEEDBACK_OUT` 时响应与退出码不变；`--inject-result` 不读不写 owner；
新增键不改变 Dashboard 消费。

复核后只剩四个 P3，均不阻塞，已处理或记录：

| # | P3 | 处置 |
|---|---|---|
| 13 | `result-scale-dropped.json` 无消费方（两个尺度缺失用例原先内联构造） | 两个用例改为直接读该夹具 |
| 14 | `undeclared_scale_versions` / `unexpected_question_ids` 会报 owner 偏差但不改变 `verdict` | 属预期：`verdict` 只描述**覆盖**是否完整，不描述与 owner 声明是否完全一致；后者由 `scale-lineage`/`release-binding` 单独报告。此处明示，避免把 `complete` 读成"完全一致" |
| 15 | `scan_result_check` 的"有缺项无总数判 partial"分支无用例 | 补 `test_declared_gaps_without_a_bank_total_are_partial` |
| 16 | `.gitattributes` 是否落到文档提交 | 已提交（`8793775`），并用 `-text` 保留夹具可读差异 |

以上 13–16 只改测试与文档：复核后 `scripts/` 与 `4685608` 逐字节相同
（`git diff 4685608 HEAD -- scripts/` 为空），因此"受审实现版本"仍是 `4685608`。

## 8. 清理与余项

- 本轮自建临时目录 `C:/Users/郑曾波/AppData/Local/Temp/iqs-f2/`：JUnit 报告、
  日志和样本草稿（37 个文件）已删除；其中一次中止运行的 pytest `--basetemp`
  子树 `bt/`（28 MB、767 个文件）保留——沙箱的批量删除守卫要求显式确认，
  未绕过，交 ROOT 或系统临时目录清理。样本正本在 `evidence/f2-iqs-feedback/`。
  pytest 自身的 `pytest-of-郑曾波/` 临时根由 pytest 管理，未手工删除。
- 未改动：`runs/`（含 `runs/r25-live/owner-workspace` 全部字节）、StockWiki、
  StockQA、Dashboard、company-wiki。本轮**未推送远端**：`origin` 上只有
  `master` 与三个 codex 分支，没有 `codex/iqs-manifest-delivery-01`，与
  MANIFEST-DELIVERY-01 原线一致（本分支领先 `origin/master` 22 个提交，全部
  本地）。推送属外部动作，留给 ROOT 按其发布安排决定。
- 余项（交 ROOT 按公开观察验收）：
  1. **真实已登记结果下的复验**：本轮真实 workspace 仍是
     `company_result_not_registered`，`coverage` 在真实完整/部分快照上的表现
     只有临时公开响应证据。等原交付方把 36 题转为可用答案并 `register` 成功后，
     按同一入口再跑一次 `scripts/company_result_feedback.py`。
  2. **Dashboard 消费入口复验**：`fd8b3db` 的 `_assessment_scale_fields` 只读
     `assessment_protocol`/`scale_version(s)`，不读新增的 `coverage`；ROOT 用该
     公开版本经 Dashboard 读同一 result 时应确认展示不变、部分结果仍由
     `missing_count` 表达。
  3. **回执侧四态的真实样本**：`settled_unsaved`/`provider_filtered`/
     `provider_truncated` 目前由建模回执夹具证明，没有一次真实运行同时产出
     四种状态；接续时若原 scan 作业能给出逐题终态，可直接喂 `--receipts` 复验。
  4. **已知边界**：
     - 某组连同题目一起消失、而同 rubric 的另一个组仍在时，公开快照无法与
       "更小的释放"区分（`scale_versions` 是 rubric 级）。需要消费方用
       `source_release_sha256` 对冻结释放复核；本卡不声称能单独判定。
     - V1 快照（无 `lineage_groups`）没有题目清单，投影只能报"数量缺口"
       （`manifest_question_count` vs `observed_count`，`claim_matches_refs=false`），
       `missing_question_ids` 只能是 owner 自己声明的那份；要逐题点名必须等
       owner 发布 V2 的 lineage groups。

## 9. 机器摘要

```json
{"lane":"F2-IQS-FEEDBACK","owner":"invest-quick-scan","worktree":"C:/Users/郑曾波/Projects/invest-quick-scan","base":"3dde7fa6a695644e646e48007916af4bda7f10af","implementation":"11d2bd9eb9dcfcf12042a1fb7bb510b783684a2a","reviewed_commit":"4685608e80d066f22eef39872d841e028de94c0e","tests":[{"command":"C:/Miniconda/python.exe -B -m pytest -q tests/test_company_assessment_v2_projection.py tests/test_dashboard_company_result.py tests/test_scan_result_check.py tests/test_company_result_coverage.py","result":"126 passed, 0 failed, 0 skipped (83.48s)"},{"command":"C:/Miniconda/python.exe -B -m pytest -q tests/test_company_assessment_v2_projection.py tests/test_dashboard_company_result.py tests/test_scan_result_check.py","result":"89 passed, 0 failed, 0 skipped (67.60s)"},{"command":"C:/Miniconda/python.exe -B -m pytest -q tests/test_dashboard_module_boundaries.py tests/test_dashboard_entity_iqs_link.py tests/test_test_suites.py","result":"45 passed"},{"command":"C:/Miniconda/python.exe -B -m pytest -q tests/test_dashboard_owner.py","result":"39 passed, 2 failed (pre-existing membership schema-7 guard)"}],"sample_refs":["docs/implementation/parallel-lanes/packages/2026-11-11-modularity-closeout/evidence/f2-iqs-feedback/real-read-absent.jsonl","docs/implementation/parallel-lanes/packages/2026-11-11-modularity-closeout/evidence/f2-iqs-feedback/injected-partial-claiming-complete.jsonl","docs/implementation/parallel-lanes/packages/2026-11-11-modularity-closeout/evidence/f2-iqs-feedback/injected-scale-dropped.jsonl","docs/implementation/parallel-lanes/packages/2026-11-11-modularity-closeout/evidence/f2-iqs-feedback/injected-group-declared-empty.jsonl","docs/implementation/parallel-lanes/packages/2026-11-11-modularity-closeout/evidence/f2-iqs-feedback/injected-modelled-run-states.jsonl","docs/implementation/parallel-lanes/packages/2026-11-11-modularity-closeout/evidence/f2-iqs-feedback/injected-complete-mixed.jsonl"],"review_ref":"本文件 §7（首轮 ACCEPT_WITH_FIXES @11d2bd9，修复版 ACCEPT @4685608）","cleanup":"临时目录的报告/样本草稿已删；pytest basetemp 子树（28MB）受批量删除守卫保留；runs/、StockWiki、StockQA、Dashboard 未改","remaining":["真实已登记结果下的复验","Dashboard 消费入口复验","回执四态的真实样本","同 rubric 下单个组消失不可判定的边界"]}
```

### ROOT 兼容版本复验

同一公开协议的一致发布家族与主版本共用一次解析。旧历史信封及同主版本的 SW 增量回复可用，公司结果、空页、业务拒绝、主体和零 IO 按实际内容核对。定向 104 项通过。独审用历史 Git 生产器验证旧结果和历史，真实 SW 正式登记经 IQS 和 Dashboard HTTP 读回原结果与历史。
