# G0 独立审查报告

- reviewer: `/root/g0_independent_review`
- review_date: `2026-09-23`
- decision: `needs_revision`
- G0_release: `blocked`
- reviewed_HEAD: `25b8d14316c06390450e5a1d8883583bfd039d0d`
- review_snapshot_sha256: `D0D9912E36B30531622D63160D4B5288C0D00BE57008F6EA8D8F8BA811AF0F8C`
- snapshot_method: 对下列 38 个输入文件逐一计算 SHA-256，按仓库相对路径排序，将 `path<TAB>hash<LF>` 的 UTF-8 字节再计算 SHA-256。范围包括 G0 规定的计划/验收/决策/交接文件、G0 packet/matrix/snapshots、`schemas/quick_scan/`、C01-C07 相关 Python helper、测试/fixture、receipts 和原始日志；不含本报告、缓存与生成物。
- key_input_hashes:
  - `docs/implementation/reviews/G0/pre-review-packet.md`: `D6057E3E8A8421A4CAC5C0588448BA31F5F0A89D6B6E1B9DEF5F50091FF520E5`
  - `docs/implementation/reviews/G0/external-interface-snapshot.md`: `F4457802586A030656A471BE128855CC8A6DD5B78472CC0C105DAA6152F9292D`
  - `docs/implementation/reviews/G0/candidate-snapshot.json`: `0A63C3F65C762AF49B49AA172F09EF7558FDFFBC066B8F2EA01A8198353F0CC7`
  - `docs/implementation/tasks.json`: `CE8DA9B6468A1B79931BCDC71204689510725C2CB9C5650C1F3FA194904E8311`
  - `docs/implementation/acceptance-cases.json`: `08FF3D678469FD0B65B26E6A7ECEBDE5E81DEB5B8B36B646522F832BC604BBC9`

## 审查结论

G0 不可放行。当前实现建立了相当完整的 schema、helper、fixture、receipt 和离线测试骨架，且独立复跑 `python -X utf8 -m pytest -q -p no:cacheprovider` 得到 `174 passed, 106 subtests passed in 94.03s`。但这些绿灯未覆盖多项直接违反冻结不变量的可复现输入；部分测试在测试文件内重新实现被测决策，部分原定集成/故障注入验收被改绑为本仓离线常量或 schema 检查。因此，测试通过不能证明 G0 契约闭合。

在修复下列 blocking findings、补齐针对反例的独立测试、重新生成与最新输入一致的候选快照，并重新接受独立审查之前，不应把 P00/C01-C07 标为 G0 verified，也不应解锁 M1。

## G0 case 结论

| Case | 结论 | 独立证据 |
|---|---|---|
| `BASE-02` | `needs_revision` | 已对 StockQAbyLLM、StockWiki、company-wiki 做当前源码只读核对。核心边界大体成立：StockQA 当前请求没有搜索工具 payload 且 `answer_generator.py` 会把模型结果退化为固定 1/5 分；StockWiki `Company` 没有 issuer ID；company-wiki 的证券身份解析会区分证券，不能直接承担跨市场同发行人归并。但 `external-interface-snapshot.md` 关于同哈希 `resolver.py` 不含 issuer-index 符号的陈述是错误的，见 `G0-09`。外部项目也尚无可直接声明为本项目已实现的 quick-scan 公共接口。 |
| `REV-01` | `fail` | 仍有 blocking 契约反例；candidate snapshot 与最新 pre-review packet 不一致；当前 receipts 不能支持“全部验收已完成”。 |
| `REV-02` | `fail` | `candidate-snapshot.json` 记录旧的 pre-review packet 哈希 `25305BF…`，而本次冻结输入为 `D6057E…`，且 candidate snapshot 未绑定新增 external snapshot。审查对象不是单一不可变候选。 |
| `REV-03` | `fail` | C01-C03 多项测试在测试代码内重写决策算法；C05-C07 的若干集成/并发/故障 case 被本地 schema/常量/helper 测试宣称为 passed；这属于 selector 与 claim 不匹配，不能作为独立证明。 |

## 不变量裁决

