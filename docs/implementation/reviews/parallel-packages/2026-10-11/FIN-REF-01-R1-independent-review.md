# FIN R1 单次独立事实审查

2026-10-11，审查者 `/root/fin_reference_source_review`。只读实际 remediation-01/pack/账，在线核官方HTML；未执行Lab、未写仓库、未下载财报或网页正文、未调用收费API。结论 `needs_revision`，只归原R1两个事实根因；软件结论由总控 [集中验收](FIN-REF-01-R1-acceptance.md)补充。没有新增逐题审批门。

快照pack raw SHA `abbd7ecae6ffc8d69a3c29ed1ba424d8fda690ffeacef06795f69897b6918525`；source-attempts SHA `420b2f81ce5213e27982b615cdeba824f5b74832600fbd1c905961b7ec6d1697`。总控冻结副本相同。

## P1：占位不等于查证完成

90行第一条attempt来源分组：SRC-SKELETON78，SRC-SEC-REV6，SRC-CATL-NEWS6。78项占位覆盖全部72非深核和全部6中信建投深核，sought明确“no research conducted”，locator n/a，termination skeleton_baseline；却计入90次查证、81行gap-terminated研究完成。README第13行声称每题真实定向查证不成立。空facts合法，未开展查证不能换标签变为完成。

Alphabet6深核attempt均用营收concept，现金/债务/ROIC/现金流来源映射不切题；没有接原卡允许的10-K HTML对应查证。CATL一篇新闻未覆盖情景，不证明cutoff所有官方HTML均无；中信建投具体通道失败也不证明全部PDF-only。记录真实尝试范围和失败即可，允许复用一次访问、多题映射，不要求90次联网。

## P1：旧错句仍在正式reference

OPERATING_01仍answerable、deep-index仍fact_decidable，falsifier依旧“维护capex占比高使FCF低于73266”；新ledger修正没有同步。IQS_10债务fact已含当期面值，pack冻结行930/954的missing/falsifier与SRC-SEC-DEBT原说明仍声称当期未含。README22及review24的“已统一修正”不属实。分析句充official quote也需改正为分析/来源局限。

## 有效材料保留

- CATL headline与亿元转人民币百万元正确，3925亿元明确是货币资金＋交易性金融资产。[CATL官方FY2025新闻](https://www.catl.com/news/9654.html)
- Alphabet Note6两种债务口径区分、新未舍入NOPAT算术，以及既定定义下历史FCF/流动性/同比算术有效。[Alphabet官方10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm)
- 全90行分数/区间仍null，独立复核not_run；没有评分proposal或正式gold。9行含facts不等于18深核或90研究全部完成。

只续 [同包R2](FIN-REF-01-R2.md)原四组集中节点，保留已正确的数字和账本；不签F05/G3或模型金融准确率。
