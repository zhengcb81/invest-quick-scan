# routing 包发布候选（选项 A）— 2026-10-18

状态：**仅在副本演练，未对真实仓发布**。目的是让 owner 在批准前看到“发布到底改什么、风险多大”。

## 副本发布结果（runs/existing-list-onboarding-2026-10-18/route-publish-rehearsal）

- 命令：`python scripts/question_sets.py publish-routing`（再 `--activate` 于副本）
- 新包：`pkg_b5a41d8c9f89adba8d57cce1792b1cac8db5378509996f6614472a691cfb5fba`
- 新 release：`modrel_fc5de4a3dcce55866c8a2a83d82cdaa8caf8a3c59b6406d3a0ea75e7c9e01e74`
- 规模：48 模块 / 222 题
- 历史包：`pkg_24f079…`（schema 1.0，router 1.0，无 routing policy）

## 与历史包的差异（关键）

| 项 | 历史 | 新 |
|---|---|---|
| 模块内容 | — | **完全相同** |
| scoring contexts | — | **完全相同** |
| release schema | 1.0.0 | 2.0.0 |
| router_version | 1.0.0 | 2.3.0 |
| routing_policy_sha256 | 无 | 05f2cf6c… |

即：发布只是给现有题目加上可执行的 v2 路由策略，**不改任何题目/上下文**。

## 000026 演练

- route decision：`route_327b3c77f112b7636c6c67010e35a8655ebac61ea1e6a1fc4166608be853a686`
- status partial；dispatch `ready_common_and_risk`；**minimum_questions = 24**
- `compose-route --max-questions 1` → 拒绝（低于 mandatory core/critical-risk coverage）
- `compose-route --max-questions 24` → 成功（manifest 137,983 bytes，questions.json 68,049 bytes）

## 真实发布的改动面（若批准）

1. `questions/releases/` 新增 release 目录与 routing policy artifact；
2. `questions/releases/current.json` 指向新 package；
3. 之后所有新 route 使用 v2 策略；旧任务/旧 release 字节不变（历史读取按 release id）；
4. 无网络、无模型调用。

## 风险 / 需要审查

- current 切换影响后续所有新路由；需要确认旧 run 的读取路径仍按 release id。
- 正式 route 至少 24 题，单家公司成本上升（按 CATL 2 题用量粗估，24 题约 0.17–0.25 美元，具体以实际 usage 为准）。
- 发布是治理动作，需 owner 批准 + 独立审查后执行；副本结果不能直接搬进真实仓。

## 备选（选项 B）

owner 手工指定 route：仍需 24 题覆盖或修改 mandatory coverage policy，且要构造合法 route/manifest；并不比 A 省事，且绕过路由策略的治理。

## 建议

- 若目标是尽快跑出 1 家正式画像：批准 A（发布 routing 包）→ 副本已验证 → 真实发布 + 审查 → 000026 准入 + 24 题 run。
- 若不接受 24 题成本：需要改 policy 的 minimum coverage（另一个治理决定），否则正式入口就是 24 题。
