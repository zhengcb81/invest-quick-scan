# PRIMARY三公司包：一次集中独立来源审查

审查日期2026-10-13。审查者为独立agent `primary_source_review`；指定源包HEAD与不可变快照记录在总控 `runs/primary-acceptance-2026-10-13-01/intake-summary.json`。本报告记录证据审查，不授 financial gold、owner、F05或生产资格。指定定位的真实网页核读，不代表90题全部原件审阅。没有保存网页全文、下载PDF、使用付费搜索或模型API。

## Alphabet

2026 Q1、Q2/H1零回购有官方10-Q支持，回购授权仍余69.5bn；不能把零执行改写成取消授权。June融资净额49.6bn、June30现金55911m与证券186563m之和242474m也有官方原件支持，名称须保持“现金及证券”，不能把合计命名为现金等价物。[Q1 10-Q](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm)、[Q2 10-Q](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000071/goog-20260630.htm)。原生[SEC companyconcept](https://data.sec.gov/api/xbrl/companyconcept/CIK0001652044/us-gaap/CashAndCashEquivalentsAtCarryingValue.json)另含2026-06-30现金55911000000 USD、accession0001652044-26-000071、filed2026-07-23、发行人Alphabet Inc.。

`FACT-RPA-PREF-BLOCK-I24`和`PROOF-RPA-PREF-BLOCK-24`将优先股存续误读成禁止任何普通股分红；[8-K Item3.03](https://www.sec.gov/Archives/edgar/data/1652044/000119312526259830/d36818d8k.htm)包含例外及累计未付优先股股利已支付/充分预留条件。[Q2公告](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000066/googexhibit991q22026.htm)还宣告普通股0.22美元股利。应保留错误claim/value并标反证，追加正确条件事实，不删历史。

真实官方来源不等于事实绑定正确。本次明确反例：

| proof后缀 | reference | 实际错绑 |
| --- | --- | --- |
| OBLIG-149-23 | IQS_23 | FY2025购买承诺绑June2026资产/长期债 |
| DEFREV-GROUP-01 | IQS_01 | FY2025合同负债绑Q2广告分拆 |
| WAYMO-VIE-17 | IQS_17 | Waymo融资绑Cloud backlog |
| RPO-GROUP-19 | IQS_19 | FY2025 group RPO绑Q1 Cloud收入 |
| CLOUD-Q2-19 | IQS_19 | Q2 Cloud绑Q1收入，segment写group |
| OPEX-OP02 | OPERATING_02 | FY2025成本绑Q2利润率 |
| INT-02-TAC | INTERNET_02 | FY2025 TAC绑Q2 TAC |
| TREND-06B | IQS_06 | TSR百分位绑Cloud/Network趋势 |

前缀均为`PROOF-RPA-`。其他年份回购/资本开支错绑同样需要撤销映射或重新精确绑定。每个proof只能一种口径、期间、币种、单位；未支持facts必须逐条保留gap，整题不能凭一条官方新闻获得confirmed。

## 中信建投

16个`confirmed_primary`不满足全部事实官方原件覆盖：9题没有官方proof，其余7题仅监管函为官方，其余财务经营facts仍是转载。全部需要撤回整题官方确认。主体核读为中信建投证券股份有限公司/CSC Financial，本次未发现与中信证券混淆。

`PROOF-RPS-011C`及自审将10.51%称包含永续债、非普通股ROE，与其引用的[年报转载第305页](https://www.9fzt.com/detail/sh_601066_9_692d784732506ca0df57c2534e981500.html)“归属于公司普通股股东的净利润”行冲突。当前pack六个ROE25-CORR1已经是正确普通股claim，应修proof/自审，不反向改错已有事实。

`PROOF-RPS-019`分部说明与结构group不符；`SRC-RPS-002`是公告转载，不能标official_statistics。自审英文股利金额少一位：中期12.7985464151亿元、末期13.5742158947亿元，proof011金额正确。[利润分配公告转载](https://paper.cnstock.com/html/2026-03/27/content_2192811.htm)。3月“尚待批准”不支持October cutoff仍未批准；后续批准状态未核则保留gap。

## 宁德时代

30题limited_primary与14个licensed_republication proof是诚实的研究状态。官网[IR页](https://www.catl.com/inverelations/)本次只是动态入口/治理信息，不支持财报数字。[年度中文新闻](https://www.catl.com/news/9654.html)可支持收入423.7bn、归母利润72.2bn、OCF133.2bn等摘要；3925亿元货币资金及交易金融资产不能替代现金等价物/完整债务，市占率须保留SNE转引属性。[英文新闻](https://www.catl.com/en/news/6773.html)写0750.HK、中文3750.HK，应记录官网文字差异，不能据英文文字重新绑定另一证券。

## 限制

SEC companyfacts、部分concept、深交所监管函、智通转载访问失败或本机DNS失败，表示本次未能独读，不是数字为假的反证。H股/IFRS原件与全部90题未完成独读。此审查只支持具体纠错与候选来源降级；软件测试、访问摘要和hash不能自动授予金融准确性。
