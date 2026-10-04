# L02 校准报告独立审查（r1 → r2）— 2026-10-05

- **最终裁决（r2，2026-10-05）：approved**——r1 全部 findings（F1–F8、F9–F12 INFO）已核实处置完毕，依据见文末"## 5. r2 复核（2026-10-05）"。
- 被审对象：`docs/implementation/reviews/L02/L02-calibration-report-2026-10-05.md`（r1 修订版）
- 审查者：独立审查代理（与实现者无关；全部数字由本审查者自有代码从磁盘产出复算，未采信报告或 summarize.py 的任何数字；summarize.py 仅作为交叉验证运行过一次）
- 数据根：`C:\Users\郑曾波\Projects\StockQAbyLLM\pilot_runs\l02_2026-10-04\`（只读）
- r1 结论（已被 r2 关闭）：needs_revision。核心校准数字（分母、statuses、搜索执行率、来源数、预算总账）全部独立复核为真，无择优删样本证据；但报告 §2.1 有三个汇总格数字口径错误/无法按其声称的方式复现，且 amendment-4 冻结的探针门（≥25 search executed）实际未达标、被事后放宽而报告未披露。均为文档/治理层修正，不需要重跑任何数据。

---

## 1. 范围

审查覆盖任务书 6 项必做核查：独立复算、LIVE-04 分母完整性、G2 case 映射充分性、000738 账本缺口、费用发现转述、过度声称扫描。参照材料：L02 冻结基线（含 amendment-3/4）、run-log.json 及两份备份、rejected_error/rejected_probe 隔离区与 repair-manifest、11 份 out/primary 产出、companies.json / companies_60_full_signed.json / repeat_subset*.json、runner.py / summarize.py、acceptance-cases.json 中 LIVE-03/04、REV-01/02/03/06、UNI-05、SC-07、task_plan.md Phase 41/74/75、invest-quick-scan 的 findings.md 与 progress.md、运行目录 logs/stock_qa_20261004.log。

## 2. 逐项核查证据

### 2.1 独立复算（核查项 1）— 6 份 MiMo 产出逐格比对

用本审查者自有 Python 脚本（临时目录，未运行 summarize.py 计数）直接解析 `out/primary/` 的 6 份 MiMo 文件（provider=mimo / requested_model=mimo-v2.6-flash / entity_id=probe:<listing_key> 六份全部核验一致）：

| 公司 | 题 | scored | insuff. | unknown | error | 搜索执行 | attempts | 修复 | response_id 非空 | 来源 URLs | 内建搜索调用 | Attempt 级均延迟 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 天马 002122 | 29 | 11 | 17 | 1 | 0 | 24 | 35 | 6 | 29 | 138 | 30 | 50.2s |
| 通富 002156 | 29 | 20 | 4 | 5 | 0 | 24 | 40 | 11 | 29 | 166 | 35 | 53.7s |
| 中颖 300327 | 33 | 20 | 13 | 0 | 0 | 31 | 40 | 7 | 33 | 191 | 38 | 49.8s |
| 航发 000738 | 29 | 17 | 10 | 2 | 0 | 24 | 41 | 12 | 29 | 189 | 36 | 27.0s |
| 万科 02202 | 33 | 27 | 5 | 1 | 0 | 30 | 45 | 12 | 33 | 226 | 42 | 53.6s |
| GENB | 29 | 16 | 11 | 2 | 0 | 28 | 38 | 9 | 29 | 186 | 37 | 46.9s |
| **合计** | **182** | **111 (61.0%)** | **60 (33.0%)** | **11 (6.0%)** | **0** | **161 (88.5%)** | **239** | **57** | **182** | **1,096** | **218** | 6 家 ≈46.9s / 5 家 ≈51.0s |

与报告比对结果：
- **§2.1 逐格相符**：scored 111 (61.0%)、insufficient 60 (33.0%)、unknown 11 (6.0%)、error 0、搜索执行 161/182 (88.5%)、来源 1,096 条、max 时延 178.9s（300327）——全部与独立复算一致。
- **§2.2 逐公司表格全部相符**：每行 题/scored/insuff./unknown/搜索执行/修复/均延迟 与复算一致（搜索执行率 83%/83%/94%/83%/91%/97% 全对；均延迟为 attempt 级均值，50.2/53.7/49.8/53.6/46.9 全对）。000738 行修复/均延迟填"—"（实际 12 次 / 27.0s），属未回填而非错误。
- **§2.1 两格不符（→F1）**：
  - "格式修复命中 **45+** 次"：6 家实际 **57** 次；45 恰等于 5 家子集（6+11+7+12+9，不含 000738 的 12）。
  - "attempts **362+**"：6 家实际 **239**（含探针 36 也只有 275）。362 精确等于备份 run-log 时刻 out/primary 10 份文件（5 份 MiniMax 旧产出 164 + 5 家 MiMo 198）的 attempts 和——跨时代（MiniMax+MiMo）口径混入 "6 家 182 题" 表头下。
  - "每题时延 avg ≈51s"：为 5 家口径（50.97s）；含 000738（27.0s）后 6 家为 46.9s。
- **探针参照（§1/§2.4）全部相符**：`rejected_probe_2026-10-05/CN_A_002122_mimo.json` 复算 = 29 题、scored 12、insufficient 16、unknown 1、error 0、搜索执行 21/29、36 attempts 全 HTTP 200、attempt 级均延迟 70.6s、max 134.8s——与报告一字不差。
- **run-log 与产出文件零漂移**：11 条 runs 的 statuses/question_attempts/output 与对应 JSON 逐项一致（含 000681 那条"record corrected from output file"手工修正后的记录）；000738 前两次失败不在产出中（见 §2.4）。
- **预算总账复核为真**：out/primary（11 份）attempts 403 + rejected 两个隔离区 537 = **940**，与 run-log `budget.primary_requests=940` 精确相等；备份前 899 = 940 − 41（000738 第三跑），账本自洽。每 receipt attempts ≤ 2，证实"修复预算=1/题"未被突破。

### 2.2 LIVE-04 分母完整性（核查项 2）

- **失败/unknown 全保留在分母**：182 题每题都有终态 status；71 个非 scored（60 insufficient + 11 unknown）全部计入分母与 §2.1/§2.2 表格；11 个 unknown 全部有真实 response_id（11/11），无伪分（21 个非 executed 搜索题中 0 个 scored）；15 个从未触发搜索（web_search_calls=0）的题 15/15 为 insufficient_evidence——"未触发搜索一律 fail-closed 为 insufficient_evidence、无伪分"的声称**在其 stated 口径上成立**（另有 6 题为"搜索已调用但回执不可核验"→unknown，报告未单独说明，见 F9/INFO）。
- **样本缩减先于批启动冻结**：amendment-4 `at=2026-10-04T21:26:31Z`；run-log（runner.py:206 用 `time.gmtime()` 写真 UTC）批窗口 `started_at=2026-10-04T21:31:46Z`（见 `run-log.backup-before-000738-repair.json` last_window，workers=6、questions_planned=153）。**amendment-4 比派发早 5 分 15 秒**；6 家样本文件 companies.json 写于 21:22:23Z（派发前 9 分钟）。样本 6 家全部在冻结 60 家内、与 MiniMax 已完成的 5 家零重叠（与 amendment-4 "避免模型混用"理由一致）、6 家中 3 家属 repeat-20 子集——**未发现事后择优迹象**。
- **原 60 家名单完整归档**：`companies_60_full_signed.json` 60 个 listing_key 与冻结基线 entities **逐一相同**，name/market/probe_entity_id 零值差；`repeat_subset_20_signed.json` 与冻结 repeat_subset.listing_keys 完全一致。注意归档文件是 runner 工作文件投影（分类 5 字段被 profile_key 替代，见 F12/INFO），成员资格可证明、分类属性以冻结 JSON 为准。运行用 `repeat_subset.json` 已被清空为 `[]`（签名单独保留，与"repeat 顺延（recorded, not silently dropped）"相符）。
- **时序证据的时钟问题（→F3）**：报告写"运行 2026-10-04 22:27–23:12Z"。经核，本机时区为 BST（UTC+1）：文件 mtime、输出文件内 `observed_at`、logs/*.log 均为**本地钟**（如 000738 第三跑日志 23:16:07/23:34:36），而 run-log/repair-manifest/amendment 时间戳为**真 UTC**（000738 窗口 started_at=22:16:06Z = 本地 23:16:06，分毫不差）。因此报告的 "22:27–23:12Z" 是**本地钟读数误标 Z**，真 UTC 批窗口为 21:31:46–22:11:58Z（≈40.2 分钟子进程墙钟）。所有先后顺序结论（amendment-3 20:45:15Z → 探针 ~20:48–21:29:57Z → amendment-4 21:26:31Z → 派发 21:31:46Z）在真 UTC 下全部成立，但报告引用的绝对时刻须更正标注。

### 2.3 G2 case 映射充分性（核查项 3）

对报告 §4 逐 case 核验：
- **LIVE-04**：分母可核验 ✓（§2.2 表 + 本审查独立复算一致）；缩减为批前冻结 ✓（§2.2 证据）。**但** §4 未披露 amendment-4 探针门未达标被放宽一事（→F2）。
- **LIVE-03**：单模型（6 份产出 provider/model 字段全为 mimo/mimo-v2.6-flash）按市场/生命周期分层呈现 ✓；repeat 顺延如实声明 ✓；"不择优删样本"成立 ✓。
- **REV-01/02/03**：产出与 run-log 逐公司对应 ✓（零漂移）；本审查独立复算证明汇总非脚本自证 ✓。但 §5 声称的 `python -X utf8 summarize.py` **今天运行聚合的是 11 家 333 题**（summarize.py 对 out/primary 无 provider 过滤，5 份 MiniMax 旧产出仍在 out/primary），原样执行**不能**重现报告中 6 家数字（→F4）；runner 重跑会因 done-set 全部跳过（runner.py:203）。
- **UNI-05 / SC-07**：引用既有 verified 证据、本批不重测——诚实限定 ✓；本批 unknown 不删分母与 SC-07"未知不删分母"口径一致 ✓（本批 not_applicable=0，未涉及 N/A 审核分支）。
- **REV-06**：分母可核验 ✓；cohort 已分层但每格 n=1（表述基本克制，建议显式标注 n=1）；恢复观察以 300327 RECOVERY 题（3 scored/1 insufficient，本审查复核一致）+ 既有 recovery-watch-1 证据支撑，偏薄但无过度声称；"低分不删池/零池写入"由 `probe:<listing_key>` 实体策略支撑——6 份产出 + 探针的 entity_id 全部核验为 `probe:*`，冻结 `zero_pool_writes: true` ✓；费用/失败留痕**部分**可核验（总账 940 精确 ✓，但 MiMo/MiniMax 时代拆分未列示、000738 缺口见 §2.4）；case 中的"用户排除"维度报告完全未提及（→F10）。原文"60 家公司校准回执"按 amendment-4 缩减并明示"G2 按修正后范围裁决"——**无把 6 家说成 60 家的过度声称** ✓。

### 2.4 000738 账本缺口（核查项 4）— 裁决：诚实披露成立，但叙述有一处证据缺口

磁盘证据链：
- **失败 #1（MiniMax 窗口1）有据**：`run-log.backup-before-repair.json`（隔离前备份）含 000738 记录 `output_exists:false, exit:1, seconds:730.6, stderr:""`；logs 行 706 显示其子进程 19:46:42 本地启动后再无任何日志（下一个公司 000783 于 ~19:58:51 接续，与 730.6s 精确衔接）。
- **"MiMo 批前检查"失败 #2 无磁盘痕迹**：两份备份中只有上述一条 000738 失败记录；MiMo 批窗口 questions_planned=153（5 家）——000738 因 stale done 条目被 runner **跳过**（runner.py:203 done-set 不检查 output_exists），并未在 MiMo 批内重试失败；logs 在 21:15–23:16 本地区间无任何 000738 子进程日志。"横跨两个 provider 同样静默"中的第二次失败在运行目录内**不可核验**（→F5）。
- **移除空 done 条目有据**：`run-log.backup-before-000738-repair.json`（mtime 23:11:59 本地，批结束同分钟）保留被删记录；现行 run-log 000738 为第三跑成功记录（exit 1 但有完整产出，29 答 17/10/2/0、搜索 24/29——本审查复核一致；exit 1 是"含非 scored 答案按 Q01–Q03 契约返回非零"的已知语义，非失败）。
- **≈29 请求缺口为真且已披露**：两次失败均无产出文件 → attempts 无处落盘 → 不在 940 总账内（账本按 out/** + rejected_* 的 receipt attempts 计数，runner.py:55-86）。披露链完整：报告 §2.3 + findings.md:1488 + progress.md（"其历史 attempts ≈29 请求未落盘，预算账本缺口已如实记录"）三处一致 ✓。但 ≈29 只够覆盖一次单跑（29 题 × 1 attempt）；若"两次"都真实派发过，上界 ≈58（→F6 量化歧义）。
- **裁决**：**可接受的诚实披露**，不构成 LIVE-04 放行阻断——失败被保留叙述、缺口主动披露、预算账本其余部分精确自洽；但 LIVE-04"保留失败在账本"的理想要求下，这是账本完整性上一个**已声明的洞**，且"第二次失败"一说不应用与第一次同等的确定性书写（→F5/F6）。runner 对无产出失败仍标记 done、resume 即跳过的设计缺陷应修（否则任何静默失败都会被后续窗口跳过）。

### 2.5 费用发现转述（核查项 5）

- findings.md:1487、progress.md、报告 §2.5 三处转述一致：owner 账单观察"搜索插件费 > 模型费"、指令"B01 全面评比必须把搜索费用与模型费用分开列示并综合进 Pareto"。与 BENCH-01 原文核对：acceptance-cases.json BENCH-01.A07 确实要求"Actual cash charges, search credits, token/cache usage, charged failures … reported separately"——"B01 step 6 原文已要求"的转述**准确，无夸大** ✓。设计含义段（Brave/Tavily 解耦可能更省）措辞为"可能"，未下结论 ✓。
- 数字佐证有两处小口径问题：§2.5 "本批 182 题 + 修复共触发 ≈246 次内建搜索"——实测 6 家产出 `web_search_calls` 合计 **218**（1.20 次/题），246 = 218 + 探针 28，把探针计入"本批 182 题"（→F7）；§0 "~200 次请求（MiMo 计费）"——MiMo 计费 attempts 实际 ≈275（探针 36 + 6 家 239），~200 = 5 家 153+45 的子集口径（→F7）。两处都偏低/混口径，但方向是保守的且明示"账单以 owner 控制台为准"。

### 2.6 过度声称扫描（核查项 6）

- **6 家 vs 60 家**：全文一致使用 6 家/182 题；§4 明示"60 家校准回执"按 amendment-4 缩减。未发现越界。唯一注意点：§2.2 观察"HK 大盘成熟公司 scored 率最高（82%）/CN 小盘成熟工业最低（38%）"是每格 n=1 的描述，建议显式标注每格 n=1（→F11/INFO）。
- **单模型 vs 跨模型**：§0/§3 明确"不声称跨模型可比性（仅 MiMo 区组）"，与产出字段核验一致 ✓。
- **逐题基线 vs 方法对照**：§0 方法论边界与 amendment-4 methodology_alignment、Phase 41（B01 设计：顺序逐题/并发逐题/分组/单批四臂、Q09/Q10/PAR-04 前置）交叉核对一致；"本批仅 B01 臂①、workers≤6 只改墙钟不改提问方法"成立 ✓；§3 明确"不声称打包策略优劣、池决策效力" ✓。
- 未发现把探针/单跑数据伪装成批统计、未发现删除负例或改冻结预期（REV-03 关注点）。

## 3. Findings 列表

阻断级（P0/P1/P2）：

- **F1 (P2) §2.1 汇总格口径错误/不可复现**："格式修复命中 45+"（实际 6 家 57；45 为 5 家子集）、"attempts 362+"（实际 6 家 239；362 = 含 5 份 MiniMax 旧产出的 10 文件之和）、"每题时延 avg ≈51s"（5 家口径，6 家 46.9s）——三者与"6 家 182 题终态"表头不符，与"数字全部来自磁盘产出文件、命令可复现"的状态声明矛盾。修复预算命中率是 LIVE-03 明确判定项（Phase 74），须改为 239/57/46.9s（或明确标注 5 家口径并单列 000738）。证据：本审查 §2.1 复算表；`run-log.backup-before-000738-repair.json` budget=899 = 940−41。
- **F2 (P2) amendment-4 冻结探针门未达标且事后放宽未入修正案、报告未披露**：amendment-4 resumption_gate 要求"probe … >=25 search executed"；实测探针 21/29 executed（29 response_id ✓、0 error ✓）。progress.md 记载"amendment-4 门从'≥25 executed'修订为 LIVE-02'非零搜索'语义"，但冻结 JSON amendments 无此修订记录，报告 §1/§4 亦未披露。链路健康实质满足（21>0、36 attempts 全 200），但按项目自身治理（REV-02：不让自报通过放行；范围/门变更须修正案），须补 amendment 记录或在报告 §4 明示后方可进 G2。

非阻断（LOW/INFO）：

- **F3 (LOW) 时钟标注混用**：报告/产出 `observed_at`/logs 为本地钟（BST=UTC+1），run-log/amendment/repair-manifest 为真 UTC；报告"22:27–23:12Z"实为本地钟误标 Z，真 UTC 批窗口 21:31:46–22:11:58Z（≈40.2 min 子进程墙钟；000738 窗口 22:16:06–22:34:36Z）。所有顺序结论不受影响，但 G2 材料应统一为真 UTC 并注明本地钟偏移 +1h。另：派发→000738 收尾全程 ≈62.8 min，严格口径超 amendment-4"≤1h"约 3 分钟（主批 40–45 min 达标；报告 §2.1 已分列两段墙钟但未给出总和）。
- **F4 (LOW) 复现命令不保真（REV-01/02/03）**：summarize.py 无 provider 过滤，今日运行聚合 11 家 333 题（含 MiniMax 旧产出，provider 字段已核为 minimax/MiniMax-M3），原样执行不能重现报告 6 家数字；runner 重跑因 done-set 全跳过。应给 provider=mimo 过滤步骤或把 5 份 MiniMax 旧产出移出 out/primary（归档保留）。§4"命令入档（§4）"应为 §5（笔误）。
- **F5 (LOW) "第二次静默失败（MiMo 批前检查）"无运行目录证据**：两份备份、logs、out/ 中均无该次尝试的任何痕迹；MiMo 批实际因 stale done 条目跳过 000738（planned=153）。应引用会话级证据或改写为"窗口1 静默失败后 done 条目残留导致批内跳过"。runner 对无产出失败标记 done、resume 跳过的设计缺陷应修复。
- **F6 (LOW) 账本缺口量化歧义**：≈29 请求只对应一次单跑口径；若两次失败均实际派发则上界 ≈58（MiniMax 窗口1 那次 730.6s 按其 ~9s/题节奏大概率发出了请求）。建议在 run-log budget_note 补记估算口径，而非只写 progress.md。
- **F7 (LOW) 费用数字口径**：§2.5 "≈246 次内建搜索"含探针 28 次（本批 6 家实测 218 次、1.20 次/题）；§0 "~200 次请求"为 5 家口径（MiMo 计费全口径 ≈275 attempts）。方向保守，建议改用全口径数字。
- **F8 (LOW) 000738 表格行"—"**：§2.2 该行修复/均延迟未回填（实际 12 次/27.0s，本审查已补齐），且 §2.1 三个 5 家口径数字与之同源——回填后 F1/F8 一并消除。
- **F9 (INFO) fail-closed 表述可更精确**：15 题"从未触发搜索"→全部 insufficient_evidence（声称成立）；另有 6 题"搜索已调用但回执不可核验"→unknown（0 伪分），报告未单列此桶。
- **F10 (INFO) REV-06 映射缺"用户排除"维度**：case 要求"用户排除可核验"，报告未提及（本批 zero-pool-write 下无排除操作，一句声明即可）。
- **F11 (INFO) cohort 每格 n=1**：§2.2 分层观察建议显式标注，避免被读成层级结论。
- **F12 (INFO) 归档文件形态**：companies_60_full_signed.json 为工作文件投影（60/60 成员一致、无值差；分类字段以冻结 JSON 为准）；repair-manifest reason 文本 "12+11+3=26" 与 files[]=27 差一（removed_count=27 与目录一致）；rejected_probe/ 下另有一份 MiniMax 时代失败探针 CN_A_002122.json（21:36:47）未在报告提及，不影响结论。

## 4. 裁决

**needs_revision**（文档/治理修订，无需重跑、无需改数据）：

放行前必须完成：
1. 更正报告 §2.1 三个汇总格为 6 家口径（attempts 239、修复 57、均延迟 ≈46.9s/max 178.9s），并回填 §2.2 000738 行（12 / 27.0s）（F1/F8）。
2. 以 amendment-5（或报告 §4 明示）记录 amendment-4 探针门的放宽及理由（F2）。
3. 时间戳统一为真 UTC 或显式标注本地钟 +1h（F3）。

建议一并处理：F4（复现命令保真）、F5/F6（第二次失败表述与缺口量化）、F7（费用数字口径）、F10–F12。

明确结论（供 G2 使用）：6 家 MiMo 批的 scored 111/182 (61.0%)、insufficient 60 (33.0%)、unknown 11 (6.0%)、error 0、搜索执行 161/182 (88.5%)、来源 1,096 条、预算 940/2600 与 897/5200 caps 内——经独立复算全部属实；样本缩减于批前 5 分 15 秒冻结、无择优证据；60/20 签名名单完整归档；000738 缺口为已披露的诚实账本洞；费用发现转述与计划原文一致；无 60→6、单模型→跨模型、逐题基线→方法对照的过度声称。

—— 独立审查代理，r1，2026-10-05

---

## 5. r2 复核（2026-10-05）— 聚焦修订面，r1 复算结果为基准

修订版：`L02-calibration-report-2026-10-05.md`（头部标注 r1 修订版，处置明细 §6 表）；随附证据 `L02-summary-6mimo-2026-10-05.json`、冻结文件补录 amendment-5、summarize.py 重写。逐核查点结论：

**(a) §2.1/§2.2 与 r1 复算一致 ✓**
- §2.1：scored 111 (61.0%)、insufficient 60、unknown 11、error 0、search 161/182 (88.5%)、attempts 239（182 首答 + 57 修复，57/182=31.3%）、来源 1,096、avg 46.9s、max 178.9s——与 r1 复算表逐格一致。"全部 receipt ≤2 attempts"与 r1 实测一致。
- §2.2：000738 行已回填 12 修复 / 27.0s（F8 并入 F1 处置），其余各行与 r1 一致。

**(b) amendment-5 时间线表述与磁盘证据一致 ✓**
- 冻结 JSON 现含 3 条修正案：amendment-3 20:45:15Z、amendment-4 **21:26:31Z**（未被改动）、amendment-5-probe-gate-interpretation-recorded at=23:12:03Z；`sample_sha256` 未变（ef415682…复算相符）、60 entities 完整。
- amendment-5 trigger 中的锚点全部对得上：探针结束 21:29:58Z（探针 attempt 级 max completed_at=21:29:57.9Z）、派发 21:31:46Z（run-log 批窗 started_at）；"当时记录于 progress.md"经 r1 核实（progress.md 开跑条目确含门语义修订记录，且先于批完成条目）。
- 关键事实声称经探针交叉表**精确验证**：探针 8 题未执行搜索 → **8/8 全部 insufficient_evidence**（探针唯一的 unknown 位于 21 个 executed 之内）——amendment-5 与报告 §4"未执行搜索的 8 题已 fail-closed 进分母"属实。
- `at=23:12:03Z` 为补录写入时刻（晚于批完成，与 `effect_on_results: none` 及证据文件 generated_at=23:10:03Z 构成自洽先后链），amendment-5 明确标注 "retroactively"、"gate interpretation changed before dispatch but after seeing probe results"，**未虚构 owner 对门修订的签认**，仅如实补录——披露诚实度达标。

**(c) 新时间戳与锚点一致 ✓**
- 探针 20:47:36Z–21:29:58Z：探针文件 attempt 级时间戳本身即真 UTC（min started=20:47:36.8Z，max completed=21:29:57.9Z→报告取 21:29:58Z），42 分钟 ✓。
- 批窗 21:31:46Z–22:11:58Z ✓（run-log started_at + 末家 mtime 23:11:58 local − 1h）；000738 单跑 22:16:06Z–22:34:36Z ✓（run-log last_window + 日志行 23:16:07/23:34:36 local）；§0 amendment-3 20:45:15Z / amendment-4 21:26:31Z ✓（JSON 内可查）。全文已统一真 UTC 并声明 local=UTC+1 ✓。

**(d) §5 复现命令实际执行 ✓**
- `python -X utf8 summarize.py <out.json> mimo` 实跑：included=6 / skipped=5，聚合 `{182, 111/60/11, 161 (0.885), attempts 239, repairs 57, urls 1096, avg 46.9s}`，**整份输出与证据文件逐字段相等**（仅 generated_at 不同）；max 178.9s 与 §2.1 相符。重写后的 summarize.py 为文件级 provider 过滤（attempts[].provider 集合判定），聚合口径与 r1 独立复算定义一致（repairs=Σ(attempts−1)，attempt 级时延加权）。F4 关闭。

**(e) 未引入新过度声称 ✓（一处残留措辞建议，不阻断）**
- F2 披露措辞：§4 如实声明"修订发生在派发之前（顺序成立），但晚于探针结果——门解释的前向修订"，未把事后补录说成事前批准 ✓。
- "≤1h 约束达成"：现依据为主批 40 分钟（21:31:46–22:11:58Z）+ 000738 单跑 18.5 分钟，分段运行时合计 58.5 分钟 ≤ 1h，两段时间与端点时刻均在 §1 明示，读者可自行算出含批间 4 分钟间隔的端到端墙钟 62.8 分钟。**残留建议（INFO，不阻断）**：若 G2 按"端到端墙钟"口径审查，建议在 §2.1 墙钟行补一句"（端到端含间隔 62.8 分钟）"。
- §2.3 重写与 r1 磁盘证据完全一致（唯一在案失败 730.6s + stale done 跳过 planned=153=182−29 + 单跑成功；删除"两次静默失败"表述 ✓；"≈29（上界）"为单次口径的合理表述）。
- §0 ≈275（239+36）、§2.5 本批 218（1.20/题）+ 探针 28 = 246——与 r1 复算一致 ✓。§2.1 的 6 题"搜索已调用但回执不可核验"→unknown、§2.2 每格 n=1 声明、§4 用户排除零操作与归档 60/60 投影——均与 r1 核查结果一致且如实标注 ✓。
- §3 "未触发/不可核验题按契约 fail-closed（insufficient_evidence/unknown），不产生伪分"——与 r1 交叉表一致（批 15 未触发→insufficient、6 不可核验→unknown；0 伪分）✓。

**残余备注（INFO，均不阻断）**：① 上条"≤1h"端到端口径提示；② 证据 JSON 的 answer_statuses 不含零值键（error=0 需由 182−111−60−11 推得，建议 G2 材料注明）；③ summarize.py provider 过滤对"无 attempt 级 provider 的文件"会纳入而非跳过（本数据不触发）；④ "≈29（上界）"若以含修复的硬上界表述应为 ≈58，现表述为单次口径估计，可接受。

## 6. r2 裁决

**approved。** F1–F8 阻断/LOW 与 F9–F12 INFO 全部处置属实：数字口径已统一为 6 家并与独立复算及可执行复现命令一致；amendment-5 如实补录门解释修订且时间线与磁盘锚点吻合；时间戳全文转真 UTC；000738 叙述已改为与证据完全对应的"单次在案失败 + stale 跳过 + 重跑成功"；费用口径拆分正确；无新增过度声称。本报告连同 `L02-summary-6mimo-2026-10-05.json` 可作为 G2（REV-06、LIVE-03/04 等 case）的校准材料提交，残余 INFO 项不构成放行条件。

—— 独立审查代理，r2，2026-10-05
