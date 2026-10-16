## 最新验收状态 — 2026-10-16

本目录三包已由用户交回，总控直接修复后签收package1.0.1并分别提交；不再等待writer或重新派发。见[六包最终验收](../../../experiments/six-tools-acceptance-2026-10-16.md)的当前commit、测试与边界。旧handoff/输入锁保留历史，不代表最新状态；金融准确率和生产owner未由此通过。

# 新一轮独立施工包：会话、论据、补证据

2026-10-16准备，**尚未派发**。上一轮ANSWER-CODEC-03 / RESEARCH-JUDGE-03 / CACHE-PLAN-03已派发，三个旧Lab仍由其harness写入，本轮不占用这些目录。

| 卡片 | 交付 | 唯一可写根（完整路径） |
|---|---|---|
| [SESSION-PACK-04](SESSION-PACK-04.md) | 公司共享证据、各问题包独立短会话的适配器及恢复边界 | `C:/Users/郑曾波/Projects/iqs-session-packing-lab` |
| [CLAIM-GUARD-04](CLAIM-GUARD-04.md) | 财务口径/引用归属检查器与独立批判提示，避免数字对却含义错 | `C:/Users/郑曾波/Projects/iqs-claim-guard-lab` |
| [EVID-GAP-04](EVID-GAP-04.md) | 按问题定位证据缺口，为Alphabet补充有时点、有出处的公开证据 | `C:/Users/郑曾波/Projects/iqs-evidence-gap-lab` |

三包可同时开工，无相互新产物依赖。每包都有可独立运行的单元/集成/公开CLI E2E任务，以及清理与交接要求；只在整包交付时集中审查。总控继续StockQA原生预算不确定性恢复、实际收费模型实验与最终跨仓集成，不与工人同时开发本轮三个候选。

请把对应卡片交给harness即可，卡片要求阅读[共同接口](integration-contract.md)、[输入锁](inputs.lock.json)及对应handoff模板。默认快照 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/research-quality-wave-2026-10-16/inputs`。快照不随Git自动发布，异机必须一并复制，再运行 `python -B -X utf8 verify_preparation.py --inputs <复制根>`；不得回活动仓追latest补文件。

最新实验依据：T0有4/72合法答案，T1有15/72；独立盲评两轮均无充分回答的槽。T0发现OCF误标FCF；T1发现报告OCF减capex被误称营运资本调整前、ROIC/留存/竞争地位过推断以及引用不足。T1还触发资源上限及一条真实连接结果未知，后3会话未启动。这里有明确待解决的问题，不代表agent路线已被否定或任何新方案已优胜。

工人不能执行真实模型/Brave/Tavily/ZAI请求、读密钥或写生产数据。EVID只允许harness自带浏览/搜索核官方公开页面，费用口径按共同规范如实记录；不保存财报/PDF/全文HTML。各包只交候选，不授予production/Financial/G3/F05资格。
