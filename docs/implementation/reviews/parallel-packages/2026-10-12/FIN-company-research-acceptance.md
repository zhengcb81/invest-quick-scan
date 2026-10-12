# 三家公司研究包验收与总控直接修复

三个包的软件交付已验收；金融研究保留为 **partial 候选**，没有赋分或授予金融 gold。每家公司30题，最终合计90题。

| 公司包 | 原测试复现 | 修复后最终测试 | 产品 commit | 最终交接 commit |
| --- | --- | --- | --- | --- |
| FIN-CATL-02 | 42P / 0skip | 55P / 0skip，PID18020 | 95e6292526e256d0c300e6375a087e4ea2827c39 | 00b55cddeeef81236fcc5fc1399cf3d96ab8b06f |
| FIN-ALPHABET-02 | 26P / 1skip | 37P / 1skip，PID61512 | 7ce3e628e9b3a2c8af23ff5d6219047c814c25ed | e27a6a408cf1058fb736b5174e3980e7d3ff58cd |
| FIN-CSC-02 | 64P / 0skip | 70P / 0skip，PID64000 | d0188fd4f7125a8793efa917d4dc1f82d98d87c4 | 2ce5a4bb0e1b3a03ac53261787bccb61cd414126 |

这是三个不同测试包的实际结果，不相加作回答准确率。Alphabet原跳过项保留。三源无remote，没有推送；Git仅各自用户授权的CodeGraph设施未跟踪，handoff据实dirty/count1。产品及交接正常提交，工件98/156/126逐bytes/raw SHA匹配。公开handoff CLI分别PID56224/57736/71912 exit0，仅验证结构/声明范围。

宁德时代修正货币资金与现金等价物混用、遗漏一年内到期债务/债券的借款租赁聚合、归母权益与集团资产负债混用的资本分母、可读表格被误记为不可得，以及减值总额/认证/政策与经济性推断。补资本开支后简单FCF可复算；维护性FCF和正常化ROIC仍未建立。五份新浪转载与两份发行人新闻分开标记，转载不是官方原件认证。

Alphabet区分FY2025报表日后与信息截止日前事项；补年度TAC、采购/合同承诺，撤回债务子集覆盖代表整体生存能力的推断。分部与非货币范围、SBC现金流调节项、历史诉讼及续聘提案等用新CORR1记录纠正。原四账项算法保留，ROIC/net-position只能是已定义代理，不能据此证明经济资本回报稳健。XBRL选择器锁accession、精确期间与披露日截止，拒冲突记录。

中信建投撤回人民币净资产与港元股价1:1相除、含永续债权益混用普通股ROE/EPS的估值比率，区分已付/拟派股息、母公司单一FV损益与集团收益、年度活跃与完整周期位置。正式报刊公告、新闻及转载来源分层，收入同比22.41%算术保留。现有冻结FIN1.1无法表达parent_company，62个母公司数字副本留在隔离附件，标记not_registered；没有把它们硬标成集团/segment，也未修改39冻结依赖。原FIN具名兼容扩展仍待总控集成。

同包独立核源与总控一次集中验收结合，不新发整改卡或增加小节点审查。原错误事实claim/value及原失败日志保留，21/67/16前序标contradicted或有隔离动作，新记录及前序hash可追溯。宁德时代12RED、Alphabet10RED、中信建投6RED；修复中的合成测试误选对象、文本否定断言和旧未审状态预期分别留原日志，不假称首次全绿或降独审为通过。

总控已在私有隔离副本做共同基线三方合并：6种顺序字节相同、并发同题冲突和外公司注入拒绝，4测试通过（PID60384）；FIN公开validate/export0/2/3通过，坏输入不发布。结果72题完成定向研究、18题具名gap、0题not_started，947条包含历史的事实，104条contradicted前序、8账项；全90评分/区间null、独审needs_revision。原helper的deep_verified_count=36只反映其既有事实存在计数，不是36项官方认证；实际金融签收0。

合并产物目前仅在 `runs/fin-company-merge-2026-10-12-01/merged`；原FIN HEAD1e7d617及39依赖保持，尚未覆盖原FIN。下一步在原F05整节点完成具名范围兼容/原FIN受影响回归与精确交付，再回原B01耐久receipt下游接线。研究候选不能替代真实owner、金融评分、G3/F05、生产UI、一键/全池验收。

三包测试生成临时文件分别精确清16/5/4个文件与20/1/1目录，保留必要小反例和日志；CIM自有Python进程0。一次sandbox CIM拒绝后按只读权限核实，不隐瞒失败。没有收费API、财报/PDF下载、网页全文保存或生产DB/名单写；源个人环境和其它writer未动。合并自有测试导出暂待收口清理，不清活动B01。

源交接可直接阅读：

- [宁德时代修复说明](C:/Users/郑曾波/Projects/iqs-reference-catl-lab/docs/handoff/FIN-CATL-02/coordinator-repair.md)
- [Alphabet修复说明](C:/Users/郑曾波/Projects/iqs-reference-alphabet-lab/docs/handoff/FIN-ALPHABET-02/coordinator-repair.md)
- [中信建投修复说明](C:/Users/郑曾波/Projects/iqs-reference-csc-lab/docs/handoff/FIN-CSC-02/coordinator-repair.md)

IQS本次公文正常本地提交，远端仍之前导出范围审批pending；不绕过、不宣称所有远端同步。私有源快照、真实财务JSON、日志、数据库与他人2026-10-10 README均不入这次IQS公文提交。
