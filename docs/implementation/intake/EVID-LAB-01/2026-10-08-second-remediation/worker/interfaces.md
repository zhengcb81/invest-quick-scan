# EVID-LAB-01 interfaces（2026-10-08 残余整改后）

## 版本

| 契约 | 版本 |
|---|---|
| 工具 | `iqs_evidence_lab 0.2.1`（`TOOL_ID=.../0.2.1` 随每份输出落盘，可与 0.2.0 结果区分） |
| 诊断文档 | `iqs_evidence_lab.diagnostic/1`，`schema_version=1.2.0`（1.1.0 新增 location.expected_field/observed_field 与5个具体 abstain 理由；**1.2.0 新增 custom 起止边界3个理由与 `unknown_source_window_present`**） |
| fixture | `iqs_evidence_lab.fixture/1`，`schema_version=1.1.0`（provenance 新增 chunk_sha256；本轮无 schema 变更，34个fixture字节不变） |
| 语义规则 | `semantic-rules/3`（period子期间/缺年份具体abstain；URL窗口按claim目标判定；**custom起止边界只比双方明示字段、缺边界abstain；存在未知窗口时不得判全冲突**） |
| 结构规则 | `structure-rules/3`（严格JSON入口含非有限数；staging+原子发布；**每条记录来源类别按 fixture `source_category` 统一映射并全量校验**） |
| 指标 | `metric-definitions/1` |
| 计划槽分母 | `iqs_evidence_lab.plan_slots/1` |
| 预注册配置 | `iqs_evidence_lab.experiment_preregistration/1`，`schema_version=1.1.0`，`execution_enabled=false`、`status=draft_not_signed` |

上一轮曾出现“文档标 `semantic-rules/2` 而输出带 `semantic-rules/1`”的不一致：
本批起规则版本只由 `src/iqs_evidence_lab/__init__.py` 单一来源给出，
`semantic.py`/`diagnostics.py` 都引用同一常量，文档与落盘输出一致。

## 消费（全部只读）

| 输入 | 版本/来源 | SHA 口径 |
|---|---|---|
| `inputs.lock.json` | IQS wave2 input lock，`1.0.0` | 文件字节 SHA256（lock 自身也是被读对象之一） |
| 实验结果索引 | `mimo_pilot_delivery/1`，绑定96文件 | index 自身 + 96 文件逐一核验；**224次SHA校验覆盖127个不同路径，含lock共128个独立文件**（校验次数≠独立文件数） |
| 三归档 | archive-manifest `retained_files` | 逐文件 SHA256 对 manifest |
| 评审/join | `mimo_pilot_source_support_review/1`、`join/1` | canonical fingerprint |
| 题面/身份/截止日/查询 | 归档 inputs-manifest、locked ledger | `frozen_hashes`（canonical JSON SHA-256），由 `tools/gen_proposal_config.py` 再生 |

不消费：生产 Observation/Answer/Exchange 写路径、StockQA 客户端、任何密钥。
所有公共JSON入口（lock、索引、归档、fixture、catalog、staging回读）都经
`hashing.strict_loads`：重复键 → `DuplicateJSONKeyError`，NaN/Infinity 常量 **与
指数溢出成 ±inf 的数字字面量**（`1e400`/`-1e400`，含嵌套 object/array 与 JSONL 行）
→ `NonFiniteJSONError`；正常整数、小数与范围内的科学计数法照常解析。
fixture 路径映射退出码4，锁定输入路径映射退出码2。

## 产出（Lab 自有，非生产）

| 产物 | 生成命令 | 说明 |
|---|---|---|
| 诊断文档 | `PYTHONPATH=src python -m iqs_evidence_lab replay ...` | 出 `input_sha256`（fixture原字节SHA）、`answer_sha256`（**当前被回放输入**在场答案canonical SHA，只记录本次输入、不构成历史来源证明：历史来源由 `archive_provenance_verifier` 独立回链锁定归档）、semantic记录的 expected/observed 字段定位；每条记录 `support_source_type` 由 fixture `source_category` 统一映射 |
| metrics/recoverability/review-join/input-verification/summary | 同上（index 模式） | `published_comparison.equal_to_published` |
| fixture catalog（交接副本） | `python -X utf8 tools/make_fixtures.py` + 覆盖生成 | 34 fixtures / **42 expectations** / **350 条诊断记录**；synthetic 28、historical 5、real-source 1（全部 collected=false） |
| 预注册配置 | `python -X utf8 tools/gen_proposal_config.py` | 冻结题组/查询/哈希/公式；开关保持 false |

