# handoff 顶部补充：测试现状

- IQS tests 共 916 个；全量在本机不可行（g0 manifest 对超大 worktree 逐文件 stat 超时）。以定向测试 + 验收脚本为准。
- QA owner budget 42 passed（1 已知 schema 失败）；SW work decision 31 passed；lab free-agent 6 passed。

# Handoff 顶部更新（2026-10-18）

## 当前事实

- 外部包 EVIDENCE-TIMELINE-11 已验收（ACCEPTED，离线工具，非生产资格）。验收记录：docs/implementation/parallel-lanes/acceptance-2026-10-18/EVIDENCE-TIMELINE-11.md。另两包 COST-LEDGER-11、DELIVERY-AUDIT-11 未见 handoff，保持隔离。
- owner 观察 5 条：IQS_12/16/05/06（research-only）+ IQS_09（search-backed completed）。金融机械检查 5/5，引用溯源 pass 1 / research_only 4。
- 已完成 search-backed 运行：IQS_09（completed）、IQS_18（completed，但 observation 因 evidence=0 被 vendor preview 拒绝，已撤回，导出保留）。
- IQS_20 模型给出 scored=6，离线 validate_single_answer 与外部引用绑定 PASS；因 refresh_admission_plan_changed 无法重跑落库。审阅页：docs/implementation/reviews/search-scored-catl-iqs20-2026-10-18/。
- 观察导入前置检查：scripts/observation_import_preflight.py（score 一致、evidence 非空且 id=src_sha16(url)、executed 搜索需真实 hash+receipt）。

## 协议限制（未改）

1. security 题（22–24）被 refresh-v1.4 policy schema 排除（routes scope 只允许 entity/segment）。
2. 有历史 binding/attempt 的题重跑会 refresh_admission_plan_changed。
3. 已 delivered 的题普通 1.4 请求只能 reuse；重跑必须走 1.2/1.3 的 work_decision_refs（owd1_* retry decision，target_generation=source+1），当前无生成该 decision 的 owner 工具（preview 会报 refresh_no_work_must_be_zero_cost）。
4. 旧观察本身过 vendor 校验（已逐条验证 PASS）；此前的 subject_contract_output_invalid 实为上述 no-work 错误的通用包装。

## 最近提交

- IQS: 7b65a40 验收、069e84a scored 审阅页、c298457 preflight、4b186f2 撤回 IQS_18