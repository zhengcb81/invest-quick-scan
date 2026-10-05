# G2b A/H Bridge 导入批次独立审查报告（2026-10-05）

审查者：独立审查 agent（与实现者无关，全部结论由本人复算/复跑取得）。
裁决：**approved**（r1 附 3 P2 / 5 LOW / 3 INFO；整改后 r2 复审通过，**终裁 approved**，见 §10）。

## 1. 范围

- 施工卡（权威）：`docs/implementation/reviews/IQS-lane/G2b-AH-bridge-import-card-2026-10-05.md`。
- 源数据：修正版 `G2b-AH-bridge-draft-2026-10-04.json`（121 行）与原件备份 `…original-122rows.json`（122 行），均 status=SIGNED。
- 被审代码（StockWiki 仓，未提交部分，HEAD=0d6adf3「W06-followup」——该提交本身不在本批范围，本批 diff 均相对它）：
  `stockwiki/quick_scan_schema.py`（v5 DDL）、`stockwiki/quick_scan_store.py`（SCHEMA_VERSION=5+迁移链）、
  `stockwiki/quick_scan_issuer_bridge.py`（新模块）、`stockwiki/cli_parsers/quick_scan.py`（+2 子命令）、
  `tests/test_quick_scan_issuer_bridge.py`（11 测试）。
- 真实库 `StockWiki/data/quick_scan/scan.sqlite` 全程只读（`file:…?mode=ro` URI 打开；journal_mode=delete；报告重跑前后 SHA-256 与目录清单均未变）。
  本批未对真实库执行任何 import；幂等性改用**临时目录库**独立复证（临时库用后即删）。
- 未联网、未调 LLM；除本报告外未写任何文件。

## 2. 方案 A 修正复算（逐字段，独立代码 diff）

### 2.1 哈希（本人重算）

| 文件 | 期望 | 实测 |
|---|---|---|
| 修正版 | 55B79EB9469A5D2392C643BEE3E81AA66CF83DB10124BA3E8C4BE9EA2C5A7A16 | **一致** |
| 原件备份 | FA9CE0B94E9FED7D99A9B4FB90D9980B1E5D0EB6BF7F9907F7A54A0A6712AF4E | **一致** |

两文件均无 BOM。

### 2.2 行级 diff

- 恰好删除 **1 行**、新增 **0 行**：`(CN-A:600849, HK:02607)`（原件 rows[47]），完整行内容含 evidence_url `https://static.cninfo.com.cn/finalpage/2026-03-31/1225062873.PDF`、content_sha256 `3b556e17…2c970`。
- 其余 **121 行逐行完全相同**（按原顺序 canonical JSON 字节级相等，`json.dumps(..., ensure_ascii=False, separators=(",",":"))` 比较为 True）。
- 独立根因证实：原件 122 行中 content_sha256 `3b556e17552b22cf…2c970` **恰好出现 2 次**——`(CN-A:600849,02607)` 与 `(CN-A:601607,02607)` 两行引用同一 PDF、同 sha、异 pair，正是导入器 sha_conflict fail-closed 的触发条件；修正版 **0 重复、121 distinct**，该冲突源已消除。

### 2.3 行派生 stats 重算（由剩余 121 行独立重算 → 与修正版 stats 比对）

| 字段 | 由 rows 重算 | 修正版 stats | 相等 |
|---|---|---|---|
| rows | 121 | 121 | ✅ |
| confidence | `{"high": 121}` | `{"high": 121}` | ✅ |
| verification_source | `{"exchange_filing": 121}` | 同 | ✅ |
| evidence_kind | `{"annual_report_ah_section": 121}` | 同 | ✅ |
| issuer_id | `{"not_found_in_sources": 121}`（121/121 issuer_id=null） | `{"not_found_in_sources": 121}` | ✅（但见 LOW-1：键集与原版不同） |
| hkex_leg_crosscheck.checked | 121（=行数） | 121 | ✅ |
| universe_coverage_pct | round(121/151×100, 1) = **80.1** | 80.1 | ✅ |

