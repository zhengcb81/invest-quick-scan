# EVID-LAB-01 interfaces

## 消费（全部只读）

| 输入 | 版本/来源 | SHA 口径 |
|---|---|---|
| `inputs.lock.json` | IQS `docs/implementation/parallel-lanes/packages/2026-10-07-wave2/` | 文件字节 SHA256（与 lock 记录一致） |
| 实验结果索引 | `mimo-pro-result-index-2026-10-07.json`，schema `mimo_pilot_delivery/1`，绑定96文件 | index 自身 + 96 文件逐一核验 |
| 三归档 | `mimo-pro-pilot-2026-10-07-01/-thinking-all/-jsonoff`，archive-manifest `retained_files` | 逐文件 SHA256 对 manifest |
| 评审/join | `mimo_pilot_source_support_review/1`（196+130）、`mimo_pilot_source_support_join/1` | canonical fingerprint（sort_keys+紧凑JSON的SHA256） |
| 题目/身份/价格/生成配置 | 归档 `inputs-manifest.json`、`mimo-pilot-pricing-2026-10-07.json`、`mimo-pilot-generation-policies-2026-10-07.json` | 随归档/索引锁定 |

不消费：生产 Observation/Answer/Exchange 的写路径、StockQA 客户端、任何密钥。

## 产出（Lab 自有，非生产）

| 产物 | 版本 | Schema | 生成命令 |
|---|---|---|---|
| 诊断文档 | `iqs_evidence_lab.diagnostic/1`，`schema_version=1.0.0` | `schemas/evidence-diagnostic-v1.schema.json` | 由 `replay` 自动产出并用 jsonschema 校验 |
| fixture | `iqs_evidence_lab.fixture/1`，`1.0.0` | `schemas/fixture-v1.schema.json` | `python -X utf8 tools/make_fixtures.py` |
| metrics/recoverability/review-join/summary | `iqs_evidence_lab.metrics/1` 等 | 内嵌 schema 字段 + 本文件说明 | `PYTHONPATH=src python -m iqs_evidence_lab replay --input index --output <dir>` |
| fixture catalog（交接副本） | `iqs_evidence_lab.fixture_catalog/1` | 见 `fixture-catalog.json` | 由 `fixtures/catalog.json` 加 provenance/hash 覆盖生成 |

`replay` 输出文件：`input-verification.json`、`metrics.json`、`recoverability.json`、
`review-join.json`、`diagnostics.json`、`summary.json`（fixture 模式为
`diagnostics.json` + `fixture-expectations.json`）。

## 输入来源与正反例

- 输入引用：`--input index`（锁定索引）、任意 lock 内相对路径、或 fixture JSON 路径。
- 正例：三归档 replay exit0，`metrics.published_comparison.equal_to_published=true`、
  `review_join_verified=true`；`validate-fixtures` exit0（34 fixtures/350 records/problems=[]）。
- 反例（退出码见下）：lock 漂移或未锁定索引 → 输入失败；输出目录已存在或越出 Lab 根 →
  拒绝；fixture 期望不匹配 → 中止且不创建输出目录；输入不存在 → 用法错误。

## 退出码

| code | 含义 |
|---:|---|
| 0 | 成功 |
| 1 | 未预期错误（不应出现） |
| 2 | `InputDriftError`：锁定输入缺失/漂移/索引未锁定 |
| 3 | `OutputDirError`：输出目录已存在或不在 Lab 根内 |
| 4 | `FixtureError`/诊断 schema 违例/fixture 期望不匹配 |
| 5 | `UsageError`：参数或输入引用无效 |
| 6 | `NetworkBlockedError`：离线守卫拦截网络尝试（正常路径不应触发） |

## 尚缺接口（明确不做/未做）

- 不产出生产 Observation/Answer/Exchange，不发新字段给生产执行器。
- 无真实来源短片段 fixture（需另行授权抓取）；无 gold 标注集。
- 无 live 实验执行器：`experiment-proposal.config.json` 为 `execution_enabled=false`
  的预注册；执行依赖用户预算授权与总控放行。
- inter-rater 校准、人类 gold 校准、生产采用：`not_run`。
