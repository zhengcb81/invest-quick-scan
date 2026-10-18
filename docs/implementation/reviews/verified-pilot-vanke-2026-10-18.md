# verified 身份试点结果：万科A — 2026-10-18

状态：**试点已写入真实 workspace**；等待独立复审通过后再做 5 家与批量。

## 批准

- Owner 批准证据规则：**以交易所官方公告页/年报为准，逐公司一条，只存 URL/法人全称，不保存正文**；owner approval id = `existing-list-verified-2026-10-18`。

## 执行结果

| 项 | 值 |
|---|---|
| 公司 | 万科A（CN-A:000002） |
| entity | `ENT_b63a2d90-5165-49a1-a36b-95a0d57ce534` |
| 法人全称 | **万科企业股份有限公司**（交易简称“万科A”保留在 source binding） |
| 身份 | verified，revision 2 |
| IVR 回执 | `IVR_02b6a702018d54ef9e9de4be0896f6b2` |
| 证据 | 深交所官方年报 PDF：`https://disc.static.szse.cn/download/disc/disk03/finalpage/2025-04-01/ba90b1be-81e2-4fcb-946a-b9eedad9d324.PDF` |
| 计数 | entity 214（不变）、security 217（不变）、binding 218（不变）、verified 2→3、receipt 217→218、candidate 216（不变） |
| 幂等重放 | 同一 payload 再来一次：exit 0、同 receipt、计数完全不变 |

## 已做的检查

- 写前备份两份 SQLite（scan + identity_receipts）。
- 导入前校验 owner approval、IVR、revision、payload 字节。
- 导入后逐项断言：法人名/状态/revision/IVR、交易简称保留、四类计数、候选不变。
- 重放后计数与状态不变。

## 边界

- provisional_scope 回执保留，未删除历史；实体行在 rev2 覆盖（无 identity_event，见既有审查结论）。
- verified 只是 checkpoint 的 identity 前置；评分仍需 search-backed checkpoint 与金融复核。
- 本试点只写 1 家；5 家与批量需本轮独立复审通过。

## 证据文件（本机）

`runs/existing-list-onboarding-2026-10-18/verified-pilot-vanke.json`、`payloads-verified-pilot/CN-A_000002.verified.json`、`backup-verified-pilot-vanke/`。