| Invariant | 结论 | 原因 |
|---|---|---|
| `I01` 轻资产边界 | `fail` | exchange `extensions[].payload` 可携带任意 `raw_document`，绕过 `document_payloads_included=false`。 |
| `I04` 统一身份 | `fail` | Entity/Security、WorkItem scope、Profile/Observation 均缺少跨对象实体一致性约束。 |
| `I05` 缺失值不可伪装为中性分 | `fail` | `insufficient_evidence + score=10` 和 `scored + score=null` 均通过 score schema；模型也可自报 formal check level。 |
| `I08` 时间/模型/历史不可覆盖 | `needs_revision` | observation 哈希与 fresh/stale helper 存在，但错误实体绑定和不充分的验收会污染时间序列；现有证据不足以放行。 |
| `I12` 幂等与断点续扫 | `needs_revision` | work identity 基础存在，但 entity scope 可指向另一实体；真实队列并发、恢复与配额拒绝路径未执行。 |
| `I17` 固定契约不可降级 | `fail` | task test binding/完成口径从真实 owner 公共入口测试改为本仓离线验证，且原集成 case 仍被标为 passed。 |
| `I18` 外部接口先行核实 | `needs_revision` | 完成了源码核实，但外部快照含可证伪事实，需纠正并重审结论。 |

## Findings

### G0-01 — Blocking — 评分状态、分值与验证等级未形成闭合契约

- trigger: 下列输入均通过 `schemas/quick_scan/score.schema.json`：`status="insufficient_evidence", score=10, check_level="formal_research_accepted"`；以及 `status="scored", score=null`。
- location: `schemas/quick_scan/score.schema.json:22-64`（`ParsedAnswer`、`score`、`check_level`）。
- impact: 缺失信息可以被伪装成高分或在“已评分”记录中留空；模型输出还可自行获得正式研究验收等级。筛选结果会违反 `I05`、`SC-02`、`SC-05`、`SC-06`，并可能把不完整公司送入白名单。
- required_fix: 用条件 schema 固定 `scored -> integer 1..10`、非 scored 状态 `-> score=null`；将原始模型声明与系统授予的 check level 分开，正式等级只能由受信任验收步骤写入。
- verification: 增加上述两个 negative fixtures 和“模型自报 formal”反例；schema 与公共 ingest helper 都必须拒绝，并验证消费者不会把 null 转为 5。

### G0-02 — Blocking — 实体绑定可跨公司漂移

- trigger: 以下数据均通过相应 schema：Entity `ENT_A` 内嵌 `Security.entity_id=ENT_B`；entity-scope WorkItem 的 `entity_id=ENT_A, scope_id=ENT_B`；Profile `ENT_WRONG` 内含 `ENT_EXAMPLE_A` 的 Observation。UniverseManifest 还允许重复 member 和任意不一致的汇总计数。
- location: `schemas/quick_scan/identity.schema.json:144-180,244-286`；`schemas/quick_scan/work.schema.json:177-220,350-389`；`schemas/quick_scan/query.schema.json:176-179`。
- impact: 扫描、去重、续扫、展示和消费者检索均可能把 A 公司的任务/结论挂到 B 公司，直接违反 `I04`，并使多地上市合并结果不可审计。
- required_fix: 在可信 helper/validator 中执行跨对象相等约束和 manifest 唯一性/计数校验；无法由 JSON Schema 表达的约束不得只写在说明文本中。所有写入和查询出口应调用同一 validator。
- verification: 把三类跨实体反例及重复 member/错误 counts 加入 negative acceptance；通过公共入口验证拒绝，而非仅调用测试内函数。

### G0-03 — Blocking — 固定验收被离线 selector 替代，测试存在自证

- trigger: `tests/test_identity_contract.py` 自定义 converted-price 计算；`tests/test_metrics_contract.py` 自定义 aggregate/comparison/diagnostic 决策；`tests/test_scoring_and_rules_contract.py` 自定义 parse、coverage 和规则执行。C05 的 `PAR-01`、`BUD-01` 等运行期 case 被配置/schema 测试标为 passed；C06 `DB-03` 的事务原子性与 C07 `START-02` 的并发单 worker 也未由真实入口执行。`tasks.json` 中 C07 的测试绑定从 owner 项目真实公共入口测试改为本仓离线协议验证。
- location: `tests/test_identity_contract.py`、`tests/test_metrics_contract.py`、`tests/test_scoring_and_rules_contract.py`；`docs/implementation/tasks.json` C05-C07；相应 C05-C07 receipts。
- impact: 测试与实现共享同一份测试内逻辑或只验证常量，无法发现公共入口缺失、事务/并发错误和模型 fallback 失效。把这些结果记作 passed 会违反 `I17`、`REV-03`。
- required_fix: 恢复固定 case 的原始语义和 owner public-entry binding。若 G0 仅要求 contract-only，则建立名称明确的新 contract cases，并把尚未执行的 integration/fault cases 标为 `not_executed/pending_owner`，不能记作 passed。测试应调用仓内唯一 reference implementation 或真实 owner adapter。
- verification: 审核 acceptance case 到 test selector 的一对一映射；故意破坏 production helper 时对应测试必须失败；并发、事务、网络阻断、额度拒绝需保留原始运行日志和退出码。

