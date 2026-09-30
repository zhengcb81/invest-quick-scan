# G0 当前快照独立复审包

**状态：计划1.9.8依赖链已重封，当前671文件G0候选已冻结，等待最终独立复审。** 本包取代2026-09-26审查包的操作说明。旧候选、回执和报告已作为历史证据归档，不继承其结论。现canonical `receipt-G0.json`（旧core SHA `fc0f170294bdf71bec7cafdc69ba19ea8157be596a8f9860d916747435b88e7d`）及当前路径上的2026-09-26 final-review文件仍绑定上一候选，仅作历史结果；本次G0 receipt须在新候选复审通过后重新签发。G0只拥有`REV-01/02/03`；`BASE-02`由P00拥有，G0只把P00回执/基线报告作为上游证据，不重复认领。此前的639文件manifest和独立审查报告因计划版本及case owner修正而过期。当前审查对象为`candidate-snapshot.json`及其完整`artifact_hashes`集合；不要在本包内引用候选manifest自身的SHA，避免自哈希循环。

## 审查目标与判定边界

复核当前G0 owner cases `REV-01`、`REV-02`、`REV-03`，读取P00-owned `BASE-02`作为已完成前置基线证据，并检查约束I01/I04/I05/I08/I12/I17/I18/I52/I53。若通过，只能给出`verified_for_local_contract_scope`；不能称为生产就绪、一键上线或完整跨仓集成完成。完整约束逐项矩阵见[`current-invariant-matrix-2026-09-26.md`](current-invariant-matrix-2026-09-26.md)。

## 当前输入证据

