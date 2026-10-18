# DELIVERY-AUDIT-11｜交付包哈希闭包与薄证据泄漏审计

唯一工作根 **C:/Users/郑曾波/Projects/iqs-delivery-audit-lab**（编制时不存在）；分支 `codex/delivery-audit-11`；module `iqs_delivery_audit`。开工若该根已存在且非空，只读核对是否本卡接续，无法确认即记 `writer_conflict` 并停止写入。

先读[本批共同规范](handoff-rules.md)、[输入锁](inputs.lock.json)、[交接 schema](../../handoff.schema.json)、[既有预检 CLI](../../../../../scripts/parallel_handoff_cli.py)。

## 目标与真实边界

总控每次收到 Lab 交付，都要人工核对"清单是否自洽、哈希是否闭合、有没有把不该外发的正文/库/凭据带进来、handoff 自述与实际文件是否一致"。规则散在 `2026-10-10/handoff-rules.md` 与既有 CLI 里，重复且易漏。

本包交付**确定性交付包审计器**：输入一个交付目录（含 `handoff.json`、`artifacts.json` 与工件），输出逐文件逐规则的可复算报告。只做四件事：与既有 CLI 的形状判定一致、清单哈希闭包、禁止内容类别检测、自述与工件一致性。

明确不做：不鉴定授权/真值/金融准确性/来源真实性/合规；不替代独立 reviewer；不执行交付里的代码、不装依赖；不联网；不判主线能否发布。

## 为什么可独立、不与在跑工作重叠

- 已派发三包分别处理 module release 差异、摘要字段保真、关系观察变化，**都不审交付目录**；本包不消费其输入与结论。
- 与 CLAIM-GUARD（指标口径/蕴含）、SESSION-PACK（上下文打包）、REVIEW-CAL（评审校准）层次不同：本包只看**文件层**闭包与泄漏。
- 与主线 publication/store-ID 节点无交集：不读 owner 库、不判 namespace、不改发布指针。

## 精确写范围

本 Lab 内：`README.md`、`.gitignore`、`pyproject.toml`、`src/iqs_delivery_audit/`、`schemas/`、`content/`、**`rules/`**、`fixtures/`、`tests/`、`tools/`、**`vendor/`**、`.tmp/`、`docs/handoff/DELIVERY-AUDIT-11/`（均已列入 `manifest.json` 的 `authorized_relative_paths`）。其他一切只读。

## 冻结输入

source_commit `4e001cd18d229a60de54d56ce6ecd23f8bc00cae`；`git cat-file blob <oid>` 读取后复制到 **`vendor/iqs/<path>`**（保持相对目录，只读）。`inputs.lock.json` 用 `iqs.support_input_lock/1.0.0`，逐条含 `vendor_path`。

