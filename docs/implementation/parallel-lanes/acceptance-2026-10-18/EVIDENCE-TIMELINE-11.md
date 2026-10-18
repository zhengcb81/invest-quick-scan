# EVIDENCE-TIMELINE-11 验收记录

- 验收时间：2026-10-18（本会话复核）
- 交付方：外部 Lab C:/Users/郑曾波/Projects/iqs-evidence-timeline-lab，分支 codex/evidence-timeline-11
- payload commit：c66a915a45cbc6dc797f97c18b746f877e1eb7dc
- metadata commit：2e82d9f4ef6f626b205100fab95323818f01cb0f
- handoff 状态：complete
- 独立评审：approved（round-01 10 项发现全部 fixed_verified；round-02 两个 accepted_as_known_edge）

## 总控复核（本会话实际执行）

| 检查 | 命令/方式 | 结果 |
|---|---|---|
| handoff 形状/声明范围 | scripts/parallel_handoff_cli.py --catalog docs/implementation/parallel-lanes/packages/2026-10-18/manifest.json | valid，errors=[] |
| handoff artifacts 哈希 | 逐项重算 sha256/bytes | 25/25 匹配，0 mismatch |
| 单元+E2E | python -m pytest -q（lab 根） | exit 0，75 dots 全过 |
| casebook | python -B -X utf8 -m iqs_evidence_timeline evaluate --cases content/casebook.json ...（PYTHONPATH=src） | 24/24 passed, 0 failed，exit 0 |
| 基线复算 | python -B -X utf8 tools/verify_baseline.py（PYTHONPATH=src） | 11/11 OK，exit 0 |

## 接口裁定

1. sources[] 实际为 14 个必填键：卡 line 46 的 11 键 + period_source、period_start、period_end。
   - 裁定：接受为显式扩展（integration-map §2 已说明）。但 consumer 接入前必须二选一：
     - 把 request protocol 升为 iqs.evidence_timeline_request/1.1.0；或
     - consumer 显式按 14 键闭合读取。
   - 当前 IQS 无该 consumer，故不阻塞交付。
2. 报告协议 iqs.evidence_timeline_report/1.0.0 闭合 payload 与四通道 counts 守恒符合卡 line 60–67。
3. production_qualified=false、data_kind=offline_candidate 固定，不得当生产资格。

## 已知边界（接受）

- 真实语料偏窄：ET-03/04/06/07/08/09 阳性触发依赖 synthetic=true 夹具（卡 line 108 已声明）。
- R2-01：duplicate_source_id 的 url 缺失对称性仍会触发，冻结语料 0 例；后续一轮一行修复。
- R2-02：cutoff>=epoch 且全行裸时间戳时 epoch>observed 不可见；失败止于 unassessable。
- back-freeze 占位 docs/handoff/EVIDENCE-TIMELINE-11-evidence-pack.json 编制时不存在；待 EVID-REF-02 的 30 槽参考包出现后，按其内容复跑 baseline 与 evaluate。

## 决定

ACCEPTED — 离线工具交付合格，非生产资格，不合并进 IQS 产品代码。

后续动作：
1. 若要接入 IQS，先完成 14 键接口版本化与 consumer 适配；
2. EVID-REF-02 参考包出现后复跑基线/casebook；
3. R2-01/R2-02 留待下一轮低风险修复。

## 证据位置

- Lab handoff：C:/Users/郑曾波/Projects/iqs-evidence-timeline-lab/docs/handoff/EVIDENCE-TIMELINE-11/
- 包卡：docs/implementation/parallel-lanes/packages/2026-10-18/EVIDENCE-TIMELINE-11.md
