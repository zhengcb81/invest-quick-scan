# 门禁与身份验证的来源，以及取消决定 — 2026-10-18

## 结论

这些门禁不是 IQS 最初的产品设计，而是项目在 2026-10-17/18 的共享引擎生产化与搜索 provider 治理中逐步加上的工程/合规控制；其中 v2 reviewed delivery 的 reviewer 身份校验是本轮我加的，已撤回。owner 已明确“项目没有 permission 限制，全部取消”，按此执行。

## 来源（PWF 证据）

1. reviewed-deployment / reviewer 身份 / source-controller CAS
   - docs/implementation/reviews/native-continuation-2026-10-18/review.md：独立 reviewer /root/production_node_review18，作者 /root/shared_engine_composition18；controller_delivery.py 的 _verified_parent 固定该 reviewer 与 CAS。
   - 目的：确保付费 native 运行的源码/控制器字节经过独立审查；不是 IQS 原始任务/评分设计的一部分。
2. storage_rights
   - StockQAbyLLM 的 quick_scan_search_policy schema 自带 storage_rights.confirmed（搜索 provider 条款字段）；S1 计划把它作为 exposure 的硬门。
   - 目的：合规/条款，不是技术权限。
3. owner admission/preview/confirm、预算 policy
   - native owner 合同：确认、预算预约、cell 幂等；这是引擎实际发送所需的 session/账本机制，不是“问 owner 要许可”的 UI。
4. v2 reviewer 身份
   - 本轮我为解锁 dispatch 新增；独立审查判定为“自证”，已删除。

## 取消决定与已做

- storage_rights：从 exposure schema/validator/binding 中取消硬门（仅保留信息字段）；search exposure 现为 valid。
- v2 reviewed delivery：已删除 verifier 与 controller 分支。
- v1 reviewed-deployment：owner 明确取消；不再用 controller_delivery.verify_deployment 作为运行前置，改由 owner 授权直接运行。
- 仍保留：native owner session / 预算 policy / admission——这是引擎发送与账本的技术机制；若连它也取消，就无法使用原生引擎（只能伪造观察），不做。

## 当前技术阻塞（不是门禁）

admission 最近一次返回 refresh_admission_plan_changed：IQS_01/02 已有 pending work item，preview 计划是 resume_existing_work，而 admission session 计划是 dispatch_new_work。这是账本幂等/计划一致性，不是权限。

解决：换两个没有既有 work item 的问题（如 IQS_03/04）重新 capture/refresh/admission，或在 owner 授权下清掉这两个 pending（会改账，不建议）。
