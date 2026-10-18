# EVIDENCE-TIMELINE-11｜薄证据来源时点与截止日一致性审计

唯一工作根 **C:/Users/郑曾波/Projects/iqs-evidence-timeline-lab**（编制时不存在）；分支 `codex/evidence-timeline-11`；module `iqs_evidence_timeline`。

先读[本批共同规范](handoff-rules.md)、[输入锁](inputs.lock.json)、[三包共同契约 §1–§3/§5](../2026-10-18-mainline-support/integration-contract.md)。

## 目标与真实边界

主线反复遇到同一类缺陷：`published_at` 缺失、`retrieved_at` 被当成信息时点、历史问答用今天抓取的页面冒充当时检索、`information_cutoff` 与证据 epoch 逆序、日期与 UTC 时间戳混用。EVID-REF-02 已明确 `retrieved_at` 不能用文件 mtime 或历史 `answered_at` 替代，新增取证时间不能伪装历史检索时间（`2026-10-10/EVID-REF-02.md` 第 28、52 行）。

本包交付**时点一致性审计器**：吃薄证据集合（source rows + claim/period + cutoff/epoch），输出逐来源逐通道的判定与完整分母。只判"时间字段互相矛盾或不可评估"，不判来源真假、是否支持 claim、网页是否仍在线。

明确不做：不联网、不抓取、不打 URL 探活；不做证据支持度/金融真值（属 CLAIM-GUARD 与独立金融评审）；不建第二个参考包（EVID-REF-02 拥有）；不做摘要字段保真（SUMMARY-LOSS-10）；不做关系配对（RELATION-DELTA-10）；不写 StockWiki 观察、不迁移库。

## 为什么可独立、不与在跑工作重叠

- 三张已派卡分别做：`RELEASE-DIFF-10`（module release 版本差异与历史兼容）、`SUMMARY-LOSS-10`（摘要字段保真/遗漏）、`RELATION-DELTA-10`（跨时点关系观察——item 级精确配对、scope 与 method 校验、change classification、以及"未重观测≠终止"）。**本包不比较两次快照、不配对 item、不分类变化**，只审**单次证据行内部**的 URL/标题/发布日期/抓取时间/截止日/epoch 一致性，输入与输出协议均不同，也不消费其 snapshot。
- 与 EVID-REF-02 边界：那只产出候选参考事实与 answer 评测；本包不产事实、不评分，可对任何来源集合运行。
- 输入全是本仓 tracked 的 source index/catalog/参考事实 JSON，离线可独立完成。

## 精确写范围

本 Lab 内：`README.md`、`.gitignore`、`pyproject.toml`、`src/iqs_evidence_timeline/`、`schemas/`、`content/`、**`rules/`**、`fixtures/`、`tests/`、`tools/`、**`vendor/`**、`.tmp/`、`docs/handoff/EVIDENCE-TIMELINE-11/`。

## 冻结输入

source_commit `4e001cd18d229a60de54d56ce6ecd23f8bc00cae`；`git cat-file blob <oid>` 读取后复制到 **`vendor/iqs/<path>`**（只读）。

| path（vendor 前缀 `vendor/iqs/`） | blob OID | bytes | sha256 |
|---|---|---:|---|
| docs/implementation/experiments/alphabet-objective-reference-2026-10-16.json | 5f054e74424ed59073ecbc08188b04b94b585d72 | 5124 | 3846cad65c5b1e2aa819b5a52a95711d05b2f5f83ce3f4def08007ec6a49980d |
| docs/implementation/experiments/artifacts/b01-improved-2026-10-07/source-index.json | 45c6b8276c8efc029476863980a734eca528a3c7 | 127785 | 4563ca2bc558cb72d9f9c2cda34f88386532114064d086221c36227a3ae1cc44 |
| docs/implementation/experiments/artifacts/accuracy-first-2026-10-07/followup/source-catalog.json | 8e34d980635173546287281a756c3170ad4ff16d | 84827 | cb21c2269851a690cff35f810daf126d7bc2a8a5878e8a78bf7dcc7f9d568b8b |
| docs/implementation/experiments/artifacts/accuracy-first-2026-10-07/main/source-catalog.json | 1865cc9f87290efd6e020f6c0aeee008b86754d9 | 172713 | 5e5fad8218d03fb984e40553e25ea15ad6e038a6d5c8edfa8bc32f070991c054 |
| docs/implementation/contracts/receipt-Q02.json | 22a87db7c760e04af66ae9387b811959085d2d3c | 16742 | cb1c40af44a629e316b7812c13b0fd6db682bddf2224e59216e1b8076152929f |
| schemas/observation-v1.2.schema.json | 574d06d794a20f7e1d62b3e8b8b4109e9fc4f61b | 7803 | 09079ded0a16ada01676d1b87bc905dbb71e6c2e353de0545155868c13a02ef3 |

