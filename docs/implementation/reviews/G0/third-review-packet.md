# G0 第三轮独立审查包

本包针对第二轮报告[`independent-re-review.md`](independent-re-review.md)的RR-01至RR-04。计划版本为1.6.0；`tasks.json` SHA-256为`DD92496E092981F31B429417BA0D905FD47ADDCCA9DBAC21F20FBA7D8AD0C7E4`，`acceptance-cases.json` SHA-256为`786B37894B38EFB8655F1501C392251FEC4E8ED55BD081D2727F0BC2A57BF7AF`。

- RR-01：可信检查回执现为带内容hash的记录，绑定entity、question、observation、精确授权等级、签发者和active状态；五类重放/升级负例已加入公共validator回归。
- RR-02：full readiness在Schema中要求G0—G6各一次，每条gate带release及manifest hash；`validate_readiness_response`把响应证据与预期ReleaseSet动态交叉核对。
- RR-03：CompositeRule递归仅接受CompositeRule，叶子必须由`condition`包装；裸叶子/嵌套policy拒绝，多层有效树可执行。
- RR-04：[`g0_candidate_manifest.py`](../../../../scripts/g0_candidate_manifest.py)从声明范围排序枚举文件，manifest标记`G0_frozen_for_independent_review`；验证器要求范围集合与hash键集合完全相等并逐项重算。候选覆盖题库、Schema、所有helper、所有测试、fixture、实施契约、历史/整改回执和原始日志，只排除manifest自身及未来最终审查报告以避免自引用。

最新本地结果为184 tests、108 subtests通过；计划为73 tasks、172 cases并明确`product_tests_executed=false`。原始摘要见[`second-remediation-validation-2026-09-23.log`](second-remediation-validation-2026-09-23.log)。E2E-06是本轮按用户要求新增的真实数据隔离/清理live案例，仍为`specified_not_executed`，不会被本地测试冒充通过。

请独立复跑全套测试、manifest集合等值检查及RR-01—RR-04恶意输入。只有全部关闭才能把G0判为verified；复审报告请新建`independent-final-review.md`，不得修改冻结范围内任何文件。
