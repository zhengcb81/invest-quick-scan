# EVID-LAB-01 summary（2026-10-08 残余整改后）

唯一工作目录 `C:/Users/郑曾波/Projects/iqs-evidence-lab`，分支 `codex/evid-lab-01`，无remote。
**源码结果 commit 见 `handoff.json.snapshot.result_commit`**（tool 0.2.1）；
本交接证据在随后的证据 commit 中（按规范不把自身hash写入文件；证据HEAD = 交付后
`git log` 的 tip，`handoff.json.snapshot.result_commit` 指向源码结果 commit）。
历史链：起点 `cc3c388…` → 原交付 `35b98cd…` → 总控验收点 `d87cf71…` →
整改代码 `f5149b9…` → 版本提升 `62fe8b2…` → 交接证据 `a1889fc…` →
收尾 `380cb49…` → **残余整改源码结果 commit → 本批证据 commit**。
开工核验：残余整改卡要求的 HEAD=380cb496 一致、工作树 clean、无活动writer、无remote。

## HEAD 与并发差异归属

- **Lab（唯一写仓）**：开工 HEAD `380cb496f30c72128c2cc8e3c88e36924f3c4f2c`（clean、无remote、
  无其他活动writer）→ 源码结果 commit `d4360fdbbd9a83d2830066546edf1827ab424834`
  （tool 0.2.1，含 LR-01..LR-06 修复、RED/GREEN 测试、schema/rule 版本、提案费用更正）
  → 随后的交接证据 commit；交付后 `git status` clean、仍无 remote。
  before→after 的全部差异就是本批修复与交接证据，没有他人改动被 reset/clean/覆盖。
- **IQS（只读）**：本会话期间出现**他人并发 commit**（`2d45452`、`54b01db`、`37b3c11`，
  2026-10-08 19:22–19:28 +0100，其他 lane 的 docs 提交），交付时 IQS HEAD=`37b3c114…`。
  本会话**未在 IQS 产生任何 commit、未修改任何已跟踪文件**，锁定 128 个输入文件 SHA 前后一致；
  上述并发差异全部归属其他 writer，与本交付无关（唯一一次越界见“边界与回退”的披露）。

## 残余整改结论（LR-01…LR-06 同批收口）

| 组 | 修复 |
|---|---|
| LR-01 | `normalize_period` 对 `kind=custom` 完整保留并归一 `start/end`；`_custom_boundary_conflict` 只比较双方明示边界（全等→pass、明示边界不同→fail、缺边界→abstain `custom_boundary_not_stated`/`claim/expected_custom_boundary_missing`）；未知形态照旧abstain；不改旧quarter/half/year与缺year规则、不从关键词补年 |
| LR-02 | `archive_provenance_verifier`：凡 `case.answer` 存在就**独立从锁定归档取答案逐字比较**，与 `answer_sha256` 有无无关；hash 降级为额外校验，空/null/非64hex、缺 `question_id`、question_id指向不存在的答案一律成问题 → 公开replay exit4 且不建输出；chunk 全字段复制绑定保持（改答案+改自digest仍拒） |
| LR-03 | `strict_loads` 增加受控 `parse_float`：解析后非有限（含 `1e400`/`-1e400`、嵌套 object/array）→ 具名 `NonFiniteJSONError`；JSONL 与 staging 回读走同一入口；fixture入口 exit4、无输出无staging；重复键与 NaN/Infinity 常量拒绝保持，正常整数/小数/范围内科学计数法照常 |
| LR-04 | `check_sources`：存在未给出窗口的引用来源时，即使已知窗口全部冲突也**abstain `unknown_source_window_present`** 并在 message 里分别报出未知数/明确冲突数，不伪造未知窗口；全明确冲突仍 fail、有匹配窗口仍 pass、全未知仍 `source_window_not_stated`；独立来源数与片段hash口径不变 |
| LR-05 | `source_kind_for()` 成为唯一来源映射，`_structural_records_for_chunk`/`_answer_records` 全部改用传入 `evidence_kind`（duplicate_json 不再硬编码 historical）；`source_kind_problems()` 校验**整个document每条记录**：synthetic 不得标 historical、未收集 real_source_snippet 不得标 real_snippet（FX-034 现标 `none`）、agent_review_only/no_human_gold 不是 gold |
| LR-06 | `output_cap_tokens_per_request` 与 `generation.output_limit` 统一为 **10000**，按冻结价与输入上限用 Decimal 复算 `per_request_usd`（0.0141 / 0.01218）与 `worst_case_usd_total=0.82296`，`token_reference_estimate_usd_max=0.83`；generator、config、Markdown 表、totals 同步改，测试断言实际生成上限进入公式；`draft_not_signed`/`execution_enabled=false`/`live_not_run=true`、300槽分母、缓存/套餐未知、unknown预约不重发全部保持 |

