# verified 身份批量（cninfo 口径）— 结果 — 2026-10-18

状态：**SH/SZ 批量已写入真实 workspace**；US/HK/BSE 按审查意见暂不升级。

## 口径与闸门

- 证据：cninfo 逐公司概况 API（`p_sysapi1133`，公司全称 + A股代码 + A股简称）+ 逐公司 cninfo 页面 URL；不下载文档。
- 名称闸门：官方 **A股简称** 与 source_binding 的交易简称归一化后一致（NFKC、去空格）；不一致视为改名/歧义，跳过。
- 代码闸门：API A股代码 == ticker；orgId == source_record_id。
- 抓取：逐家、重试 ≤2、间隔 ≥1s、不并行；失败/空/歧义 → 跳过并记录。
- 写入：逐文件、≤60/批、失败即停；写后校验 verified/rev2/IVR 与实体一致；每批计数校验 + 抽样重放；写前双库备份。
- 证据留存：200 份逐公司概况响应 + sha256 + fetched_at + endpoint 存 `docs/implementation/evidence/verified-identity-2026-10-18/cninfo-profiles.jsonl`。

## 结果

| 项 | before | after |
|---|---|---|
| entity | 214 | 214 |
| security | 217 | 217 |
| binding | 218 | 218 |
| candidate | 216 | 216 |
| verified | 8 | **202** |
| identity receipt | 223 | **417** |

- 首批 194 份 payload：150 家写入；44 家因严格“公司名包含简称”被跳过。
- 复核发现这 44 家是合法品牌简称（如工业富联/富士康工业互联网），改用官方 A股简称闸门后全部通过：44 家写入。
- 最终 CN：**201 verified / 205**（4 个缺口，见下）；全库 202 verified / 214。

## 剩余缺口（保持 provisional，不猜）

| market | ticker | 名称 | 原因 |
|---|---|---|---|
| CN | 002013 | 中航机电 | cninfo 概况 API 返回空（疑似已吸收合并/退市） |
| CN | 300114 | 中航电测 | 同上（疑似已更名/重组） |
| CN | 688555 | 退市泽达 | 已退市，概况为空 |
| CN | 872808 | 曙光数创 | 北交所，cninfo/东财均无免费概况 |
| HK | 06066 | 中信建投证券 | 需 HKEX/HKEXnews 官方页，东财 F10 被审查否决 |
| US | 7 家 | FIG/GENB/MDB/MSFT/NVO/SNOW/TAL | 需 SEC 逐公司 submissions/CIK JSON，bulk tickers 不足 |

## 边界

- verified 仅表示身份，不代表财务准确、可评分或投资结论；评分仍需 search-backed checkpoint 与金融复核。
- 2026-10-18 真实库：202 verified / 12 provisional / 2 条观察 / 0 真实搜索。
- 备份：`runs/existing-list-onboarding-2026-10-18/backup-verified-cninfo-batch/`；回滚 = 恢复两份 SQLite。
