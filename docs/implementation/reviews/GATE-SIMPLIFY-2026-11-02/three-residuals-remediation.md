# 三个残留问题整改（2026-11-02）

后续：独立相邻复查又发现并修复补封及期间端点遗漏，最新状态见[相邻整改](adjacent-remediation.md)；本页保留上次有界结果。

本次修复[实施后独检](post-implementation-independent-check.md)确认的混合恢复范围、历史数据推导预测和嵌套指标引用三个问题。相关软件测试及独立审查通过；没有新增许可、数据库、客户端、审查回执或付费请求。此结论限于本次行为范围，不声称金融回答或全项目全部完成。

## 根因与最终行为

- **恢复单位从整个scope收敛到原工作/物理包。** StockQA先依据原状态分类，pending、claimed但无attempt、unknown及in-flight都不发送请求，也不阻止其他有原响应的独立包保存。局部原响应、正文、工作冲突及租约版本问题保留错误，不产出不合格CP；全局权限及SQLite整体完整性失败仍正常抛出。最终remaining按原wanted减实际saved求差，全无响应返回partial及零保存，不误报完成。原响应/attempt/费用/检查点保持，重复恢复只读复用。同包中间成员的保存冲突也只影响该成员，后续成员继续；只有事务commit成功才计入saved，不把回滚误报为成果。
- **预测输出期间与来源输入期间分开。** Company共用`binding_findings`对实际值保持期间检查；明确forward可以引用历史原数和假设，不要求来源已披露未来输出年份。来源可用性、发布日期、计划冒充实际、币种等规则仍有效。允许预测不证明假设或公式正确。
- **按schema定义共用指标遍历。** `iter_answer_metrics`同时遍历顶层及`items[].metrics[]`，引用闭包、alias重映射、期间/计划判断和自审全部复用它。嵌套数值缺失/空引用、失效、冲突或超期来源与顶层处理一致；`value=null`仍可表示资料缺口。不改原冻结schema或历史journal/findings格式。

## 验证和独立检查

实现提交：StockQA `79746de`，Company `2f3718e`（无remote，本地提交）；IQS生产语义回归测试`9b62b7f`。StockQA正常hooks含格式、密钥扫描及mypy全部通过，未skip。

- QA作者最终组55P /99.72秒，后续typed工作错误尾4P /18.52秒，最终含同包中间冲突的尾6P /16.85秒（组有重叠）。混合状态覆盖两种存储来源（journal/旧capture），包括pending、claimed未发送、unknown、inflight、另一付费包缺正文/坏正文/绑定冲突、全无响应；验证原CP、响应、attempt与预算保持及重复零发送。
- Company作者五模块50P /0.95秒，包含实际Runner与自审的预测及嵌套引用、别名映射、真实冲突和失效负例。
- IQS最终三个相关模块74P、8subtests /21.12秒。新增两个生产语义入口正反例：历史原数生成forward与未来实际值拒绝；嵌套有效引用与MISSING拒绝。原回答及输入不改。
- 非作者`review_three_residuals`独立29例（Company/证据及IQS新增入口），QA混合与原proof19P /44.27秒、typed尾4P /11.51秒，最终79746de同包成员尾2P /5.05秒；核最终源码，无开放阻断。测试结果有重叠，不加总成新通过数。

测试去密钥、禁网络、自有TEMP均确认清理；日志在本机`runs/audit-effectiveness-2026-11-02/`下的`company-three-residual-final.log`、`three-residual-company-peer.log`、`three-residuals-root.log`及QA对应日志。只用合成短问答，不下载公司文档、不触真实库。普通恢复测试权限沿原组件seam，typed错误沿原assert seam触发；SQLite、原parser、journal/receipt与保存API为实际组件，不能将其冒充真实owner全链或金融背书。

没有重跑不覆盖本次混合范围的旧单包长冷E2E，也未跑小时全套。此前冷进程0API证据保留其原边界，本次新增实际混合范围测试不拿它替代。

## 对实际使用和下一步的影响

原8766 GET doctor仍ready，原账本仍87次计数HTTP、2053896micros（US$2.053896）、0在途/未结。普通配置、原已付答案和历史观察未改。继续用原公开补封/恢复入口，不为保存旧结果重建任务或重问模型。

本轮三个已确认残留在上述测试范围内已修；回到根计划既有小池内容质量、真实事实查询及研究消费主线。公开capabilities对旧实验范围的描述仍可日后澄清，未发现因此阻断运行，不增加为主线开工门。
