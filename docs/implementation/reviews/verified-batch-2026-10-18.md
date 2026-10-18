# verified 身份批量（cninfo / SEC 口径）— 结果 — 2026-10-18

状态：**完成**；独立复审对身份结果判 pass，5 项证据/审计必改项已闭合。

## 口径与闸门

- CN 证据：cninfo 逐公司概况 API（p_sysapi1133：公司全称 + A股代码 + A股简称）+ 逐公司 cninfo 页面 URL；不下载文档。
- US 证据：SEC 逐公司 submissions JSON（CIK##########.json：registrant name + tickers）。
- 名称闸门：官方 A股简称与 source_binding 交易简称 NFKC 归一化后一致（equal/contains 才写入）。
- 代码闸门：API A股代码 == ticker；orgId == source_record_id；SEC ticker 必须在 tickers 列表。
- 抓取：逐家、重试 ≤2、间隔 ≥1s、不并行；失败/空/歧义跳过记录。
- 写入：逐文件、≤60/批、失败即停；写后校验 verified/rev2/IVR；每批计数 + 抽样重放；双库备份。

## 结果

| 项 | before | after |
|---|---|---|
| entity | 214 | 214 |
| security | 217 | 217 |
| binding | 218 | 218 |
| candidate | 216 | 216 |
| verified | 8 | **209** |
| identity receipt | 223 | **424** |

CN 201/205、US 11/11、HK 0/1。

**算术**：CN 201 = 194 家 cninfo 批量 + 5 家 cninfo 试点 + 万科A（SZSE 年报）+ CATL（更早 verified）。194 家里首批 150 写入、44 家因严格“公司名包含简称”跳过；改用官方 A股简称闸门后 44 家全部写入——**44 是 194 的子集，不是额外 44 家**。

## 证据与审计

- cninfo：200 条逐公司概况（200/200 response sha 重算一致；200/200 带 official_short 与逐条 name_gate；原始字符串差异 2 条）。
- SEC：7 条概况 + 7 份完整 submissions（sha 与归档一致）。
- 审计脚本 `scripts/verified_evidence_audit.py`：**207 通过 / 0 失败 / 2 家 pre-existing**。
  - 审计新增：A股代码 == ticker、orgId == source_record_id、名称 gate、万科A URL stockCode/orgId、SEC ticker_listed。
  - pre-existing：Alphabet（SEC 10-K https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm，IVR_663efa01…）、CATL（https://www.catl.com/about/profile/，IVR_d5c63122…）。
- G2b 样例：000026 飞亚达导出成功（schema 2.2.0、verified、IVR_3ca69a28…、CN/XSHE），sha256 965e166a8697dfa58b2ea136a23642199f49651f72977239536b2599b036a369。

## 剩余缺口

见 [verified-gap-register-2026-10-18.md](verified-gap-register-2026-10-18.md)：002013、300114（cninfo 空，复审意见为合并/更名，未独立核实）、688555（退市）、872808（北交所无免费官方源）、06066（HKEX 官方页未取得）；第三方聚合不作证据。

## 边界

- verified 仅表示身份；不代表财务准确、可评分或投资结论。
- 2026-10-18 真实库：**209 verified / 5 provisional** / 2 条观察 / 0 真实搜索 / 0 模型调用（本轮）。
- 备份：`runs/existing-list-onboarding-2026-10-18/backup-verified-cninfo-batch/`、`backup-verified-sec/`；回滚 = 恢复两份 SQLite。
