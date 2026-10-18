# Fresh-budget exposure contract + CATL 2-question admission — 2026-10-18

## 背景

owner 批准 fresh-budget 合同改动与 $30 预算。原 1.4 exposure 要求“恰好两个 retained unknown-cash attempt”（1.5 是 1..350），而旧 ledger 有 3 笔未结算且禁止改 policy version；新 policy 又没有 retained refs。两者互斥，导致新 run 无法准入。

## 合同改动

- 新 snapshot 协议 `stockqa.owner_exposure_snapshot/1.2.0`：
  `attempts=[]`、`requests/reserved/spent=0`、`cash_actual_complete=false`、`fresh_budget=true`、`owner_ack_ref`。
- QA `exposure_snapshot(..., fresh=True, owner_ack_ref=...)`：
  - 只允许 dialect 1.4.0 且 `attempt_ids` 为空；
  - 只读校验新 policy 已安装、该 policy 下 0 attempt / 0 request / 0 reserved / 0 actual；
  - 返回 1.2.0。
- QA `validate_control` / `validate_retained_rows` 接受 1.2.0，校验 fresh 标志与空 refs、policy_id/hash、零 attempt。
- IQS `refresh-v1.4.schema.json`：`ExposureSnapshot` 允许 1.2.0；`quote.retained_unreconciled_attempts` 收紧为 `enum [0, 2]`（fresh=0，旧路径=2）。

## 治理边界（审查结论）

- `owner_ack_ref` 只是**标签**，不是可验证的 owner 决定；真正的边界是 owner policy 的写权限 + 本次 admission。
- fresh 模式不能绕过 policy 安装：preview / register / inspect 都会复核 policy_id/hash 与 0 attempt。
- `validate_control` 单独不足以授权；必须与 `validate_retained_rows` 成对使用（已写入 docstring）。

## 预算与状态

- 新 budget policy：`iqs-catl-0102b-20261018` v2，max_cost **$30**、max_requests 20、in_flight 3、mimo-pro-t2 3；spent 0。
- 旧 policy 的 3 笔未结算 attempt 原样保留，未改账。
- owner policy 已恢复为原 1.5 备份（sha `3239c35b…`）；为此安装的 14C 已撤下。
- 新预算 policy 行保留（0 attempt，无费用）。

## 准入结果（已完成，随后因 deployment 门未 dispatch）

- preview：`rv1_ce80e4d64808…`，status ready，2 items（IQS_01/02），budget_available true。
- delegated confirm：`rc2_3fdbc53b0f34…`。
- admit：accepted，`permission_authenticated=true`、`registered_with_executor=true`、**API_requests=0**。
- preview 已过期；policy 恢复后该 admission 不再可用。

## Dispatch 阻塞

计划用两题驱动 `batch-carrier-controller-candidate/run_real_profile_smoke.py`（`iqs.real-profile-smoke-config/1.0.0`），但 `controller_delivery.verify_deployment` 报：

```
ValueError: engineering_reference_path_or_hash_changed
```

controller CAS / review final 与证明的精确字节不一致，reviewer id 固定，不能自签；fresh-exposure 也不在已审 source pins 内。**在现有 reviewed-deployment 门下，2 题付费 dispatch 不能合法执行。**

## 测试

- QA 单测：fresh 快照 0 attempt、空 ack、非空 policy、dialect 1.5、显式 refs、retained 空 refs 等；41 passed（1 个既有失败与本次无关）。
- 既有失败：`test_schema_addition_keeps_existing_rows_and_new_tables_empty` 期望 user_version 24，实际 25。
- 未做 schema 单测（1.2.0 畸形逐项）——待补。

## 下一步

1. 为 fresh-exposure + 两题驱动做新的 reviewed delivery（source/controller pins + review final），或另建经审查的两题执行器；
2. 之后 preview → confirm → admit → 2 题 pack → 导入 → 刷新画像；
3. 若不做 re-delivery，则保持现状，不再尝试付费 dispatch。
