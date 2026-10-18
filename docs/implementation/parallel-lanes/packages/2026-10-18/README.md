# 2026-10-18｜三个可独立实施的大施工包（交付完整性 / 成本账本 / 证据时点）

状态：**编制完成，未派发，未实施**。本目录只描述范围与验收，不是完成记录，也不自动授权写外仓、读真实数据库、发模型或搜索请求。人类把整张卡交给某个 harness 即认领该卡范围；开工仍须核实际目录、冻结输入和唯一 writer。

编制依据：`2026-10-10/README.md`、`2026-10-10/EVID-REF-02.md`、`2026-10-10/FACT-CONTENT-01.md`、`2026-10-10/handoff-rules.md`、`2026-10-10/manifest.json`（格式与严格度）；`2026-10-18-mainline-support/README.md`、`integration-contract.md` 与 `RELEASE-DIFF-10`/`SUMMARY-LOSS-10`/`RELATION-DELTA-10`（边界）；`docs/implementation/reviews/pause-handoff-2026-10-18.md`（主线当前暂停点与已知缺口）；`task_plan.md` 前 240 行（已交付节点）；`docs/implementation/parallel-lanes/README.md`、`handoff.schema.json`、`scripts/parallel_handoff_cli.py`（既有工具与预检入口）。

## 三包一览

| 包 | 做完得到什么 | 唯一工作根 | 输入类型 |
|---|---|---|---|
| [DELIVERY-AUDIT-11](DELIVERY-AUDIT-11.md) | 交付目录的哈希闭包、自指检测与薄证据泄漏审计工具，可重放真实 handoff 语料 | `C:/Users/郑曾波/Projects/iqs-delivery-audit-lab` | 本仓 tracked handoff/schema/规则文档 |
| [COST-LEDGER-11](COST-LEDGER-11.md) | 只读成本账本审计：unpriced/uncertain、预约泄漏、重复 attempt、费率卡对账、per-policy/per-route 归因 | `C:/Users/郑曾波/Projects/iqs-cost-ledger-lab` | 本仓 tracked 预算/费用/账本导出 JSON(JSONL) |
| [EVIDENCE-TIMELINE-11](EVIDENCE-TIMELINE-11.md) | 薄证据来源时点/截止日/epoch 一致性审计：发布时间、抓取时间、信息截止、回溯冲突 | `C:/Users/郑曾波/Projects/iqs-evidence-timeline-lab` | 本仓 tracked source index/catalog/参考事实 JSON |

三个工作根本目录均不存在（编制时 2026-10-18 已核），互不包含，也都不包含 IQS / StockQAbyLLM / StockWiki / company-wiki / 既有 `iqs-*-lab`。三包互不等待、不共享可写库、缓存、端口或临时根；任一包未开工，其他包仍可独立完成。

## 与在跑工作的边界

- 已派发三包继续按活动 writer 对待：`RELEASE-DIFF-10`（module release 版本差异）、`SUMMARY-LOSS-10`（摘要字段保真）、`RELATION-DELTA-10`（跨时点关系观察）。本批三包**不读、不写、不重建**它们的输入、产物与结论，也不消费其未交付内容。
- 主线由总控负责 saved-research publication、schema24→25、store-ID/namespace、真实摘要与恢复。本批不接管、不代改：DELIVERY-AUDIT 只审交付物本身，不判定发布是否可执行；COST-LEDGER 只算已导出账本行，不领预算、不结算真实费用、不碰任何 DB；EVIDENCE-TIMELINE 只核已导出证据的时点一致性，不联网、不取新来源。
- 明确排除的重复项：release/module/question 兼容（RELEASE-DIFF-10）、身份内容边界（IDENT-EDGE-01）、故障注入与发送/预约语义（RESUME-CHAOS-06）、指标口径与证据蕴含（CLAIM-GUARD-04）、行业分类映射（TAXONOMY-CROSSWALK-09）、条款/时区多语言（LOCALE-ROBUSTNESS-09）、上下文打包（SESSION-PACK-04）。

## 接手只需读这些

每个 harness 从自己施工卡读起，卡内链接全部必要规则，不依赖聊天记录。共同必读：[本批交接与隔离规范](handoff-rules.md)、[输入锁](inputs.lock.json)、[本批 manifest](manifest.json)、[既有 handoff schema](../handoff.schema.json)、[三包共同契约](../2026-10-18-mainline-support/integration-contract.md)。

冻结输入来自本仓 Git 对象（source_commit `4e001cd18d229a60de54d56ce6ecd23f8bc00cae`），不读活动工作树。每卡列 path / Git blob OID / bytes / sha256；输入锁可由实施者按卡内清单重建后逐项核对。

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
