# 现有列表操作入口：Roster 状态 — 2026-10-18

只读工具 `scripts/roster_status.py` 读取真实 owner workspace（scan/observations），输出每家公司的身份状态、上市地、观察数和下一步动作。不写库、不调用模型。

## 当前快照

| 指标 | 数值 |
|---|---|
| 实体 | 214 |
| verified | 2（CATL、Alphabet） |
| provisional | 212 |
| 市场 | CN 205 / US 11 / HK 1 |
| 下一步：需要 verified | 212 |
| 下一步：可跑画像（已 verified、无观察） | 1 |
| 下一步：已有观察 | 1 |

## 下一步动作语义

- `needs_verified_identity`：provisional，不能出正式 checkpoint/评分；需要法人全称 + 逐发行人官方证据（见 verified-identity 报告）。
- `ready_for_profile`：verified 且无观察，可进入 owner 准入/扫描。
- `has_observations`：已有入库观察（当前 CATL 的 2 条研究型观察）。

## 用法

```powershell
python -B -X utf8 scripts/roster_status.py --json runs/existing-list-onboarding-2026-10-18/roster-status.json
```

## 边界

- 只读；不判断答案质量、不授予评分资格。
- 212 家 provisional 的升级仍受“证据来源”决策阻塞；search-backed 评分另受 provider 条款/价格/存储权利阻塞（见 search-backed 方案）。

## 证据

- 工具：`scripts/roster_status.py`
- 快照：`runs/existing-list-onboarding-2026-10-18/roster-status.json`（本机）