| path（vendor 前缀 `vendor/iqs/`） | blob OID | bytes | sha256 |
|---|---|---:|---|
| docs/implementation/parallel-lanes/handoff.schema.json | 6d77c9c960f3d790f0251f6c0e365cb3db0f0313 | 5598 | ed38a65aafed82649a071acbc9e6ee5b47c92120ad958713db4d7261a4b15c0e |
| scripts/parallel_handoff_cli.py | 18eaf979d4f8717bcc1ce04a57544944a62e6f28 | 7005 | 21e58aa56fe4680673c209cef88f8eaa5f67aad47cdfc7d1dd3177766ef28bda |
| docs/implementation/parallel-lanes/packages/2026-10-10/handoff-rules.md | 0d794f6c25c3b616f6b3ac4f3e6f3247a64c1157 | 6997 | 2793c3ebf7491080ba8bcc67539efe79707ae2e12bdd3278cb3b32dc86092fa0 |
| docs/implementation/parallel-lanes/packages/2026-10-18-mainline-support/integration-contract.md | 179473a4a420bf571b8b2bfe800798815b6c44fe | 10270 | a9ea665ad2fb331d26004f5d42c8b6330daab7c23c61977de32b1cce05d76921 |
| docs/implementation/intake/QA-NET-01/2026-10-07/owner-delivery/handoff.json | 8facebf69b55da4afc292e44e341e33db02f6f6f | 14363 | d9d7b2692167b4791255ffe66ab4cbed9e23df41a00f5598ae39634d6ce74729 |
| docs/implementation/intake/SW-REPAIR-02/2026-10-08/worker/handoff.json | 7dc33d94c0a31a50715d516055a12042decaf5f3 | 9235 | 9599f84188d64c5b0428ff5a04f054ef45c3f7792386b4ea0a48f12dd8b00048 |
| docs/implementation/intake/EVID-LAB-01/2026-10-08/worker/handoff.json | cc995b5d73aa70561da96362a2aa9acd004ad219 | 6922 | 97df817ceab3fc4c5559785811fb3f379cd03876dd944c15a8c49ea6f08d6a3a |
| docs/implementation/parallel-lanes/packages/2026-10-07/manifest.json | f306e5bda0f153cc7e9ad5735a780429c05ae4d6 | 1865 | 9a7662e61f22e274ebabab2887682bd48322d32e929e4480211a381c5d2e78b7 |
| docs/implementation/parallel-lanes/packages/2026-10-07-wave2/manifest.json | 3ef85eac41ae16172713810928aa4987b5d7e0eb | 2243 | b0534f7e7048cf76edfb28f035486263b7629cdf75d3ac12391c2cf1fe9e45d7 |

**unsupported（不得当输入）**：`docs/implementation/intake/parallel-packages/2026-10-10/received-handoff/{EVID-REF-02,FACT-CONTENT-01}/handoff.json` 工作树存在但 `git ls-files` 报 pathspec 不匹配（未 tracked、无 blob OID）。需其作语料时由总控先提交出新锁。

## 协议与 catalog 的实际用法

交接协议只用 [handoff.schema.json](../../handoff.schema.json) 1.0.0；`handoff.json` 不写 `payload_commit`/`reviewed_commit`/`inventory_ref`，本批不产 `input-catalog.json`（详见 `handoff-rules.md` 第一节）。

**catalog 约束与 DA-01 的可行路径**：`scripts/parallel_handoff_cli.py` 以**自身路径**推 `ROOT`（`Path(__file__).resolve().parents[1]`），再定 `LANE_DIR=ROOT/docs/implementation/parallel-lanes`、`package_dir=LANE_DIR/packages`，只要求解析后的 catalog `is_relative_to(package_dir)`。把冻结的 `scripts/parallel_handoff_cli.py` 与 `docs/implementation/parallel-lanes/handoff.schema.json` 一并复制到 `<lab>/vendor/iqs/`（保持相对路径）后，`ROOT` 即 `vendor/iqs`，冻结 catalog 位于 `vendor/iqs/docs/implementation/parallel-lanes/packages/...`，仍满足包含关系。**因此 Lab 内可单段离线执行 `--catalog`，不依赖总控先跑一遍。**

DA-01 以**单段为主**：Lab 用冻结 CLI + 冻结 catalog + 冻结 handoff 直接运行下表三例并逐字段比对；总控在 IQS 根复跑为**可选交叉核对**，不作为 Lab 的阻塞前置。

| package_id | catalog | input | 期望 exit | 期望 verdict |
|---|---|---|---:|---|
| QA-NET-01 | vendor/iqs/docs/implementation/parallel-lanes/packages/2026-10-07/manifest.json | vendor/iqs/docs/implementation/intake/QA-NET-01/2026-10-07/owner-delivery/handoff.json | 0 | `valid`，errors=[] |
| SW-REPAIR-02 | vendor/iqs/docs/implementation/parallel-lanes/packages/2026-10-07-wave2/manifest.json | vendor/iqs/docs/implementation/intake/SW-REPAIR-02/2026-10-08/worker/handoff.json | 2 | `invalid`，errors=[`changed_path_out_of_scope`] |
| EVID-LAB-01 | vendor/iqs/docs/implementation/parallel-lanes/packages/2026-10-07-wave2/manifest.json | vendor/iqs/docs/implementation/intake/EVID-LAB-01/2026-10-08/worker/handoff.json | 0 | `valid`，errors=[] |

