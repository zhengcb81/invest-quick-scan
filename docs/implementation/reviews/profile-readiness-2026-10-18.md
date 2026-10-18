# 画像生产就绪度（identity vs owner 准入）— 2026-10-18

只读统计：**verified 身份不等于能跑画像**。真正能跑生产画像还需要该公司在 owner policy 里有 subject/route，并拿到 ApprovedRefreshSession。

## 现状

| 状态 | 数量 | 说明 |
|---|---|---|
| 实体 | 214 | |
| verified 身份 | 209 | 身份层已就绪 |
| provisional | 5 | 002013/300114/688555/872808/06066 |
| owner 已路由 | **1** | CATL（ASJ_02f60cec…） |
| 已有观察 | 1 | CATL（2 条研究型观察） |
| 可跑画像 | **1** | 仅 CATL |
| 需要 owner 准入 | **208** | 身份 OK，但没有 subject/route/policy |
| 需要 verified | 5 | 见上 |

## 这意味着什么

- 208 家已经“身份可用”，但每家公司要跑画像，仍需一次 owner 准入：subject import → route resolve/compose → universe/policy → preview/confirm/admit → ApprovedRefreshSession。
- 这一步不是免费的：每次 run 有模型调用（研究型单题约 $0.007–0.01），并且需要在 owner policy 里登记预算曝光。
- 搜索评分路径还额外需要 provider 条款（route、单价、存储权利），仍未定。

## 工具

- `scripts/profile_readiness.py`：逐公司输出 identity_state / owner_subject_key / observations / next_action。
- `scripts/roster_status.py`：看板同步区分 `needs_verified_identity` / `needs_owner_admission` / `ready_for_profile` / `has_observations`。

## 建议的下一步

1. 先做 **1 家新公司（如 000026 飞亚达）的 owner 准入准备**，在副本演练 subject/route/policy，不付费；
2. 通过独立审查后再真实准入 + 1 题非评分画像（约 $0.01）；
3. 验证通过后，再决定是否批量准入与搜索评分。
