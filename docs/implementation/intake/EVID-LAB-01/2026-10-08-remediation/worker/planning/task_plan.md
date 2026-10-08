# EVID-LAB-01 任务计划

- **PLAN_ID（显式pin）**：`EVID-LAB-01`
- **PWF_PLAN_ROOT**：`C:/Users/郑曾波/Projects/iqs-evidence-lab`
- **规范计划目录**：`docs/handoff/EVID-LAB-01/planning/`（本卡允许写入范围内的唯一计划位置）
- 解析说明：本安装版本的 resolver 只寻址 `<root>/.planning/<PLAN_ID>`，无法直接寻址
  `docs/handoff/<pkg>/planning/`。实测 `PWF_PLAN_ROOT=<lab根> PLAN_ID=EVID-LAB-01` 返回空
  （fail-closed），**不会回落到 IQS 根 `task_plan.md` 或任何其他计划**；因此以本目录为唯一
  计划源，进度一律写这里。
- 工作目录（唯一writer）：`C:/Users/郑曾波/Projects/iqs-evidence-lab`
  （用户已在分派会话中明确授权创建并作为唯一writer）
- 唯一起点commit：`cc3c38824c90a210196d63242797113247094b22`（分支 `codex/evid-lab-01`）

## Goal

交付可复现的离线证据质量诊断工具（结构/每题有效性、claim可核验程度、评分依据、速度、
费用/套餐、缓存与失败分开报告）、≥30个fixture、只读重放CLI与 `execution_enabled=false`
的下一轮实验提案；不重新宣称60家公司校准，不启动L03，不发新生产字段。

## Phases

### Phase 1 建仓与输入锁定 — Status: complete
- 建Lab仓、分支 `codex/evid-lab-01`、起点commit、PWF pin（见上）。
- 逐项验证 `inputs.lock.json` 的 IQS 输入 SHA 与实验索引96绑定文件；任何漂移→停止并报告。
- 记录开工 HEAD/branch/status 快照（IQS/StockQA/StockWiki 只读观察）。

### Phase 2 数据结构勘察 — Status: complete
- 三归档 results/blocks/analysis/ledger/provenance/inputs-manifest/source-index 结构。
- 326 review/join、两分区、mapping、canonical fingerprint 口径。
- 价格快照、生成策略（48次实际0.7）、final-statistics 已发布分母与口径。

### Phase 3 诊断schema与metric定义 — Status: complete
- `schemas/evidence-diagnostic-v1.schema.json`（具名v1、字段有界、input/answer hash、
  rule/metric版本、错误码与位置、支持来源类型、abstain原因）。
- `docs/handoff/EVID-LAB-01/metric-definitions.md`。

### Phase 4 核心实现（TDD） — Status: complete
- 输入验证 → 归档重算（run/stage/model/thinking/包大小）→ 整包成功率与逐项可恢复率
  → 有限语义矛盾检查（显式依据才判、缺信息abstain）。

### Phase 5 fixtures与测试 — Status: complete
- ≥30明确fixture场景（synthetic / 历史真实模型输出；真实来源短片段=未收集）。
- 单元 + 集成 + 离线CLI E2E（三归档只读重放、重复新输出根、hash不变、网络/key/付费0）。

### Phase 6 CLI与报告 — Status: complete
- `python -m iqs_evidence_lab replay|validate-fixtures`；输出目录独占、不覆盖旧reports。

### Phase 7 实验提案与交接 — Status: complete
- `experiment-proposal.md` + 非执行JSON配置（`execution_enabled=false`）。
- `docs/handoff/EVID-LAB-01/` 全套交接 + 一次集中回归/审查。

### Phase 8 整改（2026-10-08 remediation卡） — Status: complete
- 六组修复：EL-01 period字典/缺year；EL-02 URL窗口/来源计数；EL-03 严格JSON+追溯深度绑定；
  EL-04 CLI原子发布；EL-05 提案冻结300槽分母；EL-06 元数据/双hash口径。
- 先固定总控9反例（8失败/1通过）为RED，最小GREEN，再一批集中回归。
- 版本升级：semantic-rules/2、structure-rules/2、diagnostic schema 1.1.0、fixture schema 1.1.0。
- RED：stash回HEAD快照复现总控反例 8失败/1通过（logs/remediation-2026-10-08/RED-*）；
  修复后 9/9 GREEN；全量 81 passed（原54 + 反例9 + 整改新增18）。
- 公开CLI：index双根重放字节一致、34 fixture 全exit0、input hash前后不变、network=0。

## Decisions Made
| 决策 | 理由 |
|---|---|
| 不 import IQS 报告工具，Lab 自研离线重算 | 原报告 `TemporaryDirectory(dir=b.ROOT)` 会写 IQS；Lab 输入必须只读 |
| 诊断 schema 用自有 `evidence-diagnostic-v1` | 研究工具输出，不扩生产 Observation |
| 费用只出“公共价格参考/上限”，不出套餐实扣 | MiniMax 套餐扣额未知，禁止推断 |
| 事实支持一律 `not_verifiable`/`agent_review_only` | 历史 snippet 已删，URL/hash 不能重建正文 |

## Next Step
Phase 8 完成：结果commit `62fe8b2f51bf498d0925b65e998c7b0a4dba7192`（tool 0.2.0，
代码含 `f5149b9`）；证据commit已交，总控预检 status=valid；81测试终验通过。
等待总控按整改卡回验（9反例+三归档+34 fixture）。

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| pytest 2 failed（missing_bound_file strict 顺序、snapshot 键） | 1 | 调整测试顺序与键名，实现改用 lock 文件名 |
| pytest 1 failed（recoverability totals 键名） | 1 | 修正测试键名与累加 |
| pytest 4 failed（“2026全年”未归一 → abstain） | 1 | normalize_period 支持全年并清理遗留重复函数体 |
| 早期 CLI 草稿先写后建目录 | 1 | 重构为 prepare→mkdir→write，验证在写入前 |