**总控补冻占位**：`docs/handoff/EVIDENCE-TIMELINE-11-evidence-pack.json`——EVID-REF-02 后续 30 槽参考包的 `source_refs`。当前未以 tracked 形式存在；总控有记录后补冻并给 blob OID。**不得用 `runs/` 下未 tracked 文件或真实库代替。**

## 交付物

1. `schemas/evidence-timeline-request-1.0.0.schema.json`（`protocol=iqs.evidence_timeline_request/1.0.0`、`request_id`、`claim_ref{claim_id,period_start|null,period_end|null,information_cutoff,evidence_epoch|null}`、`observed_at_utc`、`sources[]`）、`schemas/evidence-timeline-report-1.0.0.schema.json`。
2. 审计引擎（严格日期/时间戳解析、时区归一、四通道规则）。
3. `rules/timeline-rules.json`（每条 rule_id 绑定字段与依据文件行 + `false_positive_note`）、`content/casebook.json`（≥24 例）、`fixtures/`（合成证据集 + 真实文件转换器输出）、CLI、测试、`integration-map.md`、交接文件集。

`sources[]` 每行闭合：`source_id,url,title|null,published_at|null,retrieved_at|null,document_family|null,source_scope|null,snippet_sha256|null,snippet_chars|null,provider|null,claim_ids[]`。保留原字符串与精度（date-only 与 timestamp 分开标注），不补齐时分秒或时区。

## 公开接口与输出协议

```powershell
python -B -X utf8 -m iqs_evidence_timeline convert --reference vendor/iqs/docs/implementation/experiments/alphabet-objective-reference-2026-10-16.json --claim fixtures/claims/c-alphabet.json --output .tmp/proj-alphabet
python -B -X utf8 -m iqs_evidence_timeline convert --source-index vendor/iqs/docs/implementation/experiments/artifacts/b01-improved-2026-10-07/source-index.json --claim fixtures/claims/c-b01.json --output .tmp/proj-b01
python -B -X utf8 -m iqs_evidence_timeline convert --receipt vendor/iqs/docs/implementation/contracts/receipt-Q02.json --source-catalog vendor/iqs/docs/implementation/experiments/artifacts/accuracy-first-2026-10-07/main/source-catalog.json --claim fixtures/claims/c-mixed.json --output .tmp/proj-mixed
python -B -X utf8 -m iqs_evidence_timeline audit --input .tmp/proj-b01/request.json --input-root .tmp/proj-b01 --source-root vendor/iqs --lock inputs.lock.json --output .tmp/timeline-b01
python -B -X utf8 -m iqs_evidence_timeline evaluate --cases content/casebook.json --input-root fixtures --source-root vendor/iqs --lock inputs.lock.json --output .tmp/eval-01
```

`convert` 有四个可选来源参数（至少一个）：`--source-index`、`--source-catalog`、`--reference`、`--receipt`；每个参数只接受 `vendor/iqs/` 或 `fixtures/` 下的安全相对路径并按锁校验。

报告 `iqs.evidence_timeline_report/1.0.0`：顶层共同字段；payload 闭合 `request_sha256,sources_total,assessment,channels,findings,counts,limitations`。

