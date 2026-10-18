# DELIVERY-AUDIT-11｜交付包哈希闭包与薄证据泄漏审计

唯一工作根 **C:/Users/郑曾波/Projects/iqs-delivery-audit-lab**（编制时不存在）；分支 `codex/delivery-audit-11`；module `iqs_delivery_audit`。开工若该根已存在且非空，只读核对是否本卡接续，无法确认即记 `writer_conflict` 并停止写入。

先读[本批共同规范](handoff-rules.md)、[输入锁](inputs.lock.json)、[共同契约](../2026-10-18-mainline-support/integration-contract.md)、[既有预检 CLI](../../../../../scripts/parallel_handoff_cli.py)。

## 目标与真实边界

总控每次收到 Lab 交付，都需要人工核对"清单是否自洽、哈希是否闭合、有没有把不该外发的正文/库/凭据带进来、handoff 自述与实际文件是否一致"。这些核对现在靠人读，规则散在 `handoff-rules.md`、`integration-contract.md` §4 与各卡里，重复且易漏。

本包交付一个**确定性的交付包审计器**：输入一个交付目录（其中含 `handoff.json`、`inventory.json`、`artifacts.json` 或等价清单与工件），输出逐文件、逐规则的可复算报告。它只做四件事：形状与既有 CLI 一致、清单哈希闭包、禁止内容类别检测、自述与工件一致性。

明确不做：不鉴定授权/真值/金融准确性/来源真实性/合规；不替代独立人工或 agent 审查；不执行交付里的代码或安装依赖；不读外部网络；不判定主线能否发布。

## 为什么可独立、不与在跑工作重叠

- 已派发三包分别处理 module release 差异、摘要字段保真、关系观察变化，**都不审交付目录**；本包不消费它们的输入与结论。
- 与 CLAIM-GUARD（指标口径与证据蕴含）、SESSION-PACK（上下文打包）、REVIEW-CAL（评审校准）层次不同：本包只看**文件层**的闭包与泄漏，不解释语义。
- 与主线 publication/store-ID 节点无交集：本包不读任何 owner 库、不判 namespace、不改发布指针。
- 输入全部来自本仓 tracked blob 与调用方显式给出的交付目录，可单独立项完成。

## 精确写范围

本 Lab 内：`README.md`、`.gitignore`、`pyproject.toml`、`src/iqs_delivery_audit/`、`schemas/`、`content/`、`fixtures/`、`tests/`、`tools/`、`.tmp/`、`docs/handoff/DELIVERY-AUDIT-11/`。其他一切只读：IQS/PWF、`runs/`、StockQAbyLLM、StockWiki、company-wiki、既有 `iqs-*-lab` 和另两包。用 `python -B`，隔离 TEMP/TMP/TMPDIR 与 PYTHONPATH，禁止在源仓旁生成缓存。

## 冻结输入

来自本仓 Git 对象，source_commit `4e001cd18d229a60de54d56ce6ecd23f8bc00cae`；用 `git cat-file blob <oid>` 读二进制 stdout 后复制到本 Lab `vendor/iqs/`，逐项核对后写 `inputs.lock.json`（`iqs.support_input_lock/1.0.0`）。

| path | blob OID | bytes | sha256 |
|---|---|---:|---|
| docs/implementation/parallel-lanes/handoff.schema.json | 6d77c9c960f3d790f0251f6c0e365cb3db0f0313 | 5598 | ed38a65aafed82649a071acbc9e6ee5b47c92120ad958713db4d7261a4b15c0e |
| scripts/parallel_handoff_cli.py | 18eaf979d4f8717bcc1ce04a57544944a62e6f28 | 7005 | 21e58aa56fe4680673c209cef88f8eaa5f67aad47cdfc7d1dd3177766ef28bda |
| docs/implementation/parallel-lanes/packages/2026-10-10/handoff-rules.md | 0d794f6c25c3b616f6b3ac4f3e6f3247a64c1157 | 6997 | 2793c3ebf7491080ba8bcc67539efe79707ae2e12bdd3278cb3b32dc86092fa0 |
| docs/implementation/parallel-lanes/packages/2026-10-18-mainline-support/integration-contract.md | 179473a4a420bf571b8b2bfe800798815b6c44fe | 10270 | a9ea665ad2fb331d26004f5d42c8b6330daab7c23c61977de32b1cce05d76921 |
| docs/implementation/intake/QA-NET-01/2026-10-07/owner-delivery/handoff.json | 8facebf69b55da4afc292e44e341e33db02f6f6f | 14363 | d9d7b2692167b4791255ffe66ab4cbed9e23df41a00f5598ae39634d6ce74729 |
| docs/implementation/intake/SW-REPAIR-02/2026-10-08/worker/handoff.json | 7dc33d94c0a31a50715d516055a12042decaf5f3 | 9235 | 9599f84188d64c5b0428ff5a04f054ef45c3f7792386b4ea0a48f12dd8b00048 |
| docs/implementation/intake/EVID-LAB-01/2026-10-08/worker/handoff.json | cc995b5d73aa70561da96362a2aa9acd004ad219 | 6922 | 97df817ceab3fc4c5559785811fb3f379cd03876dd944c15a8c49ea6f08d6a3a |

