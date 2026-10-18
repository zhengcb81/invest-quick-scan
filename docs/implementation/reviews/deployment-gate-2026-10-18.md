# CATL 2-question admission 成功，dispatch 被 reviewed-deployment 门拦住 — 2026-10-18

## 已完成

- fresh-budget exposure 合同（snapshot 1.2.0 + owner ack）落地并通过校验。
- 新预算策略 `iqs-catl-0102b-20261018` v2（$30 / 20 次 / in_flight 3）安装，旧 3 笔未结算未动。
- owner 流程真实走通：
  - preview `rv1_ce80e4d64808…` status ready（IQS_01/02，budget_available true）
  - delegated confirm `rc2_3fdbc53b0f34…`
  - **admit accepted**：permission_authenticated、registered_with_executor、API_requests=0

## dispatch 阻塞

计划用现成的两题驱动 `batch-carrier-controller-candidate/run_real_profile_smoke.py`（协议 `iqs.real-profile-smoke-config/1.0.0`）运行，但其部署证明校验失败：

```
ValueError: engineering_reference_path_or_hash_changed
```

`controller_delivery.verify_deployment` 要求 controller CAS / source CAS / review final 与证明中的精确字节一致；当前 workspace 的 controller 文件已漂移（不是本次改动造成），且该证明绑定固定 reviewer id，不能自签。新的 fresh-exposure 代码也不在已审 source pins 内。

结论：**在现有 reviewed-deployment 门下，2 题付费 dispatch 不能合法执行**；需要重新交付/独立审查（new source/controller CAS + review final）或另建一个经审查的两题驱动。

## 处置

- owner policy 已恢复为原 1.5 备份（sha `3239c35b…`）。
- delegation install 已恢复为先前文件。
- 新预算 policy 行保留（0 attempt，无费用），不影响旧账。
- **无付费调用**；admission 记录留在 runs（policy 恢复后不再可用）。

## 下一步选项

1. 走完整 re-delivery：独立审查 fresh-exposure + controller，生成新的 reviewed proof，再 dispatch（多轮）。
2. 为两题路径单独做一次 reviewed driver 交付。
3. 暂停付费运行，保留 admission 证据与合同改动。
