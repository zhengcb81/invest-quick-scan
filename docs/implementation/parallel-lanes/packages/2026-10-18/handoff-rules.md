# 本批共同施工与交接规范

本文件**不是**新规则集。完整规则仍以 [2026-10-10 共同规范](../2026-10-10/handoff-rules.md) 为准，本批只声明差异与收紧项；两者冲突时以"更严格且更具体"者为准，并先交总控裁定。接口、目录、审查、commit 字段语义同时受 [三包共同契约](../2026-10-18-mainline-support/integration-contract.md) 约束。

## 一、与 2026-10-10 的共同部分（照用，不重述）

唯一写根与 allowlist、开工前读 AGENTS 与记录 Git root/HEAD/branch 与完整 status、独占 `docs/handoff/<package-id>/planning/`、输入锁与 raw SHA、先 RED 后最小实现、一次集中回归与一次集中审查、唯一短临时根与子进程隔离、保留首败与终版 GREEN 原日志、只 `git add` 精确路径、正常 hooks 不跳过、`docs/handoff/<package-id>/` 必交文件集（handoff.json、summary.md、artifacts.json、interfaces.md、case-map.md、logs/、isolation.md、planning/）、`complete` 不得冒称生产准入——以上全部沿用。

## 二、本批差异（必须遵守）

1. **输入来源**：本批只从 IQS 仓库 Git 对象读输入（`git cat-file blob <oid>`），source_commit 见 [输入锁](inputs.lock.json)。**不读 IQS 活动工作树、不 checkout 源仓、不转换换行**。三包都不新建 remote，也不推送外仓。
2. **零网络、零付费、零模型**：三包全程离线，不调用任何模型/搜索/网页/API，不读环境变量中的 provider 凭据，不下载公司文档。`network_calls=false`、`paid_calls=false` 是交付要求，不是观察结论；任何一次外呼即违规。
3. **零数据库**：不以真实 SQLite/生产 DB/生产名单为输入。COST-LEDGER 只吃本仓 tracked 的导出 JSON/JSONL；EVIDENCE-TIMELINE 只吃本仓 tracked 的薄证据 JSON；DELIVERY-AUDIT 只吃交付目录文件。不得以"只读方式打开真库"替代导出。
4. **不复制真实内容**：不得把真实 namespace、真实库副本、答案正文、隐藏思考、完整网页/财报正文、密钥或准入令牌复制进本包仓库、fixtures、日志或交接。真实 tracked 导出只作只读输入，fixture 一律标注 `synthetic` 并带 `fixture_class`。
5. **免责边界**：三包都是候选工具，输出固定 `data_kind=offline_candidate`、`production_qualified=false`，并各自在 `limitations` 写清不能证明什么（不得鉴定授权、金融真值、来源真实性、真实费用结算或合规）。"未发现问题"不得写成"安全/准确/合规"。
6. **不越界消费**：不读、不写、不重建已派发三包（RELEASE-DIFF-10 / SUMMARY-LOSS-10 / RELATION-DELTA-10）与既有 `iqs-*-lab` 的任何内容；不消费主线未交付候选。若开工发现目标工作根已存在且非空，只读核对是否为本卡接续，无法确认即记 `writer_conflict` 并停止写入该根。
7. **不接管主线**：三包都不改 IQS/StockQA/StockWiki/company-wiki 源码、题库、路由、发布指针、预算或名单，也不关闭 G3/F05/C06/L03 或任何生产门。
8. **交接字段**：`handoff.json` 沿用 1.0.0 形状；`lane_id=iqs` 只表示本批为 IQS 支撑，不授予 IQS 写权；`result_commit` 不能为 null 而自称 complete。额外要求见各卡"独立审查要求"一节。

## 三、独立审查（本批强制）

按 [共同契约 §5](../2026-10-18-mainline-support/integration-contract.md)：作者必须调用**真正不同的独立 reviewer agent** 全量审查，不得自扮。`docs/handoff/<ID>/review/` 至少含 `invocation-evidence.json`（平台、作者与 reviewer id 必须不同、UTC 实际调用时间、可打开的原始调用/返回引用；拿不到就填 null 并说明，不伪造）、`round-XX.json|md`（原始 findings、严重性、复现、依据）、`fixes.json`（逐项修复 commit 与复验结果）、`final.json`（`verdict=passed`、`open_findings=[]`、`reviewed_commit`）。复审必须由同一 reviewer 跨 round 到 `passed` 才可交接；`changes_requested`/`blocked` 如实保留。

## 四、总控只做一次集中接收

总控按 `scripts/parallel_handoff_cli.py` 预检形状后，另核 payload commit、输入 blob/SHA、测试分母、review 证据、清理证明与是否越界写。三包各一次集中接收，不设逐 helper 门；预检通过不等于业务正确或生产就绪。