顺带更正 isolation.md 旧口径：**224次校验 / 127个绑定路径 / 含lock共128个独立文件**
（不是225项）、输入为“按锁只读 IQS”而非“未读取他仓”。

## 既有功能（保持，不重做）

原81方法、总控原9反例、公开34 fixture/42 expectation/350 记录、三归档双新根稳定、
34逐fixture CLI 全部继续通过：本批 **108 passed**（81 + 残余整改新增27）。

## 残余整改前的既有结论（EL-01…EL-06）

| 组 | 修复 |
|---|---|
| EL-01 | `normalize_period` dict 保留 `half/quarter`；kind冲突即矛盾；子期间/年份缺一侧按具体理由 abstain（`claim/expected_period_year_missing` 等）；不靠关键词补年。Q1 vs Q4、H1 vs H2 → fail；`2026H1` vs `H1` → abstain |
| EL-02 | 无期间窗口 → abstain `source_window_not_stated`；无claim目标 → 同报告比较列/同URL不同内容片段互补 pass；仅 claim目标与**全部**引用窗口冲突 → `E_URL_WINDOW_CONFLICT`；`source_counts` URL去重与片段hash分离，独立来源数不因URL复用增加 |
| EL-03 | 全部公共JSON入口经 `strict_loads`（重复键/NaN/Infinity）；fixture路径→exit4、锁定输入→exit2；historical fixture 深度绑定原归档**全字段投影** + `provenance.chunk_sha256`，改 score/rationale 立即被拒 |
| EL-04 | 发布改为 staging（`.temp-roots/staging-<pid>-<uuid>`）写齐 → 逐文件严格回读 → `os.rename` 原子发布；写盘失败清staging、目标不出现、同路径可重试（反例内建重试断言），不是单纯 catch 返回1 |
| EL-05 | 预注册升 `1.1.0`/`draft_not_signed`：60请求×5=**300计划槽**主分母 + sent/not_sent/失败包内/unknown/结构有效/带claim分层，answered-only 仅条件指标；mixed/themed 四组具体题号；题面/身份/截止日 canonical hash；12条冻结query+24搜索共享规则；context与表头/单位约束；逐模型 token 上界×冻结价公式（当时写 0.48276 USD ≤ 0.49，**本批 LR-06 按 `generation.output_limit=10000` 更正为 0.82296 USD ≤ 0.83**，价格与输入上限未变）；检索缓存 key/version/TTL 与模型revision缺口；unknown预约禁自动重发；Phase96差异说明；**`execution_enabled=false`** |
| EL-06 | fixture 回放输出原字节 `input_sha256`、在场答案 `answer_sha256`、semantic 记录 `expected_field/observed_field` 定位；`evidence_kind` 不再被硬编码为 historical、agent 标签 → `agent_review`；校验口径更正为 **224次校验/127不同路径/含lock共128独立文件**；34 fixtures/42 expectations/350 诊断记录；`pyproject` 声明运行依赖 `jsonschema>=4`；artifacts 双hash见下 |

## 版本

`iqs_evidence_lab 0.2.1`；diagnostic schema **1.2.0**；fixture schema **1.1.0**；
`semantic-rules/3`；`structure-rules/3`；`metric-definitions/1`；
`plan_slots/1`；预注册 `1.1.0`（内容更新、schema 未变）。
新旧可比性：`tool.version`、`schema_version`、`rule_versions` 三项同时变化，
新诊断可与 0.2.0/1.1.0/`semantic-rules`旧输出区分；fixture 字节未改，fixture schema 保持 1.1.0。

## 准确入口命令（Lab 根）

```bash
PYTHONPATH=src python -m iqs_evidence_lab replay --input index --output <new_dir>
PYTHONPATH=src python -m iqs_evidence_lab replay --input fixtures/synthetic/FX-001.json --output <new_dir>
PYTHONPATH=src python -m iqs_evidence_lab validate-fixtures
python -m pytest tests/ -q                       # 108 = 81（原54+总控反例9+整改18） + 残余整改27
python -B -X utf8 -m pytest tests/controller/test_remaining_repairs.py -v   # 本批27
python -X utf8 tools/make_fixtures.py            # 确定性重建 fixtures
python -X utf8 tools/gen_proposal_config.py      # 从锁定输入再生预注册配置
```

