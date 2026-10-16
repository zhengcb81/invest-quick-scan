# T4真实对照登记 / 2026-10-16

沿用T2/T3冻结公司、2026-10-13信息截止、原12题、9来源18facts、DeepSeek Flash及MiMo Pro、single/pack3/company_agent各两重复，总12场144槽；原schema与1/5/10锚点完全不变，不把结构合法当金融准确。T2和T3各首场均保留，其余各11场未启动，不并入T4挑胜者。登记与输入锁在 runs/real-contrast-2026-10-16-03/，首次T4请求前冻结。

相同公司累计上限仍24 SDK steps、2M input、192k output含思考、1800秒、每请求16384 output。三种策略统一连续3次无有效进展停止，有效提交重置连续计数，公司总额绝不刷新。单题和三题第二重复倒序题包；第二重复倒转模型/策略执行顺序。不改变各组已看到的证据，不预设冷缓存。

新登记协议1.1显式绑定sdk_options={tool_argument_validation:'controller'}；旧1.0登记仍走strict默认。这一opt-in仅将submit_answers内部字段schema交给CODEC/原AnswerSink，工具名/id/角色/完成状态/严格JSON与对象边界仍由原SDK检查。原完整function schema仍发给模型，所有无效答案均原子拒绝、仅安全诊断反馈，未通过不入结果。未知请求绝不自动重发。SDK成功后新task使用原生已审计隔离投影，普通绑定仍不放行未知。

SESSION补丁1.0.2保留原协议/旧checkpoint兼容，收到HTTP但答题协议异常时保留完整安全回执和已知usage，不将已结算请求伪作未知/零token。独立SDK45P、SESSION52个不同用例分批覆盖、实际SDK→原临时native账→SESSION→CODEC→AnswerSink→CLAIM整组6P；模拟两家协议均覆盖首答错误→反馈→第二答修正、默认strict保留、缺usage/连接未知不重发，隐藏思考和key未落盘。测试不冒充金融真值。

T4前沿原policy/store累计37attempt、USD0.216014已知公开价估算、USD0.10旧未知预留；没有新seal/归零/换库。350请求/USD25上限不变。全局完整现金账单未知；新phase的完整usage可独立计价，失败、空答、修复都计入。旧T3丢失详细usage不可重建，原native已知USD0.003618单列。

先小批确认真实接线，再按固定登记完成block；不因某模型答案差重跑/改规则。共同实现错误则停phase保留全部分母。全结果交JUDGE匿名包独立评审：原问题/完整答案/公共证据及既有锁定客观子集，禁止模型/策略/费用/时间泄漏。主要错误需第二独立核。准确性先解读，再看CACHE真实缓存、官方价估算和速度；不硬选通用赢家。CLAIM/EVID规则只是诊断，不能自证金融正确。critic/新增搜索均独立阶段与新证据hash，主比较不暗加搜索。

三个经营/查看器外包根已由用户开工，全部只读避让；原冻结卡片/锁保持。T4不写生产owner/正式评分库或下载公司文档，不关闭G3/F05。
