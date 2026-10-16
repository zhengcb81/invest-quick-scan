# Alphabet 客观事实参考范围（实验前锁定）

2026-10-16，独立只读审查 agent `/root/accuracy_reference_review` 的实际最终交接；未读取模型答案、未调用收费 API、未下载文档。此文件记录增量核源，不授予整套评分题或整家公司 qualification。

基线：REF b547d8dc4d3fb3ec972800061dceff66baa044ee；slice SHA256 `6428a963a82865c3e52241d59c0e100013e8aef5718038fe77c189a99bfea483`。三个参考文件的精确基线：

```json
[
  {
    "path": "content/reference-slice.json",
    "bytes": 200910,
    "sha256": "6428a963a82865c3e52241d59c0e100013e8aef5718038fe77c189a99bfea483"
  },
  {
    "path": "evidence-public/public-evidence-board.json",
    "bytes": 172457,
    "sha256": "f1865f60b30a2905469e6732da50aa04ad7698fb815f0d94d23224b1d0184ceb"
  },
  {
    "path": "reference-private/private-reference-board.json",
    "bytes": 159175,
    "sha256": "a0db0b5222b68651b87d4b7f32897bfbfe57f1edca63beab3398c8f4758f4a2f"
  }
]
```

客观分母锁定为以下10个互不重复主标量。金额单位 USD million，FY2025 为2025完整年度；资产负债项目为2025-12-31时点。问题重复引用不增加事实分母；没有提到不算事实正确，覆盖率与拒答另报；不能从正确的个别事实推断整套准确率。

| fact_id | 精确命题 | 主值 | source_id |
|---|---|---:|---|
| RF1-ALPH-ADS25 | FY2025 Google advertising收入 | 294691 | RS-6-ALPH-10K-R44 |
| RF1-ALPH-ADS24 | FY2024 Google advertising收入 | 264590 | RS-6-ALPH-10K-R44 |
| RF1-ALPH-OI25 | FY2025合并经营利润 | 129039 | RS-6-ALPH-8K-Q4 |
| RF1-ALPH-NI25 | FY2025合并净利润 | 132170 | RS-6-ALPH-8K-Q4 |
| RF1-ALPH-OCF25 | FY2025经营活动现金净流入 | 164713 | RS-6-ALPH-8K-Q4 |
| RF1-ALPH-CAPEX25 | FY2025 PP&E现金购建支出绝对值 | 91447 | RS-6-ALPH-8K-Q4 |
| RF1-ALPH-CAPOI25 | FY2025 Cloud分部收入（非经营利润） | 58705 | RS-6-ALPH-10K-R44 |
| RF1-ALPH-CASH25 | 合并现金及现金等价物 | 30708 | RS-6-ALPH-8K-Q4 |
| RF1-ALPH-MKTS25 | 流动有价证券 | 96135 | RS-6-ALPH-8K-Q4 |
| RF1-ALPH-DEBT25 | 长期债务本金面值总额，含当前到期部分 | 49085 | RS-6-ALPH-10K-R68 |

官方来源：[R44](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/R44.htm)；[2026-02-04公告](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000012/googexhibit991q42025.htm)；[R68](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/R68.htm)；[10-K索引/2026-02-05](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/0001652044-26-000018-index.html)。均早于截止日2026-10-14。

复合记录附属命题不能自动增加分母：Cloud Q2-2026同比82%（81.8%合理舍入），年度/季度必须区分；Cloud经营利润13910；lease面值、现值、未折现付款分开；2026 capex175–185 billion仅为2026-02-04当时指引，不是截至十月最新保证。新原子命题须在看答案前另登记。

匹配主体、指标、期间/时点、币种、单位和会计口径；允许正确单位换算，Decimal按披露精度舍入。事实数值、引用支持、信息覆盖和合理拒答分别报告。未提供护城河/ROIC/AI净价值等1–10标准分；广告增长不等于留存/份额，经营利润率不等于ROIC，全部现金不等于无约束可用资金。失效XBRL及历史reused_fact_id不作为额外独立来源。现有所有qualification_granted=false保持。

本范围是历史事实核验子集。完整答案的非数值判断、最新经营动态和引用支持须通过实际盲评，accuracy/winner仍未产生。
