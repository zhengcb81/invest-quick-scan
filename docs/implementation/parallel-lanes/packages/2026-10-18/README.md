# 2026-10-18｜三个可独立实施的大施工包（交付完整性 / 成本账本 / 证据时点）

状态：**编制完成，已通过独立复审（2026-10-18）；未派发，未实施**。文档归档提交：`b5f99b4`（其后仅可能追加说明性文字，26 个输入 blob 固定在 `4e001cd`）。本目录只描述范围与验收，不是完成记录，也不自动授权写外仓、读真实数据库、发模型或搜索请求。人类把整张卡交给某个 harness 即认领该卡范围；开工仍须核实际目录、冻结输入和唯一 writer。

编制依据：`2026-10-10/README.md`、`2026-10-10/EVID-REF-02.md`、`2026-10-10/FACT-CONTENT-01.md`、`2026-10-10/handoff-rules.md`、`2026-10-10/manifest.json`（格式与严格度）；`2026-10-18-mainline-support/README.md` 与 `RELEASE-DIFF-10`/`SUMMARY-LOSS-10`/`RELATION-DELTA-10`（边界）；`docs/implementation/reviews/pause-handoff-2026-10-18.md`（主线暂停点与已知缺口）；`task_plan.md` 前 240 行；`docs/implementation/parallel-lanes/README.md`、[handoff schema](../../handoff.schema.json)、`scripts/parallel_handoff_cli.py`（唯一交接协议与预检入口）。

## 三包一览

| 包 | 做完得到什么 | 唯一工作根 | 输入类型 |
|---|---|---|---|
| [DELIVERY-AUDIT-11](DELIVERY-AUDIT-11.md) | 交付目录哈希闭包、自指检测与薄证据泄漏审计器，可重放真实 handoff 语料 | `C:/Users/郑曾波/Projects/iqs-delivery-audit-lab` | 本仓 tracked handoff/schema/规则文档 + 两个历史 package catalog |
| [COST-LEDGER-11](COST-LEDGER-11.md) | 只读成本账本审计：unpriced/uncertain、预约泄漏、重复 attempt、费率卡对账、per-policy/per-route 归因 | `C:/Users/郑曾波/Projects/iqs-cost-ledger-lab` | 本仓 tracked 预算/费用/账本导出 JSON(JSONL) |
| [EVIDENCE-TIMELINE-11](EVIDENCE-TIMELINE-11.md) | 薄证据时点一致性审计：发布时间、抓取时间、信息截止、epoch 与回溯冲突 | `C:/Users/郑曾波/Projects/iqs-evidence-timeline-lab` | 本仓 tracked source index/catalog/参考事实 JSON |

三个工作根均不存在（编制时已核），互不包含，也都不包含 IQS / StockQAbyLLM / StockWiki / company-wiki / 既有 `iqs-*-lab`。三包互不等待、不共享可写库、缓存、端口或临时根；任一包未开工，其他包仍可独立完成。

## 协议与共同约定（本批）

- **交接协议**：只用 [handoff.schema.json](../../handoff.schema.json) 1.0.0（`scripts/parallel_handoff_cli.py` 实际校验的那份）。不使用 `integration-contract.md` §4 的 `support_handoff/1.0.0` 字段，不产出 `input-catalog.json`；真实文件集见 [handoff-rules.md](handoff-rules.md) 第一节。
- **退出码**：统一采用 `integration-contract.md` §2 的四档语义（0 成功诊断 / 1 仅 evaluate 不符 / 2 输入与用法非法 / 3 分析无法执行）；旧卡的其余码值已按该表并入，映射见 [handoff-rules.md](handoff-rules.md) 第三节。
- **写范围**：三包的 `authorized_relative_paths` 均含 `rules` 与 `vendor`；输入按 `vendor/iqs/<仓库相对路径>` 布局只读挂载。
- **task_ids 只是支撑关系**：`manifest.json` 的 `task_ids` 表示"本卡为这些计划任务提供离线候选工具"，**不表示这些任务完成**。DELIVERY-AUDIT-11 声明 `X09` 仅为支撑（离线端到端验收的交付侧检查），X09 本身不因此关闭；`B01` 只由 COST-LEDGER-11 声明，EVIDENCE-TIMELINE-11 不重复声明。