### G0-04 — Blocking — 轻资产边界可由 exchange extension 绕过

- trigger: `document_payloads_included=false` 的 ExchangePackage 在 `extensions[].payload.raw_document` 放入公司正文及伪造 `source_manifest_ids`，仍通过 schema。`build_package` 仅检查 observations 的禁用 key，无法保护直接按 schema 构造或其他 producer 生成的包。
- location: `schemas/quick_scan/exchange.schema.json:52-66`；`scripts/exchange_contract.py` package 构造/验证路径。
- impact: 公司正文或正式研究文档可进入持久化交换包，违反 `I01`、`DB-06`、`DB-07`，也会与 company-wiki 的文档职责冲突。
- required_fix: 将 extension payload 限制为显式注册的轻量 capability schema；在 schema validator 和所有导入入口递归拒绝正文/二进制/文档字段，并限制尺寸。禁止用 extensions 逃逸顶层规则。
- verification: 对 extensions 多层嵌套 `raw_document/document_text/blob/content` 做 negative tests；经公共 export/import 路径验证均拒绝且不产生落盘副作用。

### G0-05 — Blocking — 部署就绪可以自我声明，reference validator 接受畸形 release set

- trigger: deployment response 可声明 `full_release_verified`，同时令 `all_required_component_hashes_match=false`、setup/doctor=false、receipts=null、gates/consumers 为空，仍通过 schema。另一个反例中，release component 只有 `component_id` 与 `required`，`scripts/deployment_contract.validate_release_set` 返回 `(True, None)`，而同一对象无法通过 deployment schema。
- location: `schemas/quick_scan/deployment.schema.json:1126-1240,1312-1417`；`scripts/deployment_contract.py:38-105`。
- impact: 启动器或 UI 可把未安装、未校验、哈希不匹配的系统显示为完整发布，违反 `I22`、`I26`、`E2E-04`、`E2E-05`。
- required_fix: readiness 必须由 validator 从证据计算，不能信任响应自报值；reference validator 先执行完整 schema 校验，再校验 component 唯一性、hash、receipt、gate、consumer、setup/doctor 的条件闭包。
- verification: 上述两个反例必须被拒绝；为每种 readiness 状态建立真值表，验证任何必要证据为 false/null 时不得得到 `full_release_verified`。

### G0-06 — Important — 查询契约允许覆盖范围、分值证据和实体结果互相矛盾

- trigger: `status=ok, items=[]` 配合 `coverage.status=not_covered` 与非空 missing fields 可通过；`ScoreRef(status=scored, score=8)` 的 observation/model/check_level/information dates 全为 null 可通过；Profile/Observation 跨实体也可通过。
- location: `schemas/quick_scan/query.schema.json:39-53,157-179`。
- impact: UI/consumer 可把未覆盖结果呈现为成功空集，或展示无法追溯到观测和模型的“有效分数”；横向比较和刷新判断失真。
- required_fix: 为 search status、coverage、items、missing fields 建立双向条件；scored ScoreRef 必须含 lineage、模型、等级与时间；profile 内容必须与请求及 profile entity 一致。
- verification: 添加三类 negative fixtures，并由真实 query adapter/consumer contract test 拒绝。

### G0-07 — Important — 诊断维度可进入质量核心聚合，空规则也可成为策略根

