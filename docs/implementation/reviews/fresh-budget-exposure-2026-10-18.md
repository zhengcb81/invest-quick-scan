# Fresh-budget exposure contract + CATL 2-question admission — 2026-10-18

## 背景

owner 批了 A（合同改动）与 $30 预算。原 1.4/1.5 exposure 合同要求“恰好两个 retained unknown-cash attempt”，而旧 ledger 有 3 笔未结算且禁止改 policy version；新 policy 又没有 retained refs。两者互斥，导致任何新 run 都无法准入。

## 合同改动（owner 显式 fresh budget）

- 新增 snapshot 协议 `stockqa.owner_exposure_snapshot/1.2.0`：
  `attempts=[]`、`requests/reserved/spent=0`、`cash_actual_complete=false`、`fresh_budget=true`、`owner_ack_ref`。
- QA `exposure_snapshot(..., fresh=True, owner_ack_ref=...)`：只读校验新 policy 已安装且该 policy 下 0 attempt/0 spend，返回 1.2.0。
- QA `validate_control` / `validate_retained_rows`：接受 1.2.0，校验 fresh 标志与空 refs。
- IQS `refresh-v1.4.schema.json`：`ExposureSnapshot` 允许 1.2.0；`quote.retained_unreconciled_attempts` 从 const 2 改为 integer 0..350（fresh 时为 0）。

## 预算与状态

- 新 budget policy：`iqs-catl-0102b-20261018` v2，max_cost **$30**、max_requests 20、in_flight 3、mimo-pro-t2 3；spent 0。
- 旧 policy 的 3 笔未结算 attempt **原样保留**，未改账。
- owner policy `IQS_CATL_0102B_POLICY14C` 已安装（含新 budget、fresh snapshot、admission config）。

## 准入结果

- preview：`rv1_ce80e4d64808…`，status ready，2 items（IQS_01/02），budget_available true。
- delegated confirm：`rc2_3fdbc53b0f34…`。
- admit：accepted，`permission_authenticated=true`、`registered_with_executor=true`、**API_requests=0**。
- 尚未 dispatch/付费；engine 的 2 题 run config 还未构建（driver 面向 24 题 bundle，需按 2 题 admission 适配）。

## Dispatch attempt (12:20Z) — blocked at prepare_execution

Cold run config built (`runs/existing-list-onboarding-2026-10-18/catl-0102-run`, 415 source pins) and launched with MIMO keys. It stopped **before any HTTP**:

```
OwnerRefreshRejected: refresh_consent_native_rejected
  prepare_execution -> read_registered -> consent inspect
```

Likely cause: the driver's `process_env=dict(os.environ)` for the job did not carry `PYTHONPATH` for StockWiki, so the nested owner CLI used by the consent endpoint could not import its package; native consent therefore rejected. No API_requests, no reservation, no dispatch.

Owner policy restored to the pre-14C backup; preview expired at 12:26Z.

### Next

1. Re-run preview -> delegated confirm -> admit (15 min TTL) with `PYTHONPATH=StockWiki;QA` exported to the driver process.
2. Re-use the same cold config (confirmation id updated) and launch immediately.
3. If consent still rejects, run the owner CLI `--permissions-request-stdin` manually for the confirmation and capture its stderr.
## 待办

1. 为 2 题 1.4 admission 构建 `iqs.real-admitted-smoke-config/1.0.0`（bundle 5 文件、confirmation、deployment、source_pins、run_root）。
2. 运行 cold 2 题 pack（预计 ~$0.015，单次上限 $0.10）。
3. capture/import 2 条 observation，刷新 CATL 画像页。
4. 若不再继续：恢复旧 owner policy 备份，并记录 admission 作废。

## 风险

- QA 合同代码与 IQS schema 已改，需补单测（fresh snapshot、validate_control、retained 空 refs）。
- owner policy 当前为 14C；旧 policy 备份在 `runs/existing-list-onboarding-2026-10-18/policy-before-flow14c.json`。