（原版为 122/80.8：rows 122→121、confidence.high 122→121、evidence_kind 122→121、verification_source 122→121、checked 122→121、universe 80.8→80.1、issuer_id.not_found_in_sources 122→121，全部同向同幅，重算一致。）

### 2.4 非行派生字段（零变化，逐键比对）

- `pairs_checked=151`、`pairs_in_universe_name_matched=151`：不变。
- `priority_list_size=13`、`priority_covered=12`、`priority_coverage_pct=92.3`：不变。
- `gaps=31`、`gap_reasons={"no_dual_code_evidence":1,"dual_code_not_confirmed":30}`（含顶层 `gaps` 对象）：不变。
- `hkex_leg_crosscheck.mismatches=0 / errors=0 / mismatch_detail=[]`：不变。
- 顶层键（schema/generated_at/pair_list_source/evidence_policy/issuer_id_policy/briefed_vs_confirmed_corrections/closes_g2b_ah*/next_step/web_access 等 14 个，rows/stats/owner_signoff 除外）：**逐一完全相同**。

### 2.5 owner_signoff / 状态

- 原 4 项决策逐项字节相同：`dual_code_not_confirmed_30`、`h_code_corrections_4`、`issuer_id`、`ningbo_002142_disproven`。
- 追加第 5 项 `shanghai_pharma_old_code_row_removal`（内容含官方现代码 601607/02607 依据、122→121、80.8→80.1、priority/gap/universe 级不变的声明——与我方复算逐项吻合）。
- `signed_by` 保留原文并追加「+ owner structured decision 2026-10-05 (ask_user_question round-38, ah_row_decision): 方案A 删旧行重签」；`signed_at=2026-10-04` 不变。
- `status=SIGNED` 不变；`decision_ref=owner-2026-10-04-g2b-ah-bridge-signoff` 不变。

**结论：方案 A 修正正确**（唯一结构瑕疵见 LOW-1）。

## 3. 导入器与测试复跑结果

- `python -X utf8 -m pytest tests/test_quick_scan_issuer_bridge.py -q -p no:cacheprovider` → **11 passed**（6.83s）。
- ruff（F/I/W，line 100）对 5 个触及文件：**All checks passed**；`black --check -l 100` 同 5 文件：**5 files would be left unchanged**。
- 卡片语义边界与实现逐条核对（实现代码通读 + 行为探针，探针全部在**临时库**执行）：

| 卡片语义 | 实现 | 复跑证据 |
|---|---|---|
| 内容寻址幂等：同 sha 重放=no-op | sha 命中且 pair 相同 → `rows_unchanged` | 套件 `test_idempotent_replay_is_a_no_op`；我的临时库全量导入 #1=inserted 121/unchanged 0，#2=**inserted 0/unchanged 121**（batch 均 AHB_55b79eb9469a5d23） |
| 同对异 sha=conflict | `pair_conflict` 回滚 | 套件 `test_same_pair_different_sha_conflicts` |
| 同 sha 异 pair=conflict（原件故障场景） | `sha_conflict` | 探针 `same_sha_new_pair` → REFUSED sha_conflict |
| 缺 status=SIGNED | `source_not_signed` | 套件 + CLI exit2 测试 |
| 行数≠申报值 | `row_count_mismatch`（stats.rows vs len(rows)） | 套件 |
| 行缺 evidence_url/content_sha256/retrieved_at | `row_shape_invalid` | 套件（evidence_url）+ 探针（retrieved_at、content_sha256 均 REFUSED） |
| entity_id/issuer 绑定禁止 | `entity_binding_forbidden`（issuer_id 非空即拒） | 套件 + 探针 |
| 零副作用 | 固定列映射，不写 entity/member/universe/scan_eligible | 套件断言；真实库与临时库导入后 entity/member/universe 均 0（详见 §4、findings LOW-2） |
| 命名拒绝 exit 2、零 traceback、规范 JSON stdout | `run_issuer_bridge_import` stderr JSON、return 2 | 套件 CLI 两测试；我复跑 `issuer-bridge-report` stdout 为紧凑排序 JSON |
| evidence_host（超出卡片的加固） | 仅允许 `https://static.cninfo.com.cn/` | 探针 `non_cninfo_host` → REFUSED evidence_host_unsupported |