## 与在跑工作的边界

- 已派发三包继续按活动 writer 对待：`RELEASE-DIFF-10`（module release 版本差异与历史兼容）、`SUMMARY-LOSS-10`（摘要字段保真与遗漏）、`RELATION-DELTA-10`（跨时点关系观察：item 级精确配对、scope/method 校验、change classification，以及"未重观测≠终止"）。本批三包不读、不写、不重建它们的输入、产物与结论。
- 主线由总控负责 saved-research publication、schema24→25、store-ID/namespace、真实摘要与恢复。本批不接管、不代改：DELIVERY-AUDIT 只审交付物本身，不判发布可执行；COST-LEDGER 只算已导出行，不领预算、不结算真实费用、不碰 DB；EVIDENCE-TIMELINE 只核已导出证据的时点，不联网取新来源。
- 明确排除的重复项：release/module/question 兼容（RELEASE-DIFF-10）、摘要保真（SUMMARY-LOSS-10）、关系配对与时间排序（RELATION-DELTA-10）、身份内容边界（IDENT-EDGE-01）、故障注入与发送/预约语义（RESUME-CHAOS-06）、指标口径与证据蕴含（CLAIM-GUARD-04）、行业分类映射（TAXONOMY-CROSSWALK-09）、多语言/时区条款（LOCALE-ROBUSTNESS-09）、上下文打包（SESSION-PACK-04）。

## 接手只需读这些

每个 harness 从自己施工卡读起，卡内链接全部必要规则，不依赖聊天记录。共同必读：[本批交接与隔离规范](handoff-rules.md)、[输入锁](inputs.lock.json)、[本批 manifest](manifest.json)、[交接 schema](../../handoff.schema.json)。§1–§3/§5 的通用约束见 [三包共同契约](../2026-10-18-mainline-support/integration-contract.md)（其 §4 字段集不适用）。

冻结输入来自本仓 Git 对象：`source_commit=4e001cd18d229a60de54d56ce6ecd23f8bc00cae`。本批施工卡为**待归档**状态：整改完成后由总控提交，归档提交号由总控事后更新，文档内不预写。每卡列 path / Git blob OID / bytes / sha256；`inputs.lock.json` 汇总 26 个冻结对象并另列 unsupported 项。

## 交回哪里、怎样预检

各包在自己仓库 `docs/handoff/<package-id>/` 交付，不得写入 IQS 根 PWF、其他包目录或既有 Lab。总控在 IQS 根运行既有公开预检入口：

```powershell
python -B -X utf8 scripts/parallel_handoff_cli.py --catalog docs/implementation/parallel-lanes/packages/2026-10-18/manifest.json --package-id DELIVERY-AUDIT-11 --input C:/Users/郑曾波/Projects/iqs-delivery-audit-lab/docs/handoff/DELIVERY-AUDIT-11/handoff.json
python -B -X utf8 scripts/parallel_handoff_cli.py --catalog docs/implementation/parallel-lanes/packages/2026-10-18/manifest.json --package-id COST-LEDGER-11 --input C:/Users/郑曾波/Projects/iqs-cost-ledger-lab/docs/handoff/COST-LEDGER-11/handoff.json
python -B -X utf8 scripts/parallel_handoff_cli.py --catalog docs/implementation/parallel-lanes/packages/2026-10-18/manifest.json --package-id EVIDENCE-TIMELINE-11 --input C:/Users/郑曾波/Projects/iqs-evidence-timeline-lab/docs/handoff/EVIDENCE-TIMELINE-11/handoff.json
```

该入口只检形状与自述范围，不鉴定真实授权、测试通过或业务真值。三包都必须：一个最终 payload commit 交独立 agent 全量审查并复审到 `passed`/`open_findings=[]`，之后只做 handoff 元数据提交；`complete` 只表示本卡限定交付完成。

## 本批不做

不新增生产门，不调模型/搜索/网页，不下载公司文档，不读密钥或环境变量中的凭据，不接真实数据库、股票池、名单或发布指针，不关闭 G3/F05/C06/L03/2000 家/一键启动，不替总控改任何产品仓。三包全部 `data_kind=offline_candidate`、`production_qualified=false`。