以上三行是编制时实际运行得到的原 verdict（见 `inputs.lock.json` 的 `oracle_expectations`）。catalog 的 `task_ids`/`lane_id`/`write_scope`/`readiness` 与 handoff 的比对规则必须按冻结 CLI 实现，不得自创。

## 交付物

1. `rules/rules.json`：每条含 `rule_id`、`kind`（shape/hash/leak/declaration）、`severity`、`source_ref`（依据文件+行号/字段 pointer）、`description`、`false_positive_note`。至少覆盖：清单缺/多文件、bytes/sha 不符、清单含自身或最终元数据、路径越界/重解析点、重复 JSON 键、1 MiB 上限、`status=complete` 而 `result_commit=null`、`lane/package/task_ids` 与 catalog 不符、**`review.status` 非 `approved` 却自述可交付**、临时根未清理。
2. `schemas/bundle-audit-request-1.0.0.schema.json`、`schemas/bundle-audit-report-1.0.0.schema.json`（Draft 2020-12，`additionalProperties=false`，required 全列，拒 NaN/重复键）。
3. `content/casebook.json`（≥24 例，expected 分离）。
4. `fixtures/`：正常包、缺文件、哈希篡改、自指、各类泄漏；`catalog.json` 记相对路径/bytes/sha256/`synthetic=true`。
5. CLI、测试、`integration-map.md`。

## 公开接口与输出协议

```powershell
python -B -X utf8 -m iqs_delivery_audit audit --input <bundle-root> --input-root <root> --source-root vendor/iqs --lock inputs.lock.json --output .tmp/audit-01
python -B -X utf8 -m iqs_delivery_audit validate --input <request.json> --input-root <root> --source-root vendor/iqs --lock inputs.lock.json
python -B -X utf8 -m iqs_delivery_audit evaluate --cases content/casebook.json --input-root fixtures --source-root vendor/iqs --lock inputs.lock.json --output .tmp/eval-01
```

报告 `iqs.bundle_audit_report/1.0.0`：顶层用共同字段（`protocol,package_id,input_lock_sha256,data_kind=offline_candidate,production_qualified=false,source_refs,limitations,payload`）；payload 闭合 `bundle_root_sha256,inventory,findings,oracle_agreement,counts,manual_review_required=true`。

- `inventory`：`declared_count,actual_count,missing_paths,extra_paths,hash_mismatches,self_reference_hits,metadata_cycle_hits`。
- `findings[]`：`finding_id,rule_id,kind,severity,relative_path,byte_offset_or_null,observed,expected,evidence_sha256`。
- `counts`：`files_total,files_checked,files_skipped,findings_by_kind`，互斥且和等于 `files_total`。

禁止内容检测只报确定性证据：`answer_body`、`hidden_thinking`、`full_page_html`、`database_copy`（`SQLite format 3\0`）、`credential_marker`（`sk-` 要求左侧 token 边界，避免误杀 `risk-adjusted`/`task-output`/`mask-based`/`disk-failure`——真实修复过的误报类别，见 `task_plan.md` 2026-10-18「修复真实金融文字被密钥检查误拒」）、`lease_or_grant_token`、`api_raw_body`。

退出码（本批统一采用 §2）：**0** 审计完成（发现泄漏仍算成功诊断）；**1** 仅 `evaluate` 与冻结预期不符；**2** 输入/schema/重复键/哈希漂移/用法错误/输出已存在或越界；**3** 内部引用不闭合、检测到网络或凭据访问尝试、意外内部错误。输出 exclusive 原子发布，不跟随 reparse。