- 全量套件 collect=**932**（917 passed + 15 skipped，含本批 11 测试，自洽）。

## 4. DB 核验证据（只读直查，sqlite `mode=ro`）

| 检查项 | 实测 |
|---|---|
| PRAGMA user_version | **5**；journal_mode=delete |
| quick_scan_issuer_bridge 行数 | **121** |
| distinct content_sha256 | **121**（distinct pair 亦 121） |
| cn_listing_key=CN-A:601607 | **1 行** |
| 600849（listing_key 或 ticker） | **0 行** |
| quick_scan_candidate | **216** |
| quick_scan_entity | **1**（`ENT_97bf6a65…` Alphabet Inc.，既有） |
| quick_scan_member / quick_scan_universe | **0 / 0** |
| SUM(scan_eligible)（quick_scan_candidate，216 行） | **0** |
| bridge.issuer_id 非空 | 0（issuer_id_status 121×not_found_in_sources） |
| import_batch_id | 单值 `AHB_55b79eb9469a5d23` = `AHB_`+sha256(修正版文件)[:16]，证明落库源即该文件 |
| imported_at | 单值 `2026-10-05T05:41:58Z`（UTC） |
| **DB↔源文件逐行逐字段 diff** | 121/121 行、13 个映射字段 + issuer_id + decision_ref 全比对：**0 不匹配、0 多余 sha**（补足卡片 §4 要求的「与源文件 diff=0 证明」，因 report 子命令未实现该项，见 P2-3） |

**幂等/只读复证（我自行重跑，未跑 import）**：
`python -m stockwiki.cli --root <StockWiki> issuer-bridge-report` → exit 0，stdout：
`{"action":"issuer-bridge-report","confidence":{"high":121},"decision_refs":["owner-2026-10-04-g2b-ah-bridge-signoff"],"llm_calls":0,"network_calls":0,"rows":121,"rules_version":"quick_scan_issuer_bridge_import/1.0.0"}`
执行前后 scan.sqlite SHA-256 均为 `D0D51CBEA95E24185D63687B068F48547C24E6D6FD350C8657B900117550EE5F`，`data/quick_scan` 目录清单（名称/大小/时间戳）完全一致——**真实库零写入**（migrate 在 version==SCHEMA_VERSION 时提前返回，不进事务）。
真实库的 import 幂等回执未重跑（按约束）；实现者 replay 回执（inserted=0/unchanged=121）见 IQS `progress.md:1757`，我以临时库独立复现同结论（§3）。

## 5. 范围合规 diff

- `git status`（StockWiki，HEAD=`0d6adf3`）恰好 **5 文件：3 改 2 增**，与施工卡一致：
  - M `stockwiki/cli_parsers/quick_scan.py`（+30）
  - M `stockwiki/quick_scan_schema.py`（+31）
  - M `stockwiki/quick_scan_store.py`（+4/-1）
  - ?? `stockwiki/quick_scan_issuer_bridge.py`（319 行）
  - ?? `tests/test_quick_scan_issuer_bridge.py`（248 行）
  - 无第 6 个文件；`.planning/sw-ident_handoff_2026-09-30.json` 未被本批修改（见 LOW-4）。
