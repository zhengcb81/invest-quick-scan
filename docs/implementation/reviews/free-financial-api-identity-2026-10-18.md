# 免费金融 API 身份核验调研 — 2026-10-18

目的：用免费、无需登录的金融 API 获取上市公司**法人全称 + 代码 + 交易所**，替代逐份年报检索；需要登录/token 的单独标注。

## 实测结果（本机联网）

| 来源 | 接口 | 返回 | 登录 | 覆盖 | 实测 |
|---|---|---|---|---|---|
| **巨潮资讯（cninfo，指定披露平台）** | `webapi.cninfo.com.cn/api/sysapi/p_sysapi1133`（AkShare `stock_profile_cninfo`） | **公司名称（法人全称）**、A股代码、A股简称、上市日期、所属市场、行业 | **不需要** | 深/沪 | 000002 万科企业股份有限公司、300750 宁德时代新能源科技股份有限公司、600519 贵州茅台酒股份有限公司；单次 1–3 秒 |
| 东方财富 F10 | `emweb.securities.eastmoney.com/PC_HSF10/CompanySurvey/PageAjax?code=SZ000002` | ORG_NAME 法人全称、简称、ORG_CODE、SECUCODE | **不需要** | 深/沪 | 000002 万科企业股份有限公司、600519、300750、688981 均返回 |
| SEC EDGAR | `https://www.sec.gov/files/company_tickers.json` | CIK、ticker、**title（法人名）** | **不需要**（带 User-Agent） | 美股 | Alphabet Inc. 等 |
| 东方财富港股 F10 | `emweb.securities.eastmoney.com/PC_HKF10/CompanyProfile/PageAjax?code=06066` | `gszl.gsmc` 法人全称、ISIN、上市日期 | **不需要** | 港股 | 06066 → 中信建投证券股份有限公司 |
| Tushare | `stock_basic`（含 fullname） | 法人全称、上市状态等 | **需要 token/注册** | A股/港股/美股 | 未安装、无 token |
| BaoStock | SDK | 代码、简称、上市日期 | 需要 SDK 匿名登录 | A股 | 未安装；通常只有简称 |
| Wind / iFinD / Choice | 商业终端 | 全量 | 付费/账号 | 全市场 | 不可用 |

## 覆盖结论（现有 214 家）

- 深/沪 204 家：cninfo 或东财 F10 可拿法人全称（万科、宁德、茅台、中芯国际等已验证）。
- 北交所 1 家（872808 曙光数创）：cninfo `p_sysapi1133` 返回空、东财 F10 报“股票代码不合法”，**目前是缺口**（可另找北交所接口，或先跳过）。
- 港股 1 家（06066 中信建投 H）：东财港股 F10 可拿法人全称（中信建投证券股份有限公司）。
- 美股 11 家：SEC EDGAR 官方 JSON 可拿法人名（Alphabet Inc. 等），无需登录。

## 建议的证据口径（需确认）

- CN：以 **cninfo 逐公司概况（p_sysapi1133）返回的公司全称 + A股代码** 为准；`evidence_ref` 用**逐公司 cninfo 页面**（`https://www.cninfo.com.cn/new/disclosure/stock?stockCode=<code>&orgId=<master org_id>`，官方指定披露平台），并把 API 响应 sha256、抓取时间写进 provenance。
- US：SEC EDGAR 公司页/JSON（官方）。
- HK：HKEX 页面或东财港股 F10（后者非官方，需确认）。
- 这样不再逐份下载年报，也不需要登录；但证据从“交易所年报 PDF”变成“官方披露平台逐公司概况页 + API 响应哈希”，需要你确认这个口径。

## 需要登录/token 的（如果你有，告诉我）

- **Tushare**：注册 token 后可批量拿 `fullname`，覆盖北交所更稳；免费额度有限。
- 其他商业源（Wind/iFinD/Choice）需账号。

## 下一步（待确认口径）

1. 批准用 cninfo 逐公司概况页 + API 响应哈希作为 CN verified 证据；
2. 我按 5 家试点 → 独立复审 → 分批（204 家深沪；北交所 1 家单列缺口；港股/美股走各自来源）。
