---
name: repair-iqs-issue
description: 处置本仓（invest-quick-scan）已证实的反馈观察：从 feedback-observation/1 事件或 docs/implementation/issues 的问题卡出发，定位责任层、做最小公开复现、先红后绿修复、登记问题卡并复验原场景。只改本仓，不跨仓修复，不派发付费扫描。
when_to_use: |
  当用户给出反馈观察引用（run_id/attempt_id/step_id/check_id 或 evidence_ref）、
  问题卡编号（F2-IQS-xxxx），或要求“按观察修一下公司结果/逐题覆盖/快扫检查”时。
  触发词：反馈观察、观察回放、F2-IQS、complete-claimed、group-lost、
  修这个偏差、复现观察、replay observation。
allowed-tools: Read Bash Write Edit
version: 1.0
---

# 修复 IQS 反馈观察

一次只处置一个已证实的问题。日常运行只负责留下观察，**不**在本技能外隐式调用
模型、搜索或任何付费请求；本技能也不联网、不写 StockWiki / StockQA / Dashboard。

## 输入

二选一：

1. **完整观察引用**：`run_id` + `attempt_id` + `step_id` + `check_id`（可附
   `evidence_ref`、`issue_key`、`version`）。事件来自 `RESEARCH_FEEDBACK_OUT`
   指向的 JSONL；按行读取，截断或坏行只跳过该行。
2. **本仓问题卡**：`docs/implementation/issues/F2-IQS-XXXX.md` 中的编号。

资料缺失、上游真离线、只有一条无法复现的观察，都是**正常状态**：保持
`待查`/`needs_evidence`，不要为了结案去猜原因。

## 处置流程

### 1. 归位观察

- 读事件行，确认 `schema_version=feedback-observation/1`，`owner` 是本仓或
  被转交的上游仓（`origin_owner=invest-quick-scan`）。
- 用 `evidence_ref` 找产物：`iqs:company/<entity>/<result_id|reason>` 指向一次
  公开读；`step_id` 是 `company-result/<entity>` 或 `company-history/<entity>`。
- 只有 `disposition=deviation` 且 `expected`/`actual` 都是稳定词的转换才进修复；
  `unknown` 只做对账。

| `check_id` | `expected` | 可能的 `actual` | 读法 |
|---|---|---|---|
| `coverage-claim` | `claim-matches-refs` | `complete-claimed` | owner 的完整性声明与它自己绑定的引用不一致 |
| `multi-group-lineage` | `no-group-loss` | `group-lost` | 某个冻结尺度组没有观察，或引用落在组外 |
| `question-status` | `statuses-published` | `statuses-missing` | 逐题状态没随公开结果发布 |
| `missing-questions` | `missing-kept` | `missing-dropped` | owner 已声明的缺项在投影里丢了 |
| `owner-absence` | `reason-named` | `reason-missing` | 无结果时没有带名原因 |

### 2. 判责任层

| 现象 | 责任层 | 动作 |
|---|---|---|
| 本仓投影丢组、丢缺项、逐题状态没发布、把部分完成说成完整 | 本仓 `scripts/iqs_scan/workbench/dashboard_company_projection.py` 与 `company_result_coverage.py` | 在本仓修 |
| owner 快照的 `completeness` 与 `observation_refs` 自相矛盾 | StockWiki（公开契约） | 回交总控与 StockWiki，本仓只保证披露而不转发成完整 |
| 已结算但没保存、provider 过滤/截断、未运行 | StockQA / 原 scan 作业 | 回交对应 owner，本仓按回执分类并保留原状 |
| Dashboard 展示层把两个尺度并成一个 | Dashboard（`G-IQS-02_*`） | 回交 Dashboard，本仓只保留各组原尺度 |
| 观察文件写不出、并发交错、重复派工 | 总控 / 宿主 | 回交 ROOT，本仓只保证业务不受影响 |
| 期望值本身写错（合法部分完成被当成偏差） | 本仓检查规则 | 先改检查规则与反例，再复验 |

判层依据是**公开结果本身**，不是投影的处置结果：先看 owner 快照声明了什么、
绑定了哪些引用，再看本仓发布成什么。owner 声明 `formal` 而引用只有 35 条，
是可证偏差（需要分诊），不能写成“数据不全所以无法判断”。

