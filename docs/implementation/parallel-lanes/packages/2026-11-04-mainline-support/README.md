# 2026-11-04 主线支撑施工包

这批只有两包，分别处理 F05 事实/关系查询和 G3 批次接续测试。它们没有共享写入目录，可交给两个不同 harness 并行实施。

施工包规格已由独立审查 agent 只读复核；审查结果和修订记录见[规格审查](package-design-review.md)。这不是代码实施验收。

| 包 | 独立工作目录 | 冻结输入 | 交付目标 |
|---|---|---|---|
| [F05-FACT-QUERY-01](F05-FACT-QUERY-01.md) | `C:\Users\郑曾波\Projects\iqs-stockwiki-f05-query-lab` | StockWiki `d8d3303cb4b91fb6bfc8db6202ea3919276f833e` | 在 StockWiki 本地隔离克隆中补齐版本化事实/关系检索、可解释候选导出与测试。 |
| [G3-BATCH-RESUME-HARNESS-01](G3-BATCH-RESUME-HARNESS-01.md) | `C:\Users\郑曾波\Projects\iqs-g3-batch-resume-harness-lab` | IQS `da557350b0dd11ea92382ad22479f874026d4ad8`；`LOAD-CASE-01` SHA-256 `99E7A7D3C98A07A2F70F7BD6C99E0137CE39F60238EE7AECB9C6E805135E2431` | 给现有批处理入口增加独立的合成端到端接续测试工装；不改 IQS 产品代码。 |

## 两包如何协作

F05 可以独立推进；G3 工装只用 IQS 冻结快照和合成数据，不消费 StockWiki 运行数据。因此两边不写同一仓库、数据库、名单或配置。`TH-IMPL-01`、`IN-IMPL-01` 消费者施工包仍按当前计划等待真实 F05/W11 公共接口；本批任何一包交付都不自动关闭 F05、G3 或消费者验收。

尤其注意：G3 的合成批处理工装用于发现接续、幂等和恢复缺陷，不能替代 200 家真实公司试点，也不授予 G3 通过状态。真实试点仍由总控按 PWF 执行。

## 共用实施与交接规则

- 两个工作目录均为新目录；若已存在或含文件，先确认 owner，不覆盖、不清理。输入基于表中精确 commit，不读取源仓未提交文件或 untracked 运行数据。克隆仅从本地源仓读取；在 Lab 中移除源仓 remote，不 push。
- 每包只改卡片规定的独立 Lab/克隆。不得连接 8766、生产数据库/名单/预算，不下载文档，不调用真实模型、搜索或任何收费 API；G3 使用合成实体和本地 fake provider。
- 按目标项目 `AGENTS.md` 执行。先用能证明目标行为的 RED，再完成实现/工装并跑定向 unit、integration、公开入口 E2E；不要每次迭代跑全套。F05 在 StockWiki 中按其 `scripts/checks.py` 规则做静态与日常验证，是否跑 `--full` 依该仓 major checkpoint 规则，不重复小时级全套。
- 工作完成后由**与作者不同的真实独立 agent**集中审查最终冻结提交，覆盖需求、接口兼容、测试有效性、数据隔离、费用和清理。审查发现的问题由作者全部修复，并对最终提交复审；不能用模拟审查 JSON 代替真实审查。只做这一轮大节点审查，不在每个小步骤增加门禁。
- 交付含本地提交 ID、变更路径、实际命令/结果、接口与输入版本、真实独审证据、未解决事项及临时文件清理状态。按 IQS `docs/implementation/parallel-lanes/handoff.schema.json` 对应字段给出 handoff；测试工装不冒充生产验收。**本批不要求推送到源仓远端。**
