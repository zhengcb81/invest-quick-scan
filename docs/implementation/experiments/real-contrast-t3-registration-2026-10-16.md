# T3请求前登记 / 2026-10-16

本轮沿用 [T2预登记](real-contrast-t2-registration-2026-10-16.md) 的公司、2026-10-13截止、12题全分母、9来源18facts、两模型三策略两重复、同公司累计资源、质量先行盲评及停止/计量规则。experiment_id=t3-alphabet，phase=fixed-evidence-t3，12场144槽，真实输出仍是isolated-company-research/1.1.0。具体字节/source/task和顺序以 runs/real-contrast-2026-10-16-02/registration.json 及其raw SHA为准，首次请求前冻结。

T2原首场1HTTP200已结算USD0.004403、0合法答案；第二步SDK因用raw未知数而错误阻断，发送前停止，无新native未知。原T2全部144计划槽与首场产物保留，剩11场不启动，不与T3合并挑胜者。

T3只作两个共同修正：原SDK成功回执后，仅在已显式independent_task绑定时使用include_isolation的blocking_unreconciled_attempts；普通绑定仍用旧保护。prompt明确每答metric_id只能出现一次，不同期间的比较写有来源的summary；原答案schema不放宽。两项修正均不读取/注入私有判定，不针对某模型单独改变，完整block用新phase。SDK回归28个不同测试已覆盖（27+1分批最终），三新增实质反例包括连续两轮、普通绑定拒绝、新unknown阻断。

原native同policy ID与账本，不再改cap或seal旧场。T3前累计36attempt/USD0.212396已知估算、旧USD0.10未知预留、raw inflight1但已审计effective0。新请求全部加到350/$25总上限内；完整现金费用仍未知，不把预留算实耗，不将SDK发送前故障称免费HTTP。

布局补全六工具自身schema资源，JUDGE保留原src/package与root/schemas结构；这些是离线载体校验依赖，不改变公共证据/答案意义。所有推理仅在原SDK内存回传；输出只收标准答案、安全回执和token计数。生产owner/正式评分库不写。