退出码：0 成功；1 意外/发布失败（staging已清、目标未建、可重试）；2 输入漂移/非严格/
非索引；3 输出目录冲突或越界；4 fixture失败；5 用法错误；6 网络守卫拦截。

## 证据（logs/remediation-2026-10-08/ 与 logs/remaining-repairs-2026-10-08/，原 logs/ 全部保留）

上一批（EL-01…EL-06）：`RED-controller-counterexamples.log`（stash 回 `d87cf71` 快照
复现 **8 failed / 1 passed / 0 error**）、`GREEN-controller-counterexamples.log`（9 passed）、
`final-regression.log`（**81 passed**）、`validate-fixtures.log`、
`replay-index-a/b.log` + `public-cli-runs.json`、8个 `cleanup-receipt-p<pid>.json`。

本批（LR-01…LR-06）在 `logs/remaining-repairs-2026-10-08/`：

- `RED-remaining-repairs.log`：修复前对本批反例复现 **10 failed / 17 passed / 0 error**
  （六项全部真实失败；首批GREEN边界3项当时即通过）。
- `GREEN-remaining-repairs.log`：修复后 **27 passed**。
- `final-regression.log`：`python -m pytest tests/ -q` → **108 passed**（一次集中回归）。
- `validate-fixtures.log`：34 fixtures / 42 expectations / 350 records，`problems=[]`。
- `replay-index-a.log`/`replay-index-b.log`/`public-cli-runs.json`：index×2 + 34 fixture
  = **36/36 exit0**、双根五payload字节一致、128个输入文件前后SHA不变、
  无staging残留、输出根跑完即删。
- `cleanup-receipt-p<pid>.json`：本批逐文件清单+manifest_sha256、
  `links_or_junctions=[]`、`verified_absent=true`、`gaps=[]`。

## 边界与回退

零网络/付费/key读取/下载；IQS等其他仓只读（锁定输入128文件前后SHA一致）；只提交本仓获授权路径；
不创建remote；不写IQS PWF；不自关 L02/G3/F05。
**披露**：会话中一条 shell 重定向 `2>nul` 曾在 IQS 根生成 0 字节未跟踪文件 `nul`，
发现后立即删除；`git status` 恢复为仅预存 `opencode.json`，无已跟踪文件改动、无新 commit。
**回退 = 删除或停用本 Lab 仓**：原三归档、评审、生产策略、公司结果未被修改。
EOL 口径：`artifacts.json`（122条）同时给出工作树原字节 `worktree_sha256`+`eol`
与 `git hash-object --path` 的 `git_blob_oid`，并按 `diff_vs_result_commit` 分类
（对本轮源码结果 commit）：`identical=95`、`not_in_result_commit=17`（证据文件，随证据
commit入库）、`updated_after_result_commit=10`（源码结果后更新的交接文件）；
`eol_counts` 记录102个CRLF文件、20个LF文件。上一批总控在旧快照上测得的37项差异为纯
CRLF/LF——本工具如实申报两类hash与EOL标记，**不称内容篡改**，不做全仓行尾改动；
导出/恢复方法见 `artifacts.json.export_restore`。
交接 shape 校验：`scripts/parallel_handoff_cli.py --catalog .../2026-10-07-wave2/manifest.json
--package-id EVID-LAB-01 --input <lab handoff.json>` → `status=valid`（只读执行、未写IQS，
证据 `logs/remaining-repairs-2026-10-08/handoff-shape-validation.json`）。

## 已做 / 未做

已做（上一批）：六组修复、9反例 RED→GREEN、81集中回归、公开CLI三归档/34fixture重放、
双根稳定与失败路径、严格清理回执、预注册实质冻结（非执行）。
已做（本批）：LR-01…LR-06 同批收口、27反例/边界 RED 10失败 → GREEN 27通过、
108集中回归、公开CLI 36/36 重放、版本/规则/schema 同步升级、isolation 口径更正、
两批独立清理回执。
未做（`not_run`，留总控）：新真实搜索/模型实验与60/24草案执行、Phase96重跑、
人类gold/inter-rater校准、真实来源短片段、生产采用、总控集中回验；
L02完整校准/G3/F05、TH/IN/L03 与完整事实/人类gold **不因本批测试通过而放行**。
预注册状态 = **draft_not_signed**（未签核，不是已签预注册；接收草案≠已签预注册）。
