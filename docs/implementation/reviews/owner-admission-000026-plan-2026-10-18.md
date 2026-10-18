# owner 准入写前报告：000026 飞亚达（正式 24 题画像）— 2026-10-18

状态：**写前报告，真实 owner policy/route/universe 尚未写**。routing 包已发布；subject 已导入真实 workspace（有备份）。

## 已就绪

- identity：000026 飞亚达精密科技股份有限公司，verified，IVR_3ca69a28…（cninfo 证据已归档）。
- subject：ASJ_67a1f0d0-f1b4-4d78-9969-f439e5aac617@1，perimeter b5ec9001…，PRC_cce87da4…（真实 analysis_subjects 已导入，备份 backup-analysis-subjects-before-000026.sqlite）。
- routing 包：pkg_b5a41d8c… / modrel_fc5de4…（48 模块，current 已切换；modules/contexts 与历史一致）。
- route：route_327b3c77…（partial，eligible=[common]，minimum_questions=24）。
- manifest：24 题（IQS_01…），compose screening-1 成功，manifest 137KB。

## 计划写入（真实 workspace）

1. **route snapshot**：RouteStore.record_snapshot(route, manifest, subject_key, expected_decision_id=route_327b3c77…)；写入 scan.sqlite 的 route 表（历史 anchor）。
2. **universe 成员**：universe-add 000026，scan_enabled=true（或按 owner policy 要求）。
3. **owner policy**：在 config/quick_scan_refresh.json 追加 route（subject_key/scope/scope_id），并写预算曝光接受（cell/controls）。
4. **preview → delegated-confirm → admission**：拿到 ApprovedRefreshSession。
5. **run**：24 题 screening-1 包（1 次 admission；约 24 次模型请求/1 个 pack？按引擎 pack 规则）。

## 成本估算

- CATL 2 题实际：input 11001 / output 11208（含 reasoning），公开价估算 US$0.014537。
- 24 题按线性外推约 US$0.17（含 reasoning 可能更高），不含搜索（本 run 零外搜）。
- 需要在 owner policy 里设单次/累计上限，预算不足即中止。

## 风险与回滚

- 写 owner policy 是暴露接受，必须 owner 批准；写前备份 policy + scan.sqlite + analysis_subjects + identity_receipts。
- route snapshot / universe 写入若中途失败：按备份恢复；不自动重试。
- preview 有 15 分钟 TTL；过期需新 action key。
- run 失败按 runner 的 lease/attempt 语义处理，不重发未知请求。

## 需要独立审查的问题

1. record_snapshot + universe + policy 的写入顺序与幂等性是否安全？
2. 24 题是否必须全部在 1 个 pack？pack 上限 12（共享引擎），是否要拆 2 包/2 次 admission？
3. 预算上限与 cell 设计是否合理（单次 hold/累计）？
4. 失败/部分完成后如何恢复，是否需要新 action key？
5. 是否允许非评分研究型 run（无搜索），还是必须等 S1–S5 搜索接线？

## 边界

- 本轮不写真实 policy/route/universe，不调用模型。
- verified 只是身份；这次 run 仍是非评分/研究型，不产生评分结论。
