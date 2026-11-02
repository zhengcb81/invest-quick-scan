# 三个问题的相邻场景复查及整改（2026-11-02）

本次按用户要求重新独立检查[上轮三个问题](three-residuals-remediation.md)，发现并直接修复保存之后的补封、期间端点及未知日期继承遗漏。没有新增许可、审批系统或收费请求。此前原反例仍有效，本次不把有限测试外推为所有软件/金融问题清零。

## 已确认并修复

1. **保存后补封仍可能整范围退出。** 普通恢复在中间一题补封遇工作局部冲突时，原来后面正常题没有尝试封包；共享finalizer的恢复handle/commit阶段也有同类屏障。现在沿已验证原工作逐题隔离WorkConflict/LeaseFenced两类工作错误，后面正常成员继续。全局权限、坏export/native绑定及数据库整体错误保留，不广泛吞Exception。
2. **保存与交付完成度混淆。** 普通路径将无合格CP的remaining与有CP但未ready/delivered的delivery_pending分别列出；blocked/left_in_flight不冒称已封包。共享路径也分checkpoint与delivery。重读原CP、正文、attempt和实际封包均已成功时，诊断不再强制pending；错误日志本身不是新的完成资格门。
3. **已有CP的快捷分支遗漏原绑定检查。** 同包处理时已有CP成员必须复用原绑定校验，不能把收集阶段已拒绝的成员又通过快捷分支挂回成果；这是原检查复用，不是新许可。
4. **期间只检查结束日，缺结束日会漏未来实际值。** IQS、QA及Company现在对已知起止端点分别检查，非forward实际期间不能晚于cutoff，各basis均不允许倒置。未知端点仍是null，不推造日期。Company校验及自审共用同一期间判断。
5. **预测总览回填历史子指标日期造成误拒。** Company不再把父forecast结束年填入日期未知的历史输入指标。历史输入与未来输出分别按自己的basis/端点处理，顶层/事实嵌套一致。来源日期、缺失引用、计划当实际等原保护保留。

## 实现和验证

- IQS `7a241ba`：共享补封及期间起点修复，两个相关测试模块更新。最初六个工作冲突反例实际RED；最终四模块139P、8subtests /13.95秒。末次只加强逐题delivery fixture，八个typed恢复/commit/seal/成功后诊断用例1.34秒通过。
- Company `639582a`：仅原answers.py及新期间边界测试。作者四模块75例通过，独立新38+原预测18共56例通过，无remote、本地提交。
- StockQA `9b66f10`：原恢复、标准答案时点及对应测试四文件。作者87P /136.93秒，最终成功后诊断尾2P /5.63秒；正常hooks含格式、mypy及密钥扫描均过并推原origin。
- 非作者`adjacent_peer_review`最终审：Company56例、IQS完整finalizer41+新endpoint24共65P /1.56秒、QA补封/CP重核/端点28P /32.60秒。源码及实际日志审查无开放阻断。各组有重叠，不累计为独立总数。

独审实读原调用链：paid恢复最终只读实际保存scope，不会因partial调用模型；普通顺位看到未解决原响应也不自动换模型重问。scope completed仅表示CP范围完整，封包和StockWiki ACK仍分别展示。

测试均为合成短问答/组件或原SQLite/SDK软件链；根共享finalizer用明确的composition端口替身，不冒称真实owner全链。最终组禁网、去密钥、自有TEMP已清理，无财报/网页下载。新日期测试最初错读自审finding字段，旧finalizer测试遗漏必需claim已改成合法fixture，不放宽产品引用规则。一次RED用的自有runs临时目录在核实绝对路径后已删除；没有清理其他writer的历史文件。

日志留本机`runs/audit-effectiveness-2026-11-02/adjacent-{root-final,root-peer,company-periods,company-peer,qa-targeted,qa-tail,qa-peer}.log`，不用逐断言回执或小时全套。真实原UI精确重载以加载新代码，最终只读核对doctor ready，新旧原观察可读，原配置hash相同，账本仍87HTTP/2053896micros、0在途/未结。

## 使用与剩余范围

普通结果同时看remaining和delivery_pending，共享结果同时看checkpoint_status、unfinalized及pending_delivery。已成功的原响应与CP继续复用；补封错误只补封，不重新提问。forecast可以引用历史输入但不是事实正确的认证。

本节点已完成有界相邻场景修复；金融内容、小池事实、研究消费者、规模及配套仍按根计划推进。不把未复现的旧diagnostic目录候选扩成新任务或门禁。
