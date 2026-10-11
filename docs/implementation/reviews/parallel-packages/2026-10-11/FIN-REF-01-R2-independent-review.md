# FIN-REF-01 R2 独立核源记录

结论：**needs_revision，允许保留partial交付，不认可原四组全部关闭**。本轮由已授权独立agent只读Lab并浏览官方HTML；结果与总控软件反例合并为一次包级验收，不增逐题审批。未写源仓、未保存正文、未下载PDF、未调用收费服务。

实际HEAD `775b6a84729e36decb742b0c25eb5c84772d074b`，reference-pack raw SHA `35e5120ebbd1e478e6f4b47fc753fd0dcb940391a2b3d3c8da711904c9d22567`。记录统计：90唯一行、三公司各30题、18深核各6题；9已研究、9缺口结束、72未研究。9行含26 fact记录，部分是同一经济事实的不同题引用，不能称26独立事实；18attempt映射7 source ID。评分/区间全null，交接 independent_review=not_run（writer交付状态，不能被本次阅读改写成owner金融资格）。

## 已可保留

- CATL 2026-03-10官方业绩新闻可支持选取的营收、利润、OCF和现金加交易性金融资产等短事实；亿元转million CNY正确。后者没有冒充现金及等价物。SNE份额是公司转述SNE，不是本包独立验证。
- Alphabet NOPAT未舍入计算、ROIC约28.74、历史FCF 73,266、所选face债务口径下净现金差额77,758、收入增长约15.09的账算术可复查。按实际选择定义评价，不能把不同债务定义混同。
- OPERATING_01历史FCF已降partial，错误维护资本支出占比推理已删除；ROIC部分missing/falsifier与新计算已改。此类修正保留。

## 原R1仍余的问题

1. **72项未研究**：每公司24非深核题directed_attempts为空。新not_started比假称gap完成更诚实，但它仍是未完成的原范围。允许一次HTML查证支撑多题，不要求90次请求；必须逐题记录实际支持范围或真实失败。若业务决定缩范围，须显式保留deferred并由总控调整，writer不能单方面将原任务done。
2. **研究覆盖泛化**：Alphabet深核部分只查一个概念或用“仅PDF/未覆盖”泛化。SEC已公开10-K HTML含business、risk、segment、debt和working capital；轻资产规则允许查HTML，不应因拒下载PDF而跳过这些网页。中信建投6题仅HKEX搜索入口和CSC TLS失败，没有实际06066结果定位；可记录具体访问失败，不能断言全部资料只能PDF。CATL一次新闻没覆盖第二曲线，不等于官方HTML整体不存在。
3. **事实与说明不同步**：SRC-SEC-DEBT来源paraphrase仍把49,085/12,000写成long-term debt/current未单列，未清楚区分Note6的face including current与noncurrent carrying。CATL IQS18“截止前没有HTML覆盖”和not_started“数字仅交易所PDF”旧句与已有HTML事实冲突。中信建投 source quote里“typically published”是作者概括，不是官方引语。review/method仍有“其余gap-terminated/逐题已查证”表述，与72not_started不符。
4. **访问数边界**：actual_source_consultations=7实际等于7唯一source_id。留档能确认18条引用映射，不能在缺访问原记录时证明7次真实查证。无需保存网页正文，只需访问时间/URL/状态/定位/短摘录或明确失败日志。

核对来源：Alphabet债务与财务口径来自[SEC官方2025 10-K HTML](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm)；CATL已有财务短事实来自[官方业绩新闻](https://www.catl.com/news/9654.html)。[HKEX官方入口](https://www.hkexnews.hk/index.htm)只能证明入口存在，不能作为06066具体财务结论的证据。

总控软件边界、PID、清理证据见[R2集中续验](FIN-REF-01-R2-acceptance.md)。本记录不产生新人工评分或真实owner golden，金融校准/模型准确率仍未完成。
