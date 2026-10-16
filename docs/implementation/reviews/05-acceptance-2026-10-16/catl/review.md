# CATL 独立最终复审：passed

本次签收精确绑定18文件CAS raw SHA `e01762a5a8bc43741941d17e7643a92dd55cd01d319b618d819b10d0531265d2`。作者payload manifest摘要 `cfc5a24393b958f45cd2073a20680a8b6056801f6d23aac6aa1354577a550d73` 属于另一摘要域，未当作CAS rawSHA。before逐项匹配originals，after逐项匹配新冻结候选、自有测试副本和签收时当前候选；actual after SHA逐文件见catl-result.json/catl2-cas-check.json。

本独立审查者未实现任何候选修复。已审阅原问题与新core拆分diff、单一material入口、五类实际输入canonical authority保留、CLI及export绑定。新整组实际144/144通过，0 fail/0 skip；独立再跑13个case（12个原缺口加1个已拒绝控制例），每例分别调用validate/coverage/export三入口，全部拒绝且0输出目录。新suite也实际执行shared-core sentinel、原反例、冻结集成、CLI搬迁改名、hash防篡改、再生逐字节一致与原子发布检查。不是把作者日志当作本次实跑。

CATL-F01（原A01未闭合）已关闭：authority.assert_material不再独立重复语义实现，而委托reference_lib.validate_material；完整validate也先调用它。日期/期间、费用/计数、有界片段、observed_subject、维度status全部共享拒绝。证据catl2-suite.json与catl2-probes.json；guard根及Python子进程网络尝试0、外根写尝试0。README旧103段已明确1.0.0历史证据。

实际逐项读17条claims、25条source日期/片段/来源属性和36维度：公司现场数/发布参数/MoU/计划产能/试运转继续company_statement，2条推断有前提；GBA 12日材料仅research，未知日期制造/技术页双不合格；唯一sufficient仍是IQS_02公开文本分层窄命题。现金流、ROIC、单位经济性、复购、客户ROI与合同价格均未自动补全，20gaps保留。没有新网页/API核查，历史正文/独立现场经营效果仍未认证；不授予财务/生产/评分gold资格。

此前首轮needs_revision与RED记录保留如下，已由上述同包闭环复审取代当前结论。

# CATL 独立最终复审（首轮，待同闭环修复）

结论 needs_revision。独立于交付作者和1.0.1修复作者，不修改候选；测试基于冻结候选的自有副本 catl/。

读取原卡、integration-contract、interface-spec、原 RED、CAS、修复报告，审读 authority / API / coverage / export / CLI / lock / strictjson / schema 及原有回归、再生测试。逐文件 raw SHA 范围见 catl-files.json。独立整组实际 130 passed / 0 fail / 0 skip，catl-suite.stderr.log。测试在最小无 key 环境和禁网/外根写 guard 下运行；子进程同样受 guard。全部397冻结输入 rawSHA/bytes实际匹配，发布锁6b8d7e88df3cbc4aa9fb92bf7a181d4bee67f9bc098a59fa1bedd1e4591ce591，详 integrity.json。

未闭合发现 CATL-F01（原A01公共API同类缺口）：authority.assert_material 是 full validate_reference 的另一套不完整语义实现。12个只改资料、重封合法 content hash 的反例被full validator拒绝，却被coverage和export接纳并实际生成bundle。包括观察期间倒置、费用unknown冒0、来源计数、company_statement带observed_subject、201英文词片段、两类日期unknown状态矛盾、以访问日自证日期、失败打开次数超过总数、完整费用小于小计、out_of_scope/reference_only带经营claim。完整最小反例和实际结果 catl_probe.py / catl-probes.json / probe3-*。query_count=21已正确被schema拒绝，是控制例。

已反馈总控，作者在同包闭环统一共享完整material校验；本轮不授予通过。原报告中的来源网页核验属于修复作者证据，本次无新网页/API访问，不认证历史网页内容。人工映射与材料仍仅窄命题支持；全题、财务资格和生产资格不授予。

CATL 新CAS到齐后必须在同闭环重新核after/before、重跑受影响整组与独立反例，方能关闭F01。候选正在修改时读取到的CAS差异不当作产品缺陷，不对移动中的内容认证。
