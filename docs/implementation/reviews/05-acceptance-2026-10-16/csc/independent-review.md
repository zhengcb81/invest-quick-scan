# CSC 独立最终复审：passed

精确绑定19文件CAS rawSHA `7a37f8ae1a71e1c51a96e50ccfaea5eb46c58f1241228dfff461b0f21db728cb`，before对originals/、after对新冻结候选与自有csc2/副本逐项匹配，签收时再核候选after不变；每文件actual after SHA在csc-result.json/csc2-cas-check.json。

独立于原作者及修复作者；没有实现或修改候选。实际重跑新整组143 passed / 0 fail / 1 skipped，唯一文件symlink权限跳过；真实junction越界及嵌套清理均通过。日志logs/independent-csc2-suite.json含argv/cwd/UTC/exit和rawSHA。独立重放period两变体与unknown费用0，完整validate、coverage和export均分别拒绝且0输出；非有限费用控制例在canonical hash入口拒绝，见csc2-probes.json。

CSC-F01、F02均关闭。审阅共享_check_claims/_check_acquisition实际diff：来源日期和观察期间分别按11日/13日推导，再递归传播整个推断DAG，维度按最终资格派生；unknown费用留null、未知依据不能自证任何金额、subtotal不能超过complete。整组包含正确research-only前提链可表示的正向例，以及已披露partial/known零费用的合法正向例，未把修复做成一概拒绝零费用或研究候选。所有新规则共用于三个公开入口。

data与source未再变化，前轮对A/H同主体、母公司/集团、规模/客户价值/费率/收入阶段、13窄命题与40gaps的人工检查继续成立；没有新网页/API操作。financial partial/needs_revision和三项false资格不变，文件symlink系统权限与历史网页真实性限制继续披露。此前needs_revision与RED记录保留如下，当前由本轮闭环结果取代。

# CSC 独立最终复审（首轮，待同闭环修复）

结论 needs_revision。独立于原作者和1.0.1修复作者，不修改候选；测试自有副本 csc/。

读取包卡、共用契约、接口、修复报告、api.py的完整校验/coverage/export共享层、lockio可信输入构造、原回归和实际资料。逐文件rawSHA见csc-files.json。19CAS的before对originals/、after对冻结候选逐字节一致，expected_head匹配snapshot。全部397冻结输入实核保持，锁SHA正确；详integrity.json。

独立完整suite129 passed / 3 skipped；另以已授权require_escalated实际运行2个junction反例2 passed，文件symlink因系统权限仍1 skipped（这些不是加成测试总数）。真实日志logs/independent-csc-suite.*和independent-csc-links.*。纯API独立反例csc_probe.py / csc-probes.json。

CSC-F01（双cutoff未闭合）：CLAIM-IB-01的period_end=2026-10-12，或period_start/end=2026-10-12/13，仍保留原题11日eligible。三个公开入口均接纳，实际export产生bundle；question视图仍使用该direct命题。api.py _check_claims只按research13日检查观察期间，expected_question只按来源日期推导。应在原共享层按两种cutoff分别核观察期间，并传播到推断和维度。

CSC-F02（费用诚实未闭合）：usage_status=unknown/cost_basis原unknown，只改known_cost_subtotal_usd=0，三个公开入口均接纳并实际export。违反无工具费用披露不能伪造0的共用契约。应核零费用依据、unknown/partial/known及总额小计一致性。非有限费用控制例在canonical hash入口被正确拒绝。

逐项阅读资料（csc-material-audit.json）：A/H同主体固定H证券；母公司资本声明未升级集团；项目阶段分列、AUM/户数规模、留存/费率/收入转化的partial边界保留；13项direct仅声明的窄命题，未聚合整题。SRC-CSC-03和07本轮不重新联网核验，历史正文/第三方原件仍是已披露限制。本次未发搜索/API。全部40 gaps和financial partial/needs_revision及三个false资格保留。

两有效问题已送总控安排原作者同包闭环修复；新CAS冻结后再核和复跑，当前不签收。