**unsupported（不得当输入）**：`docs/implementation/intake/parallel-packages/2026-10-10/received-handoff/{EVID-REF-02,FACT-CONTENT-01}/handoff.json` 在工作树存在但 `git ls-files --error-unmatch` 报 `did not match any file(s) known to git`，即未 tracked、无 blob OID。需要它们作语料时由总控先提交并出新锁，本卡不自行采用。

## 交付物

1. `rules/rules.json`：每条规则含 `rule_id`、`kind`（shape/hash/leak/declaration）、`severity`、`source_ref`（依据文件 + 行号或字段 pointer）、`description`、`false_positive_note`。至少覆盖：清单缺文件、清单多文件、bytes/sha256 不符、清单含自身 hash、清单含最终 review/handoff 元数据、路径越界或重解析点、重复 JSON 键、1 MiB 上限、`status=complete` 而 `result_commit=null`、`lane/package/task_ids` 与 catalog 不符、`review.status` 非 `passed` 却自述可交付、临时根未清理。
2. `schemas/bundle-audit-request-1.0.0.schema.json`、`schemas/bundle-audit-report-1.0.0.schema.json`（Draft 2020-12，`additionalProperties=false`，required 全列，禁 NaN/重复键）。
3. `content/casebook.json`：≥24 个有独立预期的案例（见验收），expected 与工具分离存放。
4. `fixtures/`：合成交付包——正常包、缺文件包、哈希篡改包、自指包、泄漏包（每类一个）、`traceability` 无关的正常包；`catalog.json` 记录相对路径/bytes/sha256/`synthetic=true`。
5. CLI 与测试；`integration-map.md` 说明总控在哪一步调用、能替代哪些人工核对、哪些必须人工。

## 公开接口与输出协议

```powershell
python -B -X utf8 -m iqs_delivery_audit audit --input <bundle-root> --input-root <root> --source-root vendor/iqs --lock inputs.lock.json --output .tmp/audit-01
python -B -X utf8 -m iqs_delivery_audit validate --input <request.json> --input-root <root> --source-root vendor/iqs --lock inputs.lock.json
python -B -X utf8 -m iqs_delivery_audit evaluate --cases content/casebook.json --input-root fixtures --source-root vendor/iqs --lock inputs.lock.json --output .tmp/eval-01
```

报告 `iqs.bundle_audit_report/1.0.0` 顶层用共同字段：`protocol,package_id,input_lock_sha256,data_kind=offline_candidate,production_qualified=false,source_refs,limitations,payload`。payload 闭合：`bundle_root_sha256,inventory`（`declared_count,actual_count,missing_paths,extra_paths,hash_mismatches,self_reference_hits,metadata_cycle_hits`）、`foundings`（数组，每项 `finding_id,rule_id,kind,severity,relative_path,byte_offset_or_null,observed,expected,evidence_sha256`）、`oracle_agreement`（本包与既有 CLI 在同一 handoff 上的判定是否一致）、`counts`（`files_total,files_checked,files_skipped,findings_by_kind`，互斥且和等于 files_total）、`manual_review_required=true`。

禁止内容检测只报确定性证据，不报推论：`answer_body`（`answer/answer_text/answers` 等键的非空正文形状）、`hidden_thinking`（`reasoning_content/thinking` 非空）、`full_page_html`（`<!DOCTYPE html`/`<html` 且超过阈值字节）、`database_copy`（`SQLite format 3\0` 魔数或 `.sqlite/.db` 二进制）、`credential_marker`（`sk-` 要求左侧 token 边界，避免把 `risk-adjusted`、`task-output`、`mask-based`、`disk-failure` 误杀——这是真实修复过的误报类别，见 `task_plan.md` 2026-10-18「修复真实金融文字被密钥检查误拒」）、`lease_or_grant_token`（长十六进制/无约束 token 需与声明字段绑定才报）、`api_raw_body`（`choices/usage/prompt_tokens` 形状的原始响应）。

