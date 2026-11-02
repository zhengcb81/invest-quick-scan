# 实施后的独立效果检查（2026-11-02）

后续：本页列明的三个待修项已在[三个残留整改](three-residuals-remediation.md)完成有界修复和独立审查；下文保留发现时证据。

结论：上轮原反例修复有效，但恢复和预测的同类问题仍未全面解决。本次检查不修改产品实现、不重新请求模型、不改原答案。没有新增运行门、审查凭证或施工包。复核范围与上次工程终验不同，旧已通过实例保留。

## 已重新验证的成果

实际基线IQS734df7b、StockQA9648aef、Company0af8902；StockWiki只读见f52f257，没有写入或全仓新验收。

- 总控重跑原内容探针：正常对照、同比跨年、取消计划前缀、长单位说明都接受；同HTTP少Q2时Q1完成，Q2单独missing，包装声明不再改变Q1命运。
- 新独立审查者`postfix_independent_paid`复跑原公开日志/恢复两模块：39P /43.22秒，验证普通/研究同journal、重开store、同HTTP部分scored保存、旧capture、重复恢复、预测尾项与schema一致性。去密钥、禁网、自有TEMP清理。
- 新独立审查者`postfix_independent_content`复跑部分题包及证据绑定两模块：19P，禁网去密钥，自有TEMP清理。
- 总控只读原doctor仍ready=true；原账本87HTTP/2053896micros、0在途/未结。本轮无新增收费API。
- `postfix_review_overhead`核当前Dashboard：读取不创建preview许可证，补封走recovery，交付核原scope/store_id并逐项ACK，未发现新的已证实Dashboard运行误门。

## 新确认的两个残留误门（待修）

**P1，跨工作范围的恢复屏障。** StockQA `src/utils/quick_scan_refresh_execution.py:606–612`：recovery_only将leased工作纳入候选，`list_attempts`为空时直接抛`received_checkpoint_original_response_required`，发生在保存任何物理题包之前。独立反例在原完整合法3题已付journal包旁，用真实Store公开API创建并claim另一个合成题、不发送；结果整scope异常，原3题CP数0。原parser/SQLite/响应真实组件，权限沿原测试seam，不能冒充完整真实owner E2E。

上轮修了同HTTP内的部分成员，没有覆盖“多个物理工作混合、其中一个尚未发送”。应按工作状态分类：无响应的未发送/未知项保留其缺口且不发请求，其他有原响应的独立项继续保存。原主体、receipt、hash和租约版本检查保留。

**P2，历史输入推导未来情景仍误拒。** Company `src/iqs_company_agent_lab/answers.py:313`的来源年份匹配仍作用于forward指标。合成2025收入120，明确分析师2027情景为120×1.1²=145.2，假设不称公司指引或实际值，资料均早于截止；仍因来源没有2027期间而拒`cross_year_period_binding_conflict`。独立agent及总控分别纯内存复现，正常历史对照接受。上轮forward正例是引用已标注目标年份的计划来源，未覆盖从历史基数推导未来。

应区分来源披露时点、输入期间、输出预测期间与实际/假设。预测不可能要求未来已有实际披露；允许这些输入也不表示计算或增长假设已获事实支持。

## 另一个组件质量差异

Company `answers.py:155`的`collect_cited_ids`未遍历事实项内`items[].metrics[]`。独立合成例中item本身有有效引用、内嵌数值指标引用MISSING，Company仍接受；IQS生产`validate_content`会拒缺失数值证据。此为独立组件的引用闭包不一致，待修；不是已证实错误生产入库，也不是应删除的保护。

## 审查负担及文档残留

- 现行tasks.json的B01仍要求逐原子断言登记、V18仍要求每run快照和逐文件清理证明，与同文件全局简化规则冲突。本次已直接删冗余措辞，保留真实实验结果、原请求日志及TEMP实际清理；没有改变产品行为、卡数或验收范围。
- 实操手册笼统写恢复必须有有效lease，本次澄清为：新发送需当前有效租约；已付重放仍核原绑定/版本，不要求重新取得有效租约。
- 共享capabilities混列旧12题/固定日/MiMo实验和新公司扫描范围，容易误读，尚未证实导致运行拒绝；能力描述澄清待做。本次不据此改运行许可。

本轮没有重跑小时全套或长冷E2E。新的scope和forward反例是先前测试未覆盖的组合，不用旧通过数覆盖它们，也不以“还有待验”无限重开已完成的相同实例。下一步集中处理上述两个运行残留，并补组件嵌套引用一致性；不用再增加人工审查步骤。
