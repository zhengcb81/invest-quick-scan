# Alphabet参考独立核源与后续修复保全

2026-10-15。REF源已正常本地提交 `b547d8dc4d3fb3ec972800061dceff66baa044ee`，其基线为 `cc51a2631fb97a53e15ea37cd4804828b738926e`。该Lab没有remote，不新造远端。旧a179149/cc51a26和原handoff保留为历史交付；本轮新增 `docs/handoff/AGENT-REF-02/independent-alphabet-review.md` 明确增量边界。

## 不是覆盖后续改进

用户提醒REF后来修过bug时，总控尚未写回源。随后核实际HEAD、全部本地分支、tracked/untracked状态及109文件raw SHA：仍为cc51a26，109文件与本轮冻结相同，工作树干净。工人499de66修复的锂价成本方向、ESS来源链、artifact哈希和不存在的changed path，已在基线中，本次完整保留。没有根据时间猜测“无更新”，也没有用旧副本覆盖工人修复。

## 独立审查实质结论

独立只读agent `/root/alphabet_reference_independent_review` 于20:06:12–20:07:20UTC实际打开SEC官方HTML，核Alphabet10个fact及12题私有检查；修复后于20:11:04–20:11:19复核实际差异。审查不写源、无收费API、不下载公司文档。

FY2025广告、集团利润、现金流、capex、现金/流动证券等核心数字有直接来源；同一数字在不同槽重复引用不变成独立样本。[官方年度公告](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000012/googexhibit991q42025.htm)、[收入明细](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/R44.htm)支持这些历史事实。普通OCF减capex为73266 USD million，不代表已核维护投入后的现金或多年持续性。

本轮六组修复：

1. Cloud的claim此前已改82%，value_text仍63%；统一为官方Q2 2026同比约82%。[季度公告](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000066/googexhibit991q22026.htm)
2. 撤销把Google Services利润当纯广告利润的说法，明确Services含非广告业务、广告独立利润未披露。[分部表](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/R90.htm)
3. 撤销“四期Network下降已验证”，只使用关联2024/2025期间，不把收入趋势当市场份额。[收入表](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/R44.htm)
4. 复合记录完整可得日期：Cloud为July22，debt为February5。各来源本身的日期和年度/季度期间保持，不能以早期公告日期覆盖较晚证据。[10-K申报索引](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/0001652044-26-000018-index.html)、[债务表](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/R68.htm)、[租赁表](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/R63.htm)
5. 客户证据缺口删除未经独立支持的“中间分以上”门槛，不造数值oracle。
6. IQS_12/IQS_16新增会计风险、现金限制/后续融资/压力流动性缺口，关联实际槽并更新coverage；有rubric或没有gap记录都不能证明证据充分。

独立复核确认六组已解决、其他公司payload无变化。36槽、43facts、14sources、36rubrics保持；gap27→29，Alphabet12槽均显式有gap。所有qualification=false、reference_authority=null；不能把独立内容复核当评分准确率、Financial/G3/F05或收费许可。客观评估应以公司/指标/期间/单位/会计范围/实际或指引去重，主观得分无唯一golden。

## 验证与真实交付

自有根 `runs/agent-reference-independent-2026-10-15-01/` 保存109文件原冻结、候选、独立审查/纠错复核记录、日志、提交与保持收据。

- 六项新内容反例在真实旧数据均失败：PID18772/exit1/6F。
- 修复后整个原包加新增用例：PID22100/exit0/**61P/0F/0skip**。环境keyless、禁网、SQLite query_only、外部文件写拒绝；不是收费公司实验。
- 实际公共CLI双板export/validate及portable replay通过；重复输出均exit3。生成板由真实CLI另核，不冒称独立reviewer也读过最终导出。
- 源18个精确差异按HEAD/109文件SHA/空暂存区核对后交付；97个其他原文件raw SHA保持，18交付文件与受测候选逐字一致。协议/schema仍1.0.0。
- 新slice raw SHA `6428a963a82865c3e52241d59c0e100013e8aef5718038fe77c189a99bfea483`；public board `f1865f60b30a2905469e6732da50aa04ad7698fb815f0d94d23224b1d0184ceb`，private board `a0db0b5222b68651b87d4b7f32897bfbfe57f1edca63beab3398c8f4758f4a2f`。旧双板只作历史，不能配新slice。
- 128项保持/交付核对通过，含真实owner10文件、原work、新S1零预算及他人README。自有进程结束后只清temp64文件/5,282,443 bytes，剩余0；原件/导出/日志/审查记录保留。

## 主线接续与尚存接口边界

收到RUN/EVAL稳定交付后用此新slice/双板和独立复核记录接参考资格范围；不读取活动writer变动中的工作树作为签收版本。20:12只读观察EVAL仍51项变化、RUN仍无正式handoff。本次不改其目录或冻结输入。

原生研究Runtime仍有实质接缝：现有question-pack路径只用于native_search，且同一逻辑work的response_available不能当普通新轮次自动重发。已交StockQA ee1f8c7解决的是DeepSeek payload校验，并没有完成这条多轮接线。后续必须明确研究工具轮次与最终题目结果，保留原owner/admission/发送前登记/预算与未知态处理；不能加provider白名单后伪装native_search、以format-repair绕过，或只用budget-only冒充真实主体授权。该项在既有Runtime集成节点处理，不另加逐helper审查门。

新公司S1实际模型请求仍0；下一步仍是原生scope/策略cohort/generation接线和首家公司三策略各两次，而非重跑S0或重做已签收模块。