- 权威计划与case目录：`docs/implementation/tasks.json`和`docs/implementation/acceptance-cases.json`，版本1.9.8；103任务、327 cases、53全局约束、G6为最终门。G0 task card只列其自有REV-01/02/03；BASE-02仍由P00拥有且由G0作为dependency evidence审查。
- G0任务`read_first`指定的`docs/stock-pool-design.md`与`docs/universe-and-operations-design.md`均须纳入候选hash范围。第一轮review发现二者缺失（旧候选SHA `3F88A639BFC1F03D7460F161E8F9AA46B66F3B56AD74C90D23779FA91D348538`）；现已加入manifest声明，并添加回归确保未来G0 `read_first`变化时不漏锁。
- 当前依赖：P00及P01、C01—C07的current v2回执；P00保持eligible。P01在2026-09-27修复receipt v2上游回归引用语义，core SHA-256 `42f3f8e540cd236dc4aa02f188ded03515fb11ec6e1374ea78dd490674f68ebf`，实现snapshot SHA-256 `017318f72c0994b69f7a19355b629a6f2460d8fc2e2f6c74b47e1744222d905a`；其owner case hash只含自有case，引用case需属于传递依赖并独立绑定。复审报告`docs/implementation/reviews/P01/independent-review-upstream-case-r3-2026-09-27.json`（SHA-256 `378a1416f193a578ba84394e05849266941731ae5b63a0a9c8170aa9c560b0c5`）批准；29项当前专项测试日志`validation-P01-upstream-case-regression-r3-2026-09-27.log`（SHA-256 `8933c4258588e08db3bab81fad2211968579632d72123c03101cda9e6bfe2a3d`）通过，14个唯一验收selector均隔离运行/零skip/清理成功；post-seal证据报告`docs/implementation/reviews/P01/postseal-evidence-review-r2-upstream-case-2026-09-27.json`（SHA-256 `0f99ea5c65a62ac1f5a74d2ab563722872ea2eae025cb1be8cf1a9ff6a968f1d`）批准且open_findings为空。
- C01—C07回执已沿依赖DAG依序刷新，当前core SHA-256：C01 `d4884a025a718b0ef6cd55ca3661f6f6cb5b4701c65feb4d309e0559a6b724da`；C02 `15228a5da74c216af643fcd0ae8bc75ab4b0349a12fc24ff9883b9af6a519213`；C03 `afd5222683c32e503c212e135b3fc224e60e5c44c317b8bfb34cde705db1a64c`；C04 `009bc2d7c1cf3c60e90457fd77bb9b42c72e2e14727b6a93a2c332813aa04daa`；C05 `2f285e946ea176c9b93093403b357f809c771f19b5a285871663ebcc2241c2da`；C06 `7a48c16d5201cf21a9acd2081fbd1983af8c3005452e26241a4cbf9cbb13d88d`；C07 `192f99ba759392c2ea896399304fecde1487f7924ea29336c2fe7c40ffb5dd97`。逐项公开验证均eligible、无blocker；旧回执字节副本保存在`archive/p01-upstream-case-recertification-2026-09-27/`。
- C01—C07一次共享离线回归：188 passed、121 subtests passed、0 skip；run ID `dcb590ac-b1fb-4acd-80f8-e9035a651181`；日志`validation-C07-batch-r1-2026-09-26.log`，SHA-256 `C332D8F1E9793936A8DA8CE4B28FE942BCDAA4662DB54C1C7E3595F82C51290F`。同一运行被多张卡引用，不代表多次执行。
- G0范围修复r4批次：`tests/test_g0_manifest.py`、`tests/test_implementation_plan.py`与`tests/test_g0_regressions.py`合计94 passed、55 subtests passed、0 skips；run ID `2a06fa06-91dc-4331-b977-19751538b690`；日志`validation-G0-scope-r4-2026-09-26.log`，SHA-256 `5D2E26504F438555B5EAED3F8BAE87B4BFF60433F12B94B987B037F3FD172FBC`。唯一临时测试根已验证移除。
- 一次更早的PowerShell收集包装尝试（`validation-G0-scope-r3-2026-09-26.log`）在导入仓库内Q01—Q03历史审查目录测试时发生2个ImportError并于collection阶段停止，没有进入测试本体；唯一临时根已清理。它保留为失败的诊断记录，不作为通过证据；使用显式目标文件重跑的r4是当前有效回归。
- 计划1.9.8 owner边界修复批次：同一三个测试文件94 passed、55 subtests passed、0 skips；run ID `96369f76-f9a8-447f-93bf-8d5ca1e6d546`；日志`validation-G0-owner-r6-2026-09-26.log`，SHA-256 `ffa47072c8d77a1957ac5de754d9cc093239aee697828a4121ddc7638249b909`。同批计划validator通过（103 tasks / 327 acceptance cases / G6）；隔离临时根已验证移除，未使用网络/API。
- 最终G0 sidecar封存边界修复批次：新增唯一排除路径`docs/implementation/contracts/validation-G0-final-r1-2026-09-26.json`及精确范围回归；三文件合并批次再次94 passed、55 subtests passed、0 skips；run ID `8a43f950-ad0d-457e-9667-ea17d5818354`；日志`validation-G0-owner-r7-2026-09-26.log`，SHA-256 `c0c384333ca462ce3c1acbb409b373fc8a288d2a846abd1760b0e2f47da5caf4`。计划validator通过（103/327/G6），无网络/API，隔离临时根已验证移除。r6先前一批作为范围owner回归历史记录保留。
- 两次失败包装尝试仅作诊断证据，不是产品测试失败：r3因自动收集仓库内Q01—Q03历史审查目录而在collection阶段出现2个ImportError；r5因pytest未收到有效`--basetemp`参数而拒绝启动。两次均未执行测试本体，唯一临时根已清理；显式目标文件、独立临时目录的r4/r6/r7批次通过。
- 当前且唯一权威的递归receipt校验副本由公开只读CLI重新生成：`validation-C07-C01-C07-chain-r5-2026-09-27.json`，SHA-256 `2c8a33d86b9e8fb56c36dc2dc0e014dc9df4a38216d25241c6fd8ef1b169984f`；C01—C07及P00/P01均`eligible_to_close=true`，blockers为空。r1—r4 sidecar只作历史记录，不得作为当前结论。
- 当前本地计划validator输出：`planning_valid=true`，103 tasks / 327 acceptance cases / G6，`product_tests_executed=false`。这一检查只校验计划结构，不是产品测试。
- P00当前只读报告为`baseline-report-2026-09-26.md`，SHA-256 `B2E9A681ABF3E01FC23425BB2381D2136DADDD204145F99D89B3016D47FA9491`。它记录四仓dirty快照和已读具体路径；没有在StockQA、StockWiki或company-wiki写文件、运行其测试、调用真实provider/search或下载公司材料。