### 3. 最小公开复现

只用本仓公开入口与固定夹具，离线、可重复：

```bash
# 一次真实公开读（只读，0 模型调用、0 注册/发布）
python -B -X utf8 scripts/company_result_feedback.py \
  --stockwiki-root <StockWiki checkout> \
  --workspace-root <owner workspace> \
  --entity ENT_... --out <observations.jsonl> \
  --run-id <原 run> --attempt-id <新 attempt>

# 向临时公开响应注入遗漏题/缺组，验证反馈能报出来
python -B -X utf8 scripts/company_result_feedback.py \
  --inject-result tests/fixtures/company_coverage/result-partial-claiming-complete.json \
  --out <injected.jsonl>

# 快扫结果检查：部分完成不得报成完整可用
python -B -X utf8 scripts/scan_result_check.py --run <run dir>
```

`--inject-result` 只是把已保存的快照放到 owner 读本该返回的位置，投影与检查
完全走同一条公开路径；它不产生新的公司运行、不写 owner 库。

### 4. RED → GREEN

1. 先写会失败的用例：优先用 `tests/fixtures/company_coverage/` 的固定输入，
   或 `tmp_path` 生成缩小输入；断言检查真的报 `deviation`。
2. 跑一次，记录真实失败输出（不是“应该会失败”）。
3. 只修责任层的最小点；不做顺手重构，不改既有 golden、评分、公开 DTO 语义。
4. 复跑：新用例转绿，且**合法相近对照**（真正完整的混尺度结果、单尺度结果、
   已确认的空结果）不误报。
5. 换一组题号/实体/尺度再跑一次，确认实现没有依赖样本名。

### 5. 登记问题卡

在 `docs/implementation/issues/F2-IQS-XXXX.md` 记录（模板见下），状态只取
`open` / `working` / `verified`：

- `open`：已确认、可领取，尚未动手；
- `working`：正在修，已写明责任层与最小复现；
- `verified`：修复版本已由发现方原场景复验。

同一根因再次出现时**追加发生引用**，不要新建卡；复发可把 `verified` 改回
`open`。原因未证实时写“待查”，不要填推测。

### 6. 复验与回告

- 用修复版本重跑原场景（同一 `run_id`/`attempt_id`，必要时新 `attempt`），
  确认事件身份可辨认、`disposition` 变为 `expected`。
- 回告只带公开值：`issue_ref`、`fixed_version`、`verdict`
  （`verified` / `regressed` / `unknown`）、`evidence_ref`。
- 修复版本指发现方实际能运行的版本，本仓为
  `invest-quick-scan/<projection_version>-obs<观察接线代次>`。

## 问题卡模板

```markdown
# F2-IQS-0000 <一句话标题>

- issue_key: <稳定规则签名>
- 状态: open | working | verified
- 期望/实际: <expected> / <actual>（影响：<读者会得出什么错结论>）
- 责任层: <本仓投影 | StockWiki 公开契约 | StockQA 回执 | Dashboard 消费 | 总控>
- 修复版本: invest-quick-scan/x.y-obsz
- 复验: <verdict> @ <version>

## 发生引用
| # | run_id | attempt_id | step_id | check_id | evidence_ref |
|---|---|---|---|---|---|

## 最小复现
<命令 + 输入来源 + 期望看到的 deviation>

## 根因（已证/待查）
<证据链；未证实时写待查>

## RED / GREEN
<真实失败输出摘要；修复后计数>

## 同类场景与反例
<还会在哪些输入出现；哪条合法输入必须不报错>
```

## 边界

- 只改本仓；跨仓缺口回交，不在本仓复制 owner 规则（例如不自己算 StockWiki
  的完整性、不重算 StockQA 的终态）。
- 不为了让检查变绿而放宽 `expected`；先确认哪一侧的期望错了。
- 观察文件只是投影，不替代本仓步骤日志；原文、配置和令牌不进事件。
- 需要改架构（新增端口、改 wire、改公开响应形状）时，先在本仓 PWF 增补范围与
  验收，再动手。