- 5 文件 SHA-256（记档）：
  - quick_scan_schema.py `095D2EB25CF283853483EF98E6653595DF326306BA2CFDC6E3E06CDB56914E46`
  - quick_scan_store.py `BA742B4214BC383F0D11EF9E119FA522A11230D58022C691DF5EFCD787C7F304`
  - quick_scan_issuer_bridge.py `13B0BEACE3A2F8F3D92B34CCF9B5D8886084ECA77E8B875D9C8AD037586CF34B`
  - cli_parsers/quick_scan.py `F2F4F9FABB730278F63AB4689E979BADCF821325D34377DE2CFBC94FB8517BBB`
  - tests/test_quick_scan_issuer_bridge.py `A90DB450720E319438B811A0C07DE3B9E13F1FED23CD8B79F2D6E1550E3FCDA9`
- 迁移链 v4→v5：`SCHEMA_VERSION=4→5`，`if version < 5: apply_v5(con)`；`apply_v5` DDL **仅** `CREATE TABLE quick_scan_issuer_bridge` + `CREATE INDEX idx_qsbridge_decision`，**对既有表零改动**（diff 复核）。
- store 行数：**969 < 1000 硬门**（validate-framework 报 >600 已知 baseline warning，属既有记录）。
- CLI 注册：恰好 +2 子命令 `issuer-bridge-import`（--source/--at）与 `issuer-bridge-report`。

## 6. 门结果（全量独立重跑）

`bash scripts/check_all.sh`（StockWiki 仓，后台完整跑完）：

- ruff：All checks passed ✓
- coverage 全套：**917 passed, 15 skipped**（257.39s），TOTAL ≥73% ✓，ui.py 75% ≥40% ✓ —— 与上次基线 **917 持平**（collect 932 = 917+15，含本批 11 测试）
- validate-framework：0 errors、12 warnings（11 条 OKF type 既有 + 1 条 store>600 既有）✓
- **`=== ALL CHECKS PASSED ===`，exit 0**

## 7. 语义抽查

- evidence_url：121/121 为 `https://static.cninfo.com.cn/` 前缀（且 importer 硬性强制，非 cninfo 拒收）。
- 时间戳：源 retrieved_at 121/121 为 `YYYY-MM-DDTHH:MM:SSZ`；落库 imported_at、generated_at 均 UTC Z。
- issuer_id：源 121/121 null；落库 121/121 NULL；非空即 `entity_binding_forbidden`（探针实证）。
- 密钥/网络痕迹：两份 A/H JSON 中 `http://`、`sk-/sk-ant-/AKIA/Bearer/api_key/token/secret/password`、`llm_call/network_call/openai/anthropic` 命中均为 **0**；回执与 report 均硬编码 `llm_calls=0, network_calls=0`；本批无 CSV 产出（同目录 G2b-D CSV 属另一批次，未触碰）。本审查全程未联网、未调 LLM。

## 8. Findings

### P0：无

### P1：无

### P2

- **P2-1｜decision_ref 无「不匹配」校验**：卡片拒绝项写「文件缺 status=SIGNED 或 decision_ref 不匹配」，实现只做**存在性**检查（`decision_ref_missing`），不与任何期望值比对；CLI 也无 expected-ref 参数。我在临时库实测：伪造 `decision_ref="forged-ref-xyz"` 的文件被接受且该值**落库**。实践上信任锚仍是「操作者传入的已签文件 + owner 签名」，但该条卡片语义未被强制。建议后续批次补 `--expect-decision-ref` 或在拒绝清单中明确「不匹配=缺失」。
- **P2-2｜卡片测试清单缺专门迁移测试**：卡片要求「v4 真实库升级 v5 保数据（空库与带 216 staging 库两态）」，套件无 v4→v5 专项测试。现有覆盖为间接：`test_migrate_upgrades_v1_database_preserving_data` 走完整 v1→v5 链并断言保数据与幂等，空库态由各 tmp 测试隐式覆盖，216 态由**真实库升级后 216 候选完好**（§4）实证。建议补一条 v4+216→v5 的回归测试封口。
- **P2-3｜issuer-bridge-report 缺卡片两项输出**：卡片 §4 要求 report 提供「sha 清单摘要」与「与源文件 diff=0 证明」，实现只输出行数/confidence/decision_refs。diff=0 已由我独立补证（§4）；sha 摘要缺失意味着报告消费方无法仅凭 report 校验内容寻址清单。建议 report 增加 sha256 集合摘要（如排序拼接后的 sha256）与可选 `--source` 比对。

