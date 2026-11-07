# TH-SOURCE-INTEGRATION-01｜把快扫事实接进主题研究技能源仓

**唯一写入 Lab：** `C:\Users\郑曾波\Projects\iqs-th-source-integration-01-lab`
**只读源仓基线：** analyze-theme-value-chain `master@3c9a49c7ce86f3e60eb9a6c8e6c835164cb8a903`
**只读已验收 consumer：** `iqs-th-impl-02-lab@5477353649bd86385bc9261bdb2a9f2b30ef63a1`
**接口：** IQS `acb03e3c084f61ca2b49181180195118077d43e3`，facts wire 2.7.0，schema SHA-256 `cd3e03417289a99f5194263603ead6d954fd601b875cd3d5c08a74505ba8cbad`。详见同目录 `inputs.lock.json`。

## 目标

把已经验收的离线 quick-scan consumer 移植到主题技能源仓，让主题分析在用户已选择公司/候选时可以读取 IQS 结构化 facts，并将其作为可追溯的产业链线索。主题适配、因果机制、收入弹性、预测、估值和最终研究判断仍由原技能完成。

## 只允许的改动

- `SKILL.md`：说明何时可选读取 facts、如何区分已核实关系与探索线索，以及如何保留旧流程。
- `references/quick-scan-integration.md`：参数、公开 CLI 调用与字段呈现约定。
- `scripts/quick_scan_client.py`：移植已接受 consumer；通过显式参数调用公开 CLI，不使用绝对本机路径、私有 Python import 或直接读数据库。
- `tests/test_quick_scan_integration.py`、`tests/fixtures/quick_scan/**`：仅为本包必要的定向测试与合成 fixtures。
- `docs/handoff/TH-SOURCE-INTEGRATION-01/**`：交接文件。

先核实冻结源仓树是否已有同名文件；若路径与本卡不同，只可在本 Lab 内对齐到功能等价的原入口，并将实际路径写入报告。不得触碰其它文件或扩大范围；如确需超出 allowlist，交回理由，不顺手重构。

## 行为与边界

- 用户选择公司后才查询，不扫描公司池、不自动加公司、不刷新或下载数据。
- facts 仅出现在独立的“快扫关系线索/覆盖缺口”展示中，保留 issuer/listing/subject、关系方向、scope、period、source refs、coverage、snapshot 与时间；不能合入主题评分、预测或估值。
- `explore` 始终标为待核线索；`strict` 仅表示符合 wire 的 owner facts，不意味着主题受益结论成立。
- unknown、partial、stale、unsupported、错误响应、完整空响应分别显示。调用失败时主题研究原路径仍可继续；失败不能转成“没有上下游关系”。
- 保留同一发行人多挂牌与不同研究主体的区分，不按公司简称猜身份。
- 只读消费；不触发模型/搜索、不入库、不改观察名单、不读私有源仓 API。

## TDD 与验收

1. 先在主题技能原流程写一个会失败的最小测试：quick-scan 关闭时现有输出不变；开启时在主题候选输出中出现来源/范围/时间和缺口，而原评分/预测结构不变。
2. 定向测试覆盖：strict 与 explore；source reference 丢失/有效；unknown、partial、stale、完整空、CLI 不存在/非零退出/超时/坏 JSON；多挂牌和主体隔离；重复调用不产生刷新/下载/外部副作用。
3. 使用 fake public CLI 与虚构主题、2–4 个虚构公司做一次隔离流程测试，验证原主题流程仍可完成、facts 只进入独立呈现。运行新增和受影响的主题测试及仓库现有包校验（先读其真实帮助/README，不猜命令）。不得要求实 owner 或真实网页作为本包测试条件。
4. 测试只能指向本 Lab/TEMP 下的 fake root。完成后清除本包创建且仍位于这些根内的临时文件；不清理任何源仓/其他 Lab 内容。

## 交接含义

交付表示主题技能源仓候选已接入离线 consumer 并通过合成测试。它不表示本地 canonical 源仓已被总控合并、不表示 F05/W11 当前 owner 已互通，也不关闭 G4。按 [handoff-rules.md](handoff-rules.md) 做一次最终独立 agent 审查；修完全部问题、最终 commit 复审 approved 后，交 `docs/handoff/TH-SOURCE-INTEGRATION-01/report.md` 与 `handoff.json`。