`replay` **发布语义（structure-rules/3）**：全部 payload 先写入
`.temp-roots/staging-<pid>-<uuid>`，逐文件严格回读校验后 `os.rename` 原子发布到
独占输出目录；任何失败清除本次staging、已存在目标不变、同一输出路径可直接重试。

**来源类别（structure-rules/3）**：`source_kind_for(fixture)` 是唯一映射——
synthetic→`synthetic`、historical→`historical_model_output`、
collected real_source_snippet→`real_snippet`、未收集→`none`；
`source_kind_problems()` 对**整个document的所有记录**校验，synthetic 不能标成
historical、未收集的 real_source_snippet 不能标成 `real_snippet`，
`agent_review_only`/`no_human_gold` 的记录永远不是 gold。

### 退出码

| code | 含义 |
|---:|---|
| 0 | 成功 |
| 1 | 未预期错误（含staging写盘失败：已清staging、目标未创建、可重试） |
| 2 | `InputDriftError`：锁定输入缺失/漂移/非严格JSON/文件不是 result index（schema≠`mimo_pilot_delivery/1`） |
| 3 | `OutputDirError`：输出目录已存在或不在 Lab 根内 |
| 4 | `FixtureError`：fixture 非严格JSON、schema违例、期望或provenance不匹配 |
| 5 | `UsageError`：参数或输入引用无效 |
| 6 | `NetworkBlockedError`：离线守卫拦截（正常路径不触发） |

### 正例 / 反例

- 正例：`replay --input index` 三归档重算 `equal_to_published=true`、
  326 join 一致；双新根重放五个payload字节一致；34 fixture 全 exit 0
  （证据：`logs/remediation-2026-10-08/public-cli-runs.json`、
  `logs/remaining-repairs-2026-10-08/public-cli-runs.json`，后者 36/36 exit0、
  双根字节一致、128个输入文件前后SHA不变）。
- 反例（总控冻结9反例，RED 8失败/1通过 → 现9/9通过）：period字典Q1/Q4、H1/H2冲突，
  缺年份abstain；无窗口abstain；比较列不fail；重复 `source_category` exit4且不建输出；
  写盘注入失败 exit1且无半成品（并可同路径重试）；historical答案改score/rationale
  被provenance拒绝；锁定价格文件当index → exit 2。
- 反例（2026-10-08 残余整改六项，`tests/controller/test_remaining_repairs.py`
  RED **10 failed / 17 passed** → GREEN **27 passed**，证据
  `logs/remaining-repairs-2026-10-08/RED-*`、`GREEN-*`）：
  custom 1–3月 vs 4–6月不再 `semantic.period=pass`（同形日期→fail、缺边界→abstain）；
  删 `provenance.answer_sha256` 后改历史答案 → exit4 且不建输出（带hash篡改同样拒，
  空/null/错 question_id 绑定一律 exit4）；`1e400`/`-1e400` → exit4、无staging无输出；
  已冲突+未知来源窗口 → abstain `unknown_source_window_present` 而非
  `E_URL_WINDOW_CONFLICT`；FX021 **全部**记录 `support_source_type=synthetic`；
  费用上界按 `generation.output_limit=10000` 复算 `0.82296 ≤ 0.83`。

## 尚缺接口（明确不做/未做）

- 不产出生产 Observation/Answer/Exchange，不发新字段给生产执行器。
- 无真实来源短片段 fixture（需另行授权）；无 gold 标注集。
- 预注册是 `draft_not_signed` 草案：`execution_enabled=false`，执行依赖用户预算授权、
  总控放行与签核；Phase96 既有结果不被本草案重复或覆盖。
- inter-rater 校准、人类 gold 校准、生产采用、L02/G3/F05 关闭：`not_run`（worker 不自关）。