### LOW

- **LOW-1｜stats.issuer_id 键集变化**：原版 `{"authoritative":0,"not_found_in_sources":122}`（零填充词表），修正版为 `{"not_found_in_sources":121}`——**丢弃了 `authoritative:0` 键**。数值层面与 rows 重算完全一致（authoritative 本来就为 0），仅键集不同；若按原版零填充约定重算则应为 `{"authoritative":0,"not_found_in_sources":121}`。属结构一致性瑕疵，不影响任何下游计数语义。
- **LOW-2｜scan_eligible 夹带无命名拒收**：卡片拒绝项含「尝试写入非空 entity_id 或 scan_eligible」。issuer_id 有 `entity_binding_forbidden`；行夹带 `scan_eligible` 字段则被**静默忽略**（探针 ACCEPTED，字段不落库——桥表无该列、固定列映射，故零副作用保证不受影响），但没有卡片措辞意义上的命名错误码。
- **LOW-3｜卡片 CLI 语法中 `[--report <path>]` 未实现**：实际只有 `--source/--at` + 独立 `issuer-bridge-report` 子命令；回执走 stdout。功能上被 stdout 规范 JSON 覆盖，语法与卡片字面不一致。
- **LOW-4｜handoff 未按卡追加 authorized_paths**：`.planning/sw-ident_handoff_2026-09-30.json` 的 `scope.authorized_paths` 不含 `quick_scan_schema.py`、`quick_scan_issuer_bridge.py`、`tests/test_quick_scan_issuer_bridge.py`，`changed_paths` 仍停在 W06 的两文件；卡片列其为本批允许改动之一（授权溯源记档缺口）。注意任务口径要求恰好 5 文件，此为记档缺口而非越界写。
- **LOW-5｜卡片正例「122 行全量导入」未进测试套件**：正例测试用 2 行 fixture；全量导入由真实导入（121 行落库、DB↔源 0 diff）+ 我的临时库全量 replay（121/0→0/121）覆盖。另测试 docstring 仍写「signed 122-row」（陈旧表述）。

### INFO

- **INFO-1｜content_sha256 的语义**：为**证据文档（cninfo PDF）哈希**而非行哈希——原件中同 URL 两行同 sha、不同 URL 行互异的模式证实；与模块 docstring「evidence document hash is the primary key」一致。导入器只验 64 位 hex **格式**、不重算 preimage（卡片仅要求「缺」即拒）；同 PDF 桥两对会被 `sha_conflict` 拒绝，本批 121 行 121 PDF 无此情形。副作用：内容绑定完整性依赖 owner 签名与 pair 冲突守卫，而非导入期重算。
- **INFO-2｜异常路径小边界**：`QuickScanStoreError`（如库版本高于支持值）不在两个 CLI handler 的捕获清单内，该极端情形会以 traceback 退出（正常与负例路径零 traceback 已由套件覆盖）。
- **INFO-3｜记档**：卡片提及「PWF task_plan 补 Phase 75 节」——IQS `task_plan.md` 现有 Phase 75 属 L02 试点（题面不同），本批的执行记录目前在 `progress.md:1757`；实现者如未另立章节属 IQS 侧记档事项，不影响本批实物裁决。

## 9. 裁决

**approved**。