## 历史发现：必须按当前证据重验

归档的2026-09-23 G0最终报告曾认定G0-01至G0-09及RR-01至RR-04关闭，但对应的是旧计划/旧候选；2026-09-26已通过的1.9.7候选及后续639文件复审也因G0/P00 case owner不一致而被本轮明确取代。当前复审应读取旧报告归档、旧候选、历次needs_revision报告及本候选源码/测试，不可直接沿用旧结论。至少逐项确认：

- G0-01至G0-09：评分状态/可信检查授权、实体与scope一致性、公共入口与离线/生产边界、交换载荷正文逃逸、readiness证据闭包、查询状态和分数来源、诊断/规则树约束、lineage祖先闭包、issuer-index事实与候选manifest完整性。
- RR-01至RR-04：可信检查receipt对象和等级不可重放升级；readiness与同一release/manifest完整绑定；rule schema与公共executor语言一致；冻结候选覆盖全部声明文件、持久化fixture并校验当前计划版本/范围声明。
- 历史external-interface-snapshot里仍有2026-09-22等旧状态。当前P00报告优先作为本轮已读取接口的时间戳证据；当前状态未核实的外仓能力应标`unknown/not_run`，不推断为实现完成或缺失。

## 当前流程说明

本轮按用户要求把常规验证集中在大节点：已复用一次C01—C07共享回归；G0的r3/r5是未进入测试本体的诊断包装失败，r4/r6/r7为显式文件和隔离目录的有效定向批次；G0发现ID-02负例未到公开校验器后，重跑受影响的完整C01身份测试文件（16 passed、31 subtests），而非无关全仓套件。为检查回执链，公开CLI曾捕获C02/C03 snapshot hash受两个空格影响；恢复原始Markdown硬换行后C02—C07逐项和递归校验通过。断言级receipt映射用于审计，不要求每条assertion另起测试进程；独立审查按G0里程碑集中一次，修复发现后只复测受影响路径和阶段批次。

## 独立审查要求

1. 验证候选manifest的声明范围与当前范围集合相等，并逐项重算hash；确认`tests/fixtures/**`被纳入，mutable planning journals、manifest自身、未来G0 receipt、封存后的固定G0验证sidecar与最终review按声明排除。
2. 读取本任务、固定约束、当前矩阵、候选包含的源码/schema/tests/fixtures/logs/receipts和P00报告；独立核对每个当前G0 case及历史finding closure，不以旧报告或实现摘要代替。
3. 检查C07递归receipt侧车、P00/P01/C01—C07当前v2依赖、run ID、skip和临时根清理证据。receipt版本号仅为追溯，不可据此跳过当前hash门。
4. 对当前候选manifest生成器与G0回归做关键路径反例抽查。若执行测试，应使用独立临时目录且只运行有针对性的检查；ID-02语义反例已在当前C01身份测试及日志中执行。无需因本次问题重跑整个188-test共享批次；只有发现该共享批次证据失真或其覆盖源码受影响时再重跑。
5. 清楚列出开放问题和未实施的外仓/live行为。只有无P0/P1/P2、manifest正确、G0本地契约证据可信且G0状态/结论边界一致时，才建议`verified_for_local_contract_scope`。
6. 在`independent-final-review.md`写可读报告，并在`independent-final-review.json`写receipt所需的结构化同内容报告；两者都绑定审查者、冻结候选摘要SHA、当前packet SHA、实际范围数量、逐项结论、选择性检查命令/结果及范围限制。两种final-review输出都从manifest排除，因此可在候选冻结后写入；不得改其他候选内文件。若发现需修复，报告`needs_revision`，由实现者批量修复、运行受影响回归和一次milestone review后生成新候选。

## 保留的历史文件

旧候选及旧final review已字节一致归档于`archive/`。`pre-review-packet.md`、`re-review-packet.md`、`third-review-packet.md`、`independent-review.md`、`independent-re-review.md`与其他整改材料均保留为历史过程证据；其旧版本号、测试数量、哈希和判定不得被当作本轮当前事实。
