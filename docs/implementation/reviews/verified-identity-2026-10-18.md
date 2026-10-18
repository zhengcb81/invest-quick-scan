# 已验证身份（verified issuer）批 — 写前报告 — 2026-10-18

状态：**写前报告，未写真实 workspace**。目的：把现有列表里的 provisional 实体升级为 verified，解锁正式 checkpoint / 评分 / 出版；先做 1 家（万科A）试点，通过后再批量。

## 为什么需要

- 共享引擎的 checkpoint 校验、评分与 publication 都要求 `identity_state == "verified"`；provisional 只能创建 work，不能产出正式可读 checkpoint。
- 现有 214 实体中 212 个是 provisional（本批导入），2 个既有 verified。
- 因此“公司画像与评分生产入口”的前置是：把要扫描的公司升级为 verified。

## 试点范围与证据

- 对象：`CN-A:000002` 万科A（entity `ENT_b63a2d90-5165-49a1-a36b-95a0d57ce534`），已有 1 个 provisional_scope 回执（rev1）。
- 证据：company-wiki 安全主数据的官方目录 URL（cninfo `https://www.cninfo.com.cn/new/data/szse_stock.json`），记录该 ticker 的官方 listing 归属；**这是目录级证据，不是逐发行人公告页**，报告如实标注。
- 方法：新构建 `IVR_` verified_issuer 回执，`same_legal_issuer=true`、`identity_revision=2`、`entity.verified_issuer_receipt_id=IVR_`、`recorded_at` 固定；实体升到 revision 2 / verified。
- 不删除原 provisional 回执；不覆盖历史；不改候选表。

## 隔离预演（已完成）

- 在真实 workspace 的副本 `runs/existing-list-onboarding-2026-10-18/verified-pilot-rehearsal` 上导入万科A verified payload：
  - 首次 `capacity_status=entity_saved_receipt_recorded`，receipt `IVR_33408e42dd1c6ec38abe1894d540db5d`；
  - 完全相同 payload 重放：exit 0、receipt 相同、零新增；
  - 实体落库 `verified / revision 2 / IVR_33408e42…`；回执计数 verified_issuer 2→3。
- 关键教训：同一 revision 改内容会被拒（`same identity revision replay with different content`），必须 bump 到 revision 2。

## 真实写入计划

1. 写前备份 scan.sqlite 与 identity_receipts.sqlite（字节 + 计数 + SHA），确认无 -wal/-shm。
2. 只写 1 家：导入万科A verified payload；复验实体 state/revision/IVR、回执计数 +1、候选表与其它实体不变；重放一次确认零新增。
3. 通过独立复审后，再按同一 payload 规则批量升级剩余 210 家（跳过 2 家既有 verified：Alphabet、CATL；中信建投 H 是 provisional，可一并升级）。
4. 批量按 ≤60/批，逐文件回执、每批计数校验、全量校验 expected = before + N；任一不符中止。
5. 升级后再验证 G2b 导出仍成功，并抽样确认正式 checkpoint 路径不再因 identity_state 被拒。

## 必须拒绝 / 边界

- 不把目录级证据说成逐发行人公告；不在同一 revision 改身份事实；不删除 provisional 回执。
- 不用 verified 升级替代金融准确性、search-backed 评分或正式投资结论。
- 不做 paid 调用、不搜索、不下载公司文档。
- 批量前必须完成独立审查；失败按备份恢复。

## 审查问题

1. 官方目录 URL（cninfo/SEC bulk catalog）是否足以支撑 verified_issuer 的 `same_legal_issuer` 证据？是否要求逐发行人页面？
2. revision 2 升级是否保留了原 provisional 历史与可追溯性？重复导入是否幂等？
3. 批量 211 的写范围、备份、分批与回滚是否足够？
4. 是否存在“verified 等于准确/可评分”的越界表述？