核心三轴全部通过：①方案 A 修正逐字段复算正确、两哈希吻合、sha_conflict 根因独立证实且已消除；②导入器语义与 11 测试复跑通过，ruff/black/全量门 917 全绿（exit 0），范围恰 5 文件、迁移链加法、store 969<1000；③真实库只读核验 121/121/1/0/v5/216/1/0/0/0 全数吻合，DB↔源 0 diff，report 只读重跑哈希不变，零 LLM/网络/密钥痕迹。
P2-1/2/3 为卡片语义边界与测试/报告矩阵层面的次要缺口，不改变本批导入的正确性、幂等性与零副作用，建议在下一批（verified issuer 实体化回填）前择一闭合。

## 10. 跟进复审（r2，聚焦整改面）

r2 范围：逐项核对 r1 findings 的整改实现、handoff 在册、本轮 StockWiki diff 边界、LOW-1「不改」理由；r1 的方案 A 复算/DB 只读核查不重做。全部结论为本人复跑所得。

### 10.1 整改逐项核验（(a)）

| r1 finding | 整改实现（代码核读） | 我的复跑证据 | 判定 |
|---|---|---|---|
| P2-1 decision_ref | `_DECISION_REF=^owner-\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$` 在 `_read_signed_source` 内格式校验→`decision_ref_invalid`；`import_issuer_bridge(expect_decision_ref=)` 不符→`decision_ref_mismatch`，位置在 `_read_signed_source` 之后、`sqlite3.connect` 之前（模块行 175 vs 191，**先于本函数任何 DB 连接**）；CLI `--expect-decision-ref` 已注册 | 临时库探针：`forged-ref-xyz`→**REFUSED decision_ref_invalid**；expect 不符→**REFUSED decision_ref_mismatch**；expect 匹配的 replay=0/121 正常；真实签收 ref `owner-2026-10-04-g2b-ah-bridge-signoff` 过格式校验（真实源全量导入/报告不受影响） | ✅ 闭合（见 INFO-5 关于 CLI 级 migrate 时序的注记） |
| P2-2 迁移测试 | 新增 `test_v4_to_v5_migration_preserves_staged_candidates`：态A 空库 migrate()==5 且桥表在；态B 手工 `apply_v1..v4`+`user_version=4`+插 1 条 staging candidate → migrate()==5 后 candidate 存活、user_version=5、桥表在 | 套件复跑通过（该测试独立可过） | ✅ 闭合（卡片两态均有断言；卡片原示「216」为量级指代，测试以 1 条真实 staging 行代表，结合 r1 真实库 216 完好实证，覆盖充分） |
| P2-3 report 输出 | `bridge_report(store, *, source=)`：恒有 `sha_manifest_digest="sha256:"+sha256("\n".join(sorted shas))`；`--source` 时按 `_DIFF_COLUMNS`（**15 字段**）逐 sha diff 出 `source_diff{rows_source,rows_db,mismatches,mismatch_shas,missing_in_db,extra_in_db,diff_zero}`；CLI `issuer-bridge-report --source` | 临时库：真实源 vs 库→`diff_zero=True, mismatches=0`；篡改 1 行 confidence→`mismatches=1`+指名 sha、`diff_zero=False`；源删 1 行→`extra_in_db=[…]`、`diff_zero=False`；digest 长度 71。**真实库只读 CLI**：`--source <修正版>`→`diff_zero:true, rows 121/121, digest sha256:c0cbac72147c2…`，exit 0，DB 哈希前后仍 `D0D51CBE…` 不变 | ✅ 闭合 |
| LOW-2 scan_eligible | `_validate_row`：`row.get("scan_eligible") not in (None, False)`→`scan_eligible_forbidden`；测试钉住 | 探针：`1/True/"yes"`→**REFUSED scan_eligible_forbidden**；`0/False/None`→接受（0==False 的 falsy 语义，与「非 None/False 拒收」意图一致，且这三种值不授予任何资格） | ✅ 闭合 |
| LOW-3 `--report <path>` | CLI `--report` 写 `rendered+"\n"`，内容与 stdout 同一 `rendered`；测试断言 `written == payload` | 测试 `test_cli_import_writes_receipt_report_copy` 复跑通过；代码逐字段同源确认 | ✅ 闭合 |
| LOW-4 handoff 在册 | 见 10.2 | 见 10.2 | ✅ 闭合 |
| LOW-5 docstring | 模块 docstring 改为「121 rows after the owner-approved plan-A correction… originally signed table had 122 rows — see the archived original」 | 代码核读确认 | ✅ 闭合（测试文件头仍写 "signed 122-row"，陈旧一句，降为 INFO-4） |
| INFO-2 QuickScanStoreError | 两个 CLI handler 的兜底 except 均加 `QuickScanStoreError`（顶部 import） | 代码核读确认（行 378/400） | ✅ 闭合 |

