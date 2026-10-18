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

## 现状

- 209 verified / 5 provisional；214 画像页；CATL 2 条旧观察 + 金融复核；新题运行未发生。
- 本轮无模型调用、无付费、无业务库写入。