## 确定性离线验收

| Case | 必须证明 |
|---|---|
| DA-01 | 复现上表三条 oracle verdict（含 SW-REPAIR-02 的 `changed_path_out_of_scope`），逐字段一致；catalog 规则不得自创 |
| DA-02 | 合成正常包：清单闭合、无 finding、`counts` 与 files_total 相等 |
| DA-03 | 清单少列/多列各 1 个文件 → `missing_paths`/`extra_paths` |
| DA-04 | 工件改 1 字节 → `hash_mismatches` 精确指 path 与原期望 sha |
| DA-05 | 清单含自身 sha 或 `handoff.json`/`final.json` 自身 → `self_reference_hits`/`metadata_cycle_hits`，不进入无限重算 |
| DA-06 | `../`、绝对盘符、反斜线、重解析点越界被拒，且不读外部文件 |
| DA-07 | 7 类禁止内容各 1 正例全部检出，含 rule_id 与 byte offset |
| DA-08 | 4 个已修复误报词（含 `risk-adjusted`）不产生 `credential_marker` |
| DA-09 | `status=complete` 且 `result_commit=null`；`review.status=changes_requested`；两者各报 declaration finding |
| DA-10 | `review.status=approved` 但 `review/final.json` 缺失或不一致 → finding（`approved` 是 schema 枚举值，`passed` 不是） |
| DA-11 | 重复 JSON 键、NaN、>1 MiB → exit2 且无输出 |
| DA-12 | 输出目录已存在 → exit2（不覆盖）；同一 bundle 两次新根 payload 字节相同 |
| DA-13 | 全程零网络、零子进程外呼、零付费；临时根成功与失败都清理 |
| DA-14 | 真实语料 `files_skipped` 有理由，不缺行、不把跳过算通过 |

≥24 个单测场景；集成用 3 个真实 handoff + 2 个 catalog；E2E 从公开 CLI 读文件到新结果再 `validate` 读回，含随机 cwd 与中文空格路径。工具不得读 `fixtures/expected/`。

## 禁止捷径

不得伪造回执、评分、测试通过数或 finding 数；不得跳过 hooks 或 `--no-verify`；不得复制真实 namespace/真实库/答案正文/密钥进本仓；不得把真实 tracked handoff 当"通过"证据而不核 blob；不得写生产库/名单/发布指针或他人 Lab；不得 `git add -A`；不得联网或付费补料；不得用"未发现"替代合规或安全结论。

## 独立审查要求

按 `integration-contract.md` §5：**真正不同的独立 reviewer** 全量审规则依据、检测器边界、oracle 一致性、离线与清理，并自带 ≥2 个作者未给样例（1 泄漏、1 正常限定）。`docs/handoff/DELIVERY-AUDIT-11/review/` 必含 `invocation-evidence.json`（作者与 reviewer id 不同、UTC 时间、可打开引用）、`round-XX.*`、`fixes.json`、`final.json`（`verdict=passed`、`open_findings=[]`、`reviewed_commit`）。`handoff.json.review.status` 在 `final.json` passed 后才写 `approved`。

## 交回

本仓 `docs/handoff/DELIVERY-AUDIT-11/`：见 `handoff-rules.md` 第一节文件集（含 `rules/`、`report.md`、`tests.json`、`cleanup.json`、`review/`）。先 payload commit，再 metadata-only commit。

## 风险与已知未知

- **启发式误判**：只报确定性证据、写 `false_positive_note`、`manual_review_required=true`，不自动判"安全"。
- **oracle 漂移**：若总控日后升级 CLI，判定可能不一致；锁 blob，冲突时输出 `oracle_agreement=false` 并以锁定版本为准。
- **未知**：2026-10-10 两个 received-handoff 未 tracked；Lab 交付目录除规范文件外的变体未枚举，按 `extra_paths` 报而不猜语义。