- 复跑汇总：`pytest tests/test_quick_scan_issuer_bridge.py` → **17 passed**（11 原 + 6 新）；ruff 5 文件 **All checks passed**；`black --check -l 100` 5 文件 **unchanged**；全量 `check_all.sh` 独立重跑 → **923 passed, 15 skipped**（917+6 自洽）、coverage≥73%、validate-framework 0 errors、**ALL CHECKS PASSED exit 0**。
- 新增 6 测试与整改项一一对应（forged-ref、expect-mismatch、scan_eligible、source-diff+digest、--report 回执、v4→v5 两态）。

### 10.2 handoff 在册（(b)）

- `.planning/sw-ident_handoff_2026-09-30.json` JSON 校验通过；`scope.authorized_paths` **12→17**，新增 5 路径全在：`quick_scan_schema.py`、`quick_scan_issuer_bridge.py`、`tests/test_quick_scan_issuer_bridge.py`（本批 3）+ `quick_scan_freshness.py`、`tests/test_quick_scan_freshness.py`（W06 对，顺带补既有记档缺口）。
- `authorization_scope_ref` 追加依据完整：**W13**（schema DDL 抽取）、**G2b A/H bridge import batch card 2026-10-05**（review approved）、**W06-followup card 2026-10-05**（two-round review approved, committed 0d6adf3）、**决定5** 通授——四项均在串。
- 其引用的 `IQS task_plan Phase 77` **确实存在**（`task_plan.md:1097`「Phase 77: G2b A/H bridge 导入批次（G2b 最后实物）」），引用与实物对应（顺带修正 r1 INFO-3：记档已落 Phase 77，而非卡片所写的 Phase 75）。
- 注记（INFO-6）：`changed_paths` 仍为更早批次的两文件、文件尾换行被去掉（`}\ No newline at end of file`）——均为既有/外观状态，非本批声称范围。

### 10.3 本轮 diff 范围合规（(c)）

`git status`（HEAD 仍 `0d6adf3`）恰好 **6 文件** = r1 的 5 文件 + `.planning/sw-ident_handoff_2026-09-30.json`（M，+11/-4，内容即 10.2 的在册追加），**无第 7 个文件、不越 r1 认可边界**：
M `.planning/sw-ident_handoff_2026-09-30.json` / M `stockwiki/cli_parsers/quick_scan.py`（+49）/ M `stockwiki/quick_scan_schema.py`（+31，与 r1 相同）/ M `stockwiki/quick_scan_store.py`（+4/-1，与 r1 相同）/ ?? `stockwiki/quick_scan_issuer_bridge.py`（319→409 行）/ ?? `tests/test_quick_scan_issuer_bridge.py`（248→421 行，17 测试）。
r1 已记档的 schema/store 两文件 SHA-256 未变（diff 与 r1 一致）；本轮新增改动集中于 bridge 模块、CLI、测试与 handoff。

### 10.4 LOW-1「不改」理由核验（(d)）

