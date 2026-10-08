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

### Phase 9 残余整改（2026-10-08 remaining-repairs卡） — Status: complete
- 六处残余同批收口：LR-01 custom起止边界；LR-02 历史答案绑定不看可选hash；
  LR-03 非有限数字面量；LR-04 未知来源窗口不判全冲突；LR-05 全记录来源类别；
  LR-06 草案费用上界＝实际生成上限。
- 先把总控 followup_cases.py（6）+ 首批 boundary_cases.py（5）适配进
  `tests/controller/test_remaining_repairs.py`（只换输出根为 lab 独占 temp root），
  修复前 RED **10 failed / 17 passed**，修复后 GREEN **27 passed**。
- 版本升级：tool 0.2.1、diagnostic schema 1.2.0、semantic-rules/3、structure-rules/3；
  fixture schema 与 34 个 fixture 字节不变。
- 全量回归 **108 passed**；validate-fixtures 34/42/350 `problems=[]`；
  公开CLI index×2+34 fixture = 36/36 exit0、双根字节一致、128输入SHA不变。
- isolation 口径更正：224次校验/127绑定路径/含lock 128独立文件；按锁只读IQS。
- 日志/回执独立进 `logs/remaining-repairs-2026-10-08/`，上一批日志与回执原样保留。

### Phase 10 第二次整改 LR-02B（2026-10-08 second-remediation卡） — Status: complete
- 单项收口：历史 fixture/catalog 入口在读取归档前先校验该归档的锁定 SHA。
- 新增 `inputs.verify_consumed_archive(run)`（复用现有 `inputs.lock.json`，不造第二套来源声明）
  + `fixtures.verify_fixture_archive_binding(fixture)` 在 `prepare_fixture_replay`/
  `validate_catalog` 提前校验；`_archive_rows()` 读取前必经同一闸；index 入口原有严格校验不变。
- 失败类别统一 `InputDriftError` → exit 2（缺锁/缺索引/缺归档/锁或index漂移/非严格JSON/未被锁覆盖）；
  fixture 期望/provenance 绑定问题仍 exit 4；纯 synthetic 与未收集槽不被无关历史锁阻断。
- RED：在 `git archive aeff0e6` 导出的基线Lab副本上跑当前测试 **6 failed / 4 passed**
  （核心反例 exit0 并发布 historical、catalog 在字节漂移上 `"ok": true`）；GREEN **10 passed**。
- 全量 **118 passed**；validate-fixtures 34/42/350 `problems=[]`；公开CLI 36/36 exit0、
  双根字节一致、128输入SHA不变；版本 tool 0.2.2、structure-rules/4（schema/rule 其余不变）。
- 日志/回执独立进 `logs/second-remediation-2026-10-08/`，前两批日志与回执原样保留。

## Decisions Made
| 决策 | 理由 |
|---|---|
| 不 import IQS 报告工具，Lab 自研离线重算 | 原报告 `TemporaryDirectory(dir=b.ROOT)` 会写 IQS；Lab 输入必须只读 |
| 诊断 schema 用自有 `evidence-diagnostic-v1` | 研究工具输出，不扩生产 Observation |
| 费用只出“公共价格参考/上限”，不出套餐实扣 | MiniMax 套餐扣额未知，禁止推断 |
| 事实支持一律 `not_verifiable`/`agent_review_only` | 历史 snippet 已删，URL/hash 不能重建正文 |
| LR-06 选择把费用上界提到 0.82296/0.83，而不是把生成上限降到 5000 | 历史归档 completion_tokens 最大值就是 10000、`finish_reason_length_is_failure=true`，降上限会改变实验能力；卡明确允许“调整草案上限**或**上界”，两者取诚实覆盖实际生成上限的一侧 |
| LR-02 采用“始终独立回链归档、hash仅作额外校验” | 卡给出的两种做法之一，可同时覆盖删hash、空/null、错绑定与带/不带hash篡改 |
| 本批不改 fixture schema、不加新 fixture | 卡要求 34/42/350 与旧正例保持；避免 fixture 字节与交接副本连带变更 |
| LR-02B 复用 `verify_lock` 全量严格校验（而非只校验单文件），且只在消费归档的入口触发 | 卡明确允许“复用现有严格 verify_lock”；全量严格覆盖缺锁/缺文件/锁或index漂移，按入口触发保证 synthetic 不被无关历史锁阻断 |
| 归档漂移归为 exit 2（`InputDriftError`）而不是 exit 4 | 与同一漂移副本走 index 入口的 exit 2 同类同码；fixture 自身期望/绑定问题才是 exit 4，分界在测试与退出码表固定 |
| RED 用 `git archive aeff0e6` 导出副本跑，不回退工作树 | 可复现基线且不 reset/clean 任何改动；日志 rootdir 即基线副本路径，用完即删 |

## Next Step
Phase 10 完成：LR-02B 源码结果 commit（tool 0.2.2、structure-rules/4、归档锁闸）+ 证据 commit
（logs/、artifacts 双hash、handoff.json）；118 测试终验通过。
等待总控按单项卡做一次受影响复验（10 selector + 受影响回归 + 三归档/34 fixture + 版本核对）；
提案仍单独待签核，L02/G3/F05、TH/IN/L03 与 live 不自动变绿。
## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| pytest 2 failed（missing_bound_file strict 顺序、snapshot 键） | 1 | 调整测试顺序与键名，实现改用 lock 文件名 |
| pytest 1 failed（recoverability totals 键名） | 1 | 修正测试键名与累加 |
| pytest 4 failed（“2026全年”未归一 → abstain） | 1 | normalize_period 支持全年并清理遗留重复函数体 |
| 早期 CLI 草稿先写后建目录 | 1 | 重构为 prepare→mkdir→write，验证在写入前 |
