# CATL 新题真实运行尝试（IQS_01/02）— 2026-10-18

目标：在真实 owner 环境用 CATL 已有 subject/路由跑一个 **2 题**新 pack，验证“新题 → 真实答案 → 画像”的主线；不扩公司。

## 已就绪并验证

- owner capture：`score.iqs_01/02` 成功，snapshot `snap2_2bc1a948…`。
- refresh request（1.4.0）：`refresh_contract.validate_request` 通过。
- control（`stockqa.owner_budget_continuation/1.0.0`，单 cell 2 题、snapshot 1.0.0、max_new_http_requests=1）与 policy（`stockwiki.refresh_owner_policy/1.4.0`）：`validate_policy` 通过。

## 阻塞

安装 1.4 policy 后，真实 preview 返回：

```json
{"status":"rejected","error_code":"refresh_owner_preview_rejected","API_requests":0,"dispatch_started":false}
```

直接调用 `RefreshPreviewService.preview` 拿到真实异常：

```
ValueError: refresh_executor_inspection_unavailable
```

即 preview 里的 executor inspection 子进程失败。手动复现：

```powershell
python -m src.utils.quick_scan_refresh_inspect_cli --ledger <qa.work_store> --policy <qa.budget_policy_file> \
  --request <refresh-request-catl-0102b-14.json> --schema-version 1.4.0 [--admission-config <...>]
```

返回：

```json
{"protocol":"stockqa.refresh_inspection/1.4.0","status":"rejected","error_code":"refresh_executor_inspection_rejected","API_requests":0,"reservation_created":false}
```

带/不带 admission config 结果相同；CLI 折叠了具体原因。

## 处置

- **owner policy 已按备份原样恢复**（sha 一致），没有留下半改。
- 没有 preview/confirm/admit、没有付费调用。

## 下一步（诊断顺序）

1. 直接调用 inspector 的内部函数（或给 CLI 加临时异常打印）拿具体 ValueError；
2. 对照 1.4 inspection 的请求要求：cohort/continuation、ledger budget policy、request_id 唯一性、execution profile 字段；
3. 若是 1.4 不支持该 request 形态，改回 1.5 + 找到满足 complete current sources 的两个 exposure refs；
4. 修复后再 preview → delegated confirm → admit → 1 个 2 题 pack。

## round 2：preview 已通过 executor inspection，最终卡在预算

修复两个真实问题后（research-only 读路径；`policy.qa.policy_id` 必须等于 budget policy id，而不是 owner policy id），1.4 路径的 owner preview **成功生成**：

- preview_id `rv1_812c5fe976ded69eb9da3ba82fcbaffb246fbe746d17774ab2fa3cdf1322a1a9`
- items：IQS_01、IQS_02 均为 `dispatch_new_work`
- expires_at 2026-10-18T12:04:09Z（15 分钟）

但 preview **status = blocked**，原因在 quote：

```json
{"budget_available": false, "max_cost_micros": 100000, "max_http_requests": 1,
 "planned_physical_requests": 1, "retained_unreconciled_attempts": 2,
 "cash_actual_complete": false}
```

即：ledger 里仍有 **2 个未对账（unreconciled/unpriced）attempt**，预算不可用；不是代码问题，是 **owner 预算决定**。

## 处置

- owner policy 已按备份恢复（sha 一致），没有留下 1.4 policy。
- 没有 confirm/admit/run，没有付费调用。
- 预览记录留在 runs（会随 policy 恢复而失效）。

## 下一步

1. owner 对 2 个 retained unreconciled attempts 做结算/预算 amend（这是 owner 决定，不是 agent 可代做）；
2. 重新生成 1.4 preview；budget_available=true 后 confirm → admit → 2 题 pack；
3. 若 owner 不愿动旧账，则新题真实运行只能暂缓。
## 现状

- 209 verified / 5 provisional；214 画像页；CATL 2 条旧观察 + 金融复核；新题运行未发生。
- 本轮无模型调用、无付费、无业务库写入。
