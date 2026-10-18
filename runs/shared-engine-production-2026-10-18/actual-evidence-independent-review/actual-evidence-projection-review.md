# 实际旧证据投影预审（后续节点内的接缝检查）

审查者 `/root/production_node_review18`；实现作者 `/root`。不是独立批准门，不授予原owner权限、金融正确性或搜索证明。只读原已锁输入，未写源码/PWF/真实数据库、未调用API。

已读 `project_existing_sources.py` 和其测试：实际旧锁为18个协调者facts、9个source。投影只传原bounded_excerpt，保留原URL/日期/访问时间/limitations；没有明确fact-source边时，不把18个facts变成受支持事实。原题主体映射按实际 entity+analysis subject revision，并核native-derived company ref字节/摘要，cutoff不默改；未知scope/period/unit/currency/accounting basis保持unknown/null，support保持unverified。EvidenceBoard原验证与context/excerpt上限继续生效，拒绝截断来凑上下文。

独立执行实际9源正例通过。新增两个未见反例在初始源码上均失败（2F/1P；`projection-independent-red.xml`）：

1. 旧3源虽然没有 `excerpt_sha256`，但都有 `content_hash`，且实际值恰是原bounded_excerpt的SHA-256。保留这个原摘要、改摘录后重封外层容器摘要，初始投影忽略已有摘要，只算新SHA而接受。应核这个明确旧别名（或拒绝不支持的摘要语义）并注明来源，不能把来源损坏变成“计算了一个正确新hash”。
2. 明确 `eligible_for_context=false` 的source在重封外层摘要后仍进入上下文。既然本适配器承诺完整投影这9条而不隐删，最小修复是对显式false整体拒绝并说明；若未来允许排除，必须显式列出excluded source及理由，不能静默继续。

这两例只在内存里改变待验证副本及非authority的外层ref，原锁文件字节不变。当前真实9源的三个eligible标志都为true；新增反例用于保证接缝不错误接受之后的明确冲突。`claim_kind=fact` 目前是未验证source载体分类，不应被下游当作支持升级或计划/实绩判断依据；现有unverified guard仍保持，未额外声明其金融支持。

两个发现已在同一接缝从根因修复：每个存在的原 `excerpt_sha256`/`content_hash` 都必须与摘录一致；两者冲突或都没有则拒绝。三个旧源的origin现在诚实标为 `original_content_hash`，其原值/eligibility留入provenance。明确eligibility必须是bool True，否则整份输入拒绝，不隐删。修复后独立重跑原20例和这两个未见反例：**22 passed，1.19秒**，实际锁定9源正例保留完整原摘录/日期/URL/limitations，18个未连边facts仍未投影。

结论：这项后续整节点的输入准备接缝已完成本次预审，两项发现关闭；它不是独立执行批准门，不证明实际公司事实都正确、原引用已完整证明、owner授权已安装或旧S1可续行。仍需后续节点自己的实际原权限、费用/未知态及生产接线验收。
