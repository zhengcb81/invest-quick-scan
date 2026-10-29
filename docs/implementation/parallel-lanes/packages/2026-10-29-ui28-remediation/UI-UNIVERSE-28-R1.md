# UI-UNIVERSE-28-R1：挂牌校验、草稿写归属、迟到预览及真实交接修复

交给原UNIVERSE harness即可。唯一写根 `C:/Users/郑曾波/Projects/iqs-universe-import-ui-lab`，继续 `codex/ui-universe-28`。基线HEAD `154afd936c7d1ae84f974eb6c0a689225fa883dd`，原声称payload `3fdbba0f4402942c72b5ef22731df96329f039a2`。先读 [共同规则](handoff-rules.md)、[锁](inputs.lock.json)、[原范围](../2026-10-28-independent-support/UI-UNIVERSE-28.md)、[总控报告](evidence/universe-final-report.md)。原业务/test源码未被总控修，只有授权CodeGraph本地配置；旧审查不能改写。

## 三个业务根因组，一次合并修复

### U-A：显式与隐式证券选择共用有效期验证（ACCEPT-U01）

基线 `src/iqs-universe-import/machine.js:315–371`：传security_id会校listingActiveAt，省略/null且只有一个挂牌时却绕过并自动填ID。合成旧挂牌valid_to=2021在as_of=2026-10-28被选中。普通UI单证券placeholder返回null时也可触达。

要求：两条路径走同一有效期/未知身份核验；保持 `[valid_from, valid_to)`，明确日期未知不擅自当当前挂牌。允许拒选过期/未核定挂牌，错误码不强制；不能伪造/替换证券、修改原身份库或用今天填日期。

回归：显式/省略单证券、仅有已退役挂牌、恰好valid_to、有效期未知、多证券、不同市场同ticker/同entity A-H。原用户手工选唯一entity要求保持。

### U-B：整个draft的写操作互斥及unknown归属（ACCEPT-U02/03/04）

基线 `machine.js:182–237、239–310、315–379、381–496`：

- U02：第一apply已明确进入并等待，另一row确认又发第二POST，覆盖全局inFlightRowId。普通页面view.busy已有部分保护，但导出的machine/getMachine宿主面缺守卫。
- U03：apply尚未返回时loadUpload直接换draft/source hash，使旧ACK所属记录脱离当前草稿。常见文件input也有view.busy，但领域API/宿主loadDraft路径必须守住。
- U04：超时为unknown后，resolve→重新选择→preview→confirm可在inspectMember=0时发第二POST；该路径普通UI也可触达。

要求：以整个draft/原操作为边界，跨row拒绝或安全排队，保证同一时刻最多一个原member mutation；不能通过resolve/reselect/repreview/new upload/loadDraft清除未知写归属。pending和unknown保留原输入/row/entity/连接/动作绑定。unknown先核原member/list/history，缺精确本次ACK只标observed_active_needs_reconciliation，不能自动重发/假applied。不要新造正式receipt系统或给原owner新增未承诺能力。

可以拒绝在途换文件/冲突编辑，或安全排队至原操作明确结束；不捆死特定错误码。resolve/select等只读动作如允许，应保持未知原操作记录，不能恢复写许可。修在machine/明确公共API边界，不只靠按钮disabled。若删除未承诺的调试暴露接口，仍须证明承诺的mount.loadDraft/宿主生命周期不会破坏归属。

邻接回归：同row双击、跨row确认/批确认；pending/unknown时换文件、恢复草稿、换连接、dispose；成功ACK迟到/丢ACK/另一writer改member/名单version改变；逻辑删除不自动restore；原add幂等不用于盲重发。

### U-C：异步reply绑定draft/row/选择epoch（ACCEPT-U05）

基线 `machine.js:381–436`：A预览暂停，选择改为B，A回复将row设preview_ready并挂A的token/metadata，而selected_entity_id仍B。普通UI事件有busy保护，导出machine/host调用可触达。这里只证明组件绑定错，**未证明真实owner错误写入**。

要求：迟到reply必须对应当前draft/row/选择/连接与必要version；冲突编辑拒绝或令旧reply作废。A token不能许可B行动。覆盖resolve/preview交错、输入/候选更换、旧连接回复、取消/销毁；原不透明preview payload/hash保真，不能UI造owner token。

## 有效反例和范围

[5个可移植业务反例](evidence/universe-product.test.mjs)在原实际machine/parser+传输边界fake上稳定5F，不是缺src或导入错误。已用明确entered gate协调，无15ms固定sleep，不绑错误码，并允许安全排队；将这些业务断言移入自己Lab，修成5P及上述邻接回归。fake只在外部输运，不替换machine/投影/校验函数；另用**真实交付adapter→machine→mount**覆盖原公共响应，不能全用理想fake adapter。

总控复验原unit145P；Python52P后唯一因验收无独立Git index失败的小例纠正环境后1P；浏览器初DNS保护误挡loopback不算产品失败，纠正后单真实E2E1P31.26s，另5DOM集成未复跑。修后一次运行本包完整JS/Python功能组+安全真实浏览器mock E2E，给实际新计数，不照抄204，也不把总控环境错误当成待修业务。

## 交接/测试安全同轮修复

- 原final指新C3fdbba0/最终reviewer，但invocation_ref仍指旧147500d5/第一轮reviewer；round07自述不能补这个引用。修复后调用真实不同agent审最终C，新增本轮invocation/round/final及真实hash，不把旧调用改成新日期/新C。
- 旧“没有src运行fail2”的记录保留并正确标bootstrap/import失败，不声称有效业务TDD。用本次5真实红作为修复起点。报告86/204前后矛盾要在新R1报告按实际执行范围澄清，不改写旧历史。
- 原Chrome helper缺启动失败finally/外网保护；完善本Lab真实测试保护，绑定本人profile/PID/端口，远端拒绝但本人127.0.0.1可用，任何失败都清干净。不借主UI会话或真实名单/用户文件证明。
- 本Labvalidate-delivery须拒绝错C/旧invocation/错reviewer/文字或null hash/缺引用，不用自身valid替代真实独审。

## 完成和交回

只做输入/真实红→合并修复回归→最终集中独审三个大节点。所有业务与证据/安全问题修尽，真实不同agent最终passed/open_findings=[]后交，不再用accepted limitation带过明确缺陷。原卡未接生产/gateway的边界继续保留，production_ready/financial_qualification_granted=false。

新package_id=`UI-UNIVERSE-28-R1`，新交接位置：
`C:/Users/郑曾波/Projects/iqs-universe-import-ui-lab/docs/handoff/UI-UNIVERSE-28/remediation-01/handoff.json`。

原handoff1.0.0及report/tests/artifacts/cleanup/review全齐，C/M与最终调用/文件hash闭环见共同规则。旧交付保留，其他目录禁写；总控再验收后才接原UI/唯一owner。
