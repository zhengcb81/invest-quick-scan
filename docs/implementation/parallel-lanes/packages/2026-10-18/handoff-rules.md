# 本批共同施工与交接规范

本文件不是新规则集：施工与隔离规则仍以 [2026-10-10 共同规范](../2026-10-10/handoff-rules.md) 为准。本文件只声明**本批的差异、取代项与协议选择**；冲突时以本文件更具体的规定为准，并先交总控裁定。

## 一、交接协议：只用 handoff.schema.json 1.0.0

本批**唯一**交接协议是 [../../handoff.schema.json](../../handoff.schema.json)（1.0.0），即 `scripts/parallel_handoff_cli.py` 实际校验的那一份。要点：`schema_version="1.0.0"`、`lane_id`、`package_id`、`status` ∈ `complete|partial|blocked`、`snapshot{repository,base_ref,base_commit,result_ref,result_commit,...}`、`scope{task_ids,authorization_scope_ref,owned_paths,authorized_paths,changed_paths,out_of_scope_writes}`、`interfaces[]`、`verification{checks,external_writes,network_calls,paid_calls,temporary_roots}`、`review{status,snapshot_commit,findings}`、`open_items`、可选 `next_action`。

明确不适用：`2026-10-18-mainline-support/integration-contract.md` §4 的 `iqs.support_handoff/1.0.0` 字段（`payload_commit`/`reviewed_commit`/`inventory_ref`/`ready_for_controller_acceptance`）**不进 `handoff.json`**；本批也不产出 `input-catalog.json`。该契约的 §1–§3、§5（输入冻结、公开 JSON 约束、TDD/E2E、独立审查）仍适用，仅 §4 的字段集被上面的协议取代。

`scope.task_ids` 必须与本批 `manifest.json` 中该包 `task_ids` **集合相等**（CLI 强制）；`lane_id` 与 `write_scope` 同样被比对；`changed_paths` 必须是 `write_scope` 下、且被 `authorized_paths` 覆盖的安全相对路径。

### 真实交付文件集（`docs/handoff/<ID>/`）

必须存在：`handoff.json`（上面的协议）、`summary.md`、`artifacts.json`（相对路径/bytes/raw SHA-256/角色/来源类别，**排除自身**）、`interfaces.md`、`case-map.md`（case→selector→原日志/hash→passed/failed/skip/not_run，精确分母）、`logs/`（首败与终版 GREEN 的 stdout/stderr/exit）、`isolation.md`、`planning/`（本包独占三件）、`tests.json`、`cleanup.json`、`report.md`、`review/invocation-evidence.json`、`review/final.json`、`review/round-*.json|md`、`review/fixes.json`。

不再要求：`input-catalog.json`、`inventory.json`（职责并入 `artifacts.json`）、`payload_commit`/`reviewed_commit` 字段。commit 区分改为：先提交最终功能 payload，再单独提交 handoff 元数据。`handoff.json.snapshot.result_commit` 必须写**payload commit**（即功能代码/数据/测试提交，metadata 提交之前的那个 HEAD），它由 reviewer 在 `review/final.json.reviewed_commit` 引用；`review/final.json` 不写自身提交号。**两个字段都不得为“避免自指”而留空或填占位**；metadata 提交的 HEAD 由总控验收报告外部绑定。

## 二、目录、输入与 vendor 布局

1. 每包只写 `manifest.json` 的 `write_scope` 与 `authorized_relative_paths`（含 `rules`、`vendor`）。其他一切只读：IQS/PWF、`runs/`、StockQAbyLLM、StockWiki、company-wiki、既有 `iqs-*-lab`、另两包。
2. 输入只从本仓 Git 对象取：`git cat-file blob <oid>` 读二进制 stdout，逐项核对 `bytes`/`sha256` 后复制到 **`vendor/iqs/<与仓库相同的相对路径>`**（保持目录结构，例如 `vendor/iqs/docs/implementation/contracts/providers-and-budget.md`）。不读活动工作树、不 checkout 源仓、不转 CRLF。
3. `vendor/` 只读：只往里复制，不改内容；`--source-root vendor/iqs` 与 `--input-root` 分别校验，不用 cwd 猜路径。
4. 每包自建 `.tmp/<run-id>`；TEMP/TMP/TMPDIR、pytest basetemp、缓存、日志、子进程都进入该根。失败路径也清理；清理不了如实写 `cleaned=false`。
5. 零网络、零付费、零模型、零数据库：三包不调用外部服务，不读 provider 凭据或 key，不以真实 SQLite/生产库/名单为输入，不下载文档。

## 三、退出码（本批采用 integration-contract §2 的四档）

| 码 | 含义 | 本批映射 |
|---:|---|---|
| 0 | 输入有效且报告生成；**发现冲突/缺口/不一致仍是成功诊断** | 所有 `audit`/`convert`/`validate` 正常完成 |
| 1 | 仅 `evaluate` 与被冻结的测试预期不符 | 其他命令不得返回 1 |
| 2 | 输入/schema/重复 JSON 键/NaN/非法日期/未知协议版本/输入 hash 漂移/**用法错误**/输出已存在或越界 | 原"用法(5)"并入此码 |
| 3 | 输入可读但依赖或分析无法执行：内部引用不闭合、**检测到网络或凭据访问尝试**、意外内部错误 | 原"内部不闭合(4)"、"网络/凭据(6)"、意外失败(1) 并入此码 |

原各卡中的 4/5/6 一律按上表改写；具体原因写进报告 `findings[].reason_code` 或 stderr 诊断，不得只靠码值表达。

## 四、独立审查（本批强制）

按 `integration-contract.md` §5：作者必须调用**真正不同的独立 reviewer agent** 全量审查，不得自扮。`docs/handoff/<ID>/review/` 必含 `invocation-evidence.json`（平台、作者与 reviewer id 必须不同、UTC 调用时间、可打开的原始调用/返回引用；拿不到填 null 并说明，不伪造）、`round-XX.*`、`fixes.json`（逐项修复 commit 与复验）、`final.json`（`protocol=iqs.support_review/1.0.0`、`verdict=passed`、`open_findings=[]`、`reviewed_commit`）。复审到 `passed` 才可交接；`changes_requested`/`blocked` 如实保留。

`handoff.json` 的 `review.status` 只能取冻结 schema 的枚举 `not_run|approved|changes_requested|insufficient_evidence`：只有 `review/final.json` 的 `verdict=passed` 且 `open_findings=[]` 时才可写 `approved`；`final.json` 不替代该字段，两者必须一致。

## 五、总控接收

总控先用 `scripts/parallel_handoff_cli.py` 预检（catalog 必须位于 `docs/implementation/parallel-lanes/packages/` 之下，故预检在 IQS 根执行），再核 blob/SHA、测试分母、review 证据、清理证明与越界写。预检通过只说明形状与自述范围，不鉴定业务正确或生产就绪。