退出码：0=审计完成（发现泄漏/不符仍是成功诊断，不等于包合格）；2=输入/schema/重复键/输入 hash 漂移；3=输出已存在或越界；4=内部引用不闭合；5=用法；6=检测到网络或凭据访问尝试；意外失败 1 并保留错误。输出目录 exclusive，不覆盖、不跟随 reparse。

## 确定性离线验收

| Case | 必须证明 |
|---|---|
| DA-01 | 三个真实 tracked handoff 与既有 CLI 的 `validate` 判定逐条一致（不一致即失败），并保留双方原输出 |
| DA-02 | 合成正常包：清单闭合、无 finding、`counts` 与 files_total 相等 |
| DA-03 | 清单少列 1 个文件 / 多列 1 个不存在文件，各报 `missing_paths`/`extra_paths` |
| DA-04 | 工件改 1 字节：`hash_mismatches` 精确指 path 与原期望 sha，不因类型或大小相同而放过 |
| DA-05 | 清单含自身 sha 或含 `final.json`/`handoff.json` 自身 → `self_reference_hits`/`metadata_cycle_hits`，不进入无限重算 |
| DA-06 | 路径 `../`、绝对盘符、反斜线、重解析点越界被拒，且不读外部文件 |
| DA-07 | 7 类禁止内容各 1 个正例全部检出，证据含 rule_id 与 byte offset |
| DA-08 | 4 个已修复的误报词（含 `risk-adjusted`）不产生 `credential_marker` |
| DA-09 | `status=complete` 且 `result_commit=null`、`review.status=changes_requested` 均报 declaration finding |
| DA-10 | 重复 JSON 键、NaN、>1 MiB 输入 → exit2 且无输出目录 |
| DA-11 | 同一 bundle 两次新根运行 payload 逐字节相同（幂等），输出排序稳定 |
| DA-12 | 全程零网络、零子进程外呼、零付费；临时根失败与成功路径都清理，日志保留 |
| DA-13 | 真实语料上 `files_skipped` 有明确理由，不缺行、不把跳过算通过 |

最少 24 个单测场景覆盖上述风险，再做集成（真实 handoff 语料 + 本 Lab API）与真实 CLI E2E（随机 cwd、中文空格路径）。工具不得读 `fixtures/expected/`；`evaluate` 在被测输出生成后才读期望。
## 禁止捷径

不得伪造回执、评分、测试通过数或 finding 数量；不得跳过 hooks 或 `--no-verify`；不得复制真实 namespace/真实库/答案正文/密钥进本仓；不得把真实 tracked handoff 当"通过"证据而不核 blob；不得写生产 DB、名单、发布指针或他人 Lab；不得 `git add -A`；不得付费调用或联网补料；不得用"未发现"的结论替代合规或安全结论。

## 独立审查要求

按[共同契约 §5](../2026-10-18-mainline-support/integration-contract.md)：作者必须调用**真正不同的独立 reviewer agent** 全量审查规则依据、检测器边界、oracle 一致性、离线与清理，并**自带至少 2 个作者未给的样例**（1 个泄漏、1 个正常限定）复测。`docs/handoff/DELIVERY-AUDIT-11/review/` 必含 `invocation-evidence.json`（作者与 reviewer id 不同、UTC 调用时间、可打开引用；缺项 null 并说明）、`round-XX.json|md`、`fixes.json`（逐项 commit 与复验）、`final.json`（`protocol=iqs.support_review/1.0.0`、`verdict=passed`、`open_findings=[]`、`reviewed_commit`）。未 `passed` 不得交接。

## 交回

本仓 `docs/handoff/DELIVERY-AUDIT-11/`：`handoff.json`（1.0.0 形状，`lane_id=iqs`，`status=complete|partial|blocked`）、`summary.md`、`artifacts.json`、`interfaces.md`、`case-map.md`、`logs/`、`isolation.md`、`planning/`，另加 `rules/rules.json`、`report.md`、`tests.json`、`cleanup.json`、`inventory.json`、`review/`。先交 payload commit，再交 metadata-only commit；`complete` 只表示本卡范围完成。

## 风险与已知未知

- **误判风险**：泄漏检测必然是启发式。缓解：只报确定性证据、写 `false_positive_note`、`manual_review_required=true`，绝不自动判"安全"。
- **oracle 漂移**：若总控日后升级 `parallel_handoff_cli.py`，本包判定可能与新形状不一致。缓解：锁定 blob OID，不一致时输出 `oracle_agreement=false` 并以锁定版本为准。
- **未知**：本卡未核总控未来是否为 2026-10-10 两个 received-handoff 补提交（现为 untracked）；也未核 Lab 交付目录的实际文件名变体（除本文列出的规范文件外）——实施时以 `integration-contract.md` §4 为准，出现未列出文件按 `extra_paths` 报而不猜语义。
