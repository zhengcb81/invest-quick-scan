# IN-IMPL-02｜行业研究消费快扫事实

**lane：** `industry`
**唯一 Lab：** `C:\Users\郑曾波\Projects\iqs-in-impl-02-lab`
**只读 source：** `C:\Users\郑曾波\Projects\industry-research`，`main@98640a9a1f52fc87ba9813676a3cc5ab9bf045c9`
**合同：** IQS `master@acb03e3c084f61ca2b49181180195118077d43e3`，facts wire 2.7.0；详见 [inputs.lock.json](inputs.lock.json)。
**任务映射：** T02；本卡更新旧 `IN-IMPL-01` 的实施基线，不重做已验收 IN-02 只读预研。

`tasks.json` 里的 T02 `depends_on: ["F05", "W11"]` 是真实产品/owner 接入验收依赖；它不阻止本包以冻结 facts 2.7 契约在隔离 Lab 开始离线实现和合成测试。F05/W11 尚未验收时，交付状态只能是离线实现，不得宣称真实 owner 集成完成。

## 目标和边界

在行业研究第6步公司评估中增加可选 IQS facts 输入，并在第7步报告输出有来源、范围、时间、模型和覆盖缺口的事实/关系线索。原行业框架的评分、行业证据、收入预测、估值不与 IQS 分数混合；快扫只辅助公司发现/评估，不直接证明受益或替代深研。

只在本 Lab 改：`SKILL.md`、`modules/company-evaluation.md`、`modules/report-generation.md`、新增/更新本仓风格的 `tools/quick_scan_client.py`、针对性 `tests/` 与合成 fixtures、`docs/handoff/IN-IMPL-02/`。若源仓结构变化，先在允许目录内复用现有入口；不为此改 `config.yaml`、历史 `company_list.json/companies.json`、PDF acquisition、其他技能、IQS/StockWiki、Theme、`local-skills` 或安装镜像。

只读消费本次已选择的 subject/company；不刷新、不下载、不写 StockWiki、不维护名单、不跑全池，也不自动用 LLM/search 补缺。请求失败或能力缺失时明确显示 unavailable/partial，保留旧行业研究流程，不翻译为“行业里没有公司”。

## 调用合同

- 使用 IQS facts schema 2.7.0：`query_facts` / `export_facts`，schema SHA-256 `cd3e03417289a99f5194263603ead6d954fd601b875cd3d5c08a74505ba8cbad`；capabilities 1.1/1.2。版本未知时显式 unsupported。
- owner 命令依冻结候选公开 CLI：在 `<owner-root>` 工作目录运行 `python -B -X utf8 -m stockwiki.quick_scan_query_v2_cli --root <owner-root> --iqs-code-root <iqs-root> --request <request.json>`。通过参数或明确的运行环境传根路径；不硬编码本机目录、不私自导入 StockWiki 模块、不访问 SQLite。Owner query 可能持久化 snapshot/capture，测试 root 必须是本包自有临时 workspace，本包不调用真实 owner root。
- StockWiki 当前 owner runtime 的真实 golden/正反互操作尚未由总控验收。此技能包用 contract fixture/mock CLI 完成实现和独立测试，报告不得把它写成真实 owner E2E；总控后续另做当前 runtime 联调。
- 保留 `analysis_subject_id/revision` 与 `primary_issuer_id`；security/listing/ticker单独呈现。严格事实、探索候选、unknown、unverified、partial 和完整无命中分别处理；关系方向、期间、commercial stage、来源引用、信息截止/观测时间、模型/题包版本与 coverage/snapshot 均不能丢失。不同题包/模型/期间的分数不平均、不排共同名次。

## TDD 与测试案例

1. 在本仓原公司评估入口和报告生成入口分别先写失败断言，证明新增数据为可选来源且不改变旧行业评分或既有报告输出。
2. 单元/契约测试：同 issuer 多挂牌/不同 subject、公司易混名、facts relation 方向、strict/explore、期间/截止日、来源/模型/题包版本、unsupported/unknown/stale、完整空 vs partial 空、分页 snapshot 改变、CLI timeout/错误 JSON。错范围不能合并，空缺不能视为不存在。
3. 隔离端到端：2–4 个虚构公司与小型虚构行业，用 temporary public-CLI stub，从第6步选择 quick-scan source 到第7步报告，验证旧行业量表照常、事实/关系处于独立栏目并有出处/状态，旧模式不启用时报告保持原样。无 PDF/网页下载、网络或费用。
4. 运行本包定向测试、既有受影响报告测试及源仓 `tools/pre_push_gate.py` 的真实帮助中规定的对应项；若该路径或命令变化，按当前真实源码/文档核实，不改门槛。测试数据、workspace、输出全部置于测试 TEMP/Lab。

## 完成与交接

包完成表示 industry-research 能按冻结 2.7 contract 消费 quick-scan facts 并不污染原行业评分/报告，不代表真实 owner 互操作完成。交付前由非作者独立 agent 对最终 commit 做一次集中审查，覆盖 scope、未知/空/错误场景、分数隔离、源引用、报告兼容、测试与清理；作者修复全部发现并由 reviewer 复核最终 commit。交付 `docs/handoff/IN-IMPL-02/report.md` 与 schema 1.0.0 `handoff.json`。不写其它仓库、不推 remote、不运行生产/收费任务。