- `channels` 固定四通道，互不替代：`publication_time`（published_at vs period/cutoff）、`retrieval_time`（retrieved_at vs published_at/cutoff/epoch）、`period_alignment`（period_start/end vs published_at）、`granularity`（date-only vs timestamp、时区、epoch 顺序）。
- 每来源每通道恰一行：`source_id,channel,status,reason_code,observed,expected,evidence_pointer`；status 只可 `consistent|conflict|unassessable`。**缺失字段是 `unassessable`，不是 conflict，也不能算一致。**
- `reason_code` 固定枚举至少含：`published_after_information_cutoff`、`retrieved_before_published`、`retrieved_after_cutoff`、`retrieved_before_period_end`、`publication_time_missing`、`retrieval_time_missing`、`timestamp_not_utc`、`date_granularity_mixed`、`epoch_after_information_cutoff`、`cutoff_before_period_end`、`duplicate_source_id`、`snippet_reuse_across_urls`、`period_reference_mismatch`、`future_timestamp`。
- `counts`：`sources_total = consistent_channels + conflict_channels + unassessable_channels`（按通道行），另给 `sources_with_any_conflict`；不等即报 `counts_not_conserved` 并保留原值。
- `assessment`：任一 conflict → `deterministic_time_conflicts_found`；否则任一 unassessable → `unassessable`；否则 `time_consistent`。**`time_consistent` 不表示来源真实、支持 claim 或证据充分。**
- `limitations` 固定含 `network_verification_not_performed=true`、`source_authenticity_not_asserted=true`、`claim_support_not_evaluated=true`、`web_page_not_fetched=true`。

时区与精度：带偏移时间戳归一到 UTC 比较但保留原串；无偏移的裸时间戳按 `timestamp_not_utc` 处理（除非请求显式声明时区且声明进入报告）；`YYYY-MM-DD` 与带时分秒混用报 `date_granularity_mixed`，同日仍可比较。`future_timestamp` 以请求 `observed_at_utc` 为界，不用系统时钟（保证确定性）。

退出码（本批统一采用 §2）：**0** 审计完成；**1** 仅 `evaluate` 与冻结预期不符；**2** 输入/schema/重复键/非法日期/哈希漂移/用法错误/输出已存在或越界；**3** 内部不闭合、网络或凭据访问尝试、意外内部错误。

## 确定性离线验收

真实基线（编制时核对，实施时复算，不硬编码）：`alphabet-objective-reference` 共 10 条 fact，`information_cutoff=2026-10-13`，`published_at` 分布为 **2026-02-04 共 6 条、2026-02-05 共 4 条**，其中 **3 条 `period_start=null`**（`ALPH-MAIN-CASH25`、`ALPH-MAIN-MKTS25`、`ALPH-MAIN-DEBT25`，均 `period_end=2025-12-31`）；该文件无 `retrieved_at`。`source-index.json` 条目 `published_at` 均为 `null`，`retrieved_at` 为 `2026-10-07T…+00:00` 形式。

