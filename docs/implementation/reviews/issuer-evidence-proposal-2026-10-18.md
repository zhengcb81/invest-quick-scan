# 逐发行人证据提案 — 2026-10-18

状态：**提案，未批准**。用于验证“选项 A：采集官方逐发行人页面/年报链接”的可行性；没有下载正文，没有写 verified，没有改库。

## 为什么需要

verified 身份要求逐发行人官方文件 + 法人全称 + owner 批准；现有安全主数据只有交易简称。

## 试点提案（万科A / 000002）

- 法人全称候选：**万科企业股份有限公司**
- 官方证据候选（深交所官方域名）：
  1. `https://disc.static.szse.cn/download/disc/disk03/finalpage/2026-05-23/cf6e2da9-774a-4bf2-9434-70b717637f2e.PDF`（搜索结果标题含“vanke 万科企业股份有限公司 CHINA VANKE CO., LTD.”）
  2. `https://disc.static.szse.cn/download/disc/disk03/finalpage/2025-04-01/ba90b1be-81e2-4fcb-946a-b9eedad9d324.PDF`
  3. 深交所公告页：`https://www.szse.cn/disclosure/listed/bulletinDetail/index.html?102db877-c152-4ffe-8c55-e5fe40937eb1`
- 次级溯源：cninfo 目录 `https://www.cninfo.com.cn/new/data/szse_stock.json`
- 本提案只记录 URL/标题/法人名候选，**没有抓取或保存 PDF 正文**。

## 流程（若批准 A）

1. 对每家公司检索官方域名（szse/sse/cninfo/hkex/sec）上的年报/公告链接；
2. 记录法人全称候选 + 1–3 个官方 URL + 检索标题作为证据；
3. owner 为每批批准一个证据 URL（或确认规则：以交易所公告页为准）；
4. 用批准的 URL + 法人全称构建 verified payload（revision 2），先 1 家 → 5 家 → 分批；
5. 不保存正文，不把目录级 URL 当逐发行人证据。

## 需要的批准

- 是否允许按上述流程联网检索（只存 URL/名称，不存正文）；
- 或提供法人主体清单/授权数据源（选项 B）。

提案 JSON：`runs/existing-list-onboarding-2026-10-18/evidence-proposals/CN-A_000002.json`。
