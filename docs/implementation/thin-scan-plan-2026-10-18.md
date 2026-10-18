# 薄草稿扫描方案（Thin Scan）

日期：2026-10-18

## 目的

用最短链路先看到「同一组 24 题 × 几家公司」的大致分数，不进入 owner 正式入账流程。

## 范围

- 公司：宁德时代、飞亚达（000026）、Alphabet（3 家，先用已确认名单里的公司）
- 问题：docs/implementation/questions-24.json（24 题）
- 每题：最多 2 次搜索；总搜索 ≤ 144 次
- 预估：搜索费约 $0.10（按 700 micros/次），模型 token 另计；建议设总预算硬上限后再跑

## 输出

```
drafts/<公司>/answers.json   # 24 条：question_id/status/score/summary/evidence[]/as_of
 drafts/<公司>/index.html    # 一页看完
```

每条明确标注：

- `draft: true`
- `verified: false`（未绑定 owner 凭证、未入观察库）
- `insufficient_evidence` 允许存在，不强行凑分

## 规则

1. 有分数就必须有可点开的来源；没有来源就标 insufficient。
2. 不编造 URL、不把计划当已发生、不把参考估算当发票。
3. 不写 owner 库、不做预算预留、不签确认、不生成 receipt。
4. 搜索失败/超时：该题记 insufficient，继续下一题。

## 验收

- 24/24 题都有结果（分数或 insufficient）
- 所有 scored 答案至少 1 条来源
- 页面能离线打开
- 运行日志记录每题搜索次数与总调用数

## 与正式路径的关系

薄草稿只用于「先看分、再决定谁值得走正式流程」。正式路径仍需 route/admission/receipt，二者不混用。