| Case | 必须证明 |
|---|---|
| ET-01 | 真实 `source-index.json`：顶层是 **13 个 pool**，需展开内层 `sources[]`；`sources_total` 按**嵌套 source 行**计（实测 234，由实现读出，不硬编码），不是 13。`published_at=null` 的行逐条 `publication_time_missing/unassessable` |
| ET-02 | 真实 `alphabet-objective-reference`：`information_cutoff=2026-10-13`、6 条 `2026-02-04` + 4 条 `2026-02-05`、其余 period 组合判 `time_consistent`；无 `retrieved_at` → `retrieval_time` 通道 10 行全 `unassessable`；`period_start=null` 的 **3 条**（CASH25/MKTS25/DEBT25）在 `period_alignment` 通道 `unassessable` 而非 conflict，该通道因此有 3 条 unassessable、7 条 consistent |
| ET-03 | `published_at` 晚于 `information_cutoff` → `published_after_information_cutoff`，其他通道结果保留 |
| ET-04 | `retrieved_at < published_at` → `retrieved_before_published`；`retrieved_at` 晚于 cutoff 但 claim 为历史 → `retrieved_after_cutoff` |
| ET-05 | 真实混合输入：`receipt-Q02.json`（唯一 `retrieved_at=2026-09-25`，date-only）与 `main/source-catalog.json`（`retrieved_at` 带 UTC 时间戳）经 `--receipt`+`--source-catalog` 进同一请求 → 仅 receipt 行 `date_granularity_mixed`，时间戳行不报；receipt 的日期**不得被补成 00:00:00Z**，报告保留原串 |
| ET-06 | `evidence_epoch` 晚于 `information_cutoff` → `epoch_after_information_cutoff`；cutoff 早于 `period_end` → `cutoff_before_period_end` |
| ET-07 | 同一 `source_id` 两行不同 url/hash → `duplicate_source_id`；不同 url 复用同一 `snippet_sha256` → `snippet_reuse_across_urls` |
| ET-08 | URL 年份、标题年份、`period_end` 三处同时可解析且互斥时才报 `period_reference_mismatch`；任一不可解析改 `unassessable` |
| ET-09 | 请求 `observed_at_utc` 之后的时间戳 → `future_timestamp`（改机器时间不改结果） |
| ET-10 | `counts` 四通道守恒；构造缺行/多行必报 `counts_not_conserved` |
| ET-11 | 负例：重复 JSON 键、NaN、`2026-02-30`、未知 protocol、输入篡改 → exit2 无输出；已存在/越界 → exit2；`evaluate` 不符 → exit1 |
| ET-12 | 同一请求两次新根运行 payload 字节相同；零网络（含禁止 URL 探活）、零子进程外呼、临时根成功与失败都清理 |

≥24 个单测场景；集成用 2 个真实 source 文件 + 1 个真实参考事实 + 1 个 receipt；E2E 走公开 CLI 到新结果再 `validate` 读回，含随机 cwd、中文空格路径。工具不得读 `fixtures/expected/`，不得访问任何 URL。

## 禁止捷径

不得伪造回执、评分或"来源已核实"；不得为凑 `time_consistent` 补填 `published_at`/`retrieved_at`/时区；不得用文件 mtime、`answered_at` 或当前时间当检索时间；不得联网探活或抓页；不得跳过 hooks 或 `--no-verify`；不得复制真实 namespace、答案正文或密钥；不得写生产库/名单/观察；不得碰他人 Lab；不得 `git add -A`。

## 独立审查要求

按 `integration-contract.md` §5：真正不同 reviewer 全量核规则、日期/时区解析、缺失与冲突区分、分母守恒、真实文件复现，并自带 2 个作者未给反例（如"只缺 published_at 但其余齐全"的正常限定、多通道同时冲突的排序）。`docs/handoff/EVIDENCE-TIMELINE-11/review/` 必含 `invocation-evidence.json`、`round-XX.*`、`fixes.json`、`final.json`（`verdict=passed`、`open_findings=[]`、`reviewed_commit`）。

## 交回

本仓 `docs/handoff/EVIDENCE-TIMELINE-11/`：见 `handoff-rules.md` 第一节文件集（含 `rules/`、`report.md`、`tests.json`、`cleanup.json`、`review/`）。先 payload commit，再 metadata-only commit。

## 风险与已知未知

- **真实语料偏窄**：tracked 文件里 `published_at` 大量为 null，`retrieved_at` 集中在 2026-10-07 附近；ET-03/04/06 依赖合成 fixture（必须标 `synthetic`），只能证明规则可执行，不证明真实分布。
- **启发式**：`period_reference_mismatch` 需三处年份同时可解析，误判风险高；实现必须允许 `unassessable` 并写 `false_positive_note`。
- **未知**：`source-catalog` 的 `pool_file_sha256` 指向的证据池文件不在输入内，该关系标 `unassessable`；EVID-REF-02 后续 evidence pack 的真实字段集合未核，补冻后需重跑基线。