- trigger: `dimension=recovery_watch, aggregation_role=quality_core` 的 mapping 通过 metric schema；空对象 `{}` 通过 `CompositeRule`，包含该 root rule 的 ScreeningPolicy 也通过。
- location: `schemas/quick_scan/metric.schema.json:45-69`；`schemas/quick_scan/rule.schema.json:31-63`。
- impact: 困境反转观察项可错误抬升核心质量分；空策略的行为依赖消费者实现，可能静默通过或在各端产生不同结果，违反 `I06`、`SC-08`、`RULE-03`。
- required_fix: 将 diagnostic/recovery dimensions 与 diagnostic-only aggregation role 做条件绑定；CompositeRule 强制恰好一个合法叶子/组合操作，并拒绝空对象和多操作歧义。
- verification: 上述两个反例必须失败；增加 recovery flag 只能展示/触发观察而不参与质量平均的端到端 fixture。

### G0-08 — Important — 独立证据检查只看直接 lineage

- trigger: 构造 `obs1 <- obs2 <- obs3` 的传递链，只向 `independent_support(obs1, obs3, [obs2])` 提供中间 observation 时返回 `True`；helper 没有遍历完整祖先或要求已闭包 lineage。
- location: `scripts/exchange_contract.py:145`。
- impact: 间接派生于目标结论的证据可能被当成独立支持，形成证据循环，违反 `CONS-05`、`I15`。
- required_fix: 明确并执行 lineage 闭包：由可信存储递归解析所有祖先并检测环，或要求输入携带可验证的完整祖先集合；缺少祖先数据时返回 unknown/reject，不能默认独立。
- verification: 加入两跳、三跳、环和缺失祖先 case；只有证明无共同祖先时才返回 independent。

### G0-09 — Important — G0 候选与外部核验快照不可靠

- trigger: `candidate-snapshot.json` 绑定旧 pre-review packet 哈希 `25305BF…`，最新文件为 `D6057E…`，且未绑定 external snapshot。`external-interface-snapshot.md` 又称 hash 为 `783460A9…` 的 company-wiki `resolver.py` 不含 issuer-index 符号；同一哈希源码实际在约 1249、1263-1301 行含 `_AMBIGUOUS_ISSUER` 及 issuer-index 处理。
- location: `docs/implementation/reviews/G0/candidate-snapshot.json`；`docs/implementation/reviews/G0/external-interface-snapshot.md`；外部只读 `company-wiki/scripts/company_wiki/resolver.py`。
- impact: 审查者无法确认 packet、外部接口结论和候选是同一冻结状态；错误的接口事实可能导致重复实现或错误 owner 分工，影响 `BASE-02`、`REV-02`、`I18`。
- required_fix: 纠正 issuer-index 陈述，并区分“存在 issuer index 辅助逻辑”和“resolver 不负责跨上市证券自动折叠”这两个结论；重新生成包含最新 packet、external snapshot、全部 receipts/logs 的不可变 candidate manifest。
- verification: 独立脚本重算每个文件哈希并比对 candidate manifest；对 external snapshot 中每条接口断言附精确源码位置和 hash，再由非实现者抽样复核。

## 可复现性说明

独立审查未采用实现者摘要作为结论。除全套 pytest 复跑外，审查者用 Draft 2020-12 validator 直接向相应 schema 注入上述最小反例，并直接调用 `deployment_contract.validate_release_set` 与 `exchange_contract.independent_support`；所有列出的反例均观察到 `accepted=True` 或所述 helper 返回值。修复后应把这些最小输入固化为 negative fixtures，防止仅修测试文案。

当前可接受的外部边界结论是：StockQAbyLLM 可作为未来模型/搜索执行能力的改造基础，但当前请求未携带搜索工具且结果分数丢失；StockWiki 当前 Company 模型缺少 issuer ID 和 quick-scan 公共能力；company-wiki 可提供证券/实体解析相关信息，但现有 resolver 并不自动完成本项目所需的跨市场同发行人折叠。所有这些仍是外部只读观察，不能被当作已经交付的接口。

## 放行条件

1. 修复 `G0-01` 至 `G0-05` 的 blocking 契约问题，并把所有反例转成独立 negative tests。
2. 纠正 acceptance selector 与 receipt 状态：未执行的 owner integration/fault cases 明确保持 pending，不以离线常量检查替代。
3. 修复 `G0-06` 至 `G0-09`，尤其是传递 lineage、外部接口事实和候选快照一致性。
4. 生成新的冻结 candidate manifest，包含当次 packet、external snapshot、schemas/helpers/tests/fixtures/receipts/raw logs 的逐文件 hash。
5. 由独立审查者基于新快照重跑全套测试和反例，再决定 G0 是否可放行。
