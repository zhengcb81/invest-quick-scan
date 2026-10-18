# 公司画像生产入口：owner 查询被 subject 合同拒绝 — 2026-10-18

## 已建成

- refresh 1.4 路径确认（24 题可 1 cell、1 HTTP、1 admission）。
- 000026 的 **standard-1 24 题 manifest**（pkg_b5a41d8c…，observation_ingest_ready=True）。
- **authority**（c06_authority.create_authority，schema 2.0.0）+ **context2**（24 题，每题的 subject_binding 与 listing material）：`context2-000026.json`。
- 副本 route snapshot + universe member 已演练。

## 卡点

owner 查询 CLI（`stockwiki.quick_scan_query_v2_cli`）对 000026 返回：

```
{"status":"rejected","error_code":"subject_contract_output_invalid","API_requests":0}
```

试过：
- 24 个字段（score.iqs_01…24）→ rejected；
- 2 个字段（score.iqs_01/02）→ rejected；
- CATL 用过的 score.iqs_12/16 → rejected。

说明不是字段数量/字段名，而是 **000026 这个 subject 还没被 owner profile 合同接受**。CATL 的 subject 之前有完整 bundle（authority/context/question bindings/execution inputs）并经过安装；我们目前只有 analysis_subjects 里的 subject + receipt，没有把 context2/question bindings 安装进 owner 侧。

## 判断

- 身份/route/universe 是必要但不充分；**owner 查询与 preview 还需要把 subject context（context2）与 question bindings 注册到 owner 工作区**。
- 需要找到 CATL 当时对应的安装步骤（activation 里的 execution inputs / subject-binding / listing-bindings 只是文件，真正注册可能还有一步），或者补一个 owner 侧 context 安装/注册能力。
- 这是“公司画像生产入口”真正剩下的工程缺口，不是配置错误。

## 下一步

1. 查清 CATL 的 context2 是如何进入 owner 查询/preview 合同的（activation 脚本、preview 读取路径、execution_inputs_root）；
2. 为 000026 补同样的注册（优先副本）；
3. 再重试 capture → preview → 1.4 admission。

## 边界

- 未写真实 route snapshot/universe/policy；未调用模型；只有 owner 查询 CLI 的拒绝（0 API 请求）。