理由**成立**：我重算两份已签文件哈希，仍为 `55B79EB9…` / `FA9CE0B9…`（与 r1 记档一致）——修正版若回填 `authoritative:0` 将改变文件字节 → (i) 真实库 `import_batch_id=AHB_55b79eb9469a5d23` = `AHB_`+sha256(该文件)[:16] 的批次绑定断裂；(ii) 破坏 owner 对**确切字节**的签收完整性与 r1 报告哈希记档；(iii) 而该键数值恒为 0，不参与任何计数语义。**接受不改，留档理由充分**（已同步施工卡整改节与 progress）。

### 10.5 本轮只读与边界确认

- 真实库本轮未被触碰：scan.sqlite SHA-256 前后仍 `D0D51CBEA95E24185D63687B068F48547C24E6D6FD350C8657B900117550EE5F`（=r1 值）；对真实库的唯一操作是 `issuer-bridge-report --source` 只读一次。
- 两份已签 JSON 哈希未变（见 10.4）；行为探针全部在临时目录库执行并已清理；未联网、未调 LLM。

### 10.6 r2 findings 与裁决

- **P0/P1/P2：无**。r1 三项 P2 全部闭合（证据见 10.1）。
- **LOW：无新增**。r1 LOW-2/3/4/5 已闭合；LOW-1 按理由接受留档。
- **INFO（本轮新增注记，均不阻断）**：
  - INFO-4：测试文件头 docstring 曾写「signed 122-row」——收口提交 `01a4289` 已更正为「121 rows after the owner plan-A correction … originally 122 — see the archived original」并注明 r2 扩展，**已闭合**（见 10.7）。
  - INFO-5：`decision_ref_mismatch` 在 `import_issuer_bridge` 内先于**其自身** DB 连接，但 CLI handler 在调用前先跑 `store.migrate()`——v5 真实库上 migrate 为只读提前返回（零写入，本轮已实证哈希不变）；仅在「未迁移旧库 + decision_ref 不符」组合下会先执行迁移 DDL 再拒收（迁移是加法 DDL、非桥表写入，且该组合不在本批路径内）。
  - INFO-6：handoff `changed_paths` 停留更早批次、文件尾换行缺失（既有/外观，非声称范围）。
  - r1 INFO-1（content_sha256 为证据 PDF 哈希、导入器只验格式）为设计事实，维持不变，不视为待整改项。

**r2 裁决：approved。** 整改与 r1 findings 逐项相符且有独立复跑证据；范围 6 文件合规；LOW-1 不改理由成立；门 923 全绿。可按此裁决进行隔离提交。

### 10.7 收口附记（提交后核验，2026-10-05）

按裁决隔离提交后我做了最后一次新鲜度核验（收口确认阶段）：

- `01a4289`「feat(quick-scan): G2b A/H issuer-bridge import …（two-round review approved, check_all 923; handoff authorized_paths 12→17）」父 `0d6adf3`，**提交恰含 6 文件**（M handoff / M cli_parsers / M schema / M store + A issuer_bridge / A tests），`git diff 0d6adf3 01a4289 --stat` 与 r2 §10.3 的工作树 diff 逐文件一致（409/49/31/4/11 行），工作树干净、无遗留 untracked。
- 测试文件头部 3 行 docstring 更新（121-after-plan-A 表述 + r2 扩展说明）——17 个测试名与断言主体不变，复跑 **17 passed**（2.65s）；即 INFO-4 随之闭合。
- 只读复核未变：scan.sqlite 仍 `D0D51CBE…`、修正版已签 JSON 仍 `55B79EB9…`。

**批次收口：approved（r1 + r2 终裁），StockWiki 提交 `01a4289`。**

---
*方法声明：所有数字为本审查者独立复算/复跑所得；真实库仅只读访问（mode=ro，前后哈希比对）；行为探针全部使用临时库并已清理；未联网、未调 LLM；本报告为本批唯一写入文件（UTF-8 无 BOM）。r2 段为同文件追加。*
