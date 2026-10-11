# FIN-REF-01：集中验收完成，需同包整改

结论：`changes_requested`；不能作为已完成金融参考签收，保留有效资料。源仓 `C:/Users/郑曾波/Projects/iqs-financial-reference-lab`，分支 `codex/fin-ref-01`，HEAD `b5852aac5978a268dc4dd2eb795663c69b3ab9ca`；基础 `b5275e1eb91139a3ba06919af2c021695c78661e`，产品 `97e5a26dc4569a4cffef5c09b9791fb08b7dc0a1` 是HEAD祖先。无remote，不代提交Lab。

## 有效部分与交接现状

65跟踪文件冻结；20输入副本与原锁的bytes/raw SHA全部匹配，90行仍30/30/30，14来源，所有expected_score=null、independent_review=not_run。两阶段盲核、固定分母、严格ID/hash join设计、材料有效不等于金融准确性等边界保留。

57声明工件实际有一项漂移：`docs/handoff/FIN-REF-01/isolation.md` 声明2265 bytes/SHA `53a53c30…`，实际3311 bytes/SHA `cc652c24…`；其余56匹配。原handoff自报partial，临时根有created=true/cleaned=false；总控公开handoff CLI PID41472实际exit2、`temporary_root_not_cleaned`。不能把主CLI通过当交接目录已合格。

## 实际测试与补测

仅在IQS自有 `runs/fin-acceptance-2026-10-11-01/source` 副本运行，父/子无key、禁网、写限自有根。前两次pytest在collection前因验收guard与Windows NUL设备不兼容失败，分别exit1和3，属于验收环境；保留原日志。指定`-s`和自有`--log-file`后，PID43880实际exit0：**31P，5.44秒pytest时间**。没有修改Lab代码或降低guard。

25个独立公开validate＋export控制，修改内容后正确重算pack_id，避免只测到摘要不匹配。实际只有2个exit预期匹配：正常包成功，以及事实已不一致的零分子样例被拒；该拒绝实际因为把所有零值误认成分母，不能算正确财务语义已获证明。其余20坏输入validate/export0，2坏容器exit1崩溃，1内部数值一致的合成零分子合法算术控制误拒exit2。合成控制不是真实金融正例。

| 组 | 固定case | 实际结果 |
| --- | --- | --- |
| 冻结绑定 | row-manifest-hash、questions-file-hash、questions-file-path、rubric-version | 均validate/export0 |
| 分母完整 | duplicate-question-id-distinct-ref | 30行可重复同题、遗漏另一题，仍0 |
| 支持与时点 | supported-no-source、impossible-publication-date、unknown-publication-supported、unknown-cutoff-not-marked | 仍0；缺证明未降为不确定 |
| 发行人 | catl-supported-by-alphabet-source | CATL行拿Alphabet数字来源支持，仍0 |
| 评分区间 | unknown-interval-candidate、reversed-score-interval | 无依据区间/上下界倒置仍0 |
| 计算关联 | ledger-other-pack、ledger-unknown-reference | 不同pack/不存在reference仍0 |
| 计算真值 | ledger-input-value-tamper、ledger-result-tamper、ledger-unit-mix、ledger-period-fact-mismatch | 原值/结果/单位/期间污染仍0 |
| 容器与JSON | bad-root-array、bad-reference-null、duplicate-json-key、nonfinite-ledger-result | 前2崩溃exit1；后2重复键/NaN仍0 |
| 算术对照 | zero-numerator-consistent | 非零分母、零分子被当空分母，exit2 |

正常导出仍保留90行、不覆盖已有输出等原有效测试不返工。原31P与25补充控制各自记载，不相加为模型/金融准确率。

另单独消除零分子控制的题义歧义：使用原ROIC公式，明确标注合成来源、OI=0、其余正投入资本/税输入不变，输入fact与账本数值一致。PID63824 validate及PID41340 export均exit2/empty_denominator，复现将零分子当分母错误。该项只验证算术规则，不是现实财务或owner正例；原25项中的自定义比率样例不作为唯一合法财务口径依据。

## 金融内容审查

独立agent只读查证，未执行Lab代码；总控复核两条官方HTML。90行中仅4行有事实，共18数字facts；86行无facts，72行仍标skeleton。`mark_deep`只是review_notes前缀，12条CATL/中信建投“deep_verified”没有深入核对条件，余行将题目evidence demands拼入通用渠道句。诚实弃评有效，但不能替代逐题研究和18题深核。

“CATL数字只在PDF，轻资产政策不能获取”的广义结论不成立：截至cutoff之前的官方HTML已有FY2025收入、归母利润、经营现金流及资金/金融资产合计，可用于部分参考。该新闻不能代替所有会计口径或独立证据。[CATL官方2026-03-10新闻](https://www.catl.com/news/9654.html)

Alphabet四项原算术按所填输入可复算：FCF73266百万美元、原债务面值口径流动性差额77758百万美元、收入增长15.09%、原ROIC28.74%。但债务49085/12000是含当期的票据总面值，不能同时称“当期部分未纳入”；非流动账面债务46547/10883是另一口径。简单OCF减总capex仅支持历史FCF，不足以让OPERATING_01完整answerable；维护capex占比本身不能使同一OCF下的维护后现金小于已扣全部capex后的现金。[Alphabet官方10-K Note 6和现金流表](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm)

中信建投实际访问受限保留，但通用HKEX搜索入口/站点访问失败不能证明特定issuer所有资料只有PDF，判断句不能写成官方quote。任何新资料只能作为下一版明确新增查证，不覆盖旧记录。

## 续做与资源边界

同一包的[唯一R1整改卡](FIN-REF-01-R1.md)，四组根因：研究与事实口径；冻结/发行人/时点/分母；计算绑定与算术；稳健CLI与交接清理。一个稳定候选集中TDD/审查，不新增小门，不要求每行填分。

用户授权CodeGraph已实际init exit0：17文件、227节点、210边；设施保留，不代提交`.codegraph/`。源Lab产品只读，最终逐文件保护及自有清理见本机验收根`closeout.json`；保留实际原日志、控制器、guard和冻结来源，不发布私有输入/真实身份。无收费API、财报/PDF下载、生产库/名单写入；官方联网查证在浏览工具中进行，离线CLI没有网络请求。金融/F05/G3与全局目标仍开放，B01主线不变。

清理实际终态：自有活动Python0，65源文件与65冻结副本字节/HEAD均未变；仅授权索引未跟踪变化。216生成文件、62目录按原大小/SHA/文件ID/单链接精确清理，保留26组结构输入及全部原过程。源Lab自己的venv/运行目录不代清理，留原writer按R1说明处理。
